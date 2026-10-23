# Estabilidad de la regla de vigilancia de D3: varias semillas de red

**Elaborado por:** PS con apoyo de Claude Code (uso autorizado por la universidad). **Pendiente de revisión por:** BF (decide D3) y MR. **Fecha:** 2026-10-23.

Mismo entrenamiento inicial de la 2.3.5 (100 episodios, apertura, FALABELLA, evaluación con 15 semillas nuevas) repetido con varias semillas de red por opción de R_E. La regla fijada el 14 de octubre se dispara si el cumplimiento con argmax es menor a 95 %.

## 1. Resultado por corrida

| Opción | Semilla de red | Cumplimiento argmax | Cumplimiento muestreada | Cumplimiento sin entrenar | Slippage argmax (bps) | Slippage muestreada (bps) | Slippage sin entrenar (bps) | ¿Dispara la regla? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| 0 | 1000 | 0,904 | 1,000 | 1,000 | 2,04 | 2,71 | 6,02 | sí |
| 0 | 2000 | 0,996 | 1,000 | 0,000 | 5,03 | 2,42 | — | no |
| 0 | 3000 | 0,960 | 1,000 | 0,998 | 6,30 | 3,06 | 5,77 | no |
| 0 | 4000 | 0,646 | 1,000 | 0,893 | 0,31 | 1,82 | 6,79 | sí |
| 0 | 6000 | 0,988 | 1,000 | 1,000 | 5,86 | 2,47 | 5,86 | no |
| A | 1000 | 1,000 | 1,000 | 1,000 | 6,14 | 2,83 | 6,02 | no |
| A | 2000 | 0,115 | 1,000 | 0,000 | -0,20 | 2,77 | — | sí |
| A | 3000 | 0,993 | 1,000 | 0,998 | 2,67 | 2,53 | 5,77 | no |
| A | 4000 | 1,000 | 1,000 | 0,893 | 5,63 | 2,45 | 6,79 | no |
| A | 6000 | 1,000 | 1,000 | 1,000 | 5,34 | 2,29 | 5,86 | no |

## 2. Resumen por opción

| Opción | Redes | Disparan la regla | Cumplimiento argmax (media / mínimo) | Cumplimiento muestreada (media) | Slippage argmax medio (bps) | Slippage muestreada media (bps) |
|---|---:|---:|---:|---:|---:|---:|
| Opción 0 (riesgo sobre lo ejecutado) | 5 | **2 de 5** | 0,899 / 0,646 | 1,000 | 3,91 | 2,50 |
| Opción A (riesgo sobre lo pendiente) | 5 | **1 de 5** | 0,821 / 0,115 | 1,000 | 3,92 | 2,58 |

Comparación de cuántas redes disparan la regla en cada opción (prueba exacta de Fisher): p = 1,000. Con pocas redes por opción es una guía, no una prueba concluyente.

## 3. ¿La red entrenada cuesta menos que la sin entrenar?

Wilcoxon pareado por semilla de evaluación (misma semilla, red entrenada frente a red sin entrenar); se omiten las corridas sin ejecuciones.

| Opción | Semilla de red | p con argmax | p muestreada |
|---|---:|---:|---:|
| 0 | 1000 | 0,359 | 0,720 |
| 0 | 2000 | — | — |
| 0 | 3000 | 0,890 | 0,330 |
| 0 | 4000 | 0,791 | 0,277 |
| 0 | 6000 | 0,720 | 0,421 |
| A | 1000 | 0,489 | 0,720 |
| A | 2000 | — | — |
| A | 3000 | 0,151 | 0,277 |
| A | 4000 | 0,720 | 0,277 |
| A | 6000 | 0,489 | 0,252 |

## 4. Cómo leerlo

- Opción 0: la regla se dispara en 2 de 5 redes; opción A: en 1 de 5.
- Resultado mixto: la regla se dispara en algunas redes y en otras no; la decisión de D3 queda con BF y conviene mirar las semillas que disparan.
- El cumplimiento mide si la red ejecuta toda la orden; el costo (slippage) se compara con la red sin entrenar, que sirve de control.
- Una red que elige "esperar" con argmax pero ejecuta al muestrearla no es lo mismo que una que no ejecuta nunca: por eso se informan ambas evaluaciones.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
