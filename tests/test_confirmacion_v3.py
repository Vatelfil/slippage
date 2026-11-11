"""Criterio C-6c de la v3 (desviación 10): src/experiments/confirmacion_v3.py y scripts/confirmar_v3_c6c.py."""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from src.experiments import confirmacion_v3 as cv3

ROOT = Path(__file__).resolve().parents[1]
C6B = ROOT / "data/colab_resultados/c6b_liquidez/c6b_liquidez.json"


def _datos(baja, media, alta, seed_base=8100, n=60, tamanos=(5000,)):
    firma = {"tarea": "3.1.3-C6", "entorno": "abides", "ticker": "FALABELLA", "tramo": "apertura",
             "tamanos": list(tamanos), "ventana_min": 15, "n_semillas": n, "seed_base": seed_base,
             "escenarios": {"baja": 4.0, "media": 1.0, "alta": 0.25}, "claves_abides": ["mm_pov"]}
    res = {}
    for nombre, factor, por in (("baja", 4.0, baja), ("media", 1.0, media), ("alta", 0.25, alta)):
        vals = [v for v in por if v is not None]
        res[f"{nombre}|agresiva_market|5000"] = {
            "escenario": nombre, "factor": factor, "heuristica": "agresiva_market", "q_slice": 5000,
            "slippage_bps_medio": float(np.mean(vals)), "cumplimiento_medio": 1.0, "slippage_por_semilla": list(por)}
    return {"firma": firma, "resultados": res}


def _base(n=60, seed=1):
    rng = np.random.default_rng(seed)
    return rng.normal(15.0, 8.0, n)  # mismo "día" en los tres escenarios: el ruido común se cancela al parear


def test_las_semillas_son_8101_a_8160_y_no_cruzan_las_del_c6b():
    s = cv3.semillas()
    assert s[0] == 8101 and s[-1] == 8160 and len(s) == 60
    c6b = cv3.semillas(dict(cv3.CRITERIO, seed_base=8000))
    assert c6b[0] == 8001 and c6b[-1] == 8060 and not set(s) & set(c6b)
    # tampoco con entrenamiento (1001-5000 para redes de semilla 1000 a 4000) ni con la evaluacion de 300 semillas (5001-5300)
    assert not set(s) & set(range(1001, 5301))


def test_confirmada_cuando_las_dos_diferencias_son_positivas():
    m = _base()
    rng = np.random.default_rng(2)
    res = cv3.evaluar(_datos(m + 9 + rng.normal(0, 2, 60), m, m - 3 + rng.normal(0, 2, 60)))
    assert res["veredicto"] == cv3.CONFIRMADA
    assert all(c["cumple"] for c in res["comparaciones"].values())
    assert res["comparaciones"]["baja_menos_media"]["ic_bajo"] > 0


def test_no_confirmada_si_media_menos_alta_no_excluye_el_cero():
    """Es justo el caso que el veredicto del script de PS daria por bueno: media de media − alta >= 0 sin IC sobre 0."""
    m = _base()
    rng = np.random.default_rng(3)
    res = cv3.evaluar(_datos(m + 9 + rng.normal(0, 2, 60), m, m - 0.2 + rng.normal(0, 3, 60)))
    c = res["comparaciones"]["media_menos_alta"]
    assert c["ic_bajo"] <= 0 < c["ic_alto"]
    assert res["veredicto"] == cv3.NO_CONFIRMADA and "media_menos_alta" in res["texto"]
    assert "profundidad del market maker" in res["texto"]


def test_no_confirmada_si_el_orden_es_el_inverso():
    m = _base()
    res = cv3.evaluar(_datos(m - 5, m, m + 5))
    assert res["veredicto"] == cv3.NO_CONFIRMADA
    assert not any(c["cumple"] for c in res["comparaciones"].values())


def test_un_par_incompleto_no_es_evaluable():
    m = _base()
    baja = list(m + 9)
    baja[7] = None
    res = cv3.evaluar(_datos(baja, m, m - 3))
    assert res["veredicto"] == cv3.NO_EVALUABLE
    assert res["comparaciones"]["baja_menos_media"]["n"] == 59


