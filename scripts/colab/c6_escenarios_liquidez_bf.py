"""C-6: ¿los escenarios de liquidez cambian el costo como se espera? (tarea 3.1.3; Colab con ABIDES, o Poisson en el PC).

BORRADOR de PS para BF (29 oct 2026), con apoyo de Claude Code.

Antes de gastar las 90 corridas hay que comprobar que el escenario "baja" de verdad cuesta más que "media" y que "alta"
cuesta menos. Se usan las heurísticas de siempre (comprar todo a mercado y TWAP con órdenes límite) con dos tamaños de
slice, en las MISMAS semillas para los tres escenarios, y se compara de forma pareada.

    PYTHONPATH=. python scripts/colab/c6_escenarios_liquidez_bf.py --out <drive>/c6_liquidez/c6_liquidez.json
    PYTHONPATH=. python scripts/colab/c6_escenarios_liquidez_bf.py --entorno poisson --n-semillas 10 --out /tmp/c6.json

Reanudable: guarda tras cada combinación (escenario, heurística, tamaño).
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.envs import escenarios_liquidez as el  # noqa: E402
from src.envs.rmsc04_search import load_resumable, save_json  # noqa: E402
from src.experiments import beta_phase2 as bp  # noqa: E402

HEURISTICAS = ("agresiva_market", "twap_limit_medio")


def fabrica(entorno: str, factor: float, calibrated_json: str, ticker: str, claves=el.CLAVES_ABIDES):
    if entorno == "abides":
        return el.fabrica_abides(calibrated_json, ticker=ticker, factor=factor, claves=claves)
    return el.fabrica_poisson(factor, ticker=ticker)


def ic_pareado(a: Sequence[float], b: Sequence[float], n_boot: int = 3000, seed: int = 0) -> Dict[str, float]:
    """Diferencia media a − b por semilla con IC 95 % por bootstrap (se ignoran las semillas sin dato)."""
    d = np.array([x - y for x, y in zip(a, b) if x is not None and y is not None], dtype=float)
    d = d[np.isfinite(d)]
    if len(d) < 2:
        return {"n": int(len(d)), "media": float("nan"), "ic_bajo": float("nan"), "ic_alto": float("nan")}
    rng = np.random.default_rng(seed)
    medias = rng.choice(d, size=(n_boot, len(d)), replace=True).mean(axis=1)
    return {"n": int(len(d)), "media": float(d.mean()), "ic_bajo": float(np.percentile(medias, 2.5)),
            "ic_alto": float(np.percentile(medias, 97.5))}


def analizar(resultados: Dict[str, Dict], escenarios: Sequence[str], tamanos: Sequence[int]) -> List[Dict]:
    """Por heurística y tamaño: costo medio de cada escenario y diferencias pareadas baja − media y media − alta."""
    filas = []
    for h in HEURISTICAS:
        for q in tamanos:
            claves = {e: f"{e}|{h}|{q}" for e in escenarios}
            if not all(c in resultados for c in claves.values()):
                continue
            por = {e: resultados[claves[e]]["slippage_por_semilla"] for e in escenarios}
            fila = {"heuristica": h, "q_slice": q,
                    **{f"slippage_{e}": resultados[claves[e]]["slippage_bps_medio"] for e in escenarios},
                    **{f"cumplimiento_{e}": resultados[claves[e]]["cumplimiento_medio"] for e in escenarios}}
            if {"baja", "media"} <= set(escenarios):
                fila["baja_menos_media"] = ic_pareado(por["baja"], por["media"])
            if {"media", "alta"} <= set(escenarios):
                fila["media_menos_alta"] = ic_pareado(por["media"], por["alta"])
            filas.append(fila)
    return filas


def veredicto(filas: Sequence[Dict], criterio: Optional[Dict] = None) -> str:
    """Juzga con la heurística y los tamaños del `criterio_c6` del JSON, fijados antes de correr (la v1 usa la compra a
    mercado, que en Poisson es la que depende de la profundidad). OK si en esas filas la liquidez baja cuesta más que la
    media (IC sobre 0) y la alta no cuesta más que la media; las demás filas se informan pero no deciden."""
    criterio = criterio or {"heuristica": "agresiva_market", "tamanos": None}
    agresivas = [f for f in filas if f["heuristica"] == criterio["heuristica"]
                 and (not criterio.get("tamanos") or f["q_slice"] in criterio["tamanos"])]
    if not agresivas:
        return "SIN DATOS"
    malos = [f"q={f['q_slice']}" for f in agresivas
             if not (f.get("baja_menos_media", {}).get("ic_bajo", -1) > 0 and f.get("media_menos_alta", {}).get("media", -1) >= 0)]
    if not malos:
        return f"OK: con {criterio['heuristica']} la liquidez baja cuesta más y la alta no cuesta más"
    return (f"REVISAR: con {criterio['heuristica']} no se distingue el orden esperado en " + ", ".join(malos) +
            " (ajustar los factores o subir las semillas)")


def main(argv: Optional[Sequence[str]] = None) -> Path:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--entorno", choices=["abides", "poisson"], default="abides")
    ap.add_argument("--calibrated-json", default=str(REPO_ROOT / "data/calibration/rmsc04_ipsa_FALABELLA_2026-08-23.json"))
    ap.add_argument("--ticker", default="FALABELLA")
    ap.add_argument("--escenarios-json", default=str(el.ESCENARIOS_JSON))
    ap.add_argument("--tramo", default="apertura")
    ap.add_argument("--tamanos", nargs="+", type=int, default=[1000, 5000])
    ap.add_argument("--ventana-min", type=int, default=15)
    ap.add_argument("--n-semillas", type=int, default=30)
    ap.add_argument("--seed-base", type=int, default=8000, help="semillas distintas de entrenamiento y evaluación")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    escenarios = el.cargar_escenarios(args.escenarios_json)
    claves = el.claves_de(args.escenarios_json)
    criterio = el.criterio_de(args.escenarios_json)
    out = Path(args.out)
    firma = {"tarea": "3.1.3-C6", "entorno": args.entorno, "ticker": args.ticker, "tramo": args.tramo,
             "tamanos": args.tamanos, "ventana_min": args.ventana_min, "n_semillas": args.n_semillas,
             "seed_base": args.seed_base, "escenarios": escenarios}
    if tuple(claves) != el.CLAVES_ABIDES:
        firma["claves_abides"] = list(claves)
    estado = load_resumable(out, firma)
    res = estado.setdefault("resultados", {})
    seeds = [args.seed_base + i for i in range(1, args.n_semillas + 1)]
    for e, factor in escenarios.items():
        fab = fabrica(args.entorno, factor, args.calibrated_json, args.ticker, claves)
        for h in HEURISTICAS:
            for q in args.tamanos:
                clave = f"{e}|{h}|{q}"
                if clave in res:
                    continue
                t0 = time.time()
                eps = bp.evaluar_heuristica(h, fab, args.entorno, args.tramo, seeds, q, args.ventana_min)
                r = bp.resumen_evaluacion(eps, 0.0)
                r.update({"escenario": e, "factor": factor, "heuristica": h, "q_slice": q, "segundos": round(time.time() - t0, 1)})
                res[clave] = r
                save_json(out, estado)
                print(f"{clave}: slippage {r['slippage_bps_medio']:.2f} bps, cumplimiento {r['cumplimiento_medio']:.3f} "
                      f"({r['segundos']:.0f} s)", flush=True)
    estado["analisis"] = analizar(res, list(escenarios), args.tamanos)
    estado["veredicto"] = veredicto(estado["analisis"], criterio)
    save_json(out, estado)
    for f in estado["analisis"]:
        print(f"{f['heuristica']:18s} q={f['q_slice']:6d}  " +
              "  ".join(f"{e} {f[f'slippage_{e}']:.2f}" for e in escenarios) +
              f"  | baja-media {f.get('baja_menos_media', {}).get('media', float('nan')):.2f} "
              f"media-alta {f.get('media_menos_alta', {}).get('media', float('nan')):.2f}")
    print(estado["veredicto"])
    return out


if __name__ == "__main__":
    main()
