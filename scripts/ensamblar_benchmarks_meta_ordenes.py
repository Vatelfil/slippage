"""Ensambla resultados de benchmarks de varias corridas en un solo archivo (tarea 2.3.4).

Elaborado por PS con apoyo de Claude Code.

Sirve cuando las 10 meta-ordenes de un archivo candidato se corrieron en tandas con tamanos distintos (por ejemplo,
las ordenes de apertura y media jornada con 10 % del dia y las de cierre con 5 %). Cada orden conserva su semilla de
orden (`semilla = 9000 + 10 * indice`), asi que las corridas de una tanda y otra son comparables sin repetirlas.

    python scripts/ensamblar_benchmarks_meta_ordenes.py \
        --parte "data/colab_resultados/benchmarks_meta_ordenes_abides_pct10.json:MO-01,MO-02,MO-03,MO-04,MO-05,MO-06,MO-07" \
        --parte "data/colab_resultados/benchmarks_meta_ordenes_abides_pct05_cierre.json:MO-08,MO-09,MO-10" \
        --meta-ordenes data/meta_ordenes/meta_ordenes_v2_candidata.json \
        --salida data/colab_resultados/benchmarks_meta_ordenes_abides_v2.json

Comprueba que cada orden aparezca en una sola parte, que la cantidad de cada corrida coincida con la del archivo de
meta-ordenes y que todas las ordenes tengan las mismas semillas.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _resumen(estado: Dict) -> Dict:
    """Reutiliza `resumen` del corredor de benchmarks (IS medio y error estandar por orden y estrategia)."""
    spec = importlib.util.spec_from_file_location("bench_runner", REPO_ROOT / "scripts/colab/benchmarks_meta_ordenes_ps.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.resumen(estado)


def _leer(path: str) -> Dict:
    with open(path, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def ensamblar(partes: Sequence[Tuple[Dict, Optional[Sequence[str]]]], meta_ordenes: Optional[Dict] = None) -> Dict:
    """`partes`: lista de (estado, ids de las ordenes que se toman de ese estado; None = todas)."""
    corridas: Dict[str, Dict] = {}
    origen: Dict[str, int] = {}
    for k, (estado, ids) in enumerate(partes):
        for clave, c in estado.get("corridas", {}).items():
            if "error" in c or (ids is not None and c["orden"] not in ids):
                continue
            if c["orden"] in origen and origen[c["orden"]] != k:
                raise ValueError(f"la orden {c['orden']} aparece en mas de una parte")
            origen[c["orden"]] = k
            corridas[clave] = c
    if not corridas:
        raise ValueError("no hay corridas para ensamblar")
    if meta_ordenes is not None:
        cant = {o["id"]: o["cantidad"] for o in (meta_ordenes["meta_ordenes"] if isinstance(meta_ordenes, dict) else meta_ordenes)}
        for c in corridas.values():
            if c["orden"] in cant and int(c["cantidad"]) != int(cant[c["orden"]]):
                raise ValueError(f"{c['orden']}: la corrida tiene {c['cantidad']} acciones y el archivo de ordenes {cant[c['orden']]}")
    semillas: Dict[str, set] = {}
    for c in corridas.values():
        semillas.setdefault(c["orden"], set()).add(int(c["seed"]))
    distintos = {tuple(sorted(v)) for v in semillas.values()}
    if len(distintos) > 1:
        raise ValueError(f"las ordenes no tienen las mismas semillas: {sorted(distintos)}")
    base = partes[0][0].get("firma", {})
    cantidades = {}
    for c in corridas.values():
        cantidades[c["orden"]] = c["cantidad"]
    estado = {"firma": {"tarea": base.get("tarea", "2.3.4"), "entorno": base.get("entorno"), "snapshot": base.get("snapshot"),
                        "ordenes": sorted(cantidades), "cantidades": dict(sorted(cantidades.items())),
                        "ensamblado": True},
              "resultados": {}, "corridas": dict(sorted(corridas.items()))}
    estado["resumen"] = _resumen(estado)
    return estado


def _parte(valor: str) -> Tuple[str, Optional[List[str]]]:
    """'archivo.json:MO-01,MO-02' -> (archivo, [ids]); sin ':MO...' se toma el archivo completo (incluye rutas de Windows con unidad)."""
    ruta, sep, ids = valor.rpartition(":")
    if sep and ids.strip().upper().startswith("MO"):
        return ruta, [i.strip() for i in ids.split(",") if i.strip()]
    return valor, None


def main(argv: Optional[Sequence[str]] = None) -> Path:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--parte", action="append", required=True, metavar="ARCHIVO.json[:MO-01,MO-02,...]")
    ap.add_argument("--meta-ordenes", default=None)
    ap.add_argument("--salida", required=True)
    args = ap.parse_args(argv)
    partes = []
    for v in args.parte:
        ruta, ids = _parte(v)
        partes.append((_leer(ruta), ids))
    meta = _leer(args.meta_ordenes) if args.meta_ordenes else None
    estado = ensamblar(partes, meta)
    out = Path(args.salida)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(estado, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(estado['corridas'])} corridas de {len(estado['firma']['ordenes'])} ordenes -> {out}")
    return out


if __name__ == "__main__":
    main()
