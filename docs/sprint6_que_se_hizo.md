# Sprint 6 (26 oct – 6 nov 2026): qué se hizo

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
| **3.1.4** Monitoreo y registro de métricas de entrenamiento | PS | Hecho con límite | Monitor por episodio validado con ABIDES real (100 y 1.000 episodios), panel con curvas de varias corridas, **alertas calibradas con 27 corridas reales** (`docs/calibracion_monitoreo_PS.md`), alerta nueva «la recompensa sube y el costo no», línea de costo de partida y guía de alertas. **Límite:** falta integrarlo en las corridas del ajuste de MR (dos líneas, que requieren su visto bueno) | rama `feature/ps-sprint6-monitoreo-sensibilidad` (sin mergear) | PS |
| **3.1.5** Sprint Review | Los tres | Por completar | Este documento | — | Los tres |
| **P10** Revalidar λ del Maestro | MR | Por completar | Depende del bucle de entrenamiento del Maestro, que aún no existe en `PPOTrainer` | — | MR |

## Adelantos de PS que apoyan el sprint (no son tareas del Excel)

| Qué | Para qué | Dónde | Estado |
|---|---|---|---|
| Diagnóstico y arreglo del entrenamiento del Ejecutor | Saber por qué las redes entrenadas costaban más que la red sin entrenar | `docs/diagnostico_recompensa_PS.md`, `docs/experimentos_recompensa_PS.md`, `docs/investigacion_recompensa_que_se_hizo.md` | Hecho en Poisson; **falta confirmar en ABIDES** (cuadernos de Colab listos) |
| Propuesta de cambio de R_E y de γ para BF y MR | Que revisen el arreglo (la penalización va a R_E, γ al entrenador) | `docs/propuesta_cambio_RE_para_BF_y_MR.md` | Borrador, pendiente de su revisión |
| Estabilidad de D3 con 100 y 1.000 episodios y control muestreado | Evidencia para la decisión de BF | `docs/estabilidad_D3_PS.md`, `docs/estabilidad_D3_1000ep_PS.md`, `docs/decision_RE_final_D3_para_BF.md` | Hecho |
| Evaluador del sistema completo sobre las 10 meta-órdenes | Primer punto de comparación con TWAP y VWAP | `scripts/colab/evaluar_sistema_ps.py`, `docs/c3_sistema_sin_entrenar_PS.md` | Hecho con redes sin entrenar (semilla de red fija) |
| Comparación contra TWAP y VWAP con **costo ajustado por lo no ejecutado** | Que un sistema que compra poco no parezca barato | `scripts/comparar_sistema_vs_benchmarks.py` (opción `--penalizaciones-no-ejecutado`) | Listo y probado; la penalización a usar es una decisión del equipo |
| Sensibilidad por tamaño, tramo y liquidez (3.2.4, Sprint 7) | Ver dónde gana o pierde el sistema y si el efecto crece con el tamaño | `scripts/analizar_sensibilidad_3_2_4.py` | Listo y probado con datos sintéticos; se corre cuando existan las 90 corridas |
| Archivo candidato de meta-órdenes `v2` con benchmarks ensamblados | Dejar lista la opción de D1 sin repetir corridas | `docs/benchmarks_2.3.4_v2_PS.md` | Hecho (10 de 10 órdenes ejecutables) |

## Resultados clave

- **El entrenamiento del Ejecutor no bajaba el costo y la causa está identificada.** Con la recompensa actual, la red aprende a esperar (97 % a 99 % de los pasos): nada obliga a completar la orden, y el descuento γ = 0,95 hace que un costo al final de la ventana se vea cuatro veces más barato. Con una **penalización de 30 bps por acción sin comprar y γ = 1**, 5 de 5 redes cumplen la orden y llegan al costo de la mejor heurística (17,9 frente a 17,91 bps; la red inicial, 20,3), en el simulador de Poisson. Cada cambio por separado no funciona.
- **Control justo:** una política casi uniforme ya cumple la orden y cuesta ≈ 3 bps en ABIDES. Con 1.000 episodios y la recompensa actual, las 6 redes cuestan más que ese control (+3,08 bps de media).
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

## Dónde está cada cosa

| Qué | Dónde |
|---|---|
| Bitácora de cada PR (qué se hizo en el PC, por qué y quién) | `docs/bitacora_cambios_PS.md` |
| Explicación de cada gráfico | `docs/guia_graficos.md` |
| Qué significa cada alerta del monitoreo y qué hacer | `docs/guia_alertas_monitoreo_PS.md` |
| Plan de PS para el sprint y qué está bloqueado | `docs/plan_accion_PS_sprint6.md`, `docs/plan_ejecucion_PS_sprint6.md` |
| Cierre del Sprint 5 | `docs/sprint5_que_se_hizo.md` |

## Confirmación en ABIDES de la penalización terminal (26 de octubre)
- Las 4 redes entrenadas con penalización de 30 bps y γ = 1 en ABIDES cumplen la orden (cumplimiento ≈ 1,0) pero cuestan +3,0 bps sobre la red sin entrenar muestreando (0 de 4 mejores). El cambio evita el colapso a esperar, no reduce el costo. Detalle y próximos pasos en `docs/confirmacion_abides_penalizacion_resultado_PS.md`; datos en `data/colab_resultados/conf_pen30_g1/`.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
