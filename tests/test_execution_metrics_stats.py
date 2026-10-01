"""Tests de las extensiones estadisticas de execution_metrics.py (tarea
3.2.3 adelantada -- Wilcoxon pareado y Kruskal-Wallis, 1 oct 2026)."""
from __future__ import annotations

import numpy as np
import pytest

from src.analysis.execution_metrics import cohens_d_paired, compare_groups_kruskal, compare_paired


def test_compare_paired_detecta_diferencia_real():
    rng = np.random.default_rng(42)
    a = rng.normal(100, 5, 20)       # peor (IS mas alto)
    b = a - rng.normal(20, 2, 20)    # consistentemente mejor (IS mas bajo)

    result = compare_paired(a, b, name_a="A", name_b="B")

    assert result["test_used"] == "Wilcoxon signed-rank"
    assert result["significant"] is True
    assert result["n"] == 20
    assert result["reduction_pct"] < 0  # A es peor que B -> reduccion negativa


def test_compare_paired_sin_diferencia_no_es_significativo():
    rng = np.random.default_rng(1)
    a = rng.normal(100, 10, 15)
    b = a + rng.normal(0, 0.01, 15)  # practicamente identico

    result = compare_paired(a, b)
    assert result["p_value"] > 0.05
    assert result["significant"] is False


def test_compare_paired_requiere_mismo_largo():
    with pytest.raises(ValueError):
        compare_paired([1, 2, 3], [1, 2])


def test_cohens_d_paired_signo_y_magnitud():
    a = [10, 10, 10, 10]  # mejor (constante, menor)
    b = [20, 20, 20, 20]  # peor
    # diff = b - a = 10 constante -> std=0 -> por definicion devuelve 0.0 (sin variabilidad)
    assert cohens_d_paired(a, b) == 0.0

    rng = np.random.default_rng(0)
    a2 = rng.normal(10, 1, 50)
    b2 = rng.normal(20, 1, 50)
    d = cohens_d_paired(a2, b2)
    assert d > 1.0  # a2 mucho mejor (menor) que b2 -> d grande y positivo (convencion: + = a mejor)


def test_compare_groups_kruskal_detecta_grupo_distinto():
    rng = np.random.default_rng(7)
    groups = {
        "bajo": rng.normal(10, 2, 15),
        "medio": rng.normal(10, 2, 15),
        "alto": rng.normal(40, 2, 15),  # claramente distinto
    }
    result = compare_groups_kruskal(groups)

    assert result["test_used"] == "Kruskal-Wallis"
    assert result["significant"] is True
    assert result["n_groups"] == 3
    assert len(result["post_hoc"]) == 3  # 3 pares posibles entre 3 grupos
    # El par alto-vs-bajo y alto-vs-medio deberian salir significativos tras Bonferroni
    sig_pairs = [p for p in result["post_hoc"] if p["significant"]]
    assert len(sig_pairs) >= 2


def test_compare_groups_kruskal_requiere_al_menos_3_grupos():
    with pytest.raises(ValueError):
        compare_groups_kruskal({"a": [1, 2, 3], "b": [1, 2, 3]})


def test_compare_groups_kruskal_no_significativo_no_corre_post_hoc():
    rng = np.random.default_rng(3)
    groups = {
        "x": rng.normal(10, 5, 10),
        "y": rng.normal(10, 5, 10),
        "z": rng.normal(10, 5, 10),
    }
    result = compare_groups_kruskal(groups)
    if not result["significant"]:
        assert result["post_hoc"] == []
        assert result["post_hoc_method"] is None
