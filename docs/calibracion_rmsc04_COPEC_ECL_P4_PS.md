# Calibración de `rmsc04` para COPEC y ECL (P4)

**Elaborado por:** Paolo Sepúlveda (PS) con apoyo de Claude Code, 19 oct 2026. **Pendiente de revisión por:** Benjamín Farias (BF), responsable de la calibración de `rmsc04` (2.2.4).

Archivos que entrega este documento:

- `data/calibration/rmsc04_ipsa_COPEC_2026-08-23.json` y `data/calibration/rmsc04_ipsa_ECL_2026-08-23.json`. **Reemplazan** la calibración de COPEC subida el 18 oct (PR #35), que usaba los 12 agentes de momentum por defecto y producía corridas desbocadas (§2).
- `docs/validacion_formal_2.2.5_COPEC_PS.md` y `docs/validacion_formal_2.2.5_ECL_PS.md`, con sus JSON y figuras en `data/analysis/`; las corridas crudas están en `data/colab_resultados/`.
- `scripts/colab/diagnostico_deriva_ps.py` y `diagnostico_deriva2_ps.py` (diagnóstico de la §2) y las especificaciones de grilla `scripts/colab/grid_specs/p5_{copec,ecl}_momentum.json`.

## 1. Resumen

| | COPEC | ECL |
|---|---|---|
| Configuración | 500 agentes de ruido, `lambda_a` 2,85e-12, `mm_pov` 0,025, ventana del market maker 90, **3 agentes de momentum** | igual, con ventana 30 |
| Corridas desbocadas (\|movimiento del tramo\| > 10 %), 30 semillas | **0 de 30** en los 3 tramos (antes 0 / 7 / 7) | **0 de 30** en los 3 tramos (antes 9 / 13 / 13) |
| Volatilidad de 5 min frente a la real | +0,8 % / −7,4 % / −0,4 % | −1,9 % / −1,8 % / −3,6 % |
| KS, D / D crítico | 1,43 / 1,75 / 2,40 | 1,66 / 2,22 / 1,85 |
| Veredicto formal | **NO VÁLIDO** según el criterio literal del plan (el KS rechaza) | **NO VÁLIDO** según el criterio literal del plan (el KS rechaza) |
| Criterios C (tamaño de efecto) y D (patrón entre tramos) | se cumplen | se cumplen |

Orden de los tramos: apertura / media jornada / cierre. FALABELLA, calibrada antes con 1000 agentes de ruido, no tiene el problema de §2 (0 de 30 corridas desbocadas en los tres tramos) y no se toca.

## 2. Hallazgo: con 250 agentes de ruido, los agentes de momentum desestabilizan el mercado

La calibración de COPEC y ECL con la grilla de actividad baja (250 agentes de ruido) dejaba el resto de `rmsc04` en su valor por defecto, incluidos **12 agentes de momentum** (agentes del *simulador*, no del sistema Maestro-Ejecutores). Con 30 semillas por tramo:

| Con 12 agentes de momentum | Corridas con \|movimiento\| > 10 % del tramo | Mayor movimiento |
|---|---|---|
| ECL (apertura / media jornada / cierre) | 9 / 13 / 13 de 30 | +12 % y −15 % / +19 % y −31 % / +15 % y −34 % |
| COPEC | 0 / 7 / 7 de 30 | hasta ±9 % / +11 % y −13 % / +8 % y −12 % |
| FALABELLA (1000 agentes de ruido) | 0 / 0 / 0 de 30 | ±5 % |

Esas corridas son las lentas (55–69 s frente a 6 s) y las de mayor volumen. Por eso la volatilidad agrupada de la calibración (10 semillas) se veía mala y la media por corrida de la validación (30 semillas) se veía buena: eran dos medidas distintas del mismo simulador, y la diferencia la hacía la deriva de cada corrida.

**Diagnóstico** (ECL, media jornada, 5 semillas por variante, un cambio por vez; Colab 18 oct):

| Variante | Desbocadas | Lectura |
|---|:---:|---|
| control (calibración con 12 momentum) | 4 de 5 | el precio se mueve +19 % o −26 %; el oráculo (valor fundamental) casi no se mueve (±2 %) |
| `mm_pov` 0,005 | 4 de 5 | no es el market maker |
| `fund_vol` × 0,1 (oráculo casi quieto) | 4 de 5 | no es el valor fundamental |
| ventana `adaptive` del market maker | 0 de 5 | la volatilidad cae a 4–13 bps (la real es ~35): apaga el mercado, no se usa |
| **sin agentes de momentum** | **0 de 5** | movimientos < 1 % y corridas de 20 s |

En las cuatro corridas desbocadas del control, los agentes de momentum terminan con una posición neta de 269 a 292 mil acciones en un sentido, y los agentes de valor (196 a 207 mil) y el market maker (71 a 85 mil) con la contraria: una espiral de compras (o ventas) que el resto no alcanza a frenar.

Segunda ronda (8 semillas): `momentum_3` 0 de 8 desbocadas, `momentum_6` 0 de 8, `momentum_0` con `fund_vol` × 1,5 0 de 8 pero con un volumen de 24–37 mil (el momentum aporta volumen), y `momentum_3` con `fund_vol` × 1,3 0 de 8 con volatilidad media 33,5 bps (la real es 35,2). Con la corrección el precio vuelve a seguir al oráculo (por ejemplo, en `momentum_3` el movimiento del tramo es +2,1 % y el del oráculo +1,9 %).

**Lectura (inferencia, no probada):** FALABELLA no se desboca porque 1000 agentes de ruido diluyen a los 12 de momentum; con 250, el momentum pesa cuatro veces más. La grilla de calibración nunca varió `num_momentum_agents`, así que no podía evitarlo.

## 3. Corrección aplicada

1. **`num_momentum_agents = 3`** en vez de 12: la misma proporción de agentes que FALABELLA (12 con 1000 de ruido ⇒ 3 con 250).
2. Grilla corta (3 semillas por combinación, `scripts/colab/grid_specs/p5_*_momentum.json`): momentum {3, 6} × actividad {250 ruido y `lambda_a` 1,425e-12; 500 y 2,85e-12}, con el market maker fijo en lo que ya había ganado (ventana 90 en COPEC y 30 en ECL, `mm_pov` 0,025). **Ganó momentum 3 con 500 agentes de ruido** en los dos activos. No se hizo el refinamiento (ver §6).
3. **Ajuste de `fund_vol` por tramo.** Con menos momentum la volatilidad simulada quedaba 21–32 % bajo la real; como el precio ahora sigue al oráculo, `fund_vol` se escala por tramo:

| | apertura | media jornada | cierre |
|---|:---:|:---:|:---:|
| COPEC | × 1,45 | × 1,30 | × 1,48 |
| ECL | × 1,37 | × 1,27 | × 1,30 |

Los factores son (volatilidad real) / (volatilidad simulada por corrida) de las 30 semillas sin ajuste. Los valores anteriores de `fund_vol` quedan guardados en `metadata.ajuste_fund_vol.fund_vol_antes` de cada JSON, así que el ajuste es reversible.

## 4. Resultados con 30 semillas (201–230)

Valores por tramo: apertura / media jornada / cierre.

| | COPEC | ECL |
|---|---|---|
| Volatilidad simulada por corrida (bps) | 32,1 / 19,8 / 24,6 | 41,0 / 34,5 / 34,9 |
| Volatilidad real (bps) | 31,8 / 21,4 / 24,8 | 41,8 / 35,2 / 36,2 |
| p (Wilcoxon, 1 muestra) | 0,968 / **0,031** / 0,371 | 0,503 / 0,465 / 0,124 |
| Mayor \|movimiento\| de un tramo | 6,0 % / 4,4 % / 3,9 % | 6,3 % / 5,8 % / 4,9 % |
| KS, D / D crítico | 1,43 / 1,75 / 2,40 | 1,66 / 2,22 / 1,85 |
| g de Hedges (\|retorno\|) | 0,18 / 0,11 / 0,27 | 0,28 / 0,20 / 0,22 |
| Mediana de \|retorno\| sim. / real (bps) | 16,9 / 11,0 / 14,0 frente a 12,5 / 7,9 / 7,1 | 25,3 / 21,4 / 21,4 frente a 10,0 / 12,3 / 11,4 |
| Volumen mediano por vela, sim. frente al real | −15,0 % / −34,6 % / −44,7 % | −19,9 % / −39,4 % / −43,0 % |
| Participación de volumen, sim. / real | 0,294 / 0,376 / 0,330 frente a 0,200 / 0,358 / 0,359 | 0,297 / 0,377 / 0,326 frente a 0,172 / 0,332 / 0,438 |
| Spread mediano simulado (bps) | 0,34 / 0,33 / 0,33 | 1,10 / 1,06 / 0,59 |
| Retornos en cero, sim. / real | 0,3 / 0,9 / 0,4 % frente a 10,6 / 10,2 / 11,9 % | 0,6 / 1,0 / 0,7 % frente a 22,4 / 18,2 / 17,0 % |

**Comparación con las otras versiones** (mismas 30 semillas): con 12 momentum, los g de Hedges eran 0,21 / 0,54 / 0,62 (COPEC) y 0,42 / 0,67 / 0,67 (ECL), y el KS 1,72 / 2,60 / 2,97 y 1,87 / 2,62 / 2,60. Con 3 momentum **sin** el ajuste de `fund_vol` el KS era 1,66 / 1,67 / 1,72 (COPEC) y 1,53 / 2,08 / 1,80 (ECL), y los |g| de 0,15 / 0,05 / 0,02 y 0,05 / 0,00 / 0,04.

**Lo que se gana y lo que se pierde con el ajuste de `fund_vol`:** iguala la volatilidad (el objetivo principal de la calibración 2.2.4), pero no mejora el KS (queda igual o algo peor) y hace que el retorno típico sea mayor que el real (g de Hedges de 0,05 a 0,28). Se eligió igualar la volatilidad. La versión sin ajuste queda recuperable con `fund_vol_antes`.

## 5. Límites que se declaran

- **El KS rechaza** en los seis tramos (entre 1,4 y 2,4 veces el D crítico). El criterio literal del plan no se cumple, igual que en FALABELLA (1,0 a 1,8 veces). Los efectos son triviales o pequeños (g < 0,3).
- **Volumen por vela 15 a 45 % bajo el real**, sobre todo hacia el cierre. La participación de volumen de la apertura queda 47–73 % sobre la real.
- **Spread** simulado de 0,3 a 1,1 bps, por debajo del rango de los proxies reales (el IS absoluto queda subestimado; las comparaciones entre estrategias siguen siendo válidas).
- **Retornos en cero** (10–22 % en los datos reales) y **colas pesadas** (curtosis real hasta 47 en el cierre de COPEC) no se reproducen.
- **COPEC, media jornada:** la volatilidad queda 7,4 % bajo la real (p = 0,031), el único tramo donde la diferencia es significativa.
- **El ajuste de `fund_vol` se calculó con las mismas semillas (201–230) con las que se validó** (números aleatorios comunes), así que la cercanía de la volatilidad es en parte por construcción. Una comprobación independiente con otras semillas (por ejemplo `--seed-base 300`) queda recomendada y no se hizo.
- **Integración con `EjecutorEnvAbides`:** las validaciones llaman directamente a `rmsc04.build_config` con estos parámetros (incluido `num_momentum_agents`). Después se probó el entorno de ejecución (`make_calibrated_env_factory`) en Colab para COPEC y ECL en los tres tramos: crea el entorno, hace reset y avanza 4 pasos sin errores. Es una prueba de humo con la acción de esperar, no un test de ejecución de órdenes.

## 6. Desviaciones respecto de la configuración estándar de `rmsc04`

1. `num_momentum_agents = 3` en lugar de los 12 por defecto, en COPEC y ECL (FALABELLA conserva 12).
2. `fund_vol` multiplicado por los factores de la §3.
3. Sin el refinamiento de la grilla: `refine_candidates` multiplica los parámetros numéricos por un factor y para `num_momentum_agents` daría 4,5 o 2,0 agentes. Se dejó fuera con un cambio en `src/envs/rmsc04_search.py` (`_NO_REFINAR`) y un test.

## 7. Cómo usar

```python
from src.envs.calibrate_rmsc04_ipsa import load_abides_kwargs
from src.envs.abides_ejecutor_env import make_calibrated_env_factory

kwargs = load_abides_kwargs("data/calibration/rmsc04_ipsa_COPEC_2026-08-23.json")  # por tramo
factory = make_calibrated_env_factory("data/calibration/rmsc04_ipsa_ECL_2026-08-23.json", ticker="ECL")
```

## 8. Reproducir

Cuaderno de Colab (preparación: celdas 1 a 7): diagnóstico (`scripts/colab/diagnostico_deriva_ps.py`, `diagnostico_deriva2_ps.py`), grilla (`rmsc04_grid_search.py --grid-spec scripts/colab/grid_specs/p5_<activo>_momentum.json`), validación de 10 semillas (`rmsc04_validate.py`, sin `--refine`), ajuste de `fund_vol` (§3) y validación de 30 semillas (`validacion_2_2_5_ps.py`). Los resultados intermedios están en la carpeta de Drive `slippage_colab/resultados/p5` y `p5b`.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
