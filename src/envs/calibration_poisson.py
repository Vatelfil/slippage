"""Calibracion por tramo horario de un modelo de llegadas de ordenes tipo
Poisson (lambda+, lambda-, theta) para el Order Book, con datos reales OHLCV
de 5 min del IPSA.

Tarea 2.1.3 (Sprint 3). Version original (API, modelo y demo sintetico):
Paolo Sepulveda (PS). Adaptacion a datos reales y por tramo horario:
Benjamin Farias (BF).

Fuente de datos (pipeline de las tareas 1.2.1/1.2.2):
    data/processed/clean_5m_<snapshot>/<TICKER>.parquet
donde <TICKER> NO lleva ".SN" ni sufijo. Las columnas open/high/low/close/
volume de ese parquet estan normalizadas con MinMaxScaler por ticker; las
columnas *_raw son las originales (CLP y numero de acciones). Esta
calibracion usa SIEMPRE las *_raw (ver `load_clean_data`).

Metodologia (Titulo I, seccion 4.3.3; Cont, Stoikov & Talreja, 2010)
---------------------------------------------------------------------
Se estima un triple (lambda+, lambda-, theta) por ticker x tramo, con los
tramos de los Agentes Ejecutores (hora America/Santiago):

    apertura       [09:30, 11:30)
    media_jornada  [11:30, 14:00)
    cierre         [14:00, 16:00]

Las velas etiquetadas con is_imputed=True (sin transaccion real, rellenadas
por ffill/bfill en 1.2.1) se excluyen de todas las estimaciones.

1. lambda+ / lambda- (ordenes por paso de 30 s del Ejecutor):
   El volumen de cada vela observada se asigna al lado comprador o vendedor
   segun el signo de close-open; si close == open se usa la tick rule
   (signo de close menos el ultimo close del mismo dia); si ambos son 0, el
   volumen se reparte 50/50. Luego

       lambda+/- = sum(V+/-) / (n_velas_observadas * 10) / avg_order_size

   (10 = pasos de 30 s en una vela de 5 min). `avg_order_size` es un
   SUPUESTO: por defecto se deriva de un nocional fijo por orden
   (DEFAULT_ORDER_NOTIONAL_CLP / mediana de close_raw del ticker), o se
   entrega explicitamente en acciones. lambda escala como 1/avg_order_size.

2. theta (tasa de cancelacion, por paso de 30 s):
   Sin Nivel 2 no se observan cancelaciones. Se aproxima mediante la
   persistencia del rango high-low relativo HL_t = (high-low)/mid, proxy
   del spread/profundidad disponible: si los shocks de liquidez decaen a
   tasa theta por paso, la autocorrelacion de orden 1 entre velas
   consecutivas (10 pasos) es rho = exp(-10 theta), por lo que

       theta = -ln(rho) / 10,   con rho recortado a [0.01, 0.99].

   Como proxy del spread se reporta ademas el estimador de Roll (1984),
   S = 2 sqrt(-cov(r_t, r_{t-1})), y el rango HL relativo medio, ambos en bps.

3. Validacion: los parametros se inyectan en `PoissonLOBModel`, que simula
   retornos de 5 min agregando 10 pasos de 30 s; la escala (impacto por
   orden neta) se fija por momentos igualando la desviacion estandar
   observada, de modo que el test KS de 2 muestras evalua la FORMA de la
   distribucion (colas, discrecion, asimetria), no su escala.

Limitaciones: velas de 5 min de yfinance, sin Nivel 2 ni prints
individuales; el signo del volumen y theta son proxies. Ver
docs/calibracion_poisson_2.1.3_BF.md.

Uso:
    python -m src.envs.calibration_poisson --snapshot 2026-08-23 --tickers FALABELLA
    python -m src.envs.calibration_poisson --snapshot 2026-08-23 --all
    python -m src.envs.calibration_poisson --demo     # smoke-test SINTETICO de PS
"""
from __future__ import annotations

import argparse
import json
import platform
import re
import zlib
from datetime import datetime, time, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import kurtosis, ks_2samp, skew

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = _REPO_ROOT / "data" / "processed"
DEFAULT_CALIBRATION_DIR = _REPO_ROOT / "data" / "calibration"
DEFAULT_RESULTS_DIR = _REPO_ROOT / "results" / "sprint3"
# Salidas del modo --demo (sinteticas, ignoradas por git)
DEMO_OUTPUT_DIR = DEFAULT_CALIBRATION_DIR / "demo"
DEFAULT_OUTPUT_JSON = DEMO_OUTPUT_DIR / "poisson_params_calibrated.json"
DEFAULT_OUTPUT_PLOT = DEMO_OUTPUT_DIR / "poisson_params_visualization.png"

SANTIAGO_TZ = "America/Santiago"

# Tramos de los Agentes Ejecutores (docs/arquitectura_entorno_simulacion.md,
# seccion 3.1; SE_schema.json). Intervalos [inicio, fin), salvo el ultimo,
# que incluye las 16:00.
TRAMOS: Tuple[Tuple[str, str, str], ...] = (
    ("apertura", "09:30", "11:30"),
    ("media_jornada", "11:30", "14:00"),
    ("cierre", "14:00", "16:00"),
)
TRAMO_NAMES: Tuple[str, ...] = tuple(t[0] for t in TRAMOS)

STEP_SECONDS = 30                                 # paso del Ejecutor
BAR_MINUTES = 5                                   # resolucion yfinance
STEPS_PER_BAR = BAR_MINUTES * 60 // STEP_SECONDS  # = 10

# Vela en la que 1.2.1 fusiona la subasta de cierre (CLOSING_AUCTION_NOTE
# en src/data/clean_ohlcv.py). Su volumen no proviene del flujo continuo de
# ordenes que modela el proceso de Poisson, por lo que se excluye por defecto.
CLOSING_AUCTION_BAR = "15:55"

DEFAULT_ORDER_NOTIONAL_CLP = 1_000_000.0
# Cuantil de winsorizacion del volumen por vela (sobre las velas observadas
# del ticker, sin subasta). Operaciones en bloque aisladas (ej. una vela de
# 25 M de acciones de FALABELLA el 2026-08-12) no son flujo de ordenes de
# tamano medio y dominarian lambda. 1.0 desactiva la winsorizacion.
DEFAULT_VOLUME_WINSOR_Q = 0.99
DEFAULT_SEED = 42
N_SIM_VALIDATION = 5000
RHO_CLIP = (0.01, 0.99)
MIN_PAIRS = 10

_DATE_SNAPSHOT_RE = re.compile(r"^clean_5m_(\d{4}-\d{2}-\d{2})$")


# ---------------------------------------------------------------------------
# 1) Carga de datos limpios
# ---------------------------------------------------------------------------

def normalize_ticker(ticker: str) -> str:
    """'falabella.sn' -> 'FALABELLA'. Acepta el nombre con o sin '.SN'."""
    name = ticker.strip().upper()
    if name.endswith(".SN"):
        name = name[: -len(".SN")]
    return name


def resolve_snapshot_dir(data_dir: "str | Path" = DEFAULT_DATA_DIR,
                         snapshot: Optional[str] = None) -> Path:
    """Devuelve `<data_dir>/clean_5m_<snapshot>`. Si `snapshot` es None,
    usa el snapshot fechado (YYYY-MM-DD) mas reciente; carpetas no fechadas
    como `clean_5m_demo` solo se usan si se piden explicitamente.
    """
    data_dir = Path(data_dir)
    if snapshot is not None:
        path = data_dir / f"clean_5m_{snapshot}"
        if not path.is_dir():
            raise FileNotFoundError(
                f"No existe el snapshot '{path}'. Genera los datos con "
                "src/data/clean_ohlcv.py (ver docs/evidencia_pipeline_datos_BF.md)."
            )
        return path
    dated = sorted(
        p for p in data_dir.glob("clean_5m_*") if p.is_dir() and _DATE_SNAPSHOT_RE.match(p.name)
    )
    if not dated:
        raise FileNotFoundError(
            f"No hay snapshots 'clean_5m_<YYYY-MM-DD>' en '{data_dir}'. Genera los "
            "datos con src/data/clean_ohlcv.py (ver docs/evidencia_pipeline_datos_BF.md)."
        )
    return dated[-1]


