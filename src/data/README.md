# `src/data/download_ohlcv.py`

Script de la tarea de descarga y estructuración de
datos OHLCV del IPSA vía `yfinance` (30 acciones, 60 días, velas de 5 min).

No limpia ni normaliza nada —
script solo descarga, estructura y reporta calidad.

```bash
docker compose build
```

## 1. Cómo ejecutarlo

###  desde terminal (host o VSCode)

```bash
docker compose run --rm slippage python src/data/download_ohlcv.py --check-only
docker compose run --rm slippage python src/data/download_ohlcv.py
```

El volumen `.:/workspace` en `compose.yaml` hace que todo lo que el script
escriba en `data/raw/` aparezca de inmediato en tu carpeta local — no hay
que copiar nada manualmente fuera del contenedor.



## 2. Flags disponibles

| Comando | Qué hace |
|---|---|
| `python src/data/download_ohlcv.py` | Valida los 30 tickers y descarga los 60 días completos si pasan la validación |
| `python src/data/download_ohlcv.py --check-only` | Solo valida los 30 tickers (rápido, sin descargar los 60 días) |
| `python src/data/download_ohlcv.py --suggest "Banco Itau Chile"` | Busca candidatos de ticker en Yahoo Finance por nombre de empresa (requiere `yfinance >= 0.2.40`) |

## 3. Qué genera y dónde queda

Todo cae dentro de `data/raw/`, que ya está en `.gitignore` — **no se sube
a GitHub**, se comparte por fuera del repo (ver sección 6).

```
data/raw/
├── ticker_validation_<fecha>.json      # resultado de --check-only: listas ok / failed
└── ohlcv_5m_<fecha>/
    ├── <TICKER>.parquet                # uno por acción
    ├── _combined.parquet               # las 30 acciones juntas
    ├── manifest.json                   # parámetros exactos de la corrida
    └── quality_report.json             # nulos, cobertura, rango de fechas por ticker
```

## 5. Si un ticker falla la validación

1. Primero prueba `python src/data/download_ohlcv.py --suggest "nombre de la empresa"`.
2. Si no da resultados (o tu `yfinance` es muy antiguo), búsqueda manual:
   1. Ir a [finance.yahoo.com](https://finance.yahoo.com).
   2. Buscar por **nombre de la empresa**, no por el ticker que falló.
   3. En los resultados, identificar el listado cuyo exchange sea "Santiago"
      (no el ADR en NYSE u otro mercado).
   4. Confirmar en la ficha del instrumento que la moneda es CLP.
   5. Copiar el símbolo exacto, con cuidado de guiones/series
      (`SQM-B.SN` ≠ `SQMB.SN`; `AGUAS-A.SN` ≠ `AGUAS.SN`).
   6. Verificar en la pestaña "Chart" (rango 1D/5D) que sí trae velas
      intradía, no solo cierre diario.
3. Actualizar la lista `IPSA_TICKERS` en `download_ohlcv.py` y volver a
   correr `--check-only`.

## 6. Compartir con el equipo

El período de 60 días para velas de 5 min es una **ventana móvil** de
Yahoo Finance. Si Alguien mas corren el script en otro día, van a
tener un rango de fechas distinto al subido al drive.

**Correr la descarga una sola vez** y subir la carpeta completa
`ohlcv_5m_<fecha>/` (o un `.zip`) a la carpeta compartida del equipo
(Drive), en vez de que cada uno la regenere por su cuenta.

## 7. Handoff a Sprint 2

La tarea 1.2.1 (forward fill, filtro horario 09:30–16:00, MinMaxScaler)
parte directo desde los `.parquet` de `ohlcv_5m_<fecha>/`, usando
`manifest.json` para saber con qué parámetros se generaron y
`quality_report.json` para decidir cómo tratar los huecos detectados.

## 8. `src/data/clean_ohlcv.py` (tarea 1.2.1 — limpieza)

Toma el output de `download_ohlcv.py` y produce
`data/processed/clean_5m_<fecha>/`. Pasos: filtro de horario 09:30–15:55,
reindexado a grilla regular de 78 velas de 5 min por (ticker, día hábil),
forward fill en `open/high/low/close` (`volume` se rellena con 0, nunca con
ffill — ver docstring del script), backfill acotado del borde inicial del
día, y `MinMaxScaler` por ticker sobre las 5 columnas continuas (parámetros
en `scaler_params.json`, columnas crudas conservadas con sufijo `_raw`).

```bash
docker compose run --rm slippage python src/data/clean_ohlcv.py                 # autodetecta el ultimo ohlcv_5m_<fecha>
docker compose run --rm slippage python src/data/clean_ohlcv.py --dry-run       # solo calcula e imprime el resumen
docker compose run --rm slippage python src/data/clean_ohlcv.py --edge-policy discard
```

| Flag | Qué hace |
|---|---|
| `--input-dir` | Directorio `ohlcv_5m_<fecha>` a limpiar (default: el más reciente) |
| `--output-dir` | Default: `data/processed/clean_5m_<fecha>` (misma fecha del input) |
| `--edge-policy {bfill,discard}` | Qué hacer si un día empieza sin dato a las 09:30 (default `bfill`, ver justificación en el docstring del script) |
| `--dry-run` | Corre todo el cálculo, no escribe archivos |

Genera `<TICKER>.parquet` + `_combined.parquet` + `scaler_params.json` +
`cleaning_report.json` en `data/processed/clean_5m_<fecha>/` (gitignored,
igual que `data/raw/` — se comparte por Drive).

**Ojo con la métrica de cobertura**: `cleaning_report.json` reporta
`coverage_pct` (post reindex+ffill+bfill, ~100% siempre por construcción del
propio relleno) y `coverage_pre_fill_pct` (filas realmente observadas antes
de rellenar / velas teóricas — esta sí varía por liquidez del ticker y es la
que hay que mirar para el gate de 60% acordado con el equipo). Ver
`cleaning_report.json["summary"]["coverage_metric_note"]`.

## 9. Handoff a Sprint 2.2

La tarea 1.2.2 (`src/features/build_sm_features.py`, ver
[`src/features/README.md`](../features/README.md)) parte directo desde
`data/processed/clean_5m_<fecha>/`, reutilizando y extendiendo su
`scaler_params.json`.
