"""Revalidación de λ del Maestro con una política entrenada (P10; BORRADOR de PS para MR, 29 oct 2026).

En la 2.2.2, λ = 0,05 se eligió por balance de escala: la penalización por lo no ejecutado, λ · Q_pendiente · P, debía
tener un tamaño comparable al IS sin dominarlo, medido con una política SIN entrenar
(`docs/calibracion_recompensa_maestro_2.2.2_MR.md`). Aquí se repite la cuenta con las jornadas de evaluación del
Maestro entrenado que deja `scripts/entrenar_maestro.py` (`resumen_maestro.json`).

En bps del valor de la orden, por jornada:  IS = slippage · cumplimiento  y  penalización = λ · (1 − cumplimiento) · 10⁴.

    PYTHONPATH=. python scripts/revalidar_lambda_maestro.py --resumen data/maestro/con_impacto/resumen_maestro.json

Límite: el comportamiento del Maestro depende del λ con que se entrenó. Si el cociente sale fuera del rango, lo correcto
es reentrenar con el λ propuesto y repetir esta cuenta, no solo cambiar el número.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np

LAMBDAS = (0.01, 0.02, 0.05, 0.1, 0.2)
RANGO_COCIENTE = (0.1, 1.0)     # la penalización debe pesar, pero no más que el IS (criterio de la 2.2.2)


def componentes(jornadas: Sequence[Dict], lam: float) -> Dict[str, float]:
    is_bps = np.array([j["slippage_bps"] * j["cumplimiento"] for j in jornadas if np.isfinite(j["slippage_bps"])])
    pen_bps = np.array([lam * max(0.0, 1.0 - j["cumplimiento"]) * 1e4 for j in jornadas])
    is_abs = float(np.mean(np.abs(is_bps))) if len(is_bps) else float("nan")
    pen = float(np.mean(pen_bps)) if len(pen_bps) else float("nan")
    return {"lambda": lam, "IS_bps_medio_abs": is_abs, "penalizacion_bps_media": pen,
            "cociente": pen / is_abs if is_abs and np.isfinite(is_abs) else float("nan")}


def main(argv: Optional[Sequence[str]] = None) -> List[Dict]:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--resumen", required=True, help="resumen_maestro.json de scripts/entrenar_maestro.py")
    ap.add_argument("--politica", choices=["entrenado", "sin_entrenar"], default="entrenado")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    data = json.loads(Path(args.resumen).read_text(encoding="utf-8"))
    jornadas = data[args.politica]["jornadas"]
    filas = [componentes(jornadas, lam) for lam in LAMBDAS]
    for f in filas:
        f["en_rango"] = bool(RANGO_COCIENTE[0] <= f["cociente"] <= RANGO_COCIENTE[1])
    print(f"Politica: {args.politica}; {len(jornadas)} jornadas; cumplimiento medio "
          f"{np.mean([j['cumplimiento'] for j in jornadas]):.4f}")
    for f in filas:
        print(f"lambda {f['lambda']:<5} IS {f['IS_bps_medio_abs']:.2f} bps | penalizacion {f['penalizacion_bps_media']:.2f} bps | "
              f"cociente {f['cociente']:.2f} {'(en rango)' if f['en_rango'] else ''}")
    if args.out:
        Path(args.out).write_text(json.dumps({"politica": args.politica, "rango_cociente": RANGO_COCIENTE, "filas": filas},
                                             indent=1, ensure_ascii=False), encoding="utf-8")
    return filas


if __name__ == "__main__":
    main()
