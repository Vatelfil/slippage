# Función de recompensa de los Ejecutores — Tarea 2.2.3

**Proyecto:** Coordinación de Agentes para la Mitigación del Slippage (IPSA) — Título II, UTEM
**Responsable:** Benjamín Farias (BF)

> **Estado al 2026-10-08.** Implementados σ² causal y la escala común; barrido de β de la fase 1 corrido en el fallback Poisson y en ABIDES calibrado. **Rango recomendado: β ∈ [0,0046; 0,046] CLP⁻¹** (0,1 β\* a β\* de ABIDES). **Pendientes:** una decisión sobre la definición de σ² que el barrido dejó a la vista (§5.5), la confirmación de la escala por parte de Mauricio Reynoso y la fase 2 con PPO. `BETA_RIESGO_EJECUTOR` sigue en 0.

| Qué | Dónde |
|---|---|
| Fórmula, σ² y escala (lógica pura) | [`src/envs/reward_utils.py`](../src/envs/reward_utils.py) |
| Parámetros (β, ventana, escala) | [`src/config/market_params.py`](../src/config/market_params.py) |
| Entornos | [`src/envs/fallback_poisson_env.py`](../src/envs/fallback_poisson_env.py), [`src/envs/abides_ejecutor_env.py`](../src/envs/abides_ejecutor_env.py), [`src/envs/abides_bridge.py`](../src/envs/abides_bridge.py) |
| Barrido de β | [`src/experiments/beta_sweep.py`](../src/experiments/beta_sweep.py), [`scripts/beta_sweep.py`](../scripts/beta_sweep.py), [`scripts/colab/beta_sweep_abides.py`](../scripts/colab/beta_sweep_abides.py) |
| Resultados | [`beta_sweep_poisson_2026-10-03.json`](../data/calibration/beta_sweep_poisson_2026-10-03.json), [`beta_sweep_abides_2026-10-09.json`](../data/calibration/beta_sweep_abides_2026-10-09.json) |
| Tests | `tests/test_reward_utils.py`, `tests/test_beta_sweep.py` |

---

## 1. Definición

$$
R_E = (P_{mid,t} - P_{ejec,t})\cdot q_{ejec} \;-\; \beta\cdot\sigma^2_{precio}\cdot q_{ejec} \qquad \text{(Título I, §4.2.4)}
$$

El primer término es el costo de ejecución del paso frente al precio medio: negativo cuando se compra sobre el mid. El segundo es la penalización por riesgo.

Antes de esta tarea el término de riesgo era 0 en los dos entornos: el fallback tenía `BETA_PLACEHOLDER * 0.0 * q_ejec` y `ExecutionEnv27` no le pasaba `sigma2` a `step_reward` (H7).

## 2. σ²_precio

**Definición.** Varianza muestral del P_mid en una ventana móvil de las últimas W decisiones. W = `VENTANA_SIGMA2_PASOS` = 20 pasos, es decir, 10 min con pasos de 30 s. Unidades: CLP².

**Causalidad.** La varianza que entra en la recompensa del paso *t* usa solo los P_mid observados hasta *t* − 1; el P_mid de *t* se incorpora después. `RollingPriceVariance.step(p_mid_t)` hace las dos cosas en ese orden. El test `test_sigma2_es_causal_sin_look_ahead` aplica un shock de precio en *t* = 25 y comprueba que σ² no cambia hasta *t* = 26.

**Prior.** Con menos de `SIGMA2_MIN_PUNTOS` = 5 puntos en la ventana se usa un prior del tramo:

$$
\sigma^2_{prior} = (\sigma_{5min}\cdot P_{ref})^2\cdot\frac{\Delta t_{paso}}{300\ \text{s}}
$$

con σ_5min el desvío del retorno de 5 min del tramo (`obs_return_std` de la 2.1.3) y P_ref el precio de entrada. Es la varianza del cambio de precio en un paso. Para FALABELLA a 5 970 CLP: 41,1 / 17,8 / 15,5 CLP² en apertura / media jornada / cierre.

