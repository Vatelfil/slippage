"""Fabrica de las redes del sistema jerarquico (tarea 2.1.2).

Elaborado por PS con apoyo de Claude Code; pendiente de revision por BF/MR.

Un Maestro (S_M de 7 dim -> 40 acciones) y tres Ejecutores independientes, uno
por tramo (S_E de 27 dim -> 240 acciones). Cada Ejecutor es una instancia
distinta, con pesos propios: no se comparten parametros entre tramos.

Desviacion documentada (ver docs/desviaciones_2.1.2.md): el Titulo I describe
una cabeza hibrida (discreta para el tipo de orden, continua para el volumen).
Se implementa totalmente discreta (3 x 10 x 8 = 240 logits aplanados) porque es
lo que ya usan el entorno (`EjecutorActionSpace`, MultiDiscrete[3,10,8]) y el
PPO de Mauricio, y evita mezclar dos familias de distribuciones en el gradiente.
"""
from __future__ import annotations

from typing import Dict

from src.config.market_params import TRAMOS_EJECUTOR
from src.models.actor_critic import ExecutorActorCritic, MasterActorCritic

DIM_SM = 7
DIM_SE = 27
N_ACCIONES_MAESTRO = 40
N_ACCIONES_EJECUTOR = 3 * 10 * 8


def make_master_network(obs_dim: int = DIM_SM) -> MasterActorCritic:
    return MasterActorCritic(obs_dim=obs_dim)


def make_executor_networks(obs_dim: int = DIM_SE, action_dim: int = N_ACCIONES_EJECUTOR) -> Dict[str, ExecutorActorCritic]:
    """Tres Ejecutores independientes, indexados por nombre de tramo."""
    return {nombre: ExecutorActorCritic(obs_dim, action_dim) for nombre, _, _ in TRAMOS_EJECUTOR}


def make_hierarchy():
    """(Maestro, {tramo: Ejecutor}) con las dimensiones oficiales."""
    return make_master_network(), make_executor_networks()
