# `src/features/build_sm_features.py`

Script de la tarea 1.2.2 (Sprint 2): calcula las 4 variables del vector de
estado del Agente Maestro (`S_M`) derivables de OHLCV — `tau_t`,
`volatilidad`, `vol_promedio`, `sesion` — y deja explícitas las otras 3
(`q_t`, `n_slices`, `OBI_agregado`), que calculan en runtime el entorno de
simulación y ABIDES-Gym (Sprint 3, tareas 2.1.1/2.1.4/1.2.3/1.2.4 de MR).

Contrato: [`docs/schemas/SM_schema.json`](../../docs/schemas/SM_schema.json)
(dueño Paolo Sepúlveda). `Box(shape=(7,), dtype=float32)`, orden de índice
0..6: `q_t, tau_t, n_slices, volatilidad, vol_promedio, OBI_agregado, sesion`.

## 1. Cómo ejecutarlo

Parte del output de `src/data/clean_ohlcv.py` (tarea 1.2.1).

```bash
docker compose run --rm slippage python src/features/build_sm_features.py                        # autodetecta el ultimo clean_5m_<fecha>
docker compose run --rm slippage python src/features/build_sm_features.py --dry-run               # solo calcula e imprime el resumen
docker compose run --rm slippage python src/features/build_sm_features.py --plot-ticker FALABELLA # + graficos de sanidad
```

| Flag | Qué hace |
|---|---|
| `--input-dir` | Directorio `clean_5m_<fecha>` (salida de 1.2.1). Default: el más reciente |
| `--output-dir` | Default: `data/processed/sm_features_<fecha>` (misma fecha del input) |
| `--dry-run` | Corre todo el cálculo, no escribe archivos |
| `--plot-ticker TICKER` | Genera los 2 gráficos de sanidad intradiarios + corre los sanity checks para ese ticker (ej. `FALABELLA`) |

## 2. Qué genera y dónde queda

```
data/processed/sm_features_<fecha>/     # gitignored, se comparte por Drive
├── <TICKER>.parquet                    # timestamp + 7 cols del schema + cols _raw de referencia
├── _combined.parquet
├── scaler_params.json                  # copia de 1.2.1, extendido con volatilidad/vol_promedio por ticker
└── sm_features_report.json             # estadisticos por variable, diagnostico FALABELLA, sanity checks

results/sprint2/                        # gitignored, solo con --plot-ticker
├── <TICKER>_volumen_intradiario.png
└── <TICKER>_volatilidad_intradiario.png
```

Columnas de cada `<TICKER>.parquet`, en este orden:

| Columna | Fuente / cómo se calcula |
|---|---|
| `timestamp` | = `datetime_santiago` de 1.2.1 |
| `q_t` | **NaN** — lo calcula el entorno en runtime (`(Q_total - Q_ejecutado) / Q_total`), tarea 2.1.1/2.1.4 de MR |
| `tau_t` | `(t - 09:30_del_dia) / 390 min` |
| `n_slices` | **NaN** — lo calcula el entorno en runtime (`slices_enviados / 13`), tarea 2.1.1/2.1.4 de MR |
| `volatilidad` | `close_raw.rolling(6, min_periods=6).std()` por (ticker, día), `MinMaxScaler` por ticker |
| `vol_promedio` | `volume_raw.rolling(6, min_periods=6).mean()` por (ticker, día), `MinMaxScaler` por ticker |
| `OBI_agregado` | **placeholder `0.0`** — viene de ABIDES-Gym, tareas 1.2.3/1.2.4 de MR (aún no integradas) |
| `sesion` | `[9,11)→0.0`, `[11,14)→0.5`, `[14,16]→1.0` (cortes de hora exacta, ver nota abajo) |
| `close_raw`, `volume_raw` | pass-through de 1.2.1, para implementation shortfall en CLP reales |
| `volatilidad_raw`, `vol_promedio_raw` | valor pre-`MinMaxScaler` de `volatilidad`/`vol_promedio` |
| `volatilidad_raw_min_obs` | **diagnóstico**, ver sección 4 — NUNCA se usa como input del Maestro |
| `is_imputed` | pass-through de 1.2.1 |

## 3. Decisiones tomadas

| Decisión | Elección | Por qué |
|---|---|---|
| Cortes de `sesion` | Hora exacta 11:00/14:00 (no 11:30) | Sigue `docs/arquitectura_entorno_simulacion.md` §4.1 (Paolo, dueño del schema), que es la especificación de implementación para Sprint 3. Decisión confirmada con BF antes de escribir código. |
| `min_periods` del rolling | `6` (ventana completa exigida) | Las primeras 5 velas de cada día quedan con NaN explícito en `volatilidad`/`vol_promedio` y **se conservan** en el output — análogo a los placeholders de `q_t`/`n_slices`, y coherente con que el reporte pide "% de NaN" por variable. |
| Agrupación del rolling | `groupby(ticker, día).transform(...)`, `rolling(center=False)` | El rolling nunca cruza días ni tickers (sin esto se contaminaría la volatilidad de apertura con el cierre del día anterior) y nunca mira al futuro. |
| Clip de `MinMaxScaler` a `[0,1]` | `np.clip` después de `transform()` | Bug encontrado en desarrollo: el punto exacto que define `data_max_` puede transformar a `1.0000000000000002` por redondeo de float64, lo que rompería la validación estricta de `gymnasium.spaces.Box(high=1.0)` en Sprint 3. Mismo fix aplicado en `clean_ohlcv.py`. |

