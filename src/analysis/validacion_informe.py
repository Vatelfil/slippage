"""Informe en markdown de la validacion formal 2.2.5 (PS).

Elaborado por PS con apoyo de Claude Code; pendiente de revision por BF.

Las cifras salen directo de los resultados de `validacion_formal.analizar_modo`
(no se transcribe ningun numero a mano) y las frases de lectura se calculan a
partir de ellos: este modulo no inventa conclusiones.
"""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np

from src.analysis.validacion_formal import EFECTO_MAX, TRAMOS


def _f(x, d: int = 3) -> str:
    """Numero con coma decimal; guion largo si no hay dato."""
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "—"
    txt = f"{x:.{d}f}"
    if float(txt) == 0:
        txt = txt.lstrip("-")
    return txt.replace(".", ",")


def _p(x) -> str:
    if x is None:
        return "—"
    return "< 0,0001" if x < 1e-4 else _f(x, 4 if x < 0.01 else 3)


def _si(b) -> str:
    return "—" if b is None else ("sí" if b else "no")


def render_markdown(despues: Dict, antes: Optional[Dict], comparacion: Optional[List[Dict]],
                    metadata: Dict) -> str:
    L: List[str] = []
    ap = L.append
    v = despues["veredicto"]
    ap("# Validación formal del simulador (tarea 2.2.5)")
    ap("")
    ap("**Elaborado por:** Paolo Sepúlveda (PS) con apoyo de Claude Code. **Pendiente de revisión por:** Benjamín Farias (BF), responsable de la calibración de `rmsc04` (2.2.4).")
    ap(f"**Activo:** {metadata.get('ticker', 'FALABELLA')} · **Snapshot real:** {metadata.get('snapshot', '2026-08-23')} · "
       f"**Semillas simuladas:** {metadata.get('semillas', '—')} por tramo · **Fecha:** {metadata.get('fecha', '—')}")
    ap("")
    ap("## 1. Veredicto")
    ap("")
    ap(f"**{v['texto']}.** Criterios fijados antes de ver los datos:")
    ap("")
    ap("| Criterio | Qué exige | Cumple |")
    ap("|---|---|:---:|")
    ap(f"| A. Literal del plan | Todos los p de KS y Mann–Whitney, por tramo, mayores que α = {_f(despues['alpha'], 2)} | {_si(v['A_literal_plan'])} |")
    ap(f"| B. Forma | KS con muestras estandarizadas, p > α en los 3 tramos | {_si(v['B_forma'])} |")
    ap(f"| C. Efecto | \\|g de Hedges\\| < {_f(EFECTO_MAX, 1)} en los 3 tramos | {_si(v['C_efecto_pequeno'])} |")
    ap(f"| D. Patrón | Volatilidad máxima en la apertura y volumen por vela creciente | {_si(v['D_patron'])} |")
    ap("")
    rech = [t for t in TRAMOS if despues["por_tramo"][t]["ks"].get("rechaza")]
    ap(f"- El KS crudo rechaza en {len(rech)} de 3 tramos" + (f" ({', '.join(rech)})." if rech else "."))
    ap("")

    ap("## 2. KS de 2 muestras sobre los retornos de 5 min")
    ap("")
    ap("| Tramo | n sim | n real | D | p | D crítico | D / D crít. | Rechaza | p (estandarizado) |")
    ap("|---|---:|---:|---:|---:|---:|---:|:---:|---:|")
    for t in TRAMOS:
        k = despues["por_tramo"][t]["ks"]
        ap(f"| {t} | {k['n_sim']} | {k['n_real']} | {_f(k['D'])} | {_p(k['p'])} | {_f(k['D_crit'])} | "
           f"{_f(k['D_ratio'], 2)} | {_si(k['rechaza'])} | {_p((k.get('estandarizado') or {}).get('p'))} |")
    ap("")
    ap("## 3. Escala de los retornos: Mann–Whitney sobre |retorno| y Brown–Forsythe")
    ap("")
    ap("| Tramo | p Mann–Whitney | g de Hedges | Efecto | Mediana \\|r\\| sim (bps) | Mediana \\|r\\| real (bps) | p Brown–Forsythe | Desvío sim / real |")
    ap("|---|---:|---:|---|---:|---:|---:|---:|")
    for t in TRAMOS:
        m, b = despues["por_tramo"][t]["mannwhitney_abs"], despues["por_tramo"][t]["brown_forsythe"]
        ms, mr = m.get("mediana_abs_sim"), m.get("mediana_abs_real")
        ap(f"| {t} | {_p(m.get('p'))} | {_f(m.get('g'), 2)} | {m.get('efecto', '—')} | "
           f"{_f(None if ms is None else ms * 1e4, 1)} | {_f(None if mr is None else mr * 1e4, 1)} | "
           f"{_p(b.get('p'))} | {_f(b.get('razon_desvios'), 2)} |")
    ap("")
    ap("## 4. Valores por semilla frente al valor real")
    ap("")
    ap("El valor real es un único número, así que cada fila compara las semillas contra ese objetivo con Wilcoxon de 1 muestra.")
    ap("")
    ap("| Tramo | Magnitud | Media sim | Objetivo real | Sesgo (%) | IC 95 % de la media | p |")
    ap("|---|---|---:|---:|---:|---|---:|")
    nombres = (("volatilidad_vs_objetivo", "Volatilidad 5 min (bps)", 1),
               ("volumen_vela_vs_objetivo", "Volumen mediano por vela", 0),
               ("participacion_vs_objetivo", "Participación de volumen", 3))
    for t in TRAMOS:
        for key, nombre, dec in nombres:
            r = despues["por_tramo"][t][key]
            ic = r.get("ic95")
            ic_txt = ("[" + _f(ic[0], dec) + "; " + _f(ic[1], dec) + "]") if ic else "—"
            ap(f"| {t} | {nombre} | {_f(r.get('media'), dec)} | {_f(r.get('objetivo'), dec)} | "
               f"{_f(r.get('sesgo_pct'), 1)} | {ic_txt} | {_p(r.get('p'))} |")
    ap("")
    ap("## 5. Patrón entre tramos (Kruskal–Wallis sobre |retorno|)")
    ap("")
    ap("| Fuente | H | p | Mediana \\|r\\| apertura (bps) | media jornada | cierre |")
    ap("|---|---:|---:|---:|---:|---:|")
    for nombre in ("real", "simulado"):
        k = despues["patron_entre_tramos"].get(nombre)
        if k:
            m = k["medianas_abs"]
            ap(f"| {nombre} | {_f(k['H'], 1)} | {_p(k['p'])} | {_f(m['apertura'] * 1e4, 1)} | "
               f"{_f(m['media_jornada'] * 1e4, 1)} | {_f(m['cierre'] * 1e4, 1)} |")
    rk = despues["rankings"]
    ap("")
    ap(f"- Volatilidad máxima en la apertura: **{_si(rk['volatilidad_maxima_en_apertura'])}** (por construcción: `fund_vol` se fija por tramo).")
    ap(f"- Volumen por vela creciente de apertura a cierre: **{_si(rk['volumen_vela_creciente'])}**.")
    ap("")
    ap("## 6. Spread (sin prueba de hipótesis)")
    ap("")
    ap("El spread simulado es cotizado y los reales son proxies de velas de 5 min, así que solo se verifica si cae dentro del rango de los cuatro proxies.")
    ap("")
    ap("| Tramo | Spread simulado (bps) | Rango real (bps) | Dentro | Veces por debajo del mínimo real |")
    ap("|---|---:|---|:---:|---:|")
    for t in TRAMOS:
        s = despues["por_tramo"][t]["spread"]
        rg = s.get("rango_real_bps")
        rg_txt = ("[" + _f(rg[0], 1) + "; " + _f(rg[1], 1) + "]") if rg else "—"
        ap(f"| {t} | {_f(s.get('simulado_bps'), 2)} | {rg_txt} | {_si(s.get('dentro'))} | {_f(s.get('veces_bajo_el_minimo'), 0)} |")
    ap("")
    if comparacion:
        ap("## 7. Antes y después de calibrar")
        ap("")
        ap("| Tramo | D antes | p antes | D después | p después | g antes | g después | ¿D baja? |")
        ap("|---|---:|---:|---:|---:|---:|---:|:---:|")
        for f in comparacion:
            ap(f"| {f['tramo']} | {_f(f['D_antes'])} | {_p(f['p_antes'])} | {_f(f['D_despues'])} | "
               f"{_p(f['p_despues'])} | {_f(f['g_antes'], 2)} | {_f(f['g_despues'], 2)} | {_si(f['mejora_D'])} |")
        ap("")
        if antes is not None:
            ap(f"- Veredicto del simulador de fábrica: {antes['veredicto']['texto']}.")
            ap(f"- Veredicto del simulador calibrado: {despues['veredicto']['texto']}.")
            ap("")
    ap("## 8. Corrección por comparaciones múltiples (Holm)")
    ap("")
    ap("| Prueba | p crudo | p ajustado (Holm) | ¿Rechaza tras ajustar? |")
    ap("|---|---:|---:|:---:|")
    for k in sorted(despues["p_crudos"]):
        pc, pa = despues["p_crudos"][k], despues["p_ajustados_holm"][k]
        ap(f"| {k.replace(':', ' · ')} | {_p(pc)} | {_p(pa)} | {_si(None if pa is None else pa < despues['alpha'])} |")
    ap("")
    ap("## 9. Limitaciones")
    ap("")
    ap("- Las pruebas por semilla (sección 4) tienen poca potencia con pocas semillas; el KS y Mann–Whitney sobre la muestra agrupada tienen mucha: con miles de retornos rechazan diferencias pequeñas. Por eso se reportan también el tamaño de efecto y el D/D crítico.")
    ap("- Los retornos reales y simulados vienen agrupados de varios días: no son estrictamente independientes.")
    ap("- El valor real de volatilidad, volumen por vela y participación es un único número (no hay muestra diaria real versionada), por eso se usa una prueba de 1 muestra.")
    ap("- El spread no admite prueba de hipótesis (magnitudes distintas) y el simulador queda decenas de veces por debajo de los proxies reales; el IS absoluto en ABIDES queda subestimado, aunque la comparación entre políticas sigue siendo válida.")
    ap("- Un solo activo (FALABELLA) y un solo régimen (previo a la transición del IPSA a MSCI, 1 de septiembre de 2026).")
    ap("")
    ap("🤖 Generado con [Claude Code](https://claude.com/claude-code)")
    return "\n".join(L) + "\n"
