"""Ciclo de Entrenamiento PPO Unificado (Tarea 2.3.2 - Sprint 5).

Elaborado por Mauricio Reynoso (MR).

Provee la clase `PPOTrainer` parametrizada por rol ("ejecutor" o "maestro"):
  1. Recoleccion de trayectorias con `RolloutBuffer` y calculo de GAE desacoplado.
  2. Normalizacion de ventajas y armado de minilotes aleatorios.
  3. Bucle de optimizacion PPO con recorte L_CLIP, MSE de valor y bonificacion de entropia.
  4. Parada temprana por divergencia KL aproximada (evita colapso catastrofico de politica).
  5. Gestion de checkpoints (ultimo modelo, mejor modelo y reanudacion de estado).
  6. Registro continuo en CSV con las 8 columnas requeridas:
     episodio, loss_actor, loss_critic, entropia, reward_mean, reward_std, kl, clip_fraction.
"""
from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, Sequence, Tuple, Union

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

from src.models.actor_critic import BaseActorCritic, ExecutorActorCritic, MasterActorCritic
from src.envs.spaces import EjecutorActionSpace


@dataclass
class PPOConfig:
    """Configuracion de hiperparametros para el entrenamiento PPO."""
    lr: float = 3e-4
    gamma: float = 0.95              # 0.95 en Ejecutor, 0.99 en Maestro
    gae_lambda: float = 0.95
    clip_ratio: float = 0.2
    entropy_coef: float = 0.01
    value_coef: float = 0.5
    max_grad_norm: float = 0.5
    epochs: int = 4
    minibatch_size: int = 64
    episodes_per_update: int = 10
    target_kl: float = 0.015         # Objetivo de divergencia KL
    kl_threshold_multiplier: float = 1.5  # Si KL > target_kl * mult, se corta la actualizacion


class RolloutBuffer:
    """Buffer de experiencias para PPO con calculo correcto de GAE entre episodios."""

    def __init__(self, capacity: int = 4096):
        self.capacity = capacity
        self.obs: List[np.ndarray] = []
        self.actions: List[int] = []
        self.log_probs: List[float] = []
        self.rewards: List[float] = []
        self.values: List[float] = []
        self.dones: List[bool] = []
        self.returns: List[float] = []
        self.advantages: List[float] = []

    def clear(self) -> None:
        self.obs.clear()
        self.actions.clear()
        self.log_probs.clear()
        self.rewards.clear()
        self.values.clear()
        self.dones.clear()
        self.returns.clear()
        self.advantages.clear()

    def add(self, obs: np.ndarray, action: int, log_prob: float, reward: float, value: float, done: bool) -> None:
        self.obs.append(np.array(obs, dtype=np.float32, copy=True))
        self.actions.append(int(action))
        self.log_probs.append(float(log_prob))
        self.rewards.append(float(reward))
        self.values.append(float(value))
        self.dones.append(bool(done))

    def __len__(self) -> int:
        return len(self.obs)

    def compute_returns_advantages(self, gamma: float, gae_lambda: float) -> None:
        """Calcula retornos y ventajas GAE respetando la frontera de episodios via `dones`."""
        n = len(self.rewards)
        if n == 0:
            self.returns = []
            self.advantages = []
            return

        self.returns = [0.0] * n
        self.advantages = [0.0] * n

        gae = 0.0
        for t in reversed(range(n)):
            if t == n - 1:
                next_non_terminal = 1.0 - float(self.dones[t])
                next_value = 0.0
            else:
                next_non_terminal = 1.0 - float(self.dones[t])
                next_value = self.values[t + 1]

            delta = self.rewards[t] + gamma * next_value * next_non_terminal - self.values[t]
            gae = delta + gamma * gae_lambda * next_non_terminal * gae
            self.advantages[t] = gae
            self.returns[t] = gae + self.values[t]

    def get_batches(self, batch_size: int, device: torch.device) -> Generator[Dict[str, torch.Tensor], None, None]:
        n = len(self.obs)
        if n == 0:
            return
        indices = np.random.permutation(n)
        for start in range(0, n, batch_size):
            end = min(start + batch_size, n)
            batch_idx = indices[start:end]
            yield {
                "obs": torch.as_tensor(np.array([self.obs[i] for i in batch_idx]), dtype=torch.float32, device=device),
                "actions": torch.as_tensor([self.actions[i] for i in batch_idx], dtype=torch.int64, device=device),
                "log_probs": torch.as_tensor([self.log_probs[i] for i in batch_idx], dtype=torch.float32, device=device),
                "returns": torch.as_tensor([self.returns[i] for i in batch_idx], dtype=torch.float32, device=device),
                "advantages": torch.as_tensor([self.advantages[i] for i in batch_idx], dtype=torch.float32, device=device),
            }


