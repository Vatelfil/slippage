"""
clean_ohlcv.py
--------------
Sprint 2 (Hito 5, tarea 1.2.1) - Limpieza y preprocesamiento de OHLCV IPSA.

Toma como INPUT el output de `download_ohlcv.py` (data/raw/ohlcv_5m_<fecha>/,
30 parquet en bruto + manifest.json + quality_report.json) y produce
data/processed/clean_5m_<fecha>/ con los datos ya aptos para calcular el
vector de estado S_M (tarea 1.2.2) y para alimentar `reset()` del entorno de
simulacion (docs/arquitectura_entorno_simulacion.md, seccion 2.1).

El `quality_report.json` de la descarga ya advirtio el problema central de
esta tarea: `avg_rows_per_day` va de ~16 a ~75 contra las 78 velas teoricas
de una jornada 09:30-15:55 (5 min). Eso NO son nulos -- son FILAS AUSENTES
(velas sin ninguna transaccion). Por eso el forward fill no sirve de nada si
antes no se reindexa cada (ticker, dia) contra la grilla completa de 5 min;
aplicar ffill directo sobre filas no contiguas simplemente no tiene huecos
que rellenar.

Pasos, en este orden (informe de Titulo I, seccion 7):
    1. Filtro de horario: conservar solo 09:30-16:00 hora Santiago (velas
       de 09:30 a 15:55, tz-aware).
    2. Reindexado a grilla regular de 78 marcas de 5 min por (ticker, dia
       habil). Dias sin NINGUNA observacion se descartan completos.
    3. Forward fill en open/high/low/close (ultimo precio conocido).
       volume se rellena con 0, NUNCA con ffill: una vela sin transacciones
       tuvo volumen real 0, no el volumen de la vela anterior -- propagarlo
       inflaria artificialmente la liquidez percibida en ese instante.
    4. Backfill acotado del borde inicial: si un dia empieza sin dato a las
       09:30, el ffill no tiene de donde propagar. Flag --edge-policy:
         - "bfill" (default): rellena SOLO las velas anteriores a la primera
           observacion real del dia (nunca reintroduce datos en un dia sin
           ninguna fila -- esos dias ya fueron descartados en el paso 2).
           Se elige como default porque descartar el dia completo por faltar
           solo la primera vela seria excesivo para tickers ya poco
           liquidos (ej. SALFACORP, ~16 filas/dia crudas).
         - "discard": si el dia queda con NaN en el borde inicial tras el
           ffill, se descarta el dia completo en vez de rellenarlo.
    5. Normalizacion con MinMaxScaler (scikit-learn), UN SCALER POR TICKER:
       los precios del IPSA van de decenas a miles de CLP: un scaler global
       aplastaria las acciones baratas contra 0. Se ajusta un scaler por
       columna por ticker (open, high, low, close, volume) y sus parametros
       (data_min_, data_max_, data_range_, scale_, min_) se guardan en
       scaler_params.json -- NO en .pkl (el .gitignore ignora *.pkl y el
       equipo necesita reproducir la normalizacion sin re-ejecutar nada).
       Las columnas originales se conservan con sufijo "_raw" junto a las
       normalizadas, para poder calcular el implementation shortfall en CLP
       reales mas adelante.

Verificacion de DST: se comprobo con `ZoneInfo("America/Santiago")` que la
ventana de descarga (2026-05-28 a 2026-08-21) no cruza ningun cambio de
horario -- el offset se mantiene constante en UTC-04:00 durante todo el
periodo (fechas en `quality_report.json` ya vienen consistentemente en
"-04:00"). No hay transicion de horario de verano que tratar en esta corrida
puntual, pero el codigo sigue siendo tz-aware en todo momento (nunca se resta
un offset fijo a mano) por si el pipeline se vuelve a correr en otra ventana
que si cruce un cambio de huso.

Metrica de cobertura y checkpoint de 60%: el pipeline calcula DOS metricas
de cobertura por ticker:
  - coverage_pct: filas_finales / (dias_conservados x 78), calculada
    DESPUES de reindexado+ffill+bfill. Por construccion del propio relleno,
    este valor es ~100% para cualquier ticker que conserve al menos un dia
    (cada dia conservado aporta exactamente 78 filas garantizadas) -- no
    discrimina liquidez, se reporta solo por completitud/transparencia.
  - coverage_pre_fill_pct: filas REALMENTE observadas (antes de rellenar) /
    (dias_conservados x 78). Esta es la metrica que si varia segun la
    liquidez real del ticker, y es la que se usa como gate practico de 60%
    que el equipo debe revisar manualmente antes de avanzar a la tarea 1.2.2
    (el script NO aborta solo con un sys.exit; deja la lista de tickers bajo
    el umbral bien visible en cleaning_report.json y en stdout).

Uso (dentro del contenedor Docker):
    python src/data/clean_ohlcv.py                              # autodetecta el ultimo ohlcv_5m_<fecha>
    python src/data/clean_ohlcv.py --input-dir data/raw/ohlcv_5m_2026-08-23
    python src/data/clean_ohlcv.py --edge-policy discard
    python src/data/clean_ohlcv.py --dry-run                    # calcula todo, no escribe archivos
"""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

