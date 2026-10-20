"""Entrenamiento inicial de validacion del Ejecutor (tarea 2.3.5) -- corre en Colab con ABIDES.

BORRADOR elaborado por PS con apoyo de Claude Code; pendiente de revision por BF (responsable de la 2.3.5).

Entrena un Ejecutor con el entrenador PPO de MR (`PPOTrainer`, 2.3.2) durante 100 episodios sobre ABIDES
calibrado, vigila perdida, recompensa y KL, guarda el checkpoint y el CSV, y despues mide en semillas de
evaluacion NUEVAS el slippage y el cumplimiento de la orden de: la red entrenada, la red SIN entrenar (control)
y las tres politicas heuristicas de referencia. El cumplimiento alimenta la regla de vigilancia de la decision D3
(si baja del 95 %, el plan manda pasar a la opcion A de R_E).

    PYTHONPATH=. python scripts/colab/entrenamiento_inicial_ps.py \
        --calibrated-json data/calibration/rmsc04_ipsa_FALABELLA_2026-08-23.json \
        --out-dir <carpeta_de_drive>/t5_entrenamiento --max-minutes 150

Reanudable: guarda un checkpoint cada 10 episodios y el estado de cada etapa; si se corta, volver a ejecutar
el mismo comando. `--entorno poisson` hace un ensayo local con el simulador de respaldo.
Semillas: entrenamiento 1001-1100 (--seed 1000), evaluacion 5001-5015. No se usan las 10 meta-ordenes oficiales.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.config.market_params import BETA_RIESGO_EJECUTOR  # noqa: E402
from src.envs.rmsc04_search import load_resumable, save_json  # noqa: E402
from src.experiments import beta_phase2 as bp  # noqa: E402
from src.experiments import beta_sweep as bs  # noqa: E402

CUMPLIMIENTO_MIN = 0.95  # regla de vigilancia de D3


def _factory(entorno: str, calibrated_json: str, ticker: str):
    if entorno == "abides":
        from src.envs.abides_ejecutor_env import make_calibrated_env_factory  # requiere ABIDES
        return make_calibrated_env_factory(calibrated_json, ticker=ticker)
    from src.envs.fallback_poisson_env import EjecutorEnvPoissonFallback
    return EjecutorEnvPoissonFallback


def _nuevo_trainer(seed: int):
    from src.training.ppo_trainer import PPOConfig, PPOTrainer
    cfg = PPOConfig(lr=3e-4, gamma=0.95, gae_lambda=0.95, clip_ratio=0.2, entropy_coef=0.01, value_coef=0.5,
                    epochs=4, minibatch_size=64, episodes_per_update=10)
    return PPOTrainer(role="ejecutor", cfg=cfg, seed=seed)


def _resumen_eval(factory, net, tramo, seeds: Sequence[int], q_slice: int, ventana_min: int) -> Dict:
    eps = bp.evaluar_red(net, factory, tramo, seeds, q_slice, ventana_min)
    return bp.resumen_evaluacion(eps, BETA_RIESGO_EJECUTOR)


def main(argv: Optional[Sequence[str]] = None) -> Path:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--calibrated-json", default=str(REPO_ROOT / "data/calibration/rmsc04_ipsa_FALABELLA_2026-08-23.json"))
    ap.add_argument("--ticker", default="FALABELLA")
    ap.add_argument("--entorno", choices=["abides", "poisson"], default="abides")
    ap.add_argument("--tramo", default="apertura", choices=["apertura", "media_jornada", "cierre"])
    ap.add_argument("--episodes", type=int, default=100)
    ap.add_argument("--q-slice", type=int, default=1000)
    ap.add_argument("--ventana-min", type=int, default=15)
    ap.add_argument("--seed", type=int, default=1000, help="semilla del entrenador: episodio k usa la semilla seed + k")
    ap.add_argument("--eval-seeds", type=int, default=15)
    ap.add_argument("--eval-seed-base", type=int, default=5000)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--max-minutes", type=float, default=None)
    args = ap.parse_args(argv)

    t_ini = time.time()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"entrenamiento_{args.tramo}.csv"
    ckpt_dir = out_dir / f"checkpoints_{args.tramo}"
    estado_path = out_dir / f"entrenamiento_inicial_{args.tramo}.json"
    factory = _factory(args.entorno, args.calibrated_json, args.ticker)
    firma = {"tarea": "2.3.5", "entorno": args.entorno, "ticker": args.ticker, "tramo": args.tramo,
             "episodios": args.episodes, "q_slice": args.q_slice, "ventana_min": args.ventana_min,
             "seed": args.seed, "eval_seeds": args.eval_seeds, "eval_seed_base": args.eval_seed_base,
             "beta": BETA_RIESGO_EJECUTOR, "calibrated_json": Path(args.calibrated_json).name}
    estado = load_resumable(estado_path, firma)
    estado.setdefault("segundos_entrenamiento", 0.0)
    eval_seeds = [args.eval_seed_base + i for i in range(1, args.eval_seeds + 1)]

    def excedido() -> bool:
        return args.max_minutes is not None and time.time() - t_ini > args.max_minutes * 60

    # -- Etapa 0: control, red sin entrenar (mismos pesos iniciales que el entrenador con esta semilla)
    if "evaluacion_sin_entrenar" not in estado:
        print("== Evaluando la red SIN entrenar (control)", flush=True)
        estado["evaluacion_sin_entrenar"] = _resumen_eval(factory, _nuevo_trainer(args.seed).model, args.tramo,
                                                          eval_seeds, args.q_slice, args.ventana_min)
        save_json(estado_path, estado)

    # -- Etapa 1: entrenamiento reanudable en bloques de 10 episodios (= una actualizacion PPO)
    trainer = _nuevo_trainer(args.seed)
    ckpt = ckpt_dir / "checkpoint_last.pt"
    if ckpt.exists():
        trainer.load_checkpoint(ckpt)
        print(f"Reanudando desde el episodio {trainer.current_episode}", flush=True)
    while trainer.current_episode < args.episodes:
        if excedido():
            estado["entrenamiento_completo"] = False
            save_json(estado_path, estado)
            print(f"Presupuesto de tiempo agotado en el episodio {trainer.current_episode}: volver a ejecutar para continuar.")
            return estado_path
        n = min(10, args.episodes - trainer.current_episode)
        t0 = time.time()
        trainer.train_executor_episodes(env_factory=factory, n_episodes=n, tramo=args.tramo, q_slice=args.q_slice,
                                        ventana_min=args.ventana_min, csv_path=csv_path, checkpoint_dir=ckpt_dir,
                                        checkpoint_freq=10)
        estado["segundos_entrenamiento"] = round(estado["segundos_entrenamiento"] + time.time() - t0, 1)
        save_json(estado_path, estado)
    estado["entrenamiento_completo"] = True
    estado["episodios_entrenados"] = trainer.current_episode

    # -- Etapa 2: evaluacion de la red entrenada
    if "evaluacion_entrenada" not in estado:
        print("== Evaluando la red entrenada", flush=True)
        estado["evaluacion_entrenada"] = _resumen_eval(factory, trainer.model, args.tramo, eval_seeds,
                                                       args.q_slice, args.ventana_min)
        save_json(estado_path, estado)

    # -- Etapa 3: politicas de referencia en las mismas semillas
    estado.setdefault("referencias", {})
    for nombre in bs.POLITICAS:
        if nombre in estado["referencias"]:
            continue
        if excedido():
            save_json(estado_path, estado)
            print("Presupuesto de tiempo agotado en las referencias: volver a ejecutar para continuar.")
            return estado_path
        print(f"== Referencia: {nombre}", flush=True)
        eps = bp.evaluar_heuristica(nombre, factory, args.entorno, args.tramo, eval_seeds, args.q_slice, args.ventana_min)
        estado["referencias"][nombre] = bp.resumen_evaluacion(eps, BETA_RIESGO_EJECUTOR)
        save_json(estado_path, estado)

    # -- Regla de vigilancia de D3 (solo se informa; la decision es de BF)
    cumpl = estado["evaluacion_entrenada"].get("cumplimiento_medio")
    estado["vigilancia_D3"] = {
        "cumplimiento_medio": cumpl, "umbral": CUMPLIMIENTO_MIN,
        "cumple": bool(cumpl is not None and cumpl >= CUMPLIMIENTO_MIN),
        "texto": ("El cumplimiento de la red entrenada es >= 95 %: se mantiene la opcion 0 de D3." if
                  (cumpl is not None and cumpl >= CUMPLIMIENTO_MIN) else
                  "El cumplimiento de la red entrenada es < 95 %: segun la regla de D3 corresponde pasar a la opcion A "
                  "(riesgo sobre lo pendiente) y recalcular beta*."),
    }
    estado["segundos_totales_esta_ejecucion"] = round(time.time() - t_ini, 1)
    save_json(estado_path, estado)
    print(f"\nGuardado: {estado_path}\n{estado['vigilancia_D3']['texto']}")
    return estado_path


if __name__ == "__main__":
    main()