class PPOTrainer:
    """Entrenador PPO unificado para roles de Ejecutor y Maestro."""

    CSV_HEADER = [
        "episodio",
        "loss_actor",
        "loss_critic",
        "entropia",
        "reward_mean",
        "reward_std",
        "kl",
        "clip_fraction",
    ]

    def __init__(
        self,
        role: str = "ejecutor",
        model: Optional[BaseActorCritic] = None,
        cfg: Optional[Union[PPOConfig, Dict[str, Any]]] = None,
        device: Optional[Union[str, torch.device]] = None,
        seed: int = 42,
    ):
        if role not in ("ejecutor", "maestro"):
            raise ValueError(f"Rol invalido: '{role}'. Debe ser 'ejecutor' o 'maestro'.")
        self.role = role
        self.seed = seed
        self._set_seed(seed)

        if isinstance(cfg, PPOConfig):
            self.cfg = cfg
        elif isinstance(cfg, dict):
            self.cfg = PPOConfig(**cfg)
        else:
            default_gamma = 0.99 if role == "maestro" else 0.95
            self.cfg = PPOConfig(gamma=default_gamma)

        self.device = torch.device(device) if device else torch.device("cuda" if torch.cuda.is_available() else "cpu")

        if model is not None:
            self.model = model.to(self.device)
        else:
            if role == "ejecutor":
                self.model = ExecutorActorCritic(obs_dim=27, action_dim=240).to(self.device)
            else:
                self.model = MasterActorCritic(obs_dim=7).to(self.device)

        self.optimizer = optim.Adam(self.model.parameters(), lr=self.cfg.lr)
        self.buffer = RolloutBuffer()
        self.current_episode = 0
        self.best_eval_return = -float("inf")

    def _set_seed(self, seed: int) -> None:
        torch.manual_seed(seed)
        np.random.seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

    def ppo_update(self) -> Dict[str, float]:
        """Ejecuta la actualizacion PPO con parada temprana por divergencia KL."""
        if len(self.buffer) == 0:
            return {}

        self.buffer.compute_returns_advantages(self.cfg.gamma, self.cfg.gae_lambda)

        kl_limit = self.cfg.target_kl * self.cfg.kl_threshold_multiplier
        policy_losses = []
        value_losses = []
        entropies = []
        kl_divs = []
        clip_fractions = []
        early_stopped = False

        for epoch in range(self.cfg.epochs):
            if early_stopped:
                break
            for batch in self.buffer.get_batches(self.cfg.minibatch_size, self.device):
                obs = batch["obs"]
                actions = batch["actions"]
                old_log_probs = batch["log_probs"]
                returns = batch["returns"]
                advantages = batch["advantages"]

                # Normalizacion de ventajas
                if advantages.numel() > 1 and advantages.std() > 1e-8:
                    advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

                _, new_log_probs, entropy, values = self.model.get_action_and_value(obs, actions)
                values = values.squeeze(-1)

                log_ratio = new_log_probs - old_log_probs
                ratio = torch.exp(log_ratio)

                # KL aproximado (Kullback-Leibler) segun Schulman: mean((ratio - 1) - log(ratio))
                approx_kl = torch.mean((ratio - 1.0) - log_ratio).item()
                kl_divs.append(approx_kl)

                # Fraccion de recorte
                clipped = (ratio < 1.0 - self.cfg.clip_ratio) | (ratio > 1.0 + self.cfg.clip_ratio)
                clip_fractions.append(clipped.float().mean().item())

                # Perdida de politica L_CLIP
                surr1 = ratio * advantages
                surr2 = torch.clamp(ratio, 1.0 - self.cfg.clip_ratio, 1.0 + self.cfg.clip_ratio) * advantages
                policy_loss = -torch.min(surr1, surr2).mean()

                # Perdida de valor MSE
                value_loss = F.mse_loss(values, returns)
                entropy_bonus = entropy.mean()

                total_loss = policy_loss + self.cfg.value_coef * value_loss - self.cfg.entropy_coef * entropy_bonus

                self.optimizer.zero_grad()
                total_loss.backward()
                nn.utils.clip_grad_norm_(self.model.parameters(), self.cfg.max_grad_norm)
                self.optimizer.step()

                policy_losses.append(policy_loss.item())
                value_losses.append(value_loss.item())
                entropies.append(entropy_bonus.item())

                # Parada temprana si KL supera el limite fijado
                if approx_kl > kl_limit:
                    early_stopped = True
                    break

        return {
            "loss_actor": float(np.mean(policy_losses)) if policy_losses else 0.0,
            "loss_critic": float(np.mean(value_losses)) if value_losses else 0.0,
            "entropia": float(np.mean(entropies)) if entropies else 0.0,
            "kl": float(np.mean(kl_divs)) if kl_divs else 0.0,
            "clip_fraction": float(np.mean(clip_fractions)) if clip_fractions else 0.0,
            "early_stopped": early_stopped,
        }

    def log_to_csv(self, csv_path: Union[str, Path], metrics: Dict[str, Any]) -> None:
        """Registra las 8 columnas requeridas en el archivo CSV."""
        p = Path(csv_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        write_header = not p.exists() or p.stat().st_size == 0

        row = {
            "episodio": int(metrics.get("episodio", self.current_episode)),
            "loss_actor": round(float(metrics.get("loss_actor", 0.0)), 6),
            "loss_critic": round(float(metrics.get("loss_critic", 0.0)), 6),
            "entropia": round(float(metrics.get("entropia", 0.0)), 6),
            "reward_mean": round(float(metrics.get("reward_mean", 0.0)), 6),
            "reward_std": round(float(metrics.get("reward_std", 0.0)), 6),
            "kl": round(float(metrics.get("kl", 0.0)), 6),
            "clip_fraction": round(float(metrics.get("clip_fraction", 0.0)), 6),
        }

        with open(p, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.CSV_HEADER)
            if write_header:
                writer.writeheader()
            writer.writerow(row)

    def save_checkpoint(self, path: Union[str, Path], is_best: bool = False, extra_info: Optional[Dict] = None) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "role": self.role,
            "current_episode": self.current_episode,
            "best_eval_return": self.best_eval_return,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "cfg": self.cfg.__dict__,
            "seed": self.seed,
            "extra_info": extra_info or {},
        }
        torch.save(payload, p)
        if is_best:
            best_path = p.parent / "checkpoint_best.pt"
            torch.save(payload, best_path)

    def load_checkpoint(self, path: Union[str, Path]) -> Dict[str, Any]:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Checkpoint no encontrado: {p}")
        checkpoint = torch.load(p, map_location=self.device)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.current_episode = int(checkpoint.get("current_episode", 0))
        self.best_eval_return = float(checkpoint.get("best_eval_return", -float("inf")))
        return checkpoint

    def train_executor_episodes(
        self,
        env_factory: Callable,
        n_episodes: int,
        tramo: str = "apertura",
        q_slice: int = 1000,
        ventana_min: int = 5,
        csv_path: Optional[Union[str, Path]] = None,
        checkpoint_dir: Optional[Union[str, Path]] = None,
        checkpoint_freq: int = 10,
        log_fn: Callable[[str], None] = print,
    ) -> List[Dict[str, Any]]:
        """Bucle de entrenamiento del Ejecutor para N episodios continuos."""
        space = EjecutorActionSpace()
        ep_rewards = []
        recent_rewards = []
        history = []

        start_ep = self.current_episode + 1
        end_ep = self.current_episode + n_episodes

        for ep in range(start_ep, end_ep + 1):
            self.current_episode = ep
            env = env_factory(executor_id=tramo, q_slice=q_slice, ventana_min=ventana_min, seed=self.seed + ep)
            obs, _ = env.reset()
            done, ret = False, 0.0

            while not done:
                obs_t = torch.as_tensor(obs, dtype=torch.float32, device=self.device).unsqueeze(0)
                with torch.no_grad():
                    a, lp, _, v = self.model.get_action_and_value(obs_t)
                a_idx = int(a.item())
                obs_next, r, done, trunc, _ = env.step(space.decode_flat(a_idx))
                done = bool(done or trunc)

                self.buffer.add(obs, a_idx, float(lp.item()), float(r), float(v.item()), done)
                ret += float(r)
                obs = obs_next

            env.close()
            ep_rewards.append(ret)
            recent_rewards.append(ret)

            # Actualizacion PPO
            if len(ep_rewards) % self.cfg.episodes_per_update == 0 or ep == end_ep:
                update_metrics = self.ppo_update()
                self.buffer.clear()

                r_mean = float(np.mean(recent_rewards))
                r_std = float(np.std(recent_rewards)) if len(recent_rewards) > 1 else 0.0
                recent_rewards.clear()

                update_metrics["episodio"] = ep
                update_metrics["reward_mean"] = r_mean
                update_metrics["reward_std"] = r_std

                if csv_path:
                    self.log_to_csv(csv_path, update_metrics)

                log_fn(
                    f"Episodio {ep}/{end_ep} [{self.role}] - Retorno medio: {r_mean:.2f} | "
                    f"Loss actor: {update_metrics.get('loss_actor', 0.0):.4f} | "
                    f"Loss critico: {update_metrics.get('loss_critic', 0.0):.4f} | "
                    f"KL: {update_metrics.get('kl', 0.0):.5f}"
                )
                history.append(update_metrics)

            if checkpoint_dir and (ep % checkpoint_freq == 0 or ep == end_ep):
                cp_path = Path(checkpoint_dir) / "checkpoint_last.pt"
                is_best = ret > self.best_eval_return
                if is_best:
                    self.best_eval_return = ret
                self.save_checkpoint(cp_path, is_best=is_best)

        return history
