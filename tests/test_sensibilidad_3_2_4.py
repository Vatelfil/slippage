"""Pruebas de la sensibilidad por tamaño, tramo y liquidez (3.2.4) y del costo ajustado por lo no ejecutado."""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sens", ROOT / "scripts/analizar_sensibilidad_3_2_4.py")
sens = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sens)
cmp = sens.cmp
cmp.BOOTSTRAP = 300      # menos replicas que en uso real: las pruebas miran signos y rangos, no la precision del intervalo

TRAMOS = ["apertura", "media_jornada", "cierre"]


def _escribir(tmp_path, nombre, efecto, cumpl_sistema=1.0, ordenes=9, semillas=4, ruido=2.0, seed=0):
    """Archivos de benchmark y de sistema con el formato de `benchmarks_meta_ordenes_ps.py`. El sistema cuesta `efecto(tramo)`
    bps más (o menos) que los benchmarks en cada celda."""
    rng = np.random.default_rng(seed)
    corridas_b, corridas_s = {}, {}
    for i in range(1, ordenes + 1):
        tramo = TRAMOS[(i - 1) % 3]
        base = rng.normal(50, 10)
        for s in range(1, semillas + 1):
            ruido_s = rng.normal(0, ruido)
            for est in ("TWAP", "VWAP"):
                corridas_b[f"MO-{i:02d}|{est}|{s}"] = {"orden": f"MO-{i:02d}", "estrategia": est, "seed": s, "ticker": "FALABELLA",
                                                       "tramo_inicio": tramo, "slippage_bps": base + ruido_s, "execution_rate": 1.0}
            # El sistema tiene su propio ruido: con diferencias idénticas en todas las celdas scipy usa una prueba de permutaciones
            # muy lenta, y los datos reales nunca tienen diferencias exactamente iguales.
            corridas_s[f"MO-{i:02d}|PPO|{s}"] = {"orden": f"MO-{i:02d}", "estrategia": "PPO", "seed": s, "ticker": "FALABELLA",
                                                 "tramo_inicio": tramo, "slippage_bps": base + ruido_s + efecto(tramo) + rng.normal(0, 0.5),
                                                 "execution_rate": cumpl_sistema}
    b, s_ = tmp_path / f"b_{nombre}.json", tmp_path / f"s_{nombre}.json"
    b.write_text(json.dumps({"corridas": corridas_b}), encoding="utf-8")
    s_.write_text(json.dumps({"corridas": corridas_s}), encoding="utf-8")
    return str(b), str(s_)


def test_costo_ajustado_reparte_por_unidad_de_la_orden():
    assert cmp.costo_ajustado(10.0, 1.0, 300.0) == pytest.approx(10.0)
    assert cmp.costo_ajustado(10.0, 0.5, 100.0) == pytest.approx(55.0)
    assert cmp.costo_ajustado(10.0, 0.0, 100.0) == pytest.approx(100.0)
    assert cmp.costo_ajustado(10.0, 1.7, 100.0) == pytest.approx(10.0)       # un cumplimiento fuera de rango se recorta a [0, 1]


def test_un_sistema_que_compra_poco_parece_barato_hasta_que_se_ajusta(tmp_path):
    b, s = _escribir(tmp_path, "poco", efecto=lambda t: -10.0, cumpl_sistema=0.5)       # 10 bps más barato pero compra la mitad
    r = cmp.comparar(cmp.cargar(b), cmp.cargar(s), "PPO", penalizaciones=[0.0, 300.0])
    twap = r["benchmarks"]["TWAP"]
    assert twap["global"]["dif_media"] == pytest.approx(-10.0, abs=0.7)
    assert twap["ajustado"]["0"]["global"]["dif_media"] < 0                              # sin penalización, parece mejor
    assert twap["ajustado"]["300"]["global"]["dif_media"] > 100                          # con 300 bps por lo no comprado, es mucho peor
    assert "por_tramo" in twap["ajustado"]["300"]


def test_sin_penalizaciones_el_resultado_no_cambia(tmp_path):
    b, s = _escribir(tmp_path, "igual", efecto=lambda t: 0.0)
    r = cmp.comparar(cmp.cargar(b), cmp.cargar(s), "PPO")
    assert "ajustado" not in r["benchmarks"]["TWAP"]


def _tres_tamanos(tmp_path, efecto_por_tamano):
    esc = []
    for k, (tam, ef) in enumerate(efecto_por_tamano.items()):
        b, s = _escribir(tmp_path, tam, efecto=ef, seed=k)
        esc.append((tam, "única", b, s))
    return esc


