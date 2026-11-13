"""Consolidación de las corridas de evaluación (tarea 3.2.2).

Borrador de PS (29 oct 2026); revisado y ampliado por BF como dueño de la 3.2.2 (12 nov 2026), con apoyo de Claude Code.

Lee los JSON del evaluador del sistema (`scripts/colab/evaluar_sistema_ps.py`) y de los benchmarks
(`scripts/colab/benchmarks_meta_ordenes_ps.py`), cualquiera sea el escenario de liquidez y el tamaño, y arma:

- la tabla maestra: una fila por escenario y tamaño, con el costo medio de cada estrategia, la diferencia del sistema
  frente a TWAP y VWAP (en bps, pareada por orden y semilla, con IC 95 %, y en %), y el ranking;
- estadísticas agregadas por estrategia: media, mediana, peor y mejor corrida, y cumplimiento;
- exportación a CSV, Markdown y LaTeX.

El costo es el slippage contra el precio de llegada (`slippage_bps`), tal como lo calcula `evaluate_episode`
(`src/analysis/execution_metrics.py`): (precio medio ejecutado − precio de llegada) / precio de llegada × 10.000. Con
`--penalizacion-bps P` se usa el costo ajustado por lo no ejecutado: slippage × cumplimiento + P × (1 − cumplimiento),
para que una orden incompleta no parezca barata.

Además (BF, 12 nov), siempre que hay corridas de tamaño 1:

- `calidad.json` / `calidad.md`: corridas leídas contra las esperadas por estrategia y bloque, errores, duplicados,
  pareo y corridas bajo el umbral de cumplimiento (por defecto 95 %);
- `tabla_90.*`: una fila por profundidad del market maker (tamaño 1), la fila global (las tres juntas, pareadas por
  escenario, orden y semilla) y una fila de robustez sin los pares con alguna corrida bajo el umbral;
- `tabla_tamanos.*`: el eje de tamaño (0,5 / 1 / 1,5) de un escenario, si hay más de un factor (diseño en estrella,
  desviación 12). Va aparte para que la tabla global no cuente dos veces la profundidad ×1;
- `por_tramo.csv` y `por_activo.csv`: la diferencia del sistema por tramo de inicio y por activo (tamaño 1);
- con `--ajustado-bps P`, las mismas tablas también con el costo ajustado (sufijo `_ajustado`);
- `informe_3_2_2.md`: todo lo anterior en un solo documento.

Criterios de la 3.2.2, fijados por BF el 12 nov antes de consolidar las 90: costo crudo y ajustado (+30 bps); las
corridas bajo el 95 % se mantienen, se marcan y se informa una fila sin esos pares; diferencia % = cociente de medias;
tamaños en tabla aparte.

    python scripts/consolidar_resultados_3_2_2.py --entradas <carpeta_con_json> --sistema PPO --out-dir data/analysis/3_2_2
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

REFERENCIAS = ("TWAP", "VWAP")
N_ESPERADO = 30                 # 10 meta-órdenes × 3 semillas por estrategia, escenario y tamaño
UMBRAL_CUMPLIMIENTO = 0.95      # requisito del plan de análisis de la 3.2.3


def leer_corridas(rutas: Sequence[Path]) -> pd.DataFrame:
    """Una fila por corrida válida (sin las que terminaron en error)."""
    filas = []
    for ruta in rutas:
        with open(ruta, "r", encoding="utf-8") as f:
            data = json.load(f)
        factor_liq = (data.get("firma") or {}).get("factor_liquidez")
        for c in data.get("corridas", {}).values():
            if "error" in c or c.get("slippage_bps") is None:
                continue
            filas.append({"archivo": ruta.name, "orden": c["orden"], "estrategia": c["estrategia"], "seed": int(c["seed"]),
                          "escenario": c.get("escenario", "media"), "factor_tamano": float(c.get("factor_tamano", 1.0)),
                          "factor_liquidez": float(factor_liq) if factor_liq is not None else float("nan"),
                          "ticker": c.get("ticker"), "tramo_inicio": c.get("tramo_inicio"),
                          "slippage_bps": float(c["slippage_bps"]), "cumplimiento": float(c.get("execution_rate", 1.0))})
    return pd.DataFrame(filas)


def leer_errores(rutas: Sequence[Path]) -> List[Dict]:
    """Corridas que terminaron en error (no entran a las tablas, pero sí al chequeo de calidad)."""
    errores = []
    for ruta in rutas:
        with open(ruta, "r", encoding="utf-8") as f:
            data = json.load(f)
        for c in data.get("corridas", {}).values():
            if "error" in c or c.get("slippage_bps") is None:
                errores.append({"archivo": ruta.name, "orden": c.get("orden"), "estrategia": c.get("estrategia"),
                                "seed": c.get("seed"), "error": str(c.get("error", "sin slippage_bps"))[:120]})
    return errores


def costo(df: pd.DataFrame, penalizacion_bps: Optional[float]) -> pd.Series:
    if penalizacion_bps is None:
        return df["slippage_bps"]
    return df["slippage_bps"] * df["cumplimiento"] + penalizacion_bps * (1.0 - df["cumplimiento"])


def ic_bootstrap(d: np.ndarray, n_boot: int = 3000, seed: int = 0):
    if len(d) < 2:
        return float("nan"), float("nan")
    medias = np.random.default_rng(seed).choice(d, size=(n_boot, len(d)), replace=True).mean(axis=1)
    return float(np.percentile(medias, 2.5)), float(np.percentile(medias, 97.5))


def _pruebas(d: np.ndarray):
    """p-valores pareados (Wilcoxon y t de Student) de la diferencia sistema − referencia; NaN si hay menos de 3 pares."""
    d = d[np.isfinite(d)]
    if len(d) < 3 or np.allclose(d, 0):
        return float("nan"), float("nan")
    from scipy.stats import ttest_1samp, wilcoxon
    return float(wilcoxon(d).pvalue), float(ttest_1samp(d, 0.0).pvalue)


def grafico_cajas(df: pd.DataFrame, ruta: Path, criterio: str) -> None:
    """Cajas del costo por estrategia (todas las corridas), para la 3.1.3."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    estrategias = sorted(df["estrategia"].unique())
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.boxplot([df.loc[df["estrategia"] == e, "costo"].to_numpy() for e in estrategias], showmeans=True)
    ax.set_xticks(range(1, len(estrategias) + 1))
    ax.set_xticklabels(estrategias, rotation=15, fontsize=8)
    ax.set_ylabel(f"Costo (bps; {criterio})")
    ax.axhline(0, color="grey", lw=0.6)
    ax.set_title("Costo por corrida y estrategia (triángulo: media)")
    fig.tight_layout()
    fig.savefig(ruta, dpi=130)
    plt.close(fig)


