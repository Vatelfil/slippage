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
    assert (tmp_path / "diferencia_por_tramo.png").exists() and (tmp_path / "costo_vs_tamano.png").exists()
    pp = r["tamano"]["por_punto"]
    assert pp["1.5"]["dif_twap"] == pytest.approx(-7.88, abs=0.01)
    assert pp["1.5"]["n_pares_ok"] == 25 and pp["1.5"]["dif_twap_ok"] == pytest.approx(-5.06, abs=0.01)
    assert pp["1.5"]["cumpl_min_sistema"] == pytest.approx(0.784, abs=1e-3)


def test_figuras_4_1_4(tmp_path):
    spec2 = importlib.util.spec_from_file_location("figuras_4_1_4", ROOT / "scripts/figuras_estadisticas_4_1_4_PS.py")
    f4 = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(f4)
    f4.main(["--out-dir", str(tmp_path)])
    r = json.loads((tmp_path / "cifras_4_1_4.json").read_text(encoding="utf-8"))
    assert r["diferencias"]["n"] == 90 and r["diferencias"]["wilcoxon_p"] == pytest.approx(0.386, abs=1e-3)
    assert r["varianzas"]["razon_twap"] == pytest.approx(0.77, abs=0.01) and r["varianzas"]["p_twap"] < 1e-8
    assert (tmp_path / "histograma_diferencias_90.png").exists()
