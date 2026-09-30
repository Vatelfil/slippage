"""Prueba de humo de la conexion ABIDES -> EjecutorEnv. Correr DENTRO del entorno
con ABIDES-Gym (Python 3.9), desde la raiz del repo:

    PYTHONPATH=. python src/envs/test_abides_ejecutor.py

Imprime, por cada tramo, un episodio con acciones al azar. Si algo falla, el
traceback dice cual de los puntos de INTEGRACION_ABIDES_PARA_MAURICIO.md
(seccion 'Que hay que verificar') hay que revisar.
"""
import numpy as np

from src.envs.abides_ejecutor_env import EjecutorEnvAbides


def run(tramo: str, q_slice: int = 500, ventana_min: int = 5, seed: int = 0):
    env = EjecutorEnvAbides(executor_id=tramo, q_slice=q_slice, ventana_min=ventana_min, seed=seed)
    obs, info = env.reset()
    assert obs.shape == (27,), obs.shape
    assert env.observation_space.contains(obs), f"obs fuera de rango: {obs}"
    total_reward, steps = 0.0, 0
    rng = np.random.default_rng(seed)
    while True:
        action = env.action_space.sample()
        obs, reward, done, truncated, info = env.step(action)
        assert env.observation_space.contains(obs), f"obs fuera de rango en step {steps}"
        total_reward += reward
        steps += 1
        if done or truncated or steps >= 100:
            break
    print(f"[{tramo}] pasos={steps} reward_total={total_reward:.4f} info_final={info}")
    env.close()


if __name__ == "__main__":
    for tramo in ("apertura", "media_jornada", "cierre"):
        run(tramo)
    print("OK: los 3 tramos corrieron un episodio completo")
