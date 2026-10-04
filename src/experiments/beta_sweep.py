"""Barrido de beta (aversion al riesgo de R_E), fase 1 -- tarea 2.2.3 (BF).

Logica comun a `scripts/beta_sweep.py` (fallback Poisson, local) y
`scripts/colab/beta_sweep_abides.py` (ABIDES calibrado). No importa ABIDES.

Metodo. Se evaluan tres politicas heuristicas (sin aprendizaje) en los tres
tramos con >= 20 semillas. Como una politica heuristica no mira la
recompensa, beta no cambia lo que hace: cada episodio se corre UNA vez
guardando, por paso, P_mid, P_ejec, q_ejec y sigma2, y R_E se recalcula
despues para cada beta de la grilla.

    beta* = E_q|P_mid - P_ejec| / E_q[sigma2]      (medias ponderadas por q_ejec)

es el beta con el que, en el agregado, el termino de riesgo pesa lo mismo que
el de precio. Grilla: {0; 0,1; 0,3; 1; 3} x beta*.

Metricas por (politica, tramo, beta): R_E medio por episodio, IS y slippage
(`src/analysis/execution_metrics.py`), % de cumplimiento, peso del riesgo y
ranking de politicas. Regla del plan: se descartan los beta en que el riesgo
domina (> 80 % de |R_E|) o no pesa (< 5 %).

Peso del riesgo = sum|riesgo| / (sum|precio| + sum|riesgo|), en [0, 1]. Se
usa esta forma y no |riesgo| / |R_E| porque R_E = precio - riesgo puede
quedar cerca de 0 cuando el termino de precio es positivo (una orden limite
pasiva que compra bajo el mid), y el cociente literal se dispara.
"""
from __future__ import annotations

from typing import Callable, Dict, List, Optional, Sequence

import numpy as np

from src.analysis.execution_metrics import evaluate_episode

BETA_MULTIPLOS = (0.0, 0.1, 0.3, 1.0, 3.0)
PESO_RIESGO_MIN = 0.05
PESO_RIESGO_MAX = 0.80
TRAMOS = ("apertura", "media_jornada", "cierre")

# Indices de EjecutorActionSpace: [order_type, volume_bucket, price_level]
LIMIT_BUY, MARKET = 0, 2
VOLUME_FRACS = np.linspace(0.1, 1.0, 10)
NIVEL_MEDIO = 4

# Nivel de precio "pasivo" (el mas alejado de cruzar el spread) en cada
# entorno. El contrato (spaces.py, abides_bridge.py) dice 0 = mejor precio
# propio y 7 = mas agresivo: en ABIDES el nivel 0 deja la orden en el mejor
# bid. `PoissonLOBSimulator.execute_limit_buy` usa la convencion inversa
# (probabilidad de llenado 1 - nivel / 8: el nivel 0 se llena siempre y el 7
# casi nunca), asi que ahi la politica pasiva usa el nivel 7.
NIVEL_PASIVO = {"abides": 0, "poisson": 7}


def politica_agresiva(paso: int, max_pasos: int, nivel_pasivo: int) -> np.ndarray:
    """MARKET por todo lo pendiente en cada paso."""
    return np.array([MARKET, 9, 0])


def politica_twap(paso: int, max_pasos: int, nivel_pasivo: int) -> np.ndarray:
    """LIMIT de nivel medio por 1 / (pasos restantes) de lo pendiente (el
    bucket de volumen mas cercano; el minimo del espacio de acciones es 10 %)."""
    frac = 1.0 / max(max_pasos - paso, 1)
    bucket = int(np.argmin(np.abs(VOLUME_FRACS - frac)))
    return np.array([LIMIT_BUY, bucket, NIVEL_MEDIO])


def politica_pasiva(paso: int, max_pasos: int, nivel_pasivo: int) -> np.ndarray:
    """LIMIT pasiva por todo lo pendiente, renovada en cada paso."""
    return np.array([LIMIT_BUY, 9, nivel_pasivo])


POLITICAS: Dict[str, Callable[[int, int, int], np.ndarray]] = {
    "agresiva_market": politica_agresiva,
    "twap_limit_medio": politica_twap,
    "pasiva_limit": politica_pasiva,
}


# ---------------------------------------------------------------------------
# Episodios
# ---------------------------------------------------------------------------

