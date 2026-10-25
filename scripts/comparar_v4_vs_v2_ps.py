"""Compara, por semilla de red y en las mismas semillas de evaluación, tres Ejecutores de ABIDES muestreando la política:
la red sin entrenar (control), la entrenada con la recompensa original + penalización + γ = 1 (V2) y la entrenada con la
recompensa contra el precio de llegada + penalización + γ = 1 (V4).

BORRADOR elaborado por PS con apoyo de Claude Code (Sprint 6). Solo describe: no decide nada de BF ni de MR.

Busca, dentro de cada carpeta, los `d3_opcion0_s<semilla>/entrenamiento_inicial_apertura.json` y los
`control_sin_entrenar_muestreado_s<semilla>.json` (en cualquier subcarpeta, así sirve con los zip de los dos cuadernos
descomprimidos en la misma carpeta).

    python scripts/comparar_v4_vs_v2_ps.py --v2-dir data/colab_resultados/conf_pen30_g1 --v4-dir <carpeta_con_v4_A_y_B> \
        --out-md docs/v4_vs_v2_ABIDES_PS.md --out-png data/analysis/v4_vs_v2_ABIDES.png
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[1]


def _f(x: Optional[float], d: int = 2) -> str:
    return "—" if x is None or not np.isfinite(x) else f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _wilcoxon(a: Sequence[float], b: Sequence[float]) -> Optional[float]:
    pares = [(x, y) for x, y in zip(a, b) if x is not None and y is not None and np.isfinite(x) and np.isfinite(y)]
    if len(pares) < 6 or all(x == y for x, y in pares):
        return None
    return float(stats.wilcoxon([x for x, _ in pares], [y for _, y in pares]).pvalue)


def _media(xs: Sequence[float]) -> Optional[float]:
    v = [x for x in xs if x is not None and np.isfinite(x)]
    return float(np.mean(v)) if v else None


def cargar(dir_: Path) -> Dict[int, Dict]:
    """{semilla_red: {"slip": [por semilla de evaluacion], "cumpl": media, "ctrl": [por semilla] o None}}"""
    out: Dict[int, Dict] = {}
    for f in sorted(Path(dir_).rglob("entrenamiento_inicial_apertura.json")):
        m = re.search(r"d3_opcion0_s(\d+)", str(f.parent))
        if not m:
            continue
        est = json.loads(f.read_text(encoding="utf-8")).get("evaluacion_entrenada_estocastica")
        if not est:
            continue
        out[int(m.group(1))] = {"slip": est.get("slippage_por_semilla", []), "cumpl": est.get("cumplimiento_medio"), "ctrl": None}
    for f in sorted(Path(dir_).rglob("control_sin_entrenar_muestreado_s*.json")):
        s = int(re.search(r"_s(\d+)\.json$", f.name).group(1))
        if s in out:
            out[s]["ctrl"] = json.loads(f.read_text(encoding="utf-8")).get("slippage_por_semilla", [])
    return out


def _diff(a: Optional[Sequence[float]], b: Optional[Sequence[float]]):
    """(diferencia media a - b, p Wilcoxon) sobre las semillas de evaluación que tienen las dos."""
    if a is None or b is None:
        return None, None
    n = min(len(a), len(b))
    par = [(x, y) for x, y in zip(a[:n], b[:n]) if x is not None and y is not None and np.isfinite(x) and np.isfinite(y)]
    if not par:
        return None, None
    return float(np.mean([x - y for x, y in par])), _wilcoxon([x for x, _ in par], [y for _, y in par])


def comparar(v2: Dict[int, Dict], v4: Dict[int, Dict]) -> List[Dict]:
    filas = []
    for s in sorted(v4):
        ctrl = v4[s]["ctrl"] if v4[s]["ctrl"] is not None else (v2.get(s) or {}).get("ctrl")
        d_ctrl, p_ctrl = _diff(v4[s]["slip"], ctrl)
        d_v2, p_v2 = _diff(v4[s]["slip"], (v2.get(s) or {}).get("slip"))
        filas.append({"semilla": s, "cumpl_v4": v4[s]["cumpl"], "slip_v4": _media(v4[s]["slip"]),
                      "slip_v2": _media((v2.get(s) or {}).get("slip", [])), "slip_ctrl": _media(ctrl or []),
                      "dif_v4_ctrl": d_ctrl, "p_v4_ctrl": p_ctrl, "dif_v4_v2": d_v2, "p_v4_v2": p_v2})
    return filas


def informe(filas: Sequence[Dict]) -> str:
    L = ["# V4 (recompensa contra el precio de llegada) frente a V2 y al control, en ABIDES", "",
         "**Elaborado por:** PS con apoyo de Claude Code (uso autorizado por la universidad). Describe; no decide.", "",
         "Política muestreando, mismas semillas de evaluación y misma semilla de red en las tres columnas. "
         "V2 = recompensa original + penalización 30 bps + γ = 1; V4 = recompensa contra el precio de llegada + penalización 30 bps + γ = 1. "
         "Diferencias: negativas = V4 cuesta menos.", "",
         "| Semilla de red | Cumplimiento V4 | Slippage V4 (bps) | Slippage V2 (bps) | Control (bps) | V4 − control (bps) | p | V4 − V2 (bps) | p |",
         "|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in filas:
        L.append(f"| {r['semilla']} | {_f(r['cumpl_v4'], 3)} | {_f(r['slip_v4'])} | {_f(r['slip_v2'])} | {_f(r['slip_ctrl'])} | "
                 f"{_f(r['dif_v4_ctrl'])} | {_f(r['p_v4_ctrl'], 3)} | {_f(r['dif_v4_v2'])} | {_f(r['p_v4_v2'], 3)} |")
    dc = [r["dif_v4_ctrl"] for r in filas if r["dif_v4_ctrl"] is not None]
    d2 = [r["dif_v4_v2"] for r in filas if r["dif_v4_v2"] is not None]
    L.append("")
    if dc:
        mejores = sum(1 for d in dc if d < 0)
        p = float(stats.binomtest(mejores, len(dc), 0.5).pvalue)
        L.append(f"- **V4 frente al control:** {mejores} de {len(dc)} redes cuestan menos; diferencia media {_f(float(np.mean(dc)))} bps "
                 f"(prueba de signos entre redes, p = {_f(p, 3)}; es una guía, las redes comparten diseño y entorno).")
    if d2:
        mejores = sum(1 for d in d2 if d < 0)
        L.append(f"- **V4 frente a V2:** {mejores} de {len(d2)} redes cuestan menos; diferencia media {_f(float(np.mean(d2)))} bps.")
    cum = [r["cumpl_v4"] for r in filas if r["cumpl_v4"] is not None]
    if cum:
        L.append(f"- **Cumplimiento V4 (muestreando):** media {_f(float(np.mean(cum)), 3)}, mínimo {_f(float(np.min(cum)), 3)}.")
    L += ["", "🤖 Generado con [Claude Code](https://claude.com/claude-code)", ""]
    return "\n".join(L)


def figura(filas: Sequence[Dict], ruta: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    x = np.arange(len(filas))
    ancho = 0.26
    series = [("Control (sin entrenar)", "slip_ctrl", "#9a9a9a"), ("V2: recompensa original", "slip_v2", "#d95f02"),
              ("V4: contra precio de llegada", "slip_v4", "#1b9e77")]
    for i, (nom, k, col) in enumerate(series):
        vals = [r[k] if r[k] is not None else np.nan for r in filas]
        ax.bar(x + (i - 1) * ancho, vals, ancho, label=nom, color=col)
    ax.set_xticks(x)
    ax.set_xticklabels([f"red {r['semilla']}" for r in filas])
    ax.set_ylabel("Slippage medio (bps), política muestreada")
    ax.set_title("Costo por semilla de red (menos es mejor)")
    ax.legend(frameon=False, fontsize=8)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    fig.tight_layout()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta, dpi=150)
    plt.close(fig)


def main(argv: Optional[Sequence[str]] = None) -> Path:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--v2-dir", default=str(REPO_ROOT / "data/colab_resultados/conf_pen30_g1"))
    ap.add_argument("--v4-dir", required=True)
    ap.add_argument("--out-md", default=str(REPO_ROOT / "docs/v4_vs_v2_ABIDES_PS.md"))
    ap.add_argument("--out-png", default=str(REPO_ROOT / "data/analysis/v4_vs_v2_ABIDES.png"))
    args = ap.parse_args(argv)
    filas = comparar(cargar(Path(args.v2_dir)), cargar(Path(args.v4_dir)))
    if not filas:
        raise SystemExit(f"No hay corridas de V4 en {args.v4_dir}")
    out = Path(args.out_md)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(informe(filas), encoding="utf-8")
    figura(filas, Path(args.out_png))
    print(f"Informe: {out}\nFigura: {args.out_png}")
    return out


if __name__ == "__main__":
    main()
