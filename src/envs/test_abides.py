"""Prueba de concepto (PoC) de ABIDES-Gym.

*** VERIFICADA CONTRA ABIDES-GYM REAL el 29 sept 2026 *** (en Colab, con
Python 3.9 via condacolab, gym==0.18.0 -- ver DIAGNOSTICO_COLAB_MAURICIO_29SEP.md
para la instalacion completa). Este script corrio con exito.

Historial de correcciones (para que quede el porque, no solo el que):
- Version original (Mauricio, config-entorno-abides-y-modelos): probaba
  "markets-execution-v0" y, como respaldo, "rmc-v0". "markets-execution-v0"
  SI existe; "rmc-v0" no.
- 23 sept (PS): cambiada por error a "markets-daily_investor-v0", creyendo
  que "markets-execution-v0" no existia. Fue un error mio.
- 28 sept (Mauricio, fix/arreglos-dependencias): cambiada a `gymnasium` +
  `shimmy` para compatibilizar con ABIDES-Gym. Esto NO funciona: ABIDES-Gym
  importa `gym` (la libreria vieja) directamente en su propio codigo fuente
  (abides_gym/__init__.py, markets_execution_environment_v0.py) -- shimmy
  envuelve un entorno ya creado con gym viejo para usarlo desde fuera con la
  API de gymnasium, no hace que el paquete abides_gym deje de necesitar gym
  por dentro. Ver DIAGNOSTICO_COLAB_MAURICIO_29SEP.md para el detalle.
- 29 sept (PS): confirmado en abides_gym/__init__.py del repo oficial
  (jpmorganchase/abides-jpmc-public) que se registran exactamente dos
  entornos: "markets-daily_investor-v0" y "markets-execution-v0". El de
  ejecucion de ordenes (el que corresponde a este proyecto) es
  "markets-execution-v0" -- la version ORIGINAL de Mauricio tenia el nombre
  correcto. Probado con exito real en Colab (ver arriba).
"""
import gym
import abides_gym  # noqa: F401  (el import registra los entornos "markets-*-v0")


def test_abides_orderbook():
    print("Iniciando prueba de concepto de ABIDES-Gym...")

    env_id = "markets-execution-v0"
    print(f"Creando entorno '{env_id}' (background_config='rmsc04', direction='BUY')...")
    env = gym.make(env_id, background_config="rmsc04", direction="BUY")

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
