"""EjecutorEnv: stub de entorno Gymnasium para un Agente Ejecutor.

Tarea 2.1.4 (Sprint 3). Analogo a MaestroEnv (ver ese modulo para el
contexto de por que es un stub sin ABIDES-Gym). Cada instancia representa
uno de los 3 Ejecutores (Apertura / Media jornada / Cierre), identificado
por `executor_id`.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import gymnasium as gym
import numpy as np

from src.envs.spaces import EjecutorActionSpace, EjecutorSpace

VALID_EXECUTOR_IDS = ("apertura", "media_jornada", "cierre")


class EjecutorEnv(gym.Env):
    """Entorno stub de un Agente Ejecutor (decide cada 30 seg, gamma=0.95).

    - observation_space: `EjecutorSpace().space` (Box, shape real segun
      docs/schemas/SE_schema.json; ver `EjecutorSpace.SCHEMA_DIM_WARNING`
      para la discrepancia 26 vs 27 detectada en el schema v1.0.0).
    - action_space: `EjecutorActionSpace().space`
      (MultiDiscrete([3, 10, 8]) = order_type x volume_bucket x price_level).
    - max_steps=60 (limite de este stub).
    - `executor_id`: uno de {"apertura", "media_jornada", "cierre"} o un
      indice entero 0/1/2 (se normaliza internamente).
    """

    metadata = {"render_modes": []}

    def __init__(self, executor_id="apertura", max_steps: int = 60):
        super().__init__()
        self.executor_id = self._normalize_executor_id(executor_id)

        self._ejecutor_space = EjecutorSpace()
        self._action_space_wrapper = EjecutorActionSpace()

        self.observation_space = self._ejecutor_space.space
        self.action_space = self._action_space_wrapper.space

        self.max_steps = max_steps
        self._step_count = 0

    @staticmethod
    def _normalize_executor_id(executor_id) -> str:
        if isinstance(executor_id, int):
            if not (0 <= executor_id < len(VALID_EXECUTOR_IDS)):
                raise ValueError(
                    f"executor_id entero fuera de rango: {executor_id} "
                    f"(valido: 0,1,2 -> {VALID_EXECUTOR_IDS})"
                )
            return VALID_EXECUTOR_IDS[executor_id]
        if executor_id not in VALID_EXECUTOR_IDS:
            raise ValueError(
                f"executor_id invalido: {executor_id!r}. Valores validos: {VALID_EXECUTOR_IDS}"
            )
        return executor_id

    def reset(
        self, *, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        super().reset(seed=seed)
        self._step_count = 0
        obs = self.observation_space.sample()
        info: Dict[str, Any] = {"step": self._step_count, "executor_id": self.executor_id}
        return obs, info

    def step(self, action) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        action_arr = np.asarray(action, dtype=np.int64)
        if not self.action_space.contains(action_arr):
            raise ValueError(f"Accion invalida para EjecutorEnv: {action}")

        action_parsed = self._action_space_wrapper.parse_action(action_arr)

        self._step_count += 1
        obs = self.observation_space.sample()
        reward = 0.0  # stub: R_E real = (P_mid_t - P_ejec_t)*q_ejec - beta*sigma^2*q_ejec
        done = self._step_count >= self.max_steps
        truncated = False
        info: Dict[str, Any] = {
            "step": self._step_count,
            "executor_id": self.executor_id,
            "action_parsed": action_parsed,
        }
        return obs, reward, done, truncated, info

    def render(self):  # pragma: no cover - no-op
        pass

    def close(self):  # pragma: no cover - no-op
        pass
