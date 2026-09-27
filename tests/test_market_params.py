"""Tests de src/config/market_params.py (Parte C de la 2.1.3b, BF).

Verifica que la configuracion compartida reproduce exactamente los valores
que la 2.1.3 tenia en duro y que calibration_poisson.py, leyendo desde ella,
entrega los mismos resultados que data/calibration/poisson_params_2026-08-23.json.
"""
from __future__ import annotations

import json

import numpy as np
import pytest

from src.config import market_params as mp
from src.envs import calibration_poisson as cp

REAL_SNAPSHOT = "2026-08-23"
REAL_DIR = cp.DEFAULT_DATA_DIR / f"clean_5m_{REAL_SNAPSHOT}"
REF_JSON = cp.DEFAULT_CALIBRATION_DIR / f"poisson_params_{REAL_SNAPSHOT}.json"
requires_real_snapshot = pytest.mark.skipif(
    not (REAL_DIR / "FALABELLA.parquet").exists() or not REF_JSON.exists(),
    reason="snapshot real clean_5m_2026-08-23 no disponible localmente (parquet no versionados)",
)

# Campos de la 2.1.3 que deben quedar identicos (los agregados en la 2.1.3b,
# como objetivos de validacion o D_crit, no se comparan aqui).
CAMPOS_TRAMO = ("n_obs", "n_bars_total", "imputed_share", "n_returns", "avg_order_size",
                "buy_volume", "sell_volume", "share_tick_rule", "n_bars_winsorized", "hl_ar1",
                "spread_roll_bps", "hl_range_bps", "obs_return_std", "obs_return_mean")
CAMPOS_DIRECTO = ("lambda_plus", "lambda_minus", "theta", "ks_stat", "p_value")


def test_valores_iguales_a_los_de_la_2_1_3():
    assert mp.TRAMOS_EJECUTOR == (("apertura", "09:30", "11:30"),
                                  ("media_jornada", "11:30", "14:00"),
                                  ("cierre", "14:00", "16:00"))
    assert mp.AVG_ORDER_NOTIONAL_CLP == 1_000_000
    assert mp.INCLUDE_CLOSING_AUCTION is False
    assert mp.CLOSING_AUCTION_BAR == "15:55"
    assert mp.STEPS_PER_BAR == 10
    assert mp.ORDER_SIZE_POLICY["notional_clp"] == mp.AVG_ORDER_NOTIONAL_CLP


def test_sesion_sm_igual_a_build_sm_features():
    from src.features import build_sm_features as sm
    assert mp.SESION_SM_CUTOFFS == sm.SESSION_CUTOFFS_HOUR


def test_calibration_poisson_lee_desde_config():
    assert cp.TRAMOS is mp.TRAMOS_EJECUTOR
    assert cp.DEFAULT_ORDER_NOTIONAL_CLP == mp.AVG_ORDER_NOTIONAL_CLP
    assert cp.CLOSING_AUCTION_BAR == mp.CLOSING_AUCTION_BAR
    assert cp.DEFAULT_EXCLUDE_CLOSING_AUCTION is (not mp.INCLUDE_CLOSING_AUCTION)


def test_avg_order_size_politica():
    assert mp.avg_order_size_from_price(6000.0) == 167.0          # FALABELLA (2.1.3)
    assert mp.avg_order_size_from_price(5e9) == 1.0               # minimo 1 accion
    assert mp.avg_order_size_from_price(100.0, notional_clp=250_000) == 2500.0


def _assert_close(a, b, where):
    if a is None or b is None:
        assert a is None and b is None, where
    elif isinstance(a, bool) or isinstance(b, bool):
        assert a == b, where
    else:
        assert np.isclose(a, b, rtol=1e-9, atol=0.0), f"{where}: {a} != {b}"


@requires_real_snapshot
def test_resultados_iguales_al_json_2026_08_23():
    """Los 30 tickers, estimacion directa (sin MLE): mismos lambda, theta,
    KS, proxies de spread, tamano de orden y tope de winsorizacion."""
    ref = json.loads(REF_JSON.read_text(encoding="utf-8"))
    tickers = sorted(ref["params"])
    assert len(tickers) == 30
    for t in tickers:
        res = cp.calibrate_ticker(t, snapshot=REAL_SNAPSHOT, run_mle=False)
        res = cp._json_safe({k: v for k, v in res.items() if k != "returns"})
        info = ref["tickers_info"][t]
        _assert_close(res["avg_order_size"], info["avg_order_size"], f"{t} avg_order_size")
        _assert_close(res["volume_cap"], info["volume_cap"], f"{t} volume_cap")
        for tramo in cp.TRAMO_NAMES:
            got, exp = res["tramos"][tramo], ref["params"][t][tramo]
            for k in CAMPOS_TRAMO:
                _assert_close(got[k], exp[k], f"{t}/{tramo}/{k}")
            for k in CAMPOS_DIRECTO:
                _assert_close(got["directo"][k], exp["directo"][k], f"{t}/{tramo}/directo/{k}")
        for k in ("lambda_total_menor_en_media", "spread_roll_mayor_en_media",
                  "spread_hl_mayor_en_media", "lambda_total_menor_en_media_sin_winsorizar"):
            assert res["stylized_facts"][k] == ref["stylized_facts"][t][k], f"{t} {k}"


@requires_real_snapshot
def test_falabella_con_mle_igual_al_json():
    ref = json.loads(REF_JSON.read_text(encoding="utf-8"))["params"]["FALABELLA"]
    res = cp._json_safe(cp.calibrate_ticker("FALABELLA", snapshot=REAL_SNAPSHOT)["tramos"])
    for tramo in cp.TRAMO_NAMES:
        assert res[tramo]["method"] == ref[tramo]["method"]
        for k in ("lambda_plus", "lambda_minus", "theta", "ks_stat", "p_value", "sim_drift_sd"):
            _assert_close(res[tramo][k], ref[tramo][k], f"FALABELLA/{tramo}/{k}")
        for k in ("lambda_plus", "lambda_minus", "theta", "ks_stat", "adoptado"):
            _assert_close(res[tramo]["mle_proxy"][k], ref[tramo]["mle_proxy"][k],
                          f"FALABELLA/{tramo}/mle_proxy/{k}")
