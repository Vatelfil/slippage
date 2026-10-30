"""Análisis de la reevaluación con 300 semillas que incluye las redes con la recompensa corregida (`mid_decision`).

Compara cada red con su control (la misma red sin entrenar, muestreando) y con TWAP límite, por grupo de recompensa, y
aplica la regla de D3 (opción A frente a opción 0 en las mismas semillas de red). Pareado por semilla de evaluación;
IC 95 % por bootstrap (3.000 remuestreos) y Wilcoxon.

    python scripts/analizar_reeval_mid_ps.py --dir data/colab_resultados/reeval_300_mid --out-md docs/reeval_300_mid_ABIDES_PS.md
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, Optional, Sequence

import numpy as np
from scipy.stats import wilcoxon

GRUPOS = (("rmid", "recompensa corregida (mid_decision)"), ("conf_pen30_g1", "V2: original + penalización + γ = 1"),
          ("v4_pen30_g1", "V4: precio de llegada + penalización + γ = 1"), ("d3_1000ep", "original, γ = 0,95"))


def _arr(r: Dict) -> np.ndarray:
    return np.array([np.nan if x is None else x for x in r["slippage_por_semilla"]], dtype=float)


def _ic(d: np.ndarray) -> Dict[str, float]:
    d = d[np.isfinite(d)]
    b = np.random.default_rng(0).choice(d, size=(3000, len(d))).mean(axis=1)
    return {"media": float(d.mean()), "ic_bajo": float(np.percentile(b, 2.5)), "ic_alto": float(np.percentile(b, 97.5)),
            "p_wilcoxon": float(wilcoxon(d).pvalue), "n": int(len(d))}


def analizar(carpeta: Path) -> Dict:
    leer = lambda f: json.loads(f.read_text(encoding="utf-8"))  # noqa: E731
    control = {int(re.search(r"s(\d+)", f.stem).group(1)): _arr(leer(f)) for f in carpeta.glob("control_s*.json")}
    twap = _arr(leer(carpeta / "ref_twap_limit_medio.json"))
    redes, por_grupo = [], {}
    for f in sorted(carpeta.glob("red_*.json")):
        nombre = f.stem[4:]
        r, s = leer(f), int(re.search(r"_s(\d+)$", f.stem).group(1))
        x = _arr(r)
        grupo = next((g for g, _ in GRUPOS if nombre.startswith(g)), "otro") + ("_opcionA" if "opcionA" in nombre else "")
        fila = {"red": nombre, "grupo": grupo, "slippage": float(np.nanmean(x)), "cumplimiento": r["cumplimiento_medio"],
                "menos_control": _ic(x - control[s]), "menos_twap_limite": _ic(x - twap)}
        redes.append(fila)
        por_grupo.setdefault(grupo, []).append(x - control[s])
    grupos = {g: dict(_ic(np.nanmean(np.vstack(v), axis=0)), redes=len(v)) for g, v in por_grupo.items()}
    d3 = {}
    a1, o1 = carpeta / "red_rmid_A__d3_opcionA_s1000.json", carpeta / "red_rmid_A__d3_opcion0_s1000.json"
    a2, o2 = carpeta / "red_rmid_B__d3_opcionA_s2000.json", carpeta / "red_rmid_A__d3_opcion0_s2000.json"
    if all(p.exists() for p in (a1, o1, a2, o2)):
        d1, d2 = _arr(leer(a1)) - _arr(leer(o1)), _arr(leer(a2)) - _arr(leer(o2))
        d3 = {"semilla_1000": _ic(d1), "semilla_2000": _ic(d2), "juntas": _ic((d1 + d2) / 2)}
    refs = {n: float(np.nanmean(_arr(leer(carpeta / f"ref_{n}.json")))) for n in ("twap_limit_medio", "agresiva_market", "pasiva_limit")}
    return {"redes": redes, "grupos": grupos, "d3_A_menos_0": d3, "referencias": refs,
            "controles": {s: float(np.nanmean(v)) for s, v in sorted(control.items())}}


def _f(d: Dict) -> str:
    return f"{d['media']:+.2f} [{d['ic_bajo']:+.2f}; {d['ic_alto']:+.2f}] (p = {d['p_wilcoxon']:.3f})"


def informe(an: Dict) -> str:
    l = ["# Reevaluación con 300 semillas, incluida la recompensa corregida (tabla generada)\n",
         "Generado por `scripts/analizar_reeval_mid_ps.py`. Diferencias en bps, pareadas por semilla de evaluación "
         "(5001 a 5300); negativo es mejor. Lectura en `docs/reeval_300_mid_resultado_PS.md`.\n",
         "## Por grupo (promedio de las redes del grupo − su control)\n", "| Grupo | Redes | Diferencia, IC 95 % |", "|---|---:|---|"]
    for g, d in an["grupos"].items():
        l.append(f"| {g} | {d['redes']} | {_f(d)} |")
    l += ["\n## Por red\n", "| Red | Slippage | Cumplimiento | − control | − TWAP límite |", "|---|---:|---:|---|---|"]
    for r in an["redes"]:
        l.append(f"| `{r['red']}` | {r['slippage']:.2f} | {r['cumplimiento']:.3f} | {_f(r['menos_control'])} | {_f(r['menos_twap_limite'])} |")
    if an["d3_A_menos_0"]:
        l += ["\n## D3: opción A − opción 0 (recompensa corregida, misma semilla de red)\n", "| Comparación | Diferencia |", "|---|---|"]
        for k, d in an["d3_A_menos_0"].items():
            l.append(f"| {k} | {_f(d)} |")
    ref = an["referencias"]
    l.append(f"\nReferencias: TWAP límite {ref['twap_limit_medio']:.2f}, agresiva {ref['agresiva_market']:.2f}, pasiva "
             f"{ref['pasiva_limit']:.2f} bps; controles {', '.join(f'{v:.2f}' for v in an['controles'].values())} bps.\n")
    return "\n".join(l)


def main(argv: Optional[Sequence[str]] = None) -> Dict:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out-md", default=None)
    ap.add_argument("--out-json", default=None)
    args = ap.parse_args(argv)
    an = analizar(Path(args.dir))
    if args.out_md:
        Path(args.out_md).write_text(informe(an), encoding="utf-8")
    if args.out_json:
        Path(args.out_json).write_text(json.dumps(an, indent=1, ensure_ascii=False), encoding="utf-8")
    for g, d in an["grupos"].items():
        print(f"{g:24s} {_f(d)}")
    return an


if __name__ == "__main__":
    main()
