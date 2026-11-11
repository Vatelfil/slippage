"""Cuadernos de las 90 corridas (3.2.1, PS): llaman a las CLIs con opciones que existen, cada uno corre su escenario
y su parte, usan la corrección del cierre y las semillas nuevas."""
import json
import re
from pathlib import Path

import pytest

from scripts.colab import benchmarks_meta_ordenes_ps as bm
from scripts.colab import evaluar_sistema_ps as ev

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = ("scripts/colab/evaluar_sistema_ps.py", "scripts/colab/benchmarks_meta_ordenes_ps.py",
           "scripts/consolidar_resultados_3_2_2.py")
CUADERNOS = sorted((REPO / "notebooks").glob("Colab_90corridas_*.ipynb"))


def _codigo(ruta):
    nb = json.loads(ruta.read_text(encoding="utf-8"))
    return ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]


def test_semillas_nuevas():
    assert ev.semillas(3) == [1, 2, 3]            # por defecto, las de siempre
    assert ev.semillas(3, 4) == [4, 5, 6]
    assert bm.semillas(3, 4) == [4, 5, 6]


def test_semillas_4_a_6_no_chocan_con_otras_ordenes():
    """La semilla de mercado es semilla + semilla de la orden (9010, 9020, ...): con semillas hasta 9 no se repite un día."""
    mo = json.loads((REPO / "data/meta_ordenes/meta_ordenes_v2_candidata.json").read_text(encoding="utf-8-sig"))
    mo = mo["meta_ordenes"] if isinstance(mo, dict) else mo
    dias = [s + int(o["semilla"]) for o in mo for s in ev.semillas(3, 4)]
    assert len(dias) == len(set(dias))
    previos = {s + int(o["semilla"]) for o in mo for s in ev.semillas(3, 1)}
    assert not previos & set(dias)                 # tampoco se repiten los de la 3.1.3


def test_hay_siete_cuadernos():
    nombres = {c.name for c in CUADERNOS}
    assert {f"Colab_90corridas_{e}_{p}.ipynb" for e in ("baja", "media", "alta") for p in "AB"} <= nombres
    assert "Colab_90corridas_prueba.ipynb" in nombres


@pytest.mark.parametrize("ruta", CUADERNOS, ids=lambda r: r.name)
def test_cada_celda_usa_solo_opciones_que_existen(ruta):
    for celda in _codigo(ruta):
        for script in SCRIPTS:
            if script not in celda:
                continue
            fuente = (REPO / script).read_text(encoding="utf-8")
            comando = celda[celda.index(script):].split("\n")[0]
            for flag in set(re.findall(r"(?<![\w-])--[a-z][a-z-]*", comando)) - {"--no-capture-output"}:
                assert f'"{flag}"' in fuente, f"{script} no define {flag} ({ruta.name})"


@pytest.mark.parametrize("ruta", [c for c in CUADERNOS if "prueba" not in c.name], ids=lambda r: r.name)
def test_escenario_parte_y_opciones(ruta):
    esc, parte = re.match(r"Colab_90corridas_(\w+)_([AB])\.ipynb", ruta.name).groups()
    texto = "\n".join(_codigo(ruta))
    assert f"ESCENARIO = '{esc}'" in texto and f"PARTE = '{parte}'" in texto
    esperado = "MO-01 MO-02 MO-03 MO-04 MO-05" if parte == "A" else "MO-06 MO-07 MO-08 MO-09 MO-10"
    assert f"ORDENES = '{esperado}'" in texto
    assert "SEMILLA_INICIAL = 4" in texto
    sistema = next(c for c in _codigo(ruta) if "evaluar_sistema_ps.py --" in c)
    assert "--completar-al-cierre" in sistema and "--impacto" in sistema and "--semilla-inicial" in sistema
    bench = next(c for c in _codigo(ruta) if "benchmarks_meta_ordenes_ps.py --" in c)
    assert "--impacto" in bench and "--semilla-inicial" in bench
    assert "escenarios_liquidez_v3.json" in sistema and "escenarios_liquidez_v3.json" in bench
