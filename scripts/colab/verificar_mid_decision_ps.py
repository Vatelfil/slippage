"""Verificación en ABIDES del parche `mid_decision` de R_E (Colab; no entrena; unos 5 minutos).

BORRADOR elaborado por PS con apoyo de Claude Code, para revisión de BF (R_E es de la 2.2.3).

Comprueba dos cosas antes de gastar horas de entrenamiento:

1. Que el precio contra el que se mide R_E en cada paso es el P_mid que vio el agente al decidir. En el paso 1 debe ser el
   precio de entrada, y en el paso k, el P_mid del paso k-1. Esto depende de que ABIDES arme el estado antes que la
   recompensa; si no fuera así, el parche usaría un precio corrido en un paso y aquí se vería.
2. Que la recompensa nueva se relaciona con el slippage que se evalúa. Se corre la misma política aleatoria en las
   mismas semillas con el parche apagado y encendido (la recompensa no cambia el mercado, así que los episodios son
   idénticos) y se compara la correlación entre el retorno del episodio y el slippage.

    PYTHONPATH=. python scripts/colab/verificar_mid_decision_ps.py --out <drive>/rmid_A/verificacion_mid_decision.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.envs.spaces import EjecutorActionSpace  # noqa: E402

TOLERANCIA_CLP = 1e-6


def correr_episodio(factory, semilla: int, mid_decision: bool, tramo: str, q_slice: int, ventana_min: int) -> Dict:
    espacio = EjecutorActionSpace()
    rng = np.random.default_rng(semilla)          # mismas acciones con el parche apagado y encendido
    env = factory(executor_id=tramo, q_slice=q_slice, ventana_min=ventana_min, seed=semilla, mid_decision=mid_decision)
    try:
        _, info = env.reset()
        unidades = float(info.get("unidades_por_clp", 1.0))
        p_llegada = float(info["entry_price"]) / unidades
        retorno, q_tot, notional = 0.0, 0.0, 0.0
        mid_anterior, desfases, pasos, done = p_llegada, [], 0, False
        while not done:
            _, r, done, trunc, info = env.step(espacio.decode_flat(int(rng.integers(espacio.N_FLAT))))
            done = bool(done or trunc)
            pasos += 1
            retorno += float(r)
            if mid_decision:
                desfases.append(abs(float(info["p_ref_precio_clp"]) - mid_anterior))
            mid_anterior = float(info["p_mid_clp"])
            q = float(info.get("q_fill_step", 0.0))
            if q > 0:
                q_tot += q
                notional += q * float(info["p_fill_step_clp"])
    finally:
        env.close()
    slip = (notional / q_tot - p_llegada) / p_llegada * 1e4 if q_tot > 0 else float("nan")
    return {"semilla": semilla, "pasos": pasos, "retorno": retorno, "q_ejecutado": q_tot, "slippage_bps": slip,
            "desfase_max_clp": max(desfases) if desfases else None}


def main(argv: Optional[Sequence[str]] = None) -> Path:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--calibrated-json", default=str(REPO_ROOT / "data/calibration/rmsc04_ipsa_FALABELLA_2026-08-23.json"))
    ap.add_argument("--ticker", default="FALABELLA")
    ap.add_argument("--tramo", default="apertura")
    ap.add_argument("--q-slice", type=int, default=1000)
    ap.add_argument("--ventana-min", type=int, default=15)
    ap.add_argument("--n-semillas", type=int, default=40)
    ap.add_argument("--seed-base", type=int, default=7000, help="semillas distintas de las de entrenamiento y de evaluación")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    from src.envs.abides_ejecutor_env import make_calibrated_env_factory   # requiere ABIDES
    factory = make_calibrated_env_factory(args.calibrated_json, ticker=args.ticker)
    t0 = time.time()
    filas: Dict[str, List[Dict]] = {"antes": [], "despues": []}
    for i in range(1, args.n_semillas + 1):
        s = args.seed_base + i
        filas["antes"].append(correr_episodio(factory, s, False, args.tramo, args.q_slice, args.ventana_min))
        filas["despues"].append(correr_episodio(factory, s, True, args.tramo, args.q_slice, args.ventana_min))
        print(f"semilla {s}: slippage {filas['antes'][-1]['slippage_bps']:.2f} / {filas['despues'][-1]['slippage_bps']:.2f} bps, "
              f"retorno {filas['antes'][-1]['retorno']:.3f} -> {filas['despues'][-1]['retorno']:.3f}", flush=True)

    def corr(lista):
        ok = [f for f in lista if np.isfinite(f["slippage_bps"])]
        return float(np.corrcoef([f["retorno"] for f in ok], [-f["slippage_bps"] for f in ok])[0, 1])

    mismos = all(abs(a["slippage_bps"] - d["slippage_bps"]) < 1e-9 or not np.isfinite(a["slippage_bps"])
                 for a, d in zip(filas["antes"], filas["despues"]))
    desfase = max(f["desfase_max_clp"] or 0.0 for f in filas["despues"])
    res = {
        "n_semillas": args.n_semillas,
        "precio_de_decision_correcto": bool(desfase < TOLERANCIA_CLP),
        "desfase_maximo_clp": desfase,
        "episodios_identicos": bool(mismos),
        "correlacion_retorno_vs_menos_slippage_antes": corr(filas["antes"]),
        "correlacion_retorno_vs_menos_slippage_despues": corr(filas["despues"]),
        "segundos": round(time.time() - t0, 1),
        "episodios": filas,
    }
    res["veredicto"] = ("OK: seguir con los entrenamientos" if res["precio_de_decision_correcto"] and
                        res["correlacion_retorno_vs_menos_slippage_despues"] > res["correlacion_retorno_vs_menos_slippage_antes"]
                        else "PARAR: el parche no se comporta como se esperaba; avisar antes de entrenar")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nPrecio de decision correcto: {res['precio_de_decision_correcto']} (desfase maximo {desfase:.6f} CLP)")
    print(f"Episodios identicos con el parche apagado y encendido: {res['episodios_identicos']}")
    print(f"Correlacion retorno vs costo: antes {res['correlacion_retorno_vs_menos_slippage_antes']:.2f}, "
          f"despues {res['correlacion_retorno_vs_menos_slippage_despues']:.2f}")
    print(res["veredicto"])
    return out


if __name__ == "__main__":
    main()
