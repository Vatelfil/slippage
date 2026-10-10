# Función de recompensa de los Ejecutores — Tarea 2.2.3

**Proyecto:** Coordinación de Agentes para la Mitigación del Slippage (IPSA) — Título II, UTEM
**Responsable:** Benjamín Farias (BF)

> **Estado al 2026-10-09.** Implementados σ² causal **normalizada por el largo de la ventana** (§2 y §5.5) y la escala común en CLP por acción del slice (§4). Barrido de β de la fase 1 corrido en el fallback Poisson y en ABIDES calibrado con la definición final de σ². **Rango recomendado para la fase 2: β ∈ [0,0062; 0,062] CLP⁻¹** (0,1 β\* a β\* de ABIDES). **Pendiente:** la fase 2 con PPO, que depende de la 2.2.1. `BETA_RIESGO_EJECUTOR` sigue en 0.

| Qué | Dónde |
|---|---|
| Fórmula, σ² y escala (lógica pura) | [`src/envs/reward_utils.py`](../src/envs/reward_utils.py) |
| Parámetros (β, ventana, escala) | [`src/config/market_params.py`](../src/config/market_params.py) |
| Entornos | [`src/envs/fallback_poisson_env.py`](../src/envs/fallback_poisson_env.py), [`src/envs/abides_ejecutor_env.py`](../src/envs/abides_ejecutor_env.py), [`src/envs/abides_bridge.py`](../src/envs/abides_bridge.py) |
| Barrido de β | [`src/experiments/beta_sweep.py`](../src/experiments/beta_sweep.py), [`scripts/beta_sweep.py`](../scripts/beta_sweep.py), [`scripts/colab/beta_sweep_abides.py`](../scripts/colab/beta_sweep_abides.py) |
| Resultados | [`beta_sweep_poisson_2026-10-09.json`](../data/calibration/beta_sweep_poisson_2026-10-09.json), [`beta_sweep_abides_2026-10-10.json`](../data/calibration/beta_sweep_abides_2026-10-10.json) (σ² normalizada), [`beta_sweep_abides_2026-10-09.json`](../data/calibration/beta_sweep_abides_2026-10-09.json) (σ² anterior) |
| Tests | `tests/test_reward_utils.py`, `tests/test_beta_sweep.py` |

---

## 1. Definición

$$
R_E = (P_{mid,t} - P_{ejec,t})\cdot q_{ejec} \;-\; \beta\cdot\sigma^2_{precio}\cdot q_{ejec} \qquad \text{(Título I, §4.2.4)}
$$

El primer término es el costo de ejecución del paso frente al precio medio: negativo cuando se compra sobre el mid. El segundo es la penalización por riesgo.

Antes de esta tarea el término de riesgo era 0 en los dos entornos: el fallback tenía `BETA_PLACEHOLDER * 0.0 * q_ejec` y `ExecutionEnv27` no le pasaba `sigma2` a `step_reward` (H7).

## 2. σ²_precio

**Definición.** Varianza muestral del P_mid en una ventana móvil de las últimas W decisiones, normalizada por el número *n* de puntos de la ventana:

$$
\sigma^2_{precio} = \operatorname{Var}\big(P_{mid}\ \text{en la ventana}\big)\cdot\frac{6}{n+1}
$$

W = `VENTANA_SIGMA2_PASOS` = 20 pasos, es decir, 10 min con pasos de 30 s. Unidades: CLP². Con la normalización, σ² estima la varianza del cambio de precio en **un paso**, cualquiera sea el largo de la ventana.

**Causalidad.** La varianza que entra en la recompensa del paso *t* usa solo los P_mid observados hasta *t* − 1; el P_mid de *t* se incorpora después. `RollingPriceVariance.step(p_mid_t)` hace las dos cosas en ese orden. El test `test_sigma2_es_causal_sin_look_ahead` aplica un shock de precio en *t* = 25 y comprueba que σ² no cambia hasta *t* = 26.

**Prior.** Con menos de `SIGMA2_MIN_PUNTOS` = 5 puntos en la ventana se usa un prior del tramo:

