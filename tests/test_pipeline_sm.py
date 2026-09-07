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

from src.data.clean_ohlcv import compute_tier, filter_session_hours, fold_closing_auction, process_ticker
from src.data.clean_ohlcv import main as clean_ohlcv_main
from src.features.build_sm_features import (
    build_ticker_features,
    compute_rolling_features,
    compute_sesion,
    compute_volatility_diagnostic,
    compute_volatility_diagnostic_comparison,
)
from src.features.build_sm_features import main as build_sm_features_main

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


# ---------------------------------------------------------------------------
# fold_closing_auction: yfinance a veces timestampea el cierre real a las
# 16:00 en vez de a las 15:55 (ver CLOSING_AUCTION_NOTE). Debe fusionarse
# dentro de la ultima vela de la grilla sin agregar una vela 79.
# ---------------------------------------------------------------------------

def _make_day_rows(day_str: str, times: list[str], opens, highs, lows, closes, volumes) -> pd.DataFrame:
    ts = pd.to_datetime([f"{day_str} {t}" for t in times]).tz_localize(SANTIAGO_TZ)
    return pd.DataFrame({
        "ticker": "TEST",
        "datetime_utc": ts.tz_convert("UTC"),
        "datetime_santiago": ts,
        "open": opens, "high": highs, "low": lows, "close": closes, "volume": volumes,
    })


def test_fold_closing_auction_relabels_lone_late_close():
    day = pd.Timestamp("2026-06-01").date()
    df_day = _make_day_rows(
        "2026-06-01", ["15:45", "16:00"],
        [100.0, 105.0], [101.0, 106.0], [99.0, 104.0], [100.5, 105.5], [1000.0, 500_000.0],
    )

    result = fold_closing_auction(df_day, day).sort_values("datetime_santiago")

    assert len(result) == 2  # no agrega una vela 79, solo reetiqueta la tardia
    last_row = result.iloc[-1]
    assert last_row["datetime_santiago"] == pd.Timestamp("2026-06-01 15:55", tz=SANTIAGO_TZ)
    assert last_row["close"] == 105.5
    assert last_row["volume"] == 500_000.0


def test_fold_closing_auction_merges_real_1555_with_late_1600():
    day = pd.Timestamp("2026-06-01").date()
    df_day = _make_day_rows(
        "2026-06-01", ["15:55", "16:00"],
        [200.0, 210.0], [205.0, 215.0], [195.0, 208.0], [202.0, 212.0], [1000.0, 2000.0],
    )

    result = fold_closing_auction(df_day, day)

    assert len(result) == 1
    row = result.iloc[0]
    assert row["datetime_santiago"] == pd.Timestamp("2026-06-01 15:55", tz=SANTIAGO_TZ)
    assert row["open"] == 200.0    # la mas temprana (15:55)
    assert row["high"] == 215.0    # max de ambas
    assert row["low"] == 195.0     # min de ambas
    assert row["close"] == 212.0   # la mas tardia (16:00) = precio de cierre final
    assert row["volume"] == 3000.0  # suma


# ---------------------------------------------------------------------------
# is_imputed: debe marcar exactamente las velas rellenadas (ffill o bfill de
# borde), nunca las que ya venian con una observacion real.
# ---------------------------------------------------------------------------

def test_is_imputed_flags_only_filled_rows(raw_two_days_with_gaps):
    df_clean, stats = process_ticker("TEST", raw_two_days_with_gaps, edge_policy="bfill")

    # dia 1: dos velas intermedias rellenadas por ffill (12:00, 12:05)
    day1 = df_clean[df_clean["datetime_santiago"].dt.date == pd.Timestamp("2026-06-01").date()]
    imputed_day1 = day1.loc[day1["datetime_santiago"].dt.strftime("%H:%M").isin(["12:00", "12:05"]), "is_imputed"]
    assert imputed_day1.all()
    assert not day1.loc[~day1["datetime_santiago"].dt.strftime("%H:%M").isin(["12:00", "12:05"]), "is_imputed"].any()

    # dia 2: las 2 primeras velas (09:30, 09:35) rellenadas por bfill de borde
    day2 = df_clean[df_clean["datetime_santiago"].dt.date == pd.Timestamp("2026-06-02").date()]
    imputed_day2 = day2.loc[day2["datetime_santiago"].dt.strftime("%H:%M").isin(["09:30", "09:35"]), "is_imputed"]
    assert imputed_day2.all()
    assert not day2.loc[~day2["datetime_santiago"].dt.strftime("%H:%M").isin(["09:30", "09:35"]), "is_imputed"].any()

    # ambos dias completan la grilla (edge_policy="bfill" no descarta ninguno)
    assert stats["n_days_discarded"] == 0
    assert stats["ffill_imputed_count"]["close"] == 2   # solo el hueco de media jornada del dia 1
    assert stats["bfill_edge_imputed_count"]["close"] == 2  # solo el borde inicial del dia 2


