"""Tests de los benchmarks TWAP/VWAP (tarea 2.3.4, Sprint 5)."""
from __future__ import annotations

import numpy as np

from src.analysis.benchmarks import (
    N_PERIODS, run_benchmark_episode, run_benchmark_suite, twap_schedule, vwap_schedule,
)


def test_twap_schedule_reparte_en_partes_iguales():
    schedule = twap_schedule(13000.0, n_periods=13)
    assert len(schedule) == 13
    assert all(abs(q - 1000.0) < 1e-9 for q in schedule)
    assert abs(sum(schedule) - 13000.0) < 1e-6


def test_vwap_schedule_suma_q_total_y_varia_por_tramo():
    import pandas as pd
    volume_profile = pd.DataFrame(
        {"volume_mean": [100.0, 200.0, 400.0]},
        index=["Apertura (09:30-11:00)", "Media jornada (11:00-14:00)", "Cierre (14:00-16:00)"],
    )
    schedule = vwap_schedule(10000.0, volume_profile=volume_profile, n_periods=N_PERIODS)
    assert len(schedule) == N_PERIODS
    assert abs(sum(schedule) - 10000.0) < 1e-6
    # El periodo de cierre (mayor volumen) debe recibir un slice mayor que el de apertura.
    assert schedule[-1] > schedule[0]


def test_run_benchmark_episode_ejecuta_y_devuelve_metricas_coherentes():
    schedule = twap_schedule(2000.0, n_periods=4)
    result = run_benchmark_episode(schedule, seed=0)

    assert result.q_total == 2000.0
    assert 0.0 <= result.q_executed <= result.q_total * 1.0001
    assert result.p_referencia > 0
    assert result.p_promedio_ejecutado > 0


def test_run_benchmark_suite_twap_y_vwap_dan_n_corridas():
    resultado = run_benchmark_suite(q_total=1000.0, n_meta_ordenes=3)
    assert set(resultado.keys()) >= {"TWAP", "VWAP", "metadata"}
    for name in ("TWAP", "VWAP"):
        assert len(resultado[name]["is_total_por_corrida"]) == 3
        assert all(np.isfinite(v) for v in resultado[name]["is_total_por_corrida"])
