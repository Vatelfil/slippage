"""Robustez del patron intradiario de spread y actividad en el IPSA
(tarea 2.1.3b, Parte A). Autor: Benjamin Farias (BF).

Pregunta: la 2.1.3 encontro, con Roll (1984) y el rango high-low (HL), que
el spread-proxy mas ancho esta en la APERTURA y no en la media jornada
(11:30-14:00), como supone el Titulo I (secciones 4.3.3 y 4.3.5). Este modulo
repite la comparacion con dos estimadores que separan mejor spread de
volatilidad, Corwin-Schultz (2012) y Abdi-Ranaldo (2017), agrega la
volatilidad, el cociente spread/volatilidad y el volumen mediano por vela,
por tramo del Ejecutor y por bloque de 30 min, en mas de un snapshot. No se
fuerza ningun resultado: el veredicto cuenta tickers.

Datos: data/processed/clean_5m_<snapshot>/<TICKER>.parquet (salida de
clean_ohlcv.py). Se usan SIEMPRE las columnas *_raw. Exclusiones:
- velas con is_imputed=True (sin transaccion real);
- la vela 15:55, que contiene la subasta de cierre (market_params);
- dias de sesion corta (ej. vispera de feriado con cierre a las 13:00),
  detectados a nivel de snapshot (`detect_short_sessions`): su subasta cae en
  media jornada y contaminaria la comparacion.

Estimadores por grupo g (tramo o bloque), sobre velas observadas del mismo
dia; un "par" (t-1, t) exige ambas velas observadas, del mismo dia y del
mismo grupo. Todos se expresan como spread RELATIVO (fraccion del precio) y
se reportan en puntos base:

- Roll (1984):  S = 2 sqrt(-cov(r_t, r_{t-1})), r_t = ln(C_t / C_{t-1});
  NaN si la covarianza es >= 0.
- Rango HL medio: mean[(H_t - L_t) / ((H_t + L_t)/2)]. Mezcla spread y
  volatilidad intra-vela; se incluye como referencia de la 2.1.3.
- Corwin-Schultz (2012), ecuaciones (14) y (18) del paper:
      beta  = [ln(H_{t-1}/L_{t-1})]^2 + [ln(H_t/L_t)]^2
      gamma = [ln(max(H_{t-1},H_t) / min(L_{t-1},L_t))]^2
      alpha = (sqrt(2 beta) - sqrt(beta)) / (3 - 2 sqrt 2) - sqrt(gamma / (3 - 2 sqrt 2))
      S     = 2 (e^alpha - 1) / (1 + e^alpha)
  con el ajuste por salto entre velas de la seccion 3.a del paper (si
  L_t > C_{t-1} o H_t < C_{t-1}, se desplazan H_t y L_t por el salto) y las
  estimaciones negativas de cada par fijadas en 0 antes de promediar, como
  en el paper. Identifica el spread porque la varianza escala con el largo
  del intervalo (beta vs gamma) y el spread no.
- Abdi-Ranaldo (2017), estimador CHL, ecuacion (10) del paper:
      eta_t = (ln H_t + ln L_t) / 2,   c_t = ln C_t
      S^2   = 4 E[(c_{t-1} - eta_{t-1}) (c_{t-1} - eta_t)]
      S     = sqrt(max(S^2, 0))
  (version de momentos: se promedia el producto y luego se toma la raiz;
  `ar_method="two_period"` promedia las raices por par con negativos en 0).

Volatilidad: desviacion estandar (ddof=0, igual que obs_return_std de la
2.1.3) de r_t entre velas observadas consecutivas del mismo dia, asignado al
grupo de la vela t. Actividad: volumen mediano por vela observada (mediana,
no media, para que una operacion en bloque no domine) y fraccion de velas con
transaccion.

Limitacion principal: sin Nivel 2 no se observan bid/ask; los cuatro
estimadores son proxies desde OHLC de 5 min y estan sesgados por la
discrecion del tick y por la volatilidad intra-vela. Ver
docs/robustez_patron_intradiario_BF.md.

Uso:
    python -m src.analysis.intraday_profile --snapshots 2026-08-23 2026-09-27 \\
        --post-msci-from 2026-09-01
"""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from src.config import market_params as mp

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = _REPO_ROOT / "data" / "processed"
DEFAULT_OUTPUT_JSON = _REPO_ROOT / "data" / "calibration" / "robustez_patron_intradiario.json"
DEFAULT_RESULTS_DIR = _REPO_ROOT / "results" / "sprint3"

