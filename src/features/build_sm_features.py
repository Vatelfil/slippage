"""
build_sm_features.py
---------------------
Sprint 2 (Hito 5, tarea 1.2.2) - Calculo de las variables del vector de
estado del Agente Maestro (S_M) que dependen de OHLCV.

Toma como INPUT el output de `clean_ohlcv.py` (tarea 1.2.1,
data/processed/clean_5m_<fecha>/) y produce data/processed/sm_features_<fecha>/
con las 7 columnas del contrato `docs/schemas/SM_schema.json`, en el orden de
indice que ese schema define (0..6). De esas 7, esta tarea calcula 4:

    - tau_t         (indice 1): fraccion de tiempo transcurrido de la jornada.
    - volatilidad   (indice 3): close.rolling(6).std(), normalizado MinMaxScaler.
    - vol_promedio  (indice 4): volume.rolling(6).mean(), normalizado MinMaxScaler.
    - sesion        (indice 6): tramo horario codificado en {0.0, 0.5, 1.0}.

Las otras 3 NO se calculan aca y quedan explicitas para que MR arme el
`gymnasium.spaces.Box(shape=(7,))` completo sin adivinar nada:

    - q_t       (indice 0): NaN. Lo calcula el entorno en runtime
      ((Q_total - Q_ejecutado) / Q_total), tarea 2.1.1/2.1.4 de MR.
    - n_slices  (indice 2): NaN. Lo calcula el entorno en runtime
      (slices_enviados / 13), tarea 2.1.1/2.1.4 de MR.
    - OBI_agregado (indice 5): placeholder explicito 0.0. Viene de
      ABIDES-Gym (tareas 1.2.3/1.2.4 de MR, aun no integradas), tal como
      instruye SM_schema.json.

NOTA sobre `sesion` (discrepancia a levantar en Sprint Review): el informe de
Titulo I describe esta variable como {0,1,2}; el schema de PS
(docs/schemas/SM_schema.json) la define ya normalizada a {0.0, 0.5, 1.0}
(exigido por el `Box` de gymnasium.spaces con high=1.0 en este indice). Este
script sigue el schema, que ademas fija los CORTES DE HORA EXACTA en
docs/arquitectura_entorno_simulacion.md seccion 4.1: [9,11)->0.0,
[11,14)->0.5, [14,16]->1.0 (decision confirmada con BF; no 11:30 como decia
un borrador anterior del brief).

Reglas duras (sin excepcion):
    - Las ventanas rolling NUNCA cruzan dias ni tickers: se agrupa por
      (ticker, dia) antes de cualquier `.rolling()`. Un rolling continuo
      mezclaria el cierre de un dia con la apertura del siguiente y
      contaminaria justo el patron que el Maestro debe aprender (volatilidad
      de apertura vs. cierre).
    - Sin look-ahead: `rolling(center=False)`, que es el default de pandas
      (ventana estrictamente hacia atras).
    - min_periods=6 (ventana completa exigida): las primeras 5 velas de cada
      dia (30 min sin ventana completa) quedan con NaN EXPLICITO en
      `volatilidad`/`vol_promedio`, y se CONSERVAN en el output (no se
      descartan) -- analogo a los placeholders de q_t/n_slices, y coherente
      con que `sm_features_report.json` debe reportar "% de NaN" por
      variable (si se descartaran esas filas, ese % siempre seria 0 y el
      reporte perderia sentido).

Diagnostico de volatilidad "real" vs. "con imputados" (decision del
checkpoint de 1.2.1, columna `is_imputed`): ademas de la columna oficial
`volatilidad` (rolling(6).std() sobre TODA la serie, incluyendo velas
rellenadas por ffill/bfill), se calcula una columna auxiliar
`volatilidad_raw_min_obs`: el mismo rolling(6).std(), pero calculado
SOLO sobre las velas realmente observadas (`is_imputed == False`) dentro de
cada ventana, exigiendo al menos 4 de las 6. Si hay menos de 4 velas reales
en la ventana, queda NaN. Esto se logra enmascarando `close_raw` a NaN donde
`is_imputed` es True y dejando que `rolling(6, min_periods=4).std()` ignore
esos NaN (pandas excluye NaN del calculo y exige min_periods valores no-NaN
para producir un resultado). Como las velas imputadas repiten el ultimo
precio conocido (variacion cero), incluirlas en el calculo oficial (a) tiende
a SUBESTIMAR la volatilidad real frente al calculo diagnostico (b). Para
FALABELLA (caso de referencia del informe), `sm_features_report.json`
reporta la diferencia media y maxima entre (a) y (b) como evidencia para el
Sprint Review. La columna OFICIAL del vector S_M sigue siendo (a)
(`volatilidad`); (b) es solo diagnostico, nunca se normaliza ni se usa como
input del Maestro.

Salidas en data/processed/sm_features_<fecha>/:
    - <TICKER>.parquet / _combined.parquet: 7 columnas del schema (orden
      0..6) + timestamp + columnas de referencia (_raw, is_imputed,
      volatilidad_raw_min_obs).
    - scaler_params.json: copia del de 1.2.1, extendida con las entradas de
      volatilidad/vol_promedio por ticker (mismo archivo, autocontenido).
    - sm_features_report.json: estadisticos por variable (min/max/media/std/
      %NaN), diagnostico de volatilidad de FALABELLA, y resultado de los
      sanity checks intradiarios (si se paso --plot-ticker).

Graficos de sanidad (flag --plot-ticker, ej. FALABELLA): 2 PNG en
results/sprint2/ (perfil intradiario de volumen y de volatilidad,
promediados por bucket de 5 min de tiempo-de-dia). Se espera volatilidad en
forma de U invertida (maximo apertura, minimo ~14:00, repunte al cierre,
Figuras 7.5/7.6 del informe de Titulo I) y un salto fuerte de volumen en la
subasta de cierre. Si el patron NO aparece, se imprime un banner
"[SANITY CHECK] FALLO" bien visible y se deja registro en
sm_features_report.json -- el pipeline NO se detiene solo (gate humano,
igual criterio que el "tier" de cobertura de 1.2.1).

Uso (dentro del contenedor Docker):
    python src/features/build_sm_features.py
    python src/features/build_sm_features.py --plot-ticker FALABELLA
    python src/features/build_sm_features.py --dry-run
"""

