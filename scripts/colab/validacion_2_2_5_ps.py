"""Corridas de la validacion formal 2.2.5 (PS) -- corre en Colab con ABIDES.

Elaborado por PS con apoyo de Claude Code; pendiente de revision por BF.

Prueba corta (mide cuanto tarda una corrida; 1 semilla, solo apertura):
    PYTHONPATH=. python scripts/colab/validacion_2_2_5_ps.py \
        --calibrated-json data/calibration/rmsc04_ipsa_FALABELLA_2026-08-23.json \
        --out-dir <carpeta_de_drive> --seeds 1 --tramos apertura --modos despues

Corrida completa (30 semillas por tramo, primero "despues" y luego "antes"):
    PYTHONPATH=. python scripts/colab/validacion_2_2_5_ps.py \
        --calibrated-json data/calibration/rmsc04_ipsa_FALABELLA_2026-08-23.json \
        --out-dir <carpeta_de_drive> --seeds 30 --max-minutes 240

Es reanudable: si Colab se corta, volver a ejecutar el mismo comando y sigue
donde quedo. Salida: <out-dir>/validacion_2_2_5_<modo>_<ticker>_<snapshot>.json
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.envs import rmsc04_sim_stats as ss  # noqa: E402
from src.envs.calibrate_rmsc04_ipsa import load_abides_kwargs  # noqa: E402
from src.experiments import validacion_runs as vr  # noqa: E402


def main(argv: Optional[Sequence[str]] = None) -> None:
    ap = argparse.ArgumentParser(description="Corridas de simulacion para la validacion formal 2.2.5")
    ap.add_argument("--calibrated-json", required=True,
                    help="rmsc04_ipsa_<ticker>_<snapshot>.json de la 2.2.4 (config calibrada por tramo)")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--ticker", default="FALABELLA")
    ap.add_argument("--snapshot", default="2026-08-23")
    ap.add_argument("--seeds", type=int, default=30, help="semillas por tramo (default 30)")
    ap.add_argument("--seed-base", type=int, default=200, help="semillas = base+1 .. base+N (default 201..)")
    ap.add_argument("--modos", nargs="+", default=list(vr.MODOS), choices=list(vr.MODOS))
    ap.add_argument("--tramos", nargs="+", default=list(ss.TRAMO_NAMES), choices=list(ss.TRAMO_NAMES))
    ap.add_argument("--max-minutes", type=float, default=None,
                    help="presupuesto de tiempo TOTAL; al agotarse guarda y termina (reanudable)")
    args = ap.parse_args(argv)

    calibrados = load_abides_kwargs(args.calibrated_json)
    seeds = vr.semillas(args.seed_base, args.seeds)
    t0 = time.time()
    for modo in args.modos:
        kwargs = vr.kwargs_para_modo(modo, calibrados)
        out = Path(args.out_dir) / f"validacion_2_2_5_{modo}_{args.ticker}_{args.snapshot}.json"
        parcial = vr.abrir_parcial(out, args.ticker, args.snapshot, modo, kwargs)
        parcial["semillas"] = seeds
        faltan = vr.pendientes(parcial, seeds, args.tramos)
        print(f"\n=== Modo {modo}: {faltan} corridas pendientes de {len(seeds) * len(args.tramos)} ===", flush=True)
        restante = None
        if args.max_minutes is not None:
            restante = max(0.0, args.max_minutes * 60 - (time.time() - t0))
        completo = vr.run_runs(kwargs, seeds, parcial, out, tramos=args.tramos, presupuesto_s=restante)
        print(f"Guardado: {out}", flush=True)
        if not completo:
            print("Quedaron corridas pendientes: vuelve a ejecutar el mismo comando para continuar.")
            break
    print(f"\nTiempo total de esta ejecucion: {(time.time() - t0) / 60:.1f} min")


if __name__ == "__main__":
    main()
