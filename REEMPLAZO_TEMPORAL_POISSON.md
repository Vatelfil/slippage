# ⚠️ Reemplazo Temporal: Simulador Poisson en vez de ABIDES-Gym

**Fecha:** 27 septiembre 2026
**Autor:** Paolo Sepúlveda (PS)
**Motivo:** Mauricio no ha podido confirmar si ABIDES-Gym instala/funciona (ver `PENDIENTE_MAURICIO.md`), y el equipo necesitaba avanzar con el training mientras tanto — el Título I (sección 4.3.3.c) ya contemplaba el modelo de Poisson como alternativa liviana exactamente para este escenario.

**Esto NO es la entrega final del proyecto.** Es un puente para no bloquear el training PPO con `reward=0.0` indefinidamente, usando los parámetros Poisson **reales** que Benjamín calibró (tarea 2.1.3, `docs/calibracion_poisson_2.1.3_BF.md`).

---

## Qué se agregó (y cómo eliminarlo por completo)

| Archivo | Qué hace | Acción cuando ABIDES esté listo |
|---|---|---|
| `src/envs/poisson_lob_simulator.py` | Simulador de LOB sintético (5 niveles bid/ask), gobernado por los parámetros Poisson reales (λ⁺, λ⁻, θ) de Benjamín | **Eliminar** |
| `src/envs/fallback_poisson_env.py` | `EjecutorEnvPoissonFallback`, subclase de `EjecutorEnv` que usa el simulador de arriba en vez de observaciones aleatorias | **Eliminar** |
| `tests/test_poisson_lob_fallback.py` | Tests de ambos archivos anteriores | **Eliminar** |
| `notebooks/Training_PPO_Sprint4_PS.ipynb`, celda 10 | Bandera `USE_POISSON_FALLBACK = True` que activa el reemplazo | **Poner en `False`**, o borrar ese bloque `if/else` y dejar solo la rama `else` (que ya usa `EjecutorEnv` real) |

**No se tocó ningún archivo de Mauricio ni de Benjamín** — `EjecutorEnv`, `MaestroEnv`, `calibration_poisson.py` quedan exactamente como estaban. Este reemplazo vive en archivos nuevos y separados, precisamente para poder borrarlo entero sin dejar rastros ni conflictos cuando ya no haga falta.

## Qué SÍ soluciona

- El notebook de training ya no da `reward=0.0` para los 3 Ejecutores — ahora ejecuta contra un libro de órdenes sintético cuya dinámica viene de datos reales del IPSA.
- Verificado matemáticamente contra el ejemplo exacto de `Contexto_Agente_Programacion.md` (2000@5800+5500@5810+500@5820 → 5808,125, exacto).
- Probado con 12 tests (`pytest tests/test_poisson_lob_fallback.py`) y con la red real de Mauricio (`ExecutorActorCritic.get_action_and_value`) — corre sin crashes en los 3 tramos horarios.
- Reproduce el patrón cualitativo real: ejecutar es más costoso en apertura que en cierre (spread más ancho en apertura, según el propio hallazgo de Benjamín).

## Qué NO soluciona (limitaciones explícitas)

- **No es ABIDES-Gym.** No modela agentes heterogéneos (market makers, value agents, noise agents), ni el protocolo ITCH/OUCH, ni colas de órdenes individuales — es deliberadamente más simple, tal como el Título I describe esta alternativa.
- El `MaestroEnv` **sigue siendo un stub** (no se construyó un reemplazo equivalente para el Maestro) — su recompensa sigue en `reward=0.0`. Solo se resolvió el lado de los Ejecutores, que es donde vive la mayor parte de la lógica de ejecución/slippage.
- El espaciado entre niveles del libro y la distribución de volumen por nivel son heurísticas razonables, no estimadas de datos reales de Nivel 2 (que no existen para el IPSA).
- `q_slice` (tamaño de la orden por episodio) es un valor de ejemplo fijo (`config['q_slice_fallback']`, default 2000), no viene todavía de una coordinación real con el Maestro — eso requiere integrar `maestro_ejecutor_protocol.py`, que sigue siendo pseudocódigo de referencia.

## Cuándo usar esto vs. esperar a Mauricio

Si Mauricio confirma en cualquier momento que ABIDES-Gym funciona, **usar su integración real**, no este reemplazo — este es solo para no perder tiempo mientras no responde. Bórrense los archivos de esta tabla y avísenle al equipo que se hizo así, para que quede en el registro del proyecto (y, si corresponde, se documente esta decisión en el informe de Título II como una decisión de contingencia, no un cambio de arquitectura).
