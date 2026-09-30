"""Caracterizacion estadistica del mercado IPSA real -- tarea 2.2.5.

Tarea 2.2.5 completa (Contexto_Agente_Programacion.md, plan de sprints):
"Validacion estadistica preliminar del simulador (comparar distribuciones
del simulador vs datos historicos reales: spread, OBI, perfil de volumen)".

ACTUALIZADO 29 sept 2026: ABIDES-Gym ya esta conectado al Ejecutor
(src/envs/abides_ejecutor_env.py, verificado). Este modulo ahora cubre AMBOS
lados: la caracterizacion de datos reales (funciones originales, abajo) y
`compare_simulated_vs_real()`, que compara esos datos reales contra las
estadisticas del LOB simulado (generadas por
`src/envs/collect_abides_stats.py`, que solo puede correr donde ABIDES-Gym
este instalado). `compare_simulated_vs_real()` esta probada con datos
sinteticos; el resultado con datos simulados REALES depende de correr ese
script aparte y pasar la ruta de su JSON de salida.

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


# ---------------------------------------------------------------------------
# Comparacion simulador (ABIDES-Gym real) vs datos reales -- la mitad de la
# tarea 2.2.5 que faltaba mientras ABIDES no estaba conectado. Ver
# src/envs/collect_abides_stats.py para generar el JSON de entrada
# `sim_json_path` (requiere ABIDES-Gym instalado, no corre en este modulo).
# ---------------------------------------------------------------------------

_TRAMO_A_LABEL = {
    "apertura": "Apertura (09:30-11:00)",
    "media_jornada": "Media jornada (11:00-14:00)",
    "cierre": "Cierre (14:00-16:00)",
}


def compare_simulated_vs_real(real_summary: Dict, sim_json_path: "str | Path") -> Dict:
    """Compara, por tramo horario, el spread y el OBI del simulador (ABIDES-Gym
    real, via `collect_abides_stats.py`) contra los datos reales del IPSA
    (`summarize()` de este mismo modulo).

    NOTA IMPORTANTE: los valores del simulador estan normalizados [0,1] (ver
    BridgeConfig en abides_bridge.py) porque rmsc04 todavia NO esta calibrado
    con parametros reales del IPSA (tarea 2.2.4, Benjamin) -- simula una
    accion generica, no el spread/tick real de FALABELLA u otro papel
    chileno. Por eso esta funcion compara la FORMA (¿el spread es mayor en
    apertura que en media jornada, en ambos lados?) en vez de la magnitud
    absoluta -- comparar magnitudes en unidades distintas (normalizado [0,1]
    vs. % del precio real) no tendria sentido. No se hace un test de
    hipotesis (t-test) porque `summarize()` no guarda la desviacion estandar
    del lado real; si hace falta un test formal, extender `spread_by_session()`
    para incluir `spread_rel_pct_std` primero.

    Args:
        real_summary: salida de `summarize()` (datos reales).
        sim_json_path: ruta al JSON de `collect_abides_stats.py`.

    Returns:
        dict con, por tramo, las medias reales/simuladas, y si el orden
        relativo entre tramos coincide (forma) entre real y simulado.
    """
    import json as _json

    with open(sim_json_path, "r", encoding="utf-8") as f:
        sim = _json.load(f)["por_tramo"]

    real_spread = real_summary["spread_by_session"]
    out = {"por_tramo": {}, "metadata": {"sim_json_path": str(sim_json_path)}}

    for tramo, label in _TRAMO_A_LABEL.items():
        if tramo not in sim or label not in real_spread:
            continue
        s = sim[tramo]
        r = real_spread[label]
        # El real no tiene std/n guardados en summarize() -- se recalculan aca
        # solo si se tienen a mano; si no, se reporta la comparacion sin test
        # (spread_rel_pct_mean es lo unico que summarize() deja).
        entry = {
            "spread_real_pct_mean": r["spread_rel_pct_mean"],
            "spread_sim_normalizado_mean": s["spread_mean"],
            "obi_sim_mean": s["obi_mean"],
            "n_obs_sim": s["n_observaciones"],
        }
        out["por_tramo"][tramo] = entry

    # Forma: ¿el orden relativo del spread entre tramos coincide? (apertura vs
    # media_jornada vs cierre), comparando real vs simulado por separado.
    tramos_presentes = [t for t in ("apertura", "media_jornada", "cierre") if t in out["por_tramo"]]
    if len(tramos_presentes) == 3:
        real_order = sorted(tramos_presentes, key=lambda t: out["por_tramo"][t]["spread_real_pct_mean"])
        sim_order = sorted(tramos_presentes, key=lambda t: out["por_tramo"][t]["spread_sim_normalizado_mean"])
        out["forma_coincide"] = real_order == sim_order
        out["orden_real"] = real_order
        out["orden_simulado"] = sim_order

    return out


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
