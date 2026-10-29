# Sprint 6 (26 oct – 6 nov 2026): qué se hizo

> **Nota del 29 de octubre (revisión):** los entrenamientos en ABIDES de este documento usaron una recompensa del Ejecutor que compara el precio pagado con el precio medio de 30 segundos *después* de la compra, no con el de la decisión (falla H1 de `docs/revision_opus_PS.md`). Esa recompensa casi no se relaciona con el costo, así que lo que aquí se concluye sobre si el entrenamiento mejora el costo no debe usarse para decidir. El slippage medido, el cumplimiento y los benchmarks sí son válidos: no dependen de la recompensa.

Documento de cierre del Sprint 6 (tarea 3.1.5, Sprint Review). **Borrador en curso** elaborado por PS con apoyo de Claude Code (uso autorizado por la universidad); última actualización: 26 de octubre de 2026. Se completa el viernes 6 de noviembre; cada fila debe ser confirmada por su responsable (columna "Confirma"). Lo que sigue como "Por completar" **no se ha hecho**.

Estados (los mismos que en `docs/sprint5_que_se_hizo.md`): **Hecho** · **Hecho con límite demostrado** · **Pasa al Sprint 7 por diseño** · **Por completar** (aún no hay resultado).

> **Condición de cierre:** una tarea queda cerrada cuando su código está en `main` mediante un PR mergeado.
> Las filas del Sprint 6 del Excel del plan vienen vacías; las tareas salen de `ESPECIFICACION_DETALLADA_TAREAS.md` y se confirman en la reunión de arranque del 26 de octubre.

## Tareas del sprint

| Tarea | Responsable | Estado | Qué hay hasta hoy | PR | Confirma |
|---|---|---|---|---|---|
| **3.1.1** Ajuste de tasa de aprendizaje, tamaño de lote y épocas del PPO | MR | Por completar | Valores iniciales: tasa 3 × 10⁻⁴, 4 épocas, minibatch 64. **Punto de partida nuevo:** con el factor de descuento γ = 1 y una penalización por lo no comprado, el entrenamiento del Ejecutor pasa de empeorar el costo a igualar a la mejor heurística (ver «Resultados clave»); el ajuste conviene hacerlo sobre esa base. Rejilla: por definir por MR | — | MR |
| **3.1.2** Ajuste del clipping ε y del GAE λ | MR | Por completar | Valores iniciales: ε = 0,2, λ de GAE = 0,95 | — | MR |
| **3.1.3** Corridas de evaluación por escenario de liquidez | BF | Por completar | El evaluador por escenario y la sensibilidad (3.2.4) están listos para recibir los escenarios; falta la definición de los tres niveles de liquidez | — | BF |
| **3.1.4** Monitoreo y registro de métricas de entrenamiento | PS | Hecho con límite | Monitor por episodio validado con ABIDES real (100 y 1.000 episodios), panel con curvas de varias corridas, **alertas calibradas con 27 corridas reales** (`docs/calibracion_monitoreo_PS.md`), alerta nueva «la recompensa sube y el costo no», línea de costo de partida y guía de alertas. **Límite:** falta integrarlo en las corridas del ajuste de MR (dos líneas, que requieren su visto bueno) | PR `feature/ps-sprint6-completo` (sin mergear) | PS |
| **3.1.5** Sprint Review | Los tres | Por completar | Este documento | — | Los tres |
| **P10** Revalidar λ del Maestro | MR | Por completar | Depende del bucle de entrenamiento del Maestro, que aún no existe en `PPOTrainer` | — | MR |

## Adelantos de PS que apoyan el sprint (no son tareas del Excel)