def step_record(info: Dict) -> Dict[str, float]:
    """Registro comun de un paso a partir del `info` de cualquiera de los dos
    entornos (precios en CLP)."""
    if "q_ejecutado_step" in info:   # EjecutorEnvPoissonFallback
        q = float(info["q_ejecutado_step"])
        p_mid = float(info["p_mid_decision"])
        p_ejec = float(info["p_ejecutado_step"]) if q > 0 else p_mid
    else:                            # EjecutorEnvAbides
        q = float(info.get("q_fill_step", 0.0))
        p_mid = float(info["p_mid_clp"])
        p_ejec = float(info["p_fill_step_clp"]) if q > 0 else p_mid
    return {"q": q, "p_mid": p_mid, "p_ejec": p_ejec, "sigma2": float(info["sigma2"])}


def run_episode(env, politica: Callable[[int, int, int], np.ndarray], nivel_pasivo: int,
                q_slice: float) -> Dict:
    """Corre un episodio con una politica heuristica y devuelve su resumen.
    La semilla se fija al construir el entorno (ambos entornos la reciben en
    el constructor) y el entorno se crea con beta = 0."""
    obs, info = env.reset()
    p_ref = info.get("p_referencia")
    if p_ref is None:  # ABIDES: precio de entrada en unidades de cuenta
        p_ref = float(info["entry_price"]) / float(info.get("unidades_por_clp", 1.0))
    pasos: List[Dict[str, float]] = []
    done, paso = False, 0
    while not done:
        obs, _, done, truncated, info = env.step(politica(paso, env.max_steps, nivel_pasivo))
        done = done or truncated
        pasos.append(step_record(info))
        paso += 1
    return summarize_episode(pasos, float(q_slice), float(p_ref))


def summarize_episode(pasos: Sequence[Dict[str, float]], q_slice: float, p_ref: float) -> Dict:
    """Agregados de un episodio que no dependen de beta. `precio` y
    `sigma2_q` estan en bruto (CLP): R_E(beta) = precio - beta * sigma2_q."""
    q = np.array([s["q"] for s in pasos], dtype=float)
    dif = np.array([s["p_mid"] - s["p_ejec"] for s in pasos], dtype=float)
    s2 = np.array([s["sigma2"] for s in pasos], dtype=float)
    q_ejec = float(q.sum())
    out = {
        "q_slice": q_slice, "p_referencia": p_ref, "n_pasos": len(pasos),
        "q_ejecutado": q_ejec,
        "precio": float((dif * q).sum()),            # sum (P_mid - P_ejec) q
        "abs_precio": float(np.abs(dif * q).sum()),  # sum |P_mid - P_ejec| q
        "sigma2_q": float((s2 * q).sum()),           # sum sigma2 q
        "cumplimiento": q_ejec / q_slice if q_slice > 0 else float("nan"),
        "IS_total": None, "slippage_bps": None, "p_promedio": None,
    }
    if q_ejec > 0:
        p_prom = float(sum(s["p_ejec"] * s["q"] for s in pasos) / q_ejec)
        ev = evaluate_episode(q_total=q_slice, q_executed=q_ejec, p_referencia=p_ref,
                              p_promedio_ejecutado=p_prom)
        out.update({"IS_total": ev["IS_total"], "slippage_bps": ev["slippage_bps"], "p_promedio": p_prom})
    return out


# ---------------------------------------------------------------------------
# beta* y agregacion
# ---------------------------------------------------------------------------

def beta_star_from_episodes(episodios: Sequence[Dict]) -> float:
    """beta* = sum|P_mid - P_ejec| q / sum sigma2 q sobre todos los episodios:
    con este beta, sum|riesgo| = sum|precio| en el agregado."""
    num = sum(e["abs_precio"] for e in episodios)
    den = sum(e["sigma2_q"] for e in episodios)
    return float(num / den) if den > 0 else float("nan")


def risk_weight(episodios: Sequence[Dict], beta: float) -> float:
    """Peso del riesgo en [0, 1]: sum|riesgo| / (sum|precio| + sum|riesgo|)."""
    riesgo = beta * sum(e["sigma2_q"] for e in episodios)
    precio = sum(e["abs_precio"] for e in episodios)
    return float(riesgo / (precio + riesgo)) if (precio + riesgo) > 0 else float("nan")


