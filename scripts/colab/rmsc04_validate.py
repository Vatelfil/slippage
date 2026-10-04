"""Validacion final de RMSC04 calibrado (tarea 2.2.4, bloque C) -- corre en Colab.

1. Toma la mejor configuracion de la grilla (`--grid-json`). Con `--refine`
   evalua ademas sus vecinos (<= 10, dia completo, mismas semillas de la
   grilla) y se queda con la de menor perdida.
2. Corre `--seeds` semillas NUEVAS (>= 10, distintas de las de la busqueda)
   por tramo, cada tramo con su propia config (`fund_vol` del tramo) hasta el
   fin del tramo.
3. Por tramo: KS de 2 muestras de los retornos de 5 min simulados contra los
   reales (D, p, D_crit, D/D_crit), tabla de momentos simulados contra
   `objetivos_validacion` y rankings.

    PYTHONPATH=. python scripts/colab/rmsc04_validate.py \
        --ticker FALABELLA --snapshot 2026-08-23 --seeds 10 \
        --grid-json <dir>/rmsc04_grid_FALABELLA_2026-08-23.json --out-dir <dir>

Salida: <out-dir>/rmsc04_ipsa_<ticker>_<snapshot>.json, con
`por_tramo[tramo]["abides_kwargs"]` listo para `load_abides_kwargs()` /
`background_config_extra_kvargs`. Reanudable: las corridas se guardan en
<out-dir>/rmsc04_validate_parcial_<ticker>_<snapshot>.json.

La participacion de volumen y el volumen por vela necesitan el dia completo
con una sola config: se miden en las corridas del tramo `cierre`, que llegan
hasta las 16:00 (los parametros de actividad son comunes a los tres tramos).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.colab.rmsc04_grid_search import base_json_path, day_kwargs, load_base, run_configs  # noqa: E402
from src.envs import rmsc04_search as rs  # noqa: E402
from src.envs import rmsc04_sim_stats as ss  # noqa: E402
from src.envs.calibrate_rmsc04_ipsa import DEFAULT_CALIBRATION_JSON, load_abides_kwargs  # noqa: E402

TRAMO_END_TIME = {name: f"{b // 3600:02d}:{b % 3600 // 60:02d}:00"
                  for name, (_, b) in ss.TRAMO_BOUNDS_S.items()}
TRAMO_DIA_COMPLETO = ss.TRAMO_NAMES[-1]


def select_params(grid: Dict, refine_estado: Optional[Dict] = None) -> Dict:
    """Mejor configuracion entre la grilla y (si existe) el refinamiento."""
    candidatos = dict(grid["resultados"])
    if refine_estado:
        candidatos.update(refine_estado["resultados"])
    mejor = rs.best_config(candidatos)
    if mejor is None:
        raise ValueError("la grilla no tiene ninguna configuracion completa")
    return {"id": mejor, "params": candidatos[mejor]["params"],
            "perdida_busqueda": candidatos[mejor]["perdida"]["total"],
            "origen": "refinamiento" if mejor not in grid["resultados"] else "grilla"}


def run_validation(kwargs_por_tramo: Dict[str, Dict], params: Dict, seeds: Sequence[int],
                   parcial: Dict, parcial_path: Path,
                   simular: Optional[Callable[[Dict, int, str], Dict]] = None) -> None:
    """Corre las simulaciones pendientes de la validacion (por tramo y
    semilla) y guarda tras cada una."""
    simular = simular or ss.simulate_moments
    for tramo in ss.TRAMO_NAMES:
        corridas = parcial["resultados"].setdefault(tramo, {"corridas": {}})["corridas"]
        for seed in seeds:
            if str(seed) in corridas and "momentos" in corridas[str(seed)]:
                continue
            t0 = time.time()
            try:
                mom = simular({**kwargs_por_tramo[tramo], **params}, seed, TRAMO_END_TIME[tramo])
                corridas[str(seed)] = {"momentos": mom, "segundos": round(time.time() - t0, 1)}
                print(f"{tramo} seed={seed}: {time.time() - t0:.0f}s", flush=True)
            except Exception as e:
                corridas[str(seed)] = {"error": f"{type(e).__name__}: {e}"}
                print(f"{tramo} seed={seed}: ERROR {corridas[str(seed)]['error']}", flush=True)
            rs.save_json(parcial_path, parcial)


def build_report(parcial: Dict, base: Dict, objetivos: Dict, kwargs_por_tramo: Dict[str, Dict],
                 seleccion: Dict, metadata: Dict) -> Dict:
    """Arma el JSON final a partir de las corridas guardadas."""
    def runs(tramo: str) -> List[Dict]:
        return [c["momentos"] for c in parcial["resultados"][tramo]["corridas"].values() if "momentos" in c]

    # momentos del tramo medidos con la config de ese tramo
    sim = {t: ss.pool_moments(runs(t)).get(t, {"n_corridas": 0}) for t in ss.TRAMO_NAMES}
    # participacion y volumen por vela: corridas de dia completo
    dia = ss.pool_moments(runs(TRAMO_DIA_COMPLETO))
    for t in ss.TRAMO_NAMES:
        sim[t]["participacion_volumen"] = dia.get(t, {}).get("participacion_volumen")
        sim[t]["volumen_mediano_vela"] = dia.get(t, {}).get("volumen_mediano_vela")

    obj_tramo = objetivos["por_tramo"]
    perdida = rs.loss(sim, obj_tramo)
    tabla = rs.moments_table(sim, obj_tramo)
    params = seleccion["params"]
    por_tramo = {}
    for t in ss.TRAMO_NAMES:
        reales = base["por_tramo"][t]["retornos_reales_5min"]
        por_tramo[t] = {
            "abides_kwargs": {**kwargs_por_tramo[t], **params},
            "ks": rs.ks_summary(sim[t].get("retornos_5min", []), reales),
            "momentos_sim": {k: v for k, v in sim[t].items() if k != "retornos_5min"},
            "momentos_vs_objetivo": tabla[t],
            "curtosis": {"sim": sim[t].get("curtosis"),
                         "real": base["por_tramo"][t]["curtosis_real"]["exceso_curtosis"]},
            "n_corridas": sim[t].get("n_corridas", 0),
            "n_errores": sum(1 for c in parcial["resultados"][t]["corridas"].values() if "error" in c),
        }
    rankings_sim = {
        "volatilidad_bps": ss.ranking(sim, "volatilidad_bps"),
        "spread_mediano_bps": ss.ranking(sim, "spread_mediano_bps"),
        "participacion_volumen": ss.ranking(sim, "participacion_volumen"),
        "volumen_mediano_vela": ss.ranking(sim, "volumen_mediano_vela"),
    }
    return {
        "metadata": metadata,
        "parametros_busqueda": params,
        "seleccion": seleccion,
        "perdida_validacion": perdida,
        "rankings": {
            "simulado": rankings_sim,
            "observado": objetivos["ranking_observado"],
            "robustos": perdida["rankings"],
        },
        "por_tramo": por_tramo,
    }


def print_report(rep: Dict) -> None:
    print("\ntramo           KS D     p        D_crit  D/D_crit | vol sim/obj   spread sim [CS, Roll]   curt sim/real")
    for t, r in rep["por_tramo"].items():
        ks, mo = r["ks"], r["momentos_vs_objetivo"]
        if ks["D"] is None:
            print(f"{t:14s}  sin datos")
            continue
        print(f"{t:14s}  {ks['D']:.3f}  {ks['p']:.1e}  {ks['D_crit']:.3f}   {ks['D_ratio']:.2f}    | "
              f"{mo['volatilidad_bps']['sim']:.1f}/{mo['volatilidad_bps']['objetivo']:.1f}   "
              f"{mo['spread_vs_cs_bps']['sim']:.2f} [{mo['spread_vs_cs_bps']['objetivo']:.1f}, "
              f"{mo['spread_vs_roll_bps']['objetivo']:.1f}]   "
              f"{r['curtosis']['sim']:.2f}/{r['curtosis']['real']:.2f}")
    print("rankings robustos:", rep["rankings"]["robustos"])
    print("perdida de validacion:", round(rep["perdida_validacion"]["total"], 3))


def main(argv: Optional[Sequence[str]] = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--ticker", default="FALABELLA")
    ap.add_argument("--snapshot", default="2026-08-23")
    ap.add_argument("--grid-json", required=True)
    ap.add_argument("--seeds", type=int, default=10, help="numero de semillas de validacion (>= 10)")
    ap.add_argument("--seed-base", type=int, default=100,
                    help="las semillas son seed_base+1..seed_base+N, distintas de las de la grilla")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--refine", action="store_true", help="refinamiento local alrededor del mejor de la grilla")
    ap.add_argument("--base-json", default=None)
    ap.add_argument("--calibration-json", default=str(DEFAULT_CALIBRATION_JSON))
    args = ap.parse_args(argv)
    if args.seeds < 10:
        print(f"AVISO: --seeds {args.seeds} < 10; el plan pide al menos 10 semillas para el KS.")

    out_dir = Path(args.out_dir)
    base_path = base_json_path(args.ticker, args.snapshot, args.base_json)
    base = load_base(base_path)
    objetivos = rs.load_targets(args.calibration_json, args.ticker)
    kwargs_por_tramo = load_abides_kwargs(base_path)
    with open(args.grid_json, "r", encoding="utf-8") as f:
        grid = json.load(f)
    if grid["firma"]["ticker"] != args.ticker or grid["firma"]["snapshot"] != args.snapshot:
        raise ValueError(f"{args.grid_json} es de {grid['firma']['ticker']} {grid['firma']['snapshot']}")

    refine_estado = None
    if args.refine:
        mejor_grid = select_params(grid)
        dia = day_kwargs(base, base_path)
        refine_path = out_dir / f"rmsc04_refine_{args.ticker}_{args.snapshot}.json"
        firma = {"ticker": args.ticker, "snapshot": args.snapshot, "kwargs_base": dia["kwargs"],
                 "centro": mejor_grid["id"], "modo": "refine"}
        refine_estado = rs.load_resumable(refine_path, firma)
        vecinos = rs.refine_candidates(mejor_grid["params"])
        print(f"Refinamiento: {len(vecinos)} vecinos de {mejor_grid['id']}", flush=True)
        run_configs(vecinos, dia["kwargs"], grid["semillas"], "16:00:00", refine_estado, refine_path,
                    lambda pooled: rs.loss(pooled, objetivos["por_tramo"],
                                           vol_ref_unica_bps=dia["sigma_dia_bps"]))

    seleccion = select_params(grid, refine_estado)
    print(f"Configuracion elegida ({seleccion['origen']}): {seleccion['id']} "
          f"(perdida de busqueda {seleccion['perdida_busqueda']:.3f})", flush=True)

    seeds = [args.seed_base + i for i in range(1, args.seeds + 1)]
    parcial_path = out_dir / f"rmsc04_validate_parcial_{args.ticker}_{args.snapshot}.json"
    firma = {"ticker": args.ticker, "snapshot": args.snapshot, "params": seleccion["params"],
             "kwargs_por_tramo": kwargs_por_tramo, "modo": "validate"}
    parcial = rs.load_resumable(parcial_path, firma)
    run_validation(kwargs_por_tramo, seleccion["params"], seeds, parcial, parcial_path)

    metadata = {
        "tarea": "2.2.4 bloques B y C", "ticker": args.ticker, "snapshot": args.snapshot,
        "unidad_cuenta": base["metadata"]["unidad_cuenta"],
        "semillas_validacion": seeds, "semillas_busqueda": grid.get("semillas"),
        "grid_json": Path(args.grid_json).name, "base_json": base_path.name,
        "refinamiento": bool(args.refine),
        "fecha_generacion": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "nota_participacion": "participacion y volumen por vela medidos en las corridas de "
                              "dia completo (config del tramo cierre)",
    }
    rep = build_report(parcial, base, objetivos, kwargs_por_tramo, seleccion, metadata)
    out_path = out_dir / f"rmsc04_ipsa_{args.ticker}_{args.snapshot}.json"
    rs.save_json(out_path, rep)
    print_report(rep)
    print(f"\nGuardado: {out_path}")


if __name__ == "__main__":
    main()
