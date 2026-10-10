"""Corridas de simulacion para la validacion formal de la tarea 2.2.5 (PS).

Elaborado por PS con apoyo de Claude Code; pendiente de revision por BF
(responsable de la calibracion de rmsc04, tarea 2.2.4).

Corre RMSC04 (ABIDES) con semillas NUEVAS, por tramo, en dos modos:
    - "despues": con la configuracion calibrada de la 2.2.4
      (`rmsc04_ipsa_<ticker>_<snapshot>.json`, `por_tramo[tramo].abides_kwargs`).
    - "antes": con la configuracion de fabrica de rmsc04 (sin calibrar).

Guarda el resultado de CADA corrida (momentos y retornos de 5 min por tramo)
con el mismo formato que `scripts/colab/rmsc04_validate.py` de Benjamin:
`resultados[tramo]["corridas"][semilla]["momentos"]`. A diferencia de los JSON
versionados de la 2.2.4, que solo traen momentos agrupados, aqui quedan los
valores por semilla, que es lo que necesitan Mann-Whitney y Kruskal-Wallis.

La logica pura (sin ABIDES) vive aqui para poder probarla con un simulador
de mentira; el script de Colab es `scripts/colab/validacion_2_2_5_ps.py`.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, Dict, Optional, Sequence

from src.envs import rmsc04_sim_stats as ss
from src.envs.rmsc04_search import load_resumable, save_json

MODOS = ("despues", "antes")
TRAMO_END_TIME: Dict[str, str] = {
    name: f"{b // 3600:02d}:{b % 3600 // 60:02d}:00" for name, (_, b) in ss.TRAMO_BOUNDS_S.items()
}


def kwargs_para_modo(modo: str, kwargs_calibrados: Dict[str, Dict]) -> Dict[str, Dict]:
    """Config de ABIDES por tramo para cada modo: calibrada ("despues") o la
    de fabrica de rmsc04 ("antes", diccionario vacio = todos los defaults)."""
    if modo not in MODOS:
        raise ValueError(f"modo invalido: {modo!r}. Validos: {MODOS}")
    if modo == "despues":
        return {t: dict(kwargs_calibrados[t]) for t in ss.TRAMO_NAMES}
    return {t: {} for t in ss.TRAMO_NAMES}


def semillas(seed_base: int, n: int) -> list:
    """Semillas seed_base+1 .. seed_base+n (distintas de las de la busqueda,
    101-130 y las de Benjamin, si se usa un seed_base >= 200)."""
    return [seed_base + i for i in range(1, n + 1)]


def pendientes(parcial: Dict, seeds: Sequence[int], tramos: Sequence[str]) -> int:
    """Cuantas corridas (tramo x semilla) faltan por hacer."""
    faltan = 0
    for t in tramos:
        hechas = parcial.get("resultados", {}).get(t, {}).get("corridas", {})
        faltan += sum(1 for s in seeds if "momentos" not in hechas.get(str(s), {}))
    return faltan


def run_runs(kwargs_por_tramo: Dict[str, Dict], seeds: Sequence[int], parcial: Dict, parcial_path: Path,
             simular: Optional[Callable[[Dict, int, str], Dict]] = None,
             tramos: Sequence[str] = ss.TRAMO_NAMES, presupuesto_s: Optional[float] = None,
             log: Callable[[str], None] = print) -> bool:
    """Corre las simulaciones pendientes y guarda tras cada una.

    El orden es semilla por fuera y tramo por dentro: si se agota el
    presupuesto de tiempo, todos los tramos quedan con la misma cantidad de
    semillas. Devuelve True si no quedo nada pendiente.
    """
    simular = simular or ss.simulate_moments
    t_inicio = time.time()
    for seed in seeds:
        for tramo in tramos:
            corridas = parcial.setdefault("resultados", {}).setdefault(tramo, {"corridas": {}})["corridas"]
            if "momentos" in corridas.get(str(seed), {}):
                continue
            if presupuesto_s is not None and time.time() - t_inicio > presupuesto_s:
                log(f"Presupuesto de tiempo agotado ({presupuesto_s / 60:.0f} min). "
                    f"Quedan {pendientes(parcial, seeds, tramos)} corridas; volver a ejecutar para continuar.")
                return False
            t0 = time.time()
            try:
                mom = simular(kwargs_por_tramo[tramo], int(seed), TRAMO_END_TIME[tramo])
                corridas[str(seed)] = {"momentos": mom, "segundos": round(time.time() - t0, 1)}
                log(f"{tramo:14s} seed={seed}: {time.time() - t0:.0f}s")
            except Exception as e:  # una corrida fallida no tumba toda la sesion
                corridas[str(seed)] = {"error": f"{type(e).__name__}: {e}"}
                log(f"{tramo:14s} seed={seed}: ERROR {corridas[str(seed)]['error']}")
            save_json(parcial_path, parcial)
    return pendientes(parcial, seeds, tramos) == 0


def abrir_parcial(path: Path, ticker: str, snapshot: str, modo: str, kwargs_por_tramo: Dict[str, Dict]) -> Dict:
    """Estado reanudable: solo se reutiliza si la configuracion coincide."""
    firma = {"tarea": "2.2.5", "ticker": ticker, "snapshot": snapshot, "modo": modo,
             "kwargs_por_tramo": kwargs_por_tramo}
    return load_resumable(path, firma)
