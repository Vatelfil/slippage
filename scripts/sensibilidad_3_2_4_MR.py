"""Análisis de sensibilidad 3.2.4 (MR, Sprint 8).

Calcula la sensibilidad del Implementation Shortfall (IS, bps) frente a:
  1. Tamaño de orden (diseño en estrella en profundidad ×1: factores 0,5, 1,0 y 1,5; n = 30 días pareados).
  2. Profundidad del market maker (tamaño 1,0: factores ×0,25, ×1 y ×4; n = 30 días pareados).
  3. Tramo horario de inicio (90 corridas en tamaño 1,0: apertura n = 36, media_jornada n = 27, cierre n = 27).

Para cada eje reporta derivadas numéricas (∂IS/∂parámetro) con IC 95 % por bootstrap pareado,
pruebas no paramétricas (Friedman, Spearman, Kruskal-Wallis y Wilcoxon con corrección de Holm),
análisis de robustez (costo ajustado +30 bps y días con cumplimiento ≥ 95 %), y figuras técnicas.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORRIDAS = REPO_ROOT / "data/analysis/3_2_2/corridas.csv"
DEFAULT_OUT = REPO_ROOT / "data/analysis/3_2_4"

ESTRATEGIAS = ("PPO_sistema", "TWAP", "VWAP")
TRAMOS = ("apertura", "media_jornada", "cierre")
ETIQUETAS_TRAMO = {"apertura": "Apertura", "media_jornada": "Media jornada", "cierre": "Cierre"}
PROFUNDIDADES = (0.25, 1.0, 4.0)
ETIQUETAS_PROF = {0.25: "×0,25", 1.0: "×1", 4.0: "×4"}
TAMANOS = (0.5, 1.0, 1.5)


def bootstrap_ic(valores: np.ndarray, n_boot: int = 10000, seed: int = 0) -> Tuple[float, float]:
    """IC 95 % percentil por bootstrap de la media."""
    arr = np.asarray(valores, dtype=float)
    if len(arr) == 0:
        return float("nan"), float("nan")
    if len(arr) == 1 or np.all(arr == arr[0]):
        return float(arr[0]), float(arr[0])
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(arr), size=(n_boot, len(arr)))
    medias = arr[idx].mean(axis=1)
    lo, hi = np.percentile(medias, [2.5, 97.5])
    return float(lo), float(hi)


def holm_bonferroni(p_vals: Sequence[float]) -> List[float]:
    """Ajuste secuencial de Holm-Bonferroni."""
    m = len(p_vals)
    orden = sorted(range(m), key=lambda i: p_vals[i])
    ajustados = [0.0] * m
    acum = 0.0
    for k, idx in enumerate(orden):
        val = min(1.0, p_vals[idx] * (m - k))
        acum = max(acum, val)
        ajustados[idx] = float(acum)
    return ajustados


def _wilcoxon(x: np.ndarray) -> float:
    x = np.asarray(x, dtype=float)
    nz = x[x != 0]
    if len(nz) < 2:
        return 1.0
    return float(stats.wilcoxon(nz).pvalue)


def _pivot_pareado(df: pd.DataFrame, col_valor: str, col_eje: str) -> pd.DataFrame:
    """Tabla pareada por (orden, seed, eje) con columnas para cada estrategia."""
    piv = df.pivot_table(index=["orden", "seed", col_eje], columns="estrategia", values=col_valor, aggfunc="first")
    piv = piv.reset_index()
    piv["dif_TWAP"] = piv["PPO_sistema"] - piv["TWAP"]
    piv["dif_VWAP"] = piv["PPO_sistema"] - piv["VWAP"]
    return piv


def analizar_tamano(df: pd.DataFrame, col_valor: str = "slippage_bps", n_boot: int = 10000, seed: int = 0) -> Dict:
    """Sensibilidad al tamaño de orden (factores 0.5, 1.0, 1.5 en profundidad ×1)."""
    sub = df[df["escenario"] == "media"].copy()
    piv = _pivot_pareado(sub, col_valor, "factor_tamano")
    ancho = piv.pivot(index=["orden", "seed"], columns="factor_tamano", values=list(ESTRATEGIAS) + ["dif_TWAP", "dif_VWAP"])

    series = ("PPO_sistema", "TWAP", "VWAP", "dif_TWAP", "dif_VWAP")
    derivadas: List[Dict] = []
    pares_tam = [(0.5, 1.0, 0.5), (1.0, 1.5, 0.5), (0.5, 1.5, 1.0)]

    for s in series:
        for t0, t1, dt in pares_tam:
            delta = (ancho[(s, t1)] - ancho[(s, t0)]).dropna().to_numpy()
            pendiente = delta / dt
            lo_d, hi_d = bootstrap_ic(delta, n_boot=n_boot, seed=seed)
            lo_p, hi_p = bootstrap_ic(pendiente, n_boot=n_boot, seed=seed)
            derivadas.append({
                "serie": s,
                "desde": t0,
                "hasta": t1,
                "delta_factor": dt,
                "n": int(len(delta)),
                "delta_medio_bps": float(delta.mean()),
                "delta_ic_lo": lo_d,
                "delta_ic_hi": hi_d,
                "pendiente_bps_por_unidad": float(pendiente.mean()),
                "pendiente_ic_lo": lo_p,
                "pendiente_ic_hi": hi_p,
                "wilcoxon_p": _wilcoxon(delta),
            })

    pruebas = {}
    for s in series:
        m = np.column_stack([ancho[(s, t)].to_numpy() for t in TAMANOS])
        fried = stats.friedmanchisquare(m[:, 0], m[:, 1], m[:, 2])
        x_sp = np.concatenate([np.full(len(m), t) for t in TAMANOS])
        y_sp = np.concatenate([m[:, i] for i in range(len(TAMANOS))])
        spear = stats.spearmanr(x_sp, y_sp)
        pruebas[s] = {
            "n_bloques": int(len(m)),
            "friedman_Q": float(fried.statistic),
            "friedman_p": float(fried.pvalue),
            "spearman_rho": float(spear.statistic),
            "spearman_p": float(spear.pvalue),
            "n_spearman": int(len(x_sp)),
        }

    # Robustez: días donde las 3 estrategias cumplen >= 0.95 en los 3 tamaños
    cumpl = sub.pivot_table(index=["orden", "seed"], columns=["factor_tamano", "estrategia"], values="cumplimiento")
    mask_ok = (cumpl >= 0.95).all(axis=1)
    dias_ok = cumpl.index[mask_ok]
    ancho_ok = ancho.loc[dias_ok]
    robustez_ok = {}
    for s in ("dif_TWAP", "dif_VWAP"):
        m = np.column_stack([ancho_ok[(s, t)].to_numpy() for t in TAMANOS])
        fried = stats.friedmanchisquare(m[:, 0], m[:, 1], m[:, 2])
        x_sp = np.concatenate([np.full(len(m), t) for t in TAMANOS])
        y_sp = np.concatenate([m[:, i] for i in range(len(TAMANOS))])
        spear = stats.spearmanr(x_sp, y_sp)
        robustez_ok[s] = {
            "n_bloques": int(len(m)),
            "medias": {str(t): float(m[:, i].mean()) for i, t in enumerate(TAMANOS)},
            "friedman_Q": float(fried.statistic),
            "friedman_p": float(fried.pvalue),
            "spearman_rho": float(spear.statistic),
            "spearman_p": float(spear.pvalue),
        }

    return {"derivadas": derivadas, "pruebas": pruebas, "robustez_cumpl_95": robustez_ok}


def analizar_profundidad(df: pd.DataFrame, col_valor: str = "slippage_bps", n_boot: int = 10000, seed: int = 0) -> Dict:
    """Sensibilidad a la profundidad del market maker (×0.25, ×1, ×4 en tamaño 1.0)."""
    sub = df[df["factor_tamano"] == 1.0].copy()
    piv = _pivot_pareado(sub, col_valor, "factor_liquidez")
    ancho = piv.pivot(index=["orden", "seed"], columns="factor_liquidez", values=list(ESTRATEGIAS) + ["dif_TWAP", "dif_VWAP"])

    series = ("PPO_sistema", "TWAP", "VWAP", "dif_TWAP", "dif_VWAP")
    derivadas: List[Dict] = []
    pares_prof = [(0.25, 1.0, 2.0), (1.0, 4.0, 2.0), (0.25, 4.0, 4.0)]  # Δlog2(factor)

    for s in series:
        for p0, p1, dlog2 in pares_prof:
            delta = (ancho[(s, p1)] - ancho[(s, p0)]).dropna().to_numpy()
            pendiente = delta / dlog2  # bps por cada duplicación de profundidad (×2)
            lo_d, hi_d = bootstrap_ic(delta, n_boot=n_boot, seed=seed)
            lo_p, hi_p = bootstrap_ic(pendiente, n_boot=n_boot, seed=seed)
            derivadas.append({
                "serie": s,
                "desde": ETIQUETAS_PROF[p0],
                "hasta": ETIQUETAS_PROF[p1],
                "delta_log2": dlog2,
                "n": int(len(delta)),
                "delta_medio_bps": float(delta.mean()),
                "delta_ic_lo": lo_d,
                "delta_ic_hi": hi_d,
                "pendiente_bps_por_duplicacion": float(pendiente.mean()),
                "pendiente_ic_lo": lo_p,
                "pendiente_ic_hi": hi_p,
                "wilcoxon_p": _wilcoxon(delta),
            })

    pruebas = {}
    for s in series:
        m = np.column_stack([ancho[(s, p)].to_numpy() for p in PROFUNDIDADES])
        kw = stats.kruskal(m[:, 0], m[:, 1], m[:, 2])
        fried = stats.friedmanchisquare(m[:, 0], m[:, 1], m[:, 2])
        x_sp = np.concatenate([np.full(len(m), np.log2(p)) for p in PROFUNDIDADES])
        y_sp = np.concatenate([m[:, i] for i in range(len(PROFUNDIDADES))])
        spear = stats.spearmanr(x_sp, y_sp)
        pruebas[s] = {
            "n_por_grupo": int(len(m)),
            "kruskal_H": float(kw.statistic),
            "kruskal_p": float(kw.pvalue),
            "friedman_Q": float(fried.statistic),
            "friedman_p": float(fried.pvalue),
            "spearman_rho": float(spear.statistic),
            "spearman_p": float(spear.pvalue),
        }

    return {"derivadas": derivadas, "pruebas": pruebas}


def analizar_tramo(df: pd.DataFrame, col_valor: str = "slippage_bps", n_boot: int = 10000, seed: int = 0) -> Dict:
    """Sensibilidad al tramo horario de inicio (90 corridas en tamaño 1.0)."""
    sub = df[df["factor_tamano"] == 1.0].copy()
    piv = sub.pivot_table(
        index=["escenario", "orden", "seed", "tramo_inicio"],
        columns="estrategia",
        values=col_valor,
        aggfunc="first",
    ).reset_index()
    piv["dif_TWAP"] = piv["PPO_sistema"] - piv["TWAP"]
    piv["dif_VWAP"] = piv["PPO_sistema"] - piv["VWAP"]

    res_tramos = []
    for ref in ("TWAP", "VWAP"):
        col = f"dif_{ref}"
        p_raw = []
        grupos = []
        filas_ref = []
        for tr in TRAMOS:
            vals = piv.loc[piv["tramo_inicio"] == tr, col].to_numpy()
            grupos.append(vals)
            lo, hi = bootstrap_ic(vals, n_boot=n_boot, seed=seed)
            pv = _wilcoxon(vals)
            p_raw.append(pv)
            filas_ref.append({
                "referencia": ref,
                "tramo": tr,
                "n": int(len(vals)),
                "media_bps": float(vals.mean()),
                "mediana_bps": float(np.median(vals)),
                "ic_lo": lo,
                "ic_hi": hi,
                "wilcoxon_p": pv,
            })
        p_holm = holm_bonferroni(p_raw)
        for fila, ph in zip(filas_ref, p_holm):
            fila["wilcoxon_p_holm"] = ph
        kw = stats.kruskal(*grupos)
        res_tramos.extend(filas_ref)
        if ref == "TWAP":
            kw_twap = {"H": float(kw.statistic), "p": float(kw.pvalue)}
        else:
            kw_vwap = {"H": float(kw.statistic), "p": float(kw.pvalue)}

    return {"por_tramo": res_tramos, "kruskal_dif_TWAP": kw_twap, "kruskal_dif_VWAP": kw_vwap}


def _graficar_tamano(df: pd.DataFrame, res_tam: Dict, out_path: Path) -> None:
    sub = df[df["escenario"] == "media"]
    piv = _pivot_pareado(sub, "slippage_bps", "factor_tamano")
    fig, ax = plt.subplots(figsize=(7.5, 4.8), dpi=150)

    colores = {"PPO_sistema": "#1f77b4", "TWAP": "#ff7f0e", "VWAP": "#2ca02c"}
    etiquetas = {"PPO_sistema": "Sistema PPO", "TWAP": "TWAP", "VWAP": "VWAP"}
    desplaz = {"PPO_sistema": -0.015, "TWAP": 0.0, "VWAP": 0.015}

    for est in ESTRATEGIAS:
        xs, ys, err_lo, err_hi = [], [], [], []
        for t in TAMANOS:
            vals = piv.loc[piv["factor_tamano"] == t, est].to_numpy()
            m = float(vals.mean())
            lo, hi = bootstrap_ic(vals, n_boot=5000, seed=0)
            xs.append(t + desplaz[est])
            ys.append(m)
            err_lo.append(m - lo)
            err_hi.append(hi - m)
        ax.errorbar(xs, ys, yerr=[err_lo, err_hi], marker="o", capsize=4, lw=2,
                    color=colores[est], label=etiquetas[est])

    pr = res_tam["pruebas"]["dif_TWAP"]
    ax.set_xticks(TAMANOS)
    ax.set_xticklabels(["0,5 (5 % día)", "1,0 (10 % día)", "1,5 (15 % día)"])
    ax.set_xlabel("Factor de tamaño de la meta-orden (profundidad ×1)")
    ax.set_ylabel("Implementation Shortfall medio (bps) e IC 95 %")
    ax.set_title(
        f"Sensibilidad del IS al tamaño de orden (n = 30 días pareados)\n"
        f"Tendencia Sistema − TWAP: Friedman Q = {pr['friedman_Q']:.2f} (p = {pr['friedman_p']:.3f}), "
        f"Spearman ρ = {pr['spearman_rho']:.3f} (p = {pr['spearman_p']:.3f})",
        fontsize=10,
    )
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def _graficar_profundidad(df: pd.DataFrame, res_prof: Dict, out_path: Path) -> None:
    sub = df[df["factor_tamano"] == 1.0]
    piv = _pivot_pareado(sub, "slippage_bps", "factor_liquidez")
    fig, ax = plt.subplots(figsize=(7.5, 4.8), dpi=150)

    colores = {"PPO_sistema": "#1f77b4", "TWAP": "#ff7f0e", "VWAP": "#2ca02c"}
    etiquetas = {"PPO_sistema": "Sistema PPO", "TWAP": "TWAP", "VWAP": "VWAP"}
    x_pos = np.arange(len(PROFUNDIDADES), dtype=float)
    desplaz = {"PPO_sistema": -0.05, "TWAP": 0.0, "VWAP": 0.05}

    for est in ESTRATEGIAS:
        ys, err_lo, err_hi = [], [], []
        for p in PROFUNDIDADES:
            vals = piv.loc[piv["factor_liquidez"] == p, est].to_numpy()
            m = float(vals.mean())
            lo, hi = bootstrap_ic(vals, n_boot=5000, seed=0)
            ys.append(m)
            err_lo.append(m - lo)
            err_hi.append(hi - m)
        ax.errorbar(x_pos + desplaz[est], ys, yerr=[err_lo, err_hi], marker="s", capsize=4, lw=2,
                    color=colores[est], label=etiquetas[est])

    pr = res_prof["pruebas"]["dif_TWAP"]
    ax.set_xticks(x_pos)
    ax.set_xticklabels(["×0,25 (alta)", "×1 (media)", "×4 (baja)"])
    ax.set_xlabel("Profundidad del market maker (mm_pov, tamaño 1,0)")
    ax.set_ylabel("Implementation Shortfall medio (bps) e IC 95 %")
    ax.set_title(
        f"Sensibilidad del IS a la profundidad del market maker (n = 30 días pareados por nivel)\n"
        f"Sistema − TWAP: Kruskal-Wallis H = {pr['kruskal_H']:.2f} (p = {pr['kruskal_p']:.3f}), "
        f"Friedman Q = {pr['friedman_Q']:.2f} (p = {pr['friedman_p']:.3f})",
        fontsize=10,
    )
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def _graficar_tramo(res_tramo: Dict, out_path: Path) -> None:
    filas_twap = [f for f in res_tramo["por_tramo"] if f["referencia"] == "TWAP"]
    fig, ax = plt.subplots(figsize=(7.2, 4.6), dpi=150)
    x = np.arange(len(TRAMOS))
    ys = [f["media_bps"] for f in filas_twap]
    err_lo = [f["media_bps"] - f["ic_lo"] for f in filas_twap]
    err_hi = [f["ic_hi"] - f["media_bps"] for f in filas_twap]

    ax.axhline(0.0, color="black", lw=1, linestyle="--")
    ax.errorbar(x, ys, yerr=[err_lo, err_hi], fmt="o", capsize=5, lw=2, color="#1f77b4", ms=8)
    for xi, f in zip(x, filas_twap):
        ax.annotate(f"{f['media_bps']:+.1f} bps\n(p Holm={f['wilcoxon_p_holm']:.3f})",
                    (xi, f["media_bps"]), textcoords="offset points", xytext=(10, 5), fontsize=8.5)

    kw = res_tramo["kruskal_dif_TWAP"]
    ax.set_xticks(x)
    ax.set_xticklabels([f"{ETIQUETAS_TRAMO[f['tramo']]}\n(n={f['n']})" for f in filas_twap])
    ax.set_ylabel("Diferencia Sistema − TWAP (bps) e IC 95 %")
    ax.set_title(
        f"Sensibilidad de la diferencia Sistema − TWAP al tramo horario (n = 90 corridas)\n"
        f"Kruskal-Wallis H = {kw['H']:.2f} (p = {kw['p']:.3f}); negativo favorece al sistema",
        fontsize=10,
    )
    ax.grid(True, linestyle="--", alpha=0.4)
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def ejecutar(corridas_csv: Path = DEFAULT_CORRIDAS, out_dir: Path = DEFAULT_OUT, n_boot: int = 10000) -> Dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(corridas_csv)

    res_tam_crudo = analizar_tamano(df, "slippage_bps", n_boot=n_boot, seed=0)
    res_tam_ajust = analizar_tamano(df, "costo", n_boot=n_boot, seed=0)
    res_prof_crudo = analizar_profundidad(df, "slippage_bps", n_boot=n_boot, seed=0)
    res_tramo_crudo = analizar_tramo(df, "slippage_bps", n_boot=n_boot, seed=0)

    salida = {
        "tamano_crudo": res_tam_crudo,
        "tamano_ajustado": res_tam_ajust,
        "profundidad_crudo": res_prof_crudo,
        "tramo_crudo": res_tramo_crudo,
    }

    (out_dir / "sensibilidad_3_2_4.json").write_text(
        json.dumps(salida, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    pd.DataFrame(res_tam_crudo["derivadas"]).to_csv(out_dir / "derivadas_tamano.csv", index=False)
    pd.DataFrame(res_prof_crudo["derivadas"]).to_csv(out_dir / "derivadas_profundidad.csv", index=False)
    pd.DataFrame(res_tramo_crudo["por_tramo"]).to_csv(out_dir / "sensibilidad_tramo.csv", index=False)

    _graficar_tamano(df, res_tam_crudo, out_dir / "sensibilidad_tamano.png")
    _graficar_profundidad(df, res_prof_crudo, out_dir / "sensibilidad_profundidad.png")
    _graficar_tramo(res_tramo_crudo, out_dir / "sensibilidad_tramo.png")

    return salida


def main(argv: Optional[Sequence[str]] = None) -> None:
    ap = argparse.ArgumentParser(description="Análisis de sensibilidad 3.2.4 (MR).")
    ap.add_argument("--corridas-csv", type=Path, default=DEFAULT_CORRIDAS)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--n-boot", type=int, default=10000)
    args = ap.parse_args(argv)
    res = ejecutar(args.corridas_csv, args.out_dir, n_boot=args.n_boot)
    print("Tamano dif_TWAP:", json.dumps(res["tamano_crudo"]["pruebas"]["dif_TWAP"], ensure_ascii=False))
    print("Profundidad dif_TWAP:", json.dumps(res["profundidad_crudo"]["pruebas"]["dif_TWAP"], ensure_ascii=False))
    print("Tramo dif_TWAP:", json.dumps(res["tramo_crudo"]["kruskal_dif_TWAP"], ensure_ascii=False))


if __name__ == "__main__":
    main()
