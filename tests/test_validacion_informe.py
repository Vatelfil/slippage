"""Prueba de punta a punta del analisis local 2.2.5 con archivos sinteticos."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np

from tests.test_validacion_formal import OBJ, TRAMOS, _real, _runs

REPO = Path(__file__).resolve().parents[1]


def _script():
    spec = importlib.util.spec_from_file_location("validar_2_2_5", REPO / "scripts" / "validar_2_2_5.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_pipeline_completo_genera_json_figura_e_informe(tmp_path):
    real = _real()
    base = {"por_tramo": {t: {"retornos_reales_5min": real[t]} for t in TRAMOS}}
    calib = {"objetivos_validacion": {"FALABELLA": {"por_tramo": OBJ}}}
    esc = {"apertura": 0.0034, "media_jornada": 0.0022, "cierre": 0.0020}
    paths = {}
    for nombre, datos in (("base", base), ("calib", calib),
                          ("despues", {"resultados": _runs(esc)}),
                          ("antes", {"resultados": _runs({t: 0.008 for t in TRAMOS})})):
        paths[nombre] = tmp_path / f"{nombre}.json"
        paths[nombre].write_text(json.dumps(datos), encoding="utf-8")

    out_md, out_json, out_png = tmp_path / "i.md", tmp_path / "r.json", tmp_path / "f.png"
    _script().main(["--sim-despues", str(paths["despues"]), "--sim-antes", str(paths["antes"]),
                    "--base-json", str(paths["base"]), "--calibration-json", str(paths["calib"]),
                    "--out-md", str(out_md), "--out-json", str(out_json), "--out-png", str(out_png)])

    md = out_md.read_text(encoding="utf-8")
    for titulo in ("## 1. Veredicto", "## 2. KS", "## 4. Valores por semilla", "## 7. Antes y después",
                   "## 8. Corrección", "## 9. Limitaciones"):
        assert titulo in md
    assert "nan" not in md.lower().replace("mannan", "")
    assert "pendiente de revisión por" in md.lower()
    r = json.loads(out_json.read_text(encoding="utf-8"))
    assert r["metadata"]["semillas"] == 20 and len(r["comparacion"]) == 3
    assert out_png.exists()
