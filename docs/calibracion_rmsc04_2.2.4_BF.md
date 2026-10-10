# Calibración de RMSC04 con datos del IPSA — Tarea 2.2.4

**Proyecto:** Coordinación de Agentes para la Mitigación del Slippage (IPSA) — Título II, UTEM
**Responsable:** Benjamín Farias (BF). La plantilla inicial de `calibrate_rmsc04_ipsa.py` es de Paolo Sepúlveda (PS).
**Activo:** FALABELLA (MVP), snapshot `2026-08-23`.

> **Estado al 2026-10-09.** Calibración corrida en Colab (ABIDES, Python 3.9) entre el 4 y el 9 de octubre: dos sondeos, grilla de 27 combinaciones × 3 semillas, refinamiento local y validación con **30 semillas** nuevas por tramo. **Resultado:** la volatilidad de 5 min queda dentro de un 10 % del objetivo en los tres tramos. **El KS de los retornos de 5 min rechaza en media jornada y cierre** y queda al borde en apertura; la meta del plan (p > 0,05) no se cumple en dos de tres tramos. La distancia D (0,06–0,10) es menor o igual que la del modelo de Poisson de la 2.1.3b (§8.3). **Limitación principal:** el spread simulado (≈ 0,2 bps) queda 20–100 veces por debajo de los proxies reales y RMSC04 no permite corregirlo sin romper el volumen y la volatilidad (§8.1).

| Qué | Dónde |
|---|---|
| Bloque A: unidades, config base, VR, curtosis | [`src/envs/calibrate_rmsc04_ipsa.py`](../src/envs/calibrate_rmsc04_ipsa.py) |
| Momentos del simulador por tramo | [`src/envs/rmsc04_sim_stats.py`](../src/envs/rmsc04_sim_stats.py) |
| Grilla, pérdida, rankings, KS (lógica pura) | [`src/envs/rmsc04_search.py`](../src/envs/rmsc04_search.py) |
| Scripts de Colab | [`scripts/colab/rmsc04_grid_search.py`](../scripts/colab/rmsc04_grid_search.py), [`scripts/colab/rmsc04_validate.py`](../scripts/colab/rmsc04_validate.py) |
| Antes/después de 2.2.5 | [`src/envs/collect_abides_stats.py`](../src/envs/collect_abides_stats.py) |
| Evidencia del bloque A | [`data/calibration/rmsc04_base_FALABELLA_2026-08-23.json`](../data/calibration/rmsc04_base_FALABELLA_2026-08-23.json) |
| **Config calibrada y validación** | [`data/calibration/rmsc04_ipsa_FALABELLA_2026-08-23.json`](../data/calibration/rmsc04_ipsa_FALABELLA_2026-08-23.json) |
| Grilla, refinamiento y sondeos | `data/calibration/rmsc04_{grid,refine,screen,screen_flujo}_FALABELLA_2026-08-23.json` |
| Antes/después de 2.2.5 | `data/analysis/perfil_mercado_abides_{sin_calibrar_bps,calibrado}.json` |
| Notebook | [`notebooks/Colab_Sprint4_BF.ipynb`](../notebooks/Colab_Sprint4_BF.ipynb) |

---

## 1. Objetivo

RMSC04 es la configuración de referencia de ABIDES-Gym: un mercado de fondo con 1 000 agentes de ruido, 102 agentes de valor, 12 de momentum y 2 creadores de mercado. Sus parámetros por defecto describen una acción genérica de 1 000 USD. La tarea 2.2.4 los ajusta para que el mercado de fondo **aproxime**, mediante calibración con datos reales del IPSA, las magnitudes que la tarea 2.1.3b dejó como objetivos de validación de FALABELLA (`objetivos_validacion["FALABELLA"]` en `poisson_params_2026-08-23.json`): por tramo, volatilidad de 5 min, spread, participación de volumen y volumen por vela, más sus rankings.

Los tramos son los del Ejecutor (`TRAMOS_EJECUTOR`): apertura [09:30, 11:30), media jornada [11:30, 14:00) y cierre [14:00, 16:00]. `market_validation.py` (2.2.5, PS) corta la apertura a las 11:00; esa diferencia se dejó anotada y no se modificó.

| Objetivo (FALABELLA) | Apertura | Media jornada | Cierre |
|---|---:|---:|---:|
| Volatilidad de 5 min (bps) | 33,95 | 22,34 | 20,86 |
| Spread Roll (bps) | 35,26 | 23,83 | 20,59 |
| Spread Corwin-Schultz (bps) | 5,75 | 4,15 | 4,86 |
| Participación en el volumen del día | 0,249 | 0,381 | 0,309 |
| Volumen mediano por vela (acciones) | 7 576 | 9 396 | 11 964 |

## 2. Del modelo de Poisson (2.1.3) a los parámetros de RMSC04

La calibración de Poisson describe **llegadas de órdenes** (λ⁺, λ⁻, θ); RMSC04 describe **agentes** y un valor fundamental. No hay un mapeo uno a uno. La tabla indica qué dato de la 2.1.3 alimenta cada parámetro y cómo.

