"""Comparacion estadistica del sistema Maestro-Ejecutores contra TWAP y VWAP (tareas 3.2.3 y 3.2.4, Sprint 7).

BORRADOR elaborado por PS con apoyo de Claude Code (adelanto: el script queda listo antes de tener el sistema entrenado).

Compara, sobre las mismas meta-ordenes y las mismas semillas (datos PAREADOS), el slippage del sistema con el de
TWAP y VWAP. Lee dos archivos con el formato que deja `scripts/colab/benchmarks_meta_ordenes_ps.py`:
  - el de los benchmarks (estrategias TWAP y VWAP),
  - el del sistema: mismas claves `orden|estrategia|semilla` con `estrategia` = el nombre del sistema (por defecto "PPO"),
    y los campos `ticker`, `tramo_inicio`, `slippage_bps`, `execution_rate`.
Para que el pareo sea valido, el sistema debe evaluarse con las mismas semillas que los benchmarks (`seed` de la
corrida; el simulador usa `seed + semilla de la orden`).

Estadistica (diferencia = sistema - benchmark, en bps; negativa = el sistema cuesta menos):
  - por celda (orden x semilla): media, error estandar, IC 95 % por bootstrap, Wilcoxon y t pareados;
  - por orden (media de las semillas de cada orden): Wilcoxon, que respeta que las semillas de una orden se parecen;
  - por tramo de inicio y por activo (sensibilidad, 3.2.4);
  - cumplimiento del sistema frente al del benchmark.
Con varias comparaciones (ej. tamanos de orden distintos) se arma ademas la tabla de sensibilidad por tamano.

Costo ajustado por lo no ejecutado (opcional, `--penalizaciones-no-ejecutado 50 100 300`): el slippage de una corrida solo cuenta
lo que se compro, asi que un sistema que compra poco puede parecer barato. El costo ajustado reparte el costo por unidad de la
orden completa y castiga lo no comprado con una penalizacion supuesta (en bps del precio de llegada):

    costo_ajustado = slippage * cumplimiento + penalizacion * (1 - cumplimiento)

La penalizacion es un supuesto del equipo (R_M usa lambda = 0,05, es decir 500 bps); por eso se piden varios valores y se mira si la
conclusion cambia.

    python scripts/comparar_sistema_vs_benchmarks.py \
        --comparacion "100.000 acciones=bench_100k.json,sistema_100k.json" \
        --comparacion "10 % del dia=bench_10pct.json,sistema_10pct.json" \
        --out-md docs/sistema_vs_benchmarks_3.2.3.md
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

ALPHA = 0.05
BOOTSTRAP = 10000
BENCHMARKS = ("TWAP", "VWAP")
UMBRAL_CUMPLIMIENTO = 0.95


def _f(x: Optional[float], d: int = 2) -> str:
    return "—" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def cargar(path: str) -> Dict:
    with open(path, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def celdas(estado: Dict, estrategia: str) -> Dict[Tuple[str, int], Dict]:
    """(orden, semilla) -> corrida valida de esa estrategia."""
    out = {}
    for c in estado.get("corridas", {}).values():
        if c.get("estrategia") == estrategia and "error" not in c and c.get("orden") is not None:
            out[(c["orden"], int(c["seed"]))] = c
    return out


def ic_bootstrap(d: np.ndarray, rng: np.random.Generator, n: Optional[int] = None) -> Tuple[float, float]:
    """IC 95 % de la media por bootstrap percentil (remuestrea las diferencias). `n` es el numero de replicas; si no se pasa
    se usa BOOTSTRAP (las pruebas lo bajan para no tardar)."""
    n = BOOTSTRAP if n is None else n
    if len(d) < 2:
        return float("nan"), float("nan")
    medias = rng.choice(d, size=(n, len(d)), replace=True).mean(axis=1)
    lo, hi = np.percentile(medias, [2.5, 97.5])
    return float(lo), float(hi)


def resumen_dif(d: Sequence[float], rng: np.random.Generator) -> Dict:
    d = np.asarray(d, dtype=float)
    d = d[np.isfinite(d)]
    out: Dict = {"n": int(len(d)), "dif_media": float(d.mean()) if len(d) else None,
                 "ee": float(d.std(ddof=1) / np.sqrt(len(d))) if len(d) > 1 else None,
                 "frac_sistema_mejor": float((d < 0).mean()) if len(d) else None,
                 "ic95": list(ic_bootstrap(d, rng)) if len(d) > 1 else [None, None],
                 "wilcoxon_p": None, "t_p": None}
    if len(d) >= 6 and np.any(d != 0):
        out["wilcoxon_p"] = float(stats.wilcoxon(d).pvalue)
    if len(d) >= 3 and np.std(d) > 0:
        out["t_p"] = float(stats.ttest_1samp(d, 0.0).pvalue)
    return out


def costo_ajustado(slippage_bps: float, cumplimiento: float, penalizacion_bps: float) -> float:
    """Costo por unidad de la orden completa: lo comprado cuesta su slippage y lo no comprado, la penalizacion."""
    c = min(max(float(cumplimiento), 0.0), 1.0)
    return float(slippage_bps) * c + float(penalizacion_bps) * (1.0 - c)


def comparar(bench: Dict, sistema: Dict, nombre_sistema: str = "PPO", semilla: int = 0,
             penalizaciones: Sequence[float] = ()) -> Dict:
    """Compara el sistema con TWAP y VWAP. Devuelve un dict por benchmark. Con `penalizaciones` (bps) agrega, por cada una,
    la comparacion del costo ajustado por lo no ejecutado (ver el docstring del modulo)."""
    rng = np.random.default_rng(semilla)
    cs = celdas(sistema, nombre_sistema)
    out: Dict = {"sistema": nombre_sistema, "celdas_sistema": len(cs), "benchmarks": {}}
    for b in BENCHMARKS:
        cb = celdas(bench, b)
        comunes = sorted(set(cs) & set(cb))
        filas, sin_ejecucion = [], 0
        for k in comunes:
            s, r = cs[k], cb[k]
            if s.get("slippage_bps") is None or r.get("slippage_bps") is None:
                sin_ejecucion += 1
                continue
            filas.append({"orden": k[0], "seed": k[1], "ticker": r.get("ticker"), "tramo": r.get("tramo_inicio"),
                          "dif": float(s["slippage_bps"]) - float(r["slippage_bps"]),
                          "slip_sistema": float(s["slippage_bps"]), "slip_bench": float(r["slippage_bps"]),
                          "cumpl_sistema": float(s.get("execution_rate", np.nan)), "cumpl_bench": float(r.get("execution_rate", np.nan))})
        info: Dict = {"celdas_comunes": len(comunes), "celdas_sin_ejecucion": sin_ejecucion, "global": None, "por_orden": None,
                      "por_tramo": {}, "por_activo": {}, "cumplimiento": None, "filas": filas}
        if filas:
            info["global"] = resumen_dif([f["dif"] for f in filas], rng)
            por_o: Dict[str, List[float]] = {}
            for f in filas:
                por_o.setdefault(f["orden"], []).append(f["dif"])
            medias_o = {o: float(np.mean(v)) for o, v in por_o.items()}
            info["por_orden"] = {"medias": medias_o, **resumen_dif(list(medias_o.values()), rng)}
            for clave, campo in (("por_tramo", "tramo"), ("por_activo", "ticker")):
                grupos: Dict[str, List[float]] = {}
                for f in filas:
                    grupos.setdefault(str(f[campo]), []).append(f["dif"])
                info[clave] = {g: resumen_dif(v, rng) for g, v in sorted(grupos.items())}
            cs_v = np.array([f["cumpl_sistema"] for f in filas], dtype=float)
            cb_v = np.array([f["cumpl_bench"] for f in filas], dtype=float)
            info["cumplimiento"] = {"sistema": float(np.nanmean(cs_v)), "benchmark": float(np.nanmean(cb_v)),
                                    "sistema_bajo_umbral": bool(np.nanmean(cs_v) < UMBRAL_CUMPLIMIENTO)}
            if penalizaciones:
                info["ajustado"] = {}
                for pen in penalizaciones:
                    d = [costo_ajustado(f["slip_sistema"], f["cumpl_sistema"], pen) - costo_ajustado(f["slip_bench"], f["cumpl_bench"], pen)
                         for f in filas]
                    por_t: Dict[str, List[float]] = {}
                    for f, x in zip(filas, d):
                        por_t.setdefault(str(f["tramo"]), []).append(x)
                    info["ajustado"][f"{pen:g}"] = {"global": resumen_dif(d, rng),
                                                    "por_tramo": {g: resumen_dif(v, rng) for g, v in sorted(por_t.items())}}
        out["benchmarks"][b] = info
    return out


def _veredicto(r: Optional[Dict]) -> str:
    if not r or r.get("dif_media") is None:
        return "sin datos"
    lo, hi = r["ic95"]
    if lo is None:
        return "pocos datos"
    if hi < 0:
        return "el sistema cuesta menos (IC95 % bajo 0)"
    if lo > 0:
        return "el sistema cuesta mas (IC95 % sobre 0)"
    return "sin diferencia clara (IC95 % incluye 0)"


def informe(resultados: Dict[str, Dict], meta: Dict) -> str:
    L = ["# Sistema Maestro-Ejecutores frente a TWAP y VWAP (tareas 3.2.3 y 3.2.4)", "",
         "**Borrador elaborado por:** PS con apoyo de Claude Code. "
         f"**Sistema comparado:** {meta['sistema']} · **Fecha:** {meta['fecha']}", "",
         "Diferencia = slippage del sistema − slippage del benchmark, en bps, pareada por orden y semilla (negativa = el sistema cuesta menos). "
         "IC 95 % por bootstrap sobre las diferencias.", "",
         "## 1. Resumen por tamaño de orden", "",
         "| Comparación | Benchmark | Celdas | Dif. media (bps) | IC 95 % | Wilcoxon p (celdas) | Wilcoxon p (órdenes) | Lectura |", "|---|---|---:|---:|---|---:|---:|---|"]
    for etiqueta, res in resultados.items():
        for b, info in res["benchmarks"].items():
            g = info["global"]
            if not g:
                L.append(f"| {etiqueta} | {b} | 0 | — | — | — | — | sin datos |")
                continue
            po = info["por_orden"]
            L.append(f"| {etiqueta} | {b} | {g['n']} | {_f(g['dif_media'])} | [{_f(g['ic95'][0])}; {_f(g['ic95'][1])}] | {_f(g['wilcoxon_p'], 3)} | "
                     f"{_f(po['wilcoxon_p'], 3)} | {_veredicto(g)} |")
    if any(info.get("ajustado") for res in resultados.values() for info in res["benchmarks"].values()):
        L += ["", "### Costo ajustado por lo no ejecutado", "",
              "El slippage solo cuenta lo que se compró. Aquí el costo se reparte por unidad de la orden completa y lo no comprado se castiga con una "
              "penalización supuesta: `costo ajustado = slippage × cumplimiento + penalización × (1 − cumplimiento)`. Como la penalización es un supuesto, "
              "se muestran varios valores; si la conclusión no cambia con ellos, es robusta.", "",
              "| Comparación | Benchmark | Penalización (bps) | Dif. media ajustada (bps) | IC 95 % | Wilcoxon p (celdas) | Lectura |", "|---|---|---:|---:|---|---:|---|"]
        for etiqueta, res in resultados.items():
            for b, info in res["benchmarks"].items():
                for pen, a in (info.get("ajustado") or {}).items():
                    g = a["global"]
                    L.append(f"| {etiqueta} | {b} | {pen} | {_f(g['dif_media'])} | [{_f(g['ic95'][0])}; {_f(g['ic95'][1])}] | {_f(g['wilcoxon_p'], 3)} | {_veredicto(g)} |")
    for etiqueta, res in resultados.items():
        L += ["", f"## 2. Detalle: {etiqueta}", ""]
        for b, info in res["benchmarks"].items():
            L += [f"### {meta['sistema']} frente a {b}", "",
                  f"Celdas comunes: {info['celdas_comunes']} (sin ejecución en alguna de las dos: {info['celdas_sin_ejecucion']}).", ""]
            if not info["global"]:
                L += ["Sin celdas comparables.", ""]
                continue
            L += ["| Grupo | Celdas | Dif. media (bps) | IC 95 % | Sistema mejor en |", "|---|---:|---:|---|---:|"]
            for nombre, grupos in (("Tramo", info["por_tramo"]), ("Activo", info["por_activo"])):
                for g, r in grupos.items():
                    L.append(f"| {nombre}: {g} | {r['n']} | {_f(r['dif_media'])} | [{_f(r['ic95'][0])}; {_f(r['ic95'][1])}] | {_f(100 * r['frac_sistema_mejor'], 0)} % |")
            c = info["cumplimiento"]
            L += ["", f"Cumplimiento medio: sistema {_f(100 * c['sistema'], 1)} %, {b} {_f(100 * c['benchmark'], 1)} %."
                  + (" **El sistema queda bajo el 95 %: la comparación de costo no es equivalente.**" if c["sistema_bajo_umbral"] else ""), ""]
    L += ["## 3. Limitaciones", "",
          "- Las semillas de una misma orden se parecen entre sí (mismo día simulado): por eso se informa también el Wilcoxon por orden, que usa una media por orden y es más conservador.",
          "- El slippage de una corrida solo cuenta lo ejecutado: con cumplimiento menor que 100 % el costo de lo no ejecutado no entra.",
          "- Para que el pareo sea válido el sistema debe evaluarse con las mismas semillas que los benchmarks.",
          "- El slippage absoluto en ABIDES no es el real (ver `docs/validacion_formal_2.2.5_PS.md`); la comparación relativa sí es informativa.", "",
          "🤖 Generado con [Claude Code](https://claude.com/claude-code)", ""]
    return "\n".join(L)


def figura(resultados: Dict[str, Dict], ruta: Path) -> Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    filas = []
    for etiqueta, res in resultados.items():
        for b, info in res["benchmarks"].items():
            if info["global"]:
                filas.append((f"{etiqueta} · {b}", info["global"]))
                for g, r in info["por_tramo"].items():
                    filas.append((f"   {g}", r))
    fig, ax = plt.subplots(figsize=(8, max(3, 0.32 * len(filas) + 1.5)))
    for i, (nombre, r) in enumerate(filas):
        y = len(filas) - 1 - i
        if r["ic95"][0] is not None:
            ax.plot(r["ic95"], [y, y], color="#1E2761", lw=2 if not nombre.startswith("   ") else 1)
        ax.plot([r["dif_media"]], [y], "o", color="#1E2761", ms=5 if not nombre.startswith("   ") else 3)
    ax.axvline(0, color="k", lw=0.7)
    ax.set_yticks(range(len(filas)))
    ax.set_yticklabels([n for n, _ in filas][::-1], fontsize=8)
    ax.set_xlabel("sistema − benchmark (bps); a la izquierda, el sistema cuesta menos")
    ax.grid(alpha=0.3, axis="x")
    fig.tight_layout()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta, dpi=130)
    plt.close(fig)
    return ruta


def _par(valor: str) -> Tuple[str, str, str]:
    etiqueta, sep, resto = valor.partition("=")
    partes = resto.split(",")
    if not sep or len(partes) != 2 or not all(partes):
        raise argparse.ArgumentTypeError(f"se esperaba ETIQUETA=benchmarks.json,sistema.json, llego {valor!r}")
    return etiqueta, partes[0], partes[1]


def main(argv: Optional[Sequence[str]] = None) -> Path:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--comparacion", action="append", type=_par, required=True, metavar="ETIQUETA=BENCHMARKS.json,SISTEMA.json")
    ap.add_argument("--nombre-sistema", default="PPO", help="valor de `estrategia` del sistema en su archivo")
    ap.add_argument("--penalizaciones-no-ejecutado", nargs="*", type=float, default=[], metavar="BPS",
                    help="penalizaciones (bps) para el costo ajustado por lo no ejecutado; por defecto no se calcula")
    ap.add_argument("--out-json", default=str(REPO_ROOT / "data/analysis/sistema_vs_benchmarks.json"))
    ap.add_argument("--out-png", default=str(REPO_ROOT / "data/analysis/sistema_vs_benchmarks.png"))
    ap.add_argument("--out-md", default=str(REPO_ROOT / "docs/sistema_vs_benchmarks_3.2.3.md"))
    args = ap.parse_args(argv)

    resultados: Dict[str, Dict] = {}
    for etiqueta, bench, sis in args.comparacion:
        resultados[etiqueta] = comparar(cargar(bench), cargar(sis), args.nombre_sistema, penalizaciones=args.penalizaciones_no_ejecutado)
    meta = {"sistema": args.nombre_sistema, "fecha": time.strftime("%Y-%m-%d")}
    for res in resultados.values():                       # las filas por celda no se guardan en el resumen JSON
        for info in res["benchmarks"].values():
            info.pop("filas", None)
    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).write_text(json.dumps({"meta": meta, "resultados": resultados}, indent=1, ensure_ascii=False), encoding="utf-8")
    figura(resultados, Path(args.out_png))
    Path(args.out_md).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_md).write_text(informe(resultados, meta), encoding="utf-8")
    print(f"JSON: {args.out_json}\nFigura: {args.out_png}\nInforme: {args.out_md}")
    return Path(args.out_md)


if __name__ == "__main__":
    main()
