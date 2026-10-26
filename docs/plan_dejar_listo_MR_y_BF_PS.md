# Plan para dejar listo el trabajo de MR y BF (que lleguen, ejecuten y revisen)

**Elaborado por:** PS con apoyo de Claude Code (uso autorizado por la universidad), 26 de octubre de 2026. **Estado: propuesta, sin ejecutar.** Se ejecuta cuando PS dé la orden.
**Se basa en:** el chat completo de las sesiones del proyecto, el Título I, `plan-desarrollo-titulo-2.xlsx`, `ESPECIFICACION_DETALLADA_TAREAS.md`, `Contexto_Agente_Programacion.md`, `docs/sprint5_que_se_hizo.md`, `docs/sprint6_que_se_hizo.md`, `docs/plan_borradores_para_MR_y_BF_sprint6.md` y el estado real del repositorio.

## 0. Aclaración: qué era el "plan 2"

En el chat del 25 de octubre se pidieron dos planes:

| Plan | Qué era | Estado verificado |
|---|---|---|
| **Plan 1** | Investigar y arreglar el problema crítico (la red entrenada no bajaba el costo) | Hecho: causa identificada (espera sin costo y γ = 0,95), arreglo (penalización 30 bps + γ = 1), confirmación en ABIDES y reevaluación con 300 semillas. Resultado: el arreglo hace que la red complete la orden, pero **no baja el costo** frente a la red sin entrenar |
| **Plan 2** | Desarrollo completo de la parte de PS (Sprints 6 a 9) y adelantar lo que dependa de otros | **Ejecutado lo adelantable:** monitoreo 3.1.4 con alertas calibradas, costo ajustado por lo no ejecutado, sensibilidad 3.2.4 (con datos sintéticos), Sprint Review borrador. **No ejecutado:** los borradores para MR y BF (`docs/plan_borradores_para_MR_y_BF_sprint6.md`, "plan armado, sin ejecutar") |

Verificado en el código: **no existe** bucle de entrenamiento del Maestro, ni escenarios de liquidez, ni consolidador de resultados, ni infraestructura de barrido de hiperparámetros. Este documento es el plan para ejecutar esa parte.

## 1. Dónde estamos (verificado)