| Parámetro de RMSC04 | Valor (décimos de CLP) | Fuente y justificación |
|---|---|---|
| `r_bar` | 59 698 | Mediana de `close_raw` del snapshot (5 969,75 CLP) × 10. Es el nivel alrededor del cual se mueve el valor fundamental. |
| `fund_vol` | 3,70e-4 / 2,43e-4 / 2,27e-4 (a / m / c) | `obs_return_std` del tramo (2.1.3) convertido a unidades del oráculo (§3). Una config por tramo. |
| `starting_cash` | 1 000 000 | El default de rmsc04 (100 000 CLP) en la unidad de cuenta. Los agentes de fondo envían órdenes sin control de riesgo, así que no restringe la simulación. |
| `kappa_oracle` | default (1,67e-16) | Test de razón de varianzas (§5): la reversión observada es rebote bid-ask, no reversión del fundamental. |
| `megashock_*` | default | No actúan dentro de la jornada (§6). |
| `mm_window_size`, `mm_level_spacing`, `mm_pov` | búsqueda (§7) | Sin Nivel 2 no hay dato directo de la liquidez del creador de mercado. Se buscan contra los proxies de spread (Roll, Corwin-Schultz). |
| `num_noise_agents`, `lambda_a` | búsqueda (§7) | λ⁺+λ⁻ de la 2.1.3 da el nivel de actividad (≈ 10,5–12,2 órdenes de 167 acciones por paso de 30 s), pero depende del supuesto de tamaño medio de orden. El objetivo que se usa es el volumen por vela, que no depende de ese supuesto. |
| `kappa`, `sigma_s`, `num_value_agents`, `num_momentum_agents`, resto de `mm_*` | default | Sin análogo en datos OHLCV de 5 min. |
| θ (cancelación) | no se usa | RMSC04 no tiene una tasa de cancelación global: el creador de mercado cancela y repone sus órdenes en cada despertar. |

`CAMPOS_PENDIENTES_2_2_4` lista lo que este módulo no fija; `to_abides_kwargs()` entrega el diccionario limpio para `background_config_extra_kvargs`, con todas sus llaves verificadas contra la firma real de `rmsc04.build_config` (commit `f9cbe51` de `abides-jpmc-public`).

**El ticker no se pasa a ABIDES.** ABIDES-Gym crea su agente con el símbolo `"ABM"` fijo (`abides_gym/envs/core_environment.py`). Si la config cambiara el ticker del exchange, el agente operaría un símbolo inexistente. El ticker real queda en `_metadata`.

## 3. `fund_vol`: derivación y el error de unidades (H5)

El oráculo de RMSC04 (`SparseMeanRevertingOracle`) es un proceso de Ornstein-Uhlenbeck. Para avanzar de `pt` a `ts` muestrea

$$
v \sim \mathcal{N}\!\left(\mu + (v_{pt}-\mu)\,e^{-\kappa d},\ \ \frac{\text{fund\_vol}^2}{2\kappa}\left(1-e^{-2\kappa d}\right)\right), \qquad d = ts - pt
$$

y `d` es una diferencia de timestamps de ABIDES, que están en **nanosegundos**. Con κ → 0 la varianza es `fund_vol² · d`, de modo que `fund_vol` está en unidades de precio por √ns.

La plantilla original usaba `fund_vol = σ_5min · r_bar`, que es un desvío en unidades de precio **por vela de 5 min**. Para que el fundamental tenga ese desvío en 5 min (300·10⁹ ns) hay que dividir por la raíz del número de nanosegundos:

$$
\text{fund\_vol} = \frac{\sigma_{5min}\cdot \bar r}{\sqrt{300\cdot 10^{9}}}
$$

El valor de la plantilla quedaba √(300·10⁹) ≈ 547 723 veces más grande. `fund_vol_from_sigma()` usa la inversión exacta de la varianza del OU, que con el `kappa_oracle` por defecto difiere de la fórmula anterior en 2,5·10⁻⁵ en términos relativos.

**Verificación.** `tests/test_calibrate_rmsc04_ipsa.py` simula el oráculo con la misma fórmula del código de ABIDES y comprueba que el desvío a 5 min coincide con `σ_5min · r_bar` (3 % de tolerancia con 20 000 trayectorias).

**Experimento del plan** (30 sept, r_bar del snapshot 09-27, apertura, 09:30–10:30, 1 semilla):

| Configuración | fund_vol | Vol. 5 min del mid (bps) | Spread mediano (bps) | Mid final |
|---|---|---:|---:|---|
| Default rmsc04 | 5e-5 | 0,3 | 0,02 | 6 298 CLP |
| Heurística de la plantilla | 2 139 | 8 044 | 0,01 | 17 194 199 CLP |
| Corregida, centavos | 0,0039 | 22,8–28,5 | 0,14 | 6 184 CLP |
| Corregida, 1 unidad = 1 CLP | 3,9e-5 | 35,9 (real: 34,0) | 1,61 | ≈ 6 200 CLP |

