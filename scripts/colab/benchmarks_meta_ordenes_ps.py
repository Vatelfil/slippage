"""Benchmarks TWAP y VWAP sobre las meta-ordenes oficiales (tarea 2.3.4) -- Colab.

Elaborado por PS con apoyo de Claude Code; pendiente de revision por BF y MR.

Lee `data/meta_ordenes/meta_ordenes_v1.json` (2.3.3, BF): lista de objetos con
`id`, `ticker`, `tramo_inicio` ("apertura" | "media_jornada" | "cierre"),
`cantidad` y, opcional, `semilla`. Para cada orden corre TWAP y VWAP (la orden
se reparte desde su tramo de inicio hasta el cierre, con la politica ingenua de
mercado) y guarda el IS por corrida.

Entornos:
  --entorno abides   ABIDES con la config calibrada de cada activo
                     (data/calibration/rmsc04_ipsa_<ACTIVO>_<snapshot>.json); requiere Colab.
  --entorno poisson  simulador de Poisson (plan B, corre local).

Es reanudable: guarda tras cada corrida. Ejemplo (Colab):
    PYTHONPATH=. python scripts/colab/benchmarks_meta_ordenes_ps.py \
        --entorno abides --seeds 2 --out-dir <carpeta_de_drive> --max-minutes 180

Una jornada completa en ABIDES (13 periodos) tarda ~8 min; 10 ordenes x 2
estrategias x 2 semillas = 40 jornadas = ~5-6 h (repartir en 2 cuadernos con
`--ordenes` distintas).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.analysis.benchmarks import periodo_inicio, run_benchmark_episode, schedule_desde  # noqa: E402
from src.analysis.execution_metrics import evaluate_episode  # noqa: E402
from src.envs.rmsc04_search import load_resumable, save_json  # noqa: E402

ESTRATEGIAS = ("TWAP", "VWAP")


def pendientes(estado: Dict, ordenes: Sequence[Dict], seeds: Sequence[int]) -> List[tuple]:
    hechas = estado.get("corridas", {})
    return [(o["id"], e, s) for s in seeds for o in ordenes for e in ESTRATEGIAS
            if f"{o['id']}|{e}|{s}" not in hechas]


def correr(ordenes: Sequence[Dict], seeds: Sequence[int], estado: Dict, guardar: Callable[[Dict], None],
           factory_por_ticker: Callable[[str], Optional[Callable]], volume_profile=None,
           presupuesto_s: Optional[float] = None, log: Callable[[str], None] = print) -> bool:
    """Corre lo pendiente. Devuelve True si no queda nada."""
    t_ini = time.time()
    corridas = estado.setdefault("corridas", {})
    por_id = {o["id"]: o for o in ordenes}
    for oid, estrategia, seed in pendientes(estado, ordenes, seeds):
        if presupuesto_s is not None and time.time() - t_ini > presupuesto_s:
            log("Presupuesto de tiempo agotado: volver a ejecutar para continuar.")
            return False
        o = por_id[oid]
        sched = schedule_desde(estrategia, float(o["cantidad"]), periodo_inicio(o["tramo_inicio"]), volume_profile)
        t0 = time.time()
        clave = f"{oid}|{estrategia}|{seed}"
        try:
            r = run_benchmark_episode(sched, seed=int(seed) + int(o.get("semilla", 0)), ticker=o["ticker"],
                                      env_factory=factory_por_ticker(o["ticker"]))
            m = evaluate_episode(q_total=r.q_total, q_executed=r.q_executed, p_referencia=r.p_referencia,
                                 p_promedio_ejecutado=r.p_promedio_ejecutado)
            corridas[clave] = {"orden": oid, "estrategia": estrategia, "seed": int(seed), "ticker": o["ticker"],
                               "tramo_inicio": o["tramo_inicio"], "cantidad": o["cantidad"],
                               "segundos": round(time.time() - t0, 1), **{k: _num(v) for k, v in m.items()}}
            log(f"{clave}: IS={corridas[clave].get('IS_total')} cumpl={corridas[clave].get('pct_cumplimiento')} ({time.time() - t0:.0f}s)")
        except Exception as e:  # una corrida fallida no tumba la sesion
            corridas[clave] = {"orden": oid, "estrategia": estrategia, "seed": int(seed), "error": f"{type(e).__name__}: {e}"}
            log(f"{clave}: ERROR {corridas[clave]['error']}")
        guardar(estado)
    return True


def _num(v):
    return float(v) if isinstance(v, (int, float, np.floating, np.integer)) else v


def resumen(estado: Dict) -> Dict:
    """IS medio y error estandar por orden y estrategia (sobre las semillas)."""
    out: Dict = {}
    for c in estado.get("corridas", {}).values():
        if "error" in c or c.get("IS_total") is None:
            continue
        out.setdefault(c["orden"], {}).setdefault(c["estrategia"], []).append(c["IS_total"])
    res = {}
    for oid, d in out.items():
        res[oid] = {}
        for e, v in d.items():
            v = np.asarray(v, dtype=float)
            res[oid][e] = {"n": int(len(v)), "IS_medio": float(v.mean()),
                           "EE": float(v.std(ddof=1) / np.sqrt(len(v))) if len(v) > 1 else None}
    return res


def main(argv: Optional[Sequence[str]] = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--meta-ordenes", default=str(REPO_ROOT / "data/meta_ordenes/meta_ordenes_v1.json"))
    ap.add_argument("--entorno", choices=["abides", "poisson"], default="abides")
    ap.add_argument("--snapshot", default="2026-08-23")
    ap.add_argument("--calibrated-dir", default=str(REPO_ROOT / "data/calibration"))
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--ordenes", nargs="*", default=None, help="ids a correr (para repartir entre cuadernos)")
    ap.add_argument("--max-minutes", type=float, default=None)
    args = ap.parse_args(argv)

    with open(args.meta_ordenes, "r", encoding="utf-8") as f:
        data = json.load(f)
    ordenes = data["meta_ordenes"] if isinstance(data, dict) else data
    if args.ordenes:
        ordenes = [o for o in ordenes if o["id"] in set(args.ordenes)]

    factories: Dict[str, Callable] = {}

    def factory_por_ticker(ticker: str):
        if args.entorno == "poisson":
            return None
        if ticker not in factories:  # import tardio: requiere ABIDES
            from src.envs.abides_ejecutor_env import make_calibrated_env_factory
            js = Path(args.calibrated_dir) / f"rmsc04_ipsa_{ticker}_{args.snapshot}.json"
            factories[ticker] = make_calibrated_env_factory(js, ticker=ticker)
        return factories[ticker]

    out = Path(args.out_dir) / f"benchmarks_meta_ordenes_{args.entorno}.json"
    firma = {"tarea": "2.3.4", "entorno": args.entorno, "snapshot": args.snapshot,
             "ordenes": sorted(o["id"] for o in ordenes), "cantidades": {o["id"]: o["cantidad"] for o in ordenes}}
    estado = load_resumable(out, firma)
    seeds = list(range(1, args.seeds + 1))
    print(f"{len(pendientes(estado, ordenes, seeds))} corridas pendientes", flush=True)
    ok = correr(ordenes, seeds, estado, lambda e: save_json(out, e), factory_por_ticker,
                presupuesto_s=None if args.max_minutes is None else args.max_minutes * 60)
    estado["resumen"] = resumen(estado)
    save_json(out, estado)
    print(f"Guardado: {out}")
    if not ok:
        print("Quedaron corridas pendientes: vuelve a ejecutar el mismo comando.")


if __name__ == "__main__":
    main()