| Hecho | Detalle |
|---|---|
| Fechas | Hoy es el primer día del Sprint 6 (26 oct a 6 nov). El Sprint 7 (comparación con TWAP y VWAP) termina el 20 de noviembre; el informe se escribe del 23 de noviembre al 4 de diciembre. Quedan **≈ 3,5 semanas** de experimentos |
| `main` | Último merge el 21 de octubre (PR #41, MR). Hay **19 ramas de PS sin mergear** (orden en `docs/bitacora_cambios_PS.md`) |
| Ejecutor solo | Con 300 semillas, ninguna de 8 redes entrenadas se distingue de la misma red sin entrenar (diferencias de −0,6 a +1,0 bps, todos los IC con el 0). Completan la orden, pero cuestan ≈ 2 bps más que TWAP límite. Ver `docs/reeval_300_resultado_PS.md` |
| Sistema completo sin entrenar | Cumple el 66,3 % de las 10 meta-órdenes (apertura 94,6 %; media jornada 76,3 %; cierre 18,5 %) y no se distingue de TWAP en costo. Con 300 bps de penalización por lo no comprado es claramente peor |
| Maestro | **Sin bucle de entrenamiento.** Es el camino crítico: sin él no hay sistema entrenado, ni 90 corridas con sentido, ni comparación final |
| Decisiones de BF | D1 (tamaño de las órdenes) y D3 (R_E) sin respuesta. Rigen las reglas por defecto |
| Hipótesis del proyecto | Reducir el IS al menos 10 % frente a TWAP y VWAP (`Contexto_Agente_Programacion.md`, sección 1; el Título I habla de "reducción de costos" sin cifra) |

**Lectura:** el Maestro es lo que reparte la orden entre tramos y la completa. Que el Ejecutor solo no mejore no refuta el proyecto, pero tampoco lo prueba. La prueba está en el sistema completo entrenado, y eso depende de lo que hoy falta.

## 2. Lo que exige el Título I y qué falta para cumplirlo

| Objetivo específico (Título I, sec. 5.2) | Estado | Qué falta |
|---|---|---|
| 1. Entorno de simulación de alta fidelidad | Hecho con límites documentados (volumen y spread de `rmsc04`) | Nada para este sprint |
| 2. Arquitectura jerárquica Maestro + Ejecutores con PPO | Ejecutor entrenable; **Maestro no** | Bucle del Maestro (M1) |
| 3. Recompensa que minimiza el IS | R_E y R_M implementadas; la propuesta de PS (penalización + γ = 1) espera revisión | Decisión de BF y MR; revalidar λ (M4) |
| 4. Evaluación contra TWAP y VWAP | Scripts listos (3.2.3, 3.2.4); evaluador con redes sin entrenar | Sistema entrenado, escenarios de liquidez, 90 corridas |

El Título I (etapa 6) pide demostrar "en qué medida ayuda" el sistema y qué limitaciones conserva. **Un resultado negativo, bien documentado y con intervalo de confianza, es un cierre válido**; no hay que forzar un resultado positivo.

## 3. Principio del plan: un "paquete de llegada" por persona

Cada persona recibe una carpeta y un PR propios, marcados "**BORRADOR de PS para MR/BF, pendiente de su revisión**", con:

1. **Leeme de una página** (`docs/LEEME_MR_SPRINT6.md`, `docs/LEEME_BF_SPRINT6.md`): qué es cada cosa, en qué orden se hace.
2. **Cinco pasos como máximo**, con el comando exacto (clonar la rama, correr las pruebas, correr el comando, mirar el resultado).
3. **Lista "qué debes revisar o decidir"** con el valor propuesto por defecto: cambiar algo es editar un archivo, no reprogramar.
4. **Cuaderno de Colab completo** (celdas 1 a 9 numeradas, carpeta propia en Drive) cuando haga falta entrenar.
5. **Tiempo estimado de revisión** y qué pasa si no responden (valor por defecto y plazo).

Reglas que se mantienen: nada se mergea sin el visto bueno del responsable; no se toca su código en su rama (se entrega por PR); cada PR deja entrada en la bitácora y, si trae gráficos, su explicación en `docs/guia_graficos.md`; no se actualiza el informe del Título II.

## 4. Paquete para MR

| # | Borrador | Qué recibe MR | Qué revisa o decide | Esfuerzo PS | Revisión MR |
|---|---|---|---|---:|---:|
| **M1** | Bucle de entrenamiento del Maestro (`train_maestro_episodes`, módulo nuevo; no edita `ppo_trainer.py`) | Juega jornadas con `MaestroEjecutorEnv`, muestrea una de las 40 acciones, recibe R_M terminal y actualiza con el `ppo_update` existente. Opción de entrenar a los Ejecutores a la vez con `executor_step_callback` | (1) Ejecutores **fijos**, **conjuntos** o **por turnos**; (2) dónde entrenar (**propuesta: Poisson para entrenar, ABIDES para evaluar**, porque una jornada en ABIDES toma 3 a 6 min); (3) hiperparámetros del Maestro (γ = 0,99) | 4 h | 45–60 min |
| **M2** | Checkpoint que guarda el estado aleatorio (`torch`, `numpy`, `random`) | Parche pequeño y una prueba "20 episodios seguidos = 10 + guardar + cargar + 10" | Que los checkpoints viejos sigan cargando y que el CSV no cambie | 2 h | 20 min |
| **M3** | Infraestructura del barrido de hiperparámetros (3.1.1 y 3.1.2) | Archivo de rejilla (`grid_specs/mr_hiperparametros.json`), corredor reanudable, analizador con **regla de selección fijada antes de ver los datos** (cumplimiento ≥ 95 %, menor costo, Wilcoxon pareado), informe | La rejilla (propuesta: lr {1e-4, 3e-4, 1e-3} × minibatch {64, 128}; épocas {4, 8}; ε {0,1; 0,2; 0,3}; λ GAE {0,90; 0,95; 0,98}, por etapas) y filtrar con Poisson, confirmando solo las 2 mejores en ABIDES | 5 h | 45 min |
| **M4** | Revalidar λ del Maestro (P10) | Script que repite `calibrate_lambda_maestro.py` con la política entrenada | Que el cociente penalización/slippage sea el esperado | 2 h (esqueleto hasta que haya Maestro entrenado) | 20 min |
| **M5** | Parche listo de γ = 1 en `PPOConfig` | Cambio de una línea más la nota para `DESVIACIONES_TITULO1_VS_IMPLEMENTACION.md` (γ_E pasa de 0,95 a 1,0 con su justificación) | Aceptar o rechazar | 1 h | 10 min |
| **M6** | Cuaderno de Colab para entrenar el Maestro | Celdas 1 a 9 + entrenamiento + zip, con carpeta propia en Drive | Solo "Ejecutar todas" y devolver el zip | 2 h | — |

## 5. Paquete para BF

| # | Borrador | Qué recibe BF | Qué revisa o decide | Esfuerzo PS | Revisión BF |
|---|---|---|---|---:|---:|
| **B1** | Escenarios de liquidez (3.1.3) | `data/scenarios/escenarios_liquidez_v1.json` con tres escenarios y una función que escala `num_noise_agents` y `lambda_a` juntos (y la tasa de Poisson) | Los tres factores (propuesta: baja 0,75×, media 1,0×, alta 1,25× a 1,5×, **no probado**) y si valen para los tres activos o solo FALABELLA | 4 h | 30–45 min |
| **B2** | Consolidador de resultados (3.2.2) | Script que junta los JSON por escenario, tamaño y semilla y deja una tabla maestra (CSV y Markdown) con cumplimiento | Columnas y formato | 2 h | 20 min |
| **B3** | Penalización por lo no comprado en R_E (2.2.3) | Parche listo en la recompensa del entorno (hoy vive en un envoltorio de pruebas), con pruebas | Aceptar o rechazar | 1 h | 15 min |
| **B4** | **Hoja de decisiones D1 y D3** | Una página con la pregunta, la evidencia actualizada (incluye la reevaluación de 300 semillas) y la **respuesta por defecto con fecha límite** | Marcar una opción | 1 h | 10 min |
| **B5** | Cuaderno de Colab de la corrida C-6 (estabilidad de cada escenario de liquidez, 30 semillas) | Celdas 1 a 9 + corrida + zip | "Ejecutar todas" y devolver el zip | 1,5 h | — |

## 6. Compartido y de PS

| # | Qué | Estado | Esfuerzo PS |
|---|---|---|---:|
| **X1** | Evaluador por escenario, tamaño y semilla (90 corridas). Ya existe `scripts/colab/evaluar_sistema_ps.py` con redes sin entrenar; falta que acepte **escenarios de liquidez**, **tres tamaños de orden** y **checkpoints entrenados** | Parcial | 3 h |
| **P1** | Orden de PR y merge (lo abre PS, lo mergea quien revisa) | Pendiente | 30 min |
| **P2** | Mensaje corto a MR y BF con el enlace al leeme de cada uno (**borrador, no se envía sin tu OK**) | Pendiente | 20 min |
| **P3** | Actualizar `docs/sprint6_que_se_hizo.md` con la reevaluación de 300 semillas | Pendiente | 30 min |
| **P4** | Cálculo de potencia del diseño de 90 corridas (ver sección 7) | Pendiente | 1 h |

**Total estimado de trabajo mío: ≈ 28 h** repartidas en una semana. Para MR y BF son unas **4 h de revisión** en total, en lugar de programar y probar desde cero.

## 7. Riesgo importante: el diseño de 90 corridas puede no detectar un 10 %

Con las 20 celdas del sistema sin entrenar, la diferencia con TWAP por celda tiene una desviación de **≈ 70 bps** (estimada del IC [−15,9; 49,8]), con un slippage de TWAP por orden de −8 a 310 bps. Con 90 corridas independientes, el efecto mínimo detectable (80 % de potencia, α = 0,05) queda en **≈ 20 bps**. Una reducción del 10 % del IS de TWAP son entre 5 y 30 bps según la orden.

Es una estimación hecha con un sistema que aún no completa las órdenes (hay más variación), así que **hay que recalcularla con el primer sistema entrenado**. Qué hacer:

1. Mantener el pareo por orden y semilla (el mismo precio exógeno para el sistema y el benchmark).
2. Informar siempre el IC, no solo el p-valor, y escribir en el informe qué efecto mínimo se puede detectar.
3. Decidir con la profesora guía cómo se redacta la hipótesis del 10 %, si con 90 corridas no se puede confirmar con esa precisión (decisión del grupo, no mía).

## 8. Colab: qué hay que correr y cuándo (aviso previo)

| # | Qué | Quién | Tiempo | Cuándo |
|---|---|---|---|---|
| — | Opcional: volver a ejecutar la celda de evaluación del cuaderno de reevaluación para sumar las redes V4 de las semillas 3000 y 4000 | PS | 20–40 min | Cuando quieras; no cambia la conclusión |
| **C-6** | 30 semillas por escenario de liquidez en ABIDES (estabilidad) | BF (cuaderno B5) | 1 a 1,5 h por activo | Tras B1 |
| **C-8** | Entrenamiento del Maestro (si MR decide ABIDES) o confirmación en ABIDES de lo entrenado con Poisson | MR (cuaderno M6) | Horas; se mide primero cuánto tarda una jornada en Poisson | Tras M1 |
| **C-7** | Confirmación en ABIDES de las 2 mejores configuraciones del barrido | MR | ≈ 40 min por configuración y semilla | Tras M3 |
| **C-9** | Evaluador del sistema (X1) con el Maestro y los Ejecutores entrenados | PS | ≈ 80 min por escenario y semilla de red | Tras M1 y B1 |

Cada cuaderno se entrega como `.ipynb` completo, con sus celdas 1 a 9 numeradas, carpeta propia en Drive y la explicación de qué hacer si Colab corta la ejecución.

## 9. Calendario propuesto

| Cuándo | Qué |
|---|---|
| **Lun 26 – mar 27 oct** | P1 (orden de PR), leemes y hoja de decisiones B4 |
| **Mar 27 – jue 29** | M2 y M1 (los que más desbloquean), luego B1 y X1 |
| **Vie 30 oct** | M3, B2, B3, M5; revisión de lo que MR y BF hayan comentado; P4 |
| **2 – 6 nov** (Sprint 6) | MR entrena el Maestro (M6); BF corre C-6; PS entrega el panel de comparación de corridas; **Sprint Review el 6 de nov** (3.1.5) |
| **9 – 20 nov** (Sprint 7) | 90 corridas (3.2.1), consolidación (3.2.2), comparación estadística (3.2.3), sensibilidad (3.2.4) |
| **23 nov – 4 dic** | Informe (capítulos 5, 6 y 7) con lo que haya, incluido un resultado negativo si es el caso |

## 10. Qué no se hace

- No se edita el código de MR ni de BF en sus ramas: todo va por PR marcado como borrador.
- No se actualiza el informe del Título II (solo md).
- No se entrena más al Ejecutor solo (5.000 a 10.000 episodios ni recompensa pareada contra TWAP) hasta ver el sistema completo. Queda como **plan B**: si el Maestro entrenado tampoco muestra mejora con intervalo de confianza, se retoma.
- No se envía ningún mensaje a MR ni BF sin tu OK.

## 11. Qué necesito de PS para ejecutar

1. **OK para ejecutar los borradores** de las secciones 4 a 6 (o solo algunos).
2. **Dónde entrenar el Maestro:** por defecto Poisson en el PC y evaluación en ABIDES; MR lo puede cambiar al revisar.
3. **Fecha límite por defecto para D1 y D3** si BF no responde (propuesta: viernes 30 de octubre).
4. **OK para el mensaje a MR y BF** (lo escribo; lo envías tú).

🤖 Generado con [Claude Code](https://claude.com/claude-code)