TRAMO_NAMES: Tuple[str, ...] = tuple(t[0] for t in mp.TRAMOS_EJECUTOR)
SESSION_START_MIN = 9 * 60 + 30
BLOCK_MINUTES = 30
N_BLOCKS = 13
BLOQUES_30M: Tuple[str, ...] = tuple(
    f"{(SESSION_START_MIN + i * BLOCK_MINUTES) // 60:02d}:{(SESSION_START_MIN + i * BLOCK_MINUTES) % 60:02d}"
    for i in range(N_BLOCKS)
)
ESTIMADORES: Tuple[str, ...] = ("roll", "hl", "cs", "ar")
ESTIMADOR_LABEL = {"roll": "Roll (1984)", "hl": "Rango HL", "cs": "Corwin-Schultz (2012)",
                   "ar": "Abdi-Ranaldo (2017)"}
MIN_PAIRS = 10
SHORT_SESSION_CUTOFF_MIN = 14 * 60     # dia corto: < 50% de tickers transan despues de las 14:00
FALABELLA = "FALABELLA"
_K_CS = 3.0 - 2.0 * np.sqrt(2.0)


# ---------------------------------------------------------------------------
# 1) Estimadores de spread (numpy puro, con pesos opcionales por observacion)
# ---------------------------------------------------------------------------

def _w(n: int, weights: Optional[np.ndarray]) -> np.ndarray:
    return np.ones(n) if weights is None else np.asarray(weights, dtype=float)


def roll_spread(ret: np.ndarray, ret_prev: np.ndarray,
                weights: Optional[np.ndarray] = None) -> float:
    """Roll (1984): S = 2 sqrt(-cov(r_t, r_{t-1})), relativo. NaN si cov >= 0
    o hay menos de MIN_PAIRS pares. Con pesos enteros (bootstrap) equivale a
    repetir pares; con pesos 1 coincide con np.cov (ddof=1)."""
    x, y = np.asarray(ret, float), np.asarray(ret_prev, float)
    w = _w(len(x), weights)
    ok = np.isfinite(x) & np.isfinite(y) & (w > 0)
    x, y, w = x[ok], y[ok], w[ok]
    sw = w.sum()
    if len(x) < MIN_PAIRS or sw <= 1:
        return float("nan")
    cov = np.sum(w * (x - np.sum(w * x) / sw) * (y - np.sum(w * y) / sw)) / (sw - 1.0)
    return float(2.0 * np.sqrt(-cov)) if cov < 0 else float("nan")


def hl_range(high: np.ndarray, low: np.ndarray, weights: Optional[np.ndarray] = None) -> float:
    """Rango high-low relativo medio: mean[(H - L) / ((H + L) / 2)]."""
    h, l = np.asarray(high, float), np.asarray(low, float)
    w = _w(len(h), weights)
    rel = (h - l) / ((h + l) / 2.0)
    ok = np.isfinite(rel) & (w > 0)
    if not ok.any():
        return float("nan")
    return float(np.sum(w[ok] * rel[ok]) / np.sum(w[ok]))


def corwin_schultz_pairs(h0: np.ndarray, l0: np.ndarray, c0: np.ndarray,
                         h1: np.ndarray, l1: np.ndarray, adjust_gap: bool = True,
                         clip_negative: bool = True) -> np.ndarray:
    """Spread de Corwin & Schultz (2012) para cada par de velas (t-1, t).

    beta  = ln(H0/L0)^2 + ln(H1/L1)^2
    gamma = ln(max(H0,H1) / min(L0,L1))^2
    alpha = (sqrt(2 beta) - sqrt(beta)) / (3 - 2 sqrt 2) - sqrt(gamma / (3 - 2 sqrt 2))
    S     = 2 (exp(alpha) - 1) / (1 + exp(alpha))

    `adjust_gap` aplica el ajuste de la seccion 3.a: si L1 > C0 (salto al
    alza) se restan (L1 - C0) a H1 y L1; si H1 < C0 (salto a la baja) se
    suman (C0 - H1). `clip_negative` fija en 0 los S negativos (paper)."""
    h0, l0, c0 = (np.asarray(a, float) for a in (h0, l0, c0))
    h1, l1 = np.asarray(h1, float).copy(), np.asarray(l1, float).copy()
    if adjust_gap:
        up = l1 > c0
        down = h1 < c0
        shift = np.where(up, -(l1 - c0), np.where(down, c0 - h1, 0.0))
        h1 = h1 + shift
        l1 = l1 + shift
    beta = np.log(h0 / l0) ** 2 + np.log(h1 / l1) ** 2
    gamma = np.log(np.maximum(h0, h1) / np.minimum(l0, l1)) ** 2
    alpha = (np.sqrt(2.0 * beta) - np.sqrt(beta)) / _K_CS - np.sqrt(gamma / _K_CS)
    s = 2.0 * (np.exp(alpha) - 1.0) / (1.0 + np.exp(alpha))
    if clip_negative:
        s = np.maximum(s, 0.0)
    return s


