import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical

class BaseActorCritic(nn.Module):
    def __init__(self, obs_dim, action_dim, hidden_sizes=(256, 256)):
        super().__init__()
        # Shared feature extractor
        self.shared_net = nn.Sequential(
            nn.Linear(obs_dim, hidden_sizes[0]),
            nn.ReLU(),
            nn.Linear(hidden_sizes[0], hidden_sizes[1]),
            nn.ReLU()
        )

        # Actor head (policy) - outputs logits for discrete actions
        self.actor_head = nn.Linear(hidden_sizes[1], action_dim)

        # Critic head (value function) - outputs a single scalar value
        self.critic_head = nn.Linear(hidden_sizes[1], 1)

    def forward(self, obs):
        features = self.shared_net(obs)
        logits = self.actor_head(features)
        value = self.critic_head(features)
        return logits, value

    def get_action_and_value(self, obs, action=None):
        """Helper para el rollout PPO (agregado por PS, 23 sept, tarea 3.1.1 en curso).

        Ambas subclases (MasterActorCritic, ExecutorActorCritic) son de accion
        discreta unica (un solo `actor_head` de `action_dim` logits: 40 para
        el Maestro, `action_dim` flatten para el Ejecutor), asi que Categorical
        alcanza para las dos - no hay una rama continua (Normal) porque este
        modulo no la implementa.

        Args:
            obs: tensor (batch, obs_dim).
            action: si se entrega, se evalua su log_prob en vez de samplear
                una nueva (uso: recompute durante los epochs de PPO update).

        Returns:
            (action, log_prob, entropy, value)
        """
        logits, value = self.forward(obs)
        dist = Categorical(logits=logits)
        if action is None:
            action = dist.sample()
        return action, dist.log_prob(action), dist.entropy(), value

class MasterActorCritic(BaseActorCritic):
    def __init__(self, obs_dim):
        # 10 volume fractions * 4 execution windows = 40 possible discrete actions
        super().__init__(obs_dim=obs_dim, action_dim=40)

class ExecutorActorCritic(BaseActorCritic):
    def __init__(self, obs_dim, action_dim):
        # Action dim will depend on the specific tactical discretization
        # e.g., price offsets and waiting times
        super().__init__(obs_dim=obs_dim, action_dim=action_dim)

if __name__ == "__main__":
    # Test script to verify the networks function correctly
    print("Iniciando prueba de las redes Actor-Crítico...")
    
    batch_size = 4
    
    # 1. Test Master Agent
    obs_dim_master = 50 # Example generic dimension for inventory + market state
    master_net = MasterActorCritic(obs_dim=obs_dim_master)
    dummy_obs_master = torch.randn(batch_size, obs_dim_master)
    
    logits_m, value_m = master_net(dummy_obs_master)
    assert logits_m.shape == (batch_size, 40), f"Master logits shape error: {logits_m.shape}"
    assert value_m.shape == (batch_size, 1), f"Master value shape error: {value_m.shape}"
    print(f"✅ Agente Maestro OK - Logits shape: {logits_m.shape}, Value shape: {value_m.shape}")
    
    # 2. Test Executor Agents (3 agents for different time slots)
    obs_dim_executor = 30 # Example generic dimension for local LOB features
    action_dim_executor = 20 # Example tactical actions
    
    executors = {
        "Ejecutor 1 (Apertura)": ExecutorActorCritic(obs_dim_executor, action_dim_executor),
        "Ejecutor 2 (Media jornada)": ExecutorActorCritic(obs_dim_executor, action_dim_executor),
        "Ejecutor 3 (Cierre)": ExecutorActorCritic(obs_dim_executor, action_dim_executor)
    }
    
    dummy_obs_exec = torch.randn(batch_size, obs_dim_executor)
    
    for name, net in executors.items():
        logits_e, value_e = net(dummy_obs_exec)
        assert logits_e.shape == (batch_size, action_dim_executor), f"{name} logits shape error: {logits_e.shape}"
        assert value_e.shape == (batch_size, 1), f"{name} value shape error: {value_e.shape}"
        print(f"✅ {name} OK - Logits shape: {logits_e.shape}, Value shape: {value_e.shape}")
        
    print("Todas las redes pasaron la prueba de 'forward pass' correctamente.")
