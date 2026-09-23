"""Caracterizacion estadistica del mercado IPSA real -- tarea 2.2.5 (parcial).

Tarea 2.2.5 completa (Contexto_Agente_Programacion.md, plan de sprints):
"Validacion estadistica preliminar del simulador (comparar distribuciones
del simulador vs datos historicos reales: spread, OBI, perfil de volumen)".

Este modulo SOLO cubre el lado "datos historicos reales" de esa comparacion
-- calcula spread (proxy), volatilidad y perfil de volumen por tramo horario
sobre datos reales del IPSA. El lado "simulador" (ABIDES-Gym) no existe
todavia en este repo (ver DIAGNOSTICO_Y_PLAN_23SEP.md / RESULTADOS_DESBLOQUEO
_23SEP.md), asi que la comparacion real queda pendiente para cuando ABIDES
este integrado. Lo de aqui deja la mitad "real" ya lista y verificada, para
no tener que rehacerla despues.

Fuente de datos esperada: `data/processed/clean_5m_<fecha>/_combined.parquet`
(salida de `src/data/clean_ohlcv.py`, columnas *_raw sin escalar).

OBI (Order Book Imbalance) NO se puede calcular aqui: requiere Nivel 2 del
LOB (bid/ask por niveles), que solo provee ABIDES-Gym (ver SM_schema.json,
variable OBI_agregado). No se aproxima con un proxy inventado porque no hay
una forma razonable de derivarlo de datos OHLCV agregados.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

sns.set_theme(style="whitegrid")

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROCESSED_DIR = REPO_ROOT / "data" / "processed"

SESSION_LABELS = {0.0: "Apertura (09:30-11:00)", 0.5: "Media jornada (11:00-14:00)", 1.0: "Cierre (14:00-16:00)"}


def find_latest_clean_combined(processed_dir: Path = DEFAULT_PROCESSED_DIR) -> Path:
    """Encuentra el `_combined.parquet` mas reciente de `clean_5m_*` (excluyendo `clean_5m_demo`)."""
    candidates = sorted(
        p for p in processed_dir.glob("clean_5m_*") if p.name != "clean_5m_demo"
    )
    if not candidates:
        raise FileNotFoundError(
            f"No se encontro ninguna carpeta clean_5m_* en {processed_dir}. "
            "Correr primero src/data/download_ohlcv.py y src/data/clean_ohlcv.py."
        )
    path = candidates[-1] / "_combined.parquet"
    if not path.exists():
        raise FileNotFoundError(f"No existe {path}")
    return path


def _session_from_hour(hour: pd.Series) -> pd.Series:
    """Mapea la hora del dia a tramo (0.0 apertura, 0.5 media, 1.0 cierre),
    igual que src/features/build_sm_features.py (mismo contrato, sin
    importarlo directamente para no acoplar este modulo a su CLI)."""
    return pd.cut(
        hour, bins=[-1, 11, 14, 24], labels=[0.0, 0.5, 1.0]
    ).astype(float)


def load_market_data(path: "str | Path" = None) -> pd.DataFrame:
    """Carga el parquet combinado real y agrega `spread_proxy`, `log_return`
    y `sesion` (tramo horario)."""
    path = Path(path) if path else find_latest_clean_combined()
    df = pd.read_parquet(path)
    df = df.copy()
    df["spread_proxy"] = df["high_raw"] - df["low_raw"]
    df["sesion"] = _session_from_hour(df["datetime_santiago"].dt.hour + df["datetime_santiago"].dt.minute / 60.0)
    df = df.sort_values(["ticker", "datetime_santiago"])
    df["log_return"] = df.groupby("ticker")["close_raw"].transform(lambda s: np.log(s / s.shift(1)))
    return df


def spread_by_session(df: pd.DataFrame) -> pd.DataFrame:
    """Spread promedio (proxy high-low) por tramo horario, agregado sobre todos los tickers.

    Se reporta tambien como % del precio (spread relativo), que es la forma
    comparable entre tickers de distinto precio absoluto.
    """
    tmp = df.copy()
    tmp["spread_rel_pct"] = tmp["spread_proxy"] / tmp["close_raw"] * 100
    out = tmp.groupby("sesion").agg(
        spread_abs_mean=("spread_proxy", "mean"),
        spread_rel_pct_mean=("spread_rel_pct", "mean"),
        n_obs=("spread_proxy", "count"),
    )
    out.index = out.index.map(SESSION_LABELS)
    return out


def volatility_by_session(df: pd.DataFrame, window: int = 6) -> pd.DataFrame:
    """Volatilidad (std de log-returns, ventana movil de `window` velas) por tramo horario."""
    tmp = df.copy()
    tmp["rolling_vol"] = tmp.groupby("ticker")["log_return"].transform(
        lambda s: s.rolling(window, min_periods=2).std()
    )
    out = tmp.groupby("sesion").agg(
        volatility_mean=("rolling_vol", "mean"),
        volatility_std=("rolling_vol", "std"),
        n_obs=("rolling_vol", "count"),
    )
    out.index = out.index.map(SESSION_LABELS)
    return out


def volume_profile_by_session(df: pd.DataFrame) -> pd.DataFrame:
    """Volumen promedio por tramo horario (perfil de volumen intradiario, Titulo I seccion 4.1.1:
    se espera mayor actividad en apertura/cierre que en media jornada)."""
    out = df.groupby("sesion").agg(
        volume_mean=("volume_raw", "mean"),
        volume_total=("volume_raw", "sum"),
        n_obs=("volume_raw", "count"),
    )
    out.index = out.index.map(SESSION_LABELS)
    return out


def plot_market_profile(df: pd.DataFrame, save_path: "str | Path | None" = None):
    """Grafico de 3 paneles: spread relativo, volatilidad y volumen, por tramo horario.
    Es la evidencia visual de los "hechos estilizados" citados en el Titulo I
    (seccion 4.1.1): spread mas amplio y menor profundidad en media jornada."""
    spread_df = spread_by_session(df)
    vol_df = volatility_by_session(df)
    volume_df = volume_profile_by_session(df)

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))

    axes[0].bar(spread_df.index, spread_df["spread_rel_pct_mean"], color="steelblue")
    axes[0].set_title("Spread relativo promedio (%)")
    axes[0].set_ylabel("% del precio")
    axes[0].tick_params(axis="x", rotation=20)

    axes[1].bar(vol_df.index, vol_df["volatility_mean"], color="indianred")
    axes[1].set_title("Volatilidad promedio (std log-return, rolling(6))")
    axes[1].tick_params(axis="x", rotation=20)

    axes[2].bar(volume_df.index, volume_df["volume_mean"], color="seagreen")
    axes[2].set_title("Volumen promedio por vela")
    axes[2].tick_params(axis="x", rotation=20)

    fig.suptitle("Perfil intradiario del mercado IPSA (datos reales, 30 tickers, 60 dias)")
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def summarize(df: pd.DataFrame) -> Dict:
    """Resumen consolidado (los 3 dataframes anteriores) como dict serializable a JSON."""
    return {
        "spread_by_session": spread_by_session(df).to_dict(orient="index"),
        "volatility_by_session": volatility_by_session(df).to_dict(orient="index"),
        "volume_by_session": volume_profile_by_session(df).to_dict(orient="index"),
        "n_tickers": int(df["ticker"].nunique()),
        "n_rows": int(len(df)),
        "date_range": [str(df["datetime_santiago"].min()), str(df["datetime_santiago"].max())],
    }


if __name__ == "__main__":
    import json

    market_df = load_market_data()
    summary = summarize(market_df)
    print(json.dumps(summary, indent=2, default=str))

    out_dir = REPO_ROOT / "data" / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)
    plot_market_profile(market_df, save_path=out_dir / "perfil_mercado_ipsa_real.png")
    with open(out_dir / "perfil_mercado_ipsa_real.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\nGuardado en {out_dir}")
