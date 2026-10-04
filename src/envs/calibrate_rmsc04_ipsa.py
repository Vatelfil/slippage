"""Calibracion de `rmsc04` (config de ABIDES-Gym) con parametros reales del
IPSA -- tarea 2.2.4 (Sprint 4), Benjamin Farias (BF).

Bloque A de la tarea (traduccion directa, sin busqueda). La plantilla
original es de Paolo Sepulveda (PS, 29 sept 2026); esta version corrige las
unidades de `fund_vol`, hace configurable la unidad de cuenta y agrega la
evidencia de A4 (razon de varianzas -> `kappa_oracle`) y A5 (curtosis).

Que resuelve este modulo
    - `r_bar`: precio mediano real del ticker en la unidad de cuenta elegida.
    - `fund_vol`: volatilidad del valor fundamental, con la conversion de
      unidades correcta (ver `fund_vol_from_sigma`).
    - `starting_cash`: en la misma unidad de cuenta que `r_bar`.
    - `kappa_oracle`: decidido con el test de razon de varianzas
      (`variance_ratio`, `decide_kappa_oracle`).
    - `megashock_*`: se mantiene el default de rmsc04; la curtosis real por
      tramo (`return_kurtosis`) queda guardada para compararla con la simulada.

Que NO resuelve (queda para la busqueda del bloque B, `scripts/colab/`)
    - `mm_*` (market maker) y `num_noise_agents` / `lambda_a` (actividad):
      ver `CAMPOS_PENDIENTES_2_2_4`.

Unidades (H5 del plan). El oraculo de rmsc04 (`SparseMeanRevertingOracle`)
es un proceso de Ornstein-Uhlenbeck que avanza con

    v ~ Normal(mu + (pv - mu) e^{-kappa d},
               sqrt(fund_vol^2 / (2 kappa) * (1 - e^{-2 kappa d})))

donde `d = ts - pt` es la diferencia de timestamps de ABIDES, que estan en
NANOSEGUNDOS. Con kappa -> 0, Var -> fund_vol^2 * d, de modo que `fund_vol`
esta en (unidades de precio) / sqrt(ns). La plantilla usaba
`sigma_5min * r_bar`, que es un desvio en unidades de precio por vela de
5 min: quedaba sqrt(300e9) ~ 547 723 veces mas grande y el precio explotaba.

Firma de `rmsc04.build_config` y formula del oraculo verificadas contra
jpmorganchase/abides-jpmc-public, rama main, commit f9cbe51 (2023-12-13),
el 2026-10-03.

`build_rmsc04_ipsa_config()` no importa `abides_markets`: corre sin ABIDES.

Uso (en Colab):

    from abides_markets.configs import rmsc04
    from src.envs.calibrate_rmsc04_ipsa import build_rmsc04_ipsa_config, to_abides_kwargs

    cfg = build_rmsc04_ipsa_config(ticker="FALABELLA", tramo="apertura")
    config_state = rmsc04.build_config(seed=1, **to_abides_kwargs(cfg))
    # o, con el entorno gym:
    # EjecutorEnvAbides(..., background_config_extra_kvargs=to_abides_kwargs(cfg))
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union

import numpy as np
import pandas as pd

from src.config.market_params import INCLUDE_CLOSING_AUCTION, TRAMOS_EJECUTOR

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CALIBRATION_JSON = REPO_ROOT / "data" / "calibration" / "poisson_params_2026-08-23.json"
DEFAULT_PROCESSED_DIR = REPO_ROOT / "data" / "processed"
DEFAULT_OUT_DIR = REPO_ROOT / "data" / "calibration"
# Mismo periodo que lambda y que `objetivos_validacion` (H3 del plan).
DEFAULT_SNAPSHOT = "2026-08-23"
DEFAULT_TICKER = "FALABELLA"

# Los timestamps de ABIDES son nanosegundos; una vela de 5 min = 300e9 ns.
NS_POR_SEGUNDO = 10 ** 9
NS_POR_VELA_5MIN = 300 * NS_POR_SEGUNDO

# Unidad de cuenta de ABIDES (H6). El tick del simulador es siempre 1 unidad,
# asi que la unidad elegida fija el tick efectivo: 1e4 / r_bar bps.
UNIDADES_POR_CLP: Dict[str, int] = {"centavos": 100, "decimos": 10, "clp": 1}
# Decision A2 (BF, 2026-10-03): en los datos de FALABELLA el incremento
# minimo de precio es 0,1 CLP (~0,17 bps) en los snapshots 2026-08-23 y
# 2026-09-27. Con "decimos" el tick del simulador coincide con ese valor; con
# "centavos" queda 10 veces mas fino y con "clp" 10 veces mas grueso.
DEFAULT_UNIDAD_CUENTA = "decimos"

# Default de rmsc04 para el capital por agente: 10 000 000 centavos. Se
# expresa en CLP para que la conversion a la unidad de cuenta sea explicita.
# Los agentes de fondo envian sus ordenes sin control de riesgo, asi que este
# valor no restringe la simulacion.
STARTING_CASH_CLP = 100_000

# Defaults de rmsc04 que este modulo necesita conocer (copiados de la firma).
KAPPA_ORACLE_RMSC04 = 1.67e-16

VR_QS = (2, 6, 12)

_TRAMO_HORAS = {name: (start + ":00", end + ":00") for name, start, end in TRAMOS_EJECUTOR}

# Parametros de rmsc04.build_config() que este modulo NO fija: quedan en el
# default de rmsc04 salvo que la busqueda del bloque B (grilla + validacion)
# los entregue. Resueltos en el bloque A y por eso fuera de esta lista:
# `kappa_oracle` (A4) y `megashock_*` (A5, default justificado).
CAMPOS_PENDIENTES_2_2_4 = (
    # sin analogo en datos OHLCV: se dejan en el default de rmsc04
    "kappa", "sigma_s",
    "mm_wake_up_freq", "mm_min_order_size", "mm_skew_beta", "mm_price_skew",
    "mm_backstop_quantity", "mm_cancel_limit_delay",
    "num_value_agents", "num_momentum_agents",
    # parametros libres de la busqueda (bloque B)
    "mm_window_size", "mm_pov", "mm_num_ticks", "mm_level_spacing", "mm_spread_alpha",
    "num_noise_agents", "lambda_a",
)

# Llaves de `build_rmsc04_ipsa_config()` que no se pasan a ABIDES. `ticker`
# se excluye porque ABIDES-Gym crea su agente con el simbolo "ABM" fijo
# (abides_gym/envs/core_environment.py): cambiar el ticker del exchange deja
# al agente operando un simbolo inexistente. El ticker real va en `_metadata`.
_LLAVES_NO_ABIDES = ("ticker",)


# ---------------------------------------------------------------------------
# Unidades: fund_vol y varianza del oraculo OU
# ---------------------------------------------------------------------------

def ou_variance(fund_vol: float, kappa: float, dt_ns: float) -> float:
    """Varianza condicional del oraculo OU de ABIDES tras `dt_ns` nanosegundos:
    fund_vol^2 / (2 kappa) * (1 - e^{-2 kappa dt}); con kappa -> 0 tiende a
    fund_vol^2 * dt."""
    x = 2.0 * kappa * dt_ns
    if x < 1e-12:
        return fund_vol ** 2 * dt_ns
    return fund_vol ** 2 * dt_ns * (-math.expm1(-x) / x)


def fund_vol_from_sigma(sigma_5min: float, r_bar: float,
                        kappa_oracle: float = KAPPA_ORACLE_RMSC04,
                        dt_ns: float = NS_POR_VELA_5MIN) -> float:
    """`fund_vol` tal que el desvio del fundamental en una vela de 5 min sea
    `sigma_5min * r_bar` (unidades de precio).

    Con kappa -> 0: fund_vol = sigma_5min * r_bar / sqrt(300e9). Con el
    kappa_oracle por defecto (1,67e-16 por ns) la correccion es de 2,5e-5 en
    terminos relativos; se usa la inversion exacta para que la formula siga
    valiendo si A4 entrega un kappa mayor.
    """
    return abs(sigma_5min) * r_bar / math.sqrt(ou_variance(1.0, kappa_oracle, dt_ns))


def tick_efectivo_bps(r_bar: float) -> float:
    """Tick del simulador (1 unidad de cuenta) en bps del precio."""
    return 1e4 / r_bar


# ---------------------------------------------------------------------------
# A4: razon de varianzas (Lo y MacKinlay, 1988)
# ---------------------------------------------------------------------------

Segmentos = Union[np.ndarray, Sequence[float], Sequence[Sequence[float]]]


def _as_segments(returns: Segmentos) -> List[np.ndarray]:
    if isinstance(returns, np.ndarray) and returns.ndim == 1:
        return [returns.astype(float)]
    seq = list(returns)
    if len(seq) > 0 and np.ndim(seq[0]) == 0:
        return [np.asarray(seq, dtype=float)]
    return [np.asarray(s, dtype=float) for s in seq if len(s) > 0]


def variance_ratio(returns: Segmentos, q: int) -> Dict[str, float]:
    """Razon de varianzas VR(q) con el estadistico z* robusto a
    heterocedasticidad de Lo y MacKinlay (1988).

    `returns` es una serie de retornos consecutivos o una lista de segmentos
    (cada uno de retornos consecutivos, por ejemplo un dia x tramo). Con
    segmentos, las autocorrelaciones se estiman solo con pares del mismo
    segmento, de modo que no se mezclan retornos separados por la noche, por
    un cambio de tramo o por velas sin transaccion.

        VR(q) = 1 + 2 sum_{j=1}^{q-1} (1 - j/q) rho_j
        z*(q) = (VR(q) - 1) / sqrt(sum_{j=1}^{q-1} [2 (q - j) / q]^2 delta_j)
        delta_j = sum_t e_t^2 e_{t-j}^2 / (sum_t e_t^2)^2,   e_t = r_t - media

    Bajo paseo aleatorio VR = 1 y z* ~ N(0, 1). VR < 1 indica reversion.
    """
    if q < 2:
        raise ValueError("q debe ser >= 2")
    segs = _as_segments(returns)
    n = int(sum(len(s) for s in segs))
    if n < q + 1:
        return {"q": q, "vr": float("nan"), "z_robusto": float("nan"),
                "p_valor": float("nan"), "n": n}
    mu = float(np.concatenate(segs).mean())
    dev = [s - mu for s in segs]
    s2 = float(sum(float(np.dot(e, e)) for e in dev))
    if s2 <= 0:
        return {"q": q, "vr": float("nan"), "z_robusto": float("nan"),
                "p_valor": float("nan"), "n": n}
    vr, theta = 1.0, 0.0
    for j in range(1, q):
        num = sum(float(np.dot(e[j:], e[:-j])) for e in dev if len(e) > j)
        num2 = sum(float(np.dot(e[j:] ** 2, e[:-j] ** 2)) for e in dev if len(e) > j)
        w = 2.0 * (q - j) / q
        vr += w * num / s2
        theta += w ** 2 * num2 / s2 ** 2
    z = (vr - 1.0) / math.sqrt(theta) if theta > 0 else float("nan")
    p = math.erfc(abs(z) / math.sqrt(2.0)) if math.isfinite(z) else float("nan")
    return {"q": q, "vr": float(vr), "z_robusto": float(z), "p_valor": float(p), "n": n}


def autocorr_lag1(returns: Segmentos) -> float:
    """Autocorrelacion de orden 1 con pares dentro de cada segmento."""
    segs = _as_segments(returns)
    if not segs:
        return float("nan")
    mu = float(np.concatenate(segs).mean())
    dev = [s - mu for s in segs]
    s2 = sum(float(np.dot(e, e)) for e in dev)
    if s2 <= 0:
        return float("nan")
    return float(sum(float(np.dot(e[1:], e[:-1])) for e in dev if len(e) > 1) / s2)


def vr_teorica_ma1(rho1: float, q: int) -> float:
    """VR(q) si la autocorrelacion es solo de orden 1 (rebote bid-ask, Roll
    1984): 1 + 2 (1 - 1/q) rho1. Converge a 1 + 2 rho1 al crecer q."""
    return 1.0 + 2.0 * (1.0 - 1.0 / q) * rho1


def vr_teorica_ou(rho1: float, q: int) -> float:
    """VR(q) si los retornos son incrementos de un OU muestreado cada vela,
    con persistencia del nivel phi = 1 + 2 rho1: rho_j = rho1 phi^(j-1).
    Sigue cayendo hacia 0 al crecer q."""
    phi = 1.0 + 2.0 * rho1
    return 1.0 + 2.0 * sum((1.0 - j / q) * rho1 * phi ** (j - 1) for j in range(1, q))


def decide_kappa_oracle(returns: Segmentos, qs: Sequence[int] = VR_QS, alpha: float = 0.05,
                        dt_ns: float = NS_POR_VELA_5MIN) -> Dict:
    """Aplica la regla A4 del plan y deja la evidencia.

    Regla: si VR(q) ~ 1 (no se rechaza el paseo aleatorio) se mantiene el
    default de rmsc04. Si VR(q) < 1 y es significativa en la mayoria de los
    q, `kappa_oracle = -ln(phi) / dt_ns`, con phi = 1 + 2 rho1 la
    persistencia del nivel que implica la autocorrelacion de orden 1 de los
    retornos (para un OU muestreado cada dt, rho1 = -(1 - phi) / 2).

    Ademas del kappa de la regla se reporta un diagnostico: una VR < 1 en
    velas de 5 min puede venir del rebote bid-ask (autocorrelacion solo de
    orden 1, VR se estabiliza en 1 + 2 rho1) y no de reversion del valor
    fundamental (VR sigue cayendo con q). `patron_mas_cercano` indica cual de
    las dos formas se parece mas a la VR observada.

    Decision (BF, 2026-10-03): `kappa_oracle_adoptado` es el de la regla solo
    si la reversion es significativa Y el patron mas cercano es el OU. Si la
    VR calza con el rebote bid-ask se mantiene el default de rmsc04: ese
    rebote lo genera el spread del propio simulador, no el fundamental.
    """
    tests = [variance_ratio(returns, q) for q in qs]
    z_crit = 1.959963984540054 if alpha == 0.05 else float(
        math.sqrt(2.0) * _erfcinv(alpha))
    rechazos = [t for t in tests if math.isfinite(t["z_robusto"])
                and t["vr"] < 1.0 and abs(t["z_robusto"]) > z_crit]
    reversion = len(rechazos) * 2 > len(tests)
    rho1 = autocorr_lag1(returns)
    out: Dict = {
        "tests": tests, "alpha": alpha, "rho1": rho1,
        "reversion_significativa": bool(reversion),
        "kappa_oracle_default_rmsc04": KAPPA_ORACLE_RMSC04,
    }
    if reversion and math.isfinite(rho1) and rho1 < 0:
        phi = min(max(1.0 + 2.0 * rho1, 0.01), 0.99)
        kappa = -math.log(phi) / dt_ns
        err_ma1 = sum((t["vr"] - vr_teorica_ma1(rho1, t["q"])) ** 2 for t in tests)
        err_ou = sum((t["vr"] - vr_teorica_ou(rho1, t["q"])) ** 2 for t in tests)
        out.update({
            "phi_nivel": phi,
            "kappa_oracle_regla": kappa,
            "vida_media_min": math.log(2.0) / kappa / NS_POR_SEGUNDO / 60.0,
            "vr_teorica_ma1": {str(t["q"]): vr_teorica_ma1(rho1, t["q"]) for t in tests},
            "vr_teorica_ou": {str(t["q"]): vr_teorica_ou(rho1, t["q"]) for t in tests},
            "error_cuadratico_ma1": err_ma1,
            "error_cuadratico_ou": err_ou,
            "patron_mas_cercano": "rebote_bid_ask_ma1" if err_ma1 < err_ou else "reversion_ou",
        })
        out["kappa_oracle_adoptado"] = kappa if err_ou < err_ma1 else KAPPA_ORACLE_RMSC04
    else:
        out["kappa_oracle_regla"] = KAPPA_ORACLE_RMSC04
        out["kappa_oracle_adoptado"] = KAPPA_ORACLE_RMSC04
    return out


def _erfcinv(alpha: float) -> float:
    from scipy.special import erfcinv
    return float(erfcinv(alpha))


# ---------------------------------------------------------------------------
# A5: curtosis
# ---------------------------------------------------------------------------

def return_kurtosis(returns: Segmentos) -> Dict[str, float]:
    """Exceso de curtosis (0 = normal) de los retornos, sin correccion de
    sesgo, mas el tamano de muestra."""
    segs = _as_segments(returns)
    x = np.concatenate(segs) if segs else np.array([], dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < 4 or x.std() == 0:
        return {"exceso_curtosis": float("nan"), "n": int(len(x))}
    z = (x - x.mean()) / x.std()
    return {"exceso_curtosis": float(np.mean(z ** 4) - 3.0), "n": int(len(x))}


# ---------------------------------------------------------------------------
# Datos reales
# ---------------------------------------------------------------------------

def _clean_dir(snapshot: str, processed_dir: Optional[Path] = None) -> Path:
    return Path(processed_dir or DEFAULT_PROCESSED_DIR) / f"clean_5m_{snapshot}"


def _median_close_price(ticker: str, clean_5m_dir: Path) -> float:
    """Precio mediano real del ticker (CLP) sobre el snapshot limpio. Usa
    `_combined.parquet` si existe y, si no, el parquet del ticker."""
    combined = clean_5m_dir / "_combined.parquet"
    if combined.exists():
        df = pd.read_parquet(combined, columns=["ticker", "close_raw"])
        sub = df[df["ticker"] == ticker]
        if sub.empty:
            raise ValueError(
                f"Ticker {ticker!r} no encontrado en {clean_5m_dir}. "
                f"Tickers disponibles: {sorted(df['ticker'].unique())[:5]}..."
            )
        return float(sub["close_raw"].median())
    single = clean_5m_dir / f"{ticker}.parquet"
    if not single.exists():
        raise FileNotFoundError(
            f"No hay datos de {ticker!r} en {clean_5m_dir}. Los .parquet no se "
            "versionan: descomprimir backups/snapshot_<fecha>.zip en la raiz del repo."
        )
    return float(pd.read_parquet(single, columns=["close_raw"])["close_raw"].median())


def _lambda_params_por_tramo(ticker: str, tramo: str, calibration_json: Path) -> Dict:
    """Parametros de la 2.1.3 para (ticker, tramo). De aqui solo se usa
    `obs_return_std` (sigma de 5 min) para `fund_vol`."""
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


def contiguous_return_segments(df: pd.DataFrame, bar_minutes: int = 5) -> Dict[str, List[np.ndarray]]:
    """Retornos de 5 min por tramo, agrupados en segmentos de velas
    consecutivas del mismo dia y tramo.

    `df` tiene las columnas de `calibration_poisson.load_clean_data`: `ts`,
    `day`, `tramo`, `ret` (NaN si la vela o su antecesora esta imputada) e
    `is_auction`. Aplica las mismas exclusiones que la 2.1.3 (velas imputadas
    y, por defecto, la vela de subasta), por lo que la union de los segmentos
    de un tramo es la muestra `n_returns` de `poisson_params_*.json`.
    """
    d = df[df["tramo"].notna()]
    if not INCLUDE_CLOSING_AUCTION and "is_auction" in d.columns:
        d = d[~d["is_auction"]]
    d = d[d["ret"].notna()].sort_values("ts")
    out: Dict[str, List[np.ndarray]] = {name: [] for name in _TRAMO_HORAS}
    step = pd.Timedelta(minutes=bar_minutes)
    for (_, tramo), g in d.groupby(["day", "tramo"], sort=False):
        corte = (g["ts"].diff() != step).cumsum()
        for _, run in g.groupby(corte, sort=False):
            out[tramo].append(run["ret"].to_numpy(dtype=float))
    return out


def real_returns_by_tramo(ticker: str, snapshot: str = DEFAULT_SNAPSHOT,
                          processed_dir: Optional[Path] = None) -> Dict[str, List[np.ndarray]]:
    """Segmentos de retornos reales de 5 min de `ticker` por tramo."""
    from src.envs.calibration_poisson import load_clean_data

    df = load_clean_data(ticker, data_dir=processed_dir or DEFAULT_PROCESSED_DIR, snapshot=snapshot)
    return contiguous_return_segments(df)


def evidencia_a4_a5(segmentos: Dict[str, List[np.ndarray]]) -> Dict[str, Dict]:
    """Por tramo: test de razon de varianzas con la decision de kappa (A4) y
    curtosis real (A5)."""
    out = {}
    for tramo, segs in segmentos.items():
        out[tramo] = {
            "n_retornos": int(sum(len(s) for s in segs)),
            "n_segmentos": len(segs),
            "variance_ratio": decide_kappa_oracle(segs),
            "curtosis_real": return_kurtosis(segs),
        }
    return out


# ---------------------------------------------------------------------------
# Armado de la config
# ---------------------------------------------------------------------------

def build_rmsc04_ipsa_config(
    ticker: str,
    tramo: str,
    date: str = "20260823",
    calibration_json: Optional[Path] = None,
    clean_5m_dir: Optional[Path] = None,
    starting_cash_clp: float = STARTING_CASH_CLP,
    snapshot: str = DEFAULT_SNAPSHOT,
    unidad_cuenta: str = DEFAULT_UNIDAD_CUENTA,
    kappa_oracle: Optional[float] = None,
    r_bar_clp: Optional[float] = None,
    extra: Optional[Dict] = None,
) -> Dict:
    """Arma la config de rmsc04 para (ticker, tramo) con los campos del
    bloque A. Los de `CAMPOS_PENDIENTES_2_2_4` no se incluyen salvo que
    lleguen en `extra` (resultado de la busqueda): al no pasarlos,
    `rmsc04.build_config()` usa su propio default.

    Args:
        ticker: simbolo IPSA sin sufijo .SN (ej. "FALABELLA").
        tramo: "apertura" | "media_jornada" | "cierre".
        date: fecha de simulacion (YYYYMMDD); no afecta la dinamica.
        calibration_json: `poisson_params_<fecha>.json` de la 2.1.3.
        clean_5m_dir: carpeta `clean_5m_<fecha>`; por defecto la de `snapshot`.
        starting_cash_clp: capital inicial por agente de fondo, en CLP.
        snapshot: snapshot de datos para `r_bar` (default 2026-08-23, el mismo
            periodo de lambda y de `objetivos_validacion`).
        unidad_cuenta: "decimos" (1 unidad = 0,1 CLP, default), "centavos"
            (0,01 CLP) o "clp" (1 CLP). Se aplica a `r_bar`, `starting_cash` y
            `fund_vol`.
        kappa_oracle: reversion del fundamental (por ns). None = default de
            rmsc04 (no se incluye en la config).
        r_bar_clp: precio de referencia en CLP; si se entrega no se leen los
            parquet (util en tests y en Colab sin datos).
        extra: parametros adicionales de `rmsc04.build_config` (los `mm_*`,
            `num_noise_agents`, `lambda_a` que entrega la busqueda).

    Returns:
        dict con los kwargs de rmsc04 mas `ticker`, `_campos_pendientes_2_2_4`
        y `_metadata`. Pasar por `to_abides_kwargs()` antes de entregarlo a
        ABIDES.

    Limitacion: `fund_vol` es unico por simulacion, asi que la volatilidad
    calza solo en el tramo de la config (una config por tramo). No es una
    volatilidad intradiaria variable.
    """
    if tramo not in _TRAMO_HORAS:
        raise ValueError(f"tramo invalido: {tramo!r}. Validos: {list(_TRAMO_HORAS)}")
    if unidad_cuenta not in UNIDADES_POR_CLP:
        raise ValueError(
            f"unidad_cuenta invalida: {unidad_cuenta!r}. Validas: {list(UNIDADES_POR_CLP)}")

    calibration_json = Path(calibration_json or DEFAULT_CALIBRATION_JSON)
    hora_inicio, hora_fin = _TRAMO_HORAS[tramo]
    if r_bar_clp is None:
        r_bar_clp = _median_close_price(ticker, Path(clean_5m_dir or _clean_dir(snapshot)))
        r_bar_fuente = f"mediana de close_raw, snapshot {snapshot}"
    else:
        r_bar_fuente = "entregado por el usuario"
    sigma_5min = abs(_lambda_params_por_tramo(ticker, tramo, calibration_json)["obs_return_std"])

    escala = UNIDADES_POR_CLP[unidad_cuenta]
    r_bar = int(round(r_bar_clp * escala))
    kappa_efectivo = KAPPA_ORACLE_RMSC04 if kappa_oracle is None else float(kappa_oracle)
    fund_vol = fund_vol_from_sigma(sigma_5min, r_bar, kappa_efectivo)

    cfg: Dict = {
        "ticker": ticker,
        "date": date,
        "end_time": "16:00:00",
        "starting_cash": int(round(starting_cash_clp * escala)),
        "r_bar": r_bar,
        "fund_vol": fund_vol,
    }
    if kappa_oracle is not None:
        cfg["kappa_oracle"] = float(kappa_oracle)
    extra = dict(extra or {})
    cfg.update(extra)
    fijados = set(cfg)
    cfg["_campos_pendientes_2_2_4"] = [c for c in CAMPOS_PENDIENTES_2_2_4 if c not in fijados]
    cfg["_metadata"] = {
        "ticker": ticker, "tramo": tramo, "hora_inicio": hora_inicio, "hora_fin": hora_fin,
        "snapshot": snapshot,
        "unidad_cuenta": unidad_cuenta,
        "unidades_por_clp": escala,
        "r_bar_clp_mediano": r_bar_clp,
        "r_bar_fuente": r_bar_fuente,
        "tick_efectivo_bps": tick_efectivo_bps(r_bar),
        "tick_efectivo_clp": 1.0 / escala,
        "sigma_5min": sigma_5min,
        "sigma_5min_fuente": f"obs_return_std de {calibration_json.name} (2.1.3)",
        "fund_vol_formula": "sigma_5min * r_bar / sqrt(Var_OU(fund_vol=1, kappa_oracle, 300e9 ns))",
        "kappa_oracle_usado_en_fund_vol": kappa_efectivo,
        "desvio_5min_objetivo_unidades": sigma_5min * r_bar,
        "parametros_de_busqueda": sorted(extra),
    }
    return cfg


def to_abides_kwargs(cfg: Dict) -> Dict:
    """Dict limpio para `rmsc04.build_config(**kwargs)` o para
    `background_config_extra_kvargs` de `EjecutorEnvAbides`: sin las llaves
    internas (`_metadata`, `_campos_pendientes_2_2_4`) y sin `ticker` (ver
    `_LLAVES_NO_ABIDES`). No incluye `seed`: la fija quien corre la simulacion."""
    return {k: v for k, v in cfg.items()
            if not k.startswith("_") and k not in _LLAVES_NO_ABIDES}


def load_abides_kwargs(json_path: Union[str, Path]) -> Dict[str, Dict]:
    """{tramo: abides_kwargs} desde un JSON de la 2.2.4 (`rmsc04_base_*.json`
    de este modulo o `rmsc04_ipsa_*.json` de la validacion). Ambos guardan la
    config de cada tramo en `por_tramo[tramo]["abides_kwargs"]`."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    faltan = [t for t in _TRAMO_HORAS if "abides_kwargs" not in data.get("por_tramo", {}).get(t, {})]
    if faltan:
        raise ValueError(f"{json_path}: falta por_tramo[tramo]['abides_kwargs'] para {faltan}")
    return {t: to_abides_kwargs(data["por_tramo"][t]["abides_kwargs"]) for t in _TRAMO_HORAS}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_base_report(ticker: str, snapshot: str, unidad_cuenta: str,
                      calibration_json: Optional[Path] = None,
                      processed_dir: Optional[Path] = None,
                      usar_kappa_regla: bool = False) -> Dict:
    """Bloque A completo para un ticker: config por tramo (lista para
    `to_abides_kwargs`) mas la evidencia de A4 y A5."""
    segmentos = real_returns_by_tramo(ticker, snapshot, processed_dir)
    evidencia = evidencia_a4_a5(segmentos)
    por_tramo = {}
    for tramo in _TRAMO_HORAS:
        llave = "kappa_oracle_regla" if usar_kappa_regla else "kappa_oracle_adoptado"
        kappa = evidencia[tramo]["variance_ratio"][llave]
        if kappa == KAPPA_ORACLE_RMSC04:
            kappa = None
        cfg = build_rmsc04_ipsa_config(
            ticker, tramo, calibration_json=calibration_json, snapshot=snapshot,
            clean_5m_dir=_clean_dir(snapshot, processed_dir),
            unidad_cuenta=unidad_cuenta, kappa_oracle=kappa)
        por_tramo[tramo] = {"config": cfg, "abides_kwargs": to_abides_kwargs(cfg), **evidencia[tramo]}
    return {
        "metadata": {
            "tarea": "2.2.4 bloque A", "ticker": ticker, "snapshot": snapshot,
            "unidad_cuenta": unidad_cuenta, "kappa_regla_literal_forzada": usar_kappa_regla,
            "megashock": "default de rmsc04 (megashock_lambda_a = 2,78e-18 por ns: "
                         "~1 evento cada 11 anios; no actua dentro de la jornada)",
            "fecha_generacion": pd.Timestamp.now(tz="America/Santiago").isoformat(timespec="seconds"),
        },
        "por_tramo": por_tramo,
    }


