"""
Calibracion Experimental del Hiperparametro Lambda de la Recompensa del Maestro
=============================================================================
Tarea 2.2.2 (Sprint 4) - Mauricio Reynoso (MR).

Formula de Recompensa Terminal (Perold 1988 + Penalizacion de Inventario):
    R_M = -IS_total - lambda * max(0, Q_pendiente) * P_mid_cierre

Este script corre simulaciones controladas del orquestador MaestroEjecutorEnv
probando valores de lambda en [0.01, 0.05, 0.1, 0.5, 1.0] sobre distintas
metaordenes (1.000, 5.000, 10.000, 20.000 acciones) para determinar el valor
optimo de lambda que penalice el inventario residual sin provocar explosiones
de gradiente ni opacar el objetivo principal de reduccion de slippage.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import json
import numpy as np
import pandas as pd

from src.envs.maestro_ejecutor_protocol import MaestroEjecutorEnv, maestro_policy, executor_policy
from src.envs.fallback_poisson_env import EjecutorEnvPoissonFallback


def run_lambda_experiments(
    lambdas: list[float] = [0.01, 0.05, 0.1, 0.5, 1.0],
    meta_ordenes: list[int] = [1000, 5000, 10000, 20000],
    n_runs_per_config: int = 5,
    seed: int = 42,
) -> pd.DataFrame:
    records = []
    
    # Datos sinteticos para la jornada (09:30 a 16:00)
    idx = pd.date_range("2026-09-29 09:30", "2026-09-29 16:00", freq="5min")
    rng = np.random.default_rng(seed)
    # Las politicas sin entrenar (redes inicializadas al azar) deben ser reproducibles:
    # se fija la semilla y se descartan las redes por defecto ya creadas, para que se
    # vuelvan a inicializar y a muestrear desde el mismo estado del generador.
    torch.manual_seed(seed)
    import src.envs.maestro_ejecutor_protocol as _mep
    _mep._default_master_network = None
    _mep._default_executor_network = None
    df_datos = pd.DataFrame(
        {
            "volatilidad": rng.uniform(0.001, 0.003, len(idx)),
            "vol_promedio": rng.uniform(0.1, 0.3, len(idx)),
        },
        index=idx,
    )

    for q_total in meta_ordenes:
        for lam in lambdas:
            for run_i in range(n_runs_per_config):
                n_env = [0]
                def _factory(*a, _s=seed + 1000 * len(records) + run_i, **kw):
                    n_env[0] += 1
                    return EjecutorEnvPoissonFallback(*a, seed=_s + n_env[0], **kw)

                env = MaestroEjecutorEnv(
                    meta_orden_quantity=q_total,
                    datos_historicos=df_datos,
                    executor_env_factory=_factory,
                    lambda_penalty=lam,
                )
                s_m = env.reset()
                done = False
                n_decisiones = 0
                
                while not done and n_decisiones < 15:
                    a_m = maestro_policy(s_m)
                    s_m, r_m, done, info = env.step(a_m)
                    n_decisiones += 1
                
                env.close()
                
                q_exec = env.Q_executed
                q_pend = max(0.0, q_total - q_exec)
                pct_exec = (q_exec / q_total) * 100.0
                
                # Desglose de componentes del reward terminal
                is_total = sum(r["slippage_parcial"] for r in env.executor_reports)
                p_cierre = env.executor_reports[-1]["p_promedio"] if env.executor_reports else env.P_referencia
                p_cierre = p_cierre or 5800.0
                penalizacion = lam * q_pend * p_cierre
                
                # Ratio penalizacion / (|IS| + 1e-6)
                ratio_penalizacion_is = penalizacion / (abs(is_total) + 1.0)
                
                records.append({
                    "lambda": lam,
                    "q_total": q_total,
                    "run": run_i,
                    "q_executed": q_exec,
                    "q_pendiente": q_pend,
                    "pct_executed": pct_exec,
                    "is_total_clp": is_total,
                    "p_cierre_clp": p_cierre,
                    "penalizacion_clp": penalizacion,
                    "r_m_total": r_m,
                    "ratio_pen_is": ratio_penalizacion_is,
                })
                
    df = pd.DataFrame(records)
    return df


def summarize_results(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula agregados por lambda."""
    summary = df.groupby("lambda").agg(
        q_pendiente_mean=("q_pendiente", "mean"),
        pct_executed_mean=("pct_executed", "mean"),
        is_total_mean=("is_total_clp", "mean"),
        penalizacion_mean=("penalizacion_clp", "mean"),
        r_m_mean=("r_m_total", "mean"),
        r_m_std=("r_m_total", "std"),
        ratio_pen_is_mean=("ratio_pen_is", "mean"),
    ).reset_index()
    return summary


if __name__ == "__main__":
    print("Iniciando experimentos de calibracion de lambda...")
    df_results = run_lambda_experiments()
    summary = summarize_results(df_results)
    
    print("\n--- RESUMEN POR LAMBDA ---")
    print(summary.to_string(index=False))
    
    out_dir = Path("data/calibration")
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = out_dir / "lambda_maestro_calibration_results.csv"
    summary.to_csv(summary_path, index=False)
    df_results.to_csv(out_dir / "lambda_maestro_raw_runs.csv", index=False)
    print(f"\nResultados guardados en {summary_path}")
