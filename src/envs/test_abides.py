import gymnasium as gym
# Si abides_gym requiere gym antiguo, puede ser necesario usar un wrapper o importar abides_gym 
# independientemente. Por ahora, asumimos que abides_gym se ha adaptado o se está adaptando.
try:
    import abides_gym
except ImportError:
    print("Advertencia: abides_gym no está instalado.")

def test_abides_orderbook():
    print("Iniciando prueba de concepto de ABIDES-Gym con Gymnasium...")
    
    # Crear un entorno básico de ABIDES (markets-v0 o smc-v0 dependiendo de la versión)
    # markets-execution-v0 es común para problemas de ejecución de órdenes
    try:
        env = gym.make("markets-execution-v0")
        print("Entorno 'markets-execution-v0' creado correctamente.")
    except Exception as e:
        print(f"Error al crear el entorno markets-execution-v0: {e}")
        print("Intentando crear 'rmc-v0' (entorno base)...")
        try:
            env = gym.make("rmc-v0")
        except Exception as e2:
            print(f"Error al crear rmc-v0: {e2}. Asegúrate de que los entornos de abides_gym estén registrados en Gymnasium.")
            return
    
    # Resetear el entorno para iniciar el día de simulación (Gymnasium devuelve obs, info)
    obs, info = env.reset()
    print("\nSimulación iniciada. Estado inicial del Order Book (Observación):")
    
    # La observación típica incluye LOB features (precios de bid/ask, volúmenes)
    print(obs)
    
    # Tomar una acción aleatoria o dummy (esperar) para simular un paso en el tiempo
    # En muchos entornos discretos, 0 puede ser 'do nothing' o similar
    action = env.action_space.sample() 
    print(f"\nEjecutando acción de prueba: {action}")
    
    # Step en el entorno (Gymnasium devuelve 5 valores)
    obs, reward, terminated, truncated, step_info = env.step(action)
    done = terminated or truncated
    
    print("\nEstado del Order Book después del primer Step:")
    print(f"Observación: {obs}")
    print(f"Recompensa: {reward}")
    print(f"Terminated: {terminated}")
    print(f"Truncated: {truncated}")
    print(f"Info adicional: {step_info}")
    
    print("\nPrueba de concepto completada con éxito. ABIDES-Gym es funcional con Gymnasium.")

if __name__ == '__main__':
    test_abides_orderbook()
