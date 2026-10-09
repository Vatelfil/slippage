"""Recolecta estadisticas del LOB simulado por ABIDES-Gym (spread, OBI, volumen)
corriendo varios episodios del Ejecutor, para completar la tarea 2.2.5
(validacion estadistica: simulador vs datos reales).

*** CORRE SOLO DONDE ABIDES-GYM ESTE INSTALADO *** (Colab con condacolab, ver
DIAGNOSTICO_COLAB_MAURICIO_29SEP.md).

Uso (en Colab, dentro de la carpeta del repo clonado):

    # rmsc04 sin calibrar (linea base de PS, 2.2.5)
    PYTHONPATH=. python src/envs/collect_abides_stats.py

    # rmsc04 calibrado al IPSA (2.2.4, BF): antes/despues de la 2.2.5
    PYTHONPATH=. python src/envs/collect_abides_stats.py \
        --calibrated-json <dir>/rmsc04_ipsa_FALABELLA_2026-08-23.json --out-dir <dir>

Produce `perfil_mercado_abides_simulado.json` (sin calibrar) o
`perfil_mercado_abides_calibrado.json` (con `--calibrated-json`), con el
formato de agregacion por tramo que lee `compare_simulated_vs_real()` de
src/analysis/market_validation.py. Ademas del spread normalizado [0,1] de
S_E se reporta el spread cotizado en bps (`spread_bps_*`), comparable en
magnitud con los proxies reales.

Reanudable: el JSON se guarda al terminar cada tramo y los tramos ya
guardados se saltan (usar `--overwrite` para recalcular).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT_DIR = REPO_ROOT / "data" / "analysis"
OUTPUT_NAME = "perfil_mercado_abides_simulado.json"
OUTPUT_NAME_CALIBRADO = "perfil_mercado_abides_calibrado.json"
OUTPUT_PATH = DEFAULT_OUT_DIR / OUTPUT_NAME  # compatibilidad con el uso original

TRAMOS = ("apertura", "media_jornada", "cierre")
N_EPISODIOS_POR_TRAMO = 10  # subir si el tiempo de computo lo permite (cierre es el mas lento, ver nota en abides_ejecutor_env.py)
Q_SLICE = 500
VENTANA_MIN = 10
P_REFERENCIA = 5800.0  # precio de ejemplo, solo informativo en metadata


def _random_policy_action(rng: np.random.Generator) -> np.ndarray:
    """Politica aleatoria de ejemplo -- NO es la politica entrenada (esa es
    tarea de Mauricio, PPO). Sirve solo para generar trafico de ordenes
    variado y medir como reacciona el LOB simulado, no para evaluar calidad
    de ejecucion."""
    return np.array([rng.integers(0, 3), rng.integers(0, 10), rng.integers(0, 8)])


def quoted_spread_bps(best_bid: Optional[float], best_ask: Optional[float]) -> Optional[float]:
    """Spread cotizado relativo en bps; None si falta un lado del libro (el
    entorno informa bid = ask = mid en ese caso)."""
    if best_bid is None or best_ask is None or not best_ask > best_bid > 0:
        return None
    return float((best_ask - best_bid) / ((best_ask + best_bid) / 2.0) * 1e4)


def summarize_tramo(tramo: str, n_episodios: int, spreads: Sequence[float], obis: Sequence[float],
                    p_mids: Sequence[float], spreads_bps: Sequence[float]) -> Dict:
    """Agrega las observaciones de un tramo. Las llaves originales
    (`spread_mean`, `obi_mean`, `n_observaciones`, ...) no cambian; las
    `spread_bps_*` son nuevas."""
    return {
        "tramo": tramo,
        "n_episodios": n_episodios,
        "spread_mean": float(np.mean(spreads)) if len(spreads) else None,
        "spread_std": float(np.std(spreads)) if len(spreads) else None,
        "obi_mean": float(np.mean(obis)) if len(obis) else None,
        "obi_std": float(np.std(obis)) if len(obis) else None,
        "p_mid_mean": float(np.mean(p_mids)) if len(p_mids) else None,
        "n_observaciones": len(spreads),
        "spread_bps_mean": float(np.mean(spreads_bps)) if len(spreads_bps) else None,
        "spread_bps_median": float(np.median(spreads_bps)) if len(spreads_bps) else None,
        "spread_bps_std": float(np.std(spreads_bps)) if len(spreads_bps) else None,
        "n_observaciones_spread_bps": len(spreads_bps),
    }


def collect_tramo_stats(tramo: str, n_episodios: int, seed_base: int = 0,
                        abides_kwargs: Optional[Dict] = None) -> dict:
    """Corre `n_episodios` del Ejecutor en `tramo`. `abides_kwargs` (salida de
    `to_abides_kwargs`) se pasa a rmsc04 via `background_config_extra_kvargs`;
    None = rmsc04 sin calibrar."""
    from src.envs.abides_ejecutor_env import EjecutorEnvAbides  # requiere ABIDES

    spreads: List[float] = []
    obis: List[float] = []
    p_mids: List[float] = []
    spreads_bps: List[float] = []
    extra = {"background_config_extra_kvargs": dict(abides_kwargs)} if abides_kwargs else {}

    for ep in range(n_episodios):
        env = EjecutorEnvAbides(executor_id=tramo, q_slice=Q_SLICE, ventana_min=VENTANA_MIN,
                                 seed=seed_base + ep, **extra)
        rng = np.random.default_rng(seed_base + ep)
        obs, info = env.reset()
        done = False
        while not done:
            action = _random_policy_action(rng)
            obs, reward, done, truncated, info = env.step(action)
            done = done or truncated
            # obs, en el orden de SE_schema.json: indice 23=spread_t, 24=OBI_t, 26=P_mid (normalizados [0,1]/[-1,1])
            spreads.append(float(obs[23]))
            obis.append(float(obs[24]))
            p_mids.append(float(obs[26]))
            s_bps = quoted_spread_bps(info.get("best_bid"), info.get("best_ask"))
            if s_bps is not None:
                spreads_bps.append(s_bps)
        env.close()

    return summarize_tramo(tramo, n_episodios, spreads, obis, p_mids, spreads_bps)


def load_partial(path: Path, metadata: Dict) -> Dict:
    """Resultado parcial previo si existe y fue generado con la misma
    configuracion; si no, un resultado vacio."""
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            prev = json.load(f)
        if prev.get("metadata") == metadata:
            return prev
    return {"metadata": metadata, "por_tramo": {}}


def main(argv: Optional[Sequence[str]] = None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--calibrated-json", default=None,
                    help="JSON de la 2.2.4 con `por_tramo[tramo].abides_kwargs` "
                         "(rmsc04_ipsa_<ticker>_<snapshot>.json o rmsc04_base_*.json)")
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    ap.add_argument("--episodes", type=int, default=N_EPISODIOS_POR_TRAMO)
    ap.add_argument("--seed-base", type=int, default=0)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args(argv)

    kwargs_por_tramo: Dict[str, Optional[Dict]] = {t: None for t in TRAMOS}
    metadata = {"q_slice": Q_SLICE, "ventana_min": VENTANA_MIN,
                "p_referencia": P_REFERENCIA, "n_episodios_por_tramo": args.episodes}
    name = OUTPUT_NAME
    if args.calibrated_json:
        from src.envs.calibrate_rmsc04_ipsa import load_abides_kwargs

        kwargs_por_tramo = load_abides_kwargs(args.calibrated_json)
        metadata.update({"calibrated_json": Path(args.calibrated_json).name,
                         "abides_kwargs": kwargs_por_tramo, "seed_base": args.seed_base})
        name = OUTPUT_NAME_CALIBRADO

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / name
    resultado = {"metadata": metadata, "por_tramo": {}} if args.overwrite else load_partial(out_path, metadata)

    print("Recolectando estadisticas del LOB simulado (ABIDES-Gym real)...")
    print("spread_mean esta normalizado [0,1] (BridgeConfig); spread_bps_* es el spread cotizado en bps.\n")
    for tramo in TRAMOS:
        if tramo in resultado["por_tramo"]:
            print(f"Tramo: {tramo}... ya guardado, se salta")
            continue
        print(f"Tramo: {tramo}...")
        stats = collect_tramo_stats(tramo, args.episodes, seed_base=args.seed_base,
                                    abides_kwargs=kwargs_por_tramo[tramo])
        resultado["por_tramo"][tramo] = stats
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(resultado, f, indent=2)
        bps = stats["spread_bps_median"]
        print(f"  spread_mean={stats['spread_mean']:.4f}  "
              f"spread_bps_mediano={'nan' if bps is None else format(bps, '.2f')}  "
              f"obi_mean={stats['obi_mean']:.4f}  n_obs={stats['n_observaciones']}")

    print(f"\nGuardado: {out_path}")
    print("Siguiente paso: correr compare_simulated_vs_real() en src/analysis/market_validation.py")


if __name__ == "__main__":
    main()
