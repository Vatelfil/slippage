"""Maestro (sin entrenar y entrenado) frente a TWAP y VWAP en Poisson, pareado por semilla (BORRADOR de PS para MR).

Las jornadas de evaluación de `scripts/entrenar_maestro.py` usan, para la ventana k de la jornada con semilla s, la
semilla de mercado s · 1000 + k. Los benchmarks usan la misma regla para el periodo k (`run_benchmark_episode`), así
que cada jornada del Maestro tiene su TWAP y su VWAP en el mismo mercado. Se compara el IS en bps de la orden completa
(slippage × cumplimiento), con IC 95 % por bootstrap.

    PYTHONPATH=. python scripts/comparar_maestro_vs_twap_ps.py --resumen data/maestro/primer_entrenamiento_29oct/con_impacto/resumen_maestro.json --impacto
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.analysis.benchmarks import run_benchmark_episode, schedule_desde  # noqa: E402
from src.analysis.execution_metrics import evaluate_episode  # noqa: E402
from src.envs.impacto_acumulado import con_impacto, fabrica_poisson, parametros_para  # noqa: E402

VOLUMEN_DIA_FALABELLA = 882768


def comparar(resumen: Dict, impacto: bool, volumen_dia: float, ticker: str = "FALABELLA") -> List[Dict]:
    perfil = pd.read_csv(REPO_ROOT / "data/meta_ordenes/perfil_volumen_v1.csv", index_col=0)
    if resumen["config"].get("inicio_aleatorio"):
        raise SystemExit("Esta comparacion supone jornadas desde las 09:30; con --inicio-aleatorio usar el evaluador del sistema.")
    q_total = float(resumen["config"]["q_total"])
    filas = []
    for politica in ("sin_entrenar", "entrenado"):
        jornadas = resumen[politica]["jornadas"]
        for est in ("TWAP", "VWAP"):
            d, cum_b = [], []
            for j in jornadas:
                fab = fabrica_poisson(ticker)
                if impacto:
                    fab = con_impacto(fab, parametros_para(ticker, volumen_dia))
                r = run_benchmark_episode(schedule_desde(est, q_total, 0, perfil), seed=int(j["semilla"]), ticker=ticker,
                                          env_factory=fab)
                m = evaluate_episode(q_total=r.q_total, q_executed=r.q_executed, p_referencia=r.p_referencia,
                                     p_promedio_ejecutado=r.p_promedio_ejecutado)
                d.append(j["slippage_bps"] * j["cumplimiento"] - m["slippage_bps"] * m["execution_rate"])
                cum_b.append(m["execution_rate"])
            d = np.array(d)
            boot = np.random.default_rng(0).choice(d, size=(3000, len(d))).mean(axis=1)
            filas.append({"maestro": politica, "referencia": est, "dif_IS_bps": float(d.mean()),
                          "ic_bajo": float(np.percentile(boot, 2.5)), "ic_alto": float(np.percentile(boot, 97.5)),
                          "cumplimiento_maestro": float(np.mean([j["cumplimiento"] for j in jornadas])),
                          "cumplimiento_referencia": float(np.mean(cum_b)), "n": int(len(d))})
    return filas


def main(argv: Optional[Sequence[str]] = None) -> List[Dict]:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--resumen", required=True)
    ap.add_argument("--impacto", action="store_true")
    ap.add_argument("--volumen-dia", type=float, default=VOLUMEN_DIA_FALABELLA)
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    resumen = json.loads(Path(args.resumen).read_text(encoding="utf-8"))
    filas = comparar(resumen, args.impacto, args.volumen_dia)
    for f in filas:
        print(f"Maestro {f['maestro']:12s} - {f['referencia']}: {f['dif_IS_bps']:+.2f} bps [{f['ic_bajo']:+.2f}; {f['ic_alto']:+.2f}]"
              f"  cumplimiento {f['cumplimiento_maestro']:.4f} / {f['cumplimiento_referencia']:.4f}")
    if args.out:
        Path(args.out).write_text(json.dumps(filas, indent=1, ensure_ascii=False), encoding="utf-8")
    return filas


if __name__ == "__main__":
    main()
