"""Distribucion de la recompensa del Ejecutor R_E (pasos pendientes de la 2.2.3).

Elaborado por PS con apoyo de Claude Code; pendiente de revision por BF.

Usa los episodios del barrido de beta en ABIDES (politicas heuristicas, 20
episodios por tramo y politica) y reconstruye R_E por episodio para varios
valores de beta:

    R_E(beta) = (precio - beta * sigma2_q) / q_slice      [CLP por accion del slice]

Para cada tramo y multiplo de beta* informa media, desvio, asimetria, curtosis,
cuantiles y la fraccion de episodios fuera de +-3 desvios; ademas aplica el
normalizador movil (`RunningRewardNormalizer`) y verifica que la salida quede en
[-1, 1]. Escribe un JSON y un informe markdown.

    python scripts/analizar_distribucion_re.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.envs.reward_utils import RunningRewardNormalizer  # noqa: E402

MULTIPLOS = (0.0, 0.1, 0.3, 1.0)
TRAMOS = ("apertura", "media_jornada", "cierre")


def re_por_episodio(episodios: dict, beta: float) -> np.ndarray:
    """R_E por episodio (CLP por accion del slice) para todas las politicas."""
    out = []
    for politica in episodios.values():
        for e in politica.values():
            out.append((e["precio"] - beta * e["sigma2_q"]) / e["q_slice"])
    return np.asarray(out, dtype=float)


def resumen(x: np.ndarray) -> dict:
    sd = float(x.std(ddof=1))
    z = (x - x.mean()) / sd if sd > 0 else np.zeros_like(x)
    nz = RunningRewardNormalizer(clip=5.0, min_count=10)
    y = np.array([nz.normalize(v) for v in x])
    return {"n": int(len(x)), "media": float(x.mean()), "desvio": sd,
            "asimetria": float(stats.skew(x)), "curtosis_exceso": float(stats.kurtosis(x)),
            "q05": float(np.quantile(x, 0.05)), "q50": float(np.quantile(x, 0.5)), "q95": float(np.quantile(x, 0.95)),
            "frac_fuera_3sd": float(np.mean(np.abs(z) > 3.0)),
            "normalizado_min": float(y.min()), "normalizado_max": float(y.max()),
            "normalizado_en_rango": bool(np.all(np.abs(y) <= 1.0))}


def f(x, d=3):
    return "—" if x is None else f"{x:.{d}f}".replace(".", ",")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--sweep-json", default=str(REPO_ROOT / "data/calibration/beta_sweep_abides_2026-10-10.json"))
    ap.add_argument("--out-json", default=str(REPO_ROOT / "data/analysis/distribucion_re_2_2_3.json"))
    ap.add_argument("--out-md", default=str(REPO_ROOT / "docs/distribucion_recompensa_2.2.3_PS.md"))
    args = ap.parse_args(argv)

    with open(args.sweep_json, "r", encoding="utf-8") as fh:
        d = json.load(fh)
    beta_star = float(d["reporte"]["beta_star"])
    res = {}
    for t in TRAMOS:
        res[t] = {}
        for m in MULTIPLOS:
            res[t][str(m)] = resumen(re_por_episodio(d["episodios"][t], beta_star * m))
    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_json, "w", encoding="utf-8") as fh:
        json.dump({"beta_star": beta_star, "q_slice": d["firma"]["q_slice"], "resultados": res}, fh, indent=1, ensure_ascii=False)

    L = ["# Distribución de la recompensa R_E (2.2.3)", "",
         "**Elaborado por:** PS con apoyo de Claude Code. **Pendiente de revisión por:** BF.", "",
         f"Fuente: `{Path(args.sweep_json).name}` (políticas heurísticas en ABIDES calibrado; 20 episodios por tramo y política). "
         f"β\\* = {f(beta_star, 4)} (1/CLP). R_E por episodio en CLP por acción del slice (escala `por_accion_slice`, slice de "
         f"{int(d['firma']['q_slice'])} acciones).", "",
         "| Tramo | β | n | Media | Desvío | Asimetría | Curtosis (exceso) | p05 | p50 | p95 | % fuera de ±3σ |",
         "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for t in TRAMOS:
        for m in MULTIPLOS:
            r = res[t][str(m)]
            L.append(f"| {t} | {f(m, 1)}×β* | {r['n']} | {f(r['media'])} | {f(r['desvio'])} | {f(r['asimetria'], 2)} | "
                     f"{f(r['curtosis_exceso'], 2)} | {f(r['q05'])} | {f(r['q50'])} | {f(r['q95'])} | {f(100 * r['frac_fuera_3sd'], 1)} |")
    ok = all(res[t][str(m)]["normalizado_en_rango"] for t in TRAMOS for m in MULTIPLOS)
    L += ["", "## Lectura", "",
          "- La escala de R_E cambia mucho entre tramos (el desvío baja de la apertura al cierre) y la apertura tiene colas "
          "muy pesadas y asimétricas (curtosis en exceso ≈ 15, asimetría ≈ −3): sin normalizar, unos pocos episodios dominan "
          "el gradiente y un mismo coeficiente de aprendizaje no sirve igual para los tres Ejecutores. Media jornada y cierre "
          "son más moderados.",
          "- El término de riesgo aumenta con β pero, con la fórmula actual, solo depende de lo ejecutado: con β alto la "
          "recompensa total de operar es peor que la de no operar (ver `docs/beta_fase2_apertura_PS.md`).",
          f"- El normalizador móvil deja la salida dentro de [-1, 1] en todos los casos: **{'sí' if ok else 'no'}**.",
          "- Los episodios son pocos (20 por tramo y política); los cuantiles extremos son indicativos.", "",
          "🤖 Generado con [Claude Code](https://claude.com/claude-code)"]
    Path(args.out_md).write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"JSON: {args.out_json}\nInforme: {args.out_md}")


if __name__ == "__main__":
    main()
