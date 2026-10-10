"""Fase 2 de la eleccion de beta (tarea 2.2.3) en ABIDES calibrado -- corre en Colab.

Elaborado por PS con apoyo de Claude Code; pendiente de revision por BF y MR.

Prueba corta (mide tiempos; 4 episodios de entrenamiento, 2 de evaluacion):
    PYTHONPATH=. python scripts/colab/beta_fase2_ppo.py \
        --calibrated-json data/calibration/rmsc04_ipsa_FALABELLA_2026-08-23.json \
        --out-dir <carpeta_de_drive>/prueba_b --episodes 4 --eval-seeds 2

Corrida completa:
    PYTHONPATH=. python scripts/colab/beta_fase2_ppo.py \
        --calibrated-json data/calibration/rmsc04_ipsa_FALABELLA_2026-08-23.json \
        --out-dir <carpeta_de_drive> --episodes 200 --eval-seeds 30 --max-minutes 240

Reanudable: guarda tras cada beta. Salida: <out-dir>/beta_fase2_<tramo>_<fecha>.json,
los modelos .pt y el informe .md.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.envs.rmsc04_search import load_resumable, save_json  # noqa: E402
from src.experiments import beta_phase2 as bp  # noqa: E402

DEFAULT_SWEEP = REPO_ROOT / "data/calibration/beta_sweep_abides_2026-10-10.json"


def main(argv: Optional[Sequence[str]] = None) -> Path:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--calibrated-json", required=True)
    ap.add_argument("--beta-sweep-json", default=str(DEFAULT_SWEEP),
                    help="barrido de BF en ABIDES (de ahi sale beta*)")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--ticker", default="FALABELLA")
    ap.add_argument("--tramo", default="apertura", choices=["apertura", "media_jornada", "cierre"])
    ap.add_argument("--episodes", type=int, default=200, help="episodios de entrenamiento por beta")
    ap.add_argument("--eval-seeds", type=int, default=30)
    ap.add_argument("--q-slice", type=int, default=1000)
    ap.add_argument("--ventana-min", type=int, default=15)
    ap.add_argument("--max-minutes", type=float, default=None)
    ap.add_argument("--fecha", default=dt.date.today().isoformat())
    args = ap.parse_args(argv)

    from src.envs.abides_ejecutor_env import make_calibrated_env_factory  # requiere ABIDES

    with open(args.beta_sweep_json, "r", encoding="utf-8") as f:
        beta_star = float(json.load(f)["reporte"]["beta_star"])
    out_dir = Path(args.out_dir)
    out_path = out_dir / f"beta_fase2_{args.tramo}_{args.fecha}.json"
    firma = {"entorno": "abides", "ticker": args.ticker, "tramo": args.tramo, "n_train": args.episodes,
             "n_eval": args.eval_seeds, "q_slice": args.q_slice, "ventana_min": args.ventana_min,
             "beta_star": beta_star, "cfg": bp.PPO_CFG, "calibrated_json": Path(args.calibrated_json).name}
    estado = load_resumable(out_path, firma)
    factory = make_calibrated_env_factory(args.calibrated_json, ticker=args.ticker)

    completo = bp.correr_fase2(
        factory, "abides", beta_star, args.tramo, args.episodes, args.eval_seeds, args.q_slice,
        args.ventana_min, estado, lambda e: save_json(out_path, e), out_dir,
        presupuesto_s=None if args.max_minutes is None else args.max_minutes * 60)
    if completo:
        md = out_dir / f"beta_fase2_{args.tramo}_{args.fecha}.md"
        md.write_text(bp.informe_markdown(estado), encoding="utf-8")
        print(f"\nGuardado: {out_path}\nInforme: {md}")
    else:
        print("\nQuedo trabajo pendiente: volver a ejecutar el mismo comando para continuar.")
    return out_path


if __name__ == "__main__":
    main()
