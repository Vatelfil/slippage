"""Tests del simulador de LOB Poisson y su wrapper de entorno.

*** REEMPLAZO TEMPORAL *** — ver src/envs/poisson_lob_simulator.py y
REEMPLAZO_TEMPORAL_POISSON.md. Estos tests deben eliminarse junto con el
resto de los archivos de reemplazo cuando Mauricio integre ABIDES-Gym.
"""
from __future__ import annotations

import numpy as np
import pytest
import torch

from src.envs.fallback_poisson_env import EjecutorEnvPoissonFallback
from src.envs.poisson_lob_simulator import PoissonLOBSimulator, load_calibrated_params
from src.models.actor_critic import ExecutorActorCritic


def test_load_calibrated_params_real_falabella():
    """Los parametros deben venir del JSON real de Benjamin, no inventados."""
    p = load_calibrated_params("FALABELLA", "apertura")
    assert p["lambda_plus"] > 0
    assert p["lambda_minus"] > 0
    assert p["theta"] > 0
    assert p["avg_order_size"] > 0
    assert "calibration_path" in p


def test_load_calibrated_params_ticker_desconocido():
    with pytest.raises(KeyError):
        load_calibrated_params("TICKER_QUE_NO_EXISTE", "apertura")


@pytest.mark.parametrize("tramo", ["apertura", "media_jornada", "cierre"])
def test_reset_produce_book_valido(tramo):
    sim = PoissonLOBSimulator("FALABELLA", tramo, seed=0)
    sim.reset(p_referencia=5800.0)

    assert np.all(sim.bid_prices < sim.ask_prices[0])  # spread positivo
    assert np.all(np.diff(sim.bid_prices) < 0)  # bids decrecientes desde el mejor
    assert np.all(np.diff(sim.ask_prices) > 0)  # asks crecientes desde el mejor
    assert np.all(sim.bid_volumes > 0)
    assert np.all(sim.ask_volumes > 0)


def test_execute_market_buy_matematica_exacta():
    """Verifica la aritmetica de ejecucion contra un libro conocido (mismo
    ejemplo numerico de Contexto_Agente_Programacion.md, seccion 2:
    2000@5800 + 5500@5810 + 500@5820 = 46.465.000 / 8000 = 5808.125)."""
    sim = PoissonLOBSimulator("FALABELLA", "apertura", seed=0)
    sim.reset(p_referencia=5800.0)
    sim.ask_prices = np.array([5800.0, 5810.0, 5820.0, 5830.0, 5840.0])
    sim.ask_volumes = np.array([2000.0, 5500.0, 500.0, 1000.0, 1000.0])

    filled, avg_price = sim.execute_market_buy(8000)

    assert filled == 8000
    assert avg_price == pytest.approx(5808.125, abs=1e-9)
    # el libro debe quedar sin liquidez en los 3 primeros niveles
    assert sim.ask_volumes[0] == 0
    assert sim.ask_volumes[1] == 0
    assert sim.ask_volumes[2] == 0
    assert sim.ask_volumes[3] == 1000.0  # nivel 4 no se toco


def test_execute_market_buy_liquidez_insuficiente():
    """Si se pide mas de lo que hay en los 5 niveles, ejecuta lo que hay
    (no inventa liquidez ni lanza error)."""
    sim = PoissonLOBSimulator("FALABELLA", "apertura", seed=0)
    sim.reset(p_referencia=5800.0)
    sim.ask_volumes = np.array([10.0, 10.0, 10.0, 10.0, 10.0])
    total_liquidity = sim.ask_volumes.sum()

    filled, avg_price = sim.execute_market_buy(10_000)

    assert filled == total_liquidity
    assert filled < 10_000


def test_env_observation_space_shape_y_contrato():
    """El wrapper debe respetar EXACTAMENTE el observation_space/action_space
    de EjecutorEnv (SE_schema.json, 27 dims)."""
    env = EjecutorEnvPoissonFallback(executor_id="apertura", max_steps=10, q_slice=1000, seed=0)
    assert env.observation_space.shape == (27,)
    obs, info = env.reset()
    assert obs.shape == (27,)
    assert obs.dtype == np.float32
    assert env.observation_space.contains(obs)


@pytest.mark.parametrize("executor_id", ["apertura", "media_jornada", "cierre"])
def test_rollout_completo_sin_crash_y_rewards_no_triviales(executor_id):
    """Corre un episodio completo con una red real (no entrenada) y verifica:
    sin crashes, observaciones siempre validas, rewards finitos, y que NO
    todas las recompensas son 0.0 (a diferencia del EjecutorEnv stub)."""
    torch.manual_seed(0)
    net = ExecutorActorCritic(obs_dim=27, action_dim=240)
    env = EjecutorEnvPoissonFallback(executor_id=executor_id, max_steps=15,
                                      q_slice=2000, p_referencia=5800.0, seed=1)

    obs, _ = env.reset()
    rewards = []
    for _ in range(15):
        obs_t = torch.as_tensor(obs, dtype=torch.float32).unsqueeze(0)
        action, _, _, _ = net.get_action_and_value(obs_t)
        action_env = env._action_space_wrapper.decode_flat(action.item())
        obs, reward, done, truncated, info = env.step(action_env)
        assert env.observation_space.contains(obs)
        assert np.isfinite(reward)
        rewards.append(reward)
        if done:
            break

    assert not all(r == 0.0 for r in rewards), "las recompensas no deberian ser todas 0.0 (eso seria el bug del stub original)"
    assert info["q_pendiente"] <= 2000


def test_q_pendiente_nunca_negativo():
    """q_pendiente no debe volverse negativo aunque se ejecute de mas por
    redondeo (contrato interno de EjecutorEnvPoissonFallback)."""
    env = EjecutorEnvPoissonFallback(executor_id="cierre", max_steps=50, q_slice=100, seed=2)
    obs, _ = env.reset()
    for _ in range(50):
        # Accion fija: MARKET, volumen maximo, nivel 0 -- para forzar ejecucion agresiva.
        action_env = np.array([2, 9, 0])  # order_type=MARKET(idx2), volume_bucket=9(max), price_level=0
        obs, reward, done, truncated, info = env.step(action_env)
        assert info["q_pendiente"] >= 0
        if done:
            break
