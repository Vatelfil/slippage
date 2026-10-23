"""Pruebas del lanzador y del resumen de estabilidad de D3 (Poisson, corridas muy cortas)."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _cargar(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, ROOT / ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


lanz = _cargar("d3_lanzador", "scripts/colab/d3_estabilidad_ps.py")
anal = _cargar("d3_analizador", "scripts/analizar_estabilidad_D3.py")


def test_semillas_de_red_no_pisan_las_de_evaluacion():
    for s in lanz.SEMILLAS_RED:
        assert not (s + 1 <= 5015 and s + 100 >= 5001), f"los episodios de la semilla {s} usarian semillas de evaluacion"


def test_plan_salta_las_terminadas_y_alterna_opciones(tmp_path):
    assert lanz.plan(tmp_path, ["0", "A"], [1000, 2000]) == [("0", 1000), ("A", 1000), ("0", 2000), ("A", 2000)]
    d = lanz.carpeta(tmp_path, "0", 1000)
    d.mkdir(parents=True)
    (d / "entrenamiento_inicial_apertura.json").write_text(json.dumps({"vigilancia_D3": {"cumple": True}}), encoding="utf-8")
    assert ("0", 1000) not in lanz.plan(tmp_path, ["0", "A"], [1000, 2000])


@pytest.fixture(scope="module")
def corridas(tmp_path_factory):
    out = tmp_path_factory.mktemp("d3")
    lanz.main(["--entorno", "poisson", "--episodes", "10", "--eval-seeds", "7", "--semillas", "1000", "2000", "--out-dir", str(out)])
    return out


def test_lanzador_deja_una_carpeta_terminada_por_corrida(corridas):
    assert all(lanz.terminada(corridas, o, s) for o in ("0", "A") for s in (1000, 2000))
    assert lanz.plan(corridas, ["0", "A"], [1000, 2000]) == []


def test_lanzador_reanuda_sin_repetir(corridas):
    assert lanz.main(["--entorno", "poisson", "--episodes", "10", "--eval-seeds", "7", "--semillas", "1000", "2000",
                      "--out-dir", str(corridas)]) == []


def test_analizador_arma_informe_json_y_figura(corridas, tmp_path):
    md = anal.main(["--dir", str(corridas), "--out-json", str(tmp_path / "e.json"), "--out-png", str(tmp_path / "e.png"),
                    "--out-md", str(tmp_path / "e.md")])
    texto = md.read_text(encoding="utf-8")
    assert "Resumen por opción" in texto and (tmp_path / "e.png").stat().st_size > 1000
    datos = json.loads((tmp_path / "e.json").read_text(encoding="utf-8"))
    assert len(datos["corridas"]) == 4 and set(datos["resumen"]) == {"0", "A"}


def test_wilcoxon_pareado_ignora_none_y_pocos_datos():
    assert anal.wilcoxon_pareado([1, 2, None], [2, 3, 4]) is None
    a, b = [1.0, 2.0, 3.0, 4.0, 5.0, 6.5, 8.0], [2.0, 3.5, 3.1, 5.2, 6.1, 7.7, 9.3]
    assert 0.0 < anal.wilcoxon_pareado(a, b) < 0.05


def test_resumen_cuenta_las_que_disparan():
    filas = [{"opcion": "0", "semilla": s, "cumpl_argmax": c, "cumpl_muestreo": 1.0, "slip_argmax": 1.0, "slip_muestreo": 1.0,
              "dispara_regla": c < 0.95} for s, c in [(1, 0.0), (2, 0.9), (3, 1.0)]]
    filas += [{"opcion": "A", "semilla": s, "cumpl_argmax": 1.0, "cumpl_muestreo": 1.0, "slip_argmax": 2.0, "slip_muestreo": 2.0,
               "dispara_regla": False} for s in (1, 2, 3)]
    r = anal.resumen_por_opcion(filas)
    assert r["0"]["dispara"] == 2 and r["A"]["dispara"] == 0 and r["0"]["semillas_disparan"] == [1, 2]
    assert anal.fisher(r) is not None