SANTIAGO_TZ = ZoneInfo("America/Santiago")

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

SESSION_START = "09:30"
SESSION_END = "15:55"          # ultima vela de 5 min de la jornada (cubre el tramo hasta las 16:00)
BARS_PER_DAY = 78              # (15:55 - 09:30) / 5 min + 1

CONTINUOUS_COLS: list[str] = ["open", "high", "low", "close", "volume"]

EDGE_POLICIES = ("bfill", "discard")
DEFAULT_EDGE_POLICY = "bfill"
COVERAGE_THRESHOLD = 0.60

DST_NOTE = (
    "Verificado con ZoneInfo('America/Santiago'): offset constante UTC-04:00 "
    "en toda la ventana de descarga (2026-05-28 a 2026-08-21), sin transicion "
    "de horario de verano. El codigo se mantiene tz-aware de todas formas por "
    "si una corrida futura cruza un cambio de huso."
)


# ---------------------------------------------------------------------------
# Descubrimiento de rutas de entrada/salida
# ---------------------------------------------------------------------------

def find_latest_raw_dir(raw_root: Path = RAW_DIR) -> Path | None:
    """Busca el subdirectorio 'ohlcv_5m_<fecha>' mas reciente dentro de
    raw_root (orden lexicografico == orden cronologico por ser fecha ISO).
    Devuelve None si no hay ninguno. Se usa como default de --input-dir
    cuando el usuario no lo especifica explicitamente.
    """
    if not raw_root.exists():
        return None
    candidates = sorted(
        p for p in raw_root.iterdir() if p.is_dir() and p.name.startswith("ohlcv_5m_")
    )
    return candidates[-1] if candidates else None


def derive_output_dir(input_dir: Path, output_root: Path = PROCESSED_DIR,
                       prefix: str = "clean_5m_") -> Path:
    """Extrae el sufijo de fecha del nombre de input_dir (ej.
    'ohlcv_5m_2026-08-23' -> '2026-08-23') y arma output_root/f'{prefix}{fecha}'.

    Se reusa la fecha del RAW, no la fecha de hoy: la limpieza puede correrse
    dias despues de la descarga, y reusar la fecha del raw mantiene la
    trazabilidad raw <-> processed sin ambiguedad.
    """
    name = input_dir.name
    if not name.startswith("ohlcv_5m_"):
        raise ValueError(
            f"No se pudo extraer la fecha de '{name}' (se esperaba el patron "
            "'ohlcv_5m_<fecha>'). Especifica --output-dir explicitamente."
        )
    fecha = name[len("ohlcv_5m_"):]
    return output_root / f"{prefix}{fecha}"


# ---------------------------------------------------------------------------
# Carga
# ---------------------------------------------------------------------------

def load_raw_ticker_files(input_dir: Path) -> dict[str, pd.DataFrame]:
    """Carga cada <TICKER>.parquet de input_dir (excluye _combined.parquet,
    manifest.json y quality_report.json). Devuelve {ticker: DataFrame}.
    """
    tickers: dict[str, pd.DataFrame] = {}
    for path in sorted(input_dir.glob("*.parquet")):
        if path.stem == "_combined":
            continue
        tickers[path.stem] = pd.read_parquet(path)
    return tickers


