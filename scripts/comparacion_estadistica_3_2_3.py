"""Comparación estadística del sistema contra TWAP y VWAP (tarea 3.2.3, PS).

Sigue el plan de análisis fijado antes de ver las 90 corridas (`docs/plan_analisis_3_2_3_PS.md`):

- Pregunta principal: diferencia de costo sistema − referencia en todas las corridas, pareada por escenario, orden y
  semilla. Wilcoxon de rangos con signo (bilateral) como test principal; t-test pareado como complemento.
- Normalidad: Shapiro-Wilk de las diferencias (decide si el t-test es válido) y gráfico Q-Q.
- Tamaños de efecto: diferencia media con IC 95 % por bootstrap, d de Cohen pareado (media / desviación de las
  diferencias) y correlación biserial de rangos (r, el efecto natural del Wilcoxon).
- Por escenario: lo mismo, con los p del Wilcoxon corregidos por Holm (varias comparaciones).
- Entre escenarios: Kruskal-Wallis sobre las diferencias (¿la ventaja depende de la liquidez?), Mann-Whitney U entre
  pares de escenarios con Holm, y Friedman como control porque las mismas órdenes y semillas se repiten en cada escenario.
- Robustez: sin MO-06 (en la 3.1.3 movía el promedio) y con el promedio por orden y semilla (las 90 no son del todo
  independientes, porque la misma orden aparece en los tres escenarios).

Lee los mismos JSON que la 3.2.2 (evaluador del sistema y de benchmarks) o el `corridas.csv` del consolidador.

    python scripts/comparacion_estadistica_3_2_3.py --entradas <carpetas o json> --sistema PPO_sistema \
        --out-dir data/analysis/3_2_3 --out-md docs/comparacion_estadistica_3_2_3_PS.md
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np
import pandas as pd
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.consolidar_resultados_3_2_2 import costo, ic_bootstrap, leer_corridas  # noqa: E402

REFERENCIAS = ("TWAP", "VWAP")
ALFA = 0.05
ORDEN_ESCENARIOS = ("baja", "media", "alta")
CLAVE = ["escenario", "factor_tamano", "orden", "seed"]


# ---------------------------------------------------------------- datos

def cargar(entradas: Sequence[str]) -> pd.DataFrame:
    """Una fila por corrida, desde JSON (carpetas o archivos) o desde un corridas.csv de la 3.2.2."""
    csvs = [Path(e) for e in entradas if e.endswith(".csv")]
    rutas: List[Path] = []
    for e in entradas:
        p = Path(e)
        if p.suffix == ".csv":
            continue
        if not p.exists():
            print(f"(se salta {p}: no existe)")
            continue
        rutas += sorted(p.rglob("*.json")) if p.is_dir() else [p]
    partes = [leer_corridas(rutas)] if rutas else []
    partes += [pd.read_csv(c) for c in csvs]
    if not partes:
        return pd.DataFrame()
    df = pd.concat(partes, ignore_index=True)
    return df.drop_duplicates(subset=CLAVE + ["estrategia"], keep="last")


def diferencias(df: pd.DataFrame, sistema: str, ref: str) -> pd.DataFrame:
    """Pares sistema − referencia por escenario, tamaño, orden y semilla (solo los que tienen ambos)."""
    piv = df.pivot_table(index=CLAVE, columns="estrategia", values="costo", aggfunc="mean")
    if sistema not in piv.columns or ref not in piv.columns:
        return pd.DataFrame(columns=CLAVE + ["sistema", "ref", "dif"])
    par = piv[[sistema, ref]].dropna().reset_index()
    par = par.rename(columns={sistema: "sistema", ref: "ref"})
    par["dif"] = par["sistema"] - par["ref"]
    return par


# ---------------------------------------------------------------- estadística

def holm(pvalores: Sequence[Optional[float]]) -> List[Optional[float]]:
    """Corrección de Holm-Bonferroni (los None quedan como None)."""
    idx = [i for i, p in enumerate(pvalores) if p is not None and not np.isnan(p)]
    orden = sorted(idx, key=lambda i: pvalores[i])
    m, out, acumulado = len(orden), list(pvalores), 0.0
    for k, i in enumerate(orden):
        acumulado = max(acumulado, min(1.0, (m - k) * float(pvalores[i])))
        out[i] = acumulado
    return out


def biserial_rangos(d: np.ndarray) -> float:
    """Correlación biserial de rangos pareada: (R+ − R−) / (R+ + R−), entre −1 y 1. Negativa = el sistema cuesta menos."""
    d = d[d != 0]
    if len(d) == 0:
        return float("nan")
    rangos = stats.rankdata(np.abs(d))
    rp, rn = rangos[d > 0].sum(), rangos[d < 0].sum()
    return float((rp - rn) / (rp + rn))


def resumen(d: Sequence[float], base: Optional[Sequence[float]] = None) -> Dict:
    """Todo lo de una comparación pareada: n, media, IC, normalidad, Wilcoxon, t, d de Cohen y r."""
    d = np.asarray(d, dtype=float)
    n = len(d)
    out: Dict = {"n": n, "dif_media": float(d.mean()) if n else None, "dif_mediana": float(np.median(d)) if n else None,
                 "sd_dif": float(d.std(ddof=1)) if n > 1 else None, "ic95": [None, None], "shapiro_p": None,
                 "normal": None, "wilcoxon_p": None, "t_p": None, "d_cohen": None, "r_rangos": None,
                 "gana_sistema": int((d < 0).sum()), "dif_pct": None}
    if n >= 2:
        out["ic95"] = list(ic_bootstrap(d))
    if n >= 3:
        out["shapiro_p"] = float(stats.shapiro(d).pvalue)
        out["normal"] = out["shapiro_p"] >= ALFA
    if n >= 2 and np.any(d != 0):
        out["wilcoxon_p"] = float(stats.wilcoxon(d).pvalue)
        out["t_p"] = float(stats.ttest_1samp(d, 0.0).pvalue)
        out["r_rangos"] = biserial_rangos(d)
        if out["sd_dif"]:
            out["d_cohen"] = float(d.mean() / out["sd_dif"])
    if base is not None and n:
        m = float(np.mean(base))
        out["dif_pct"] = 100.0 * float(d.mean()) / abs(m) if m else None
    return out


def magnitud_d(d: Optional[float]) -> str:
    """Rótulo convencional de Cohen para |d|."""
    if d is None or np.isnan(d):
        return "—"
    a = abs(d)
    return "despreciable" if a < 0.2 else "pequeño" if a < 0.5 else "mediano" if a < 0.8 else "grande"


def entre_escenarios(par: pd.DataFrame) -> Optional[Dict]:
    """Kruskal-Wallis, Mann-Whitney por pares (Holm) y Friedman sobre las diferencias de cada escenario."""
    escenarios = [e for e in _orden_escenarios(par["escenario"].unique())]
    if len(escenarios) < 2:
        return None
    grupos = {e: par.loc[par["escenario"] == e, "dif"].to_numpy() for e in escenarios}
    kw = stats.kruskal(*grupos.values())
    n_tot, k = sum(len(g) for g in grupos.values()), len(grupos)
    eps2 = float((kw.statistic - k + 1) / (n_tot - k)) if n_tot > k else None   # épsilon² (efecto del KW)
    pares = list(itertools.combinations(escenarios, 2))
    mw = [stats.mannwhitneyu(grupos[a], grupos[b], alternative="two-sided") for a, b in pares]
    p_holm = holm([float(x.pvalue) for x in mw])
    out = {"escenarios": escenarios, "kruskal_H": float(kw.statistic), "kruskal_p": float(kw.pvalue), "epsilon2": eps2,
           "mann_whitney": [{"a": a, "b": b, "U": float(x.statistic), "p": float(x.pvalue), "p_holm": ph,
                             "r": float(1 - 2 * x.statistic / (len(grupos[a]) * len(grupos[b])))}
                            for (a, b), x, ph in zip(pares, mw, p_holm)],
           "friedman_p": None, "friedman_bloques": 0}
    ancho = par.pivot_table(index=["orden", "seed"], columns="escenario", values="dif").dropna()
    if len(escenarios) >= 3 and len(ancho) >= 2:
        out["friedman_p"] = float(stats.friedmanchisquare(*[ancho[e] for e in escenarios]).pvalue)
        out["friedman_bloques"] = int(len(ancho))
    return out


def _orden_escenarios(valores) -> List[str]:
    vals = list(valores)
    return [e for e in ORDEN_ESCENARIOS if e in vals] + sorted(v for v in vals if v not in ORDEN_ESCENARIOS)


def analizar(df: pd.DataFrame, sistema: str, excluir: Sequence[str] = ("MO-06",)) -> Dict:
    resultado: Dict = {"sistema": sistema, "n_corridas": int(len(df)), "referencias": {}}
    for ref in REFERENCIAS:
        par = diferencias(df, sistema, ref)
        if par.empty:
            continue
        escenarios = _orden_escenarios(par["escenario"].unique())
        r: Dict = {"total": resumen(par["dif"], par["ref"]), "por_escenario": {}}
        for e in escenarios:
            g = par[par["escenario"] == e]
            r["por_escenario"][e] = resumen(g["dif"], g["ref"])
        p_holm = holm([r["por_escenario"][e]["wilcoxon_p"] for e in escenarios])
        for e, ph in zip(escenarios, p_holm):
            r["por_escenario"][e]["wilcoxon_p_holm"] = ph
        sin = par[~par["orden"].isin(excluir)]
        r["sin_" + "_".join(excluir)] = resumen(sin["dif"], sin["ref"])
        prom = par.groupby(["orden", "seed"], as_index=False)[["dif", "ref"]].mean()
        r["promedio_por_orden_y_semilla"] = resumen(prom["dif"], prom["ref"])
        r["entre_escenarios"] = entre_escenarios(par)
        r["diferencias"] = par[CLAVE + ["dif"]].to_dict(orient="records")
        resultado["referencias"][ref] = r
    return resultado


# ---------------------------------------------------------------- salidas

def _f(x, d: int = 2) -> str:
    return "—" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{d}f}"


def _p(x) -> str:
    return "—" if x is None or (isinstance(x, float) and np.isnan(x)) else ("< 0,001" if x < 0.001 else f"{x:.3f}")


def _fila(etiqueta: str, ref: str, g: Dict, holm_p=None) -> str:
    sig = "**sí**" if g["wilcoxon_p"] is not None and (holm_p if holm_p is not None else g["wilcoxon_p"]) < ALFA else "no"
    return (f"| {etiqueta} | {ref} | {g['n']} | {_f(g['dif_media'])} | [{_f(g['ic95'][0])}; {_f(g['ic95'][1])}] | "
            f"{_f(g['dif_pct'], 1)} % | {_p(g['shapiro_p'])} | {_p(g['wilcoxon_p'])} | "
            f"{_p(holm_p) if holm_p is not None else '—'} | {_p(g['t_p'])} | {_f(g['d_cohen'])} ({magnitud_d(g['d_cohen'])}) | "
            f"{_f(g['r_rangos'])} | {g['gana_sistema']}/{g['n']} | {sig} |")


def informe(res: Dict, titulo: str, fuentes: str) -> str:
    L = [f"# {titulo}", "", f"Sistema: `{res['sistema']}`. Corridas leídas: {res['n_corridas']}. {fuentes}", "",
         "Diferencia = costo del sistema − costo de la referencia, en bps, pareada por escenario, orden y semilla. "
         "**Negativa = el sistema cuesta menos.** IC 95 % por bootstrap. Shapiro p ≥ 0,05: no se rechaza la normalidad "
         "de las diferencias (el t-test es válido). d de Cohen pareado: 0,2 pequeño, 0,5 mediano, 0,8 grande. "
         "r: correlación biserial de rangos (−1 = el sistema siempre más barato). Significativo: Wilcoxon (con Holm "
         "cuando hay varios escenarios) < 0,05.", "",
         "## Tabla de p-valores y efectos", "",
         "| Grupo | Ref. | n | Dif. media | IC 95 % | Dif. % | Shapiro p | Wilcoxon p | Wilcoxon p (Holm) | t p | d de Cohen | r | Gana el sistema | Signif. |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    clave_sin = None
    for ref, r in res["referencias"].items():
        L.append(_fila("**Total (principal)**", ref, r["total"]))
        for e, g in r["por_escenario"].items():
            if len(r["por_escenario"]) > 1:
                L.append(_fila(f"Liquidez {e}", ref, g, g.get("wilcoxon_p_holm")))
        clave_sin = next(k for k in r if k.startswith("sin_"))
        L.append(_fila(f"Total {clave_sin.replace('_', ' ')}", ref, r[clave_sin]))
        L.append(_fila("Promedio por orden y semilla", ref, r["promedio_por_orden_y_semilla"]))
    L += ["", "## Entre escenarios (¿la ventaja depende de la liquidez?)", ""]
    hubo = False
    for ref, r in res["referencias"].items():
        ee = r["entre_escenarios"]
        if ee is None:
            continue
        hubo = True
        L += [f"**{ref}.** Kruskal-Wallis H = {_f(ee['kruskal_H'])}, p = {_p(ee['kruskal_p'])}, épsilon² = {_f(ee['epsilon2'], 3)}. "
              f"Friedman (bloques orden × semilla: {ee['friedman_bloques']}): p = {_p(ee['friedman_p'])}.", "",
              "| Escenarios | U | p | p (Holm) | r |", "|---|---|---|---|---|"]
        L += [f"| {m['a']} vs {m['b']} | {_f(m['U'], 1)} | {_p(m['p'])} | {_p(m['p_holm'])} | {_f(m['r'])} |"
              for m in ee["mann_whitney"]]
        L.append("")
    if not hubo:
        L += ["Hay un solo escenario en los datos: Kruskal-Wallis, Mann-Whitney y Friedman se calculan cuando estén las "
              "tres liquideces.", ""]
    return "\n".join(L) + "\n"


def figuras(res: Dict, out: Path) -> Dict[str, Path]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rutas = {}
    refs = list(res["referencias"])
    # 1) Q-Q de las diferencias
    fig, axes = plt.subplots(1, len(refs), figsize=(5.2 * len(refs), 4.2), squeeze=False)
    for ax, ref in zip(axes[0], refs):
        d = np.array([x["dif"] for x in res["referencias"][ref]["diferencias"]])
        (osm, osr), (m, b, _) = stats.probplot(d, dist="norm")
        ax.scatter(osm, osr, s=16, color="#0B6E64")
        ax.plot(osm, m * np.asarray(osm) + b, color="#999999", lw=1)
        sp = res["referencias"][ref]["total"]["shapiro_p"]
        ax.set_title(f"Sistema − {ref}: Q-Q normal (Shapiro p = {_p(sp)})", fontsize=10)
        ax.set_xlabel("cuantil teórico normal")
        ax.set_ylabel("diferencia observada (bps)")
        ax.grid(alpha=0.3)
    fig.tight_layout()
    rutas["qq"] = out / "qq_diferencias.png"
    fig.savefig(rutas["qq"], dpi=130)
    plt.close(fig)
    # 2) bosque: diferencia media e IC por grupo
    filas = []
    for ref in refs:
        r = res["referencias"][ref]
        filas.append((f"{ref} · total", r["total"]))
        if len(r["por_escenario"]) > 1:
            filas += [(f"{ref} · liquidez {e}", g) for e, g in r["por_escenario"].items()]
        clave_sin = next(k for k in r if k.startswith("sin_"))
        filas.append((f"{ref} · {clave_sin.replace('_', ' ')}", r[clave_sin]))
    fig, ax = plt.subplots(figsize=(7.5, 0.45 * len(filas) + 1.2))
    for i, (et, g) in enumerate(filas):
        y = len(filas) - 1 - i
        lo, hi = g["ic95"]
        color = "#0B6E64" if hi is not None and hi < 0 else "#7A7A7A"
        ax.plot([lo, hi], [y, y], color=color, lw=2)
        ax.plot(g["dif_media"], y, "o", color=color)
        ax.text(hi + 2 if hi is not None else 0, y, f" {_f(g['dif_media'], 1)}  d={_f(g['d_cohen'])}", va="center", fontsize=8)
    ax.axvline(0, color="#C0392B", lw=1, ls="--")
    ax.set_xlim(right=max([g["ic95"][1] or 0 for _, g in filas] + [0]) + 30)   # espacio para los rótulos
    ax.set_yticks(range(len(filas)))
    ax.set_yticklabels([et for et, _ in filas][::-1], fontsize=9)
    ax.set_xlabel("sistema − referencia (bps); a la izquierda del 0 = el sistema cuesta menos")
    ax.set_title("Diferencia media con IC 95 % (verde: el IC no toca el 0)", fontsize=10)
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    rutas["bosque"] = out / "bosque_diferencias.png"
    fig.savefig(rutas["bosque"], dpi=130)
    plt.close(fig)
    # 3) diferencias por escenario (cajas + puntos)
    fig, axes = plt.subplots(1, len(refs), figsize=(5.2 * len(refs), 4.2), squeeze=False, sharey=True)
    for ax, ref in zip(axes[0], refs):
        dd = pd.DataFrame(res["referencias"][ref]["diferencias"])
        esc = _orden_escenarios(dd["escenario"].unique())
        datos = [dd.loc[dd["escenario"] == e, "dif"].to_numpy() for e in esc]
        ax.boxplot(datos, widths=0.5, showfliers=False)
        ax.set_xticks(range(1, len(esc) + 1))
        ax.set_xticklabels(esc)   # sin `labels=`/`tick_labels=`: cambia de nombre entre versiones de matplotlib
        for k, v in enumerate(datos, start=1):
            ax.scatter(np.full(len(v), k) + np.random.default_rng(k).uniform(-0.12, 0.12, len(v)), v, s=12,
                       color="#0B6E64", alpha=0.7)
        ax.axhline(0, color="#C0392B", lw=1, ls="--")
        ax.set_title(f"Sistema − {ref} por liquidez", fontsize=10)
        ax.set_xlabel("escenario de liquidez")
        ax.grid(axis="y", alpha=0.3)
    axes[0][0].set_ylabel("diferencia por corrida (bps); bajo 0 = sistema más barato")
    fig.tight_layout()
    rutas["por_escenario"] = out / "diferencias_por_escenario.png"
    fig.savefig(rutas["por_escenario"], dpi=130)
    plt.close(fig)
    return rutas


def main(argv: Optional[Sequence[str]] = None) -> Dict:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--entradas", nargs="+", required=True, help="carpetas o archivos JSON, o un corridas.csv de la 3.2.2")
    ap.add_argument("--sistema", default="PPO_sistema")
    ap.add_argument("--penalizacion-bps", type=float, default=None, help="costo ajustado por lo no ejecutado (como la 3.2.2)")
    ap.add_argument("--excluir", nargs="*", default=["MO-06"], help="órdenes para el análisis de robustez")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--out-md", default=None)
    ap.add_argument("--titulo", default="Comparación estadística 3.2.3")
    ap.add_argument("--sin-figuras", action="store_true")
    args = ap.parse_args(argv)

    df = cargar(args.entradas)
    if df.empty:
        sys.exit("No hay corridas válidas en las entradas.")
    if "costo" not in df.columns or args.penalizacion_bps is not None:
        df["costo"] = costo(df, args.penalizacion_bps)
    res = analizar(df, args.sistema, args.excluir)
    if not res["referencias"]:
        sys.exit(f"No hay pares de `{args.sistema}` con TWAP o VWAP.")
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "comparacion_3_2_3.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=float),
                                                 encoding="utf-8")
    fuentes = "Entradas: " + ", ".join(f"`{e}`" for e in args.entradas) + "."
    md = informe(res, args.titulo, fuentes)
    (out / "tabla_p_valores.md").write_text(md, encoding="utf-8")
    if args.out_md:
        Path(args.out_md).write_text(md, encoding="utf-8")
    if not args.sin_figuras:
        res["figuras"] = {k: str(v) for k, v in figuras(res, out).items()}
    try:
        print(md)
    except UnicodeEncodeError:   # consola de Windows sin UTF-8
        print(md.encode("ascii", "replace").decode())
    return res


if __name__ == "__main__":
    main()
