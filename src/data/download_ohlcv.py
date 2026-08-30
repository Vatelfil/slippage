"""
download_ohlcv.py
------------------
Sprint 1 (Hito 5, tarea 1.1.3) - Descarga y estructuracion de datos OHLCV IPSA via yfinance.

Descarga velas de 5 minutos para las 30 acciones del indice IPSA usando yfinance,
las guarda EN BRUTO (sin limpiar) en data/raw/, genera un manifest.json con los
parametros de la corrida y un reporte de calidad de datos (nulos, cobertura,
rango de fechas) que sirve de insumo directo para el Sprint 2 (limpieza y
preprocesamiento: forward fill, filtro horario, MinMaxScaler).

Uso (dentro del contenedor Docker, con acceso a internet):
    python src/data/download_ohlcv.py                 # descarga completa (30 tickers, 60 dias, 5 min)
    python src/data/download_ohlcv.py --check-only     # solo valida que los tickers respondan (rapido)
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf

# ---------------------------------------------------------------------------
# 1. Universo de 30 acciones del IPSA (nemotecnico Yahoo Finance, sufijo .SN)
# ---------------------------------------------------------------------------
# Fuente: composicion vigente tras el rebalanceo del 23-03-2026 (S&P DJI, sin
# adiciones/eliminaciones respecto al rebalanceo previo). IMPORTANTE:
# verificar esta lista contra la nomina oficial de la Bolsa de Santiago o
# S&P DJI antes de correr el pipeline completo -- algunos nemotecnicos de
# Yahoo difieren levemente del oficial (guiones, series). Por eso el script
# trae un modo --check-only: valida los 30 tickers en segundos, antes de
# gastar las 12 HH asignadas a la tarea en una descarga que podria fallar
# a mitad de camino.
IPSA_TICKERS: list[str] = [
    "AGUAS-A.SN", "CHILE.SN", "BCI.SN", "ITAUCL.SN", "BSANTANDER.SN",
    "CAP.SN", "CENCOSUD.SN", "CENCOMALLS.SN", "COLBUN.SN", "CCU.SN",
    "VAPORES.SN", "ANDINA-B.SN", "ENTEL.SN", "CMPC.SN", "COPEC.SN",
    "ENELAM.SN", "ENELCHILE.SN", "ECL.SN", "FALABELLA.SN", "IAM.SN",
    "ILC.SN", "LTM.SN", "PARAUCO.SN", "MALLPLAZA.SN", "QUINENCO.SN",
    "RIPLEY.SN", "SALFACORP.SN", "SMU.SN", "SQM-B.SN", "CONCHATORO.SN",
]

INTERVAL = "5m"
PERIOD = "60d"           # limite real de Yahoo Finance para velas de 5 min
SANTIAGO_TZ = ZoneInfo("America/Santiago")

RAW_DIR = Path("data/raw")


def validate_tickers(tickers: list[str]) -> tuple[list[str], list[str]]:
    """Descarga una ventana corta (5 dias / 15 min) por ticker solo para
    confirmar que Yahoo lo reconoce. Barato y rapido -- correr esto SIEMPRE
    antes del batch completo de 60 dias en 5 min.
    """
    ok, failed = [], []
    for t in tickers:
        try:
            df = yf.download(t, period="5d", interval="15m",
                              auto_adjust=True, progress=False)
            if df is None or df.empty:
                failed.append(t)
            else:
                ok.append(t)
        except Exception:
            failed.append(t)
    return ok, failed


def save_validation_result(ok: list[str], failed: list[str]) -> Path:
    """Persiste el resultado de la validacion en disco (no solo en consola),
    para no perderlo si se cierra la terminal. Se guarda siempre, incluso
    en modo --check-only.
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    run_date = datetime.now(SANTIAGO_TZ).strftime("%Y-%m-%d")
    out_path = RAW_DIR / f"ticker_validation_{run_date}.json"
    out_path.write_text(json.dumps(
        {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "ok": ok,
            "failed": failed,
        },
        indent=2, ensure_ascii=False,
    ))
    return out_path


def suggest_ticker(query: str, limit: int = 5) -> None:
    """Busca candidatos de simbolo en Yahoo Finance a partir de un nombre de
    empresa (ej. 'Banco Itau Chile'). Util para corregir un ticker que fallo
    la validacion sin tener que abrir el navegador.

    Requiere yfinance >= 0.2.40 (incluye la clase Search). Si tu version es
    mas antigua, actualiza con 'pip install --upgrade yfinance' o recurre a
    la busqueda manual en https://finance.yahoo.com.
    """
    try:
        from yfinance import Search
    except ImportError:
        print(
            "Tu version de yfinance no incluye yfinance.Search. "
            "Actualiza con 'pip install --upgrade yfinance' o busca "
            "manualmente en https://finance.yahoo.com"
        )
        return

    try:
        results = Search(query, max_results=limit).quotes
    except Exception as exc:
        print(f"No se pudo completar la busqueda ({exc}). Prueba la busqueda manual.")
        return

    if not results:
        print(f"Sin resultados para '{query}'. Prueba con otro nombre (ej. sin 'S.A.').")
        return

    print(f"Candidatos para '{query}':")
    for r in results:
        symbol = r.get("symbol", "?")
        name = r.get("shortname") or r.get("longname") or ""
        exchange = r.get("exchange", "?")
        marker = "  <- Santiago" if exchange in ("SGO", "SAN") or symbol.endswith(".SN") else ""
        print(f"  {symbol:15s} {name:35s} exchange={exchange}{marker}")


