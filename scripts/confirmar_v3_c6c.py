"""Aplica el criterio de confirmación de la v3 (C-6c, desviación 10) al JSON del C-6. BF, 2 nov 2026, con apoyo de Claude Code.

    python scripts/confirmar_v3_c6c.py --entrada data/colab_resultados/c6c_liquidez/c6c_liquidez.json \\
        --out-json data/analysis/c6c_confirmacion_v3.json --out-md data/analysis/c6c_confirmacion_v3.md

El criterio está en `src/experiments/confirmacion_v3.py` (CRITERIO) y se fijó antes de correr el C-6c. Con
`--seed-base` se puede leer otro C-6 con el mismo cálculo (por ejemplo el C-6b, semillas 8001 a 8060); eso es solo una lectura,
no la confirmación.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.experiments import confirmacion_v3 as cv3  # noqa: E402


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--entrada", required=True, help="JSON que escribe scripts/colab/c6_escenarios_liquidez_bf.py")
    ap.add_argument("--out-json", default=None)
    ap.add_argument("--out-md", default=None)
    ap.add_argument("--seed-base", type=int, default=None,
                    help=f"solo para leer otro C-6 (por defecto {cv3.CRITERIO['seed_base']}, el del criterio)")
    args = ap.parse_args(argv)

    with open(args.entrada, "r", encoding="utf-8-sig") as f:
        datos = json.load(f)
    criterio = dict(cv3.CRITERIO)
    if args.seed_base is not None:
        criterio["seed_base"] = args.seed_base
    res = cv3.evaluar(datos, criterio)
    res["entrada"] = Path(args.entrada).name
    md = cv3.tabla_md(res)
    if args.out_json:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.out_md:
        Path(args.out_md).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_md).write_text(md, encoding="utf-8")
    if hasattr(sys.stdout, "reconfigure"):  # la consola de Windows no es UTF-8 por defecto
        sys.stdout.reconfigure(encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
