"""Control de la red SIN entrenar evaluada MUESTREANDO la politica (complemento de `d3_estabilidad_ps.py`) -- Colab.

BORRADOR elaborado por PS con apoyo de Claude Code (Sprint 6). La decision D3 es de BF.

En `entrenamiento_inicial_ps.py` la red sin entrenar se evalua solo con argmax, mientras que la red entrenada se evalua con
argmax y muestreando. Con una politica casi uniforme (entropia ~99,8 % del maximo tras 100 episodios) la evaluacion
muestreada de una red entrenada se parece a la de una red sin entrenar, asi que comparar "entrenada muestreada" con "sin
entrenar argmax" no mide aprendizaje. Este script evalua la red inicial de cada semilla muestreando, en las MISMAS semillas de
evaluacion (5001-5015), y deja un JSON por semilla de red. No entrena: son unos minutos por semilla.

    PYTHONPATH=. python scripts/colab/control_muestreado_ps.py --out-dir <carpeta_de_drive>/d3_estabilidad

La red inicial de una semilla es la misma en la opcion 0 y en la A (mismo `seed`), asi que basta una evaluacion por semilla.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.config.market_params import BETA_RIESGO_EJECUTOR  # noqa: E402
from src.experiments import beta_phase2 as bp  # noqa: E402

SEMILLAS_RED = (1000, 2000, 3000, 4000, 6000)


def _entrenamiento():
    spec = importlib.util.spec_from_file_location("entrenamiento_inicial_ps", REPO_ROOT / "scripts/colab/entrenamiento_inicial_ps.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def archivo(out_dir: Path, semilla: int) -> Path:
    return out_dir / f"control_sin_entrenar_muestreado_s{semilla}.json"


def main(argv: Optional[Sequence[str]] = None) -> list:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--calibrated-json", default=str(REPO_ROOT / "data/calibration/rmsc04_ipsa_FALABELLA_2026-08-23.json"))
    ap.add_argument("--ticker", default="FALABELLA")
    ap.add_argument("--entorno", choices=["abides", "poisson"], default="abides")
    ap.add_argument("--tramo", default="apertura", choices=["apertura", "media_jornada", "cierre"])
    ap.add_argument("--q-slice", type=int, default=1000)
    ap.add_argument("--ventana-min", type=int, default=15)
    ap.add_argument("--semillas", nargs="+", type=int, default=list(SEMILLAS_RED))
    ap.add_argument("--eval-seeds", type=int, default=15)
    ap.add_argument("--eval-seed-base", type=int, default=5000)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args(argv)

    ent = _entrenamiento()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    factory = ent._factory(args.entorno, args.calibrated_json, args.ticker)
    eval_seeds = [args.eval_seed_base + i for i in range(1, args.eval_seeds + 1)]
    hechos = []
    for s in args.semillas:
        f = archivo(out_dir, s)
        if f.exists():
            print(f"semilla {s}: ya existe, se salta", flush=True)
            continue
        t0 = time.time()
        print(f"== Red inicial de la semilla {s}, muestreando la politica", flush=True)
        net = ent._nuevo_trainer(s).model
        eps = ent._evaluar_estocastica(factory, net, args.tramo, eval_seeds, args.q_slice, args.ventana_min)
        res = bp.resumen_evaluacion(eps, BETA_RIESGO_EJECUTOR)
        res.update({"semilla_red": s, "tramo": args.tramo, "eval_seeds": eval_seeds, "segundos": round(time.time() - t0, 1)})
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        hechos.append(f)
        print(f"   slippage {res['slippage_bps_medio']} bps, cumplimiento {res['cumplimiento_medio']} ({res['segundos']} s)", flush=True)
    return hechos


if __name__ == "__main__":
    main()