def snapshot_tag(snapshot_dir: Path) -> str:
    return snapshot_dir.name[len("clean_5m_"):]


def list_snapshot_tickers(snapshot_dir: Path) -> List[str]:
    """Tickers disponibles en un snapshot (sin '.SN' ni '_clean')."""
    names = set()
    for path in snapshot_dir.glob("*.parquet"):
        if path.stem.startswith("_"):
            continue
        names.add(normalize_ticker(path.stem.replace("_clean", "")))
    return sorted(names)


def assign_tramo(ts) -> Optional[str]:
    """Tramo del Ejecutor para un timestamp. Los timestamps tz-aware se
    convierten a America/Santiago; los naive se asumen ya en esa hora.
    Devuelve None fuera de 09:30-16:00.
    """
    ts = pd.Timestamp(ts)
    if ts.tzinfo is not None:
        ts = ts.tz_convert(SANTIAGO_TZ)
    t = ts.time()
    for i, (name, start, end) in enumerate(TRAMOS):
        start_t = time.fromisoformat(start)
        end_t = time.fromisoformat(end)
        is_last = i == len(TRAMOS) - 1
        if start_t <= t < end_t or (is_last and t == end_t):
            return name
    return None


def assign_tramos(timestamps: pd.Series) -> pd.Series:
    """Version vectorizada de `assign_tramo` (NaN fuera de la sesion)."""
    ts = pd.to_datetime(timestamps)
    if ts.dt.tz is not None:
        ts = ts.dt.tz_convert(SANTIAGO_TZ)
    minutes = ts.dt.hour * 60 + ts.dt.minute + ts.dt.second / 60.0
    out = pd.Series(np.nan, index=timestamps.index, dtype=object)
    for i, (name, start, end) in enumerate(TRAMOS):
        s = int(start[:2]) * 60 + int(start[3:])
        e = int(end[:2]) * 60 + int(end[3:])
        mask = (minutes >= s) & ((minutes < e) | ((i == len(TRAMOS) - 1) & (minutes == e)))
        out[mask] = name
    return out


