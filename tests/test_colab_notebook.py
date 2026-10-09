"""El notebook de Colab (notebooks/Colab_Sprint4_BF.ipynb) debe llamar a las
CLIs con argumentos que existen y encadenar los nombres de archivo que los
scripts realmente escriben."""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = REPO_ROOT / "notebooks" / "Colab_Sprint4_BF.ipynb"
SCRIPTS = (
    "scripts/colab/rmsc04_grid_search.py",
    "scripts/colab/rmsc04_validate.py",
    "scripts/colab/beta_sweep_abides.py",
    "src/envs/collect_abides_stats.py",
    "src/envs/test_abides.py",
    "src/envs/test_abides_ejecutor.py",
)
FLAGS_DE_CONDA = {"--no-capture-output"}


def _celdas():
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    return ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]


def test_cada_celda_usa_solo_argumentos_que_la_cli_define():
    usados = set()
    for celda in _celdas():
        if celda.startswith("%%writefile"):
            continue
        for script in SCRIPTS:
            if script not in celda:
                continue
            usados.add(script)
            fuente = (REPO_ROOT / script).read_text(encoding="utf-8")
            comando = celda[celda.index(script):]
            for flag in set(re.findall(r"(?<![\w-])--[a-z][a-z-]*", comando)) - FLAGS_DE_CONDA:
                assert f'"{flag}"' in fuente, f"{script} no define {flag}"
    assert usados == set(SCRIPTS), f"scripts sin celda: {set(SCRIPTS) - usados}"


def test_nombres_de_archivo_encadenados_entre_celdas():
    texto = "\n".join(_celdas())
    grid = (REPO_ROOT / "scripts/colab/rmsc04_grid_search.py").read_text(encoding="utf-8")
    val = (REPO_ROOT / "scripts/colab/rmsc04_validate.py").read_text(encoding="utf-8")
    assert 'f"rmsc04_grid_{args.ticker}_{args.snapshot}.json"' in grid
    assert 'f"rmsc04_ipsa_{args.ticker}_{args.snapshot}.json"' in val
    # la celda 10 lee lo que escribe la 9; las celdas 11 y 12 leen lo que escribe la 10
    assert texto.count('--grid-json "{RESULTS_DIR}/rmsc04_grid_FALABELLA_2026-08-23.json"') == 1
    assert texto.count('--calibrated-json "{RESULTS_DIR}/rmsc04_ipsa_FALABELLA_2026-08-23.json"') == 2
    assert "--ticker FALABELLA --snapshot 2026-08-23 --seeds 3 --out-dir" in texto
    assert "BRANCH = 'feature/2.2.4-2.2.3-rmsc04-recompensa-BF'" in texto


def test_todas_las_celdas_de_trabajo_escriben_en_results_dir():
    for celda in _celdas():
        if any(s in celda for s in SCRIPTS[:4]):
            assert '--out-dir "{RESULTS_DIR}"' in celda