**Repetición en Colab** (4 oct, snapshot 2026-08-23, r_bar = 5 969,75 CLP, apertura, 09:30–10:30, 1 semilla; σ_5min real = 34,0 bps):

| Configuración | fund_vol | Vol. 5 min del mid (bps) | Spread mediano | Mid inicial → final |
|---|---|---:|---|---|
| Default rmsc04 | 5e-5 | 0,4 | 0,02 bps (1 tick) | 596 988 → 596 808 |
| Heurística de la plantilla | 2 030 | 7 944 | — | 16 940 119 → 2 632 899 371 |
| Corregida, centavos | 0,0037 | 23,0 | 0,20 bps (12 ticks) | 597 060 → 585 212 |
| **Corregida, décimos** | 0,00037 | 24,3 | 0,67 bps (4 ticks) | 59 707 → 57 820 |
| Corregida, 1 unidad = 1 CLP | 3,7e-5 | 35,4 | 1,69 bps (1 tick) | 5 968 → 5 870 |

Con la plantilla original el precio explota; con la conversión corregida la volatilidad queda en el orden de magnitud correcto en las tres unidades. La volatilidad de esta celda es una estimación gruesa (una hora, una semilla, velas de 1 min, spread por evento). La medición que vale es la de la validación (§8.3), donde cada tramo corre con su `fund_vol` y 30 semillas: 34,0 / 20,0 / 20,5 bps contra 34,0 / 22,3 / 20,9.

**Limitación.** `fund_vol` es único por simulación. Se usa una configuración por tramo: cada Ejecutor corre su propio episodio y basta con que calce el tramo medido. No es una volatilidad intradiaria variable.

## 4. Unidad de cuenta y tick (H6)

El tick de ABIDES es siempre 1 unidad de cuenta, así que la unidad fija el tick efectivo: `1e4 / r_bar` bps.

En los datos de FALABELLA el incremento mínimo entre precios distintos es **0,1 CLP** en los snapshots 2026-08-23 y 2026-09-27 (≈ 0,17 bps a 5 970 CLP). Esto se midió sobre `close_raw`; no se consultó la tabla de ticks de la Bolsa de Santiago, por lo que es un tick empírico de los datos de yfinance.

| Unidad | `r_bar` | Tick efectivo | Frente al tick observado |
|---|---:|---:|---|
| `centavos` (0,01 CLP) | 596 975 | 0,017 bps | 10 veces más fino |
| **`decimos`** (0,1 CLP) | 59 698 | 0,168 bps | igual |
| `clp` (1 CLP) | 5 970 | 1,675 bps | 10 veces más grueso |

**Decisión (2026-10-03):** `decimos`, por el criterio del plan (que el tick del simulador quede lo más cerca posible del real). La unidad se aplica de forma consistente a `r_bar`, `starting_cash` y `fund_vol`, y `BridgeConfig.unidades_por_clp` convierte los precios de ABIDES a CLP para la recompensa (2.2.3).

**El spread simulado es de pocos ticks en cualquier unidad** (12, 4 y 1 tick en centavos, décimos y CLP; tabla de §3), así que en bps lo determina sobre todo el tamaño del tick. Con 1 CLP el spread sube a 1,7 bps, pero porque queda pegado a un tick 10 veces mayor que el real: elegir la unidad por el spread sería ajustar un artefacto. Se mantuvo `decimos` (decisión del 4 oct, con los dos sondeos a la vista) y el spread se declara como limitación (§8.1).

## 5. Reversión del fundamental: razón de varianzas y `kappa_oracle`

`variance_ratio()` calcula VR(q) de Lo y MacKinlay (1988) con el estadístico z\* robusto a heterocedasticidad. Las autocorrelaciones se estiman con pares de retornos del mismo segmento (velas consecutivas del mismo día y tramo), sin mezclar retornos separados por la noche o por velas sin transacción. La muestra es la misma `n_returns` de la 2.1.3.

| Tramo | n | ρ₁ | VR(2) | VR(6) | VR(12) | z\*(2) / z\*(6) / z\*(12) |
|---|---:|---:|---:|---:|---:|---|
| Apertura | 1 111 | −0,238 | 0,762 | 0,634 | 0,587 | −4,55 / −3,64 / −3,26 |
| Media jornada | 1 690 | −0,267 | 0,733 | 0,593 | 0,588 | −6,39 / −4,58 / −3,38 |
| Cierre | 1 252 | −0,229 | 0,771 | 0,613 | 0,544 | −6,36 / −4,64 / −3,90 |

VR < 1 y es significativa en los tres tramos y los tres horizontes. La regla literal del plan (`kappa_oracle = −ln(φ)/Δt`, con φ = 1 + 2ρ₁) daría una vida media de 4,5–5,7 min.

**Esa regla no se aplicó**, porque la forma de la VR no es la de un fundamental que revierte. Hay dos mecanismos que dan VR < 1 y se distinguen por cómo cae VR con q:

- **Rebote bid-ask** (Roll, 1984): autocorrelación solo de orden 1. VR(q) = 1 + 2(1 − 1/q)ρ₁, que se estabiliza en 1 + 2ρ₁.
- **Reversión OU del nivel:** ρ_j = ρ₁φ^(j−1). VR(q) sigue cayendo hacia 0.