def _fila_comparacion(piv: pd.DataFrame, sistema: str) -> Dict:
    """Costo medio por estrategia, diferencia pareada del sistema frente a cada referencia y ranking, sobre una tabla
    pivote (una fila por día pareado, una columna por estrategia)."""
    fila: Dict = {"n_pares": 0}
    medias = {e: float(piv[e].mean()) for e in piv.columns}
    for e, m in medias.items():
        fila[f"IS_{e}"] = m
    if sistema in piv.columns:
        fila[f"sd_{sistema}"] = float(piv[sistema].std(ddof=1)) if piv[sistema].count() > 1 else float("nan")
        for ref in REFERENCIAS:
            if ref not in piv.columns:
                continue
            par = piv[[sistema, ref]].dropna()
            d = (par[sistema] - par[ref]).to_numpy()
            lo, hi = ic_bootstrap(d)
            fila["n_pares"] = max(fila["n_pares"], len(d))
            fila[f"dif_vs_{ref}_bps"] = float(d.mean()) if len(d) else float("nan")
            fila[f"dif_vs_{ref}_ic"] = f"[{lo:.2f}; {hi:.2f}]"
            fila[f"p_wilcoxon_vs_{ref}"], fila[f"p_ttest_vs_{ref}"] = _pruebas(d)
            base = float(par[ref].mean())
            fila[f"dif_vs_{ref}_pct"] = 100.0 * float(d.mean()) / abs(base) if len(d) and base else float("nan")
    fila["ranking"] = " < ".join(sorted(medias, key=medias.get))
    return fila


