"""Aplica los criterios de convergencia de la 2.3.5 a las corridas versionadas (sin Colab).

Elaborado por BF con apoyo de Claude Code. La logica esta en `src/experiments/criterios_2_3_5.py`.

    python scripts/criterios_convergencia_2_3_5.py      # escribe data/analysis/criterios_2.3.5.json

Corrida principal: `t5_1000ep_opcion0` (1000 episodios, opcion 0 de D3). Las demas se informan como comparacion.
Tambien cuenta, con el puente real (`src/envs/abides_bridge.map_action_to_abides_orders`), cuantas de las 240
acciones del Ejecutor no envian ninguna orden a ABIDES.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.experiments import criterios_2_3_5 as cr  # noqa: E402

RES = "data/colab_resultados"
PRINCIPAL = "t5_1000ep_opcion0"
CORRIDAS = {  # etiqueta -> (estado JSON, CSV del entrenador o None, descripcion)
    "t5_1000ep_opcion0": (f"{RES}/t5_1000ep_opcion0.json", f"{RES}/t5_1000ep_opcion0.csv",
                          "1000 episodios, opcion 0 (riesgo sobre lo ejecutado)"),
    "t5_1000ep_opcionA": (f"{RES}/t5_1000ep_opcionA.json", None,
                          "1000 episodios, opcion A (riesgo sobre lo pendiente), exploratoria con el mismo beta"),
    "t5_100ep_opcion0": (f"{RES}/t5_100ep_opcion0.json", f"{RES}/t5_100ep_opcion0.csv",
                         "100 episodios, opcion 0, primera (reanudada desde el episodio 30)"),
    "t5_100ep_opcion0_repeticion": (f"{RES}/t5_100ep_opcion0_repeticion.json", None,
                                    "100 episodios, opcion 0, repeticion sin cortes"),
}
NOMBRES = {
    "sin_nan": "Sin NaN en el CSV",
    "retorno_final_mayor": "Retorno final > inicial (Mann-Whitney unilateral, 10 vs 10 actualizaciones)",
    "kl_mediano_bajo_target": "KL mediano < 0,015",
    "cumplimiento_95": "Cumplimiento medio >= 95 % (argmax, regla de D3)",
    "slippage_vs_twap": "Menos slippage que la TWAP heuristica (Wilcoxon pareado, argmax)",
}


def leer_csv(path: Path) -> List[Dict[str, float]]:
    with open(path, "r", encoding="utf-8-sig") as fh:
        return [{k: float(v) for k, v in fila.items()} for fila in csv.DictReader(fh)]


def _leer(path: Path) -> Dict:
    with open(path, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def acciones_espera() -> Dict:
    from src.envs.abides_bridge import map_action_to_abides_orders
    from src.envs.spaces import ORDER_TYPES, EjecutorActionSpace

    space = EjecutorActionSpace()
    out = cr.contar_acciones_espera(space.decode_flat, map_action_to_abides_orders, space.N_FLAT)
    out["tipos"] = sorted({ORDER_TYPES[int(space.decode_flat(i)[0])] for i in out.pop("indices")})
    out["regla"] = "src/envs/abides_bridge.py:170 (`if size <= 0 or order_type == ORDER_LIMIT_SELL: return []`)"
    return out


def valor(c: Dict) -> str:
    if not c.get("aplicable"):
        return c.get("motivo", "-")
    if "valores_no_finitos" in c:
        return f"{c['valores_no_finitos']} no finitos en {c['n_actualizaciones']} actualizaciones"
    if "U" in c:
        return f"{c['media_inicial']:.3f} -> {c['media_final']:.3f}, U = {c['U']:.0f}, p = {c['p']:.4f}"
    if "mediana" in c:
        return f"mediana {c['mediana']:.6f} (max {c['maximo']:.5f})"
    if "umbral" in c:
        return f"{c['valor']:.3f}"
    return f"dif {c['dif_media_bps']:+.2f} bps (EE {c['ee_bps']:.2f}), p = {c['p_wilcoxon']:.3f}"


def veredicto(c: Dict) -> str:
    return {True: "cumple", False: "no cumple", None: "no evaluable"}[c.get("cumple")]


def main(argv: Optional[Sequence[str]] = None) -> Path:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--salida", default=str(REPO_ROOT / "data/analysis/criterios_2.3.5.json"))
    args = ap.parse_args(argv)
    resultados = {}
    for etiqueta, (js, csv_rel, desc) in CORRIDAS.items():
        estado = _leer(REPO_ROOT / js)
        filas = leer_csv(REPO_ROOT / csv_rel) if csv_rel else None
        r = cr.evaluar_corrida(estado, filas)
        r.update({"descripcion": desc, "estado": js, "csv": csv_rel,
                  "episodios": estado.get("episodios_entrenados"), "riesgo_sobre": estado["firma"].get("riesgo_sobre", "ejecutado")})
        resultados[etiqueta] = r
    diag = _leer(REPO_ROOT / f"{RES}/t5_1000ep_opcion0_diagnostico.json")
    resultados[PRINCIPAL]["informativo"]["parametros_no_finitos_checkpoint"] = diag.get("parametros_no_finitos")
    out = {
        "tarea": "2.3.5",
        "corrida_principal": PRINCIPAL,
        "criterios": {k: v for k, v in NOMBRES.items()},
        "parametros": {"alfa": cr.ALFA, "n_actualizaciones_por_grupo": cr.N_ACTUALIZACIONES, "target_kl": cr.TARGET_KL,
                       "umbral_cumplimiento": cr.UMBRAL_CUMPLIMIENTO, "referencia_twap": cr.REFERENCIA_TWAP},
        "desviaciones": [
            "Mann-Whitney sobre actualizaciones (10 episodios cada una): primeras 10 contra ultimas 10, en vez de "
            "primeros contra ultimos 20 episodios (el CSV no trae el retorno por episodio).",
            "Evaluacion con 15 semillas (5001-5015) en vez de 30.",
        ],
        "acciones_espera": acciones_espera(),
        "corridas": resultados,
    }
    p = Path(args.salida)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for etiqueta, r in resultados.items():
        print(f"\n== {etiqueta}: {r['descripcion']}")
        for k, nombre in NOMBRES.items():
            c = r["criterios"][k]
            print(f"  {nombre:<80} {valor(c):<60} {veredicto(c)}")
    a = out["acciones_espera"]
    print(f"\nAcciones que no envian orden: {a['n_espera']} de {a['n_acciones']} ({100 * a['fraccion']:.1f} %), tipos {a['tipos']}")
    print(f"Guardado: {p}")
    return p


if __name__ == "__main__":
    main()