def corwin_schultz(h0, l0, c0, h1, l1, weights: Optional[np.ndarray] = None,
                   adjust_gap: bool = True) -> float:
    """Promedio (ponderado) de `corwin_schultz_pairs`. NaN con < MIN_PAIRS pares."""
    s = corwin_schultz_pairs(h0, l0, c0, h1, l1, adjust_gap=adjust_gap)
    w = _w(len(s), weights)
    ok = np.isfinite(s) & (w > 0)
    if ok.sum() < MIN_PAIRS:
        return float("nan")
    return float(np.sum(w[ok] * s[ok]) / np.sum(w[ok]))


def abdi_ranaldo_products(h0, l0, c0, h1, l1) -> np.ndarray:
    """Producto (c_{t-1} - eta_{t-1}) (c_{t-1} - eta_t) de Abdi & Ranaldo
    (2017), con eta = (ln H + ln L)/2 y c = ln C."""
    eta0 = (np.log(np.asarray(h0, float)) + np.log(np.asarray(l0, float))) / 2.0
    eta1 = (np.log(np.asarray(h1, float)) + np.log(np.asarray(l1, float))) / 2.0
    c = np.log(np.asarray(c0, float))
    return (c - eta0) * (c - eta1)


def abdi_ranaldo(h0, l0, c0, h1, l1, weights: Optional[np.ndarray] = None,
                 method: str = "moment") -> float:
    """Abdi & Ranaldo (2017), estimador CHL.

    method="moment":     S = sqrt(max(4 E[prod], 0))
    method="two_period": S = E[sqrt(max(4 prod, 0))]
    NaN con < MIN_PAIRS pares."""
    prod = abdi_ranaldo_products(h0, l0, c0, h1, l1)
    w = _w(len(prod), weights)
    ok = np.isfinite(prod) & (w > 0)
    if ok.sum() < MIN_PAIRS:
        return float("nan")
    p, w = prod[ok], w[ok]
    if method == "moment":
        return float(np.sqrt(max(4.0 * np.sum(w * p) / np.sum(w), 0.0)))
    if method == "two_period":
        return float(np.sum(w * np.sqrt(np.maximum(4.0 * p, 0.0))) / np.sum(w))
    raise ValueError(f"method desconocido: {method!r}")


def weighted_median(x: np.ndarray, weights: Optional[np.ndarray] = None) -> float:
    x = np.asarray(x, float)
    w = _w(len(x), weights)
    ok = np.isfinite(x) & (w > 0)
    if not ok.any():
        return float("nan")
    x, w = x[ok], w[ok]
    if weights is None:
        return float(np.median(x))
    order = np.argsort(x, kind="mergesort")
    x, cw = x[order], np.cumsum(w[order])
    half = cw[-1] / 2.0
    i = int(np.searchsorted(cw, half))
    if np.isclose(cw[i], half) and i + 1 < len(x):
        return float((x[i] + x[i + 1]) / 2.0)
    return float(x[i])


# ---------------------------------------------------------------------------
# 2) Carga y preparacion de velas
# ---------------------------------------------------------------------------

def snapshot_dir(snapshot: str, data_dir: "str | Path" = DEFAULT_DATA_DIR) -> Path:
    path = Path(data_dir) / f"clean_5m_{snapshot}"
    if not path.is_dir():
        raise FileNotFoundError(f"No existe '{path}'. Genera el snapshot con src/data/clean_ohlcv.py.")
    return path


def list_tickers(snap_dir: Path) -> List[str]:
    return sorted(p.stem for p in snap_dir.glob("*.parquet") if not p.stem.startswith("_"))


def read_tiers(snap_dir: Path) -> Dict[str, Optional[str]]:
    path = snap_dir / "cleaning_report.json"
    if not path.exists():
        return {}
    rep = json.loads(path.read_text(encoding="utf-8"))
    return {t: v.get("tier") for t, v in rep.get("per_ticker", {}).items()}


def _minutes(ts: pd.Series) -> pd.Series:
    return ts.dt.hour * 60 + ts.dt.minute


def tramo_from_minutes(minutes: pd.Series) -> pd.Series:
    out = pd.Series(np.nan, index=minutes.index, dtype=object)
    for i, (name, start, end) in enumerate(mp.TRAMOS_EJECUTOR):
        s = int(start[:2]) * 60 + int(start[3:])
        e = int(end[:2]) * 60 + int(end[3:])
        last = i == len(mp.TRAMOS_EJECUTOR) - 1
        out[(minutes >= s) & ((minutes < e) | (last & (minutes == e)))] = name
    return out


def bloque_from_minutes(minutes: pd.Series) -> pd.Series:
    idx = (minutes - SESSION_START_MIN) // BLOCK_MINUTES
    ok = (idx >= 0) & (idx < N_BLOCKS)
    out = pd.Series(np.nan, index=minutes.index, dtype=object)
    out[ok] = [BLOQUES_30M[int(i)] for i in idx[ok]]
    return out