def _mean(vals: Sequence[Optional[float]]) -> Optional[float]:
    v = [x for x in vals if x is not None and np.isfinite(x)]
    return float(np.mean(v)) if v else None


def metrics(episodios: Sequence[Dict], beta: float, escala: str = "por_accion_slice") -> Dict:
    """Metricas de un grupo de episodios (una politica en un tramo) para un beta."""
    div = [e["q_slice"] if escala == "por_accion_slice" else 1.0 for e in episodios]
    r = [(e["precio"] - beta * e["sigma2_q"]) / d for e, d in zip(episodios, div)]
    riesgo = [beta * e["sigma2_q"] / d for e, d in zip(episodios, div)]
    tot_r, tot_riesgo = sum(r), sum(riesgo)
    return {
        "n_episodios": len(episodios),
        "R_E_medio": float(np.mean(r)) if r else None,
        "R_E_std": float(np.std(r)) if r else None,
        "riesgo_medio": float(np.mean(riesgo)) if riesgo else None,
        "peso_riesgo": risk_weight(episodios, beta),
        "riesgo_sobre_abs_R_E": float(abs(tot_riesgo) / abs(tot_r)) if abs(tot_r) > 0 else None,
        "IS_total_medio": _mean([e["IS_total"] for e in episodios]),
        "slippage_bps_medio": _mean([e["slippage_bps"] for e in episodios]),
        "cumplimiento_medio": _mean([e["cumplimiento"] for e in episodios]),
        "episodios_sin_ejecucion": sum(1 for e in episodios if e["q_ejecutado"] <= 0),
    }


def build_report(episodios: Dict[str, Dict[str, List[Dict]]], escala: str = "por_accion_slice",
                 multiplos: Sequence[float] = BETA_MULTIPLOS) -> Dict:
    """`episodios[tramo][politica]` -> reporte del barrido.

    Returns:
        beta_star (global y por tramo), grilla de beta, por beta: metricas
        por tramo y politica, ranking de politicas (de mayor a menor R_E
        medio), peso del riesgo por tramo y global, y la recomendacion.
    """
    todos = [e for por_pol in episodios.values() for eps in por_pol.values() for e in eps]
    b_star = beta_star_from_episodes(todos)
    por_tramo_star = {t: beta_star_from_episodes([e for eps in por_pol.values() for e in eps])
                      for t, por_pol in episodios.items()}
    out: Dict = {"beta_star": b_star, "beta_star_por_tramo": por_tramo_star,
                 "multiplos": list(multiplos), "escala": escala, "por_beta": []}
    for m in multiplos:
        beta = m * b_star
        fila: Dict = {"multiplo": m, "beta": beta, "por_tramo": {}, "ranking": {},
                      "peso_riesgo_por_tramo": {}, "peso_riesgo_global": risk_weight(todos, beta)}
        for tramo, por_pol in episodios.items():
            fila["por_tramo"][tramo] = {p: metrics(eps, beta, escala) for p, eps in por_pol.items()}
            fila["ranking"][tramo] = sorted(
                por_pol, key=lambda p: -(fila["por_tramo"][tramo][p]["R_E_medio"] or float("-inf")))
            fila["peso_riesgo_por_tramo"][tramo] = risk_weight(
                [e for eps in por_pol.values() for e in eps], beta)
        out["por_beta"].append(fila)
    out["ranking_cambia_con_beta"] = {
        t: len({tuple(f["ranking"][t]) for f in out["por_beta"]}) > 1 for t in episodios}
    out["recomendacion"] = recommend_beta_range(out)
    return out


