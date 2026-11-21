"""Pruebas unitarias del análisis de sensibilidad 3.2.4 (MR): scripts/sensibilidad_3_2_4_MR.py."""
from pathlib import Path
import json

import pytest

from scripts import sensibilidad_3_2_4_MR as s324

ROOT = Path(__file__).resolve().parents[1]
CORRIDAS = ROOT / "data/analysis/3_2_2/corridas.csv"


def test_sensibilidad_3_2_4_reproduce_cifras_y_figuras(tmp_path):
    res = s324.ejecutar(CORRIDAS, tmp_path, n_boot=500)

    # Tamaño: Friedman pareado significativo al 5%
    pr_tam = res["tamano_crudo"]["pruebas"]["dif_TWAP"]
    assert pr_tam["n_bloques"] == 30
    assert pr_tam["friedman_Q"] == pytest.approx(6.4667, abs=1e-3)
    assert pr_tam["friedman_p"] == pytest.approx(0.0394, abs=1e-3)
    assert pr_tam["spearman_rho"] == pytest.approx(-0.0487, abs=1e-3)

    # Robustez sin días bajo 95%
    rob = res["tamano_crudo"]["robustez_cumpl_95"]["dif_TWAP"]
    assert rob["n_bloques"] == 25
    assert rob["friedman_p"] == pytest.approx(0.0478, abs=1e-3)

    # Profundidad: Kruskal-Wallis no significativo
    pr_prof = res["profundidad_crudo"]["pruebas"]["dif_TWAP"]
    assert pr_prof["kruskal_H"] == pytest.approx(0.1449, abs=1e-3)
    assert pr_prof["kruskal_p"] == pytest.approx(0.9301, abs=1e-3)

    # Tramo horario: Kruskal-Wallis significativo
    kw_tr = res["tramo_crudo"]["kruskal_dif_TWAP"]
    assert kw_tr["H"] == pytest.approx(8.9779, abs=1e-3)
    assert kw_tr["p"] == pytest.approx(0.0112, abs=1e-3)

    # Archivos de salida y figuras
    for fname in (
        "sensibilidad_3_2_4.json",
        "derivadas_tamano.csv",
        "derivadas_profundidad.csv",
        "sensibilidad_tramo.csv",
        "sensibilidad_tamano.png",
        "sensibilidad_profundidad.png",
        "sensibilidad_tramo.png",
    ):
        assert (tmp_path / fname).exists() and (tmp_path / fname).stat().st_size > 0
