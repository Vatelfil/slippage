"""Tests de la logica pura de src/envs/abides_bridge.py (no requiere ABIDES).
Usan datos falsos con el MISMO formato que raw_state de ABIDES-Gym."""
from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from src.envs import abides_bridge as br
from src.envs.spaces import EjecutorSpace, ORDER_TYPES

BIDS = [[9990, 300], [9989, 200], [9988, 100], [9987, 50], [9986, 10], [9985, 5]]  # 6 niveles
ASKS = [[10010, 250], [10011, 150], [10012, 90]]                                   # solo 3 niveles


def test_obs_dim_y_rango_contra_schema():
    obs = br.build_observation(BIDS, ASKS, 10000, entry_price=10000, parent_size=1000,
                               remaining=800, time_pct=0.3)
    space = EjecutorSpace(warn=False).space
    assert obs.shape == (27,) and obs.dtype == np.float32
    assert space.contains(obs)


def test_obs_libro_incompleto_y_vacio_no_revienta():
    space = EjecutorSpace(warn=False).space
    for b, a in [([], ASKS), (BIDS, []), ([], [])]:
        obs = br.build_observation(b, a, 10000, 10000, 1000, 1000, 0.0)
        assert space.contains(obs)


def test_obs_valores_conocidos():
    obs = br.build_observation(BIDS, ASKS, 10000, 10000, 1000, 500, 0.5)
    assert obs[1] == pytest.approx(0.5)           # q_pendiente = 500/1000
    assert obs[2] == pytest.approx(0.5)           # tau_slice
    assert obs[3] > obs[4] > obs[5]               # bid_precios decrecen desde el mejor
    assert obs[13] < obs[14]                      # ask_precios crecen
    tot_b, tot_a = 300 + 200 + 100 + 50 + 10, 250 + 150 + 90
    assert obs[24] == pytest.approx((tot_b - tot_a) / (tot_b + tot_a), abs=1e-6)  # OBI top-5


def test_last_snapshot_acepta_buffer_y_snapshot():
    assert br.last_snapshot(BIDS) == BIDS
    assert br.last_snapshot([[[1, 1]], BIDS]) == BIDS   # buffer: toma el ultimo
    assert br.last_snapshot([]) == []
    assert br.last_scalar([1, 2, 3]) == 3 and br.last_scalar(7) == 7


def test_map_action_market_limit_y_esperar():
    mkt = br.map_action_to_abides_orders([2, 4, 0], remaining=1000, best_bid=9990, best_ask=10010)
    assert mkt[0] == {"type": "CCL_ALL"}
    assert mkt[1] == {"type": "MKT", "direction": "BUY", "size": 500}  # frac 0.5

    lmt = br.map_action_to_abides_orders([0, 9, 3], remaining=200, best_bid=9990, best_ask=10010)
    assert lmt[1]["type"] == "LMT" and lmt[1]["size"] == 200 and lmt[1]["limit_price"] == 9993

    assert br.map_action_to_abides_orders([1, 5, 2], 1000, 9990, 10010) == []  # LIMIT_SELL = esperar


def test_map_action_tamano_entero_y_acotado():
    for bucket in range(10):
        for remaining in (1, 7, 33, 1000):
            o = br.map_action_to_abides_orders([2, bucket, 0], remaining, 9990, 10010)
            size = o[1]["size"]
            assert isinstance(size, int) and 1 <= size <= remaining
    assert br.map_action_to_abides_orders([2, 3, 0], remaining=0, best_bid=1, best_ask=2) == []


def test_indices_de_orden_coinciden_con_spaces():
    assert ORDER_TYPES[br.ORDER_MARKET] == "MARKET"
    assert ORDER_TYPES[br.ORDER_LIMIT_BUY] == "LIMIT_BUY"
    assert ORDER_TYPES[br.ORDER_LIMIT_SELL] == "LIMIT_SELL"


def test_step_reward_signo_y_escala():
    orders = [SimpleNamespace(fill_price=10005, quantity=100),   # bajo el mid -> ganancia
              SimpleNamespace(fill_price=10015, quantity=50)]    # sobre el mid -> perdida
    r = br.step_reward(orders, mid=10010, parent_size=1000)
    assert r == pytest.approx((5 * 100 + (-5) * 50) / 1000)
    assert br.step_reward([], 10010, 1000) == 0.0
    # beta > 0 penaliza (queda 0.0 por defecto: pendiente de calibracion)
    assert br.step_reward(orders, 10010, 1000, beta=1.0, sigma2=2.0) < r
