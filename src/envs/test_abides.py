"""Prueba de concepto (PoC) de ABIDES-Gym.

Corregido 23 sept 2026 (PS): la version anterior adivinaba nombres de entorno
inexistentes ("markets-execution-v0", "rmc-v0") envueltos en un try/except que
nunca se confirmo que pasara con exito. Verificado contra el README real de
https://github.com/jpmorganchase/abides-jpmc-public: el entorno de ejemplo
registrado es "markets-daily_investor-v0", que requiere el kwarg
`background_config="rmsc04"` (la configuracion RMSC04 citada en el Titulo I,
seccion 4.3.3.a: 1 Exchange Agent, 2 Market Makers, 102 Value Agents,
12 Momentum Agents, 1000 Noise Agents).

IMPORTANTE: este script NO se pudo ejecutar en el entorno donde se corrigio
(sin Docker/sin ABIDES-Gym instalado localmente). El nombre de entorno y el
kwarg estan verificados contra la documentacion oficial, pero Mauricio debe
correr este script dentro del contenedor (ver Dockerfile) y confirmar que
realmente pasa. Si "markets-daily_investor-v0" no es el entorno mas adecuado
para el problema de ejecucion de ordenes de este proyecto (podria existir un
"markets-execution-v0" real en una version distinta del repo), validarlo
contra `gym.envs.registry` dentro del contenedor:
    import gym, abides_gym
    print([k for k in gym.envs.registry.env_specs.keys() if 'markets' in k])
"""
import gym
import abides_gym  # noqa: F401  (el import registra los entornos "markets-*-v0")


def test_abides_orderbook():
    print("Iniciando prueba de concepto de ABIDES-Gym...")

    env_id = "markets-daily_investor-v0"
    print(f"Creando entorno '{env_id}' (background_config='rmsc04')...")
    env = gym.make(env_id, background_config="rmsc04")

    # gym==0.18.0 (version pineada por el repo oficial de ABIDES-Gym) usa la
    # API vieja de 4 valores: reset() -> obs, step() -> (obs, reward, done, info).
    obs = env.reset()
    print("\nSimulacion iniciada. Estado inicial (observacion):")
    print(obs)

    action = env.action_space.sample()
    print(f"\nEjecutando accion de prueba: {action}")

    obs, reward, done, info = env.step(action)

    print("\nEstado despues del primer step:")
    print(f"Observacion: {obs}")
    print(f"Recompensa: {reward}")
    print(f"Terminado (done): {done}")
    print(f"Info adicional: {info}")

    print("\nPrueba de concepto completada con exito. ABIDES-Gym es funcional.")
    return obs, reward, done, info


if __name__ == "__main__":
    test_abides_orderbook()