def test_firma_distinta_no_es_evaluable():
    m = _base()
    res = cv3.evaluar(_datos(m + 9, m, m - 3, seed_base=8000))
    assert res["veredicto"] == cv3.NO_EVALUABLE and any("seed_base" in p for p in res["problemas"])
    res = cv3.evaluar(_datos(m + 9, m, m - 3, tamanos=(1000,)))
    assert res["veredicto"] == cv3.NO_EVALUABLE


def test_identifica_los_escenarios_por_factor_y_no_por_nombre():
    """Con los nombres de la v2 (baja = ×0,25) el resultado tiene que ser el mismo."""
    m = _base()
    d = _datos(m + 9, m, m - 3)
    for r in d["resultados"].values():
        r["escenario"] = {4.0: "alta", 1.0: "media", 0.25: "baja"}[r["factor"]]
    assert cv3.evaluar(d)["veredicto"] == cv3.CONFIRMADA


def test_bootstrap_reproducible():
    a, b = _base(seed=4), _base(seed=5)
    assert cv3.diferencia_pareada(a, b) == cv3.diferencia_pareada(a, b)
    with pytest.raises(ValueError):
        cv3.diferencia_pareada([1.0, 2.0], [1.0])


def test_lectura_del_c6b_reproduce_los_numeros_publicados():
    """Solo lectura (esos datos eligieron el orden de la v3): +9,50 y +2,90 bps de docs/c6_liquidez_resultado_PS.md."""
    datos = json.loads(C6B.read_text(encoding="utf-8"))
    res = cv3.evaluar(datos, dict(cv3.CRITERIO, seed_base=8000))
    c = res["comparaciones"]
    assert c["baja_menos_media"]["media"] == pytest.approx(9.50, abs=0.01)
    assert c["media_menos_alta"]["media"] == pytest.approx(2.90, abs=0.01)
    assert res["escenarios"]["baja"]["costo_medio_bps"] == pytest.approx(24.15, abs=0.01)
    assert res["veredicto"] == cv3.CONFIRMADA


def test_resultado_oficial_del_c6c_no_confirma_la_v3():
    """C-6c corrido el 5 nov (semillas 8101-8160): docs/c6c_confirmacion_v3_BF.md. El JSON del criterio coincide con el
    que se calcula aquí desde la corrida."""
    base = ROOT / "data/colab_resultados/c6c_liquidez"
    datos = json.loads((base / "c6c_liquidez.json").read_text(encoding="utf-8"))
    res = cv3.evaluar(datos)
    assert res["problemas"] == [] and res["veredicto"] == cv3.NO_CONFIRMADA
    c = res["comparaciones"]
    assert c["baja_menos_media"]["media"] == pytest.approx(6.69, abs=0.01)
    assert c["baja_menos_media"]["ic_bajo"] < 0 and not c["baja_menos_media"]["cumple"]
    assert c["media_menos_alta"]["media"] == pytest.approx(7.56, abs=0.01) and c["media_menos_alta"]["cumple"]
    colab = json.loads((base / "c6c_confirmacion_v3.json").read_text(encoding="utf-8"))
    assert colab["veredicto"] == res["veredicto"] and colab["comparaciones"] == res["comparaciones"]


def test_cli_escribe_utf8_sin_bom(tmp_path):
    spec = importlib.util.spec_from_file_location("confirmar_v3_c6c", ROOT / "scripts/confirmar_v3_c6c.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    m = _base()
    entrada = tmp_path / "c6c.json"
    entrada.write_text(json.dumps(_datos(m + 9, m, m - 3)), encoding="utf-8")
    assert mod.main(["--entrada", str(entrada), "--out-json", str(tmp_path / "o.json"),
                     "--out-md", str(tmp_path / "o.md")]) == 0
    for p in ("o.json", "o.md"):
        assert not (tmp_path / p).read_bytes().startswith(b"\xef\xbb\xbf")
    assert json.loads((tmp_path / "o.json").read_text(encoding="utf-8"))["veredicto"] == cv3.CONFIRMADA
    assert "baja − media" in (tmp_path / "o.md").read_text(encoding="utf-8")
