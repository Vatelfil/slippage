"""Analisis de los benchmarks TWAP y VWAP sobre las meta-ordenes (tarea 2.3.4).

Elaborado por PS con apoyo de Claude Code; pendiente de revision por BF y MR.

Lee el JSON que deja `scripts/colab/benchmarks_meta_ordenes_ps.py` y genera:
  - una tabla por orden y estrategia (IS medio en CLP, slippage medio en bps,
    cumplimiento, numero de semillas y error estandar),
  - la comparacion TWAP frente a VWAP (diferencia por orden y Wilcoxon pareado
    sobre el slippage medio por orden),
  - una figura (slippage por orden y estrategia) y un informe markdown.

    python scripts/analizar_benchmarks_meta_ordenes.py \
        --resultados data/colab_resultados/benchmarks_meta_ordenes_abides.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

ESTRATEGIAS = ("TWAP", "VWAP")
ALPHA = 0.05
UMBRAL_EJECUCION = 0.95  # criterio de T3: la orden se considera ejecutable si TWAP completa al menos el 95 %


def _ee(x: np.ndarray) -> Optional[float]:
    return float(x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 1 else None


def tabla(estado: Dict) -> List[Dict]:
    """Una fila por (orden, estrategia) con medias sobre las semillas."""
    grupos: Dict[tuple, List[Dict]] = {}
    meta: Dict[str, Dict] = {}
    for c in estado.get("corridas", {}).values():
        if "error" in c or c.get("IS_total") is None:
            continue
        grupos.setdefault((c["orden"], c["estrategia"]), []).append(c)
        meta[c["orden"]] = {"ticker": c.get("ticker"), "tramo_inicio": c.get("tramo_inicio"), "cantidad": c.get("cantidad")}
    filas = []
    for (oid, est), cs in sorted(grupos.items()):
        is_ = np.array([c["IS_total"] for c in cs], dtype=float)
        sl = np.array([c["slippage_bps"] for c in cs], dtype=float)
        ex = np.array([c.get("execution_rate", np.nan) for c in cs], dtype=float)
        filas.append({"orden": oid, "estrategia": est, **meta[oid], "n": len(cs),
                      "IS_medio": float(is_.mean()), "IS_ee": _ee(is_),
                      "slippage_bps_medio": float(sl.mean()), "slippage_bps_ee": _ee(sl),
                      "cumplimiento_medio": float(np.nanmean(ex)) if np.isfinite(ex).any() else None})
    return filas


def comparar(filas: Sequence[Dict]) -> Dict:
    """TWAP frente a VWAP por orden y Wilcoxon pareado del slippage medio por orden."""
    por = {(f["orden"], f["estrategia"]): f for f in filas}
    ordenes = sorted({f["orden"] for f in filas})
    difs, detalle = [], []
    for o in ordenes:
        if (o, "TWAP") in por and (o, "VWAP") in por:
            a, b = por[(o, "TWAP")]["slippage_bps_medio"], por[(o, "VWAP")]["slippage_bps_medio"]
            detalle.append({"orden": o, "TWAP_bps": a, "VWAP_bps": b, "diferencia_bps": a - b,
                            "identicas": bool(abs(a - b) < 1e-9)})
            difs.append(a - b)
    out: Dict = {"por_orden": detalle, "n_ordenes": len(difs), "diferencia_media_bps": float(np.mean(difs)) if difs else None}
    distintas = [d for d in difs if abs(d) > 1e-9]
    out["n_ordenes_distintas"] = len(distintas)
    if len(distintas) >= 6:
        w = stats.wilcoxon(distintas)
        out.update({"wilcoxon_p": float(w.pvalue), "rechaza": bool(w.pvalue < ALPHA)})
    else:
        out.update({"wilcoxon_p": None, "rechaza": None})
    return out


def figura(filas: Sequence[Dict], ruta: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ordenes = sorted({f["orden"] for f in filas})
    x = np.arange(len(ordenes))
    fig, ax = plt.subplots(figsize=(max(6, 0.7 * len(ordenes) + 2), 4))
    for k, est in enumerate(ESTRATEGIAS):
        ys, es = [], []
        for o in ordenes:
            f = next((f for f in filas if f["orden"] == o and f["estrategia"] == est), None)
            ys.append(f["slippage_bps_medio"] if f else np.nan)
            es.append((f["slippage_bps_ee"] or 0.0) if f else 0.0)
        ax.bar(x + (k - 0.5) * 0.38, ys, 0.38, yerr=es, capsize=3, label=est)
    ax.set_xticks(x)
    ax.set_xticklabels(ordenes, rotation=45, ha="right")
    ax.set_ylabel("Slippage medio (bps)")
    ax.set_title("TWAP y VWAP por meta-orden (barras: error estándar)")
    ax.axhline(0, color="k", lw=0.6)
    ax.legend()
    fig.tight_layout()
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta, dpi=130)
    plt.close(fig)


def f(x, d=1):
    return "—" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def ejecutabilidad(estado: Dict) -> Dict:
    """Cumplimiento de TWAP por orden (cada semilla y media) y cuantas corridas llegan al umbral."""
    por: Dict[str, Dict] = {}
    for c in estado.get("corridas", {}).values():
        if c.get("estrategia") != "TWAP" or "error" in c or c.get("execution_rate") is None:
            continue
        o = por.setdefault(c["orden"], {"ticker": c.get("ticker"), "tramo_inicio": c.get("tramo_inicio"),
                                        "cantidad": c.get("cantidad"), "semillas": {}})
        o["semillas"][int(c["seed"])] = float(c["execution_rate"])
    filas = []
    for oid, o in sorted(por.items()):
        v = np.array([o["semillas"][k] for k in sorted(o["semillas"])])
        filas.append({"orden": oid, "ticker": o["ticker"], "tramo_inicio": o["tramo_inicio"], "cantidad": o["cantidad"],
                      "cumplimiento_por_semilla": [float(x) for x in v], "cumplimiento_medio": float(v.mean()),
                      "corridas_ok": int((v >= UMBRAL_EJECUCION).sum()), "corridas": int(len(v)),
                      "ejecutable": bool(v.mean() >= UMBRAL_EJECUCION)})
    return {"umbral": UMBRAL_EJECUCION, "ordenes": filas,
            "corridas_ok": sum(r["corridas_ok"] for r in filas), "corridas": sum(r["corridas"] for r in filas),
            "ordenes_ejecutables": sum(r["ejecutable"] for r in filas)}


def seccion_ejecutabilidad(ejec: Dict, alternativas: Optional[Dict[str, Dict]] = None) -> List[str]:
    """`alternativas`: {etiqueta: ejecutabilidad(...)} de otras corridas (otros tamanos de orden) para comparar."""
    u = f(100 * ejec["umbral"], 0)
    L = ["## 3. Ejecutabilidad de las meta-órdenes (criterio de T3)", "",
         f"Una orden es ejecutable si TWAP completa al menos el {u} % (`execution_rate`). Se informa el cumplimiento de cada semilla y su media.", "",
         "| Orden | Activo | Inicio | Acciones | Cumplimiento por semilla | Media | Corridas ≥ umbral | ¿Ejecutable? |", "|---|---|---|---:|---|---:|---:|:---:|"]
    for r in ejec["ordenes"]:
        L.append(f"| {r['orden']} | {r['ticker']} | {r['tramo_inicio']} | {f(r['cantidad'], 0)} | "
                 + " · ".join(f(100 * x, 1) + " %" for x in r["cumplimiento_por_semilla"])
                 + f" | {f(100 * r['cumplimiento_medio'], 1)} % | {r['corridas_ok']}/{r['corridas']} | {'sí' if r['ejecutable'] else 'no'} |")
    L += ["", f"- **{ejec['ordenes_ejecutables']} de {len(ejec['ordenes'])} órdenes** son ejecutables en promedio; {ejec['corridas_ok']} de {ejec['corridas']} corridas llegan al umbral."]
    if alternativas:
        etiquetas = list(alternativas)
        base = {r["orden"]: r for r in ejec["ordenes"]}
        alt = {e: {r["orden"]: r for r in alternativas[e]["ordenes"]} for e in etiquetas}
        L += ["", "**Comparación con otros tamaños de orden** (mismas órdenes y semillas; la base es la tabla de arriba):", "",
              "| Orden | Activo | Inicio | Base: acciones | Base: media | "
              + " | ".join(f"{e}: acciones | {e}: media | {e}: ¿ejecutable?" for e in etiquetas) + " |",
              "|---|---|---|---:|---:|" + "---:|---:|:---:|" * len(etiquetas)]
        for oid, r in base.items():
            celdas = []
            for e in etiquetas:
                x = alt[e].get(oid)
                celdas += [f(x["cantidad"], 0), f"{f(100 * x['cumplimiento_medio'], 1)} % ({len(x['cumplimiento_por_semilla'])} sem.)",
                           "sí" if x["ejecutable"] else "no"] if x else ["—", "—", "—"]
            L.append(f"| {oid} | {r['ticker']} | {r['tramo_inicio']} | {f(r['cantidad'], 0)} | {f(100 * r['cumplimiento_medio'], 1)} % | " + " | ".join(celdas) + " |")
        L.append("")
        for e in etiquetas:
            a = alternativas[e]
            L.append(f"- **{e}:** {a['ordenes_ejecutables']} de {len(a['ordenes'])} órdenes ejecutables en promedio ({a['corridas_ok']} de {a['corridas']} corridas).")
    return L + [""]


def informe(estado: Dict, filas: Sequence[Dict], comp: Dict, meta: Dict, ejec: Optional[Dict] = None, alternativas: Optional[Dict[str, Dict]] = None) -> str:
    ejec = ejec if ejec is not None else ejecutabilidad(estado)
    L = ["# Benchmarks TWAP y VWAP sobre las meta-órdenes (tarea 2.3.4)", "",
         "**Elaborado por:** PS con apoyo de Claude Code. **Pendiente de revisión por:** BF y MR.",
         f"**Entorno:** {meta.get('entorno', '?')} · **Órdenes:** {comp['n_ordenes']} · **Fecha:** {meta.get('fecha')}", "",
         "Cada orden se reparte desde su tramo de inicio hasta el cierre con la política ingenua de mercado (TWAP: partes iguales; "
         "VWAP: proporcional al volumen histórico por tramo). IS = (P_prom − P_ref) × Q; slippage en bps sobre P_ref.", "",
         "## 1. Resultados por orden", "",
         "| Orden | Activo | Inicio | Cantidad | Estrategia | n | IS medio (CLP) | Slippage medio (bps) | EE (bps) | Cumplimiento |",
         "|---|---|---|---:|---|---:|---:|---:|---:|---:|"]
    for r in filas:
        L.append(f"| {r['orden']} | {r.get('ticker')} | {r.get('tramo_inicio')} | {f(r.get('cantidad'), 0)} | {r['estrategia']} | {r['n']} | "
                 f"{f(r['IS_medio'], 0)} | {f(r['slippage_bps_medio'], 2)} | {f(r['slippage_bps_ee'], 2)} | {f(r['cumplimiento_medio'], 3)} |")
    L += ["", "## 2. TWAP frente a VWAP", "",
          "| Orden | TWAP (bps) | VWAP (bps) | TWAP − VWAP (bps) | ¿Idénticas? |", "|---|---:|---:|---:|:---:|"]
    for d in comp["por_orden"]:
        L.append(f"| {d['orden']} | {f(d['TWAP_bps'], 2)} | {f(d['VWAP_bps'], 2)} | {f(d['diferencia_bps'], 2)} | {'sí' if d['identicas'] else 'no'} |")
    p = comp["wilcoxon_p"]
    L += ["", f"- Diferencia media TWAP − VWAP: **{f(comp['diferencia_media_bps'], 2)} bps** (n = {comp['n_ordenes']} órdenes; "
              f"{comp['n_ordenes_distintas']} con calendarios distintos).",
          (f"- Wilcoxon pareado sobre las órdenes con calendarios distintos: p = {f(p, 3)}; "
           f"{'se rechaza' if comp['rechaza'] else 'no se rechaza'} la igualdad con α = 0,05." if p is not None else
           "- No hay suficientes órdenes con calendarios distintos (mínimo 6) para el Wilcoxon pareado."), "",
          ] + seccion_ejecutabilidad(ejec, alternativas) + [
          "## 4. Limitaciones", "",
          "- Las órdenes que empiezan en el cierre tienen un TWAP y un VWAP idénticos: el perfil de volumen se calcula por tramo y dentro de un tramo los periodos pesan igual.",
          "- Pocas semillas por orden (ver n): los errores estándar son amplios y el slippage absoluto en ABIDES está subestimado porque el spread simulado es mucho menor que el real (ver `docs/validacion_formal_2.2.5_PS.md`); la comparación entre estrategias sigue siendo válida.",
          "- Una jornada completa son 13 periodos independientes (un entorno nuevo por periodo, igual que el orquestador).",
          "- El IS se calcula sobre lo ejecutado: cuando el cumplimiento es menor que 100 %, el costo de lo que no se ejecutó no entra, y comparar estrategias con cumplimientos distintos tiene ese sesgo.",
          "- Cada periodo usa un entorno nuevo y lo que no se ejecuta en un periodo no se traslada al siguiente; es una causa probable del cumplimiento incompleto (no comprobada).", "",
          "🤖 Generado con [Claude Code](https://claude.com/claude-code)"]
    return "\n".join(L) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--resultados", required=True, help="benchmarks_meta_ordenes_<entorno>.json")
    ap.add_argument("--alternativas", nargs="*", default=[], metavar="ETIQUETA=ARCHIVO",
                    help="otras corridas (otro tamano de orden) para comparar la ejecutabilidad, p. ej. 'B 10 %%=ruta.json'")
    ap.add_argument("--out-json", default=str(REPO_ROOT / "data/analysis/benchmarks_meta_ordenes.json"))
    ap.add_argument("--out-png", default=str(REPO_ROOT / "data/analysis/benchmarks_meta_ordenes.png"))
    ap.add_argument("--out-md", default=str(REPO_ROOT / "docs/benchmarks_2.3.4_PS.md"))
    args = ap.parse_args(argv)

    with open(args.resultados, "r", encoding="utf-8") as fh:
        estado = json.load(fh)
    filas = tabla(estado)
    if not filas:
        raise SystemExit("El archivo no tiene corridas completas.")
    comp = comparar(filas)
    ejec = ejecutabilidad(estado)
    alternativas: Dict[str, Dict] = {}
    for item in args.alternativas:
        etiqueta, _, ruta = item.rpartition("=")
        with open(ruta, "r", encoding="utf-8") as fh:
            alternativas[etiqueta] = ejecutabilidad(json.load(fh))
    meta = {"entorno": estado.get("firma", {}).get("entorno"), "fecha": time.strftime("%Y-%m-%d")}
    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_json, "w", encoding="utf-8") as fh:
        json.dump({"metadata": meta, "tabla": filas, "comparacion": comp, "ejecutabilidad": ejec, "ejecutabilidad_alternativas": alternativas}, fh, indent=1, ensure_ascii=False)
    figura(filas, Path(args.out_png))
    Path(args.out_md).write_text(informe(estado, filas, comp, meta, ejec, alternativas), encoding="utf-8")
    print(f"JSON: {args.out_json}\nFigura: {args.out_png}\nInforme: {args.out_md}")


if __name__ == "__main__":
    main()
