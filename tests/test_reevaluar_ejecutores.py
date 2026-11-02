"""Prueba del reevaluador de Ejecutores con muchas semillas (Poisson, corridas muy cortas)."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _cargar(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, ROOT / ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ent = _cargar("ent_reeval", "scripts/colab/entrenamiento_inicial_ps.py")
ree = _cargar("reeval", "scripts/colab/reevaluar_ejecutores_ps.py")


def test_reevalua_redes_controles_y_referencias_y_es_reanudable(tmp_path):
    raiz = tmp_path / "v4_demo"
    ent.main(["--entorno", "poisson", "--episodes", "10", "--eval-seeds", "2", "--seed", "1000", "--sin-monitoreo",
              "--out-dir", str(raiz / "d3_opcion0_s1000")])
    assert [e for e, _, _ in ree.descubrir([raiz])] == ["v4_demo__d3_opcion0_s1000"]
    salida = tmp_path / "reeval"
    hechos = ree.main(["--raices", str(raiz), "--entorno", "poisson", "--n-semillas", "4", "--out-dir", str(salida)])
    assert hechos["redes"] == ["v4_demo__d3_opcion0_s1000"] and hechos["controles"] == [1000]
    red = json.loads((salida / "red_v4_demo__d3_opcion0_s1000.json").read_text(encoding="utf-8"))
    assert len(red["slippage_por_semilla"]) == 4 and red["episodios"] == 10
    assert (salida / "control_s1000.json").exists() and len(list(salida.glob("ref_*.json"))) == 3
    # al volver a lanzarlo no repite nada
    otra = ree.main(["--raices", str(raiz), "--entorno", "poisson", "--n-semillas", "4", "--out-dir", str(salida)])
    assert otra["redes"] == [] and otra["controles"] == [] and otra["referencias"] == []
