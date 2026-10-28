# Propuesta de cambio en el entrenamiento del Ejecutor (BORRADOR de PS para BF y MR)

**Elaborado por:** PS con apoyo de Claude Code (uso autorizado por la universidad), 25 de octubre de 2026. **Para:** BF (recompensa R_E, tarea 2.2.3) y MR (entrenador PPO, tarea 2.3.2). Es una propuesta para que la revisen, la modifiquen o la rechacen: **no se tocó ningún archivo de sus tareas**. Todo está en un envoltorio de pruebas.

## 1. Para qué
Con la recompensa actual, las redes entrenadas con 1.000 episodios cuestan más que una red sin entrenar muestreando (+3 bps, 0 de 6 redes mejores). Aviso: esa comparación usó 15 semillas de evaluación y con 40 cambia de signo; en ABIDES el cambio mantiene el cumplimiento y su efecto en el costo está por confirmarse (sección 6). El diagnóstico está en `docs/diagnostico_recompensa_PS.md` y las pruebas de arreglo en `docs/experimentos_recompensa_PS.md`.

## 2. Qué se propone (dos cambios pequeños)

| # | Cambio | Dónde está hoy | Valor propuesto |
|---|---|---|---|
| 1 | **Penalización terminal** por cada acción del slice que queda sin comprar al terminar la ventana | R_E (2.2.3, BF) | 30 bps del precio de llegada, por acción pendiente / q_slice (≈ 17 CLP por acción pendiente con el precio de FALABELLA) |
| 2 | **Factor de descuento del Ejecutor γ = 1** | `PPOConfig` (2.3.2, MR); hoy 0,95 para el Ejecutor | 1,0 |

**Por qué los dos:** sin el primero, esperar da la recompensa máxima (cero); sin el segundo, la penalización que llega al final de la ventana se ve desde el comienzo multiplicada por 0,23 y no alcanza. En las pruebas, cada cambio por separado no funciona (0 de 5 redes buenas) y juntos funcionan en 5 de 5.

## 3. Evidencia (simulador de Poisson, 5 semillas de red, 1.000 episodios, 50 semillas de evaluación)

| | Slippage (bps) | Cumplimiento voluntario | Redes buenas |
|---|---:|---:|---:|
| Recompensa actual (γ = 0,95) | 21,48 | 0,05 | 0 de 5 |
| Penalización de 30 bps, γ = 0,95 | 21,24 | 0,14 | 0 de 5 |
| **Penalización de 30 bps, γ = 1** | **17,92** | 0,99 | **5 de 5** |
| Mejor heurística (TWAP con órdenes límite) | 17,91 | 0,98 | — |
| Red inicial sin entrenar | 20,26 | 1,00 | — |

## 4. Cómo se aplica sin modificar su código

- `src/experiments/variantes_recompensa.py`: envoltorio `EntornoVariante`; la penalización solo lee el `info` del entorno y funciona con Poisson y con ABIDES.
- `scripts/colab/entrenamiento_inicial_ps.py`: nuevas opciones `--gamma 1.0` y `--penalizacion-bps 30`. Sin ellas el script se comporta como antes.
- La evaluación sigue usando el entorno original, así que el slippage y el cumplimiento que se informan se pueden comparar con las corridas anteriores.

Si deciden adoptarlo, lo correcto es llevar la penalización a la recompensa del entorno (2.2.3) y cambiar el `gamma` del Ejecutor en `PPOConfig` (2.3.2), y anotar en `DESVIACIONES_TITULO1_VS_IMPLEMENTACION.md` que γ_E pasa de 0,95 (Título I) a 1,0 con esta justificación.

## 5. Lo que no se recomienda (probado y sin ganancia)
Tamaños y ventanas aleatorios en el entrenamiento, hiperparámetros alternativos, arranque por imitación y costo de espera denso de 100 bps: ninguno mejora la base con este presupuesto de 1.000 episodios.

## 6. Riesgos y límites
- En el simulador de Poisson (sin impacto de precio ni tendencia) funciona. **En ABIDES (26 de octubre, 4 semillas de 1.000 episodios) evita que la red se quede esperando (cumplimiento ≈ 1,0). El efecto en el costo no está resuelto:** con 15 semillas de evaluación las redes parecían costar +3,0 bps más que la red sin entrenar, y con 40 semillas cuestan 2,2 bps menos (no significativo), porque el ruido del precio entre semillas es mucho mayor que la diferencia entre estrategias. **Con 300 semillas (`docs/reeval_300_resultado_PS.md`) la diferencia con el control es de −0,08 bps (IC 95 % de −0,98 a +0,77): el cambio hace que el Ejecutor complete la orden, pero no baja el costo de forma medible.** Es una razón para adoptarlo por cumplimiento, no por costo.
- La penalización de 30 bps es relativa al costo típico de comprar; con otro activo o spread habría que revisarla. Con 100 bps también funcionó.
- γ = 1 se aparta del Título I; hay que declararlo.
- El Ejecutor se entrenó solo; falta el Maestro.

## 7. Qué se les pide
- **BF:** revisar la penalización en R_E y decidir si entra en 2.2.3.
- **MR:** revisar el cambio de γ y, de aceptarlo, aplicarlo al entrenador. También, el bucle de entrenamiento del Maestro (pendiente) para evaluar el sistema completo con estos Ejecutores.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