def load_bars(ticker: str, snap_dir: Path) -> pd.DataFrame:
    """Velas del ticker con columnas crudas renombradas (open/high/low/close/
    volume = *_raw), ts en America/Santiago, day, minute, tramo, bloque,
    is_auction e is_imputed."""
    df = pd.read_parquet(snap_dir / f"{ticker}.parquet")
    base = ["open", "high", "low", "close", "volume"]
    if all(f"{c}_raw" in df.columns for c in base):
        df = df.drop(columns=[c for c in base if c in df.columns]).rename(
            columns={f"{c}_raw": c for c in base})
    ts = pd.to_datetime(df["datetime_santiago"])
    ts = ts.dt.tz_convert(mp.SANTIAGO_TZ) if ts.dt.tz is not None else ts.dt.tz_localize(mp.SANTIAGO_TZ)
    out = pd.DataFrame({
        "ts": ts, "open": df["open"].astype(float), "high": df["high"].astype(float),
        "low": df["low"].astype(float), "close": df["close"].astype(float),
        "volume": df["volume"].astype(float),
        "is_imputed": df["is_imputed"].astype(bool) if "is_imputed" in df else False,
    }).sort_values("ts").reset_index(drop=True)
    out["day"] = out["ts"].dt.date
    out["minute"] = _minutes(out["ts"])
    out["tramo"] = tramo_from_minutes(out["minute"])
    out["bloque"] = bloque_from_minutes(out["minute"])
    out["is_auction"] = out["ts"].dt.strftime("%H:%M") == mp.CLOSING_AUCTION_BAR
    return out


def detect_short_sessions(bars_by_ticker: Dict[str, pd.DataFrame]) -> List[date]:
    """Dias en que menos de la mitad de los tickers tiene alguna vela
    observada despues de las 14:00 (sesion corta, p. ej. vispera de feriado).
    Se detecta a nivel de snapshot para no confundir sesion corta con
    iliquidez de un ticker."""
    flags = []
    for bars in bars_by_ticker.values():
        obs = bars[~bars["is_imputed"]]
        late = obs.groupby("day")["minute"].max() >= SHORT_SESSION_CUTOFF_MIN
        flags.append(late.rename(None))
    if not flags:
        return []
    frac_late = pd.concat(flags, axis=1).mean(axis=1, skipna=True)
    return sorted(d for d, f in frac_late.items() if f < 0.5)


def add_pair_columns(bars: pd.DataFrame, group_col: str) -> pd.DataFrame:
    """Agrega, por vela t, las cantidades por observacion que usan los
    estimadores. Las cantidades de pares quedan en la fila t y solo son
    validas si (t-1, t) son observadas, del mismo dia y del mismo grupo."""
    df = bars.copy()
    by_day = df.groupby("day", sort=False)
    obs = ~df["is_imputed"]
    prev = {c: by_day[c].shift(1) for c in ("high", "low", "close", group_col)}
    prev_obs = ~by_day["is_imputed"].shift(1, fill_value=True).astype(bool)
    same_group = (prev[group_col] == df[group_col]) & df[group_col].notna()
    pair = obs & prev_obs & same_group

    df["hl_rel"] = ((df["high"] - df["low"]) / ((df["high"] + df["low"]) / 2.0)).where(obs)
    df["ret"] = np.log(df["close"] / prev["close"]).where(obs & prev_obs)
    ret_prev = df.groupby("day", sort=False)["ret"].shift(1)
    df["ret_prev"] = ret_prev.where(same_group)
    df["cs_s"] = pd.Series(corwin_schultz_pairs(prev["high"], prev["low"], prev["close"],
                                                df["high"], df["low"]), index=df.index).where(pair)
    df["ar_prod"] = pd.Series(abdi_ranaldo_products(prev["high"], prev["low"], prev["close"],
                                                    df["high"], df["low"]), index=df.index).where(pair)
    df["volume_obs"] = df["volume"].where(obs)
    return df


def prepare(bars: pd.DataFrame, group_col: str, exclude_days: Iterable[date] = (),
            date_from: Optional[date] = None,
            include_auction: bool = mp.INCLUDE_CLOSING_AUCTION) -> pd.DataFrame:
    df = bars
    excl = set(exclude_days)
    if excl:
        df = df[~df["day"].isin(excl)]
    if date_from is not None:
        df = df[df["day"] >= date_from]
    df = add_pair_columns(df, group_col)
    if not include_auction:
        df = df[~df["is_auction"]]
    return df[df[group_col].notna()]


# ---------------------------------------------------------------------------
# 3) Metricas por grupo
# ---------------------------------------------------------------------------

