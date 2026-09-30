# Integración ABIDES-Gym → EjecutorEnv

**Estado (29 sept, actualizado): ✅ VERIFICADO contra ABIDES-Gym real**, corriendo en Colab (Python 3.9 vía `condacolab`, ver `DIAGNOSTICO_COLAB_MAURICIO_29SEP.md` para cómo se instaló). Un episodio completo corrió sin errores en los 3 tramos:

```
[apertura]      pasos=10 reward_total=-3.6250 holdings=494/500
[media_jornada] pasos=10 reward_total=-4.8100 holdings=491/500
[cierre]        pasos=6  reward_total=0.8530  holdings=500/500 (orden completa)
```

Se encontraron y corrigieron 2 bugs reales al probarlo (no eran solo teoría):
1. Faltaban los decoradores `raw_state_pre_process`/`raw_state_to_state_pre_process` (heredados de `SubGymMarketsExecutionEnv_v0` pero no re-declarados, así que no se aplicaban a los métodos sobreescritos). Sin ellos, `raw_state` llegaba en su forma más cruda y no como el dict `{'parsed_mkt_data':..., 'internal_data':...}` esperado.
2. El `observation_space` tenía shape `(27,)` en vez de `(27,1)` (así es como ABIDES reshapea el estado internamente), lo que hacía fallar el `assert` interno de ABIDES aunque los valores estuvieran bien.

Rama con todo esto: `fix/desbloqueo-abides-poc-v3` (main sigue protegido, y las ramas anteriores de esta misma serie quedaron bloqueadas a mitad de camino — revisa cuál es la vigente antes de trabajar sobre esto).

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

## Qué ya se verificó (dejó de ser hipótesis)
1. ✅ El import de `SubGymMarketsExecutionEnv_v0` funciona.
2. ✅ La forma de `raw_state` (buffer de snapshots) — confirmada leyendo el código fuente real en vivo (`inspect.getsource`) y corrigiendo los decoradores.
3. ✅ `step()` acepta el arreglo de 3 números sin problema (la validación de `Discrete(3)` del padre no se ejecuta porque sobreescribimos `_map_action_space_to_ABIDES_SIMULATOR_SPACE`, no `step()`).
4. ✅ `inter_wakeup_executed_orders` trae objetos con `.fill_price`/`.quantity` — el cálculo de `R_E` dio números con sentido (negativo = costo, como se esperaba).
5. ✅ **Conflicto de versiones resuelto en Colab**: instalar todo en un solo `pip install` (no en comandos separados) con `ray[tune]` en vez de `ray[rllib]` evita que se sobreescriban `numpy`/`gym`. Ver `DIAGNOSTICO_COLAB_MAURICIO_29SEP.md` para las versiones exactas que sí conviven.

## Qué sigue sin verificar
1. Que el libro traiga **≥5 niveles reales** (si `rmsc04` trae menos, se rellena con 0 — no se confirmó cuántos niveles trae en la práctica).
2. Que exista `env.seed()` de verdad (se llama con `hasattr`, nunca se confirmó si existe en esta versión).
3. Si los valores de `tasa_ordenes` (placeholder 0.0) y las constantes de normalización de `BridgeConfig` dan resultados razonables con muchos episodios, no solo con 1.
4. El Maestro sigue sin resolver (ver limitaciones abajo).

## Pendiente / limitaciones
- `tasa_ordenes` (S_E) queda en **0.0** (placeholder): ABIDES no la entrega directa. Hay que derivarla del número de actualizaciones del libro entre despertares.
- Las constantes de normalización (`BridgeConfig`: ±5 % de precio, volumen máx. 2000, etc.) son heurísticas; ajustar al calibrar `rmsc04` con el IPSA (tarea 2.2.4, Benjamín).
- Los precios de ABIDES están en centavos y `rmsc04` simula una acción de ~$1000, no una del IPSA. Todo se normaliza contra el precio de entrada, así que funciona, pero no es "FALABELLA" hasta calibrar.
- Los episodios de `cierre` serán lentos: ABIDES simula 4 h 30 min de mercado antes de que el agente entre.
- **El Maestro no está resuelto.** Cada episodio de ABIDES es una simulación independiente; las 13 decisiones de una jornada no caben en un solo episodio. Lo razonable es ventanas del Ejecutor independientes, con el Maestro agregando resultados. Falta decidirlo.
