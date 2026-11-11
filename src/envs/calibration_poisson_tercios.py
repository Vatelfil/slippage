"""Calibración del modelo de Poisson por tercios de actividad diaria (BF, 11 nov 2026).

La calibración de la 2.1.3 (`calibration_poisson.py`) promedia los 60 días del snapshot 2026-08-23 en un solo juego
de parámetros por activo y tramo: todas las jornadas simuladas son «el día promedio». Este módulo calibra lo mismo,
con el mismo método (`calibrate_tramo`), pero por separado para los días de actividad baja, media y alta, para que
el entrenamiento pueda sortear un tipo de día por jornada.

Reglas (decididas por BF el 11 nov, antes de ver los parámetros por tercio):

- **Días:** la unión de los snapshots `SNAPSHOTS`. Si un día está en varios, se toma de la descarga más reciente
  (yfinance corrige volúmenes después; es el mismo criterio de «el print más reciente» de la 1.2.1). Se excluye el
  día en que se hizo cada descarga, porque sus velas todavía no son definitivas.
- **Tercios:** por activo, según el volumen del día completo (velas observadas, sin la subasta de cierre, con el tope
  del percentil 99 de la 2.1.3). El día tiene la misma clase en los tres tramos, así que la condición dura toda la
  jornada.
- **Qué se informa:** λ+ y λ− salen del volumen, así que difieren entre tercios por construcción; eso no prueba nada.
  Lo informativo es si la volatilidad (desviación de los retornos de 5 min) también difiere: IC 95 % bootstrap por
  días del alto − bajo. La decisión de reentrenar no se toma aquí, sino con la prueba de reglas fijas (tarea B).

Los archivos van en `data/calibration/poisson_tercios/` con nombres que NO calzan con `poisson_params_*.json`:
`find_latest_calibration` (simulador de Poisson) sigue tomando `poisson_params_2026-08-23.json` y el sistema del
Sprint 6 se reproduce igual. Cada archivo tiene el formato de la 2.1.3, así que se usa con
`PoissonLOBSimulator(..., calibration_path=...)`.

    python -m src.envs.calibration_poisson_tercios
"""
from __future__ import annotations

import argparse
import json
import platform
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from src.envs import calibration_poisson as cp
from src.config import market_params as mp

SNAPSHOTS: Tuple[str, ...] = ("2026-08-23", "2026-09-27", "2026-11-11")
TICKERS: Tuple[str, ...] = ("FALABELLA", "COPEC", "ECL")
TERCIOS: Tuple[str, ...] = ("bajo", "medio", "alto")
OUT_DIR = cp.DEFAULT_CALIBRATION_DIR / "poisson_tercios"
N_BOOT = 2000
SEMILLA_BOOT = 0
NIVEL = 0.95


# ---------------------------------------------------------------------------
# Días: unión de snapshots
# ---------------------------------------------------------------------------

def combinar_snapshots(frames: Mapping[str, pd.DataFrame]) -> Tuple[pd.DataFrame, Dict[date, str]]:
    """Une los días de varios snapshots (clave: fecha 'YYYY-MM-DD' de la descarga; valor: salida de
    `load_clean_data`). Cada día sale de la descarga más reciente que lo tiene; el día de cada descarga se excluye."""
    origen: Dict[date, str] = {}
    for snap in sorted(frames):
        dia_descarga = date.fromisoformat(snap)
        for d in frames[snap]["day"].unique():
            if d != dia_descarga:
                origen[d] = snap
    partes = [df[df["day"].map(origen).eq(snap)] for snap, df in sorted(frames.items())]
    out = pd.concat(partes, ignore_index=True).sort_values("ts").reset_index(drop=True)
    return out, origen


def cargar_union(ticker: str, snapshots: Sequence[str] = SNAPSHOTS,
                 data_dir: Path = cp.DEFAULT_DATA_DIR) -> Tuple[pd.DataFrame, Dict[date, str]]:
    frames = {s: cp.load_clean_data(ticker, data_dir=data_dir, snapshot=s) for s in snapshots}
    return combinar_snapshots(frames)


def preparar(df: pd.DataFrame, exclude_closing_auction: bool = cp.DEFAULT_EXCLUDE_CLOSING_AUCTION,
             volume_winsor_q: float = cp.DEFAULT_VOLUME_WINSOR_Q,
             order_notional_clp: float = cp.DEFAULT_ORDER_NOTIONAL_CLP) -> Tuple[pd.DataFrame, float, float]:
    """Mismo preprocesamiento que `calibrate_ticker` de la 2.1.3, sobre la unión de días."""
    median_price = float(df.loc[~df["is_imputed"], "close"].median())
    avg_order_size = float(mp.avg_order_size_from_price(median_price, order_notional_clp))
    if exclude_closing_auction:
        df = df[~df["is_auction"]]
    df = df.copy()
    cap = float(df.loc[~df["is_imputed"], "volume"].quantile(volume_winsor_q))
    df["volume_w"] = df["volume"].clip(upper=cap)
    return df, avg_order_size, cap


# ---------------------------------------------------------------------------
# Tercios
# ---------------------------------------------------------------------------

