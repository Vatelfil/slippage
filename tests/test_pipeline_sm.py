"""
test_pipeline_sm.py
--------------------
Sprint 2 (tareas 1.2.1 / 1.2.2) - Validacion del pipeline de limpieza OHLCV y
del calculo del vector de estado S_M del Agente Maestro.

Todos los tests usan datos sinteticos pequenos (fixtures fabricadas en este
mismo archivo), NUNCA los 30 tickers reales de data/raw|processed/, para que
la suite corra rapido y sea determinista sin depender de haber corrido antes
los scripts del pipeline.

Se corre dentro del contenedor con:
    docker compose run --rm slippage pytest tests/ -v

pytest.ini agrega la raiz del repo a sys.path (pythonpath = .), por lo que
los imports de src.* funcionan sin __init__.py ni conftest.py.
"""

from __future__ import annotations

from datetime import time
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pytest

from src.data.clean_ohlcv import filter_session_hours

SANTIAGO_TZ = ZoneInfo("America/Santiago")


# ---------------------------------------------------------------------------
# Fixtures compartidas
# ---------------------------------------------------------------------------

@pytest.fixture
def santiago_tz() -> ZoneInfo:
    return SANTIAGO_TZ


@pytest.fixture
def raw_two_days_with_gaps() -> pd.DataFrame:
    """1 ticker sintetico ('TEST'), 2 dias habiles consecutivos (2026-06-01 y
    2026-06-02), con:
      - Filas fuera de horario (08:00 y 17:00 del dia 1) para el test de
        filtro de sesion.
      - Un hueco a media jornada el dia 1 (12:00 y 12:05 ausentes) para
        probar el forward fill.
      - Un hueco en las primeras 2 velas del dia 2 (09:30 y 09:35 ausentes)
        para probar el backfill acotado del borde inicial.

    Columnas identicas al output de download_ohlcv.py: ticker, datetime_utc,
    datetime_santiago, open, high, low, close, volume.
    """
    day1_grid = pd.date_range("2026-06-01 09:30", "2026-06-01 15:55",
                               freq="5min", tz=SANTIAGO_TZ)
    day2_grid = pd.date_range("2026-06-02 09:30", "2026-06-02 15:55",
                               freq="5min", tz=SANTIAGO_TZ)

    # dia 1: se quitan las velas de 12:00 y 12:05 (hueco intermedio)
    day1_ts = [t for t in day1_grid if t.strftime("%H:%M") not in ("12:00", "12:05")]
    # dia 2: se quitan las primeras 2 velas (hueco de borde inicial)
    day2_ts = list(day2_grid[2:])

    out_of_hours = pd.to_datetime([
        "2026-06-01 08:00", "2026-06-01 17:00",
    ]).tz_localize(SANTIAGO_TZ)

    all_ts = pd.DatetimeIndex(day1_ts + day2_ts).append(out_of_hours).sort_values()

    n = len(all_ts)
    prices = 100.0 + np.arange(n)
    df = pd.DataFrame({
        "ticker": "TEST",
        "datetime_utc": all_ts.tz_convert("UTC"),
        "datetime_santiago": all_ts,
        "open": prices,
        "high": prices + 0.5,
        "low": prices - 0.5,
        "close": prices,
        "volume": 1000.0 + np.arange(n) * 10,
    })
    return df


# ---------------------------------------------------------------------------
# Test 1: ninguna fila fuera de 09:30-15:55 hora Santiago
# ---------------------------------------------------------------------------

def test_filter_session_hours_excludes_outside_window(raw_two_days_with_gaps):
    result = filter_session_hours(raw_two_days_with_gaps)

    times = result["datetime_santiago"].dt.time
    assert times.between(time(9, 30), time(15, 55)).all()
    # la fixture incluye 2 filas fuera de horario (08:00 y 17:00) que deben caer
    assert len(result) == len(raw_two_days_with_gaps) - 2