| Tramo | VR(12) observada | VR(12) si es rebote | VR(12) si es OU | Error cuadrático: rebote / OU |
|---|---:|---:|---:|---|
| Apertura | 0,587 | 0,563 | 0,175 | 0,002 / 0,255 |
| Media jornada | 0,588 | 0,510 | 0,156 | 0,008 / 0,267 |
| Cierre | 0,544 | 0,580 | 0,182 | 0,001 / 0,198 |

La VR observada calza con el rebote bid-ask en los tres tramos. Es la misma autocovarianza negativa de la que sale el estimador de Roll (35 / 24 / 21 bps), y el simulador la genera por su propio spread, no por el fundamental.

**Decisión (2026-10-03):** se mantiene `kappa_oracle` por defecto (vida media ≈ 48 días, sin reversión intradiaria). La regla quedó codificada en `decide_kappa_oracle()`: solo adopta el κ de la regla si la reversión es significativa **y** el patrón más cercano es el OU.

## 6. Megashocks y curtosis

`megashock_lambda_a = 2,78·10⁻¹⁸` por ns equivale a un evento cada 11 años en promedio: no actúa dentro de una jornada, así que los megashocks no aportan colas a los retornos de 5 min. Se mantiene el default.

Exceso de curtosis real de los retornos de 5 min (0 = normal):

| Apertura | Media jornada | Cierre |
|---:|---:|---:|
| 5,87 | 5,14 | 3,36 |

Curtosis simulada con la config calibrada: **8,67 / 2,70 / 5,56** con 30 semillas; con las primeras 10 había dado 5,73 / 2,50 / 1,94. El estimador es inestable (en cierre pasa de 1,9 a 5,6 al agregar semillas): depende de unos pocos retornos extremos, así que no permite concluir si las colas simuladas son más livianas o más pesadas que las reales. No se agregaron megashocks a la búsqueda: un megashock de RMSC04 es un salto del fundamental de ≈ 1 000 unidades (≈ 1,7 % del precio en décimos), demasiado grande para ajustar colas de retornos de 5 min.

## 7. Diseño de la búsqueda (método de momentos simulado)

**Momentos por tramo**, medidos en el mercado de fondo sin nuestro agente (`rmsc04_sim_stats.moments_from_l1`), con las mismas velas que los datos reales (23 / 30 / 23 retornos por día; se excluyen la vela 09:30, que no tiene antecesora, y la 15:55, que en los datos reales es la subasta):

- volatilidad de 5 min del mid;
- spread cotizado mediano, ponderado por tiempo;
- participación del tramo en el volumen del día y volumen mediano por vela.

**Grilla (27 = 3 × 3 × 3).** Unidades en décimos: 1 tick = 0,168 bps.

| Factor | Niveles | Por qué |
|---|---|---|
| Liquidez del creador de mercado | `mm_window_size` ∈ {adaptive, 30, 90}; con ventana fija, `mm_level_spacing` = 0,1 | En modo adaptive el creador de mercado cotiza alrededor del spread que observa: lo sigue, no lo fija. Con ventana entera cotiza a mid ± ventana/2. 30 y 90 ticks son ≈ 5 y ≈ 15 bps, entre Corwin-Schultz y Roll. Con ventana fija la separación entre niveles es `ceil(50 · spacing)` ticks: 0,1 → 5 ticks; el default (5) daría 250 ticks. |
| Profundidad | `mm_pov` ∈ {0,005; 0,025; 0,1} | Fracción del volumen del último minuto que se pone en cada nivel. Default al centro, 5× a cada lado. |
| Actividad | (`num_noise_agents`, `lambda_a`) ∈ {(1000; 5,7e-12), (2000; 1,14e-11), (4000; 2,28e-11)} | Escalados juntos ×1, ×2 y ×4. |

Respecto del plan: `mm_spread_alpha` quedó fuera (solo es el peso del promedio móvil del spread en modo adaptive; no mueve su nivel) y `mm_num_ticks` se dejó en el default para no pasar de 27 combinaciones.

**Estos niveles se eligieron leyendo el código de ABIDES, antes de correrlo.** Los sondeos (§8.1) mostraron después que dos de las tres palancas no hacen lo que se esperaba: la ventana del creador de mercado no fija el spread, y el nivel de actividad por defecto ya queda por sobre el volumen objetivo, de modo que ×2 y ×4 se alejan. La grilla se corrió igual tal como estaba definida, para que el resultado saliera del procedimiento fijado de antemano; el script tiene `--screen` (un factor por vez, 1 semilla, solo apertura) y `--grid-spec` para explorar otros niveles sin tocar el código.

**Pérdida.**

$$
L = \sum_{\text{tramo}} \Big[ 1{,}0\,|\ln\tfrac{\sigma_{sim}}{\sigma_{obj}}| + 1{,}0\, d_{spread} + 0{,}5\,|\ln\tfrac{part_{sim}}{part_{obj}}| + 0{,}5\,|\ln\tfrac{V_{sim}}{V_{obj}}| \Big] + 1{,}0 \cdot \#\{\text{rankings robustos fallidos}\}
$$

