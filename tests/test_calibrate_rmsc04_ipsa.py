"""Prueba de la plantilla de calibracion rmsc04/IPSA (tarea 2.2.4, base para
Benjamin -- ver src/envs/calibrate_rmsc04_ipsa.py). No depende de ABIDES-Gym
(no importa abides_markets), solo de datos ya locales."""
from __future__ import annotations

from src.envs.calibrate_rmsc04_ipsa import CAMPOS_PENDIENTES_2_2_4, build_rmsc04_ipsa_config


def test_build_rmsc04_ipsa_config_campos_cableados_son_numericos():
    cfg = build_rmsc04_ipsa_config(ticker="FALABELLA", tramo="apertura")

    assert cfg["ticker"] == "FALABELLA"
    assert cfg["r_bar"] > 0
    assert cfg["fund_vol"] > 0
    assert cfg["starting_cash"] > 0


def test_build_rmsc04_ipsa_config_no_inventa_los_campos_pendientes():
    cfg = build_rmsc04_ipsa_config(ticker="FALABELLA", tramo="cierre")

    for campo in CAMPOS_PENDIENTES_2_2_4:
        assert campo not in cfg, (
            f"{campo!r} no deberia estar en el dict devuelto -- "
            "dejar que rmsc04.build_config() use su propio default "
            "hasta que la tarea 2.2.4 lo calibre de verdad."
        )
    assert cfg["_campos_pendientes_2_2_4"] == list(CAMPOS_PENDIENTES_2_2_4)


def test_build_rmsc04_ipsa_config_varia_por_tramo():
    cfg_apertura = build_rmsc04_ipsa_config(ticker="FALABELLA", tramo="apertura")
    cfg_cierre = build_rmsc04_ipsa_config(ticker="FALABELLA", tramo="cierre")

    # r_bar no depende del tramo (mismo ticker, mismo periodo); fund_vol si,
    # porque obs_return_std viene de la calibracion Poisson por tramo.
    assert cfg_apertura["r_bar"] == cfg_cierre["r_bar"]
    assert cfg_apertura["fund_vol"] != cfg_cierre["fund_vol"]


def test_build_rmsc04_ipsa_config_tramo_invalido():
    import pytest

    with pytest.raises(ValueError):
        build_rmsc04_ipsa_config(ticker="FALABELLA", tramo="no_existe")
