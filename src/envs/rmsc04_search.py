"""Logica pura de la busqueda y validacion de RMSC04 -- tarea 2.2.4, bloques
B y C (BF). Sin ABIDES: armado de la grilla, funcion de perdida, rankings
robustos, refinamiento local y resumen del KS. Los scripts que corren las
simulaciones estan en `scripts/colab/`.

Metodo de momentos simulado. Parametros libres: liquidez del market maker
(`mm_*`) y actividad (`num_noise_agents`, `lambda_a`). El resto queda fijo
segun el bloque A (`calibrate_rmsc04_ipsa`). Momentos, por tramo y medidos en
el mercado de fondo sin nuestro agente:

    - volatilidad de 5 min (bps);
    - spread cotizado mediano (bps), contra el rango [Corwin-Schultz, Roll]
      de los proxies reales: ambos vienen de velas OHLCV y Roll sobreestima
      el spread cotizado, asi que el objetivo es un intervalo y no un punto;
    - participacion de cada tramo en el volumen del dia;
    - volumen mediano por vela de 5 min;
    - rankings robustos de la 2.1.3b: la volatilidad es maxima en la
      apertura y el volumen por vela crece durante el dia.

Perdida = suma ponderada de |ln(sim / objetivo)| por momento y tramo, mas
`PESOS["ranking"]` por cada ranking robusto que no se reproduce.
"""
from __future__ import annotations

import itertools
import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union

import numpy as np

from src.envs.rmsc04_sim_stats import TRAMO_NAMES

# ---------------------------------------------------------------------------
# Grilla
# ---------------------------------------------------------------------------

MAX_COMBINACIONES = 27

# Cada factor es una lista de niveles; cada nivel es un dict de kwargs de
# rmsc04 (asi un nivel puede mover dos parametros acoplados). Valores en
# unidades de cuenta "decimos" (1 tick = 0,1 CLP ~ 0,17 bps para FALABELLA).
#
# mm_liquidez. En modo "adaptive" el market maker cotiza alrededor del spread
#   que observa (lo sigue, no lo fija) y `mm_spread_alpha` solo cambia la
#   velocidad de ese promedio movil. Con `mm_window_size` entero cotiza a
#   mid +/- ventana/2: es la palanca directa del spread. 30 y 90 ticks son
#   ~5 y ~15 bps, entre Corwin-Schultz (4-6 bps) y Roll (21-35 bps). Con
#   ventana fija la separacion entre niveles es ceil(50 * mm_level_spacing)
#   ticks: 0,1 -> 5 ticks (0,84 bps); el default 5 daria 250 ticks (42 bps).
# mm_pov. Fraccion del volumen transado en el ultimo minuto que el market
#   maker pone en cada nivel: profundidad. Default 0,025; se cubre 5x a cada
#   lado.
# actividad. `num_noise_agents` (tomadores, una orden por dia, llegadas en U)
#   y `lambda_a` (tasa de llegada de los 102 agentes de valor) escalados
#   juntos por 1, 2 y 4: el volumen mediano real por vela (7 600-12 000
#   acciones) es del orden de 2-4 veces el flujo de rmsc04 por defecto.
GRID_DEFAULT: Dict[str, List[Dict]] = {
    "mm_liquidez": [
        {"mm_window_size": "adaptive"},
        {"mm_window_size": 30, "mm_level_spacing": 0.1},
        {"mm_window_size": 90, "mm_level_spacing": 0.1},
    ],
    "mm_pov": [{"mm_pov": 0.005}, {"mm_pov": 0.025}, {"mm_pov": 0.1}],
    "actividad": [
        {"num_noise_agents": 1000, "lambda_a": 5.7e-12},
        {"num_noise_agents": 2000, "lambda_a": 1.14e-11},
        {"num_noise_agents": 4000, "lambda_a": 2.28e-11},
    ],
}


def config_id(params: Dict) -> str:
    """Identificador estable y legible de una combinacion de parametros."""
    return "|".join(f"{k}={params[k]!r}" if isinstance(params[k], str) else f"{k}={params[k]:g}"
                    for k in sorted(params))


