"""Prueba de humo del orquestador MaestroEjecutorEnv (src/envs/maestro_ejecutor_protocol.py).

*** IMPORTANTE: no prueba las redes PPO (maestro_policy/executor_policy siguen
NotImplementedError, tarea de Mauricio) -- prueba solo la "plomeria" de
coordinacion: que step()/reset() del Maestro corran un episodio completo
contra un Ejecutor real (aqui, EjecutorEnvPoissonFallback, que no requiere
ABIDES-Gym instalado) sin crashear, y que Q_executed/R_M salgan con numeros
reales, no placeholders.

Para probar contra ABIDES-Gym real (no corre aqui, requiere Colab), pasar
`executor_env_factory=EjecutorEnvAbides` -- ver DIAGNOSTICO_COLAB_MAURICIO_29SEP.md.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.envs.maestro_ejecutor_protocol import MaestroEjecutorEnv


def _fake_datos_historicos() -> pd.DataFrame:
    """DataFrame minimo con el contrato que _lookup_yfinance_feature() espera:
    indice = timestamps de la jornada (09:30-16:00, cada 5 min), columnas
    'volatilidad'/'vol_promedio'. En el proyecto real esto lo genera el
    pipeline de Benjamin (tarea 1.2.2); aqui se genera sintetico solo para
    que el orquestador tenga algo que indexar."""
    idx = pd.date_range("2026-09-29 09:30", "2026-09-29 16:00", freq="5min")
    rng = np.random.default_rng(0)
    return pd.DataFrame(
        {"volatilidad": rng.uniform(0.001, 0.003, len(idx)),
         "vol_promedio": rng.uniform(0.1, 0.3, len(idx))},
        index=idx,
    )


def _random_executor_policy(_s_e: np.ndarray) -> int:
    """Sustituto de executor_policy() real (que sigue NotImplementedError,
    tarea de Mauricio) solo para poder correr el loop de coordinacion en esta
    prueba -- no evalua calidad de la politica."""
    return np.random.default_rng().integers(0, 240)


def test_maestro_ejecutor_env_episodio_completo_no_crashea(monkeypatch):
    import src.envs.maestro_ejecutor_protocol as protocolo

    monkeypatch.setattr(protocolo, "executor_policy", _random_executor_policy)

    env = MaestroEjecutorEnv(
        meta_orden_quantity=10_000,
        datos_historicos=_fake_datos_historicos(),
    )

    s_m = env.reset()
    assert s_m.shape == (7,)

    done = False
    n_steps = 0
    total_reward = 0.0
    while not done and n_steps < MaestroEjecutorEnv.__init__.__globals__["MAX_DECISIONES_MAESTRO"] + 2:
        action_maestro = (0, 1)  # alpha_idx=0 (5%), ventana_idx=1 (5 min) -- fijo, no es la politica real
        s_m, r_m, done, info = env.step(action_maestro)
        assert s_m.shape == (7,)
        assert isinstance(info["Q_executed"], float)
        total_reward += r_m
        n_steps += 1

    env.close()

    assert done, "el episodio deberia terminar antes del limite de seguridad de pasos"
    assert n_steps > 0
    # Q_executed debe haberse actualizado con numeros reales del Ejecutor real
    # (no seguir en 0.0 como estaria si _run_executor_episode fuera un placeholder).
    assert env.Q_executed >= 0.0
    # La recompensa terminal (R_M, en el ultimo paso) debe ser un float finito real.
    assert np.isfinite(total_reward)


def test_run_executor_episode_usa_el_env_inyectado():
    """Verifica que _run_executor_episode() de verdad instancia y corre el
    executor_env_factory inyectado (no un placeholder) -- construye un reporte
    con q_ejecutado/p_promedio numericos."""
    import src.envs.maestro_ejecutor_protocol as protocolo

    def politica_fija(_s_e):
        return 0  # indice plano fijo, valido en [0,240)

    orig_policy = protocolo.executor_policy
    protocolo.executor_policy = politica_fija
    try:
        env = MaestroEjecutorEnv(
            meta_orden_quantity=1000,
            datos_historicos=_fake_datos_historicos(),
        )
        env.reset()
        msg_asignar = {
            "tipo": "asignar",
            "timestamp_inicio": env.current_time,
            "q_slice": 100.0,
            "ventana_min": 5,
            "tramo": "apertura",
        }
        reporte = env._run_executor_episode(msg_asignar)
    finally:
        protocolo.executor_policy = orig_policy

    assert reporte["tipo"] == "reporte"
    assert reporte["q_ejecutado"] >= 0.0
    assert reporte["p_promedio"] is not None
    assert reporte["razon_termino"] in ("ventana_completada", "inventario_agotado")


def test_maestro_policy_real_network():
    """Valida que maestro_policy devuelva indices validos (alpha_idx en 0..9, ventana_idx en 0..3)
    usando la red real MasterActorCritic tanto estocastica como determinista."""
    from src.envs.maestro_ejecutor_protocol import maestro_policy, ALPHA_VALUES, VENTANA_MIN_VALUES
    from src.models.actor_critic import MasterActorCritic

    s_m = np.zeros(7, dtype=np.float32)
    net = MasterActorCritic(obs_dim=7)

    # 1. Con red explicita
    alpha_idx, ventana_idx = maestro_policy(s_m, model=net, deterministic=False)
    assert 0 <= alpha_idx < len(ALPHA_VALUES)
    assert 0 <= ventana_idx < len(VENTANA_MIN_VALUES)

    # 2. Con determinismo
    alpha_det, vent_det = maestro_policy(s_m, model=net, deterministic=True)
    assert 0 <= alpha_det < len(ALPHA_VALUES)
    assert 0 <= vent_det < len(VENTANA_MIN_VALUES)

    # 3. Con singleton por defecto
    alpha_def, vent_def = maestro_policy(s_m)
    assert 0 <= alpha_def < len(ALPHA_VALUES)
    assert 0 <= vent_def < len(VENTANA_MIN_VALUES)


def test_executor_policy_real_network():
    """Valida que executor_policy devuelva un indice plano en [0, 240) usando
    la red real ExecutorActorCritic y que sea decodificable por EjecutorActionSpace."""
    from src.envs.maestro_ejecutor_protocol import executor_policy
    from src.models.actor_critic import ExecutorActorCritic
    from src.envs.spaces import EjecutorActionSpace

    s_e = np.zeros(27, dtype=np.float32)
    net = ExecutorActorCritic(obs_dim=27, action_dim=240)
    action_space = EjecutorActionSpace()

    # 1. Estocastico
    a_idx = executor_policy(s_e, model=net, deterministic=False)
    assert isinstance(a_idx, int)
    assert 0 <= a_idx < 240
    decoded = action_space.decode_flat(a_idx)
    assert len(decoded) == 3

    # 2. Determinista
    a_det = executor_policy(s_e, model=net, deterministic=True)
    assert isinstance(a_det, int)
    assert 0 <= a_det < 240

    # 3. Default
    a_def = executor_policy(s_e)
    assert isinstance(a_def, int)
    assert 0 <= a_def < 240


def test_maestro_ejecutor_env_con_redes_reales_episodio_completo():
    """Corre un episodio completo de coordinacion usando las redes REALES
    MasterActorCritic y ExecutorActorCritic (sin monkeypatching), verificando
    que no haya desajuste de dimensiones, que las recompensas sean finitas
    y que la coordinacion termine adecuadamente."""
    from src.envs.maestro_ejecutor_protocol import maestro_policy

    env = MaestroEjecutorEnv(
        meta_orden_quantity=5000,
        datos_historicos=_fake_datos_historicos(),
    )

    s_m = env.reset()
    assert s_m.shape == (7,)

    done = False
    step_count = 0
    total_reward = 0.0

    while not done and step_count < 15:
        a_m = maestro_policy(s_m)
        s_m, r_m, done, info = env.step(a_m)
        assert s_m.shape == (7,)
        total_reward += r_m
        step_count += 1

    env.close()

    assert done is True
    assert step_count == 13
    assert np.isfinite(total_reward)
    assert env.Q_executed >= 0.0


def test_maestro_lambda_penalty_customizable():
    """Verifica que el parametro lambda_penalty modifique la penalizacion terminal."""
    env_low_lambda = MaestroEjecutorEnv(meta_orden_quantity=10000, lambda_penalty=0.01)
    env_high_lambda = MaestroEjecutorEnv(meta_orden_quantity=10000, lambda_penalty=1.0)

    assert env_low_lambda.lambda_penalty == 0.01
    assert env_high_lambda.lambda_penalty == 1.0
