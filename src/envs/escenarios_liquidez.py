"""Escenarios de liquidez baja, media y alta (tarea 3.1.3).

BORRADOR de PS para BF (29 oct 2026), con apoyo de Claude Code. Los factores salen de
`data/scenarios/escenarios_liquidez_v1.json` y son una PROPUESTA sin validar: BF los fija y el cuaderno C-6
(`scripts/colab/c6_escenarios_liquidez_bf.py`) comprueba que "baja" de verdad cuesta más que "media" y "alta".

Un escenario es un solo factor f que multiplica la liquidez del mercado simulado, sin tocar los entornos:

- ABIDES (rmsc04 calibrado, 2.2.4): `num_noise_agents`, `lambda_a` (llegada de los agentes de valor) y `mm_pov`
  (tamaño de las cotizaciones del market maker) se multiplican por f.
- Poisson (2.1.3): solo la profundidad del libro (`avg_order_size`) se multiplica por f. Las tasas de llegada no se
  tocan porque en ese simulador solo mueven el precio medio: subirlas daría más volatilidad, no más liquidez. Se ajusta
  el simulador ya creado, así que el entorno de BF no cambia.

Con f = 1 todo queda como estaba.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Dict, Optional, Union

REPO_ROOT = Path(__file__).resolve().parents[2]
ESCENARIOS_JSON = REPO_ROOT / "data" / "scenarios" / "escenarios_liquidez_v1.json"

CLAVES_ABIDES = ("num_noise_agents", "lambda_a", "mm_pov")
CLAVES_POISSON = ("avg_order_size",)


def cargar_escenarios(ruta: Optional[Union[str, Path]] = None) -> Dict[str, float]:
    """{nombre: factor} desde el JSON de escenarios."""
    with open(ruta or ESCENARIOS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {nombre: float(e["factor"]) for nombre, e in data["escenarios"].items()}


def factor_de(escenario: Optional[str], ruta: Optional[Union[str, Path]] = None) -> float:
    """Factor de un escenario por nombre; None o "media" sin JSON dan 1."""
    if escenario is None:
        return 1.0
    escenarios = cargar_escenarios(ruta)
    if escenario not in escenarios:
        raise ValueError(f"escenario desconocido: {escenario!r}. Validos: {sorted(escenarios)}")
    return escenarios[escenario]


def escalar_kwargs_abides(kwargs: Dict, factor: float) -> Dict:
    """Copia de los kwargs de rmsc04 de un tramo con la liquidez multiplicada por `factor`."""
    out = dict(kwargs)
    if "num_noise_agents" in out:
        out["num_noise_agents"] = max(1, int(round(out["num_noise_agents"] * factor)))
    for clave in ("lambda_a", "mm_pov"):
        if clave in out:
            out[clave] = float(out[clave]) * factor
    return out


def aplicar_escenario_poisson(env, factor: float):
    """Ajusta el simulador de un `EjecutorEnvPoissonFallback` ya creado (antes del primer reset)."""
    if factor == 1.0:
        return env
    sim = env._sim
    sim.calib["avg_order_size"] = float(sim.calib["avg_order_size"]) * factor
    sim._avg_order_size = max(sim.calib["avg_order_size"], 1.0)
    return env


def fabrica_poisson(factor: float = 1.0, **comunes) -> Callable:
    """Fábrica de Ejecutores de Poisson con el escenario aplicado (misma firma que `EjecutorEnvPoissonFallback`)."""
    from src.envs.fallback_poisson_env import EjecutorEnvPoissonFallback

    def fabrica(**kw):
        return aplicar_escenario_poisson(EjecutorEnvPoissonFallback(**{**comunes, **kw}), factor)

    return fabrica


def fabrica_abides(calibrated_json, ticker: str = "FALABELLA", factor: float = 1.0, **comunes) -> Callable:
    """Como `make_calibrated_env_factory`, pero con la liquidez del escenario. Requiere ABIDES."""
    from src.envs.abides_ejecutor_env import make_calibrated_env_factory
    from src.envs.calibrate_rmsc04_ipsa import load_abides_kwargs

    base = make_calibrated_env_factory(calibrated_json, ticker=ticker, **comunes)
    if factor == 1.0:
        return base
    por_tramo = load_abides_kwargs(calibrated_json)

    def fabrica(executor_id="apertura", **kw):
        kw.setdefault("background_config_extra_kvargs", escalar_kwargs_abides(por_tramo[executor_id], factor))
        return base(executor_id=executor_id, **kw)

    return fabrica


# ---------------------------------------------------------------------------
# Lo que comparten el evaluador del sistema y el de benchmarks (90 corridas)
# ---------------------------------------------------------------------------

def ajustar_ordenes(ordenes, factor_tamano: float = 1.0):
    """Copia de las meta-órdenes con la cantidad multiplicada por `factor_tamano` (los tres tamaños de la 3.2.1: con las
    órdenes v2, 0,5 / 1 / 1,5 dan 5 %, 10 % y 15 % del volumen del día; las de cierre, la mitad)."""
    if factor_tamano == 1.0:
        return list(ordenes)
    return [dict(o, cantidad=max(1, int(round(float(o["cantidad"]) * factor_tamano)))) for o in ordenes]


def sufijo_condicion(escenario: Optional[str], factor_tamano: float) -> str:
    """Parte del nombre de archivo que distingue la condición; vacía en la condición por defecto (archivos de siempre)."""
    partes = []
    if escenario is not None:
        partes.append(f"liq-{escenario}")
    if factor_tamano != 1.0:
        partes.append(f"tam-{factor_tamano:g}")
    return ("_" + "_".join(partes)) if partes else ""


def fabricas_por_ticker(entorno: str, calibrated_dir, snapshot: str, factor: float = 1.0) -> Callable:
    """`ticker -> fábrica` (o None para el Poisson de siempre) con el escenario aplicado."""
    cache: Dict[str, Callable] = {}

    def por_ticker(ticker: str):
        if entorno == "poisson":
            return None if factor == 1.0 else fabrica_poisson(factor, ticker=ticker)
        if ticker not in cache:
            js = Path(calibrated_dir) / f"rmsc04_ipsa_{ticker}_{snapshot}.json"
            cache[ticker] = fabrica_abides(js, ticker=ticker, factor=factor)
        return cache[ticker]

    return por_ticker