METRICAS: Tuple[str, ...] = (
    "roll_bps", "hl_bps", "cs_bps", "ar_bps", "vol_bps",
    "roll_sobre_vol", "hl_sobre_vol", "cs_sobre_vol", "ar_sobre_vol",
    "volumen_mediano_vela", "frac_velas_con_transaccion",
)


def group_metrics(g: pd.DataFrame, weights: Optional[np.ndarray] = None,
                  ar_method: str = "moment") -> Dict[str, float]:
    """Metricas de un grupo (tramo o bloque). `weights` por fila (bootstrap)."""
    w = _w(len(g), weights)
    ret = g["ret"].to_numpy(float)
    ok_r = np.isfinite(ret) & (w > 0)
    vol = float("nan")
    if ok_r.sum() >= MIN_PAIRS:
        wr, rr = w[ok_r], ret[ok_r]
        m = np.sum(wr * rr) / np.sum(wr)
        vol = float(np.sqrt(np.sum(wr * (rr - m) ** 2) / np.sum(wr)))
    hl = g["hl_rel"].to_numpy(float)
    cs = g["cs_s"].to_numpy(float)
    ar = g["ar_prod"].to_numpy(float)
    ok_cs = np.isfinite(cs) & (w > 0)
    ok_ar = np.isfinite(ar) & (w > 0)
    out = {
        "roll_bps": roll_spread(ret, g["ret_prev"].to_numpy(float), w) * 1e4,
        "hl_bps": (float(np.sum(w[np.isfinite(hl)] * hl[np.isfinite(hl)]) / np.sum(w[np.isfinite(hl)])) * 1e4
                   if np.sum(w[np.isfinite(hl)]) > 0 else float("nan")),
        "cs_bps": (float(np.sum(w[ok_cs] * cs[ok_cs]) / np.sum(w[ok_cs])) * 1e4
                   if ok_cs.sum() >= MIN_PAIRS else float("nan")),
        "vol_bps": vol * 1e4,
        "volumen_mediano_vela": weighted_median(g["volume_obs"].to_numpy(float),
                                                None if weights is None else w),
        "frac_velas_con_transaccion": float(np.sum(w * (~g["is_imputed"].to_numpy())) / np.sum(w))
        if np.sum(w) > 0 else float("nan"),
        "n_velas_obs": int((~g["is_imputed"]).sum()),
        "n_retornos": int(np.isfinite(ret).sum()),
        "n_pares": int(np.isfinite(cs).sum()),
    }
    if ok_ar.sum() >= MIN_PAIRS:
        p, wa = ar[ok_ar], w[ok_ar]
        if ar_method == "moment":
            out["ar_bps"] = float(np.sqrt(max(4.0 * np.sum(wa * p) / np.sum(wa), 0.0))) * 1e4
        else:
            out["ar_bps"] = float(np.sum(wa * np.sqrt(np.maximum(4.0 * p, 0.0))) / np.sum(wa)) * 1e4
    else:
        out["ar_bps"] = float("nan")
    for est in ESTIMADORES:
        s = out[f"{est}_bps"]
        out[f"{est}_sobre_vol"] = float(s / out["vol_bps"]) if np.isfinite(s) and out["vol_bps"] > 0 else float("nan")
    return out


def metrics_by_group(prepared: pd.DataFrame, group_col: str, groups: Sequence[str],
                     ar_method: str = "moment") -> Dict[str, Dict[str, float]]:
    return {grp: group_metrics(prepared[prepared[group_col] == grp], ar_method=ar_method)
            for grp in groups}


def bootstrap_tramo_diffs(prepared: pd.DataFrame, n_boot: int = 500, seed: int = 42,
                          metrics: Sequence[str] = ("roll_bps", "hl_bps", "cs_bps", "ar_bps",
                                                    "vol_bps", "volumen_mediano_vela"),
                          ) -> Dict[str, Dict[str, Dict[str, float]]]:
    """Bootstrap por dias (remuestreo de dias completos con reemplazo, que
    conserva la dependencia intradiaria) de las diferencias
    media_jornada - apertura y media_jornada - cierre. Devuelve la
    estimacion puntual y el IC 95 % percentil."""
    days = np.array(sorted(prepared["day"].unique()))
    day_idx = pd.Index(days).get_indexer(prepared["day"])
    rng = np.random.default_rng(seed)
    groups = {t: prepared["tramo"].to_numpy() == t for t in TRAMO_NAMES}
    draws = {m: {"media_menos_apertura": [], "media_menos_cierre": []} for m in metrics}

    def diffs(row_w):
        vals = {t: group_metrics(prepared[groups[t]], weights=row_w[groups[t]]) for t in TRAMO_NAMES}
        return {m: (vals["media_jornada"][m] - vals["apertura"][m],
                    vals["media_jornada"][m] - vals["cierre"][m]) for m in metrics}

    point = diffs(np.ones(len(prepared)))
    for _ in range(n_boot):
        counts = np.bincount(rng.integers(0, len(days), len(days)), minlength=len(days))
        d = diffs(counts[day_idx].astype(float))
        for m in metrics:
            draws[m]["media_menos_apertura"].append(d[m][0])
            draws[m]["media_menos_cierre"].append(d[m][1])
    out = {}
    for m in metrics:
        out[m] = {}
        for i, k in enumerate(("media_menos_apertura", "media_menos_cierre")):
            arr = np.asarray(draws[m][k], float)
            arr = arr[np.isfinite(arr)]
            out[m][k] = {
                "estimacion": point[m][i],
                "ic95": [float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5))] if len(arr) else None,
                "n_boot_validos": int(len(arr)),
            }
    return out