| Qué | Para qué | Dónde | Estado |
|---|---|---|---|
| Diagnóstico y arreglo del entrenamiento del Ejecutor | Saber por qué las redes entrenadas costaban más que la red sin entrenar | `docs/diagnostico_recompensa_PS.md`, `docs/experimentos_recompensa_PS.md`, `docs/investigacion_recompensa_que_se_hizo.md` | Hecho. En Poisson el arreglo baja el costo; **en ABIDES (300 semillas) hace que la red complete la orden pero no baja el costo** (`docs/reeval_300_resultado_PS.md`) |
| Propuesta de cambio de R_E y de γ para BF y MR | Que revisen el arreglo (la penalización va a R_E, γ al entrenador) | `docs/propuesta_cambio_RE_para_BF_y_MR.md` | Borrador, pendiente de su revisión |
| Estabilidad de D3 con 100 y 1.000 episodios y control muestreado | Evidencia para la decisión de BF | `docs/estabilidad_D3_PS.md`, `docs/estabilidad_D3_1000ep_PS.md`, `docs/decision_RE_final_D3_para_BF.md` | Hecho |
| Evaluador del sistema completo sobre las 10 meta-órdenes | Primer punto de comparación con TWAP y VWAP | `scripts/colab/evaluar_sistema_ps.py`, `docs/c3_sistema_sin_entrenar_PS.md` | Hecho con redes sin entrenar (semilla de red fija) |
| Comparación contra TWAP y VWAP con **costo ajustado por lo no ejecutado** | Que un sistema que compra poco no parezca barato | `scripts/comparar_sistema_vs_benchmarks.py` (opción `--penalizaciones-no-ejecutado`) | Listo y probado; la penalización a usar es una decisión del equipo |
| Sensibilidad por tamaño, tramo y liquidez (3.2.4, Sprint 7) | Ver dónde gana o pierde el sistema y si el efecto crece con el tamaño | `scripts/analizar_sensibilidad_3_2_4.py` | Listo y probado con datos sintéticos; se corre cuando existan las 90 corridas |
| Archivo candidato de meta-órdenes `v2` con benchmarks ensamblados | Dejar lista la opción de D1 sin repetir corridas | `docs/benchmarks_2.3.4_v2_PS.md` | Hecho (10 de 10 órdenes ejecutables) |

## Resultados clave

- **El entrenamiento del Ejecutor no bajaba el costo y la causa está identificada.** Con la recompensa actual, la red aprende a esperar (97 % a 99 % de los pasos): nada obliga a completar la orden, y el descuento γ = 0,95 hace que un costo al final de la ventana se vea cuatro veces más barato. Con una **penalización de 30 bps por acción sin comprar y γ = 1**, 5 de 5 redes cumplen la orden y llegan al costo de la mejor heurística (17,9 frente a 17,91 bps; la red inicial, 20,3), en el simulador de Poisson. Cada cambio por separado no funciona.
- **Control justo:** una política casi uniforme ya cumple la orden. Con 15 semillas de evaluación parecía que las 6 redes de 1.000 episodios costaban más que ese control (+3,08 bps); **con 300 semillas ninguna red entrenada se distingue de su control** (diferencias de −0,6 a +1,0 bps, todos los intervalos con el 0). Los números de 15 y 40 semillas eran ruido del precio.
- **Reevaluación con 300 semillas (ABIDES, FALABELLA, apertura):** las 8 redes juntas cuestan −0,08 bps respecto de su control (IC 95 % de −0,98 a +0,77); la penalización más γ = 1 (V2) y la recompensa contra el precio de llegada (V4) no se distinguen entre sí; redes y control cuestan ≈ 2 bps más que TWAP límite. Entrenar 1.000 episodios no cambió el costo de forma medible (`docs/reeval_300_resultado_PS.md`).
- **Regla de vigilancia de D3** (cumplimiento con argmax < 95 %): se dispara en 1 de 3 redes de 1.000 episodios con la opción 0 y en 0 de 3 con la A; con 100 episodios no distingue las opciones.
- **Evaluador del sistema completo (redes sin entrenar):** cumple el 66,3 % de las órdenes (apertura 94,6 %, media jornada 76,3 %, cierre 18,5 %) y no se distingue de TWAP en costo; con una penalización de 300 bps por lo no comprado es claramente peor, así que la conclusión depende de cómo se valore lo no ejecutado.
- **Monitoreo:** las alertas se calibraron con corridas buenas y malas. La alerta nueva avisa en 7 de 10 corridas malas y en ninguna buena; la entropía baja, que daba falsas alarmas, quedó como aviso informativo.

## Decisiones

| Decisión | Quién decide | Estado al 26 de octubre | Regla por defecto |
|---|---|---|---|
| D1: tamaño de las meta-órdenes | BF | Sin respuesta | 100.000 acciones por orden (`meta_ordenes_v1.json`); la propuesta de PS queda como candidata |
| D3: R_E (opción 0 u opción A) | BF | Sin respuesta | Opción 0 con regla de vigilancia. Propuesta de PS: «D3: A» por robustez del cumplimiento, sin recalcular β∗ hasta tener entrenamientos que bajen el costo (`docs/decision_RE_final_D3_para_BF.md`, secciones 7 a 9) |
| Penalización por lo no comprado en R_E y γ = 1 en el Ejecutor | BF (R_E) y MR (entrenador) | Propuesta enviada (borrador) | Sin cambios hasta que la revisen y se confirme en ABIDES |
| Valor de la penalización por lo no ejecutado en la comparación final | Los tres | Por definir | Se informan varios valores (50, 100 y 300 bps) |