# ---------------------------------------------------------------------------
# Paso 1: filtro de horario
# ---------------------------------------------------------------------------

def filter_session_hours(df: pd.DataFrame, session_start: str = SESSION_START,
                          session_end: str = SESSION_END) -> pd.DataFrame:
    """Conserva solo las filas cuyo 'datetime_santiago' cae dentro de
    [session_start, session_end] (ambos limites inclusive), descartando
    pre/post-mercado. Trabaja siempre sobre la columna tz-aware
    'datetime_santiago', nunca sobre una hora naive.
    """
    start_t = pd.Timestamp(session_start).time()
    end_t = pd.Timestamp(session_end).time()
    times = df["datetime_santiago"].dt.time
    mask = (times >= start_t) & (times <= end_t)
    return df.loc[mask].copy()


# ---------------------------------------------------------------------------
# Paso 2: reindexado a grilla regular
# ---------------------------------------------------------------------------

def build_trading_day_grid(day: date, tz: ZoneInfo = SANTIAGO_TZ) -> pd.DatetimeIndex:
    """Grilla de 78 marcas de 5 min entre SESSION_START y SESSION_END del
    dia dado, tz-aware.
    """
    start = pd.Timestamp(f"{day} {SESSION_START}", tz=tz)
    end = pd.Timestamp(f"{day} {SESSION_END}", tz=tz)
    return pd.date_range(start, end, freq="5min", tz=tz)


def reindex_ticker_day(df_day: pd.DataFrame, day: date) -> pd.DataFrame:
    """Reindexa las filas de un (ticker, dia) sobre build_trading_day_grid(day).
    Las columnas continuas quedan NaN donde no habia observacion real.
    """
    grid = build_trading_day_grid(day)
    df_indexed = df_day.set_index("datetime_santiago").reindex(grid)
    df_indexed.index.name = "datetime_santiago"
    return df_indexed.reset_index()


# ---------------------------------------------------------------------------
# Pasos 3 y 4: forward fill + backfill/descarte de borde inicial
# ---------------------------------------------------------------------------

def fill_ticker_day(df_grid: pd.DataFrame, edge_policy: str) -> tuple[pd.DataFrame, dict, bool]:
    """Aplica, sobre un (ticker, dia) ya reindexado a 78 filas:
      1. ffill en open/high/low/close (ultimo precio conocido).
      2. Segun edge_policy:
           - "bfill": bfill SOLO de lo que el ffill no pudo llenar (huecos
             antes de la primera observacion real del dia).
           - "discard": si quedan NaN tras el ffill, se marca el dia
             completo para descarte (no se rellena nada mas).
      3. volume = volume.fillna(0.0) SIEMPRE, nunca ffill/bfill (una vela
         sin transacciones tiene volumen real 0).

    Devuelve (df_relleno_o_original, stats_del_dia, dropped).
    stats_del_dia = {'ffill_count': {col:int}, 'bfill_edge_count': {col:int}}
    """
    if edge_policy not in EDGE_POLICIES:
        raise ValueError(f"edge_policy invalido: {edge_policy!r} (opciones: {EDGE_POLICIES})")

    df = df_grid.copy()
    ohlc_cols = [c for c in ("open", "high", "low", "close") if c in df.columns]

    before = df[ohlc_cols].isna()
    df[ohlc_cols] = df[ohlc_cols].ffill()
    after_ffill = df[ohlc_cols].isna()

    ffill_count = {col: int((before[col] & ~after_ffill[col]).sum()) for col in ohlc_cols}

    dropped = False
    bfill_edge_count = {col: 0 for col in ohlc_cols}
    if after_ffill.to_numpy().any():
        if edge_policy == "discard":
            dropped = True
        else:  # "bfill": solo rellena el remanente que el ffill no pudo (borde inicial)
            before_bfill = after_ffill.copy()
            df[ohlc_cols] = df[ohlc_cols].bfill()
            after_bfill = df[ohlc_cols].isna()
            bfill_edge_count = {
                col: int((before_bfill[col] & ~after_bfill[col]).sum()) for col in ohlc_cols
            }

    if "volume" in df.columns:
        df["volume"] = df["volume"].fillna(0.0)

    stats = {"ffill_count": ffill_count, "bfill_edge_count": bfill_edge_count}
    return df, stats, dropped


