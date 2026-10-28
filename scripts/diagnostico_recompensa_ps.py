"""Diagnóstico de por qué el entrenamiento no baja el costo (fases 0 y 1 del plan de investigación; BORRADOR de PS).

Reúne en un solo informe (`docs/diagnostico_recompensa_PS.md`) la evidencia de que la red optimiza la recompensa R_E y no lo
que se evalúa:

  1. reproduce la falla en el PC con el simulador de Poisson (entrenamiento con la recompensa original),
  2. repasa las corridas de ABIDES que ya existen (recompensa, slippage y tipo de orden a lo largo del entrenamiento),
  3. audita R_E: qué recompensa recibe cada estrategia simple frente a su costo real,
  4. mide cuántas semillas de evaluación hacen falta para ver una diferencia de 1, 2 o 3 bps,
  5. compara el tamaño de las órdenes con que se entrena (1.000 acciones) con el que opera el Maestro.

    python scripts/diagnostico_recompensa_ps.py
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _f(x: Optional[float], d: int = 2) -> str:
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "—"
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ---------------------------------------------------------------------------
# 1. Reproducción en Poisson
# ---------------------------------------------------------------------------

def _entrenar_v0(args):
    import torch
    torch.set_num_threads(1)
    from src.experiments import entrenamiento_variantes as ev
    from src.experiments import variantes_recompensa as vr
    q, semilla, episodios = args
    _, _, registro, _ = ev.entrenar(vr.V0, semilla, episodios, q_slice=q)
    return {"q_slice": q, "semilla": semilla, "curvas": ev.curvas(registro)}


def reproducir_falla(episodios: int, semillas: Sequence[int], tamanos: Sequence[int], procesos: int) -> List[Dict]:
    trabajos = [(q, s, episodios) for q in tamanos for s in semillas]
    with ProcessPoolExecutor(max_workers=min(procesos, len(trabajos))) as pool:
        return list(pool.map(_entrenar_v0, trabajos))


# ---------------------------------------------------------------------------
# 2. Evidencia en ABIDES (archivos ya existentes)
# ---------------------------------------------------------------------------

def evidencia_abides(directorio: Path) -> List[Dict]:
    """Recompensa, slippage y tipo de orden por bloques de 100 episodios en cada corrida de 1.000 episodios."""
    filas = []
    for f in sorted(glob.glob(str(directorio / "d3_opcion*" / "monitoreo_episodios.csv"))):
        with open(f, "r", encoding="utf-8-sig") as fh:
            rows = list(csv.DictReader(fh))
        if len(rows) < 1000:
            continue

        def media(k, a, b):
            v = [float(r[k]) for r in rows[a:b] if r.get(k) not in (None, "", "nan")]
            return float(np.mean(v)) if v else float("nan")

        blocks = []
        for a in range(0, 1000, 100):
            blocks.append({k: media(k, a, a + 100) for k in ("retorno", "slippage_bps", "pct_espera", "pct_mercado", "pct_limite_compra")})
        filas.append({"corrida": Path(f).parent.name, "bloques": blocks})
    return filas


# ---------------------------------------------------------------------------
# 3. Auditoría de R_E
# ---------------------------------------------------------------------------

def auditoria_re(q_slice: int = 5000, ventana: int = 15, n_semillas: int = 50) -> List[Dict]:
    """Recompensa que ve el agente (con la fórmula actual de R_E) y costo real de cada estrategia simple."""
    import torch
    from src.config.market_params import BETA_RIESGO_EJECUTOR
    from src.experiments import variantes_recompensa as vr
    from src.models.networks_factory import make_executor_networks

    semillas = list(range(5001, 5001 + n_semillas))
    kw = dict(q_slice=q_slice, ventana_min=ventana, beta=BETA_RIESGO_EJECUTOR)
    esperar = lambda s: (lambda obs, paso, mx: np.array([vr.LIMIT_SELL_IDX, 0, 0]))
    torch.manual_seed(1000)
    red = make_executor_networks()["apertura"]
    estrategias = {
        "Esperar siempre": vr.evaluar(esperar, semillas, **kw),
        "Mercado por todo lo pendiente (agresiva)": vr.evaluar_heuristica("agresiva_market", semillas, **kw),
        "Orden límite por tramos (TWAP límite)": vr.evaluar_heuristica("twap_limit_medio", semillas, **kw),
        "Orden límite pasiva": vr.evaluar_heuristica("pasiva_limit", semillas, **kw),
        "Red sin entrenar (muestreando)": vr.evaluar_red(red, semillas, muestrear=True, **kw),
    }
    filas = []
    for nombre, res in estrategias.items():
        p = vr.promedios(res)
        filas.append({"estrategia": nombre, "retorno_visto": p["retorno"],
                      "retorno_con_liquidacion": p["retorno"] + p["retorno_liquidacion"],
                      "slippage_bps": p["slippage_bps"], "cumplimiento_voluntario": p["cumplimiento_voluntario"],
                      "pct_espera": p["pct_espera"]})
    return filas


# ---------------------------------------------------------------------------
# 4. Potencia de la evaluación
# ---------------------------------------------------------------------------

def potencia(directorio: Path) -> Dict:
    """Desvío de la diferencia pareada (entrenada muestreando − red inicial muestreando) por semilla de evaluación y
    cantidad de semillas necesarias (prueba bilateral, 5 %, potencia 80 %) para detectar 1, 2 o 3 bps."""
    from scipy import stats
    desvios = []
    for carpeta in sorted(glob.glob(str(directorio / "d3_opcion*_s*"))):
        m = Path(carpeta).name.split("_s")[-1]
        archivo = Path(carpeta) / "entrenamiento_inicial_apertura.json"
        control = directorio / f"control_sin_entrenar_muestreado_s{m}.json"
        if not archivo.exists() or not control.exists():
            continue
        a = json.load(open(archivo, encoding="utf-8-sig"))["evaluacion_entrenada_estocastica"].get("slippage_por_semilla", [])
        b = json.load(open(control, encoding="utf-8-sig")).get("slippage_por_semilla", [])
        d = [x - y for x, y in zip(a, b) if x is not None and y is not None]
        if len(d) > 2:
            desvios.append(float(np.std(d, ddof=1)))
    if not desvios:
        return {}
    sd = float(np.median(desvios))
    z = stats.norm.ppf(0.975) + stats.norm.ppf(0.80)
    return {"sd_diferencia": sd, "n_corridas": len(desvios),
            "semillas_necesarias": {str(dif): int(np.ceil((z * sd / dif) ** 2)) for dif in (1, 2, 3)}}


# ---------------------------------------------------------------------------
# 5. Tamaño de las órdenes
# ---------------------------------------------------------------------------

def tamanos_reales(directorio: Path) -> Dict:
    """Cantidad ejecutada por ventana en la evaluación del sistema completo (el Maestro asigna α × lo pendiente)."""
    q = []
    for f in glob.glob(str(directorio / "sistema_PPO_sin_entrenar_argmax_*MO*.json")):
        d = json.load(open(f, encoding="utf-8-sig"))
        for c in d["corridas"].values():
            q += [x["q_ejecutado"] for x in c.get("decisiones", []) if x["q_ejecutado"] > 0]
    if not q:
        return {}
    q = np.asarray(q)
    return {"n_ventanas": int(len(q)), "p10": float(np.percentile(q, 10)), "mediana": float(np.median(q)),
            "p90": float(np.percentile(q, 90)), "maximo": float(q.max())}


# ---------------------------------------------------------------------------
# Figura e informe
# ---------------------------------------------------------------------------

def figura(poisson: List[Dict], abides: List[Dict], audit: List[Dict], ruta: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(2, 2, figsize=(13, 8.5))
    # (a) Poisson: % de pasos en espera por bloque
    for r in poisson:
        x = np.arange(1, len(r["curvas"]) + 1) * 100
        ax[0, 0].plot(x, [100 * c["pct_espera"] for c in r["curvas"]], marker="o", ms=3,
                      ls="-" if r["q_slice"] == 1000 else "--", label=f"q={r['q_slice']}, semilla {r['semilla']}")
    ax[0, 0].set_title("(a) Poisson, recompensa original: % de pasos esperando")
    ax[0, 0].set_xlabel("episodio")
    ax[0, 0].set_ylabel("% de pasos en espera")
    ax[0, 0].legend(fontsize=8)
    # (b) ABIDES: retorno y slippage por bloque (promedio de las corridas)
    if abides:
        x = np.arange(1, 11) * 100
        ret = np.mean([[b["retorno"] for b in f["bloques"]] for f in abides], axis=0)
        slp = np.mean([[b["slippage_bps"] for b in f["bloques"]] for f in abides], axis=0)
        ax[0, 1].plot(x, ret, color="#0F6E56", marker="o", label="recompensa R_E (izq.)")
        ax[0, 1].set_ylabel("retorno por episodio", color="#0F6E56")
        b2 = ax[0, 1].twinx()
        b2.plot(x, slp, color="#993C1D", marker="s", label="slippage (der.)")
        b2.set_ylabel("slippage (bps)", color="#993C1D")
    ax[0, 1].set_title("(b) ABIDES: la recompensa sube, el slippage no baja")
    ax[0, 1].set_xlabel("episodio")
    # (c) auditoría: retorno visto vs slippage real
    nombres = [a["estrategia"].split(" (")[0] for a in audit]
    y = np.arange(len(audit))
    ax[1, 0].barh(y, [a["retorno_visto"] for a in audit], color="#0F6E56")
    ax[1, 0].set_yticks(y, nombres, fontsize=8)
    ax[1, 0].invert_yaxis()
    ax[1, 0].set_title("(c) Recompensa R_E que ve el agente\n(mayor = mejor)")
    ax[1, 0].set_xlabel("R_E por episodio")
    # (d) auditoría: slippage real
    ax[1, 1].barh(y, [a["slippage_bps"] for a in audit], color="#993C1D")
    ax[1, 1].set_yticks(y, nombres, fontsize=8)
    ax[1, 1].invert_yaxis()
    ax[1, 1].set_title("(d) Costo real: slippage con el remanente liquidado\n(menor = mejor)")
    ax[1, 1].set_xlabel("bps")
    # valor al final de cada barra, para que «esperar siempre» (R_E = 0) no parezca una barra que falta
    for i, a_ in enumerate(audit):
        ax[1, 0].text(a_["retorno_visto"] - 0.15 if a_["retorno_visto"] < -0.5 else 0.15, i, f"{a_['retorno_visto']:.1f}".replace(".", ","),
                      va="center", ha="right" if a_["retorno_visto"] < -0.5 else "left", fontsize=8,
                      color="white" if a_["retorno_visto"] < -0.5 else "black")
        ax[1, 1].text(a_["slippage_bps"] - 0.3, i, f"{a_['slippage_bps']:.1f}".replace(".", ","), va="center", ha="right", fontsize=8, color="white")
    for a in ax.ravel():
        a.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta, dpi=140)
    plt.close(fig)


def informe(poisson, abides, audit, pot, tam, png_rel: str) -> str:
    L = ["# Diagnóstico: por qué el entrenamiento no baja el costo", "",
         "**Elaborado por:** PS con apoyo de Claude Code (uso autorizado por la universidad). **Pendiente de revisión por:** BF (R_E) y MR (entrenamiento).", "",
         "Este documento reúne la evidencia de las fases 0 y 1 del plan de investigación. Se genera con "
         "`scripts/diagnostico_recompensa_ps.py`; los números salen de los archivos del repositorio y de corridas en el PC con el simulador de Poisson.", "",
         f"![Diagnóstico]({png_rel})", "",
         "## 1. Qué se observó",
         "- Con 1.000 episodios, las redes entrenadas con R_E cuestan **más** que la misma red sin entrenar (+3,08 bps, 0 de 6 redes mejores; `docs/estabilidad_D3_1000ep_PS.md`).",
         "- En el entrenamiento la recompensa mejora, pero el slippage frente al precio de llegada no, y la conducta cambia de órdenes de mercado a órdenes límite pasivas.", "",
         "## 2. Reproducción en el PC (Poisson, recompensa original)", "",
         "| Tamaño del slice | Semilla de red | Pasos en espera: ep. 1-100 | ep. 451-550 | ep. 901-1000 | Cumplimiento voluntario al final |",
         "|---:|---:|---:|---:|---:|---:|"]
    for r in poisson:
        c = r["curvas"]
        L.append(f"| {r['q_slice']} | {r['semilla']} | {_f(100 * c[0]['pct_espera'], 0)} % | {_f(100 * c[4]['pct_espera'], 0)} % | "
                 f"{_f(100 * c[-1]['pct_espera'], 0)} % | {_f(c[-1]['cumplimiento_voluntario'], 2)} |")
    L += ["", "La red aprende a no operar: pasa de esperar ≈ 30 % de los pasos (política inicial casi uniforme) a esperar casi todos. "
          "La corrida entera dura cerca de un minuto, así que se puede repetir cuantas veces haga falta.", "",
          "## 3. Auditoría de R_E", "",
          f"Estrategias simples en 50 semillas nuevas, slice de 5.000 acciones y ventana de 15 min. «R_E visto» es la recompensa que recibe el agente "
          f"hoy; «slippage» es el costo real frente al precio de llegada, **liquidando a mercado lo que no se compró** para que todas las filas sean comparables.", "",
          "| Estrategia | R_E visto por el agente | R_E si se liquida el remanente | Slippage (bps) | Cumplimiento voluntario | Pasos en espera |",
          "|---|---:|---:|---:|---:|---:|"]
    for a in audit:
        L.append(f"| {a['estrategia']} | {_f(a['retorno_visto'], 2)} | {_f(a['retorno_con_liquidacion'], 2)} | {_f(a['slippage_bps'])} | "
                 f"{_f(a['cumplimiento_voluntario'], 2)} | {_f(100 * a['pct_espera'], 0)} % |")
    L += ["", "**Lectura:** con la recompensa original, *esperar siempre* obtiene la mayor recompensa posible (cero: no paga ningún costo), "
          "aunque no compra nada. Operar siempre cuesta recompensa, porque cada compra paga el spread frente al precio medio. Nada en R_E obliga a completar la orden "
          "(la penalización por lo no ejecutado está en R_M, que todavía no se entrena) ni castiga el costo de esperar frente al precio de llegada. Por eso el "
          "óptimo de R_E y el óptimo de la evaluación no coinciden.", "",
          "**El orden de las estrategias también se invierte.** La orden límite pasiva recibe mejor R_E que el TWAP con órdenes límite y cuesta bastante más en la realidad, "
          "porque la parte que no logra comprar no entra en R_E. Una red que maximiza R_E tiende, entonces, a preferir lo pasivo y lo que no compra.", ""]
    L += ["## 4. Evidencia en ABIDES (corridas de 1.000 episodios)", "",
          "| Corrida | Recompensa (ep. 1-100 → 901-1000) | Slippage (bps) | Mercado | Límite de compra | Espera |", "|---|---|---|---|---|---|"]
    for f in abides:
        b0, b1 = f["bloques"][0], f["bloques"][-1]
        L.append(f"| {f['corrida']} | {_f(b0['retorno'])} → {_f(b1['retorno'])} | {_f(b0['slippage_bps'], 1)} → {_f(b1['slippage_bps'], 1)} | "
                 f"{_f(100 * b0['pct_mercado'], 0)} % → {_f(100 * b1['pct_mercado'], 0)} % | "
                 f"{_f(100 * b0['pct_limite_compra'], 0)} % → {_f(100 * b1['pct_limite_compra'], 0)} % | {_f(100 * b0['pct_espera'], 0)} % → {_f(100 * b1['pct_espera'], 0)} % |")
    L += ["", "La recompensa mejora en todas las corridas, el slippage queda igual o peor, y las órdenes de mercado se reemplazan por órdenes límite pasivas, "
          "que R_E premia (comprar bajo el precio medio da recompensa positiva) y que la evaluación no recompensa.", ""]
    if pot:
        L += ["## 5. Potencia de la evaluación", "",
              f"El desvío de la diferencia pareada (entrenada − red inicial, por semilla de evaluación) es de {_f(pot['sd_diferencia'])} bps (mediana de {pot['n_corridas']} corridas). "
              "Semillas de evaluación necesarias para detectar una diferencia (prueba bilateral, 5 %, potencia 80 %):", "",
              "| Diferencia a detectar | Semillas necesarias |", "|---:|---:|"]
        for dif, n in pot["semillas_necesarias"].items():
            L.append(f"| {dif} bps | {n} |")
        L += ["", "Con 15 semillas solo se detectan diferencias grandes. Los experimentos nuevos evalúan con 50 semillas.", ""]
    if tam:
        L += ["## 6. Tamaño de las órdenes: entrenamiento frente a uso", "",
              f"El Ejecutor se entrena con slices de 1.000 acciones. En la evaluación del sistema completo (sin entrenar), cada ventana compra entre "
              f"{_f(tam['p10'], 0)} (percentil 10) y {_f(tam['p90'], 0)} (percentil 90) acciones, con mediana de {_f(tam['mediana'], 0)} y máximo de {_f(tam['maximo'], 0)} "
              f"({tam['n_ventanas']} ventanas). La red se usaría en un rango de tamaños que no vio al entrenar.", ""]
    L += ["## 7. Conclusión", "",
          "1. **Desalineación entre recompensa y métrica (confirmada en Poisson, visible en ABIDES):** R_E premia no pagar ahora y no exige completar; la evaluación mide el costo total frente al precio de llegada.",
          "2. **El simulador de Poisson con 1.000 acciones casi no distingue estrategias** (todas ≈ 18 bps), de modo que ahí no hay nada que aprender; hay que entrenar con tamaños donde sí importa (desde ≈ 5.000 acciones).",
          "3. **Faltan semillas de evaluación** para detectar diferencias de 1 a 3 bps.",
          "4. **El tamaño de entrenamiento no coincide con el de uso.**",
          "5. **El factor de descuento del Ejecutor (γ = 0,95) agrava el problema.** Con ventanas de 30 pasos, un costo que llega al final de la ventana "
          "(por ejemplo, el de lo que quedó sin comprar) se ve desde el primer paso multiplicado por 0,95²⁹ ≈ 0,23: parece cuatro veces más barato de lo que es. "
          "Es una causa distinta de la recompensa y se comprobó por separado (`docs/experimentos_recompensa_A2_PS.md`).",
          "Los arreglos que se probaron para cada punto y sus resultados están en `docs/experimentos_recompensa_PS.md`.", "",
          "🤖 Generado con [Claude Code](https://claude.com/claude-code)", ""]
    return "\n".join(L)


def main(argv: Optional[Sequence[str]] = None) -> Path:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--episodios", type=int, default=1000)
    ap.add_argument("--semillas", nargs="+", type=int, default=[2000, 3000])
    ap.add_argument("--tamanos", nargs="+", type=int, default=[1000, 5000])
    ap.add_argument("--procesos", type=int, default=4)
    ap.add_argument("--abides", default=str(REPO_ROOT / "data/colab_resultados/d3_1000ep"))
    ap.add_argument("--d3-100ep", default=str(REPO_ROOT / "data/colab_resultados/d3_estabilidad"))
    ap.add_argument("--c3", default=str(REPO_ROOT / "data/colab_resultados/c3_sistema_v2"))
    ap.add_argument("--out-md", default=str(REPO_ROOT / "docs/diagnostico_recompensa_PS.md"))
    ap.add_argument("--out-png", default=str(REPO_ROOT / "data/analysis/diagnostico_recompensa.png"))
    ap.add_argument("--out-json", default=str(REPO_ROOT / "data/analysis/diagnostico_recompensa.json"))
    ap.add_argument("--desde-json", action="store_true",
                    help="no recalcula nada: regenera la figura y el informe a partir de --out-json (útil al cambiar solo los textos)")
    args = ap.parse_args(argv)

    if args.desde_json:
        d = json.load(open(args.out_json, encoding="utf-8"))
        poisson, abides, audit, pot, tam = d["poisson"], d["abides"], d["auditoria"], d["potencia"], d["tamanos"]
    else:
        poisson = reproducir_falla(args.episodios, args.semillas, args.tamanos, args.procesos)
        abides = evidencia_abides(Path(args.abides))
        audit = auditoria_re()
        pot = potencia(Path(args.abides)) or potencia(Path(args.d3_100ep))
        tam = tamanos_reales(Path(args.c3))
    png = Path(args.out_png)
    figura(poisson, abides, audit, png)
    try:
        png_rel = "../" + png.resolve().relative_to(Path(args.out_md).resolve().parent.parent).as_posix()
    except ValueError:
        png_rel = png.name
    Path(args.out_md).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_md).write_text(informe(poisson, abides, audit, pot, tam, png_rel), encoding="utf-8")
    Path(args.out_json).write_text(json.dumps({"poisson": poisson, "abides": abides, "auditoria": audit, "potencia": pot,
                                               "tamanos": tam}, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Informe: {args.out_md}")
    return Path(args.out_md)


if __name__ == "__main__":
    main()
