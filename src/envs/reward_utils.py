"""Recompensa de los Agentes Ejecutores -- tarea 2.2.3 (BF).

    R_E = (P_mid_t - P_ejec_t) * q_ejec - beta * sigma2_precio * q_ejec
    (Titulo I, seccion 4.2.4)

Helper unico para los dos entornos del Ejecutor (`fallback_poisson_env.py` y
`abides_ejecutor_env.py`), de modo que la formula, la varianza y la escala
sean las mismas en ambos. Logica pura: no importa ABIDES ni gymnasium.

sigma2_precio
    Varianza del P_mid en una ventana movil CAUSAL de las ultimas W
    decisiones (`VENTANA_SIGMA2_PASOS`, 20 pasos = 10 min con pasos de 30 s):
    la varianza que entra en la recompensa del paso t usa solo los P_mid
    observados hasta t-1. Mientras la ventana tiene menos de
    `SIGMA2_MIN_PUNTOS` puntos se usa un prior del tramo,

        prior = (sigma_5min * P_ref)^2 * (dt_paso / 300 s),

    la varianza de un cambio de precio de un paso. Para un paseo aleatorio,
    la varianza muestral de n niveles consecutivos vale en promedio
    sigma_paso^2 * (n + 1) / 6: con n = 5 coincide con el prior (por eso el
    minimo es 5) y con la ventana llena (n = 20) es 3,5 veces el prior.
    Unidades: (unidad de precio)^2; en los entornos, CLP^2.

Interpretacion
    Todo el slice debe ejecutarse, asi que el termino de riesgo no castiga
    esperar (eso lo hace lambda en R_M): empuja a ejecutar cuando la varianza
    reciente del precio es menor.

Escala
    "bruta": R_E en CLP (crece con el tamano del slice).
    "por_accion_slice": R_E / q_slice, en CLP por accion del slice asignado.
"""
from __future__ import annotations

import json
from collections import deque
from pathlib import Path
from typing import Deque, Dict, Optional, Union

import numpy as np

from src.config.market_params import (
    BAR_MINUTES,
    BETA_RIESGO_EJECUTOR,
    ESCALA_RECOMPENSA_EJECUTOR,
    ESCALAS_RECOMPENSA,
    SIGMA2_MIN_PUNTOS,
    STEP_SECONDS,
    VENTANA_SIGMA2_PASOS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CALIBRATION_JSON = REPO_ROOT / "data" / "calibration" / "poisson_params_2026-08-23.json"


def prior_sigma2(sigma_5min: float, p_ref: float, step_seconds: float = STEP_SECONDS) -> float:
    """Prior de sigma2: varianza del cambio de precio en un paso de decision,
    (sigma_5min * P_ref)^2 * (dt_paso / 300 s). `sigma_5min` es el desvio del
    retorno log de 5 min del tramo (`obs_return_std` de la 2.1.3)."""
    return float((sigma_5min * p_ref) ** 2 * (step_seconds / (BAR_MINUTES * 60.0)))


def sigma_5min_tramo(ticker: str, tramo: str,
                     calibration_json: Optional[Union[str, Path]] = None) -> float:
    """`obs_return_std` de (ticker, tramo) en `poisson_params_<fecha>.json`."""
    with open(calibration_json or DEFAULT_CALIBRATION_JSON, "r", encoding="utf-8") as f:
        params = json.load(f)["params"]
    return float(abs(params[ticker.replace(".SN", "").upper()][tramo]["obs_return_std"]))


class RollingPriceVariance:
    """Varianza muestral del P_mid en una ventana movil de `window` puntos.

    Uso causal: leer `sigma2` ANTES de `update(p_mid_t)`, o llamar a
    `step(p_mid_t)`, que devuelve la varianza con los datos hasta t-1 y luego
    incorpora p_mid_t.
    """

    def __init__(self, window: int = VENTANA_SIGMA2_PASOS, prior_sigma2: float = 0.0,
                 min_points: int = SIGMA2_MIN_PUNTOS):
        if min_points < 2 or window < min_points:
            raise ValueError("se requiere window >= min_points >= 2")
        self.window = int(window)
        self.min_points = int(min_points)
        self.prior_sigma2 = float(prior_sigma2)
        self._buf: Deque[float] = deque(maxlen=self.window)

    def reset(self, prior_sigma2: Optional[float] = None) -> None:
        self._buf.clear()
        if prior_sigma2 is not None:
            self.prior_sigma2 = float(prior_sigma2)

    def __len__(self) -> int:
        return len(self._buf)

    @property
    def usa_prior(self) -> bool:
        return len(self._buf) < self.min_points

    @property
    def sigma2(self) -> float:
        """Varianza con los puntos incorporados hasta ahora (el prior si hay
        menos de `min_points`)."""
        if self.usa_prior:
            return self.prior_sigma2
        return float(np.var(np.fromiter(self._buf, dtype=float), ddof=1))

    def update(self, p_mid: float) -> None:
        self._buf.append(float(p_mid))

    def step(self, p_mid: float) -> float:
        s2 = self.sigma2
        self.update(p_mid)
        return s2


def reward_components(p_mid: float, p_ejec: float, q_ejec: float, sigma2: float,
                      beta: float = BETA_RIESGO_EJECUTOR,
                      escala: str = ESCALA_RECOMPENSA_EJECUTOR,
                      q_slice: Optional[float] = None) -> Dict[str, float]:
    """Componentes de R_E ya escaladas: `precio` = (P_mid - P_ejec) q_ejec,
    `riesgo` = beta sigma2 q_ejec y `total` = precio - riesgo."""
    if escala not in ESCALAS_RECOMPENSA:
        raise ValueError(f"escala invalida: {escala!r}. Validas: {list(ESCALAS_RECOMPENSA)}")
    precio = (float(p_mid) - float(p_ejec)) * float(q_ejec)
    riesgo = float(beta) * float(sigma2) * float(q_ejec)
    if escala == "por_accion_slice":
        if q_slice is None or q_slice <= 0:
            raise ValueError("escala 'por_accion_slice' requiere q_slice > 0")
        precio, riesgo = precio / float(q_slice), riesgo / float(q_slice)
    return {"precio": precio, "riesgo": riesgo, "total": precio - riesgo}


def executor_reward(p_mid: float, p_ejec: float, q_ejec: float, sigma2: float,
                    beta: float = BETA_RIESGO_EJECUTOR,
                    escala: str = ESCALA_RECOMPENSA_EJECUTOR,
                    q_slice: Optional[float] = None) -> float:
    """R_E = (P_mid - P_ejec) q_ejec - beta sigma2 q_ejec, en la escala pedida."""
    return reward_components(p_mid, p_ejec, q_ejec, sigma2, beta, escala, q_slice)["total"]


def beta_star(abs_price_diff_mean: float, sigma2_mean: float) -> float:
    """beta* = E|P_mid - P_ejec| / E[sigma2]: el beta con el que el termino de
    riesgo pesa en promedio lo mismo que el de precio. Unidades: 1 / CLP."""
    if not sigma2_mean > 0:
        return float("nan")
    return float(abs_price_diff_mean / sigma2_mean)