# ---------------------------------------------------------------------------
# Orquestacion por ticker
# ---------------------------------------------------------------------------

def process_ticker(ticker: str, df_raw: pd.DataFrame, edge_policy: str) -> tuple[pd.DataFrame, dict]:
    """Orquesta la limpieza de UN ticker: filtro de horario -> agrupa por
    dia habil (solo dias que YA tienen >=1 fila real; un dia sin ninguna
    fila jamas se materializa, cumpliendo 'dias sin ninguna observacion se
    descartan completos') -> reindexado + relleno por dia -> concatena.

    Devuelve (df_limpio_sin_normalizar, ticker_stats).
    """
    df_session = filter_session_hours(df_raw)
    rows_raw_session_filtered = len(df_session)

    grouped = df_session.groupby(df_session["datetime_santiago"].dt.date)
    trading_days_raw = grouped.ngroups

    kept_frames: list[pd.DataFrame] = []
    trading_days_discarded: list[str] = []
    ffill_totals: dict[str, int] = {c: 0 for c in ("open", "high", "low", "close")}
    bfill_totals: dict[str, int] = {c: 0 for c in ("open", "high", "low", "close")}
    volume_zero_filled_count = 0

    for day, df_day in grouped:
        df_grid = reindex_ticker_day(df_day, day)
        # volumen real observado antes de rellenar (para el conteo de ceros agregados)
        volume_missing_before = int(df_grid["volume"].isna().sum()) if "volume" in df_grid else 0

        df_filled, stats, dropped = fill_ticker_day(df_grid, edge_policy)
        if dropped:
            trading_days_discarded.append(str(day))
            continue

        for col, n in stats["ffill_count"].items():
            ffill_totals[col] += n
        for col, n in stats["bfill_edge_count"].items():
            bfill_totals[col] += n
        volume_zero_filled_count += volume_missing_before

        df_filled["ticker"] = ticker
        kept_frames.append(df_filled)

    df_clean = (
        pd.concat(kept_frames, ignore_index=True)
        if kept_frames
        else df_session.iloc[0:0].copy()
    )

    stats = {
        "rows_raw_session_filtered": rows_raw_session_filtered,
        "trading_days_raw": trading_days_raw,
        "trading_days_kept": trading_days_raw - len(trading_days_discarded),
        "trading_days_discarded": trading_days_discarded,
        "n_days_discarded": len(trading_days_discarded),
        "ffill_imputed_count": ffill_totals,
        "bfill_edge_imputed_count": bfill_totals,
        "volume_zero_filled_count": volume_zero_filled_count,
        "rows_final": len(df_clean),
    }
    return df_clean, stats


# ---------------------------------------------------------------------------
# Paso 5: normalizacion MinMaxScaler por ticker
# ---------------------------------------------------------------------------

def normalize_ticker(df_ticker: pd.DataFrame, columns: list[str] = CONTINUOUS_COLS
                      ) -> tuple[pd.DataFrame, dict]:
    """Ajusta UN MinMaxScaler por columna (no uno multi-columna) sobre
    df_ticker[columns], para que scaler_params.json quede uniforme y sea
    facil de invertir columna por columna en runtime. Conserva la columna
    original con sufijo '_raw' junto a la normalizada (mismo nombre que
    antes) para poder calcular el implementation shortfall en CLP reales.

    Devuelve (df_con_raw_y_normalizadas, scaler_params_de_este_ticker).
    """
    df = df_ticker.copy()
    params: dict[str, dict[str, float]] = {}

    for col in columns:
        if col not in df.columns:
            continue
        raw_col = f"{col}_raw"
        df[raw_col] = df[col].astype(float)

        values = df[[raw_col]].to_numpy(dtype=float)
        scaler = MinMaxScaler()
        scaler.fit(values)
        df[col] = scaler.transform(values).ravel()

        params[col] = {
            "data_min_": float(scaler.data_min_[0]),
            "data_max_": float(scaler.data_max_[0]),
            "data_range_": float(scaler.data_range_[0]),
            "scale_": float(scaler.scale_[0]),
            "min_": float(scaler.min_[0]),
        }

    return df, params