from __future__ import annotations

import argparse
import copy
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

PROCESSED_DIR = Path("data/processed")
RESULTS_DIR = Path("results/sprint2")

ROLLING_WINDOW = 6                 # 6 velas de 5 min = 30 min, frecuencia de decision del Maestro
MIN_PERIODS = 6                    # ventana completa exigida (ver docstring de modulo)
MIN_OBSERVED_FOR_DIAGNOSTIC = 4    # minimo de velas REALES (no imputadas) para el diagnostico (b)
JORNADA_DURACION_MIN = 390

FALABELLA_TICKER = "FALABELLA"     # caso de referencia del informe de Titulo I

FEATURE_COLUMNS_ORDER: list[str] = [
    "timestamp", "q_t", "tau_t", "n_slices",
    "volatilidad", "vol_promedio", "OBI_agregado", "sesion",
]
SM_VARIABLES: list[str] = ["q_t", "tau_t", "n_slices", "volatilidad", "vol_promedio", "OBI_agregado", "sesion"]
RAW_REFERENCE_COLUMNS: list[str] = [
    "close_raw", "volume_raw", "volatilidad_raw", "vol_promedio_raw",
    "volatilidad_raw_min_obs", "is_imputed",
]

SESSION_CUTOFFS_HOUR = {"apertura": [9, 11], "media_jornada": [11, 14], "cierre": [14, 16]}

MIN_PERIODS_JUSTIFICATION = (
    "Ventana completa exigida (min_periods=6, sin look-ahead parcial); los "
    "primeros 30 min de cada jornada (5 velas) quedan con NaN explicito en "
    "volatilidad/vol_promedio y se conservan en el output -- analogo a los "
    "placeholders de q_t/n_slices."
)

