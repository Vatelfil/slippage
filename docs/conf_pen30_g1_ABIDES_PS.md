# Estabilidad de la regla de vigilancia de D3: varias semillas de red

**Elaborado por:** PS con apoyo de Claude Code (uso autorizado por la universidad). **Pendiente de revisión por:** BF (decide D3) y MR. **Fecha:** 2026-10-25.

Mismo entrenamiento inicial de la 2.3.5 (1000 episodios, apertura, FALABELLA, evaluación con 15 semillas nuevas) repetido con varias semillas de red por opción de R_E. La regla fijada el 14 de octubre se dispara si el cumplimiento con argmax es menor a 95 %.

## 1. Resultado por corrida

| Opción | Semilla de red | Cumplimiento argmax | Cumplimiento muestreada | Cumplimiento sin entrenar | Slippage argmax (bps) | Slippage muestreada (bps) | Slippage sin entrenar (bps) | ¿Dispara la regla? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| 0 | 1000 | 1,000 | 1,000 | 1,000 | 7,16 | 6,47 | 11,04 | no |
| 0 | 2000 | 0,000 | 0,999 | 0,000 | — | 6,71 | — | sí |
| 0 | 3000 | 1,002 | 1,000 | 0,999 | 7,89 | 5,32 | 7,12 | no |
| 0 | 4000 | 0,929 | 1,001 | 0,907 | 7,25 | 6,89 | 6,18 | sí |

Política al final del entrenamiento: entropía (100 % = uniforme sobre las 240 acciones) y fracción de pasos en espera (promedio de los primeros 100 y de los últimos 100 episodios).

| Opción | Semilla de red | Episodios | Entropía final | Pasos en espera: primeros 100 → últimos 100 |
|---|---:|---:|---:|---|
| 0 | 1000 | 1000 | 85,4 % | 34 % → 28 % |
| 0 | 2000 | 1000 | 86,5 % | 30 % → 40 % |
| 0 | 3000 | 1000 | 79,7 % | 31 % → 20 % |
| 0 | 4000 | 1000 | 82,7 % | 29 % → 40 % |

## 2. Resumen por opción

| Opción | Redes | Disparan la regla | Cumplimiento argmax (media / mínimo) | Cumplimiento muestreada (media) | Slippage argmax medio (bps) | Slippage muestreada media (bps) |
|---|---:|---:|---:|---:|---:|---:|
| Opción 0 (riesgo sobre lo ejecutado) | 4 | **2 de 4** | 0,733 / 0,000 | 1,000 | 7,43 | 6,35 |

## 3. ¿La red entrenada cuesta menos que la sin entrenar?

Wilcoxon pareado por semilla de evaluación (misma semilla, red entrenada frente a red sin entrenar); se omiten las corridas sin ejecuciones.

| Opción | Semilla de red | p con argmax | p muestreada |
|---|---:|---:|---:|
| 0 | 1000 | 0,868 | 0,460 |
| 0 | 2000 | — | — |
| 0 | 3000 | 0,452 | 0,053 |
| 0 | 4000 | 0,259 | 0,581 |

### Control justo: la red sin entrenar también muestreando la política

La comparación anterior pone la red entrenada muestreando frente a la red sin entrenar con argmax. Aquí ambas muestrean (`scripts/colab/control_muestreado_ps.py`), en las mismas semillas de evaluación.

| Opción | Semilla de red | Slippage entrenada muestreada (bps) | Slippage sin entrenar muestreada (bps) | Diferencia (bps) | p (Wilcoxon pareado) |
|---|---:|---:|---:|---:|---:|
| 0 | 1000 | 5,17 | 3,00 | 2,17 | 0,421 |
| 0 | 2000 | 5,27 | 2,99 | 2,28 | 0,454 |
| 0 | 3000 | 5,26 | 2,64 | 2,62 | 0,489 |
| 0 | 4000 | 7,96 | 2,94 | 5,02 | 0,055 |

En 0 de 4 redes la entrenada muestreando cuesta menos que la inicial muestreando (diferencia media 3,02 bps; prueba de signos entre redes, p = 0,125). Las redes comparten el diseño de la recompensa y el entorno, así que la prueba de signos es una guía y no una prueba independiente.

## 4. Cómo leerlo

- El cumplimiento mide si la red ejecuta toda la orden; el costo (slippage) se compara con la red sin entrenar, que sirve de control.
- Una red que elige "esperar" con argmax pero ejecuta al muestrearla no es lo mismo que una que no ejecuta nunca: por eso se informan ambas evaluaciones.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