def _add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega tramo, dia, signo del volumen (close-open con tick rule de
    respaldo), retornos log validos y rango HL relativo, junto con sus
    rezagos. Un retorno/rezago solo es valido si ambas velas son observadas,
    del mismo dia y (para rezagos) del mismo tramo.
    """
    df = df.sort_values("ts").reset_index(drop=True)
    df["tramo"] = assign_tramos(df["ts"])
    df["day"] = df["ts"].dt.date
    df["is_auction"] = df["ts"].dt.strftime("%H:%M") == CLOSING_AUCTION_BAR

    by_day = df.groupby("day", sort=False)
    prev_close = by_day["close"].shift(1)
    prev_obs = ~by_day["is_imputed"].shift(1, fill_value=True).astype(bool)
    prev_tramo = by_day["tramo"].shift(1)
    obs = ~df["is_imputed"]

    body = np.sign(df["close"] - df["open"])
    tick = np.sign(df["close"] - prev_close).fillna(0.0)
    df["trade_sign"] = np.where(body != 0, body, tick)

    ret = np.log(df["close"] / prev_close)
    df["ret"] = ret.where(obs & prev_obs)

    mid = (df["high"] + df["low"]) / 2.0
    df["hl_rel"] = ((df["high"] - df["low"]) / mid).where(obs)

    same_tramo = prev_tramo == df["tramo"]
    by_day = df.groupby("day", sort=False)
    df["ret_prev"] = by_day["ret"].shift(1).where(same_tramo)
    df["hl_rel_prev"] = by_day["hl_rel"].shift(1).where(same_tramo)
    return df


def load_clean_data(ticker: str, data_dir: "str | Path" = DEFAULT_DATA_DIR,
                    snapshot: Optional[str] = None, use_raw: bool = True) -> pd.DataFrame:
    """Carga el parquet limpio de `ticker` (con o sin '.SN') del snapshot
    pedido (o del mas reciente) y agrega columnas derivadas.

    Con `use_raw=True` las columnas open/high/low/close/volume del resultado
    son las *_raw del parquet (sin normalizar); las normalizadas se
    descartan. Tambien acepta el formato del demo sintetico de PS
    (`<TICKER>[.SN]_clean.parquet`, sin *_raw ni is_imputed).

    Columnas agregadas: ts (tz America/Santiago), tramo, day, is_auction,
    trade_sign, ret, ret_prev, hl_rel, hl_rel_prev. `ret` es NaN cuando la
    vela o su antecesora esta imputada o cambia el dia.
    """
    snapshot_dir = resolve_snapshot_dir(data_dir, snapshot)
    name = normalize_ticker(ticker)
    candidates = [
        snapshot_dir / f"{name}.parquet",
        snapshot_dir / f"{name}_clean.parquet",
        snapshot_dir / f"{name}.SN_clean.parquet",
    ]
    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        raise FileNotFoundError(
            f"No se encontro '{name}' en '{snapshot_dir}' (se buscaron: "
            f"{[p.name for p in candidates]})."
        )
    df = pd.read_parquet(path)

    base_cols = ["open", "high", "low", "close", "volume"]
    if use_raw and all(f"{c}_raw" in df.columns for c in base_cols):
        df = df.drop(columns=base_cols).rename(columns={f"{c}_raw": c for c in base_cols})

    missing = {"open", "high", "low", "close", "volume"} - set(df.columns)
    if missing:
        raise ValueError(f"'{path}' no tiene las columnas {sorted(missing)}.")

    ts_col = "datetime_santiago" if "datetime_santiago" in df.columns else "timestamp"
    ts = pd.to_datetime(df[ts_col])
    ts = ts.dt.tz_convert(SANTIAGO_TZ) if ts.dt.tz is not None else ts.dt.tz_localize(SANTIAGO_TZ)
    df = df.copy()
    df["ts"] = ts
    if "is_imputed" not in df.columns:
        df["is_imputed"] = False
    df["is_imputed"] = df["is_imputed"].astype(bool)
    df.attrs["source_file"] = str(path)
    return _add_derived_columns(df)


def read_cleaning_report(snapshot_dir: Path) -> Dict:
    path = snapshot_dir / "cleaning_report.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# 2) Extraccion de features del LOB (aproximadas desde OHLC, sin nivel 2 real)
# ---------------------------------------------------------------------------

def extract_lob_features(df: pd.DataFrame, window: int = 6) -> Dict[str, float]:
    """Features resumen (API original de PS): spread (proxy high-low, en
    unidades de precio), volatilidad (rolling std de retornos), skewness y
    kurtosis de los retornos.

    NOTA: `spread` queda en CLP, que no es comparable con los eventos
    normalizados de `PoissonLOBModel`; para la calibracion por tramo se usa
    `extract_tramo_features`, que entrega medidas relativas.
    """
    spread = float((df["high"] - df["low"]).mean())
    ret = df["ret"].dropna()
    volatility = float(df["ret"].rolling(window=window).std().mean())
    features = {
        "spread": spread,
        "volatility": volatility,
        "skewness": float(skew(ret)) if len(ret) > 2 else 0.0,
        "kurtosis": float(kurtosis(ret)) if len(ret) > 2 else 0.0,
    }
    return features


def extract_tramo_features(returns: np.ndarray) -> Dict[str, float]:
    """Features de retornos en las mismas unidades que simula
    `PoissonLOBModel.likelihood`: `spread` = E|r| (la likelihood lo compara
    con la media del valor absoluto de los eventos), `volatility` = std(r).
    """
    r = np.asarray(returns, dtype=float)
    r = r[~np.isnan(r)]
    return {
        "spread": float(np.mean(np.abs(r))),
        "volatility": float(np.std(r)),
        "skewness": float(skew(r)) if len(r) > 2 else 0.0,
        "kurtosis": float(kurtosis(r)) if len(r) > 2 else 0.0,
    }


# ---------------------------------------------------------------------------
# 3) Modelo Poisson del LOB
# ---------------------------------------------------------------------------

class PoissonLOBModel:
    """Modelo simplificado de llegadas de ordenes al Order Book:
    - lambda_plus: tasa de llegada de ordenes de compra (eventos/paso).
    - lambda_minus: tasa de llegada de ordenes de venta (eventos/paso).
    - theta: tasa de cancelacion de ordenes (eventos/paso).

    Cada paso k produce un impacto (N+_k - N-_k) / (1 + C_k), con
    N+/- ~ Poisson(lambda+/-) y C_k ~ Poisson(theta): las cancelaciones
    amortiguan el impacto de la orden neta. Un "evento" agrega
    `steps_per_event` pasos (10 para una vela de 5 min con pasos de 30 s).
    """

    def __init__(self, lambda_plus: float = 0.5, lambda_minus: float = 0.5, theta: float = 0.3):
        self.lambda_plus = float(lambda_plus)
        self.lambda_minus = float(lambda_minus)
        self.theta = float(theta)

    def generate_events(self, n_events: int = 1000, rng: Optional[np.random.Generator] = None,
                        steps_per_event: int = 1,
                        target_std: Optional[float] = 0.01,
                        center: bool = False) -> np.ndarray:
        """Simula `n_events` incrementos de precio.

        Con los valores por defecto (`steps_per_event=1`, `target_std=0.01`)
        reproduce exactamente el comportamiento original de PS. Si
        `target_std` es None, devuelve el impacto en ordenes netas sin
        reescalar; si no, reescala para que std(eventos) = target_std (el
        impacto por orden neta queda fijado por momentos). `center=True`
        resta la media muestral (elimina la deriva 10*(lambda+ - lambda-)
        por vela que este modelo reducido asocia a cualquier desbalance).
        """
        rng = rng if rng is not None else np.random.default_rng()
        total_rate = self.lambda_plus + self.lambda_minus
        if total_rate <= 0:
            return np.zeros(n_events)

        shape = (n_events, int(steps_per_event))
        n_buy_arrivals = rng.poisson(lam=self.lambda_plus, size=shape)
        n_sell_arrivals = rng.poisson(lam=self.lambda_minus, size=shape)
        n_cancel = rng.poisson(lam=self.theta, size=shape)

        raw_impact = (n_buy_arrivals - n_sell_arrivals).astype(float)
        damping = 1.0 / (1.0 + n_cancel)
        events = (raw_impact * damping).sum(axis=1)
        if center:
            events = events - events.mean()
        if target_std is not None:
            std = events.std()
            if std > 0:
                events = events / std * target_std
        return events

    def likelihood(self, obs_spread: float, obs_skew: float, obs_vol: float,
                   n_events: int = 2000, rng: Optional[np.random.Generator] = None,
                   steps_per_event: int = 1, target_std: Optional[float] = 0.01,
                   center: bool = False) -> float:
        """Log-verosimilitud aproximada (distancia gaussiana entre
        estadisticos simulados y observados). Mayor es mejor."""
        events = self.generate_events(n_events=n_events, rng=rng, steps_per_event=steps_per_event,
                                      target_std=target_std, center=center)
        sim_vol = float(np.std(events)) if len(events) else 0.0
        sim_spread = float(np.mean(np.abs(events))) if len(events) else 0.0
        sim_skew = float(skew(events)) if len(events) > 2 and np.std(events) > 0 else 0.0

        eps = 1e-8
        dist = (
            ((sim_vol - obs_vol) / (abs(obs_vol) + eps)) ** 2
            + ((sim_spread - obs_spread) / (abs(obs_spread) + eps)) ** 2
            + ((sim_skew - obs_skew) / (abs(obs_skew) + 1.0)) ** 2
        )
        return -dist

    def to_dict(self) -> Dict[str, float]:
        return {"lambda_plus": self.lambda_plus, "lambda_minus": self.lambda_minus, "theta": self.theta}


# ---------------------------------------------------------------------------
# 4) Calibracion
# ---------------------------------------------------------------------------

def calibrate_poisson_params(
    features_dict: Dict[str, float],
    x0: Tuple[float, float, float] = (0.5, 0.5, 0.3),
    seed: int = 42,
    bounds: Optional[Sequence[Tuple[float, float]]] = None,
    steps_per_event: int = 1,
    target_std: Optional[float] = 0.01,
    center: bool = False,
) -> Dict[str, float]:
    """MLE-proxy de PS: minimiza la distancia entre estadisticos simulados
    por `PoissonLOBModel` y los de `features_dict` con L-BFGS-B.

    En la calibracion por tramo este metodo es ALTERNATIVO: arranca desde
    las estimaciones empiricas directas (x0) y solo se adopta si mejora el
    estadistico KS (ver `calibrate_tramo`). Motivo: una vez fijada la escala
    por momentos (`target_std` = volatilidad observada), la funcion objetivo
    solo depende de la forma de la distribucion simulada, que es casi
    invariante a escalar (lambda+, lambda-) conjuntamente; los niveles de
    lambda no quedan identificados por este objetivo y el optimizador puede
    desplazarlos sin respaldo en el volumen observado. La estimacion directa
    desde volumen si identifica el nivel (dado avg_order_size).

    `bounds` por defecto: [(1e-4, 10), (1e-4, 10), (1e-4, 1)] (original).
    """
    obs_spread = features_dict["spread"]
    obs_skew = features_dict["skewness"]
    obs_vol = features_dict["volatility"]

    def neg_log_likelihood(params):
        lp, lm, th = params
        model = PoissonLOBModel(lambda_plus=lp, lambda_minus=lm, theta=th)
        # "Common random numbers": misma semilla en cada evaluacion para que
        # las diferencias finitas de L-BFGS-B no queden dominadas por ruido.
        rng = np.random.default_rng(seed)
        return -model.likelihood(obs_spread, obs_skew, obs_vol, n_events=4000, rng=rng,
                                 steps_per_event=steps_per_event, target_std=target_std,
                                 center=center)

    if bounds is None:
        bounds = [(1e-4, 10.0), (1e-4, 10.0), (1e-4, 1.0)]
    x0_arr = np.clip(np.array(x0, dtype=float), [b[0] for b in bounds], [b[1] for b in bounds])
    # eps=1e-2: con conteos Poisson discretos, el paso por defecto (~1.5e-8)
    # no cambia los estadisticos simulados (gradiente numerico ~0).
    result = minimize(
        neg_log_likelihood,
        x0=x0_arr,
        method="L-BFGS-B",
        bounds=bounds,
        options={"eps": 1e-2, "maxiter": 100},
    )

    return {
        "lambda_plus": float(result.x[0]),
        "lambda_minus": float(result.x[1]),
        "theta": float(result.x[2]),
        "optimizer_success": bool(result.success),
        "optimizer_message": str(result.message),
        "neg_log_likelihood": float(result.fun),
    }


def estimate_order_rates(df_tramo: pd.DataFrame, avg_order_size: float) -> Dict[str, float]:
    """lambda+/- en ordenes por paso de 30 s, desde el volumen de las velas
    observadas del tramo (ver docstring del modulo)."""
    obs = df_tramo[~df_tramo["is_imputed"]]
    n_obs = int(len(obs))
    vol_col = "volume_w" if "volume_w" in obs.columns else "volume"
    vol = obs[vol_col].to_numpy(dtype=float)
    sign = obs["trade_sign"].to_numpy(dtype=float)
    buy = np.where(sign > 0, vol, np.where(sign == 0, 0.5 * vol, 0.0)).sum()
    sell = np.where(sign < 0, vol, np.where(sign == 0, 0.5 * vol, 0.0)).sum()
    steps = n_obs * STEPS_PER_BAR
    if steps == 0:
        return {"lambda_plus": float("nan"), "lambda_minus": float("nan"), "n_obs": 0,
                "buy_volume": 0.0, "sell_volume": 0.0, "share_tick_rule": float("nan"),
                "n_bars_winsorized": 0}
    body_zero = (obs["close"] == obs["open"]).to_numpy()
    n_winsor = int((obs["volume"] > obs[vol_col]).sum())
    return {
        "n_bars_winsorized": n_winsor,
        "lambda_plus": float(buy / steps / avg_order_size),
        "lambda_minus": float(sell / steps / avg_order_size),
        "n_obs": n_obs,
        "buy_volume": float(buy),
        "sell_volume": float(sell),
        "share_tick_rule": float(body_zero.mean()),
    }


def estimate_theta(df_tramo: pd.DataFrame) -> Dict[str, float]:
    """theta = -ln(rho)/10 con rho = autocorrelacion de orden 1 del rango HL
    relativo entre velas observadas consecutivas del mismo tramo y dia."""
    pairs = df_tramo[["hl_rel", "hl_rel_prev"]].dropna()
    n_pairs = int(len(pairs))
    if n_pairs < MIN_PAIRS or pairs["hl_rel"].std() == 0 or pairs["hl_rel_prev"].std() == 0:
        return {"theta": float("nan"), "hl_ar1": float("nan"), "hl_ar1_clipped": False,
                "n_pairs_hl": n_pairs}
    rho = float(np.corrcoef(pairs["hl_rel"], pairs["hl_rel_prev"])[0, 1])
    rho_c = float(np.clip(rho, *RHO_CLIP))
    return {
        "theta": float(-np.log(rho_c) / STEPS_PER_BAR),
        "hl_ar1": rho,
        "hl_ar1_clipped": bool(rho_c != rho),
        "n_pairs_hl": n_pairs,
    }


def estimate_spread_proxies(df_tramo: pd.DataFrame) -> Dict[str, float]:
    """Roll (1984) relativo y rango HL relativo medio, ambos en bps. Roll
    queda NaN si la autocovarianza de retornos no es negativa."""
    pairs = df_tramo[["ret", "ret_prev"]].dropna()
    roll = float("nan")
    cov = float("nan")
    if len(pairs) >= MIN_PAIRS:
        cov = float(np.cov(pairs["ret"], pairs["ret_prev"])[0, 1])
        if cov < 0:
            roll = 2.0 * np.sqrt(-cov) * 1e4
    return {
        "spread_roll_bps": float(roll),
        "roll_autocov": cov,
        "hl_range_bps": float(df_tramo["hl_rel"].mean() * 1e4),
    }


def _tramo_seed(seed: int, ticker: str, tramo: str) -> int:
    ss = np.random.SeedSequence([seed, zlib.crc32(ticker.encode("utf-8")), TRAMO_NAMES.index(tramo)])
    return int(ss.generate_state(1)[0])


def _observed_returns(df_tramo: pd.DataFrame) -> np.ndarray:
    return df_tramo["ret"].dropna().to_numpy(dtype=float)


def calibrate_tramo(df_tramo: pd.DataFrame, ticker: str, tramo: str,
                    avg_order_size: float, seed: int = DEFAULT_SEED,
                    run_mle: bool = True) -> Dict:
    """Calibra (lambda+, lambda-, theta) para un ticker x tramo y valida con KS.

    Metodo principal: estimacion empirica directa (`estimate_order_rates` +
    `estimate_theta`). Metodo alternativo: `calibrate_poisson_params` desde
    x0 = estimacion directa; se adopta solo si reduce el estadistico KS,
    el optimizador converge y ningun parametro queda en el limite de
    `bounds` (una solucion en el limite indica que el objetivo no identifica
    ese parametro, no que el ajuste sea mejor).
    """
    tramo_seed = _tramo_seed(seed, ticker, tramo)
    rates = estimate_order_rates(df_tramo, avg_order_size)
    th = estimate_theta(df_tramo)
    spreads = estimate_spread_proxies(df_tramo)
    returns = _observed_returns(df_tramo)
    n_bars = int(len(df_tramo))

    direct = {"lambda_plus": rates["lambda_plus"], "lambda_minus": rates["lambda_minus"],
              "theta": th["theta"]}
    out = {
        **direct,
        "n_obs": rates["n_obs"],
        "n_bars_total": n_bars,
        "imputed_share": float(df_tramo["is_imputed"].mean()) if n_bars else float("nan"),
        "n_returns": int(len(returns)),
        "ks_stat": float("nan"),
        "p_value": float("nan"),
        "method": "empirico_directo",
        "avg_order_size": float(avg_order_size),
        "buy_volume": rates["buy_volume"],
        "sell_volume": rates["sell_volume"],
        "share_tick_rule": rates["share_tick_rule"],
        "n_bars_winsorized": rates["n_bars_winsorized"],
        "hl_ar1": th["hl_ar1"],
        "hl_ar1_clipped": th["hl_ar1_clipped"],
        **spreads,
        "obs_return_std": float(np.std(returns)) if len(returns) else float("nan"),
        "obs_return_mean": float(np.mean(returns)) if len(returns) else float("nan"),
    }
    if not all(np.isfinite(v) and v > 0 for v in direct.values()) or len(returns) < MIN_PAIRS:
        out["method"] = "insuficiente"
        return out

    target_std = float(np.std(returns))
    val = validate_calibration(direct, returns, n_events=N_SIM_VALIDATION, seed=tramo_seed,
                               steps_per_event=STEPS_PER_BAR, target_std=target_std, center=True)
    out["ks_stat"] = val["ks_statistic"]
    out["p_value"] = val["p_value"]
    out["sim_drift_sd"] = val["sim_drift_sd"]
    out["directo"] = {**direct, "ks_stat": val["ks_statistic"], "p_value": val["p_value"]}

    if run_mle:
        feats = extract_tramo_features(returns)
        bounds = [(v / 20.0, v * 20.0) for v in (direct["lambda_plus"], direct["lambda_minus"])]
        bounds.append((1e-3, 1.0))
        mle = calibrate_poisson_params(
            feats, x0=(direct["lambda_plus"], direct["lambda_minus"], direct["theta"]),
            seed=tramo_seed, bounds=bounds, steps_per_event=STEPS_PER_BAR, target_std=target_std,
            center=True,
        )
        mle_val = validate_calibration(mle, returns, n_events=N_SIM_VALIDATION, seed=tramo_seed,
                                       steps_per_event=STEPS_PER_BAR, target_std=target_std,
                                       center=True)
        at_bound = any(
            np.isclose(mle[k], lo, rtol=1e-3) or np.isclose(mle[k], hi, rtol=1e-3)
            for k, (lo, hi) in zip(("lambda_plus", "lambda_minus", "theta"), bounds)
        )
        improves = bool(mle_val["ks_statistic"] < val["ks_statistic"])
        adopt = improves and mle["optimizer_success"] and not at_bound
        out["mle_proxy"] = {
            "lambda_plus": mle["lambda_plus"],
            "lambda_minus": mle["lambda_minus"],
            "theta": mle["theta"],
            "ks_stat": mle_val["ks_statistic"],
            "p_value": mle_val["p_value"],
            "optimizer_success": mle["optimizer_success"],
            "en_limite": bool(at_bound),
            "mejora_ks": improves,
            "adoptado": adopt,
        }
        if adopt:
            out.update({k: mle[k] for k in ("lambda_plus", "lambda_minus", "theta")})
            out["ks_stat"] = mle_val["ks_statistic"]
            out["p_value"] = mle_val["p_value"]
            out["method"] = "mle_proxy"
            out["sim_drift_sd"] = mle_val["sim_drift_sd"]
    return out


def check_stylized_facts(tramo_results: Dict[str, Dict],
                         lambda_total_raw: Optional[Dict[str, float]] = None) -> Dict:
    """Hecho estilizado esperado: menor intensidad de ordenes y spread-proxy
    mayor en media_jornada que en apertura y cierre. Se evalua sobre las
    estimaciones empiricas directas (es un hecho de los datos, no del
    modelo), sin forzar el resultado. None si algun valor no es finito.
    `lambda_total_raw` (volumen sin winsorizar) se evalua como sensibilidad."""
    def cmp(key_fn, lower: bool) -> Optional[bool]:
        vals = {t: key_fn(dict(tramo_results[t], _tramo=t)) for t in TRAMO_NAMES}
        if not all(v is not None and np.isfinite(v) for v in vals.values()):
            return None
        m = vals["media_jornada"]
        if lower:
            return bool(m < vals["apertura"] and m < vals["cierre"])
        return bool(m > vals["apertura"] and m > vals["cierre"])

    def lam_total(r):
        if r["n_obs"] == 0:
            return None
        return (r["buy_volume"] + r["sell_volume"]) / (r["n_obs"] * STEPS_PER_BAR) / r["avg_order_size"]

    out = {
        "lambda_total_menor_en_media": cmp(lam_total, lower=True),
        "spread_roll_mayor_en_media": cmp(lambda r: r["spread_roll_bps"], lower=False),
        "spread_hl_mayor_en_media": cmp(lambda r: r["hl_range_bps"], lower=False),
        "lambda_total_directo": {t: lam_total(tramo_results[t]) for t in TRAMO_NAMES},
    }
    if lambda_total_raw is not None:
        out["lambda_total_sin_winsorizar"] = dict(lambda_total_raw)
        out["lambda_total_menor_en_media_sin_winsorizar"] = cmp(
            lambda r: lambda_total_raw[r["_tramo"]], lower=True)
    return out


def calibrate_ticker(ticker: str, data_dir: "str | Path" = DEFAULT_DATA_DIR,
                     snapshot: Optional[str] = None, avg_order_size: Optional[float] = None,
                     order_notional_clp: float = DEFAULT_ORDER_NOTIONAL_CLP,
                     exclude_closing_auction: bool = True, seed: int = DEFAULT_SEED,
                     run_mle: bool = True,
                     volume_winsor_q: float = DEFAULT_VOLUME_WINSOR_Q) -> Dict:
    """Calibra los 3 tramos de un ticker. Devuelve
    {'ticker', 'avg_order_size', 'tramos': {tramo: dict}, 'stylized_facts',
    'returns': {tramo: np.ndarray}} (returns solo para graficar)."""
    name = normalize_ticker(ticker)
    df = load_clean_data(name, data_dir=data_dir, snapshot=snapshot)
    if avg_order_size is None:
        median_price = float(df.loc[~df["is_imputed"], "close"].median())
        avg_order_size = max(1.0, round(order_notional_clp / median_price))
    if exclude_closing_auction:
        df = df[~df["is_auction"]]
    df = df.copy()
    cap = float(df.loc[~df["is_imputed"], "volume"].quantile(volume_winsor_q))
    df["volume_w"] = df["volume"].clip(upper=cap)

    tramos = {}
    returns = {}
    lambda_total_raw = {}
    for tramo in TRAMO_NAMES:
        df_t = df[df["tramo"] == tramo]
        tramos[tramo] = calibrate_tramo(df_t, name, tramo, avg_order_size, seed=seed, run_mle=run_mle)
        returns[tramo] = _observed_returns(df_t)
        raw = estimate_order_rates(df_t.drop(columns="volume_w"), avg_order_size)
        lambda_total_raw[tramo] = raw["lambda_plus"] + raw["lambda_minus"]
    return {
        "ticker": name,
        "avg_order_size": float(avg_order_size),
        "volume_cap": cap,
        "source_file": df.attrs.get("source_file"),
        "tramos": tramos,
        "stylized_facts": check_stylized_facts(tramos, lambda_total_raw),
        "returns": returns,
    }


# ---------------------------------------------------------------------------
# 5) Validacion estadistica (KS test simulado vs observado)
# ---------------------------------------------------------------------------

def validate_calibration(
    calibrated: Dict[str, float],
    observed_returns: np.ndarray,
    n_events: int = 2000,
    seed: int = 123,
    alpha: float = 0.05,
    steps_per_event: int = 1,
    target_std: Optional[float] = 0.01,
    center: bool = False,
) -> Dict[str, float]:
    """KS de 2 muestras (`scipy.stats.ks_2samp`) entre eventos simulados por
    el modelo calibrado y retornos observados. `valid = p_value > alpha`.
    Los defaults reproducen el comportamiento original de PS; en la
    calibracion por tramo se usa steps_per_event=10, target_std=std
    observada y center=True (ambas muestras centradas: el KS evalua forma).
    `sim_drift_sd` reporta la deriva que tendria la simulacion sin centrar,
    en desviaciones estandar.
    """
    rng = np.random.default_rng(seed)
    model = PoissonLOBModel(
        lambda_plus=calibrated["lambda_plus"],
        lambda_minus=calibrated["lambda_minus"],
        theta=calibrated["theta"],
    )
    simulated = model.generate_events(n_events=n_events, rng=rng,
                                      steps_per_event=steps_per_event, target_std=target_std)
    observed = np.asarray(observed_returns)
    observed = observed[~np.isnan(observed)]
    sim_std = simulated.std()
    sim_drift_sd = float(simulated.mean() / sim_std) if sim_std > 0 else 0.0
    if center:
        simulated = simulated - simulated.mean()
        if len(observed):
            observed = observed - observed.mean()

    if len(observed) < 2 or len(simulated) < 2:
        return {
            "ks_statistic": float("nan"),
            "p_value": float("nan"),
            "valid": False,
            "n_observed": int(len(observed)),
            "n_simulated": int(len(simulated)),
            "alpha": alpha,
            "sim_drift_sd": sim_drift_sd,
        }

    ks_stat, p_value = ks_2samp(simulated, observed)
    return {
        "ks_statistic": float(ks_stat),
        "p_value": float(p_value),
        "valid": bool(p_value > alpha),
        "n_observed": int(len(observed)),
        "n_simulated": int(len(simulated)),
        "alpha": alpha,
        "sim_drift_sd": sim_drift_sd,
    }


# ---------------------------------------------------------------------------
# 6) Persistencia y visualizacion
# ---------------------------------------------------------------------------

def save_calibration(
    calibrated: Dict[str, float],
    validation: Dict[str, float],
    output_file: "str | Path" = DEFAULT_OUTPUT_JSON,
    metadata: Optional[Dict] = None,
) -> Path:
    """Guarda un unico set de parametros + validacion en JSON (API original,
    usada por el demo)."""
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "calibrated_params": calibrated,
        "validation": validation,
        "metadata": metadata or {},
    }
    with open(output_file, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
    return output_file


def _json_safe(obj):
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, (np.floating, float)):
        return None if not np.isfinite(obj) else float(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    return obj


def build_metadata(snapshot_dir: Path, avg_order_size: Optional[float], order_notional_clp: float,
                   exclude_closing_auction: bool, seed: int,
                   volume_winsor_q: float = DEFAULT_VOLUME_WINSOR_Q) -> Dict:
    return {
        "tarea": "2.1.3 - Calibracion de parametros del modelo de Poisson por tramo horario",
        "autor": "Benjamin Farias (BF); API y modelo base de Paolo Sepulveda (PS)",
        "fecha_generacion": datetime.now(timezone.utc).isoformat(),
        "fuente": "yfinance, velas OHLCV de 5 min, 30 tickers IPSA (.SN)",
        "snapshot": snapshot_tag(snapshot_dir),
        "input_dir": (snapshot_dir.resolve().relative_to(_REPO_ROOT).as_posix()
                      if _REPO_ROOT in snapshot_dir.resolve().parents else str(snapshot_dir)),
        "tramos": {name: [start, end] for name, start, end in TRAMOS},
        "timezone": SANTIAGO_TZ,
        "unidades": {
            "lambda_plus": "ordenes de compra por paso de 30 s",
            "lambda_minus": "ordenes de venta por paso de 30 s",
            "theta": "tasa de cancelacion por paso de 30 s",
            "ks_stat": "KS 2 muestras, retornos log de 5 min simulados vs observados",
            "spread_roll_bps": "Roll (1984), relativo, puntos base",
            "hl_range_bps": "rango high-low / mid medio, puntos base",
        },
        "supuestos": [
            "Se usan precios y volumen sin normalizar (*_raw de clean_5m); velas con is_imputed=True excluidas.",
            "Signo del volumen: close-open; si es 0, tick rule contra el ultimo close del dia; si tambien es 0, 50/50.",
            (f"avg_order_size = {avg_order_size} acciones para todos los tickers." if avg_order_size else
             f"avg_order_size = round({order_notional_clp:.0f} CLP / mediana(close_raw)) por ticker (nocional fijo por orden)."),
            (f"Volumen por vela winsorizado en el cuantil {volume_winsor_q} de las velas observadas del ticker "
             "(operaciones en bloque aisladas no son flujo de ordenes de tamano medio)."),
            "lambda condicional a velas con transaccion (las velas sin transaccion no entran al denominador).",
            "theta = -ln(rho_HL)/10, rho_HL = autocorrelacion AR(1) del rango HL relativo entre velas consecutivas observadas del mismo tramo; rho recortado a [0.01, 0.99].",
            ("Vela 15:55 (subasta de cierre fusionada en 1.2.1) excluida de todas las estimaciones."
             if exclude_closing_auction else "Vela 15:55 (subasta de cierre) incluida."),
            ("Validacion KS: el impacto por orden neta se fija por momentos (std simulada = std observada) y ambas muestras se centran; "
             "el KS evalua la forma de la distribucion. Sin centrar, el modelo reducido convierte el desbalance lambda+ - lambda- en una "
             "deriva por vela (campo sim_drift_sd) que los retornos observados no presentan."),
            "Sin Nivel 2: spread, profundidad y cancelaciones se aproximan desde velas de 5 min.",
        ],
        "avg_order_size_global": avg_order_size,
        "order_notional_clp": None if avg_order_size else order_notional_clp,
        "exclude_closing_auction": exclude_closing_auction,
        "volume_winsor_q": volume_winsor_q,
        "seed": seed,
        "n_sim_validacion": N_SIM_VALIDATION,
        "python": platform.python_version(),
        "referencias": [
            "Cont, R., Stoikov, S. & Talreja, R. (2010). A stochastic model for order book dynamics. Operations Research, 58(3).",
            "Roll, R. (1984). A simple implicit measure of the effective bid-ask spread. Journal of Finance, 39(4).",
        ],
    }


def save_calibration_by_tramo(results: Sequence[Dict], metadata: Dict, cleaning_report: Dict,
                              output_file: "str | Path") -> Path:
    """Escribe {metadata, params[ticker][tramo], tickers_info[ticker],
    stylized_facts[ticker]}."""
    per_ticker = cleaning_report.get("per_ticker", {})
    params: Dict[str, Dict] = {}
    info: Dict[str, Dict] = {}
    facts: Dict[str, Dict] = {}
    for res in results:
        t = res["ticker"]
        params[t] = res["tramos"]
        stats = per_ticker.get(t, {})
        tier = stats.get("tier")
        info[t] = {
            "avg_order_size": res["avg_order_size"],
            "volume_cap": res["volume_cap"],
            "tier": tier,
            "coverage_pre_fill_pct": stats.get("coverage_pre_fill_pct"),
            "cobertura_baja": None if tier is None else tier != "A",
        }
        facts[t] = res["stylized_facts"]
    payload = {"metadata": metadata, "params": params, "tickers_info": info, "stylized_facts": facts}
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as fh:
        json.dump(_json_safe(payload), fh, indent=2, ensure_ascii=False)
    return output_file


def plot_tramo_results(result: Dict, snapshot: str, output_file: "str | Path",
                       seed: int = DEFAULT_SEED) -> Path:
    """Figura por tramo para un ticker: fila superior, histogramas de
    retornos observados vs simulados con KS; fila inferior, lambda+/-,
    theta y proxies de spread por tramo."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    c_obs, c_sim = "#2a78d6", "#eb6834"      # slots 1-2 de la paleta categorica
    ink, ink2, grid = "#0b0b0b", "#52514e", "#e4e3df"
    labels = {"apertura": "Apertura\n09:30-11:30", "media_jornada": "Media jornada\n11:30-14:00",
              "cierre": "Cierre\n14:00-16:00"}
    tramos = result["tramos"]

    plt.rcParams.update({"axes.edgecolor": grid, "axes.labelcolor": ink2, "xtick.color": ink2,
                         "ytick.color": ink2, "axes.titlecolor": ink, "font.size": 9})
    fig, axes = plt.subplots(2, 3, figsize=(13, 7.5), facecolor="#fcfcfb")
    for ax in axes.flat:
        ax.set_facecolor("#fcfcfb")
        ax.grid(axis="y", color=grid, linewidth=0.6)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)

    for ax, tramo in zip(axes[0], TRAMO_NAMES):
        r = tramos[tramo]
        obs = result["returns"][tramo] * 1e4
        ax.set_title(labels[tramo].replace("\n", " "), loc="left", fontsize=10)
        if r["method"] == "insuficiente" or len(obs) == 0:
            ax.text(0.5, 0.5, "datos insuficientes", ha="center", transform=ax.transAxes, color=ink2)
            continue
        model = PoissonLOBModel(r["lambda_plus"], r["lambda_minus"], r["theta"])
        sim = model.generate_events(N_SIM_VALIDATION, rng=np.random.default_rng(
            _tramo_seed(seed, result["ticker"], tramo)), steps_per_event=STEPS_PER_BAR,
            target_std=r["obs_return_std"], center=True) * 1e4
        obs = obs - obs.mean()
        lim = np.nanpercentile(np.abs(obs), 99.5)
        bins = np.linspace(-lim, lim, 61)
        ax.hist(obs, bins=bins, density=True, color=c_obs, alpha=0.55, label="Observado",
                edgecolor="#fcfcfb", linewidth=0.4)
        ax.hist(sim, bins=bins, density=True, histtype="step", color=c_sim, linewidth=2,
                label="Simulado (Poisson)")
        ax.set_xlabel("retorno log 5 min centrado (bps)")
        ax.text(0.98, 0.95, f"KS = {r['ks_stat']:.3f}\np = {r['p_value']:.2g}\nn obs = {len(obs)}",
                transform=ax.transAxes, ha="right", va="top", color=ink, fontsize=8.5)
    axes[0][0].set_ylabel("densidad")
    axes[0][0].legend(loc="upper left", frameon=False, fontsize=8)

    x = np.arange(len(TRAMO_NAMES))
    xt = [labels[t] for t in TRAMO_NAMES]
    lp = [tramos[t]["lambda_plus"] for t in TRAMO_NAMES]
    lm = [tramos[t]["lambda_minus"] for t in TRAMO_NAMES]
    ax = axes[1][0]
    b1 = ax.bar(x - 0.19, lp, 0.36, color=c_obs, label="lambda+ (compra)")
    b2 = ax.bar(x + 0.19, lm, 0.36, color=c_sim, label="lambda- (venta)")
    ax.bar_label(b1, fmt="%.2f", fontsize=8, color=ink2, padding=2)
    ax.bar_label(b2, fmt="%.2f", fontsize=8, color=ink2, padding=2)
    ax.set_xticks(x, xt)
    ax.set_title(f"Llegadas por paso de 30 s (orden = {result['avg_order_size']:.0f} acc.)",
                 loc="left", fontsize=10)
    ax.legend(frameon=False, fontsize=8, loc="upper left", ncol=2)

    ax = axes[1][1]
    th = [tramos[t]["theta"] for t in TRAMO_NAMES]
    b = ax.bar(x, th, 0.5, color=c_obs)
    ax.bar_label(b, fmt="%.3f", fontsize=8, color=ink2, padding=2)
    ax.set_xticks(x, xt)
    ax.set_title("theta (cancelacion, proxy persistencia HL)", loc="left", fontsize=10)

    ax = axes[1][2]
    roll = [tramos[t]["spread_roll_bps"] for t in TRAMO_NAMES]
    hl = [tramos[t]["hl_range_bps"] for t in TRAMO_NAMES]
    b1 = ax.bar(x - 0.19, roll, 0.36, color=c_obs, label="Roll (1984)")
    b2 = ax.bar(x + 0.19, hl, 0.36, color=c_sim, label="Rango HL relativo")
    ax.bar_label(b1, fmt="%.1f", fontsize=8, color=ink2, padding=2)
    ax.bar_label(b2, fmt="%.1f", fontsize=8, color=ink2, padding=2)
    ax.set_xticks(x, xt)
    ax.set_ylabel("bps")
    ax.set_title("Proxies de spread", loc="left", fontsize=10)
    ax.legend(frameon=False, fontsize=8, loc="upper right", ncol=2)
    for ax in axes[1]:
        ax.margins(y=0.3)

    fig.suptitle(
        f"{result['ticker']}: calibracion Poisson por tramo horario  |  snapshot {snapshot}, "
        "yfinance 5 min, velas imputadas y subasta de cierre excluidas",
        x=0.01, ha="left", fontsize=11, color=ink,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=130, facecolor=fig.get_facecolor())
    plt.close(fig)
    return output_file


