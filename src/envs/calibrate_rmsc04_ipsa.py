"""Plantilla de calibracion de `rmsc04` (config de ABIDES-Gym) con parametros
reales del IPSA -- tarea 2.2.4 (Sprint 4), Benjamin Farias (BF).

*** BASE / PLANTILLA, NO LA TAREA TERMINADA (29 sept 2026, PS) ***
Dejo cableados (`campos_cableados`, abajo) solo los parametros de rmsc04 que
se derivan DIRECTAMENTE de datos ya existentes, sin ninguna decision de
metodologia:
    - `r_bar`: precio mediano real del ticker (de `data/processed/clean_5m_*`).
    - `fund_vol`: heuristica simple (obs_return_std * r_bar), documentada como
      heuristica, NO una conversion de unidades validada.
    - `starting_cash`, `ticker`, `date`, `end_time`: valores de contexto, sin
      calibrar (no dependen de la microestructura real).

Dejo EXPLICITAMENTE sin calibrar (`campos_pendientes`, abajo, con el default
de rmsc04 sin tocar) los parametros que requieren una decision de metodologia
que no me corresponde inventar -- son justamente la tarea 2.2.4:
    - `kappa` / `kappa_oracle`: mean-reversion del valor fundamental. No hay
      una formula directa desde lambda_plus/lambda_minus/theta (que describen
      LLEGADA DE ORDENES en el modelo de Poisson de Benjamin, tarea 2.1.3) a
      esto (que describe la DINAMICA DEL VALOR FUNDAMENTAL en el modelo de
      agentes de ABIDES) -- son dos modelos de microestructura distintos, con
      escalas de tiempo y unidades distintas. Traducir uno al otro es una
      decision de metodologia real, no un porteo mecanico.
    - `sigma_s`, `lambda_a`, `megashock_*`: mismo problema -- estos parametros
      viven en la escala interna de ABIDES (ValueAgent/Oracle), no tienen un
      analogo directo calculable desde `poisson_params_2026-08-23.json`.
    - `mm_*` (market maker): dependen de decisiones de diseno de mercado
      (¿que tan agresivo debe ser el market maker simulado?), no de un dato
      historico a estimar.
    - `num_noise_agents` / `num_value_agents` / `num_momentum_agents`: podrian
      escalarse con el volumen real (`avg_order_size`, `volume_cap` en
      `tickers_info` del JSON de calibracion), pero eso YA es una decision de
      diseno del experimento (Sprint 4/5, cuantos agentes representan al
      "resto del mercado" para cada ticker), no algo que deba decidir por mi
      cuenta.

Verificado contra la firma real de `build_config()` en
`abides_markets/configs/rmsc04.py` (repo oficial jpmorganchase/abides-jpmc-
public, rama main) via WebFetch el 29 sept 2026 -- no se adivinaron nombres
de parametros.

Uso (en Colab, donde abides_markets este instalado):

    from abides_markets.configs import rmsc04
    from src.envs.calibrate_rmsc04_ipsa import build_rmsc04_ipsa_config

    cfg_kwargs = build_rmsc04_ipsa_config(ticker="FALABELLA", tramo="apertura")
    config_state = rmsc04.build_config(**cfg_kwargs)  # los pendientes usan el default de rmsc04

Sin ABIDES instalado (como en este entorno), este archivo solo se puede
syntax-chequear e importar -- `build_rmsc04_ipsa_config()` no depende de
`abides_markets`, asi que SI corre sin ABIDES (se probo localmente, ver
`tests/test_calibrate_rmsc04_ipsa.py`).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CALIBRATION_JSON = REPO_ROOT / "data" / "calibration" / "poisson_params_2026-08-23.json"
# NOTA: el snapshot `clean_5m_2026-08-23` (mismo periodo que la calibracion
# Poisson de Benjamin) solo tiene localmente `cleaning_report.json`/
# `scaler_params.json`, sin los parquet -- se ve que no se conservaron. El
# snapshot que SI tiene los datos completos localmente (`_combined.parquet`
# + un parquet por ticker) es `clean_5m_2026-09-23` (un mes despues); se usa
# ese como default para que `r_bar` sea calculable ahora. Repetir con
# `clean_5m_2026-08-23` si en algun momento se recupera ese snapshot, para
# que `r_bar` sea del mismo periodo exacto que `lambda_plus`/`lambda_minus`.
DEFAULT_CLEAN_5M_DIR = REPO_ROOT / "data" / "processed" / "clean_5m_2026-09-23"

# Mapeo tramo (Poisson, Benjamin) -> hora de inicio/fin dentro de la jornada,
# igual que TRAMO_FIRST_INTERVAL en src/envs/abides_ejecutor_env.py (no se
# reimporta para no acoplar este modulo, que debe poder importarse sin
# ABIDES instalado).
_TRAMO_HORAS = {
    "apertura": ("09:30:00", "11:30:00"),
    "media_jornada": ("11:30:00", "14:00:00"),
    "cierre": ("14:00:00", "16:00:00"),
}

# Parametros de rmsc04.build_config() que este modulo NO calibra (quedan en
# el default de rmsc04 -- no se listan valores aqui para no duplicar/desincronizar
# con la firma real; ver docstring de modulo para el porque de cada grupo).
CAMPOS_PENDIENTES_2_2_4 = (
    "kappa", "kappa_oracle", "sigma_s", "lambda_a",
    "megashock_lambda_a", "megashock_mean", "megashock_var",
    "mm_window_size", "mm_pov", "mm_num_ticks", "mm_wake_up_freq",
    "mm_min_order_size", "mm_skew_beta", "mm_price_skew", "mm_level_spacing",
    "mm_spread_alpha", "mm_backstop_quantity", "mm_cancel_limit_delay",
    "num_noise_agents", "num_value_agents", "num_momentum_agents",
)


def _median_close_price(ticker: str, clean_5m_dir: Path) -> float:
    """Precio mediano real del ticker (CLP) sobre el snapshot de datos
    limpios, para usar como `r_bar` (rmsc04 lo espera en CENTAVOS de la
    unidad de cuenta interna -- ver `starting_cash` en la misma escala en
    el config real -- por eso se multiplica x100 en `build_rmsc04_ipsa_config`,
    no aqui)."""
    df = pd.read_parquet(clean_5m_dir / "_combined.parquet")
    sub = df[df["ticker"] == ticker]
    if sub.empty:
        raise ValueError(
            f"Ticker {ticker!r} no encontrado en {clean_5m_dir}. "
            f"Tickers disponibles: {sorted(df['ticker'].unique())[:5]}..."
        )
    return float(sub["close_raw"].median())


def _lambda_params_por_tramo(ticker: str, tramo: str, calibration_json: Path) -> Dict:
    """Lee lambda_plus/lambda_minus/theta/obs_return_std reales de Benjamin
    (tarea 2.1.3) para (ticker, tramo). Se usan solo para `fund_vol` (heuristica
    documentada arriba); lambda_plus/lambda_minus en si NO se mapean a ningun
    campo de rmsc04 (ver `CAMPOS_PENDIENTES_2_2_4`)."""
    with open(calibration_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    params = data["params"]
    if ticker not in params:
        raise ValueError(
            f"Ticker {ticker!r} no esta en {calibration_json}. "
            f"Tickers disponibles: {sorted(params.keys())[:5]}..."
        )
    if tramo not in params[ticker]:
        raise ValueError(f"Tramo {tramo!r} invalido. Validos: {list(_TRAMO_HORAS)}")
    return params[ticker][tramo]


def build_rmsc04_ipsa_config(
    ticker: str,
    tramo: str,
    date: str = "20260823",
    calibration_json: Optional[Path] = None,
    clean_5m_dir: Optional[Path] = None,
    starting_cash: int = 10_000_000,
) -> Dict:
    """Arma el dict de kwargs para `rmsc04.build_config(**kwargs)`, con los
    campos derivables de datos reales del IPSA ya rellenos, y el resto
    (`CAMPOS_PENDIENTES_2_2_4`) deliberadamente AUSENTE del dict -- al no
    pasarlos, `build_config()` usa su propio default de rmsc04 (no se copian
    aqui para no desincronizarse si rmsc04 cambia). Rellenarlos con valores
    reales calibrados es la tarea 2.2.4 completa.

    Args:
        ticker: simbolo IPSA tal como aparece en `poisson_params_2026-08-23.json`
            y en `clean_5m_*/_combined.parquet` (ej. "FALABELLA", sin sufijo .SN).
        tramo: "apertura" | "media_jornada" | "cierre".
        date: fecha de simulacion para rmsc04 (formato YYYYMMDD), default el
            snapshot de calibracion de Benjamin.
        calibration_json: ruta a `poisson_params_2026-08-23.json` (Benjamin,
            tarea 2.1.3). Default: `data/calibration/poisson_params_2026-08-23.json`.
        clean_5m_dir: carpeta `clean_5m_<fecha>` con `_combined.parquet`
            (Benjamin, tarea 1.2.1). Default: snapshot 2026-08-23 (mismo que
            la calibracion, para que `r_bar` y `lambda_plus/minus` sean del
            mismo periodo).
        starting_cash: capital inicial por agente (centavos), sin calibrar
            (no depende de microestructura real, solo de que alcance para
            operar sin quedar sin efectivo).

    Returns:
        dict listo para `rmsc04.build_config(**dict)` (o para inspeccionar/
        loggear antes de correrlo). Incluye una llave extra
        `_campos_pendientes_2_2_4` (lista, no un kwarg real de rmsc04 --
        quitar antes de pasar el dict a build_config) que documenta que
        falta calibrar, para que quede explicito en cualquier notebook que
        use esta funcion.
    """
    if tramo not in _TRAMO_HORAS:
        raise ValueError(f"tramo invalido: {tramo!r}. Validos: {list(_TRAMO_HORAS)}")

    calibration_json = calibration_json or DEFAULT_CALIBRATION_JSON
    clean_5m_dir = clean_5m_dir or DEFAULT_CLEAN_5M_DIR
    hora_inicio, hora_fin = _TRAMO_HORAS[tramo]

    r_bar_clp = _median_close_price(ticker, clean_5m_dir)
    lambda_params = _lambda_params_por_tramo(ticker, tramo, calibration_json)
    obs_return_std = lambda_params["obs_return_std"]  # std de retorno log, ventana de 5 min

    r_bar_centavos = r_bar_clp * 100  # rmsc04 opera en centavos (misma escala que starting_cash)
    # fund_vol heuristico: escala el ruido fundamental de ABIDES a la
    # volatilidad real observada del ticker. Es una heuristica de PRIMER
    # ORDEN (no valida las unidades internas del proceso de Oracle de ABIDES
    # contra esto), documentada asi para que Benjamin la revise/reemplace en
    # 2.2.4 si encuentra una conversion mas rigurosa.
    fund_vol_heuristico = abs(obs_return_std) * r_bar_centavos

    cfg = {
        "ticker": ticker,
        "date": date,
        "end_time": "16:00:00",
        "starting_cash": starting_cash,
        "r_bar": r_bar_centavos,
        "fund_vol": fund_vol_heuristico,
        "_campos_pendientes_2_2_4": list(CAMPOS_PENDIENTES_2_2_4),
        "_metadata": {
            "tramo": tramo, "hora_inicio": hora_inicio, "hora_fin": hora_fin,
            "r_bar_clp_mediano": r_bar_clp,
            "obs_return_std_fuente": "poisson_params_2026-08-23.json (Benjamin, 2.1.3)",
        },
    }
    return cfg


if __name__ == "__main__":
    cfg = build_rmsc04_ipsa_config(ticker="FALABELLA", tramo="apertura")
    print(json.dumps(cfg, indent=2, ensure_ascii=False, default=str))
