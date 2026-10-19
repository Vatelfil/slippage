# 2.1.1 Red actor-crítico del Maestro: especificación frente a implementación

> **Borrador** elaborado por PS con apoyo de Claude Code el 15 oct 2026, a partir de la lectura de `src/models/actor_critic.py`; pendiente de revisión del equipo. Cubre también la estructura común de los Ejecutores (2.1.2).

## 1. Qué pedía el Excel (tarea 2.1.1)

Red de PyTorch con entrada de 7 dimensiones (S_M), **2 capas de 64 neuronas con ReLU**, salidas `logits_alpha(10)`, `logits_ventana(4)` y `value_critic(1)`, **inicialización Xavier** y **Dropout 0,2**. Pasos del plan: diseño, implementación, inicialización Xavier, grafo de cómputo, pruebas exhaustivas de formas y gradientes, documentación.

## 2. Qué hay implementado

`BaseActorCritic` (compartida por el Maestro y los Ejecutores):
- Tronco compartido de **2 capas de 256 neuronas con ReLU**.
- **Una cabeza de política** (`actor_head`) con logits discretos y **una cabeza de valor** (`critic_head`).
- Maestro: 40 logits (10 fracciones × 4 ventanas, decodificados con `divmod`). Ejecutores: 240 logits (3 × 10 × 8 aplanados).
- Inicialización por defecto de PyTorch; sin Dropout.
- Muestreo con `torch.distributions.Categorical` (`get_action_and_value`).

## 3. Diferencias y razón

| Punto | Excel | Implementado | Razón y consecuencia |
|---|---|---|---|
| Neuronas por capa | 64 | 256 | Mayor capacidad para el vector de estado de los Ejecutores (27 entradas); sin evidencia de que 64 baste. Costo: más parámetros (≈ 78 mil en la red del Maestro y ≈ 135 mil en cada Ejecutor). No se ha hecho búsqueda de arquitectura; se revisa en el ajuste de hiperparámetros (Sprint 6) |
| Salidas del Maestro | Dos cabezas (10 y 4) | Una categórica conjunta de 40 | Es más expresiva (modela la dependencia entre fracción y ventana) y mantiene un solo log-probabilidad para el cociente de PPO. Con dos cabezas independientes el log-prob sería la suma de dos |
| Actor y crítico | Dos redes en el Título I; tronco único con dos cabezas en el Excel | Tronco compartido con dos cabezas | Es la forma habitual en PPO con entradas de baja dimensión. Riesgo: el gradiente del crítico afecta al actor; se vigila con las curvas de pérdida (tarea 3.1.4) |
| Inicialización | Xavier | Por defecto de PyTorch (Kaiming uniforme) | No se ha medido diferencia. Se puede cambiar sin tocar la interfaz |
| Dropout | 0,2 | Ninguno | En PPO el Dropout agrega ruido al cociente de probabilidades entre la política vieja y la nueva y suele evitarse |
| Pruebas de formas y gradientes | Exhaustivas | Cubiertas ahora en `tests/test_actor_critic.py` | Antes solo había un bloque de prueba en el propio archivo |

## 4. Qué se verifica (tests)

`tests/test_actor_critic.py`: formas de entrada y salida del Maestro (7 → 40) y de un Ejecutor (27 → 240); ausencia de NaN; gradientes distintos de cero en **todos** los parámetros tras una pérdida compuesta; consistencia de `get_action_and_value` (el log-prob de una acción dada coincide con el de la distribución); acciones dentro de rango; reproducibilidad con semilla.

## 5. Decisión pendiente del equipo

Dos caminos para cerrar la tarea:
1. **Aceptar la implementación actual** con esta nota de desviación (recomendado: cambiar la red ahora obliga a reentrenar y a rehacer la fase 2 de β).
2. **Alinear la red al Excel** (64 neuronas, Xavier, Dropout, dos cabezas): trabajo de unas 6 h más reentrenamiento, y requiere ajustar el decodificador de acciones del orquestador.

Hasta que el equipo decida, el estado de la tarea es "hecho con desviación documentada".
