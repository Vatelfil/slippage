"""Figuras y cifras exploratorias del Capitulo 7 (PS, 15 nov 2026): diferencia sistema - TWAP por tramo de inicio
y por direccion del dia en las 90 corridas, y costo frente al tamano (0,5 y 1) en profundidad x1.

Uso: python scripts/figuras_capitulo7_PS.py --out-dir data/analysis/cap7
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
ESC = [("baja", "×4"), ("media", "×1"), ("alta", "×0,25")]
TRAMOS = [("apertura", "apertura"), ("media_jornada", "media jornada"), ("cierre", "cierre")]
VERDE, GRIS = "#0B6E64", "#7A7A7A"


def ic_boot(x, n=10000, seed=0):
    rng = np.random.default_rng(seed)
    x = np.asarray(x, float)
    m = rng.choice(x, (n, len(x))).mean(1)
    return [float(v) for v in np.percentile(m, [2.5, 97.5])]


def cargar_90():
    d = pd.concat([pd.read_csv(ROOT / f"data/colab_resultados/corridas_90/{e}/tabla/corridas.csv").assign(esc=k)
                   for e, k in ESC])
    tramo = d[d.estrategia == "PPO_sistema"].set_index(["esc", "orden", "seed"])["tramo_inicio"]
    p = d.pivot_table(index=["esc", "orden", "seed"], columns="estrategia", values="costo")
    p["dif"] = p["PPO_sistema"] - p["TWAP"]
    p["tramo"] = tramo
    return p


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="data/analysis/cap7")
    a = ap.parse_args(argv)
    out = Path(a.out_dir) if Path(a.out_dir).is_absolute() else ROOT / a.out_dir
    out.mkdir(parents=True, exist_ok=True)
    res = {}
    p = cargar_90()
    # direccion del dia
    r, pr = stats.pearsonr(p["dif"], p["TWAP"])
    rho, prho = stats.spearmanr(p["dif"], p["TWAP"])
    sube = p["TWAP"] >= 0
    res["dia"] = {"n": int(len(p)), "pearson_r": float(r), "pearson_p": float(pr), "spearman_rho": float(rho),
                  "spearman_p": float(prho), "sube_n": int(sube.sum()), "sube_dif": float(p.loc[sube, "dif"].mean()),
                  "baja_n": int((~sube).sum()), "baja_dif": float(p.loc[~sube, "dif"].mean())}
    # tramo
    grupos = {t: p.loc[p["tramo"] == t, "dif"].to_numpy() for t, _ in TRAMOS}
    kw = stats.kruskal(*grupos.values())
    pw = {t: float(stats.wilcoxon(v).pvalue) for t, v in grupos.items()}
    orden = sorted(pw, key=pw.get)
    holm, prev = {}, 0.0
    for i, t in enumerate(orden):
        prev = max(prev, min(1.0, pw[t] * (len(orden) - i)))
        holm[t] = prev
    res["tramo"] = {"kruskal_H": float(kw.statistic), "kruskal_p": float(kw.pvalue),
                    "grupos": {t: {"n": int(len(v)), "media": float(v.mean()), "mediana": float(np.median(v)),
                                   "ic95": ic_boot(v), "wilcoxon_p": pw[t], "wilcoxon_p_holm": holm[t]}
                               for t, v in grupos.items()}}
    # tamano 0,5 vs 1 en x1
    t1 = pd.read_csv(ROOT / "data/colab_resultados/corridas_90/media/tabla/corridas.csv").assign(f=1.0)
    t05 = pd.read_csv(ROOT / "data/colab_resultados/tamanos/media_f0.5/tabla/corridas.csv").assign(f=0.5)
    q = pd.concat([t1, t05]).pivot_table(index=["orden", "seed"], columns=["f", "estrategia"], values="costo")
    res["tamano"] = {}
    for s in ["PPO_sistema", "TWAP", "VWAP"]:
        x = (q[(1.0, s)] - q[(0.5, s)]).to_numpy()
        res["tamano"][s] = {"is_05": float(q[(0.5, s)].mean()), "is_1": float(q[(1.0, s)].mean()),
                            "pendiente_por_0_5": float(x.mean()), "ic95": ic_boot(x),
                            "wilcoxon_p": float(stats.wilcoxon(x).pvalue)}
    dd = ((q[(1.0, "PPO_sistema")] - q[(1.0, "TWAP")]) - (q[(0.5, "PPO_sistema")] - q[(0.5, "TWAP")])).to_numpy()
    res["tamano"]["cambio_ventaja"] = {"media": float(dd.mean()), "ic95": ic_boot(dd),
                                       "wilcoxon_p": float(stats.wilcoxon(dd).pvalue)}
    (out / "cifras_capitulo7.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")

    # figura 1: diferencia por tramo
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    datos = [grupos[t] for t, _ in TRAMOS]
    ax.boxplot(datos, widths=0.5, showfliers=False)
    for k, v in enumerate(datos, start=1):
        ax.scatter(np.full(len(v), k) + np.random.default_rng(k).uniform(-0.12, 0.12, len(v)), v, s=12,
                   color=VERDE, alpha=0.7)
    ax.set_xticks([1, 2, 3])
    ax.set_xticklabels([f"{n}\n(n = {len(grupos[t])}; p Holm = {holm[t]:.3f})" for t, n in TRAMOS], fontsize=8)
    ax.axhline(0, color="#C0392B", lw=1, ls="--")
    ax.set_ylabel("sistema − TWAP por corrida (bps)")
    ax.set_title(f"Diferencia sistema − TWAP por tramo de inicio, 90 corridas (Kruskal-Wallis p = {kw.pvalue:.3f})",
                 fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out / "diferencia_por_tramo.png", dpi=130)
    plt.close(fig)

    # figura 2: costo frente al tamano
    fig, ax = plt.subplots(figsize=(6.0, 4.0))
    for s, c in [("PPO_sistema", VERDE), ("TWAP", GRIS), ("VWAP", "#B07D2B")]:
        ax.plot([0.5, 1.0], [res["tamano"][s]["is_05"], res["tamano"][s]["is_1"]], "o-", color=c,
                label=f"{s}: +{res['tamano'][s]['pendiente_por_0_5']:.1f} bps (p = {res['tamano'][s]['wilcoxon_p']:.1e})")
    ax.set_xticks([0.5, 1.0])
    ax.set_xticklabels(["0,5 (5 % del día)", "1 (10 % del día)"])
    ax.set_ylabel("costo medio (bps)")
    ax.set_title("Costo medio frente al factor de tamaño, profundidad ×1 (n = 30 pares)", fontsize=9)
    ax.legend(fontsize=7)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out / "costo_vs_tamano_parcial.png", dpi=130)
    plt.close(fig)
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