def plot_calibration_results(
    calibrated: Dict[str, float],
    observed_returns: Optional[np.ndarray] = None,
    n_events: int = 2000,
    seed: int = 7,
    output_file: "str | Path" = DEFAULT_OUTPUT_PLOT,
) -> Path:
    """Grafico del demo sintetico original de PS (un unico set de
    parametros). Para datos reales usar `plot_tramo_results`."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rng = np.random.default_rng(seed)
    model = PoissonLOBModel(
        lambda_plus=calibrated["lambda_plus"],
        lambda_minus=calibrated["lambda_minus"],
        theta=calibrated["theta"],
    )
    simulated = model.generate_events(n_events=n_events, rng=rng)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    axes[0].hist(simulated, bins=40, alpha=0.6, label="Simulado (Poisson calibrado)", color="tab:blue")
    if observed_returns is not None:
        obs = np.asarray(observed_returns)
        obs = obs[~np.isnan(obs)]
        if len(obs) > 0:
            axes[0].hist(obs, bins=40, alpha=0.6, label="Observado", color="tab:orange")
    axes[0].set_title("Distribucion de retornos: simulado vs observado")
    axes[0].set_xlabel("retorno (escala arbitraria)")
    axes[0].legend()

    params = ["lambda_plus", "lambda_minus", "theta"]
    values = [calibrated[p] for p in params]
    axes[1].bar(params, values, color=["tab:green", "tab:red", "tab:gray"])
    axes[1].set_title("Parametros calibrados")
    axes[1].set_ylabel("valor")

    fig.suptitle("Calibracion Poisson del LOB (Tarea 2.1.3) -- DATOS SINTETICOS DE DEMO", fontsize=10)
    fig.tight_layout()

    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=120)
    plt.close(fig)
    return output_file


# ---------------------------------------------------------------------------
# 7) Dataset sintetico de demo (SOLO para smoke-test, NO datos reales)
# ---------------------------------------------------------------------------

def generate_synthetic_demo_dataset(
    output_dir: "str | Path" = _REPO_ROOT / "data" / "processed" / "clean_5m_demo",
    tickers=("FALABELLA.SN", "SQM-B.SN", "CHILE.SN"),
    n_rows: int = 200,
    seed: int = 2026,
) -> Dict[str, Path]:
    """Genera un dataset OHLC sintetico minimo (camino aleatorio) para
    probar el pipeline sin datos reales. NO es data de mercado."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    paths = {}
    for i, ticker in enumerate(tickers):
        local_rng = np.random.default_rng(seed + i)
        s0 = 1000.0 + 100.0 * i
        log_returns = local_rng.normal(loc=0.0, scale=0.003, size=n_rows)
        close = s0 * np.exp(np.cumsum(log_returns))
        intraperiod_noise = np.abs(local_rng.normal(loc=0.002, scale=0.001, size=n_rows))
        high = close * (1 + intraperiod_noise)
        low = close * (1 - intraperiod_noise)
        open_ = np.concatenate([[s0], close[:-1]])
        volume = local_rng.integers(1000, 50000, size=n_rows).astype(float)

        timestamps = pd.date_range("2026-09-01 09:30", periods=n_rows, freq="5min")
        df = pd.DataFrame(
            {"timestamp": timestamps, "open": open_, "high": high, "low": low,
             "close": close, "volume": volume}
        )
        out_path = output_dir / f"{ticker}_clean.parquet"
        df.to_parquet(out_path, index=False)
        paths[ticker] = out_path

    (output_dir / "README_SINTETICO.md").write_text(
        "# Dataset SINTETICO de demo (NO datos reales de mercado)\n\n"
        "Generado por `src/envs/calibration_poisson.generate_synthetic_demo_dataset` "
        "(`python -m src.envs.calibration_poisson --demo`) solo como smoke-test. "
        "NO usar como fuente de resultados de la tesis.\n",
        encoding="utf-8",
    )
    return paths


