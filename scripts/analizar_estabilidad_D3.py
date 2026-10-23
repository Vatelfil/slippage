"""Resumen de la estabilidad de la regla de vigilancia de D3 (varias semillas de red por opcion de R_E).

BORRADOR elaborado por PS con apoyo de Claude Code; la decision D3 es de BF.

Lee las carpetas `d3_opcion<0|A>_s<semilla>/entrenamiento_inicial_apertura.json` que deja
`scripts/colab/d3_estabilidad_ps.py` y arma:
  - la tabla por corrida (cumplimiento y slippage con argmax y muestreando, y de la red sin entrenar);
  - cuantas semillas disparan la regla (cumplimiento con argmax < 95 %) por opcion;
  - slippage de la red entrenada frente a la sin entrenar (Wilcoxon pareado por semilla de evaluacion);
  - la figura del cumplimiento por semilla de red y opcion.
No decide: describe. Con 5 semillas por opcion la comparacion entre opciones es descriptiva (prueba exacta de Fisher).

    python scripts/analizar_estabilidad_D3.py --dir <carpeta_de_drive>/d3_estabilidad \
        --out-md docs/estabilidad_D3_PS.md --out-png data/analysis/estabilidad_D3.png
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

UMBRAL = 0.95
NOMBRE_OPCION = {"0": "Opción 0 (riesgo sobre lo ejecutado)", "A": "Opción A (riesgo sobre lo pendiente)"}


def _f(x: Optional[float], d: int = 2) -> str:
    return "—" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def cargar(dir_: Path) -> List[Dict]:
    """Una fila por corrida terminada, ordenada por opcion y semilla de red."""
    filas = []
    for carpeta in sorted(Path(dir_).glob("d3_opcion*_s*")):
        m = re.fullmatch(r"d3_opcion(0|A)_s(\d+)", carpeta.name)
        archivo = carpeta / "entrenamiento_inicial_apertura.json"
        if not m or not archivo.exists():
            continue
        with open(archivo, "r", encoding="utf-8-sig") as fh:
            e = json.load(fh)
        if "vigilancia_D3" not in e:
            continue
        ent, est, sin = e["evaluacion_entrenada"], e["evaluacion_entrenada_estocastica"], e["evaluacion_sin_entrenar"]
        filas.append({"opcion": m.group(1), "semilla": int(m.group(2)),
                      "cumpl_argmax": ent.get("cumplimiento_medio"), "cumpl_muestreo": est.get("cumplimiento_medio"),
                      "cumpl_sin_entrenar": sin.get("cumplimiento_medio"),
                      "slip_argmax": ent.get("slippage_bps_medio"), "slip_muestreo": est.get("slippage_bps_medio"),
                      "slip_sin_entrenar": sin.get("slippage_bps_medio"),
                      "por_semilla_argmax": ent.get("slippage_por_semilla", []),
                      "por_semilla_muestreo": est.get("slippage_por_semilla", []),
                      "por_semilla_sin_entrenar": sin.get("slippage_por_semilla", []),
                      "dispara_regla": not e["vigilancia_D3"]["cumple"],
                      "segundos": e.get("segundos_entrenamiento")})
    return sorted(filas, key=lambda r: (r["opcion"], r["semilla"]))


def wilcoxon_pareado(a: Sequence[Optional[float]], b: Sequence[Optional[float]]) -> Optional[float]:
    """p del Wilcoxon pareado entre dos listas (se descartan los pares con algun None)."""
    pares = [(x, y) for x, y in zip(a, b) if x is not None and y is not None and np.isfinite(x) and np.isfinite(y)]
    if len(pares) < 6 or all(x == y for x, y in pares):
        return None
    return float(stats.wilcoxon([x for x, _ in pares], [y for _, y in pares]).pvalue)


def resumen_por_opcion(filas: Sequence[Dict]) -> Dict[str, Dict]:
    out = {}
    for o in ("0", "A"):
        f = [r for r in filas if r["opcion"] == o]
        if not f:
            continue
        cu = np.array([r["cumpl_argmax"] for r in f], dtype=float)
        out[o] = {"n": len(f), "dispara": int(sum(r["dispara_regla"] for r in f)),
                  "cumpl_argmax_medio": float(cu.mean()), "cumpl_argmax_min": float(cu.min()),
                  "cumpl_muestreo_medio": float(np.mean([r["cumpl_muestreo"] for r in f])),
                  "slip_argmax_medio": float(np.nanmean([r["slip_argmax"] if r["slip_argmax"] is not None else np.nan for r in f])) if any(r["slip_argmax"] is not None for r in f) else None,
                  "slip_muestreo_medio": float(np.nanmean([r["slip_muestreo"] if r["slip_muestreo"] is not None else np.nan for r in f])) if any(r["slip_muestreo"] is not None for r in f) else None,
                  "semillas_disparan": [r["semilla"] for r in f if r["dispara_regla"]]}
    return out


def fisher(res: Dict[str, Dict]) -> Optional[float]:
    if "0" not in res or "A" not in res:
        return None
    t = [[res["0"]["dispara"], res["0"]["n"] - res["0"]["dispara"]], [res["A"]["dispara"], res["A"]["n"] - res["A"]["dispara"]]]
    return float(stats.fisher_exact(t)[1])


def informe(filas: Sequence[Dict], res: Dict[str, Dict], p_fisher: Optional[float]) -> str:
    L = ["# Estabilidad de la regla de vigilancia de D3: varias semillas de red", "",
         f"**Elaborado por:** PS con apoyo de Claude Code (uso autorizado por la universidad). **Pendiente de revisión por:** BF (decide D3) y MR. "
         f"**Fecha:** {time.strftime('%Y-%m-%d')}.", "",
         "Mismo entrenamiento inicial de la 2.3.5 (100 episodios, apertura, FALABELLA, evaluación con 15 semillas nuevas) repetido con "
         "varias semillas de red por opción de R_E. La regla fijada el 14 de octubre se dispara si el cumplimiento con argmax es menor a 95 %.", "",
         "## 1. Resultado por corrida", "",
         "| Opción | Semilla de red | Cumplimiento argmax | Cumplimiento muestreada | Cumplimiento sin entrenar | Slippage argmax (bps) | Slippage muestreada (bps) | Slippage sin entrenar (bps) | ¿Dispara la regla? |",
         "|---|---:|---:|---:|---:|---:|---:|---:|:---:|"]
    for r in filas:
        L.append(f"| {r['opcion']} | {r['semilla']} | {_f(r['cumpl_argmax'], 3)} | {_f(r['cumpl_muestreo'], 3)} | {_f(r['cumpl_sin_entrenar'], 3)} | "
                 f"{_f(r['slip_argmax'])} | {_f(r['slip_muestreo'])} | {_f(r['slip_sin_entrenar'])} | {'sí' if r['dispara_regla'] else 'no'} |")
    L += ["", "## 2. Resumen por opción", "",
          "| Opción | Redes | Disparan la regla | Cumplimiento argmax (media / mínimo) | Cumplimiento muestreada (media) | Slippage argmax medio (bps) | Slippage muestreada media (bps) |",
          "|---|---:|---:|---:|---:|---:|---:|"]
    for o, v in res.items():
        L.append(f"| {NOMBRE_OPCION[o]} | {v['n']} | **{v['dispara']} de {v['n']}** | {_f(v['cumpl_argmax_medio'], 3)} / {_f(v['cumpl_argmax_min'], 3)} | "
                 f"{_f(v['cumpl_muestreo_medio'], 3)} | {_f(v['slip_argmax_medio'])} | {_f(v['slip_muestreo_medio'])} |")
    L.append("")
    if p_fisher is not None:
        L.append(f"Comparación de cuántas redes disparan la regla en cada opción (prueba exacta de Fisher): p = {_f(p_fisher, 3)}. "
                 "Con pocas redes por opción es una guía, no una prueba concluyente.")
        L.append("")
    L += ["## 3. ¿La red entrenada cuesta menos que la sin entrenar?", "",
          "Wilcoxon pareado por semilla de evaluación (misma semilla, red entrenada frente a red sin entrenar); se omiten las corridas sin ejecuciones.", "",
          "| Opción | Semilla de red | p con argmax | p muestreada |", "|---|---:|---:|---:|"]
    for r in filas:
        L.append(f"| {r['opcion']} | {r['semilla']} | {_f(wilcoxon_pareado(r['por_semilla_argmax'], r['por_semilla_sin_entrenar']), 3)} | "
                 f"{_f(wilcoxon_pareado(r['por_semilla_muestreo'], r['por_semilla_sin_entrenar']), 3)} |")
    L += ["", "## 4. Cómo leerlo", ""]
    r0, rA = res.get("0"), res.get("A")
    if r0 and rA:
        L.append(f"- Opción 0: la regla se dispara en {r0['dispara']} de {r0['n']} redes; opción A: en {rA['dispara']} de {rA['n']}.")
        if r0["dispara"] > r0["n"] / 2 and rA["dispara"] == 0:
            L.append("- La opción 0 deja a la red sin ejecutar con argmax en la mayoría de las semillas y la opción A no: es una tendencia de la opción, no de una red.")
        elif r0["dispara"] == 0:
            L.append("- La opción 0 cumple en todas las semillas: la corrida que disparó la regla fue una excepción de esa red.")
        else:
            L.append("- Resultado mixto: la regla se dispara en algunas redes y en otras no; la decisión de D3 queda con BF y conviene mirar las semillas que disparan.")
    L += ["- El cumplimiento mide si la red ejecuta toda la orden; el costo (slippage) se compara con la red sin entrenar, que sirve de control.",
          "- Una red que elige \"esperar\" con argmax pero ejecuta al muestrearla no es lo mismo que una que no ejecuta nunca: por eso se informan ambas evaluaciones.",
          "", "🤖 Generado con [Claude Code](https://claude.com/claude-code)", ""]
    return "\n".join(L)


def figura(filas: Sequence[Dict], ruta: Path) -> Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    colores = {"0": "#d95f02", "A": "#1b9e77"}
    for i, o in enumerate(("0", "A")):
        f = [r for r in filas if r["opcion"] == o]
        x = np.full(len(f), i, dtype=float) + np.linspace(-0.12, 0.12, max(len(f), 1))[:len(f)]
        ax.scatter(x, [r["cumpl_argmax"] for r in f], s=70, color=colores[o], label="argmax", zorder=3)
        ax.scatter(x, [r["cumpl_muestreo"] for r in f], s=70, facecolors="none", edgecolors=colores[o], linewidths=1.8,
                   label="muestreada", zorder=3)
    ax.axhline(UMBRAL, color="grey", linestyle="--", linewidth=1)
    ax.text(1.45, UMBRAL + 0.01, "umbral 95 %", ha="right", color="grey", fontsize=9)
    ax.set_xticks([0, 1], ["Opción 0\n(riesgo sobre lo ejecutado)", "Opción A\n(riesgo sobre lo pendiente)"])
    ax.set_xlim(-0.5, 1.5)
    ax.set_ylim(-0.05, 1.08)
    ax.set_ylabel("Cumplimiento de la orden")
    ax.set_title("Cumplimiento por semilla de red (cada punto = una red de 100 episodios)")
    h, l = ax.get_legend_handles_labels()
    ax.legend(dict(zip(l, h)).values(), dict(zip(l, h)).keys(), loc="lower right", frameon=False, labelcolor="black")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta, dpi=140)
    plt.close(fig)
    return ruta


def main(argv: Optional[Sequence[str]] = None) -> Path:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dir", required=True, help="carpeta con las d3_opcion*_s*")
    ap.add_argument("--out-json", default=str(REPO_ROOT / "data/analysis/estabilidad_D3.json"))
    ap.add_argument("--out-png", default=str(REPO_ROOT / "data/analysis/estabilidad_D3.png"))
    ap.add_argument("--out-md", default=str(REPO_ROOT / "docs/estabilidad_D3_PS.md"))
    args = ap.parse_args(argv)
    filas = cargar(Path(args.dir))
    if not filas:
        raise SystemExit(f"No hay corridas terminadas en {args.dir}")
    res = resumen_por_opcion(filas)
    p = fisher(res)
    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).write_text(json.dumps({"corridas": filas, "resumen": res, "p_fisher": p}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    figura(filas, Path(args.out_png))
    Path(args.out_md).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_md).write_text(informe(filas, res, p), encoding="utf-8")
    print(f"Informe: {args.out_md}")
    return Path(args.out_md)


if __name__ == "__main__":
    main()