def volumen_diario(df: pd.DataFrame) -> pd.Series:
    obs = df[~df["is_imputed"]]
    return obs.groupby("day")["volume_w"].sum().reindex(sorted(df["day"].unique()), fill_value=0.0)


def asignar_tercios(volumen: pd.Series) -> Dict[date, str]:
    """Ordena los días por volumen (empates por fecha) y los reparte en tres grupos lo más parejos posible."""
    orden = sorted(volumen.index, key=lambda d: (float(volumen[d]), d))
    grupos = np.array_split(np.arange(len(orden)), len(TERCIOS))
    return {orden[i]: TERCIOS[k] for k, g in enumerate(grupos) for i in g}


# ---------------------------------------------------------------------------
# Bootstrap por días (alto − bajo)
# ---------------------------------------------------------------------------

def agregados_diarios(df: pd.DataFrame) -> pd.DataFrame:
    """Por día y tramo: volumen observado, velas observadas y momentos de los retornos (para remuestrear días)."""
    obs = df[~df["is_imputed"]]
    vol = obs.groupby(["day", "tramo"]).agg(vol=("volume_w", "sum"), n_obs=("volume_w", "size"))
    r = df.dropna(subset=["ret"])
    mom = r.groupby(["day", "tramo"])["ret"].agg(n_ret="size", s1="sum", s2=lambda x: float((x * x).sum()))
    return vol.join(mom, how="outer").fillna(0.0).reset_index()


def _lambda_total(g: pd.DataFrame, avg_order_size: float) -> float:
    pasos = g["n_obs"].sum() * cp.STEPS_PER_BAR
    return float(g["vol"].sum() / pasos / avg_order_size) if pasos else float("nan")


def _std(g: pd.DataFrame) -> float:
    n = g["n_ret"].sum()
    if n < 2:
        return float("nan")
    m = g["s1"].sum() / n
    return float(np.sqrt(max(g["s2"].sum() / n - m * m, 0.0)))   # ddof = 0, igual que obs_return_std


def bootstrap_alto_bajo(agg: pd.DataFrame, tercios: Mapping[date, str], avg_order_size: float,
                        n_boot: int = N_BOOT, semilla: int = SEMILLA_BOOT, nivel: float = NIVEL) -> Dict[str, Dict]:
    """IC por bootstrap de días (percentil) de alto − bajo, por tramo, para λ total y la desviación de retornos."""
    rng = np.random.default_rng(semilla)
    q = [(1 - nivel) / 2 * 100, (1 + nivel) / 2 * 100]
    out: Dict[str, Dict] = {}
    for tramo in cp.TRAMO_NAMES:
        a = agg[agg["tramo"] == tramo]
        por = {t: {d: g for d, g in a.groupby("day") if tercios.get(d) == t} for t in ("bajo", "alto")}
        dias = {t: list(v) for t, v in por.items()}
        res = {}
        for nombre, f in (("lambda_total", lambda g: _lambda_total(g, avg_order_size)), ("ret_std", _std)):
            punto = {t: f(pd.concat(por[t].values())) for t in dias}
            difs = []
            for _ in range(n_boot):
                v = {t: f(pd.concat([por[t][dias[t][i]] for i in rng.integers(0, len(dias[t]), len(dias[t]))]))
                     for t in dias}
                difs.append(v["alto"] - v["bajo"])
            lo, hi = np.nanpercentile(difs, q)
            res[nombre] = {"bajo": punto["bajo"], "alto": punto["alto"], "alto_menos_bajo": punto["alto"] - punto["bajo"],
                           "ic_bajo": float(lo), "ic_alto": float(hi), "excluye_cero": bool(lo > 0 or hi < 0)}
        out[tramo] = res
    return out


# ---------------------------------------------------------------------------
# Calibración por tercio
# ---------------------------------------------------------------------------

def calibrar_ticker(ticker: str, snapshots: Sequence[str] = SNAPSHOTS, data_dir: Path = cp.DEFAULT_DATA_DIR,
                    seed: int = cp.DEFAULT_SEED, run_mle: bool = True, n_boot: int = N_BOOT) -> Dict:
    name = cp.normalize_ticker(ticker)
    union, origen = cargar_union(name, snapshots, data_dir)
    df, avg_order_size, cap = preparar(union)
    vol = volumen_diario(df)
    tercios = asignar_tercios(vol)
    por_tercio = {}
    for t in TERCIOS:
        dias_t = sorted(d for d, k in tercios.items() if k == t)
        sub = df[df["day"].isin(dias_t)]
        por_tercio[t] = {
            "dias": [d.isoformat() for d in dias_t],
            "volumen_diario": {"min": float(vol[dias_t].min()), "mediana": float(vol[dias_t].median()),
                               "max": float(vol[dias_t].max())},
            "tramos": {tramo: cp.calibrate_tramo(sub[sub["tramo"] == tramo], name, tramo, avg_order_size,
                                                 seed=seed, run_mle=run_mle)
                       for tramo in cp.TRAMO_NAMES},
        }
    return {"ticker": name, "avg_order_size": avg_order_size, "volume_cap": cap, "n_dias": len(tercios),
            "origen_dias": {s: sum(v == s for v in origen.values()) for s in snapshots},
            "tercios": por_tercio,
            "alto_menos_bajo": bootstrap_alto_bajo(agregados_diarios(df), tercios, avg_order_size, n_boot=n_boot)}