**Por qué 5 puntos.** Para un paseo aleatorio, la varianza muestral de *n* niveles consecutivos vale en promedio σ²_paso · (n + 1)/6. Con *n* = 5 coincide con el prior, de modo que el paso del prior a la ventana no tiene un salto en promedio. Con la ventana llena (*n* = 20) vale 3,5 veces el prior: σ² mide la dispersión del nivel en 10 min, no la de un paso.

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

**Pendiente de acordar.** El default está fijado de forma provisional; se envió la propuesta a Mauricio porque cambia la escala que ve PPO en el fallback. Si se objeta, basta con cambiar la constante.

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

β\* = **0,59 CLP⁻¹** (por tramo: 0,48 / 0,68 / 0,78).

Peso del riesgo por tramo (las tres políticas juntas):

| β | Apertura | Media jornada | Cierre | Regla |
|---|---:|---:|---:|---|
| 0 | 0 % | 0 % | 0 % | descartado (< 5 %) |
| 0,1 β\* = 0,059 | 10,9 % | 8,0 % | 7,0 % | admisible |
| 0,3 β\* = 0,177 | 26,9 % | 20,8 % | 18,5 % | admisible |
| β\* = 0,591 | 55,1 % | 46,6 % | 43,0 % | admisible |
| 3 β\* = 1,772 | 78,7 % | 72,4 % | 69,4 % | admisible, al borde en apertura |

Por política el margen es más estrecho: con 3 β\* la política agresiva tiene 81–87 % de peso de riesgo, y con 0,1 β\* la TWAP tiene 3–5 %.

R_E medio por episodio (CLP por acción) en apertura:

| β | Agresiva | TWAP | Pasiva | Ranking |
|---|---:|---:|---:|---|
| 0 | −10,87 | −9,70 | −10,92 | TWAP > agresiva > pasiva |
| 0,1 β\* | −13,29 | −10,17 | −11,89 | TWAP > pasiva > agresiva |
| β\* | −35,13 | −14,37 | −20,65 | TWAP > pasiva > agresiva |
| 3 β\* | −83,65 | −23,72 | −40,12 | TWAP > pasiva > agresiva |

El slippage (18,2 / 17,7 / 18,4 bps en apertura) y el cumplimiento (100 % / 92 % / 100 %) no dependen de β. El ranking cambia con β en apertura y media jornada (la agresiva pasa del segundo al tercer lugar ya con 0,1 β\*) y no cambia en cierre.

### 5.2 Por qué el resultado del fallback no fija β

**El fallback Poisson no sirve para calibrar el nivel de β.** Su P_mid se mueve ≈ 0,19–0,21 CLP por paso, contra 3,9–6,4 CLP del prior (que sale de la volatilidad real). La σ² de la ventana, una vez que deja el prior, es 157–479 veces menor que el prior:

| Tramo | Prior (CLP²) | σ² mediana de la ventana (CLP²) | Razón |
|---|---:|---:|---:|
| Apertura | 41,08 | 0,086 | 479 |
| Media jornada | 17,79 | 0,073 | 244 |
| Cierre | 15,51 | 0,099 | 157 |

En el fallback el término de riesgo pesa casi solo en los cuatro primeros pasos del episodio, mientras rige el prior. Por eso la política agresiva, que ejecuta todo en el primer paso, es la más castigada: el barrido mide el efecto "ejecutar antes de que la ventana se llene", no "ejecutar cuando el precio está volátil". β\* queda determinado por el prior y por cuánto se ejecuta bajo él.

**Otras dos limitaciones del fallback que afectan la lectura:**

- *Convención del nivel de precio invertida.* El contrato (`spaces.py`, `abides_bridge.py`) dice que el nivel 0 es el más pasivo y el 7 el más agresivo. `PoissonLOBSimulator.execute_limit_buy` usa la probabilidad de llenado `1 − nivel/8`: el nivel 0 se llena siempre y el 7 casi nunca. La política pasiva usa el nivel 7 en el fallback y el 0 en ABIDES (`NIVEL_PASIVO`). No se modificó el simulador.
- *Una LIMIT llenada paga como una MARKET.* En el fallback una orden límite que se llena barre el lado ask igual que una de mercado, así que nunca compra bajo el mid: el término de precio es siempre negativo y las políticas se diferencian solo por cuándo y cuánto barren.

