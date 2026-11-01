"""Control de la 3.2.3: qué aporta el Maestro y qué aportan los Ejecutores (PS, 1 nov 2026, con apoyo de Claude Code).

Compara, en las mismas órdenes, semillas y escenarios (pareado):

1. **Regla fija − sistema**: ¿el Maestro entrenado hace algo distinto de «α = 0,5 y 15 min siempre»?
2. **Sistema − regla uniforme**: aporte del *calendario* del Maestro (los dos usan los mismos Ejecutores).
3. **Regla uniforme − TWAP**: aporte de los *Ejecutores* (los dos usan el calendario de TWAP).

Las comparaciones 2 y 3 suman exactamente sistema − TWAP, corrida por corrida, así que la ventaja (o desventaja) del
sistema se reparte entre el Maestro y los Ejecutores. Wilcoxon pareado con Holm sobre las tres comparaciones.
Es un análisis agregado al plan después de ver la liquidez media (declarado en `docs/control_reglas_3_2_3_PS.md`);
no reemplaza al test principal de la 3.2.3.

    python scripts/control_reglas_3_2_3.py --entradas <carpeta media 90> <carpeta control> \
        --out-dir data/analysis/3_2_3_control --out-md docs/control_reglas_3_2_3_resultado_PS.md
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.comparacion_estadistica_3_2_3 import CLAVE, cargar, holm, magnitud_d, resumen  # noqa: E402
from scripts.consolidar_resultados_3_2_2 import costo  # noqa: E402

SISTEMA, FIJA, UNIFORME, TWAP = "PPO_sistema", "Regla_fija", "Regla_uniforme", "TWAP"
COMPARACIONES = (
    ("maestro_vs_regla_fija", FIJA, SISTEMA, "Regla fija − sistema", "¿El Maestro hace algo distinto de «α = 0,5 siempre»?"),
    ("aporte_calendario", SISTEMA, UNIFORME, "Sistema − regla uniforme", "Aporte del calendario del Maestro (mismos Ejecutores)"),
    ("aporte_ejecutores", UNIFORME, TWAP, "Regla uniforme − TWAP", "Aporte de los Ejecutores (mismo calendario que TWAP)"),
)


def pares(df: pd.DataFrame, a: str, b: str) -> pd.DataFrame:
    """Diferencias a − b por escenario, tamaño, orden y semilla (solo los pares completos)."""
    piv = df.pivot_table(index=CLAVE, columns="estrategia", values="costo", aggfunc="mean")
    if a not in piv.columns or b not in piv.columns:
        return pd.DataFrame(columns=CLAVE + ["a", "b", "dif"])
    p = piv[[a, b]].dropna().reset_index().rename(columns={a: "a", b: "b"})
    p["dif"] = p["a"] - p["b"]
    return p


def igual_al_sistema(df: pd.DataFrame, tol_bps: float = 1e-6) -> Optional[Dict]:
    """Cuántas corridas de la regla fija salen idénticas al sistema (pasa cuando el Maestro eligió α = 0,5 en todo)."""
    p = pares(df, FIJA, SISTEMA)
    if p.empty:
        return None
    return {"n": int(len(p)), "identicas": int((p["dif"].abs() <= tol_bps).sum())}


def descomposicion(df: pd.DataFrame) -> Optional[Dict]:
    """sistema − TWAP = (sistema − uniforme) + (uniforme − TWAP), en promedio, con la comprobación de que suma."""
    piv = df.pivot_table(index=CLAVE, columns="estrategia", values="costo", aggfunc="mean")
    if not {SISTEMA, UNIFORME, TWAP} <= set(piv.columns):
        return None
    p = piv[[SISTEMA, UNIFORME, TWAP]].dropna()
    total = (p[SISTEMA] - p[TWAP]).mean()
    cal = (p[SISTEMA] - p[UNIFORME]).mean()
    eje = (p[UNIFORME] - p[TWAP]).mean()
    return {"n": int(len(p)), "sistema_menos_twap": float(total), "calendario": float(cal), "ejecutores": float(eje),
            "cuadra": bool(abs(total - cal - eje) < 1e-6)}


def por_movimiento(df: pd.DataFrame) -> Optional[Dict]:
    """Aporte del calendario según el día: TWAP con costo ≥ 0 (el precio subió) o < 0 (el precio bajó). Descriptivo."""
    piv = df.pivot_table(index=CLAVE, columns="estrategia", values="costo", aggfunc="mean")
    if not {SISTEMA, UNIFORME, TWAP} <= set(piv.columns):
        return None
    p = piv[[SISTEMA, UNIFORME, TWAP]].dropna()
    cal = p[SISTEMA] - p[UNIFORME]
    sube, baja = p[TWAP] >= 0, p[TWAP] < 0
    return {"sube": {"n": int(sube.sum()), "calendario": float(cal[sube].mean()) if sube.any() else None},
            "baja": {"n": int(baja.sum()), "calendario": float(cal[baja].mean()) if baja.any() else None}}


def analizar(df: pd.DataFrame) -> Dict:
    filas: List[Dict] = []
    for clave, a, b, etiqueta, pregunta in COMPARACIONES:
        p = pares(df, a, b)
        r = resumen(p["dif"].to_numpy(), base=p["b"].to_numpy()) if len(p) else {"n": 0}
        r.update({"clave": clave, "a": a, "b": b, "etiqueta": etiqueta, "pregunta": pregunta})
        filas.append(r)
    for r, ph in zip(filas, holm([r.get("wilcoxon_p") for r in filas])):
        r["wilcoxon_p_holm"] = ph
    return {"comparaciones": filas, "igual_al_sistema": igual_al_sistema(df), "descomposicion": descomposicion(df),
            "por_movimiento": por_movimiento(df), "estrategias": sorted(df["estrategia"].unique().tolist())}


def _f(x, d: int = 2) -> str:
    return "—" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{d}f}"


def informe(res: Dict, titulo: str, fuentes: str) -> str:
    L = [f"# {titulo}", "", fuentes, "",
         "Diferencia en bps, pareada por escenario, orden y semilla. **Negativa = la primera estrategia cuesta menos.** "
         "IC 95 % por bootstrap. Wilcoxon con corrección de Holm sobre las tres comparaciones.", "",
         "| Comparación | Pregunta | n | Dif. media | IC 95 % | Wilcoxon p | p (Holm) | d de Cohen | Gana la primera |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in res["comparaciones"]:
        if not r.get("n"):
            L.append(f"| {r['etiqueta']} | {r['pregunta']} | 0 | — | — | — | — | — | — |")
            continue
        ic = r["ic95"]
        L.append(f"| {r['etiqueta']} | {r['pregunta']} | {r['n']} | {_f(r['dif_media'])} | [{_f(ic[0])}; {_f(ic[1])}] | "
                 f"{_f(r['wilcoxon_p'], 3)} | {_f(r['wilcoxon_p_holm'], 3)} | {_f(r['d_cohen'])} ({magnitud_d(r['d_cohen'])}) | "
                 f"{r['gana_sistema']}/{r['n']} |")
    ig = res.get("igual_al_sistema")
    if ig:
        L += ["", f"**Regla fija igual al sistema:** {ig['identicas']} de {ig['n']} corridas salen idénticas "
                  "(son las órdenes en que el Maestro eligió α = 0,5 y 15 min en todas sus decisiones)."]
    de = res.get("descomposicion")
    if de:
        L += ["", "## Descomposición de la diferencia con TWAP", "",
              "| | bps |", "|---|---|",
              f"| Sistema − TWAP (total) | {_f(de['sistema_menos_twap'])} |",
              f"| … por el calendario del Maestro (sistema − uniforme) | {_f(de['calendario'])} |",
              f"| … por los Ejecutores (uniforme − TWAP) | {_f(de['ejecutores'])} |",
              "", f"n = {de['n']}. La suma cuadra: {'sí' if de['cuadra'] else 'NO (revisar)'}."]
    pm = res.get("por_movimiento")
    if pm:
        L += ["", "**Aporte del calendario según el día** (descriptivo): "
                  f"cuando el precio subió (TWAP ≥ 0, n = {pm['sube']['n']}) fue {_f(pm['sube']['calendario'])} bps; "
                  f"cuando bajó (TWAP < 0, n = {pm['baja']['n']}) fue {_f(pm['baja']['calendario'])} bps."]
    return "\n".join(L) + "\n"


def figura(res: Dict, out: Path) -> Optional[Path]:
    """Barras de la diferencia media con su IC para las tres comparaciones."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    filas = [r for r in res["comparaciones"] if r.get("n")]
    if not filas:
        return None
    fig, ax = plt.subplots(figsize=(7, 3.6))
    y = np.arange(len(filas))[::-1]
    medias = [r["dif_media"] for r in filas]
    err = np.array([[m - r["ic95"][0], r["ic95"][1] - m] for m, r in zip(medias, filas)]).T
    colores = ["#9aa5b1", "#2e7d5b", "#7fb069"][:len(filas)]
    ax.barh(y, medias, xerr=err, color=colores, capsize=4)
    ax.axvline(0, color="#333", lw=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels([r["etiqueta"] for r in filas])
    ax.set_xlabel("Diferencia media de costo (bps), IC 95 %  —  negativo = la primera cuesta menos")
    ax.set_title("Qué aporta cada nivel del sistema")
    fig.tight_layout()
    ruta = out / "control_reglas.png"
    fig.savefig(ruta, dpi=150)
    plt.close(fig)
    return ruta


def main(argv: Optional[Sequence[str]] = None) -> Dict:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--entradas", nargs="+", required=True, help="carpetas o JSON con el sistema, las reglas y TWAP")
    ap.add_argument("--penalizacion-bps", type=float, default=None, help="costo ajustado por lo no ejecutado")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--out-md", default=None)
    ap.add_argument("--titulo", default="Control de la 3.2.3: aporte del Maestro y de los Ejecutores")
    ap.add_argument("--sin-figuras", action="store_true")
    args = ap.parse_args(argv)

    df = cargar(args.entradas)
    if df.empty:
        sys.exit("No hay corridas válidas en las entradas.")
    df["costo"] = costo(df, args.penalizacion_bps)
    res = analizar(df)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "control_reglas.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=float), encoding="utf-8")
    md = informe(res, args.titulo, "Entradas: " + ", ".join(f"`{e}`" for e in args.entradas) + ".")
    (out / "control_reglas.md").write_text(md, encoding="utf-8")
    if args.out_md:
        Path(args.out_md).write_text(md, encoding="utf-8")
    if not args.sin_figuras:
        f = figura(res, out)
        res["figura"] = str(f) if f else None
    try:
        print(md)
    except UnicodeEncodeError:   # consola de Windows sin UTF-8
        print(md.encode("ascii", "replace").decode())
    return res


if __name__ == "__main__":
    main()
