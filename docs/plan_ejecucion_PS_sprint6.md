# Plan de ejecución de PS: cierre del Sprint 5 y Sprint 6

**Elaborado por:** Paolo Sepúlveda (PS) con apoyo de Claude Code (uso autorizado por la universidad), 22 de octubre de 2026.
**Complementa a:** `docs/plan_accion_PS_sprint6.md` (qué pide el Sprint 6 y qué se adelantó). Este documento dice **qué se puede hacer ya, qué está bloqueado y por quién**, en qué orden, y qué hay que correr en Colab.

> Estado de este documento: **plan armado, sin ejecutar**. Se ejecuta cuando PS dé la orden.

## 1. Punto de partida (verificado el 22 de octubre)

| Hecho | Detalle |
|---|---|
| `main` | Último merge: PR #41 (21 oct, Mauricio): conversión a CLP del REPORTE de ABIDES y decisión de unidades **resuelta por MR**. |
| Sprint 5 de PS (T3, T4 y T5) | **Sin mergear.** Rama `feature/ps-sprint5-final-v2` (T3 meta-órdenes, T4 benchmarks, T5 entrenamiento con 1.000 episodios, opción A, diagnóstico y repetición de 100 episodios). |
| Sprint 6 adelantado | **Sin mergear.** Rama `feature/ps-sprint6-adelanto-3-1-4` (monitoreo, comparador sistema vs benchmarks, `--pct-dia-cierre`, plan). Se apoya en la rama del Sprint 5. |
| Informe y presentación | Rama `feature/ps-informe-titulo2-sprint4-v2` (Word, generador y PPT). Presentación del 22 oct: realizada. |
| Decisiones de BF | **Sin respuesta registrada:** D1 (tamaño de las meta-órdenes) y D3 (R_E, opción 0 o A). Rigen las reglas por defecto. |
| Código de MR | `PPOTrainer` solo trae `train_executor_episodes`: **no hay bucle de entrenamiento del Maestro**. |
| Evidencia nueva sobre D3 | Con la opción 0 y argmax el cumplimiento fue 0,000 (1.000 episodios), 1,000 (100 episodios, corrida reanudada) y 0,904 (repetición sin cortes): la regla de vigilancia **no es estable**; con la opción A, 1,000 en la única corrida. |

## 2. Clasificación de tareas

**Leyenda:** 🟢 desbloqueada (PS puede hacerla ya) · 🟡 parcial (parte sí, parte necesita a alguien) · 🔴 bloqueada (depende de otra persona o de un resultado que aún no existe).

### Bloque A: cierre del Sprint 5 (viernes 23)

| ID | Tarea | Estado | Depende de | Esfuerzo | Entregable |
|---|---|:---:|---|---|---|
| A1 | Abrir y mergear los PR en este orden: (1) Sprint 5 `final-v2`, (2) Sprint 6 adelanto, (3) informe v2, (4) esta rama (plan, bitácora, guía de gráficos) | 🟢 | PS (abre el PR); quien revisa mergea | 30 min | `main` con todo lo anterior |
| A2 | `docs/sprint5_que_se_hizo.md` (vence el viernes 23) | 🟢 | Nada. Lo pendiente de BF queda marcado "rige la regla por defecto" | 1,5 h | Documento de cierre del Sprint 5 |
| A3 | Memo de decisión D3 con evidencia (`docs/decision_RE_final_D3_para_BF.md`) | 🟡 | Redacción: nada. Evidencia ampliada: C1 (semillas de red) | 1 h | Memo con tabla de corridas, recomendación de PS y costo de pasar a la A |
| A4 | Decisión D3 (opción 0 u opción A) y D1 (tamaño de las órdenes) | 🔴 | **BF** | — | Respuesta de BF en el grupo |
| A5 | Revisión final de R_E (viernes 23, con los tres) | 🔴 | **BF** (decide); MR y PS opinan | 30 min de reunión | Acta breve |

