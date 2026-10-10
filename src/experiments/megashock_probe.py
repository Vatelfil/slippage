"""Sondeo de megashocks para acercar las colas de rmsc04 a las reales (2.2.4).

Elaborado por PS con apoyo de Claude Code; pendiente de revision por BF.

Contexto: con 30 semillas el KS de BF rechaza en media jornada y cierre, y la
curtosis simulada no calza (2,7 frente a 5,1 real en media jornada). BF dejo
anotado que, si la curtosis quedaba por debajo, los megashocks (saltos raros
del valor fundamental) entrarian a la busqueda. Este modulo lo prueba.

Metodo: por candidato (combinacion de parametros de megashock) se corren K
semillas de DIA COMPLETO con la config calibrada del tramo cierre, y se mide,
por tramo, el D del KS ESTANDARIZADO (compara solo la forma) contra los retornos
reales y la curtosis. Es un sondeo barato: los bloques de apertura y media
jornada usan el `fund_vol` del cierre, asi que su escala no es la final; por eso
se estandariza y solo se compara entre candidatos (el megashock por defecto de
rmsc04 es la referencia). La validacion
con la config de cada tramo se hace despues, solo para el candidato elegido.

Regla de adopcion (fijada antes de ver datos):
  (i)  el D estandarizado medio de los 3 tramos baja al menos 15 % respecto del candidato
       por defecto, y
  (ii) la volatilidad del bloque de cierre queda a +-15 % del objetivo real.
Si ningun candidato la cumple, se conserva la config de BF y la tarea se cierra
documentando que los megashocks no resuelven la diferencia de colas.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence

import numpy as np

from src.analysis.validacion_formal import TRAMOS, ks_test
from src.envs import rmsc04_sim_stats as ss
from src.envs import rmsc04_search as rs

MEJORA_D_MIN = 0.15
TOLERANCIA_VOL = 0.15
DEFAULT_MEGASHOCK = {"megashock_lambda_a": 2.77778e-18, "megashock_var": 50000}
SPEC_DEFAULT: Dict[str, List[Dict]] = {
    "base": [{"mm_pov": 0.005}],
    "megashock_frecuencia": [{"megashock_lambda_a": 2.77778e-18}, {"megashock_lambda_a": 5e-14},
                             {"megashock_lambda_a": 2e-13}],
    "megashock_tamano": [{"megashock_var": 50000}, {"megashock_var": 500000}],
}


def candidatos(spec: Optional[Dict[str, List[Dict]]] = None) -> List[Dict]:
    """Candidatos = producto de los niveles de la grilla (`rmsc04_search.build_grid`)."""
    return rs.build_grid(spec or SPEC_DEFAULT, max_combinaciones=64)


def es_default(params: Dict) -> bool:
    return all(params.get(k) == v for k, v in DEFAULT_MEGASHOCK.items())


def metricas_candidato(momentos: Sequence[Dict], real_returns: Dict[str, Sequence[float]]) -> Dict:
    """D del KS, curtosis y volatilidad por tramo, con los retornos de todas las
    semillas del candidato (corridas de dia completo)."""
    out: Dict = {"n_semillas": len(momentos), "por_tramo": {}}
    ds = []
    for t in TRAMOS:
        rets: List[float] = []
        for m in momentos:
            if m.get(t, {}).get("completo"):
                rets.extend(m[t].get("retornos_5min", []))
        r = np.asarray(rets, dtype=float)
        ks = ks_test(r, real_returns[t])
        z = ks.get("estandarizado") or {}
        out["por_tramo"][t] = {"n": int(len(r)), "D": z.get("D"), "p": z.get("p"),
                                "curtosis": ss.excess_kurtosis(r) if len(r) > 3 else None,
                                "volatilidad_bps": float(r.std() * 1e4) if len(r) > 1 else None}
        if z.get("D") is not None:
            ds.append(z["D"])
    out["D_medio"] = float(np.mean(ds)) if len(ds) == len(TRAMOS) else None
    return out


def correr_probe(kwargs_cierre: Dict, cands: Sequence[Dict], seeds: Sequence[int], estado: Dict,
                 guardar: Callable[[Dict], None],
                 simular: Optional[Callable[[Dict, int, str], Dict]] = None,
                 presupuesto_s: Optional[float] = None, log: Callable[[str], None] = print) -> bool:
    """Corre las simulaciones pendientes (candidato x semilla, dia completo)."""
    simular = simular or ss.simulate_moments
    t_ini = time.time()
    corridas = estado.setdefault("corridas", {})
    for seed in seeds:
        for c in cands:
            hechas = corridas.setdefault(c["id"], {})
            if str(seed) in hechas and "momentos" in hechas[str(seed)]:
                continue
            if presupuesto_s is not None and time.time() - t_ini > presupuesto_s:
                log("Presupuesto de tiempo agotado: volver a ejecutar para continuar.")
                return False
            t0 = time.time()
            try:
                mom = simular({**kwargs_cierre, **c["params"]}, int(seed), "16:00:00")
                hechas[str(seed)] = {"momentos": mom, "segundos": round(time.time() - t0, 1)}
                log(f"{c['id']} seed={seed}: {time.time() - t0:.0f}s")
            except Exception as e:  # una corrida fallida no tumba la sesion
                hechas[str(seed)] = {"error": f"{type(e).__name__}: {e}"}
                log(f"{c['id']} seed={seed}: ERROR {hechas[str(seed)]['error']}")
            guardar(estado)
    return True


def evaluar_y_decidir(estado: Dict, cands: Sequence[Dict], real_returns: Dict[str, Sequence[float]],
                      vol_objetivo_cierre_bps: float) -> Dict:
    """Metricas por candidato y decision segun la regla del encabezado."""
    res: Dict[str, Dict] = {}
    for c in cands:
        moms = [v["momentos"] for v in estado.get("corridas", {}).get(c["id"], {}).values() if "momentos" in v]
        if moms:
            m = metricas_candidato(moms, real_returns)
            m["params"] = c["params"]
            res[c["id"]] = m
    base_id = next((c["id"] for c in cands if es_default(c["params"])), None)
    base = res.get(base_id)
    decision: Dict = {"referencia": base_id, "adopta": None, "motivo": "", "candidatos": {}}
    if base is None or base.get("D_medio") is None:
        decision["motivo"] = "sin datos del candidato de referencia (megashock por defecto)"
        return {"metricas": res, "decision": decision}
    mejores = []
    for cid, m in res.items():
        if cid == base_id or m.get("D_medio") is None:
            continue
        mejora = 1.0 - m["D_medio"] / base["D_medio"]
        vol = m["por_tramo"]["cierre"]["volatilidad_bps"]
        vol_ok = vol is not None and abs(vol - vol_objetivo_cierre_bps) / vol_objetivo_cierre_bps <= TOLERANCIA_VOL
        cumple = bool(mejora >= MEJORA_D_MIN and vol_ok)
        decision["candidatos"][cid] = {"mejora_D_medio": float(mejora), "volatilidad_cierre_ok": bool(vol_ok),
                                        "cumple_regla": cumple}
        if cumple:
            mejores.append((mejora, cid))
    if mejores:
        mejores.sort(reverse=True)
        decision["adopta"] = mejores[0][1]
        decision["motivo"] = (f"{mejores[0][1]} baja el D medio un {mejores[0][0] * 100:.0f} % y mantiene la "
                              "volatilidad del cierre: pasa a validacion con 30 semillas por tramo.")
    else:
        decision["motivo"] = ("Ningun candidato baja el D medio al menos 15 % con la volatilidad del cierre dentro de "
                              "+-15 %: se conserva la config de BF y los megashocks no resuelven la diferencia de colas.")
    return {"metricas": res, "decision": decision}
