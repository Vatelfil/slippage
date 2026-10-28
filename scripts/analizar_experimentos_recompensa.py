"""Resumen de la matriz de experimentos de recompensa (BORRADOR de PS).

Lee los JSON que deja `scripts/experimentos_recompensa_ps.py` en una carpeta de etapa y arma el informe, la figura y un
JSON con el veredicto por variante.

Criterio para dar por buena una red (se aplica a cada red, en el escenario de 5.000 acciones y ventana de 15 min, con la
política muestreada como se entrena):
  1. cumple la orden por su cuenta (cumplimiento voluntario >= 90 %: casi nada se liquida a la fuerza),
  2. no se queda esperando (pasos en espera <= 50 %),
  3. cuesta menos que su propia red inicial muestreando (diferencia media < 0 y Wilcoxon pareado con p < 0,05).
Una variante «funciona» si al menos 4 de sus 5 redes cumplen los tres puntos. La referencia a la que se quiere llegar es la
mejor heurística (TWAP con órdenes límite). Las mismas métricas se miden para todas las filas con la misma regla: lo que no
se compra voluntariamente se liquida a mercado, así el costo de dejar cosas pendientes siempre cuenta.

    python scripts/analizar_experimentos_recompensa.py --dir data/experimentos_recompensa/etapa_A \
        --out-md docs/experimentos_recompensa_A_PS.md --out-png data/analysis/experimentos_recompensa_A.png
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

ESCENARIO_CLAVE = "q5000_v15"
CUMPL_MIN, ESPERA_MAX, P_MAX, REDES_MIN = 0.90, 0.50, 0.05, 4


def _f(x: Optional[float], d: int = 2) -> str:
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "—"
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def cargar(directorio: Path) -> Dict[str, List[Dict]]:
    """Corridas agrupadas por variante, ordenadas por semilla de red."""
    out: Dict[str, List[Dict]] = {}
    for f in sorted(glob.glob(str(directorio / "*_s*.json"))):
        r = json.load(open(f, encoding="utf-8"))
        out.setdefault(r["variante"], []).append(r)
    for v in out.values():
        v.sort(key=lambda r: r["semilla_red"])
    return out


def cumple_criterio(r: Dict, escenario: str = ESCENARIO_CLAVE) -> Dict:
    e = r["evaluacion"][escenario]
    red, ini = e["red_muestreada"], e["inicial_muestreada"]
    a, b = red["slippage_por_semilla"], ini["slippage_por_semilla"]
    d = [x - y for x, y in zip(a, b) if x is not None and y is not None and np.isfinite(x) and np.isfinite(y)]
    dif = float(np.mean(d)) if d else float("nan")
    p = float(stats.wilcoxon(d).pvalue) if len(d) > 5 and any(x != 0 for x in d) else float("nan")
    c1 = red["promedio"]["cumplimiento_voluntario"] >= CUMPL_MIN
    c2 = red["promedio"]["pct_espera"] <= ESPERA_MAX
    c3 = bool(np.isfinite(dif) and dif < 0 and np.isfinite(p) and p < P_MAX)
    return {"cumple_orden": bool(c1), "no_espera": bool(c2), "mejora_costo": c3, "todo": bool(c1 and c2 and c3),
            "dif_vs_inicial": dif, "p": p}


def resumen_variante(corridas: Sequence[Dict]) -> Dict:
    fila: Dict = {"n_redes": len(corridas), "descripcion": corridas[0]["descripcion"]}
    for esc in corridas[0]["evaluacion"]:
        def med(modo, k):
            v = [r["evaluacion"][esc][modo]["promedio"][k] for r in corridas]
            v = [x for x in v if x is not None and np.isfinite(x)]
            return float(np.mean(v)) if v else float("nan")
        fila[esc] = {"slippage": med("red_muestreada", "slippage_bps"), "cumpl_vol": med("red_muestreada", "cumplimiento_voluntario"),
                     "espera": med("red_muestreada", "pct_espera"), "slippage_inicial": med("inicial_muestreada", "slippage_bps"),
                     "slippage_argmax": med("red_argmax", "slippage_bps"), "cumpl_vol_argmax": med("red_argmax", "cumplimiento_voluntario")}
    crit = [cumple_criterio(r) for r in corridas]
    fila["criterio"] = {k: int(sum(c[k] for c in crit)) for k in ("cumple_orden", "no_espera", "mejora_costo", "todo")}
    # el mismo criterio en cada escenario: dice si la red sirve también con tamaños distintos al de entrenamiento
    fila["criterio_por_escenario"] = {esc: int(sum(cumple_criterio(r, esc)["todo"] for r in corridas)) for esc in corridas[0]["evaluacion"]}
    fila["dif_vs_inicial"] = float(np.nanmean([c["dif_vs_inicial"] for c in crit]))
    c = [r["curvas"] for r in corridas]
    fila["entrenamiento"] = {k: [float(np.nanmean([x[0][k] for x in c])), float(np.nanmean([x[-1][k] for x in c]))]
                             for k in ("retorno", "pct_espera", "pct_mercado", "pct_limite", "slippage_bps", "cumplimiento_voluntario")}
    fila["funciona"] = fila["criterio"]["todo"] >= REDES_MIN
    return fila


def elegir_mejor(res: Dict[str, Dict]) -> str:
    """Variante con más redes buenas; si empatan, la de menor diferencia frente a la red inicial."""
    return sorted(res, key=lambda v: (-res[v]["criterio"]["todo"], res[v]["dif_vs_inicial"]))[0]


def figura(res: Dict[str, Dict], ref: Dict, ruta: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    nombres = list(res)
    y = np.arange(len(nombres))
    esc = ESCENARIO_CLAVE
    fig, ax = plt.subplots(1, 3, figsize=(15, 1.6 + 0.42 * len(nombres)), sharey=True)
    ax[0].barh(y, [res[v][esc]["slippage"] for v in nombres], color="#534AB7")
    ref_esc = ref.get(esc, {})
    ini = float(np.mean([res[v][esc]["slippage_inicial"] for v in nombres]))
    ax[0].axvline(ini, color="#5F5E5A", ls="--", lw=1.2)
    ax[0].text(ini, -0.9, " red inicial", fontsize=8, color="#5F5E5A", va="bottom")
    if "twap_limit_medio" in ref_esc:
        t = ref_esc["twap_limit_medio"]["promedio"]["slippage_bps"]
        ax[0].axvline(t, color="#0F6E56", ls="--", lw=1.2)
        ax[0].text(t, len(nombres) - 0.4, "TWAP límite ", fontsize=8, color="#0F6E56", va="top", ha="right")
    valores = [res[v][esc]["slippage"] for v in nombres]
    ax[0].set_xlim(min(valores + [ini]) - 2, max(valores + [ini]) + 1.5)   # el eje no empieza en 0: lo que importa son unos bps
    ax[0].set_title("Costo (slippage, bps; menor es mejor)\n5.000 acciones, ventana de 15 min", fontsize=10)
    ax[1].barh(y, [100 * res[v][esc]["espera"] for v in nombres], color="#993C1D")
    ax[1].axvline(50, color="#5F5E5A", ls=":", lw=1)
    ax[1].set_title("Pasos en espera (%)", fontsize=10)
    ax[2].barh(y, [res[v]["criterio"]["todo"] for v in nombres], color="#0F6E56")
    ax[2].axvline(REDES_MIN, color="#5F5E5A", ls=":", lw=1)
    ax[2].set_xlim(0, 5.3)
    ax[2].set_title("Redes (de 5) que cumplen los tres criterios", fontsize=10)
    ax[0].set_yticks(y, nombres, fontsize=9)
    ax[0].invert_yaxis()
    for a in ax:
        a.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta, dpi=140)
    plt.close(fig)


def informe(res: Dict[str, Dict], ref: Dict, png_rel: str, etapa: str) -> str:
    esc_t = {"q1000_v15": "1.000 acciones, 15 min", "q5000_v15": "5.000 acciones, 15 min", "q20000_v15": "20.000 acciones, 15 min"}
    L = [f"# Experimentos de recompensa, etapa {etapa}", "",
         "**Elaborado por:** PS con apoyo de Claude Code (uso autorizado por la universidad). **Pendiente de revisión por:** BF (R_E) y MR (entrenamiento). "
         "Simulador de Poisson en el PC; 1.000 episodios por red y 5 semillas de red por variante; evaluación con 50 semillas nuevas.", "",
         f"![Resumen]({png_rel})", "",
         "Criterio para dar por buena una red (escenario de 5.000 acciones, política muestreada): (1) cumple la orden por su cuenta (≥ 90 % voluntario), "
         "(2) no se queda esperando (≤ 50 % de los pasos) y (3) cuesta menos que su propia red inicial (Wilcoxon pareado, p < 0,05). Una variante funciona si 4 de 5 redes lo cumplen.", "",
         "## 1. Qué cambia en cada variante", "", "| Variante | Qué cambia |", "|---|---|"]
    for v, r in res.items():
        L.append(f"| {v} | {r['descripcion']} |")
    L += ["", "## 2. Resultado por escenario (promedio de las 5 redes, política muestreada)", ""]
    for esc, tit in esc_t.items():
        if esc not in next(iter(res.values())):
            continue
        L += [f"### {tit}", "", "| Variante | Slippage (bps) | Red inicial (bps) | Cumplimiento voluntario | Pasos en espera |", "|---|---:|---:|---:|---:|"]
        for v, r in res.items():
            e = r[esc]
            L.append(f"| {v} | {_f(e['slippage'])} | {_f(e['slippage_inicial'])} | {_f(e['cumpl_vol'], 2)} | {_f(100 * e['espera'], 0)} % |")
        if esc in ref:
            for k, nombre in (("twap_limit_medio", "Referencia: TWAP con órdenes límite"), ("agresiva_market", "Referencia: mercado agresiva"),
                              ("esperar_siempre", "Referencia: esperar siempre")):
                if k in ref[esc]:
                    p = ref[esc][k]["promedio"]
                    L.append(f"| *{nombre}* | {_f(p['slippage_bps'])} | — | {_f(p['cumplimiento_voluntario'], 2)} | {_f(100 * p['pct_espera'], 0)} % |")
        L.append("")
    L += ["## 3. Criterio por variante", "",
          "| Variante | Redes que cumplen la orden | Redes que no esperan | Redes que bajan el costo | **Redes que cumplen los tres** | Diferencia media frente a la red inicial (bps) | ¿Funciona? |",
          "|---|---:|---:|---:|---:|---:|:---:|"]
    for v, r in res.items():
        c = r["criterio"]
        L.append(f"| {v} | {c['cumple_orden']} de {r['n_redes']} | {c['no_espera']} de {r['n_redes']} | {c['mejora_costo']} de {r['n_redes']} | "
                 f"**{c['todo']} de {r['n_redes']}** | {_f(r['dif_vs_inicial'])} | {'sí' if r['funciona'] else 'no'} |")
    L += ["", "### Redes que cumplen los tres criterios en cada escenario de evaluación", "",
          "| Variante | 1.000 acciones | 5.000 acciones | 20.000 acciones |", "|---|---:|---:|---:|"]
    for v, r in res.items():
        pe = r["criterio_por_escenario"]
        L.append(f"| {v} | {pe.get('q1000_v15', '—')} de {r['n_redes']} | {pe.get('q5000_v15', '—')} de {r['n_redes']} | {pe.get('q20000_v15', '—')} de {r['n_redes']} |")
    L += ["", "## 4. Qué pasó durante el entrenamiento (primer y último bloque de 100 episodios)", "",
          "| Variante | Recompensa | Pasos en espera | Órdenes de mercado | Órdenes límite | Slippage (bps) |", "|---|---|---|---|---|---|"]
    for v, r in res.items():
        t = r["entrenamiento"]
        L.append(f"| {v} | {_f(t['retorno'][0])} → {_f(t['retorno'][1])} | {_f(100 * t['pct_espera'][0], 0)} % → {_f(100 * t['pct_espera'][1], 0)} % | "
                 f"{_f(100 * t['pct_mercado'][0], 0)} % → {_f(100 * t['pct_mercado'][1], 0)} % | {_f(100 * t['pct_limite'][0], 0)} % → {_f(100 * t['pct_limite'][1], 0)} % | "
                 f"{_f(t['slippage_bps'][0], 1)} → {_f(t['slippage_bps'][1], 1)} |")
    mejor = elegir_mejor(res)
    L += ["", f"**Mejor variante según el criterio:** `{mejor}` ({res[mejor]['criterio']['todo']} de {res[mejor]['n_redes']} redes cumplen los tres puntos).", "",
          "🤖 Generado con [Claude Code](https://claude.com/claude-code)", ""]
    return "\n".join(L)


def main(argv: Optional[Sequence[str]] = None) -> Path:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dir", required=True)
    ap.add_argument("--etapa", default="A")
    ap.add_argument("--out-md", default=None)
    ap.add_argument("--out-png", default=None)
    ap.add_argument("--out-json", default=None)
    args = ap.parse_args(argv)
    d = Path(args.dir)
    corridas = cargar(d)
    if not corridas:
        raise SystemExit(f"No hay corridas en {d}")
    ref = json.load(open(d / "referencias.json", encoding="utf-8")) if (d / "referencias.json").exists() else {}
    res = {v: resumen_variante(c) for v, c in corridas.items()}
    md = Path(args.out_md or REPO_ROOT / f"docs/experimentos_recompensa_{args.etapa}_PS.md")
    png = Path(args.out_png or REPO_ROOT / f"data/analysis/experimentos_recompensa_{args.etapa}.png")
    figura(res, ref, png)
    try:
        png_rel = "../" + png.resolve().relative_to(md.resolve().parent.parent).as_posix()
    except ValueError:
        png_rel = png.name
    md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text(informe(res, ref, png_rel, args.etapa), encoding="utf-8")
    out_json = Path(args.out_json or REPO_ROOT / f"data/analysis/experimentos_recompensa_{args.etapa}.json")
    out_json.write_text(json.dumps({"resumen": res, "mejor": elegir_mejor(res)}, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Informe: {md}\nMejor: {elegir_mejor(res)}")
    return md


if __name__ == "__main__":
    main()
