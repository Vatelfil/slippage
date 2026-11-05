"""Cuaderno del Maestro v2: usa opciones que existen, entrena con las correcciones y evalua en las mismas
condiciones que la liquidez media de las 90 corridas."""
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
NB = REPO / "notebooks" / "Colab_maestro_v2.ipynb"
SCRIPTS = ("scripts/colab/evaluar_sistema_ps.py", "scripts/entrenar_maestro.py", "scripts/comparacion_estadistica_3_2_3.py")


def _codigo():
    return ["".join(c["source"]) for c in json.loads(NB.read_text(encoding="utf-8"))["cells"] if c["cell_type"] == "code"]


def test_solo_opciones_que_existen():
    for celda in _codigo():
        for script in SCRIPTS:
            if script not in celda:
                continue
            fuente = (REPO / script).read_text(encoding="utf-8")
            comando = celda[celda.index(script):].split("\n")[0]
            for flag in set(re.findall(r"(?<![\w-])--[a-z][a-z-]*", comando)) - {"--no-capture-output"}:
                assert f'"{flag}"' in fuente, f"{script} no define {flag}"


def test_entrena_y_evalua_con_las_correcciones():
    texto = "\n".join(_codigo())
    entrenar = next(c for c in _codigo() if "entrenar_maestro.py" in c)
    for f in ("--completar-al-cierre", "--sm-mercado", "--jornadas 2000", "--lambda-penalty 0.02", "--inicio-aleatorio", "ejecutor_elegido.pt"):
        assert f in entrenar
    evals = [c for c in _codigo() if "evaluar_sistema_ps.py --" in c]
    assert len(evals) == 2
    for c in evals:
        for f in ("--sm-mercado", "--completar-al-cierre", "--semilla-inicial 4", "--escenario media", "--nombre PPO_sistema_v2",
                  "escenarios_liquidez_v3.json", "--impacto", "--modo muestreo"):
            assert f in c
    assert "--referencias PPO_sistema TWAP VWAP" in texto and "corridas_90/media" in texto