def metadata(snapshots: Sequence[str], tercio: Optional[str] = None) -> Dict:
    return {
        "tarea": "2.1.3 (extensión) - Calibración del modelo de Poisson por tercios de actividad diaria",
        "autor": "Benjamin Farias (BF), con apoyo de Claude Code; método de estimación de la 2.1.3",
        "fecha_generacion": datetime.now(timezone.utc).isoformat(),
        "fuente": "yfinance, velas OHLCV de 5 min",
        "snapshots": list(snapshots),
        "tercio": tercio,
        "tramos": {name: [start, end] for name, start, end in cp.TRAMOS},
        "timezone": cp.SANTIAGO_TZ,
        "supuestos": [
            "Unión de días de los snapshots; un día repetido se toma de la descarga más reciente.",
            "Se excluye el día de cada descarga (sus velas todavía no son definitivas).",
            "Tercios por activo según el volumen del día completo (velas observadas, sin subasta de cierre, tope p99); "
            "la clase del día es la misma en los tres tramos.",
            "avg_order_size y el tope p99 se calculan sobre la unión de días (no por tercio), así λ es comparable "
            "entre tercios.",
            "Estimación por tramo idéntica a la 2.1.3 (calibrate_tramo: empírico directo, MLE proxy solo si mejora KS).",
            "Nombre fuera del patrón poisson_params_*.json a propósito: no reemplaza a la calibración oficial.",
        ],
        "n_boot": N_BOOT, "semilla_boot": SEMILLA_BOOT, "nivel": NIVEL,
        "python": platform.python_version(),
    }


def escribir(resultados: Sequence[Dict], snapshots: Sequence[str], out_dir: Path = OUT_DIR) -> List[Path]:
    """Un JSON por tercio con el formato de la 2.1.3 (params[ticker][tramo], tickers_info) y un resumen."""
    out_dir.mkdir(parents=True, exist_ok=True)
    rutas = []
    for t in TERCIOS:
        payload = {"metadata": metadata(snapshots, t),
                   "params": {r["ticker"]: r["tercios"][t]["tramos"] for r in resultados},
                   "tickers_info": {r["ticker"]: {"avg_order_size": r["avg_order_size"], "volume_cap": r["volume_cap"],
                                                  "n_dias": len(r["tercios"][t]["dias"]),
                                                  "volumen_diario": r["tercios"][t]["volumen_diario"]}
                                    for r in resultados}}
        rutas.append(_dump(payload, out_dir / f"poisson_tercio_{t}.json"))
    resumen = {"metadata": metadata(snapshots),
               "por_ticker": {r["ticker"]: {
                   "n_dias": r["n_dias"], "origen_dias": r["origen_dias"], "avg_order_size": r["avg_order_size"],
                   "dias": {t: r["tercios"][t]["dias"] for t in TERCIOS},
                   "volumen_diario": {t: r["tercios"][t]["volumen_diario"] for t in TERCIOS},
                   "parametros": {t: {tramo: {k: r["tercios"][t]["tramos"][tramo].get(k)
                                              for k in ("lambda_plus", "lambda_minus", "theta", "obs_return_std",
                                                        "ks_d_ratio", "method", "n_obs")}
                                      for tramo in cp.TRAMO_NAMES} for t in TERCIOS},
                   "alto_menos_bajo": r["alto_menos_bajo"]} for r in resultados}}
    rutas.append(_dump(resumen, out_dir / "resumen_tercios.json"))
    return rutas


def _dump(payload: Dict, ruta: Path) -> Path:
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(cp._json_safe(payload), fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return ruta


def main(argv: Optional[Iterable[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--snapshots", nargs="+", default=list(SNAPSHOTS))
    ap.add_argument("--tickers", nargs="+", default=list(TICKERS))
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    ap.add_argument("--n-boot", type=int, default=N_BOOT)
    args = ap.parse_args(list(argv) if argv is not None else None)
    resultados = []
    for t in args.tickers:
        r = calibrar_ticker(t, args.snapshots, n_boot=args.n_boot)
        resultados.append(r)
        print(f"[{r['ticker']}] {r['n_dias']} días {r['origen_dias']} | orden {r['avg_order_size']:.0f} acc")
        for tercio in TERCIOS:
            p = r["tercios"][tercio]["tramos"]
            print(f"   {tercio:5s} ({len(r['tercios'][tercio]['dias'])} días): " + " | ".join(
                f"{tr}: λ={p[tr]['lambda_plus'] + p[tr]['lambda_minus']:.2f} σ={p[tr]['obs_return_std'] * 1e4:.1f}bps "
                f"KS/D={p[tr].get('ks_d_ratio', float('nan')):.2f}" for tr in cp.TRAMO_NAMES))
    for ruta in escribir(resultados, args.snapshots, args.out_dir):
        print("JSON ->", ruta)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