- `d_spread` es la distancia logarítmica al intervalo [Corwin-Schultz, Roll]: 0 si el spread simulado cae dentro. Los dos son proxies desde OHLCV y Roll sobreestima el spread cotizado, así que el objetivo es un intervalo y no un punto. La tabla final reporta la comparación contra cada uno por separado.
- Rankings robustos (2.1.3b): la volatilidad es máxima en la apertura y el volumen por vela crece de apertura a cierre.
- Un momento simulado ausente o no positivo cuenta como un factor 100.

**Un solo `fund_vol` en la grilla.** La participación de volumen exige simular el día completo con una sola config. La grilla usa el `fund_vol` de la volatilidad del día (25,66 bps) y compara la volatilidad simulada de cada tramo contra esa referencia; para el ranking la reescala por σ_tramo/σ_día. La validación corre cada tramo con su propio `fund_vol`.

**Presupuesto.** 27 × 3 semillas × día completo (H8: ≈ 40 s por día con rmsc04 por defecto; más con actividad ×4). Reanudable: se guarda después de cada simulación.

**Validación** (`rmsc04_validate.py`):

1. toma la mejor configuración de la grilla y, con `--refine`, evalúa hasta 10 vecinos (cada parámetro ×1,5 y ÷1,5, de a uno);
2. corre semillas **nuevas** (101 en adelante, distintas de las de la búsqueda) por tramo, cada uno con su config. Se corrieron 10 y después se amplió a 30;
3. KS de 2 muestras de los retornos de 5 min simulados contra los reales por tramo: D, p, D_crit y D/D_crit con `ks_critical_value`, como en la 2.1.3b. También sobre las muestras estandarizadas, que compara solo la forma;
4. tabla de momentos simulados contra objetivos y rankings.

La participación y el volumen por vela se miden en las corridas del tramo cierre, que son de día completo.

## 8. Resultados

Todo en Colab con ABIDES (`abides-jpmc-public`, commit `f9cbe51`), Python 3.9, unidad décimos.

### 8.1 Sondeos: qué mueve el spread

**Primer sondeo** (apertura, 1 semilla, un factor por vez desde el default; objetivo: spread 5,7–35 bps, volumen por vela 7 576):

| Cambio respecto del default | Spread (bps) | Vol. (bps) | Volumen por vela |
|---|---:|---:|---:|
| ninguno (rmsc04 por defecto) | 0,34 | 25,7 | 11 714 |
| `mm_window_size` = 30 | 0,50 | 14,4 | 20 720 |
| `mm_window_size` = 90 | 0,34 | 36,8 | 10 602 |
| `mm_pov` = 0,005 | 0,34 | 29,3 | 10 538 |
| `mm_pov` = 0,1 | 0,34 | 23,2 | 20 267 |
| actividad ×2 | 0,34 | 27,2 | 17 138 |
| actividad ×4 | 0,17 | 23,6 | 35 986 |

El spread queda en 1–3 ticks con todas las palancas. La ventana fija del creador de mercado no lo fija.

**Segundo sondeo** (apertura, 1 semilla, factorial sobre el flujo de agentes de valor y de ruido):

| Flujo de agentes de valor | Agentes de ruido | Spread (bps) | Vol. (bps) | Volumen por vela |
|---|---:|---:|---:|---:|
| default (102 agentes, λ = 5,7e-12) | 1 000 | 0,34 | 25,7 | 11 714 |
| default | 4 000 | 0,34 | 28,6 | 11 289 |
| ÷4 (25 agentes) | 1 000 | 1,35 | 26,3 | 2 321 |
| ÷10 (λ/10) | 1 000 | 2,51 | 19,9 | 1 476 |
| ÷10 | 4 000 | 1,34 | 31,0 | 3 494 |
| ÷40 | 1 000 | 2,86 | 13,6 | 802 |
| ÷4 | 4 000 | 8,06 | 4 463 | 5 926 |
| ÷40 | 4 000 | 4,37 | 8 085 | 2 912 |

**Lectura.** Los agentes de valor colocan sus órdenes límite alrededor del mejor precio, la mitad dentro del spread, y llegan unas 15 veces más seguido que los agentes de ruido: cierran cualquier spread ancho en segundos. Reducir su flujo abre el spread, pero:

- se satura cerca de 2,5–3 bps, la mitad del piso del objetivo;
- ese mismo flujo es casi todo el volumen (÷4 lo baja 5 veces);
- también es lo que transmite la volatilidad del fundamental al precio (19,9 y 13,6 bps con ÷10 y ÷40);
- las dos filas con spread "dentro del rango" son mercados rotos (volatilidad de miles de bps).

**En RMSC04 el spread, el volumen y la volatilidad dependen de la misma palanca y no se pueden calzar los tres a la vez.** Se decidió calzar volatilidad y volumen y declarar el spread como limitación. Son sondeos de una semilla y un tramo: los niveles son aproximados, el patrón es claro.

### 8.2 Grilla y refinamiento