# ---------------------------------------------------------------------------
# tier: etiqueta, no filtro
# ---------------------------------------------------------------------------

def test_compute_tier_labels_without_filtering():
    assert compute_tier(92.05) == "A"
    assert compute_tier(60.0) == "A"       # limite inclusive
    assert compute_tier(59.99) == "B"
    assert compute_tier(19.91) == "B"


# ---------------------------------------------------------------------------
# Fixture para las features del vector S_M (tarea 1.2.2): simula el output
# YA LIMPIO de clean_ohlcv.py (con columnas _raw + is_imputed), 2 dias x 78
# velas c/u, con un salto de nivel deliberado entre el cierre del dia 1 y la
# apertura del dia 2 (para detectar si el rolling llegara a cruzar dias) y un
# bloque de 3 velas imputadas dentro del dia 1 (para el diagnostico de
# volatilidad, punto 4 del checkpoint de 1.2.1).
# ---------------------------------------------------------------------------

def _volume_profile_con_salto_de_cierre(n: int) -> np.ndarray:
    volumes = np.full(n, 1000.0)
    volumes[-2:] = 5000.0  # salto de volumen en la subasta de cierre (ultimas 2 barras)
    return volumes


@pytest.fixture
def clean_two_days_full_grid() -> pd.DataFrame:
    day1 = pd.date_range("2026-06-01 09:30", "2026-06-01 15:55", freq="5min", tz=SANTIAGO_TZ)
    day2 = pd.date_range("2026-06-02 09:30", "2026-06-02 15:55", freq="5min", tz=SANTIAGO_TZ)
    all_ts = day1.append(day2)
    n1, n2 = len(day1), len(day2)

    close_raw = np.concatenate([
        100.0 + np.sin(np.linspace(0, 6, n1)),    # dia 1: oscila alrededor de 100
        1000.0 + np.sin(np.linspace(0, 6, n2)),   # dia 2: salto de nivel deliberado a 1000
    ])
    volume_raw = np.concatenate([
        _volume_profile_con_salto_de_cierre(n1),
        _volume_profile_con_salto_de_cierre(n2),
    ])

    is_imputed = np.zeros(n1 + n2, dtype=bool)
    is_imputed[10:13] = True  # 3 velas imputadas consecutivas dentro del dia 1

    return pd.DataFrame({
        "datetime_santiago": all_ts,
        "close_raw": close_raw,
        "volume_raw": volume_raw,
        "is_imputed": is_imputed,
    })


# ---------------------------------------------------------------------------
# Test 2: columnas normalizadas dentro de [0,1] / OBI_agregado dentro de [-1,1]
# ---------------------------------------------------------------------------

def test_normalized_columns_within_bounds(clean_two_days_full_grid):
    df, _ = build_ticker_features("TEST", clean_two_days_full_grid)

    for col in ("tau_t", "volatilidad", "vol_promedio", "sesion"):
        s = df[col].dropna()
        assert ((s >= 0.0) & (s <= 1.0)).all(), col

    assert ((df["OBI_agregado"] >= -1.0) & (df["OBI_agregado"] <= 1.0)).all()


# ---------------------------------------------------------------------------
# Test 3: tau_t monotona creciente dentro de cada dia, se reinicia en cada jornada
# ---------------------------------------------------------------------------

def test_tau_t_monotonic_and_resets_per_day(clean_two_days_full_grid):
    df, _ = build_ticker_features("TEST", clean_two_days_full_grid)

    for _, day_df in df.groupby(df["timestamp"].dt.date):
        assert (day_df["tau_t"].diff().dropna() > 0).all()

    firsts = df.groupby(df["timestamp"].dt.date)["tau_t"].first()
    assert np.allclose(firsts.to_numpy(), 0.0)


# ---------------------------------------------------------------------------
# Test 4: sesion toma exactamente {0.0, 0.5, 1.0} y coincide con los cortes
# de hora exacta acordados (11:00 / 14:00, no 11:30)
# ---------------------------------------------------------------------------

def test_sesion_matches_hour_cutoffs():
    ts = pd.Series(pd.to_datetime([
        "2026-06-01 09:30", "2026-06-01 10:59",
        "2026-06-01 11:00", "2026-06-01 13:59",
        "2026-06-01 14:00", "2026-06-01 15:55",
    ]).tz_localize(SANTIAGO_TZ))

    result = compute_sesion(ts)

    assert list(result) == [0.0, 0.0, 0.5, 0.5, 1.0, 1.0]
    assert set(result.unique()) == {0.0, 0.5, 1.0}


