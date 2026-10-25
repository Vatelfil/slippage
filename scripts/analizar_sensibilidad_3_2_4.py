"""Sensibilidad del sistema frente a TWAP y VWAP por tamaño de orden, tramo horario y liquidez (tarea 3.2.4; BORRADOR de PS).

Complementa a `scripts/comparar_sistema_vs_benchmarks.py` (3.2.3). Aquella compara el sistema con cada benchmark por tamaño; esta
cruza los factores para ver **dónde** gana o pierde el sistema y si el efecto crece con el tamaño de la orden:

  - diferencia media (sistema − benchmark, en bps) por tamaño × tramo, liquidez × tamaño y liquidez × tramo, con IC 95 % por bootstrap;
  - ¿cambia la diferencia con el tamaño? Correlación de Spearman entre el tamaño (en orden) y la diferencia, y Kruskal-Wallis entre
    tamaños, entre tramos y entre escenarios de liquidez;
  - figura: diferencia frente al tamaño, una línea por tramo.

Cada escenario es un par de archivos (benchmarks y sistema, con el formato de `benchmarks_meta_ordenes_ps.py`) con las mismas
órdenes y semillas. Con las 90 corridas del plan (3 liquidez × 3 tamaños × 10 semillas) se pasan 9 escenarios:

    python scripts/analizar_sensibilidad_3_2_4.py \\
        --escenario "pequeña:baja=bench_peq_baja.json,sis_peq_baja.json" \\
        --escenario "pequeña:media=bench_peq_media.json,sis_peq_media.json" ... \\
        --orden-tamanos pequeña mediana grande --nombre-sistema PPO

Sin `:liquidez` el escenario se toma como una sola liquidez. Con `--penalizacion-no-ejecutado BPS` se usa el costo ajustado por lo
no ejecutado (ver `comparar_sistema_vs_benchmarks.py`) en lugar del slippage, que solo cuenta lo comprado.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

_spec = importlib.util.spec_from_file_location("comparar_3_2_3", REPO_ROOT / "scripts/comparar_sistema_vs_benchmarks.py")
cmp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cmp)

BENCHMARKS = cmp.BENCHMARKS


def _f(x: Optional[float], d: int = 2) -> str:
    return cmp._f(x, d)


def parse_escenario(valor: str) -> Tuple[str, str, str, str]:
    """'TAMANO:LIQUIDEZ=bench.json,sistema.json' -> (tamano, liquidez, bench, sistema)."""
    clave, sep, resto = valor.partition("=")
    partes = resto.split(",")
    if not sep or len(partes) != 2 or not all(partes):
        raise argparse.ArgumentTypeError(f"se esperaba TAMANO[:LIQUIDEZ]=benchmarks.json,sistema.json, llegó {valor!r}")
    tam, _, liq = clave.partition(":")
    return tam, liq or "única", partes[0], partes[1]


def filas(escenarios: Sequence[Tuple[str, str, str, str]], nombre_sistema: str, benchmark: str,
          penalizacion_bps: Optional[float] = None) -> List[Dict]:
    """Una fila por celda (orden × semilla × escenario) con la diferencia sistema − benchmark."""
    out: List[Dict] = []
    for tam, liq, bpath, spath in escenarios:
        res = cmp.comparar(cmp.cargar(bpath), cmp.cargar(spath), nombre_sistema,
                           penalizaciones=[penalizacion_bps] if penalizacion_bps is not None else ())
        info = res["benchmarks"][benchmark]
        for f in info["filas"]:
            if penalizacion_bps is None:
                dif = f["dif"]
            else:
                dif = (cmp.costo_ajustado(f["slip_sistema"], f["cumpl_sistema"], penalizacion_bps)
                       - cmp.costo_ajustado(f["slip_bench"], f["cumpl_bench"], penalizacion_bps))
            out.append({"tamano": tam, "liquidez": liq, "tramo": str(f["tramo"]), "ticker": f["ticker"], "orden": f["orden"],
                        "seed": f["seed"], "dif": float(dif)})
    return out


def agrupar(filas_: Sequence[Dict], a: str, b: str, rng: np.random.Generator) -> Dict[Tuple[str, str], Dict]:
    """Resumen de la diferencia por cada combinación de los factores `a` y `b`."""
    grupos: Dict[Tuple[str, str], List[float]] = {}
    for f in filas_:
        grupos.setdefault((f[a], f[b]), []).append(f["dif"])
    return {k: cmp.resumen_dif(v, rng) for k, v in grupos.items()}


def pruebas(filas_: Sequence[Dict], orden_tamanos: Sequence[str]) -> Dict:
    """Spearman entre el tamaño y la diferencia, y Kruskal-Wallis entre tamaños, tramos y escenarios de liquidez."""
    out: Dict = {}
    idx = {t: i for i, t in enumerate(orden_tamanos)}
    x = np.array([idx[f["tamano"]] for f in filas_ if f["tamano"] in idx], float)
    y = np.array([f["dif"] for f in filas_ if f["tamano"] in idx], float)
    if len(set(x)) >= 2 and len(x) >= 6 and np.std(y) > 0:
        r = stats.spearmanr(x, y)
        out["spearman_tamano"] = {"rho": float(r.statistic), "p": float(r.pvalue), "n": int(len(x))}
    for factor in ("tamano", "tramo", "liquidez"):
        grupos: Dict[str, List[float]] = {}
        for f in filas_:
            grupos.setdefault(f[factor], []).append(f["dif"])
        validos = [v for v in grupos.values() if len(v) >= 3]
        if len(validos) >= 2 and np.std(np.concatenate(validos)) > 0:
            h = stats.kruskal(*validos)
            out[f"kruskal_{factor}"] = {"H": float(h.statistic), "p": float(h.pvalue), "grupos": len(validos)}
    return out


def resumen(escenarios, nombre_sistema: str, orden_tamanos: Optional[Sequence[str]] = None,
            penalizacion_bps: Optional[float] = None, semilla: int = 0) -> Dict:
    orden = list(orden_tamanos) if orden_tamanos else list(dict.fromkeys(e[0] for e in escenarios))
    rng = np.random.default_rng(semilla)
    out: Dict = {"orden_tamanos": orden, "penalizacion_bps": penalizacion_bps, "benchmarks": {}}
    for b in BENCHMARKS:
        fs = filas(escenarios, nombre_sistema, b, penalizacion_bps)
        out["benchmarks"][b] = {
            "n_celdas": len(fs),
            "tamano_x_tramo": {f"{k[0]}|{k[1]}": v for k, v in agrupar(fs, "tamano", "tramo", rng).items()},
            "liquidez_x_tamano": {f"{k[0]}|{k[1]}": v for k, v in agrupar(fs, "liquidez", "tamano", rng).items()},
            "liquidez_x_tramo": {f"{k[0]}|{k[1]}": v for k, v in agrupar(fs, "liquidez", "tramo", rng).items()},
            "pruebas": pruebas(fs, orden) if fs else {},
        }
    return out


def _tabla(grupos: Dict[str, Dict], filas_lab: Sequence[str], cols_lab: Sequence[str], nombre_filas: str) -> List[str]:
    L = [f"| {nombre_filas} | " + " | ".join(cols_lab) + " |", "|---|" + "---:|" * len(cols_lab)]
    for r in filas_lab:
        celdas = []
        for c in cols_lab:
            g = grupos.get(f"{r}|{c}")
            celdas.append("—" if not g or g["dif_media"] is None else
                          f"{_f(g['dif_media'])} [{_f(g['ic95'][0], 1)}; {_f(g['ic95'][1], 1)}] (n={g['n']})")
        L.append(f"| {r} | " + " | ".join(celdas) + " |")
    return L


def informe(res: Dict, nombre_sistema: str) -> str:
    orden = res["orden_tamanos"]
    pen = res["penalizacion_bps"]
    L = ["# Sensibilidad del sistema por tamaño, tramo y liquidez (tarea 3.2.4)", "",
         f"**Borrador elaborado por:** PS con apoyo de Claude Code. **Sistema:** {nombre_sistema} · **Fecha:** {time.strftime('%Y-%m-%d')}", "",
         "Diferencia = costo del sistema − costo del benchmark, en bps, pareada por orden y semilla (negativa = el sistema cuesta menos). "
         + ("Costo ajustado por lo no ejecutado con una penalización de " + _f(pen, 0) + " bps."
            if pen is not None else "Se usa el slippage de lo comprado (no incluye lo no ejecutado).")
         + " Cada celda de las tablas: media [IC 95 % por bootstrap] (n).", ""]
    for b, r in res["benchmarks"].items():
        L += [f"## Frente a {b} ({r['n_celdas']} celdas)", ""]
        if not r["n_celdas"]:
            L += ["Sin celdas comparables.", ""]
            continue
        tramos = sorted({k.split("|")[1] for k in r["tamano_x_tramo"]})
        liqs = sorted({k.split("|")[0] for k in r["liquidez_x_tamano"]})
        L += ["### Tamaño × tramo de inicio", ""] + _tabla(r["tamano_x_tramo"], orden, tramos, "Tamaño") + [""]
        if len(liqs) > 1:
            L += ["### Liquidez × tamaño", ""] + _tabla(r["liquidez_x_tamano"], liqs, orden, "Liquidez") + [""]
            L += ["### Liquidez × tramo", ""] + _tabla(r["liquidez_x_tramo"], liqs, tramos, "Liquidez") + [""]
        p = r["pruebas"]
        L += ["### ¿Cambia la diferencia con el tamaño o el tramo?", ""]
        if "spearman_tamano" in p:
            s = p["spearman_tamano"]
            L.append(f"- Spearman entre el tamaño (en orden {' < '.join(orden)}) y la diferencia: ρ = {_f(s['rho'], 2)}, p = {_f(s['p'], 3)} (n = {s['n']}).")
        for factor, nombre in (("tamano", "tamaños"), ("tramo", "tramos"), ("liquidez", "escenarios de liquidez")):
            k = p.get(f"kruskal_{factor}")
            if k:
                L.append(f"- Kruskal-Wallis entre {nombre}: H = {_f(k['H'], 2)}, p = {_f(k['p'], 3)} ({k['grupos']} grupos).")
        L.append("")
    L += ["## Limitaciones", "",
          "- Las semillas de una orden se parecen entre sí; las pruebas por celda subestiman la incertidumbre. Con pocas órdenes por grupo, las tablas son orientativas.",
          "- Con pocos grupos (n < 3 por grupo) no se calculan las pruebas.",
          "- Una diferencia que cambia con el tamaño puede deberse también a que el cumplimiento cambia con el tamaño: conviene mirarla junto con el costo ajustado.", "",
          "🤖 Generado con [Claude Code](https://claude.com/claude-code)", ""]
    return "\n".join(L)


def figura(res: Dict, ruta: Path) -> Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    orden = res["orden_tamanos"]
    fig, ax = plt.subplots(1, len(BENCHMARKS), figsize=(6.2 * len(BENCHMARKS), 4.4), sharey=True)
    colores = ["#0F6E56", "#534AB7", "#993C1D", "#854F0B"]
    for a, b in zip(np.atleast_1d(ax), BENCHMARKS):
        r = res["benchmarks"][b]
        tramos = sorted({k.split("|")[1] for k in r["tamano_x_tramo"]})
        for j, tr in enumerate(tramos):
            xs, ys, lo, hi = [], [], [], []
            for i, tam in enumerate(orden):
                g = r["tamano_x_tramo"].get(f"{tam}|{tr}")
                if g and g["dif_media"] is not None:
                    xs.append(i + 0.06 * (j - (len(tramos) - 1) / 2))
                    ys.append(g["dif_media"])
                    lo.append(g["dif_media"] - (g["ic95"][0] if g["ic95"][0] is not None else g["dif_media"]))
                    hi.append((g["ic95"][1] if g["ic95"][1] is not None else g["dif_media"]) - g["dif_media"])
            if xs:
                a.errorbar(xs, ys, yerr=[lo, hi], marker="o", capsize=3, color=colores[j % 4], label=tr.replace("_", " "))
        a.axhline(0, color="k", lw=0.7)
        a.set_xticks(range(len(orden)), orden)
        a.set_title(f"Sistema − {b} (bps)")
        a.set_xlabel("tamaño de la orden")
        a.grid(alpha=0.3)
        a.spines[["top", "right"]].set_visible(False)
    np.atleast_1d(ax)[0].set_ylabel("diferencia (bps); negativa = el sistema cuesta menos")
    np.atleast_1d(ax)[0].legend(title="tramo de inicio", fontsize=8)
    fig.tight_layout()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta, dpi=140)
    plt.close(fig)
    return ruta


def main(argv: Optional[Sequence[str]] = None) -> Path:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--escenario", action="append", type=parse_escenario, required=True, metavar="TAMANO[:LIQUIDEZ]=BENCHMARKS.json,SISTEMA.json")
    ap.add_argument("--nombre-sistema", default="PPO")
    ap.add_argument("--orden-tamanos", nargs="*", default=None, help="tamaños de menor a mayor (por defecto, el orden en que aparecen)")
    ap.add_argument("--penalizacion-no-ejecutado", type=float, default=None, metavar="BPS")
    ap.add_argument("--out-md", default=str(REPO_ROOT / "docs/sensibilidad_3_2_4.md"))
    ap.add_argument("--out-png", default=str(REPO_ROOT / "data/analysis/sensibilidad_3_2_4.png"))
    ap.add_argument("--out-json", default=str(REPO_ROOT / "data/analysis/sensibilidad_3_2_4.json"))
    args = ap.parse_args(argv)
    res = resumen(args.escenario, args.nombre_sistema, args.orden_tamanos, args.penalizacion_no_ejecutado)
    for p in (args.out_md, args.out_png, args.out_json):
        Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    figura(res, Path(args.out_png))
    Path(args.out_md).write_text(informe(res, args.nombre_sistema), encoding="utf-8")
    print(f"Informe: {args.out_md}")
    return Path(args.out_md)


if __name__ == "__main__":
    main()