27 combinaciones × 3 semillas × día completo. Las mejores y algunas de referencia (apertura / media jornada / cierre):

| Pérdida | Rankings fallidos | Config (lo que difiere del default) | Vol. (bps) | Volumen por vela |
|---:|:---:|---|---|---|
| **9,83** | 0 | `mm_pov` = 0,005 | 27,2 / 24,4 / 23,5 | 10 838 / 11 260 / 12 478 |
| 10,10 | 0 | ventana 30, `mm_pov` = 0,005 | 20,8 / 21,9 / 19,0 | 10 909 / 11 130 / 12 252 |
| 10,31 | 0 | ventana 90, `mm_pov` = 0,005 | 22,0 / 19,7 / 20,1 | 10 939 / 11 476 / 12 470 |
| 10,62 | 0 | actividad ×2 | 23,1 / 23,2 / 26,7 | 18 442 / 18 531 / 20 646 |
| 11,77 | 1 | ninguna (rmsc04 por defecto) | 20,2 / 19,4 / 29,7 | 12 504 / 12 149 / 12 950 |
| 12,25 | 0 | actividad ×4, `mm_pov` = 0,005 | 22,5 / 24,4 / 27,1 | 31 155 / 31 587 / 34 648 |
| 12,89 | 0 | ventana 30, `mm_pov` = 0,1 | 7,4 / 10,3 / 10,1 | 18 305 / 20 186 / 21 853 |

- **El spread no discrimina.** Queda entre 0,17 y 0,34 bps en las 27 combinaciones y su término suma entre 2,5 y 3,5 por tramo (≈ 9 en total) a todas. La pérdida sin el spread de la ganadora es ≈ 0,57.
- **Las mejores están casi empatadas.** Con 3 semillas la volatilidad de un tramo varía varios bps entre configuraciones sin patrón, y un ranking fallido (+1) pesa más que las diferencias de nivel.
- **La ganadora es rmsc04 por defecto con `mm_pov` = 0,005.** Actividad ×2 y ×4 dan 1,5–3 veces el volumen objetivo.
- **Refinamiento local** (4 vecinos, mismas semillas): ninguno mejora (9,93 / 10,70 / 11,13 / 11,71).

**Inestabilidad con poco flujo de valor.** En una corrida exploratoria del 4 oct (grilla de 8, flujo de valor en 0,4 / 0,6 / 0,8 / 1,0 × `mm_pov` en 0,005 / 0,025, con el peso del spread en 0), el flujo 0,4× dio volatilidades de 40 a 6 863 bps: el precio explota durante la tarde. Eligió la misma config ganadora. Su archivo no se conservó (lo sobrescribió la grilla de 27), por lo que estas cifras salen de la salida de consola y no de un JSON versionado.

### 8.3 Validación (30 semillas nuevas por tramo, 101–130)

Config calibrada: rmsc04 por defecto con `mm_pov` = 0,005 y, por tramo, `r_bar` = 59 698 y `fund_vol` = 3,70e-4 / 2,43e-4 / 2,27e-4.

**KS de 2 muestras, retornos de 5 min simulados contra reales:**

| Tramo | n sim / n real | D | p | D_crit | D/D_crit | Rechaza al 5 % |
|---|---|---:|---:|---:|---:|:---:|
| Apertura | 690 / 1 111 | 0,064 | 0,058 | 0,066 | 0,97 | no (al borde) |
| Media jornada | 900 / 1 690 | 0,074 | 0,003 | 0,056 | 1,32 | **sí** |
| Cierre | 690 / 1 252 | 0,099 | 0,0003 | 0,064 | 1,54 | **sí** |

**La meta del plan (p > 0,05) no se cumple en media jornada ni en cierre.** Con ambas muestras estandarizadas (solo forma) rechaza en los tres tramos: p = 0,040 / 0,002 / 0,0003.

**Qué pasó con 10 semillas.** La primera validación (semillas 101–110) no rechazaba en ningún tramo (p = 0,35 / 0,079 / 0,17). Era falta de potencia: con 230–300 retornos simulados D_crit valía 0,085–0,098. La distancia D casi no cambió al triplicar la muestra (0,067 → 0,064; 0,079 → 0,074; 0,079 → 0,099); lo que bajó fue el umbral. Por eso se amplió a 30 semillas antes de dar el resultado por bueno.

**Tamaño de la diferencia, como en la 2.1.3b.** D mide la mayor distancia entre las dos funciones de distribución acumulada. Comparado con el modelo de Poisson calibrado para el mismo activo:

| Tramo | D con RMSC04 calibrado | D con Poisson compuesto (2.1.3b) | D con Poisson base (2.1.3) |
|---|---:|---:|---:|
| Apertura | 0,064 | 0,091 | 0,100 |
| Media jornada | 0,074 | 0,109 | 0,116 |
| Cierre | 0,099 | 0,100 | 0,114 |

