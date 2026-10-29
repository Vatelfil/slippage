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
import functools
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
from src.training.monitoreo import MonitorEntrenamiento  # noqa: E402

CUMPLIMIENTO_MIN = 0.95  # regla de vigilancia de D3


def _factory(entorno: str, calibrated_json: str, ticker: str, riesgo_sobre: str = "ejecutado", mid_decision: bool = False):
    extra = {} if riesgo_sobre == "ejecutado" else {"riesgo_sobre": riesgo_sobre}   # opcion A de D3: riesgo sobre lo pendiente
    if entorno == "abides":
        if mid_decision:   # R_E contra el P_mid al decidir (borrador para BF, ver docs/revision_opus_PS.md)
            extra["mid_decision"] = True
        from src.envs.abides_ejecutor_env import make_calibrated_env_factory  # requiere ABIDES
        return make_calibrated_env_factory(calibrated_json, ticker=ticker, **extra)
    from src.envs.fallback_poisson_env import EjecutorEnvPoissonFallback
    return functools.partial(EjecutorEnvPoissonFallback, **extra) if extra else EjecutorEnvPoissonFallback


def _con_tamanos_aleatorios(factory):
    """En cada episodio sortea el tamaño del slice y la ventana entre los valores que pedirá el Maestro (hallazgo H4 de
    `docs/revision_opus_PS.md`). El sorteo sale de la semilla del episodio, así que no cambia al reanudar."""
    import numpy as np
    from src.experiments.variantes_recompensa import Q_SLICE_MAESTRO, VENTANAS_MAESTRO

    def fabrica(**kw):
        rng = np.random.default_rng(int(kw.get("seed", 0)) + 77)
        kw = dict(kw, q_slice=int(rng.choice(Q_SLICE_MAESTRO)), ventana_min=int(rng.choice(VENTANAS_MAESTRO)))
        return factory(**kw)
    return fabrica


def _con_variante(factory, penalizacion_bps: float, costo_espera_bps: float, recompensa: str = "original"):
    """Aplica al entrenamiento la penalización por lo no comprado, el costo de espera y/o la recompensa de slippage contra el
    precio de llegada (ver `src/experiments/variantes_recompensa.py`). La evaluación sigue usando la fábrica original, así que
    el slippage y el cumplimiento que se informan son los de siempre y se pueden comparar con corridas anteriores."""
    from src.experiments.variantes_recompensa import EntornoVariante, Variante
    variante = Variante("entrenamiento", recompensa=recompensa, penalizacion_bps=penalizacion_bps,
                        costo_espera_bps=costo_espera_bps)
    return lambda **kw: EntornoVariante(factory(**kw), variante)


HP_DEFECTO = {"lr": 3e-4, "epochs": 4, "minibatch": 64, "clip": 0.2, "gae_lambda": 0.95, "entropy_coef": 0.01}


def _nuevo_trainer(seed: int, gamma: float = 0.95, hp: Optional[Dict] = None):
    """Entrenador del Ejecutor. `hp` cambia los hiperparametros del barrido (3.1.1 y 3.1.2); sin `hp`, los de siempre."""
    from src.training.ppo_trainer import PPOConfig, PPOTrainer
    h = dict(HP_DEFECTO, **(hp or {}))
    cfg = PPOConfig(lr=h["lr"], gamma=gamma, gae_lambda=h["gae_lambda"], clip_ratio=h["clip"], entropy_coef=h["entropy_coef"],
                    value_coef=0.5, epochs=int(h["epochs"]), minibatch_size=int(h["minibatch"]), episodes_per_update=10)
    return PPOTrainer(role="ejecutor", cfg=cfg, seed=seed)


def _resumen_eval(factory, net, tramo, seeds: Sequence[int], q_slice: int, ventana_min: int) -> Dict:
    eps = bp.evaluar_red(net, factory, tramo, seeds, q_slice, ventana_min)
    return bp.resumen_evaluacion(eps, BETA_RIESGO_EJECUTOR)


