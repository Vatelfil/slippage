"""Resumen de la reevaluación con muchas semillas (`scripts/colab/reevaluar_ejecutores_ps.py`).

BORRADOR elaborado por PS con apoyo de Claude Code (Sprint 6). Solo describe.

Para cada red entrenada: diferencia de slippage frente a la red inicial de su semilla (control, mismas semillas de evaluación,
las dos muestreando la política), con intervalo bootstrap, Wilcoxon pareado y cuántas semillas gana. Después, un resumen por
grupo de redes (según la recompensa con que se entrenaron) y las heurísticas de referencia.

    python scripts/analizar_reevaluacion_ps.py --dir <carpeta_reeval> --out-md docs/reevaluacion_PS.md --out-png data/analysis/reevaluacion.png
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
N_BOOT = 2000


def grupo_de(etiqueta: str) -> str:
    if "v4_pen30" in etiqueta:
        return "V4: recompensa contra el precio de llegada + penalización 30 bps + γ = 1"
    if "conf_pen30" in etiqueta:
        return "V2: recompensa original + penalización 30 bps + γ = 1"
    if "opcionA" in etiqueta:
        return "Original sin arreglo, opción A (riesgo sobre lo pendiente)"
    return "Original sin arreglo (γ = 0,95), opción 0"


def _f(x: Optional[float], d: int = 2) -> str:
    return "—" if x is None or not np.isfinite(x) else f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _leer(ruta: Path) -> Dict:
    return json.loads(ruta.read_text(encoding="utf-8"))


def diferencia(red: Sequence[float], ctrl: Sequence[float], seed: int = 0) -> Dict:
    """Diferencia pareada red - control (negativa = la red cuesta menos), con IC bootstrap al 95 %."""
    n = min(len(red), len(ctrl))
    par = [(a, b) for a, b in zip(red[:n], ctrl[:n]) if a is not None and b is not None and np.isfinite(a) and np.isfinite(b)]
    d = np.array([a - b for a, b in par], float)
    if len(d) == 0:
        return {"n": 0}
    rng = np.random.default_rng(seed)
    medias = rng.choice(d, size=(N_BOOT, len(d)), replace=True).mean(axis=1)
    p = None
    if len(d) >= 6 and np.any(d != 0):
        p = float(stats.wilcoxon([a for a, _ in par], [b for _, b in par]).pvalue)
    return {"n": int(len(d)), "media": float(d.mean()), "mediana": float(np.median(d)), "ic_inf": float(np.percentile(medias, 2.5)),
            "ic_sup": float(np.percentile(medias, 97.5)), "p": p, "mejores": int((d < 0).sum())}


def cargar(dir_: Path) -> Dict:
    dir_ = Path(dir_)
    refs = {f.stem[4:]: _leer(f) for f in sorted(dir_.glob("ref_*.json"))}
    filas = []
    for f in sorted(dir_.glob("red_*.json")):
        r = _leer(f)
        c = dir_ / f"control_s{r['semilla_red']}.json"
        if not c.exists():
            continue
        ctrl = _leer(c)
        d = diferencia(r["slippage_por_semilla"], ctrl["slippage_por_semilla"])
        filas.append({"etiqueta": r["etiqueta"], "grupo": grupo_de(r["etiqueta"]), "semilla": r["semilla_red"],
                      "episodios": r.get("episodios"), "cumpl": r.get("cumplimiento_medio"), "slip": r.get("slippage_bps_medio"),
                      "slip_ctrl": ctrl.get("slippage_bps_medio"), **d})
    return {"refs": refs, "filas": filas}


def resumen_grupos(filas: Sequence[Dict]) -> List[Dict]:
    out = []
    for g in dict.fromkeys(r["grupo"] for r in filas):
        f = [r for r in filas if r["grupo"] == g and r.get("n")]
        if not f:
            continue
        mejores = sum(1 for r in f if r["media"] < 0)
        out.append({"grupo": g, "redes": len(f), "media": float(np.mean([r["media"] for r in f])), "mejores": mejores,
                    "p_signos": float(stats.binomtest(mejores, len(f), 0.5).pvalue),
                    "cumpl": float(np.mean([r["cumpl"] for r in f if r["cumpl"] is not None]))})
    return out


def informe(datos: Dict) -> str:
    filas, refs = datos["filas"], datos["refs"]
    n = filas[0]["n"] if filas else 0
    L = ["# Reevaluación de los Ejecutores con muchas semillas de evaluación", "",
         "**Elaborado por:** PS con apoyo de Claude Code (uso autorizado por la universidad). Describe; no decide.", "",
         f"Todas las redes y su control (la red inicial de la misma semilla, también muestreando la política) se evaluaron en las "
         f"mismas **{n} semillas**. Diferencia = red − control: **negativa significa que la red cuesta menos**. IC = intervalo bootstrap "
         "al 95 % de la diferencia media; p = Wilcoxon pareado por semilla de evaluación.", "",
         "| Grupo | Semilla de red | Episodios | Cumpl. | Slippage red (bps) | Control (bps) | Diferencia media (bps) | IC 95 % | Mediana | Semillas que gana | p |",
         "|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|"]
    for r in sorted(filas, key=lambda r: (r["grupo"], r["semilla"])):
        L.append(f"| {r['grupo'].split(':')[0].split(' (')[0]} | {r['semilla']} | {r.get('episodios') or '—'} | {_f(r['cumpl'], 3)} | "
                 f"{_f(r['slip'])} | {_f(r['slip_ctrl'])} | {_f(r.get('media'))} | [{_f(r.get('ic_inf'))}; {_f(r.get('ic_sup'))}] | "
                 f"{_f(r.get('mediana'))} | {r.get('mejores', '—')} de {r['n']} | {_f(r.get('p'), 3)} |")
    L += ["", "## Resumen por grupo", "", "| Grupo | Redes | Diferencia media entre redes (bps) | Redes que cuestan menos | Prueba de signos (p) | Cumplimiento medio |",
          "|---|---:|---:|---:|---:|---:|"]
    for g in resumen_grupos(filas):
        L.append(f"| {g['grupo']} | {g['redes']} | {_f(g['media'])} | {g['mejores']} de {g['redes']} | {_f(g['p_signos'], 3)} | {_f(g['cumpl'], 3)} |")
    L += ["", "La prueba de signos entre redes es solo una guía: las redes de un mismo grupo comparten recompensa y entorno.", "",
          "## Heurísticas de referencia (mismas semillas)", "", "| Heurística | Slippage (bps) | Cumplimiento |", "|---|---:|---:|"]
    for k, v in refs.items():
        L.append(f"| {k} | {_f(v.get('slippage_bps_medio'))} | {_f(v.get('cumplimiento_medio'), 3)} |")
    L += ["", "🤖 Generado con [Claude Code](https://claude.com/claude-code)", ""]
    return "\n".join(L)


def figura(filas: Sequence[Dict], ruta: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    orden = sorted([r for r in filas if r.get("n")], key=lambda r: (r["grupo"], r["semilla"]))
    grupos = list(dict.fromkeys(r["grupo"] for r in orden))
    colores = dict(zip(grupos, ["#9a9a9a", "#d95f02", "#1b9e77", "#7570b3", "#e7298a"]))
    fig, ax = plt.subplots(figsize=(8, max(3.2, 0.34 * len(orden) + 1.6)))
    for i, r in enumerate(orden):
        ax.errorbar(r["media"], i, xerr=[[r["media"] - r["ic_inf"]], [r["ic_sup"] - r["media"]]], fmt="o", color=colores[r["grupo"]],
                    capsize=3)
    ax.axvline(0, color="black", lw=0.8)
    ax.set_yticks(range(len(orden)))
    ax.set_yticklabels([f"{r['grupo'].split(':')[0].split(' (')[0]} · red {r['semilla']}" for r in orden], fontsize=7)
    ax.invert_yaxis()
    ax.set_xlabel("Red − control (bps): a la izquierda la red cuesta menos")
    ax.set_title("Diferencia de costo frente al control, con IC 95 %")
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    handles = [plt.Line2D([], [], marker="o", ls="", color=c, label=g.split(":")[0].split(" (")[0]) for g, c in colores.items()]
    ax.legend(handles=handles, frameon=False, fontsize=7, loc="lower right")
    fig.tight_layout()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta, dpi=150)
    plt.close(fig)


def main(argv: Optional[Sequence[str]] = None) -> Path:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out-md", default=str(REPO_ROOT / "docs/reevaluacion_PS.md"))
    ap.add_argument("--out-png", default=str(REPO_ROOT / "data/analysis/reevaluacion.png"))
    args = ap.parse_args(argv)
    datos = cargar(Path(args.dir))
    if not datos["filas"]:
        raise SystemExit(f"No hay redes con control en {args.dir}")
    out = Path(args.out_md)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(informe(datos), encoding="utf-8")
    figura(datos["filas"], Path(args.out_png))
    print(f"Informe: {out}\nFigura: {args.out_png}")
    return out


if __name__ == "__main__":
    main()
