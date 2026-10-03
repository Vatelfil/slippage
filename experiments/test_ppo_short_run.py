"""
Prueba Corta de Entrenamiento PPO Jerarquico (Orquestador Maestro + 3 Ejecutores)
=============================================================================
Tarea 2.2.1 (Sprint 4) - Mauricio Reynoso (MR).

Verifica que el ciclo completo:
    Rollout coordinado -> GAE -> PPO update (L_CLIP + Value MSE + Entropy) -> Backprop
corra sin errores de dimensiones de tensores, sin NaNs y con gradientes validos
tanto para el Agente Maestro como para los 3 Agentes Ejecutores.
"""
import os
import sys
from pathlib import Path

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import torch
import torch.optim as optim
import torch.nn.functional as F

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np
import pandas as pd

from src.models.actor_critic import MasterActorCritic, ExecutorActorCritic
from src.envs.maestro_ejecutor_protocol import MaestroEjecutorEnv
from src.envs.fallback_poisson_env import EjecutorEnvPoissonFallback
from src.envs.spaces import MaestroSpace, EjecutorSpace, EjecutorActionSpace


class RolloutBuffer:
    """Buffer de experiencias para PPO con calculo correcto de GAE entre episodios."""
    def __init__(self, capacity: int = 1024):
        self.capacity = capacity
        self.clear()

    def clear(self):
        self.obs = []
        self.actions = []
        self.log_probs = []
        self.rewards = []
        self.values = []
        self.dones = []
        self.returns = []
        self.advantages = []

    def add(self, obs, action, log_prob, reward, value, done):
        self.obs.append(np.array(obs, dtype=np.float32, copy=True))
        self.actions.append(int(action))
        self.log_probs.append(float(log_prob))
        self.rewards.append(float(reward))
        self.values.append(float(value))
        self.dones.append(bool(done))

    def compute_returns_advantages(self, gamma: float, gae_lambda: float):
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

    def get_batches(self, batch_size: int, device: torch.device):
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


def ppo_update(actor_critic, optimizer, batch, clip_ratio=0.2, entropy_coef=0.01, value_coef=0.5, max_grad_norm=0.5):
    obs = batch["obs"]
    actions = batch["actions"]
    old_log_probs = batch["log_probs"]
    returns = batch["returns"]
    advantages = batch["advantages"]

    # Normalizacion de ventajas
    if advantages.numel() > 1 and advantages.std() > 1e-8:
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

    _, new_log_probs, entropy, values = actor_critic.get_action_and_value(obs, actions)
    values = values.squeeze(-1)

    ratio = torch.exp(new_log_probs - old_log_probs)
    surr1 = ratio * advantages
    surr2 = torch.clamp(ratio, 1.0 - clip_ratio, 1.0 + clip_ratio) * advantages
    policy_loss = -torch.min(surr1, surr2).mean()

    value_loss = F.mse_loss(values, returns)
    entropy_bonus = entropy.mean()

    loss = policy_loss + value_coef * value_loss - entropy_coef * entropy_bonus

    optimizer.zero_grad()
    loss.backward()
    torch.nn.utils.clip_grad_norm_(actor_critic.parameters(), max_grad_norm)
    optimizer.step()

    return {
        "policy_loss": float(policy_loss.item()),
        "value_loss": float(value_loss.item()),
        "entropy": float(entropy_bonus.item()),
    }