# ---------------------------------------------------------------------------
# 4) Analisis de un snapshot y veredicto
# ---------------------------------------------------------------------------

def _median_across(per_ticker: Dict[str, Dict[str, Dict[str, float]]], tickers: Sequence[str],
                   groups: Sequence[str]) -> Dict[str, Dict[str, float]]:
    out = {}
    for grp in groups:
        out[grp] = {}
        for m in METRICAS:
            vals = [per_ticker[t][grp][m] for t in tickers if t in per_ticker]
            vals = [v for v in vals if v is not None and np.isfinite(v)]
            out[grp][m] = float(np.median(vals)) if vals else float("nan")
            out[grp][f"{m}_n_tickers"] = len(vals)
    return out


def analyze_snapshot(snapshot: str, data_dir: "str | Path" = DEFAULT_DATA_DIR,
                     date_from: Optional[date] = None, label: Optional[str] = None,
                     n_boot: int = 500, seed: int = 42) -> Dict:
    """Metricas por ticker x tramo, perfil de 30 min (FALABELLA y mediana de
    tier A) y bootstrap de FALABELLA para un snapshot (opcionalmente
    restringido a dias >= date_from)."""
    snap = snapshot_dir(snapshot, data_dir)
    tiers = read_tiers(snap)
    tickers = list_tickers(snap)
    bars = {t: load_bars(t, snap) for t in tickers}
    short = detect_short_sessions(bars)
    all_days = sorted(set().union(*[set(b["day"]) for b in bars.values()]))
    used_days = [d for d in all_days if d not in set(short) and (date_from is None or d >= date_from)]

    tramo_m, bloque_m = {}, {}
    prepared_fal = None
    for t in tickers:
        p_tr = prepare(bars[t], "tramo", short, date_from)
        tramo_m[t] = metrics_by_group(p_tr, "tramo", TRAMO_NAMES)
        if t == FALABELLA:
            prepared_fal = p_tr
        p_bl = prepare(bars[t], "bloque", short, date_from)
        bloque_m[t] = metrics_by_group(p_bl, "bloque", BLOQUES_30M)

    tier_a = [t for t in tickers if tiers.get(t) == "A"]
    result = {
        "snapshot": snapshot,
        "label": label or snapshot,
        "date_from": date_from.isoformat() if date_from else None,
        "rango_fechas": [used_days[0].isoformat(), used_days[-1].isoformat()] if used_days else None,
        "n_dias": len(used_days),
        "dias_sesion_corta_excluidos": [d.isoformat() for d in short],
        "tickers": tickers,
        "tier_A": tier_a,
        "por_ticker_tramo": tramo_m,
        "perfil_30m": {
            "FALABELLA": bloque_m.get(FALABELLA),
            "mediana_tier_A": _median_across(bloque_m, tier_a, BLOQUES_30M),
        },
        "mediana_tramo": {
            "todos": _median_across(tramo_m, tickers, TRAMO_NAMES),
            "tier_A": _median_across(tramo_m, tier_a, TRAMO_NAMES),
        },
    }
    if prepared_fal is not None and n_boot > 0:
        result["bootstrap_FALABELLA"] = bootstrap_tramo_diffs(prepared_fal, n_boot=n_boot, seed=seed)
    result["veredicto"] = verdict(tramo_m, tickers, tier_a)
    return result


def _count(per_ticker, tickers, metric, cond) -> Dict:
    ok, valid = [], []
    for t in tickers:
        vals = {tr: per_ticker[t][tr][metric] for tr in TRAMO_NAMES}
        if not all(v is not None and np.isfinite(v) for v in vals.values()):
            continue
        valid.append(t)
        if cond(vals):
            ok.append(t)
    return {"n_cumple": len(ok), "n_validos": len(valid), "tickers": ok}


def _argcount(per_ticker, tickers, metric, fn) -> Dict[str, int]:
    out = {tr: 0 for tr in TRAMO_NAMES}
    for t in tickers:
        vals = {tr: per_ticker[t][tr][metric] for tr in TRAMO_NAMES}
        if all(v is not None and np.isfinite(v) for v in vals.values()):
            out[fn(vals, key=vals.get)] += 1
    return out


