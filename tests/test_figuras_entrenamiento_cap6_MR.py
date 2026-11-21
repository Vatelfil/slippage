"""Pruebas unitarias para la generación de figuras del Capítulo 6 (MR)."""
from pathlib import Path

from scripts import figuras_entrenamiento_cap6_MR as fig6


def test_figuras_cap6_se_generan_sin_errores(tmp_path):
    p1 = fig6.graficar_maestro(tmp_path)
    p2 = fig6.graficar_ejecutor(tmp_path)
    assert p1.exists() and p1.stat().st_size > 0
    assert p2.exists() and p2.stat().st_size > 0
