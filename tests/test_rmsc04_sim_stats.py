"""Tests de la logica pura de src/envs/rmsc04_sim_stats.py con series L1
sinteticas de valores conocidos. No requieren ABIDES."""
from __future__ import annotations

import math

import numpy as np
import pytest

from src.envs import rmsc04_sim_stats as ss

DIA_NS = 20_688 * ss.NS_POR_DIA  # un dia cualquiera (2026-08-23) en ns desde epoch


def _ns(segundos):
    return (DIA_NS + (np.asarray(segundos, dtype=float) * ss.NS_POR_SEGUNDO).astype(np.int64)).tolist()


def _hm(h, m=0):
    return h * 3600 + m * 60


def _l1_constante(mid=60_000.0, half=30.0, cada_s=10):
    """Libro con mid y spread fijos, una cotizacion cada `cada_s` segundos."""
    t = np.arange(_hm(9, 30), _hm(16) + 1, cada_s)
    return _ns(t), [mid - half] * len(t), [mid + half] * len(t)


def test_seconds_of_day_y_tramos():
    assert ss.seconds_of_day(_ns([_hm(9, 30), _hm(15, 59) + 59.5])).tolist() == [34_200.0, 57_599.5]
    assert ss.tramo_of_seconds(_hm(9, 30)) == "apertura"
    assert ss.tramo_of_seconds(_hm(11, 30)) == "media_jornada"
    assert ss.tramo_of_seconds(_hm(14)) == "cierre"
    assert ss.tramo_of_seconds(_hm(16)) == "cierre"
    assert ss.tramo_of_seconds(_hm(9)) is None
    assert ss.TRAMO_NAMES == ("apertura", "media_jornada", "cierre")


def test_last_value_at_y_ffill():
    t = np.array([10.0, 20.0, 30.0])
    v = np.array([1.0, 2.0, 3.0])
    out = ss.last_value_at(np.array([5.0, 10.0, 25.0, 99.0]), t, v)
    assert math.isnan(out[0]) and out[1:].tolist() == [1.0, 2.0, 3.0]
    assert np.allclose(ss._ffill(np.array([np.nan, 1.0, np.nan, 3.0])), [np.nan, 1.0, 1.0, 3.0], equal_nan=True)


def test_libro_constante_spread_exacto_y_retornos_cero():
    times, bid, ask = _l1_constante(mid=60_000.0, half=30.0)
    m = ss.moments_from_l1(times, bid, ask)
    for tramo, n in (("apertura", 23), ("media_jornada", 30), ("cierre", 23)):
        r = m[tramo]
        assert r["completo"] and r["n_retornos"] == n          # mismas velas que los datos reales
        assert r["volatilidad_bps"] == 0.0
        assert r["spread_mediano_bps"] == pytest.approx(10.0)  # 60 / 60000 = 10 bps
        assert r["spread_medio_bps"] == pytest.approx(10.0)
        assert r["volumen"] == 0.0


def test_volatilidad_conocida_por_tramo():
    """mid que sube y baja alternadamente un factor fijo cada vela: los
    retornos de 5 min son +/- g y su desvio es g."""
    g = 0.002
    bordes = np.arange(_hm(9, 30), _hm(16) + 1, 300)
    mid = 60_000.0 * np.exp(g * (np.arange(len(bordes)) % 2))
    m = ss.moments_from_l1(_ns(bordes), (mid - 5).tolist(), (mid + 5).tolist())
    rets = np.array(m["media_jornada"]["retornos_5min"])
    assert np.allclose(np.abs(rets), g)
    assert m["media_jornada"]["volatilidad_bps"] == pytest.approx(g * 1e4, rel=1e-6)
    assert m["apertura"]["volatilidad_bps"] == pytest.approx(g * 1e4, rel=0.01)
    # dos valores simetricos: exceso de curtosis -2
    assert m["media_jornada"]["curtosis"] == pytest.approx(-2.0, abs=1e-6)