# ---------------------------------------------------------------------------
# Cobertura
# ---------------------------------------------------------------------------

def compute_coverage(rows_final: int, trading_days_kept: int,
                      bars_per_day: int = BARS_PER_DAY) -> float:
    """Metrica pedida literalmente: filas finales / (dias conservados x
    barras teoricas por dia), calculada DESPUES de reindex+ffill+bfill.
    Por construccion del propio relleno, este valor es ~100% para
    cualquier ticker que conserve al menos un dia (ver docstring de modulo).
    """
    theoretical = trading_days_kept * bars_per_day
    if theoretical == 0:
        return 0.0
    return round(100.0 * rows_final / theoretical, 2)


def compute_pre_fill_coverage(rows_raw_session_filtered: int, trading_days_kept: int,
                               bars_per_day: int = BARS_PER_DAY) -> float:
    """Metrica diagnostica real: filas REALMENTE observadas (antes de
    reindexar/rellenar) sobre el total teorico de barras de los dias
    conservados. Esta es la que varia segun la liquidez del ticker y la
    que se usa como gate practico de 60%.
    """
    theoretical = trading_days_kept * bars_per_day
    if theoretical == 0:
        return 0.0
    return round(100.0 * rows_raw_session_filtered / theoretical, 2)


# ---------------------------------------------------------------------------
# Orquestacion global + reportes
# ---------------------------------------------------------------------------

def clean_all(input_dir: Path, edge_policy: str
              ) -> tuple[dict[str, pd.DataFrame], dict[str, dict], dict[str, dict]]:
    """Itera todos los tickers de input_dir con process_ticker + normalize_ticker.

    Devuelve (cleaned_dfs, scaler_params_por_ticker, per_ticker_stats).
    """
    raw_tickers = load_raw_ticker_files(input_dir)

    cleaned: dict[str, pd.DataFrame] = {}
    scaler_params: dict[str, dict] = {}
    per_ticker_stats: dict[str, dict] = {}

    for ticker, df_raw in raw_tickers.items():
        df_clean, stats = process_ticker(ticker, df_raw, edge_policy)
        df_normalized, params = normalize_ticker(df_clean)

        stats["coverage_pct"] = compute_coverage(stats["rows_final"], stats["trading_days_kept"])
        stats["coverage_pre_fill_pct"] = compute_pre_fill_coverage(
            stats["rows_raw_session_filtered"], stats["trading_days_kept"]
        )
        stats["under_threshold_post_fill"] = stats["coverage_pct"] < COVERAGE_THRESHOLD * 100
        stats["under_threshold_pre_fill"] = stats["coverage_pre_fill_pct"] < COVERAGE_THRESHOLD * 100

        cleaned[ticker] = df_normalized
        scaler_params[ticker] = params
        per_ticker_stats[ticker] = stats

    return cleaned, scaler_params, per_ticker_stats


def build_cleaning_report(per_ticker_stats: dict, edge_policy: str,
                           input_dir: Path, output_dir: Path) -> dict:
    """Arma el dict final de cleaning_report.json."""
    tickers_bajo_umbral_pre_fill = sorted(
        t for t, s in per_ticker_stats.items() if s["under_threshold_pre_fill"]
    )
    total_rows_final = sum(s["rows_final"] for s in per_ticker_stats.values())

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "edge_policy": edge_policy,
        "coverage_threshold": COVERAGE_THRESHOLD,
        "session_window": {
            "start": SESSION_START,
            "end": SESSION_END,
            "timezone": "America/Santiago",
            "bars_per_day": BARS_PER_DAY,
        },
        "dst_note": DST_NOTE,
        "per_ticker": per_ticker_stats,
        "summary": {
            "n_tickers": len(per_ticker_stats),
            "total_rows_final": total_rows_final,
            "tickers_bajo_umbral_60pct_pre_fill": tickers_bajo_umbral_pre_fill,
            "coverage_metric_note": (
                "coverage_pct se calcula tal como fue definido en el briefing "
                "(filas_finales / (dias_conservados x 78), post reindex+ffill+"
                "bfill), pero por construccion del propio relleno es ~100% para "
                "cualquier ticker que conserve al menos un dia -- no discrimina "
                "liquidez. coverage_pre_fill_pct (filas realmente observadas "
                "antes de rellenar / velas teoricas de los dias conservados) es "
                "la metrica que si varia y la que debe usarse como gate manual "
                "de 60% antes de avanzar a la tarea 1.2.2."
            ),
        },
    }


