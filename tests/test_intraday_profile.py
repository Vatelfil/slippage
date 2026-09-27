"""Tests de src/analysis/intraday_profile.py (2.1.3b, Parte A, BF).

Casos conocidos de los estimadores de spread (resultado exacto o con
tolerancia en un modelo de Roll simulado) y consistencia con la 2.1.3.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from src.analysis import intraday_profile as ip

REAL_DIR = ip.DEFAULT_DATA_DIR / "clean_5m_2026-08-23"
CALIB_JSON = ip._REPO_ROOT / "data" / "calibration" / "poisson_params_2026-08-23.json"
requires_real_snapshot = pytest.mark.skipif(
    not (REAL_DIR / "FALABELLA.parquet").exists(),
    reason="snapshot real clean_5m_2026-08-23 no disponible localmente",
)


# --- Casos exactos ------------------------------------------------------------

def test_corwin_schultz_solo_spread_es_exacto():
    """Sin volatilidad, H = ask y L = bid fijos: beta = 2k^2, gamma = k^2 con
    k = ln(H/L), luego alpha = k y S = 2(H-L)/(H+L) (spread relativo)."""
    n = 20
    h, l, c = np.full(n, 100.5), np.full(n, 99.5), np.full(n, 100.0)
    s = ip.corwin_schultz_pairs(h, l, c, h, l)
    assert np.allclose(s, 0.01, rtol=1e-12)
    assert ip.corwin_schultz(h, l, c, h, l) == pytest.approx(0.01, rel=1e-12)


def test_corwin_schultz_negativos_a_cero():
    """Dos velas sin rango propio pero separadas por un salto grande (sin
    ajuste de gap): alpha < 0 y la estimacion del par se fija en 0."""
    h0 = l0 = c0 = np.array([100.0])
    h1 = l1 = np.array([101.0])
    raw = ip.corwin_schultz_pairs(h0, l0, c0, h1, l1, adjust_gap=False, clip_negative=False)
    assert raw[0] < 0
    assert ip.corwin_schultz_pairs(h0, l0, c0, h1, l1, adjust_gap=False)[0] == 0.0


def test_corwin_schultz_ajuste_de_gap():
    """Con el ajuste de la seccion 3.a, un salto puro entre velas (vela t
    completamente sobre el cierre de t-1) no se confunde con spread: se
    desplaza la vela t y el resultado es el del caso sin salto."""
    h0, l0, c0 = np.array([100.5]), np.array([99.5]), np.array([100.0])
    h1, l1 = np.array([102.5]), np.array([101.5])            # L1 > C0: salto de 1.5
    adj = ip.corwin_schultz_pairs(h0, l0, c0, h1, l1)
    same = ip.corwin_schultz_pairs(h0, l0, c0, h1 - 1.5, l1 - 1.5)
    assert adj[0] == pytest.approx(same[0], rel=1e-12)


def test_abdi_ranaldo_mid_constante_es_exacto():
    """Mid constante, H = ask, L = bid y cierre en bid o ask: cada producto
    vale (ln(ask/bid)/2)^2, luego S = ln(ask/bid) en ambas versiones."""
    rng = np.random.default_rng(0)
    n = 50
    h, l = np.full(n, 100.5), np.full(n, 99.5)
    c = np.where(rng.random(n) < 0.5, 100.5, 99.5)
    esperado = np.log(100.5 / 99.5)
    assert ip.abdi_ranaldo(h, l, c, h, l) == pytest.approx(esperado, rel=1e-12)
    assert ip.abdi_ranaldo(h, l, c, h, l, method="two_period") == pytest.approx(esperado, rel=1e-12)


def test_roll_sin_reversion_es_nan_y_pesos_como_repeticion():
    x = np.linspace(-1, 1, 30)
    assert np.isnan(ip.roll_spread(x, x))                     # cov > 0 -> NaN
    rng = np.random.default_rng(1)
    a, b = rng.normal(size=40), rng.normal(size=40)
    w = rng.integers(0, 3, size=40).astype(float)
    rep = np.repeat(np.arange(40), w.astype(int))
    v_w = ip.roll_spread(a, b, w)
    v_r = ip.roll_spread(a[rep], b[rep])
    assert (np.isnan(v_w) and np.isnan(v_r)) or v_w == pytest.approx(v_r, rel=1e-12)


def test_hl_y_mediana_ponderada():
    assert ip.hl_range([101.0, 102.0], [99.0, 98.0]) == pytest.approx((0.02 + 0.04) / 2)
    assert ip.weighted_median(np.array([1.0, 2.0, 100.0]), np.array([1.0, 1.0, 1.0])) == 2.0
    assert ip.weighted_median(np.array([1.0, 2.0, 100.0]), np.array([3.0, 1.0, 1.0])) == 1.0


# --- Modelo de Roll simulado ----------------------------------------------------

def _simular_roll(spread_rel: float, sigma_paso: float, n_barras: int = 4000,
                  pasos: int = 60, seed: int = 7):
    """Precio eficiente log-normal con transacciones al bid o al ask al azar;
    velas OHLC de `pasos` transacciones."""
    rng = np.random.default_rng(seed)
    m = np.cumsum(rng.normal(0, sigma_paso, n_barras * pasos)) + np.log(1000.0)
    side = np.where(rng.random(len(m)) < 0.5, 1.0, -1.0)
    p = np.exp(m) * (1 + side * spread_rel / 2)
    bars = p.reshape(n_barras, pasos)
    return bars.max(axis=1), bars.min(axis=1), bars[:, -1]


def test_estimadores_recuperan_spread_en_modelo_de_roll():
    s = 0.002                                                  # 20 bps
    h, l, c = _simular_roll(s, sigma_paso=0.0001)
    r = np.diff(np.log(c))
    roll = ip.roll_spread(r[1:], r[:-1])
    cs = ip.corwin_schultz(h[:-1], l[:-1], c[:-1], h[1:], l[1:])
    ar = ip.abdi_ranaldo(h[:-1], l[:-1], c[:-1], h[1:], l[1:])
    assert roll == pytest.approx(s, rel=0.25)
    assert cs == pytest.approx(s, rel=0.25)
    assert ar == pytest.approx(s, rel=0.25)
    # HL mezcla spread y volatilidad: sobreestima el spread
    assert ip.hl_range(h, l) > 1.5 * s


def test_sin_spread_cs_y_ar_cercanos_a_cero_hl_no():
    h, l, c = _simular_roll(0.0, sigma_paso=0.0002)
    cs = ip.corwin_schultz(h[:-1], l[:-1], c[:-1], h[1:], l[1:])
    ar = ip.abdi_ranaldo(h[:-1], l[:-1], c[:-1], h[1:], l[1:])
    hl = ip.hl_range(h, l)
    assert cs < 0.25 * hl and ar < 0.25 * hl


# --- Agrupacion y datos -----------------------------------------------------------

def _bars_sinteticas(n_days=5, seed=0):
    rng = np.random.default_rng(seed)
    frames = []
    for d in range(n_days):
        day = pd.Timestamp("2026-06-01") + pd.Timedelta(days=d)
        grid = pd.date_range(f"{day.date()} 09:30", f"{day.date()} 15:55", freq="5min",
                             tz=ip.mp.SANTIAGO_TZ)
        c = 1000 * np.exp(np.cumsum(rng.normal(0, 0.002, len(grid))))
        frames.append(pd.DataFrame({
            "ts": grid, "open": c, "high": c * 1.001, "low": c * 0.999, "close": c,
            "volume": rng.integers(1, 100, len(grid)).astype(float),
            "is_imputed": rng.random(len(grid)) < 0.1,
        }))
    df = pd.concat(frames, ignore_index=True)
    df["day"] = df["ts"].dt.date
    df["minute"] = ip._minutes(df["ts"])
    df["tramo"] = ip.tramo_from_minutes(df["minute"])
    df["bloque"] = ip.bloque_from_minutes(df["minute"])
    df["is_auction"] = df["ts"].dt.strftime("%H:%M") == "15:55"
    return df


def test_bloques_y_tramos():
    assert len(ip.BLOQUES_30M) == 13 and ip.BLOQUES_30M[0] == "09:30" and ip.BLOQUES_30M[-1] == "15:30"
    df = _bars_sinteticas(1)
    assert df.groupby("bloque").size().loc["09:30"] == 6
    assert df.groupby("bloque").size().loc["15:30"] == 6
    assert df.groupby("tramo").size().to_dict() == {"apertura": 24, "cierre": 24, "media_jornada": 30}


def test_pares_no_cruzan_dia_grupo_ni_velas_imputadas():
    df = ip.add_pair_columns(_bars_sinteticas(3), "tramo")
    prev_imp = df.groupby("day")["is_imputed"].shift(1, fill_value=True)
    prev_tr = df.groupby("day")["tramo"].shift(1)
    malos = df["is_imputed"] | prev_imp | (prev_tr != df["tramo"])
    assert df.loc[malos, "cs_s"].isna().all()
    assert df.loc[malos, "ar_prod"].isna().all()
    assert df.loc[~malos, "cs_s"].notna().all()


def test_prepare_excluye_subasta_y_dias():
    bars = _bars_sinteticas(4)
    d0 = bars["day"].iloc[0]
    p = ip.prepare(bars, "tramo", exclude_days=[d0])
    assert not p["is_auction"].any()
    assert d0 not in set(p["day"])


def test_sesion_corta_detectada():
    b1, b2 = _bars_sinteticas(3, seed=1), _bars_sinteticas(3, seed=2)
    corto = b1["day"].iloc[-1]
    for b in (b1, b2):
        b.loc[(b["day"] == corto) & (b["minute"] >= 13 * 60), "is_imputed"] = True
    assert ip.detect_short_sessions({"A": b1, "B": b2}) == [corto]


def test_veredicto_cuenta_tickers():
    def m(a, mj, c):
        base = {k: 1.0 for k in ip.METRICAS}
        return {"apertura": {**base, "cs_bps": a}, "media_jornada": {**base, "cs_bps": mj},
                "cierre": {**base, "cs_bps": c}}
    per = {"X": m(1, 3, 2), "Y": m(3, 2, 1), "Z": m(1, float("nan"), 1)}
    v = ip.verdict(per, ["X", "Y", "Z"], ["X"])
    assert v["spread"]["cs"]["media_jornada_mayor"]["todos"] == {"n_cumple": 1, "n_validos": 2, "tickers": ["X"]}
    assert v["spread"]["cs"]["tramo_con_maximo"]["todos"] == {"apertura": 1, "media_jornada": 1, "cierre": 0}


@requires_real_snapshot
def test_roll_hl_y_vol_iguales_a_calibracion_2_1_3():
    ref = json.loads(CALIB_JSON.read_text(encoding="utf-8"))["params"]["FALABELLA"]
    bars = ip.load_bars("FALABELLA", REAL_DIR)
    m = ip.metrics_by_group(ip.prepare(bars, "tramo"), "tramo", ip.TRAMO_NAMES)
    for t in ip.TRAMO_NAMES:
        assert m[t]["roll_bps"] == pytest.approx(ref[t]["spread_roll_bps"], rel=1e-9)
        assert m[t]["hl_bps"] == pytest.approx(ref[t]["hl_range_bps"], rel=1e-9)
        assert m[t]["vol_bps"] == pytest.approx(ref[t]["obs_return_std"] * 1e4, rel=1e-9)