def _evaluar_estocastica(factory, net, tramo, seeds: Sequence[int], q_slice: int, ventana_min: int):
    """Igual que `bp.evaluar_red`, pero MUESTREANDO la accion de la politica (como en el entrenamiento) en vez de
    tomar el argmax. Con una politica de alta entropia el argmax puede ser una accion de espera y no ejecutar nada."""
    import torch
    from src.envs.spaces import EjecutorActionSpace

    space, out = EjecutorActionSpace(), []
    for seed in seeds:
        torch.manual_seed(int(seed))
        env = factory(executor_id=tramo, q_slice=q_slice, ventana_min=ventana_min, seed=int(seed), beta=0.0)
        try:
            obs, info = env.reset()
            p_ref = info.get("p_referencia")
            if p_ref is None:
                p_ref = float(info["entry_price"]) / float(info.get("unidades_por_clp", 1.0))
            pasos, done = [], False
            while not done:
                with torch.no_grad():
                    logits, _ = net(torch.as_tensor(obs, dtype=torch.float32).unsqueeze(0))
                idx = int(torch.distributions.Categorical(logits=logits.squeeze(0)).sample().item())
                obs, _, done, trunc, info = env.step(space.decode_flat(idx))
                done = bool(done or trunc)
                pasos.append(bs.step_record(info))
            out.append(bs.summarize_episode(pasos, float(q_slice), float(p_ref)))
        finally:
            env.close()
    return out


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
    ap.add_argument("--riesgo-sobre", choices=["ejecutado", "pendiente"], default="ejecutado",
                    help="ejecutado = opcion 0 de D3 (Titulo I); pendiente = opcion A (riesgo sobre lo que falta ejecutar)")
    ap.add_argument("--gamma", type=float, default=0.95,
                    help="factor de descuento del Ejecutor; con 1,0 un costo al final de la ventana no se achica al verlo desde el principio")
    ap.add_argument("--penalizacion-bps", type=float, default=0.0,
                    help="castigo, en bps del precio de llegada, por cada acción del slice sin comprar al terminar la ventana")
    ap.add_argument("--costo-espera-bps", type=float, default=0.0,
                    help="costo denso por inventario pendiente (total en bps si no se compra nada en la ventana)")
    ap.add_argument("--recompensa", choices=["original", "is_llegada"], default="original",
                    help="original = R_E del Titulo I (compara con el precio medio de cada instante); is_llegada = lo que cuesta cada "
                         "compra frente al precio de llegada de la orden (variante V4 con --penalizacion-bps 30 y --gamma 1)")
    ap.add_argument("--mid-decision", action="store_true",
                    help="solo ABIDES: R_E compara el precio pagado con el P_mid que vio el agente al decidir (como en Poisson), "
                         "no con el del despertar siguiente")
    ap.add_argument("--aleatorizar", action="store_true",
                    help="entrenar con tamaños (1.000 a 20.000) y ventanas (1 a 15 min) sorteados por episodio; la evaluación sigue "
                         "con --q-slice y --ventana-min")
    for nombre, valor in HP_DEFECTO.items():   # hiperparametros del barrido de MR (borrador de PS para MR)
        ap.add_argument(f"--{nombre.replace('_', '-')}", type=type(valor), default=valor)
    ap.add_argument("--sin-monitoreo", action="store_true",
                    help="no escribir monitoreo_episodios.csv (costo, cumplimiento y fraccion de espera por episodio; 3.1.4)")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--max-minutes", type=float, default=None)
    args = ap.parse_args(argv)

    t_ini = time.time()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"entrenamiento_{args.tramo}.csv"
    ckpt_dir = out_dir / f"checkpoints_{args.tramo}"
    estado_path = out_dir / f"entrenamiento_inicial_{args.tramo}.json"
    factory = _factory(args.entorno, args.calibrated_json, args.ticker, args.riesgo_sobre, args.mid_decision)
    firma = {"tarea": "2.3.5", "entorno": args.entorno, "ticker": args.ticker, "tramo": args.tramo,
             "episodios": args.episodes, "q_slice": args.q_slice, "ventana_min": args.ventana_min,
             "seed": args.seed, "eval_seeds": args.eval_seeds, "eval_seed_base": args.eval_seed_base,
             "beta": BETA_RIESGO_EJECUTOR, "calibrated_json": Path(args.calibrated_json).name}
    if args.riesgo_sobre != "ejecutado":   # solo si no es la opcion por defecto, para no invalidar corridas anteriores
        firma["riesgo_sobre"] = args.riesgo_sobre
    # igual que arriba: estos campos solo entran a la firma cuando se usan
    if args.gamma != 0.95:
        firma["gamma"] = args.gamma
    if args.penalizacion_bps:
        firma["penalizacion_bps"] = args.penalizacion_bps
    if args.costo_espera_bps:
        firma["costo_espera_bps"] = args.costo_espera_bps
    if args.recompensa != "original":
        firma["recompensa"] = args.recompensa
    if args.mid_decision:
        firma["mid_decision"] = True
    if args.aleatorizar:
        firma["aleatorizar"] = True
    hp = {k: getattr(args, k) for k in HP_DEFECTO}
    if hp != HP_DEFECTO:   # solo si cambia, para no invalidar corridas anteriores
        firma["hiperparametros"] = hp
    monitor = None if args.sin_monitoreo else MonitorEntrenamiento(out_dir / "monitoreo_episodios.csv", seed_base=args.seed)
    usa_variante = args.penalizacion_bps or args.costo_espera_bps or args.recompensa != "original"
    factory_base = _con_tamanos_aleatorios(factory) if args.aleatorizar else factory
    factory_variante = (_con_variante(factory_base, args.penalizacion_bps, args.costo_espera_bps, args.recompensa)
                        if usa_variante else factory_base)
    factory_entrenamiento = monitor.envolver(factory_variante) if monitor else factory_variante
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
    trainer = _nuevo_trainer(args.seed, args.gamma, hp)
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
        trainer.train_executor_episodes(env_factory=factory_entrenamiento, n_episodes=n, tramo=args.tramo, q_slice=args.q_slice,
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

    if "evaluacion_entrenada_estocastica" not in estado:
        print("== Evaluando la red entrenada MUESTREANDO la politica (como en el entrenamiento)", flush=True)
        eps = _evaluar_estocastica(factory, trainer.model, args.tramo, eval_seeds, args.q_slice, args.ventana_min)
        estado["evaluacion_entrenada_estocastica"] = bp.resumen_evaluacion(eps, BETA_RIESGO_EJECUTOR)
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
        "cumplimiento_politica_muestreada": estado["evaluacion_entrenada_estocastica"].get("cumplimiento_medio"),
        "cumple": bool(cumpl is not None and cumpl >= CUMPLIMIENTO_MIN),
        "texto": ("El cumplimiento de la red entrenada es >= 95 %: se mantiene la opcion 0 de D3." if
                  (cumpl is not None and cumpl >= CUMPLIMIENTO_MIN) else
                  "El cumplimiento de la red entrenada es < 95 %: segun la regla de D3 corresponde pasar a la opcion A "
                  "(riesgo sobre lo pendiente) y recalcular beta*."),
    }
    if args.riesgo_sobre != "ejecutado":   # el texto de arriba habla de la opcion 0; en una corrida con la A solo se informa el dato
        estado["vigilancia_D3"]["texto"] = (f"Corrida con la opcion A de R_E (riesgo sobre lo pendiente): cumplimiento con argmax "
                                            f"{'>=' if estado['vigilancia_D3']['cumple'] else '<'} 95 %; la regla de D3 se aplica a la opcion 0.")
    estado["segundos_totales_esta_ejecucion"] = round(time.time() - t_ini, 1)
    save_json(estado_path, estado)
    print(f"\nGuardado: {estado_path}\n{estado['vigilancia_D3']['texto']}")
    return estado_path


if __name__ == "__main__":
    main()
