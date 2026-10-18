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
3. Costo: 240 logits en vez de 3 + 1 parámetros; es manejable (61 680 parámetros en la cabeza, 134 897 en toda la red de un Ejecutor).

Si el comité exige la cabeza híbrida, el cambio queda acotado a `ExecutorActorCritic` y a la política del bucle PPO; se deja como mejora opcional del Sprint 6.

## Qué falta (y no se afirma)
No hay evidencia de que 256×256 sea el tamaño óptimo: no se ha hecho búsqueda de arquitectura. Es el tamaño ya usado por MR.

## Revisión de BF (2026-10-18)

Revisado con apoyo de Claude Code.

- Dimensiones verificadas contra el código: S_M de 7 (`build_sm_features.py`), Maestro con 40 acciones (`MaestroDiscreteActionSpace`), S_E de 27 y `MultiDiscrete([3, 10, 8])` aplanado a 240 (`EjecutorActionSpace.N_FLAT`). Los tests de la fábrica comprueban que los 3 Ejecutores no comparten pesos.
- **Hueco encontrado:** nadie usaba `make_hierarchy()`. Si no se le pasa `executor_policy_fn`, `MaestroEjecutorEnv` usa `get_default_executor_network()`, que es **una sola red para los tres tramos**. Se agregó `make_executor_policy_fn(redes)`, que devuelve la política `(s_e, tramo) -> idx` con la red del tramo activo, y un test que lo comprueba. El entrenamiento de la 3.1.x debe pasar esa política (o una equivalente) al protocolo.
- Cabeza totalmente discreta: **se mantiene**, por las razones 1 y 2 de arriba. La desviación queda declarada aquí.
