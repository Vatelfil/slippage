"""Pruebas formales de la validacion del simulador -- tarea 2.2.5 (PS).

Elaborado por PS con apoyo de Claude Code; pendiente de revision por BF.

Compara el mercado simulado (RMSC04 de ABIDES-Gym, ya calibrado o de fabrica)
contra el mercado real del IPSA con las pruebas que pide el plan: KS,
Mann-Whitney U, Kruskal-Wallis, tamano de efecto (d de Cohen / g de Hedges) y
correccion de Holm por comparaciones multiples.

Que se compara con que (el spread simulado y el real NO miden lo mismo, asi
que no se le aplica una prueba de hipotesis):

    retornos de 5 min (muestra agrupada)  ->  KS (crudo y estandarizado),
                                              Mann-Whitney sobre |retorno|,
                                              Brown-Forsythe (varianza)
    valores por semilla (volatilidad,     ->  Wilcoxon de 1 muestra contra el
    volumen por vela, participacion)          valor objetivo real (el real es
                                              un unico numero, no una muestra)
    patron entre tramos                   ->  Kruskal-Wallis en cada fuente
    spread cotizado simulado              ->  rango de los 4 proxies reales

Veredicto fijado ANTES de ver datos:
    A (literal del plan): todos los p de KS crudo y Mann-Whitney, por tramo,
      mayores que alpha.
    B (forma): KS estandarizado con p > alpha en todos los tramos.
    C (efecto): |g de Hedges| de Mann-Whitney menor que 0,5 en todos los tramos.
    D (patron): la volatilidad maxima cae en la apertura y el volumen por vela
      crece de apertura a cierre, igual que en los datos reales.
El simulador se declara VALIDO solo si se cumple A; B, C y D se reportan para
interpretar por que pasa o no pasa.
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence

import numpy as np
from scipy import stats

from src.analysis.execution_metrics import compare_groups_kruskal

TRAMOS = ("apertura", "media_jornada", "cierre")
ALPHA = 0.05
EFECTO_MAX = 0.5


# ---------------------------------------------------------------------------
# Piezas basicas
# ---------------------------------------------------------------------------

def _clean(x: Sequence[float]) -> np.ndarray:
    a = np.asarray(list(x), dtype=float)
    return a[np.isfinite(a)]


def ks_d_crit(n: int, m: int, alpha: float = ALPHA) -> float:
    """Valor critico asintotico del KS de 2 muestras."""
    c = math.sqrt(-0.5 * math.log(alpha / 2.0))
    return c * math.sqrt((n + m) / (n * m))


def ks_test(sim: Sequence[float], real: Sequence[float], alpha: float = ALPHA) -> Dict:
    """KS de 2 muestras sobre los retornos (D, p, D critico, D/Dcrit) y sobre
    las muestras estandarizadas (media 0, desvio 1), que compara solo la forma."""
    s, r = _clean(sim), _clean(real)
    out: Dict = {"n_sim": int(len(s)), "n_real": int(len(r)), "alpha": alpha}
    if len(s) < 5 or len(r) < 5:
        out.update({"D": None, "p": None, "D_crit": None, "D_ratio": None, "rechaza": None, "estandarizado": None})
        return out
    d_crit = ks_d_crit(len(s), len(r), alpha)
    res = stats.ks_2samp(s, r)
    out.update({"D": float(res.statistic), "p": float(res.pvalue), "D_crit": float(d_crit),
                "D_ratio": float(res.statistic / d_crit), "rechaza": bool(res.pvalue < alpha)})
    if s.std() > 0 and r.std() > 0:
        z = stats.ks_2samp((s - s.mean()) / s.std(), (r - r.mean()) / r.std())
        out["estandarizado"] = {"D": float(z.statistic), "p": float(z.pvalue),
                                "D_ratio": float(z.statistic / d_crit), "rechaza": bool(z.pvalue < alpha)}
    else:
        out["estandarizado"] = None
    return out


def hedges_g(a: Sequence[float], b: Sequence[float]) -> float:
    """g de Hedges (d de Cohen con correccion de muestra chica), muestras
    independientes. Positivo si la media de `a` es mayor que la de `b`."""
    a, b = _clean(a), _clean(b)
    n1, n2 = len(a), len(b)
    if n1 < 2 or n2 < 2:
        return float("nan")
    sp = math.sqrt(((n1 - 1) * a.var(ddof=1) + (n2 - 1) * b.var(ddof=1)) / (n1 + n2 - 2))
    if sp == 0:
        return 0.0
    d = (a.mean() - b.mean()) / sp
    j = 1.0 - 3.0 / (4.0 * (n1 + n2) - 9.0)
    return float(d * j)


def interpretar_efecto(g: float) -> str:
    """Escala convencional de Cohen (1988) para |d|."""
    if g is None or not np.isfinite(g):
        return "sin dato"
    a = abs(g)
    return "trivial" if a < 0.2 else "pequeno" if a < 0.5 else "mediano" if a < 0.8 else "grande"


def mannwhitney_abs(sim: Sequence[float], real: Sequence[float]) -> Dict:
    """Mann-Whitney U sobre |retorno| (escala de los retornos, es decir su
    volatilidad). Tamano de efecto: g de Hedges sobre |retorno| y correlacion
    biserial de rangos."""
    s, r = np.abs(_clean(sim)), np.abs(_clean(real))
    if len(s) < 5 or len(r) < 5:
        return {"U": None, "p": None, "g": None, "rank_biserial": None, "efecto": "sin dato"}
    res = stats.mannwhitneyu(s, r, alternative="two-sided")
    g = hedges_g(s, r)
    return {"U": float(res.statistic), "p": float(res.pvalue), "g": g, "efecto": interpretar_efecto(g),
            "rank_biserial": float(1.0 - 2.0 * res.statistic / (len(s) * len(r))),
            "mediana_abs_sim": float(np.median(s)), "mediana_abs_real": float(np.median(r))}


def brown_forsythe(sim: Sequence[float], real: Sequence[float]) -> Dict:
    """Igualdad de varianzas (Levene con mediana = Brown-Forsythe)."""
    s, r = _clean(sim), _clean(real)
    if len(s) < 5 or len(r) < 5:
        return {"W": None, "p": None, "razon_desvios": None}
    res = stats.levene(s, r, center="median")
    return {"W": float(res.statistic), "p": float(res.pvalue),
            "razon_desvios": float(s.std(ddof=1) / r.std(ddof=1))}


def contra_objetivo(valores: Sequence[float], objetivo: Optional[float]) -> Dict:
    """Valores por semilla contra el valor real (un unico numero): sesgo
    relativo, IC95 % de la media y Wilcoxon de 1 muestra."""
    v = _clean(valores)
    out: Dict = {"n": int(len(v)), "objetivo": objetivo}
    if len(v) == 0 or objetivo is None or not np.isfinite(objetivo):
        out.update({"media": None, "mediana": None, "sesgo_pct": None, "ic95": None, "p": None})
        return out
    out.update({"media": float(v.mean()), "mediana": float(np.median(v)),
                "sesgo_pct": float((v.mean() - objetivo) / objetivo * 100.0) if objetivo else None})
    if len(v) >= 3 and v.std(ddof=1) > 0:
        se = v.std(ddof=1) / math.sqrt(len(v))
        t = stats.t.ppf(0.975, len(v) - 1)
        out["ic95"] = [float(v.mean() - t * se), float(v.mean() + t * se)]
    else:
        out["ic95"] = None
    dif = v - objetivo
    if len(v) >= 6 and np.any(dif != 0):
        out["p"] = float(stats.wilcoxon(dif).pvalue)
    else:
        out["p"] = None
    return out


def spread_en_rango(valor_bps: Optional[float], proxies_bps: Sequence[Optional[float]]) -> Dict:
    """El spread simulado es un spread cotizado y los reales son proxies de
    velas de 5 min: no se hace prueba de hipotesis, solo se mira si cae en el
    rango [min, max] de los proxies."""
    px = [p for p in proxies_bps if p is not None and np.isfinite(p)]
    if valor_bps is None or not np.isfinite(valor_bps) or not px:
        return {"simulado_bps": valor_bps, "rango_real_bps": None, "dentro": None, "veces_bajo_el_minimo": None}
    lo, hi = min(px), max(px)
    return {"simulado_bps": float(valor_bps), "rango_real_bps": [float(lo), float(hi)],
            "dentro": bool(lo <= valor_bps <= hi),
            "veces_bajo_el_minimo": float(lo / valor_bps) if valor_bps > 0 and valor_bps < lo else None}


def holm(pvalores: Dict[str, Optional[float]]) -> Dict[str, Optional[float]]:
    """Valores p ajustados por Holm-Bonferroni. Los None se ignoran."""
    items = [(k, p) for k, p in pvalores.items() if p is not None]
    items.sort(key=lambda kv: kv[1])
    m = len(items)
    ajustado: Dict[str, Optional[float]] = {k: None for k in pvalores}
    corrida = 0.0
    for i, (k, p) in enumerate(items):
        corrida = max(corrida, min(1.0, (m - i) * p))
        ajustado[k] = corrida
    return ajustado


# ---------------------------------------------------------------------------
# Extraccion de muestras desde los resultados de las corridas
# ---------------------------------------------------------------------------

def _corridas_ok(runs: Dict, tramo: str) -> List[Dict]:
    cs = runs.get(tramo, {}).get("corridas", {})
    return [c["momentos"] for c in cs.values() if "momentos" in c]


def retornos_simulados(runs: Dict) -> Dict[str, List[float]]:
    """Retornos de 5 min agrupados (todas las semillas) por tramo, tomados del
    bloque del propio tramo de cada corrida (su config propia)."""
    out: Dict[str, List[float]] = {}
    for t in TRAMOS:
        rets: List[float] = []
        for m in _corridas_ok(runs, t):
            blk = m.get(t, {})
            if blk.get("completo"):
                rets.extend(blk.get("retornos_5min", []))
        out[t] = rets
    return out


def valores_por_semilla(runs: Dict) -> Dict[str, Dict[str, List[float]]]:
    """Un valor por semilla y tramo: volatilidad (bps) y spread mediano de las
    corridas del propio tramo; volumen mediano por vela y participacion de las
    corridas de dia completo (tramo cierre), como hace la 2.2.4."""
    out = {t: {"volatilidad_bps": [], "spread_mediano_bps": [], "volumen_mediano_vela": [],
               "participacion_volumen": []} for t in TRAMOS}
    for t in TRAMOS:
        for m in _corridas_ok(runs, t):
            blk = m.get(t, {})
            if not blk.get("completo"):
                continue
            r = np.asarray(blk.get("retornos_5min", []), dtype=float)
            if len(r) > 1:
                out[t]["volatilidad_bps"].append(float(r.std() * 1e4))
            out[t]["spread_mediano_bps"].append(blk.get("spread_mediano_bps", float("nan")))
    for m in _corridas_ok(runs, TRAMOS[-1]):
        for t in TRAMOS:
            blk = m.get(t, {})
            if blk.get("completo"):
                out[t]["volumen_mediano_vela"].append(blk.get("volumen_mediano_vela", float("nan")))
                if blk.get("participacion_volumen") is not None:
                    out[t]["participacion_volumen"].append(blk["participacion_volumen"])
    return out


# ---------------------------------------------------------------------------
# Analisis completo de un modo ("despues" o "antes")
# ---------------------------------------------------------------------------

def _ranking_desc(valores: Dict[str, Optional[float]]) -> Optional[List[str]]:
    if any(v is None or not np.isfinite(v) for v in valores.values()):
        return None
    return sorted(valores, key=lambda t: -valores[t])


def analizar_modo(real_returns: Dict[str, Sequence[float]], runs: Dict,
                  objetivos_por_tramo: Dict[str, Dict], alpha: float = ALPHA) -> Dict:
    """Aplica todas las pruebas a un modo y arma el veredicto."""
    sim_rets = retornos_simulados(runs)
    por_semilla = valores_por_semilla(runs)
    res: Dict = {"alpha": alpha, "por_tramo": {}}
    pvals: Dict[str, Optional[float]] = {}

    for t in TRAMOS:
        obj = objetivos_por_tramo.get(t, {})
        ks = ks_test(sim_rets[t], real_returns[t], alpha)
        mw = mannwhitney_abs(sim_rets[t], real_returns[t])
        bf = brown_forsythe(sim_rets[t], real_returns[t])
        vol = contra_objetivo(por_semilla[t]["volatilidad_bps"], obj.get("volatilidad_bps"))
        vvela = contra_objetivo(por_semilla[t]["volumen_mediano_vela"], obj.get("volumen_mediano_vela"))
        part = contra_objetivo(por_semilla[t]["participacion_volumen"], obj.get("participacion_volumen_dia"))
        spread_med = float(np.nanmedian(por_semilla[t]["spread_mediano_bps"])) if por_semilla[t]["spread_mediano_bps"] else None
        spr = spread_en_rango(spread_med, [obj.get(k) for k in ("spread_roll_bps", "spread_hl_bps", "spread_cs_bps", "spread_ar_bps")])
        res["por_tramo"][t] = {"ks": ks, "mannwhitney_abs": mw, "brown_forsythe": bf,
                               "volatilidad_vs_objetivo": vol, "volumen_vela_vs_objetivo": vvela,
                               "participacion_vs_objetivo": part, "spread": spr,
                               "n_semillas": len(por_semilla[t]["volatilidad_bps"])}
        pvals[f"{t}:ks"] = ks.get("p")
        pvals[f"{t}:ks_estandarizado"] = (ks.get("estandarizado") or {}).get("p")
        pvals[f"{t}:mannwhitney"] = mw.get("p")
        pvals[f"{t}:brown_forsythe"] = bf.get("p")
        pvals[f"{t}:volatilidad"] = vol.get("p")
        pvals[f"{t}:volumen_vela"] = vvela.get("p")
        pvals[f"{t}:participacion"] = part.get("p")

    res["p_ajustados_holm"] = holm(pvals)
    res["p_crudos"] = pvals

    # patron entre tramos (Kruskal-Wallis en cada fuente)
    patron: Dict = {}
    for nombre, fuente in (("real", real_returns), ("simulado", sim_rets)):
        muestras = {t: np.abs(_clean(fuente[t])) for t in TRAMOS}
        if all(len(v) >= 3 for v in muestras.values()):
            kw = compare_groups_kruskal(muestras, alpha)
            patron[nombre] = {"H": kw["statistic"], "p": kw["p_value"], "significativo": kw["significant"],
                              "medianas_abs": {t: float(np.median(muestras[t])) for t in TRAMOS},
                              "post_hoc": kw["post_hoc"]}
    res["patron_entre_tramos"] = patron

    # rankings (criterio D)
    vol_sim = {t: np.mean(por_semilla[t]["volatilidad_bps"]) if por_semilla[t]["volatilidad_bps"] else None for t in TRAMOS}
    vvela_sim = {t: np.mean(por_semilla[t]["volumen_mediano_vela"]) if por_semilla[t]["volumen_mediano_vela"] else None for t in TRAMOS}
    rank_vol = _ranking_desc(vol_sim)
    vol_max_apertura = bool(rank_vol and rank_vol[0] == TRAMOS[0])
    vvela_creciente = None
    if all(v is not None for v in vvela_sim.values()):
        vvela_creciente = bool(vvela_sim[TRAMOS[0]] < vvela_sim[TRAMOS[1]] < vvela_sim[TRAMOS[2]])
    res["rankings"] = {"volatilidad_sim_bps": vol_sim, "ranking_volatilidad_desc": rank_vol,
                       "volatilidad_maxima_en_apertura": vol_max_apertura,
                       "volumen_vela_sim": vvela_sim, "volumen_vela_creciente": vvela_creciente}

    # veredicto
    ks_ok = [res["por_tramo"][t]["ks"].get("p") for t in TRAMOS]
    mw_ok = [res["por_tramo"][t]["mannwhitney_abs"].get("p") for t in TRAMOS]
    kse_ok = [(res["por_tramo"][t]["ks"].get("estandarizado") or {}).get("p") for t in TRAMOS]
    g_ok = [res["por_tramo"][t]["mannwhitney_abs"].get("g") for t in TRAMOS]

    def todos(ps, f):
        return None if any(p is None for p in ps) else bool(all(f(p) for p in ps))

    A = todos(ks_ok + mw_ok, lambda p: p > alpha)
    B = todos(kse_ok, lambda p: p > alpha)
    C = todos(g_ok, lambda g: abs(g) < EFECTO_MAX)
    D = bool(vol_max_apertura and vvela_creciente) if vvela_creciente is not None else None
    res["veredicto"] = {
        "A_literal_plan": A, "B_forma": B, "C_efecto_pequeno": C, "D_patron": D,
        "simulador_valido": A,
        "texto": ("VÁLIDO según el criterio del plan (todos los p > α)" if A
                  else "NO VÁLIDO según el criterio del plan" if A is not None else "sin datos suficientes"),
    }
    return res


def comparar_antes_despues(antes: Dict, despues: Dict) -> List[Dict]:
    """Tabla por tramo con D, p y efecto antes y despues de calibrar."""
    filas = []
    for t in TRAMOS:
        a, d = antes["por_tramo"][t], despues["por_tramo"][t]
        filas.append({
            "tramo": t,
            "D_antes": a["ks"].get("D"), "p_antes": a["ks"].get("p"),
            "D_despues": d["ks"].get("D"), "p_despues": d["ks"].get("p"),
            "g_antes": a["mannwhitney_abs"].get("g"), "g_despues": d["mannwhitney_abs"].get("g"),
            "mejora_D": (a["ks"].get("D") is not None and d["ks"].get("D") is not None
                         and d["ks"]["D"] < a["ks"]["D"]),
        })
    return filas


# ---------------------------------------------------------------------------
# Figuras
# ---------------------------------------------------------------------------

def figuras(real_returns: Dict[str, Sequence[float]], sim_despues: Dict[str, Sequence[float]],
            sim_antes: Optional[Dict[str, Sequence[float]]], out_png: str) -> str:
    """CDF empirica de los retornos de 5 min (real, simulado antes y despues)
    por tramo, y diagrama de cajas de |retorno|."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 3, figsize=(14, 7.5))
    for j, t in enumerate(TRAMOS):
        ax = axes[0, j]
        series = [("Real", real_returns[t], "#1E2761"), ("Simulado, calibrado", sim_despues[t], "#F2A900")]
        if sim_antes is not None:
            series.append(("Simulado, de fabrica", sim_antes[t], "#8FA3D9"))
        for nombre, datos, color in series:
            d = np.sort(_clean(datos))
            if len(d):
                ax.plot(d * 1e4, np.arange(1, len(d) + 1) / len(d), label=nombre, color=color, lw=1.8)
        ax.set_title(t.replace("_", " ").capitalize())
        ax.set_xlabel("retorno de 5 min (bps)")
        ax.set_ylabel("CDF")
        ax.set_xlim(-150, 150)
        if j == 0:
            ax.legend(fontsize=8)
        bx = axes[1, j]
        datos = [np.abs(_clean(real_returns[t])) * 1e4, np.abs(_clean(sim_despues[t])) * 1e4]
        etiquetas = ["Real", "Calibrado"]
        if sim_antes is not None:
            datos.append(np.abs(_clean(sim_antes[t])) * 1e4)
            etiquetas.append("De fabrica")
        bx.boxplot(datos, tick_labels=etiquetas, showfliers=False)
        bx.set_ylabel("|retorno| (bps)")
    fig.suptitle("Validacion formal 2.2.5: retornos de 5 min, real frente a simulado (FALABELLA)")
    fig.tight_layout()
    fig.savefig(out_png, dpi=140, bbox_inches="tight")
    plt.close(fig)
    return out_png
