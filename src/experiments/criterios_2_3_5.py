"""Criterios de convergencia del entrenamiento inicial del Ejecutor (tarea 2.3.5).

Elaborado por BF con apoyo de Claude Code. Logica pura (numpy y scipy): no importa torch ni ABIDES.

Criterios fijados por BF antes de correr (regla R6 del plan):
  1. Sin NaN: ningun valor no finito en el CSV del entrenador.
  2. El retorno final es mayor que el inicial: Mann-Whitney unilateral (alfa 0,05). El CSV trae `reward_mean`
     por actualizacion (10 episodios cada una), no por episodio, asi que se comparan las primeras 10
     actualizaciones con las ultimas 10. DESVIACION: el criterio original era primeros contra ultimos 20 episodios.
  3. KL mediano bajo el objetivo del entrenador (`target_kl` = 0,015).
  4. Cumplimiento medio >= 95 % en la evaluacion con la politica determinista (regla de vigilancia de D3).
  5. Slippage frente a la TWAP heuristica (`twap_limit_medio`) en las mismas semillas: Wilcoxon pareado,
     el mismo calculo que `scripts/analizar_entrenamiento_inicial.py` (bilateral). Se cumple si la red tiene
     menos slippage que la TWAP con p < alfa.
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence

import numpy as np
from scipy import stats

ALFA = 0.05
N_ACTUALIZACIONES = 10        # actualizaciones de cada extremo para el Mann-Whitney (10 x 10 episodios)
TARGET_KL = 0.015             # PPOConfig.target_kl (src/training/ppo_trainer.py)
UMBRAL_CUMPLIMIENTO = 0.95    # regla de vigilancia de D3
REFERENCIA_TWAP = "twap_limit_medio"


def sin_nan(filas: Optional[Sequence[Dict[str, float]]]) -> Dict:
    """Criterio 1. `filas` es el CSV del entrenador como lista de diccionarios (None si no hay CSV)."""
    if filas is None:
        return {"aplicable": False, "motivo": "sin CSV del entrenador", "cumple": None}
    n = sum(1 for r in filas for v in r.values() if not math.isfinite(float(v)))
    return {"aplicable": True, "n_actualizaciones": len(filas), "valores_no_finitos": n, "cumple": n == 0}


def retorno_mejora(reward_mean: Optional[Sequence[float]], n: int = N_ACTUALIZACIONES, alfa: float = ALFA) -> Dict:
    """Criterio 2: Mann-Whitney unilateral (las ultimas `n` actualizaciones > las primeras `n`). Necesita al menos
    2n actualizaciones para que los dos grupos no se solapen."""
    if reward_mean is None:
        return {"aplicable": False, "motivo": "sin CSV del entrenador", "cumple": None}
    r = np.asarray(reward_mean, dtype=float)
    if len(r) < 2 * n:
        return {"aplicable": False, "motivo": f"solo {len(r)} actualizaciones (hacen falta {2 * n})", "cumple": None}
    ini, fin = r[:n], r[-n:]
    mw = stats.mannwhitneyu(fin, ini, alternative="greater")
    return {"aplicable": True, "n_por_grupo": n, "media_inicial": float(ini.mean()), "media_final": float(fin.mean()),
            "U": float(mw.statistic), "p": float(mw.pvalue), "alfa": alfa, "cumple": bool(mw.pvalue < alfa)}


def kl_mediano(kl: Optional[Sequence[float]], target: float = TARGET_KL) -> Dict:
    """Criterio 3."""
    if kl is None:
        return {"aplicable": False, "motivo": "sin CSV del entrenador", "cumple": None}
    k = np.asarray(kl, dtype=float)
    med = float(np.median(k))
    return {"aplicable": True, "mediana": med, "maximo": float(k.max()), "target": target, "cumple": med < target}


def cumplimiento(evaluacion: Optional[Dict], umbral: float = UMBRAL_CUMPLIMIENTO) -> Dict:
    """Criterio 4, sobre el resumen de evaluacion (`evaluacion_entrenada`, politica determinista)."""
    if not evaluacion or evaluacion.get("cumplimiento_medio") is None:
        return {"aplicable": False, "motivo": "sin evaluacion", "cumple": None}
    c = float(evaluacion["cumplimiento_medio"])
    return {"aplicable": True, "valor": c, "umbral": umbral, "n_semillas": evaluacion.get("n"), "cumple": c >= umbral}


def slippage_pareado(entrenada: Optional[Dict], otra: Optional[Dict], alfa: float = ALFA) -> Dict:
    """Criterio 5: red entrenada menos la alternativa, pareado por semilla (negativo = la red tiene menos
    slippage). Si la red no ejecuto en alguna semilla no hay slippage que comparar."""
    if not entrenada or not otra:
        return {"aplicable": False, "motivo": "sin evaluacion", "cumple": None}
    tr = np.asarray([np.nan if v is None else v for v in entrenada["slippage_por_semilla"]], dtype=float)
    x = np.asarray([np.nan if v is None else v for v in otra["slippage_por_semilla"]], dtype=float)
    if not (np.isfinite(tr).all() and np.isfinite(x).all()):
        n_sin = int((~np.isfinite(tr)).sum())
        return {"aplicable": False, "motivo": f"la red no ejecuto en {n_sin} de {len(tr)} semillas", "cumple": False}
    d = tr - x
    p = float(stats.wilcoxon(tr, x).pvalue) if np.any(d != 0) else 1.0
    dif = float(d.mean())
    return {"aplicable": True, "n": int(len(d)), "dif_media_bps": dif, "ee_bps": float(d.std(ddof=1) / np.sqrt(len(d))),
            "p_wilcoxon": p, "alfa": alfa, "cumple": bool(dif < 0 and p < alfa)}


def evaluar_corrida(estado: Dict, filas: Optional[List[Dict[str, float]]] = None) -> Dict:
    """Los cinco criterios de una corrida (estado JSON de `entrenamiento_inicial_ps.py` y su CSV, si existe).
    El criterio 5 se evalua con la politica determinista (la de la regla de D3); la muestreada se informa aparte."""
    refs = estado.get("referencias", {})
    twap = refs.get(REFERENCIA_TWAP)
    det = estado.get("evaluacion_entrenada")
    mue = estado.get("evaluacion_entrenada_estocastica")
    criterios = {
        "sin_nan": sin_nan(filas),
        "retorno_final_mayor": retorno_mejora(None if filas is None else [r["reward_mean"] for r in filas]),
        "kl_mediano_bajo_target": kl_mediano(None if filas is None else [r["kl"] for r in filas]),
        "cumplimiento_95": cumplimiento(det),
        "slippage_vs_twap": slippage_pareado(det, twap),
    }
    informativo = {
        "slippage_vs_twap_muestreada": slippage_pareado(mue, twap) if mue else None,
        "slippage_vs_red_sin_entrenar": slippage_pareado(det, estado.get("evaluacion_sin_entrenar")),
        "slippage_vs_red_sin_entrenar_muestreada": (slippage_pareado(mue, estado.get("evaluacion_sin_entrenar"))
                                                    if mue else None),
        "cumplimiento_muestreada": None if not mue else mue.get("cumplimiento_medio"),
    }
    veredictos = [c["cumple"] for c in criterios.values()]
    return {"criterios": criterios, "informativo": informativo,
            "cumple_todos": all(v is True for v in veredictos),
            "n_cumple": sum(v is True for v in veredictos), "n_no_cumple": sum(v is False for v in veredictos),
            "n_no_evaluable": sum(v is None for v in veredictos)}


def contar_acciones_espera(decode, traducir, n_acciones: int, remaining: float = 1000.0,
                           best_bid: float = 59_690.0, best_ask: float = 59_700.0) -> Dict:
    """Cuenta las acciones del espacio plano que el puente traduce a `[]` (no envia ordenes = esperar) con
    inventario pendiente. `decode(idx)` -> (tipo, bucket, nivel); `traducir(accion, remaining, bid, ask)` -> lista.
    Se pasan como funciones para que este modulo no importe gymnasium ni el puente."""
    espera = [i for i in range(n_acciones) if traducir(decode(i), remaining, best_bid, best_ask) == []]
    return {"n_acciones": n_acciones, "n_espera": len(espera), "fraccion": len(espera) / n_acciones, "indices": espera}