_VARIABLE_NOTES = {
    "q_t": "Placeholder interno (runtime del entorno, tarea 2.1.1/2.1.4 MR). No calculado por este pipeline.",
    "n_slices": "Placeholder interno (runtime del entorno, tarea 2.1.1/2.1.4 MR). No calculado por este pipeline.",
    "OBI_agregado": "Placeholder explicito 0.0, pendiente integracion ABIDES-Gym (tareas 1.2.3/1.2.4, MR).",
}


# ---------------------------------------------------------------------------
# Descubrimiento de rutas de entrada/salida
# ---------------------------------------------------------------------------

def find_latest_clean_dir(processed_root: Path = PROCESSED_DIR) -> Path | None:
    """Busca el subdirectorio 'clean_5m_<fecha>' mas reciente (salida de la
    tarea 1.2.1) dentro de processed_root. Devuelve None si no hay ninguno.
    """
    if not processed_root.exists():
        return None
    candidates = sorted(
        p for p in processed_root.iterdir() if p.is_dir() and p.name.startswith("clean_5m_")
    )
    return candidates[-1] if candidates else None


def derive_output_dir(input_dir: Path, output_root: Path = PROCESSED_DIR,
                       prefix: str = "sm_features_") -> Path:
    """Reusa la fecha del directorio de entrada (mismo criterio que
    clean_ohlcv.derive_output_dir): 'clean_5m_2026-08-23' -> 'sm_features_2026-08-23'.
    """
    name = input_dir.name
    if not name.startswith("clean_5m_"):
        raise ValueError(
            f"No se pudo extraer la fecha de '{name}' (se esperaba el patron "
            "'clean_5m_<fecha>'). Especifica --output-dir explicitamente."
        )
    fecha = name[len("clean_5m_"):]
    return output_root / f"{prefix}{fecha}"


# ---------------------------------------------------------------------------
# Carga
# ---------------------------------------------------------------------------

def load_clean_ticker_files(input_dir: Path) -> dict[str, pd.DataFrame]:
    """Carga cada <TICKER>.parquet de input_dir (excluye _combined.parquet).
    Devuelve {ticker: DataFrame}, ordenado por 'datetime_santiago'.
    """
    tickers: dict[str, pd.DataFrame] = {}
    for path in sorted(input_dir.glob("*.parquet")):
        if path.stem == "_combined":
            continue
        df = pd.read_parquet(path).sort_values("datetime_santiago").reset_index(drop=True)
        tickers[path.stem] = df
    return tickers


def load_clean_scaler_params(input_dir: Path) -> dict:
    """Carga scaler_params.json escrito por clean_ohlcv.py (tarea 1.2.1)."""
    path = input_dir / "scaler_params.json"
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# tau_t y sesion
# ---------------------------------------------------------------------------

def compute_tau_t(datetime_santiago: pd.Series) -> pd.Series:
    """tau_t = (t - 09:30_del_mismo_dia_de_t) / 390 min.

    Se reinicia solo porque la apertura del dia se recalcula fila a fila con
    la FECHA de esa misma fila (no requiere agrupar por dia para resetear).
    """
    day_open = datetime_santiago.dt.normalize() + pd.Timedelta(hours=9, minutes=30)
    minutos = (datetime_santiago - day_open).dt.total_seconds() / 60.0
    return minutos / JORNADA_DURACION_MIN


def compute_sesion(datetime_santiago: pd.Series) -> pd.Series:
    """Cortes de HORA EXACTA (docs/arquitectura_entorno_simulacion.md, 4.1,
    decision confirmada con BF): [9,11)->0.0, [11,14)->0.5, [14,16]->1.0.
    """
    hour = datetime_santiago.dt.hour
    values = np.select([hour < 11, hour < 14], [0.0, 0.5], default=1.0)
    return pd.Series(values, index=datetime_santiago.index, dtype=float)


# ---------------------------------------------------------------------------
# Rolling: volatilidad y vol_promedio (oficiales) + diagnostico
# ---------------------------------------------------------------------------

