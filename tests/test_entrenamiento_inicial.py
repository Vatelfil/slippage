"""Pruebas del entrenamiento inicial de la 2.3.5 (borrador de PS pendiente de revision de BF). Sin ABIDES."""
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


@pytest.fixture(scope="module")
def corrida(tmp_path_factory):
    entreno = _cargar("entreno", "scripts/colab/entrenamiento_inicial_ps.py")
    out = tmp_path_factory.mktemp("t5")
    args = ["--entorno", "poisson", "--episodes", "10", "--eval-seeds", "2", "--ventana-min", "5", "--out-dir", str(out)]
    ruta = entreno.main(args)
    return entreno, args, out, ruta


def test_el_ensayo_con_poisson_completa_todas_las_etapas(corrida):
    _, _, out, ruta = corrida
    estado = json.loads(Path(ruta).read_text(encoding="utf-8"))
    assert estado["entrenamiento_completo"] is True and estado["episodios_entrenados"] == 10
    for k in ("evaluacion_sin_entrenar", "evaluacion_entrenada", "evaluacion_entrenada_estocastica", "referencias", "vigilancia_D3"):
        assert k in estado
    assert set(estado["referencias"]) == {"agresiva_market", "twap_limit_medio", "pasiva_limit"}
    assert (out / "entrenamiento_apertura.csv").exists() and (out / "checkpoints_apertura" / "checkpoint_last.pt").exists()
    v = estado["vigilancia_D3"]
    assert v["umbral"] == 0.95 and v["cumple"] == (v["cumplimiento_medio"] >= 0.95)


def test_volver_a_ejecutar_reanuda_sin_repetir_el_entrenamiento(corrida):
    entreno, args, out, ruta = corrida
    antes = json.loads(Path(ruta).read_text(encoding="utf-8"))
    entreno.main(args)
    despues = json.loads(Path(ruta).read_text(encoding="utf-8"))
    assert despues["segundos_entrenamiento"] == antes["segundos_entrenamiento"]
    assert despues["episodios_entrenados"] == 10


def test_el_analisis_genera_informe_y_figura(corrida, tmp_path):
    _, _, out, ruta = corrida
    analisis = _cargar("analisis", "scripts/analizar_entrenamiento_inicial.py")
    md, png = tmp_path / "informe.md", tmp_path / "curvas.png"
    analisis.main(["--estado", str(ruta), "--csv", str(out / "entrenamiento_apertura.csv"),
                   "--out-md", str(md), "--out-png", str(png)])
    texto = md.read_text(encoding="utf-8")
    assert png.exists() and "Regla de vigilancia de D3" in texto and "Red sin entrenar" in texto
    assert "Poisson" in texto  # el ensayo se declara como tal
    assert "Comparación pareada" in texto and "Lectura preliminar de PS" in texto


def test_el_diagnostico_de_la_politica_corre_y_guarda_resumen(corrida):
    _, _, out, _ = corrida
    diag = _cargar("diag", "scripts/colab/diagnostico_politica_entrenada_ps.py")
    ruta = diag.main(["--checkpoint", str(out / "checkpoints_apertura" / "checkpoint_last.pt"), "--entorno", "poisson",
                      "--ventana-min", "5", "--seeds", "5001", "--out-dir", str(out)])
    r = json.loads(Path(ruta).read_text(encoding="utf-8"))
    assert r["parametros_no_finitos"] == [] and set(r) >= {"determinista", "estocastico"}
    assert 0.0 <= r["determinista"]["cumplimiento_medio"] <= 1.5


def test_la_opcion_a_de_d3_se_puede_entrenar_y_queda_en_la_firma(tmp_path):
    entreno = _cargar("entreno_a", "scripts/colab/entrenamiento_inicial_ps.py")
    ruta = entreno.main(["--entorno", "poisson", "--episodes", "10", "--eval-seeds", "2", "--ventana-min", "5",
                         "--riesgo-sobre", "pendiente", "--out-dir", str(tmp_path)])
    estado = json.loads(Path(ruta).read_text(encoding="utf-8"))
    assert estado["firma"]["riesgo_sobre"] == "pendiente" and estado["entrenamiento_completo"] is True

