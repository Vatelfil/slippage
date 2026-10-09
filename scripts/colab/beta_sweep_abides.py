"""Barrido de beta en ABIDES calibrado (tarea 2.2.3, fase 1) -- corre en Colab.

    PYTHONPATH=. python scripts/colab/beta_sweep_abides.py \
        --calibrated-json <dir>/rmsc04_ipsa_FALABELLA_2026-08-23.json --out-dir <dir>

Mismas politicas, tramos, grilla de beta y metricas que `scripts/beta_sweep.py`
(ver `src/experiments/beta_sweep.py`), pero con `EjecutorEnvAbides` sobre
rmsc04 calibrado (config por tramo de la 2.2.4, precios pasados a CLP).

Salida: <out-dir>/beta_sweep_abides_<fecha>.json. Reanudable: guarda tras
cada episodio y salta los ya guardados. Los episodios de `cierre` son los mas
lentos (ABIDES simula el mercado desde la apertura hasta las 14:00).
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path
from typing import Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.config.market_params import ESCALA_RECOMPENSA_EJECUTOR, VENTANA_SIGMA2_PASOS  # noqa: E402
from src.envs.calibrate_rmsc04_ipsa import load_abides_kwargs, load_unidades_por_clp  # noqa: E402
from src.envs.rmsc04_search import load_resumable, save_json  # noqa: E402
from src.experiments import beta_sweep as bs  # noqa: E402

ENTORNO = "abides"


def main(argv: Optional[Sequence[str]] = None) -> Path:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--calibrated-json", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--ticker", default="FALABELLA")
    ap.add_argument("--seeds", type=int, default=20, help="semillas por (tramo, politica): 1..N")
    ap.add_argument("--q-slice", type=int, default=1000)
    ap.add_argument("--ventana-min", type=int, default=15)
    ap.add_argument("--tramos", nargs="+", default=list(bs.TRAMOS), choices=list(bs.TRAMOS))
    ap.add_argument("--fecha", default=dt.date.today().isoformat())
    args = ap.parse_args(argv)

    from src.envs.abides_ejecutor_env import make_calibrated_env_factory  # requiere ABIDES

    out_path = Path(args.out_dir) / f"beta_sweep_{ENTORNO}_{args.fecha}.json"
    firma = {"entorno": ENTORNO, "ticker": args.ticker, "q_slice": args.q_slice,
             "ventana_min": args.ventana_min, "ventana_sigma2": VENTANA_SIGMA2_PASOS, "sigma2": "nivel_normalizada_6_sobre_n_mas_1",
             "politicas": list(bs.POLITICAS), "nivel_pasivo": bs.NIVEL_PASIVO[ENTORNO],
             "calibrated_json": Path(args.calibrated_json).name,
             "abides_kwargs": load_abides_kwargs(args.calibrated_json),
             "unidades_por_clp": load_unidades_por_clp(args.calibrated_json)}
    estado = load_resumable(out_path, firma)
    factory = make_calibrated_env_factory(args.calibrated_json, ticker=args.ticker, beta=0.0)

    bs.run_sweep(factory, ENTORNO, list(range(1, args.seeds + 1)), args.q_slice, args.ventana_min,
                 estado, lambda e: save_json(out_path, e), tramos=args.tramos)
    estado["reporte"] = bs.report_from_state(estado, ESCALA_RECOMPENSA_EJECUTOR)
    estado["semillas"] = args.seeds
    save_json(out_path, estado)
    bs.print_report(estado["reporte"])
    print(f"\nGuardado: {out_path}")
    return out_path


if __name__ == "__main__":
    main()
