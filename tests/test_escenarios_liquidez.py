"""Escenarios de liquidez, C-6 y consolidador 3.2.2 (borrador de PS para BF)."""
import json

import numpy as np
import pytest

from src.envs import escenarios_liquidez as el


def test_escenarios_del_json():
    esc = el.cargar_escenarios()
    assert esc == {"baja": 0.5, "media": 1.0, "alta": 2.0}
    assert el.factor_de(None) == 1.0
    with pytest.raises(ValueError):
        el.factor_de("muy_baja")


def test_escalar_kwargs_abides_no_toca_lo_demas():
    base = {"num_noise_agents": 1000, "lambda_a": 5.7e-12, "mm_pov": 0.005, "fund_vol": 3.7e-4, "r_bar": 59698}
    k = el.escalar_kwargs_abides(base, 0.5)
    assert k["num_noise_agents"] == 500 and k["lambda_a"] == pytest.approx(2.85e-12) and k["mm_pov"] == pytest.approx(0.0025)
    assert k["fund_vol"] == base["fund_vol"] and k["r_bar"] == base["r_bar"]
    assert base["num_noise_agents"] == 1000          # no modifica el original


def test_escenario_poisson_cambia_la_profundidad_y_no_la_volatilidad():
    baja = el.fabrica_poisson(0.5)(executor_id="apertura", q_slice=1000, ventana_min=15, seed=1)
    media = el.fabrica_poisson(1.0)(executor_id="apertura", q_slice=1000, ventana_min=15, seed=1)
    assert baja._sim._avg_order_size == pytest.approx(media._sim._avg_order_size * 0.5)
    for clave in ("lambda_plus", "lambda_minus", "theta"):
        assert baja._sim.calib[clave] == media._sim.calib[clave]


def test_ajustar_ordenes_y_sufijo():
    ordenes = [{"id": "MO-01", "cantidad": 88300}, {"id": "MO-02", "cantidad": 3}]
    assert [o["cantidad"] for o in el.ajustar_ordenes(ordenes, 1.5)] == [132450, 4]
    assert ordenes[0]["cantidad"] == 88300
    assert el.sufijo_condicion(None, 1.0) == ""
    assert el.sufijo_condicion("baja", 0.5) == "_liq-baja_tam-0.5"


def test_c6_en_poisson_ordena_los_escenarios(tmp_path):
    from scripts.colab import c6_escenarios_liquidez_bf as c6
    out = c6.main(["--entorno", "poisson", "--n-semillas", "12", "--tamanos", "1000", "--out", str(tmp_path / "c6.json")])
    d = json.loads(out.read_text(encoding="utf-8"))
    fila = next(f for f in d["analisis"] if f["heuristica"] == "agresiva_market")
    assert fila["slippage_baja"] > fila["slippage_media"] >= fila["slippage_alta"]
    assert d["veredicto"].startswith("OK")


def _archivo(tmp_path, nombre, corridas):
    p = tmp_path / nombre
    p.write_text(json.dumps({"corridas": {f"{c['orden']}|{c['estrategia']}|{c['seed']}": c for c in corridas}}), encoding="utf-8")
    return p


def test_consolidador_pareado_y_ajustado(tmp_path):
    from scripts import consolidar_resultados_3_2_2 as cons
    filas_sis, filas_ref = [], []
    for s in range(1, 6):
        for est, base in (("TWAP", 10.0), ("VWAP", 12.0)):
            filas_ref.append({"orden": "MO-01", "estrategia": est, "seed": s, "escenario": "baja", "factor_tamano": 1.0,
                              "slippage_bps": base + s, "execution_rate": 1.0})
        filas_sis.append({"orden": "MO-01", "estrategia": "PPO", "seed": s, "escenario": "baja", "factor_tamano": 1.0,
                          "slippage_bps": 9.0 + s, "execution_rate": 0.5})
    _archivo(tmp_path, "bench.json", filas_ref)
    _archivo(tmp_path, "sis.json", filas_sis + [{"orden": "MO-01", "estrategia": "PPO", "seed": 9, "error": "x"}])
    out = tmp_path / "out"
    cons.main(["--entradas", str(tmp_path), "--out-dir", str(out)])
    import pandas as pd
    t = pd.read_csv(out / "tabla_maestra.csv")
    assert t.loc[0, "dif_vs_TWAP_bps"] == pytest.approx(-1.0) and t.loc[0, "dif_vs_VWAP_bps"] == pytest.approx(-3.0)
    assert t.loc[0, "ranking"] == "PPO < TWAP < VWAP"
    # con penalización por lo no ejecutado el sistema (cumplimiento 0,5) pasa a ser el más caro
    cons.main(["--entradas", str(tmp_path), "--out-dir", str(out), "--penalizacion-bps", "100"])
    t = pd.read_csv(out / "tabla_maestra.csv")
    assert t.loc[0, "ranking"].endswith("PPO")
    assert (out / "tabla_maestra.tex").read_text(encoding="utf-8").startswith("\\begin{tabular}")
