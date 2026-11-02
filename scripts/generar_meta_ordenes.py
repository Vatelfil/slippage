"""Generador de las 10 meta-ordenes oficiales (tarea 2.3.3).

Borrador de PS con apoyo de Claude Code; revisado, completado y aprobado por BF con apoyo de Claude Code
(responsable de la 2.3.3). Decision D1 de BF (22 oct 2026): 10 % del volumen del dia simulado para las
ordenes de apertura y media jornada y 5 % para las de cierre (ver docs/meta_ordenes_2.3.3.md).

    python scripts/generar_meta_ordenes.py                      # version oficial -> data/meta_ordenes/meta_ordenes_v2.json
    python scripts/generar_meta_ordenes.py --cantidad 100000 --salida <ruta>   # tamanos de la v1 (historica)
    python scripts/generar_meta_ordenes.py --pct-dia 0.10 --salida <ruta>      # otra variante (sensibilidad)

Es determinista: no usa azar. Toma de los archivos del repositorio
  - `data/calibration/rmsc04_ipsa_<ACTIVO>_2026-08-23.json`: precio de referencia (`r_bar`) y unidad de cuenta.
  - `data/colab_resultados/validacion_2_2_5_despues_<ACTIVO>_2026-08-23.json`: volumen simulado por tramo
    (mediana de 30 jornadas) para saber que fraccion del mercado representa cada orden.
y, si esta en local, del snapshot de mercado `data/processed/clean_5m_2026-08-23/<ACTIVO>.parquet` (no se
versiona) el ADV real y el precio real, con `src.experiments.meta_orders.load_daily_volume`. Sin el parquet
esos campos quedan en null. Las 10 ordenes se reservan para evaluar (T4 y despues): el entrenamiento (T5)
NO las usa.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.envs.calibrate_rmsc04_ipsa import load_unidades_por_clp  # noqa: E402

SNAPSHOT = "2026-08-23"
TRAMOS = ("apertura", "media_jornada", "cierre")
# Hora de inicio de cada tramo segun el orquestador (src/analysis/benchmarks.periodo_inicio): la media jornada
# arranca a las 11:00 (corte del Maestro), no a las 11:30 de la calibracion (discrepancia D5/P9).
HORA_INICIO = {"apertura": "09:30", "media_jornada": "11:00", "cierre": "14:00"}
CANTIDAD_V1 = 100_000           # D1, opcion A del plan: tamano de la v1 (historica, la de la corrida base de T4)
PCT_DIA_OFICIAL = 0.10          # D1 de BF: fraccion del dia simulado para apertura y media jornada
PCT_DIA_CIERRE_OFICIAL = 0.05   # D1 de BF: fraccion del dia simulado para las ordenes que parten en el cierre
SEMILLA_BASE = 9000             # distinta de calibracion (100-300), entrenamiento (1000s) y evaluacion (5000s)
SALIDA_OFICIAL = REPO_ROOT / "data/meta_ordenes/meta_ordenes_v2.json"

# Decision de BF (D2/T3): reparto activo x tramo. El plan pide FALABELLA 4, COPEC 3, ECL 3 y apertura 4,
# media jornada 3, cierre 3, sin repetir activo-tramo-semilla. Con la calibracion nueva de COPEC y ECL
# (volumen del dia de ~290-320 mil acciones), una orden de 100 mil que parte en el cierre seria el
# 96-104 % del volumen que queda, es decir, no ejecutable; por eso el cierre se asigna a FALABELLA
# y COPEC y ECL parten en apertura o media jornada. Se mantiene con la D1 final.
REPARTO = [
    ("FALABELLA", "apertura"),
    ("COPEC", "apertura"),
    ("COPEC", "apertura"),
    ("ECL", "apertura"),
    ("COPEC", "media_jornada"),
    ("ECL", "media_jornada"),
    ("ECL", "media_jornada"),
    ("FALABELLA", "cierre"),
    ("FALABELLA", "cierre"),
    ("FALABELLA", "cierre"),
]


def ruta_calibracion(ticker: str) -> Path:
    return REPO_ROOT / f"data/calibration/rmsc04_ipsa_{ticker}_{SNAPSHOT}.json"


def precio_referencia_clp(ticker: str) -> float:
    """Precio de llegada de la calibracion (r_bar de la apertura) en CLP por accion."""
    js = ruta_calibracion(ticker)
    with open(js, "r", encoding="utf-8-sig") as f:
        r_bar = json.load(f)["por_tramo"]["apertura"]["abides_kwargs"]["r_bar"]
    return round(float(r_bar) / load_unidades_por_clp(js), 2)


def huella_archivo(path: Path) -> Dict[str, str]:
    """sha256 y id de blob de git del contenido con fin de linea LF (el que guarda git). Se normaliza porque en
    Windows, con core.autocrlf, el archivo en disco puede tener CRLF y el sha256 de los bytes no seria portable.
    El blob se verifica con `git rev-parse <commit>:<ruta>`."""
    contenido = path.read_bytes().replace(b"\r\n", b"\n")
    blob = hashlib.sha1(b"blob %d\0" % len(contenido) + contenido).hexdigest()
    return {"sha256_lf": hashlib.sha256(contenido).hexdigest(), "git_blob": blob}


def volumenes_simulados(ticker: str) -> Dict[str, float]:
    """Mediana (sobre las jornadas validadas) del volumen simulado por tramo y del dia completo, en acciones."""
    f = REPO_ROOT / f"data/colab_resultados/validacion_2_2_5_despues_{ticker}_{SNAPSHOT}.json"
    with open(f, "r", encoding="utf-8-sig") as fh:
        res = json.load(fh)["resultados"]["cierre"]["corridas"]
    filas = []
    for c in res.values():
        m = c.get("momentos", {})
        if all(m.get(t, {}).get("completo") for t in TRAMOS):
            filas.append({t: float(m[t]["volumen"]) for t in TRAMOS})
    if not filas:
        raise ValueError(f"{ticker}: no hay jornadas completas en {f.name}")
    dia = [sum(r.values()) for r in filas]
    # Volumen que queda desde el inicio de la orden hasta el cierre (aproximacion con los tramos de la calibracion).
    disp = {
        "apertura": dia,
        "media_jornada": [r["media_jornada"] + r["cierre"] for r in filas],
        "cierre": [r["cierre"] for r in filas],
    }
    out = {"dia": float(np.median(dia)), "n_jornadas": float(len(filas))}
    out.update({f"disp_{t}": float(np.median(v)) for t, v in disp.items()})
    return out


def generar(cantidad: Optional[int] = None, pct_dia: Optional[float] = None,
            pct_dia_cierre: Optional[float] = None, version: str = "v1") -> Dict:
    """Arma el diccionario con las 10 ordenes. `cantidad` fija el tamano; `pct_dia` lo calcula como
    fraccion del volumen del dia simulado de cada activo (redondeado a 100 acciones). `pct_dia_cierre` (solo con
    `pct_dia`) usa otra fraccion para las ordenes que parten en el cierre: en el cierre queda poco volumen y
    la misma fraccion pesa mucho mas sobre lo que queda (ver docs/benchmarks_2.3.4_PS.md)."""
    if cantidad is not None and pct_dia is not None:
        raise ValueError("usar `cantidad` o `pct_dia`, no los dos")
    if pct_dia_cierre is not None and pct_dia is None:
        raise ValueError("`pct_dia_cierre` solo se usa junto con `pct_dia`")
    cantidad_fija = CANTIDAD_POR_DEFECTO if (cantidad is None and pct_dia is None) else cantidad
    cache_vol: Dict[str, Dict[str, float]] = {}
    ordenes: List[Dict] = []
    for i, (ticker, tramo) in enumerate(REPARTO, start=1):
        if ticker not in cache_vol:
            cache_vol[ticker] = volumenes_simulados(ticker)
        v = cache_vol[ticker]
        pct = pct_dia_cierre if (tramo == "cierre" and pct_dia_cierre is not None) else pct_dia
        q = int(cantidad_fija) if cantidad_fija is not None else int(round(pct * v["dia"], -2))
        ordenes.append({
            "id": f"MO-{i:02d}",
            "ticker": ticker,
            "fecha": SNAPSHOT,
            "tramo_inicio": tramo,
            "hora_inicio": HORA_INICIO[tramo],
            "cantidad": q,
            "p_referencia": precio_referencia_clp(ticker),
            "p_referencia_real": real["precio_referencia_real"] if real else None,
            "semilla": SEMILLA_BASE + 10 * i,
            "volumen_dia_simulado": round(v["dia"]),
            "volumen_disponible_desde_inicio": round(v[f"disp_{tramo}"]),
            "pct_volumen_dia": round(100.0 * q / v["dia"], 1),
            "pct_volumen_disponible": round(100.0 * q / v[f"disp_{tramo}"], 1),
            "adv_real_acciones": round(real["adv_acciones"]) if real else None,
            "pct_adv_real": round(100.0 * q / real["adv_acciones"], 2) if real else None,
        })
    tickers = sorted({t for t, _ in REPARTO})
    return {
        "version": version,
        "estado": "BORRADOR de PS con apoyo de Claude Code, pendiente de decision y revision de BF (2.3.3)",
        "snapshot": SNAPSHOT,
        "generacion": {
            "comando": comando(cantidad, pct_dia, pct_dia_cierre),
            "commit": commit,
            "calibracion": {t: {"archivo": ruta_calibracion(t).relative_to(REPO_ROOT).as_posix(),
                                **huella_archivo(ruta_calibracion(t))} for t in tickers},
            "adv_real": {"fuente": f"data/processed/clean_5m_{SNAPSHOT}/<ACTIVO>.parquet (no versionado)",
                         "activos_con_dato": sorted(reales)},
        },
        "criterios": {
            "tamano": (f"{cantidad_fija} acciones por orden (D1, opcion A del plan)" if cantidad_fija is not None
                       else f"{pct_dia:.0%} del volumen del dia simulado de cada activo (D1, opcion B)"
                       + (f", salvo las ordenes que parten en el cierre: {pct_dia_cierre:.0%}" if pct_dia_cierre is not None else "")),
            "reparto": "FALABELLA 4, COPEC 3, ECL 3; apertura 4, media jornada 3, cierre 3 (DECISION BF)",
            "semillas": f"semilla = {SEMILLA_BASE} + 10 * indice; el runner suma la semilla de la corrida (1, 2, ...)",
            "volumen": "mediana de 30 jornadas simuladas con la calibracion vigente de cada activo "
                       "(data/colab_resultados/validacion_2_2_5_despues_*.json)",
            "p_referencia": "r_bar de la calibracion (lo que uso T4); p_referencia_real = mediana de close_raw "
                            "no imputado del snapshot, solo informativo",
            "adv_real": "mediana diaria de volume_raw sin la vela de subasta 15:55 (src/experiments/meta_orders.py)",
            "uso": "las 10 ordenes se reservan para evaluar; el entrenamiento (2.3.5) no las usa",
        },
        "meta_ordenes": ordenes,
    }


def commit_actual() -> Optional[str]:
    """Commit de HEAD; con sufijo `-modificado` si este script tiene cambios sin commitear (entonces el commit
    no basta para reproducir la generacion)."""
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True)
        s = subprocess.run(["git", "status", "--porcelain", "--", "scripts/generar_meta_ordenes.py"],
                           cwd=REPO_ROOT, capture_output=True, text=True)
    except OSError:
        return None
    if r.returncode != 0 or not r.stdout.strip():
        return None
    return r.stdout.strip() + ("-modificado" if s.stdout.strip() else "")


def main(argv: Optional[List[str]] = None) -> Path:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--cantidad", type=int, default=None, help="acciones por orden (la v1 historica usaba 100000)")
    ap.add_argument("--pct-dia", type=float, default=None, help="fraccion del volumen del dia (ej. 0.10)")
    ap.add_argument("--pct-dia-cierre", type=float, default=None,
                    help="con --pct-dia: otra fraccion para las ordenes que parten en el cierre (ej. 0.05)")
    ap.add_argument("--version", default="v1", help="etiqueta de version del archivo (ej. v2-candidata)")
    ap.add_argument("--salida", default=str(REPO_ROOT / "data/meta_ordenes/meta_ordenes_v1.json"))
    args = ap.parse_args(argv)
    data = generar(cantidad=args.cantidad, pct_dia=args.pct_dia, pct_dia_cierre=args.pct_dia_cierre, version=args.version)
    out = Path(args.salida)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(data['meta_ordenes'])} ordenes ({data['version']}) -> {out}")
    for f in faltan:
        print(f"  AVISO: falta {f}; adv_real_acciones, pct_adv_real y p_referencia_real quedan en null")
    for o in data["meta_ordenes"]:
        adv = "   s/d" if o["pct_adv_real"] is None else f"{o['pct_adv_real']:5.2f}"
        print(f"  {o['id']} {o['ticker']:9s} {o['tramo_inicio']:13s} {o['cantidad']:>7d} acc  "
              f"{o['pct_volumen_dia']:5.1f} % del dia  {o['pct_volumen_disponible']:5.1f} % de lo que queda  "
              f"{adv} % del ADV real")
    return out


if __name__ == "__main__":
    main()
