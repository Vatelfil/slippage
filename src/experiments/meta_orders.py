"""Meta-ordenes como porcentaje del volumen diario (preparacion de la 2.3.3).

Autor: Benjamin Farias (BF). PROPUESTA para el Sprint Review: este modulo NO
modifica el entorno. Hoy la meta-orden es fija, Q_total = 10_000 acciones
(`meta_orden_quantity` en src/envs/maestro_ejecutor_protocol.py), igual para
cualquier ticker. Aqui se calcula el volumen diario mediano (ADV) por ticker
desde clean_5m y se generan meta-ordenes como fraccion del ADV, para que el
tamano del problema sea comparable entre tickers y snapshots.

ADV (acciones) = mediana, sobre los dias del snapshot, de la suma diaria de
volume_raw. Se usa la mediana y no la media para que un dia con operaciones
en bloque no domine. Dos versiones:
- con subasta: todas las velas del dia;
- sin subasta: excluye la vela 15:55, donde clean_ohlcv.py fusiona la
  subasta de cierre (market_params.CLOSING_AUCTION_BAR). Es la base por
  defecto, porque el Ejecutor opera en el flujo continuo
  (market_params.INCLUDE_CLOSING_AUCTION = False). La vela 15:55 incluye
  tambien los ultimos 5 min de negociacion continua; no se pueden separar.

Monto en CLP = acciones x precio de referencia, con el mismo precio que usa
ORDER_SIZE_POLICY (mediana de close_raw de velas observadas).

Uso:
    python -m src.experiments.meta_orders --snapshot 2026-08-23
    python -m src.experiments.meta_orders --snapshot 2026-08-23 --pct-adv 0.01 0.05 0.15
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

from src.config import market_params as mp

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = _REPO_ROOT / "data" / "processed"
DEFAULT_CONFIG_DIR = _REPO_ROOT / "config"
DEFAULT_PCT_ADV: List[float] = [0.01, 0.05, 0.15]
# Meta-orden actual del entorno (maestro_ejecutor_protocol.py, meta_orden_quantity).
CURRENT_Q_TOTAL = 10_000


def load_daily_volume(ticker: str, snapshot: str, data_dir: "str | Path" = DEFAULT_DATA_DIR) -> pd.DataFrame:
    """Volumen diario por ticker, con y sin la vela de subasta, y precio de
    referencia. Columnas: day, vol_con_subasta, vol_sin_subasta."""
    path = Path(data_dir) / f"clean_5m_{snapshot}" / f"{ticker}.parquet"
    df = pd.read_parquet(path, columns=["datetime_santiago", "volume_raw", "close_raw", "is_imputed"])
    ts = pd.to_datetime(df["datetime_santiago"])
    ts = ts.dt.tz_convert(mp.SANTIAGO_TZ) if ts.dt.tz is not None else ts.dt.tz_localize(mp.SANTIAGO_TZ)
    df = df.assign(day=ts.dt.date, is_auction=ts.dt.strftime("%H:%M") == mp.CLOSING_AUCTION_BAR)
    daily = df.groupby("day").agg(vol_con_subasta=("volume_raw", "sum"))
    daily["vol_sin_subasta"] = df[~df["is_auction"]].groupby("day")["volume_raw"].sum()
    daily = daily.fillna(0.0).reset_index()
    daily.attrs["precio_referencia"] = float(df.loc[~df["is_imputed"].astype(bool), "close_raw"].median())
    return daily


def meta_orders_for_ticker(daily: pd.DataFrame, pct_adv: Sequence[float],
                           base: str = "sin_subasta",
                           current_q: int = CURRENT_Q_TOTAL) -> Dict:
    """ADV y meta-ordenes de un ticker. `base` elige el ADV de referencia."""
    price = daily.attrs["precio_referencia"]
    adv = {"con_subasta": float(daily["vol_con_subasta"].median()),
           "sin_subasta": float(daily["vol_sin_subasta"].median())}
    ref = adv[base]
    orders = []
    for p in pct_adv:
        shares = int(max(1, round(p * ref)))
        orders.append({"pct_adv": float(p), "acciones": shares, "monto_clp": float(shares * price)})
    return {
        "precio_referencia_clp": price,
        "n_dias": int(len(daily)),
        "adv_acciones": adv,
        "adv_clp": {k: v * price for k, v in adv.items()},
        "base_adv": base,
        "meta_ordenes": orders,
        "orden_actual": {
            "acciones": int(current_q),
            "monto_clp": float(current_q * price),
            "pct_adv_sin_subasta": float(current_q / adv["sin_subasta"]) if adv["sin_subasta"] > 0 else None,
            "pct_adv_con_subasta": float(current_q / adv["con_subasta"]) if adv["con_subasta"] > 0 else None,
        },
    }


def build_meta_orders(snapshot: str, pct_adv: Sequence[float] = DEFAULT_PCT_ADV,
                      data_dir: "str | Path" = DEFAULT_DATA_DIR,
                      tickers: Optional[Sequence[str]] = None) -> Dict:
    snap = Path(data_dir) / f"clean_5m_{snapshot}"
    if not snap.is_dir():
        raise FileNotFoundError(f"No existe '{snap}'.")
    names = list(tickers) if tickers else sorted(
        p.stem for p in snap.glob("*.parquet") if not p.stem.startswith("_"))
    tiers = {}
    report = snap / "cleaning_report.json"
    if report.exists():
        tiers = {t: v.get("tier") for t, v in
                 json.loads(report.read_text(encoding="utf-8")).get("per_ticker", {}).items()}
    per_ticker = {}
    for t in names:
        res = meta_orders_for_ticker(load_daily_volume(t, snapshot, data_dir), pct_adv)
        res["tier"] = tiers.get(t)
        per_ticker[t] = res
    return {
        "metadata": {
            "tarea": "Preparacion 2.3.3 - meta-ordenes como % del ADV (propuesta, no integrada al entorno)",
            "autor": "Benjamin Farias (BF)",
            "fecha_generacion": datetime.now(timezone.utc).isoformat(),
            "snapshot": snapshot,
            "pct_adv": [float(p) for p in pct_adv],
            "definicion_adv": "mediana sobre los dias del snapshot de la suma diaria de volume_raw (acciones)",
            "base_adv": "sin_subasta (excluye la vela 15:55 con la subasta de cierre)",
            "precio_referencia": mp.ORDER_SIZE_POLICY["precio_referencia"],
            "orden_actual": f"Q_total = {CURRENT_Q_TOTAL} acciones (maestro_ejecutor_protocol.py)",
            "nota": "La vela 15:55 incluye la subasta y los ultimos 5 min de negociacion continua; no se separan.",
        },
        "tickers": per_ticker,
    }


def main(argv: Optional[Sequence[str]] = None) -> Path:
    parser = argparse.ArgumentParser(description="Meta-ordenes como % del ADV (preparacion 2.3.3).")
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--pct-adv", type=float, nargs="+", default=DEFAULT_PCT_ADV)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--tickers", nargs="+", default=None)
    parser.add_argument("--output", type=Path, default=None,
                        help="Default: config/meta_orders_<snapshot>.json")
    args = parser.parse_args(argv)
    payload = build_meta_orders(args.snapshot, args.pct_adv, args.data_dir, args.tickers)
    out = args.output or DEFAULT_CONFIG_DIR / f"meta_orders_{args.snapshot}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"JSON -> {out}")
    fal = payload["tickers"].get("FALABELLA")
    if fal:
        print("FALABELLA", json.dumps({k: fal[k] for k in ("adv_acciones", "orden_actual", "meta_ordenes")}))
    return out


if __name__ == "__main__":
    main()