def build_grid(spec: Optional[Dict[str, List[Dict]]] = None,
               max_combinaciones: int = MAX_COMBINACIONES) -> List[Dict]:
    """Producto cartesiano de los niveles de cada factor. Cada elemento es
    `{"id", "params", "niveles"}`; `niveles` guarda el indice del nivel de
    cada factor. Falla si la grilla supera `max_combinaciones` o si dos
    factores fijan el mismo parametro."""
    spec = GRID_DEFAULT if spec is None else spec
    if not spec or any(len(v) == 0 for v in spec.values()):
        raise ValueError("la especificacion de la grilla no puede tener factores vacios")
    factores = list(spec)
    n = 1
    for f in factores:
        n *= len(spec[f])
    if n > max_combinaciones:
        raise ValueError(f"la grilla tiene {n} combinaciones (maximo {max_combinaciones})")
    llaves = [set().union(*[set(nivel) for nivel in spec[f]]) for f in factores]
    for a, b in itertools.combinations(range(len(factores)), 2):
        if llaves[a] & llaves[b]:
            raise ValueError(f"los factores {factores[a]!r} y {factores[b]!r} comparten "
                             f"parametros: {sorted(llaves[a] & llaves[b])}")
    grid = []
    for idx in itertools.product(*[range(len(spec[f])) for f in factores]):
        params: Dict = {}
        for f, i in zip(factores, idx):
            params.update(spec[f][i])
        grid.append({"id": config_id(params), "params": params,
                     "niveles": dict(zip(factores, idx))})
    return grid


def build_screen(spec: Optional[Dict[str, List[Dict]]] = None) -> List[Dict]:
    """Sondeo de sensibilidad: la combinacion base (primer nivel de cada
    factor... salvo que se indique otro) y, de a un factor por vez, cada uno
    de sus otros niveles. Sirve para ver que palanca mueve cada momento antes
    de gastar el presupuesto de la grilla."""
    spec = GRID_DEFAULT if spec is None else spec
    factores = list(spec)
    base_idx = {f: _nivel_base(spec[f]) for f in factores}
    combos = [dict(base_idx)]
    for f in factores:
        for i in range(len(spec[f])):
            if i != base_idx[f]:
                combos.append({**base_idx, f: i})
    out = []
    for idx in combos:
        params: Dict = {}
        for f in factores:
            params.update(spec[f][idx[f]])
        out.append({"id": config_id(params), "params": params, "niveles": idx})
    return out


# Defaults de rmsc04 para los parametros de la grilla (firma verificada el
# 2026-10-03): el nivel "base" de cada factor es el que coincide con ellos.
RMSC04_DEFAULTS = {"mm_window_size": "adaptive", "mm_pov": 0.025, "mm_num_ticks": 10,
                   "mm_level_spacing": 5, "mm_spread_alpha": 0.75,
                   "num_noise_agents": 1000, "lambda_a": 5.7e-12}


def _nivel_base(niveles: Sequence[Dict]) -> int:
    for i, nivel in enumerate(niveles):
        if all(RMSC04_DEFAULTS.get(k) == v for k, v in nivel.items()):
            return i
    return 0


# ---------------------------------------------------------------------------
# Objetivos
# ---------------------------------------------------------------------------

