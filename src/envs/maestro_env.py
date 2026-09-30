"""MaestroEnv: stub de entorno Gymnasium para el Agente Maestro.

Tarea 2.1.4 (Sprint 3). Este entorno NO integra ABIDES-Gym (esa integracion
es responsabilidad de BF, tareas 1.2.3/1.2.4/2.2.4). Es un stub que formaliza
observation_space / action_space y el ciclo reset/step para que MR pueda
desarrollar y probar la red Actor-Critico del Maestro de forma aislada,
usando dinamica dummy (observaciones aleatorias validas, reward=0.0).

Reemplazar la logica interna de `step`/`reset` cuando ABIDES-Gym este
integrado (no cambiar la forma de los spaces sin avisar al equipo).

ACTUALIZADO 23 sept 2026 (PS): `action_space` paso de `MaestroActionSpace`
(Box continuo) a `MaestroDiscreteActionSpace` (Discrete(40)). Motivo: al
conectar `MasterActorCritic` (red real de Mauricio, que produce un unico
indice discreto 0-39) a este entorno, el Box continuo era incompatible --
`env.step(action)` no podia interpretar un entero como `alpha_t` continuo.
`Discrete(40)` es el contrato OFICIAL de A_M (SM_schema.json, MultiDiscrete
[10,4] aplanado) y es lo que la red real ya implementa, asi que se ajusto el
entorno en vez de pedirle a Mauricio que cambiace la arquitectura de red ya
construida. Ver `spaces.MaestroDiscreteActionSpace` para el decode/encode.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import gymnasium as gym
import numpy as np

from src.envs.spaces import MaestroDiscreteActionSpace, MaestroSpace


class MaestroEnv(gym.Env):
    """Entorno stub del Agente Maestro (decide cada 30 min, gamma=0.99).

    - observation_space: `MaestroSpace().space` (Box, shape (7,), ver
      docs/schemas/SM_schema.json).
    - action_space: `MaestroDiscreteActionSpace().space` (Discrete(40) --
      alpha_t discretizado en 10 valores x ventana_min en 4 valores,
      aplanado; ver `spaces.MaestroDiscreteActionSpace.decode()`). Este es
      el contrato OFICIAL de A_M (SM_schema.json), y coincide con lo que
      `MasterActorCritic` (src/models/actor_critic.py) ya produce.
    - max_steps=30 (limite arbitrario de este stub, no confundir con las 13
      decisiones/jornada reales de S_M; sirve para acotar episodios de
      prueba unitaria).
    """

    metadata = {"render_modes": []}

    def __init__(self, max_steps: int = 30):
        super().__init__()
        self._maestro_space = MaestroSpace()
        self._action_space_wrapper = MaestroDiscreteActionSpace()

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
        if not self._action_space_wrapper.contains(action):
            raise ValueError(f"Accion invalida para MaestroEnv: {action}")

        alpha_t, ventana_min = self._action_space_wrapper.decode(action)

        self._step_count += 1
        obs = self.observation_space.sample()
        reward = 0.0  # stub: R_M real = -IS_total - lambda*max(0,Q_pend)*P_mid_cierre
        done = self._step_count >= self.max_steps
        truncated = False
        info: Dict[str, Any] = {
            "step": self._step_count,
            "alpha_t": alpha_t,
            "ventana_min": ventana_min,
        }
        return obs, reward, done, truncated, info

    def render(self):  # pragma: no cover - no-op
        pass

    def close(self):  # pragma: no cover - no-op
        pass