$$
\sigma^2_{prior} = (\sigma_{5min}\cdot P_{ref})^2\cdot\frac{\Delta t_{paso}}{300\ \text{s}}
$$

con σ_5min el desvío del retorno de 5 min del tramo (`obs_return_std` de la 2.1.3) y P_ref el precio de entrada. Es la varianza del cambio de precio en un paso. Para FALABELLA a 5 970 CLP: 41,1 / 17,8 / 15,5 CLP² en apertura / media jornada / cierre.

**Por qué se normaliza.** Para un paseo aleatorio, la varianza muestral de *n* niveles consecutivos vale en promedio σ²_paso · (n + 1)/6: crece con *n*, de 1 vez la varianza de un paso con 5 puntos a 3,5 veces con 20. Sin el factor 6/(n + 1), σ² subía mientras la ventana se llenaba y el término de riesgo castigaba ejecutar tarde aunque el mercado no estuviera más volátil; el barrido en ABIDES lo dejó a la vista (§5.4). Con el factor, la ventana es comparable con el prior para cualquier *n*. El test `test_sigma2_normalizada_no_crece_con_el_largo_de_la_ventana` comprueba que la media de σ² es la varianza de un paso con 5, 10 y 20 puntos.

**Por qué 5 puntos como mínimo.** Con *n* = 5 el factor vale 1, así que el paso del prior a la ventana no cambia la fórmula; con menos puntos la varianza muestral es demasiado ruidosa.

## 3. Interpretación del término de riesgo

Todo el slice asignado debe ejecutarse, así que el término de riesgo no castiga la espera en sí (eso le corresponde a λ en R_M). Castiga ejecutar cuando la varianza reciente del precio es alta y, por lo tanto, empuja la ejecución hacia momentos de menor varianza. β tiene unidades de 1/CLP: β·σ² es un costo en CLP por acción.

## 4. Escala

Antes los dos entornos entregaban R_E en escalas distintas:

| Entorno | Antes | Ahora (default) |
|---|---|---|
| `EjecutorEnvPoissonFallback` | CLP totales | CLP por acción del slice |
| `EjecutorEnvAbides` | unidad de cuenta de ABIDES (centavos) ÷ `parent_order_size` | CLP por acción del slice |

`reward_escala` admite `"por_accion_slice"` (R_E ÷ q_slice) y `"bruta"` (CLP totales). El default, `ESCALA_RECOMPENSA_EJECUTOR = "por_accion_slice"`, es el mismo en los dos entornos. En ABIDES los precios se pasan a CLP con `BridgeConfig.unidades_por_clp` (100 con rmsc04 sin calibrar, 10 con la config en décimos de la 2.2.4).

**Evidencia.** Con una política MARKET en apertura, el retorno por episodio en escala bruta es −2 045 / −10 225 / −56 745 CLP para slices de 200 / 1 000 / 5 000 acciones; por acción es −10,2 / −10,2 / −11,3. En `experiments/test_ppo_short_run.py` el `value_loss` de los Ejecutores pasa de ≈ 17 000–65 000 (bruta) a ≈ 2–7 (por acción); el script termina bien con las dos escalas.

**Consistencia entre entornos.** `test_misma_secuencia_de_fills_da_la_misma_recompensa_en_ambos_entornos` corre el fallback, repite la misma secuencia de mids y fills en `ExecutorRewardState` con los precios en la unidad de cuenta de ABIDES (décimos y centavos) y comprueba que la recompensa, σ² y las componentes coinciden.

**Regresión.** Con β = 0 y la escala anterior de cada entorno, la recompensa es idéntica a la previa (`test_fallback_beta_cero_reproduce_la_recompensa_anterior`, `test_bridge_beta_cero_reproduce_step_reward_anterior`).

**Decisión (2026-10-09).** La escala queda en CLP por acción del slice. Cambia la escala que ve PPO en el fallback respecto de la previa a esta tarea; `"bruta"` sigue disponible como opción.

**`info`.** Los dos entornos exponen `sigma2`, `reward_precio`, `reward_riesgo` y `reward_escala` en cada paso.