def compute_rolling_features(df_ticker: pd.DataFrame, window: int = ROLLING_WINDOW,
                              min_periods: int = MIN_PERIODS) -> pd.DataFrame:
    """Agrega 'volatilidad_raw' (close_raw.rolling(6).std()) y
    'vol_promedio_raw' (volume_raw.rolling(6).mean()), agrupando SIEMPRE por
    (ticker, dia) via `groupby(date).transform(...)` para que el rolling
    jamas cruce el cierre de un dia con la apertura del siguiente.
    `rolling(center=False)` (default de pandas) asegura cero look-ahead.
    """
    df = df_ticker.copy()
    date_key = df["datetime_santiago"].dt.date

    df["volatilidad_raw"] = df.groupby(date_key)["close_raw"].transform(
        lambda s: s.rolling(window, min_periods=min_periods).std()
    )
    df["vol_promedio_raw"] = df.groupby(date_key)["volume_raw"].transform(
        lambda s: s.rolling(window, min_periods=min_periods).mean()
    )
    return df


def compute_volatility_diagnostic(df_ticker: pd.DataFrame, window: int = ROLLING_WINDOW,
                                   min_observed: int = MIN_OBSERVED_FOR_DIAGNOSTIC) -> pd.Series:
    """Version diagnostica de la volatilidad: mismo rolling(6).std() sobre
    close_raw, pero calculado SOLO con las velas realmente observadas
    (is_imputed == False) dentro de la ventana, exigiendo al menos
    min_observed de las `window`. Se enmascara close_raw a NaN donde
    is_imputed es True: pandas `.rolling(..., min_periods=min_observed)`
    ignora los NaN dentro de la ventana para el calculo y solo produce un
    valor si hay al menos min_observed observaciones no-NaN -- exactamente
    la semantica pedida, sin loops explicitos.
    """
    date_key = df_ticker["datetime_santiago"].dt.date
    close_masked = df_ticker["close_raw"].where(~df_ticker["is_imputed"])
    return close_masked.groupby(date_key).transform(
        lambda s: s.rolling(window, min_periods=min_observed).std()
    )


def compute_volatility_diagnostic_comparison(df_ticker: pd.DataFrame) -> dict:
    """Compara, fila a fila donde ambas existen, la volatilidad oficial (a,
    con imputados) contra la diagnostica (b, solo velas reales). Como las
    velas imputadas repiten el ultimo precio (variacion cero), (a) tiende a
    subestimar la dispersion real frente a (b) cuando hay imputacion dentro
    de la ventana.
    """
    a = df_ticker["volatilidad_raw"]
    b = df_ticker["volatilidad_raw_min_obs"]
    both_valid = a.notna() & b.notna()
    diff = (a[both_valid] - b[both_valid]).abs()

    return {
        "methodology": (
            "(a) volatilidad_raw = close_raw.rolling(6, min_periods=6).std() "
            "sobre la serie completa (incluye velas imputadas por ffill/bfill). "
            "(b) volatilidad_raw_min_obs = mismo rolling(6).std(), pero solo "
            "sobre velas con is_imputed=False, exigiendo al menos "
            f"{MIN_OBSERVED_FOR_DIAGNOSTIC} de {ROLLING_WINDOW} observadas."
        ),
        "n_windows_total": int(len(df_ticker)),
        "n_windows_compared": int(both_valid.sum()),
        "pct_windows_diagnostic_nan": round(100.0 * b.isna().mean(), 2),
        "mean_abs_diff": float(diff.mean()) if len(diff) else None,
        "max_abs_diff": float(diff.max()) if len(diff) else None,
    }


# ---------------------------------------------------------------------------
# Normalizacion (post-rolling, por ticker)
# ---------------------------------------------------------------------------

