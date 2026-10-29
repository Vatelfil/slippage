"""Bucle de entrenamiento del Maestro (BORRADOR de PS para MR, 29 oct 2026, con apoyo de Claude Code).

Usa el `PPOTrainer` de MR con `role="maestro"` (γ = 0,99, 40 acciones) y su `ppo_update` sin cambios. Lo nuevo es
solo el bucle: jugar jornadas completas con `MaestroEjecutorEnv`, guardar las transiciones del Maestro en el buffer y
actualizar cada `episodes_per_update` jornadas.

Decisiones de este borrador (MR las puede cambiar):

- **Ejecutores fijos**: no aprenden mientras aprende el Maestro (sin entrenar, muestreando su política, o cargados de
  un checkpoint). Entrenar los dos niveles a la vez mezcla dos señales que se mueven; esto se puede probar después.
- **Recompensa en bps**: R_M viene en CLP (−IS_total − λ·Q_pendiente·P). Se divide por el valor de la orden a precio de
  llegada (Q_total · P_ref) y se multiplica por 10⁴. Es un cambio de escala positivo, no cambia qué política es mejor,
  y evita que la pérdida del crítico tenga valores de millones.
- **Semillas**: la jornada k usa la semilla `seed_base + k`; la ventana j de esa jornada, `(seed_base + k) * 1000 + j`.
- **Entorno**: por defecto Poisson (una jornada tarda menos de un segundo). En ABIDES una jornada toma de 3 a 6 minutos,
  así que la propuesta es entrenar en Poisson y evaluar en ABIDES con `scripts/colab/evaluar_sistema_ps.py`.
- **Impacto acumulado entre ventanas** opcional (`src/envs/impacto_acumulado.py`); sin él el Maestro no tiene
  nada que coordinar (ver `docs/LEEME_MR.md`).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Union

import numpy as np
import torch

from src.envs.impacto_acumulado import ParametrosImpacto, con_impacto, fabrica_poisson
from src.envs.maestro_ejecutor_protocol import MaestroEjecutorEnv
from src.training.ppo_trainer import PPOConfig, PPOTrainer


@dataclass
class ConfigJornada:
    q_total: int = 30000
    ticker: str = "FALABELLA"
    lambda_penalty: Optional[float] = None          # None: el LAMBDA_PENALTY del protocolo (0,05)
    impacto: Optional[ParametrosImpacto] = None
    datos_historicos: Optional[object] = None        # tabla S_M (1.2.2); None: la sintética del protocolo
    fabrica_ejecutor: Optional[Callable] = None      # None: Poisson del ticker
    executor_policy_fn: Optional[Callable] = None    # None: Ejecutores sin entrenar muestreando (ver politica_ejecutores)


def redes_ejecutores(seed_red: int = 1000) -> Dict:
    """Los tres Ejecutores sin entrenar, con pesos fijados por `seed_red` (sin tocar el estado aleatorio global)."""
    from src.models.networks_factory import make_executor_networks
    estado = torch.random.get_rng_state()
    torch.manual_seed(int(seed_red))
    redes = make_executor_networks()
    torch.random.set_rng_state(estado)            # no cambia la semilla del Maestro
    return redes


def guardar_ejecutores(redes: Dict, carpeta: Union[str, Path]) -> Dict[str, str]:
    """Guarda los Ejecutores fijos con que se entrenó el Maestro, en el formato que lee el evaluador del sistema
    (`--ckpt-ejecutor tramo=ruta`). Así el Maestro se evalúa con los mismos Ejecutores con que aprendió."""
    rutas = {}
    for tramo, red in redes.items():
        ruta = Path(carpeta) / f"ejecutor_{tramo}.pt"
        torch.save({"model_state_dict": red.state_dict()}, ruta)
        rutas[tramo] = str(ruta)
    return rutas


def politica_ejecutores(redes: Optional[Dict] = None, deterministic: bool = False, seed_red: int = 1000) -> Callable:
    """Política fija de los tres Ejecutores. Sin `redes`, crea las tres sin entrenar con pesos fijados por `seed_red`."""
    from src.models.networks_factory import make_executor_policy_fn
    if redes is None:
        redes = redes_ejecutores(seed_red)
    for r in redes.values():
        r.eval()
    return make_executor_policy_fn(redes, deterministic=deterministic)


def _fabrica_con_semillas(base: Callable, semilla_jornada: int) -> Callable:
    contador = {"k": 0}

    def f(**kw):
        kw = dict(kw, seed=int(semilla_jornada) * 1000 + contador["k"])
        contador["k"] += 1
        return base(**kw)

    return f


def crear_jornada(cfg: ConfigJornada, semilla: int, executor_policy_fn: Callable) -> MaestroEjecutorEnv:
    base = cfg.fabrica_ejecutor or fabrica_poisson(cfg.ticker)
    fabrica = con_impacto(_fabrica_con_semillas(base, semilla), cfg.impacto)
    return MaestroEjecutorEnv(meta_orden_quantity=int(cfg.q_total), datos_historicos=cfg.datos_historicos,
                              executor_env_factory=fabrica, executor_policy_fn=executor_policy_fn,
                              lambda_penalty=cfg.lambda_penalty)


def resumen_jornada(env: MaestroEjecutorEnv, r_m: float, acciones: List[int]) -> Dict[str, float]:
    q = sum(r["q_ejecutado"] for r in env.executor_reports)
    monto = sum(r["q_ejecutado"] * r["p_promedio"] for r in env.executor_reports)
    p_ref = float(env.P_referencia or 0.0)
    slip = (monto / q - p_ref) / p_ref * 1e4 if q > 0 and p_ref > 0 else float("nan")
    alfas = [divmod(a, 4)[0] for a in acciones]
    return {"R_M": float(r_m), "R_M_bps": recompensa_bps(r_m, env.Q_total, p_ref), "q_ejecutado": float(q),
            "cumplimiento": float(q) / float(env.Q_total), "slippage_bps": float(slip), "decisiones": len(acciones),
            "alpha_idx_medio": float(np.mean(alfas)) if alfas else float("nan"),
            "ventana_idx_medio": float(np.mean([a % 4 for a in acciones])) if acciones else float("nan")}


def recompensa_bps(r_m: float, q_total: float, p_ref: float) -> float:
    return float(r_m) / (float(q_total) * float(p_ref)) * 1e4 if q_total and p_ref else 0.0


def jugar_jornada(trainer: PPOTrainer, env: MaestroEjecutorEnv, guardar: bool = True,
                  deterministic: bool = False) -> Dict[str, float]:
    """Una jornada completa. Con `guardar` las transiciones van al buffer del entrenador (recompensa en bps)."""
    s = env.reset()
    done, acciones, transiciones, r_m = False, [], [], 0.0
    while not done:
        obs_t = torch.as_tensor(s, dtype=torch.float32, device=trainer.device).unsqueeze(0)
        with torch.no_grad():
            if deterministic:
                logits, v = trainer.model(obs_t)
                a = torch.argmax(logits, dim=-1)
                lp = torch.distributions.Categorical(logits=logits).log_prob(a)
            else:
                a, lp, _, v = trainer.model.get_action_and_value(obs_t)
        idx = int(a.item())
        s_next, r_m, done, _ = env.step(divmod(idx, 4))
        transiciones.append((np.asarray(s, dtype=np.float32), idx, float(lp.item()), float(v.item()), bool(done)))
        acciones.append(idx)
        s = s_next
    env.close()
    r_bps = recompensa_bps(r_m, env.Q_total, env.P_referencia or 0.0)
    if guardar:
        for k, (obs, idx, lp, v, d) in enumerate(transiciones):
            trainer.buffer.add(obs, idx, lp, r_bps if d else 0.0, v, d)
    return resumen_jornada(env, r_m, acciones)


def nuevo_trainer(seed: int = 1000, **cfg) -> PPOTrainer:
    base = dict(lr=3e-4, gamma=0.99, gae_lambda=0.95, clip_ratio=0.2, entropy_coef=0.01, value_coef=0.5,
                epochs=4, minibatch_size=64, episodes_per_update=10)
    base.update(cfg)
    return PPOTrainer(role="maestro", cfg=PPOConfig(**base), seed=seed, device="cpu")


def train_maestro_episodes(trainer: PPOTrainer, cfg: ConfigJornada, n_jornadas: int, seed_base: int = 20000,
                           csv_path: Optional[Union[str, Path]] = None,
                           checkpoint_dir: Optional[Union[str, Path]] = None, checkpoint_freq: int = 10,
                           log_fn: Callable[[str], None] = print) -> List[Dict[str, float]]:
    """Entrena `n_jornadas` más a partir de `trainer.current_episode`. Devuelve el resumen de cada jornada."""
    politica = cfg.executor_policy_fn or politica_ejecutores()
    historial, recientes = [], []
    inicio = trainer.current_episode + 1
    fin = trainer.current_episode + n_jornadas
    for ep in range(inicio, fin + 1):
        trainer.current_episode = ep
        res = jugar_jornada(trainer, crear_jornada(cfg, seed_base + ep, politica))
        res["episodio"] = ep
        historial.append(res)
        recientes.append(res)
        if len(recientes) == trainer.cfg.episodes_per_update or ep == fin:
            m = trainer.ppo_update()
            trainer.buffer.clear()
            r = np.array([x["R_M_bps"] for x in recientes])
            m.update({"episodio": ep, "reward_mean": float(r.mean()), "reward_std": float(r.std()) if len(r) > 1 else 0.0})
            if csv_path:
                trainer.log_to_csv(csv_path, m)
            log_fn(f"Jornada {ep}/{fin} [maestro] R_M {m['reward_mean']:.2f} bps | cumplimiento "
                   f"{np.mean([x['cumplimiento'] for x in recientes]):.3f} | alpha_idx {np.mean([x['alpha_idx_medio'] for x in recientes]):.2f}")
            recientes = []
        if checkpoint_dir and (ep % checkpoint_freq == 0 or ep == fin):
            trainer.save_checkpoint(Path(checkpoint_dir) / "checkpoint_last.pt")
    return historial


def evaluar_maestro(trainer: PPOTrainer, cfg: ConfigJornada, semillas, deterministic: bool = False) -> List[Dict[str, float]]:
    """Jornadas de evaluación sin guardar nada en el buffer (semillas aparte de las de entrenamiento)."""
    politica = cfg.executor_policy_fn or politica_ejecutores()
    gen = torch.random.get_rng_state()
    out = []
    for s in semillas:
        torch.manual_seed(int(s))
        out.append(dict(jugar_jornada(trainer, crear_jornada(cfg, int(s), politica), guardar=False,
                                      deterministic=deterministic), semilla=int(s)))
    torch.random.set_rng_state(gen)
    return out
