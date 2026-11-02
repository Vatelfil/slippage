"""Elige el Ejecutor PPO del sistema final con una regla fijada antes de ver las 30 corridas (cierre del Sprint 6).

Regla: entre todas las redes PPO reevaluadas en las mismas 300 semillas (`red_*.json` de la carpeta de reevaluación), gana
la de menor slippage medio que cumpla al menos el 95 % de la orden muestreando su política. Las heurísticas (`ref_*`) y los
controles sin entrenar no compiten, y tampoco las redes solo imitadas (raíces que terminan en `_bc`), que no pasaron por
PPO: el Título I pide Ejecutores entrenados con PPO (objetivo específico 2).

Escribe `ejecutor_elegido.json` con la etiqueta, la ruta del checkpoint en Drive y los números que justifican la elección.

    PYTHONPATH=. python scripts/elegir_ejecutor_ps.py --reeval-dir <drive>/reeval_300 --results-dir <drive> --out <drive>/sistema_final
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Sequence

CUMPLIMIENTO_MIN = 0.95
PATRON = re.compile(r"^red_(?P<raiz>.+)__(?P<carpeta>d3_opcion[0A]_s\d+)$")


def candidatas(reeval_dir: Path) -> List[Dict]:
    out = []
    for f in sorted(Path(reeval_dir).glob("red_*.json")):
        m = PATRON.match(f.stem)
        if not m or m["raiz"].endswith("_bc"):
            continue
        r = json.loads(f.read_text(encoding="utf-8"))
        out.append({"etiqueta": f.stem[4:], "raiz": m["raiz"], "carpeta": m["carpeta"],
                    "slippage_bps": r.get("slippage_bps_medio"), "cumplimiento": r.get("cumplimiento_medio"),
                    "n": r.get("n")})
    return out


def elegir(cands: Sequence[Dict]) -> Optional[Dict]:
    validas = [c for c in cands if c["slippage_bps"] is not None and (c["cumplimiento"] or 0) >= CUMPLIMIENTO_MIN]
    return min(validas, key=lambda c: c["slippage_bps"]) if validas else None


def main(argv: Optional[Sequence[str]] = None) -> Dict:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--reeval-dir", required=True)
    ap.add_argument("--results-dir", required=True, help="carpeta que contiene las raíces de entrenamiento (resultados de Drive)")
    ap.add_argument("--tramo", default="apertura")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    cands = candidatas(Path(args.reeval_dir))
    g = elegir(cands)
    if g is None:
        raise SystemExit("Ninguna red cumple el 95 %: revisar antes de seguir.")
    ckpt = Path(args.results_dir) / g["raiz"] / g["carpeta"] / f"checkpoints_{args.tramo}" / "checkpoint_last.pt"
    if not ckpt.exists():
        raise SystemExit(f"No está el checkpoint de la red elegida: {ckpt}")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    shutil.copy(ckpt, out / "ejecutor_elegido.pt")
    res = {"regla": f"menor slippage medio en la reevaluación con cumplimiento >= {CUMPLIMIENTO_MIN}",
           "elegida": g, "checkpoint_origen": str(ckpt), "checkpoint": str(out / "ejecutor_elegido.pt"),
           "candidatas": sorted(cands, key=lambda c: (c["slippage_bps"] is None, c["slippage_bps"]))}
    (out / "ejecutor_elegido.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Elegida: {g['etiqueta']} ({g['slippage_bps']:.2f} bps, cumplimiento {g['cumplimiento']:.3f}) de {len(cands)} redes")
    return res


if __name__ == "__main__":
    main()