def test_detecta_que_el_efecto_crece_con_el_tamano(tmp_path):
    esc = _tres_tamanos(tmp_path, {"pequeña": lambda t: -1.0, "mediana": lambda t: -6.0, "grande": lambda t: -12.0})
    res = sens.resumen(esc, "PPO", ["pequeña", "mediana", "grande"])
    p = res["benchmarks"]["TWAP"]["pruebas"]
    assert p["spearman_tamano"]["rho"] < -0.6 and p["spearman_tamano"]["p"] < 0.001
    assert p["kruskal_tamano"]["p"] < 0.001


def test_detecta_diferencias_entre_tramos_pero_no_entre_tamanos_iguales(tmp_path):
    efecto = lambda t: {"apertura": -8.0, "media_jornada": 0.0, "cierre": 8.0}[t]
    esc = _tres_tamanos(tmp_path, {"pequeña": efecto, "mediana": efecto, "grande": efecto})
    p = sens.resumen(esc, "PPO", ["pequeña", "mediana", "grande"])["benchmarks"]["VWAP"]["pruebas"]
    assert p["kruskal_tramo"]["p"] < 0.001 and p["kruskal_tamano"]["p"] > 0.05


def test_las_tablas_cruzan_tamano_y_tramo(tmp_path):
    esc = _tres_tamanos(tmp_path, {"pequeña": lambda t: 0.0, "grande": lambda t: 3.0})
    res = sens.resumen(esc, "PPO")
    g = res["benchmarks"]["TWAP"]["tamano_x_tramo"]
    assert set(g) == {f"{t}|{tr}" for t in ("pequeña", "grande") for tr in TRAMOS}
    assert g["grande|cierre"]["dif_media"] == pytest.approx(3.0, abs=1.0)
    assert res["orden_tamanos"] == ["pequeña", "grande"]


def test_la_liquidez_se_lee_del_escenario(tmp_path):
    b1, s1 = _escribir(tmp_path, "a", efecto=lambda t: 0.0)
    b2, s2 = _escribir(tmp_path, "b", efecto=lambda t: 5.0, seed=1)
    esc = [sens.parse_escenario(f"pequeña:baja={b1},{s1}"), sens.parse_escenario(f"pequeña:alta={b2},{s2}")]
    assert esc[0][:2] == ("pequeña", "baja")
    r = sens.resumen(esc, "PPO")["benchmarks"]["TWAP"]
    assert r["liquidez_x_tamano"]["alta|pequeña"]["dif_media"] == pytest.approx(5.0, abs=0.7)
    assert sens.parse_escenario(f"x={b1},{s1}")[1] == "única"
    with pytest.raises(Exception):
        sens.parse_escenario("sin_igual")


def test_con_penalizacion_la_sensibilidad_usa_el_costo_ajustado(tmp_path):
    b, s = _escribir(tmp_path, "adj", efecto=lambda t: -10.0, cumpl_sistema=0.5)
    sin = sens.resumen([("x", "única", b, s)], "PPO")["benchmarks"]["TWAP"]["tamano_x_tramo"]["x|apertura"]["dif_media"]
    con = sens.resumen([("x", "única", b, s)], "PPO", penalizacion_bps=300.0)["benchmarks"]["TWAP"]["tamano_x_tramo"]["x|apertura"]["dif_media"]
    assert sin == pytest.approx(-10.0, abs=1.0) and con > 100


def test_el_script_escribe_informe_figura_y_json(tmp_path):
    esc = _tres_tamanos(tmp_path, {"pequeña": lambda t: -1.0, "grande": lambda t: -9.0})
    args = []
    for tam, liq, b, s in esc:
        args += ["--escenario", f"{tam}={b},{s}"]
    md = sens.main(args + ["--nombre-sistema", "PPO", "--orden-tamanos", "pequeña", "grande", "--out-md", str(tmp_path / "r.md"),
                           "--out-png", str(tmp_path / "r.png"), "--out-json", str(tmp_path / "r.json")])
    texto = Path(md).read_text(encoding="utf-8")
    assert "Tamaño × tramo de inicio" in texto and "Spearman" in texto and (tmp_path / "r.png").stat().st_size > 1000
    assert json.loads((tmp_path / "r.json").read_text(encoding="utf-8"))["orden_tamanos"] == ["pequeña", "grande"]
