"""MaestroEnv: stub de entorno Gymnasium para el Agente Maestro.

Tarea 2.1.4 (Sprint 3). Este entorno NO integra ABIDES-Gym (esa integracion
es responsabilidad de BF, tareas 1.2.3/1.2.4/2.2.4). Es un stub que formaliza
observation_space / action_space y el ciclo reset/step para que MR pueda
desarrollar y probar la red Actor-Critico del Maestro de forma aislada,
usando dinamica dummy (observaciones aleatorias validas, reward=0.0).

Reemplazar la logica interna de `step`/`reset` cuando ABIDES-Gym este
integrado (no cambiar la forma de los spaces sin avisar al equipo).
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import gymnasium as gym
import numpy as np

from src.envs.spaces import MaestroActionSpace, MaestroSpace


class MaestroEnv(gym.Env):
    """Entorno stub del Agente Maestro (decide cada 30 min, gamma=0.99).

    - observation_space: `MaestroSpace().space` (Box, shape (7,), ver
      docs/schemas/SM_schema.json).
    - action_space: `MaestroActionSpace().space` (Box, alpha_t en [0,1],
      shape (1,); version continua simplificada pedida en Tarea 2.1.4 -- el
      contrato de equipo MultiDiscrete([10,4]) sigue vigente y documentado en
      SM_schema.json, ver docstring de `spaces.MaestroActionSpace`).
    - max_steps=30 (limite arbitrario de este stub, no confundir con las 13
      decisiones/jornada reales de S_M; sirve para acotar episodios de
      prueba unitaria).
    """

    metadata = {"render_modes": []}

    def __init__(self, max_steps: int = 30):
        super().__init__()
        self._maestro_space = MaestroSpace()
        self._action_space_wrapper = MaestroActionSpace()

        self.observation_space = self._maestro_space.space
        self.action_space = self._action_space_wrapper.space

        self.max_steps = max_steps
        self._step_count = 0
        self._np_random = None  # seteado en reset()

    def reset(
        self, *, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        super().reset(seed=seed)
        self._step_count = 0
        obs = self.observation_space.sample()
        info: Dict[str, Any] = {"step": self._step_count}
        return obs, info

    def step(self, action) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        if not self.action_space.contains(np.asarray(action, dtype=np.float32)):
            raise ValueError(f"Accion invalida para MaestroEnv: {action}")

        self._step_count += 1
        obs = self.observation_space.sample()
        reward = 0.0  # stub: R_M real = -IS_total - lambda*max(0,Q_pend)*P_mid_cierre
        done = self._step_count >= self.max_steps
        truncated = False
        info: Dict[str, Any] = {
            "step": self._step_count,
            "alpha_t": float(np.asarray(action).reshape(-1)[0]),
        }
        return obs, reward, done, truncated, info

    def render(self):  # pragma: no cover - no-op
        pass

    def close(self):  # pragma: no cover - no-op
        pass