def build_scaler_params_report(scaler_params: dict, input_dir: Path) -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_task": "1.2.1",
        "input_dir": str(input_dir),
        "columns_normalized_1_2_1": CONTINUOUS_COLS,
        "scalers": scaler_params,
    }


def write_outputs(cleaned: dict[str, pd.DataFrame], scaler_params: dict,
                   cleaning_report: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    frames = []
    for ticker, df in cleaned.items():
        df.to_parquet(output_dir / f"{ticker}.parquet", index=False)
        frames.append(df)

    if frames:
        combined = pd.concat(frames, ignore_index=True)
        combined.to_parquet(output_dir / "_combined.parquet", index=False)

    (output_dir / "cleaning_report.json").write_text(
        json.dumps(cleaning_report, indent=2, ensure_ascii=False)
    )
    (output_dir / "scaler_params.json").write_text(
        json.dumps(scaler_params, indent=2, ensure_ascii=False)
    )


def main(input_dir: Path | None = None, output_dir: Path | None = None,
         edge_policy: str = DEFAULT_EDGE_POLICY, dry_run: bool = False) -> None:
    if input_dir is None:
        input_dir = find_latest_raw_dir()
        if input_dir is None:
            raise SystemExit(
                f"No se encontro ningun directorio 'ohlcv_5m_<fecha>' en {RAW_DIR}. "
                "Corre primero src/data/download_ohlcv.py o especifica --input-dir."
            )
        print(f"--input-dir no especificado, autodetectado: {input_dir}")

    if output_dir is None:
        output_dir = derive_output_dir(input_dir)

    print(f"Limpiando OHLCV desde: {input_dir}")
    print(f"edge-policy: {edge_policy}")

    cleaned, scaler_params_by_ticker, per_ticker_stats = clean_all(input_dir, edge_policy)
    cleaning_report = build_cleaning_report(per_ticker_stats, edge_policy, input_dir, output_dir)
    scaler_report = build_scaler_params_report(scaler_params_by_ticker, input_dir)

    n_tickers = len(per_ticker_stats)
    total_rows = cleaning_report["summary"]["total_rows_final"]
    bajo_umbral = cleaning_report["summary"]["tickers_bajo_umbral_60pct_pre_fill"]

    print(f"Tickers procesados: {n_tickers} | filas finales totales: {total_rows}")
    if bajo_umbral:
        print(f"ATENCION: {len(bajo_umbral)} ticker(s) bajo el 60% de cobertura pre-fill: {bajo_umbral}")
        print("  Revisar antes de avanzar a la tarea 1.2.2 (gate manual, no se detiene el pipeline).")
    else:
        print("Ningun ticker bajo el umbral de cobertura pre-fill del 60%.")

    if dry_run:
        print(f"[dry-run] No se escribieron archivos. Output hubiera sido: {output_dir}")
        return

    write_outputs(cleaned, scaler_report, cleaning_report, output_dir)
    print(f"\nListo. Datos limpios en: {output_dir}")
    print("Entregable para Sprint 2 (1.2.2): <TICKER>.parquet + _combined.parquet + scaler_params.json + cleaning_report.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir", type=Path, default=None,
        help="Directorio 'data/raw/ohlcv_5m_<fecha>' a limpiar. Default: el mas reciente disponible.",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=None,
        help="Directorio de salida. Default: 'data/processed/clean_5m_<fecha>' (misma fecha del input).",
    )
    parser.add_argument(
        "--edge-policy", choices=EDGE_POLICIES, default=DEFAULT_EDGE_POLICY,
        help="Que hacer si un dia empieza sin dato a las 09:30: 'bfill' (default, "
             "rellena solo el borde inicial) o 'discard' (descarta el dia completo).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Calcula todo el pipeline e imprime el resumen, pero no escribe archivos.",
    )
    args = parser.parse_args()

    main(input_dir=args.input_dir, output_dir=args.output_dir,
         edge_policy=args.edge_policy, dry_run=args.dry_run)