Los retornos simulados quedan a 6–10 puntos porcentuales de los reales en el peor punto de la CDF: más cerca que el modelo de Poisson en apertura y media jornada, e igual en cierre. El simulador aproxima la distribución de retornos; no se puede afirmar que sea la misma. (Los D/D_crit no son comparables entre las dos tareas, porque la 2.1.3 simulaba 5 000 retornos.)

**Momentos simulados contra objetivos:**

| Momento | Apertura | Media jornada | Cierre |
|---|---|---|---|
| Volatilidad de 5 min (bps) | 34,0 / 34,0 (0 %) | 20,0 / 22,3 (−10 %) | 20,5 / 20,9 (−2 %) |
| Participación de volumen | 0,285 / 0,249 | 0,390 / 0,381 | 0,323 / 0,309 |
| Volumen mediano por vela | 11 268 / 7 576 (+49 %) | 11 471 / 9 396 (+22 %) | 12 399 / 11 964 (+4 %) |
| Spread mediano (bps) | 0,23 / [5,7; 35,3] | 0,17 / [4,1; 23,8] | 0,17 / [4,9; 20,6] |
| Exceso de curtosis | 8,67 / 5,87 | 2,70 / 5,14 | 5,56 / 3,36 |

Pérdida de validación: 10,27, de la cual 9,72 es el término del spread; el resto suma 0,55.

**Rankings.**

- *Volatilidad máxima en la apertura:* se cumple, **por construcción** (`fund_vol` por tramo). El orden completo simulado es apertura > cierre > media jornada; el observado, apertura > media jornada > cierre. Los dos últimos difieren en 0,5 bps, dentro del ruido.
- *Volumen por vela creciente:* se cumple (11 268 < 11 471 < 12 399), pero el aumento es de 10 % entre apertura y cierre contra 58 % en los datos reales. RMSC04 no tiene un mecanismo que haga crecer el volumen; no se da por reproducido.
- *Participación de volumen:* mismo orden que el observado (media jornada > cierre > apertura). Es en buena parte aritmética: la media jornada dura 30 velas y los otros tramos 24.

## 9. Antes y después de la 2.2.5

`collect_abides_stats.py` (10 episodios por tramo, política aleatoria) con rmsc04 sin calibrar y con la config calibrada, comparados con `compare_simulated_vs_real()`:

| | Apertura | Media jornada | Cierre | `forma_coincide` |
|---|---:|---:|---:|:---:|
| Real: spread proxy high−low (% del precio) | 0,138 | 0,112 | 0,128 | — |
| Antes: spread normalizado | 0,00193 | 0,00082 | 0,00081 | False |
| Después: spread normalizado | 0,00290 | 0,00233 | 0,00472 | False |
| Antes: spread mediano (bps) | 0,100 | 0,100 | 0,100 | — |
| Después: spread mediano (bps) | 0,168 | 0,170 | 0,172 | — |
| Antes: spread medio (bps) | 0,39 | 0,16 | 0,16 | — |
| Después: spread medio (bps) | 0,58 | 0,47 | 0,95 | — |

Orden de menor a mayor: real media jornada → cierre → apertura; antes cierre → media jornada → apertura; después media jornada → apertura → cierre.

**La calibración no mejora la forma del spread.** En ambos casos el spread mediano es exactamente 1 tick en los tres tramos (0,1 bps con centavos y precio 1 000; 0,17 bps con décimos y precio 5 970). El orden entre tramos lo deciden unas pocas observaciones anchas (desvío de 0,1 a 3,4 bps con 86–118 observaciones por tramo), es decir, ruido. Lo que cambia con la calibración es la escala de precios y la volatilidad, no el spread. La línea base coincide con la que PS versionó el 3 de octubre; la versión con spread en bps se guardó aparte (`perfil_mercado_abides_sin_calibrar_bps.json`) sin tocar su archivo.

## 10. Limitaciones

1. **El spread simulado no alcanza los proxies reales.** Es de 1–2 ticks (≈ 0,2 bps) contra 4–35 bps de Corwin-Schultz y Roll, y RMSC04 no permite abrirlo sin perder el volumen y la volatilidad (§8.1). Consecuencia para el proyecto: el costo de cruzar el spread es mucho menor en el simulador que en el mercado, así que el Implementation Shortfall absoluto queda subestimado. La comparación relativa entre políticas (PPO contra TWAP/VWAP) sigue siendo válida. Los proxies, a su vez, son estimaciones indirectas desde velas OHLCV que difieren en un factor 4–6 entre sí: el spread cotizado real no se observa.
2. **`fund_vol` constante por tramo.** Una config por tramo; el simulador no tiene volatilidad intradiaria variable.
3. **Tick empírico.** El tick de 0,1 CLP se midió en los datos de yfinance, no en la tabla oficial de la Bolsa de Santiago.
4. **Actividad estacionaria y volumen alto en la apertura.** RMSC04 no tiene un mecanismo que haga crecer el volumen durante el día; el volumen por vela simulado queda 49 % sobre el real en apertura y 4 % en cierre.
5. **Sin subasta ni operaciones en bloque.** Los objetivos excluyen la subasta de cierre; el simulador no la modela.
6. **Un activo y un régimen.** Solo FALABELLA, con el snapshot previo a la transición del IPSA a MSCI (1-sep-2026).
7. **El KS rechaza en dos de tres tramos** con 30 semillas (§8.3). La calibración aproxima la distribución de retornos de 5 min (D = 0,06–0,10), no la reproduce.
8. **Colas.** La curtosis simulada es inestable entre muestras y no permite comparar las colas con las reales.
9. **Python.** Los tests corren en Python 3.11; la compatibilidad con 3.9 se verificó estáticamente (`vermin`: mínimo 3.7) y el código que usa ABIDES corrió en Colab con Python 3.9. La suite de tests no se ha ejecutado en 3.9.

