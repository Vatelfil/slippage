"""Momentos del mercado de fondo de RMSC04 por tramo -- tarea 2.2.4 (BF).

Dos capas:

1. Logica pura (sin ABIDES, testeable con series sinteticas): a partir de
   las cotizaciones L1 (mejor bid / mejor ask con timestamp) y de las
   transacciones, calcula por tramo del Ejecutor (`TRAMOS_EJECUTOR`) la
   volatilidad de 5 min, el spread cotizado mediano y medio, la
   participacion de volumen, el volumen mediano por vela, la curtosis y los
   retornos de 5 min (para el KS de `scripts/colab/rmsc04_validate.py`).

2. `run_rmsc04()`: corre RMSC04 sin nuestro agente e importa ABIDES dentro
   de la funcion (solo corre en Colab / Docker).

Convenciones, alineadas con los datos reales de la 2.1.3:
    - Los timestamps de ABIDES son nanosegundos; la hora del dia es
      `t mod 86400e9`.
    - Una "vela" que empieza en s tiene retorno ln(mid(s + 5 min) / mid(s)) y
      pertenece al tramo de s. Se excluyen la vela 09:30 (en los datos reales
      su retorno necesita la vela anterior, que no existe) y la vela 15:55
      (subasta de cierre, `INCLUDE_CLOSING_AUCTION = False`). Quedan 23 / 30 /
      23 retornos por dia, igual que en los datos reales.
    - El volumen de la vela 15:55 tampoco entra en la participacion.
    - Spread cotizado relativo: (ask - bid) / mid, muestreado en una grilla
      regular (por defecto 1 s) con la ultima cotizacion vigente; es una
      media/mediana ponderada por tiempo, no por evento.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence

import numpy as np

from src.config.market_params import (
    BAR_MINUTES,
    CLOSING_AUCTION_BAR,
    INCLUDE_CLOSING_AUCTION,
    TRAMOS_EJECUTOR,
)

NS_POR_SEGUNDO = 10 ** 9
NS_POR_DIA = 86_400 * NS_POR_SEGUNDO
ABIDES_SYMBOL = "ABM"  # simbolo por defecto de rmsc04 y el unico que usa ABIDES-Gym


def _hhmm_to_seconds(hhmm: str) -> int:
    h, m = hhmm.split(":")[:2]
    return int(h) * 3600 + int(m) * 60


TRAMO_NAMES = tuple(name for name, _, _ in TRAMOS_EJECUTOR)
TRAMO_BOUNDS_S = {name: (_hhmm_to_seconds(a), _hhmm_to_seconds(b)) for name, a, b in TRAMOS_EJECUTOR}
SESSION_START_S = TRAMO_BOUNDS_S[TRAMO_NAMES[0]][0]
SESSION_END_S = TRAMO_BOUNDS_S[TRAMO_NAMES[-1]][1]
BAR_S = BAR_MINUTES * 60
AUCTION_BAR_S = _hhmm_to_seconds(CLOSING_AUCTION_BAR)


# ---------------------------------------------------------------------------
# Helpers puros
# ---------------------------------------------------------------------------

def seconds_of_day(times_ns: Sequence) -> np.ndarray:
    """Hora del dia en segundos a partir de timestamps de ABIDES (ns)."""
    t = np.asarray(times_ns, dtype=np.int64)
    return (t % NS_POR_DIA) / float(NS_POR_SEGUNDO)


def _to_float(x: Sequence) -> np.ndarray:
    """Convierte a float; None (lado del libro vacio) pasa a NaN."""
    return np.array([np.nan if v is None else v for v in x], dtype=float)


def last_value_at(grid_s: np.ndarray, times_s: np.ndarray, values: np.ndarray) -> np.ndarray:
    """Valor del ultimo evento con tiempo <= cada punto de `grid_s` (NaN si
    todavia no hay ninguno). `times_s` debe venir ordenado."""
    idx = np.searchsorted(times_s, grid_s, side="right") - 1
    out = np.full(len(grid_s), np.nan)
    ok = idx >= 0
    out[ok] = values[idx[ok]]
    return out


def _ffill(values: np.ndarray) -> np.ndarray:
    """Rellena NaN con el ultimo valor valido anterior."""
    v = np.asarray(values, dtype=float)
    idx = np.where(np.isfinite(v), np.arange(len(v)), -1)
    idx = np.maximum.accumulate(idx)
    out = np.full(len(v), np.nan)
    out[idx >= 0] = v[idx[idx >= 0]]
    return out


def tramo_of_seconds(s: float) -> Optional[str]:
    for i, name in enumerate(TRAMO_NAMES):
        a, b = TRAMO_BOUNDS_S[name]
        if a <= s < b or (i == len(TRAMO_NAMES) - 1 and s == b):
            return name
    return None


def excess_kurtosis(x: Sequence[float]) -> float:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < 4 or x.std() == 0:
        return float("nan")
    z = (x - x.mean()) / x.std()
    return float(np.mean(z ** 4) - 3.0)


# ---------------------------------------------------------------------------
# (1) Momentos de una corrida
# ---------------------------------------------------------------------------

def moments_from_l1(times_ns: Sequence, best_bid: Sequence, best_ask: Sequence,
                    trade_times_ns: Sequence = (), trade_qty: Sequence = (),
                    end_s: int = SESSION_END_S, spread_sample_s: int = 1,
                    exclude_closing_auction: bool = not INCLUDE_CLOSING_AUCTION) -> Dict[str, Dict]:
    """Momentos por tramo de UNA corrida (un dia simulado).

    Args:
        times_ns, best_bid, best_ask: una fila por actualizacion del libro;
            `best_bid` / `best_ask` pueden traer None o NaN si el lado esta vacio.
        trade_times_ns, trade_qty: transacciones (tiempo en ns, acciones).
        end_s: hora (segundos del dia) hasta la que se simulo. Los tramos que
            terminan despues quedan con `completo = False` y sin momentos.

    Returns:
        {tramo: {completo, retornos_5min, n_retornos, volatilidad_bps,
                 curtosis, spread_mediano_bps, spread_medio_bps,
                 n_muestras_spread, volumen, volumen_mediano_vela, n_velas,
                 participacion_volumen}}.
        `participacion_volumen` solo se calcula si la corrida cubre toda la
        sesion (si no, es None).
    """
    t = seconds_of_day(times_ns)
    order = np.argsort(t, kind="stable")
    t = t[order]
    bid = _to_float(best_bid)[order]
    ask = _to_float(best_ask)[order]
    both = np.isfinite(bid) & np.isfinite(ask)
    mid_ff = _ffill(np.where(both, (bid + ask) / 2.0, np.nan))

    tt = seconds_of_day(trade_times_ns) if len(trade_times_ns) else np.array([], dtype=float)
    tq = np.asarray(trade_qty, dtype=float) if len(trade_qty) else np.array([], dtype=float)

    out: Dict[str, Dict] = {}
    for name in TRAMO_NAMES:
        a, b = TRAMO_BOUNDS_S[name]
        completo = b <= end_s
        r: Dict = {"completo": bool(completo)}
        if not completo:
            out[name] = r
            continue

        # velas del tramo (inicio s): se excluyen 09:30 y, por defecto, 15:55
        starts = np.arange(a, b, BAR_S)
        starts = starts[starts != SESSION_START_S]
        vol_starts = np.arange(a, b, BAR_S)
        if exclude_closing_auction:
            starts = starts[starts != AUCTION_BAR_S]
            vol_starts = vol_starts[vol_starts != AUCTION_BAR_S]
        m0 = last_value_at(starts.astype(float), t, mid_ff)
        m1 = last_value_at((starts + BAR_S).astype(float), t, mid_ff)
        ok = np.isfinite(m0) & np.isfinite(m1) & (m0 > 0) & (m1 > 0)
        rets = np.log(m1[ok] / m0[ok])

        # spread cotizado, ponderado por tiempo
        fin_spread = AUCTION_BAR_S if (exclude_closing_auction and a <= AUCTION_BAR_S < b) else b
        grid = np.arange(a, fin_spread, spread_sample_s, dtype=float)
        gb, ga = last_value_at(grid, t, bid), last_value_at(grid, t, ask)
        okq = np.isfinite(gb) & np.isfinite(ga) & (ga > gb)
        spr = (ga[okq] - gb[okq]) / ((ga[okq] + gb[okq]) / 2.0) * 1e4

        # volumen por vela
        bar_vol = np.array([tq[(tt >= s) & (tt < s + BAR_S)].sum() for s in vol_starts]) \
            if len(tq) else np.zeros(len(vol_starts))

        r.update({
            "retornos_5min": rets.tolist(),
            "n_retornos": int(len(rets)),
            "volatilidad_bps": float(rets.std() * 1e4) if len(rets) > 1 else float("nan"),
            "curtosis": excess_kurtosis(rets),
            "spread_mediano_bps": float(np.median(spr)) if len(spr) else float("nan"),
            "spread_medio_bps": float(np.mean(spr)) if len(spr) else float("nan"),
            "n_muestras_spread": int(len(spr)),
            "volumen": float(bar_vol.sum()),
            "volumen_mediano_vela": float(np.median(bar_vol)) if len(bar_vol) else float("nan"),
            "n_velas": int(len(bar_vol)),
            "participacion_volumen": None,
        })
        out[name] = r

    if all(out[n]["completo"] for n in TRAMO_NAMES):
        total = sum(out[n]["volumen"] for n in TRAMO_NAMES)
        for n in TRAMO_NAMES:
            out[n]["participacion_volumen"] = float(out[n]["volumen"] / total) if total > 0 else float("nan")
    return out


def pool_moments(runs: Sequence[Dict[str, Dict]]) -> Dict[str, Dict]:
    """Agrega varias corridas (semillas) por tramo.

    - volatilidad y curtosis: sobre los retornos de todas las semillas juntos
      (misma definicion que el objetivo real, que junta todos los dias);
    - spread mediano / medio y volumen mediano por vela: media entre semillas;
    - participacion de volumen: mediana entre semillas (el objetivo real es
      la mediana de las participaciones diarias).
    Las corridas en que el tramo no esta completo se ignoran.
    """
    out: Dict[str, Dict] = {}
    for name in TRAMO_NAMES:
        rs = [r[name] for r in runs if name in r and r[name].get("completo")]
        if not rs:
            out[name] = {"n_corridas": 0}
            continue
        rets = np.concatenate([np.asarray(r["retornos_5min"], dtype=float) for r in rs])
        part = [r["participacion_volumen"] for r in rs if r.get("participacion_volumen") is not None]

        def _mean(key: str) -> float:
            v = np.array([r[key] for r in rs], dtype=float)
            v = v[np.isfinite(v)]
            return float(v.mean()) if len(v) else float("nan")

        out[name] = {
            "n_corridas": len(rs),
            "n_retornos": int(len(rets)),
            "retornos_5min": rets.tolist(),
            "volatilidad_bps": float(rets.std() * 1e4) if len(rets) > 1 else float("nan"),
            "curtosis": excess_kurtosis(rets),
            "spread_mediano_bps": _mean("spread_mediano_bps"),
            "spread_medio_bps": _mean("spread_medio_bps"),
            "volumen_mediano_vela": _mean("volumen_mediano_vela"),
            "participacion_volumen": float(np.median(part)) if part else None,
        }
    return out


def strip_returns(moments: Dict[str, Dict]) -> Dict[str, Dict]:
    """Copia de los momentos sin la lista de retornos (para JSON livianos)."""
    return {t: {k: v for k, v in m.items() if k != "retornos_5min"} for t, m in moments.items()}


def ranking(moments: Dict[str, Dict], key: str) -> Optional[List[str]]:
    """Tramos ordenados de mayor a menor segun `key` (None si falta alguno),
    igual que `ranking_observado` de `objetivos_validacion`."""
    vals = {t: moments.get(t, {}).get(key) for t in TRAMO_NAMES}
    if any(v is None or not np.isfinite(v) for v in vals.values()):
        return None
    return sorted(TRAMO_NAMES, key=lambda t: -vals[t])


# ---------------------------------------------------------------------------
# (2) Corrida de RMSC04 (necesita ABIDES)
# ---------------------------------------------------------------------------

def run_rmsc04(cfg_kwargs: Dict, seed: int, end_time: str = "16:00:00") -> Dict[str, List]:
    """Corre RMSC04 sin agente de ejecucion y devuelve las series crudas.

    Args:
        cfg_kwargs: salida de `calibrate_rmsc04_ipsa.to_abides_kwargs()`.
        seed: semilla de la simulacion.
        end_time: hora de cierre de la simulacion (HH:MM:SS); sobrescribe el
            `end_time` de `cfg_kwargs`.

    Returns:
        dict con `times_ns`, `best_bid`, `best_ask`, `trade_times_ns`,
        `trade_qty` y `end_s`, listo para `moments_from_l1(**...)`.
    """
    from abides_core import abides  # import local: solo existe con ABIDES instalado
    from abides_markets.configs import rmsc04

    kwargs = dict(cfg_kwargs)
    kwargs.pop("seed", None)
    kwargs.pop("ticker", None)  # el libro se lee por ABIDES_SYMBOL
    kwargs["end_time"] = end_time
    kwargs.setdefault("stdout_log_level", "ERROR")
    kwargs.setdefault("log_orders", False)
    kwargs["book_logging"] = True
    config = rmsc04.build_config(seed=int(seed), **kwargs)
    end_state = abides.run(config)
    book = end_state["agents"][0].order_books[ABIDES_SYMBOL]

    l1 = book.get_L1_snapshots()
    bb, ba = l1["best_bids"], l1["best_asks"]
    trades = sorted(list(book.buy_transactions) + list(book.sell_transactions), key=lambda x: x[0])
    return {
        "times_ns": [int(row[0]) for row in bb],
        "best_bid": [row[1] for row in bb],
        "best_ask": [row[1] for row in ba],
        "trade_times_ns": [int(tr[0]) for tr in trades],
        "trade_qty": [float(tr[1]) for tr in trades],
        "end_s": _hhmm_to_seconds(end_time),
    }


def simulate_moments(cfg_kwargs: Dict, seed: int, end_time: str = "16:00:00") -> Dict[str, Dict]:
    """`run_rmsc04` + `moments_from_l1` para una semilla."""
    return moments_from_l1(**run_rmsc04(cfg_kwargs, seed, end_time))
