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
from itertools import combinations
from typing import Dict, List, Optional, Sequence

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


# ---------------------------------------------------------------------------
# Extension (1 oct 2026, PS) -- tarea 3.2.3 (Sprint 7) pide explicitamente
# Wilcoxon signed-rank, Kruskal-Wallis y effect size (Cohen's d), que
# `compare_strategies()` (arriba, Sprint 4) no cubre: esa solo compara 2
# muestras INDEPENDIENTES (t-test de Welch o Mann-Whitney U). Las funciones
# de aqui abajo cubren los 2 casos que faltan:
#   - Mismas corridas evaluadas con 2 estrategias distintas (ej. TWAP y VWAP
#     sobre las mismas 10 meta-ordenes) -> muestras PAREADAS -> Wilcoxon.
#   - Comparar 3+ estrategias a la vez (ej. PPO vs TWAP vs VWAP) -> test
#     omnibus -> Kruskal-Wallis, con post-hoc pareado si resulta
#     significativo.
# Probadas con las corridas reales de TWAP/VWAP de `src/analysis/benchmarks.py`
# (tarea 2.3.4) -- no solo con datos sinteticos.
# ---------------------------------------------------------------------------

def cohens_d_paired(sample_a: Sequence[float], sample_b: Sequence[float]) -> float:
    """Effect size de Cohen's d para muestras PAREADAS: d = media(diff) / std(diff).

    Convencion de signo: positivo si `sample_a` tuvo, en promedio, MENOR IS
    (mejor) que `sample_b` -- igual convencion que `reduction_pct` en
    `compare_strategies()`.
    """
    a = np.asarray(sample_a, dtype=float)
    b = np.asarray(sample_b, dtype=float)
    diff = b - a  # positivo si a es mejor (menor IS) que b
    std_diff = np.std(diff, ddof=1)
    if std_diff == 0:
        return 0.0
    return float(np.mean(diff) / std_diff)


def compare_paired(sample_a: Sequence[float], sample_b: Sequence[float],
                    alpha: float = 0.05, name_a: str = "A", name_b: str = "B") -> Dict:
    """Compara 2 muestras PAREADAS de IS (misma corrida/semilla evaluada con
    2 estrategias distintas, ej. TWAP vs VWAP sobre las mismas 10
    meta-ordenes) -- requiere `len(sample_a) == len(sample_b)`.

    Usa Wilcoxon signed-rank (no asume normalidad de las diferencias; test
    estandar para datos pareados no parametricos, pedido explicitamente por
    la tarea 3.2.3) y reporta Cohen's d pareado como effect size.

    Returns:
        dict con: test_used ("Wilcoxon signed-rank"), statistic, p_value,
        significant, cohens_d, mean_a, mean_b, reduction_pct (positivo =
        `sample_a` mejor), n.
    """
    a = np.asarray(sample_a, dtype=float)
    b = np.asarray(sample_b, dtype=float)
    if len(a) != len(b):
        raise ValueError(f"Las muestras pareadas deben tener el mismo largo "
                          f"(se recibieron {len(a)} de {name_a} y {len(b)} de {name_b}).")
    if len(a) < 3:
        raise ValueError(f"Se necesitan al menos 3 pares para un test confiable (se recibieron {len(a)}).")

    diff = a - b
    if np.all(diff == 0):
        statistic, p_value = 0.0, 1.0
    else:
        statistic, p_value = stats.wilcoxon(a, b, alternative="two-sided")

    mean_a, mean_b = float(np.mean(a)), float(np.mean(b))
    reduction_pct = float((mean_b - mean_a) / abs(mean_b) * 100) if mean_b != 0 else float("nan")

    return {
        "test_used": "Wilcoxon signed-rank",
        "statistic": float(statistic),
        "p_value": float(p_value),
        "significant": bool(p_value < alpha),
        "alpha": alpha,
        "cohens_d": cohens_d_paired(a, b),
        "mean_a": mean_a,
        "mean_b": mean_b,
        "reduction_pct": reduction_pct,
        "n": int(len(a)),
        "name_a": name_a,
        "name_b": name_b,
    }


def compare_groups_kruskal(samples: Dict[str, Sequence[float]], alpha: float = 0.05) -> Dict:
    """Compara 3+ grupos de IS (ej. PPO vs TWAP vs VWAP) con Kruskal-Wallis
    (test omnibus no parametrico -- no asume normalidad ni varianzas
    iguales), pedido explicitamente por la tarea 3.2.3.

    Si el resultado es significativo, corre post-hoc pareado (Mann-Whitney U
    entre cada par de grupos, con correccion de Bonferroni: alpha_corregido =
    alpha / n_comparaciones) para saber CUALES pares difieren -- Kruskal-
    Wallis por si solo solo dice que "al menos un grupo difiere", no cual.

    Args:
        samples: dict {nombre_grupo: lista_de_IS}, minimo 3 grupos.

    Returns:
        dict con: statistic (H), p_value, significant, n_groups, means (por
        grupo), post_hoc (lista de comparaciones pareadas con su p-value
        corregido y Cohen's d, solo si el omnibus fue significativo).
    """
    if len(samples) < 3:
        raise ValueError(f"Kruskal-Wallis necesita al menos 3 grupos (se recibieron {len(samples)}).")

    names = list(samples.keys())
    arrays = [np.asarray(samples[n], dtype=float) for n in names]
    for n, arr in zip(names, arrays):
        if len(arr) < 3:
            raise ValueError(f"Grupo {n!r} tiene menos de 3 muestras ({len(arr)}).")

    statistic, p_value = stats.kruskal(*arrays)
    significant = bool(p_value < alpha)

    post_hoc: List[Dict] = []
    if significant:
        pairs = list(combinations(range(len(names)), 2))
        alpha_corregido = alpha / len(pairs)
        for i, j in pairs:
            u_stat, p_pair = stats.mannwhitneyu(arrays[i], arrays[j], alternative="two-sided")
            pooled_std = np.sqrt((np.var(arrays[i], ddof=1) + np.var(arrays[j], ddof=1)) / 2)
            d = float((np.mean(arrays[j]) - np.mean(arrays[i])) / pooled_std) if pooled_std > 0 else 0.0
            post_hoc.append({
                "group_a": names[i], "group_b": names[j],
                "p_value": float(p_pair), "alpha_corregido": alpha_corregido,
                "significant": bool(p_pair < alpha_corregido),
                "cohens_d": d,
            })

    return {
        "test_used": "Kruskal-Wallis",
        "statistic": float(statistic),
        "p_value": float(p_value),
        "significant": significant,
        "alpha": alpha,
        "n_groups": len(names),
        "group_names": names,
        "means": {n: float(np.mean(arr)) for n, arr in zip(names, arrays)},
        "post_hoc_method": "Mann-Whitney U pareado, correccion de Bonferroni" if significant else None,
        "post_hoc": post_hoc,
    }
