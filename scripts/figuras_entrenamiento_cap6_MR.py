"""Figuras de entrenamiento y convergencia para el Capítulo 6 (MR, Sprint 8 / 4.1.4).

Genera:
  - data/analysis/cap6_MR/curvas_maestro.png: reward_mean, loss_critic, entropia y kl (2.000 episodios, sistema_final vs maestro_v2).
  - data/analysis/cap6_MR/curvas_ejecutor.png: reward_mean, loss_critic, entropia, kl y mezcla de acciones (1.000 episodios, rimit s1000).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
MAESTRO_V1_CSV = REPO_ROOT / "data/colab_resultados/sistema_final/maestro/entrenamiento_maestro.csv"
MAESTRO_V2_CSV = REPO_ROOT / "data/colab_resultados/maestro_v2/entrenamiento_maestro.csv"
EJECUTOR_CSV = REPO_ROOT / "data/colab_resultados/rimit/d3_opcion0_s1000/entrenamiento_apertura.csv"
EJECUTOR_MON_CSV = REPO_ROOT / "data/colab_resultados/rimit/d3_opcion0_s1000/monitoreo_episodios.csv"
OUT_DIR = REPO_ROOT / "data/analysis/cap6_MR"


def graficar_maestro(out_dir: Path = OUT_DIR) -> Path:
    df1 = pd.read_csv(MAESTRO_V1_CSV)
    df2 = pd.read_csv(MAESTRO_V2_CSV)

    fig, axes = plt.subplots(2, 2, figsize=(10.5, 6.8), dpi=150)
    paneles = [
        ("reward_mean", "Recompensa media R_M (bps)", "Evolución de la recompensa media"),
        ("loss_critic", "Pérdida del crítico (MSE)", "Convergencia de la pérdida del crítico"),
        ("entropia", "Entropía de la política H(π)", "Decaimiento de entropía (exploración)"),
        ("kl", "Divergencia KL aproximada", "Estabilidad de actualización (KL)"),
    ]

    for ax, (col, ylabel, sub) in zip(axes.flat, paneles):
        ax.plot(df1["episodio"], df1[col], color="#0B6E64", lw=1.8, label="Maestro oficial (Sprint 6)")
        ax.plot(df2["episodio"], df2[col], color="#B07D2B", lw=1.4, alpha=0.85, linestyle="--", label="Maestro v2 (S_M simulado)")
        ax.set_xlabel("Episodio (jornadas simuladas en Poisson)")
        ax.set_ylabel(ylabel)
        ax.set_title(sub, fontsize=10)
        ax.grid(True, linestyle="--", alpha=0.4)
        if col == "loss_critic":
            ax.set_yscale("log")

    axes[0, 0].legend(fontsize=8.5)
    fig.suptitle("Curvas de entrenamiento y convergencia del Agente Maestro (2.000 episodios en Poisson)", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    out = out_dir / "curvas_maestro.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def graficar_ejecutor(out_dir: Path = OUT_DIR) -> Path:
    df = pd.read_csv(EJECUTOR_CSV)
    mon = pd.read_csv(EJECUTOR_MON_CSV)
    mon["bloque"] = ((mon["episodio"] - 1) // 25) * 25 + 25
    mon_grp = mon.groupby("bloque")[["pct_limite_compra", "pct_mercado", "pct_espera"]].mean().reset_index()

    fig, axes = plt.subplots(2, 2, figsize=(10.5, 6.8), dpi=150)

    axes[0, 0].plot(df["episodio"], df["reward_mean"], color="#0B6E64", lw=1.6, label="Media (cada 10 ep.)")
    axes[0, 0].plot(df["episodio"], df["reward_mean"].rolling(10, min_periods=1).mean(), color="#1f77b4", lw=2.0, label="Media móvil (100 ep.)")
    axes[0, 0].set_title("Recompensa media del Ejecutor por ventana", fontsize=10)
    axes[0, 0].set_ylabel("reward_mean (CLP)")
    axes[0, 0].legend(fontsize=8.5)

    axes[0, 1].plot(df["episodio"], df["loss_critic"], color="#0B6E64", lw=1.6)
    axes[0, 1].set_title("Pérdida del crítico (MSE)", fontsize=10)
    axes[0, 1].set_ylabel("loss_critic")

    axes[1, 0].plot(df["episodio"], df["kl"], color="#7A7A7A", lw=1.5, label="KL aprox.")
    ax_twin = axes[1, 0].twinx()
    ax_twin.plot(df["episodio"], df["entropia"], color="#B07D2B", lw=1.6, linestyle="--", label="Entropía")
    axes[1, 0].set_title("Divergencia KL y entropía de política", fontsize=10)
    axes[1, 0].set_ylabel("KL", color="#7A7A7A")
    ax_twin.set_ylabel("Entropía", color="#B07D2B")

    axes[1, 1].plot(mon_grp["bloque"], mon_grp["pct_limite_compra"] * 100, color="#0B6E64", lw=1.8, label="Límite compra (%)")
    axes[1, 1].plot(mon_grp["bloque"], mon_grp["pct_mercado"] * 100, color="#B07D2B", lw=1.6, label="Mercado (%)")
    axes[1, 1].plot(mon_grp["bloque"], mon_grp["pct_espera"] * 100, color="#7A7A7A", lw=1.6, label="Espera (%)")
    axes[1, 1].set_title("Composición de acciones (promedios por 25 ep.)", fontsize=10)
    axes[1, 1].set_ylabel("Porcentaje de pasos (%)")
    axes[1, 1].legend(fontsize=8.5)

    for ax in axes.flat:
        ax.set_xlabel("Episodio (ABIDES apertura, s1000)")
        ax.grid(True, linestyle="--", alpha=0.4)

    fig.suptitle("Curvas de entrenamiento del Ejecutor elegido: Imitación twap_limit_medio + PPO (1.000 episodios)", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    out = out_dir / "curvas_ejecutor.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    p1 = graficar_maestro()
    p2 = graficar_ejecutor()
    print("Figuras generadas:", p1, p2)


if __name__ == "__main__":
    main()