# ---------------------------------------------------------------------------
# 8) Demo / smoke-test end-to-end (sintetico, flag --demo)
# ---------------------------------------------------------------------------

def run_demo(verbose: bool = True) -> Dict[str, Dict]:
    """Pipeline original de PS (un unico set de parametros por ticker) sobre
    el dataset SINTETICO. Smoke-test de ingenieria, NO resultado de tesis.
    Salidas en data/calibration/demo/ (ignorado por git)."""
    demo_dir = _REPO_ROOT / "data" / "processed" / "clean_5m_demo"
    tickers = ("FALABELLA.SN", "SQM-B.SN", "CHILE.SN")

    if not any((demo_dir / f"{t}_clean.parquet").exists() for t in tickers):
        generate_synthetic_demo_dataset(output_dir=demo_dir, tickers=tickers)

    summary = {}
    for ticker in tickers:
        df = load_clean_data(ticker, data_dir=demo_dir.parent, snapshot="demo")
        features = extract_lob_features(df)
        calibrated = calibrate_poisson_params(features)
        validation = validate_calibration(calibrated, df["ret"].values)
        save_calibration(
            calibrated,
            validation,
            output_file=DEMO_OUTPUT_DIR / f"poisson_params_calibrated_{ticker.replace('.', '_')}.json",
            metadata={"ticker": ticker, "data_source": "SINTETICO (demo, NO datos reales de mercado)",
                      "n_rows": int(len(df))},
        )
        summary[ticker] = {"features": features, "calibrated": calibrated, "validation": validation}
        if verbose:
            print(f"[{ticker}] calibrado={calibrated}")
            print(f"[{ticker}] validacion KS={validation}")

    last_ticker = tickers[-1]
    save_calibration(
        summary[last_ticker]["calibrated"],
        summary[last_ticker]["validation"],
        output_file=DEFAULT_OUTPUT_JSON,
        metadata={"ticker": last_ticker, "data_source": "SINTETICO (demo, NO datos reales de mercado)"},
    )
    plot_calibration_results(
        summary[last_ticker]["calibrated"],
        observed_returns=load_clean_data(last_ticker, data_dir=demo_dir.parent, snapshot="demo")["ret"].values,
        output_file=DEFAULT_OUTPUT_PLOT,
    )
    if verbose:
        n_valid = sum(1 for t in summary.values() if t["validation"]["valid"])
        print(f"\n[DEMO SINTETICO] {n_valid}/{len(tickers)} tickers con p-value > 0.05 "
              "(smoke-test, NO resultado de validacion real).")
    return summary