def verdict(per_ticker: Dict, tickers: Sequence[str], tier_a: Sequence[str]) -> Dict:
    """Cuenta tickers que cumplen 'media jornada mayor spread' (estricto: mayor
    que apertura Y que cierre) y 'media jornada menor actividad', mas el
    tramo en que cae el maximo/minimo de cada metrica."""
    mayor = lambda v: v["media_jornada"] > v["apertura"] and v["media_jornada"] > v["cierre"]
    menor = lambda v: v["media_jornada"] < v["apertura"] and v["media_jornada"] < v["cierre"]
    out = {"spread": {}, "spread_sobre_volatilidad": {}, "actividad": {}, "volatilidad": {}}
    for est in ESTIMADORES:
        for key, metric in (("spread", f"{est}_bps"), ("spread_sobre_volatilidad", f"{est}_sobre_vol")):
            out[key][est] = {
                "media_jornada_mayor": {"todos": _count(per_ticker, tickers, metric, mayor),
                                        "tier_A": _count(per_ticker, tier_a, metric, mayor)},
                "tramo_con_maximo": {"todos": _argcount(per_ticker, tickers, metric, max),
                                     "tier_A": _argcount(per_ticker, tier_a, metric, max)},
            }
    for metric in ("volumen_mediano_vela", "frac_velas_con_transaccion"):
        out["actividad"][metric] = {
            "media_jornada_menor": {"todos": _count(per_ticker, tickers, metric, menor),
                                    "tier_A": _count(per_ticker, tier_a, metric, menor)},
            "tramo_con_minimo": {"todos": _argcount(per_ticker, tickers, metric, min),
                                 "tier_A": _argcount(per_ticker, tier_a, metric, min)},
        }
    out["volatilidad"]["vol_bps"] = {
        "tramo_con_maximo": {"todos": _argcount(per_ticker, tickers, "vol_bps", max),
                             "tier_A": _argcount(per_ticker, tier_a, "vol_bps", max)},
    }
    return out


# ---------------------------------------------------------------------------
# 5) Salidas
# ---------------------------------------------------------------------------