## 5. Calibración de β, fase 1

**Método.** Tres políticas heurísticas, tres tramos, 20 semillas, slice de 1 000 acciones y ventana de 15 min (30 pasos). Una política heurística no mira la recompensa, así que β no cambia lo que hace: cada episodio se corre una vez y R_E se recalcula para cada β.

| Política | Acción |
|---|---|
| `agresiva_market` | MARKET por todo lo pendiente |
| `twap_limit_medio` | LIMIT de nivel medio (4) por 1/(pasos restantes) de lo pendiente (mínimo 10 %, el del espacio de acciones) |
| `pasiva_limit` | LIMIT pasiva por todo lo pendiente, renovada en cada paso |

**Escala de referencia.**

$$
\beta^* = \frac{E_q\,|P_{mid}-P_{ejec}|}{E_q[\sigma^2]}
$$

con medias ponderadas por q_ejec: es el β con el que, en el agregado, el término de riesgo pesa lo mismo que el de precio. Grilla: {0; 0,1; 0,3; 1; 3} × β\*.

**Peso del riesgo.** Σ|riesgo| / (Σ|precio| + Σ|riesgo|), entre 0 y 1. Se usa esta forma y no |riesgo|/|R_E| porque R_E = precio − riesgo puede quedar cerca de 0 cuando el término de precio es positivo (una orden pasiva que compra bajo el mid) y el cociente literal se dispara. El cociente literal también se guarda (`riesgo_sobre_abs_R_E`). Regla del plan: se descartan los β con peso > 80 % o < 5 %.

### 5.1 Resultado en el fallback Poisson

Corrido con la σ² normalizada. β\* = **0,59 CLP⁻¹** (por tramo: 0,48 / 0,68 / 0,79). Es prácticamente igual al obtenido antes de normalizar (0,5905 contra 0,5917), porque en el fallback casi todo el riesgo se acumula mientras rige el prior, que no cambió.

Peso del riesgo por tramo (las tres políticas juntas):

| β | Apertura | Media jornada | Cierre | Regla |
|---|---:|---:|---:|---|
| 0 | 0 % | 0 % | 0 % | descartado (< 5 %) |
| 0,1 β\* = 0,059 | 10,9 % | 8,0 % | 7,0 % | admisible |
| 0,3 β\* = 0,177 | 26,9 % | 20,8 % | 18,5 % | admisible |
| β\* = 0,592 | 55,1 % | 46,6 % | 43,0 % | admisible |
| 3 β\* = 1,775 | 78,7 % | 72,4 % | 69,4 % | admisible, al borde en apertura |

Por política el margen es más estrecho: con 3 β\* la política agresiva tiene 81–87 % de peso de riesgo, y con 0,1 β\* la TWAP tiene 3–5 %.

R_E medio por episodio (CLP por acción) en apertura:

| β | Agresiva | TWAP | Pasiva | Ranking |
|---|---:|---:|---:|---|
| 0 | −10,87 | −9,70 | −10,92 | TWAP > agresiva > pasiva |
| 0,1 β\* | −13,30 | −10,17 | −11,89 | TWAP > pasiva > agresiva |
| β\* | −35,17 | −14,36 | −20,66 | TWAP > pasiva > agresiva |
| 3 β\* | −83,79 | −23,67 | −40,14 | TWAP > pasiva > agresiva |

El slippage (18,2 / 17,7 / 18,4 bps en apertura) y el cumplimiento (100 % / 92 % / 100 %) no dependen de β. El ranking cambia con β en apertura y media jornada (la agresiva pasa del segundo al tercer lugar ya con 0,1 β\*) y no cambia en cierre.

### 5.2 Por qué el resultado del fallback no fija β

**El fallback Poisson no sirve para calibrar el nivel de β.** Su P_mid se mueve ≈ 0,19–0,21 CLP por paso, contra 3,9–6,4 CLP del prior (que sale de la volatilidad real). La σ² de la ventana, una vez que deja el prior, es 400–1 350 veces menor que el prior:

