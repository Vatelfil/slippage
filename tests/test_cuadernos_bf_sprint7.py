"""Cuadernos de BF del Sprint 7: C-6c (confirmación de la v3) y tamaños en la liquidez media (diseño en estrella).

Verifica que las celdas llamen a las CLIs con opciones que existen, que las semillas no se crucen con las de otros
experimentos y que los archivos de salida no choquen con los de las 90 corridas."""
import json
import re
import subprocess
from pathlib import Path

import pytest

from src.envs import escenarios_liquidez as el
from src.experiments import confirmacion_v3 as cv3

REPO = Path(__file__).resolve().parents[1]
C6C = REPO / "notebooks/Colab_C6c_confirmacion_v3_BF.ipynb"
C6B = REPO / "notebooks/Colab_C6b_liquidez_mm_BF.ipynb"
TAM = REPO / "notebooks/Colab_tamanos_media_BF.ipynb"
RAMA_PS = "origin/feature/ps-3-2-1-cuadernos"   # la que clona el cuaderno de tamaños (el mismo código de las 90)
# Opciones que el cuaderno de tamaños toma de la rama de PS y que main todavía no tiene
SOLO_EN_RAMA_PS = {"--semilla-inicial"}


def _nb(ruta):
    return json.loads(ruta.read_text(encoding="utf-8"))


def _codigo(ruta):
    return ["".join(c["source"]) for c in _nb(ruta)["cells"] if c["cell_type"] == "code"]


def _celda(ruta, prefijo):
    return next(c for c in _codigo(ruta) if c.startswith(prefijo))


def _comando(celda, script):
    return celda[celda.index(script):].split("\n")[0]


def _flags(comando):
    return set(re.findall(r"(?<![\w-])--[a-z][a-z-]*", comando)) - {"--no-capture-output"}


def _valor(comando, flag):
    m = re.search(rf"{flag} (\S+)", comando)
    return m.group(1) if m else None


def _definidas(fuente):
    return set(re.findall(r'add_argument\(\s*"(--[a-z][a-z-]*)"', fuente))


@pytest.mark.parametrize("ruta", [C6C, TAM], ids=lambda r: r.name)
def test_utf8_sin_bom_nbformat_4_y_sin_salidas(ruta):
    assert not ruta.read_bytes().startswith(b"\xef\xbb\xbf")
    nb = _nb(ruta)
    assert nb["nbformat"] == 4
    assert all(not c.get("outputs") for c in nb["cells"] if c["cell_type"] == "code")


def test_c6c_copia_la_preparacion_del_c6b_salvo_la_rama():
    prep = lambda r: [c for c in _codigo(r) if re.match(r"# CELDA [1-9]\b", c)]
    a, b = prep(C6B), prep(C6C)
    assert len(a) == len(b) == 9
    for x, y in zip(a, b):
        if x.startswith("# CELDA 7"):
            assert "origin/feature/bf-sprint7-cuadernos" in y and "confirmacion_v3.py" in y
        else:
            assert x == y


def test_c6c_corre_el_criterio_fijado_con_opciones_que_existen():
    celda = _celda(C6C, "# CELDA 10")
    script = "scripts/colab/c6_escenarios_liquidez_bf.py"
    cmd = _comando(celda, script)
    assert _flags(cmd) <= _definidas((REPO / script).read_text(encoding="utf-8"))
    assert _valor(cmd, "--escenarios-json") == "data/scenarios/escenarios_liquidez_v3.json"
    assert _valor(cmd, "--tamanos") == str(cv3.CRITERIO["q_slice"])
    assert _valor(cmd, "--n-semillas") == str(cv3.CRITERIO["n_semillas"])
    assert _valor(cmd, "--seed-base") == str(cv3.CRITERIO["seed_base"])
    assert "--entorno" not in cmd and "--ticker" not in cmd and "--tramo" not in cmd   # los valores por defecto del criterio
    # los factores del JSON v3 son los del criterio
    assert el.cargar_escenarios(REPO / "data/scenarios/escenarios_liquidez_v3.json") == cv3.CRITERIO["factores"]
    assert list(el.claves_de(REPO / "data/scenarios/escenarios_liquidez_v3.json")) == cv3.CRITERIO["claves_abides"]
    salida = _valor(cmd, "--out")
    criterio = _comando(_celda(C6C, "# CELDA 11"), "scripts/confirmar_v3_c6c.py")
    assert _flags(criterio) <= _definidas((REPO / "scripts/confirmar_v3_c6c.py").read_text(encoding="utf-8"))
    assert _valor(criterio, "--entrada") == salida and "--seed-base" not in criterio


def test_semillas_del_c6c_no_cruzan_otros_experimentos():
    s = set(cv3.semillas())
    assert s == set(range(8101, 8161))
    assert not s & set(range(8001, 8061))           # C-6b
    assert not s & set(range(8001, 8031))           # C-6 (30 semillas desde la 8001)
    assert not s & set(range(1001, 5001))           # entrenamiento de redes con semilla 1000 a 4000
    assert not s & set(range(5001, 5301))           # evaluación de 15 y 300 semillas
    assert not s & set(range(90001, 90031))         # evaluación del Maestro


def _parametros_tam():
    celda = _celda(TAM, "# CELDA 10")
    ns = {"RESULTS_DIR": "/r"}
    exec(celda, ns)  # solo asignaciones y asserts
    return ns


def test_tamanos_parametros_y_salida():
    ns = _parametros_tam()
    assert ns["FACTOR_TAMANO"] in (0.5, 1.5) and ns["ESCENARIO"] == "media" and ns["SEMILLA_INICIAL"] == 4
    assert ns["SEMILLAS"] == 3 and ns["OUT"] == f"/r/tamanos/media_f{ns['FACTOR']}/{ns['PARTE']}"
    for parte, ids in (("A", range(1, 6)), ("B", range(6, 11))):
        celda = _celda(TAM, "# CELDA 10").replace("PARTE = 'A'", f"PARTE = '{parte}'")
        ns = {"RESULTS_DIR": "/r"}
        exec(celda, ns)
        assert ns["ORDENES"].split() == [f"MO-{i:02d}" for i in ids]


