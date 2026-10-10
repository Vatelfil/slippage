# 2.1.2 Redes de los 3 Ejecutores — nota de diseño

**Elaborado por PS con apoyo de Claude Code; pendiente de revisión por BF (responsable de la tarea) y MR.**

## Qué se entrega
`src/models/networks_factory.py`: `make_master_network()`, `make_executor_networks()` y `make_hierarchy()`.
- Maestro: S_M de 7 dim → 40 acciones (10 fracciones × 4 ventanas).
- Ejecutores: 3 instancias **independientes** (apertura, media jornada, cierre), S_E de 27 dim → 240 acciones (3 × 10 × 8 aplanado).
- Cuerpo compartido por rol: 2 capas ocultas de 256 con ReLU, cabeza de política (logits) y cabeza de valor.

## Desviación respecto del Título I
El Título I describe una cabeza **híbrida** (discreta para el tipo de orden, continua para el volumen). Aquí es **totalmente discreta**:
1. El entorno ya expone `MultiDiscrete([3, 10, 8])` (`EjecutorActionSpace`, tarea 2.1.4); una cabeza continua obligaría a discretizar de todos modos.
2. El PPO de MR (`ExecutorActorCritic` + `get_action_and_value`) usa una sola distribución categórica; mezclar dos familias complica el ratio de PPO y el gradiente.
3. Costo: 240 logits en vez de 3 + 1 parámetros; es manejable (≈ 66 mil parámetros en la cabeza).

Si el comité exige la cabeza híbrida, el cambio queda acotado a `ExecutorActorCritic` y a la política del bucle PPO; se deja como mejora opcional del Sprint 6.

## Qué falta (y no se afirma)
No hay evidencia de que 256×256 sea el tamaño óptimo: no se ha hecho búsqueda de arquitectura. Es el tamaño ya usado por MR.
