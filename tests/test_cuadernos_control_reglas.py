"""Cuadernos del control de la 3.2.3 (PS): mismas órdenes, semillas, escenario y checkpoints que las 90 corridas de la
liquidez media, y opciones que existen en las CLIs."""
import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = ("scripts/colab/evaluar_sistema_ps.py", "scripts/control_reglas_3_2_3.py")
CUADERNOS = [REPO / "notebooks" / f"Colab_control_reglas_media_{p}.ipynb" for p in "AB"]


def _codigo(ruta):
    nb = json.loads(ruta.read_text(encoding="utf-8"))
    return ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]


def test_existen_los_dos_cuadernos():
    assert all(c.exists() for c in CUADERNOS)


@pytest.mark.parametrize("ruta", CUADERNOS, ids=lambda r: r.name)
def test_solo_opciones_que_existen(ruta):
    for celda in _codigo(ruta):
        for script in SCRIPTS:
            if script not in celda:
                continue
            fuente = (REPO / script).read_text(encoding="utf-8")
            comando = celda[celda.index(script):].split("\n")[0]
            for flag in set(re.findall(r"(?<![\w-])--[a-z][a-z-]*", comando)) - {"--no-capture-output"}:
                assert f'"{flag}"' in fuente, f"{script} no define {flag} ({ruta.name})"


@pytest.mark.parametrize("ruta", CUADERNOS, ids=lambda r: r.name)
def test_mismas_condiciones_que_las_90(ruta):
    parte = ruta.stem[-1]
    texto = "\n".join(_codigo(ruta))
    esperado = "MO-01 MO-02 MO-03 MO-04 MO-05" if parte == "A" else "MO-06 MO-07 MO-08 MO-09 MO-10"
    assert f"ORDENES = '{esperado}'" in texto and f"PARTE = '{parte}'" in texto
    assert "ESCENARIO = 'media'" in texto and "SEMILLA_INICIAL = 4" in texto
    corridas = [c for c in _codigo(ruta) if "evaluar_sistema_ps.py --" in c]
    assert sorted(re.search(r"--regla (\w+)", c).group(1) for c in corridas) == ["fija", "uniforme"]
    for c in corridas:
        for flag in ("--completar-al-cierre", "--impacto", "--modo muestreo", "--semilla-inicial", "escenarios_liquidez_v3.json",
                     "sistema_final/maestro/checkpoint_last.pt", "ejecutor_cierre.pt"):
            assert flag in c, f"falta {flag} en {ruta.name}"
    assert "control_reglas/" in texto and "corridas_90/" in texto
