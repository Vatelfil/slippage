# Plan de borradores para MR y BF (Sprint 6)

**Elaborado por:** Paolo Sepúlveda (PS) con apoyo de Claude Code (uso autorizado por la universidad), 22 de octubre de 2026.
**Objetivo:** adelantar la parte de programación de las tareas de Mauricio (MR) y Benjamín (BF) del Sprint 6 para que solo tengan que **aceptar o modificar**, y puedan dedicar su poco tiempo a entrenar y analizar.
**Estado:** plan armado, **sin ejecutar**. Se ejecuta cuando PS dé la orden.

## 1. Reglas del juego

- Cada borrador va en una **rama y un PR propios**, marcado "**BORRADOR de PS para MR/BF, pendiente de su revisión**". Nada se mergea sin el visto bueno del responsable de la tarea.
- Cada borrador trae una lista **"Qué debes revisar o decidir"** con las propuestas y sus valores por defecto, para que cambiar algo sea editar un archivo, no reprogramar.
- **Todo se prueba en el PC** (con el simulador de Poisson y pruebas automáticas); **no se corre Colab** en esta etapa. Lo que haya que validar con ABIDES queda como lista de corridas posteriores (sección 6).
- Cada PR agrega su entrada en `docs/bitacora_cambios_PS.md` y, si trae gráficos, en `docs/guia_graficos.md`.
- No se toca el código de MR o BF en su rama: los parches se entregan como PR para su revisión (igual que el PR #41, que MR mergeó).

## 2. Qué pide el Sprint 6 a cada uno y qué se puede adelantar

| Responsable | Tarea del plan | Qué falta programar | Borrador de PS |
|---|---|---|---|
| **MR** | 2.3.2 versión final (vencía el 20 oct): ciclo de entrenamiento para Ejecutores **y Maestro**, con "un checkpoint reanuda sin cambiar el resultado" | Bucle de entrenamiento del Maestro (hoy `PPOTrainer` solo tiene `train_executor_episodes`); checkpoint sin estado aleatorio | **M1** y **M2** |
| **MR** | 3.1.1 tasa de aprendizaje, lote, épocas; 3.1.2 clipping ε y GAE λ | Infraestructura de barrido, reanudable y con análisis | **M3** |
| **MR** | P10: revalidar λ del Maestro con entrenamiento real | Script que repita la calibración de λ con la política entrenada | **M4** (depende de M1) |
| **MR** | 3.2.1 (Sprint 7): 90 corridas de evaluación | Evaluador del sistema por escenario, tamaño y semilla | **X1** (compartido) |
| **BF** | 3.1.3 corridas de evaluación por escenario de liquidez | Definición de los 3 escenarios y cómo aplicarlos al simulador | **B1** y **X1** |
| **BF** | 3.2.2 (Sprint 7): IS por corrida y consolidación | Consolidador de resultados por escenario y tamaño | **B2** |
| **BF** | D1 y D3 (decisiones pendientes) | Memos con evidencia y archivo candidato | Ya en el plan de ejecución de PS (`docs/plan_ejecucion_PS_sprint6.md`, A3 y E1) |

## 3. Borradores para Mauricio

### M1: bucle de entrenamiento del Maestro (y entrenamiento conjunto)
- **Qué es:** método `train_maestro_episodes` (en un módulo nuevo, sin editar `ppo_trainer.py`) que juega jornadas con `MaestroEjecutorEnv`: observa S_M, muestrea una de las 40 acciones, la decodifica a (α, ventana), recibe la recompensa terminal R_M, guarda en el buffer y actualiza con el `ppo_update` existente. Incluye la opción de **entrenar a los Ejecutores a la vez** usando el `executor_step_callback` que ya trae el orquestador.
- **Qué debe revisar o decidir MR:** (1) entrenar al Maestro con los Ejecutores **fijos**, **conjuntos** o por **turnos**; (2) **dónde entrenar**: cada decisión del Maestro simula un episodio de ABIDES (13 por jornada, de 3 a 6 minutos por jornada completa según los benchmarks); entrenar en ABIDES costaría horas, por lo que el borrador propone entrenar con el simulador de Poisson y **evaluar** en ABIDES; (3) hiperparámetros del Maestro (γ = 0,99 y los demás iniciales de `docs/ciclo_ppo_2.3.2.md`).
- **Pruebas locales:** 20 jornadas con Poisson sin NaN, CSV con las 8 columnas, mismo resultado con la misma semilla.
- **Esfuerzo de PS:** 4 h. **Revisión estimada de MR:** 45 a 60 min. **Desbloquea:** monitoreo del Maestro (B5), P10, entrenamiento completo y toda la comparación con TWAP y VWAP.

### M2: checkpoint que guarda el estado aleatorio
- **Qué es:** parche a `save_checkpoint` y `load_checkpoint` para guardar y restaurar el estado de `torch`, `numpy` y `random`, más una prueba nueva "entrenar 20 episodios seguidos = entrenar 10, guardar, cargar y entrenar 10 más".
- **Por qué:** el plan de T2 exige que un checkpoint reanude sin cambiar el resultado. La prueba actual (`test_checkpoint_y_reanudacion`) comprueba que el contador de episodios continúa, no que los resultados coincidan; en la corrida de 100 episodios reanudada desde el episodio 30 las curvas divergieron.
- **Qué debe revisar MR:** que el checkpoint sea compatible con los ya guardados (los antiguos se cargan sin el estado aleatorio) y que no cambie el formato del CSV.
- **Esfuerzo de PS:** 2 h. **Revisión de MR:** 20 min. **Es el borrador más pequeño y el de mayor retorno:** deja los resultados reproducibles al reanudar en Colab.

### M3: barrido de hiperparámetros (3.1.1 y 3.1.2)
- **Qué es:**
  - un archivo de rejilla (`grid_specs/mr_hiperparametros.json`, como las rejillas de `rmsc04`);
  - un corredor reanudable que entrena cada configuración con varias semillas de red, con el monitoreo activado y el mismo conjunto de semillas de evaluación;
  - un analizador con la **regla de selección fijada antes de ver los datos** (mismo método de la fase 2 de β): cumplimiento mínimo de 95 %, menor slippage y Wilcoxon pareado entre candidatos;
  - un informe con tabla y figura.
- **Propuesta de rejilla (MR la modifica):** tasa de aprendizaje {1e-4, 3e-4, 1e-3} × minibatch {64, 128}; épocas {4, 8}; clipping ε {0,1; 0,2; 0,3}; GAE λ {0,90; 0,95; 0,98}. Se recorre por etapas (los dos primeros factores primero, luego los otros alrededor del mejor), no el producto completo.
- **Decisión de diseño que MR debe confirmar:** una corrida de 100 episodios casi no mueve la política (la entropía queda en 99,9 % del máximo), por lo que el barrido necesita **1.000 episodios por configuración**. En ABIDES son ≈ 40 minutos cada una (18 corridas ≈ 12 h). El borrador propone **filtrar con el simulador de Poisson en el PC** (minutos por corrida) y **confirmar solo las 2 mejores configuraciones en ABIDES**. Hay que declarar que Poisson tiene otra dinámica.
- **Pruebas locales:** rejilla pequeña de 4 configuraciones con Poisson, reanudación, informe generado.
- **Esfuerzo de PS:** 5 h. **Revisión de MR:** 45 min (rejilla y regla). **Desbloquea:** 3.1.1 y 3.1.2 sin escribir infraestructura.

### M4: revalidar λ del Maestro (P10)
- **Qué es:** script que repite `experiments/calibrate_lambda_maestro.py` usando la política **entrenada** del Maestro (salida de M1) y compara el cociente penalización/slippage para los mismos valores de λ.
- **Depende de:** M1 y de que el Maestro tenga algún entrenamiento. **Esfuerzo de PS:** 2 h. **Estado:** se escribe después de M1; sin entrenamiento queda como esqueleto.

## 4. Borradores para Benjamín

### B1: escenarios de liquidez (3.1.3)
- **Qué es:** (1) `data/scenarios/escenarios_liquidez_v1.json` con tres escenarios (baja, media y alta liquidez); (2) una función que, a partir de la calibración vigente de cada activo, **escala la actividad** (`num_noise_agents` y `lambda_a` juntos, y la tasa de llegada en el simulador de Poisson) conservando la proporción de agentes de momentum.
- **Propuesta de valores (BF los decide):** media = calibración vigente (1,0×); baja = 0,75× (la grilla de actividad del 18 de octubre mostró mercado estable en 0,75× y roto en 0,5× y 0,25×); alta = 1,25× o 1,5× (**no probado todavía**).
- **Qué debe revisar o decidir BF:** los tres factores, y si los escenarios se aplican a los tres activos o solo a FALABELLA.
- **Pruebas locales:** transformación de los parámetros (pruebas sin ABIDES) y episodios con Poisson.
- **Lo que no se puede cerrar sin Colab:** comprobar que el mercado de ABIDES **sigue siendo estable** con cada factor (30 semillas por escenario, sin corridas desbocadas). Queda como corrida **C-6** (sección 6).
- **Esfuerzo de PS:** 4 h. **Revisión de BF:** 30 a 45 min.

### B2: consolidador de resultados (3.2.2)
- **Qué es:** script que junta los JSON de las corridas (por escenario, tamaño y semilla), calcula el IS y el slippage de cada una y deja una tabla maestra en CSV y Markdown, con el cumplimiento de cada orden.
- **Esfuerzo de PS:** 2 h. **Revisión de BF:** 20 min. Aprovecha el formato de los benchmarks (mismas claves `orden|estrategia|semilla`).

## 5. Borrador compartido

### X1: evaluador del sistema por escenario, tamaño y semilla
- **Qué es:** `scripts/colab/evaluar_sistema_ps.py`: corre `MaestroEjecutorEnv` con las redes (entrenadas o sin entrenar) sobre las 10 meta-órdenes, con un DataFrame que parte en el tramo de cada orden, y repite por escenario de liquidez (B1), tamaño y semilla; escribe el resultado en el formato de los benchmarks con `estrategia = "PPO"`, de modo que `comparar_sistema_vs_benchmarks.py` lo compara directamente.
- **Sirve a:** MR (3.2.1: 90 corridas = 3 liquidez × 3 tamaños × 10 semillas), BF (3.1.3) y PS (3.2.3 y 3.2.4).
- **Qué deben decidir:** los tres tamaños de orden (propuesta, a confirmar con la decisión D1: 5 %, 10 % y 20 % del volumen del día; recordar que con 20 % la ejecutabilidad probablemente falle).
- **Pruebas locales:** corrida con Poisson y redes sin entrenar, formato compatible con el comparador. **Esfuerzo de PS:** 4 h.

## 6. Qué se valida en Colab después (no ahora)

| # | Qué | Para qué | Tiempo aproximado |
|---|---|---|---|
| C-6 | 30 semillas por escenario de liquidez (B1) en ABIDES: estabilidad y momentos | Confirmar que los tres escenarios no rompen el mercado | ≈ 1 a 1,5 h por activo |
| C-7 | Confirmación en ABIDES de las 2 mejores configuraciones del barrido (M3) | Contrastar el filtro hecho con Poisson | ≈ 40 min por configuración y semilla |
| C-8 | Entrenamiento del Maestro en ABIDES (si MR lo decide en M1) | Entrenamiento realista | Horas; depende de la decisión de M1 |
| C-9 | Corrida del evaluador (X1) con redes entrenadas | Primera comparación del sistema con TWAP y VWAP | ≈ 80 min por escenario y semilla de red |

## 7. Orden y calendario

| Cuándo | Qué |
|---|---|
| **Viernes 23 oct** | M2 (2 h) y M1 (4 h): son los que más desbloquean; se entregan como PR para que MR los revise el fin de semana |
| **Lunes 26 oct** (arranque del Sprint 6) | Entregar M1 y M2 a MR; empezar M3 y B1; presentar el plan en la reunión |
| **Martes 27 a jueves 29 oct** | M3 (5 h) y B1 (4 h); X1 (4 h) |
| **Viernes 30 oct** | B2 (2 h) y M4 (2 h, si hay Maestro entrenado); revisión de lo que MR y BF hayan comentado |
| **Semana 2** | Ajustar los borradores según sus cambios; corridas C-6 a C-9 que ellos autoricen |

**Total para PS:** unas 23 h de programación (M1 4, M2 2, M3 5, M4 2, B1 4, B2 2, X1 4), repartidas en una semana. **Para ellos:** unas 4 h de revisión en total en lugar de programar y probar desde cero.

## 8. Mensajes cortos para el grupo (para cuando se ejecute)

**A Mauricio:**
> Mauri, para ahorrarte tiempo dejé tres borradores en PR, marcados "borrador de PS para MR": (1) el bucle de entrenamiento del Maestro, (2) un parche para que el checkpoint guarde el azar y reanudar no cambie los resultados, y (3) la infraestructura del barrido de hiperparámetros con una rejilla propuesta. Solo tienes que revisar y cambiar lo que quieras; no se mergea nada sin tu visto bueno.

**A Benjamín:**
> Benja, dejé dos borradores en PR, marcados "borrador de PS para BF": los tres escenarios de liquidez (con factores propuestos) y el consolidador de resultados. También queda pendiente tu decisión de D1 y D3, con el memo y la evidencia lista.

## 9. Riesgos y decisiones abiertas

| Riesgo o decisión | Qué hacer |
|---|---|
| MR prefiere otro diseño para el Maestro (turnos, otro simulador) | El borrador es un punto de partida; el PR deja las opciones en parámetros y MR elige |
| Entrenar el Maestro en ABIDES es demasiado lento | M1 propone Poisson para entrenar y ABIDES para evaluar; MR confirma |
| El filtro con Poisson no coincide con ABIDES | Se confirman las 2 mejores configuraciones en ABIDES (C-7) y se declara el límite |
| El escenario de alta liquidez rompe el mercado (no se probó) | C-6 lo detecta; BF decide otro factor o se deja solo baja y media |
| MR y BF tienen poco tiempo para revisar | Los PR son pequeños y cada uno trae su checklist; se agrupan en dos PR (uno por persona) |
| Conflictos con los PR de Sprint 5 y 6 sin mergear | Los borradores se basan en `main` una vez mergeados; mientras tanto, en la rama del plan |

🤖 Generado con [Claude Code](https://claude.com/claude-code)
