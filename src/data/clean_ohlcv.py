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
    1. Filtro de horario: conservar 09:30-16:00 hora Santiago, tz-aware
       (FILTER_SESSION_END="16:00", no "15:55" -- ver CLOSING_AUCTION_NOTE:
       yfinance a veces timestampea el cierre real a las 16:00, y filtrar en
       15:55 lo descartaba por completo).
    1.5. Fusion de la vela tardia de cierre (fold_closing_auction): cualquier
       fila en (15:55, 16:00] se fusiona, por dia, dentro de la ultima vela
       de la grilla (15:55). Ver CLOSING_AUCTION_NOTE para la evidencia
       completa (hallazgo del checkpoint de sanity-check de la tarea 1.2.2).
    2. Reindexado a grilla regular de 78 marcas de 5 min por (ticker, dia
       habil), 09:30 a 15:55 (SESSION_END, sin cambios -- la grilla sigue
       en 78 velas). Dias sin NINGUNA observacion se descartan completos.
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

Columna `is_imputed` (auditoria de relleno): cada fila del output trae un
booleano que marca si esa vela NO tenia observacion real en el grid original
(o sea, si su precio vino de ffill o de bfill de borde, en vez de una
transaccion real). Requisito para poder auditar en la tarea 1.2.2 cuanta de
la `volatilidad`/`vol_promedio` calculadas es real vs. artefacto del
relleno -- ver `build_sm_features.py`, que usa esta columna para calcular una
version diagnostica de la volatilidad de FALABELLA exigiendo un minimo de
velas realmente observadas por ventana.

Verificacion de DST: se comprobo con `ZoneInfo("America/Santiago")` que la
ventana de descarga (2026-05-28 a 2026-08-21) no cruza ningun cambio de
horario -- el offset se mantiene constante en UTC-04:00 durante todo el
periodo (fechas en `quality_report.json` ya vienen consistentemente en
"-04:00"). No hay transicion de horario de verano que tratar en esta corrida
puntual, pero el codigo sigue siendo tz-aware en todo momento (nunca se resta
un offset fijo a mano) por si el pipeline se vuelve a correr en otra ventana
que si cruce un cambio de huso.

Metrica de cobertura y "tier" (NO es un filtro): el pipeline calcula DOS
metricas de cobertura por ticker:
  - coverage_pct: filas_finales / (dias_conservados x 78), calculada
    DESPUES de reindexado+ffill+bfill. Por construccion del propio relleno,
    este valor es ~100% para cualquier ticker que conserve al menos un dia
    (cada dia conservado aporta exactamente 78 filas garantizadas) -- es
    TAUTOLOGICO, no discrimina liquidez. Se reporta solo por completitud,
    porque asi se definio literalmente en el briefing original.
  - coverage_pre_fill_pct: filas REALMENTE observadas (antes de rellenar) /
    (dias_conservados x 78). Esta es la metrica valida: si varia segun la
    liquidez real del ticker (19.9% en SALFACORP vs. 95.3% en SQM-B, en la
    corrida de referencia 2026-08-23).

Con esa metrica se corrio el checkpoint de la tarea 1.2.1 con el equipo:
15 de los 30 tickers del IPSA quedaron bajo 60% de cobertura pre-fill. Se
decidio EXPLICITAMENTE que esto NO filtra tickers del pipeline (los 30 se
procesan siempre): en cambio, cada ticker recibe un campo `tier` en
cleaning_report.json ("A" si coverage_pre_fill_pct >= 60%, "B" si no). El
universo real de entrenamiento del Agente Maestro es un solo activo
(FALABELLA, tier A con ~92%); los tickers tier B siguen siendo utiles para
caracterizacion agregada del mercado y calibracion de ABIDES-Gym/RMSC04
(tarea 2.2.4 de MR), un uso mucho mas tolerante a huecos. Que la mitad del
IPSA caiga en tier B no es un defecto de este pipeline: es evidencia
empirica que respalda la premisa del proyecto (mercado chileno de liquidez
fina fuera de las acciones mas transadas) y queda documentada como tal para
el Sprint Review, no como una limitacion a corregir.

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
SESSION_END = "15:55"          # etiqueta de la ULTIMA vela de la grilla de 78 (cubre el tramo hasta las 16:00)
FILTER_SESSION_END = "16:00"   # limite superior del FILTRO de horario (distinto de SESSION_END, ver fold_closing_auction)
BARS_PER_DAY = 78              # (15:55 - 09:30) / 5 min + 1

