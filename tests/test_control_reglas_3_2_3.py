"""Pruebas del análisis de control de la 3.2.3 (aporte del Maestro y de los Ejecutores)."""
import json

import numpy as np
import pytest

from scripts import control_reglas_3_2_3 as cr


def _json(ruta, estrategia, costos, cumpl=1.0):
    corr = {}
    for i, c in enumerate(costos):
        orden, seed = f"MO-{i // 3 + 1:02d}", 4 + i % 3
        corr[f"{orden}|{estrategia}|{seed}"] = {"orden": orden, "estrategia": estrategia, "seed": seed, "escenario": "media",
                                                "factor_tamano": 1.0, "slippage_bps": float(c), "execution_rate": cumpl}
    ruta.write_text(json.dumps({"firma": {}, "corridas": corr}), encoding="utf-8")


@pytest.fixture
def carpeta(tmp_path):
    rng = np.random.default_rng(0)
    twap = rng.normal(50, 60, 30)
    unif = twap - 5 + rng.normal(0, 3, 30)          # los Ejecutores ahorran ≈ 5 bps
    sis = unif + rng.normal(0, 40, 30)              # el calendario no aporta en promedio
    fija = sis.copy()
    fija[:3] += 7.0                                 # 27 de 30 idénticas al sistema
    for nombre, v in (("TWAP", twap), ("Regla_uniforme", unif), ("PPO_sistema", sis), ("Regla_fija", fija)):
        _json(tmp_path / f"{nombre}.json", nombre, v)
    return tmp_path, twap, unif, sis


def test_la_descomposicion_suma_el_total(carpeta):
    d, twap, unif, sis = carpeta
    res = cr.main(["--entradas", str(d), "--out-dir", str(d / "out"), "--sin-figuras"])
    de = res["descomposicion"]
    assert de["cuadra"] and de["n"] == 30
    assert de["sistema_menos_twap"] == pytest.approx((sis - twap).mean())
    assert de["ejecutores"] == pytest.approx((unif - twap).mean())


def test_cuenta_las_corridas_identicas_y_detecta_a_los_ejecutores(carpeta):
    d, *_ = carpeta
    res = cr.main(["--entradas", str(d), "--out-dir", str(d / "out"), "--sin-figuras"])
    assert res["igual_al_sistema"] == {"n": 30, "identicas": 27}
    eje = next(r for r in res["comparaciones"] if r["clave"] == "aporte_ejecutores")
    assert eje["dif_media"] < 0 and eje["wilcoxon_p_holm"] < 0.05
    assert all(r["wilcoxon_p_holm"] >= r["wilcoxon_p"] for r in res["comparaciones"])


def test_sin_las_reglas_no_falla(tmp_path):
    _json(tmp_path / "t.json", "TWAP", [10, 20, 30])
    _json(tmp_path / "s.json", "PPO_sistema", [5, 25, 20])
    res = cr.main(["--entradas", str(tmp_path), "--out-dir", str(tmp_path / "o"), "--sin-figuras"])
    assert res["descomposicion"] is None and res["igual_al_sistema"] is None
    assert all(r["n"] == 0 for r in res["comparaciones"])


def test_informe_y_figura(carpeta):
    d, *_ = carpeta
    md = d / "r.md"
    res = cr.main(["--entradas", str(d), "--out-dir", str(d / "out"), "--out-md", str(md)])
    texto = md.read_text(encoding="utf-8")
    assert "Descomposición" in texto and "27 de 30" in texto
    assert (d / "out" / "control_reglas.png").exists() and res["figura"]
