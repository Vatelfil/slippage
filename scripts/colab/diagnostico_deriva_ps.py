"""Diagnostico de las corridas 'desbocadas' del simulador (2.2.4, P4) -- corre en Colab con ABIDES.

Elaborado por PS con apoyo de Claude Code; pendiente de revision por BF.

Uso (despues de las celdas de preparacion del cuaderno):
    PYTHONPATH=. python scripts/colab/diagnostico_deriva_ps.py \n        --calibrated-json <p4>/rmsc04_ipsa_ECL_2026-08-23.json --out <drive>/diagnostico_deriva_ECL.json


Pregunta: por que algunas semillas mueven el precio 17-30 % en un tramo?
Mide, para unas pocas semillas, tres cosas y compara variantes de UN cambio cada una:
  1. cuanto se mueve el precio en el tramo (y si se pega a un tope),
  2. si se mueve el precio o el valor fundamental (oraculo),
  3. que tipo de agente termina con la posicion grande.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

from src.envs import rmsc04_sim_stats as ss
from src.envs.calibrate_rmsc04_ipsa import load_abides_kwargs
from src.experiments import validacion_runs as vr

DESBOCADA_PCT = 10.0  # |movimiento del tramo| mayor a esto = corrida desbocada


def correr(cfg, seed, end_time):
    from abides_core import abides
    from abides_markets.configs import rmsc04
    kw = dict(cfg)
    kw.pop("seed", None)
    kw.pop("ticker", None)
    kw["end_time"] = end_time
    kw.setdefault("stdout_log_level", "ERROR")
    kw.setdefault("log_orders", False)
    kw["book_logging"] = True
    config = rmsc04.build_config(seed=int(seed), **kw)
    end_state = abides.run(config)
    book = end_state["agents"][0].order_books[ss.ABIDES_SYMBOL]
    l1 = book.get_L1_snapshots()
    bb, ba = l1["best_bids"], l1["best_asks"]
    trades = sorted(list(book.buy_transactions) + list(book.sell_transactions), key=lambda x: x[0])
    serie = {
        "times_ns": [int(r[0]) for r in bb],
        "best_bid": [r[1] for r in bb],
        "best_ask": [r[1] for r in ba],
        "trade_times_ns": [int(t[0]) for t in trades],
        "trade_qty": [float(t[1]) for t in trades],
        "end_s": ss._hhmm_to_seconds(end_time),
    }
    return serie, end_state, config


def mid_ffill(serie):
    bb = np.array([np.nan if x is None else x for x in serie["best_bid"]], dtype=float)
    ba = np.array([np.nan if x is None else x for x in serie["best_ask"]], dtype=float)
    mid = (bb + ba) / 2.0
    idx = np.where(~np.isnan(mid), np.arange(len(mid)), 0)
    np.maximum.accumulate(idx, out=idx)
    return ss.seconds_of_day(serie["times_ns"]), mid[idx]


def valor_en(t_s, v, s):
    i = int(np.searchsorted(t_s, s, side="right")) - 1
    return float(v[i]) if i >= 0 else float("nan")


def fundamental(config):
    """(t_s, valor) del oraculo, o None si esta version de ABIDES no lo deja leer."""
    try:
        orc = config["custom_properties"]["oracle"]
        f = orc.f_log[ss.ABIDES_SYMBOL]
        ts, vs = [], []
        for e in f:
            t = e["FundamentalTime"] if isinstance(e, dict) else e[0]
            v = e["FundamentalValue"] if isinstance(e, dict) else e[1]
            ts.append(int(getattr(t, "value", t)))
            vs.append(float(v))
        return ss.seconds_of_day(ts), np.array(vs)
    except Exception:
        return None


def posiciones(end_state):
    out = {}
    for a in end_state["agents"]:
        h = getattr(a, "holdings", None)
        if not isinstance(h, dict):
            continue
        q = h.get(ss.ABIDES_SYMBOL, 0)
        d = out.setdefault(type(a).__name__, {"n": 0, "neto": 0, "abs": 0})
        d["n"] += 1
        d["neto"] += int(q)
        d["abs"] += abs(int(q))
    return out


def medir(cfg, seed, tramo):
    t0 = time.time()
    serie, end_state, config = correr(cfg, seed, vr.TRAMO_END_TIME[tramo])
    seg = time.time() - t0
    a, b = ss.TRAMO_BOUNDS_S[tramo]
    t_s, mid = mid_ffill(serie)
    p0, p1 = valor_en(t_s, mid, a), valor_en(t_s, mid, b)
    ventana = (t_s >= a) & (t_s <= b)
    mov = 100.0 * (p1 / p0 - 1.0)
    rec = {
        "segundos": round(seg, 1), "mid_ini": p0, "mid_fin": p1, "mov_pct": round(mov, 2),
        "mid_min_pct": round(100 * (np.nanmin(mid[ventana]) / p0 - 1), 2) if ventana.any() else None,
        "mid_max_pct": round(100 * (np.nanmax(mid[ventana]) / p0 - 1), 2) if ventana.any() else None,
        "n_actualizaciones_libro": int(ventana.sum()),
        "trayectoria_mid_pct": [round(100 * (valor_en(t_s, mid, s) / p0 - 1), 1) for s in np.linspace(a, b, 7)],
        "posiciones": posiciones(end_state),
    }
    m = ss.moments_from_l1(**serie)[tramo]
    r = np.array(m["retornos_5min"]) * 1e4
    rec.update({"std_5min_bps": round(float(r.std()), 1), "mediana_abs_bps": round(float(np.median(np.abs(r))), 1),
                "pct_retornos_cero": round(100 * float(np.mean(r == 0)), 1), "volumen": m["volumen"]})
    fu = fundamental(config)
    if fu is not None:
        f_s, f_v = fu
        f0, f1 = valor_en(f_s, f_v, a), valor_en(f_s, f_v, b)
        rec["oraculo_mov_pct"] = round(100 * (f1 / f0 - 1.0), 2)
        rec["trayectoria_oraculo_pct"] = [round(100 * (valor_en(f_s, f_v, s) / f0 - 1), 1) for s in np.linspace(a, b, 7)]
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--calibrated-json", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tramo", default="media_jornada")
    ap.add_argument("--seeds", default="213,206,209,203,215")  # 1 tranquila, 2 que suben, 2 que caen
    ap.add_argument("--max-minutes", type=float, default=40.0)
    args = ap.parse_args()

    cfg = load_abides_kwargs(args.calibrated_json)[args.tramo]
    # Cada variante cambia UNA sola cosa respecto de 'control' (la calibracion actual).
    # FALABELLA, que no se desboca, usa mm_pov=0.005 y ventana 'adaptive'.
    variantes = {
        "control": {},
        "mm_pov_bajo": {"mm_pov": 0.005},
        "mm_ventana_adaptive": {"mm_window_size": "adaptive"},
        "sin_momentum": {"num_momentum_agents": 0},
        "oraculo_quieto": {"fund_vol": cfg["fund_vol"] * 0.1},
    }
    seeds = [int(s) for s in args.seeds.split(",")]
    out = Path(args.out)
    est = json.loads(out.read_text()) if out.exists() else {}
    t_ini = time.time()
    for vn, cambio in variantes.items():
        for s in seeds:
            clave = f"{vn}|{s}"
            if clave in est and "error" not in est[clave]:
                continue
            if time.time() - t_ini > args.max_minutes * 60:
                print("Presupuesto de tiempo agotado; volver a ejecutar para continuar.")
                break
            try:
                est[clave] = medir({**cfg, **cambio}, s, args.tramo)
            except Exception as e:
                est[clave] = {"error": f"{type(e).__name__}: {e}"}
            out.write_text(json.dumps(est, indent=1))
            r = est[clave]
            print(clave, "ERROR " + r["error"] if "error" in r else
                  f"{r['segundos']}s mov={r['mov_pct']}%")

    print("\n=== RESULTADO (tramo %s) ===" % args.tramo)
    print("variante         seed  seg  mov_tramo%  oraculo%  std5m  medAbs  %cero  tray_precio%")
    for vn in variantes:
        for s in seeds:
            r = est.get(f"{vn}|{s}")
            if not r or "error" in r:
                print(f"{vn:15s} {s:5d}  ", (r or {}).get("error", "sin correr"))
                continue
            print(f"{vn:15s} {s:5d} {r['segundos']:4.0f} {r['mov_pct']:9.1f} {r.get('oraculo_mov_pct', float('nan')):9.1f}"
                  f" {r['std_5min_bps']:6.1f} {r['mediana_abs_bps']:6.1f} {r['pct_retornos_cero']:6.1f}  {r['trayectoria_mid_pct']}")
    print("\n=== DESBOCADAS (|mov| > %.0f%%) POR VARIANTE ===" % DESBOCADA_PCT)
    for vn in variantes:
        rs = [est[f"{vn}|{s}"] for s in seeds if f"{vn}|{s}" in est and "error" not in est[f"{vn}|{s}"]]
        n = sum(1 for r in rs if abs(r["mov_pct"]) > DESBOCADA_PCT)
        print(f"{vn:15s} {n} de {len(rs)}")
    print("\n=== POSICION FINAL POR TIPO DE AGENTE (neto / absoluto), semillas desbocadas de 'control' ===")
    for s in seeds:
        r = est.get(f"control|{s}")
        if r and "error" not in r and abs(r["mov_pct"]) > DESBOCADA_PCT:
            print(f"seed {s} (mov {r['mov_pct']}%):",
                  {k: (v["n"], v["neto"], v["abs"]) for k, v in r["posiciones"].items()})
    print("\nTiempo total: %.1f min" % ((time.time() - t_ini) / 60))


if __name__ == "__main__":
    main()
