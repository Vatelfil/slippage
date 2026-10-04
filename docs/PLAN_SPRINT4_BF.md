# Plan de desarrollo Sprint 4 — Benjamín Farias (BF)

**Tareas:** 2.2.4 Calibración RMSC04 con IPSA (16 h) · 2.2.3 Función de recompensa de los Ejecutores (20 h)
**Ventana:** 30 sept – 9 oct 2026 (Sprint Review el 9 oct; Sprint 5 arranca el 12 oct)
**Entorno:** código y tests en local con Claude Code; simulaciones ABIDES en Google Colab (Python 3.9 vía condacolab)
**Base:** `SEGUIMIENTO_CIERRE_SPRINT4_30SEP.md` (Paolo, 30 sept) y el notebook `tesis_prueba_uno.ipynb`, ambos contrastados con `origin/main` (merge del PR #18, commit `3189789`).

---

## 0. Hallazgos verificados antes de planificar (30 sept)

Todo lo de esta sección se reprodujo hoy en un entorno Python 3.9.23 con la misma receta de Colab, ABIDES instalado desde `jpmorganchase/abides-jpmc-public` y el repo `slippage` en `main`.

| # | Hallazgo | Impacto | Acción |
|---|---|---|---|
| H1 | **La Celda 3 del notebook falla** (`gym==0.18.0`: `metadata-generation-failed`). El entorno conda nuevo trae pip 25.2; el pin `pip==23.3.2` del mismo comando no rige hasta que termina la instalación, y `gym 0.18.0` tiene un requisito con versión mal formada (`opencv-python>=3.`) que pip/setuptools modernos rechazan. Además `gym 0.18.0` exige `Pillow<=7.2.0`, que no tiene wheel para Python 3.9 y no compila sin `libjpeg`. Por último, `ray 1.7.0` falla al importar con protobuf ≥ 4. | Sin esto, ABIDES no se instala y todo lo demás falla en cascada. | Receta corregida y **probada** (ver §4): 1) fijar pip/setuptools/wheel solos; 2) `cython<3` + `numpy==1.22.0`; 3) `gym==0.18.0 --no-deps --no-build-isolation`; 4) resto con `--no-build-isolation` + `Pillow<10` + `protobuf==3.20.3`. Resultado: gym 0.18.0, numpy 1.22.0, pandas 1.2.4, ray 1.7.0 y gymnasium 0.29.1; `src/envs/test_abides.py` corre OK. |
| H2 | **Las Celdas 5-7 fallan porque el repo nunca se clonó** (`/content/slippage` no existe). Además, la rama `feature/sprint4-base-validacion-ps` ya está mergeada en `main` (PR #18). | — | Clonar `main` (o la rama de trabajo BF) antes de `%cd`. |
| H3 | **Los `.parquet` no están en git** (`.gitignore`). En Colab, `calibrate_rmsc04_ipsa.py` no encuentra `_combined.parquet`. Su default apunta a `clean_5m_2026-09-23` (snapshot de Paolo), que tú no tienes; tú tienes `2026-08-23` (en el zip de respaldo) y `2026-09-27`. | `r_bar` no se puede calcular en Colab. | Subir `backups/snapshot_2026-08-23.zip` (y el de 09-27) a Drive y descomprimirlos en la raíz del repo en Colab; agregar el argumento `--snapshot`. **Usar 2026-08-23 como principal**, por ser el mismo período de λ y de `objetivos_validacion`, y 2026-09-27 como chequeo de robustez. |
| H4 | **Tu rama `feature/2.1.3b-robustez-BF` no está en `main`.** Ahí viven `src/config/market_params.py`, `ks_critical_value`, `build_validation_targets` y el bloque `objetivos_validacion` del JSON, que es justamente lo que 2.2.4 tiene que reproducir. El merge contra `main` es limpio (se probó `git merge --no-commit`). | Sin esto, 2.2.4 no tiene contra qué validar. | **Paso 0:** PR de 2.1.3b → `main` y crear la rama 2.2.4 desde ese `main`. |
| H5 | **`fund_vol` heurístico de la plantilla está mal en unidades (bug).** El oráculo de ABIDES (`SparseMeanRevertingOracle`) es un OU con `Var ≈ fund_vol² · Δt` y Δt en **nanosegundos**, por lo que `fund_vol` está en centavos/√ns. La plantilla usa `σ_5min · r_bar`, que es un desvío en centavos por 5 min, y queda ~547.723× (√(300·10⁹)) más grande. | Con el valor actual el precio **explota**. | Fórmula corregida: `fund_vol = σ_5min · r_bar / √(300·10⁹)`. |
| H6 | **El spread simulado queda en ~1 tick.** El tick de ABIDES es 1 unidad de cuenta. Con centavos de CLP (r_bar = 630.055), 1 tick ≈ 0,016 bps y el spread mediano da 0,14 bps, contra ~35 bps del estimador Roll real de FALABELLA en apertura. Con "1 unidad = 1 CLP" (r_bar = 6.301), 1 tick ≈ 1,6 bps y el spread da 1,61 bps. | La unidad de cuenta y los parámetros del market maker son las palancas reales del spread. | Decisión metodológica explícita (§1, A2) más búsqueda de `mm_*`. **Verificar la tabla de ticks de la Bolsa de Santiago** para el rango de precio de FALABELLA. |
| H7 | **R_E no tiene la misma escala en los dos entornos.** `fallback_poisson_env.py` usa CLP sin normalizar; `abides_bridge.step_reward` usa centavos ÷ `parent_order_size`. Además, `ExecutionEnv27.raw_state_to_reward` **no le pasa `sigma2`** a `step_reward` (queda en 0 también en ABIDES, no solo en el fallback). | Un β calibrado en un entorno no sirve en el otro, y PPO (Mauricio) ve escalas distintas. | Helper único de recompensa (§2) y convención de escala acordada con Mauricio. |
| H8 | **Tiempos de simulación:** 30 min de mercado ≈ 5-6 s y un día completo (09:30-16:00) ≈ 40 s con RMSC04 por defecto. | Una grilla de ~30 configuraciones × 3 semillas cabe en 1-2 h de Colab. | Diseñar la búsqueda con ese presupuesto. |

**Experimento de H5/H6** (FALABELLA, r_bar de la mediana del snapshot 09-27 = 6.300,55 CLP; σ_5min apertura = 0,003395; RMSC04 09:30-10:30; seed 1):

| Configuración | fund_vol | Vol. 5 min del mid (bps) | Spread mediano (bps) | Mid final |
|---|---|---|---|---|
| Default rmsc04 | 5e-5 | 0,3 | 0,02 | 6.298 CLP |
| Heurística actual (plantilla) | 2.139 | **8.044** | 0,01 | **17.194.199 CLP** (precios negativos descartados) |
| Corregida, centavos | 0,0039 | 22,8–28,5 (según corrida) | 0,14 | 6.184 CLP |
| Corregida, 1 unidad = 1 CLP | 3,9e-5 | **35,9** (real: 34,0) | 1,61 | ≈ 6.200 CLP |

Conclusión: con la conversión de unidades corregida, la volatilidad ya queda en el orden de magnitud correcto **sin buscar nada**. Lo que de verdad falta calibrar es el spread y la actividad (§1, bloque B).

---

## 1. Tarea 2.2.4 — Calibración de RMSC04 con IPSA

**Activo:** FALABELLA (MVP). Si sobra tiempo, extender a 1-2 tickers tier A como chequeo.
**Objetivos de validación:** `objetivos_validacion["FALABELLA"]` de `poisson_params_2026-08-23.json` (rama 2.1.3b): por tramo, `volatilidad_bps`, `spread_roll_bps`, `spread_cs_bps`, `spread_hl_bps`, `participacion_volumen_dia`, `lambda_total`, `volumen_mediano_vela` y `ranking_observado`.
**Tramos:** `TRAMOS_EJECUTOR` de `market_params.py` (09:30-11:30 / 11:30-14:00 / 14:00-16:00), los mismos que `TRAMO_FIRST_INTERVAL` de ABIDES. *Nota:* `market_validation.py` (Paolo) corta a las 11:00. Dejarlo anotado, sin cambiarlo.

### Bloque A — Traducción directa (sin búsqueda)

- **A1 `r_bar`:** mediana de `close_raw` del snapshot elegido.
- **A2 Unidad de cuenta:** evaluar `centavos` (como hoy) y `1 unidad = 1 CLP`. Criterio de elección: que el tick de ABIDES quede lo más cerca posible del tick real de la Bolsa de Santiago en bps. Documentar la elección. `starting_cash`, `BridgeConfig.tick` y la escala de R_E deben seguir esa misma unidad.
- **A3 `fund_vol`:** `σ_5min · r_bar / √(300·10⁹)`, con σ por tramo (`obs_return_std`). Como `fund_vol` es único por simulación, se usa una **configuración por tramo**: cada Ejecutor corre su propio episodio y basta con que el tramo medido calce. Anotar la limitación: no es un σ intradiario variable.
- **A4 `kappa_oracle`:** test de razón de varianzas (Lo-MacKinlay, VR(q) con q = 2, 6, 12) sobre los retornos de 5 min reales por tramo. Si VR ≈ 1 (paseo aleatorio), se mantiene el default (vida media ≈ 48 días, sin reversión intradiaria) con esa justificación. Si VR < 1 y es significativa, `kappa_oracle = −ln(ρ̂)/Δt_ns`.
- **A5 `megashock_*`:** en principio, mantener el default y justificarlo midiendo la curtosis real de los retornos de 5 min frente a la simulada. Solo se entra en la búsqueda si la curtosis simulada queda muy por debajo.

### Bloque B — Búsqueda acotada (método de momentos simulado)

- **Parámetros libres:** `mm_spread_alpha`, `mm_num_ticks`, `mm_level_spacing`, `mm_pov` (spread y profundidad) y `num_noise_agents` / `lambda_a` (actividad y volumen). El resto queda fijo según A.
- **Momentos por tramo, medidos en el mercado de fondo sin nuestro agente:**
  - vol. de 5 min (bps);
  - spread mediano cotizado (bps), comparado contra Roll y CS reales. **Ojo:** ambos son *proxies* desde OHLCV y Roll sobreestima el spread cotizado, así que hay que reportar la comparación contra los dos;
  - participación de volumen por tramo;
  - rankings entre tramos.
- **Pérdida:** suma ponderada de errores relativos (log-ratio) por momento y tramo, más una penalización si los rankings robustos no coinciden. Según 2.1.3b, los robustos son "volatilidad máxima en la apertura" y "el volumen por vela crece durante el día".
- **Presupuesto:** grilla gruesa de ≤ 27 combinaciones × 3 semillas × día completo (≈ 1 h en Colab), seguida de un refinamiento local de ≤ 10 combinaciones.

### Bloque C — Validación

- **KS de 2 muestras** sobre retornos log de 5 min, simulado (≥ 10 semillas) contra real, por tramo. Reportar D, p y **D/D_crit** con `ks_critical_value`, igual que en la 2.1.3b.
- **Meta del plan oficial:** p > 0,05. Si no se alcanza, se informa como en la 2.1.3, cuando Poisson dio p ≈ 1e-8 con n grande: se da D/D_crit y el calce de los hechos estilizados, sin maquillar el resultado.
- **Antes/después para 2.2.5:** volver a correr `collect_abides_stats.py` y `compare_simulated_vs_real()` con la configuración calibrada. Para eso hay que hacer que `collect_abides_stats.py` acepte la configuración y reporte el spread también en bps (no solo normalizado). Paolo puede cerrar la comparación con ese JSON.

### Entregables de 2.2.4

- `src/envs/calibrate_rmsc04_ipsa.py`: fund_vol corregido, unidad de cuenta configurable, `--snapshot`, salida con el **dict limpio** (sin `_campos_pendientes`/`_metadata`) para usar en `background_config_extra_kvargs`.
- `src/envs/rmsc04_sim_stats.py`: corre RMSC04 standalone, extrae L1 y devuelve los momentos por tramo. Se separa la lógica pura (testeable sin ABIDES) de la que ejecuta ABIDES.
- `scripts/colab/rmsc04_grid_search.py` → `data/calibration/rmsc04_grid_FALABELLA_<fecha>.json`
- `scripts/colab/rmsc04_validate.py` → `data/calibration/rmsc04_ipsa_FALABELLA_<fecha>.json` (parámetros finales, momentos, KS y decisiones)
- `docs/calibracion_rmsc04_2.2.4_BF.md`: metodología, tabla de traducción Poisson → ABIDES, decisiones (unidad, tick, kappa, megashock), resultados, limitaciones y texto listo para el capítulo de Título II.
- Tests de la lógica pura (fórmulas de unidades, VR, pérdida, armado de config).

---

## 2. Tarea 2.2.3 — Recompensa de los Ejecutores

**Especificación (Título I §4.2.4):** `R_E = (P_mid_t − P_ejec_t) · q_ejec − β · σ²_precio · q_ejec`

### Diseño

- **σ²_precio:** varianza del `P_mid` en una ventana móvil **causal** de las últimas W decisiones (default W = 20, es decir, 10 min con pasos de 30 s), usando solo información hasta t-1 para no mirar el futuro. Mientras la ventana tiene menos de 5 puntos, se usa un *prior* del tramo: `(σ_5min · P_ref)² · (Δt_paso/300 s)`. Unidades: CLP² (o la unidad de cuenta de A2).
- **Interpretación (para la tesis):** como todo `q_slice` debe ejecutarse, el término de riesgo empuja a ejecutar en momentos de menor varianza. No penaliza la espera en sí; eso le corresponde a λ en R_M.
- **Helper único `src/envs/reward_utils.py`:** `RollingPriceVariance` y `executor_reward(p_mid, p_ejec, q_ejec, sigma2, beta, escala)`. Lo usan `fallback_poisson_env.py` y `ExecutionEnv27` (que pasa a enviar `sigma2` a `step_reward`). β y W salen de `market_params.py` (o del config compartido), no de constantes sueltas.
- **Escala común:** proponer a Mauricio "CLP por acción del slice" (R_E ÷ q_slice) en los dos entornos y dejar la convención escrita. Este punto se coordina con él porque afecta a PPO.

### Calibración de β

- **Escala de referencia:** `β* = E[|P_mid − P_ejec|] / E[σ²]`, que es el β con el que el término de riesgo pesa lo mismo que el de precio. Grilla: β ∈ {0; 0,1β*; 0,3β*; β*; 3β*}.
- **Fase 1 (ahora, sin PPO):** evaluar políticas heurísticas (agresiva MARKET, TWAP con LIMIT nivel medio, pasiva LIMIT nivel 0) bajo cada β. Primero en el fallback Poisson (local y rápido) y después en ABIDES calibrado (Colab). Se mide IS, % de cumplimiento, el aporte relativo del término de riesgo y si el ranking entre políticas cambia de forma razonable (más β favorece ejecutar en tramos o momentos de menor varianza). Se descartan los β en que el riesgo domina por completo (> 80 % de |R_E|) o no pesa nada (< 5 %).
- **Fase 2 (3-6 oct, cuando 2.2.1 corra):** corridas PPO cortas con 2-3 β finalistas; se elige por IS y cumplimiento.

### Entregables de 2.2.3

`reward_utils.py` + tests, ambos entornos actualizados, `scripts/beta_sweep.py` (local) y su variante para Colab, `data/calibration/beta_sweep_<fecha>.json` y `docs/recompensa_ejecutores_2.2.3_BF.md`.

---

## 3. Cronograma (30 sept – 9 oct)

| Día | Fecha | Local (Claude Code) | Colab |
|---|---|---|---|
| 1 | mié 30 sept | Paso 0: PR 2.1.3b → main; rama `feature/2.2.4-2.2.3-rmsc04-recompensa-BF`; subir los zips de snapshot a Drive | Notebook corregido: instalar y correr `test_abides.py` (smoke test) |
| 2 | jue 1 oct | A1-A5 + fix de fund_vol + `rmsc04_sim_stats.py` + tests | Experimento de unidades (centavos frente a CLP) y momentos con la configuración base |
| 3 | vie 2 oct | `reward_utils.py` + σ² en los dos entornos + tests (2.2.3) | Grilla gruesa (bloque B) |
| 4 | sáb 3 oct | Refinamiento + `rmsc04_validate.py`; β sweep fase 1 en el fallback Poisson | Refinamiento + KS con ≥ 10 semillas |
| 5 | lun 5 oct | Documento 2.2.4 (borrador) | `collect_abides_stats` con la config calibrada (antes/después 2.2.5); β sweep en ABIDES |
| 6 | mar 6 oct | β fase 2 con el PPO de Mauricio (si 2.2.1 está lista) | Corridas PPO cortas por β |
| 7 | mié 7 oct | Documento 2.2.3 + cerrar documento 2.2.4 | Reserva |
| 8-9 | 8-9 oct | Buffer, PR y material para el Sprint Review | — |

**Dependencias:**

- 2.2.4 es independiente.
- La fase 1 de 2.2.3 es independiente; la fase 2 depende de 2.2.1 (Mauricio).
- La escala de R_E se acuerda con Mauricio antes del día 3.
- El antes/después de 2.2.5 se le entrega a Paolo el día 5.

## 4. Flujo Colab (resumen)

1. Abrir `Colab_Sprint4_BF.ipynb` (incluido en esta entrega). Celda 1: `condacolab` reinicia el runtime; es normal.
2. Celdas 2-4: entorno `abides` (Python 3.9) con la receta corregida de H1 y ABIDES desde el repo de JPMorgan.
3. Celda 5: clonar `slippage` en la rama de trabajo BF. Celda 6: montar Drive y descomprimir los snapshots.
4. Las celdas siguientes corren los scripts de `scripts/colab/` vía `conda run -n abides`, y los JSON resultantes se copian a Drive y se descargan.
5. Los JSON vuelven al repo local y Claude Code los commitea y los analiza.

**Con Claude Code + Colab MCP** (opcional y recomendado): `claude mcp add colab-mcp -- uvx git+https://github.com/googlecolab/colab-mcp`. Con eso, Claude Code puede ejecutar celdas en un Colab abierto en tu navegador. Limitaciones: hay que aceptar la conexión en el navegador, el reinicio de runtime de condacolab requiere un clic manual y la conexión se pierde si se reinicia Claude Code.

## 5. Definición de terminado

- [ ] 2.1.3b mergeada en `main`.
- [ ] fund_vol corregido con test de unidades; unidad de cuenta elegida y documentada.
- [ ] Config calibrada de FALABELLA por tramo en JSON versionado, cargable vía `background_config_extra_kvargs`.
- [ ] KS por tramo (D, p, D/D_crit) y momentos sim frente a reales en una tabla; rankings robustos reproducidos o la discrepancia explicada.
- [ ] JSON del antes/después de 2.2.5 entregado a Paolo.
- [ ] σ²_precio real en los dos entornos, β calibrado (fase 1 como mínimo) y escala de R_E acordada.
- [ ] Docs 2.2.3 y 2.2.4, tests en verde, PR abierto y HANDOFF actualizado.

## 6. Riesgos

- **Colab desconecta en corridas largas.** Guardar resultados parciales en Drive tras cada configuración y hacer los scripts reanudables.
- **KS con p > 0,05 inalcanzable con n grande.** Se reporta D/D_crit, como en la 2.1.3b; se acuerda con la profesora que el criterio sea de forma y magnitud.
- **2.2.1 se atrasa.** β se cierra con la fase 1 y la fase 2 pasa al Sprint 5, documentado.
- **Spread real desconocido.** Roll/CS son proxies; el rango aceptable se define entre los dos y se declara como limitación.