## 4. Diagnóstico de volatilidad "real" vs. "con imputados"

Decisión del checkpoint de la tarea 1.2.1 (columna `is_imputed`): además de
la `volatilidad` oficial (rolling sobre toda la serie, incluyendo velas
rellenadas por ffill/bfill), se calcula `volatilidad_raw_min_obs`: el mismo
rolling, pero solo con velas realmente observadas (`is_imputed == False`),
exigiendo al menos 4 de 6. Como las velas imputadas repiten el último precio
(variación cero), la oficial tiende a **subestimar** la volatilidad real.
`sm_features_report.json["volatility_diagnostic_falabella"]` reporta la
diferencia media y máxima entre ambas para FALABELLA — evidencia para el
Sprint Review. `volatilidad_raw_min_obs` es solo diagnóstico, nunca se
normaliza ni se usa como input del vector `S_M`.

## 5. Gráficos y sanity checks (`--plot-ticker`)

Se generan 2 PNG por ticker en `results/sprint2/` (perfil intradiario de
volumen y de volatilidad, promediados por bucket de 5 min de tiempo-de-día)
y se corren 2 chequeos automáticos: el volumen promedio máximo debe caer en
las últimas 2 barras de la jornada (subasta de cierre), y la volatilidad
promedio debe seguir una forma en U invertida (mínimo entre 13:00-15:00,
apertura y cierre por encima de la media jornada). Si alguno falla, se
imprime un banner `[SANITY CHECK] FALLO` y queda registrado en
`sm_features_report.json["sanity_checks"]`, pero el pipeline **no se
detiene** (gate humano, mismo criterio que el `tier` de cobertura de 1.2.1).

**Nota de proceso**: la primera corrida de este chequeo para FALABELLA SÍ
falló, y llevó a descubrir y corregir un bug real en `clean_ohlcv.py` (ver
`src/data/README.md`, sección "Por qué el filtro llega hasta las 16:00").
Tras el fix, ambos chequeos pasan (`pass: true`) para FALABELLA en la
corrida de referencia `2026-08-23`.

## 6. Nota de discrepancia (a levantar en Sprint Review)

`src/envs/maestro_ejecutor_protocol.py` (pseudocódigo de referencia de
Paolo, no ejecutable) menciona `data/processed/vector_estado_SM_*.csv` como
nombre informal del output de esta tarea. **No es el contrato real**: el
formato acordado con BF es parquet (`sm_features_<fecha>/<TICKER>.parquet` +
`_combined.parquet`), no CSV. Se señala aquí para que no se tome como
referencia al integrar en Sprint 3.

## 7. Handoff a Sprint 3

**Para MR (tareas 2.1.1 / 2.1.4 — entorno de simulación y red del Maestro):**

- Los parquet están en `data/processed/sm_features_<fecha>/`, ya en el orden
  de columnas del `Box(shape=(7,))` (`q_t, tau_t, n_slices, volatilidad,
  vol_promedio, OBI_agregado, sesion`, más `timestamp` al inicio).
- `q_t` y `n_slices` vienen en **NaN**: no los inventes, calcúlalos en
  runtime como especifica `SM_schema.json` / `docs/arquitectura_entorno_simulacion.md` §4.1.
- `OBI_agregado` viene en **`0.0`** (placeholder): reemplázalo por
  `ABIDES-Gym.get_market_imbalance()` cuando integres 1.2.3/1.2.4.
- Para invertir la normalización de `volatilidad`/`vol_promedio` (o de
  cualquier columna de 1.2.1) sin recalcular nada, usa
  `scaler_params.json["scalers"][<TICKER>][<col>]` (`data_min_`,
  `data_max_`, `scale_`, `min_` — mismos atributos que expone
  `sklearn.preprocessing.MinMaxScaler`), o directamente las columnas `_raw`
  que ya vienen en el parquet.

**Para PS (tarea 1.2.5 — validación estadística):**

- `sm_features_report.json` trae min/max/media/std/%NaN por variable y por
  ticker, más el diagnóstico de volatilidad de FALABELLA (sección 4) — insumo
  directo para la validación.
- `cleaning_report.json` (de 1.2.1) trae el detalle de imputación y el
  campo `tier` por ticker (A/B según cobertura pre-fill ≥60%).
