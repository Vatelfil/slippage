"""Tests del bloque A de la 2.2.4 (src/envs/calibrate_rmsc04_ipsa.py). No
dependen de ABIDES. Los que leen los .parquet del snapshot (no versionados)
se saltan si no estan en disco."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from src.envs import calibrate_rmsc04_ipsa as cal
from src.envs.calibrate_rmsc04_ipsa import (
    CAMPOS_PENDIENTES_2_2_4,
    NS_POR_VELA_5MIN,
    build_rmsc04_ipsa_config,
    fund_vol_from_sigma,
    ou_variance,
    to_abides_kwargs,
    variance_ratio,
)

# Firma de rmsc04.build_config. Fuente: jpmorganchase/abides-jpmc-public,
# abides-markets/abides_markets/configs/rmsc04.py, rama main, commit f9cbe51
# (2023-12-13). Copiada el 2026-10-03.
RMSC04_BUILD_CONFIG_PARAMS = (
    "seed", "date", "end_time", "stdout_log_level", "ticker", "starting_cash", "log_orders",
    "book_logging", "book_log_depth", "stream_history_length", "exchange_log_orders",
    "num_noise_agents", "num_value_agents", "r_bar", "kappa", "lambda_a",
    "kappa_oracle", "sigma_s", "fund_vol",
    "megashock_lambda_a", "megashock_mean", "megashock_var",
    "mm_window_size", "mm_pov", "mm_num_ticks", "mm_wake_up_freq", "mm_min_order_size",
    "mm_skew_beta", "mm_price_skew", "mm_level_spacing", "mm_spread_alpha",
    "mm_backstop_quantity", "mm_cancel_limit_delay", "num_momentum_agents",
)

R_BAR_CLP = 5969.75  # mediana de close_raw de FALABELLA, snapshot 2026-08-23

_HAY_PARQUET = (cal.DEFAULT_PROCESSED_DIR / f"clean_5m_{cal.DEFAULT_SNAPSHOT}" / "FALABELLA.parquet").exists()
requiere_parquet = pytest.mark.skipif(not _HAY_PARQUET, reason="snapshot 2026-08-23 no esta en disco")


def _cfg(tramo="apertura", **kw):
    return build_rmsc04_ipsa_config(ticker="FALABELLA", tramo=tramo, r_bar_clp=R_BAR_CLP, **kw)


# --- plantilla original (PS), adaptada -------------------------------------

def test_build_rmsc04_ipsa_config_campos_cableados_son_numericos():
    cfg = _cfg()
    assert cfg["ticker"] == "FALABELLA"
    assert cfg["r_bar"] > 0
    assert cfg["fund_vol"] > 0
    assert cfg["starting_cash"] > 0


def test_build_rmsc04_ipsa_config_no_inventa_los_campos_pendientes():
    cfg = _cfg("cierre")
    for campo in CAMPOS_PENDIENTES_2_2_4:
        assert campo not in cfg
    assert cfg["_campos_pendientes_2_2_4"] == list(CAMPOS_PENDIENTES_2_2_4)


def test_build_rmsc04_ipsa_config_varia_por_tramo():
    a, c = _cfg("apertura"), _cfg("cierre")
    assert a["r_bar"] == c["r_bar"]
    assert a["fund_vol"] != c["fund_vol"]


def test_build_rmsc04_ipsa_config_tramo_invalido():
    with pytest.raises(ValueError):
        build_rmsc04_ipsa_config(ticker="FALABELLA", tramo="no_existe", r_bar_clp=R_BAR_CLP)


@requiere_parquet
def test_default_usa_snapshot_2026_08_23():
    cfg = build_rmsc04_ipsa_config(ticker="FALABELLA", tramo="apertura")
    assert cfg["_metadata"]["snapshot"] == "2026-08-23"
    assert cfg["_metadata"]["r_bar_clp_mediano"] == pytest.approx(R_BAR_CLP)


# --- unidades de fund_vol (H5) ---------------------------------------------

def test_fund_vol_es_sigma_r_bar_sobre_raiz_de_ns_por_vela():
    sigma, r_bar = 0.003395, 596_975
    fv = fund_vol_from_sigma(sigma, r_bar, kappa_oracle=0.0)
    assert fv == pytest.approx(sigma * r_bar / math.sqrt(300e9), rel=1e-12)
    # el kappa por defecto de rmsc04 cambia fund_vol en ~2,5e-5 relativo
    assert fund_vol_from_sigma(sigma, r_bar) == pytest.approx(fv, rel=1e-4)


def test_varianza_ou_en_5min_calza_con_sigma_r_bar():
    """Simula el oraculo de ABIDES (misma formula de
    SparseMeanRevertingOracle.compute_fundamental_at_timestamp, con Delta t en
    ns) y verifica Var(OU, 5 min) ~ (sigma_5min * r_bar)^2 con kappa -> 0."""
    sigma, r_bar, kappa = 0.003395, 596_975.0, 1.67e-16
    fv = fund_vol_from_sigma(sigma, r_bar, kappa)
    assert ou_variance(fv, kappa, NS_POR_VELA_5MIN) == pytest.approx((sigma * r_bar) ** 2, rel=1e-9)

    rng = np.random.default_rng(0)
    pasos, d = 30, NS_POR_VELA_5MIN / 30  # 30 consultas de 10 s dentro de la vela
    v = np.full(20_000, r_bar)
    for _ in range(pasos):
        v = rng.normal(loc=r_bar + (v - r_bar) * math.exp(-kappa * d),
                       scale=math.sqrt(fv ** 2 / (2 * kappa) * (1 - math.exp(-2 * kappa * d))))
    assert v.std() == pytest.approx(sigma * r_bar, rel=0.03)
    # la heuristica de la plantilla original quedaba sqrt(300e9) veces mas grande
    assert (sigma * r_bar) / fv == pytest.approx(math.sqrt(300e9), rel=1e-4)


def test_fund_vol_compensa_un_kappa_grande():
    sigma, r_bar, kappa = 0.002, 6000.0, 2e-12  # vida media ~ 6 min
    fv = fund_vol_from_sigma(sigma, r_bar, kappa)
    assert fv > fund_vol_from_sigma(sigma, r_bar, 0.0)
    assert ou_variance(fv, kappa, NS_POR_VELA_5MIN) == pytest.approx((sigma * r_bar) ** 2)


# --- unidad de cuenta (H6) -------------------------------------------------

def test_unidad_cuenta_es_consistente_en_r_bar_cash_y_fund_vol():
    cent, dec, clp = (_cfg(unidad_cuenta=u) for u in ("centavos", "decimos", "clp"))
    assert cent["r_bar"] == 596_975 and dec["r_bar"] == 59_698 and clp["r_bar"] == 5_970
    assert cent["starting_cash"] == 100 * clp["starting_cash"] == 10_000_000
    # el desvio relativo del fundamental no depende de la unidad
    for c in (cent, dec, clp):
        assert c["fund_vol"] / c["r_bar"] == pytest.approx(cent["fund_vol"] / cent["r_bar"], rel=1e-9)
    assert cent["_metadata"]["tick_efectivo_bps"] == pytest.approx(1e4 / 596_975)
    assert dec["_metadata"]["tick_efectivo_bps"] == pytest.approx(0.1675, abs=1e-4)
    assert clp["_metadata"]["tick_efectivo_bps"] == pytest.approx(1.675, abs=1e-3)
    assert isinstance(cent["r_bar"], int) and isinstance(cent["starting_cash"], int)
    assert _cfg()["_metadata"]["unidad_cuenta"] == "decimos"


def test_unidad_cuenta_invalida():
    with pytest.raises(ValueError):
        _cfg(unidad_cuenta="uf")


# --- to_abides_kwargs ------------------------------------------------------

def test_to_abides_kwargs_solo_tiene_llaves_de_la_firma_real():
    cfg = _cfg(kappa_oracle=1e-13, extra={"mm_pov": 0.05, "num_noise_agents": 500})
    kw = to_abides_kwargs(cfg)
    assert set(kw) <= set(RMSC04_BUILD_CONFIG_PARAMS)
    assert not any(k.startswith("_") for k in kw)
    # ABIDES-Gym fija el simbolo del agente en "ABM": el ticker no se pasa
    assert "ticker" not in kw and "seed" not in kw
    assert kw["mm_pov"] == 0.05 and kw["kappa_oracle"] == 1e-13
    assert {"r_bar", "fund_vol", "starting_cash", "end_time", "date"} <= set(kw)


def test_campos_pendientes_estan_en_la_firma_y_se_descuentan_los_fijados():
    assert set(CAMPOS_PENDIENTES_2_2_4) <= set(RMSC04_BUILD_CONFIG_PARAMS)
    cfg = _cfg(extra={"mm_pov": 0.05})
    assert "mm_pov" not in cfg["_campos_pendientes_2_2_4"]
    assert "kappa_oracle" not in CAMPOS_PENDIENTES_2_2_4


# --- A4: razon de varianzas ------------------------------------------------

def test_variance_ratio_paseo_aleatorio_no_rechaza():
    rng = np.random.default_rng(1)
    r = rng.normal(0, 0.002, size=6000)
    for q in (2, 6, 12):
        t = variance_ratio(r, q)
        assert t["vr"] == pytest.approx(1.0, abs=0.08)
        assert abs(t["z_robusto"]) < 2.5


def test_variance_ratio_ma1_y_ou_dan_la_vr_teorica():
    rng = np.random.default_rng(2)
    n = 40_000
    # rebote bid-ask: r_t = e_t + s_t - s_{t-1}  -> rho1 = -s2 / (e2 + 2 s2)
    e, s = rng.normal(0, 1.0, n), rng.normal(0, 1.0, n + 1)
    r_ma1 = e + s[1:] - s[:-1]
    rho1 = cal.autocorr_lag1(r_ma1)
    assert rho1 == pytest.approx(-1 / 3, abs=0.02)
    for q in (2, 6, 12):
        assert variance_ratio(r_ma1, q)["vr"] == pytest.approx(cal.vr_teorica_ma1(-1 / 3, q), abs=0.04)
    # OU en niveles con phi = 0,5 -> rho1 de los retornos = -(1 - phi) / 2 = -0,25
    x = np.zeros(n)
    for i in range(1, n):
        x[i] = 0.5 * x[i - 1] + rng.normal()
    r_ou = np.diff(x)
    assert cal.autocorr_lag1(r_ou) == pytest.approx(-0.25, abs=0.02)
    assert variance_ratio(r_ou, 12)["vr"] == pytest.approx(cal.vr_teorica_ou(-0.25, 12), abs=0.04)
    assert variance_ratio(r_ou, 12)["z_robusto"] < -10

    d_ma1, d_ou = cal.decide_kappa_oracle(r_ma1), cal.decide_kappa_oracle(r_ou)
    assert d_ma1["reversion_significativa"] and d_ou["reversion_significativa"]
    assert d_ma1["patron_mas_cercano"] == "rebote_bid_ask_ma1"
    assert d_ou["patron_mas_cercano"] == "reversion_ou"
    # solo el patron OU cambia kappa; el rebote bid-ask mantiene el default
    assert d_ma1["kappa_oracle_adoptado"] == cal.KAPPA_ORACLE_RMSC04
    assert d_ou["kappa_oracle_adoptado"] == d_ou["kappa_oracle_regla"]
    assert d_ou["phi_nivel"] == pytest.approx(0.5, abs=0.04)
    assert d_ou["kappa_oracle_regla"] == pytest.approx(-math.log(0.5) / NS_POR_VELA_5MIN, rel=0.12)


def test_variance_ratio_por_segmentos_no_cruza_cortes():
    rng = np.random.default_rng(3)
    segs = [rng.normal(0, 1, 20) for _ in range(300)]
    t = variance_ratio(segs, 6)
    assert t["n"] == 6000 and abs(t["z_robusto"]) < 2.5
    # una sola serie y la misma serie como unico segmento dan lo mismo
    r = np.concatenate(segs)
    assert variance_ratio(r, 6)["vr"] == pytest.approx(variance_ratio([r], 6)["vr"])
    assert math.isnan(variance_ratio([np.array([0.1, 0.2])], 6)["vr"])


def test_decide_kappa_paseo_aleatorio_mantiene_default():
    r = np.random.default_rng(4).normal(0, 0.002, size=3000)
    d = cal.decide_kappa_oracle(r)
    assert not d["reversion_significativa"]
    assert d["kappa_oracle_regla"] == d["kappa_oracle_adoptado"] == cal.KAPPA_ORACLE_RMSC04


# --- A5: curtosis ----------------------------------------------------------

def test_return_kurtosis_normal_y_colas_pesadas():
    rng = np.random.default_rng(5)
    assert cal.return_kurtosis(rng.normal(size=50_000))["exceso_curtosis"] == pytest.approx(0.0, abs=0.1)
    assert cal.return_kurtosis(rng.laplace(size=50_000))["exceso_curtosis"] == pytest.approx(3.0, abs=0.4)
    assert math.isnan(cal.return_kurtosis(np.zeros(10))["exceso_curtosis"])


# --- segmentos de retornos reales ------------------------------------------

def test_contiguous_return_segments_corta_en_huecos_y_excluye_subasta():
    ts = pd.to_datetime(["2026-08-03 09:35", "2026-08-03 09:40", "2026-08-03 09:50",
                         "2026-08-03 15:50", "2026-08-03 15:55", "2026-08-04 09:35"])
    df = pd.DataFrame({
        "ts": ts, "day": ts.date,
        "tramo": ["apertura", "apertura", "apertura", "cierre", "cierre", "apertura"],
        "ret": [0.01, 0.02, 0.03, 0.04, 0.05, 0.06],
        "is_auction": [False, False, False, False, True, False],
    })
    segs = cal.contiguous_return_segments(df)
    assert [list(s) for s in segs["apertura"]] == [[0.01, 0.02], [0.03], [0.06]]
    assert [list(s) for s in segs["cierre"]] == [[0.04]]
    assert segs["media_jornada"] == []


@requiere_parquet
def test_retornos_reales_calzan_con_n_returns_de_la_2_1_3():
    segs = cal.real_returns_by_tramo("FALABELLA", "2026-08-23")
    n = {t: sum(len(s) for s in v) for t, v in segs.items()}
    assert n == {"apertura": 1111, "media_jornada": 1690, "cierre": 1252}
    sd = np.concatenate(segs["apertura"]).std()
    assert sd == pytest.approx(0.003395219386417957, rel=1e-6)


@requiere_parquet
def test_falabella_real_vr_calza_con_rebote_bid_ask_y_mantiene_kappa():
    ev = cal.evidencia_a4_a5(cal.real_returns_by_tramo("FALABELLA", "2026-08-23"))
    for tramo, e in ev.items():
        vr = e["variance_ratio"]
        assert vr["reversion_significativa"], tramo
        assert vr["patron_mas_cercano"] == "rebote_bid_ask_ma1", tramo
        assert vr["kappa_oracle_adoptado"] == cal.KAPPA_ORACLE_RMSC04
        assert e["curtosis_real"]["exceso_curtosis"] > 3.0


def test_load_abides_kwargs_lee_el_json_base_versionado():
    path = cal.DEFAULT_OUT_DIR / "rmsc04_base_FALABELLA_2026-08-23.json"
    kw = cal.load_abides_kwargs(path)
    assert set(kw) == {"apertura", "media_jornada", "cierre"}
    for tramo, k in kw.items():
        assert set(k) <= set(RMSC04_BUILD_CONFIG_PARAMS) and "ticker" not in k
        assert k["r_bar"] == 59_698  # decimos de CLP
    assert kw["apertura"]["fund_vol"] > kw["media_jornada"]["fund_vol"] > kw["cierre"]["fund_vol"]


def test_load_abides_kwargs_rechaza_json_sin_config(tmp_path):
    bad = tmp_path / "x.json"
    bad.write_text('{"por_tramo": {"apertura": {}}}', encoding="utf-8")
    with pytest.raises(ValueError):
        cal.load_abides_kwargs(bad)
