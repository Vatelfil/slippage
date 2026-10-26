"""Reevaluación de los Ejecutores ya entrenados con MUCHAS semillas de evaluación (Colab; no entrena).

BORRADOR elaborado por PS con apoyo de Claude Code (Sprint 6).

Por qué existe: las primeras comparaciones contra el control usaron solo 15 semillas de evaluación y el slippage de cada semilla
depende sobre todo de hacia dónde se mueve el precio en esa simulación (hay semillas de -25 y de +75 bps para TODAS las
estrategias). Con 15 semillas la diferencia entre dos estrategias queda tapada por ese ruido, y al pasar a 40 semillas una
conclusión cambió de signo. Aquí se evalúan, en las MISMAS semillas, las redes entrenadas (a partir de su
`checkpoint_last.pt`), la red inicial de cada semilla (control, muestreando la política) y las tres heurísticas.

    PYTHONPATH=. python scripts/colab/reevaluar_ejecutores_ps.py --raices <drive>/conf_pen30_g1_A <drive>/v4_pen30_g1_A \
        --n-semillas 150 --out-dir <drive>/reeval_150

Es reanudable: lo que ya está en `--out-dir` se salta, así que se puede volver a lanzar cuando aparezcan redes nuevas
(p. ej. las del cuaderno B). Orden: control y heurísticas primero, después las redes.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import time
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.config.market_params import BETA_RIESGO_EJECUTOR  # noqa: E402
from src.experiments import beta_phase2 as bp  # noqa: E402
from src.experiments import beta_sweep as bs  # noqa: E402

PATRON = re.compile(r"d3_opcion(0|A)_s(\d+)$")


def _entrenamiento():
    spec = importlib.util.spec_from_file_location("entrenamiento_inicial_ps", REPO_ROOT / "scripts/colab/entrenamiento_inicial_ps.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def descubrir(raices: Sequence[Path], tramo: str = "apertura") -> List[Tuple[str, int, Path]]:
    """[(etiqueta, semilla de red, checkpoint)] de todas las redes terminadas bajo las raíces. La etiqueta es
    `<carpeta raíz>__<d3_opcion*_s*>`, única aunque dos raíces repitan nombres de subcarpeta."""
    redes = []
    for raiz in raices:
        for ckpt in sorted(Path(raiz).rglob(f"checkpoints_{tramo}/checkpoint_last.pt")):
            m = PATRON.search(ckpt.parent.parent.name)
            if m:
                redes.append((f"{Path(raiz).name}__{ckpt.parent.parent.name}", int(m.group(2)), ckpt))
    return redes


def _guardar(ruta: Path, res: dict, extra: dict) -> None:
    res = dict(res)
    res.update(extra)
    ruta.write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv: Optional[Sequence[str]] = None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--raices", nargs="+", required=True, help="carpetas que contienen las d3_opcion*_s*/checkpoints_apertura")
    ap.add_argument("--calibrated-json", default=str(REPO_ROOT / "data/calibration/rmsc04_ipsa_FALABELLA_2026-08-23.json"))
    ap.add_argument("--ticker", default="FALABELLA")
    ap.add_argument("--entorno", choices=["abides", "poisson"], default="abides")
    ap.add_argument("--tramo", default="apertura", choices=["apertura", "media_jornada", "cierre"])
    ap.add_argument("--q-slice", type=int, default=1000)
    ap.add_argument("--ventana-min", type=int, default=15)
    ap.add_argument("--n-semillas", type=int, default=150)
    ap.add_argument("--eval-seed-base", type=int, default=5000)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--max-minutes", type=float, default=None)
    args = ap.parse_args(argv)

    ent = _entrenamiento()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    factory = ent._factory(args.entorno, args.calibrated_json, args.ticker)
    seeds = [args.eval_seed_base + i for i in range(1, args.n_semillas + 1)]
    t_ini = time.time()
    hechos = {"referencias": [], "controles": [], "redes": [], "pendientes": []}

    def excedido() -> bool:
        return args.max_minutes is not None and time.time() - t_ini > args.max_minutes * 60

    redes = descubrir([Path(r) for r in args.raices], args.tramo)
    print(f"{len(redes)} redes encontradas; {len(seeds)} semillas de evaluación", flush=True)

    # 1) heurísticas de referencia (una vez para todos)
    for nombre in bs.POLITICAS:
        f = out_dir / f"ref_{nombre}.json"
        if f.exists() or excedido():
            continue
        t0 = time.time()
        print(f"== Referencia {nombre}", flush=True)
        eps = bp.evaluar_heuristica(nombre, factory, args.entorno, args.tramo, seeds, args.q_slice, args.ventana_min)
        _guardar(f, bp.resumen_evaluacion(eps, BETA_RIESGO_EJECUTOR), {"eval_seeds": seeds, "segundos": round(time.time() - t0, 1)})
        hechos["referencias"].append(nombre)

    # 2) control: la red inicial de cada semilla de red, muestreando
    for s in sorted({s for _, s, _ in redes}):
        f = out_dir / f"control_s{s}.json"
        if f.exists() or excedido():
            continue
        t0 = time.time()
        print(f"== Control, red inicial de la semilla {s}", flush=True)
        eps = ent._evaluar_estocastica(factory, ent._nuevo_trainer(s).model, args.tramo, seeds, args.q_slice, args.ventana_min)
        _guardar(f, bp.resumen_evaluacion(eps, BETA_RIESGO_EJECUTOR), {"semilla_red": s, "eval_seeds": seeds,
                                                                      "segundos": round(time.time() - t0, 1)})
        hechos["controles"].append(s)

    # 3) las redes entrenadas, muestreando
    for etiqueta, s, ckpt in redes:
        f = out_dir / f"red_{etiqueta}.json"
        if f.exists():
            continue
        if excedido():
            hechos["pendientes"].append(etiqueta)
            continue
        t0 = time.time()
        print(f"== Red {etiqueta}", flush=True)
        trainer = ent._nuevo_trainer(s)
        trainer.load_checkpoint(ckpt)
        eps = ent._evaluar_estocastica(factory, trainer.model, args.tramo, seeds, args.q_slice, args.ventana_min)
        res = bp.resumen_evaluacion(eps, BETA_RIESGO_EJECUTOR)
        _guardar(f, res, {"etiqueta": etiqueta, "semilla_red": s, "episodios": trainer.current_episode, "eval_seeds": seeds,
                          "segundos": round(time.time() - t0, 1)})
        hechos["redes"].append(etiqueta)
        print(f"   slippage {res['slippage_bps_medio']:.2f} bps, cumplimiento {res['cumplimiento_medio']:.3f}", flush=True)
    if hechos["pendientes"]:
        print(f"Tiempo agotado: faltan {len(hechos['pendientes'])} redes; vuelve a lanzar para continuar.", flush=True)
    return hechos


if __name__ == "__main__":
    main()
