# Calibración de RMSC04 con datos del IPSA — Tarea 2.2.4

**Proyecto:** Coordinación de Agentes para la Mitigación del Slippage (IPSA) — Título II, UTEM
**Responsable:** Benjamín Farias (BF). La plantilla inicial de `calibrate_rmsc04_ipsa.py` es de Paolo Sepúlveda (PS).
**Activo:** FALABELLA (MVP), snapshot `2026-08-23`.

> **Estado al 2026-10-03.** Están cerrados el bloque A (traducción directa), el código de la búsqueda y de la validación, y sus tests. **Las simulaciones de ABIDES (bloques B y C) todavía no se han corrido en Colab:** las secciones 8 y 9 quedan marcadas como pendientes y no contienen ningún resultado simulado.

| Qué | Dónde |
|---|---|
| Bloque A: unidades, config base, VR, curtosis | [`src/envs/calibrate_rmsc04_ipsa.py`](../src/envs/calibrate_rmsc04_ipsa.py) |
| Momentos del simulador por tramo | [`src/envs/rmsc04_sim_stats.py`](../src/envs/rmsc04_sim_stats.py) |
| Grilla, pérdida, rankings, KS (lógica pura) | [`src/envs/rmsc04_search.py`](../src/envs/rmsc04_search.py) |
| Scripts de Colab | [`scripts/colab/rmsc04_grid_search.py`](../scripts/colab/rmsc04_grid_search.py), [`scripts/colab/rmsc04_validate.py`](../scripts/colab/rmsc04_validate.py) |
| Antes/después de 2.2.5 | [`src/envs/collect_abides_stats.py`](../src/envs/collect_abides_stats.py) |
| Evidencia del bloque A | [`data/calibration/rmsc04_base_FALABELLA_2026-08-23.json`](../data/calibration/rmsc04_base_FALABELLA_2026-08-23.json) |
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

*Pendiente:* repetirlo en Colab con el snapshot 2026-08-23 y la unidad elegida (décimos), celda "Experimento rápido H5/H6" del notebook.

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

**Advertencia.** En el experimento del plan el spread simulado fue de pocos ticks en ambas unidades (≈ 8 ticks en centavos, 1 tick en CLP). Si el spread en ticks es poco sensible a la unidad, una unidad más fina da un spread más angosto en bps. Elegir la unidad por el spread sería ajustar un artefacto; se elige por el tick y el spread se trabaja con los parámetros del creador de mercado (§7).

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

*Pendiente:* la validación reporta la curtosis simulada junto a la real (`por_tramo[tramo].curtosis`). Si la simulada queda muy por debajo, los megashocks entran a la búsqueda.

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

**Estos niveles salen de leer el código de ABIDES, no de haberlo corrido.** Por eso el script tiene `--screen` (7 configuraciones, un factor por vez, 1 semilla, solo apertura) para ver qué palanca mueve cada momento antes de gastar el presupuesto de la grilla, y `--grid-spec` para cambiar los niveles sin tocar el código.

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
2. corre 10 semillas **nuevas** (101–110, distintas de las de la búsqueda) por tramo, cada uno con su config;
3. KS de 2 muestras de los retornos de 5 min simulados contra los reales por tramo: D, p, D_crit y D/D_crit con `ks_critical_value`, como en la 2.1.3b. También sobre las muestras estandarizadas, que compara solo la forma;
4. tabla de momentos simulados contra objetivos y rankings.

La participación y el volumen por vela se miden en las corridas del tramo cierre, que son de día completo.

## 8. Resultados

**Pendiente: no se ha corrido ninguna simulación de ABIDES para esta tarea.** Al tener `rmsc04_grid_FALABELLA_2026-08-23.json` y `rmsc04_ipsa_FALABELLA_2026-08-23.json` se completan aquí:

- sondeo de sensibilidad y, si corresponde, ajuste de la grilla;
- mejor configuración y su pérdida;
- tabla de momentos simulados contra objetivos por tramo;
- KS por tramo (D, p, D_crit, D/D_crit);
- rankings reproducidos o no, con la explicación.

**Lo que se anticipa del diseño de RMSC04, a confirmar:**

