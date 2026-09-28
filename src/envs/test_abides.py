"""Prueba de concepto (PoC) de ABIDES-Gym.

CORREGIDO 27 sept 2026 (PS), segunda correccion. Historial:
- Version original (Mauricio): probaba "markets-execution-v0" y, como respaldo,
  "rmc-v0". "markets-execution-v0" SI existe; "rmc-v0" no.
- Mi correccion del 23 sept la cambio a "markets-daily_investor-v0" (el unico
  ejemplo del README) por error: pense que "markets-execution-v0" no existia.
  Verificado ahora contra abides-gym/abides_gym/__init__.py del repo oficial
  (jpmorganchase/abides-jpmc-public): se registran exactamente dos entornos,
  "markets-daily_investor-v0" y "markets-execution-v0". El de ejecucion de
  ordenes (el que corresponde a este proyecto) es "markets-execution-v0".

Ese entorno tiene 3 acciones discretas (0=MKT, 1=LMT near touch, 2=Hold, con
tamano fijo `order_fixed_size`) y ~8 features de observacion (holdings_pct,
time_pct, diff_pct, imbalance_all, imbalance_5, price_impact, spread,
direction_feature) + historial de retornos. NO coincide con nuestros contratos
S_E (27 dims) / A_E (240 acciones): ver el documento de mapeo.

IMPORTANTE: este script NO se ha ejecutado (ABIDES-Gym no esta instalado en el
entorno donde se escribio). Mauricio debe correrlo dentro del contenedor.
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
