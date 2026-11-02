"""Genera las figuras del informe de Título II que se arman con cifras ya publicadas en los documentos de cada tarea.

Elaborado por PS con apoyo de Claude Code. No calcula nada nuevo: cada cifra viene de un documento del repositorio
(ver `docs/guia_graficos.md`, sección 6). Uso:

    python docs/informe_titulo2/generador/generar_figuras.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = Path(__file__).resolve().parent / "fig"
OUT.mkdir(exist_ok=True)
NAVY, C2, AMBER, LIGHT = "#1E2761", "#5A6B9C", "#E8A33D", "#9FB0DC"


def beta_fase2_apertura():
    """docs/beta_fase2_apertura_PS.md: slippage (error estándar) y cumplimiento por β."""
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
    lab = ["0×\n(control)", "0,1×β∗", "0,3×β∗", "1×β∗"]
    slip, ee, cum = [5.12, 4.71, 5.77, np.nan], [3.47, 2.79, 2.42, np.nan], [97.3, 100, 34.1, 0]
    x = np.arange(4)
    ax[0].bar(x, [0 if np.isnan(s) else s for s in slip], yerr=[0 if np.isnan(e) else e for e in ee], color=[C2, NAVY, C2, C2], capsize=3)
    ax[0].set_xticks(x)
    ax[0].set_xticklabels(lab, fontsize=8)
    ax[0].set_ylabel("Slippage medio (bps)")
    ax[0].set_title("Costo (error estándar)", fontsize=10)
    ax[0].text(3, 0.3, "sin\nejecuciones", ha="center", fontsize=8, color="gray")
    ax[0].axhline(4.06, color=AMBER, ls="--", lw=1)
    ax[0].text(3.45, 4.2, "TWAP límite\n4,06", fontsize=7, color=AMBER, ha="right")
    ax[1].bar(x, cum, color=[C2, NAVY, C2, C2])
    ax[1].axhline(95, color="gray", ls="--", lw=1)
    ax[1].set_xticks(x)
    ax[1].set_xticklabels(lab, fontsize=8)
    ax[1].set_ylabel("Orden completada (%)")
    ax[1].set_title("Cumplimiento (umbral 95 %)", fontsize=10)
    for a in ax:
        a.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(OUT / "beta_fase2_apertura.png", dpi=140)
    plt.close(fig)


def lambda_maestro():
    """docs/calibracion_recompensa_maestro_2.2.2_MR.md: razón penalización / slippage por λ."""
    fig, ax = plt.subplots(figsize=(6.2, 3.4))
    lam, ratio = ["0,01", "0,05", "0,10", "0,50", "1,00"], [0.23, 1.06, 2.34, 6.18, 20.79]
    ax.bar(lam, ratio, color=[C2, NAVY, C2, C2, C2])
    ax.set_yscale("log")
    ax.axhline(1, color="gray", ls="--", lw=1)
    ax.set_xlabel("λ")
    ax.set_ylabel("Penalización / slippage (veces, escala log)")
    ax.set_title("Calibración de λ del Maestro (100 simulaciones)", fontsize=10)
    for i, v in enumerate(ratio):
        ax.text(i, v * 1.1, f"{v:.2f}×".replace(".", ","), ha="center", fontsize=8)
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(OUT / "lambda_maestro.png", dpi=140)
    plt.close(fig)


def rmsc04_volatilidad():
    """docs/calibracion_rmsc04_2.2.4_BF.md, sección 8.3: volatilidad de 5 min simulada y real (FALABELLA)."""
    fig, ax = plt.subplots(figsize=(6.2, 3.4))
    tr, sim, real = ["Apertura", "Media jornada", "Cierre"], [34.0, 20.0, 20.5], [34.0, 22.3, 20.9]
    x = np.arange(3)
    ax.bar(x - 0.18, real, 0.36, label="Real", color=NAVY)
    ax.bar(x + 0.18, sim, 0.36, label="Simulado (rmsc04 calibrado)", color=C2)
    ax.set_xticks(x)
    ax.set_xticklabels(tr)
    ax.set_ylabel("Volatilidad de 5 min (bps)")
    ax.set_title("FALABELLA: volatilidad simulada frente a real (30 semillas)", fontsize=10)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(OUT / "rmsc04_volatilidad.png", dpi=140)
    plt.close(fig)


def horas_sprint(completadas=(104, 96, 16, 0, 0, 0, 0), fecha="22 de octubre de 2026"):
    """plan-desarrollo-titulo-2.xlsx (horas por sprint) y acta de cierre (tareas cerradas)."""
    sp, plan = ["S3", "S4", "S5", "S6", "S7", "S8", "S9"], [104, 96, 108, 72, 96, 88, 40]
    x = np.arange(7)
    fig, ax = plt.subplots(figsize=(7, 3.3))
    ax.bar(x, plan, 0.6, color=LIGHT, label="Planificadas")
    ax.bar(x, completadas, 0.6, color=NAVY, label="Completadas")
    for i, (p, h) in enumerate(zip(plan, completadas)):
        ax.text(i, p + 2, f"{p}", ha="center", fontsize=8)
        if h:
            ax.text(i, h / 2, f"{h}", ha="center", fontsize=8, color="white")
    ax.set_xticks(x)
    ax.set_xticklabels(sp)
    ax.set_ylabel("Horas")
    ax.set_title(f"Horas del plan por sprint y horas completadas al {fecha}", fontsize=10)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(OUT / "horas_sprint.png", dpi=140)
    plt.close(fig)


if __name__ == "__main__":
    beta_fase2_apertura()
    lambda_maestro()
    rmsc04_volatilidad()
    horas_sprint()
    print("figuras escritas en", OUT)
