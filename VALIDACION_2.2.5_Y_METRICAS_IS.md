# Validación Estadística Preliminar (2.2.5, parcial) + Métricas de Ejecución

**Autor:** Paolo Sepúlveda (PS) — 23 septiembre 2026
**Tareas que adelanta:** 2.2.5 (parcial — solo el lado "datos reales") y deja lista la función de Implementation Shortfall que necesitarán las tareas 3.2.3 (comparación PPO vs TWAP/VWAP) y 3.1.2/3.1.3 (validación de episodios).

---

## 1. Validación estadística — lado "datos reales" (tarea 2.2.5)

La tarea 2.2.5 completa (según el plan) es **comparar el simulador contra los datos históricos reales** (spread, OBI, perfil de volumen). Como ABIDES-Gym todavía no está integrado (ver `DIAGNOSTICO_Y_PLAN_23SEP.md`), esto solo cubre el lado "datos históricos reales" — la comparación de verdad queda pendiente para cuando exista el simulador.

**Fuente:** `src/analysis/market_validation.py`, corrido sobre los datos reales que descargué ayer (30 tickers IPSA, 60 días, `data/processed/clean_5m_2026-09-23/`).

### Resultado (perfil intradiario real del IPSA)

| Tramo | Spread relativo (%) | Volatilidad (std log-return) | Volumen promedio |
|---|---|---|---|
| Apertura (09:30–11:00) | 0.138% | 0.00251 | 396,765 |
| Media jornada (11:00–14:00) | 0.112% | 0.00156 | 456,967 |
| Cierre (14:00–16:00) | 0.128% | 0.00151 | 698,419 |

Ver gráfico: `data/analysis/perfil_mercado_ipsa_real.png`.

### ⚠️ Hallazgo honesto — no ocultar esto

El **Título I (sección 4.1.1)** planteaba la hipótesis de que la media jornada tendría **spreads más amplios** (menor liquidez) y que la actividad se concentraría en apertura y cierre. Lo que muestran estos datos reales es distinto:

- El **spread relativo es más ancho en la apertura** (0.138%), no en la media jornada (que de hecho es el tramo con spread *más angosto*, 0.112%).
- La **volatilidad sí decrece** de apertura a cierre, consistente con la intuición general de mercados (apertura más volátil), pero **no muestra el "rebote" en el cierre** que suele describirse en la literatura clásica de microestructura.
- El **volumen crece monótonamente** hacia el cierre, en vez del patrón de "U" (alto-bajo-alto) esperado.

**No fuerzo estos datos para que calcen con la hipótesis del Título I.** Puede deberse a: (a) que esta muestra son solo 60 días con datos de 5 minutos agregados (no tick-by-tick), (b) que el proxy de spread (high−low de la vela) es una aproximación gruesa, no el spread bid-ask real, o (c) que el IPSA en este período específico simplemente no siguiera el patrón típico de mercados más grandes. Esto es información real que el equipo debería anotar en el capítulo de resultados — si se mantiene con más datos o con el spread real de ABIDES-Gym, podría ser un hallazgo genuino de la tesis, no un error de cálculo.

**Actualización 27 sept — confirmado independientemente por Benjamín.** Su calibración Poisson por tramo (`docs/calibracion_poisson_2.1.3_BF.md`, sección 5.3, con datos de un snapshot distinto y metodología mucho más rigurosa: proxy de Roll además de high-low, winsorización, 30 tickers) llega a la **misma conclusión**: el spread real del IPSA es mayor en apertura y decrece hacia el cierre ("forma de L"), no la "U" esperada por el Título I. Dos análisis independientes coincidiendo es una señal fuerte de que es un hallazgo real del IPSA en este período, no un artefacto de esta implementación. **Su documento es la referencia autoritativa** para este hallazgo (mucho más detallado); este documento queda como la primera detección, más simple.

**OBI (Order Book Imbalance) no se pudo calcular** — requiere el libro de órdenes Nivel 2, que solo existe una vez que ABIDES-Gym esté integrado. No hay un proxy razonable desde datos OHLCV agregados, así que no se inventó uno.

### Actualización 29 sept — ya se puede completar la comparación real (falta correrla)

Ahora que ABIDES-Gym está conectado al Ejecutor (verificado, ver `INTEGRACION_ABIDES_PARA_MAURICIO.md`), la mitad que faltaba de la tarea 2.2.5 — comparar el simulador contra los datos reales — ya es técnicamente posible. Dejé todo el código listo y probado con datos sintéticos, pero **no lo pude correr con ABIDES real** porque no lo tengo instalado en este entorno (solo corre en Colab):

1. `src/envs/collect_abides_stats.py` — corre varios episodios del Ejecutor contra ABIDES real (los 3 tramos) y guarda `data/analysis/perfil_mercado_abides_simulado.json` con spread/OBI simulados. Se corre así, en Colab:
   ```bash
   PYTHONPATH=. python src/envs/collect_abides_stats.py
   ```
2. `compare_simulated_vs_real()` (nuevo, en `src/analysis/market_validation.py`) — compara ese JSON contra los datos reales ya caracterizados arriba. **Probada con datos sintéticos** (round-trip verificado), lista para usar con el resultado real del paso 1.

