import gym
import abides_gym

def test_abides_orderbook():
    print("Iniciando prueba de concepto de ABIDES-Gym...")
    
    # Crear un entorno básico de ABIDES (markets-v0 o smc-v0 dependiendo de la versión)
    # markets-execution-v0 es común para problemas de ejecución de órdenes
    try:
        env = gym.make("markets-execution-v0")
        print("Entorno 'markets-execution-v0' creado correctamente.")
    except Exception as e:
        print(f"Error al crear el entorno markets-execution-v0: {e}")
        print("Intentando crear 'rmc-v0' (entorno base)...")
        env = gym.make("rmc-v0")
    
    # Resetear el entorno para iniciar el día de simulación
    obs = env.reset()
    print("\nSimulación iniciada. Estado inicial del Order Book (Observación):")
    
    # La observación típica incluye LOB features (precios de bid/ask, volúmenes)
    print(obs)
    
    # Tomar una acción aleatoria o dummy (esperar) para simular un paso en el tiempo
    # En muchos entornos ABIDES-Gym discretos, 0 puede ser 'do nothing' o similar
    action = env.action_space.sample() 
    print(f"\nEjecutando acción de prueba: {action}")
    
    # Step en el entorno
    obs, reward, done, info = env.step(action)
    
    print("\nEstado del Order Book después del primer Step:")
    print(f"Observación: {obs}")
    print(f"Recompensa: {reward}")
    print(f"Terminado (Done): {done}")
    print(f"Info adicional: {info}")
    
    print("\nPrueba de concepto completada con éxito. ABIDES-Gym es funcional.")

if __name__ == '__main__':
    test_abides_orderbook()
