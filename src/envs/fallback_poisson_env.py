"""EjecutorEnvPoissonFallback: reemplazo TEMPORAL de EjecutorEnv con dinamica
real (no dummy), usando el simulador de `poisson_lob_simulator.py`.

*** REEMPLAZO TEMPORAL — LEER poisson_lob_simulator.py Y REEMPLAZO_TEMPORAL_
POISSON.md ANTES DE USAR ESTE ARCHIVO EN EL PROYECTO FINAL ***

Por que existe: mientras Mauricio no confirme que ABIDES-Gym instala
(PENDIENTE_MAURICIO.md), el training del notebook corre con reward=0.0
siempre (EjecutorEnv es un stub intencional de Sprint 3). Esta clase
extiende EjecutorEnv preservando EXACTAMENTE su observation_space y
action_space (mismo contrato, mismo Gymnasium.Env), pero calcula S_E y
R_E de verdad a partir del LOB sintetico calibrado con datos reales del
IPSA. Cualquier codigo que ya use EjecutorEnv (incluido el notebook de
training) funciona igual sin cambios, solo instanciando esta clase en vez
de la original.

NO modifica `ejecutor_env.py` -- ese archivo queda intacto para cuando
Mauricio integre ABIDES-Gym de verdad.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import numpy as np

from src.config.market_params import (
    BETA_RIESGO_EJECUTOR,
    ESCALA_RECOMPENSA_EJECUTOR,
    VENTANA_SIGMA2_PASOS,
)
from src.envs.ejecutor_env import EjecutorEnv, VALID_EXECUTOR_IDS
from src.envs.poisson_lob_simulator import PoissonLOBSimulator
from src.envs.reward_utils import (
    RollingPriceVariance,
    prior_sigma2,
    reward_components,
    sigma_5min_tramo,
)

# Mapeo executor_id (Sprint 3, spaces.py) -> tramo (calibracion de Benjamin).
# Son exactamente los mismos 3 tramos, solo con nombres definidos en modulos
# distintos -- se listan explicitamente ambos para que la correspondencia
# quede documentada en un solo lugar.
_EXECUTOR_TO_TRAMO = {
    "apertura": "apertura",
    "media_jornada": "media_jornada",
    "cierre": "cierre",
}

# Activo representativo (Titulo I, seccion 5): FALABELLA.SN se usa en todos
# los graficos/analisis exploratorios del proyecto. Configurable.
DEFAULT_TICKER = "FALABELLA"

# beta (aversion al riesgo en R_E), la ventana de sigma2 y la escala de la
# recompensa viven en src/config/market_params.py (tarea 2.2.3): son comunes a
# este entorno y a EjecutorEnvAbides. beta sigue en 0.0 hasta cerrar su
# calibracion (ver docs/recompensa_ejecutores_2.2.3_BF.md).


class EjecutorEnvPoissonFallback(EjecutorEnv):
    """Igual a `EjecutorEnv` (mismo observation_space/action_space), pero con
    dinamica real via `PoissonLOBSimulator` en vez de observaciones aleatorias.

    Args adicionales respecto a EjecutorEnv:
        ticker: activo a simular (default FALABELLA, ver Titulo I).
        q_slice: cantidad de acciones asignadas a este Ejecutor para el
            episodio (viene del Maestro en el protocolo real; aqui se pasa
            directo porque este env corre standalone).
        p_referencia: precio de referencia (arrival price) al inicio del
            episodio. Si None, usa un valor de ejemplo razonable (5800,
            el mismo del ejemplo de Contexto_Agente_Programacion.md) --
            para un episodio real, pasar el P_mid observado en ese momento.
        beta: aversion al riesgo de R_E (1/CLP). Default
            `BETA_RIESGO_EJECUTOR`.
        reward_escala: "por_accion_slice" (R_E / q_slice) o "bruta" (CLP).
            Default `ESCALA_RECOMPENSA_EJECUTOR`.
        ventana_sigma2: pasos de la ventana movil causal de sigma2_precio.
    """

    def __init__(self, executor_id="apertura", max_steps: Optional[int] = None,
                 ventana_min: Optional[int] = None,
                 ticker: str = DEFAULT_TICKER, q_slice: float = 1000.0,
                 p_referencia: Optional[float] = None, seed: Optional[int] = None,
                 beta: float = BETA_RIESGO_EJECUTOR,
                 reward_escala: str = ESCALA_RECOMPENSA_EJECUTOR,
                 ventana_sigma2: int = VENTANA_SIGMA2_PASOS,
                 **_ignored_kwargs):
        # Mismo contrato que EjecutorEnvAbides (abides_ejecutor_env.py): acepta
        # `ventana_min` (minutos de la ventana asignada por el Maestro) y lo
        # convierte a pasos de 30 seg (max_steps = ventana_min * 2). Si se pasa
        # `max_steps` directo (uso standalone, sin Maestro) tiene prioridad.
        # `**_ignored_kwargs` absorbe kwargs propios de EjecutorEnvAbides
        # (background_config, timestep_duration, etc.) para que
        # `MaestroEjecutorEnv` pueda pasar `executor_env_kwargs` compartidos
        # sin que este fallback truene por un kwarg que no usa.
        if max_steps is None:
            max_steps = max(1, int(ventana_min) * 2) if ventana_min is not None else 60
        super().__init__(executor_id=executor_id, max_steps=max_steps)
        tramo = _EXECUTOR_TO_TRAMO[self.executor_id]
        self._sim = PoissonLOBSimulator(ticker=ticker, tramo=tramo, seed=seed)
        self.ticker = ticker
        self.q_slice = float(q_slice)
        self._p_referencia_arg = p_referencia
        self.q_pendiente = self.q_slice
        self.p_referencia = 0.0
        self.beta = float(beta)
        self.reward_escala = reward_escala
        self._sigma_5min = sigma_5min_tramo(ticker, tramo, self._sim.calib["calibration_path"])
        self._var = RollingPriceVariance(window=ventana_sigma2)

    def reset(self, *, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None
              ) -> Tuple[np.ndarray, Dict[str, Any]]:
        # Nota: no llamamos a super().reset() de EjecutorEnv (que devuelve una
        # observacion aleatoria) -- reimplementamos reset() completo para usar
        # el LOB real, conservando la misma firma/contrato de Gymnasium.
        self._step_count = 0
        self.p_referencia = float(self._p_referencia_arg or 5800.0)
        self.q_pendiente = self.q_slice
        self._sim.reset(p_referencia=self.p_referencia)
        # sigma2: prior del tramo hasta juntar SIGMA2_MIN_PUNTOS mids; el precio
        # de referencia es el primer punto de la ventana.
        self._var.reset(prior_sigma2=prior_sigma2(self._sigma_5min, self.p_referencia))
        self._var.update(self.p_referencia)

        obs = self._compute_obs()
        info: Dict[str, Any] = {
            "step": self._step_count, "executor_id": self.executor_id,
            "ticker": self.ticker, "p_referencia": self.p_referencia,
        }
        return obs, info

    def step(self, action) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        action_arr = np.asarray(action, dtype=np.int64)
        if not self.action_space.contains(action_arr):
            raise ValueError(f"Accion invalida para EjecutorEnvPoissonFallback: {action}")
        parsed = self._action_space_wrapper.parse_action(action_arr)

        self._sim.advance()  # dinamica de mercado (llegada de ordenes Poisson) del paso
        p_mid_before = self._sim.mid_price

        q_ejec, p_ejec = self._execute(parsed)
        self.q_pendiente = max(self.q_pendiente - q_ejec, 0.0)

        # R_E = (P_mid_t - P_ejec_t) * q_ejec - beta * sigma^2_precio * q_ejec
        # (Contexto_Agente_Programacion.md, seccion 5.3). sigma2 es causal: usa
        # los P_mid hasta t-1 y recien despues incorpora el de este paso.
        sigma2 = self._var.step(p_mid_before)
        comp = reward_components(p_mid_before, p_ejec, q_ejec, sigma2, self.beta,
                                 self.reward_escala, q_slice=self.q_slice)
        reward = comp["total"]

        self._step_count += 1
        done = (self._step_count >= self.max_steps) or (self.q_pendiente <= 0)
        truncated = False

        obs = self._compute_obs()
        info: Dict[str, Any] = {
            "step": self._step_count, "executor_id": self.executor_id,
            "action_parsed": parsed, "q_ejecutado_step": q_ejec,
            "p_ejecutado_step": p_ejec, "q_pendiente": self.q_pendiente,
            "p_mid": self._sim.mid_price,
            "sigma2": sigma2, "reward_precio": comp["precio"],
            "reward_riesgo": comp["riesgo"], "reward_escala": self.reward_escala,
            "p_mid_decision": p_mid_before,
        }
        return obs, reward, done, truncated, info

    # ------------------------------------------------------------------
    def _execute(self, parsed: Dict[str, Any]) -> Tuple[float, float]:
        """Ejecuta la accion parseada contra el LOB. Devuelve (q_ejecutado, p_ejecutado).

        NOTA sobre ORDER_TYPES: EjecutorActionSpace (Sprint 3) define
        {LIMIT_BUY, LIMIT_SELL, MARKET}, no {mercado, limite, esperar} como
        en el contrato narrativo original de SE_schema.json. Como el
        proyecto solo modela COMPRA (Contexto_Agente_Programacion.md, nota
        4), LIMIT_SELL no tiene sentido aqui y se trata como "esperar"
        (no ejecuta). Esto no es una decision mia sobre el contrato --
        es la interpretacion mas consistente del contrato ya existente.
        """
        quantity = parsed["volume_frac"] * self.q_pendiente
        if quantity <= 0:
            return 0.0, self._sim.mid_price

        if parsed["order_type"] == "MARKET":
            return self._sim.execute_market_buy(quantity)
        if parsed["order_type"] == "LIMIT_BUY":
            return self._sim.execute_limit_buy(quantity, parsed["price_level"])
        # LIMIT_SELL -> tratado como esperar (ver docstring)
        return 0.0, self._sim.mid_price

    def _compute_obs(self) -> np.ndarray:
        """Arma el vector S_E (27,) en el orden EXACTO de
        `EjecutorSpace.variable_names` (privado[3] + bid[10] + ask[10] + mercado[4]),
        normalizado a los rangos declarados en SE_schema.json."""
        sim = self._sim
        feats = sim.get_market_features()

        # Banda de normalizacion de precios: +/-5% del precio de referencia.
        # (heuristica explicita -- ver limitaciones en poisson_lob_simulator.py)
        band_low = self.p_referencia * 0.95
        band_width = self.p_referencia * 0.10

        def norm_price(p):
            return np.clip((p - band_low) / band_width, 0.0, 1.0)

        volume_cap = sim._avg_order_size * 20.0  # ver PoissonLOBSimulator._rebuild_book
        # Tope de normalizacion para q_slice: un slice "grande" respecto al tamano medio
        # de orden del ticker (heuristica explicita, no un limite fisico real).
        q_slice_cap = sim._avg_order_size * 200.0

        def norm_volume(v):
            return np.clip(v / volume_cap, 0.0, 1.0)

        privado = np.array([
            np.clip(self.q_slice / q_slice_cap, 0.0, 1.0),
            np.clip(self.q_pendiente / max(self.q_slice, 1e-6), 0.0, 1.0),
            np.clip(self._step_count / max(self.max_steps, 1), 0.0, 1.0),
        ], dtype=np.float32)

        bid_p = norm_price(sim.bid_prices)
        bid_v = norm_volume(sim.bid_volumes)
        ask_p = norm_price(sim.ask_prices)
        ask_v = norm_volume(sim.ask_volumes)

        mercado = np.array([
            np.clip(feats["spread_t"] / (self.p_referencia * 0.02), 0.0, 1.0),  # spread normalizado a 2% del precio
            np.clip(feats["OBI_t"], -1.0, 1.0),
            np.clip(feats["tasa_ordenes"], 0.0, 1.0),
            norm_price(feats["P_mid"]),
        ], dtype=np.float32)

        obs = np.concatenate([privado, bid_p, bid_v, ask_p, ask_v, mercado]).astype(np.float32)
        return obs