def load_targets(calibration_json: Union[str, Path], ticker: str) -> Dict:
    """`objetivos_validacion[ticker]` del JSON de la 2.1.3b."""
    with open(calibration_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["objetivos_validacion"][ticker]


def pooled_sigma_bps(retornos_por_tramo: Dict[str, Sequence[float]]) -> float:
    """Volatilidad de 5 min del dia completo (bps): raiz de la media de las
    varianzas por tramo, ponderada por el numero de retornos."""
    num = sum(len(r) * float(np.var(r)) for r in retornos_por_tramo.values())
    den = sum(len(r) for r in retornos_por_tramo.values())
    return math.sqrt(num / den) * 1e4


# ---------------------------------------------------------------------------
# Perdida
# ---------------------------------------------------------------------------

PESOS: Dict[str, float] = {
    "volatilidad": 1.0, "spread": 1.0, "participacion": 0.5, "volumen_vela": 0.5, "ranking": 1.0,
}
# |ln| asignado a un momento simulado ausente, no finito o <= 0 (factor 100).
PENALIZACION_FALTANTE = math.log(100.0)
RANKINGS_ROBUSTOS = ("volatilidad_max_apertura", "volumen_vela_creciente")


def abs_log_ratio(sim: Optional[float], obj: Optional[float]) -> float:
    """|ln(sim / obj)|; `PENALIZACION_FALTANTE` si `sim` no sirve y NaN si el
    objetivo no existe (el termino se omite)."""
    if obj is None or not np.isfinite(obj) or obj <= 0:
        return float("nan")
    if sim is None or not np.isfinite(sim) or sim <= 0:
        return PENALIZACION_FALTANTE
    return abs(math.log(sim / obj))


def spread_distance(sim: Optional[float], bajo: float, alto: float) -> float:
    """Distancia log del spread simulado al intervalo [bajo, alto]: 0 dentro
    y |ln(sim / borde mas cercano)| fuera."""
    lo, hi = min(bajo, alto), max(bajo, alto)
    if sim is None or not np.isfinite(sim) or sim <= 0:
        return PENALIZACION_FALTANTE
    if sim < lo:
        return math.log(lo / sim)
    if sim > hi:
        return math.log(sim / hi)
    return 0.0


def robust_rankings(vol_por_tramo: Dict[str, Optional[float]],
                    volumen_vela_por_tramo: Dict[str, Optional[float]]) -> Dict[str, Optional[bool]]:
    """Rankings robustos de la 2.1.3b (se repiten en los tres cortes de
    datos): la volatilidad es maxima en la apertura y el volumen mediano por
    vela crece de apertura a media jornada a cierre. None si falta un dato."""
    def ok(d):
        return all(d.get(t) is not None and np.isfinite(d[t]) for t in TRAMO_NAMES)

    a, m, c = TRAMO_NAMES
    return {
        "volatilidad_max_apertura": (
            bool(vol_por_tramo[a] > vol_por_tramo[m] and vol_por_tramo[a] > vol_por_tramo[c])
            if ok(vol_por_tramo) else None),
        "volumen_vela_creciente": (
            bool(volumen_vela_por_tramo[a] < volumen_vela_por_tramo[m] < volumen_vela_por_tramo[c])
            if ok(volumen_vela_por_tramo) else None),
    }


def loss(sim: Dict[str, Dict], objetivos_por_tramo: Dict[str, Dict],
         pesos: Optional[Dict[str, float]] = None,
         vol_ref_unica_bps: Optional[float] = None) -> Dict:
    """Perdida de una configuracion.

    Args:
        sim: momentos simulados por tramo (`rmsc04_sim_stats.pool_moments`).
        objetivos_por_tramo: `objetivos_validacion[ticker]["por_tramo"]`.
        pesos: ver `PESOS`.
        vol_ref_unica_bps: modo grilla. La grilla simula el dia completo con
            un solo `fund_vol` (el de la volatilidad del dia), asi que la
            volatilidad simulada de cada tramo se compara contra esa
            referencia unica. Para el ranking, la volatilidad simulada se
            reescala por sigma_tramo / sigma_dia, que es lo que hara la
            config por tramo de la validacion (la volatilidad del mid es
            proporcional a `fund_vol`). En la validacion (None) cada tramo se
            corre con su `fund_vol` y se compara contra su propio objetivo.

    Returns:
        {"total", "terminos": {momento: {tramo: valor}}, "rankings",
         "n_rankings_fallidos", "vol_para_ranking"}.
    """
    w = dict(PESOS)
    w.update(pesos or {})
    terminos: Dict[str, Dict[str, float]] = {k: {} for k in ("volatilidad", "spread", "participacion", "volumen_vela")}
    vol_rank: Dict[str, Optional[float]] = {}
    for t in TRAMO_NAMES:
        s, o = sim.get(t, {}), objetivos_por_tramo[t]
        vol = s.get("volatilidad_bps")
        if vol_ref_unica_bps is None:
            terminos["volatilidad"][t] = abs_log_ratio(vol, o["volatilidad_bps"])
            vol_rank[t] = vol
        else:
            terminos["volatilidad"][t] = abs_log_ratio(vol, vol_ref_unica_bps)
            vol_rank[t] = (vol * o["volatilidad_bps"] / vol_ref_unica_bps
                           if vol is not None and np.isfinite(vol) else None)
        terminos["spread"][t] = spread_distance(
            s.get("spread_mediano_bps"), o["spread_cs_bps"], o["spread_roll_bps"])
        terminos["participacion"][t] = abs_log_ratio(
            s.get("participacion_volumen"), o["participacion_volumen_dia"])
        terminos["volumen_vela"][t] = abs_log_ratio(
            s.get("volumen_mediano_vela"), o["volumen_mediano_vela"])

    total = 0.0
    for k, por_tramo in terminos.items():
        total += w[k] * sum(v for v in por_tramo.values() if np.isfinite(v))
    rankings = robust_rankings(vol_rank, {t: sim.get(t, {}).get("volumen_mediano_vela") for t in TRAMO_NAMES})
    fallidos = sum(1 for v in rankings.values() if v is not True)
    total += w["ranking"] * fallidos
    return {"total": float(total), "terminos": terminos, "rankings": rankings,
            "n_rankings_fallidos": int(fallidos), "vol_para_ranking": vol_rank, "pesos": w}


def best_config(resultados: Dict[str, Dict]) -> Optional[str]:
    """Id de la configuracion completa con menor perdida (None si no hay)."""
    ok = {k: v for k, v in resultados.items()
          if v.get("completa") and v.get("perdida") and np.isfinite(v["perdida"]["total"])}
    if not ok:
        return None
    return min(ok, key=lambda k: (ok[k]["perdida"]["total"], k))


# ---------------------------------------------------------------------------
# Refinamiento local
# ---------------------------------------------------------------------------

REFINE_FACTOR = 1.5
# Parametros que se mueven juntos en el refinamiento; el resto, de a uno.
_GRUPOS_REFINE = (("num_noise_agents", "lambda_a"),)
_NO_REFINAR = ("mm_level_spacing",)
_ENTEROS = ("num_noise_agents", "mm_window_size", "mm_num_ticks")


def refine_candidates(best_params: Dict, factor: float = REFINE_FACTOR, max_n: int = 10) -> List[Dict]:
    """Vecinos del mejor punto de la grilla: cada parametro numerico (o
    grupo acoplado) multiplicado y dividido por `factor`, de a uno por vez.
    Los parametros no numericos (`mm_window_size = "adaptive"`) no se mueven."""
    grupos: List[Sequence[str]] = [g for g in _GRUPOS_REFINE if all(k in best_params for k in g)]
    agrupados = {k for g in grupos for k in g}
    for k in sorted(best_params):
        if k in agrupados or k in _NO_REFINAR:
            continue
        if isinstance(best_params[k], (int, float)) and not isinstance(best_params[k], bool):
            grupos.append((k,))
    out, vistos = [], {config_id(best_params)}
    for g in grupos:
        for f in (1.0 / factor, factor):
            p = dict(best_params)
            for k in g:
                v = best_params[k] * f
                p[k] = max(1, int(round(v))) if k in _ENTEROS else float(v)
            cid = config_id(p)
            if cid not in vistos:
                vistos.add(cid)
                out.append({"id": cid, "params": p})
    return out[:max_n]


# ---------------------------------------------------------------------------
# KS y tabla de momentos
# ---------------------------------------------------------------------------

def ks_summary(sim: Sequence[float], real: Sequence[float], alpha: float = 0.05) -> Dict:
    """KS de 2 muestras de retornos de 5 min simulados contra reales: D, p,
    D_crit y D/D_crit (como en la 2.1.3b). Se reporta sobre los retornos tal
    cual y, como referencia de forma, sobre ambas muestras estandarizadas
    (media 0, desvio 1)."""
    from scipy import stats

    from src.envs.calibration_poisson import ks_critical_value

    s = np.asarray(sim, dtype=float)
    r = np.asarray(real, dtype=float)
    s, r = s[np.isfinite(s)], r[np.isfinite(r)]
    out: Dict = {"n_sim": int(len(s)), "n_real": int(len(r)), "alpha": alpha}
    if len(s) < 2 or len(r) < 2:
        out.update({"D": None, "p": None, "D_crit": None, "D_ratio": None, "rechaza": None})
        return out
    d_crit = ks_critical_value(len(r), len(s), alpha)
    res = stats.ks_2samp(s, r)
    out.update({"D": float(res.statistic), "p": float(res.pvalue), "D_crit": float(d_crit),
                "D_ratio": float(res.statistic / d_crit), "rechaza": bool(res.pvalue < alpha)})
    if s.std() > 0 and r.std() > 0:
        z = stats.ks_2samp((s - s.mean()) / s.std(), (r - r.mean()) / r.std())
        out["estandarizado"] = {"D": float(z.statistic), "p": float(z.pvalue),
                                "D_ratio": float(z.statistic / d_crit),
                                "rechaza": bool(z.pvalue < alpha)}
    return out


def moments_table(sim: Dict[str, Dict], objetivos_por_tramo: Dict[str, Dict]) -> Dict[str, Dict]:
    """Por tramo, cada momento simulado junto a su objetivo y a ln(sim/obj).
    El spread se compara contra Roll y contra Corwin-Schultz."""
    pares = (
        ("volatilidad_bps", "volatilidad_bps", "volatilidad_bps"),
        ("spread_vs_roll_bps", "spread_mediano_bps", "spread_roll_bps"),
        ("spread_vs_cs_bps", "spread_mediano_bps", "spread_cs_bps"),
        ("participacion_volumen", "participacion_volumen", "participacion_volumen_dia"),
        ("volumen_mediano_vela", "volumen_mediano_vela", "volumen_mediano_vela"),
    )
    out: Dict[str, Dict] = {}
    for t in TRAMO_NAMES:
        s, o = sim.get(t, {}), objetivos_por_tramo[t]
        fila = {}
        for nombre, k_sim, k_obj in pares:
            vs, vo = s.get(k_sim), o.get(k_obj)
            ratio = (math.log(vs / vo) if vs is not None and vo and np.isfinite(vs) and vs > 0 else None)
            fila[nombre] = {"sim": vs, "objetivo": vo, "ln_sim_sobre_objetivo": ratio}
        out[t] = fila
    return out


# ---------------------------------------------------------------------------
# Persistencia reanudable
# ---------------------------------------------------------------------------

def save_json(path: Union[str, Path], data: Dict) -> None:
    """Escribe el JSON a un archivo temporal y lo renombra, para que una
    desconexion de Colab a mitad de escritura no deje un archivo corrupto."""
    import os

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    os.replace(tmp, path)


def load_resumable(path: Union[str, Path], firma: Dict) -> Dict:
    """Resultado parcial previo si su `firma` (lo que define la corrida:
    ticker, snapshot, config base, semillas...) coincide; si no, uno vacio.
    Una firma distinta nunca reutiliza resultados viejos."""
    path = Path(path)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            prev = json.load(f)
        if prev.get("firma") == firma:
            return prev
    return {"firma": firma, "resultados": {}}


def seeds_pendientes(entrada: Optional[Dict], seeds: Sequence[int],
                     reintentar_errores: bool = False) -> List[int]:
    """Semillas que faltan correr para una configuracion."""
    hechas = (entrada or {}).get("corridas", {})
    out = []
    for s in seeds:
        r = hechas.get(str(s))
        if r is None or (reintentar_errores and "error" in r):
            out.append(s)
    return out