- *Volumen por vela creciente.* Los agentes de valor llegan con tasa constante y los de ruido con una distribución en U entre 09:00 y 16:00. Ninguno de los dos produce un volumen que crezca de forma monótona durante el día. Es probable que este ranking no se reproduzca; si ocurre, se informa como limitación estructural del simulador y no se ajusta a la fuerza.
- *KS con p > 0,05.* Con ~1 100–1 700 retornos reales y 230–300 simulados, D_crit ≈ 0,085–0,10. Los retornos reales tienen masa en cero (tick e iliquidez) y curtosis de 3–6; se informará D/D_crit, como en la 2.1.3b.
- *Volatilidad máxima en la apertura.* En la validación se cumple por construcción (`fund_vol` por tramo); no es una predicción del simulador.

## 9. Antes y después de la 2.2.5

**Pendiente.** `collect_abides_stats.py` acepta ahora `--calibrated-json` y `--out-dir`, pasa la config por `background_config_extra_kvargs` y agrega el spread cotizado en bps (`spread_bps_mean`, `spread_bps_median`). Con config calibrada escribe `perfil_mercado_abides_calibrado.json`, sin pisar `perfil_mercado_abides_simulado.json` de PS. El formato que lee `compare_simulated_vs_real()` no cambió (hay un test que lo verifica).

Línea base de PS (rmsc04 sin calibrar, 3 oct): `forma_coincide = False`; orden simulado del spread cierre → media jornada → apertura contra el real media jornada → cierre → apertura.

## 10. Limitaciones

1. **Proxies de spread.** No hay Nivel 1 ni Nivel 2 del IPSA. Roll y Corwin-Schultz se construyen desde velas OHLCV de 5 min y difieren en un factor 4–6 entre sí. El objetivo de spread es un intervalo ancho.
2. **`fund_vol` constante por tramo.** Una config por tramo; el simulador no tiene volatilidad intradiaria variable.
3. **Tick empírico.** El tick de 0,1 CLP se midió en los datos de yfinance, no en la tabla oficial de la Bolsa de Santiago.
4. **Actividad estacionaria.** RMSC04 no tiene un mecanismo que haga crecer el volumen durante el día.
5. **Sin subasta ni operaciones en bloque.** Los objetivos excluyen la subasta de cierre; el simulador no la modela.
6. **Un activo y un régimen.** Solo FALABELLA, con el snapshot previo a la transición del IPSA a MSCI (1-sep-2026).
7. **Niveles de la grilla sin evidencia previa.** Se eligieron leyendo el código de ABIDES (§7).
8. **Python.** Los tests corrieron en Python 3.11; la compatibilidad con 3.9 se verificó estáticamente (`vermin`: mínimo 3.7) y la ejecución en 3.9 ocurre recién en Colab.

## 11. Párrafo para el informe

> Para que el mercado simulado fuera representativo del activo en estudio, la configuración de referencia RMSC04 de ABIDES-Gym se ajustó con datos reales de FALABELLA. El nivel de precios se fijó en la mediana observada y la volatilidad del valor fundamental se derivó, por tramo horario, del desvío de los retornos de cinco minutos, corrigiendo un error de unidades de la configuración inicial: el oráculo del simulador mide el tiempo en nanosegundos, por lo que el parámetro de volatilidad debe dividirse por la raíz del número de nanosegundos de una vela. La unidad de cuenta se eligió de modo que el tick del simulador coincidiera con el incremento mínimo de precio observado en los datos. Un test de razón de varianzas mostró reversión significativa en los retornos de cinco minutos, pero con la forma propia del rebote entre precios de compra y de venta y no la de un valor fundamental que revierte, por lo que no se introdujo reversión intradiaria en el oráculo. Los parámetros del creador de mercado y de la actividad, que no pueden estimarse directamente sin datos del libro de órdenes, se obtuvieron mediante una búsqueda en grilla que minimiza la distancia entre momentos simulados y observados. De este modo, el simulador aproxima, mediante calibración con datos reales del IPSA, la volatilidad, el spread y el perfil de volumen del activo. *[Completar con los resultados: momentos alcanzados, estadístico KS por tramo y rankings reproducidos.]* La calibración tiene limitaciones que se declaran: el spread real no se observa y se compara contra dos estimadores indirectos, y la volatilidad se fija por tramo en lugar de variar de forma continua durante la jornada.

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