CLOSING_AUCTION_NOTE = (
    "yfinance no timestampea de forma consistente el ultimo print de la "
    "jornada para el IPSA: en la corrida de referencia (2026-08-23), ~35 de "
    "60 dias no traen NINGUNA vela a las 15:55 -- el cierre real llega "
    "timestampeado a las 16:00 (con volumen consistente con la subasta de "
    "cierre, ej. varios millones de acciones). La vela 15:50 no existe NUNCA "
    "en ningun dia ni ticker verificado. Sin correccion, el filtro de "
    "horario y la grilla de 78 velas (fija en 09:30-15:55) descartaban ese "
    "cierre por completo, y el perfil de volumen/volatilidad no mostraba el "
    "salto esperado en la subasta de cierre (confirmado con "
    "--plot-ticker FALABELLA). Fix (fold_closing_auction, decision "
    "confirmada con BF): el filtro de horario acepta hasta las 16:00 "
    "inclusive, y cualquier fila con timestamp en (15:55, 16:00] se fusiona "
    "dentro de la ultima vela de la grilla (15:55): open=el mas temprano, "
    "high=max, low=min, close=el mas tardio (precio de cierre final), "
    "volume=suma. La grilla se mantiene en 78 velas, sin agregar una vela 79."
)

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
                          session_end: str = FILTER_SESSION_END) -> pd.DataFrame:
    """Conserva solo las filas cuyo 'datetime_santiago' cae dentro de
    [session_start, session_end] (ambos limites inclusive), descartando
    pre/post-mercado. Trabaja siempre sobre la columna tz-aware
    'datetime_santiago', nunca sobre una hora naive.

    OJO: el limite superior por defecto es FILTER_SESSION_END ("16:00"), NO
    SESSION_END ("15:55", la etiqueta de la ultima vela de la grilla). Son
    distintos a proposito: yfinance a veces timestampea el cierre real a las
    16:00 (ver CLOSING_AUCTION_NOTE). Ese remanente entre (15:55, 16:00] se
    deja pasar aca y se fusiona despues, por dia, en fold_closing_auction()
    -- antes de reindexar sobre la grilla fija de 78 velas.
    """
    start_t = pd.Timestamp(session_start).time()
    end_t = pd.Timestamp(session_end).time()
    times = df["datetime_santiago"].dt.time
    mask = (times >= start_t) & (times <= end_t)
    return df.loc[mask].copy()