| Tramo | Prior (CLP²) | σ² mediana de la ventana (CLP²) | Razón |
|---|---:|---:|---:|
| Apertura | 41,08 | 0,030 | 1 349 |
| Media jornada | 17,79 | 0,029 | 615 |
| Cierre | 15,51 | 0,039 | 401 |

En el fallback el término de riesgo pesa casi solo en los cuatro primeros pasos del episodio, mientras rige el prior. Por eso la política agresiva, que ejecuta todo en el primer paso, es la más castigada: el barrido mide el efecto "ejecutar antes de que la ventana se llene", no "ejecutar cuando el precio está volátil". β\* queda determinado por el prior y por cuánto se ejecuta bajo él.

**Otras dos limitaciones del fallback que afectan la lectura:**

- *Convención del nivel de precio invertida.* El contrato (`spaces.py`, `abides_bridge.py`) dice que el nivel 0 es el más pasivo y el 7 el más agresivo. `PoissonLOBSimulator.execute_limit_buy` usa la probabilidad de llenado `1 − nivel/8`: el nivel 0 se llena siempre y el 7 casi nunca. La política pasiva usa el nivel 7 en el fallback y el 0 en ABIDES (`NIVEL_PASIVO`). No se modificó el simulador.
- *Una LIMIT llenada paga como una MARKET.* En el fallback una orden límite que se llena barre el lado ask igual que una de mercado, así que nunca compra bajo el mid: el término de precio es siempre negativo y las políticas se diferencian solo por cuándo y cuánto barren.

### 5.3 Resultado en ABIDES calibrado (σ² sin normalizar)

> Esta corrida es del 8 de octubre y usa la definición **anterior** de σ² (varianza del nivel sin el factor 6/(n + 1)). Se conserva porque es la evidencia que motivó el cambio. Las cifras de las políticas agresiva y pasiva casi no dependen de la definición (ejecutan bajo el prior); las de la TWAP sí.

Config de la 2.2.4 (`rmsc04_ipsa_FALABELLA_2026-08-23.json`), 20 semillas, slice de 1 000 acciones, ventana de 15 min. Se corrió dos veces (5 y 8 de octubre) con resultados idénticos.

β\* = **0,0456 CLP⁻¹** (por tramo: 0,0455 / 0,0439 / 0,0488), 13 veces menor que el del fallback, como se anticipaba: en ABIDES la volatilidad del mid es la real.

Peso del riesgo por tramo:

| β | Apertura | Media jornada | Cierre | Regla |
|---|---:|---:|---:|---|
| 0 | 0 % | 0 % | 0 % | descartado (< 5 %) |
| 0,1 β\* = 0,0046 | 9,1 % | 9,4 % | 8,6 % | admisible |
| 0,3 β\* = 0,0137 | 23,1 % | 23,8 % | 21,9 % | admisible |
| β\* = 0,0456 | 50,0 % | 51,0 % | 48,3 % | admisible |
| 3 β\* = 0,137 | 75,0 % | 75,7 % | 73,7 % | admisible por tramo; la política pasiva llega a 86–90 % |

R_E medio por episodio (CLP por acción):

| Tramo | β | Agresiva | TWAP | Pasiva | Ranking |
|---|---|---:|---:|---:|---|
| Apertura | 0 | −2,57 | −0,87 | −0,09 | pasiva > TWAP > agresiva |
| Apertura | β\* | −4,41 | −3,26 | −1,76 | pasiva > TWAP > agresiva |
| Media jornada | 0 | −1,55 | −0,69 | +0,01 | pasiva > TWAP > agresiva |
| Media jornada | β\* | −2,36 | −3,33 | −1,08 | pasiva > agresiva > TWAP |
| Cierre | 0 | −0,20 | −0,24 | +0,19 | pasiva > agresiva > TWAP |
| Cierre | β\* | −0,89 | −1,39 | −0,62 | pasiva > agresiva > TWAP |

Qué se observa:

