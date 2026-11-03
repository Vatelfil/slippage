"""Pruebas del generador de meta-ordenes (2.3.3). Borrador de PS; completado y aprobado por BF."""
import hashlib
import importlib.util
import json
import subprocess
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("gen_mo", ROOT / "scripts" / "generar_meta_ordenes.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

CAMPOS = {"id", "ticker", "fecha", "tramo_inicio", "hora_inicio", "cantidad", "p_referencia", "p_referencia_real",
          "semilla", "volumen_dia_simulado", "volumen_disponible_desde_inicio", "pct_volumen_dia",
          "pct_volumen_disponible", "adv_real_acciones", "pct_adv_real"}
CAMPOS_REALES = ("p_referencia_real", "adv_real_acciones", "pct_adv_real")
V1 = ROOT / "data/meta_ordenes/meta_ordenes_v1.json"
V2 = ROOT / "data/meta_ordenes/meta_ordenes_v2.json"


def _leer(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


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


def test_fraccion_distinta_para_las_ordenes_de_cierre():
    d = gen.generar(pct_dia=0.10, pct_dia_cierre=0.05)
    por_tramo = {}
    for o in d["meta_ordenes"]:
        por_tramo.setdefault(o["tramo_inicio"], set()).add(round(o["pct_volumen_dia"]))
    assert por_tramo["apertura"] == {10} and por_tramo["media_jornada"] == {10} and por_tramo["cierre"] == {5}
    assert "cierre: 5%" in d["criterios"]["tamano"]
    with pytest.raises(ValueError):
        gen.generar(pct_dia_cierre=0.05)


# --- D1 de BF y version oficial ------------------------------------------------------------------------------

def test_sin_argumentos_es_la_version_oficial_d1():
    d = gen.generar()
    assert d["version"] == "v2" and "aprobado por BF" in d["estado"]
    assert d == gen.generar(pct_dia=gen.PCT_DIA_OFICIAL, pct_dia_cierre=gen.PCT_DIA_CIERRE_OFICIAL)
    assert d["generacion"]["comando"] == "python scripts/generar_meta_ordenes.py"
    cant = {o["id"]: o["cantidad"] for o in d["meta_ordenes"]}
    # Las cantidades de las corridas de validacion en ABIDES (pct10 y pct05_cierre de la 2.3.4).
    assert cant == {"MO-01": 88_300, "MO-02": 29_100, "MO-03": 29_100, "MO-04": 32_100, "MO-05": 29_100,
                    "MO-06": 32_100, "MO-07": 32_100, "MO-08": 44_100, "MO-09": 44_100, "MO-10": 44_100}


def test_variantes_no_son_oficiales_y_anotan_su_comando():
    d = gen.generar(cantidad=100_000)
    assert d["version"] == "no_oficial"
    assert d["generacion"]["comando"] == "python scripts/generar_meta_ordenes.py --cantidad 100000"
    d = gen.generar(pct_dia=0.10)
    assert d["version"] == "no_oficial" and d["generacion"]["comando"].endswith("--pct-dia 0.1")


def test_campos_reales_con_y_sin_snapshot():
    sin = gen.generar()
    assert all(o[k] is None for o in sin["meta_ordenes"] for k in CAMPOS_REALES)
    assert sin["generacion"]["adv_real"]["activos_con_dato"] == []
    reales = {"FALABELLA": {"adv_acciones": 1_000_000.0, "n_dias": 60, "precio_referencia_real": 6000.0}}
    con = gen.generar(reales=reales)
    for o in con["meta_ordenes"]:
        if o["ticker"] == "FALABELLA":
            assert o["adv_real_acciones"] == 1_000_000 and o["p_referencia_real"] == 6000.0
            assert o["pct_adv_real"] == pytest.approx(100 * o["cantidad"] / 1_000_000, abs=0.006)
        else:
            assert all(o[k] is None for k in CAMPOS_REALES)
    assert con["generacion"]["adv_real"]["activos_con_dato"] == ["FALABELLA"]


def test_datos_reales_avisa_el_parquet_que_falta(tmp_path):
    datos, faltan = gen.datos_reales(["FALABELLA"], tmp_path)
    assert datos == {} and faltan == [str(tmp_path / "clean_5m_2026-08-23" / "FALABELLA.parquet")]


@pytest.mark.skipif(not (ROOT / "data/processed/clean_5m_2026-08-23/FALABELLA.parquet").exists(),
                    reason="snapshot parquet no disponible (no se versiona)")
def test_datos_reales_usa_las_definiciones_de_meta_orders():
    from src.experiments.meta_orders import load_daily_volume, meta_orders_for_ticker
    datos, faltan = gen.datos_reales(["FALABELLA"])
    ref = meta_orders_for_ticker(load_daily_volume("FALABELLA", "2026-08-23"), [])
    assert faltan == []
    assert datos["FALABELLA"]["adv_acciones"] == ref["adv_acciones"]["sin_subasta"]
    assert datos["FALABELLA"]["precio_referencia_real"] == round(ref["precio_referencia_clp"], 2)


# --- Evidencia del congelamiento -----------------------------------------------------------------------------

def test_sha256_coincide_con_los_archivos_de_calibracion():
    cal = gen.generar()["generacion"]["calibracion"]
    assert set(cal) == {"FALABELLA", "COPEC", "ECL"}
    for t, h in cal.items():
        assert h["archivo"] == f"data/calibration/rmsc04_ipsa_{t}_2026-08-23.json"
        contenido = (ROOT / h["archivo"]).read_bytes().replace(b"\r\n", b"\n")
        assert h["sha256_lf"] == hashlib.sha256(contenido).hexdigest()


def test_blob_coincide_con_el_de_git():
    cal = gen.generar()["generacion"]["calibracion"]
    for h in cal.values():
        r = subprocess.run(["git", "rev-parse", f"HEAD:{h['archivo']}"], cwd=ROOT, capture_output=True, text=True)
        if r.returncode != 0:
            pytest.skip("sin git o archivo fuera de HEAD")
        assert h["git_blob"] == r.stdout.strip()


def test_huella_no_depende_del_fin_de_linea(tmp_path):
    lf, crlf = tmp_path / "lf.json", tmp_path / "crlf.json"
    lf.write_bytes(b'{\n "a": 1\n}\n')
    crlf.write_bytes(b'{\r\n "a": 1\r\n}\r\n')
    assert gen.huella_archivo(lf) == gen.huella_archivo(crlf)


# --- CLI -----------------------------------------------------------------------------------------------------

def test_cli_variante_sin_salida_no_sobrescribe_la_oficial(tmp_path):
    with pytest.raises(SystemExit):
        gen.main(["--pct-dia", "0.10", "--data-dir", str(tmp_path)])


def test_cli_escribe_utf8_sin_bom(tmp_path):
    out = tmp_path / "mo.json"
    gen.main(["--pct-dia", "0.10", "--pct-dia-cierre", "0.05", "--salida", str(out), "--data-dir", str(tmp_path)])
    crudo = out.read_bytes()
    assert not crudo.startswith(b"\xef\xbb\xbf")
    d = json.loads(crudo.decode("utf-8"))
    assert d["version"] == "v2" and len(d["meta_ordenes"]) == 10


# --- v1 (historica, la de la corrida base de T4) -------------------------------------------------------------

def test_v1_historica_es_la_misma_lista_con_100000_acciones():
    v1 = _leer(V1)["meta_ordenes"]
    actual = gen.generar(cantidad=gen.CANTIDAD_V1)["meta_ordenes"]
    assert all(o["cantidad"] == 100_000 for o in v1)
    comunes = set(v1[0]) & set(actual[0])
    assert [{k: o[k] for k in comunes} for o in v1] == [{k: o[k] for k in comunes} for o in actual]


@pytest.mark.parametrize("archivo", [V1, V2])
def test_el_runner_de_benchmarks_puede_leer_el_archivo(archivo):
    spec_r = importlib.util.spec_from_file_location("bench_runner", ROOT / "scripts/colab/benchmarks_meta_ordenes_ps.py")
    runner = importlib.util.module_from_spec(spec_r)
    spec_r.loader.exec_module(runner)
    ordenes = _leer(archivo)["meta_ordenes"]
    assert runner.pendientes({}, ordenes, [1, 2]) and len(runner.pendientes({}, ordenes, [1])) == 20


# --- v2 (oficial) --------------------------------------------------------------------------------------------

def test_el_archivo_oficial_es_el_que_genera_el_script():
    versionado = _leer(V2)
    reales, faltan = gen.datos_reales(["COPEC", "ECL", "FALABELLA"])
    generado = gen.generar(reales=reales)
    assert versionado["generacion"].pop("commit") and generado["generacion"].pop("commit") is None
    if faltan:  # sin el parquet (no se versiona) se comparan todos los campos salvo los reales
        for d in (versionado, generado):
            d["generacion"]["adv_real"]["activos_con_dato"] = []
            for o in d["meta_ordenes"]:
                o.update({k: None for k in CAMPOS_REALES})
    assert versionado == generado


def test_oficial_reparto_esquema_del_runner_y_campos_nuevos():
    d = _leer(V2)
    ordenes = d["meta_ordenes"]
    assert d["version"] == "v2"
    assert Counter(o["ticker"] for o in ordenes) == {"FALABELLA": 4, "COPEC": 3, "ECL": 3}
    assert Counter(o["tramo_inicio"] for o in ordenes) == {"apertura": 4, "media_jornada": 3, "cierre": 3}
    for o in ordenes:  # lo que lee scripts/colab/benchmarks_meta_ordenes_ps.py
        assert isinstance(o["id"], str) and o["ticker"] in ("FALABELLA", "COPEC", "ECL")
        assert o["tramo_inicio"] in gen.TRAMOS and isinstance(o["cantidad"], int) and isinstance(o["semilla"], int)
        assert set(o) == CAMPOS and all(o[k] is not None for k in CAMPOS_REALES)
    g = d["generacion"]
    assert g["comando"] and not g["commit"].endswith("-modificado")
    assert set(g["calibracion"]) == {"FALABELLA", "COPEC", "ECL"}


def test_v1_y_v2_comparten_ids_tramos_y_semillas():
    """Las corridas de la 2.3.4 no guardan la semilla de la orden: se deduce del id (ver validar_meta_ordenes.py)."""
    clave = lambda o: (o["id"], o["ticker"], o["tramo_inicio"], o["semilla"])
    assert [clave(o) for o in _leer(V1)["meta_ordenes"]] == [clave(o) for o in _leer(V2)["meta_ordenes"]]


def test_las_diez_ordenes_oficiales_estan_validadas_en_abides():
    spec_v = importlib.util.spec_from_file_location("val_mo", ROOT / "scripts/validar_meta_ordenes.py")
    val = importlib.util.module_from_spec(spec_v)
    spec_v.loader.exec_module(val)
    fuentes = {n: _leer(ROOT / r) for n, r in val.FUENTES.items()}
    filas = val.trazar(_leer(V2)["meta_ordenes"], fuentes)
    assert [f["estado"] for f in filas] == ["validada"] * 10
    assert all(f["n_corridas"] == 2 and f["ejecutable"] for f in filas)
    assert _leer(ROOT / "data/analysis/validacion_meta_ordenes_2.3.3.json")["ordenes"] == filas
