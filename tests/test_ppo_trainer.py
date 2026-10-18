"""Pruebas del Ciclo de Entrenamiento PPO Unificado (Tarea 2.3.2).

Verifica:
  1. Mismo seed = mismos resultados (reproducibilidad exacta).
  2. Parada temprana por divergencia KL cuando approx_kl supera el umbral.
  3. Guardado y reanudacion de checkpoints sin corromper estado.
  4. Corrida de 20 episodios continuos sin NaNs, verificando escritura del CSV
     con las 8 columnas requeridas.
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pytest
import torch

from src.training.ppo_trainer import PPOTrainer, PPOConfig, RolloutBuffer
from src.envs.fallback_poisson_env import EjecutorEnvPoissonFallback


def _create_env(executor_id: str = "apertura", q_slice: int = 500, ventana_min: int = 5, seed: int = 42):
    return EjecutorEnvPoissonFallback(
        executor_id=executor_id,
        q_slice=q_slice,
        ventana_min=ventana_min,
        seed=seed,
    )


def test_rollout_buffer_y_gae():
    buf = RolloutBuffer()
    obs_dim = 27
    for t in range(50):
        obs = np.random.randn(obs_dim).astype(np.float32)
        done = (t == 24 or t == 49)
        buf.add(obs, action=1, log_prob=-0.5, reward=1.0, value=0.5, done=done)

    assert len(buf) == 50
    buf.compute_returns_advantages(gamma=0.95, gae_lambda=0.95)
    assert len(buf.returns) == 50
    assert len(buf.advantages) == 50
    assert all(np.isfinite(buf.returns))
    assert all(np.isfinite(buf.advantages))


def test_reproducibilidad_misma_semilla():
    cfg = PPOConfig(epochs=2, episodes_per_update=2, minibatch_size=16)

    trainer1 = PPOTrainer(role="ejecutor", cfg=cfg, seed=123)
    hist1 = trainer1.train_executor_episodes(
        env_factory=_create_env,
        n_episodes=4,
        tramo="apertura",
        q_slice=200,
        ventana_min=1,
    )

    trainer2 = PPOTrainer(role="ejecutor", cfg=cfg, seed=123)
    hist2 = trainer2.train_executor_episodes(
        env_factory=_create_env,
        n_episodes=4,
        tramo="apertura",
        q_slice=200,
        ventana_min=1,
    )

    # Las metricas de loss y retornos deben ser identicas
    for m1, m2 in zip(hist1, hist2):
        assert pytest.approx(m1["loss_actor"], rel=1e-5) == m2["loss_actor"]
        assert pytest.approx(m1["loss_critic"], rel=1e-5) == m2["loss_critic"]
        assert pytest.approx(m1["reward_mean"], rel=1e-5) == m2["reward_mean"]


def test_parada_temprana_por_kl():
    """Fuerza un target_kl minusculo para verificar que early_stopped sea True."""
    cfg = PPOConfig(target_kl=1e-8, kl_threshold_multiplier=1.0, epochs=10, episodes_per_update=2)
    trainer = PPOTrainer(role="ejecutor", cfg=cfg, seed=99)

    hist = trainer.train_executor_episodes(
        env_factory=_create_env,
        n_episodes=2,
        tramo="apertura",
        q_slice=200,
        ventana_min=1,
    )
    assert len(hist) > 0
    assert hist[0]["early_stopped"] is True


def test_checkpoint_y_reanudacion(tmp_path):
    checkpoint_dir = tmp_path / "checkpoints"
    csv_path = tmp_path / "training_log.csv"

    cfg = PPOConfig(episodes_per_update=2, epochs=2)
    trainer1 = PPOTrainer(role="ejecutor", cfg=cfg, seed=77)

    # Entrenar primeros 4 episodios
    trainer1.train_executor_episodes(
        env_factory=_create_env,
        n_episodes=4,
        tramo="apertura",
        q_slice=200,
        ventana_min=1,
        csv_path=csv_path,
        checkpoint_dir=checkpoint_dir,
        checkpoint_freq=2,
    )

    assert (checkpoint_dir / "checkpoint_last.pt").exists()
    assert trainer1.current_episode == 4

    # Instanciar nuevo trainer y reanudar
    trainer2 = PPOTrainer(role="ejecutor", cfg=cfg, seed=77)
    ckpt = trainer2.load_checkpoint(checkpoint_dir / "checkpoint_last.pt")
    assert trainer2.current_episode == 4
    assert ckpt["current_episode"] == 4

    # Entrenar 2 episodios mas
    trainer2.train_executor_episodes(
        env_factory=_create_env,
        n_episodes=2,
        tramo="apertura",
        q_slice=200,
        ventana_min=1,
        csv_path=csv_path,
        checkpoint_dir=checkpoint_dir,
        checkpoint_freq=2,
    )
    assert trainer2.current_episode == 6


def test_corrida_20_episodios_sin_nans_y_csv_valido(tmp_path):
    csv_path = tmp_path / "train_20_episodes.csv"
    checkpoint_dir = tmp_path / "checkpoints"

    cfg = PPOConfig(
        epochs=2,
        minibatch_size=32,
        episodes_per_update=5,
    )
    trainer = PPOTrainer(role="ejecutor", cfg=cfg, seed=42)

    hist = trainer.train_executor_episodes(
        env_factory=_create_env,
        n_episodes=20,
        tramo="apertura",
        q_slice=300,
        ventana_min=1,
        csv_path=csv_path,
        checkpoint_dir=checkpoint_dir,
        checkpoint_freq=10,
    )

    # Verificar que no hay NaNs
    for h in hist:
        for k, v in h.items():
            if isinstance(v, float):
                assert np.isfinite(v), f"NaN o Inf detectado en metrica {k}"

    # Verificar archivo CSV
    assert csv_path.exists()
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 4  # 20 episodios / 5 por update = 4 registros
        assert set(reader[0].keys()) == set(PPOTrainer.CSV_HEADER)
        for row in reader:
            assert int(row["episodio"]) in (5, 10, 15, 20)
            assert np.isfinite(float(row["loss_actor"]))
            assert np.isfinite(float(row["loss_critic"]))
            assert np.isfinite(float(row["entropia"]))
            assert np.isfinite(float(row["reward_mean"]))
            assert np.isfinite(float(row["kl"]))
            assert np.isfinite(float(row["clip_fraction"]))