def test_spread_ponderado_por_tiempo_y_lado_vacio():
    """En apertura: 1 h con spread 10 bps y 1 h con 30 bps -> media 20; un
    tramo con el ask vacio no aporta muestras de spread."""
    t = [_hm(9, 30), _hm(10, 30), _hm(11, 30), _hm(14)]
    bid = [59_970.0, 59_910.0, 59_970.0, 59_970.0]
    ask = [60_030.0, 60_090.0, None, 60_030.0]
    m = ss.moments_from_l1(_ns(t), bid, ask)
    assert m["apertura"]["spread_medio_bps"] == pytest.approx(20.0, abs=0.01)
    assert m["apertura"]["spread_mediano_bps"] in (pytest.approx(10.0), pytest.approx(30.0), pytest.approx(20.0))
    assert m["media_jornada"]["n_muestras_spread"] == 0
    assert math.isnan(m["media_jornada"]["spread_mediano_bps"])
    assert m["cierre"]["spread_mediano_bps"] == pytest.approx(10.0)
    # el mid se arrastra mientras falta un lado: los retornos existen y son 0
    assert m["media_jornada"]["n_retornos"] == 30


def test_participacion_y_volumen_por_vela():
    times, bid, ask = _l1_constante()
    # 100 acciones por vela en apertura, 200 en media jornada, 300 en cierre;
    # mas 1 000 000 en la vela de subasta (15:55), que se excluye
    tt, tq = [], []
    for s in np.arange(_hm(9, 30), _hm(16), 300):
        q = 100.0 if s < _hm(11, 30) else (200.0 if s < _hm(14) else 300.0)
        tt.append(s + 1.0)
        tq.append(1_000_000.0 if s == _hm(15, 55) else q)
    m = ss.moments_from_l1(times, bid, ask, _ns(tt), tq)
    vol = {"apertura": 24 * 100.0, "media_jornada": 30 * 200.0, "cierre": 23 * 300.0}
    total = sum(vol.values())
    for tramo, v in vol.items():
        assert m[tramo]["volumen"] == v
        assert m[tramo]["participacion_volumen"] == pytest.approx(v / total)
    assert [m[t]["volumen_mediano_vela"] for t in ss.TRAMO_NAMES] == [100.0, 200.0, 300.0]
    assert m["cierre"]["n_velas"] == 23
    assert ss.ranking(m, "volumen_mediano_vela") == ["cierre", "media_jornada", "apertura"]

    con_subasta = ss.moments_from_l1(times, bid, ask, _ns(tt), tq, exclude_closing_auction=False)
    assert con_subasta["cierre"]["volumen"] == 23 * 300.0 + 1_000_000.0
    assert con_subasta["cierre"]["n_retornos"] == 24


def test_corrida_parcial_solo_reporta_tramos_completos():
    t = np.arange(_hm(9, 30), _hm(11, 30) + 1, 10)
    m = ss.moments_from_l1(_ns(t), [59_970.0] * len(t), [60_030.0] * len(t), end_s=_hm(11, 30))
    assert m["apertura"]["completo"] and m["apertura"]["n_retornos"] == 23
    assert m["apertura"]["participacion_volumen"] is None  # no hay dia completo
    assert m["media_jornada"] == {"completo": False}
    assert ss.ranking(m, "volatilidad_bps") is None


def test_pool_moments_junta_retornos_y_promedia_spread():
    rng = np.random.default_rng(0)
    runs = []
    for half in (30.0, 60.0):  # 10 bps y 20 bps
        bordes = np.arange(_hm(9, 30), _hm(16) + 1, 300)
        mid = 60_000.0 * np.exp(np.cumsum(rng.normal(0, 0.002, len(bordes))))
        runs.append(ss.moments_from_l1(_ns(bordes), (mid - half).tolist(), (mid + half).tolist(),
                                       _ns(bordes[:-1] + 1.0), [50.0] * (len(bordes) - 1)))
    pooled = ss.pool_moments(runs)
    a = pooled["apertura"]
    assert a["n_corridas"] == 2 and a["n_retornos"] == 46
    todos = np.concatenate([r["apertura"]["retornos_5min"] for r in runs])
    assert a["volatilidad_bps"] == pytest.approx(todos.std() * 1e4)
    assert a["spread_mediano_bps"] == pytest.approx(
        np.mean([r["apertura"]["spread_mediano_bps"] for r in runs]))
    assert a["participacion_volumen"] == pytest.approx(24 / 77)
    assert "retornos_5min" not in ss.strip_returns(pooled)["apertura"]
    # una corrida parcial no aporta a los tramos incompletos
    parcial = ss.moments_from_l1(_ns([_hm(9, 30)]), [1.0], [2.0], end_s=_hm(11, 30))
    assert ss.pool_moments([parcial])["cierre"] == {"n_corridas": 0}


def test_run_rmsc04_no_importa_abides_al_importar_el_modulo():
    import sys
    assert "abides_core" not in sys.modules
    with pytest.raises(ImportError):
        ss.run_rmsc04({}, seed=1)
