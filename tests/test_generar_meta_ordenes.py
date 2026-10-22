"""Pruebas del generador de meta-ordenes (2.3.3, borrador de PS pendiente de revision de BF)."""
import importlib.util
import json
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("gen_mo", ROOT / "scripts" / "generar_meta_ordenes.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

CAMPOS = {"id", "ticker", "fecha", "tramo_inicio", "hora_inicio", "cantidad", "p_referencia", "semilla",
          "volumen_dia_simulado", "volumen_disponible_desde_inicio", "pct_volumen_dia", "pct_volumen_disponible"}


def test_hay_diez_ordenes_con_el_esquema_del_plan():
    ordenes = gen.generar()["meta_ordenes"]
    assert len(ordenes) == 10
    for o in ordenes:
        assert set(o) == CAMPOS
        assert o["tramo_inicio"] in gen.TRAMOS and o["ticker"] in ("FALABELLA", "COPEC", "ECL")
        assert o["cantidad"] > 0 and o["p_referencia"] > 0 and o["volumen_dia_simulado"] > 0


def test_reparto_del_plan_y_sin_repetir_activo_tramo_semilla():
    ordenes = gen.generar()["meta_ordenes"]
    assert Counter(o["ticker"] for o in ordenes) == {"FALABELLA": 4, "COPEC": 3, "ECL": 3}
    assert Counter(o["tramo_inicio"] for o in ordenes) == {"apertura": 4, "media_jornada": 3, "cierre": 3}
    claves = {(o["ticker"], o["tramo_inicio"], o["semilla"]) for o in ordenes}
    assert len(claves) == 10
    assert len({o["id"] for o in ordenes}) == 10


def test_hora_de_inicio_coincide_con_el_periodo_del_runner():
    from src.analysis.benchmarks import periodo_inicio
    for o in gen.generar()["meta_ordenes"]:
        periodo = periodo_inicio(o["tramo_inicio"])
        hh, mm = divmod(9 * 60 + 30 + 30 * periodo, 60)
        assert o["hora_inicio"] == f"{hh:02d}:{mm:02d}"


def test_porcentajes_son_coherentes_con_la_cantidad():
    for o in gen.generar(cantidad=50_000)["meta_ordenes"]:
        assert o["cantidad"] == 50_000
        assert o["pct_volumen_dia"] == pytest.approx(100 * 50_000 / o["volumen_dia_simulado"], abs=0.06)
        assert o["pct_volumen_disponible"] >= o["pct_volumen_dia"]  # queda menos volumen que el del dia


def test_modo_porcentaje_del_dia_y_exclusion_mutua():
    ordenes = gen.generar(pct_dia=0.10)["meta_ordenes"]
    assert all(abs(o["pct_volumen_dia"] - 10.0) < 0.2 for o in ordenes)
    with pytest.raises(ValueError):
        gen.generar(cantidad=1000, pct_dia=0.1)


def test_el_archivo_versionado_es_el_que_genera_el_script():
    versionado = json.loads((ROOT / "data/meta_ordenes/meta_ordenes_v1.json").read_text(encoding="utf-8-sig"))
    assert versionado == gen.generar()


def test_el_runner_de_benchmarks_puede_leer_el_archivo():
    spec_r = importlib.util.spec_from_file_location("bench_runner", ROOT / "scripts/colab/benchmarks_meta_ordenes_ps.py")
    runner = importlib.util.module_from_spec(spec_r)
    spec_r.loader.exec_module(runner)
    data = json.loads((ROOT / "data/meta_ordenes/meta_ordenes_v1.json").read_text(encoding="utf-8-sig"))
    ordenes = data["meta_ordenes"]
    assert runner.pendientes({}, ordenes, [1, 2]) and len(runner.pendientes({}, ordenes, [1])) == 20


def test_fraccion_distinta_para_las_ordenes_de_cierre():
    d = gen.generar(pct_dia=0.10, pct_dia_cierre=0.05)
    por_tramo = {}
    for o in d["meta_ordenes"]:
        por_tramo.setdefault(o["tramo_inicio"], set()).add(round(o["pct_volumen_dia"]))
    assert por_tramo["apertura"] == {10} and por_tramo["media_jornada"] == {10} and por_tramo["cierre"] == {5}
    assert "cierre: 5%" in d["criterios"]["tamano"]
    with pytest.raises(ValueError):
        gen.generar(pct_dia_cierre=0.05)