- **La política pasiva domina en los tres tramos y para todos los β.** Una orden límite de 1 000 acciones en el mejor bid se llena completa en 2–4 pasos (mediana) y casi sin costo frente al mid.
- **La agresiva paga impacto, no spread:** ≈ 2,6 CLP por acción en apertura (4,4 bps) con un spread de 0,2 bps. El libro es poco profundo (`mm_pov` = 0,005) y una orden de mercado de 1 000 acciones lo recorre; en apertura necesita una mediana de 3 pasos para completarse.
- **El ranking cambia con β solo en media jornada:** la TWAP pasa del segundo al tercer lugar con β\*.
- **Cumplimiento:** 100 % en agresiva y pasiva; 95–100 % en TWAP (usa los 30 pasos).
- **El slippage frente al precio de llegada no discrimina** con 20 semillas: su desvío entre episodios (2–15 CLP) es del tamaño de las diferencias entre políticas o mayor. El término de precio de R_E, medido contra el mid del paso, sí las separa.

### 5.4 Qué medía el término de riesgo sin normalizar

| Tramo | Prior (CLP²) | σ² media al ejecutar: agresiva | pasiva | TWAP |
|---|---:|---:|---:|---:|
| Apertura | 41,1 | 40,3 | 36,7 | 52,7 |
| Media jornada | 17,8 | 17,7 | 23,9 | 58,1 |
| Cierre | 15,5 | 15,3 | 17,6 | 25,4 |

Las políticas agresiva y pasiva terminan en los primeros pasos, cuando todavía rige el prior. La TWAP reparte la ejecución en 30 pasos y ve la ventana llena, cuya varianza es 1,3–3,3 veces el prior. Eso **no** refleja un mercado más volátil: es la propiedad descrita en §2. La varianza del *nivel* del precio en una ventana de *n* puntos crece como (n + 1)/6 veces la varianza de un paso, de 1× con 5 puntos a 3,5× con 20.

**Consecuencia: sin normalizar, el término de riesgo castigaba ejecutar tarde durante los primeros 20 pasos del episodio**, con independencia del estado del mercado. Eso contradecía la interpretación de §3 (el riesgo no debería penalizar la espera) y explica por qué la TWAP perdía posiciones al subir β.

### 5.5 Decisión: σ² normalizada por el largo de la ventana

Había dos formas de quitar ese efecto:

- **Normalizar por el largo de la ventana**, σ²·6/(n + 1). Estima la varianza de un paso para cualquier *n* y es comparable con el prior. Es el cambio mínimo y mantiene la redacción del Título I ("varianza del precio").
- Usar la varianza de los incrementos del mid en vez de la del nivel.

**Se adoptó la primera (2026-10-09)** y está implementada en `RollingPriceVariance`. Con β = 0 la recompensa no cambia.

### 5.6 Resultado en ABIDES calibrado con la σ² normalizada

Misma config, semillas y políticas que en §5.3 (corrida del 9 de octubre). La dinámica de los episodios es idéntica: solo cambia σ².

**La normalización hace lo que se buscaba.** σ² media al ejecutar, en CLP²:

| Tramo | Prior | Agresiva | Pasiva | TWAP (antes → ahora) |
|---|---:|---:|---:|---|
| Apertura | 41,1 | 40,2 | 36,6 | 52,7 → 26,1 |
| Media jornada | 17,8 | 17,7 | 21,1 | 58,1 → 26,5 |
| Cierre | 15,5 | 15,3 | 16,4 | 25,4 → 12,4 |

La σ² que ve la TWAP ya no está inflada por el largo de la ventana: queda entre 0,6 y 1,5 veces el prior, sin sesgo sistemático hacia arriba. Las políticas que ejecutan en los primeros pasos casi no cambian.

β\* = **0,0618 CLP⁻¹** (por tramo: 0,0574 / 0,0669 / 0,0645); con la definición anterior era 0,0456.

Peso del riesgo por tramo:

