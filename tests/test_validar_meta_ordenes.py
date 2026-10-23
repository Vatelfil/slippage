"""Pruebas de la trazabilidad de la validacion de ejecutabilidad (2.3.3, BF)."""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("val_mo", ROOT / "scripts" / "validar_meta_ordenes.py")
val = importlib.util.module_from_spec(spec)
spec.loader.exec_module(val)


def _corrida(orden, seed, rate, cantidad=1000, estrategia="TWAP", ticker="FALABELLA", tramo="cierre"):
    return {"orden": orden, "estrategia": estrategia, "seed": seed, "ticker": ticker, "tramo_inicio": tramo,
            "cantidad": cantidad, "execution_rate": rate}


def _estado(*corridas):
    return {"corridas": {f"{c['orden']}|{c['estrategia']}|{c['seed']}|{i}": c for i, c in enumerate(corridas)}}


ORDEN = {"id": "MO-08", "ticker": "FALABELLA", "tramo_inicio": "cierre", "cantidad": 1000, "semilla": 9080}


def test_calza_por_id_activo_tramo_y_cantidad_y_promedia_las_semillas():
    fuentes = {"a": _estado(_corrida("MO-08", 2, 1.0), _corrida("MO-08", 1, 0.90),
                            _corrida("MO-08", 1, 0.10, estrategia="VWAP"),       # otra estrategia: no cuenta
                            _corrida("MO-08", 1, 0.10, cantidad=2000))}          # otra cantidad: no cuenta
    f = val.trazar([ORDEN], fuentes)[0]
    assert f["estado"] == "validada" and f["n_corridas"] == 2
    assert [c["seed_corrida"] for c in f["corridas"]] == [1, 2]
    assert [c["semilla_efectiva"] for c in f["corridas"]] == [9081, 9082]
    assert f["media"] == pytest.approx(0.95) and f["ejecutable"] and f["corridas_sobre_umbral"] == 1


def test_orden_sin_corrida_exacta_queda_sin_validar():
    fuentes = {"a": _estado(_corrida("MO-08", 1, 1.0, cantidad=999), _corrida("MO-08", 1, 1.0, tramo="apertura"))}
    f = val.trazar([ORDEN], fuentes)[0]
    assert f["estado"] == val.SIN_VALIDAR and f["corridas"] == [] and f["ejecutable"] is None


def test_corridas_con_error_no_cuentan():
    malo = {"orden": "MO-08", "estrategia": "TWAP", "seed": 1, "error": "RuntimeError: x"}
    f = val.trazar([ORDEN], {"a": _estado(malo)})[0]
    assert f["estado"] == val.SIN_VALIDAR


def test_resumen_por_fuente():
    est = _estado(_corrida("MO-01", 1, 1.0), _corrida("MO-01", 2, 0.96),
                  _corrida("MO-02", 1, 0.90), _corrida("MO-02", 2, 0.97))
    r = val.resumen_fuente(est)
    assert r == {"n_ordenes": 2, "ordenes_ejecutables": 1, "n_corridas": 4, "corridas_sobre_umbral": 3,
                 "no_ejecutables": ["MO-02"]}


def test_resumen_de_las_corridas_versionadas_de_la_2_3_4():
    """Las cifras que justifican D1 (docs/meta_ordenes_2.3.3.md)."""
    import json
    res = {}
    for n, r in val.FUENTES.items():
        res[n] = val.resumen_fuente(json.loads((ROOT / r).read_text(encoding="utf-8-sig")))
    assert (res["base_100000"]["ordenes_ejecutables"], res["base_100000"]["corridas_sobre_umbral"]) == (5, 11)
    assert (res["pct10"]["ordenes_ejecutables"], res["pct10"]["corridas_sobre_umbral"]) == (8, 17)
    assert (res["pct05_cierre"]["ordenes_ejecutables"], res["pct05_cierre"]["corridas_sobre_umbral"]) == (3, 5)
    assert res["pct10"]["no_ejecutables"] == ["MO-09", "MO-10"]