def download_ticker(ticker: str) -> pd.DataFrame | None:
    df = yf.download(ticker, period=PERIOD, interval=INTERVAL,
                      auto_adjust=True, progress=False)
    if df is None or df.empty:
        return None

    # yfinance puede devolver columnas MultiIndex incluso pidiendo un solo
    # ticker (versiones recientes) -- aplanamos por seguridad.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.reset_index()
    ts_col = "Datetime" if "Datetime" in df.columns else "Date"

    # Los timestamps de yfinance vienen en UTC; normalizamos y convertimos
    # EXPLICITAMENTE a America/Santiago (horario real de la sesion Telepregon).
    ts = pd.to_datetime(df[ts_col], utc=True)
    df["datetime_utc"] = ts
    df["datetime_santiago"] = ts.dt.tz_convert(SANTIAGO_TZ)
    df["ticker"] = ticker.replace(".SN", "")

    cols = ["ticker", "datetime_utc", "datetime_santiago",
            "Open", "High", "Low", "Close", "Volume"]
    df = df[cols].rename(columns=str.lower)
    return df


def quality_report(df: pd.DataFrame) -> dict:
    """Metricas basicas de calidad, SIN limpiar nada (eso es tarea de Sprint 2,
    item 1.2.1). Sirve para que el equipo sepa, antes de empezar a limpiar,
    que tan completos llegaron los datos por accion.
    """
    n = len(df)
    nulls = df[["open", "high", "low", "close", "volume"]].isna().sum().to_dict()
    trading_days = df["datetime_santiago"].dt.date.nunique()
    return {
        "rows": n,
        "trading_days": trading_days,
        "avg_rows_per_day": round(n / trading_days, 1) if trading_days else 0,
        "date_min": str(df["datetime_santiago"].min()),
        "date_max": str(df["datetime_santiago"].max()),
        "null_counts": nulls,
    }


def main(check_only: bool = False) -> None:
    print(f"Universo: {len(IPSA_TICKERS)} tickers | interval={INTERVAL} | period={PERIOD}")

    ok, failed = validate_tickers(IPSA_TICKERS)
    print(f"Validacion rapida -> OK: {len(ok)} | fallidos: {len(failed)}")
    validation_path = save_validation_result(ok, failed)
    print(f"Resultado de la validacion guardado en: {validation_path}")
    if failed:
        print("  Revisar nemotecnico en Yahoo Finance antes de continuar:", failed)
        print("  Tip: python src/data/download_ohlcv.py --suggest \"nombre de la empresa\"")

    if check_only:
        return

    if failed:
        print("Continuando solo con los tickers validos. Corrige los fallidos y vuelve a correr despues.")

    run_date = datetime.now(SANTIAGO_TZ).strftime("%Y-%m-%d")
    out_dir = RAW_DIR / f"ohlcv_5m_{run_date}"
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "interval": INTERVAL,
        "period": PERIOD,
        "timezone": "America/Santiago",
        "auto_adjust": True,
        "source": "yfinance",
        "tickers_requested": IPSA_TICKERS,
        "tickers_failed_validation": failed,
        "tickers_downloaded": [],
        "tickers_empty": [],
    }
    quality: dict[str, dict] = {}
    frames = []

    for ticker in ok:
        print(f"Descargando {ticker} ...")
        df = download_ticker(ticker)
        if df is None:
            manifest["tickers_empty"].append(ticker)
            print(f"  -> sin datos para {ticker}, se omite")
            continue
        df.to_parquet(out_dir / f"{ticker.replace('.SN', '')}.parquet", index=False)
        quality[ticker.replace(".SN", "")] = quality_report(df)
        manifest["tickers_downloaded"].append(ticker)
        frames.append(df)

    if frames:
        combined = pd.concat(frames, ignore_index=True)
        combined.to_parquet(out_dir / "_combined.parquet", index=False)
        print(f"Consolidado: {len(combined)} filas, {combined['ticker'].nunique()} tickers")

    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False)
    )
    (out_dir / "quality_report.json").write_text(
        json.dumps(quality, indent=2, ensure_ascii=False)
    )

    print(f"\nListo. Datos en: {out_dir}")
    print("Entregable para Sprint 2: manifest.json + quality_report.json + *.parquet por ticker")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-only", action="store_true",
        help="Solo valida que los 30 tickers respondan en Yahoo Finance, sin descargar los 60 dias completos.",
    )
    parser.add_argument(
        "--suggest", metavar="NOMBRE_EMPRESA", default=None,
        help='Busca candidatos de ticker por nombre, ej. --suggest "Banco Itau Chile"',
    )
    args = parser.parse_args()

    if args.suggest:
        suggest_ticker(args.suggest)
    else:
        main(check_only=args.check_only)