def recommend_beta_range(report: Dict, w_min: float = PESO_RIESGO_MIN,
                         w_max: float = PESO_RIESGO_MAX) -> Dict:
    """Regla del plan: se descartan los beta cuyo peso del riesgo es > 80 % o
    < 5 % en algun tramo (y beta = 0, que no pesa). Devuelve los beta
    admisibles y el rango [min, max]."""
    admisibles, descartados = [], []
    for f in report["por_beta"]:
        pesos = dict(f["peso_riesgo_por_tramo"])
        motivo = None
        if any(not np.isfinite(w) for w in pesos.values()):
            motivo = "peso del riesgo indefinido"
        elif min(pesos.values()) < w_min:
            motivo = f"peso del riesgo < {w_min:.0%} en algun tramo"
        elif max(pesos.values()) > w_max:
            motivo = f"peso del riesgo > {w_max:.0%} en algun tramo"
        (descartados if motivo else admisibles).append(
            {"multiplo": f["multiplo"], "beta": f["beta"], "pesos": pesos, **({"motivo": motivo} if motivo else {})})
    betas = [a["beta"] for a in admisibles]
    return {
        "criterio": f"peso del riesgo en [{w_min:.0%}, {w_max:.0%}] en los tres tramos",
        "admisibles": admisibles, "descartados": descartados,
        "rango_beta": [min(betas), max(betas)] if betas else None,
        "rango_multiplos": ([min(a["multiplo"] for a in admisibles), max(a["multiplo"] for a in admisibles)]
                            if admisibles else None),
    }


# ---------------------------------------------------------------------------
# Corrida reanudable
# ---------------------------------------------------------------------------

def run_sweep(env_factory: Callable[..., object], entorno: str, seeds: Sequence[int],
              q_slice: int, ventana_min: int, estado: Dict, guardar: Callable[[Dict], None],
              tramos: Sequence[str] = TRAMOS, verbose: bool = True) -> Dict:
    """Corre los episodios pendientes (tramo x politica x semilla) y guarda
    tras cada uno. `env_factory(executor_id=, q_slice=, ventana_min=, seed=)`
    crea el entorno; `estado["episodios"][tramo][politica][str(seed)]` guarda
    el resumen de cada episodio y es lo que permite reanudar."""
    import time

    nivel_pasivo = NIVEL_PASIVO[entorno]
    episodios = estado.setdefault("episodios", {})
    for tramo in tramos:
        for nombre, politica in POLITICAS.items():
            hechos = episodios.setdefault(tramo, {}).setdefault(nombre, {})
            for seed in seeds:
                if str(seed) in hechos:
                    continue
                t0 = time.time()
                env = env_factory(executor_id=tramo, q_slice=q_slice, ventana_min=ventana_min, seed=seed)
                try:
                    hechos[str(seed)] = run_episode(env, politica, nivel_pasivo, q_slice)
                finally:
                    env.close()
                guardar(estado)
                if verbose:
                    e = hechos[str(seed)]
                    print(f"{tramo:14s} {nombre:17s} seed={seed}: cumplimiento={e['cumplimiento']:.2f} "
                          f"({time.time() - t0:.0f}s)", flush=True)
    return estado


def report_from_state(estado: Dict, escala: str) -> Dict:
    eps = {t: {p: list(por_seed.values()) for p, por_seed in por_pol.items()}
           for t, por_pol in estado["episodios"].items()}
    return build_report(eps, escala)


def print_report(rep: Dict) -> None:
    print(f"\nbeta* = {rep['beta_star']:.5g} (1/CLP); por tramo: "
          + ", ".join(f"{t}={b:.5g}" for t, b in rep["beta_star_por_tramo"].items()))
    for f in rep["por_beta"]:
        print(f"\nbeta = {f['multiplo']:g} x beta* = {f['beta']:.5g}   peso del riesgo global = "
              f"{f['peso_riesgo_global']:.1%}")
        for tramo, por_pol in f["por_tramo"].items():
            print(f"  {tramo:14s} peso riesgo {f['peso_riesgo_por_tramo'][tramo]:6.1%}  "
                  f"ranking: {' > '.join(f['ranking'][tramo])}")
            for pol, m in por_pol.items():
                sl = "   -" if m["slippage_bps_medio"] is None else f"{m['slippage_bps_medio']:6.2f}"
                print(f"      {pol:17s} R_E={m['R_E_medio']:9.4f}  slippage={sl} bps  "
                      f"cumplimiento={m['cumplimiento_medio']:.1%}  peso riesgo={m['peso_riesgo']:.1%}")
    rec = rep["recomendacion"]
    print(f"\nRecomendacion ({rec['criterio']}): rango de beta = {rec['rango_beta']} "
          f"(multiplos {rec['rango_multiplos']})")
    for d in rec["descartados"]:
        print(f"  descartado {d['multiplo']:g} x beta*: {d['motivo']}")
    print("El ranking de politicas cambia con beta:", rep["ranking_cambia_con_beta"])
