# Sprint 6 (26 oct – 6 nov 2026): qué se hizo

Documento de cierre del Sprint 6 (tarea 3.1.5, Sprint Review). **Esqueleto** elaborado por PS con apoyo de Claude Code (uso autorizado por la universidad) el 23 de octubre de 2026, con lo que ya existe en el repositorio. Se completa el viernes 6 de noviembre; cada fila debe ser confirmada por su responsable (columna "Confirma"). Lo que sigue en blanco o con "por completar" **no se ha hecho**.

Estados (los mismos que en `docs/sprint5_que_se_hizo.md`): **Hecho** · **Hecho con límite demostrado** · **Pasa al Sprint 7 por diseño** · **Por completar** (aún no hay resultado).

> **Condición de cierre:** una tarea queda cerrada cuando su código está en `main` mediante un PR mergeado.
> Las filas del Sprint 6 del Excel del plan vienen vacías; las tareas salen de `ESPECIFICACION_DETALLADA_TAREAS.md` y se confirman en la reunión de arranque del 26 de octubre.

## Tareas del sprint

| Tarea | Responsable | Estado | Qué hay hasta hoy | PR | Confirma |
|---|---|---|---|---|---|
| **3.1.1** Ajuste de tasa de aprendizaje, tamaño de lote y épocas del PPO | MR | Por completar | Valores iniciales: tasa 3 × 10⁻⁴, 4 épocas, minibatch 64. Rejilla del ajuste: por definir por MR | — | MR |
| **3.1.2** Ajuste del clipping ε y del GAE λ | MR | Por completar | Valores iniciales: ε = 0,2, λ de GAE = 0,95. Rejilla: por definir por MR | — | MR |
| **3.1.3** Corridas de evaluación por escenario de liquidez | BF | Por completar | — | — | BF |
| **3.1.4** Monitoreo y registro de métricas de entrenamiento | PS | Por completar (código adelantado) | Monitor por episodio (`src/training/monitoreo.py`), panel con alertas y resumen JSON (`scripts/monitorear_entrenamiento.py`; `docs/monitoreo_entrenamiento.md`). **Falta:** validar con ABIDES real (C-1), calibrar umbrales con corridas reales y que las corridas de MR y BF lo escriban | `feature/ps-sprint6-adelanto-3-1-4` y la rama de ejecución (sin mergear) | PS |
| **3.1.5** Sprint Review | Los tres | Por completar | Este documento | — | Los tres |
| **P10** Revalidar λ del Maestro | MR | Por completar | Depende del bucle de entrenamiento del Maestro, que aún no existe en `PPOTrainer` | — | MR |

## Adelantos de PS que apoyan el sprint (no son tareas del Excel)

| Qué | Para qué | Dónde | Estado |
|---|---|---|---|
| Comparación estadística del sistema contra TWAP y VWAP | Adelanto de 3.2.3 y 3.2.4 (Sprint 7) | `scripts/comparar_sistema_vs_benchmarks.py` | Listo y probado con datos sintéticos |
| Evaluador del sistema completo (Maestro + 3 Ejecutores) sobre las 10 meta-órdenes | Dejar el resultado en el formato de los benchmarks (`estrategia = "PPO"`) | `scripts/colab/evaluar_sistema_ps.py` | Listo y probado con Poisson; falta correrlo con ABIDES y redes sin entrenar (C-3) |
| Estabilidad de la regla de vigilancia de D3 con 5 semillas de red | Evidencia para la decisión de BF | `scripts/colab/d3_estabilidad_ps.py`, `scripts/analizar_estabilidad_D3.py` | Listo y probado con Poisson; falta correrlo en Colab (C-2) |
| Archivo candidato `meta_ordenes_v2_candidata.json` con benchmarks ensamblados | Dejar lista la opción de D1 (10 % del día y 5 % en el cierre) sin repetir corridas | `docs/benchmarks_2.3.4_v2_PS.md`, `scripts/ensamblar_benchmarks_meta_ordenes.py` | Hecho (10 de 10 órdenes ejecutables; MO-10 en el borde) |
| Memo de decisión D3 | Que BF decida con la evidencia a la vista | `docs/decision_RE_final_D3_para_BF.md` | Redactado; se amplía con C-2 |

## Resultados clave

_Por completar el 6 de noviembre._ Candidatos, según lo que llegue:

- Cumplimiento de la regla de D3 en 5 semillas de red por opción (C-2).
- Primer punto de comparación del sistema sin entrenar frente a TWAP y VWAP (C-3).
- Curvas y alertas de las corridas del ajuste de hiperparámetros de MR, en el panel de monitoreo.

## Decisiones

| Decisión | Quién decide | Estado al 23 de octubre | Regla por defecto |
|---|---|---|---|
| D1: tamaño de las meta-órdenes | BF | Sin respuesta | 100.000 acciones por orden (`meta_ordenes_v1.json`); la propuesta de PS queda como candidata |
| D3: R_E (opción 0 u opción A) | BF | Sin respuesta | Opción 0 con regla de vigilancia; memo con evidencia en `docs/decision_RE_final_D3_para_BF.md` |

## Qué pasa al Sprint 7

_Por completar._ Ya se sabe que dependen de un sistema entrenado: 3.2.1 a 3.2.4 (corridas y comparación final contra TWAP y VWAP).

## Dónde está cada cosa

| Qué | Dónde |
|---|---|
| Bitácora de cada PR (qué se hizo en el PC, por qué y quién) | `docs/bitacora_cambios_PS.md` |
| Explicación de cada gráfico | `docs/guia_graficos.md` |
| Plan de PS para el sprint y qué está bloqueado | `docs/plan_accion_PS_sprint6.md`, `docs/plan_ejecucion_PS_sprint6.md` |
| Cierre del Sprint 5 | `docs/sprint5_que_se_hizo.md` |

🤖 Generado con [Claude Code](https://claude.com/claude-code)
