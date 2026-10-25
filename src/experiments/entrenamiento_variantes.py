"""Entrenamiento y evaluación de las variantes de recompensa (BORRADOR de PS; ver `variantes_recompensa.py`).

Usa el `PPOTrainer` de MR tal cual está. Lo único que se agrega es:
- una fábrica de entornos que aplica la variante (`variantes_recompensa.fabrica_entrenamiento`),
- un arranque opcional por imitación de una heurística (`imitar`),
- una evaluación común (`evaluar_red`) que mide igual a todas las variantes y a las políticas de referencia.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field, replace
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from src.experiments import variantes_recompensa as vr

# Escenarios de evaluación (tamaño del slice, ventana en minutos). El de 1.000 acciones es el que se usó hasta ahora;
# los otros dos se parecen más a lo que el Maestro le va a pedir a un Ejecutor.
ESCENARIOS = {"q1000_v15": (1000, 15), "q5000_v15": (5000, 15), "q20000_v15": (20000, 15)}
SEMILLAS_EVAL = tuple(range(5001, 5051))     # 50 semillas nuevas, nunca usadas para entrenar


@dataclass(frozen=True)
class ConfigPPO:
    """Hiperparámetros que se tocan en las pruebas; el resto queda como en `PPOConfig`."""
    lr: float = 3e-4
    gamma: float = 0.95                  # 0,95 es el valor del Título I para el Ejecutor
    entropy_coef: float = 0.01
    epochs: int = 4
    minibatch_size: int = 64
    episodes_per_update: int = 10


HIPER_ALTERNATIVOS = ConfigPPO(lr=5e-4, entropy_coef=0.02, epochs=8, minibatch_size=128, episodes_per_update=30)


def nuevo_trainer(semilla: int, cfg: ConfigPPO = ConfigPPO()):
    from src.training.ppo_trainer import PPOConfig, PPOTrainer
    c = PPOConfig(lr=cfg.lr, gamma=cfg.gamma, gae_lambda=0.95, clip_ratio=0.2, entropy_coef=cfg.entropy_coef, value_coef=0.5,
                  epochs=cfg.epochs, minibatch_size=cfg.minibatch_size, episodes_per_update=cfg.episodes_per_update)
    return PPOTrainer(role="ejecutor", cfg=c, seed=semilla)


def imitar(net, heuristica: str, semilla: int, episodios: int = 200, q_slice: int = 5000, ventana_min: int = 15,
           epocas: int = 30, lr: float = 1e-3) -> float:
    """Arranque por imitación: la red copia a una heurística (por defecto la mejor, `twap_limit_medio`) antes de que PPO
    la afine. Se juntan pares (observación, acción) corriendo la heurística y se entrena el actor con entropía cruzada
    (con suavizado, para que la política no quede con probabilidad 1 y PPO todavía pueda explorar). Devuelve la exactitud
    final sobre los datos de imitación."""
    import torch
    import torch.nn.functional as F
    from src.envs.spaces import EjecutorActionSpace
    from src.experiments import beta_sweep as bs

    espacio = EjecutorActionSpace()
    politica = bs.POLITICAS[heuristica]
    nivel = bs.NIVEL_PASIVO["poisson"]
    obs_l: List[np.ndarray] = []
    act_l: List[int] = []
    for k in range(episodios):
        env = vr._entorno_base("apertura", q_slice, ventana_min, 10_000 + semilla * 1000 + k, "FALABELLA", 0.0, "ejecutado")
        obs, _ = env.reset()
        paso, done = 0, False
        while not done:
            a = politica(paso, env.max_steps, nivel)
            obs_l.append(obs.copy())
            act_l.append(espacio.encode_flat(int(a[0]), int(a[1]), int(a[2])))
            obs, _, done, trunc, _ = env.step(a)
            done = bool(done or trunc)
            paso += 1
    X = torch.as_tensor(np.array(obs_l), dtype=torch.float32)
    y = torch.as_tensor(act_l, dtype=torch.int64)
    opt = torch.optim.Adam(net.parameters(), lr=lr)
    torch.manual_seed(semilla)
    for _ in range(epocas):
        perm = torch.randperm(len(X))
        for i in range(0, len(X), 128):
            idx = perm[i:i + 128]
            logits, _ = net(X[idx])
            loss = F.cross_entropy(logits, y[idx], label_smoothing=0.1)
            opt.zero_grad()
            loss.backward()
            opt.step()
    with torch.no_grad():
        logits, _ = net(X)
        return float((logits.argmax(-1) == y).float().mean())


def entrenar(variante: vr.Variante, semilla: int, episodios: int, q_slice: int = 5000, ventana_min: int = 15,
             cfg: ConfigPPO = ConfigPPO(), arranque: Optional[str] = None):
    """Entrena una red con la variante. Devuelve (red entrenada, red inicial, registro por episodio, exactitud de la
    imitación o None). La red inicial es la que el entrenador crea con esa semilla, antes de cualquier ajuste."""
    trainer = nuevo_trainer(semilla, cfg)
    inicial = copy.deepcopy(trainer.model)
    exactitud = imitar(trainer.model, arranque, semilla, q_slice=q_slice, ventana_min=ventana_min) if arranque else None
    registro: List[Dict[str, float]] = []
    fabrica = vr.fabrica_entrenamiento(variante, registro=registro, semilla_sorteo=semilla)
    trainer.train_executor_episodes(env_factory=fabrica, n_episodes=episodios, tramo="apertura", q_slice=q_slice,
                                    ventana_min=ventana_min, log_fn=lambda *_: None)
    fabrica.cerrar()
    return trainer.model, inicial, registro, exactitud


def curvas(registro: Sequence[Dict[str, float]], bloque: int = 100) -> List[Dict[str, float]]:
    """Medias del registro de entrenamiento por bloques de `bloque` episodios."""
    claves = ("retorno", "cumplimiento_voluntario", "cumplimiento_total", "pct_espera", "pct_mercado", "pct_limite",
              "slippage_bps")
    out = []
    for i in range(0, len(registro), bloque):
        trozo = registro[i:i + bloque]
        fila = {"episodios": f"{i + 1}-{i + len(trozo)}"}
        for k in claves:
            v = [r[k] for r in trozo if not np.isnan(r[k])]
            fila[k] = float(np.mean(v)) if v else float("nan")
        out.append(fila)
    return out


def evaluar_en_escenarios(red, inicial, semillas: Sequence[int] = SEMILLAS_EVAL) -> Dict[str, Dict]:
    """Red entrenada (muestreada y con argmax) y red inicial (muestreada), en cada escenario. Guarda también el slippage por
    semilla para poder comparar de a pares con la red inicial."""
    out: Dict[str, Dict] = {}
    for nombre, (q, v) in ESCENARIOS.items():
        kw = dict(q_slice=q, ventana_min=v)
        e = {
            "red_muestreada": vr.evaluar_red(red, semillas, muestrear=True, **kw),
            "red_argmax": vr.evaluar_red(red, semillas, muestrear=False, **kw),
            "inicial_muestreada": vr.evaluar_red(inicial, semillas, muestrear=True, **kw),
        }
        out[nombre] = {k: {"promedio": vr.promedios(r), "slippage_por_semilla": [x["slippage_bps"] for x in r]}
                       for k, r in e.items()}
    return out


def referencias(semillas: Sequence[int] = SEMILLAS_EVAL) -> Dict[str, Dict]:
    """Heurísticas y 'esperar siempre' con la misma regla de evaluación (una sola vez; no dependen de la red)."""
    esperar = lambda s: (lambda obs, paso, mx: np.array([vr.LIMIT_SELL_IDX, 0, 0]))
    out: Dict[str, Dict] = {}
    for nombre, (q, v) in ESCENARIOS.items():
        kw = dict(q_slice=q, ventana_min=v)
        filas = {n: vr.evaluar_heuristica(n, semillas, **kw) for n in ("agresiva_market", "twap_limit_medio", "pasiva_limit")}
        filas["esperar_siempre"] = vr.evaluar(esperar, semillas, **kw)
        out[nombre] = {k: {"promedio": vr.promedios(r), "slippage_por_semilla": [x["slippage_bps"] for x in r]}
                       for k, r in filas.items()}
    return out
