"""Impacto acumulado entre ventanas del Maestro (BORRADOR de PS para MR, 29 oct 2026, con apoyo de Claude Code).

Por qué existe
--------------
`MaestroEjecutorEnv` crea un mercado nuevo para cada ventana, así que lo que el sistema compró a las 10:00 no encarece
lo que compra a las 10:30. Sin eso el Maestro no tiene nada que coordinar: le conviene comprar lo antes posible. Ver
`docs/revision_opus_PS.md` y la decisión de diseño en `docs/LEEME_MR.md`.

Modelo (supuesto declarado, no calibrado)
------------------------------------------
Ley de la raíz cuadrada del impacto (Tóth et al., 2011; Almgren et al., 2005) con decaimiento exponencial:

    impacto_bps = Y · sigma_dia_bps · sqrt(Q_efectiva / V_dia)
    Q_efectiva  = Q_efectiva · exp(−minutos / tau) + q comprado en la ventana

- Y = 0,5 es un valor típico de la literatura (del orden de 1). Es el parámetro que habría que contrastar con ABIDES.
- sigma_dia_bps sale de la volatilidad de 5 minutos calibrada para Poisson (2.1.3), escalada a un día de 78 barras.
- V_dia es el volumen del día simulado de la meta-orden (`volumen_dia_simulado` de las órdenes v2).
- tau = 120 min: la mitad del impacto se disipa en ≈ 83 minutos.

Al empezar cada ventana se calcula el impacto con lo comprado antes y se multiplican por (1 + impacto) los precios de
esa ventana que leen el Maestro, los evaluadores y los benchmarks. El impacto dentro de una ventana ya lo simula el
entorno (ABIDES o Poisson), por eso aquí solo se arrastra lo de las ventanas anteriores. La primera ventana no se toca,
así que el precio de llegada no cambia. Se aplica igual a todas las estrategias, de modo que la comparación con TWAP y
VWAP sigue siendo pareada.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Dict, Optional

BARRAS_5MIN_DIA = 78
MINUTOS_ENTRE_VENTANAS = 30.0     # una decisión del Maestro y un periodo de TWAP/VWAP

CAMPOS_PRECIO = ("p_fill_step_clp", "p_ejecutado_step", "p_mid_clp", "p_mid_decision", "p_mid", "best_ask", "best_bid")
CAMPOS_CANTIDAD = ("q_fill_step", "q_ejecutado_step")


@dataclass(frozen=True)
class ParametrosImpacto:
    sigma_dia_bps: float
    volumen_dia: float
    y: float = 0.5
    tau_min: float = 120.0
    minutos_entre_ventanas: float = MINUTOS_ENTRE_VENTANAS


def sigma_dia_bps(ticker: str) -> float:
    """Volatilidad diaria en bps a partir de la de 5 minutos de cada tramo (promedio de los tres)."""
    from src.envs.reward_utils import sigma_5min_tramo
    s5 = [sigma_5min_tramo(ticker, t) for t in ("apertura", "media_jornada", "cierre")]
    return float(sum(s5) / len(s5) * math.sqrt(BARRAS_5MIN_DIA) * 1e4)


def parametros_para(ticker: str, volumen_dia: float, **kw) -> ParametrosImpacto:
    return ParametrosImpacto(sigma_dia_bps=sigma_dia_bps(ticker), volumen_dia=float(volumen_dia), **kw)


class ImpactoAcumulado:
    """Estado de una meta-orden (o una jornada del Maestro): lo comprado en ventanas anteriores, ya decaído."""

    def __init__(self, p: ParametrosImpacto):
        self.p = p
        self.q_efectiva = 0.0
        self.ventanas = 0
        self.impacto_actual_bps = 0.0

    def impacto_bps(self) -> float:
        if self.q_efectiva <= 0 or self.p.volumen_dia <= 0:
            return 0.0
        return self.p.y * self.p.sigma_dia_bps * math.sqrt(self.q_efectiva / self.p.volumen_dia)

    def nueva_ventana(self) -> float:
        """Llamar al empezar cada ventana: decae lo anterior y devuelve el impacto (bps) que tendrá esta ventana."""
        if self.ventanas > 0:
            self.q_efectiva *= math.exp(-self.p.minutos_entre_ventanas / self.p.tau_min)
        self.ventanas += 1
        self.impacto_actual_bps = self.impacto_bps()
        return self.impacto_actual_bps

    def registrar(self, q: float) -> None:
        if q > 0:
            self.q_efectiva += float(q)


class EntornoConImpacto:
    """Envuelve un Ejecutor (ABIDES o Poisson) y desplaza los precios de su `info` por el impacto acumulado."""

    def __init__(self, env, estado: ImpactoAcumulado):
        self._env, self._estado = env, estado
        self._factor = 1.0

    def reset(self, *a, **k):
        obs, info = self._env.reset(*a, **k)
        self._factor = 1.0 + self._estado.nueva_ventana() / 1e4
        info = dict(info)
        info["impacto_acumulado_bps"] = self._estado.impacto_actual_bps
        return obs, info

    def step(self, action):
        obs, r, done, trunc, info = self._env.step(action)
        info = dict(info)
        for campo in CAMPOS_PRECIO:
            if info.get(campo) is not None:
                info[campo] = float(info[campo]) * self._factor
        for campo in CAMPOS_CANTIDAD:
            if campo in info:
                self._estado.registrar(float(info[campo]))
                break
        info["impacto_acumulado_bps"] = self._estado.impacto_actual_bps
        return obs, r, done, trunc, info

    def close(self):
        if hasattr(self._env, "close"):
            self._env.close()

    def __getattr__(self, nombre):
        return getattr(self._env, nombre)


def con_impacto(fabrica: Callable, p: Optional[ParametrosImpacto]) -> Callable:
    """Fábrica nueva con un estado de impacto propio. Crear UNA por meta-orden o jornada (el estado no se reinicia solo).
    Con `p = None` devuelve la fábrica tal cual."""
    if p is None:
        return fabrica
    estado = ImpactoAcumulado(p)

    def f(**kw):
        return EntornoConImpacto(fabrica(**kw), estado)

    f.estado = estado
    return f


def fabrica_poisson(ticker: str) -> Callable:
    """Fábrica de Poisson con el ticker fijado (para envolverla cuando el evaluador usaría el Poisson por defecto)."""
    from src.envs.fallback_poisson_env import EjecutorEnvPoissonFallback

    def f(**kw):
        kw.setdefault("ticker", ticker)
        return EjecutorEnvPoissonFallback(**kw)

    return f


def resumen(p: Optional[ParametrosImpacto]) -> Optional[Dict[str, float]]:
    if p is None:
        return None
    return {"y": p.y, "sigma_dia_bps": p.sigma_dia_bps, "volumen_dia": p.volumen_dia, "tau_min": p.tau_min}