# ---------------------------------------------------------------------------
# 9) CLI
# ---------------------------------------------------------------------------

def run_calibration(tickers: Optional[Sequence[str]] = None, snapshot: Optional[str] = None,
                    data_dir: "str | Path" = DEFAULT_DATA_DIR,
                    avg_order_size: Optional[float] = None,
                    order_notional_clp: float = DEFAULT_ORDER_NOTIONAL_CLP,
                    exclude_closing_auction: bool = True, seed: int = DEFAULT_SEED,
                    output_json: Optional["str | Path"] = None,
                    plot_ticker: Optional[str] = "FALABELLA",
                    plot_dir: "str | Path" = DEFAULT_RESULTS_DIR,
                    run_mle: bool = True,
                    volume_winsor_q: float = DEFAULT_VOLUME_WINSOR_Q,
                    verbose: bool = True) -> Dict:
    """Calibra `tickers` (todos los del snapshot si es None), escribe el
    JSON y, si `plot_ticker` esta entre ellos, su figura por tramo."""
    snapshot_dir = resolve_snapshot_dir(data_dir, snapshot)
    tag = snapshot_tag(snapshot_dir)
    names = [normalize_ticker(t) for t in tickers] if tickers else list_snapshot_tickers(snapshot_dir)
    report = read_cleaning_report(snapshot_dir)

    results = []
    for name in names:
        res = calibrate_ticker(name, data_dir=data_dir, snapshot=tag, avg_order_size=avg_order_size,
                               order_notional_clp=order_notional_clp,
                               exclude_closing_auction=exclude_closing_auction, seed=seed,
                               run_mle=run_mle, volume_winsor_q=volume_winsor_q)
        results.append(res)
        if verbose:
            parts = []
            for tramo in TRAMO_NAMES:
                r = res["tramos"][tramo]
                parts.append(f"{tramo}: l+={r['lambda_plus']:.3f} l-={r['lambda_minus']:.3f} "
                             f"th={r['theta']:.3f} KS={r['ks_stat']:.3f} ({r['method']})")
            print(f"[{name}] orden={res['avg_order_size']:.0f} acc | " + " | ".join(parts))

    output_json = Path(output_json) if output_json else DEFAULT_CALIBRATION_DIR / f"poisson_params_{tag}.json"
    metadata = build_metadata(snapshot_dir, avg_order_size, order_notional_clp,
                              exclude_closing_auction, seed, volume_winsor_q)
    save_calibration_by_tramo(results, metadata, report, output_json)
    if verbose:
        print(f"JSON -> {output_json}")

    plot_path = None
    if plot_ticker:
        target = normalize_ticker(plot_ticker)
        match = next((r for r in results if r["ticker"] == target), None)
        if match is not None:
            plot_path = plot_tramo_results(match, tag, Path(plot_dir) / f"{target}_poisson_por_tramo.png",
                                           seed=seed)
            if verbose:
                print(f"PNG  -> {plot_path}")
    return {"results": results, "json": output_json, "plot": plot_path}


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        description="Calibracion Poisson (lambda+, lambda-, theta) por tramo horario (tarea 2.1.3).")
    parser.add_argument("--snapshot", default=None,
                        help="Fecha del snapshot clean_5m_<fecha>, ej. 2026-08-23. Default: el mas reciente.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--tickers", nargs="+", help="Tickers a calibrar (con o sin .SN).")
    group.add_argument("--all", action="store_true", help="Calibra todos los tickers del snapshot.")
    group.add_argument("--demo", action="store_true",
                       help="Corre el smoke-test SINTETICO original de PS (no usa datos reales).")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--avg-order-size", type=float, default=None,
                        help="Tamano medio de orden en acciones (supuesto). Si se omite, se deriva de --order-notional-clp.")
    parser.add_argument("--order-notional-clp", type=float, default=DEFAULT_ORDER_NOTIONAL_CLP,
                        help="Nocional medio por orden en CLP (default: %(default).0f).")
    parser.add_argument("--include-closing-auction", action="store_true",
                        help="Incluye la vela 15:55 (subasta de cierre) en las estimaciones.")
    parser.add_argument("--volume-winsor-q", type=float, default=DEFAULT_VOLUME_WINSOR_Q,
                        help="Cuantil de winsorizacion del volumen por vela (1.0 = sin winsorizar).")
    parser.add_argument("--no-mle", action="store_true", help="Omite el MLE-proxy alternativo.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--output", type=Path, default=None,
                        help="Ruta del JSON. Default: data/calibration/poisson_params_<snapshot>.json")
    parser.add_argument("--plot-ticker", default="FALABELLA",
                        help="Ticker para results/sprint3/<TICKER>_poisson_por_tramo.png ('' para omitir).")
    args = parser.parse_args(argv)

    if args.demo:
        run_demo()
        return
    if not args.tickers and not args.all:
        parser.error("indica --tickers, --all o --demo")
    run_calibration(
        tickers=None if args.all else args.tickers,
        snapshot=args.snapshot,
        data_dir=args.data_dir,
        avg_order_size=args.avg_order_size,
        order_notional_clp=args.order_notional_clp,
        exclude_closing_auction=not args.include_closing_auction,
        seed=args.seed,
        output_json=args.output,
        plot_ticker=args.plot_ticker or None,
        run_mle=not args.no_mle,
        volume_winsor_q=args.volume_winsor_q,
    )


if __name__ == "__main__":
    main()
