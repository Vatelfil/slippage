"""Estabilidad de la regla de vigilancia de D3: varias semillas de red por opcion de R_E -- Colab.

BORRADOR elaborado por PS con apoyo de Claude Code (adelanto del Sprint 6). La decision D3 es de BF.

Repite el entrenamiento inicial de la 2.3.5 (`entrenamiento_inicial_ps.py`, 100 episodios, apertura, FALABELLA) con
varias semillas de red, para la opcion 0 de R_E (riesgo sobre lo ejecutado) y la opcion A (riesgo sobre lo pendiente), y
deja una carpeta por corrida. Responde si el cumplimiento bajo 95 % de la corrida unica era casualidad de esa red o una
tendencia de la opcion 0. Despues se resume con `scripts/analizar_estabilidad_D3.py`.

    PYTHONPATH=. python scripts/colab/d3_estabilidad_ps.py --out-dir <carpeta_de_drive>/d3_estabilidad --max-minutes 150
    # repartir en dos cuadernos:  --opciones 0   y   --opciones A

Semillas de red por defecto: 1000 (repite la corrida del Sprint 5), 2000, 3000, 4000 y 6000. Los episodios de
entrenamiento usan `semilla + k` (k = 1..100); se evita 5000 porque sus episodios (5001-5100) pisarian las semillas de
evaluacion 5001-5015. Es reanudable: cada corrida guarda su estado y las terminadas se saltan.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

SEMILLAS_RED = (1000, 2000, 3000, 4000, 6000)
OPCIONES = {"0": "ejecutado", "A": "pendiente"}   # opcion de D3 -> valor de --riesgo-sobre
TRAMO = "apertura"


def _entrenamiento():
    spec = importlib.util.spec_from_file_location("entrenamiento_inicial_ps", REPO_ROOT / "scripts/colab/entrenamiento_inicial_ps.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def carpeta(out_dir: Path, opcion: str, semilla: int) -> Path:
    return out_dir / f"d3_opcion{opcion}_s{semilla}"


def terminada(out_dir: Path, opcion: str, semilla: int) -> bool:
    import json
    f = carpeta(out_dir, opcion, semilla) / f"entrenamiento_inicial_{TRAMO}.json"
    if not f.exists():
        return False
    with open(f, "r", encoding="utf-8") as fh:
        return "vigilancia_D3" in json.load(fh)


def plan(out_dir: Path, opciones: Sequence[str], semillas: Sequence[int]) -> List[tuple]:
    """Corridas pendientes (opcion, semilla), alternando opciones para que un corte deje ambas representadas."""
    return [(o, s) for s in semillas for o in opciones if not terminada(out_dir, o, s)]


def main(argv: Optional[Sequence[str]] = None) -> List[Path]:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--calibrated-json", default=str(REPO_ROOT / "data/calibration/rmsc04_ipsa_FALABELLA_2026-08-23.json"))
    ap.add_argument("--entorno", choices=["abides", "poisson"], default="abides")
    ap.add_argument("--opciones", nargs="+", choices=list(OPCIONES), default=list(OPCIONES))
    ap.add_argument("--semillas", nargs="+", type=int, default=list(SEMILLAS_RED))
    ap.add_argument("--episodes", type=int, default=100)
    ap.add_argument("--eval-seeds", type=int, default=15)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--max-minutes", type=float, default=None)
    args = ap.parse_args(argv)

    t_ini = time.time()
    out_dir = Path(args.out_dir)
    entrenar = _entrenamiento()
    pendientes = plan(out_dir, args.opciones, args.semillas)
    print(f"{len(pendientes)} corridas pendientes de {len(args.opciones) * len(args.semillas)}", flush=True)
    estados: List[Path] = []
    for opcion, semilla in pendientes:
        restante = None if args.max_minutes is None else args.max_minutes - (time.time() - t_ini) / 60
        if restante is not None and restante <= 0:
            print("Presupuesto de tiempo agotado: volver a ejecutar para continuar.")
            break
        print(f"\n===== opcion {opcion} (riesgo sobre {OPCIONES[opcion]}), semilla de red {semilla} =====", flush=True)
        cmd = ["--calibrated-json", args.calibrated_json, "--entorno", args.entorno, "--tramo", TRAMO,
               "--episodes", str(args.episodes), "--seed", str(semilla), "--eval-seeds", str(args.eval_seeds),
               "--riesgo-sobre", OPCIONES[opcion], "--out-dir", str(carpeta(out_dir, opcion, semilla))]
        if restante is not None:
            cmd += ["--max-minutes", f"{restante:.2f}"]
        estados.append(entrenar.main(cmd))
    faltan = plan(out_dir, args.opciones, args.semillas)
    print(f"\nTerminadas: {len(args.opciones) * len(args.semillas) - len(faltan)}; faltan {len(faltan)}.")
    if faltan:
        print("Volver a ejecutar el mismo comando para continuar.")
    return estados


if __name__ == "__main__":
    main()
