"""Metricas de calidad de ejecucion -- Implementation Shortfall, slippage y
% de cumplimiento (Contexto_Agente_Programacion.md, seccion 13; formula base
en seccion 2; formato de episode_summary.json en
docs/arquitectura_entorno_simulacion.md, seccion 5.4).

Se escribe ANTES de tener entrenamiento real (Sprint 3.1.1 aun en borrador,
sin ABIDES) para no descubrir errores en la metrica PRINCIPAL de la tesis a
ultima hora -- las funciones aqui son las que va a consumir cada episodio de
entrenamiento/evaluacion en cuanto exista.

Formula (Perold 1988, citada en el Titulo I seccion 4.1.3):
    IS_total = (P_ejecucion_promedio - P_referencia) x Q_total

P_referencia = precio mid al momento de la decision de inversion (arrival
price), NO el precio de la primera ejecucion.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Sequence

import numpy as np
from scipy import stats


@dataclass
class EpisodeExecutionResult:
    """Resultado de un episodio (una jornada), con los campos minimos para
    calcular todas las metricas de esta seccion. Los nombres calzan con
    `episode_summary.json` (docs/arquitectura_entorno_simulacion.md, 5.4).
    """
    q_total: float           # Q_total: meta-orden completa (acciones)
    q_executed: float        # Q_executed: lo realmente ejecutado
    p_referencia: float      # arrival price (P_mid al inicio de la jornada)
    p_promedio_ejecutado: float  # precio promedio ponderado por volumen de las ejecuciones


def implementation_shortfall(result: EpisodeExecutionResult) -> float:
    """IS_total = (P_ejecucion_promedio - P_referencia) x Q_total.

    Signo: positivo = costo (se pago mas caro que la referencia, para una
    orden de COMPRA -- este proyecto solo modela compra, Contexto_Agente_
    Programacion.md nota 4). Negativo = se ejecuto mas barato que la
    referencia (favorable).
    """
    return (result.p_promedio_ejecutado - result.p_referencia) * result.q_total


def slippage_bps(result: EpisodeExecutionResult) -> float:
    """Slippage relativo en basis points (1 bps = 0.01%), la unidad estandar
    en la industria para comparar slippage entre activos de distinto precio
    (100 CLP de slippage en una accion de 5.000 CLP no es lo mismo que en
    una de 50.000 CLP)."""
    if result.p_referencia == 0:
        raise ValueError("p_referencia no puede ser 0 (division por cero).")
    return (result.p_promedio_ejecutado - result.p_referencia) / result.p_referencia * 10_000


def pct_cumplimiento(result: EpisodeExecutionResult) -> float:
    """Fraccion de la meta-orden que se logro ejecutar, en [0, 1].
    1.0 = se ejecuto el 100% de Q_total dentro de la jornada."""
    if result.q_total == 0:
        raise ValueError("q_total no puede ser 0.")
    return result.q_executed / result.q_total


def evaluate_episode(q_total: float, q_executed: float, p_referencia: float,
                      p_promedio_ejecutado: float) -> Dict[str, float]:
    """Calcula las 3 metricas de una sola vez para un episodio, en el mismo
    formato de campos que `episode_summary.json`.

    Returns:
        dict con IS_total, slippage_bps, execution_rate (= pct_cumplimiento),
        P_referencia, P_promedio_ejecutado, Q_total, Q_executed.
    """
    result = EpisodeExecutionResult(
        q_total=q_total, q_executed=q_executed,
        p_referencia=p_referencia, p_promedio_ejecutado=p_promedio_ejecutado,
    )
    return {
        "Q_total": q_total,
        "Q_executed": q_executed,
        "execution_rate": pct_cumplimiento(result),
        "P_referencia": p_referencia,
        "P_promedio_ejecutado": p_promedio_ejecutado,
        "IS_total": implementation_shortfall(result),
        "slippage_bps": slippage_bps(result),
    }


# ---------------------------------------------------------------------------
# Comparacion estadistica vs benchmarks (TWAP/VWAP) -- para la tarea 3.2.3
# ("Comparacion estadistica del sistema propuesto frente a TWAP y VWAP",
# Sprint 7). Se escribe ahora para no bloquear esa tarea despues por no tener
# la funcion de test lista; el INPUT (muestras de IS de N corridas) todavia
# no existe (requiere entrenamiento real).
# ---------------------------------------------------------------------------

def compare_strategies(is_ppo: Sequence[float], is_benchmark: Sequence[float],
                        alpha: float = 0.05, benchmark_name: str = "TWAP/VWAP") -> Dict:
    """Compara dos muestras de Implementation Shortfall (una por corrida/
    episodio) usando el test apropiado segun normalidad, siguiendo el
    Contexto_Agente_Programacion.md (seccion 13.6: "test-t o Mann-Whitney U").

    Elige automaticamente:
        - Shapiro-Wilk sobre ambas muestras para chequear normalidad.
        - Si ambas son ~normales (p > 0.05 en Shapiro): t-test de Welch
          (no asume varianzas iguales).
        - Si no: Mann-Whitney U (no parametrico).

    H0: no hay diferencia entre IS_ppo e IS_benchmark.
    Hipotesis del proyecto (Titulo I): IS_ppo < IS_benchmark en al menos 10%
    (reduccion de costo). Este test solo dice si la diferencia es
    estadisticamente significativa; la magnitud de la reduccion se reporta
    aparte (`reduction_pct`).

    Args:
        is_ppo: IS_total por episodio/corrida del sistema PPO propuesto.
        is_benchmark: IS_total por episodio/corrida de TWAP o VWAP.

    Returns:
        dict con: test_used, statistic, p_value, significant,
        mean_is_ppo, mean_is_benchmark, reduction_pct (positivo = PPO mejor).
    """
    is_ppo = np.asarray(is_ppo, dtype=float)
    is_benchmark = np.asarray(is_benchmark, dtype=float)

    if len(is_ppo) < 3 or len(is_benchmark) < 3:
        raise ValueError(
            f"Se necesitan al menos 3 muestras por grupo para un test confiable "
            f"(se recibieron {len(is_ppo)} de PPO y {len(is_benchmark)} de {benchmark_name})."
        )

    _, p_norm_ppo = stats.shapiro(is_ppo)
    _, p_norm_bench = stats.shapiro(is_benchmark)
    both_normal = (p_norm_ppo > 0.05) and (p_norm_bench > 0.05)

    if both_normal:
        statistic, p_value = stats.ttest_ind(is_ppo, is_benchmark, equal_var=False)
        test_used = "t-test (Welch)"
    else:
        statistic, p_value = stats.mannwhitneyu(is_ppo, is_benchmark, alternative="two-sided")
        test_used = "Mann-Whitney U"

    mean_ppo = float(np.mean(is_ppo))
    mean_bench = float(np.mean(is_benchmark))
    # reduction_pct > 0 significa que PPO tuvo, en promedio, MENOR costo (IS mas bajo/mas negativo)
    reduction_pct = float((mean_bench - mean_ppo) / abs(mean_bench) * 100) if mean_bench != 0 else float("nan")

    return {
        "test_used": test_used,
        "shapiro_p_ppo": float(p_norm_ppo),
        "shapiro_p_benchmark": float(p_norm_bench),
        "statistic": float(statistic),
        "p_value": float(p_value),
        "significant": bool(p_value < alpha),
        "alpha": alpha,
        "mean_is_ppo": mean_ppo,
        "mean_is_benchmark": mean_bench,
        "reduction_pct": reduction_pct,
        "meets_10pct_hypothesis": bool(reduction_pct >= 10.0 and p_value < alpha),
        "n_ppo": int(len(is_ppo)),
        "n_benchmark": int(len(is_benchmark)),
        "benchmark_name": benchmark_name,
    }