## 11. Párrafo para el informe

> Para que el mercado simulado fuera representativo del activo en estudio, la configuración de referencia RMSC04 de ABIDES-Gym se ajustó con datos reales de FALABELLA. El nivel de precios se fijó en la mediana observada y la volatilidad del valor fundamental se derivó, por tramo horario, del desvío de los retornos de cinco minutos, corrigiendo un error de unidades de la configuración inicial: el oráculo del simulador mide el tiempo en nanosegundos, por lo que el parámetro de volatilidad debe dividirse por la raíz del número de nanosegundos de una vela. La unidad de cuenta se eligió de modo que el tick del simulador coincidiera con el incremento mínimo de precio observado en los datos. Un test de razón de varianzas mostró reversión significativa en los retornos de cinco minutos, pero con la forma propia del rebote entre precios de compra y de venta y no la de un valor fundamental que revierte, por lo que no se introdujo reversión intradiaria en el oráculo. Los parámetros del creador de mercado y de la actividad, que no pueden estimarse directamente sin datos del libro de órdenes, se obtuvieron mediante una búsqueda en grilla que minimiza la distancia entre momentos simulados y observados. De este modo, el simulador aproxima, mediante calibración con datos reales del IPSA, la volatilidad y el perfil de volumen del activo. Con treinta simulaciones independientes por tramo, la volatilidad de cinco minutos quedó dentro de un 10 % de la observada (34,0, 20,0 y 20,5 puntos base frente a 34,0, 22,3 y 20,9). La prueba de Kolmogórov-Smirnov rechazó la igualdad entre las distribuciones de retornos simulados y reales en la media jornada y en el cierre (p = 0,003 y 0,0003) y no la rechazó, por un margen estrecho, en la apertura (p = 0,058); la distancia máxima entre las distribuciones acumuladas fue de 0,06 a 0,10, menor o igual que la obtenida con el modelo de Poisson calibrado en la etapa anterior. La participación de cada tramo en el volumen diario se aproximó a la observada y el volumen por vela resultó entre un 4 % y un 49 % mayor. La calibración tiene limitaciones que se declaran. La principal es que el spread simulado, de uno a dos ticks, es entre veinte y cien veces menor que los estimadores indirectos del spread real, y la arquitectura del simulador no permite ampliarlo sin deteriorar el volumen y la volatilidad; por ello el costo absoluto de ejecución queda subestimado y las conclusiones deben leerse en términos relativos entre estrategias. Además, la volatilidad se fija por tramo en lugar de variar de forma continua durante la jornada.

## 12. Reproducción

```bash
# Local (necesita los .parquet del snapshot): bloque A y evidencia
python -m src.envs.calibrate_rmsc04_ipsa --ticker FALABELLA --snapshot 2026-08-23

# Colab (ver notebooks/Colab_Sprint4_BF.ipynb, celdas 9a a 11)
python scripts/colab/rmsc04_grid_search.py --ticker FALABELLA --snapshot 2026-08-23 --screen --out-dir <dir>
python scripts/colab/rmsc04_grid_search.py --ticker FALABELLA --snapshot 2026-08-23 --seeds 3 --out-dir <dir>
python scripts/colab/rmsc04_validate.py --ticker FALABELLA --snapshot 2026-08-23 --seeds 10 --refine \
    --grid-json <dir>/rmsc04_grid_FALABELLA_2026-08-23.json --out-dir <dir>
python src/envs/collect_abides_stats.py --calibrated-json <dir>/rmsc04_ipsa_FALABELLA_2026-08-23.json --out-dir <dir>

# Tests (sin ABIDES)
pytest tests/test_calibrate_rmsc04_ipsa.py tests/test_rmsc04_sim_stats.py tests/test_rmsc04_search.py tests/test_collect_abides_stats.py
```

## Referencias

- Byrd, D., Hybinette, M., & Balch, T. H. (2020). ABIDES: Towards high-fidelity multi-agent market simulation. *ACM SIGSIM-PADS*.
- Corwin, S. A., & Schultz, P. (2012). A simple way to estimate bid-ask spreads from daily high and low prices. *Journal of Finance*, 67(2), 719–760.
- Lo, A. W., & MacKinlay, A. C. (1988). Stock market prices do not follow random walks: Evidence from a simple specification test. *Review of Financial Studies*, 1(1), 41–66.
- Roll, R. (1984). A simple implicit measure of the effective bid-ask spread in an efficient market. *Journal of Finance*, 39(4), 1127–1139.
