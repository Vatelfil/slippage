"""Sondeo de megashocks (2.2.4) -- corre en Colab con ABIDES.

Elaborado por PS con apoyo de Claude Code; pendiente de revision por BF.

Prueba corta (mide cuanto tarda un dia completo):
    PYTHONPATH=. python scripts/colab/megashock_probe_ps.py \
        --calibrated-json data/calibration/rmsc04_ipsa_FALABELLA_2026-08-23.json \
        --out-dir <carpeta_de_drive> --seeds 1 --max-candidatos 1

Corrida completa (6 candidatos x 10 semillas, reanudable):
    PYTHONPATH=. python scripts/colab/megashock_probe_ps.py \
        --calibrated-json data/calibration/rmsc04_ipsa_FALABELLA_2026-08-23.json \
        --out-dir <carpeta_de_drive> --seeds 10 --max-minutes 180

Salida: <out-dir>/megashock_probe_<ticker>_<snapshot>.json (corridas) y
megashock_probe_decision_<ticker>_<snapshot>.json (metricas y decision).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.analysis.validacion_formal import TRAMOS  # noqa: E402
from src.envs import rmsc04_search as rs  # noqa: E402
from src.envs.calibrate_rmsc04_ipsa import load_abides_kwargs  # noqa: E402
from src.experiments import megashock_probe as mp  # noqa: E402
from src.experiments import validacion_runs as vr  # noqa: E402


def main(argv: Optional[Sequence[str]] = None) -> None:
    ap = argparse.ArgumentParser(description="Sondeo de megashocks para la calibracion 2.2.4")
    ap.add_argument("--calibrated-json", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--base-json", default=str(REPO_ROOT / "data/calibration/rmsc04_base_FALABELLA_2026-08-23.json"))
    ap.add_argument("--calibration-json", default=str(REPO_ROOT / "data/calibration/poisson_params_2026-08-23.json"))
    ap.add_argument("--ticker", default="FALABELLA")
    ap.add_argument("--snapshot", default="2026-08-23")
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--seed-base", type=int, default=300)
    ap.add_argument("--max-candidatos", type=int, default=None)
    ap.add_argument("--max-minutes", type=float, default=None)
    args = ap.parse_args(argv)

    kwargs_cierre = load_abides_kwargs(args.calibrated_json)["cierre"]
    cands = mp.candidatos()[: args.max_candidatos]
    seeds = vr.semillas(args.seed_base, args.seeds)
    out = Path(args.out_dir) / f"megashock_probe_{args.ticker}_{args.snapshot}.json"
    firma = {"tarea": "2.2.4-megashock", "ticker": args.ticker, "snapshot": args.snapshot,
             "kwargs_cierre": kwargs_cierre, "candidatos": [c["id"] for c in cands]}
    estado = rs.load_resumable(out, firma)
    ok = mp.correr_probe(kwargs_cierre, cands, seeds, estado, lambda e: rs.save_json(out, e),
                         presupuesto_s=None if args.max_minutes is None else args.max_minutes * 60)
    with open(args.base_json, "r", encoding="utf-8") as f:
        base = json.load(f)
    real = {t: base["por_tramo"][t]["retornos_reales_5min"] for t in TRAMOS}
    with open(args.calibration_json, "r", encoding="utf-8") as f:
        vol_obj = json.load(f)["objetivos_validacion"][args.ticker]["por_tramo"]["cierre"]["volatilidad_bps"]
    res = mp.evaluar_y_decidir(estado, cands, real, vol_obj)
    dec = Path(args.out_dir) / f"megashock_probe_decision_{args.ticker}_{args.snapshot}.json"
    rs.save_json(dec, res)
    for cid, m in res["metricas"].items():
        print(f"{cid}: D_est_medio={m['D_medio']}  curtosis={[round(m['por_tramo'][t]['curtosis'] or 0, 2) for t in TRAMOS]}")
    print("DECISION:", res["decision"]["motivo"])
    if not ok:
        print("Quedaron corridas pendientes: vuelve a ejecutar el mismo comando.")


if __name__ == "__main__":
    main()
