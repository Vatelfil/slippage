"""Pruebas del resumen de la reevaluación (datos sintéticos con la forma de los JSON del reevaluador)."""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("anal_reeval", ROOT / "scripts/analizar_reevaluacion_ps.py")
anal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(anal)


def _datos(tmp_path, rng):
    # el slippage de cada semilla de evaluación lo domina el movimiento del precio: lo comparten red y control
    deriva = rng.normal(5, 20, 60)
    (tmp_path / "control_s1000.json").write_text(json.dumps({"slippage_por_semilla": list(deriva), "slippage_bps_medio": float(deriva.mean())}))
    for etiqueta, efecto in (("conf_pen30_g1_A__d3_opcion0_s1000", -2.0), ("v4_pen30_g1_A__d3_opcion0_s1000", 0.0)):
        red = deriva + efecto + rng.normal(0, 1.0, 60)
        (tmp_path / f"red_{etiqueta}.json").write_text(json.dumps(
            {"etiqueta": etiqueta, "semilla_red": 1000, "episodios": 1000, "slippage_por_semilla": list(red),
             "slippage_bps_medio": float(red.mean()), "cumplimiento_medio": 1.0}))
    (tmp_path / "ref_twap_limit_medio.json").write_text(json.dumps({"slippage_bps_medio": 2.8, "cumplimiento_medio": 0.99}))


def test_la_diferencia_pareada_ve_el_efecto_aunque_la_deriva_sea_enorme(tmp_path):
    _datos(tmp_path, np.random.default_rng(0))
    datos = anal.cargar(tmp_path)
    por = {r["etiqueta"].split("__")[0]: r for r in datos["filas"]}
    v2, v4 = por["conf_pen30_g1_A"], por["v4_pen30_g1_A"]
    assert v2["media"] == pytest.approx(-2.0, abs=0.4) and v2["ic_sup"] < 0 and v2["p"] < 0.01
    assert abs(v4["media"]) < 0.6 and v4["ic_inf"] < 0 < v4["ic_sup"]
    assert v2["n"] == 60 and v2["mejores"] > 45


def test_grupos_informe_y_figura(tmp_path):
    _datos(tmp_path, np.random.default_rng(1))
    out = anal.main(["--dir", str(tmp_path), "--out-md", str(tmp_path / "r.md"), "--out-png", str(tmp_path / "r.png")])
    texto = Path(out).read_text(encoding="utf-8")
    assert "V2: recompensa original" in texto and "V4: recompensa contra el precio de llegada" in texto
    assert "twap_limit_medio" in texto and (tmp_path / "r.png").stat().st_size > 1000
    grupos = {g["grupo"][:2]: g for g in anal.resumen_grupos(anal.cargar(tmp_path)["filas"])}
    assert grupos["V2"]["mejores"] == 1
