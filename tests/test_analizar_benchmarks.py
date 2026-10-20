import importlib.util
from pathlib import Path

import pytest

RUTA = Path(__file__).resolve().parents[1] / "scripts" / "analizar_benchmarks_meta_ordenes.py"
spec = importlib.util.spec_from_file_location("analisis_bench", RUTA)
an = importlib.util.module_from_spec(spec)
spec.loader.exec_module(an)


def _estado(n_ordenes=8, seeds=3, igual_ultima=True):
    corridas = {}
    for i in range(1, n_ordenes + 1):
        oid = f"MO{i:02d}"
        for s in range(1, seeds + 1):
            twap = 10.0 + i + 0.1 * s
            vwap = twap - 2.0 - 0.01 * i
            if igual_ultima and i == n_ordenes:
                vwap = twap
            for est, bps in (("TWAP", twap), ("VWAP", vwap)):
                corridas[f"{oid}|{est}|{s}"] = {"orden": oid, "estrategia": est, "seed": s, "ticker": "FALABELLA",
                                                "tramo_inicio": "apertura", "cantidad": 100000,
                                                "IS_total": bps * 1000.0, "slippage_bps": bps, "execution_rate": 1.0}
    corridas["MO01|TWAP|99"] = {"orden": "MO01", "estrategia": "TWAP", "seed": 99, "error": "boom"}   # se ignora
    return {"firma": {"entorno": "poisson"}, "corridas": corridas}


def test_tabla_y_comparacion():
    filas = an.tabla(_estado())
    assert len(filas) == 16 and all(r["n"] == 3 for r in filas)
    comp = an.comparar(filas)
    assert comp["n_ordenes"] == 8 and comp["n_ordenes_distintas"] == 7
    assert comp["por_orden"][-1]["identicas"] is True
    assert comp["diferencia_media_bps"] > 0            # VWAP mejor en este conjunto sintetico
    assert comp["wilcoxon_p"] is not None and comp["rechaza"] is True


def test_pocas_ordenes_no_hay_wilcoxon():
    comp = an.comparar(an.tabla(_estado(n_ordenes=4)))
    assert comp["wilcoxon_p"] is None and comp["rechaza"] is None


def test_informe_y_figura(tmp_path):
    estado = _estado()
    filas = an.tabla(estado)
    comp = an.comparar(filas)
    md = an.informe(estado, filas, comp, {"entorno": "poisson", "fecha": "2026-10-14"})
    assert "# Benchmarks TWAP y VWAP" in md and "MO01" in md and "idénticas" in md.lower()
    png = tmp_path / "f.png"
    an.figura(filas, png)
    assert png.exists() and png.stat().st_size > 1000


def test_ejecutabilidad_por_orden_y_umbral():
    estado = {"corridas": {
        "MO01|TWAP|1": {"orden": "MO01", "estrategia": "TWAP", "seed": 1, "ticker": "COPEC", "tramo_inicio": "apertura", "cantidad": 1000, "execution_rate": 0.99},
        "MO01|TWAP|2": {"orden": "MO01", "estrategia": "TWAP", "seed": 2, "ticker": "COPEC", "tramo_inicio": "apertura", "cantidad": 1000, "execution_rate": 0.90},
        "MO01|VWAP|1": {"orden": "MO01", "estrategia": "VWAP", "seed": 1, "execution_rate": 0.10},   # solo cuenta TWAP
        "MO02|TWAP|1": {"orden": "MO02", "estrategia": "TWAP", "seed": 1, "ticker": "ECL", "tramo_inicio": "cierre", "cantidad": 1000, "execution_rate": 0.80},
        "MO02|TWAP|2": {"orden": "MO02", "estrategia": "TWAP", "seed": 2, "error": "boom"},           # se ignora
    }}
    e = an.ejecutabilidad(estado)
    por = {r["orden"]: r for r in e["ordenes"]}
    assert por["MO01"]["corridas_ok"] == 1 and por["MO01"]["corridas"] == 2 and por["MO01"]["ejecutable"] is False  # media 0,945
    assert por["MO02"]["corridas"] == 1 and por["MO02"]["ejecutable"] is False
    assert e["ordenes_ejecutables"] == 0 and e["corridas"] == 3 and e["corridas_ok"] == 1
    md = an.informe(estado | {"firma": {"entorno": "abides"}}, [], {"n_ordenes": 0, "por_orden": [], "wilcoxon_p": None, "diferencia_media_bps": None, "n_ordenes_distintas": 0}, {"entorno": "abides", "fecha": "x"}, e, e)
    assert "Ejecutabilidad" in md and "opción B" in md

