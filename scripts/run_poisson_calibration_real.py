"""Corre la calibracion Poisson (src/envs/calibration_poisson.py, Mauricio,
tarea 2.1.3) sobre datos REALES de IPSA en vez del dataset sintetico de demo.

Contexto (23 sept 2026, PS): el modulo de calibracion esperaba archivos
`<TICKER>_clean.parquet`, pero el pipeline real de limpieza (Benjamin,
`src/data/clean_ohlcv.py`) los guarda como `<TICKER>.parquet` (sin sufijo
`_clean`) -- otra discrepancia de contrato entre componentes, distinta de la
de MaestroEnv/MasterActorCritic. Este script no modifica ninguno de los dos
archivos (para no decidir unilateralmente cual convencion "gana"); carga los
parquet reales directamente con pandas, usando las funciones de calibracion
tal cual estan.

Uso:
    python scripts/run_poisson_calibration_real.py

Requiere que ya exista `data/processed/clean_5m_<fecha>/` (salida de
`src/data/clean_ohlcv.py`) y `data/processed/sm_features_<fecha>/` no es
necesario para este script (usa el parquet limpio, no las features S_M).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.envs.calibration_poisson import (
    DEFAULT_OUTPUT_JSON,
    calibrate_poisson_params,
    extract_lob_features,
    validate_calibration,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"

# Tier A = cobertura pre-fill >= 60% (ver salida de clean_ohlcv.py) -> los mas
# aptos para calibracion individual. Se calibra 1 por 1 y tambien un agregado
# "IPSA_AGREGADO" concatenando los retornos de los 15 para tener una cifra
# unica de referencia, ya que R_M/S_M operan sobre el indice, no un ticker.
TIER_A_TICKERS = [
    "ANDINA-B", "BCI", "BSANTANDER", "CENCOSUD", "CHILE", "CMPC", "COPEC",
    "ENELAM", "ENELCHILE", "FALABELLA", "ITAUCL", "LTM", "MALLPLAZA",
    "PARAUCO", "SQM-B",
]


def find_latest_clean_dir() -> Path:
    candidates = sorted(p for p in PROCESSED_DIR.glob("clean_5m_*") if p.name != "clean_5m_demo")
    if not candidates:
        raise FileNotFoundError(
            f"No se encontro ninguna carpeta clean_5m_* en {PROCESSED_DIR}. "
            "Correr primero src/data/download_ohlcv.py y src/data/clean_ohlcv.py."
        )
    return candidates[-1]


def load_real_clean(ticker: str, clean_dir: Path) -> pd.DataFrame:
    """Carga `<ticker>.parquet` (convencion real de clean_ohlcv.py) y agrega
    `ret` a partir de los precios SIN escalar (`close_raw`), no de las
    columnas `close`/`high`/`low` normalizadas con MinMaxScaler -- el spread
    (high-low) y los retornos deben calcularse en la escala real de precios,
    no en [0,1], o pierden su interpretacion economica."""
    path = clean_dir / f"{ticker}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"No existe {path}")
    df = pd.read_parquet(path)
    # Seleccionar las columnas _raw ANTES de renombrar: el parquet ya tiene
    # una columna 'close' (escalada [0,1]) -- renombrar sin seleccionar antes
    # produce dos columnas 'close' duplicadas y rompe el calculo de 'ret'.
    df = df[["close_raw", "high_raw", "low_raw"]].rename(
        columns={"close_raw": "close", "high_raw": "high", "low_raw": "low"}
    ).copy()
    df["ret"] = np.log(df["close"] / df["close"].shift(1))
    return df


def main():
    clean_dir = find_latest_clean_dir()
    print(f"Usando datos reales de: {clean_dir}")

    per_ticker = {}
    all_rets = []

    for ticker in TIER_A_TICKERS:
        try:
            df = load_real_clean(ticker, clean_dir)
        except FileNotFoundError as e:
            print(f"[{ticker}] SKIP: {e}")
            continue

        features = extract_lob_features(df)
        calibrated = calibrate_poisson_params(features)
        ret_clean = df["ret"].dropna().values
        validation = validate_calibration(calibrated, ret_clean)
        all_rets.append(ret_clean)

        per_ticker[ticker] = {
            "features": features,
            "calibrated_params": calibrated,
            "validation": validation,
            "n_rows": int(len(df)),
        }
        print(f"[{ticker}] lambda+={calibrated['lambda_plus']:.4f} "
              f"lambda-={calibrated['lambda_minus']:.4f} theta={calibrated['theta']:.4f} "
              f"| KS valid={validation['valid']} (p={validation['p_value']:.4g})")

    # Agregado IPSA: concatenar retornos de los 15 tickers Tier A y calibrar
    # una sola vez sobre esa serie combinada -> parametros que puede usar el
    # Agente Maestro (que opera sobre el indice, no un solo activo).
    combined_ret = np.concatenate(all_rets)
    combined_df = pd.DataFrame({"ret": combined_ret})
    combined_features = {
        "spread": float(np.mean([per_ticker[t]["features"]["spread"] for t in per_ticker])),
        "volatility": float(np.nanstd(combined_ret)),
        "skewness": float(pd.Series(combined_ret).skew()),
        "kurtosis": float(pd.Series(combined_ret).kurt()),
    }
    combined_calibrated = calibrate_poisson_params(combined_features)
    combined_validation = validate_calibration(combined_calibrated, combined_ret)

    print(f"\n[IPSA_AGREGADO, {len(per_ticker)} tickers Tier A] "
          f"lambda+={combined_calibrated['lambda_plus']:.4f} "
          f"lambda-={combined_calibrated['lambda_minus']:.4f} "
          f"theta={combined_calibrated['theta']:.4f} | "
          f"KS valid={combined_validation['valid']} (p={combined_validation['p_value']:.4g})")

    n_valid = sum(1 for t in per_ticker.values() if t["validation"]["valid"])
    print(f"\n{n_valid}/{len(per_ticker)} tickers Tier A con p-value > 0.05 (KS test).")
    if n_valid < len(per_ticker):
        print("NOTA: un modelo de Poisson simple no necesariamente captura toda la")
        print("dinamica de retornos reales (colas pesadas, clustering de volatilidad).")
        print("Esto es información real de calibración a reportar, no un error del script.")

    payload = {
        "calibrated_params": combined_calibrated,
        "validation": combined_validation,
        "metadata": {
            "data_source": "REAL (yfinance, IPSA, descargado 23 sept 2026)",
            "clean_dir": str(clean_dir.relative_to(REPO_ROOT)),
            "tier": "Tier A (cobertura pre-fill >= 60%)",
            "n_tickers": len(per_ticker),
            "tickers": list(per_ticker.keys()),
            "nota": "Calibracion agregada sobre retornos concatenados de los tickers Tier A. "
                    "Ver poisson_params_calibrated_por_ticker.json para el detalle individual.",
        },
    }
    DEFAULT_OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(DEFAULT_OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"\nGuardado: {DEFAULT_OUTPUT_JSON.relative_to(REPO_ROOT)}")

    per_ticker_path = DEFAULT_OUTPUT_JSON.parent / "poisson_params_calibrated_por_ticker.json"
    with open(per_ticker_path, "w", encoding="utf-8") as f:
        json.dump(per_ticker, f, indent=2)
    print(f"Guardado: {per_ticker_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
