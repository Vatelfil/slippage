"""Evidencia con ABIDES de T1 (protocolo CTDE) y T2 (entrenador PPO) -- corre en Colab.

Borrador elaborado por PS con apoyo de Claude Code; pendiente de revision por MR.
Cubre dos puntos de la revision cruzada de PS (Sprint 5):
  A) T1: una ventana del Ejecutor con ABIDES intercambiando solo mensajes ASIGNAR/REPORTE
     validos; guarda el log del canal (plan: "aunque sea una ventana").
  B) T2: corrida corta del entrenador PPO sobre ABIDES calibrado (sin NaN, CSV, checkpoint
     y reanudacion), para detectar problemas de integracion antes de la tarea 2.3.5.

Uso (Colab, entorno `abides` listo y torch instalado):
    PYTHONPATH=. python scripts/colab/evidencia_ctde_ppo_abides_ps.py \
        --calibrated-json data/calibration/rmsc04_ipsa_FALABELLA_2026-08-23.json \
        --out-dir <carpeta_de_drive>/evidencia_mr

`--entorno poisson` corre lo mismo con el simulador de Poisson (ensayo local, sin ABIDES).
Salida en --out-dir: ctde_log_ventana_<entorno>.json, entrenamiento_<entorno>.csv,
checkpoints/ y resumen_evidencia_<entorno>.json (con los numeros para documentar).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _factory(entorno: str, calibrated_json: str, ticker: str):
    if entorno == "abides":
        from src.envs.abides_ejecutor_env import make_calibrated_env_factory  # requiere ABIDES
        return make_calibrated_env_factory(calibrated_json, ticker=ticker)
    from src.envs.fallback_poisson_env import EjecutorEnvPoissonFallback
    return EjecutorEnvPoissonFallback


def parte_a_log_ctde(factory, out_dir: Path, entorno: str, alpha_idx: int, ventana_idx: int, q_total: int) -> dict:
    """Una decision del Maestro = una ventana del Ejecutor, solo con mensajes del canal."""
    from src.envs.ctde_protocol import validar_mensaje_asignar, validar_mensaje_reporte
    from src.envs.maestro_ejecutor_protocol import ALPHA_VALUES, VENTANA_MIN_VALUES, MaestroEjecutorEnv

    t0 = time.time()
    env = MaestroEjecutorEnv(meta_orden_quantity=q_total, executor_env_factory=factory)
    env.reset()
    _, r_m, done, info = env.step((alpha_idx, ventana_idx))
    env.close()
    hist = env.canal.obtener_historial()
    for entrada in hist:
        payload = entrada["payload"]
        if entrada["direccion"] == "Maestro -> Ejecutor":
            validar_mensaje_asignar(payload)
        else:
            validar_mensaje_reporte(payload)
    ruta = out_dir / f"ctde_log_ventana_{entorno}.json"
    env.canal.guardar_log(ruta)
    rep = info["executor_report"]
    return {
        "mensajes": len(hist), "asignar": sum(h["direccion"] == "Maestro -> Ejecutor" for h in hist),
        "reporte": sum(h["direccion"] != "Maestro -> Ejecutor" for h in hist),
        "todos_validos": True, "alpha": ALPHA_VALUES[alpha_idx], "ventana_min": VENTANA_MIN_VALUES[ventana_idx],
        "q_total": q_total, "q_ejecutado": float(rep.get("q_ejecutado", float("nan"))),
        "jornada_terminada": bool(done), "log": ruta.name, "segundos": round(time.time() - t0, 1),
    }


def _sin_nan(historial) -> bool:
    return all(math.isfinite(v) for h in historial for v in h.values() if isinstance(v, float))


def parte_b_entrenador(factory, out_dir: Path, entorno: str, n_episodios: int, q_slice: int, ventana_min: int) -> dict:
    """Entrena unos episodios, comprueba CSV y checkpoint y reanuda un episodio mas."""
    import csv

    from src.training.ppo_trainer import PPOConfig, PPOTrainer

    csv_path = out_dir / f"entrenamiento_{entorno}.csv"
    ckpt_dir = out_dir / "checkpoints"
    if csv_path.exists():
        csv_path.unlink()
    cfg = PPOConfig(epochs=2, minibatch_size=32, episodes_per_update=2)
    t0 = time.time()
    trainer = PPOTrainer(role="ejecutor", cfg=cfg, seed=42)
    hist = trainer.train_executor_episodes(env_factory=factory, n_episodes=n_episodios, tramo="apertura",
                                           q_slice=q_slice, ventana_min=ventana_min, csv_path=csv_path,
                                           checkpoint_dir=ckpt_dir, checkpoint_freq=1)
    seg_train = round(time.time() - t0, 1)
    with open(csv_path, "r", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    columnas_ok = set(filas[0].keys()) == set(PPOTrainer.CSV_HEADER) if filas else False
    ckpt = ckpt_dir / "checkpoint_last.pt"
    reanuda = PPOTrainer(role="ejecutor", cfg=cfg, seed=42)
    info_ck = reanuda.load_checkpoint(ckpt)
    ep_antes = reanuda.current_episode
    t1 = time.time()
    hist2 = reanuda.train_executor_episodes(env_factory=factory, n_episodes=2, tramo="apertura", q_slice=q_slice,
                                            ventana_min=ventana_min, csv_path=csv_path)
    return {
        "episodios": n_episodios, "actualizaciones": len(hist), "sin_nan": _sin_nan(hist) and _sin_nan(hist2),
        "filas_csv_tras_reanudar": len(list(csv.DictReader(open(csv_path, "r", encoding="utf-8")))),
        "columnas_csv_ok": columnas_ok, "checkpoint_existe": ckpt.exists(),
        "reanudo_en_episodio": ep_antes + 1, "episodio_final_tras_reanudar": reanuda.current_episode,
        "claves_checkpoint": sorted(info_ck.keys()), "segundos_entrenar": seg_train,
        "segundos_reanudar": round(time.time() - t1, 1),
        "ultimo_retorno_medio": hist2[-1]["reward_mean"] if hist2 else None,
    }


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--calibrated-json", default=str(REPO_ROOT / "data/calibration/rmsc04_ipsa_FALABELLA_2026-08-23.json"))
    ap.add_argument("--ticker", default="FALABELLA")
    ap.add_argument("--entorno", choices=["abides", "poisson"], default="abides")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--episodios", type=int, default=4, help="episodios de la parte B (par: se actualiza cada 2)")
    ap.add_argument("--q-slice", type=int, default=1000)
    ap.add_argument("--ventana-min", type=int, default=5)
    ap.add_argument("--q-total", type=int, default=10_000, help="meta-orden de la parte A")
    ap.add_argument("--alpha-idx", type=int, default=1, help="indice en ALPHA_VALUES (1 = 10 %%)")
    ap.add_argument("--ventana-idx", type=int, default=1, help="indice en VENTANA_MIN_VALUES (1 = 5 min)")
    args = ap.parse_args(argv)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    factory = _factory(args.entorno, args.calibrated_json, args.ticker)
    resumen = {"entorno": args.entorno, "calibrated_json": Path(args.calibrated_json).name, "ticker": args.ticker}

    print(f"== Parte A: una ventana CTDE ({args.entorno})")
    resumen["parte_a_t1"] = parte_a_log_ctde(factory, out_dir, args.entorno, args.alpha_idx, args.ventana_idx, args.q_total)
    print("  ", resumen["parte_a_t1"])

    print(f"== Parte B: entrenador PPO ({args.entorno}), {args.episodios} episodios + reanudar 2")
    resumen["parte_b_t2"] = parte_b_entrenador(factory, out_dir, args.entorno, args.episodios, args.q_slice, args.ventana_min)
    print("  ", resumen["parte_b_t2"])

    a, b = resumen["parte_a_t1"], resumen["parte_b_t2"]
    ok = (a["todos_validos"] and a["mensajes"] >= 2 and b["sin_nan"] and b["columnas_csv_ok"] and b["checkpoint_existe"]
          and b["episodio_final_tras_reanudar"] == b["reanudo_en_episodio"] + 1)
    resumen["resultado"] = "OK" if ok else "REVISAR"
    ruta = out_dir / f"resumen_evidencia_{args.entorno}.json"
    ruta.write_text(json.dumps(resumen, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"\n== RESULTADO: {resumen['resultado']}  (guardado en {ruta})")


if __name__ == "__main__":
    main()