def normalize_with_minmax(series: pd.Series) -> tuple[pd.Series, dict]:
    """MinMaxScaler ignora NaN en fit() y los preserva en transform()
    (comportamiento documentado de scikit-learn): permite normalizar
    volatilidad_raw/vol_promedio_raw sin filtrar antes las filas con NaN de
    los primeros 30 min de cada jornada.

    Se recorta (`np.clip`) el resultado a [0, 1] porque `scale_*x + min_`
    puede desbordar por redondeo de float64 justo en el punto que definio
    data_min_/data_max_ (ej. 1.0000000000000002 en vez de 1.0) -- sin
    tolerancia, ese desborde microscopico rompe la validacion estricta de
    `gymnasium.spaces.Box(high=1.0)` en Sprint 3. `np.clip` preserva NaN.
    """
    values = series.to_numpy(dtype=float).reshape(-1, 1)
    scaler = MinMaxScaler()
    scaler.fit(values)
    transformed = np.clip(scaler.transform(values).ravel(), 0.0, 1.0)

    params = {
        "data_min_": float(scaler.data_min_[0]),
        "data_max_": float(scaler.data_max_[0]),
        "data_range_": float(scaler.data_range_[0]),
        "scale_": float(scaler.scale_[0]),
        "min_": float(scaler.min_[0]),
    }
    return pd.Series(transformed, index=series.index), params


# ---------------------------------------------------------------------------
# Orquestacion por ticker
# ---------------------------------------------------------------------------