@pytest.mark.parametrize("script", ["scripts/colab/evaluar_sistema_ps.py", "scripts/colab/benchmarks_meta_ordenes_ps.py"])
def test_tamanos_mismas_opciones_que_las_90_mas_el_factor(script):
    celda = next(c for c in _codigo(TAM) if script in c and (c.startswith("# CELDA 11") or c.startswith("# CELDA 12")))
    cmd = _comando(celda, script)
    assert _valor(cmd, "--factor-tamano") == "{FACTOR_TAMANO}"
    assert _valor(cmd, "--escenario") == "{ESCENARIO}" and _valor(cmd, "--semilla-inicial") == "{SEMILLA_INICIAL}"
    assert _valor(cmd, "--escenarios-json") == "data/scenarios/escenarios_liquidez_v3.json"
    assert _valor(cmd, "--meta-ordenes") == "data/meta_ordenes/meta_ordenes_v2_candidata.json"
    assert "--impacto" in cmd
    if "evaluar_sistema" in script:
        assert "--completar-al-cierre" in cmd and _valor(cmd, "--modo") == "muestreo"
        assert "{RESULTS_DIR}/sistema_final/maestro/checkpoint_last.pt" in cmd
    # opciones que existen en el script de este repo, salvo las que vienen de la rama de PS
    assert _flags(cmd) - SOLO_EN_RAMA_PS <= _definidas((REPO / script).read_text(encoding="utf-8"))


def _fuente_rama_ps(ruta):
    r = subprocess.run(["git", "show", f"{RAMA_PS}:{ruta}"], cwd=REPO, capture_output=True)
    if r.returncode != 0:
        pytest.skip(f"no está {RAMA_PS} en este clon")
    return r.stdout.decode("utf-8")


@pytest.mark.parametrize("script", ["scripts/colab/evaluar_sistema_ps.py", "scripts/colab/benchmarks_meta_ordenes_ps.py"])
def test_tamanos_usa_opciones_que_existen_en_la_rama_que_clona(script):
    assert RAMA_PS.split("/", 1)[1] in _celda(TAM, "# CELDA 7")
    celda = next(c for c in _codigo(TAM) if script in c and (c.startswith("# CELDA 11") or c.startswith("# CELDA 12")))
    assert _flags(_comando(celda, script)) <= _definidas(_fuente_rama_ps(script))


def test_tamanos_es_igual_al_cuaderno_media_de_ps_salvo_el_factor():
    """Mismo código, mismas opciones: así cada corrida queda pareada con la media x1 de PS."""
    ps = _fuente_rama_ps("notebooks/Colab_90corridas_media_A.ipynb")
    cel_ps = ["".join(c["source"]) for c in json.loads(ps)["cells"] if c["cell_type"] == "code"]
    for n in range(1, 10):
        p = next(c for c in cel_ps if c.startswith(f"# CELDA {n} ") or c.startswith(f"# CELDA {n}\n"))
        b = next(c for c in _codigo(TAM) if c.startswith(f"# CELDA {n} ") or c.startswith(f"# CELDA {n}\n"))
        assert p == b, f"CELDA {n}"
    for n in (11, 12):
        p = next(c for c in cel_ps if c.startswith(f"# CELDA {n}:")).split("\n", 1)[1]
        b = next(c for c in _codigo(TAM) if c.startswith(f"# CELDA {n}:")).split("\n", 1)[1]
        assert b.replace(" --factor-tamano {FACTOR_TAMANO}", "").rstrip() == p.rstrip()


def test_nombre_de_archivo_no_choca_con_las_90():
    noventa = el.sufijo_condicion("media", 1.0)
    for f in (0.5, 1.5):
        assert el.sufijo_condicion("media", f) != noventa
        assert el.sufijo_condicion("media", f).endswith(f"_tam-{f:g}")
    assert el.sufijo_condicion("media", 0.5) != el.sufijo_condicion("media", 1.5)
    ns = _parametros_tam()
    assert "/corridas_90/" not in ns["OUT"]


def test_cantidades_del_diseno_en_estrella():
    mo = json.loads((REPO / "data/meta_ordenes/meta_ordenes_v2_candidata.json").read_text(encoding="utf-8"))["meta_ordenes"]
    for f, pct, pct_cierre in ((0.5, 5.0, 2.5), (1.5, 15.0, 7.5)):
        for o in el.ajustar_ordenes(mo, f):
            esperado = pct_cierre if o["tramo_inicio"] == "cierre" else pct
            assert 100 * o["cantidad"] / o["volumen_dia_simulado"] == pytest.approx(esperado, abs=0.05)


def test_semillas_del_diseno_en_estrella_son_las_de_las_90():
    """Semillas 4 a 6 (pareo con la media x1); no repiten un día de la 3.1.3 (semillas 1 a 3)."""
    mo = json.loads((REPO / "data/meta_ordenes/meta_ordenes_v2_candidata.json").read_text(encoding="utf-8"))["meta_ordenes"]
    ns = _parametros_tam()
    s = list(range(ns["SEMILLA_INICIAL"], ns["SEMILLA_INICIAL"] + ns["SEMILLAS"]))
    assert s == [4, 5, 6]
    dias = {x + int(o["semilla"]) for o in mo for x in s}
    assert len(dias) == len(mo) * len(s)
    assert not dias & {x + int(o["semilla"]) for o in mo for x in (1, 2, 3)}
