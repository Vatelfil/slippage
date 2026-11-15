"""Capitulo 7 (PS): las cifras exploratorias salen de las 90 corridas y del tamano 0,5, y cuadran con el informe."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("figuras_capitulo7_PS", ROOT / "scripts/figuras_capitulo7_PS.py")
fc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fc)


def test_cifras_y_figuras(tmp_path):
    fc.main(["--out-dir", str(tmp_path)])
    r = json.loads((tmp_path / "cifras_capitulo7.json").read_text(encoding="utf-8"))
    assert r["dia"]["n"] == 90 and r["dia"]["spearman_rho"] < -0.7
    assert r["tramo"]["grupos"]["cierre"]["wilcoxon_p_holm"] < 0.05
    assert r["tramo"]["kruskal_p"] == pytest.approx(0.0112, abs=1e-3)
    assert r["tamano"]["TWAP"]["pendiente_por_0_5"] == pytest.approx(14.04, abs=0.01)
    assert (tmp_path / "diferencia_por_tramo.png").exists() and (tmp_path / "costo_vs_tamano_parcial.png").exists()
