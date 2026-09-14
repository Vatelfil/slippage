"""
Analisis de convergencia del entrenamiento PPO - Sprint 4, Tarea 3.1.5.

Lee el CSV de metricas que genera `log_metrics()` en
`notebooks/Training_PPO_Sprint4_PS.ipynb` (Seccion 8) y produce los graficos
y el test estadistico de convergencia usados en `notebooks/Analysis_Sprint4.ipynb`
y en `ANALYSIS_RESULTS.md`.

Formato de entrada esperado (logs/<run_id>/metrics.csv):
    step, maestro_return, maestro_loss_policy, maestro_loss_value,
    maestro_entropy, ejecutor0_return, ejecutor1_return, ejecutor2_return

Owner: Paolo Sepulveda (PS)
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

sns.set_theme(style="whitegrid")

REQUIRED_COLUMNS = [
    "step",
    "maestro_return",
    "maestro_loss_policy",
    "maestro_loss_value",
    "maestro_entropy",
]
EJECUTOR_RETURN_COLUMNS = ["ejecutor0_return", "ejecutor1_return", "ejecutor2_return"]


class ConvergenceAnalyzer:
    """Analiza la convergencia de un run de entrenamiento PPO a partir de su metrics.csv.

    Ejemplo de uso:
        analyzer = ConvergenceAnalyzer("logs/ppo_sprint4_20260913_090000/metrics.csv")
        fig1 = analyzer.plot_returns(window=100)
        fig2 = analyzer.plot_losses()
        result = analyzer.statistical_test()
        print(result)
    """

    def __init__(self, csv_path: str | Path):
        self.csv_path = Path(csv_path)
        if not self.csv_path.exists():
            raise FileNotFoundError(
                f"No se encontro el archivo de metricas: {self.csv_path}. "
                "Verifica que el training loop haya llamado a log_metrics() al menos una vez."
            )

        self.df = pd.read_csv(self.csv_path)
        if self.df.empty:
            raise ValueError(
                f"{self.csv_path} existe pero esta vacio (solo tiene encabezado). "
                "No hay filas para analizar todavia."
            )

        missing = [c for c in REQUIRED_COLUMNS if c not in self.df.columns]
        if missing:
            raise ValueError(
                f"Faltan columnas obligatorias en {self.csv_path}: {missing}. "
                f"Columnas disponibles: {list(self.df.columns)}"
            )

        self.step = self.df["step"].values
        self.ejecutor_cols = [c for c in EJECUTOR_RETURN_COLUMNS if c in self.df.columns]

    # ------------------------------------------------------------------
    # Graficos
    # ------------------------------------------------------------------

    def plot_returns(self, window: int = 100, save_path: str | Path | None = None):
        """Retornos del Maestro y de cada Ejecutor, suavizados con media movil.

        Args:
            window: tamano de la ventana de la media movil (en filas del CSV, no en timesteps).
            save_path: si se entrega, guarda la figura ahi (dpi=150).
        """
        fig, ax = plt.subplots(figsize=(12, 6))

        maestro_ret = self.df["maestro_return"].rolling(window, min_periods=1).mean()
        ax.plot(self.step, maestro_ret, label="Maestro", linewidth=2)

        for col in self.ejecutor_cols:
            ret = self.df[col].rolling(window, min_periods=1).mean()
            ax.plot(self.step, ret, label=col.replace("_return", "").replace("ejecutor", "Ejecutor "),
                     linewidth=1.5, alpha=0.85)

        ax.set_xlabel("Timestep")
        ax.set_ylabel(f"Return (media movil, window={window})")
        ax.set_title("Convergencia de Returns")
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches="tight")
        return fig

    def plot_losses(self, save_path: str | Path | None = None):
        """Policy loss, value loss y entropy del Maestro a lo largo del entrenamiento."""
        fig, axes = plt.subplots(1, 3, figsize=(15, 4))

        axes[0].plot(self.step, self.df["maestro_loss_policy"])
        axes[0].set_title("Policy Loss (Maestro)")
        axes[0].set_ylabel("Loss")

        axes[1].plot(self.step, self.df["maestro_loss_value"])
        axes[1].set_title("Value Loss (Maestro)")
        axes[1].set_ylabel("Loss")

        axes[2].plot(self.step, self.df["maestro_entropy"], color="purple")
        axes[2].set_title("Entropy (Maestro)")
        axes[2].set_ylabel("Entropy")

        for ax in axes:
            ax.set_xlabel("Timestep")
            ax.grid(True, alpha=0.3)

        fig.tight_layout()
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches="tight")
        return fig

    # ------------------------------------------------------------------
    # Metricas numericas
    # ------------------------------------------------------------------

    def compute_stability(self, window: int = 5000):
        """Desviacion estandar del return del Maestro en bloques consecutivos de `window` filas.

        Una politica que converge suele mostrar `std` decreciente entre bloques.

        Returns:
            (steps, stds): arrays de igual largo, un valor de std por bloque.
        """
        stds, steps = [], []
        for i in range(0, len(self.df), window):
            segment = self.df.iloc[i : i + window]["maestro_return"]
            if len(segment) > 1:
                stds.append(segment.std())
                steps.append(self.df.iloc[i]["step"])
        return np.array(steps), np.array(stds)

    def compute_improvement_factor(self, baseline_return: float = 0.0) -> float:
        """Retorno final del Maestro respecto de un baseline (ej. TWAP/VWAP o politica aleatoria)."""
        final_return = self.df["maestro_return"].iloc[-1]
        return final_return / (baseline_return + 1e-6)

    def statistical_test(self, alpha: float = 0.05) -> dict:
        """Regresion lineal simple sobre el return del Maestro vs. el indice de fila.

        No prueba causalidad ni es un test de convergencia en sentido estricto (RL no
        garantiza monotonicidad), pero es un indicador reproducible de tendencia:
        una pendiente positiva y significativa es evidencia de que la politica mejora
        en el tiempo; ausencia de significancia no implica que no haya aprendizaje
        (puede haber convergido a un plateau).

        Returns:
            dict con slope, intercept, r_squared, p_value, significant (bool, p < alpha).
        """
        x = np.arange(len(self.df))
        y = self.df["maestro_return"].values

        if len(x) < 3:
            raise ValueError(
                "Se necesitan al menos 3 puntos para un test de regresion confiable; "
                f"solo hay {len(x)} filas en {self.csv_path}."
            )

        slope, intercept, r, p, se = stats.linregress(x, y)
        return {
            "slope": slope,
            "intercept": intercept,
            "r_squared": r ** 2,
            "p_value": p,
            "std_err": se,
            "significant": p < alpha,
            "alpha": alpha,
        }


# ----------------------------------------------------------------------
# Reporte PDF (opcional) - requiere `pip install reportlab`
# ----------------------------------------------------------------------

def generate_report_pdf(analyzer: ConvergenceAnalyzer, save_path: str | Path = "report_sprint4.pdf",
                         autor: str = "Paolo Sepulveda (PS)"):
    """Genera un PDF de 3 paginas (portada+convergencia, losses, metricas) a partir de un ConvergenceAnalyzer.

    Opcional: solo se llama si el usuario quiere el entregable en PDF. Requiere `reportlab`
    (ver requirements.txt). Guarda imagenes temporales junto a `save_path` y las deja
    (no las borra) para que puedan revisarse o reutilizarse en el informe de tesis.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.platypus import (
            Image, PageBreak, Paragraph, SimpleDocTemplate, Table, TableStyle,
        )
    except ImportError as e:
        raise ImportError(
            "generate_report_pdf() requiere 'reportlab'. Instalar con: pip install reportlab"
        ) from e

    save_path = Path(save_path)
    tmp_returns = save_path.with_name(save_path.stem + "_tmp_returns.png")
    tmp_losses = save_path.with_name(save_path.stem + "_tmp_losses.png")

    fig_returns = analyzer.plot_returns(window=100, save_path=tmp_returns)
    plt.close(fig_returns)
    fig_losses = analyzer.plot_losses(save_path=tmp_losses)
    plt.close(fig_losses)

    stats_result = analyzer.statistical_test()

    doc = SimpleDocTemplate(str(save_path), pagesize=letter)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle", parent=styles["Heading1"], fontSize=22,
        textColor=colors.HexColor("#1f77b4"), spaceAfter=24,
    )

    elements = [
        Paragraph("Reporte Sprint 4 - Convergencia PPO", title_style),
        Paragraph(f"{autor} | Coordinacion de Agentes para la Mitigacion del Slippage (IPSA)", styles["Normal"]),
        PageBreak(),
        Paragraph("1. Convergencia de Retornos", styles["Heading2"]),
        Image(str(tmp_returns), width=480, height=280),
        PageBreak(),
        Paragraph("2. Perdidas del Maestro (Policy / Value / Entropy)", styles["Heading2"]),
        Image(str(tmp_losses), width=480, height=200),
        PageBreak(),
        Paragraph("3. Test Estadistico de Tendencia", styles["Heading2"]),
    ]

    table_data = [
        ["Metrica", "Valor"],
        ["Slope (tendencia)", f"{stats_result['slope']:.6f}"],
        ["R^2", f"{stats_result['r_squared']:.4f}"],
        ["P-value", f"{stats_result['p_value']:.4f}"],
        ["Significativo (alpha=0.05)", "Si" if stats_result["significant"] else "No"],
    ]
    table = Table(table_data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)

    doc.build(elements)
    print(f"Reporte guardado: {save_path}")
    return save_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analiza un metrics.csv de un run de PPO.")
    parser.add_argument("csv_path", help="Ruta a logs/<run_id>/metrics.csv")
    parser.add_argument("--pdf", action="store_true", help="Ademas, generar report_sprint4.pdf")
    args = parser.parse_args()

    analyzer = ConvergenceAnalyzer(args.csv_path)
    result = analyzer.statistical_test()
    print("Test estadistico (tendencia del return del Maestro):")
    for k, v in result.items():
        print(f"  {k}: {v}")

    if args.pdf:
        generate_report_pdf(analyzer)
