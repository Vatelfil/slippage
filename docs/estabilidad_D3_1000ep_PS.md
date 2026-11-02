# Estabilidad de la regla de vigilancia de D3: varias semillas de red

> **Nota del 29 de octubre (revisión):** los entrenamientos en ABIDES de este documento usaron una recompensa del Ejecutor que compara el precio pagado con el precio medio de 30 segundos *después* de la compra, no con el de la decisión (falla H1 de `docs/revision_opus_PS.md`). Esa recompensa casi no se relaciona con el costo, así que lo que aquí se concluye sobre si el entrenamiento mejora el costo o sobre la opción de D3 no debe usarse para decidir. El slippage medido, el cumplimiento y los benchmarks sí son válidos: no dependen de la recompensa.

**Elaborado por:** PS con apoyo de Claude Code (uso autorizado por la universidad). **Pendiente de revisión por:** BF (decide D3) y MR. **Fecha:** 2026-10-25.

Mismo entrenamiento inicial de la 2.3.5 (1000 episodios, apertura, FALABELLA, evaluación con 15 semillas nuevas) repetido con varias semillas de red por opción de R_E. La regla fijada el 14 de octubre se dispara si el cumplimiento con argmax es menor a 95 %.

## 1. Resultado por corrida

| Opción | Semilla de red | Cumplimiento argmax | Cumplimiento muestreada | Cumplimiento sin entrenar | Slippage argmax (bps) | Slippage muestreada (bps) | Slippage sin entrenar (bps) | ¿Dispara la regla? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| 0 | 1000 | 0,000 | 1,000 | 1,000 | — | 5,43 | 6,02 | sí |
| 0 | 2000 | 1,000 | 1,000 | 0,000 | 6,59 | 6,11 | — | no |
| 0 | 3000 | 0,989 | 1,000 | 0,998 | 4,92 | 8,29 | 5,77 | no |
| A | 1000 | 1,000 | 1,000 | 1,000 | 5,91 | 4,60 | 6,02 | no |
| A | 2000 | 1,000 | 1,000 | 0,000 | 5,58 | 6,55 | — | no |
| A | 3000 | 1,000 | 1,000 | 0,998 | 5,45 | 4,79 | 5,77 | no |

Política al final del entrenamiento: entropía (100 % = uniforme sobre las 240 acciones) y fracción de pasos en espera (promedio de los primeros 100 y de los últimos 100 episodios).

| Opción | Semilla de red | Episodios | Entropía final | Pasos en espera: primeros 100 → últimos 100 |
|---|---:|---:|---:|---|
| 0 | 1000 | 1000 | 80,1 % | — |
| 0 | 2000 | 1000 | 35,3 % | 30 % → 11 % |
| 0 | 3000 | 1000 | 82,4 % | 31 % → 32 % |
| A | 1000 | 1000 | — | — |
| A | 2000 | 1000 | 71,4 % | 30 % → 8 % |
| A | 3000 | 1000 | 38,6 % | 31 % → 6 % |

## 2. Resumen por opción

| Opción | Redes | Disparan la regla | Cumplimiento argmax (media / mínimo) | Cumplimiento muestreada (media) | Slippage argmax medio (bps) | Slippage muestreada media (bps) |
|---|---:|---:|---:|---:|---:|---:|
| Opción 0 (riesgo sobre lo ejecutado) | 3 | **1 de 3** | 0,663 / 0,000 | 1,000 | 5,75 | 6,61 |
| Opción A (riesgo sobre lo pendiente) | 3 | **0 de 3** | 1,000 / 1,000 | 1,000 | 5,65 | 5,31 |

Comparación de cuántas redes disparan la regla en cada opción (prueba exacta de Fisher): p = 1,000. Con pocas redes por opción es una guía, no una prueba concluyente.

## 3. ¿La red entrenada cuesta menos que la sin entrenar?

Wilcoxon pareado por semilla de evaluación (misma semilla, red entrenada frente a red sin entrenar); se omiten las corridas sin ejecuciones.

| Opción | Semilla de red | p con argmax | p muestreada |
|---|---:|---:|---:|
| 0 | 1000 | — | 0,679 |
| 0 | 2000 | — | — |
| 0 | 3000 | 0,421 | 0,679 |
| A | 1000 | 0,524 | 0,804 |
| A | 2000 | — | — |
| A | 3000 | 0,804 | 0,804 |

### Control justo: la red sin entrenar también muestreando la política

La comparación anterior pone la red entrenada muestreando frente a la red sin entrenar con argmax. Aquí ambas muestrean (`scripts/colab/control_muestreado_ps.py`), en las mismas semillas de evaluación.

| Opción | Semilla de red | Slippage entrenada muestreada (bps) | Slippage sin entrenar muestreada (bps) | Diferencia (bps) | p (Wilcoxon pareado) |
|---|---:|---:|---:|---:|---:|
| 0 | 1000 | 5,43 | 3,00 | 2,43 | 0,890 |
| 0 | 2000 | 6,11 | 2,99 | 3,12 | 0,978 |
| 0 | 3000 | 8,29 | 2,64 | 5,65 | 0,421 |
| A | 1000 | 4,60 | 3,00 | 1,59 | 0,978 |
| A | 2000 | 6,55 | 2,99 | 3,56 | 0,073 |
| A | 3000 | 4,79 | 2,64 | 2,15 | 0,561 |

En 0 de 6 redes la entrenada muestreando cuesta menos que la inicial muestreando (diferencia media 3,08 bps; prueba de signos entre redes, p = 0,031). Las redes comparten el diseño de la recompensa y el entorno, así que la prueba de signos es una guía y no una prueba independiente.

> **Nota del 26 de octubre (noche), 300 semillas:** la reevaluación con 300 semillas de evaluación (`docs/reeval_300_resultado_PS.md`) mostró que ninguna de las 8 redes entrenadas cuesta distinto a su control (diferencias de −0,6 a +1,0 bps, todos los intervalos con el 0). Las cifras de 15 y 40 semillas de este documento eran ruido del precio y no deben citarse como evidencia de costo; el cumplimiento y el colapso a esperar no dependen de eso.

## 4. Cómo leerlo

- Opción 0: la regla se dispara en 1 de 3 redes; opción A: en 0 de 3.
- Resultado mixto: la regla se dispara en algunas redes y en otras no; la decisión de D3 queda con BF y conviene mirar las semillas que disparan.
- El cumplimiento mide si la red ejecuta toda la orden; el costo (slippage) se compara con la red sin entrenar, que sirve de control.
- Una red que elige "esperar" con argmax pero ejecuta al muestrearla no es lo mismo que una que no ejecuta nunca: por eso se informan ambas evaluaciones.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