def build_ticker_features(ticker: str, df_clean: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Arma las 7 columnas del vector S_M para UN ticker + columnas de
    referencia. Devuelve (df_features, scaler_params_de_este_ticker) donde
    scaler_params_de_este_ticker = {'volatilidad': {...}, 'vol_promedio': {...}}.
    """
    df = compute_rolling_features(df_clean)
    df["volatilidad_raw_min_obs"] = compute_volatility_diagnostic(df)

    df["volatilidad"], vol_params = normalize_with_minmax(df["volatilidad_raw"])
    df["vol_promedio"], volp_params = normalize_with_minmax(df["vol_promedio_raw"])

    df["tau_t"] = compute_tau_t(df["datetime_santiago"])
    df["sesion"] = compute_sesion(df["datetime_santiago"])

    df["q_t"] = np.nan       # ver docstring de modulo: calculado por el entorno en runtime
    df["n_slices"] = np.nan  # idem
    df["OBI_agregado"] = 0.0  # placeholder explicito, pendiente ABIDES-Gym

    df["timestamp"] = df["datetime_santiago"]

    df_out = df[FEATURE_COLUMNS_ORDER + RAW_REFERENCE_COLUMNS].copy()
    scaler_params_ticker = {"volatilidad": vol_params, "vol_promedio": volp_params}
    return df_out, scaler_params_ticker


# ---------------------------------------------------------------------------
# Estadisticos / reporte
# ---------------------------------------------------------------------------

def _safe_float(x: float) -> float | None:
    return None if pd.isna(x) else float(x)


def compute_variable_stats(df_combined: pd.DataFrame) -> dict:
    """Para cada una de las 7 variables del vector S_M: min, max, media,
    std y % de NaN (sobre todos los tickers juntos).
    """
    stats: dict[str, dict] = {}
    for col in SM_VARIABLES:
        series = df_combined[col]
        entry = {
            "min": _safe_float(series.min()),
            "max": _safe_float(series.max()),
            "mean": _safe_float(series.mean()),
            "std": _safe_float(series.std()),
            "pct_nan": round(100.0 * series.isna().mean(), 2),
        }
        if col in _VARIABLE_NOTES:
            entry["note"] = _VARIABLE_NOTES[col]
        stats[col] = entry
    return stats


def merge_scaler_params(clean_scaler_params: dict, sm_scaler_params_by_ticker: dict) -> dict:
    """Copia (sin mutar) el scaler_params.json de 1.2.1 y le agrega las
    entradas de volatilidad/vol_promedio por ticker, para que
    sm_features_<fecha>/ quede autocontenido (MR/PS no necesitan conservar
    tambien clean_5m_<fecha>/ para invertir la normalizacion).
    """
    merged = copy.deepcopy(clean_scaler_params)
    merged["generated_at"] = datetime.now(timezone.utc).isoformat()
    merged["source_task"] = "1.2.1 + 1.2.2"
    merged["columns_normalized_1_2_2"] = ["volatilidad", "vol_promedio"]
    merged.setdefault("scalers", {})
    for ticker, params in sm_scaler_params_by_ticker.items():
        merged["scalers"].setdefault(ticker, {})
        merged["scalers"][ticker].update(params)
    return merged


# ---------------------------------------------------------------------------
# Sanity checks + graficos intradiarios
# ---------------------------------------------------------------------------

def _time_of_day_bucket(timestamp: pd.Series) -> pd.Series:
    """78 buckets de 5 min por tiempo-de-dia ('HH:MM'), NUNCA por hora
    completa: una agregacion horaria diluiria el salto de volumen de la
    subasta de cierre (~15:55), que es justo lo que el chequeo debe detectar.
    """
    return timestamp.dt.strftime("%H:%M")


def sanity_check_volume_profile(df_ticker: pd.DataFrame) -> dict:
    """El bucket de volumen promedio maximo debe caer en las ultimas 2
    barras de la jornada (15:50, 15:55) -- salto de la subasta de cierre.
    """
    buckets = df_ticker.groupby(_time_of_day_bucket(df_ticker["timestamp"]))["volume_raw"].mean()
    buckets = buckets.reindex(sorted(buckets.index))

    last_two = list(buckets.index[-2:])
    max_bucket = buckets.idxmax()
    passed = max_bucket in last_two

    warning = None
    if not passed:
        warning = (
            f"Volumen promedio maximo en el bucket {max_bucket}, se esperaba en "
            f"las ultimas 2 barras de la jornada ({last_two})."
        )
    return {"pass": bool(passed), "max_avg_volume_bucket": max_bucket, "warning": warning}


def sanity_check_volatility_profile(df_ticker: pd.DataFrame) -> dict:
    """Chequeo laxo de forma en U invertida: el bucket de volatilidad
    promedio minima cae en una ventana amplia 13:00-15:00, y tanto la
    apertura como el cierre promedian mas volatilidad que la mitad del dia.
    """
    buckets = df_ticker.groupby(_time_of_day_bucket(df_ticker["timestamp"]))["volatilidad_raw"].mean()
    buckets = buckets.reindex(sorted(buckets.index)).dropna()

    if buckets.empty:
        return {
            "pass": False, "min_avg_volatility_bucket": None,
            "warning": "Sin suficientes valores no-NaN de volatilidad_raw para el chequeo.",
        }

    min_bucket = buckets.idxmin()
    min_bucket_ok = "13:00" <= min_bucket <= "15:00"

    apertura = buckets.iloc[:6].mean()
    cierre = buckets.iloc[-6:].mean()
    media_jornada = buckets.iloc[6:-6].mean() if len(buckets) > 12 else buckets.mean()

    apertura_mayor = apertura > media_jornada
    cierre_mayor = cierre > media_jornada
    passed = min_bucket_ok and apertura_mayor and cierre_mayor

    warning = None
    if not passed:
        warning = (
            f"Patron U-invertida no confirmado: bucket minimo={min_bucket} "
            f"(esperado en [13:00, 15:00]); apertura={apertura:.4g} vs "
            f"media_jornada={media_jornada:.4g} ({'OK' if apertura_mayor else 'FALLA'}); "
            f"cierre={cierre:.4g} vs media_jornada={media_jornada:.4g} "
            f"({'OK' if cierre_mayor else 'FALLA'})."
        )
    return {"pass": bool(passed), "min_avg_volatility_bucket": min_bucket, "warning": warning}


def plot_intraday_profiles(df_ticker: pd.DataFrame, ticker: str, output_dir: Path) -> dict:
    """Genera 2 PNG (volumen y volatilidad promedio por bucket de 5 min de
    tiempo-de-dia) reusando el df_ticker ya calculado en memoria, y corre
    los 2 sanity checks. Si alguno falla, imprime un banner visible en
    stdout pero NO detiene la ejecucion (gate humano).
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_dir.mkdir(parents=True, exist_ok=True)
    bucket_key = _time_of_day_bucket(df_ticker["timestamp"])

    volume_profile = df_ticker.groupby(bucket_key)["volume_raw"].mean()
    volume_profile = volume_profile.reindex(sorted(volume_profile.index))
    volatility_profile = df_ticker.groupby(bucket_key)["volatilidad_raw"].mean()
    volatility_profile = volatility_profile.reindex(sorted(volatility_profile.index))

    fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(volume_profile.index, volume_profile.to_numpy())
    ax.set_title(f"{ticker} - Perfil intradiario de volumen promedio")
    ax.set_xlabel("Hora del dia (bucket de 5 min)")
    ax.set_ylabel("Volumen promedio")
    ax.set_xticks(volume_profile.index[::6])
    ax.tick_params(axis="x", rotation=90)
    fig.tight_layout()
    volume_path = output_dir / f"{ticker}_volumen_intradiario.png"
    fig.savefig(volume_path)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(volatility_profile.index, volatility_profile.to_numpy(), color="darkred")
    ax.set_title(f"{ticker} - Perfil intradiario de volatilidad promedio")
    ax.set_xlabel("Hora del dia (bucket de 5 min)")
    ax.set_ylabel("Volatilidad promedio (std de close, CLP)")
    ax.set_xticks(volatility_profile.index[::6])
    ax.tick_params(axis="x", rotation=90)
    fig.tight_layout()
    volatility_path = output_dir / f"{ticker}_volatilidad_intradiario.png"
    fig.savefig(volatility_path)
    plt.close(fig)

    volume_check = sanity_check_volume_profile(df_ticker)
    volatility_check = sanity_check_volatility_profile(df_ticker)

    for name, check in (("volume_profile", volume_check), ("volatility_profile", volatility_check)):
        if not check["pass"]:
            print(f"[SANITY CHECK] FALLO - {name} ({ticker}) - revisar antes de avanzar a Sprint 3")
            print(f"  detalle: {check['warning']}")

    return {
        "volume_profile": volume_check,
        "volatility_profile": volatility_check,
        "plots": [str(volume_path), str(volatility_path)],
    }


# ---------------------------------------------------------------------------
# Reporte + escritura
# ---------------------------------------------------------------------------

def build_sm_features_report(variable_stats: dict, per_ticker_meta: dict,
                              volatility_diagnostic_falabella: dict | None,
                              sanity_results: dict, input_dir: Path, output_dir: Path) -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "rolling_window_bars": ROLLING_WINDOW,
        "min_periods": MIN_PERIODS,
        "min_periods_justification": MIN_PERIODS_JUSTIFICATION,
        "min_observed_for_diagnostic": MIN_OBSERVED_FOR_DIAGNOSTIC,
        "session_cutoffs_hour": SESSION_CUTOFFS_HOUR,
        "variables": variable_stats,
        "per_ticker": per_ticker_meta,
        "volatility_diagnostic_falabella": volatility_diagnostic_falabella,
        "sanity_checks": sanity_results,
    }