⚠️ **Limitación real, no maquillable:** `rmsc04` (la configuración de ABIDES) todavía no está calibrada con parámetros del IPSA (tarea 2.2.4, pendiente de Benjamín) — simula genéricamente, no el spread/tick real de un papel chileno. Por eso la comparación es de **forma** (¿el spread es más ancho en el mismo tramo en ambos lados?), no de magnitud absoluta, hasta que 2.2.4 esté lista. Repetir esta comparación después de esa calibración.

**Para cerrar la tarea de verdad:** correr el paso 1 en Colab, pasarme el JSON resultante (o los números), y termino el análisis con datos reales del simulador — en vez de la comparación sintética que valida solo el mecanismo.

### Actualización 3 oct — tarea 2.2.5 cerrada con datos reales del simulador

Paolo corrió `collect_abides_stats.py` en Colab (30 episodios, ABIDES-Gym real, `rmsc04` sin calibrar) y se ejecutó `compare_simulated_vs_real()` con el resultado real (`data/analysis/perfil_mercado_abides_simulado.json`).

| Tramo | Spread real (%, high-low proxy) | Spread simulado (normalizado, ABIDES real) | OBI simulado |
|---|---|---|---|
| Apertura (09:30–11:00) | 0.138% | 0.00193 | -0.035 |
| Media jornada (11:00–14:00) | 0.112% | 0.00082 | 0.102 |
| Cierre (14:00–16:00) | 0.128% | 0.00081 | 0.081 |

- **Orden real** (spread, menor→mayor): media jornada → cierre → apertura.
- **Orden simulado** (spread, menor→mayor): cierre → media jornada → apertura.
- **`forma_coincide = False`** — la forma del spread simulado (por ABIDES-Gym con `rmsc04` genérico) **no** replica la forma real del IPSA (la "L" descrita en la sección 1).

**Hallazgo honesto, esperado y no maquillado:** esto no es un bug — es exactamente la limitación anotada arriba: `rmsc04` todavía simula un mercado genérico (agentes de ruido/valor/momentum sin calibrar a ningún activo real), no al IPSA. No hay ninguna razón para que su forma coincida con la del mercado chileno hasta que la tarea 2.2.4 (calibración de `rmsc04` con parámetros reales, base dejada en `src/envs/calibrate_rmsc04_ipsa.py`) esté completa. **Recomendación para el capítulo de resultados del Título II:** presentar esta comparación como la línea base *pre-calibración* (spread simulado sin forma real) y, si el tiempo lo permite, repetirla *post-calibración* (2.2.4) para mostrar la mejora — es un antes/después más fuerte para la tesis que un solo número aislado.

Con esto, la tarea 2.2.5 queda **completa** (ambos lados: datos reales y datos simulados, comparados).

---

## 2. Métricas de ejecución — Implementation Shortfall (métrica principal de la tesis)

**Fuente:** `src/analysis/execution_metrics.py`.

Implementé y **verifiqué contra el propio ejemplo numérico del `Contexto_Agente_Programacion.md`** (sección 2): comprar 8.000 acciones a un precio de referencia de 5.800 CLP, ejecutando en promedio a 5.808 CLP → `IS_total = 64.000 CLP`. La función reproduce exactamente ese número.

Funciones disponibles:

| Función | Qué calcula |
|---|---|
| `implementation_shortfall(result)` | `IS_total = (P_ejec_promedio − P_referencia) × Q_total` |
| `slippage_bps(result)` | Slippage relativo en basis points (comparable entre activos de distinto precio) |
| `pct_cumplimiento(result)` | Fracción de la meta-orden ejecutada |
| `evaluate_episode(...)` | Las 3 anteriores juntas, en el formato de `episode_summary.json` |
| `compare_strategies(is_ppo, is_benchmark)` | Test estadístico (t-test de Welch o Mann-Whitney U, elegido automáticamente según normalidad vía Shapiro-Wilk) para la tarea 3.2.3 — compara si el sistema PPO reduce el IS respecto a TWAP/VWAP de forma significativa, y si cumple la hipótesis de reducción ≥10% |

**Probado con datos sintéticos de ejemplo**, no con corridas reales — porque el entrenamiento real todavía no existe (depende de ABIDES-Gym). Cuando exista, `compare_strategies()` ya está lista para recibir las 90 corridas de evaluación (Sprint 7, tarea 3.2.1: 3 escenarios de liquidez × 3 tamaños × 10 semillas) sin tener que escribirla desde cero bajo presión de tiempo.

---

## Archivos generados

- `src/analysis/market_validation.py` — caracterización del mercado real
- `src/analysis/execution_metrics.py` — Implementation Shortfall + comparación estadística
- `data/analysis/perfil_mercado_ipsa_real.png` + `.json` — resultado de la validación (sí se versionan: son un resumen pequeño, no los datos crudos, que siguen fuera de git en `data/raw/`/`data/processed/`)

## Nota de reconciliación (27 sept)

Mi script `scripts/run_poisson_calibration_real.py` (calibración Poisson rápida sobre datos reales) quedó **retirado del repo**: Benjamín entregó una calibración muchísima más rigurosa (por ticker × tramo horario, con proxies de Roll y HL, winsorización, MLE-proxy, análisis de sensibilidad — ver `docs/calibracion_poisson_2.1.3_BF.md`). Su archivo, `data/calibration/poisson_params_2026-08-23.json`, es la fuente de verdad para los parámetros Poisson del proyecto, no el mío. Se retira para no dejar dos calibraciones distintas compitiendo en el repo.