### Bloque B: 3.1.4 Monitoreo y registro de métricas (tarea de PS en el Sprint 6)

| ID | Tarea | Estado | Depende de | Esfuerzo | Colab |
|---|---|:---:|---|---|---|
| B1 | Validar el monitoreo por episodio con ABIDES real (hasta ahora solo se probó con Poisson) | 🟢 | Nada | 20 min | ≈ 7 min (**C-1**) |
| B2 | Informe automático por corrida y resumen JSON para la Sprint Review | 🟢 | Nada | 1,5 h | — |
| B3 | Calibrar los umbrales de las alertas con las corridas reales | 🟢 | B1 | 1 h | — |
| B4 | Que las corridas de MR y BF escriban el monitoreo (dos líneas, ya documentadas) | 🟡 | Aviso y acuerdo de **MR** | 30 min | — |
| B5 | Monitoreo del Maestro (R_M, α y ventana elegidos, inventario por decisión) durante el **entrenamiento** | 🔴 | **MR**: falta el bucle de entrenamiento del Maestro en `PPOTrainer` | 3 h | Después |

### Bloque C: evidencia para la decisión D3

| ID | Tarea | Estado | Depende de | Esfuerzo | Colab |
|---|---|:---:|---|---|---|
| C1 | 5 semillas de red × {opción 0, opción A} con 100 episodios (10 corridas) para medir la estabilidad de la regla de cumplimiento | 🟢 | Nada | 30 min de preparación | ≈ 70 min en un cuaderno, ≈ 35 min en dos (**C-2**) |
| C2 | Análisis de C1 y actualización del memo A3 | 🟢 | C1 | 1,5 h | — |

### Bloque D: preparación del Sprint 7 (tareas 3.2.3 y 3.2.4, de PS)

| ID | Tarea | Estado | Depende de | Esfuerzo | Colab |
|---|---|:---:|---|---|---|
| D1 | Evaluador del sistema: corre `MaestroEjecutorEnv` con las redes sobre las 10 meta-órdenes (con un DataFrame que parte en el tramo de cada orden) y deja los resultados en el mismo formato que los benchmarks (`estrategia = "PPO"`) | 🟢 | Nada (código de MR ya en `main`) | 3–4 h | — |
| D2 | Corrida con las **redes sin entrenar** sobre las 10 meta-órdenes (valida el flujo completo y da un primer punto de comparación) | 🟢 | D1 | 30 min | ≈ 80 min (**C-3**) |
| D3 | Comparación estadística de esa corrida frente a TWAP y VWAP (prueba el script `comparar_sistema_vs_benchmarks.py` con datos reales) | 🟢 | D2 | 30 min | — |
| D4 | Comparación con el sistema **entrenado** | 🔴 | **MR/BF**: entrenamiento completo (Sprints 5–6) y tamaño oficial de las órdenes (D1) | — | — |

### Bloque E: meta-órdenes (decisión D1)

| ID | Tarea | Estado | Depende de | Esfuerzo | Colab |
|---|---|:---:|---|---|---|
| E1 | Archivo candidato `meta_ordenes_v2.json` (10 % del día en apertura y media jornada, 5 % en el cierre) y su resultado de benchmarks **ensamblado con las corridas ya hechas** (10 % con 2 semillas y 5 % de cierre con 2 semillas; mismas semillas de órdenes) | 🟢 | Nada | 1,5 h | No |
| E2 | Archivo oficial de meta-órdenes | 🔴 | **BF** (D1) | — | — |
| E3 | Si BF elige otro tamaño: repetir los benchmarks | 🔴 | **BF** | 30 min | ≈ 65 min por semilla (**C-4**) |

### Bloque F: apoyo a MR y BF (solo con su consentimiento)

