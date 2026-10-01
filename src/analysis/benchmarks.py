"""Benchmarks TWAP y VWAP -- tarea 2.3.4 (Sprint 5), adelantada por Paolo
el 1 oct 2026 mientras se espera que Mauricio/Benjamin avancen sus tareas
del Sprint 4 (no depende de sus redes PPO ni del simulador calibrado).

Definiciones (Titulo I, seccion 4.1.4, citadas textual -- no reinterpretadas):

    TWAP (Time Weighted Average Price): "Distribuye el volumen total de la
    orden en partes iguales a lo largo del tiempo, ejecutando Q/T acciones
    en cada periodo... completamente 'ciego' a las condiciones de liquidez."

    VWAP (Volume Weighted Average Price): "Intenta replicar el perfil
    historico de volumen del mercado, enviando ordenes mayores en los
    periodos de mayor actividad historica."

Decision de diseno (por que esto NO pasa por MaestroEjecutorEnv/PPO):
`MaestroDiscreteActionSpace` (alpha_t en {0.05,...,0.50}) esta disenado para
la red PPO del Maestro -- forzar TWAP/VWAP a pasar por esas 10 fracciones
discretas introduciria un error de discretizacion ajeno a la definicion
clasica (fracciones continuas de Q/T). TWAP y VWAP corren aqui como reglas
simples e independientes, que solo reutilizan el Ejecutor
(`EjecutorEnvPoissonFallback`) y las metricas de `execution_metrics.py` --
exactamente el mismo "LOB" y la misma formula de IS que va a usar el sistema
PPO cuando exista, para que la comparacion sea de manzanas con manzanas.

Politica de ejecucion dentro de cada periodo: "ingenua" (siempre orden de
MERCADO, todo el volumen asignado de una vez) -- consistente con que, segun
el Titulo I, TWAP/VWAP son reglas fijas sin tactica de microejecucion, no
con la politica aprendida del Ejecutor (esa es tarea de Mauricio, 2.2.1/2.3.1,
no se toca aqui).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

from src.analysis.execution_metrics import EpisodeExecutionResult, evaluate_episode
from src.analysis.market_validation import load_market_data, volume_profile_by_session, SESSION_LABELS
from src.envs.fallback_poisson_env import EjecutorEnvPoissonFallback
from src.envs.maestro_ejecutor_protocol import MAX_DECISIONES_MAESTRO, VENTANA_MIN_VALUES, MaestroEjecutorEnv
from src.envs.spaces import EjecutorActionSpace

N_PERIODS = MAX_DECISIONES_MAESTRO  # 13 decisiones de 30 min (09:30-16:00), igual que el Maestro
VENTANA_MIN_BENCHMARK = VENTANA_MIN_VALUES[-1]  # 15 min: usa toda la ventana del periodo, sin apuro
DEFAULT_TICKER = "FALABELLA"  # mismo activo representativo que el resto del proyecto (Titulo I, seccion 5)

# orden_type=MARKET (indice 2, ver ORDER_TYPES en spaces.py), volume_bucket=9 (fraccion 1.0,
# ejecuta todo el q_pendiente del paso), price_level irrelevante para ordenes de mercado -> 0.
_NAIVE_ACTION_SPACE = EjecutorActionSpace()
NAIVE_ACTION_FLAT = _NAIVE_ACTION_SPACE.encode_flat(order_type=2, volume_bucket=9, price_level=0)


def _tramo_for_period(period_idx: int) -> str:
    """Tramo horario del periodo `period_idx` (0..12), usando el mismo mapeo
    reloj->tramo que `MaestroEjecutorEnv._tramo_de()` (no se reinventa el
    limite horario aqui)."""
    ts = pd.Timestamp("2026-01-01 09:30:00") + pd.Timedelta(minutes=30 * period_idx)
    return MaestroEjecutorEnv._tramo_de(ts)


def twap_schedule(q_total: float, n_periods: int = N_PERIODS) -> List[float]:
    """TWAP: Q/T acciones por periodo (Titulo I, 4.1.4) -- reparto uniforme,
    ignora por completo el perfil de liquidez."""
    return [q_total / n_periods] * n_periods


def vwap_schedule(q_total: float, volume_profile: Optional[pd.DataFrame] = None,
                   n_periods: int = N_PERIODS) -> List[float]:
    """VWAP: reparte `q_total` proporcional al volumen HISTORICO REAL del
    IPSA por tramo horario (Titulo I, 4.1.4) -- no se inventan pesos: se usa
    `volume_profile_by_session()` (market_validation.py), ya calculada sobre
    datos reales de 30 tickers IPSA.

    Cada uno de los 13 periodos de 30 min recibe el peso de SU tramo
    (apertura/media jornada/cierre); dentro del mismo tramo los periodos
    quedan con peso igual (no hay dato mas fino que el promedio por tramo
    en `volume_profile_by_session`)."""
    if volume_profile is None:
        volume_profile = volume_profile_by_session(load_market_data())

    tramo_a_label = {"apertura": SESSION_LABELS[0.0], "media_jornada": SESSION_LABELS[0.5], "cierre": SESSION_LABELS[1.0]}
    weights = np.array([
        volume_profile.loc[tramo_a_label[_tramo_for_period(i)], "volume_mean"]
        for i in range(n_periods)
    ], dtype=float)
    weights = weights / weights.sum()
    return (weights * q_total).tolist()


def run_benchmark_episode(schedule: Sequence[float], seed: int = 0,
                           ticker: str = DEFAULT_TICKER) -> EpisodeExecutionResult:
    """Corre una jornada completa (los `len(schedule)` periodos) ejecutando,
    en cada uno, el `q_slice` que diga el `schedule` (TWAP o VWAP) con la
    politica ingenua (ver docstring de modulo), contra
    `EjecutorEnvPoissonFallback` -- el mismo Ejecutor real (dinamica Poisson
    calibrada con datos del IPSA) que usa el resto del proyecto.

    Un `EjecutorEnvPoissonFallback` nuevo por periodo, igual que hace
    `MaestroEjecutorEnv._run_executor_episode()` -- mismo patron, para que
    la comparacion contra el sistema PPO (cuando exista) sea consistente.
    """
    naive_action = _NAIVE_ACTION_SPACE.decode_flat(NAIVE_ACTION_FLAT)

    q_executed_total = 0.0
    monto_acumulado = 0.0
    p_referencia: Optional[float] = None

    for i, q_slice in enumerate(schedule):
        if q_slice <= 0:
            continue
        tramo = _tramo_for_period(i)
        env = EjecutorEnvPoissonFallback(
            executor_id=tramo, q_slice=max(q_slice, 1.0), ventana_min=VENTANA_MIN_BENCHMARK,
            ticker=ticker, seed=seed * 1000 + i,
        )
        obs, info = env.reset()
        if p_referencia is None:
            p_referencia = float(info["p_referencia"])

        done = False
        while not done:
            obs, reward, done, truncated, info = env.step(naive_action)
            done = done or truncated
            q_paso = float(info.get("q_ejecutado_step", 0.0))
            p_paso = float(info.get("p_ejecutado_step", p_referencia))
            if q_paso > 0:
                q_executed_total += q_paso
                monto_acumulado += p_paso * q_paso
        env.close()

    p_promedio = monto_acumulado / q_executed_total if q_executed_total > 0 else p_referencia
    return EpisodeExecutionResult(
        q_total=float(sum(schedule)), q_executed=q_executed_total,
        p_referencia=p_referencia, p_promedio_ejecutado=p_promedio,
    )


def run_benchmark_suite(q_total: float = 5000.0, n_meta_ordenes: int = 10,
                         ticker: str = DEFAULT_TICKER) -> Dict:
    """Corre TWAP y VWAP sobre `n_meta_ordenes` meta-ordenes de prueba (misma
    `q_total`, distinta semilla aleatoria cada una -- 10 realizaciones
    distintas del mercado simulado, no 10 ordenes de tamanos distintos, para
    que el resultado sea comparable 1-a-1 entre TWAP y VWAP, tarea 3.2.3).

    Returns:
        dict con, por estrategia: lista de `EpisodeExecutionResult` y las 3
        metricas (`implementation_shortfall`, `slippage_bps`,
        `pct_cumplimiento`) de `evaluate_episode()` por corrida.
    """
    volume_profile = volume_profile_by_session(load_market_data())
    schedules = {
        "TWAP": twap_schedule(q_total),
        "VWAP": vwap_schedule(q_total, volume_profile=volume_profile),
    }

    out: Dict[str, Dict] = {}
    for name, schedule in schedules.items():
        episodios = []
        for seed in range(n_meta_ordenes):
            result = run_benchmark_episode(schedule, seed=seed, ticker=ticker)
            metrics = evaluate_episode(
                q_total=result.q_total, q_executed=result.q_executed,
                p_referencia=result.p_referencia, p_promedio_ejecutado=result.p_promedio_ejecutado,
            )
            episodios.append({"seed": seed, **metrics})
        out[name] = {
            "schedule": schedule,
            "episodios": episodios,
            "is_total_por_corrida": [e["IS_total"] for e in episodios],
        }
    out["metadata"] = {"q_total": q_total, "n_meta_ordenes": n_meta_ordenes, "ticker": ticker,
                        "n_periodos": N_PERIODS, "ventana_min_benchmark": VENTANA_MIN_BENCHMARK}
    return out


if __name__ == "__main__":
    import json

    resultado = run_benchmark_suite()
    for name in ("TWAP", "VWAP"):
        is_vals = resultado[name]["is_total_por_corrida"]
        print(f"{name}: IS medio = {np.mean(is_vals):.2f} CLP (std {np.std(is_vals):.2f}), "
              f"n={len(is_vals)}")

    out_path = "data/analysis/benchmarks_twap_vwap.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nGuardado: {out_path}")
