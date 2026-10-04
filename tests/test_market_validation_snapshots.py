"""find_latest_clean_combined debe saltarse carpetas de snapshot sin parquet
(en el repo se versionan los reportes pero no los datos)."""
from __future__ import annotations

import pandas as pd
import pytest

from src.analysis.market_validation import find_latest_clean_combined


def test_salta_carpeta_mas_nueva_sin_parquet(tmp_path):
    (tmp_path / "clean_5m_2026-09-23").mkdir()
    pd.DataFrame({"a": [1]}).to_parquet(tmp_path / "clean_5m_2026-09-23" / "_combined.parquet")
    (tmp_path / "clean_5m_2026-09-27").mkdir()  # solo reportes, sin parquet

    assert find_latest_clean_combined(tmp_path).parent.name == "clean_5m_2026-09-23"


def test_error_claro_si_ninguna_tiene_parquet(tmp_path):
    (tmp_path / "clean_5m_2026-09-27").mkdir()
    with pytest.raises(FileNotFoundError, match="ninguna carpeta|Ninguna carpeta"):
        find_latest_clean_combined(tmp_path)
