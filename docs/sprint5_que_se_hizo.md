# Sprint 5 (12–23 oct 2026): qué se hizo

Documento de cierre del Sprint 5. **Borrador** elaborado por PS con apoyo de Claude Code (uso autorizado por la universidad) el 23 de octubre de 2026, a partir del repositorio, los documentos de cada tarea y las corridas de Colab. Cada fila debe ser confirmada por su responsable (columna "Confirma"); lo que nadie objete en la reunión de cierre queda como está escrito.

Estados (los del plan del Sprint 5): **Hecho** · **Hecho con límite demostrado** (se ejecutó y midió; el resultado no alcanza el criterio ideal y el límite está escrito con su causa) · **Pasa al Sprint 6 por diseño** (con la razón y el costo medido).

> **Condición de cierre del plan:** una tarea queda cerrada cuando su código está en `main` mediante un PR mergeado. Varias filas dependen de PR todavía abiertos; se indican en la columna "PR".

## Tareas del sprint

| Tarea | Responsable | Estado | Qué hay | PR | Confirma |
|---|---|---|---|---|---|
| **T1 · 2.3.1** Integración CTDE Maestro–Ejecutores | MR | Hecho | Protocolo de mensajes ASIGNAR/REPORTE validados con JSON (`docs/protocolo_ctde_2.3.1.md`). Evidencia con ABIDES real: 2 mensajes válidos y episodio completo. El REPORTE de ABIDES venía en décimos de peso; MR lo convirtió a pesos con `unidades_por_clp` | #34 y #41 (mergeados) | MR |
| **T2 · 2.3.2** Ciclo de entrenamiento PPO | MR | Hecho con límite | Entrenador unificado `PPOTrainer` (GAE, parada por KL, checkpoints, CSV; `docs/ciclo_ppo_2.3.2.md`) para el **Ejecutor**. Entrena 4 episodios con ABIDES y reanuda sin NaN. **Límite 1:** no hay bucle de entrenamiento del Maestro (solo `train_executor_episodes`). **Límite 2:** el checkpoint no guarda el estado aleatorio: reanudar cambia los resultados, y el plan pide que no los cambie | #34 y #41 (mergeados) | MR |
| **T3 · 2.3.3** Meta-órdenes de prueba | BF (borrador de PS) | Hecho con límite | Las 10 órdenes (100.000 acciones; FALABELLA 4, COPEC 3, ECL 3; apertura 4, media jornada 3, cierre 3), generador reproducible y documento (`docs/meta_ordenes_2.3.3.md`). Validación de ejecutabilidad con TWAP: **5 de 10 órdenes** llegan al 95 % con 100.000 acciones (2 semillas) | `final-v2` (sin mergear) | BF |
| **T4 · 2.3.4** Benchmarks TWAP y VWAP | PS | Hecho | Tabla de IS y slippage de TWAP y VWAP para las 10 órdenes con 2 semillas, media y error estándar (`docs/benchmarks_2.3.4_PS.md`); además, con 10 % del volumen del día y con 5 % en el cierre | `final-v2` (sin mergear) | PS |
| **T5 · 2.3.5** Entrenamiento inicial de validación | BF (borrador de PS) | Hecho con límite | Entrenamiento de 100 episodios (apertura, FALABELLA) con checkpoint, CSV e informe; además 1.000 episodios con la opción 0 y con la opción A, diagnóstico de la política y repetición de 100 episodios (`docs/entrenamiento_inicial_2.3.5.md`). **Límite:** ninguna red entrenada mejora el slippage de la red sin entrenar de forma significativa | #39 (100 episodios, mergeado) y `final-v2` (sin mergear) | BF |
| **P1** Normalización de R_E | PS | Hecho | Normalizador móvil: la salida queda dentro de [−1, 1] (`docs/distribucion_recompensa_2.2.3_PS.md`) | #28 | PS |
| **P2** Decidir e implementar R_E (D3) | BF decide | Hecho con límite | Rige la opción 0 (fórmula del Título I, β = 0,0061796) con regla de vigilancia; la opción A (riesgo sobre lo pendiente) está implementada y apagada por defecto. **La regla no es estable** con una sola corrida (ver abajo); la decisión final es la revisión del 23 de octubre | #28, #29, #30 | BF |
| **P3** Volumen y spread de `rmsc04` | BF (PS valida) | Hecho con límite | Grilla de actividad hacia abajo (18 oct): el volumen alto queda como **límite demostrado**; el spread se acepta como límite documentado (D4, opción A) | #32 | BF |
| **P4** Calibración de COPEC y ECL | PS | Hecho con límite | Con 3 agentes de momentum y `fund_vol` ajustado: 0 de 30 corridas desbocadas en los tres tramos; el KS rechaza (`docs/calibracion_rmsc04_COPEC_ECL_P4_PS.md`) | #35 y #36 | PS |
| **P5** β en media jornada y cierre | PS | Hecho | Solo 0,1 × β∗ cumple el 95 % en los tres tramos; propuesta de β común (`docs/beta_fase2_media_cierre_PS.md`) | #37 | BF |
| **P6** Ratificar la fábrica de redes (2.1.2) | BF | Hecho | Ratificada el 18 oct, con la corrección `make_executor_policy_fn()` | #32 | BF |
| **P7** Barrido de β en Poisson | BF | Hecho | Regenerado con el simulador corregido; el anterior queda marcado como obsoleto | #32 | BF |
| **P8** PR de cierre del Sprint 4 | MR (mergea) | Hecho | PR de cierre del Sprint 4 (#27) y acta de cierre de los sprints 1 a 4 (#36) mergeados; MR confirmó el cierre en el PR #34 | #27, #34 y #36 | MR |
| **P9 / D5** Corte de tramos 11:00 frente a 11:30 | MR (documento), BF decide | Hecho | Rige la opción A: se mantienen ambos cortes y se documenta (`DESVIACIONES_TITULO1_VS_IMPLEMENTACION.md`) | #34 | MR |
| **P10** Revalidar λ del Maestro | MR | Pasa al Sprint 6 | Depende de un Maestro entrenado, y el bucle de entrenamiento del Maestro no existe aún (T2, límite 1). La nota de alcance de λ (provisional) se cerró en el PR #33 | #33 | MR |

## Resultados clave

**T4 (benchmarks, 2 semillas por orden, ABIDES calibrado).** Con 100.000 acciones, la diferencia media TWAP − VWAP es de −4,9 bps y no es significativa (Wilcoxon p = 0,156). En las órdenes que parten en el cierre, TWAP y VWAP son idénticos (un solo tramo restante).

**Ejecutabilidad de las órdenes (criterio de T3: TWAP completa al menos el 95 %).**

| Tamaño de las órdenes | Órdenes ejecutables | Qué falla |
|---|---|---|
| 100.000 acciones (opción A de D1) | 5 de 10 | MO-02, MO-06, MO-07, MO-09, MO-10 |
| 10 % del volumen del día | 8 de 10 | FALABELLA al cierre: MO-09 (93,2 %) y MO-10 (87,4 %) |
| 5 % del día solo en el cierre (44.100 acciones) | 3 de 3 de cierre | MO-10 en el borde (95,1 %: 90,2 % y 100 %) |

Las órdenes de 100.000 acciones equivalen al 31–49 % del volumen simulado que queda en COPEC y ECL, y al 35 % en FALABELLA al cierre. Una combinación que deja las 10 órdenes ejecutables es 10 % del día en apertura y media jornada y 5 % en el cierre (propuesta de PS; la decisión D1 es de BF).

**T5 (entrenamiento inicial del Ejecutor).**

| Corrida | Cumplimiento con argmax | Slippage con argmax (bps) | Cumplimiento muestreada |
|---|---:|---:|---:|
| 100 episodios, opción 0 (reanudada desde el episodio 30) | 1,000 | 3,28 | — |
| 100 episodios, opción 0 (repetición sin cortes) | 0,904 | 2,04 | 1,000 |
| 1.000 episodios, opción 0 | **0,000** | sin ejecuciones | 0,9996 |
| 1.000 episodios, opción A (riesgo sobre lo pendiente) | 1,000 | 5,91 | 1,000 |
| Red sin entrenar (control) | 1,000 | 6,02 | — |

- Con la opción 0, la acción más probable de la red es `LIMIT_SELL`, que el puente de ABIDES traduce a "esperar": con argmax no ejecuta; muestreando, sí. Con la opción A, el argmax ejecuta toda la orden.
- **Ninguna corrida se distingue de la red sin entrenar en slippage** (diferencias pareadas con p entre 0,36 y 0,80).
- **La regla de vigilancia de D3 no es estable con la opción 0:** el cumplimiento con argmax fue 1,000, 0,904 y 0,000 en tres corridas (2 de 3 bajo el 95 %). La primera de 100 episodios se reanudó desde el episodio 30 y por eso difiere de su repetición sin cortes. Con la opción A hay solo una corrida.

**P4 y P5.** Ver los documentos de cada tarea (cifras en la tabla anterior y en `docs/calibracion_rmsc04_COPEC_ECL_P4_PS.md` y `docs/beta_fase2_media_cierre_PS.md`).

## Decisiones pendientes al cierre del sprint

| Decisión | Quién | Qué rige mientras no se decida | Evidencia |
|---|---|---|---|
| **D1** Tamaño de las meta-órdenes | BF | Opción A: 100.000 acciones. B (porcentaje del día) queda como análisis de sensibilidad del Sprint 7 | Tabla de ejecutabilidad (arriba) y `docs/benchmarks_2.3.4_PS.md` |
| **D3** R_E: opción 0 u opción A | BF (con MR y PS) | Opción 0 con regla de vigilancia | `docs/decision_RE_final_D3_para_BF.md` |
| β común o por tramo | BF | β = 0,0061796 (0,1 × β∗) | `docs/beta_fase2_media_cierre_PS.md` |

## Hallazgos de este sprint

- **Reproducibilidad:** con las mismas semillas un entrenamiento sin cortes da curvas idénticas, pero reanudar desde un checkpoint cambia los resultados (el checkpoint no guarda el estado aleatorio). Es el límite 2 de T2.
- **Evaluación determinista:** una política con alta entropía puede tener como acción más probable una acción que no hace nada; por eso conviene evaluar también muestreando. Se agregó esa evaluación al script de T5 y alertas en el monitoreo (`src/training/monitoreo.py`).
- **COPEC y ECL:** los 12 agentes de momentum por defecto desestabilizan el mercado cuando hay pocos agentes de ruido; con 3 se estabiliza.
- **Conversión de unidades:** el REPORTE de ABIDES venía en décimos de peso sin convertir; MR lo corrigió en el PR #41.

## Pasa al Sprint 6 por diseño

| Qué | Responsable | Razón y costo medido |
|---|---|---|
| Bucle de entrenamiento del Maestro | MR | Es lo que falta para entrenar el sistema completo. Con ABIDES cada jornada simula 13 episodios (de 3 a 6 minutos por jornada completa en los benchmarks), por lo que entrenar allí costaría horas |
| Checkpoint con estado aleatorio | MR | El plan de T2 pide que reanudar no cambie los resultados |
| Revalidar λ del Maestro (P10) | MR | Necesita el Maestro entrenado |
| Ajuste de hiperparámetros (3.1.1 y 3.1.2) | MR | Una corrida de 100 episodios casi no mueve la política (entropía al 99,9 %); 1.000 episodios cuestan ≈ 40 minutos en ABIDES |
| Evaluación por escenario de liquidez (3.1.3) | BF | Los escenarios aún no están definidos; la actividad 0,5× rompió el mercado en la grilla del 18 de octubre |
| Monitoreo y registro de métricas (3.1.4) | PS | Código adelantado; falta validarlo con ABIDES y usarlo en las corridas de MR y BF |
| β en media jornada y cierre con la opción A (si BF cambia D3) | BF y PS | Repite β∗ y la fase 2: varias horas de Colab |

## Dónde está cada cosa

| Tema | Archivo |
|---|---|
| Protocolo CTDE y ciclo PPO | `docs/protocolo_ctde_2.3.1.md`, `docs/ciclo_ppo_2.3.2.md` |
| Meta-órdenes | `docs/meta_ordenes_2.3.3.md`; `data/meta_ordenes/` |
| Benchmarks | `docs/benchmarks_2.3.4_PS.md`; `data/colab_resultados/benchmarks_meta_ordenes_abides*.json` |
| Entrenamiento inicial | `docs/entrenamiento_inicial_2.3.5.md`; `data/colab_resultados/t5_*` |
| Decisión D3 | `docs/decision_RE_para_BF.md` y `docs/decision_RE_final_D3_para_BF.md` |
| COPEC y ECL, β en media jornada y cierre | `docs/calibracion_rmsc04_COPEC_ECL_P4_PS.md`, `docs/beta_fase2_media_cierre_PS.md` |
| Qué hay en cada PR y gráficos | `docs/bitacora_cambios_PS.md`, `docs/guia_graficos.md` |
| Plan del Sprint 6 | `docs/plan_accion_PS_sprint6.md`, `docs/plan_ejecucion_PS_sprint6.md`, `docs/plan_borradores_para_MR_y_BF_sprint6.md` |

🤖 Generado con [Claude Code](https://claude.com/claude-code)
