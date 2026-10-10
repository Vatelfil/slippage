import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from src.analysis import benchmarks as bm

RUNNER = Path(__file__).resolve().parents[1] / "scripts" / "colab" / "benchmarks_meta_ordenes_ps.py"
spec = importlib.util.spec_from_file_location("bench_runner", RUNNER)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def test_periodo_inicio_por_tramo():
    assert bm.periodo_inicio("apertura") == 0
    assert bm.periodo_inicio("media_jornada") == 3  # el orquestador corta a las 11:00 (ver P9)
    assert bm.periodo_inicio("cierre") == 9
    with pytest.raises(ValueError):
        bm.periodo_inicio("noche")


@pytest.mark.parametrize("kind", ["TWAP", "VWAP"])
def test_schedule_desde_suma_q_y_deja_ceros_antes(kind):
    import pandas as pd
    perfil = pd.DataFrame({"volume_mean": [3.0, 1.0, 2.0]}, index=list(bm.SESSION_LABELS.values()))
    s = bm.schedule_desde(kind, 100_000.0, start_period=4, volume_profile=perfil)
    assert len(s) == bm.N_PERIODS and sum(s) == pytest.approx(100_000.0)
    assert all(x == 0.0 for x in s[:4]) and all(x > 0 for x in s[4:])


def test_runner_poisson_reanuda_y_resume(tmp_path):
    ordenes = [{"id": "MO01", "ticker": "FALABELLA", "tramo_inicio": "cierre", "cantidad": 2000}]
    estado = {}
    guardados = []
    ok = runner.correr(ordenes, [1], estado, lambda e: guardados.append(1), lambda t: None, log=lambda *_: None)
    assert ok and len(estado["corridas"]) == 2 and guardados
    n = len(guardados)
    runner.correr(ordenes, [1], estado, lambda e: guardados.append(1), lambda t: None, log=lambda *_: None)
    assert len(guardados) == n                       # nada pendiente: no recalcula
    res = runner.resumen(estado)
    assert set(res["MO01"]) == {"TWAP", "VWAP"}
    assert all("error" not in c for c in estado["corridas"].values())


def test_runner_presupuesto_corta():
    ordenes = [{"id": "MO01", "ticker": "FALABELLA", "tramo_inicio": "cierre", "cantidad": 2000}]
    assert runner.correr(ordenes, [1], {}, lambda e: None, lambda t: None, presupuesto_s=-1, log=lambda *_: None) is False

