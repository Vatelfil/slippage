# Evidencia del pipeline de datos OHLCV IPSA — snapshot 2026-08-23

**Tareas:** 1.2.1 (limpieza) y 1.2.2 (features S_M) — Benjamín Farias (BF)
**Propósito:** dejar en Git evidencia verificable de que el pipeline de datos se ejecutó con datos reales, atendiendo el punto 3 del bloque "Bloqueado" de `DIAGNOSTICO_Y_PLAN_23SEP.md` (rama `fix/ps-conecta-redes-y-diagnostico`). Se versionan solo los reportes JSON y las figuras; los `.parquet` quedan fuera de Git (ver `.gitignore`).

Todas las cifras de este documento se leyeron de los JSON versionados; ninguna se calculó a mano ni se estimó.

## 1. Artefactos versionados

| Etapa | Ruta | Contenido |
|---|---|---|
| Validación de tickers | `data/raw/ticker_validation_2026-08-23.json` | 30/30 tickers `.SN` responden en Yahoo Finance (`failed: []`). |
| Descarga (raw) | `data/raw/ohlcv_5m_2026-08-23/manifest.json` | Parámetros de la descarga: `interval=5m`, `period=60d`, `auto_adjust=true`, `source=yfinance`, 30 tickers descargados, 0 vacíos. |
| Descarga (raw) | `data/raw/ohlcv_5m_2026-08-23/quality_report.json` | Filas, días, filas por día, rango de fechas y nulos por ticker, antes de limpiar. |
| Limpieza (1.2.1) | `data/processed/clean_5m_2026-08-23/cleaning_report.json` | Cobertura, tier, conteo de imputaciones y días descartados por ticker. |
| Limpieza (1.2.1) | `data/processed/clean_5m_2026-08-23/scaler_params.json` | Parámetros MinMaxScaler por ticker y columna (para revertir la normalización). |
| Features S_M (1.2.2) | `data/processed/sm_features_2026-08-23/sm_features_report.json` | Estadísticos de las 7 variables de S_M, diagnóstico de volatilidad de FALABELLA y sanity checks. |
| Features S_M (1.2.2) | `data/processed/sm_features_2026-08-23/scaler_params.json` | Parámetros MinMaxScaler de `volatilidad` y `vol_promedio`. |
| Figuras | `results/sprint2/FALABELLA_volumen_intradiario.png` | Perfil intradiario de volumen (sanity check `volume_profile`: pass, máximo en la vela 15:55). |
| Figuras | `results/sprint2/FALABELLA_volatilidad_intradiario.png` | Perfil intradiario de volatilidad (sanity check `volatility_profile`: pass). |

**No versionados (solo locales):** los 30 `<TICKER>.parquet` más `_combined.parquet` de cada una de las 3 carpetas de snapshot. Se regeneran con los comandos de la sección 4.

## 2. Cobertura y calidad por ticker

Ventana: 2026-05-28 a 2026-08-21 (60 días hábiles), grilla de 78 velas de 5 min por día (09:30–15:55, America/Santiago). Umbral de tier: 60 % de cobertura pre-fill.

Definición de las columnas (fuente entre paréntesis):

- **Filas raw**: filas descargadas por yfinance (`quality_report.json` → `rows`).
- **Filas finales**: filas tras reindexar a la grilla de 78 velas (`cleaning_report.json` → `rows_final`).
- **Cobertura pre-fill %**: velas realmente observadas / velas teóricas (`coverage_pre_fill_pct`). Es la métrica válida de liquidez.
- **Cobertura post-fill %**: `coverage_pct`. Vale 100 % por construcción del relleno y se incluye solo para mostrarlo.
- **% imputadas**: `(ffill_imputed_count.close + bfill_edge_imputed_count.close) / rows_final`, es decir, la fracción de filas con `is_imputed=True`.

Ordenado de mayor a menor cobertura pre-fill:

