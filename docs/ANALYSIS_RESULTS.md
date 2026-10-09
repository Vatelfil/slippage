# Análisis Sprint 4 — Resultados de Convergencia

**Tarea:** 3.1.5 — Análisis de Convergencia
**Autor:** Paolo Sepúlveda Parraguez (PS)
**Fecha:** _(completar al momento de redactar, con datos reales)_
**Run analizado:** `logs/<RUN_ID>/metrics.csv` — _(reemplazar RUN_ID)_

> **Plantilla.** Este documento se completa con `notebooks/Analysis_Sprint4.ipynb`
> corriendo sobre un `metrics.csv` **real** (no el sintético de prueba). Cada
> sección indica qué celda del notebook produce el número o gráfico a pegar aquí.
> No reemplazar los placeholders `_(pendiente)_` con datos sintéticos.

---

## 0. Resumen ejecutivo

_(2-3 frases: ¿convergió el entrenamiento? ¿hubo señales de inestabilidad?
¿está listo para Sprint 5 o requiere reajuste de hiperparámetros?)_

_(pendiente)_

---

## 1. Convergencia de Retornos

**Fuente:** `analyzer.plot_returns()` — notebook, sección 5.

![Convergencia de returns](logs/<RUN_ID>/plot_returns.png)

**Lectura del Maestro:**
- ¿El return promedio (media móvil) muestra tendencia ascendente sostenida, ascenso-y-plateau, u oscilación sin tendencia clara?
- ¿En qué rango de timesteps se estabiliza (si lo hace)?

_(pendiente)_

**Lectura de los Ejecutores (Apertura / Media jornada / Cierre):**
- ¿Convergen los 3 de forma independiente, como se esperaba por el paralelismo de la arquitectura (Título I, sección 4.2)?
- ¿Alguno diverge o se mantiene plano (posible señal de falta de exploración)?

_(pendiente)_

---

## 2. Pérdidas del Maestro (Policy / Value / Entropy)

**Fuente:** `analyzer.plot_losses()` — notebook, sección 6.

![Losses del Maestro](logs/<RUN_ID>/plot_losses.png)

- **Policy loss:** ¿se mantiene acotada (sin explosiones), consistente con el clipping PPO (ε ∈ [0.1, 0.2])?
- **Value loss:** ¿decrece o se estabiliza? Un value loss que no baja sugiere que el crítico no está aprendiendo un buen baseline para GAE.
- **Entropy:** se espera que **decrezca** con el entrenamiento (la política se vuelve menos aleatoria / más determinista). Una entropía que no baja indica que el agente no está convergiendo hacia una estrategia clara; una que cae demasiado rápido puede indicar colapso prematuro de exploración.

_(pendiente)_

---

## 3. Estabilidad del Entrenamiento

**Fuente:** `analyzer.compute_stability()` — notebook, sección 7.

| Bloque (step inicial) | std(maestro_return) |
|---|---|
| _(pendiente)_ | _(pendiente)_ |

**Conclusión:** ¿la desviación estándar por bloques decrece con el entrenamiento (más estable) o se mantiene/aumenta (inestabilidad persistente, posible necesidad de ajustar `learning_rate` o `clip_ratio` en Sprint 5, tarea 3.1.1 en adelante o recalibración en fases posteriores)?

_(pendiente)_

---

## 4. Comparación vs. Benchmark

**Fuente:** `analyzer.compute_improvement_factor()` — notebook, sección 8.

⚠️ **Nota importante:** esta sección solo tiene validez una vez que Benjamin entregue los benchmarks TWAP/VWAP reales (Sprint 5, tarea 2.3.4). Mientras `BASELINE_RETURN` sea un placeholder (0.0), el "improvement factor" reportado aquí **no debe citarse como resultado de tesis**.

| Métrica | Valor |
|---|---|
| Return final del Maestro | _(pendiente)_ |
| Return benchmark (TWAP/VWAP) | _(pendiente — requiere Sprint 5)_ |
| Improvement factor | _(pendiente)_ |

_(pendiente)_

---

## 5. Test Estadístico de Tendencia

**Fuente:** `analyzer.statistical_test()` — notebook, sección 9.

| Métrica | Valor |
|---|---|
| Slope | _(pendiente)_ |
| R² | _(pendiente)_ |
| P-value | _(pendiente)_ |
| ¿Significativo (α=0.05)? | _(pendiente)_ |

**Interpretación:** una pendiente positiva y significativa (`p < 0.05`) es evidencia de que el return del Maestro mejora con el entrenamiento. La ausencia de significancia **no** implica ausencia de aprendizaje — puede haber alcanzado un plateau (revisar sección 1) o la relación puede no ser lineal.

_(pendiente)_

---

## 6. Interpretabilidad (si aplica en este run)

_(Opcional para esta iteración — requiere logs de acciones, no solo de retornos/losses.
Si `executor_states.csv` / `maestro_actions.csv` (ver `docs/arquitectura_entorno_simulacion.md`,
sección 5) están disponibles, completar:)_

- ¿Cuándo decide el Maestro fracciones altas de `alpha_t` (> 0.30–0.35, la mitad superior de `{0.05,...,0.50}`)? ¿Correlaciona con `volatilidad` o `sesion` altas?
- ¿Qué `tipo_orden` prefieren los Ejecutores por tramo (Apertura/Media/Cierre)?

_(pendiente)_

---

## 7. Conclusiones

_(pendiente — completar tras revisar las secciones 1-5)_

---

## 8. Recomendaciones para Sprint 5

_(pendiente — ejemplos de qué tipo de recomendación va aquí, ajustar según hallazgos reales:)_
- Si la entropía no decreció: revisar `entropy_coef` en `config` (actualmente `0.01`).
- Si el value loss no bajó: revisar arquitectura del crítico o `value_coef` (actualmente `0.5`).
- Si hubo inestabilidad (sección 3): considerar reducir `learning_rate` (actualmente `3e-4`) o `clip_ratio` (actualmente `0.2`).
- Validar contra datos out-of-sample (no usados en este entrenamiento) antes de reportar el improvement factor final en la tesis.

---

## Referencias

- `src/analysis/convergence_analysis.py` — implementación de `ConvergenceAnalyzer`.
- `notebooks/Analysis_Sprint4.ipynb` — notebook que generó los gráficos y métricas de este documento.
- `notebooks/Training_PPO_Sprint4_PS.ipynb`, sección 8 — origen de `metrics.csv` (`log_metrics()`).
- `docs/arquitectura_entorno_simulacion.md` — contrato de S_M/S_E y protocolo Maestro↔Ejecutor (Sprint 2, tarea 1.2.5).
- `PLAN_SPRINT4_PS.md` — plan detallado de la tarea 3.1.5 y sus criterios de éxito.