### 5.3 Resultado en ABIDES calibrado

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

### 5.4 Qué mide realmente el término de riesgo

| Tramo | Prior (CLP²) | σ² media al ejecutar: agresiva | pasiva | TWAP |
|---|---:|---:|---:|---:|
| Apertura | 41,1 | 40,3 | 36,7 | 52,7 |
| Media jornada | 17,8 | 17,7 | 23,9 | 58,1 |
| Cierre | 15,5 | 15,3 | 17,6 | 25,4 |

Las políticas agresiva y pasiva terminan en los primeros pasos, cuando todavía rige el prior. La TWAP reparte la ejecución en 30 pasos y ve la ventana llena, cuya varianza es 1,3–3,3 veces el prior. Eso **no** refleja un mercado más volátil: es la propiedad descrita en §2. La varianza del *nivel* del precio en una ventana de *n* puntos crece como (n + 1)/6 veces la varianza de un paso, de 1× con 5 puntos a 3,5× con 20.

**Consecuencia: tal como está definido, el término de riesgo castiga ejecutar tarde durante los primeros 20 pasos del episodio**, con independencia del estado del mercado. Eso contradice la interpretación de §3 (el riesgo no debería penalizar la espera) y explica por qué la TWAP pierde posiciones al subir β.

### 5.5 Decisión abierta sobre σ²

Dos formas de quitar ese efecto, ninguna implementada:

- **Normalizar por el largo de la ventana:** usar σ²·6/(n + 1), que estima la varianza de un paso para cualquier *n* y es comparable con el prior. Es el cambio mínimo.
- **Usar la varianza de los incrementos del mid** en vez de la del nivel. No depende de *n*, pero se aparta de la redacción del Título I ("varianza del precio").

Con cualquiera de las dos β\* sube (σ² medio baja) y hay que repetir el barrido. Se mantuvo la definición del plan hasta decidirlo con el equipo, porque cambia la recompensa que verá PPO.

### 5.6 Recomendación

- **Rango para la fase 2: β ∈ [0,0046; 0,046] CLP⁻¹** (0,1 β\* a β\*). Se deja fuera 3 β\*: aunque pasa la regla por tramo, la política pasiva queda con 86–90 % de peso de riesgo y la TWAP con 80–85 %.
- **Finalistas sugeridos:** 0,3 β\* = 0,014 y β\* = 0,046.
- **Condición:** estos valores valen para la definición actual de σ². Si se adopta la normalización de §5.5 hay que recalcularlos.
- `BETA_RIESGO_EJECUTOR` se mantiene en 0,0 hasta la fase 2.

## 6. Pendientes

1. **Definición de σ²** (§5.5): decidir si se normaliza por el largo de la ventana y, si se hace, repetir el barrido.
2. **Fase 2 (PPO).** Corridas cortas con 2–3 β finalistas y elección por IS y cumplimiento. Depende de la 2.2.1 (Mauricio); si se atrasa pasa al Sprint 5.
3. **Escala.** Confirmación de Mauricio del default `por_accion_slice`.
4. **P_mid de referencia.** El fallback usa el mid previo a la ejecución y `ExecutionEnv27` el del despertar siguiente, posterior a los fills (así estaba antes de esta tarea; no se cambió para no romper la regresión con β = 0). Con una orden de mercado grande el mid posterior ya incorpora parte del impacto y subestima el costo. Conviene unificarlo en el mid previo.
5. **Schema.** `SE_schema.json` lista β en `pending_calibration`. Cuando β quede fijado, propuesta para el equipo: reemplazar esa entrada por el valor, la ventana W = 20 y la escala. No se modificó el schema.

## 7. Reproducción

```bash
python scripts/beta_sweep.py --seeds 20            # fallback Poisson, local
pytest tests/test_reward_utils.py tests/test_beta_sweep.py

# Colab
python scripts/colab/beta_sweep_abides.py --calibrated-json <dir>/rmsc04_ipsa_FALABELLA_2026-08-23.json --out-dir <dir>
```
