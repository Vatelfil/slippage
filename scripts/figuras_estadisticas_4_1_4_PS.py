"""Figuras estadisticas de PS para el informe (tarea 4.1.4, Sprint 9): distribucion de las diferencias pareadas
de las 90 corridas con su prueba, y costo por estrategia con la prueba de varianzas pareadas.

Titulos tecnicos y valor p en cada figura (criterio de la profesora, 6 nov 2026).
Uso: python scripts/figuras_estadisticas_4_1_4_PS.py --out-dir data/analysis/figuras_4_1_4
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
ESC = ["baja", "media", "alta"]
VERDE, GRIS, OCRE = "#0B6E64", "#7A7A7A", "#B07D2B"


def pitman_morgan(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    n = len(a)
    r, _ = stats.pearsonr(a + b, a - b)
    t = r * np.sqrt((n - 2) / (1 - r ** 2))
    return float(a.std(ddof=1) / b.std(ddof=1)), float(2 * stats.t.sf(abs(t), n - 2))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="data/analysis/figuras_4_1_4")
    a = ap.parse_args(argv)
    out = Path(a.out_dir) if Path(a.out_dir).is_absolute() else ROOT / a.out_dir
    out.mkdir(parents=True, exist_ok=True)
    d = pd.concat([pd.read_csv(ROOT / f"data/colab_resultados/corridas_90/{e}/tabla/corridas.csv").assign(esc=e)
                   for e in ESC])
    p = d.pivot_table(index=["esc", "orden", "seed"], columns="estrategia", values="costo")
    res = {}

    # Figura A: histograma de las diferencias sistema - TWAP
    dif = (p["PPO_sistema"] - p["TWAP"]).to_numpy()
    w = stats.wilcoxon(dif)
    sh = stats.shapiro(dif)
    res["diferencias"] = {"n": int(len(dif)), "media": float(dif.mean()), "mediana": float(np.median(dif)),
                          "wilcoxon_p": float(w.pvalue), "shapiro_p": float(sh.pvalue)}
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.hist(dif, bins=18, color=VERDE, alpha=0.8, edgecolor="white")
    ax.axvline(0, color="#C0392B", ls="--", lw=1, label="0 = sin diferencia")
    ax.axvline(np.median(dif), color="black", lw=1.5, label=f"mediana = {np.median(dif):.1f} bps")
    ax.axvline(dif.mean(), color=OCRE, lw=1.5, label=f"media = {dif.mean():.1f} bps")
    ax.set_xlabel("costo del sistema − costo de TWAP por corrida (bps); negativo = sistema más barato")
    ax.set_ylabel("número de corridas")
    ax.set_title(f"Distribución de las diferencias pareadas sistema − TWAP (n = {len(dif)})\n"
                 f"Wilcoxon de rangos con signo p = {w.pvalue:.3f}; Shapiro-Wilk p = {sh.pvalue:.3f}", fontsize=9)
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out / "histograma_diferencias_90.png", dpi=150)
    plt.close(fig)

    # Figura B: costo por estrategia con Pitman-Morgan
    est = [("PPO_sistema", "Sistema", VERDE), ("TWAP", "TWAP", GRIS), ("VWAP", "VWAP", OCRE)]
    rt, pt = pitman_morgan(p["PPO_sistema"], p["TWAP"])
    rv, pv = pitman_morgan(p["PPO_sistema"], p["VWAP"])
    res["varianzas"] = {"desv": {k: float(p[k].std(ddof=1)) for k, _, _ in est},
                        "razon_twap": rt, "p_twap": pt, "razon_vwap": rv, "p_vwap": pv}
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    datos = [p[k].to_numpy() for k, _, _ in est]
    b = ax.boxplot(datos, widths=0.5, showfliers=False, patch_artist=True)
    for patch, (_, _, c) in zip(b["boxes"], est):
        patch.set_facecolor(c)
        patch.set_alpha(0.35)
    for k, v in enumerate(datos, start=1):
        ax.scatter(np.full(len(v), k) + np.random.default_rng(k).uniform(-0.13, 0.13, len(v)), v, s=9,
                   color=est[k - 1][2], alpha=0.7)
    ax.set_xticks([1, 2, 3])
    ax.set_xticklabels([f"{n}\n(desv. = {p[k].std(ddof=1):.1f} bps)" for k, n, _ in est], fontsize=8)
    ax.set_ylabel("costo por corrida (bps)")
    ax.set_title("Costo por corrida según estrategia, 90 corridas pareadas\n"
                 f"Pitman-Morgan (varianzas pareadas): sistema/TWAP razón {rt:.2f}, p = {pt:.1e};\n"
                 f"sistema/VWAP razón {rv:.2f}, p = {pv:.1e}", fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out / "costo_por_estrategia_varianzas.png", dpi=150)
    plt.close(fig)
    (out / "cifras_4_1_4.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
