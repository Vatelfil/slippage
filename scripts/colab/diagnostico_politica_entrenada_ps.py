"""Diagnostico de la politica entrenada del Ejecutor (tarea 2.3.5) -- corre en Colab con ABIDES.

BORRADOR elaborado por PS con apoyo de Claude Code; pendiente de revision por BF.

Carga un checkpoint de `entrenamiento_inicial_ps.py` y corre pocos episodios de evaluacion, en dos modos:
  - determinista (argmax, el que usa la evaluacion de la 2.3.5),
  - estocastico (muestreo de la politica, el que se usa al entrenar).
Imprime, por paso, la accion decodificada (tipo de orden, bucket de volumen, nivel de precio), lo ejecutado y lo
pendiente, y guarda un resumen con el histograma de acciones y la entropia. Sirve para saber POR QUE una red
entrenada no ejecuta la orden (cumplimiento 0).

    PYTHONPATH=. python scripts/colab/diagnostico_politica_entrenada_ps.py \
        --checkpoint <carpeta_de_drive>/t5_entrenamiento_1000/checkpoints_apertura/checkpoint_last.pt \
        --out-dir <carpeta_de_drive>/t5_entrenamiento_1000 --entorno abides
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.envs.spaces import ORDER_TYPES, EjecutorActionSpace  # noqa: E402
from src.experiments import beta_sweep as bs  # noqa: E402


def _factory(entorno: str, calibrated_json: str, ticker: str):
    if entorno == "abides":
        from src.envs.abides_ejecutor_env import make_calibrated_env_factory  # requiere ABIDES
        return make_calibrated_env_factory(calibrated_json, ticker=ticker)
    from src.envs.fallback_poisson_env import EjecutorEnvPoissonFallback
    return EjecutorEnvPoissonFallback


def _episodio(net, factory, tramo: str, seed: int, q_slice: int, ventana_min: int, determinista: bool, imprimir: bool) -> Dict:
    import torch

    space = EjecutorActionSpace()
    env = factory(executor_id=tramo, q_slice=q_slice, ventana_min=ventana_min, seed=int(seed), beta=0.0)
    acciones, q_total, paso, done = Counter(), 0.0, 0, False
    try:
        obs, _ = env.reset()
        while not done:
            with torch.no_grad():
                logits, _ = net(torch.as_tensor(obs, dtype=torch.float32).unsqueeze(0))
            logits = logits.squeeze(0)
            dist = torch.distributions.Categorical(logits=logits)
            idx = int(torch.argmax(logits).item()) if determinista else int(dist.sample().item())
            a = space.decode_flat(idx)
            obs, _, done, trunc, info = env.step(a)
            done = bool(done or trunc)
            rec = bs.step_record(info)
            q_total += rec["q"]
            acciones[(ORDER_TYPES[int(a[0])], int(a[1]), int(a[2]))] += 1
            paso += 1
            if imprimir:
                print(f"  paso {paso:2d}: {ORDER_TYPES[int(a[0])]:<10} bucket {int(a[1])} nivel {int(a[2])} "
                      f"(p = {float(dist.probs[idx]):.3f}) -> ejecutado {rec['q']:.0f}, pendiente {rec['q_pend']}", flush=True)
    finally:
        env.close()
    return {"seed": int(seed), "pasos": paso, "q_ejecutado": q_total, "cumplimiento": q_total / q_slice,
            "acciones": {f"{k[0]}|bucket{k[1]}|nivel{k[2]}": v for k, v in acciones.most_common()}}


def main(argv: Optional[Sequence[str]] = None) -> Path:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--calibrated-json", default=str(REPO_ROOT / "data/calibration/rmsc04_ipsa_FALABELLA_2026-08-23.json"))
    ap.add_argument("--ticker", default="FALABELLA")
    ap.add_argument("--entorno", choices=["abides", "poisson"], default="abides")
    ap.add_argument("--tramo", default="apertura", choices=["apertura", "media_jornada", "cierre"])
    ap.add_argument("--q-slice", type=int, default=1000)
    ap.add_argument("--ventana-min", type=int, default=15)
    ap.add_argument("--seeds", type=int, nargs="*", default=[5001, 5002, 5003])
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args(argv)

    import torch
    from src.training.ppo_trainer import PPOConfig, PPOTrainer

    trainer = PPOTrainer(role="ejecutor", cfg=PPOConfig(), seed=0)
    trainer.load_checkpoint(args.checkpoint)
    net = trainer.model
    net.eval()
    nan_params = [n for n, p in net.named_parameters() if not torch.isfinite(p).all()]
    print(f"Parametros no finitos: {nan_params or 'ninguno'}")
    factory = _factory(args.entorno, args.calibrated_json, args.ticker)
    resumen: Dict = {"checkpoint": str(args.checkpoint), "episodio_checkpoint": trainer.current_episode,
                     "parametros_no_finitos": nan_params}
    for modo, det in (("determinista", True), ("estocastico", False)):
        print(f"\n== Modo {modo}")
        eps = []
        for s in args.seeds:
            print(f"semilla {s}:")
            eps.append(_episodio(net, factory, args.tramo, s, args.q_slice, args.ventana_min, det, imprimir=True))
        resumen[modo] = {"episodios": eps, "cumplimiento_medio": sum(e["cumplimiento"] for e in eps) / len(eps)}
        print(f"Cumplimiento medio ({modo}): {resumen[modo]['cumplimiento_medio']:.3f}")
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    ruta = out / "diagnostico_politica.json"
    ruta.write_text(json.dumps(resumen, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\nGuardado: {ruta}")
    return ruta


if __name__ == "__main__":
    main()