def _json_safe(obj):
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, (np.floating, float)):
        return None if not np.isfinite(obj) else float(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    return obj


def build_payload(analyses: Sequence[Dict]) -> Dict:
    tabla = []
    for a in analyses:
        v = a["veredicto"]
        for est in ESTIMADORES:
            s = v["spread"][est]["media_jornada_mayor"]
            r = v["spread_sobre_volatilidad"][est]["media_jornada_mayor"]
            tabla.append({
                "snapshot": a["label"], "estimador": est,
                "media_mayor_spread_todos": f"{s['todos']['n_cumple']}/{s['todos']['n_validos']}",
                "media_mayor_spread_tierA": f"{s['tier_A']['n_cumple']}/{s['tier_A']['n_validos']}",
                "tramo_max_spread_tierA": v["spread"][est]["tramo_con_maximo"]["tier_A"],
                "media_mayor_spread_sobre_vol_tierA": f"{r['tier_A']['n_cumple']}/{r['tier_A']['n_validos']}",
            })
    return {
        "metadata": {
            "tarea": "2.1.3b - Robustez del patron intradiario de spread y actividad",
            "autor": "Benjamin Farias (BF)",
            "fecha_generacion": datetime.now(timezone.utc).isoformat(),
            "tramos": {n: [s, e] for n, s, e in mp.TRAMOS_EJECUTOR},
            "bloques_30m": list(BLOQUES_30M),
            "exclusiones": [
                "velas con is_imputed=True",
                f"vela {mp.CLOSING_AUCTION_BAR} (subasta de cierre)",
                "dias de sesion corta (< 50% de tickers con transacciones despues de las 14:00)",
            ],
            "estimadores": {k: ESTIMADOR_LABEL[k] for k in ESTIMADORES},
            "unidades": {"*_bps": "puntos base (spread relativo x 1e4)",
                         "vol_bps": "desv. estandar del retorno log de 5 min, bps",
                         "*_sobre_vol": "spread_bps / vol_bps",
                         "volumen_mediano_vela": "acciones, mediana de velas observadas"},
            "criterios": {
                "media_jornada_mayor": "metrica(media_jornada) > metrica(apertura) y > metrica(cierre)",
                "media_jornada_menor": "metrica(media_jornada) < metrica(apertura) y < metrica(cierre)",
                "n_validos": "tickers con la metrica finita en los 3 tramos (Roll es NaN si la autocovarianza >= 0)",
            },
            "limitacion": "Sin Nivel 2: los cuatro estimadores son proxies de spread desde OHLC de 5 min (yfinance).",
        },
        "tabla_resumen": tabla,
        "snapshots": {a["label"]: a for a in analyses},
    }


def plot_profiles(analyses: Sequence[Dict], who: str, output_file: "str | Path") -> Path:
    """Perfil de 30 min (small multiples) de FALABELLA o de la mediana tier A,
    un color por snapshot (orden categorico fijo)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = ["#2a78d6", "#eb6834", "#1baf7a"]       # slots 1-3 de la paleta categorica
    styles = ["-", "-", "--"]
    markers = ["o", "s", "^"]
    ink, ink2, grid, surface = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
    panels = [("roll_bps", "Roll (bps)"), ("hl_bps", "Rango HL (bps)"),
              ("cs_bps", "Corwin-Schultz (bps)"), ("ar_bps", "Abdi-Ranaldo (bps)"),
              ("vol_bps", "Volatilidad 5 min (bps)"), ("cs_sobre_vol", "Corwin-Schultz / volatilidad"),
              ("ar_sobre_vol", "Abdi-Ranaldo / volatilidad"),
              ("volumen_mediano_vela", "Volumen mediano por vela (acc.)")]
    key = "FALABELLA" if who == "FALABELLA" else "mediana_tier_A"
    plt.rcParams.update({"axes.edgecolor": grid, "axes.labelcolor": ink2, "xtick.color": ink2,
                         "ytick.color": ink2, "axes.titlecolor": ink, "font.size": 8.5})
    fig, axes = plt.subplots(2, 4, figsize=(15, 7.2), facecolor=surface)
    x = np.arange(N_BLOCKS)
    # Bandas de tramo: media jornada = bloques 11:30..13:30 (indices 4-8)
    for ax, (metric, title) in zip(axes.flat, panels):
        ax.set_facecolor(surface)
        ax.axvspan(3.5, 8.5, color="#efeee9", zorder=0, linewidth=0)
        ax.grid(axis="y", color=grid, linewidth=0.6)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for i, a in enumerate(analyses):
            prof = a["perfil_30m"][key]
            if prof is None:
                continue
            y = [prof[b][metric] for b in BLOQUES_30M]
            y = [np.nan if v is None else v for v in y]
            ax.plot(x, y, styles[i], color=colors[i], linewidth=2, marker=markers[i], markersize=4.5,
                    markeredgecolor=surface, markeredgewidth=1, label=a["label"], zorder=3)
        ax.set_title(title, loc="left", fontsize=9.5)
        ax.set_xticks(x[::2], [BLOQUES_30M[j] for j in range(0, N_BLOCKS, 2)])
        ax.margins(y=0.15)
    handles, labels = axes[0][0].get_legend_handles_labels()
    from matplotlib.patches import Patch
    handles.append(Patch(facecolor="#efeee9", edgecolor="none"))
    labels.append("media jornada (11:30-14:00)")
    fig.legend(handles, labels, loc="upper left", bbox_to_anchor=(0.005, 0.955), ncol=len(labels),
               frameon=False, fontsize=8.5)
    name = "FALABELLA" if who == "FALABELLA" else "Mediana de tickers tier A"
    fig.suptitle(f"{name}: perfil intradiario por bloques de 30 min (eje x = inicio del bloque). "
                 "Velas imputadas, subasta 15:55 y sesiones cortas excluidas; sin Nivel 2.",
                 x=0.01, y=0.995, ha="left", fontsize=10.5, color=ink)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=130, facecolor=surface)
    plt.close(fig)
    return output_file


def main(argv: Optional[Sequence[str]] = None) -> Dict:
    parser = argparse.ArgumentParser(description="Robustez del patron intradiario (2.1.3b, Parte A).")
    parser.add_argument("--snapshots", nargs="+", default=["2026-08-23"])
    parser.add_argument("--post-msci-from", default=None,
                        help="Fecha YYYY-MM-DD: agrega, para el ULTIMO snapshot, una variante restringida a dias >= fecha.")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--plot-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--n-boot", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)

    analyses = [analyze_snapshot(s, args.data_dir, n_boot=args.n_boot, seed=args.seed)
                for s in args.snapshots]
    if args.post_msci_from:
        d0 = date.fromisoformat(args.post_msci_from)
        last = args.snapshots[-1]
        analyses.append(analyze_snapshot(last, args.data_dir, date_from=d0,
                                         label=f"{last} (desde {d0.isoformat()})",
                                         n_boot=args.n_boot, seed=args.seed))
    payload = _json_safe(build_payload(analyses))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"JSON -> {args.output}")
    for who, fname in (("FALABELLA", "FALABELLA_perfil_30min.png"), ("tier_A", "tierA_perfil_30min.png")):
        print(f"PNG  -> {plot_profiles(payload['snapshots'].values(), who, args.plot_dir / fname)}")
    for row in payload["tabla_resumen"]:
        print(row)
    return payload


if __name__ == "__main__":
    main()
