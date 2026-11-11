"""Calibración de Poisson por tercios de actividad diaria: src/envs/calibration_poisson_tercios.py."""
import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.envs import calibration_poisson_tercios as ct
from src.envs.poisson_lob_simulator import PoissonLOBSimulator, find_latest_calibration, load_calibrated_params
from src.envs.reward_utils import sigma_5min_tramo

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "data/calibration/poisson_tercios"
TRAMOS = ("apertura", "media_jornada", "cierre")


def _frame(dias, vol):
    filas = [{"ts": pd.Timestamp(f"{d} 10:00", tz="America/Santiago"), "day": date.fromisoformat(d), "volume": vol,
              "is_imputed": False} for d in dias]
    return pd.DataFrame(filas)


def test_el_simulador_sigue_usando_la_calibracion_oficial():
    """Los tercios no pueden reemplazar por nombre a poisson_params_2026-08-23.json (sistema del Sprint 6)."""
    assert find_latest_calibration().name == "poisson_params_2026-08-23.json"
    assert not list(DIR.glob("poisson_params_*.json"))


def test_un_dia_repetido_sale_de_la_descarga_mas_reciente_y_se_excluye_el_dia_de_descarga():
    frames = {"2026-08-23": _frame(["2026-08-20", "2026-08-21"], 1.0),
              "2026-09-27": _frame(["2026-08-21", "2026-09-25", "2026-09-27"], 2.0)}
    df, origen = ct.combinar_snapshots(frames)
    assert origen == {date(2026, 8, 20): "2026-08-23", date(2026, 8, 21): "2026-09-27",
                      date(2026, 9, 25): "2026-09-27"}
    assert list(df["volume"]) == [1.0, 2.0, 2.0]   # el 21 de agosto viene una sola vez, con el volumen corregido


def test_los_tercios_son_parejos_y_ordenados_por_volumen():
    vol = pd.Series({date(2026, 9, d): float(v) for d, v in zip(range(1, 8), [5, 1, 7, 3, 3, 9, 2])})
    t = ct.asignar_tercios(vol)
    assert sorted(t.values()).count("bajo") == 3 and list(t.values()).count("alto") == 2
    assert {d for d, k in t.items() if k == "bajo"} == {date(2026, 9, 2), date(2026, 9, 7), date(2026, 9, 4)}
    assert {d for d, k in t.items() if k == "alto"} == {date(2026, 9, 3), date(2026, 9, 6)}
    assert ct.asignar_tercios(vol) == t


@pytest.mark.parametrize("tercio", ct.TERCIOS)
def test_cada_archivo_de_tercio_carga_en_el_simulador(tercio):
    ruta = DIR / f"poisson_tercio_{tercio}.json"
    assert not ruta.read_bytes().startswith(b"\xef\xbb\xbf")
    for ticker in ct.TICKERS:
        for tramo in TRAMOS:
            p = load_calibrated_params(ticker, tramo, ruta)
            assert all(np.isfinite(p[k]) and p[k] > 0 for k in ("lambda_plus", "lambda_minus", "theta",
                                                                 "avg_order_size", "spread_roll_bps"))
            assert sigma_5min_tramo(ticker, tramo, ruta) > 0
    sim = PoissonLOBSimulator("FALABELLA", "apertura", calibration_path=ruta, seed=1)
    assert sim.calib["calibration_path"] == str(ruta)


def test_los_tercios_parten_los_dias_y_la_actividad_crece():
    r = json.loads((DIR / "resumen_tercios.json").read_text(encoding="utf-8"))
    assert r["metadata"]["snapshots"] == list(ct.SNAPSHOTS)
    for ticker, v in r["por_ticker"].items():
        dias = [set(v["dias"][t]) for t in ct.TERCIOS]
        assert sum(len(d) for d in dias) == len(set().union(*dias)) == v["n_dias"] == 115
        assert "2026-11-11" not in set().union(*dias)            # día de la descarga, excluido
        assert v["volumen_diario"]["bajo"]["max"] <= v["volumen_diario"]["medio"]["min"]
        assert v["volumen_diario"]["medio"]["max"] <= v["volumen_diario"]["alto"]["min"]
        for tramo in TRAMOS:
            lam = v["alto_menos_bajo"][tramo]["lambda_total"]
            assert lam["alto"] > lam["bajo"] and lam["excluye_cero"], (ticker, tramo)