| Ticker | Filas raw | Filas finales | Días | Cobertura pre-fill % | Cobertura post-fill % | Tier | % imputadas |
|---|---:|---:|---:|---:|---:|:---:|---:|
| LTM | 4527 | 4680 | 60 | 96.65 | 100.0 | A | 3.53 |
| SQM-B | 4504 | 4680 | 60 | 96.22 | 100.0 | A | 4.00 |
| **FALABELLA** | **4350** | **4680** | **60** | **92.93** | **100.0** | **A** | **7.20** |
| CHILE | 4350 | 4680 | 60 | 92.91 | 100.0 | A | 7.22 |
| BSANTANDER | 4092 | 4680 | 60 | 87.44 | 100.0 | A | 12.67 |
| CENCOSUD | 4042 | 4680 | 60 | 86.37 | 100.0 | A | 13.74 |
| BCI | 4030 | 4680 | 60 | 86.07 | 100.0 | A | 14.02 |
| COPEC | 3785 | 4680 | 60 | 80.88 | 100.0 | A | 19.38 |
| ITAUCL | 3656 | 4680 | 60 | 78.12 | 100.0 | A | 22.12 |
| MALLPLAZA | 3656 | 4680 | 60 | 78.08 | 100.0 | A | 22.09 |
| PARAUCO | 3465 | 4680 | 60 | 73.93 | 100.0 | A | 26.26 |
| ENELCHILE | 3393 | 4680 | 60 | 72.50 | 100.0 | A | 27.71 |
| CMPC | 3244 | 4680 | 60 | 69.32 | 100.0 | A | 30.85 |
| ENELAM | 3149 | 4680 | 60 | 67.29 | 100.0 | A | 32.78 |
| ANDINA-B | 2963 | 4680 | 60 | 63.31 | 100.0 | A | 36.79 |
| VAPORES | 2606 | 4680 | 60 | 55.68 | 100.0 | B | 44.42 |
| AGUAS-A | 2467 | 4680 | 60 | 52.71 | 100.0 | B | 47.35 |
| QUINENCO | 2453 | 4680 | 60 | 52.41 | 100.0 | B | 47.63 |
| ECL | 2102 | 4680 | 60 | 44.91 | 100.0 | B | 55.24 |
| COLBUN | 1995 | 4680 | 60 | 42.63 | 100.0 | B | 57.46 |
| ENTEL | 1870 | 4680 | 60 | 39.96 | 100.0 | B | 60.06 |
| CCU | 1829 | 4680 | 60 | 39.08 | 100.0 | B | 60.98 |
| ILC | 1796 | 4680 | 60 | 38.38 | 100.0 | B | 61.67 |
| SMU | 1711 | 4680 | 60 | 36.56 | 100.0 | B | 63.53 |
| CAP | 1620 | 4680 | 60 | 34.62 | 100.0 | B | 65.49 |
| RIPLEY | 1564 | 4680 | 60 | 33.42 | 100.0 | B | 66.60 |
| CENCOMALLS | 1527 | 4680 | 60 | 32.63 | 100.0 | B | 67.52 |
| CONCHATORO | 1091 | 4680 | 60 | 23.31 | 100.0 | B | 76.71 |
| SALFACORP | 967 | 4680 | 60 | 20.66 | 100.0 | B | 79.40 |
| IAM | 920 | 4680 | 60 | 19.66 | 100.0 | B | 80.36 |

**Resumen** (`cleaning_report.json` → `summary`): 30 tickers, 140 400 filas finales, 15 en tier A y 15 en tier B. Ningún ticker perdió días (`n_days_discarded = 0` en los 30).

**FALABELLA** (activo MVP) es tier A, con 92.93 % de cobertura pre-fill. Tiene 337 velas imputadas de 4680 (310 por ffill y 27 por bfill de borde inicial), lo que da 7.20 %, y 337 velas con volumen rellenado en 0. En 41 de sus 60 días el cierre llegó con timestamp 16:00 y se fusionó en la vela 15:55 (`days_with_late_close_folded`). En `sm_features_report.json` pasa los dos sanity checks, y el diagnóstico de volatilidad compara 4275 de 4680 ventanas.

> La cobertura pre-fill (92.93 %) y el complemento del % imputadas (92.80 %) difieren ligeramente porque `rows_raw_session_filtered` cuenta también las filas tardías de las 16:00, que luego se fusionan en la vela 15:55 y no ocupan una vela propia de la grilla.

## 3. Cómo leer las columnas del parquet limpio

`clean_5m_<fecha>/<TICKER>.parquet` (sin sufijo `.SN`) contiene:

- `open`, `high`, `low`, `close`, `volume`: **normalizadas** con MinMaxScaler por ticker, en [0, 1].
- `open_raw`, `high_raw`, `low_raw`, `close_raw`, `volume_raw`: **sin normalizar**, en CLP y número de acciones. Deben usarse para cualquier cálculo en unidades reales, como el implementation shortfall o la calibración Poisson de la tarea 2.1.3.
- `is_imputed`: `True` si la vela no tenía una transacción real (se rellenó por ffill o bfill).
- `datetime_santiago` (tz-aware), `datetime_utc` y `ticker`.

## 4. Reproducción

Desde la raíz del repo, dentro del contenedor Docker o de un entorno con `requirements.txt` instalado:

```bash
# 0) (opcional) validar que los 30 tickers respondan en Yahoo Finance
python src/data/download_ohlcv.py --check-only

# 1) Descarga: escribe data/raw/ohlcv_5m_<fecha_de_hoy>/ (30 parquet + manifest.json + quality_report.json)
python src/data/download_ohlcv.py

# 2) Limpieza 1.2.1: escribe data/processed/clean_5m_<fecha>/ (misma fecha del raw)
python src/data/clean_ohlcv.py --input-dir data/raw/ohlcv_5m_2026-08-23

# 3) Features S_M 1.2.2: escribe data/processed/sm_features_<fecha>/ y las figuras de results/sprint2/
python src/features/build_sm_features.py --input-dir data/processed/clean_5m_2026-08-23 --plot-ticker FALABELLA

# 4) Tests del pipeline
pytest tests/test_pipeline_sm.py
```

**Limitación de reproducibilidad:** yfinance solo entrega velas de 5 min de los últimos 60 días. Por eso, correr hoy el paso 1 genera un snapshot distinto (`ohlcv_5m_<hoy>`) y no el de 2026-08-23. Los pasos 2 y 3 son deterministas dado un raw fijo. Para reproducir exactamente las cifras de este documento hacen falta los parquet de `data/raw/ohlcv_5m_2026-08-23/`, que existen solo localmente.

## 5. Tests

`pytest tests/test_pipeline_sm.py` → **13 passed** (Python 3.11, pandas 2.2.1, numpy 1.26.4, scikit-learn 1.6.1; ejecutado el 2026-09-26).