def write_outputs(features: dict[str, pd.DataFrame], scaler_params_merged: dict,
                   report: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    frames = []
    for ticker, df in features.items():
        df.to_parquet(output_dir / f"{ticker}.parquet", index=False)
        frames.append(df)

    if frames:
        combined = pd.concat(frames, ignore_index=True)
        combined.to_parquet(output_dir / "_combined.parquet", index=False)

    (output_dir / "sm_features_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False)
    )
    (output_dir / "scaler_params.json").write_text(
        json.dumps(scaler_params_merged, indent=2, ensure_ascii=False)
    )


def main(input_dir: Path | None = None, output_dir: Path | None = None,
         dry_run: bool = False, plot_ticker: str | None = None) -> None:
    if input_dir is None:
        input_dir = find_latest_clean_dir()
        if input_dir is None:
            raise SystemExit(
                f"No se encontro ningun directorio 'clean_5m_<fecha>' en {PROCESSED_DIR}. "
                "Corre primero src/data/clean_ohlcv.py (tarea 1.2.1) o especifica --input-dir."
            )
        print(f"--input-dir no especificado, autodetectado: {input_dir}")

    if output_dir is None:
        output_dir = derive_output_dir(input_dir)

    print(f"Calculando features S_M desde: {input_dir}")

    clean_tickers = load_clean_ticker_files(input_dir)
    clean_scaler_params = load_clean_scaler_params(input_dir)

    features: dict[str, pd.DataFrame] = {}
    sm_scaler_params_by_ticker: dict[str, dict] = {}
    per_ticker_meta: dict[str, dict] = {}

    for ticker, df_clean in clean_tickers.items():
        df_features, scaler_params_ticker = build_ticker_features(ticker, df_clean)
        features[ticker] = df_features
        sm_scaler_params_by_ticker[ticker] = scaler_params_ticker
        per_ticker_meta[ticker] = {
            "rows": len(df_features),
            "days": int(df_features["timestamp"].dt.date.nunique()),
            "pct_nan_volatilidad": round(100.0 * df_features["volatilidad"].isna().mean(), 2),
            "pct_nan_vol_promedio": round(100.0 * df_features["vol_promedio"].isna().mean(), 2),
        }

    combined = pd.concat(features.values(), ignore_index=True)
    variable_stats = compute_variable_stats(combined)

    volatility_diagnostic_falabella = None
    if FALABELLA_TICKER in features:
        volatility_diagnostic_falabella = compute_volatility_diagnostic_comparison(features[FALABELLA_TICKER])
    else:
        print(f"ADVERTENCIA: {FALABELLA_TICKER} no esta en el input; se omite el diagnostico de volatilidad de referencia.")

    sanity_results: dict[str, dict] = {}
    if plot_ticker:
        if plot_ticker not in features:
            raise SystemExit(f"--plot-ticker {plot_ticker!r} no esta en el input. Tickers disponibles: {sorted(features)}")
        sanity_results[plot_ticker] = plot_intraday_profiles(features[plot_ticker], plot_ticker, RESULTS_DIR)

    scaler_params_merged = merge_scaler_params(clean_scaler_params, sm_scaler_params_by_ticker)
    report = build_sm_features_report(
        variable_stats, per_ticker_meta, volatility_diagnostic_falabella,
        sanity_results, input_dir, output_dir,
    )

    print(f"Tickers procesados: {len(features)}")
    if volatility_diagnostic_falabella:
        print(
            f"Diagnostico volatilidad {FALABELLA_TICKER} -> "
            f"diff media: {volatility_diagnostic_falabella['mean_abs_diff']:.6g} | "
            f"diff maxima: {volatility_diagnostic_falabella['max_abs_diff']:.6g} | "
            f"ventanas comparadas: {volatility_diagnostic_falabella['n_windows_compared']}"
        )

    if dry_run:
        print(f"[dry-run] No se escribieron archivos. Output hubiera sido: {output_dir}")
        return

    write_outputs(features, scaler_params_merged, report, output_dir)
    print(f"\nListo. Features S_M en: {output_dir}")
    print("Entregable para Sprint 3: <TICKER>.parquet + _combined.parquet + scaler_params.json + sm_features_report.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir", type=Path, default=None,
        help="Directorio 'data/processed/clean_5m_<fecha>' (salida de 1.2.1). Default: el mas reciente.",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=None,
        help="Directorio de salida. Default: 'data/processed/sm_features_<fecha>' (misma fecha del input).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Calcula todo el pipeline e imprime el resumen, pero no escribe archivos.",
    )
    parser.add_argument(
        "--plot-ticker", metavar="TICKER", default=None,
        help="Genera los 2 graficos de sanidad intradiarios + sanity checks para este ticker, ej. FALABELLA.",
    )
    args = parser.parse_args()

    main(input_dir=args.input_dir, output_dir=args.output_dir,
         dry_run=args.dry_run, plot_ticker=args.plot_ticker)
