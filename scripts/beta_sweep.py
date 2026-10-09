"""Barrido de beta en el fallback Poisson (tarea 2.2.3, fase 1) -- corre en local.

    python scripts/beta_sweep.py [--seeds 20] [--q-slice 1000] [--ventana-min 15]

Evalua las politicas heuristicas (agresiva MARKET, TWAP con LIMIT de nivel
medio, pasiva LIMIT) en los 3 tramos, calcula beta* y las metricas para
beta en {0; 0,1; 0,3; 1; 3} x beta*.

Salida: data/calibration/beta_sweep_poisson_<fecha>.json. Reanudable: los
episodios ya guardados (mismo archivo y misma configuracion) se saltan.

Ver `src/experiments/beta_sweep.py` para el metodo y las metricas.
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path
from typing import Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.config.market_params import ESCALA_RECOMPENSA_EJECUTOR, VENTANA_SIGMA2_PASOS  # noqa: E402
from src.envs.fallback_poisson_env import EjecutorEnvPoissonFallback  # noqa: E402
from src.envs.rmsc04_search import load_resumable, save_json  # noqa: E402
from src.experiments import beta_sweep as bs  # noqa: E402

DEFAULT_OUT_DIR = REPO_ROOT / "data" / "calibration"
ENTORNO = "poisson"
P_REFERENCIA = 5969.75  # mediana de close_raw de FALABELLA, snapshot 2026-08-23


def main(argv: Optional[Sequence[str]] = None) -> Path:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--ticker", default="FALABELLA")
    ap.add_argument("--seeds", type=int, default=20, help="semillas por (tramo, politica): 1..N")
    ap.add_argument("--q-slice", type=int, default=1000)
    ap.add_argument("--ventana-min", type=int, default=15)
    ap.add_argument("--p-referencia", type=float, default=P_REFERENCIA)
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    ap.add_argument("--fecha", default=dt.date.today().isoformat())
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    out_path = Path(args.out_dir) / f"beta_sweep_{ENTORNO}_{args.fecha}.json"
    firma = {"entorno": ENTORNO, "ticker": args.ticker, "q_slice": args.q_slice,
             "ventana_min": args.ventana_min, "p_referencia": args.p_referencia,
             "ventana_sigma2": VENTANA_SIGMA2_PASOS, "sigma2": "nivel_normalizada_6_sobre_n_mas_1", "politicas": list(bs.POLITICAS),
             "nivel_pasivo": bs.NIVEL_PASIVO[ENTORNO]}
    estado = load_resumable(out_path, firma)

    def factory(executor_id, q_slice, ventana_min, seed):
        return EjecutorEnvPoissonFallback(
            executor_id=executor_id, ticker=args.ticker, q_slice=float(q_slice),
            ventana_min=ventana_min, p_referencia=args.p_referencia, seed=seed, beta=0.0)

    bs.run_sweep(factory, ENTORNO, list(range(1, args.seeds + 1)), args.q_slice, args.ventana_min,
                 estado, lambda e: save_json(out_path, e), verbose=not args.quiet)
    estado["reporte"] = bs.report_from_state(estado, ESCALA_RECOMPENSA_EJECUTOR)
    estado["semillas"] = args.seeds
    save_json(out_path, estado)
    bs.print_report(estado["reporte"])
    print(f"\nGuardado: {out_path}")
    return out_path


if __name__ == "__main__":
    main()