| β | Apertura | Media jornada | Cierre | Regla |
|---|---:|---:|---:|---|
| 0 | 0 % | 0 % | 0 % | descartado (< 5 %) |
| 0,1 β\* = 0,0062 | 9,7 % | 8,5 % | 8,7 % | admisible |
| 0,3 β\* = 0,0185 | 24,4 % | 21,7 % | 22,3 % | admisible |
| β\* = 0,0618 | 51,9 % | 48,0 % | 48,9 % | admisible |
| 3 β\* = 0,185 | 76,4 % | 73,5 % | 74,2 % | admisible por tramo; la política pasiva llega a 88–92 % |

R_E medio por episodio (CLP por acción):

| Tramo | β | Agresiva | TWAP | Pasiva | Ranking |
|---|---|---:|---:|---:|---|
| Apertura | 0 | −2,57 | −0,87 | −0,09 | pasiva > TWAP > agresiva |
| Apertura | β\* | −5,05 | −2,47 | −2,35 | pasiva > TWAP > agresiva |
| Apertura | 3 β\* | −10,02 | −5,68 | −6,86 | TWAP > pasiva > agresiva |
| Media jornada | 0 | −1,55 | −0,69 | +0,01 | pasiva > TWAP > agresiva |
| Media jornada | β\* | −2,65 | −2,32 | −1,29 | pasiva > TWAP > agresiva |
| Media jornada | 3 β\* | −4,83 | −5,59 | −3,90 | pasiva > agresiva > TWAP |
| Cierre | 0 | −0,20 | −0,24 | +0,19 | pasiva > agresiva > TWAP |
| Cierre | β\* | −1,14 | −1,00 | −0,82 | pasiva > TWAP > agresiva |
| Cierre | 3 β\* | −3,03 | −2,52 | −2,85 | TWAP > pasiva > agresiva |

Qué se observa:

- **La TWAP ya no pierde posiciones al subir β.** Con la definición anterior caía al tercer lugar en media jornada con β\*; ahora con β\* es segunda en los tres tramos, y en apertura y cierre pasa al primer lugar con 3 β\*.
- **La política pasiva sigue primera hasta β\*** en los tres tramos: compra casi al mid y termina en 2–4 pasos.
- **El ranking cambia con β en los tres tramos**, que es lo que se espera de un término de riesgo que distingue cuándo se ejecuta.
- Cumplimiento y slippage son los mismos de §5.3, porque no dependen de σ².

### 5.7 Recomendación

- **Rango para la fase 2: β ∈ [0,0062; 0,062] CLP⁻¹** (0,1 β\* a β\*). Se deja fuera 3 β\*: pasa la regla por tramo, pero la política pasiva queda con 88–92 % de peso de riesgo y la TWAP con 72–77 %.
- **Finalistas sugeridos:** 0,3 β\* = 0,019 y β\* = 0,062.
- **Alcance:** el rango sale de políticas heurísticas con un slice de 1 000 acciones y una ventana de 15 min en FALABELLA. Sirve para acotar la búsqueda de la fase 2, no como valor final.
- `BETA_RIESGO_EJECUTOR` se mantiene en 0,0 hasta la fase 2.

## 6. Pendientes

1. **Fase 2 (PPO).** Corridas cortas con 2–3 β finalistas y elección por IS y cumplimiento. Depende de la 2.2.1 (Mauricio); si se atrasa pasa al Sprint 5.
2. **P_mid de referencia.** El fallback usa el mid previo a la ejecución y `ExecutionEnv27` el del despertar siguiente, posterior a los fills (así estaba antes de esta tarea; no se cambió para no romper la regresión con β = 0). Con una orden de mercado grande el mid posterior ya incorpora parte del impacto y subestima el costo. Conviene unificarlo en el mid previo.
3. **Schema.** `SE_schema.json` lista β en `pending_calibration`. Cuando β quede fijado, propuesta para el equipo: reemplazar esa entrada por el valor, la ventana W = 20 y la escala. No se modificó el schema.

## 7. Reproducción

```bash
python scripts/beta_sweep.py --seeds 20            # fallback Poisson, local
pytest tests/test_reward_utils.py tests/test_beta_sweep.py

# Colab
python scripts/colab/beta_sweep_abides.py --calibrated-json <dir>/rmsc04_ipsa_FALABELLA_2026-08-23.json --out-dir <dir>
```
