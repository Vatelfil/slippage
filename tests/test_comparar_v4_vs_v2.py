"""Pruebas del comparador V4 frente a V2 y al control (datos sintéticos con la forma de los JSON de Colab)."""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("comp_v4", ROOT / "scripts/comparar_v4_vs_v2_ps.py")
comp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comp)


def _escribir(base: Path, semilla: int, slip, cumpl=1.0, ctrl=None):
    d = base / f"d3_opcion0_s{semilla}"
    d.mkdir(parents=True)
    (d / "entrenamiento_inicial_apertura.json").write_text(json.dumps(
        {"evaluacion_entrenada_estocastica": {"slippage_por_semilla": list(slip), "cumplimiento_medio": cumpl}}), encoding="utf-8")
    if ctrl is not None:
        (base / f"control_sin_entrenar_muestreado_s{semilla}.json").write_text(
            json.dumps({"slippage_por_semilla": list(ctrl)}), encoding="utf-8")


def test_compara_v4_con_control_y_con_v2(tmp_path):
    rng = np.random.default_rng(0)
    ctrl = rng.normal(3, 2, 40)
    _escribir(tmp_path / "v2", 1000, ctrl + 3 + rng.normal(0, 0.3, 40))
    _escribir(tmp_path / "v4" / "A", 1000, ctrl + 1 + rng.normal(0, 0.3, 40), ctrl=ctrl)
    _escribir(tmp_path / "v4" / "B", 3000, ctrl - 1 + rng.normal(0, 0.3, 40), ctrl=ctrl)
    filas = comp.comparar(comp.cargar(tmp_path / "v2"), comp.cargar(tmp_path / "v4"))
    assert [r["semilla"] for r in filas] == [1000, 3000]
    a = filas[0]
    assert a["dif_v4_ctrl"] == pytest.approx(1.0, abs=0.3) and a["p_v4_ctrl"] < 0.05
    assert a["dif_v4_v2"] == pytest.approx(-2.0, abs=0.3)
    assert filas[1]["slip_v2"] is None and filas[1]["dif_v4_v2"] is None     # la semilla 3000 no tiene V2
    assert filas[1]["dif_v4_ctrl"] == pytest.approx(-1.0, abs=0.3)


def test_informe_y_figura(tmp_path):
    rng = np.random.default_rng(1)
    ctrl = rng.normal(3, 2, 40)
    _escribir(tmp_path / "v2", 1000, ctrl + 3 + rng.normal(0, 0.3, 40))
    _escribir(tmp_path / "v4", 1000, ctrl - 1 + rng.normal(0, 0.3, 40), cumpl=0.99, ctrl=ctrl)
    out = comp.main(["--v2-dir", str(tmp_path / "v2"), "--v4-dir", str(tmp_path / "v4"),
                     "--out-md", str(tmp_path / "r.md"), "--out-png", str(tmp_path / "r.png")])
    texto = Path(out).read_text(encoding="utf-8")
    assert "V4 frente al control" in texto and "1 de 1 redes cuestan menos" in texto
    assert (tmp_path / "r.png").stat().st_size > 1000


def test_incluye_v2_frente_al_control(tmp_path):
    rng = np.random.default_rng(2)
    ctrl = rng.normal(3, 20, 40)          # la deriva del precio domina; red y control la comparten
    _escribir(tmp_path / "v2", 1000, ctrl - 2 + rng.normal(0, 0.5, 40))
    _escribir(tmp_path / "v4", 1000, ctrl + rng.normal(0, 0.5, 40), ctrl=ctrl)
    fila = comp.comparar(comp.cargar(tmp_path / "v2"), comp.cargar(tmp_path / "v4"))[0]
    assert fila["dif_v2_ctrl"] == pytest.approx(-2.0, abs=0.5) and fila["p_v2_ctrl"] < 0.01
