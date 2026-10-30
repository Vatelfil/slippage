"""Prueba de cordura del PPOTrainer de MR: ¿aprende algo trivial? (PS, revisión del 29 oct; ≈ 11 min en el PC)

    python scripts/prueba_cordura_ppo_ps.py

Entorno de juguete con la misma forma que el Ejecutor (observación de 27, acción MultiDiscrete [3, 10, 8] que llega
desde 240 índices planos, 10 pasos por episodio). En cada paso, comprar a mercado (tipo 2) da +1 y lo demás 0, más
ruido normal de desviación sigma. Se mide la probabilidad de elegir "mercado" antes y después de 1.000 episodios.

El ruido se elige para reproducir la relación señal/ruido por episodio que se midió en ABIDES:
ganancia de la mejor política frente a la aleatoria ≈ 2 bps, desviación del costo por episodio ≈ 16,6 bps.
"""
import os
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.training.ppo_trainer import PPOConfig, PPOTrainer  # noqa: E402

PASOS = 10


class Juguete:
    def __init__(self, sigma, seed, **_):
        self.sigma = sigma
        self.rng = np.random.default_rng(seed)
        self.t = 0

    def _obs(self):
        o = np.full(27, 0.5, dtype=np.float32)
        o[0] = self.t / PASOS
        return o

    def reset(self):
        self.t = 0
        return self._obs(), {}

    def step(self, a):
        r = (1.0 if int(a[0]) == 2 else 0.0) + self.rng.normal(0.0, self.sigma)
        self.t += 1
        return self._obs(), r, self.t >= PASOS, False, {}

    def close(self):
        pass


def prob_mercado(model):
    with torch.no_grad():
        o = torch.full((1, 27), 0.5)
        o[0, 0] = 0.3
        logits, _ = model(o)
        p = torch.softmax(logits, -1).reshape(3, 10, 8)
    return float(p[2].sum())


def correr(sigma, episodios=1000, seed=1000):
    cfg = PPOConfig(lr=3e-4, gamma=1.0, gae_lambda=0.95, clip_ratio=0.2, entropy_coef=0.01, value_coef=0.5,
                    epochs=4, minibatch_size=64, episodes_per_update=10)
    tr = PPOTrainer(role="ejecutor", cfg=cfg, seed=seed, device="cpu")
    p0 = prob_mercado(tr.model)
    fab = lambda executor_id=None, q_slice=None, ventana_min=None, seed=0: Juguete(sigma, seed)  # noqa: E731
    hitos = {}
    hechos = 0
    for meta in (1000, 5000, 20000):
        if meta > episodios:
            break
        tr.train_executor_episodes(fab, meta - hechos, log_fn=lambda *_: None)
        hechos = meta
        hitos[meta] = prob_mercado(tr.model)
    return p0, hitos


if __name__ == "__main__":
    señal_ep = PASOS * (1 - 1 / 3)               # ganancia por episodio de la política óptima frente a la aleatoria
    filas = []
    for etiqueta, snr in (("sin ruido", None), ("señal/ruido 1", 1.0), ("señal/ruido 0,3", 0.3), ("como ABIDES (0,12)", 2 / 16.6)):
        sigma = 0.0 if snr is None else señal_ep / (snr * np.sqrt(PASOS))
        t0 = time.time()
        p0, hitos = correr(sigma, episodios=20000 if snr is not None and snr < 0.5 else 1000)
        filas.append(f"{etiqueta:20s} sigma={sigma:6.2f}  P(mercado) inicial={p0:.3f}  " +
                     "  ".join(f"{k} ep: {v:.3f}" for k, v in hitos.items()) + f"  ({time.time() - t0:.0f} s)")
        print(filas[-1], flush=True)
    with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "analysis", "prueba_cordura_ppo.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(filas) + "\n")