def fold_closing_auction(df_day: pd.DataFrame, day: date) -> pd.DataFrame:
    """Fusiona cualquier fila con timestamp en (SESSION_END, FILTER_SESSION_END]
    (tipicamente una unica fila a las 16:00, ocasionalmente tambien una
    16:10 suelta) dentro de la ultima vela de la grilla (SESSION_END, 15:55).
    Ver CLOSING_AUCTION_NOTE para la evidencia y motivacion completa.

    Si el dia YA tiene una fila real a las 15:55 y ademas llega una tardia,
    se agregan juntas: open=la mas temprana, high=max, low=min, close=la mas
    tardia (el print mas reciente es el precio de cierre "final" de la
    jornada), volume=suma. Si solo existe la fila tardia, simplemente se
    reetiqueta su timestamp a las 15:55 (es la unica observacion real del
    cierre ese dia, no hay nada que agregar).

    No cambia el numero de velas de la grilla (sigue en 78): esta funcion
    corre ANTES de reindex_ticker_day, sobre las filas ya filtradas por
    filter_session_hours pero agrupadas por dia.
    """
    df = df_day.sort_values("datetime_santiago").reset_index(drop=True).copy()
    session_end_t = pd.Timestamp(SESSION_END).time()
    is_late = df["datetime_santiago"].dt.time > session_end_t

    if not is_late.any():
        return df

    grid_close_ts = pd.Timestamp(f"{day} {SESSION_END}", tz=SANTIAGO_TZ)
    df.loc[is_late, "datetime_santiago"] = grid_close_ts

    agg_spec = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    other_cols = [c for c in df.columns if c not in ("datetime_santiago", *agg_spec)]
    agg_spec.update({c: "first" for c in other_cols})

    # df ya esta ordenado cronologicamente (sort_values de mas arriba), asi
    # que 'first'/'last' dentro del grupo fusionado respetan el orden real
    # de llegada aunque ahora compartan el mismo datetime_santiago.
    return df.groupby("datetime_santiago", as_index=False).agg(agg_spec)


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
      4. agrega la columna booleana 'is_imputed': True si la fila NO tenia
         una observacion real en el grid original (o sea, si 'close' fue
         reindexado a NaN y por lo tanto vino de ffill o de bfill de borde).
         Se marca por CUALQUIER imputacion, no solo ffill, porque el
         proposito es auditar cuanta de la volatilidad/vol_promedio
         calculados en 1.2.2 es real vs. artefacto del relleno -- una vela
         rellenada por bfill de borde es igual de "no observada" que una
         rellenada por ffill.

    Devuelve (df_relleno_o_original, stats_del_dia, dropped).
    stats_del_dia = {'ffill_count': {col:int}, 'bfill_edge_count': {col:int}}
    """
    if edge_policy not in EDGE_POLICIES:
        raise ValueError(f"edge_policy invalido: {edge_policy!r} (opciones: {EDGE_POLICIES})")

    df = df_grid.copy()
    ohlc_cols = [c for c in ("open", "high", "low", "close") if c in df.columns]

    before = df[ohlc_cols].isna()
    is_imputed = (before["close"] if "close" in ohlc_cols else before.any(axis=1)).to_numpy()

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

    df["is_imputed"] = is_imputed

    stats = {"ffill_count": ffill_count, "bfill_edge_count": bfill_edge_count}
    return df, stats, dropped


# ---------------------------------------------------------------------------
# Orquestacion por ticker
# ---------------------------------------------------------------------------

def process_ticker(ticker: str, df_raw: pd.DataFrame, edge_policy: str) -> tuple[pd.DataFrame, dict]:
    """Orquesta la limpieza de UN ticker: filtro de horario (hasta las 16:00,
    ver CLOSING_AUCTION_NOTE) -> agrupa por dia habil (solo dias que YA
    tienen >=1 fila real; un dia sin ninguna fila jamas se materializa,
    cumpliendo 'dias sin ninguna observacion se descartan completos') ->
    fusion de la vela tardia de cierre (fold_closing_auction) -> reindexado
    a la grilla de 78 + relleno por dia -> concatena.

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
    days_with_late_close_folded = 0

    session_end_t = pd.Timestamp(SESSION_END).time()
    for day, df_day in grouped:
        had_late_close = bool((df_day["datetime_santiago"].dt.time > session_end_t).any())
        df_day = fold_closing_auction(df_day, day)
        if had_late_close:
            days_with_late_close_folded += 1

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
        "days_with_late_close_folded": days_with_late_close_folded,
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
        # np.clip: scale_*x + min_ puede desbordar [0,1] por redondeo de
        # float64 justo en el punto que definio data_min_/data_max_ (ej.
        # 1.0000000000000002). Preserva NaN si los hubiera.
        df[col] = np.clip(scaler.transform(values).ravel(), 0.0, 1.0)

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
    conservados. Esta es la que varia segun la liquidez del ticker.
    """
    theoretical = trading_days_kept * bars_per_day
    if theoretical == 0:
        return 0.0
    return round(100.0 * rows_raw_session_filtered / theoretical, 2)


def compute_tier(coverage_pre_fill_pct: float, threshold: float = COVERAGE_THRESHOLD) -> str:
    """Clasifica el ticker segun su cobertura pre-fill, SIN filtrar nada del
    pipeline (decision del equipo tras revisar el checkpoint de la tarea
    1.2.1): el 60% deja de ser un filtro que descarta tickers y pasa a ser
    una ETIQUETA de uso.
      - "A": coverage_pre_fill_pct >= 60% -> apto para entrenamiento del
        Agente Maestro (el universo de entrenamiento real es un solo activo,
        FALABELLA, que queda comodamente en tier A con ~92%).
      - "B": coverage_pre_fill_pct < 60% -> demasiado ralo para usarse como
        activo de entrenamiento individual, pero sigue siendo valido para
        caracterizacion agregada del mercado y calibracion de ABIDES-Gym /
        RMSC04 (tarea 2.2.4 de MR), uso mucho mas tolerante a huecos.
    """
    return "A" if coverage_pre_fill_pct >= threshold * 100 else "B"


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
        stats["tier"] = compute_tier(stats["coverage_pre_fill_pct"])

        cleaned[ticker] = df_normalized
        scaler_params[ticker] = params
        per_ticker_stats[ticker] = stats

    return cleaned, scaler_params, per_ticker_stats


def build_cleaning_report(per_ticker_stats: dict, edge_policy: str,
                           input_dir: Path, output_dir: Path) -> dict:
    """Arma el dict final de cleaning_report.json.

    Decision del equipo (checkpoint de la tarea 1.2.1, revisado con BF):
    el 60% de cobertura pre-fill NO filtra tickers del pipeline -- los 30
    se procesan siempre. Se usa solo para clasificar cada ticker en un
    'tier' (A/B, ver compute_tier), porque el universo real de
    entrenamiento del Agente Maestro es un solo activo (FALABELLA, ~92%
    de cobertura pre-fill), y los tickers de baja cobertura igual aportan
    valor para caracterizacion agregada del mercado / calibracion de
    ABIDES-Gym (tarea 2.2.4 de MR).
    """
    tickers_bajo_umbral_pre_fill = sorted(
        t for t, s in per_ticker_stats.items() if s["under_threshold_pre_fill"]
    )
    tickers_tier_a = sorted(t for t, s in per_ticker_stats.items() if s["tier"] == "A")
    tickers_tier_b = sorted(t for t, s in per_ticker_stats.items() if s["tier"] == "B")
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
        "closing_auction_note": CLOSING_AUCTION_NOTE,
        "per_ticker": per_ticker_stats,
        "summary": {
            "n_tickers": len(per_ticker_stats),
            "total_rows_final": total_rows_final,
            "tickers_bajo_umbral_60pct_pre_fill": tickers_bajo_umbral_pre_fill,
            "tickers_tier_A": tickers_tier_a,
            "tickers_tier_B": tickers_tier_b,
            "coverage_metric_note": (
                "coverage_pct se calcula tal como fue definido en el briefing "
                "(filas_finales / (dias_conservados x 78), post reindex+ffill+"
                "bfill), pero por construccion del propio relleno es ~100% para "
                "cualquier ticker que conserve al menos un dia -- no discrimina "
                "liquidez, se reporta solo por completitud/transparencia. "
                "coverage_pre_fill_pct (filas realmente observadas antes de "
                "rellenar / velas teoricas de los dias conservados) es la "
                "metrica valida, y define el campo 'tier' de cada ticker (A si "
                ">=60%, B si no). Que la mitad del IPSA (tier B) tenga cobertura "
                "pre-fill baja no es un defecto del pipeline: es evidencia "
                "empirica que respalda la premisa del proyecto (mercado "
                "chileno de liquidez fina fuera de las acciones mas liquidas). "
                "El pipeline NO descarta ningun ticker por esto; 'tier' es una "
                "etiqueta de uso, no un filtro."
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
    tier_a = cleaning_report["summary"]["tickers_tier_A"]
    tier_b = cleaning_report["summary"]["tickers_tier_B"]

    print(f"Tickers procesados: {n_tickers} | filas finales totales: {total_rows}")
    print(f"Tier A (cobertura pre-fill >= 60%, apto entrenamiento): {len(tier_a)} tickers -> {tier_a}")
    print(f"Tier B (cobertura pre-fill < 60%, solo calibracion agregada): {len(tier_b)} tickers -> {tier_b}")
    print("  El pipeline NO descarta ningun ticker por esto -- 'tier' es una etiqueta en cleaning_report.json, no un filtro.")

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