| ID | Tarea | Estado | Depende de | Esfuerzo | Colab |
|---|---|:---:|---|---|---|
| F1 | Nota técnica para MR: el checkpoint no guarda el estado aleatorio, por eso reanudar cambia los resultados (evidencia: corrida de 100 episodios reanudada desde el episodio 30) | 🟡 | La nota: nada. El parche en `ppo_trainer.py` es código de MR: **consentimiento de MR** | 45 min (nota) | — |
| F2 | Hiperparámetros por línea de comandos en el script de entrenamiento (tasa de aprendizaje, clipping, épocas, minibatch, entropía) para que cada corrida del ajuste quede comparable en el panel | 🟡 | **Consentimiento de MR** (3.1.1 y 3.1.2 son suyas) | 1 h | — |
| F3 | Corridas del barrido de hiperparámetros | 🔴 | **MR** define la rejilla | — | Por definir |
| F4 | Si D3 = opción A: recalcular β∗ y repetir la fase 2 de β | 🔴 | **BF** decide; es trabajo pesado | 2 h | Varias horas (**C-5**) |

### Bloque G: documentación (permanente)

| ID | Tarea | Estado | Depende de | Esfuerzo |
|---|---|:---:|---|---|
| G1 | Esqueleto de `docs/sprint6_que_se_hizo.md` (3.1.5, se completa el 6 de noviembre) | 🟢 | Nada | 45 min |
| G2 | Actualizar el informe de Título II con el Sprint 5 (capítulos 5 a 9 y anexos) una vez mergeados los PR | 🟢 | A1 | 3–4 h |
| G3 | Una entrada en `docs/bitacora_cambios_PS.md` por cada PR y, si hay gráficos, su explicación en `docs/guia_graficos.md` | 🟢 | Nada | 15 min por PR |

## 3. Qué está bloqueado, por qué y qué rige mientras tanto

| Bloqueo | Responsable | Qué rige por defecto |
|---|---|---|
| D1: tamaño de las meta-órdenes | BF | Las 10 órdenes de 100.000 acciones (`meta_ordenes_v1.json`). La propuesta de PS (10 % del día y 5 % en el cierre) queda documentada como candidata. |
| D3: R_E, opción 0 u opción A | BF | Opción 0 con regla de vigilancia (decisión del 14 de octubre). La evidencia nueva se entrega en el memo A3 para que BF decida. |
| Entrenamiento del Maestro | MR | Sin él no hay monitoreo ni evaluación significativa del Maestro. |
| Barrido de hiperparámetros | MR | Se usan los valores iniciales (tasa de aprendizaje 3 × 10⁻⁴, clip 0,2, 4 épocas, minibatch 64). |
| Entrenamiento completo del sistema | MR y BF | Se prepara el evaluador (D1) y se prueba con redes sin entrenar (D2). |

## 4. Orden de ejecución

**Viernes 23 de octubre (cierre del Sprint 5)**

1. A1: abrir y mergear los PR en el orden indicado.
2. B1 (Colab, 7 min) y C1 (Colab, 35 a 70 min): se lanzan al principio del día y corren mientras se escribe.
3. A2: `docs/sprint5_que_se_hizo.md`.
4. E1: archivo candidato v2 y benchmarks combinados.
5. C2 y A3: memo D3 con las 10 corridas.
6. A5: reunión de cierre; si BF no responde, se deja constancia de las reglas por defecto en el acta.

**Lunes 26 de octubre (reunión de arranque del Sprint 6)**

7. Presentar este plan y pedir consentimiento a MR para F1, F2 y B4; a BF, respuesta de D1 y D3.
8. D1 (evaluador del sistema) y B2 (informe automático por corrida).

**Semana 1 (27 a 30 de octubre)**

9. D2 (Colab, 80 min) y D3.
10. B3: umbrales de las alertas con corridas reales.
11. B4, F1 y F2 si MR consintió.
12. G2: informe de Título II con el Sprint 5.

**Semana 2 (2 a 6 de noviembre)**