def main(argv: Optional[Sequence[str]] = None) -> None:
    ap = argparse.ArgumentParser(description="Bloque A de la 2.2.4: config base de rmsc04 por tramo.")
    ap.add_argument("--ticker", default=DEFAULT_TICKER)
    ap.add_argument("--snapshot", default=DEFAULT_SNAPSHOT)
    ap.add_argument("--unidad-cuenta", default=DEFAULT_UNIDAD_CUENTA, choices=list(UNIDADES_POR_CLP))
    ap.add_argument("--calibration-json", default=None)
    ap.add_argument("--kappa-regla-vr", action="store_true",
                    help="fuerza el kappa_oracle de la regla literal aunque la VR calce con rebote bid-ask")
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    args = ap.parse_args(argv)

    report = build_base_report(
        args.ticker, args.snapshot, args.unidad_cuenta,
        calibration_json=Path(args.calibration_json) if args.calibration_json else None,
        usar_kappa_regla=args.kappa_regla_vr)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"rmsc04_base_{args.ticker}_{args.snapshot}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    for tramo, r in report["por_tramo"].items():
        k = r["abides_kwargs"]
        vr = " ".join("VR({q})={vr:.3f} z={z_robusto:.2f}".format(**t) for t in r["variance_ratio"]["tests"])
        print(f"{tramo:14s} r_bar={k['r_bar']} fund_vol={k['fund_vol']:.4g} "
              f"tick={r['config']['_metadata']['tick_efectivo_bps']:.3f} bps | {vr} | "
              f"curtosis={r['curtosis_real']['exceso_curtosis']:.2f}")
    print(f"Guardado: {out}")


if __name__ == "__main__":
    main()
