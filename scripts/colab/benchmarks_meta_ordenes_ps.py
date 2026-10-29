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
           presupuesto_s: Optional[float] = None, log: Callable[[str], None] = print,
           impacto_por_orden: Optional[Callable[[Dict], object]] = None) -> bool:
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
            fab = factory_por_ticker(o["ticker"])
            if impacto_por_orden is not None:   # estado de impacto nuevo por meta-orden (borrador de PS para MR)
                from src.envs.impacto_acumulado import con_impacto, fabrica_poisson
                fab = con_impacto(fab or fabrica_poisson(o["ticker"]), impacto_por_orden(o))
            r = run_benchmark_episode(sched, seed=int(seed) + int(o.get("semilla", 0)), ticker=o["ticker"],
                                      env_factory=fab)
            m = evaluate_episode(q_total=r.q_total, q_executed=r.q_executed, p_referencia=r.p_referencia,
                                 p_promedio_ejecutado=r.p_promedio_ejecutado)
            corridas[clave] = {"orden": oid, "estrategia": estrategia, "seed": int(seed), "ticker": o["ticker"],
                               "tramo_inicio": o["tramo_inicio"], "cantidad": o["cantidad"],
                               "segundos": round(time.time() - t0, 1), **{k: _num(v) for k, v in m.items()}}
            log(f"{clave}: IS={corridas[clave].get('IS_total')} cumpl={corridas[clave].get('execution_rate')} ({time.time() - t0:.0f}s)")
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


def _parametros_impacto(orden: Dict, y: float, tau: float):
    from src.envs.impacto_acumulado import parametros_para
    if "volumen_dia_simulado" not in orden:
        raise ValueError(f"{orden['id']}: --impacto necesita volumen_dia_simulado (usar meta_ordenes_v2_candidata.json)")
    return parametros_para(orden["ticker"], float(orden["volumen_dia_simulado"]), y=y, tau_min=tau)


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
    ap.add_argument("--impacto", action="store_true",
                    help="impacto acumulado entre ventanas (src/envs/impacto_acumulado.py; borrador de PS para MR)")
    ap.add_argument("--impacto-y", type=float, default=0.5)
    ap.add_argument("--impacto-tau", type=float, default=120.0)
    ap.add_argument("--escenario", default=None, help="escenario de liquidez (baja, media, alta; ver data/scenarios); sin la opcion, la calibracion de siempre")
    ap.add_argument("--escenarios-json", default=None)
    ap.add_argument("--factor-tamano", type=float, default=1.0, help="multiplica la cantidad de cada meta-orden (0.5, 1, 1.5)")
    ap.add_argument("--perfil-volumen", default=str(REPO_ROOT / "data/meta_ordenes/perfil_volumen_v1.csv"),
                    help="perfil de volumen por tramo para VWAP (evita depender del parquet de mercado, que no se versiona)")
    args = ap.parse_args(argv)

    with open(args.meta_ordenes, "r", encoding="utf-8-sig") as f:  # tolera el BOM que agrega Windows
        data = json.load(f)
    ordenes = data["meta_ordenes"] if isinstance(data, dict) else data
    if args.ordenes:
        ordenes = [o for o in ordenes if o["id"] in set(args.ordenes)]
    # escenario de liquidez y tamaño (3.1.3 / 3.2.1, borrador de PS para BF); sin opciones queda todo como antes
    from src.envs import escenarios_liquidez as el
    ordenes = el.ajustar_ordenes(ordenes, args.factor_tamano)
    factor_liq = el.factor_de(args.escenario, args.escenarios_json)
    factory_por_ticker = el.fabricas_por_ticker(args.entorno, args.calibrated_dir, args.snapshot, factor_liq)

    sufijo = el.sufijo_condicion(args.escenario, args.factor_tamano) + ("_impacto" if args.impacto else "")
    out = Path(args.out_dir) / f"benchmarks_meta_ordenes_{args.entorno}{sufijo}.json"
    firma = {"tarea": "2.3.4", "entorno": args.entorno, "snapshot": args.snapshot,
             "ordenes": sorted(o["id"] for o in ordenes), "cantidades": {o["id"]: o["cantidad"] for o in ordenes}}
    if sufijo:
        firma.update({"escenario": args.escenario, "factor_liquidez": factor_liq, "factor_tamano": args.factor_tamano})
    if args.impacto:
        firma["impacto"] = {"y": args.impacto_y, "tau_min": args.impacto_tau}
    estado = load_resumable(out, firma)
    seeds = list(range(1, args.seeds + 1))
    print(f"{len(pendientes(estado, ordenes, seeds))} corridas pendientes", flush=True)
    perfil = None
    if Path(args.perfil_volumen).exists():
        import pandas as pd
        perfil = pd.read_csv(args.perfil_volumen, index_col=0)
        print(f"Perfil de volumen: {args.perfil_volumen}", flush=True)
    ok = correr(ordenes, seeds, estado, lambda e: save_json(out, e), factory_por_ticker,
                volume_profile=perfil,
                presupuesto_s=None if args.max_minutes is None else args.max_minutes * 60,
                impacto_por_orden=(lambda o: _parametros_impacto(o, args.impacto_y, args.impacto_tau)) if args.impacto else None)
    for c in estado.get("corridas", {}).values():
        c.setdefault("escenario", args.escenario or "media")
        c.setdefault("factor_tamano", args.factor_tamano)
    estado["resumen"] = resumen(estado)
    save_json(out, estado)
    print(f"Guardado: {out}")
    if not ok:
        print("Quedaron corridas pendientes: vuelve a ejecutar el mismo comando.")


if __name__ == "__main__":
    main()
