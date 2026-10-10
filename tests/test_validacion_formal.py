"""Pruebas de las pruebas formales de la validacion 2.2.5, con datos
sinteticos de distribucion conocida. Elaborado por PS con apoyo de Claude Code."""
from __future__ import annotations

import math

import numpy as np
import pytest

from src.analysis import validacion_formal as vf

TRAMOS = vf.TRAMOS


def _heavy(rng, n, escala):
    return (rng.standard_t(4, n) * escala).tolist()


def _real(seed=0):
    rng = np.random.default_rng(seed)
    return {"apertura": _heavy(rng, 1100, 0.0034), "media_jornada": _heavy(rng, 1600, 0.0022),
            "cierre": _heavy(rng, 1200, 0.0020)}


def _runs(escalas, n_seeds=20, seed=1, n_ret=23, spread=0.2):
    rng = np.random.default_rng(seed)
    runs = {t: {"corridas": {}} for t in TRAMOS}
    for t in TRAMOS:
        for s in range(n_seeds):
            mom = {}
            for u in TRAMOS:
                mom[u] = {"completo": True, "retornos_5min": _heavy(rng, n_ret, escalas[u]),
                          "spread_mediano_bps": spread, "volumen_mediano_vela": 10000 + 1000 * TRAMOS.index(u) + rng.normal(0, 50),
                          "participacion_volumen": 0.3 + 0.01 * TRAMOS.index(u)}
            runs[t]["corridas"][str(200 + s)] = {"momentos": mom}
    return runs


OBJ = {t: {"volatilidad_bps": v, "volumen_mediano_vela": 10000 + 1000 * i, "participacion_volumen_dia": 0.3,
           "spread_roll_bps": 30.0, "spread_hl_bps": 20.0, "spread_cs_bps": 5.0, "spread_ar_bps": 25.0}
       for i, (t, v) in enumerate(zip(TRAMOS, (34.0, 22.0, 20.0)))}


def test_ks_d_crit_valor_conocido():
    assert vf.ks_d_crit(100, 100) == pytest.approx(1.358 * math.sqrt(0.02), rel=1e-3)


def test_hedges_g_signo_y_nulo():
    rng = np.random.default_rng(0)
    a, b = rng.normal(10, 1, 200), rng.normal(10, 1, 200)
    assert abs(vf.hedges_g(a, b)) < 0.25
    assert vf.hedges_g(a + 5, b) > 3
    assert vf.hedges_g(a, a) == pytest.approx(0.0)
    assert vf.interpretar_efecto(0.1) == "trivial" and vf.interpretar_efecto(-0.9) == "grande"


def test_holm_valores_conocidos():
    aj = vf.holm({"a": 0.01, "b": 0.04, "c": 0.03, "d": None})
    assert aj["a"] == pytest.approx(0.03)
    assert aj["c"] == pytest.approx(0.06)
    assert aj["b"] == pytest.approx(0.06)
    assert aj["d"] is None


def test_ks_y_mannwhitney_mismo_vs_distinto():
    rng = np.random.default_rng(3)
    base = rng.standard_t(4, 1500) * 0.003
    igual = rng.standard_t(4, 600) * 0.003
    mas_grande = rng.standard_t(4, 600) * 0.0045
    assert vf.ks_test(igual, base)["p"] > 0.05
    assert vf.mannwhitney_abs(igual, base)["p"] > 0.05
    assert vf.ks_test(mas_grande, base)["rechaza"] is True
    mw = vf.mannwhitney_abs(mas_grande, base)
    assert mw["p"] < 0.001 and mw["g"] > 0.3
    assert vf.brown_forsythe(mas_grande, base)["p"] < 0.001


def test_contra_objetivo_y_spread():
    r = vf.contra_objetivo([34, 35, 33, 34.5, 36, 33.5, 35.2], 34.0)
    assert r["n"] == 7 and abs(r["sesgo_pct"]) < 5 and r["ic95"][0] < 34.5 < r["ic95"][1]
    assert vf.contra_objetivo([], 5)["media"] is None
    s = vf.spread_en_rango(0.2, [30, 20, 5, 25])
    assert s["dentro"] is False and s["veces_bajo_el_minimo"] == pytest.approx(25.0)
    assert vf.spread_en_rango(10, [30, 20, 5, 25])["dentro"] is True


def test_analizar_modo_simulador_bueno_y_malo():
    real = _real()
    escalas_buenas = {"apertura": 0.0034, "media_jornada": 0.0022, "cierre": 0.0020}
    buena = vf.analizar_modo(real, _runs(escalas_buenas), OBJ)
    escalas_malas = {t: v * 1.8 for t, v in escalas_buenas.items()}
    mala = vf.analizar_modo(real, _runs(escalas_malas), OBJ)

    assert buena["veredicto"]["C_efecto_pequeno"] is True
    assert mala["veredicto"]["simulador_valido"] is False
    assert mala["veredicto"]["C_efecto_pequeno"] is False
    for t in TRAMOS:
        assert mala["por_tramo"][t]["ks"]["rechaza"] is True
        assert buena["por_tramo"][t]["n_semillas"] == 20
        assert buena["por_tramo"][t]["spread"]["dentro"] is False
    # patron: volumen por vela creciente y volatilidad max en apertura en los datos de prueba
    assert buena["rankings"]["volumen_vela_creciente"] is True
    assert set(buena["p_ajustados_holm"]) == set(buena["p_crudos"])
    assert "real" in buena["patron_entre_tramos"] and "simulado" in buena["patron_entre_tramos"]
    # Holm nunca baja un p
    for k, p in buena["p_crudos"].items():
        if p is not None:
            assert buena["p_ajustados_holm"][k] >= p - 1e-12


def test_comparar_antes_despues_y_figuras(tmp_path):
    real = _real()
    despues = vf.analizar_modo(real, _runs({"apertura": 0.0034, "media_jornada": 0.0022, "cierre": 0.0020}), OBJ)
    antes = vf.analizar_modo(real, _runs({"apertura": 0.008, "media_jornada": 0.008, "cierre": 0.008}), OBJ)
    filas = vf.comparar_antes_despues(antes, despues)
    assert [f["tramo"] for f in filas] == list(TRAMOS)
    assert all(f["mejora_D"] for f in filas)
    out = vf.figuras(real, vf.retornos_simulados(_runs({t: 0.003 for t in TRAMOS})),
                     vf.retornos_simulados(_runs({t: 0.008 for t in TRAMOS})), str(tmp_path / "f.png"))
    assert (tmp_path / "f.png").exists() and out.endswith("f.png")


def test_tolera_corridas_con_error_y_tramos_incompletos():
    runs = _runs({t: 0.003 for t in TRAMOS}, n_seeds=8)
    runs["apertura"]["corridas"]["200"] = {"error": "boom"}
    runs["media_jornada"]["corridas"]["201"]["momentos"]["media_jornada"]["completo"] = False
    res = vf.analizar_modo(_real(), runs, OBJ)
    assert res["por_tramo"]["apertura"]["n_semillas"] == 7
    assert res["por_tramo"]["media_jornada"]["n_semillas"] == 7