13. Panel de comparación de las corridas del ajuste de MR; entrega a MR y BF.
14. G1: completar `docs/sprint6_que_se_hizo.md` (viernes 6, Sprint Review 3.1.5).
15. Si BF decidió D3 = opción A: F4.

## 5. Consentimientos que hay que pedir

| A quién | Qué | Para qué tarea |
|---|---|---|
| MR | Dos líneas en sus corridas para registrar el monitoreo por episodio | B4 |
| MR | Parche para guardar el estado aleatorio en los checkpoints | F1 |
| MR | Hiperparámetros por línea de comandos en el script de entrenamiento | F2 |
| BF | Respuesta a D1 y D3 | A4, E2, F4 |

Nada de esto se hace sin su consentimiento: son partes de su sprint.

## 6. Qué hacer en Colab cuando el plan esté ejecutado

Las celdas completas y numeradas se entregan **al terminar la ejecución del plan**, porque dependen de scripts que todavía no existen (el evaluador) o que se ajustarán (el monitoreo). La lista de lo que hay que correr y traer de vuelta:

| # | Qué correr | Para qué | Tiempo | Qué traer al PC |
|---|---|---|---|---|
| **C-1** | Entrenamiento de 100 episodios (apertura) con el monitoreo activado | Validar B1 con ABIDES real | ≈ 7 min | `monitoreo_episodios.csv`, `entrenamiento_apertura.csv`, `entrenamiento_inicial_apertura.json` |
| **C-2** | 5 semillas de red × {opción 0, opción A}, 100 episodios cada una | Medir la estabilidad de la regla de D3 (C1) | ≈ 70 min en un cuaderno; ≈ 35 min en dos | Un JSON y un CSV por corrida (10 de cada) |
| **C-3** | Evaluador del sistema con las redes sin entrenar sobre las 10 meta-órdenes | D2: validar el flujo y obtener el primer punto de comparación | ≈ 80 min | `sistema_meta_ordenes_abides.json` |
| **C-4** (condicional) | Benchmarks con el tamaño que decida BF | E3 | ≈ 65 min por semilla | `benchmarks_meta_ordenes_abides.json` |
| **C-5** (condicional) | β∗ y fase 2 de β con la opción A | F4 | Varias horas; se estima al decidir | JSON de β∗ y de la fase 2 |

- **Cuadernos:** Colab gratuito permite dos sesiones a la vez; C-2 se reparte entre ambas.
- **Preparación de cada cuaderno:** las mismas celdas 1 a 8 de siempre (condacolab, entorno de ABIDES, dependencias, ABIDES, verificación, torch, repositorio y Drive), más `seaborn` para los benchmarks.
- **Orden recomendado:** C-1 primero (confirma que el monitoreo funciona), luego C-2 y C-3 en paralelo.
- **Archivos por Escritorio:** como antes, se renombran con un sufijo que indique la corrida para que no se pisen.

## 7. Riesgos

| Riesgo | Efecto | Qué se hace |
|---|---|---|
| BF no responde D1 y D3 | Bloques A4, E2, E3 y F4 sin decisión | Regir los valores por defecto y declararlo en el acta; el memo A3 deja la evidencia lista |
| MR no consiente F1, F2 o B4 | El monitoreo queda en las corridas de PS | El panel funciona con solo el CSV del entrenador y el JSON de estado |
| Colab se desconecta durante C-2 o C-3 | Corridas incompletas | Los scripts son reanudables; la reanudación de **entrenamientos** cambia los resultados (hallazgo F1), por lo que C-2 se reinicia desde cero si se corta una corrida a la mitad |
| Los PR del Sprint 5 y 6 se mergean en otro orden | Conflictos en `entrenamiento_inicial_ps.py` | Orden de A1; si hay conflicto, se resuelve a favor de la versión más nueva y se registra en la bitácora |

🤖 Generado con [Claude Code](https://claude.com/claude-code)
