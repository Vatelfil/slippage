# Integración ABIDES-Gym → EjecutorEnv (borrador para Mauricio)

**Estado: escrito, NO probado contra ABIDES** (no se pudo instalar donde se escribió). La lógica pura sí está probada (8 tests con datos falsos en el formato de ABIDES). Está hecho a partir del código fuente real de `SubGymMarketsExecutionEnv_v0`.

## Archivos
| Archivo | Qué es |
|---|---|
| `src/envs/abides_bridge.py` | Lógica pura: vector S_E de 27 dims, traducción de las 240 acciones a órdenes ABIDES, recompensa R_E. Sin imports de ABIDES. |
| `src/envs/abides_ejecutor_env.py` | `ExecutionEnv27` (subclase del entorno de ABIDES) y `EjecutorEnvAbides` (adaptador gymnasium, mismo `observation_space` y `action_space` que `EjecutorEnv`). |
| `src/envs/test_abides_ejecutor.py` | Prueba de humo: un episodio por tramo con acciones al azar. |
| `tests/test_abides_bridge.py` | Tests de la lógica pura (corren sin ABIDES). |

## Cómo usarlo
```bash
# dentro del entorno con ABIDES (Python 3.9)
PYTHONPATH=. python src/envs/test_abides_ejecutor.py
```
En el notebook, en la celda 10, reemplazar `EjecutorEnvPoissonFallback(...)` por `EjecutorEnvAbides(executor_id=i, q_slice=..., ventana_min=...)`. El resto del training loop no cambia.

## Qué se decidió (revisar)
Se eligió la **opción B (extender ABIDES)** para respetar el Título I (27 variables, 240 acciones) en vez de achicar nuestros contratos a los de ABIDES (3 acciones, ~8 variables).
- `MARKET` → cancelar todo + orden de mercado por `fracción × pendiente`.
- `LIMIT_BUY` → cancelar todo + límite a `mejor_bid + nivel × 1 centavo` (nivel 0 pasivo, 7 agresivo).
- `LIMIT_SELL` → esperar (el proyecto solo modela compra).
- Cada tramo arranca en su hora real (`first_interval`: 00:00:30, 02:00:00, 04:30:00 tras la apertura) y `timestep_duration="30s"`.
- `R_E = Σ (P_mid − P_ejec)·q / tamaño_orden`, con β=0 (pendiente de calibración).
- La penalización de ABIDES por orden incompleta se anula: en nuestro diseño es el λ de R_M, del Maestro.

## Qué hay que verificar (no pude)
1. Que `from abides_gym.envs.markets_execution_environment_v0 import SubGymMarketsExecutionEnv_v0` funcione.
2. La **forma de `raw_state`**: si `bids/asks` llegan como buffer de snapshots o el último. El código acepta ambas, pero confirmarlo imprimiendo `raw_state`.
3. Que el libro traiga **≥5 niveles**. Si trae menos, se rellena con 0. Si trae menos de 5, subir `market_data_buffer_length` / niveles suscritos.
4. Que `step()` del entorno base **no valide** la acción contra `Discrete(3)` (le pasamos un arreglo de 3 números).
5. Que exista `env.seed()` (se llama con `hasattr`). Si no, fijar la semilla en la config de fondo.
6. Que `self.first_interval` y `self.execution_window` sean números en nanosegundos (así los usa el código base).
7. Que `inter_wakeup_executed_orders` traiga objetos con `.fill_price` y `.quantity`.
8. **Conflicto de versiones:** `requirements.txt` fija `numpy==1.26.4` y `pandas==2.2.1`, pero ABIDES pide `numpy==1.22.0` y `pandas==1.2.4`. En el `Dockerfile`, `pip install -r requirements.txt` va al final y puede romper ABIDES. Probablemente hay que instalar PyTorch/gymnasium con restricciones o separar los requirements.

## Pendiente / limitaciones
- `tasa_ordenes` (S_E) queda en **0.0** (placeholder): ABIDES no la entrega directa. Hay que derivarla del número de actualizaciones del libro entre despertares.
- Las constantes de normalización (`BridgeConfig`: ±5 % de precio, volumen máx. 2000, etc.) son heurísticas; ajustar al calibrar `rmsc04` con el IPSA (tarea 2.2.4, Benjamín).
- Los precios de ABIDES están en centavos y `rmsc04` simula una acción de ~$1000, no una del IPSA. Todo se normaliza contra el precio de entrada, así que funciona, pero no es "FALABELLA" hasta calibrar.
- Los episodios de `cierre` serán lentos: ABIDES simula 4 h 30 min de mercado antes de que el agente entre.
- **El Maestro no está resuelto.** Cada episodio de ABIDES es una simulación independiente; las 13 decisiones de una jornada no caben en un solo episodio. Lo razonable es ventanas del Ejecutor independientes, con el Maestro agregando resultados. Falta decidirlo.
