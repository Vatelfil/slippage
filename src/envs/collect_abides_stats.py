"""Recolecta estadisticas del LOB simulado por ABIDES-Gym (spread, OBI, volumen)
corriendo varios episodios del Ejecutor, para completar la tarea 2.2.5
(validacion estadistica: simulador vs datos reales).

*** CORRE SOLO DONDE ABIDES-GYM ESTE INSTALADO *** (Colab con condacolab, ver
DIAGNOSTICO_COLAB_MAURICIO_29SEP.md). No se pudo ejecutar donde se escribio
este script -- solo se verifico la sintaxis y que importa correctamente.

Uso (en Colab, dentro de la carpeta del repo clonado):
    !conda run -n abides bash -c "cd /content/slippage && PYTHONPATH=. python src/envs/collect_abides_stats.py"

Produce: data/analysis/perfil_mercado_abides_simulado.json, con el mismo
formato de agregacion (por tramo horario) que
src/analysis/market_validation.py usa para los datos reales -- para poder
compararlos directo con `compare_simulated_vs_real()`.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from src.envs.abides_ejecutor_env import EjecutorEnvAbides

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = REPO_ROOT / "data" / "analysis" / "perfil_mercado_abides_simulado.json"

TRAMOS = ("apertura", "media_jornada", "cierre")
N_EPISODIOS_POR_TRAMO = 10  # subir si el tiempo de computo lo permite (cierre es el mas lento, ver nota en abides_ejecutor_env.py)
Q_SLICE = 500
VENTANA_MIN = 10
P_REFERENCIA = 5800.0  # precio de ejemplo (ver limitaciones: rmsc04 no esta calibrado al IPSA todavia, tarea 2.2.4)


def _random_policy_action(rng: np.random.Generator) -> np.ndarray:
    """Politica aleatoria de ejemplo -- NO es la politica entrenada (esa es
    tarea de Mauricio, PPO). Sirve solo para generar trafico de ordenes
    variado y medir como reacciona el LOB simulado, no para evaluar calidad
    de ejecucion."""
    return np.array([rng.integers(0, 3), rng.integers(0, 10), rng.integers(0, 8)])


def collect_tramo_stats(tramo: str, n_episodios: int, seed_base: int = 0) -> dict:
    spreads, obis, p_mids = [], [], []

    for ep in range(n_episodios):
        env = EjecutorEnvAbides(executor_id=tramo, q_slice=Q_SLICE, ventana_min=VENTANA_MIN,
                                 seed=seed_base + ep)
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
        env.close()

    return {
        "tramo": tramo,
        "n_episodios": n_episodios,
        "spread_mean": float(np.mean(spreads)) if spreads else None,
        "spread_std": float(np.std(spreads)) if spreads else None,
        "obi_mean": float(np.mean(obis)) if obis else None,
        "obi_std": float(np.std(obis)) if obis else None,
        "p_mid_mean": float(np.mean(p_mids)) if p_mids else None,
        "n_observaciones": len(spreads),
    }


def main():
    print("Recolectando estadisticas del LOB simulado (ABIDES-Gym real)...")
    print("NOTA: valores normalizados [0,1] (ver BridgeConfig en abides_bridge.py),")
    print("no directamente comparables en unidades absolutas con los datos reales")
    print("hasta que rmsc04 este calibrado al IPSA (tarea 2.2.4, Benjamin).\n")

    resultado = {"metadata": {"q_slice": Q_SLICE, "ventana_min": VENTANA_MIN,
                               "p_referencia": P_REFERENCIA, "n_episodios_por_tramo": N_EPISODIOS_POR_TRAMO},
                 "por_tramo": {}}

    for tramo in TRAMOS:
        print(f"Tramo: {tramo}...")
        stats = collect_tramo_stats(tramo, N_EPISODIOS_POR_TRAMO)
        resultado["por_tramo"][tramo] = stats
        print(f"  spread_mean={stats['spread_mean']:.4f}  obi_mean={stats['obi_mean']:.4f}  "
              f"n_obs={stats['n_observaciones']}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2)
    print(f"\nGuardado: {OUTPUT_PATH}")
    print("Siguiente paso: correr compare_simulated_vs_real() en src/analysis/market_validation.py")


if __name__ == "__main__":
    main()