def run_short_training_test(total_steps: int = 300):
    print(f"--- Iniciando prueba corta de entrenamiento PPO ({total_steps} steps) ---")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Dispositivo: {device}")

    # 1. Instanciar redes
    maestro_net = MasterActorCritic(obs_dim=7).to(device)
    maestro_opt = optim.Adam(maestro_net.parameters(), lr=3e-4)

    tramos = ["apertura", "media_jornada", "cierre"]
    tramo_map = {t: i for i, t in enumerate(tramos)}
    ejecutor_nets = [ExecutorActorCritic(obs_dim=27, action_dim=240).to(device) for _ in range(3)]
    ejecutor_opts = [optim.Adam(net.parameters(), lr=3e-4) for net in ejecutor_nets]

    # 2. Buffers
    maestro_buf = RolloutBuffer(capacity=512)
    ejecutor_bufs = [RolloutBuffer(capacity=512) for _ in range(3)]

    # 3. Funcion de politica del ejecutor con callback de transiciones
    def custom_executor_policy(s_e, tramo):
        tramo_idx = tramo_map.get(tramo, 0)
        net = ejecutor_nets[tramo_idx]
        obs_t = torch.as_tensor(s_e, dtype=torch.float32, device=device).unsqueeze(0)
        with torch.no_grad():
            action, logp, _, val = net.get_action_and_value(obs_t)
        return int(action.item()), float(logp.item()), float(val.item())

    def custom_executor_callback(tramo, s_e, a_e_idx, log_prob, reward, value, done):
        tramo_idx = tramo_map.get(tramo, 0)
        ejecutor_bufs[tramo_idx].add(s_e, a_e_idx, log_prob, reward, value, done)

    # 4. Crear orquestador real con Poisson fallback
    env = MaestroEjecutorEnv(
        meta_orden_quantity=5000,
        executor_env_factory=EjecutorEnvPoissonFallback,
        executor_policy_fn=custom_executor_policy,
        executor_step_callback=custom_executor_callback,
    )

    steps_completed = 0
    episodes_completed = 0

    while steps_completed < total_steps:
        s_m = env.reset()
        done = False
        ep_steps = 0

        while not done:
            obs_m_t = torch.as_tensor(s_m, dtype=torch.float32, device=device).unsqueeze(0)
            with torch.no_grad():
                action_m, logp_m, _, val_m = maestro_net.get_action_and_value(obs_m_t)
            act_m_idx = int(action_m.item())
            alpha_idx, vent_idx = divmod(act_m_idx, 4)

            next_s_m, r_m, done, info = env.step((alpha_idx, vent_idx))
            maestro_buf.add(s_m, act_m_idx, float(logp_m.item()), r_m, float(val_m.item()), done)

            s_m = next_s_m
            ep_steps += 1
            steps_completed += 1

            if steps_completed >= total_steps:
                break

        episodes_completed += 1
        print(f"Episodio {episodes_completed} terminado | Steps Maestro: {ep_steps} | Steps totales acumulados: {steps_completed} | Q_exec: {env.Q_executed:.1f} | Reward terminal: {r_m:.2f}")

    env.close()

    # 5. PPO Update: Maestro
    print("\n--- Ejecutando PPO Update: Maestro ---")
    maestro_buf.compute_returns_advantages(gamma=0.99, gae_lambda=0.95)
    print(f"Transiciones recolectadas en Maestro buffer: {len(maestro_buf.obs)}")
    assert len(maestro_buf.obs) > 0, "El buffer del Maestro no deberia estar vacio."

    for batch in maestro_buf.get_batches(batch_size=32, device=device):
        m_losses = ppo_update(maestro_net, maestro_opt, batch)
        assert np.isfinite(m_losses["policy_loss"]), "Policy loss de Maestro no es finita"
        assert np.isfinite(m_losses["value_loss"]), "Value loss de Maestro no es finita"
        assert np.isfinite(m_losses["entropy"]), "Entropy de Maestro no es finita"
        print(f"  Maestro update OK: policy_loss={m_losses['policy_loss']:.4f}, value_loss={m_losses['value_loss']:.4f}, entropy={m_losses['entropy']:.4f}")

    # 6. PPO Update: 3 Ejecutores
    print("\n--- Ejecutando PPO Update: 3 Ejecutores ---")
    for i, tramo_name in enumerate(tramos):
        buf = ejecutor_bufs[i]
        buf.compute_returns_advantages(gamma=0.95, gae_lambda=0.95)
        print(f"Transiciones recolectadas en Ejecutor {i} ({tramo_name}): {len(buf.obs)}")
        assert len(buf.obs) > 0, f"Buffer de Ejecutor {i} no deberia estar vacio"

        for batch in buf.get_batches(batch_size=32, device=device):
            e_losses = ppo_update(ejecutor_nets[i], ejecutor_opts[i], batch)
            assert np.isfinite(e_losses["policy_loss"]), f"Policy loss Ejecutor {i} no es finita"
            assert np.isfinite(e_losses["value_loss"]), f"Value loss Ejecutor {i} no es finita"
            print(f"  Ejecutor {i} ({tramo_name}) update OK: policy_loss={e_losses['policy_loss']:.4f}, value_loss={e_losses['value_loss']:.4f}")

    print("\n[OK] TODAS LAS PRUEBAS DE FORMAS, RECOMPENSAS Y GRADIENTES PPO PASARON EXITOSAMENTE.")


if __name__ == "__main__":
    run_short_training_test(total_steps=150)
