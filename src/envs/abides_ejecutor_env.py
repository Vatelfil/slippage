"""Conexion REAL de ABIDES-Gym con nuestro EjecutorEnv (Opcion B: extender ABIDES).

*** SIN PROBAR CONTRA ABIDES *** Escrito a partir del codigo fuente publico de
`SubGymMarketsExecutionEnv_v0` (no se pudo instalar ABIDES donde se escribio).
La logica pura (observacion 27 dims, mapeo de acciones, recompensa) SI esta
probada con datos falsos en tests/test_abides_bridge.py; lo que falta verificar
es el pegamento con ABIDES (ver INTEGRACION_ABIDES_PARA_MAURICIO.md, seccion
"Que hay que verificar").

Dos capas:
  - ExecutionEnv27: subclase del entorno de ejecucion de ABIDES (API vieja de
    gym 0.18) que reemplaza accion, observacion y recompensa por las nuestras.
  - EjecutorEnvAbides: adaptador a la API de gymnasium con EXACTAMENTE el mismo
    observation_space (27,) y action_space MultiDiscrete([3,10,8]) que
    EjecutorEnv, asi el training loop y las redes no cambian.

Requiere ABIDES-Gym instalado (Python 3.9, ver Dockerfile).
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Tuple

import gymnasium
import numpy as np

from src.config.market_params import (
    BETA_RIESGO_EJECUTOR,
    ESCALA_RECOMPENSA_EJECUTOR,
    VENTANA_SIGMA2_PASOS,
)
from src.envs import abides_bridge as br
from src.envs.ejecutor_env import EjecutorEnv

try:  # ABIDES solo existe en el entorno con Python 3.9 / Docker
    import gym
    import abides_markets.agents.utils as markets_agent_utils
    from abides_gym.envs.markets_execution_environment_v0 import SubGymMarketsExecutionEnv_v0
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "abides_ejecutor_env necesita ABIDES-Gym instalado (ver Dockerfile / "
        "docs/conexion_colab.md). Sin ABIDES usar EjecutorEnv (stub) o "
        "EjecutorEnvPoissonFallback."
    ) from e

# Offset de inicio de cada tramo respecto de la apertura (09:30) -> `first_interval`.
# ADVERTENCIA de costo: ABIDES simula todo el mercado desde la apertura hasta que
# el agente parte, asi que 'cierre' (4h30 de simulacion previa) sera bastante
# mas lento por episodio que 'apertura'.
TRAMO_FIRST_INTERVAL = {"apertura": "00:00:30", "media_jornada": "02:00:00", "cierre": "04:30:00"}


class ExecutionEnv27(SubGymMarketsExecutionEnv_v0):
    """Entorno de ejecucion de ABIDES con nuestro S_E (27), A_E (240) y R_E.

    CORREGIDO 29 sept 2026 (PS), tras probar contra ABIDES real: a los metodos
    `raw_state_to_*` les faltaban los decoradores `raw_state_pre_process` /
    `raw_state_to_state_pre_process` que trae la clase original. Sin ellos,
    `raw_state` llega en su forma mas cruda (una secuencia, no el dict
    {'parsed_mkt_data':..., 'internal_data':...} que el resto del codigo
    asume) -- de ahi el error real observado: "sequence index must be
    integer, not 'str'". Se reasignan aqui explicitamente porque son
    decoradores resueltos por NOMBRE en el cuerpo de la clase: heredarlos de
    SubGymMarketsExecutionEnv_v0 no los deja utilizables como `@nombre` en el
    cuerpo de ESTA subclase, solo via `self.` o `NombreClase.atributo`.
    """

    raw_state_pre_process = markets_agent_utils.ignore_buffers_decorator
    raw_state_to_state_pre_process = markets_agent_utils.ignore_mkt_data_buffer_decorator

    def __init__(self, *args, bridge_cfg: Optional[br.BridgeConfig] = None,
                 beta: float = BETA_RIESGO_EJECUTOR,
                 reward_escala: str = ESCALA_RECOMPENSA_EJECUTOR,
                 sigma_5min: Optional[float] = None,
                 ventana_sigma2: int = VENTANA_SIGMA2_PASOS, **kwargs):
        self._cfg = bridge_cfg or br.BridgeConfig()
        self._beta = beta
        # R_E (2.2.3): varianza movil causal del P_mid, escala comun con el
        # fallback y precios en CLP. `sigma_5min` fija el prior de sigma2.
        self._reward = br.ExecutorRewardState(
            beta=beta, escala=reward_escala, unidades_por_clp=self._cfg.unidades_por_clp,
            sigma_5min=sigma_5min, window=ventana_sigma2)
        self._entry_price: Optional[float] = None
        self._best_bid = 0.0
        self._best_ask = 0.0
        super().__init__(*args, **kwargs)
        self._remaining = float(self.parent_order_size)
        self.action_space = gym.spaces.MultiDiscrete([3, 10, 8])
        # CORREGIDO 29 sept: shape debe ser (OBS_DIM, 1), no (OBS_DIM,) -- asi es
        # como ABIDES reshapea el estado internamente (ver raw_state_to_state,
        # `.reshape(num_state_features, 1)`, mismo patron que el original). Con
        # shape (OBS_DIM,) el assert interno `observation_space.contains(state)`
        # de core_environment.py fallaba SIEMPRE por desajuste de forma, no por
        # valores fuera de rango (el traceback "INVALID STATE" con valores todos
        # dentro de [0,1]/[-1,1] fue la pista).
        self.observation_space = gym.spaces.Box(
            low=np.array([0] * 24 + [-1] + [0] * 2, dtype=np.float32).reshape(br.OBS_DIM, 1),
            high=np.ones((br.OBS_DIM, 1), dtype=np.float32),
            dtype=np.float32,
        )

    def reset(self):
        self._entry_price = None
        self._remaining = float(self.parent_order_size)
        state = super().reset()  # fija self._entry_price en raw_state_to_state
        self._reward.reset(self._entry_price)
        return state

    # --- accion: nuestras 240 -> ordenes ABIDES ---
    def _map_action_space_to_ABIDES_SIMULATOR_SPACE(self, action):
        return br.map_action_to_abides_orders(
            action, remaining=self._remaining, best_bid=self._best_bid,
            best_ask=self._best_ask, direction=self.direction, cfg=self._cfg)

    # --- observacion: S_E de 27 dims ---
    @raw_state_to_state_pre_process
    def raw_state_to_state(self, raw_state: Dict[str, Any]) -> np.ndarray:
        mkt, internal = raw_state["parsed_mkt_data"], raw_state["internal_data"]
        bids, asks = br.last_snapshot(mkt["bids"]), br.last_snapshot(mkt["asks"])
        last_tx = br.last_scalar(mkt["last_transaction"])
        holdings = br.last_scalar(internal["holdings"])
        now = br.last_scalar(internal["current_time"])
        mkt_open = br.last_scalar(internal["mkt_open"])

        mid = br.mid_price(bids, asks, last_tx)
        if self._entry_price is None:
            self._entry_price = mid
        self._best_bid = bids[0][0] if len(bids) else mid
        self._best_ask = asks[0][0] if len(asks) else mid
        self._remaining = max(float(self.parent_order_size) - float(holdings), 0.0)

        time_pct = (now - mkt_open - self.first_interval) / self.execution_window
        obs = br.build_observation(bids, asks, last_tx, self._entry_price,
                                   self.parent_order_size, self._remaining,
                                   time_pct, self._cfg)
        return obs.reshape(br.OBS_DIM, 1)

    # --- recompensa R_E ---
    @raw_state_pre_process
    def raw_state_to_reward(self, raw_state: Dict[str, Any]) -> float:
        mkt = raw_state["parsed_mkt_data"]
        bids, asks = br.last_snapshot(mkt["bids"]), br.last_snapshot(mkt["asks"])
        mid = br.mid_price(bids, asks, br.last_scalar(mkt["last_transaction"]))
        orders = br.last_orders(raw_state["internal_data"]["inter_wakeup_executed_orders"])
        return self._reward.step(orders, mid, self.parent_order_size)

    @raw_state_pre_process
    def raw_state_to_update_reward(self, raw_state: Dict[str, Any]) -> float:
        # ABIDES penaliza aqui la orden incompleta al final. En nuestro contrato esa
        # penalizacion (lambda * Q_pendiente) pertenece a R_M del Maestro, no a R_E.
        return 0.0

    @raw_state_pre_process
    def raw_state_to_info(self, raw_state: Dict[str, Any]) -> Dict[str, Any]:
        internal = raw_state["internal_data"]
        info = {"holdings": br.last_scalar(internal["holdings"]),
                "remaining": self._remaining, "entry_price": self._entry_price,
                "best_bid": self._best_bid, "best_ask": self._best_ask,
                "unidades_por_clp": self._cfg.unidades_por_clp}
        info.update(self._reward.last)  # sigma2 y componentes de R_E del paso (en CLP)
        return info


class EjecutorEnvAbides(EjecutorEnv):
    """Adaptador gymnasium. Hereda de EjecutorEnv para conservar observation_space,
    action_space y `_action_space_wrapper.decode_flat` (el notebook no cambia)."""

    def __init__(self, executor_id="apertura", q_slice: int = 1000, ventana_min: int = 10,
                 timestep_duration: str = "30s", background_config: str = "rmsc04",
                 seed: Optional[int] = None, **abides_kwargs):
        # `abides_kwargs` llega a ExecutionEnv27: ademas de los argumentos de
        # ABIDES (p. ej. `background_config_extra_kvargs` con la config
        # calibrada de la 2.2.4) acepta `bridge_cfg`, `beta`, `reward_escala`,
        # `sigma_5min` y `ventana_sigma2`.
        super().__init__(executor_id=executor_id, max_steps=max(1, ventana_min * 2))
        self._seed = seed
        self._inner = ExecutionEnv27(
            background_config=background_config,
            timestep_duration=timestep_duration,
            first_interval=TRAMO_FIRST_INTERVAL[self.executor_id],
            parent_order_size=int(q_slice),
            execution_window=f"00:{int(ventana_min):02d}:00",
            direction="BUY",
            mkt_close="16:00:00",
            **abides_kwargs,
        )

    def reset(self, *, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None
              ) -> Tuple[np.ndarray, Dict[str, Any]]:
        gymnasium.Env.reset(self, seed=seed)
        s = seed if seed is not None else self._seed
        if s is not None and hasattr(self._inner, "seed"):
            self._inner.seed(s)  # API vieja de gym; verificar que existe (ver doc)
        obs = np.asarray(self._inner.reset(), dtype=np.float32).reshape(br.OBS_DIM)
        self._step_count = 0
        # `entry_price` es lo que MaestroEjecutorEnv usa como P_referencia del
        # primer episodio; sin esta llave quedaba en None con ABIDES.
        return obs, {"executor_id": self.executor_id,
                     "entry_price": self._inner._entry_price,
                     "unidades_por_clp": self._inner._cfg.unidades_por_clp}

    def step(self, action) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        action_arr = np.asarray(action, dtype=np.int64)
        if not self.action_space.contains(action_arr):
            raise ValueError(f"Accion invalida para EjecutorEnvAbides: {action}")
        obs, reward, done, info = self._inner.step(action_arr)  # gym 0.18: 4 valores
        self._step_count += 1
        obs = np.asarray(obs, dtype=np.float32).reshape(br.OBS_DIM)
        return obs, float(reward), bool(done), False, info

    def close(self):
        if hasattr(self._inner, "close"):
            self._inner.close()


def make_calibrated_env_factory(calibrated_json, ticker: str = "FALABELLA", **common) -> Callable:
    """Fabrica de `EjecutorEnvAbides` con rmsc04 calibrado (2.2.4), para pasar
    como `executor_env_factory` a `MaestroEjecutorEnv`. Cada tramo usa su
    propia config (`fund_vol` es por tramo), la unidad de cuenta del JSON y el
    `sigma_5min` del tramo como prior de sigma2."""
    from src.envs.calibrate_rmsc04_ipsa import load_abides_kwargs, load_unidades_por_clp
    from src.envs.reward_utils import sigma_5min_tramo

    kwargs_por_tramo = load_abides_kwargs(calibrated_json)
    unidades = load_unidades_por_clp(calibrated_json)

    def factory(executor_id="apertura", **kw):
        args = {"background_config_extra_kvargs": dict(kwargs_por_tramo[executor_id]),
                "bridge_cfg": br.BridgeConfig(unidades_por_clp=unidades),
                "sigma_5min": sigma_5min_tramo(ticker, executor_id)}
        args.update(common)
        args.update(kw)
        return EjecutorEnvAbides(executor_id=executor_id, **args)

    return factory
