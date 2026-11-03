"""Trazabilidad de la validacion de ejecutabilidad de las meta-ordenes (tarea 2.3.3, paso 5).

Elaborado por BF con apoyo de Claude Code.

No corre ABIDES: busca, para cada orden de `meta_ordenes_v2.json`, las corridas de TWAP ya hechas por el runner
de la 2.3.4 (`scripts/colab/benchmarks_meta_ordenes_ps.py`, versionadas en data/colab_resultados/) con el mismo
id, activo, tramo de inicio y cantidad, y resume el cumplimiento (`execution_rate`) por semilla. Criterio del plan
(fijado antes de ver datos): una orden es ejecutable si TWAP completa al menos el 95 % en promedio.

Las corridas no guardan la semilla de la orden, solo la de la corrida (1, 2, ...); el runner usa
`semilla de la orden + semilla de la corrida`. La semilla de la orden se deduce del id: el reparto y
`semilla = 9000 + 10 * indice` no cambiaron entre las versiones del archivo (lo comprueba un test).

    python scripts/validar_meta_ordenes.py      # escribe data/analysis/validacion_meta_ordenes_2.3.3.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
UMBRAL = 0.95
ESTRATEGIA = "TWAP"
SIN_VALIDAR = "sin validar con ABIDES"
FUENTES = {
    "base_100000": "data/colab_resultados/benchmarks_meta_ordenes_abides.json",
    "pct10": "data/colab_resultados/benchmarks_meta_ordenes_abides_pct10.json",
    "pct05_cierre": "data/colab_resultados/benchmarks_meta_ordenes_abides_pct05_cierre.json",
}


def corridas_twap(estado: Dict) -> List[Dict]:
    """Corridas de TWAP sin error de un archivo del runner."""
    return [c for c in estado.get("corridas", {}).values()
            if c.get("estrategia") == ESTRATEGIA and "error" not in c and c.get("execution_rate") is not None]


def trazar(ordenes: Sequence[Dict], fuentes: Dict[str, Dict], umbral: float = UMBRAL) -> List[Dict]:
    """Una fila por orden con las corridas de TWAP que calzan exactamente (id, activo, tramo y cantidad)."""
    filas = []
    for o in ordenes:
        hits = [(nombre, c) for nombre, est in fuentes.items() for c in corridas_twap(est)
                if c.get("orden") == o["id"] and c.get("ticker") == o["ticker"]
                and c.get("tramo_inicio") == o["tramo_inicio"] and int(c.get("cantidad", -1)) == int(o["cantidad"])]
        fila = {"id": o["id"], "ticker": o["ticker"], "tramo_inicio": o["tramo_inicio"], "cantidad": int(o["cantidad"]),
                "semilla": o.get("semilla")}
        if not hits:
            fila.update({"estado": SIN_VALIDAR, "corridas": [], "media": None, "ejecutable": None})
        else:
            hits.sort(key=lambda h: int(h[1]["seed"]))
            tasas = [float(c["execution_rate"]) for _, c in hits]
            media = float(np.mean(tasas))
            fila.update({
                "estado": "validada",
                "corridas": [{"fuente": n, "seed_corrida": int(c["seed"]),
                              "semilla_efectiva": None if o.get("semilla") is None else int(o["semilla"]) + int(c["seed"]),
                              "execution_rate": float(c["execution_rate"])} for n, c in hits],
                "media": media, "corridas_sobre_umbral": sum(t >= umbral for t in tasas), "n_corridas": len(tasas),
                "ejecutable": media >= umbral,
            })
        filas.append(fila)
    return filas


def resumen_fuente(estado: Dict, umbral: float = UMBRAL) -> Dict:
    """Cuantas ordenes de un archivo del runner son ejecutables (media de TWAP >= umbral) y cuantas corridas llegan."""
    por_orden: Dict[str, List[float]] = {}
    for c in corridas_twap(estado):
        por_orden.setdefault(c["orden"], []).append(float(c["execution_rate"]))
    medias = {k: float(np.mean(v)) for k, v in por_orden.items()}
    tasas = [t for v in por_orden.values() for t in v]
    return {"n_ordenes": len(medias), "ordenes_ejecutables": sum(m >= umbral for m in medias.values()),
            "n_corridas": len(tasas), "corridas_sobre_umbral": sum(t >= umbral for t in tasas),
            "no_ejecutables": sorted(k for k, m in medias.items() if m < umbral)}


def _leer(path: Path) -> Dict:
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def main(argv: Optional[Sequence[str]] = None) -> Path:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--meta-ordenes", default=str(REPO_ROOT / "data/meta_ordenes/meta_ordenes_v2.json"))
    ap.add_argument("--salida", default=str(REPO_ROOT / "data/analysis/validacion_meta_ordenes_2.3.3.json"))
    args = ap.parse_args(argv)
    ordenes = _leer(Path(args.meta_ordenes))["meta_ordenes"]
    fuentes = {n: _leer(REPO_ROOT / r) for n, r in FUENTES.items()}
    filas = trazar(ordenes, fuentes)
    out = {
        "tarea": "2.3.3", "criterio": f"media de execution_rate de {ESTRATEGIA} >= {UMBRAL}",
        "meta_ordenes": Path(args.meta_ordenes).resolve().relative_to(REPO_ROOT).as_posix(),
        "fuentes": FUENTES,
        "resumen_por_fuente": {n: resumen_fuente(e) for n, e in fuentes.items()},
        "ordenes": filas,
        "sin_validar": [f["id"] for f in filas if f["estado"] == SIN_VALIDAR],
    }
    p = Path(args.salida)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for f in filas:
        if f["estado"] == SIN_VALIDAR:
            print(f"  {f['id']} {f['ticker']:9s} {f['tramo_inicio']:13s} {f['cantidad']:>7d}  {SIN_VALIDAR}")
            continue
        por = " / ".join(f"{100 * c['execution_rate']:.1f} %" for c in f["corridas"])
        print(f"  {f['id']} {f['ticker']:9s} {f['tramo_inicio']:13s} {f['cantidad']:>7d}  {por}  media {100 * f['media']:.1f} %"
              f"  {'ejecutable' if f['ejecutable'] else 'NO ejecutable'}")
    for n, r in out["resumen_por_fuente"].items():
        print(f"  {n}: {r['ordenes_ejecutables']}/{r['n_ordenes']} ordenes, {r['corridas_sobre_umbral']}/{r['n_corridas']} corridas")
    print(f"Guardado: {p}")
    return p


if __name__ == "__main__":
    main()
