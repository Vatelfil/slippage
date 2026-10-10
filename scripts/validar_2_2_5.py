"""Analisis local de la validacion formal 2.2.5 (PS): lee los resultados de las
corridas de Colab y genera JSON, figura e informe markdown.

    python scripts/validar_2_2_5.py \
        --sim-despues <dir>/validacion_2_2_5_despues_FALABELLA_2026-08-23.json \
        --sim-antes   <dir>/validacion_2_2_5_antes_FALABELLA_2026-08-23.json

Elaborado por PS con apoyo de Claude Code; pendiente de revision por BF.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.analysis import validacion_formal as vf  # noqa: E402
from src.analysis.validacion_informe import render_markdown  # noqa: E402


def _load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--sim-despues", required=True)
    ap.add_argument("--sim-antes", default=None)
    ap.add_argument("--ticker", default="FALABELLA")
    ap.add_argument("--snapshot", default="2026-08-23")
    ap.add_argument("--base-json", default=str(REPO_ROOT / "data/calibration/rmsc04_base_FALABELLA_2026-08-23.json"))
    ap.add_argument("--calibration-json", default=str(REPO_ROOT / "data/calibration/poisson_params_2026-08-23.json"))
    ap.add_argument("--out-json", default=str(REPO_ROOT / "data/analysis/validacion_formal_2_2_5.json"))
    ap.add_argument("--out-png", default=str(REPO_ROOT / "data/analysis/validacion_formal_2_2_5.png"))
    ap.add_argument("--out-md", default=str(REPO_ROOT / "docs/validacion_formal_2.2.5_PS.md"))
    args = ap.parse_args(argv)

    base = _load(args.base_json)
    real = {t: base["por_tramo"][t]["retornos_reales_5min"] for t in vf.TRAMOS}
    obj = _load(args.calibration_json)["objetivos_validacion"][args.ticker]["por_tramo"]

    sim_d = _load(args.sim_despues)
    res_d = vf.analizar_modo(real, sim_d["resultados"], obj)
    sim_a = _load(args.sim_antes) if args.sim_antes else None
    res_a = vf.analizar_modo(real, sim_a["resultados"], obj) if sim_a else None
    comp = vf.comparar_antes_despues(res_a, res_d) if res_a else None

    n_sem = min(res_d["por_tramo"][t]["n_semillas"] for t in vf.TRAMOS)
    meta = {"ticker": args.ticker, "snapshot": args.snapshot, "semillas": n_sem, "fecha": time.strftime("%Y-%m-%d")}
    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump({"metadata": meta, "despues": res_d, "antes": res_a, "comparacion": comp},
                  f, indent=1, ensure_ascii=False)
    vf.figuras(real, vf.retornos_simulados(sim_d["resultados"]),
               vf.retornos_simulados(sim_a["resultados"]) if sim_a else None, args.out_png)
    Path(args.out_md).write_text(render_markdown(res_d, res_a, comp, meta), encoding="utf-8")
    print(res_d["veredicto"]["texto"])
    print(f"JSON: {args.out_json}\nFigura: {args.out_png}\nInforme: {args.out_md}")


if __name__ == "__main__":
    main()