def tabla_maestra(df: pd.DataFrame, sistema: str) -> pd.DataFrame:
    filas = []
    for (esc, tam), g in df.groupby(["escenario", "factor_tamano"], sort=True):
        piv = g.pivot_table(index=["orden", "seed"], columns="estrategia", values="costo", aggfunc="mean")
        filas.append({"escenario": esc, "factor_tamano": tam, **_fila_comparacion(piv, sistema)})
    return pd.DataFrame(filas)


def base_global(df: pd.DataFrame) -> Tuple[pd.DataFrame, str]:
    """Corridas para los agregados y las cajas globales. Si se leen varios tamaños y está el 1, solo el tamaño 1
    (criterio 4 de la 3.2.2: el eje de tamaño va aparte); si no, todas, como en los cuadernos."""
    es_1 = np.isclose(df["factor_tamano"], 1.0)
    if df["factor_tamano"].nunique() > 1 and es_1.any():
        return df[es_1], " (solo tamaño 1; los otros tamaños van en tabla_tamanos)"
    return df, ""


def agregados(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("estrategia")
    return pd.DataFrame({"n": g["costo"].size(), "media": g["costo"].mean(), "mediana": g["costo"].median(),
                         "peor": g["costo"].max(), "mejor": g["costo"].min(),
                         "cumplimiento_medio": g["cumplimiento"].mean()}).reset_index()


# ---------------------------------------------------------------------------
# Ampliación de BF (12 nov): calidad, tabla de las 90, tamaños y cortes
# ---------------------------------------------------------------------------

def etiqueta_profundidad(factor: float) -> str:
    """«×4», «×1», «×0,25»: nombre del escenario desde el C-6c (desviación 10)."""
    if factor is None or not np.isfinite(factor):
        return ""
    return "×" + f"{factor:g}".replace(".", ",")


def _profundidad_por_escenario(df: pd.DataFrame) -> Dict[str, str]:
    return {esc: etiqueta_profundidad(float(g["factor_liquidez"].dropna().iloc[0]))
            if g["factor_liquidez"].notna().any() else "" for esc, g in df.groupby("escenario")}


def chequeo_calidad(df: pd.DataFrame, errores: Sequence[Dict], n_esperado: int = N_ESPERADO,
                    umbral: float = UMBRAL_CUMPLIMIENTO) -> Dict:
    """Por escenario y tamaño: corridas por estrategia contra las esperadas, duplicados, días pareados y corridas bajo el
    umbral de cumplimiento. REVISAR si falta algo, sobra algo o hay errores; las corridas bajo el umbral se listan pero
    no cambian el veredicto (criterio de la 3.2.2: se mantienen y se marcan)."""
    bloques, revisar = [], bool(errores)
    for (esc, tam), g in df.groupby(["escenario", "factor_tamano"], sort=True):
        claves = {e: set(zip(sg["orden"], sg["seed"])) for e, sg in g.groupby("estrategia")}
        pares = set.intersection(*claves.values()) if claves else set()
        dup = g[g.duplicated(["estrategia", "orden", "seed"], keep=False)]
        bajo = g[g["cumplimiento"] < umbral].sort_values(["orden", "seed", "estrategia"])
        n_por = {e: int(len(v)) for e, v in claves.items()}
        ok = (not dup.shape[0] and len(pares) == n_esperado and all(v == n_esperado for v in n_por.values()))
        revisar |= not ok
        bloques.append({
            "escenario": esc, "factor_tamano": float(tam), "corridas_por_estrategia": n_por, "esperadas": n_esperado,
            "dias_pareados": len(pares), "duplicados": int(dup.shape[0]),
            "cumplimiento_minimo": {e: float(sg["cumplimiento"].min()) for e, sg in g.groupby("estrategia")},
            "bajo_umbral": [{"orden": r.orden, "seed": int(r.seed), "estrategia": r.estrategia,
                             "cumplimiento": round(float(r.cumplimiento), 4)} for r in bajo.itertuples()],
            "ok": bool(ok)})
    return {"veredicto": "REVISAR" if revisar else "OK", "corridas_leidas": int(len(df)), "errores": list(errores),
            "umbral_cumplimiento": umbral, "bloques": bloques}


def tabla_90(df: pd.DataFrame, sistema: str, umbral: float = UMBRAL_CUMPLIMIENTO) -> pd.DataFrame:
    """Tamaño 1: una fila por profundidad del market maker, la global (escenarios juntos, pareada por escenario, orden y
    semilla) y la de robustez sin los días con alguna corrida bajo el umbral."""
    d1 = df[np.isclose(df["factor_tamano"], 1.0)]
    if d1.empty:
        return pd.DataFrame()
    prof = _profundidad_por_escenario(d1)
    filas = []
    for esc, g in d1.groupby("escenario", sort=True):
        piv = g.pivot_table(index=["orden", "seed"], columns="estrategia", values="costo", aggfunc="mean")
        filas.append({"bloque": esc, "profundidad_mm": prof.get(esc, ""), **_fila_comparacion(piv, sistema)})
    claves = ["escenario", "orden", "seed"]
    piv = d1.pivot_table(index=claves, columns="estrategia", values="costo", aggfunc="mean")
    filas.append({"bloque": "global", "profundidad_mm": "todas", **_fila_comparacion(piv, sistema)})
    malos = set(map(tuple, d1.loc[d1["cumplimiento"] < umbral, claves].drop_duplicates().to_numpy()))
    if malos:
        piv_r = piv[[k not in malos for k in piv.index]]
        filas.append({"bloque": f"global sin días bajo {umbral:.0%}", "profundidad_mm": "todas",
                      **_fila_comparacion(piv_r, sistema)})
    return pd.DataFrame(filas)


def tabla_tamanos(df: pd.DataFrame, sistema: str) -> pd.DataFrame:
    """Eje de tamaño del diseño en estrella: escenarios con más de un factor de tamaño."""
    prof = _profundidad_por_escenario(df) if not df.empty else {}
    filas = []
    for esc, g in df.groupby("escenario", sort=True):
        if g["factor_tamano"].nunique() < 2:
            continue
        for tam, gt in g.groupby("factor_tamano", sort=True):
            piv = gt.pivot_table(index=["orden", "seed"], columns="estrategia", values="costo", aggfunc="mean")
            filas.append({"escenario": esc, "profundidad_mm": prof.get(esc, ""), "factor_tamano": float(tam),
                          **_fila_comparacion(piv, sistema)})
    return pd.DataFrame(filas)


def por_grupo(df: pd.DataFrame, sistema: str, columna: str) -> pd.DataFrame:
    """Diferencia del sistema frente a TWAP y VWAP por `columna` (tramo_inicio o ticker), con tamaño 1: las tres
    profundidades juntas y cada una por separado."""
    d1 = df[np.isclose(df["factor_tamano"], 1.0)]
    filas = []
    for bloque, sub in [("global", d1)] + [(esc, g) for esc, g in d1.groupby("escenario", sort=True)]:
        for valor, g in sub.groupby(columna, sort=True):
            piv = g.pivot_table(index=["escenario", "orden", "seed"], columns="estrategia", values="costo", aggfunc="mean")
            fila = {"bloque": bloque, columna: valor, **_fila_comparacion(piv, sistema)}
            for ref in REFERENCIAS:
                if sistema in piv.columns and ref in piv.columns:
                    d = (piv[sistema] - piv[ref]).dropna()
                    fila[f"gana_vs_{ref}"] = f"{int((d < 0).sum())}/{len(d)}"
            filas.append(fila)
    return pd.DataFrame(filas)


def agregados_por_escenario(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(["escenario", "factor_tamano", "estrategia"])
    return pd.DataFrame({"n": g["costo"].size(), "media": g["costo"].mean(), "mediana": g["costo"].median(),
                         "peor": g["costo"].max(), "mejor": g["costo"].min(),
                         "cumplimiento_medio": g["cumplimiento"].mean(),
                         "cumplimiento_minimo": g["cumplimiento"].min()}).reset_index()


def calidad_md(cal: Dict) -> str:
    lineas = [f"**Veredicto: {cal['veredicto']}.** Corridas leídas: {cal['corridas_leidas']}. "
              f"Errores: {len(cal['errores'])}.", "",
              "| escenario | factor_tamano | corridas por estrategia | esperadas | días pareados | duplicados | "
              f"bajo {cal['umbral_cumplimiento']:.0%} | ok |", "|---|---|---|---|---|---|---|---|"]
    for b in cal["bloques"]:
        bajo = "; ".join(f"{x['orden']} s{x['seed']} {x['estrategia']} {x['cumplimiento']:.3f}" for x in b["bajo_umbral"])
        n = ", ".join(f"{e} {v}" for e, v in sorted(b["corridas_por_estrategia"].items()))
        lineas.append(f"| {b['escenario']} | {b['factor_tamano']:g} | {n} | {b['esperadas']} | {b['dias_pareados']} | "
                      f"{b['duplicados']} | {bajo or 'ninguna'} | {'sí' if b['ok'] else 'NO'} |")
    for e in cal["errores"]:
        lineas.append(f"- Error: {e['archivo']} {e['orden']} {e['estrategia']} s{e['seed']}: {e['error']}")
    return "\n".join(lineas) + "\n"


def _con_costo(df: pd.DataFrame, penalizacion_bps: Optional[float]) -> pd.DataFrame:
    out = df.copy()
    out["costo"] = costo(out, penalizacion_bps)
    return out


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


def _escribir_tabla(t: pd.DataFrame, out: Path, nombre: str, salidas: Dict[str, Path]) -> None:
    if t.empty:
        return
    for ext, contenido in (("csv", None), ("md", a_markdown(t)), ("tex", a_latex(t))):
        ruta = out / f"{nombre}.{ext}"
        if contenido is None:
            t.to_csv(ruta, index=False)
        else:
            ruta.write_text(contenido, encoding="utf-8")
        salidas[f"{nombre}_{ext}"] = ruta


def informe(df: pd.DataFrame, errores: Sequence[Dict], sistema: str, out: Path, n_esperado: int, umbral: float,
            ajustado_bps: Optional[float], n_archivos: int) -> Dict[str, Path]:
    """Salidas de la ampliación de BF. Las tablas con costo crudo; con `ajustado_bps`, también con el ajustado."""
    salidas: Dict[str, Path] = {}
    cal = chequeo_calidad(df, errores, n_esperado, umbral)
    salidas["calidad_json"] = out / "calidad.json"
    salidas["calidad_json"].write_text(json.dumps(cal, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    salidas["calidad_md"] = out / "calidad.md"
    salidas["calidad_md"].write_text(calidad_md(cal), encoding="utf-8")

    crudo = _con_costo(df, None)
    variantes = [("", crudo, "slippage crudo contra el precio de llegada")]
    if ajustado_bps is not None:
        variantes.append(("_ajustado", _con_costo(df, ajustado_bps),
                          f"costo ajustado: slippage × cumplimiento + {ajustado_bps:g} × (1 − cumplimiento)"))
    secciones = [f"# Consolidación 3.2.2\n\nSistema: `{sistema}`. Diferencias pareadas por día (escenario, orden y "
                 f"semilla); IC 95 % por bootstrap (3.000 remuestreos, semilla 0); diferencia % = 100 × media(sistema − "
                 f"referencia) / |media(referencia)|. Corridas leídas: {len(df)} de {n_archivos} archivos.\n",
                 "## Chequeo de calidad\n\n" + calidad_md(cal)]
    for sufijo, d, criterio in variantes:
        t90, ttam = tabla_90(d, sistema, umbral), tabla_tamanos(d, sistema)
        _escribir_tabla(t90, out, f"tabla_90{sufijo}", salidas)
        _escribir_tabla(ttam, out, f"tabla_tamanos{sufijo}", salidas)
        if not t90.empty:
            secciones.append(f"## Tamaño 1 por profundidad del market maker ({criterio})\n\n" + a_markdown(t90))
        if not ttam.empty:
            secciones.append(f"## Eje de tamaño ({criterio})\n\n" + a_markdown(ttam))
    for col, nombre in (("tramo_inicio", "por_tramo"), ("ticker", "por_activo")):
        t = por_grupo(crudo, sistema, col)
        if not t.empty:
            t.to_csv(out / f"{nombre}.csv", index=False)
            salidas[f"{nombre}_csv"] = out / f"{nombre}.csv"
            secciones.append(f"## {'Por tramo de inicio' if col == 'tramo_inicio' else 'Por activo'} (slippage crudo, "
                             f"tamaño 1)\n\n" + a_markdown(t))
    agg = agregados_por_escenario(crudo)
    agg.to_csv(out / "agregados_por_escenario.csv", index=False)
    salidas["agregados_por_escenario_csv"] = out / "agregados_por_escenario.csv"
    secciones.append("## Por estrategia, escenario y tamaño (slippage crudo)\n\n" + a_markdown(agg))
    salidas["informe_md"] = out / "informe_3_2_2.md"
    salidas["informe_md"].write_text("\n".join(secciones), encoding="utf-8")
    return salidas


def main(argv: Optional[Sequence[str]] = None) -> Dict[str, Path]:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--entradas", nargs="+", required=True, help="archivos JSON o carpetas con JSON")
    ap.add_argument("--sistema", default="PPO", help="nombre de la estrategia del sistema en los JSON")
    ap.add_argument("--penalizacion-bps", type=float, default=None,
                    help="costo de la tabla maestra: ajustado con P bps por acción no ejecutada (sin esto, crudo)")
    ap.add_argument("--ajustado-bps", type=float, default=None,
                    help="además del crudo, tablas de la 3.2.2 con el costo ajustado (criterio de BF: 30)")
    ap.add_argument("--n-esperado", type=int, default=N_ESPERADO, help="corridas esperadas por estrategia y bloque")
    ap.add_argument("--umbral-cumplimiento", type=float, default=UMBRAL_CUMPLIMIENTO)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args(argv)

    rutas: List[Path] = []
    for e in args.entradas:
        p = Path(e)
        if not p.exists():   # p. ej. un bloque de las 30 corridas que todavia no se corre
            print(f"(se salta {p}: no existe)")
            continue
        rutas += sorted(p.glob("*.json")) if p.is_dir() else [p]
    df = leer_corridas(rutas)
    if df.empty:
        sys.exit("No hay corridas válidas en las entradas.")
    df["costo"] = costo(df, args.penalizacion_bps)
    base, nota_base = base_global(df)
    maestra, agg = tabla_maestra(df, args.sistema), agregados(base)

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
        + a_markdown(maestra) + f"\n## Por estrategia{nota_base}\n\n" + a_markdown(agg), encoding="utf-8")
    salidas["tex"].write_text(a_latex(maestra), encoding="utf-8")
    salidas["png"] = out / "cajas.png"
    grafico_cajas(base, salidas["png"], criterio + ("; solo tamaño 1" if nota_base else ""))
    salidas.update(informe(df, leer_errores(rutas), args.sistema, out, args.n_esperado, args.umbral_cumplimiento,
                           args.ajustado_bps, len(rutas)))
    print(maestra.to_string(index=False))
    return salidas


if __name__ == "__main__":
    main()