# ---------------------------------------------------------------------------
# Test 5: el rolling de volatilidad NO cruza dias
# ---------------------------------------------------------------------------

def test_rolling_does_not_cross_days(clean_two_days_full_grid):
    df = compute_rolling_features(clean_two_days_full_grid)

    for _, day_df in df.groupby(df["datetime_santiago"].dt.date):
        day_df = day_df.reset_index(drop=True)
        # min_periods=6 -> las primeras 5 velas del dia quedan NaN
        assert day_df["volatilidad_raw"].iloc[:5].isna().all()
        assert day_df["volatilidad_raw"].iloc[5:].notna().all()

        # el primer valor con ventana completa debe coincidir con el calculo
        # manual AISLADO por dia; si el rolling cruzara dias, el salto de
        # nivel deliberado de la fixture lo haria disparar muy por encima
        manual_std = day_df["close_raw"].iloc[:6].std()
        assert day_df["volatilidad_raw"].iloc[5] == pytest.approx(manual_std)


# ---------------------------------------------------------------------------
# Test 6: shape (n,7) y dtype float32, consistente con el Box del schema
# ---------------------------------------------------------------------------

def test_output_shape_and_dtype_matches_schema(clean_two_days_full_grid):
    df, _ = build_ticker_features("TEST", clean_two_days_full_grid)

    sm_cols = ["q_t", "tau_t", "n_slices", "volatilidad", "vol_promedio", "OBI_agregado", "sesion"]
    arr = df[sm_cols].to_numpy(dtype=np.float32)

    assert arr.shape == (len(df), 7)
    assert arr.dtype == np.float32
    # q_t y n_slices son placeholders NaN (los calcula el entorno en runtime);
    # np.float32(np.nan) es representable sin excepcion, por eso el cast no rompe.
    assert np.isnan(arr[:, 0]).all()
    assert np.isnan(arr[:, 2]).all()


# ---------------------------------------------------------------------------
# Bonus: diagnostico de volatilidad (punto 4 del checkpoint de 1.2.1) --
# debe exigir al menos 4/6 velas realmente observadas por ventana.
# ---------------------------------------------------------------------------

def test_volatility_diagnostic_respects_min_observed_threshold(clean_two_days_full_grid):
    df = compute_rolling_features(clean_two_days_full_grid)
    df["volatilidad_raw_min_obs"] = compute_volatility_diagnostic(df)

    day1 = df[df["datetime_santiago"].dt.date == pd.Timestamp("2026-06-01").date()].reset_index(drop=True)

    # ventana [posiciones 6..11]: imputadas={10,11} (2) -> 4 observadas -> pasa el minimo
    assert pd.notna(day1["volatilidad_raw_min_obs"].iloc[11])
    # ventana [posiciones 7..12]: imputadas={10,11,12} (3) -> solo 3 observadas -> NaN
    assert pd.isna(day1["volatilidad_raw_min_obs"].iloc[12])


def test_volatility_diagnostic_comparison_reports_differences(clean_two_days_full_grid):
    df, _ = build_ticker_features("TEST", clean_two_days_full_grid)
    comparison = compute_volatility_diagnostic_comparison(df)

    assert comparison["n_windows_compared"] > 0
    assert comparison["mean_abs_diff"] is not None
    assert comparison["mean_abs_diff"] >= 0.0
    assert comparison["max_abs_diff"] >= comparison["mean_abs_diff"]


# ---------------------------------------------------------------------------
# Bonus: pipeline end-to-end (CLI de ambos scripts) sobre un directorio temporal
# ---------------------------------------------------------------------------

def test_end_to_end_pipeline_tmp_path(tmp_path, raw_two_days_with_gaps):
    raw_dir = tmp_path / "raw" / "ohlcv_5m_2026-06-01"
    raw_dir.mkdir(parents=True)
    raw_two_days_with_gaps.to_parquet(raw_dir / "TEST.parquet", index=False)

    clean_dir = tmp_path / "clean"
    clean_ohlcv_main(input_dir=raw_dir, output_dir=clean_dir, edge_policy="bfill", dry_run=False)

    features_dir = tmp_path / "features"
    build_sm_features_main(input_dir=clean_dir, output_dir=features_dir, dry_run=False, plot_ticker=None)

    assert (features_dir / "_combined.parquet").exists()
    assert (features_dir / "sm_features_report.json").exists()
    assert (features_dir / "scaler_params.json").exists()
