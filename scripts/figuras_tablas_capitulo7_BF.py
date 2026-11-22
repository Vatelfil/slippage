"""Figuras y tablas del Capítulo 7 «Resultados y evaluación» (BF, 4.1.2, Sprint 8).

No recalcula ninguna prueba: lee las salidas de la 3.2.2 (`data/analysis/3_2_2/`), que son la única fuente de las
cifras, y las deja en el formato del informe (coma decimal, LaTeX sin caracteres Unicode, profundidad ×4 / ×1 / ×0,25).

Salidas en --out-dir (por defecto data/analysis/capitulo7_BF/):
- cajas_profundidad.png: costo por corrida, 3 profundidades × 3 estrategias, mismo eje (tamaño 1). La leyenda va
  en el informe (LEYENDA_CAJAS).
- tabla_profundidad.{tex,md}: IS por estrategia, diferencias del sistema con IC 95 % y p de Wilcoxon (tabla_90.csv).
- tabla_tamanos.{tex,md}: lo mismo para el eje de tamaño en ×1 (tabla_tamanos.csv).
- tabla_cumplimiento.{tex,md}: cumplimiento mínimo y corridas con >= 95 % por bloque y estrategia (corridas.csv).
- tabla_estrategias.{tex,md}: media, mediana, desviación, peor, mejor y cumplimiento mínimo por profundidad y
  estrategia (corridas.csv, descriptivo).
- cifras_capitulo7_BF.json: las cifras que cita el texto del capítulo (docs/capitulo7_resultados_BF.md).

Uso: python scripts/figuras_tablas_capitulo7_BF.py [--entrada data/analysis/3_2_2] [--out-dir data/analysis/capitulo7_BF]
"""
import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.consolidar_resultados_3_2_2 import _pruebas, ic_bootstrap  # noqa: E402  (mismos métodos que la 3.2.2)
SISTEMA = "PPO_sistema"
ESTRATEGIAS = [(SISTEMA, "Sistema"), ("TWAP", "TWAP"), ("VWAP", "VWAP")]
# Colores del equipo (los mismos de las figuras de PS): el color acompaña al nombre, nunca va solo.
COLORES = {SISTEMA: "#0B6E64", "TWAP": "#7A7A7A", "VWAP": "#B07D2B"}
PROFUNDIDADES = [("baja", "×4", r"$\times$4"), ("media", "×1", r"$\times$1"), ("alta", "×0,25", r"$\times$0,25")]
UMBRAL = 0.95
LEYENDA_CAJAS = ("Costo por corrida (slippage contra el precio de llegada, bps) según la profundidad del market maker, "
                 "tamaño 1. Caja: cuartiles; línea: mediana; rombo: media; bigotes: 1,5 veces el rango intercuartil; "
                 "círculos: corridas fuera de los bigotes. 30 corridas por caja (10 órdenes × 3 semillas).")


def coma(x: float, dec: int = 2, signo: bool = False) -> str:
    """Número con coma decimal; signo explícito si se pide (para diferencias)."""
    if x is None or not np.isfinite(x):
        return "—"
    s = f"{x:+.{dec}f}" if signo else f"{x:.{dec}f}"
    return s.replace(".", ",")


