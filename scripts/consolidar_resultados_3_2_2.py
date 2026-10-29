"""Consolidación de las corridas de evaluación (tarea 3.2.2).

BORRADOR de PS para BF (29 oct 2026), con apoyo de Claude Code.

Lee los JSON del evaluador del sistema (`scripts/colab/evaluar_sistema_ps.py`) y de los benchmarks
(`scripts/colab/benchmarks_meta_ordenes_ps.py`), cualquiera sea el escenario de liquidez y el tamaño, y arma:

- la tabla maestra: una fila por escenario y tamaño, con el costo medio de cada estrategia, la diferencia del sistema
  frente a TWAP y VWAP (en bps, pareada por orden y semilla, con IC 95 %, y en %), y el ranking;
- estadísticas agregadas por estrategia: media, mediana, peor y mejor corrida, y cumplimiento;
- exportación a CSV, Markdown y LaTeX.

El costo es el slippage contra el precio de llegada (`slippage_bps`). Con `--penalizacion-bps P` se usa el costo
ajustado por lo no ejecutado: slippage × cumplimiento + P × (1 − cumplimiento), para que una orden incompleta no
parezca barata.

    python scripts/consolidar_resultados_3_2_2.py --entradas <carpeta_con_json> --sistema PPO --out-dir data/analysis/3_2_2
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

REFERENCIAS = ("TWAP", "VWAP")


def leer_corridas(rutas: Sequence[Path]) -> pd.DataFrame:
    """Una fila por corrida válida (sin las que terminaron en error)."""
    filas = []
    for ruta in rutas:
        with open(ruta, "r", encoding="utf-8") as f:
            data = json.load(f)
        for c in data.get("corridas", {}).values():
            if "error" in c or c.get("slippage_bps") is None:
                continue
            filas.append({"archivo": ruta.name, "orden": c["orden"], "estrategia": c["estrategia"], "seed": int(c["seed"]),
                          "escenario": c.get("escenario", "media"), "factor_tamano": float(c.get("factor_tamano", 1.0)),
                          "ticker": c.get("ticker"), "tramo_inicio": c.get("tramo_inicio"),
                          "slippage_bps": float(c["slippage_bps"]), "cumplimiento": float(c.get("execution_rate", 1.0))})
    return pd.DataFrame(filas)


def costo(df: pd.DataFrame, penalizacion_bps: Optional[float]) -> pd.Series:
    if penalizacion_bps is None:
        return df["slippage_bps"]
    return df["slippage_bps"] * df["cumplimiento"] + penalizacion_bps * (1.0 - df["cumplimiento"])


def ic_bootstrap(d: np.ndarray, n_boot: int = 3000, seed: int = 0):
    if len(d) < 2:
        return float("nan"), float("nan")
    medias = np.random.default_rng(seed).choice(d, size=(n_boot, len(d)), replace=True).mean(axis=1)
    return float(np.percentile(medias, 2.5)), float(np.percentile(medias, 97.5))


def tabla_maestra(df: pd.DataFrame, sistema: str) -> pd.DataFrame:
    filas = []
    for (esc, tam), g in df.groupby(["escenario", "factor_tamano"], sort=True):
        piv = g.pivot_table(index=["orden", "seed"], columns="estrategia", values="costo", aggfunc="mean")
        fila = {"escenario": esc, "factor_tamano": tam, "n_pares": 0}
        medias = {e: float(piv[e].mean()) for e in piv.columns}
        for e, m in medias.items():
            fila[f"IS_{e}"] = m
        if sistema in piv.columns:
            for ref in REFERENCIAS:
                if ref not in piv.columns:
                    continue
                par = piv[[sistema, ref]].dropna()
                d = (par[sistema] - par[ref]).to_numpy()
                lo, hi = ic_bootstrap(d)
                fila["n_pares"] = max(fila["n_pares"], len(d))
                fila[f"dif_vs_{ref}_bps"] = float(d.mean()) if len(d) else float("nan")
                fila[f"dif_vs_{ref}_ic"] = f"[{lo:.2f}; {hi:.2f}]"
                base = float(par[ref].mean())
                fila[f"dif_vs_{ref}_pct"] = 100.0 * float(d.mean()) / abs(base) if len(d) and base else float("nan")
        fila["ranking"] = " < ".join(sorted(medias, key=medias.get))
        filas.append(fila)
    return pd.DataFrame(filas)


def agregados(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("estrategia")
    return pd.DataFrame({"n": g["costo"].size(), "media": g["costo"].mean(), "mediana": g["costo"].median(),
                         "peor": g["costo"].max(), "mejor": g["costo"].min(),
                         "cumplimiento_medio": g["cumplimiento"].mean()}).reset_index()


def a_latex(t: pd.DataFrame) -> str:
    cols = list(t.columns)
    lineas = ["\\begin{tabular}{" + "l" * len(cols) + "}", "\\hline",
              " & ".join(c.replace("_", "\\_") for c in cols) + " \\\\", "\\hline"]
    for _, r in t.iterrows():
        vals = [f"{v:.2f}" if isinstance(v, float) else str(v) for v in r]
        lineas.append(" & ".join(v.replace("_", "\\_").replace("%", "\\%") for v in vals) + " \\\\")
    lineas += ["\\hline", "\\end{tabular}"]
    return "\n".join(lineas) + "\n"


def a_markdown(t: pd.DataFrame) -> str:
    cols = list(t.columns)
    lineas = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in t.iterrows():
        lineas.append("| " + " | ".join(f"{v:.2f}" if isinstance(v, float) else str(v) for v in r) + " |")
    return "\n".join(lineas) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> Dict[str, Path]:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--entradas", nargs="+", required=True, help="archivos JSON o carpetas con JSON")
    ap.add_argument("--sistema", default="PPO", help="nombre de la estrategia del sistema en los JSON")
    ap.add_argument("--penalizacion-bps", type=float, default=None)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args(argv)

    rutas: List[Path] = []
    for e in args.entradas:
        p = Path(e)
        rutas += sorted(p.glob("*.json")) if p.is_dir() else [p]
    df = leer_corridas(rutas)
    if df.empty:
        sys.exit("No hay corridas válidas en las entradas.")
    df["costo"] = costo(df, args.penalizacion_bps)
    maestra, agg = tabla_maestra(df, args.sistema), agregados(df)

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    salidas = {"corridas_csv": out / "corridas.csv", "maestra_csv": out / "tabla_maestra.csv",
               "agregados_csv": out / "agregados.csv", "md": out / "tabla_maestra.md", "tex": out / "tabla_maestra.tex"}
    df.to_csv(salidas["corridas_csv"], index=False)
    maestra.to_csv(salidas["maestra_csv"], index=False)
    agg.to_csv(salidas["agregados_csv"], index=False)
    criterio = ("slippage contra el precio de llegada" if args.penalizacion_bps is None
                else f"costo ajustado con {args.penalizacion_bps:g} bps por acción no ejecutada")
    salidas["md"].write_text(
        f"# Tabla maestra 3.2.2\n\nCosto: {criterio}. Sistema: `{args.sistema}`. Diferencias pareadas por orden y semilla; "
        f"IC 95 % por bootstrap. Corridas leídas: {len(df)} de {len(rutas)} archivos.\n\n## Por escenario y tamaño\n\n"
        + a_markdown(maestra) + "\n## Por estrategia\n\n" + a_markdown(agg), encoding="utf-8")
    salidas["tex"].write_text(a_latex(maestra), encoding="utf-8")
    print(maestra.to_string(index=False))
    return salidas


if __name__ == "__main__":
    main()