## Qué pasa al Sprint 7

3.2.1 a 3.2.4 dependen de un sistema entrenado. **Ya están listos** (y probados con datos de ejemplo): la comparación contra TWAP y VWAP (3.2.3), el costo ajustado por lo no ejecutado y la sensibilidad por tamaño, tramo y liquidez (3.2.4). Falta el entrenamiento del Maestro (bucle de MR) y los escenarios de liquidez (BF).

## Qué toca revisar a MR y a BF (propuesta, nada de esto está ejecutado)

El detalle, con tiempos y valores por defecto, está en `docs/plan_dejar_listo_MR_y_BF_PS.md`. PS no modificó ningún archivo de sus tareas; lo que sigue son documentos para leer y decidir.

| Para | Qué hay que mirar | Dónde | Tiempo estimado |
|---|---|---|---|
| MR | Propuesta de γ = 1 en el entrenador del Ejecutor (y declararlo como desviación del Título I) | `docs/propuesta_cambio_RE_para_BF_y_MR.md` | 30 min |
| MR | Visto bueno para conectar el monitoreo en sus corridas (dos líneas) | `docs/guia_alertas_monitoreo_PS.md` | 15 min |
| MR | Plan de lo que PS puede dejar escrito para el bucle de entrenamiento del Maestro, el barrido de hiperparámetros y la revalidación de λ (decidir cuáles quiere) | `docs/plan_dejar_listo_MR_y_BF_PS.md`, sección 4 | 30 min |
| BF | Decisión D3 (R_E opción 0 u opción A) con la evidencia y la regla por defecto | `docs/decision_RE_final_D3_para_BF.md` | 30 min |
| BF | Decisión D1 (tamaño de las meta-órdenes) con la regla por defecto | `docs/meta_ordenes_2.3.3.md`, `docs/benchmarks_2.3.4_v2_PS.md` | 20 min |
| BF | Penalización por lo no comprado en R_E | `docs/propuesta_cambio_RE_para_BF_y_MR.md` | 30 min |
| BF | Definir los tres niveles de liquidez (lo que desbloquea 3.1.3 y las 90 corridas) y qué se prepara de antemano | `docs/plan_dejar_listo_MR_y_BF_PS.md`, sección 5 | 30 min |
| Los tres | Valor de la penalización por lo no ejecutado en la comparación final; cómo redactar la hipótesis del 10 % dado que 90 corridas solo detectan ≈ 20 bps | `docs/plan_dejar_listo_MR_y_BF_PS.md`, secciones 6 y 7 | reunión |

## Dónde está cada cosa

| Qué | Dónde |
|---|---|
| Informe del Sprint 6 de PS para futura redacción del Título II | `docs/informe_sprint6_PS.md` |
| Plan para que MR y BF solo lleguen, ejecuten y revisen | `docs/plan_dejar_listo_MR_y_BF_PS.md` |
| Resultado con 300 semillas | `docs/reeval_300_resultado_PS.md` |
| Bitácora de cada PR (qué se hizo en el PC, por qué y quién) | `docs/bitacora_cambios_PS.md` |
| Explicación de cada gráfico | `docs/guia_graficos.md` |
| Qué significa cada alerta del monitoreo y qué hacer | `docs/guia_alertas_monitoreo_PS.md` |
| Plan de PS para el sprint y qué está bloqueado | `docs/plan_accion_PS_sprint6.md`, `docs/plan_ejecucion_PS_sprint6.md` |
| Cierre del Sprint 5 | `docs/sprint5_que_se_hizo.md` |

## Confirmación en ABIDES de la penalización terminal (26 de octubre)
- Las 4 redes entrenadas con penalización de 30 bps y γ = 1 en ABIDES cumplen la orden (cumplimiento ≈ 1,0). Su costo frente a la red sin entrenar fue +3,0 bps con 15 semillas de evaluación y −2,2 bps con 40 (no significativo); **con 300 semillas la diferencia es nula** (`docs/reeval_300_resultado_PS.md`). Detalle en `docs/v4_abides_resultado_parcial_A_PS.md` y `docs/confirmacion_abides_penalizacion_resultado_PS.md`; datos en `data/colab_resultados/conf_pen30_g1/`.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
