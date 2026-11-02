"""Entrena el Maestro en Poisson y lo compara con el mismo Maestro sin entrenar (BORRADOR de PS para MR, 29 oct 2026).

    PYTHONPATH=. python scripts/entrenar_maestro.py --jornadas 400 --out-dir data/maestro/sin_impacto
    PYTHONPATH=. python scripts/entrenar_maestro.py --jornadas 400 --impacto --out-dir data/maestro/con_impacto

Reanudable: si existe `checkpoint_last.pt` en la carpeta, sigue desde ahí. Guarda el CSV de entrenamiento de
`PPOTrainer` (`entrenamiento_maestro.csv`), el checkpoint y `resumen_maestro.json` con la evaluación del Maestro sin
entrenar y del entrenado en las mismas semillas de evaluación (los Ejecutores son siempre los mismos, fijos).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.envs.impacto_acumulado import parametros_para, resumen as resumen_impacto  # noqa: E402
from src.training import maestro_trainer as mt  # noqa: E402

VOLUMEN_DIA_FALABELLA = 882768     # volumen_dia_simulado de MO-01 (meta_ordenes_v2_candidata.json)


def _agregar(evals: List[Dict]) -> Dict[str, float]:
    out = {}
    for k in ("R_M_bps", "cumplimiento", "slippage_bps", "alpha_idx_medio", "ventana_idx_medio"):
        v = np.array([e[k] for e in evals], dtype=float)
        v = v[np.isfinite(v)]
        out[k] = float(v.mean()) if len(v) else float("nan")
        out[k + "_ee"] = float(v.std(ddof=1) / np.sqrt(len(v))) if len(v) > 1 else float("nan")
    return out


def diferencia_pareada(a: List[Dict], b: List[Dict], clave: str = "R_M_bps", n_boot: int = 3000) -> Dict[str, float]:
    d = np.array([x[clave] - y[clave] for x, y in zip(a, b)], dtype=float)
    medias = np.random.default_rng(0).choice(d, size=(n_boot, len(d)), replace=True).mean(axis=1)
    return {"media": float(d.mean()), "ic_bajo": float(np.percentile(medias, 2.5)), "ic_alto": float(np.percentile(medias, 97.5)),
            "n": int(len(d))}


def main(argv: Optional[Sequence[str]] = None) -> Path:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--jornadas", type=int, default=400)
    ap.add_argument("--q-total", type=int, default=30000)
    ap.add_argument("--ticker", default="FALABELLA")
    ap.add_argument("--impacto", action="store_true", help="impacto acumulado entre ventanas (src/envs/impacto_acumulado.py)")
    ap.add_argument("--impacto-y", type=float, default=0.5)
    ap.add_argument("--impacto-tau", type=float, default=120.0)
    ap.add_argument("--volumen-dia", type=float, default=VOLUMEN_DIA_FALABELLA)
    ap.add_argument("--lambda-penalty", type=float, default=None)
    ap.add_argument("--seed", type=int, default=1000)
    ap.add_argument("--eval-semillas", type=int, default=30)
    ap.add_argument("--eval-seed-base", type=int, default=90000, help="aparte de las de entrenamiento (20.000 + jornada)")
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--seed-red-ejecutores", type=int, default=1000, help="pesos de los Ejecutores fijos (sin entrenar)")
    ap.add_argument("--inicio-aleatorio", action="store_true",
                    help="cada jornada parte en apertura, media jornada o cierre (como las meta-ordenes de evaluacion)")
    ap.add_argument("--ckpt-ejecutor", default=None,
                    help="checkpoint de un Ejecutor entrenado (PPOTrainer) para los tres tramos; sin esto, Ejecutores sin entrenar")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args(argv)

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    impacto = (parametros_para(args.ticker, args.volumen_dia, y=args.impacto_y, tau_min=args.impacto_tau)
               if args.impacto else None)
    redes = mt.redes_ejecutores(args.seed_red_ejecutores)
    if args.ckpt_ejecutor:   # el mismo Ejecutor entrenado en los tres tramos (solo hay redes entrenadas en apertura)
        import torch
        try:   # torch >= 2.6 pide weights_only para objetos que no son tensores; 1.13 (Colab) no conoce el argumento
            ck = torch.load(args.ckpt_ejecutor, map_location="cpu", weights_only=False)
        except TypeError:
            ck = torch.load(args.ckpt_ejecutor, map_location="cpu")
        for red in redes.values():
            red.load_state_dict(ck.get("model_state_dict", ck.get("model", ck)))
    mt.guardar_ejecutores(redes, out)            # para evaluar en ABIDES con los mismos Ejecutores
    cfg = mt.ConfigJornada(q_total=args.q_total, ticker=args.ticker, lambda_penalty=args.lambda_penalty, impacto=impacto,
                           executor_policy_fn=mt.politica_ejecutores(redes), inicio_aleatorio=args.inicio_aleatorio)
    semillas = [args.eval_seed_base + i for i in range(1, args.eval_semillas + 1)]
    resumen_path = out / "resumen_maestro.json"
    resumen = json.loads(resumen_path.read_text(encoding="utf-8")) if resumen_path.exists() else {}

    t0 = time.time()
    if "sin_entrenar" not in resumen:
        evs = mt.evaluar_maestro(mt.nuevo_trainer(args.seed, lr=args.lr), cfg, semillas)
        resumen["sin_entrenar"] = {"agregado": _agregar(evs), "jornadas": evs}
        resumen_path.write_text(json.dumps(resumen, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"Sin entrenar: {resumen['sin_entrenar']['agregado']}", flush=True)

    tr = mt.nuevo_trainer(args.seed, lr=args.lr)
    ckpt = out / "checkpoint_last.pt"
    if ckpt.exists():
        tr.load_checkpoint(ckpt)
        print(f"Reanudando desde la jornada {tr.current_episode}", flush=True)
    faltan = args.jornadas - tr.current_episode
    if faltan > 0:
        mt.train_maestro_episodes(tr, cfg, faltan, csv_path=out / "entrenamiento_maestro.csv", checkpoint_dir=out)

    evs = mt.evaluar_maestro(tr, cfg, semillas)
    resumen["entrenado"] = {"agregado": _agregar(evs), "jornadas": evs, "episodios": tr.current_episode}
    resumen["entrenado_menos_sin_entrenar_R_M_bps"] = diferencia_pareada(evs, resumen["sin_entrenar"]["jornadas"])
    resumen["entrenado_menos_sin_entrenar_slippage_bps"] = diferencia_pareada(evs, resumen["sin_entrenar"]["jornadas"], "slippage_bps")
    resumen["config"] = {"inicio_aleatorio": args.inicio_aleatorio, "ckpt_ejecutor": args.ckpt_ejecutor, "q_total": args.q_total, "ticker": args.ticker, "impacto": resumen_impacto(impacto),
                         "lambda_penalty": args.lambda_penalty, "seed": args.seed, "lr": args.lr,
                         "eval_semillas": semillas, "segundos_esta_ejecucion": round(time.time() - t0, 1)}
    resumen_path.write_text(json.dumps(resumen, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Entrenado: {resumen['entrenado']['agregado']}")
    print(f"Entrenado - sin entrenar (R_M en bps, mayor es mejor): {resumen['entrenado_menos_sin_entrenar_R_M_bps']}")
    return resumen_path


if __name__ == "__main__":
    main()
