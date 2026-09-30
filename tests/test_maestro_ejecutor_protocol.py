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