def coma_ic(ic: str, dec: int = 2) -> str:
    """'[-16.56; 25.30]' -> '[-16,56; 25,30]' (formato de los CSV de la 3.2.2)."""
    lo, hi = (float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", ic))
    return f"[{coma(lo, dec)}; {coma(hi, dec)}]"


def p_txt(p: float) -> str:
    return coma(p, 2) if p >= 0.01 else f"{p:.1e}".replace(".", ",")


def a_latex_num(s: str) -> str:
    """Signo menos tipográfico en LaTeX: '-3,34' -> '$-$3,34'."""
    return s.replace("-", "$-$")


# ---------------------------------------------------------------------------
# Tablas
# ---------------------------------------------------------------------------

def filas_profundidad(t90: pd.DataFrame) -> List[Dict[str, str]]:
    etiqueta = {k: (u, l) for k, u, l in PROFUNDIDADES}
    etiqueta["global"] = ("Global", "Global")
    etiqueta["global sin días bajo 95%"] = ("Global sin días bajo 95 %", r"Global sin días bajo 95 \%")
    filas = []
    for clave in ("baja", "media", "alta", "global", "global sin días bajo 95%"):
        sel = t90[t90["bloque"] == clave]
        if sel.empty:
            continue
        r = sel.iloc[0]
        filas.append({"md": etiqueta[clave][0], "tex": etiqueta[clave][1], "n": str(int(r["n_pares"])),
                      "sis": coma(r[f"IS_{SISTEMA}"]), "twap": coma(r["IS_TWAP"]), "vwap": coma(r["IS_VWAP"]),
                      "d_twap": coma(r["dif_vs_TWAP_bps"], signo=True), "ic_twap": coma_ic(r["dif_vs_TWAP_ic"]),
                      "p_twap": p_txt(r["p_wilcoxon_vs_TWAP"]),
                      "d_vwap": coma(r["dif_vs_VWAP_bps"], signo=True), "ic_vwap": coma_ic(r["dif_vs_VWAP_ic"]),
                      "p_vwap": p_txt(r["p_wilcoxon_vs_VWAP"])})
    return filas


def filas_tamanos(tt: pd.DataFrame) -> List[Dict[str, str]]:
    filas = []
    for _, r in tt.sort_values("factor_tamano").iterrows():
        tam = coma(float(r["factor_tamano"]), 1).replace(",0", "")
        filas.append({"md": tam, "tex": tam, "n": str(int(r["n_pares"])),
                      "sis": coma(r[f"IS_{SISTEMA}"]), "twap": coma(r["IS_TWAP"]), "vwap": coma(r["IS_VWAP"]),
                      "d_twap": coma(r["dif_vs_TWAP_bps"], signo=True), "ic_twap": coma_ic(r["dif_vs_TWAP_ic"]),
                      "p_twap": p_txt(r["p_wilcoxon_vs_TWAP"]),
                      "d_vwap": coma(r["dif_vs_VWAP_bps"], signo=True), "ic_vwap": coma_ic(r["dif_vs_VWAP_ic"]),
                      "p_vwap": p_txt(r["p_wilcoxon_vs_VWAP"])})
    return filas


COLS_COMP = [("n", "n"), ("sis", "Sistema"), ("twap", "TWAP"), ("vwap", "VWAP"),
             ("d_twap", "Sist. − TWAP"), ("ic_twap", "IC 95 %"), ("p_twap", "p"),
             ("d_vwap", "Sist. − VWAP"), ("ic_vwap", "IC 95 %"), ("p_vwap", "p")]


def md_comparacion(filas: List[Dict[str, str]], primera: str) -> str:
    cab = [primera] + [c for _, c in COLS_COMP]
    lineas = ["| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)]
    for f in filas:
        lineas.append("| " + " | ".join([f["md"]] + [f[k].replace("-", "−") for k, _ in COLS_COMP]) + " |")
    return "\n".join(lineas) + "\n"


def tex_comparacion(filas: List[Dict[str, str]], primera: str, caption: str, label: str) -> str:
    cab = (f"{primera} & $n$ & Sistema & TWAP & VWAP & Sist.\\ $-$ TWAP & IC 95\\,\\% & $p$ "
           f"& Sist.\\ $-$ VWAP & IC 95\\,\\% & $p$ \\\\")
    cuerpo = []
    for i, f in enumerate(filas):
        if f["md"].startswith("Global") and (i == 0 or not filas[i - 1]["md"].startswith("Global")):
            cuerpo.append(r"\hline")
        celdas = [f["tex"]] + [a_latex_num(f[k]) for k, _ in COLS_COMP]
        cuerpo.append(" & ".join(celdas) + r" \\")
    return "\n".join([
        "% Generado por scripts/figuras_tablas_capitulo7_BF.py desde data/analysis/3_2_2/. No editar a mano.",
        r"\begin{table}[htbp]", r"\centering", r"\small", r"\setlength{\tabcolsep}{4pt}",
        f"\\caption{{{caption}}}", f"\\label{{{label}}}",
        r"\begin{tabular}{lrrrrrcrrcr}", r"\hline", cab, r"\hline", *cuerpo, r"\hline", r"\end{tabular}",
        r"\end{table}", ""])


def tabla_cumplimiento(corr: pd.DataFrame) -> pd.DataFrame:
    """Por bloque (profundidad con tamaño 1; tamaños con ×1) y estrategia: mínimo y corridas con >= 95 %."""
    filas = []
    bloques = [(k, 1.0, f"{u}, tamaño 1", f"{l}, tamaño 1") for k, u, l in PROFUNDIDADES]
    bloques += [("media", t, f"×1, tamaño {coma(t, 1)}", f"$\\times$1, tamaño {coma(t, 1)}") for t in (0.5, 1.5)]
    for esc, tam, md, tex in bloques:
        g = corr[(corr["escenario"] == esc) & np.isclose(corr["factor_tamano"], tam)]
        if g.empty:
            continue
        fila = {"bloque_md": md, "bloque_tex": tex}
        for e, _ in ESTRATEGIAS:
            c = g.loc[g["estrategia"] == e, "cumplimiento"]
            fila[f"{e}_min"] = float(c.min())
            fila[f"{e}_ok"] = int((c >= UMBRAL).sum())
            fila[f"{e}_n"] = int(len(c))
        filas.append(fila)
    return pd.DataFrame(filas)


def md_cumplimiento(tc: pd.DataFrame) -> str:
    cab = ["Bloque"] + [f"{n}: mínimo / ≥ 95 %" for _, n in ESTRATEGIAS]
    lineas = ["| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)]
    for _, r in tc.iterrows():
        celdas = [r["bloque_md"]] + [f"{coma(100 * r[f'{e}_min'], 1)} % / {r[f'{e}_ok']} de {r[f'{e}_n']}"
                                     for e, _ in ESTRATEGIAS]
        lineas.append("| " + " | ".join(celdas) + " |")
    return "\n".join(lineas) + "\n"


def tex_cumplimiento(tc: pd.DataFrame) -> str:
    cab = "Bloque & " + " & ".join(f"\\multicolumn{{2}}{{c}}{{{n}}}" for _, n in ESTRATEGIAS) + r" \\"
    sub = " & " + " & ".join(r"Mín. & $\geq$ 95\,\%" for _ in ESTRATEGIAS) + r" \\"
    cuerpo = []
    for _, r in tc.iterrows():
        celdas = [r["bloque_tex"]]
        for e, _ in ESTRATEGIAS:
            celdas += [f"{coma(100 * r[f'{e}_min'], 1)}\\,\\%", f"{r[f'{e}_ok']}/{r[f'{e}_n']}"]
        cuerpo.append(" & ".join(celdas) + r" \\")
    return "\n".join([
        "% Generado por scripts/figuras_tablas_capitulo7_BF.py desde data/analysis/3_2_2/corridas.csv. No editar a mano.",
        r"\begin{table}[htbp]", r"\centering", r"\small",
        r"\caption{Cumplimiento de la orden (acciones ejecutadas / acciones de la orden): mínimo por bloque y "
        r"corridas que llegan al 95\,\%. 30 corridas por estrategia y bloque.}",
        r"\label{tab:cumplimiento}", r"\begin{tabular}{lrrrrrr}", r"\hline", cab, sub, r"\hline", *cuerpo,
        r"\hline", r"\end{tabular}", r"\end{table}", ""])


def tabla_estrategias(corr: pd.DataFrame) -> pd.DataFrame:
    """Distribución del costo por profundidad (tamaño 1) y estrategia, y las 90 juntas. Descriptivo."""
    d = corr[np.isclose(corr["factor_tamano"], 1.0)]
    bloques = [(k, u, l) for k, u, l in PROFUNDIDADES] + [(None, "Las 90", "Las 90")]
    filas = []
    for esc, md, tex in bloques:
        g = d if esc is None else d[d["escenario"] == esc]
        for e, nombre in ESTRATEGIAS:
            c = g.loc[g["estrategia"] == e]
            filas.append({"bloque_md": md, "bloque_tex": tex, "estrategia": nombre, "n": int(len(c)),
                          "media": float(c["slippage_bps"].mean()), "mediana": float(c["slippage_bps"].median()),
                          "desv": float(c["slippage_bps"].std(ddof=1)), "peor": float(c["slippage_bps"].max()),
                          "mejor": float(c["slippage_bps"].min()), "cumpl_min": float(c["cumplimiento"].min())})
    return pd.DataFrame(filas)


def md_estrategias(te: pd.DataFrame) -> str:
    cab = ["Profundidad", "Estrategia", "n", "Media", "Mediana", "Desv. est.", "Peor", "Mejor", "Cumplimiento mínimo"]
    lineas = ["| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)]
    for _, r in te.iterrows():
        celdas = [r["bloque_md"], r["estrategia"], str(r["n"])]
        celdas += [coma(r[k]).replace("-", "−") for k in ("media", "mediana", "desv", "peor", "mejor")]
        celdas.append(f"{coma(100 * r['cumpl_min'], 1)} %")
        lineas.append("| " + " | ".join(celdas) + " |")
    return "\n".join(lineas) + "\n"


def tex_estrategias(te: pd.DataFrame) -> str:
    cab = r"Profundidad & Estrategia & $n$ & Media & Mediana & Desv.\ est. & Peor & Mejor & Cumpl.\ mín. \\"
    cuerpo, previo = [], None
    for _, r in te.iterrows():
        if previo is not None and r["bloque_tex"] != previo:
            cuerpo.append(r"\hline")
        bloque = r["bloque_tex"] if r["bloque_tex"] != previo else ""
        previo = r["bloque_tex"]
        celdas = [bloque, r["estrategia"], str(r["n"])]
        celdas += [a_latex_num(coma(r[k])) for k in ("media", "mediana", "desv", "peor", "mejor")]
        celdas.append(coma(100 * r["cumpl_min"], 1) + r"\,\%")
        cuerpo.append(" & ".join(celdas) + r" \\")
    return "\n".join([
        "% Generado por scripts/figuras_tablas_capitulo7_BF.py desde data/analysis/3_2_2/corridas.csv. No editar a mano.",
        r"\begin{table}[htbp]", r"\centering", r"\small",
        r"\caption{Distribución del costo por corrida (slippage contra el precio de llegada, bps) por profundidad del "
        r"market maker y estrategia, tamaño 1. Peor: costo máximo; mejor: costo mínimo (negativo = compró bajo el "
        r"precio de llegada).}",
        r"\label{tab:distribucion_costo}", r"\begin{tabular}{llrrrrrrr}", r"\hline", cab, r"\hline", *cuerpo,
        r"\hline", r"\end{tabular}", r"\end{table}", ""])


def _dif_pareada(corr: pd.DataFrame, filtro, ref: str = "TWAP", solo_completos: bool = False) -> Dict:
    """Sistema − referencia por día (escenario, orden, semilla). Mismo bootstrap que la 3.2.2. Con solo_completos,
    se quitan los días en que alguna estrategia ejecutó menos del 95 %."""
    g = corr[filtro(corr)]
    idx = ["escenario", "orden", "seed"]
    costo = g.pivot_table(index=idx, columns="estrategia", values="slippage_bps")
    if solo_completos:
        cum = g.pivot_table(index=idx, columns="estrategia", values="cumplimiento")
        costo = costo[(cum >= UMBRAL).all(axis=1)]
    d = (costo[SISTEMA] - costo[ref]).to_numpy()
    lo, hi = ic_bootstrap(d)
    p_wil, _ = _pruebas(d)
    return {"n": int(len(d)), "dif": float(d.mean()), "ic": [float(lo), float(hi)], "p_wilcoxon": float(p_wil),
            "gana": int((d < 0).sum()), "pierde": int((d > 0).sum())}


def cifras(corr: pd.DataFrame, tc: pd.DataFrame, ent: Path) -> Dict:
    """Cifras que cita el texto. Las medias y los IC repiten los de la 3.2.2 (mismo bootstrap); lo nuevo son los
    días ganados y la variante del tamaño 1,5 sin días bajo el 95 % (descriptiva)."""
    def t1(df):
        return np.isclose(df["factor_tamano"], 1.0)

    out: Dict = {"fuente": "data/analysis/3_2_2/ (3.2.2, BF)", "corridas": int(len(corr)),
                 "por_profundidad": {}, "tamano": {}}
    for esc, uni, _ in PROFUNDIDADES:
        out["por_profundidad"][uni] = {ref: _dif_pareada(corr, lambda df, e=esc: t1(df) & (df["escenario"] == e), ref)
                                       for ref in ("TWAP", "VWAP")}
    out["global"] = {ref: _dif_pareada(corr, t1, ref) for ref in ("TWAP", "VWAP")}
    for tam in (0.5, 1.0, 1.5):
        def f(df, t=tam):
            return (df["escenario"] == "media") & np.isclose(df["factor_tamano"], t)
        out["tamano"][coma(tam, 1)] = {"todos": _dif_pareada(corr, f),
                                       "sin_dias_bajo_95": _dif_pareada(corr, f, solo_completos=True)}
    out["cumplimiento"] = {"sistema_ok": int(tc["PPO_sistema_ok"].sum()), "sistema_n": int(tc["PPO_sistema_n"].sum()),
                           "sistema_min": float(tc["PPO_sistema_min"].min()),
                           "twap_ok": int(tc["TWAP_ok"].sum()), "vwap_ok": int(tc["VWAP_ok"].sum())}
    for corte, archivo in (("tramo_inicio", "por_tramo.csv"), ("ticker", "por_activo.csv")):
        t = pd.read_csv(ent / archivo, encoding="utf-8")
        t = t[t["bloque"] == "global"]
        out[corte] = {r[corte]: {"n": int(r["n_pares"]), "dif": float(r["dif_vs_TWAP_bps"]),
                                 "ic": r["dif_vs_TWAP_ic"], "gana": r["gana_vs_TWAP"]} for _, r in t.iterrows()}
    return out


# ---------------------------------------------------------------------------
# Figura
# ---------------------------------------------------------------------------

def figura_cajas(corr: pd.DataFrame, t90: pd.DataFrame, ruta: Path) -> Dict[str, Dict[str, float]]:
    """Cajas del costo por corrida: un panel por profundidad (tamaño 1), las tres estrategias, mismo eje y. Cada panel
    indica n, la diferencia sistema − TWAP y su p de Wilcoxon (criterio de figuras de la profesora, 6 nov)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter

    d = corr[np.isclose(corr["factor_tamano"], 1.0)]
    fig, axes = plt.subplots(1, 3, figsize=(9.0, 4.6), sharey=True)
    comp = t90.set_index("bloque")
    medias: Dict[str, Dict[str, float]] = {}
    for ax, (esc, uni, _) in zip(axes, PROFUNDIDADES):
        datos = [d.loc[(d["escenario"] == esc) & (d["estrategia"] == e), "slippage_bps"].to_numpy()
                 for e, _ in ESTRATEGIAS]
        medias[esc] = {e: float(np.mean(v)) for (e, _), v in zip(ESTRATEGIAS, datos)}
        cajas = ax.boxplot(datos, widths=0.55, patch_artist=True, showmeans=True,
                           medianprops={"color": "#1F1F1F", "lw": 1.6},
                           meanprops={"marker": "D", "markersize": 6, "markerfacecolor": "white",
                                      "markeredgecolor": "#1F1F1F", "markeredgewidth": 1.0},
                           whiskerprops={"color": "#52514E", "lw": 1.0}, capprops={"color": "#52514E", "lw": 1.0},
                           flierprops={"marker": "o", "markersize": 4, "markerfacecolor": "none",
                                       "markeredgecolor": "#52514E", "markeredgewidth": 0.8})
        for caja, (e, _) in zip(cajas["boxes"], ESTRATEGIAS):
            caja.set_facecolor(COLORES[e])
            caja.set_alpha(0.85)
            caja.set_edgecolor("white")
            caja.set_linewidth(1.5)
        ax.axhline(0, color="#9A9994", lw=0.8, zorder=0)
        ax.set_xticks([1, 2, 3])
        ax.set_xticklabels([f"{n}\nmedia {coma(medias[esc][e], 2)}" for e, n in ESTRATEGIAS], fontsize=8.5)
        r = comp.loc[esc]
        ax.set_title(f"Profundidad del market maker {uni}", fontsize=10, pad=30)
        ax.text(0.5, 1.015, f"n = {int(r['n_pares'])} días; sistema − TWAP = "
                            f"{coma(r['dif_vs_TWAP_bps'], signo=True).replace('-', '−')} bps\n"
                            f"Wilcoxon pareado, p = {p_txt(r['p_wilcoxon_vs_TWAP'])}",
                transform=ax.transAxes, ha="center", va="bottom", fontsize=8, color="#52514E", linespacing=1.3)
        ax.grid(axis="y", color="#E4E3DF", lw=0.6)
        ax.set_axisbelow(True)
        for lado in ("top", "right"):
            ax.spines[lado].set_visible(False)
        ax.tick_params(axis="y", labelsize=8.5)
    axes[0].set_ylabel("Slippage contra el precio de llegada (bps)", fontsize=9)
    axes[0].yaxis.set_major_formatter(FuncFormatter(lambda v, _: coma(v, 0).replace("-", "−")))
    fig.tight_layout()
    fig.savefig(ruta, dpi=200)
    plt.close(fig)
    return medias


# ---------------------------------------------------------------------------

def main(argv: Optional[Sequence[str]] = None) -> Dict[str, Path]:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--entrada", default="data/analysis/3_2_2")
    ap.add_argument("--out-dir", default="data/analysis/capitulo7_BF")
    a = ap.parse_args(argv)
    ent = Path(a.entrada) if Path(a.entrada).is_absolute() else ROOT / a.entrada
    out = Path(a.out_dir) if Path(a.out_dir).is_absolute() else ROOT / a.out_dir
    out.mkdir(parents=True, exist_ok=True)

    t90 = pd.read_csv(ent / "tabla_90.csv", encoding="utf-8")
    tt = pd.read_csv(ent / "tabla_tamanos.csv", encoding="utf-8")
    corr = pd.read_csv(ent / "corridas.csv", encoding="utf-8")

    salidas: Dict[str, Path] = {}
    fp = filas_profundidad(t90)
    salidas["profundidad_md"] = out / "tabla_profundidad.md"
    salidas["profundidad_md"].write_text(md_comparacion(fp, "Profundidad"), encoding="utf-8")
    salidas["profundidad_tex"] = out / "tabla_profundidad.tex"
    salidas["profundidad_tex"].write_text(tex_comparacion(
        fp, "Profundidad",
        r"Costo medio (slippage contra el precio de llegada, bps) por profundidad del market maker, tamaño 1. "
        r"Diferencias pareadas por orden y semilla; IC 95\,\% por bootstrap; $p$ de Wilcoxon.",
        "tab:resultados_profundidad"), encoding="utf-8")

    ft = filas_tamanos(tt)
    salidas["tamanos_md"] = out / "tabla_tamanos.md"
    salidas["tamanos_md"].write_text(md_comparacion(ft, "Tamaño"), encoding="utf-8")
    salidas["tamanos_tex"] = out / "tabla_tamanos.tex"
    salidas["tamanos_tex"].write_text(tex_comparacion(
        ft, "Tamaño",
        r"Costo medio (bps) según el tamaño de la orden (factor sobre el 10\,\% del volumen del día), profundidad "
        r"$\times$1. Diferencias pareadas por orden y semilla; IC 95\,\% por bootstrap; $p$ de Wilcoxon.",
        "tab:resultados_tamano"), encoding="utf-8")

    tc = tabla_cumplimiento(corr)
    salidas["cumplimiento_md"] = out / "tabla_cumplimiento.md"
    salidas["cumplimiento_md"].write_text(md_cumplimiento(tc), encoding="utf-8")
    salidas["cumplimiento_tex"] = out / "tabla_cumplimiento.tex"
    salidas["cumplimiento_tex"].write_text(tex_cumplimiento(tc), encoding="utf-8")

    salidas["cajas_png"] = out / "cajas_profundidad.png"
    figura_cajas(corr, t90, salidas["cajas_png"])

    te = tabla_estrategias(corr)
    salidas["estrategias_md"] = out / "tabla_estrategias.md"
    salidas["estrategias_md"].write_text(md_estrategias(te), encoding="utf-8")
    salidas["estrategias_tex"] = out / "tabla_estrategias.tex"
    salidas["estrategias_tex"].write_text(tex_estrategias(te), encoding="utf-8")

    salidas["cifras_json"] = out / "cifras_capitulo7_BF.json"
    salidas["cifras_json"].write_text(json.dumps(cifras(corr, tc, ent), ensure_ascii=False, indent=2) + "\n",
                                      encoding="utf-8")
    for k, p in salidas.items():
        print(f"{k}: {p}")
    return salidas


if __name__ == "__main__":
    main()
