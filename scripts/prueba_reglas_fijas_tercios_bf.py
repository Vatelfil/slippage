"""Prueba de viabilidad del reentrenamiento del Maestro (tarea B de BF, 11 nov 2026).

Pregunta: ¿la mejor regla fija «compra α de lo que falta cada 30 min» cambia entre días de actividad baja y alta?
Si no cambia, ningún Maestro puede ganar adaptándose al tipo de día, y no se reentrena.

- **Mercado:** Poisson con la calibración por tercios (`data/calibration/poisson_tercios/`, BF) e impacto acumulado
  con la σ y el volumen diario mediano del mismo tercio (y = 0,5, τ = 120 min).
- **Órdenes:** las 10 de `meta_ordenes_v2_candidata.json`, con su tamaño en acciones: la misma orden pesa más en un
  día flojo, como en la realidad.
- **Ejecutores:** los del sistema final (`sistema_final/maestro/ejecutor_*.pt`), en modo muestreo como en las 90.
- **Reglas:** α ∈ {10, 20, 30, 40, 50 %} con la ventana de 15 min (la que eligen los dos Maestros) y corrección del
  cierre. Las cinco reglas ven el mismo mercado en cada orden y semilla (pareo).

El criterio está en `CRITERIO` y se fijó antes de correr. Reutiliza sin modificarlos `_factory_pareada`,
`_Acumulador`, `datos_desde` y `cargar_redes` de `scripts/colab/evaluar_sistema_ps.py` (PS).

    python scripts/prueba_reglas_fijas_tercios_bf.py --ckpt-dir <carpeta con ejecutor_*.pt>
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence

import torch  # noqa: F401  # antes que pandas: en Windows, torch después de pandas falla al cargar c10.dll (WinError 1114)
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

CRITERIO = {
    "fecha": "2026-11-11",
    "alfa_idx": [1, 3, 5, 7, 9],          # 10, 20, 30, 40 y 50 % de lo que falta (ALPHA_VALUES)
    "ventana_idx": 3,                      # 15 min (VENTANA_MIN_VALUES)
    "tercios": ["bajo", "medio", "alto"],
    "semillas": list(range(101, 111)),     # 10 por orden; se suman a la semilla de cada orden (9010 ... 9100)
    "impacto": {"y": 0.5, "tau_min": 120.0},
    "completar_al_cierre": True,
    "modo_ejecutores": "muestreo",
    "n_boot": 3000, "semilla_boot": 0, "nivel": 0.95,
    "cumplimiento_min": 0.95,              # una corrida «completa» la orden si ejecuta al menos el 95 %
    "fraccion_completas_min": 0.95,        # una regla es admisible en un tercio si al menos el 95 % de sus corridas completa
    "regla": ("SIGUE (vale la pena reentrenar) si la mejor α admisible del tercio bajo y la del alto son distintas y, en "
              "CADA uno de esos dos tercios, la α óptima del otro es peor que la propia: o no es admisible ahí, o cuesta "
              "más (diferencia pareada por orden y semilla con IC 95 % bootstrap cuyo límite inferior es > 0). Si no, SE "
              "DETIENE: una sola regla fija sirve para los dos tipos de día. El tercio medio se informa, pero no decide."),
    "cambio_declarado": ("11 nov, antes de la corrida completa y después de una prueba de 30 corridas: la versión "
                         "inicial comparaba solo el slippage, y con α bajo la orden no se completa (MO-08 al 83 %), así "
                         "que dejar saldo parecía barato. BF eligió exigir que la regla complete (requisito de cumplimiento "
                         "del plan de análisis de la 3.2.3) en lugar del costo ajustado de +30 bps."),
}
NO_EVALUABLE = "NO EVALUABLE"
SIGUE, SE_DETIENE = "SIGUE", "SE DETIENE"
DIR_TERCIOS = REPO_ROOT / "data/calibration/poisson_tercios"
META_ORDENES = REPO_ROOT / "data/meta_ordenes/meta_ordenes_v2_candidata.json"
OUT_DIR = REPO_ROOT / "data/analysis/reglas_fijas_tercios_BF"


# ---------------------------------------------------------------------------
# Mercado de un tercio
# ---------------------------------------------------------------------------

def ruta_tercio(tercio: str) -> Path:
    return DIR_TERCIOS / f"poisson_tercio_{tercio}.json"


def fabrica_tercio(ticker: str, tercio: str) -> Callable:
    """Ejecutor de Poisson con los parámetros del tercio (mismo entorno de la 2.1.4; solo cambia la calibración)."""
    from src.envs.fallback_poisson_env import EjecutorEnvPoissonFallback
    from src.envs.poisson_lob_simulator import PoissonLOBSimulator
    from src.envs.reward_utils import sigma_5min_tramo
    ruta = ruta_tercio(tercio)

    def f(executor_id="apertura", q_slice=1000, ventana_min=15, seed=None, **kw):
        env = EjecutorEnvPoissonFallback(executor_id=executor_id, q_slice=max(float(q_slice), 1.0),
                                         ventana_min=ventana_min, ticker=ticker, seed=seed)
        tramo = env.executor_id
        env._sim = PoissonLOBSimulator(ticker=ticker, tramo=tramo, seed=seed, calibration_path=ruta)
        env._sigma_5min = sigma_5min_tramo(ticker, tramo, ruta)
        return env

    return f


def impacto_tercio(ticker: str, tercio: str):
    """σ del día (misma fórmula que `impacto_acumulado.sigma_dia_bps`) y volumen diario mediano, del tercio."""
    from src.envs.impacto_acumulado import BARRAS_5MIN_DIA, ParametrosImpacto
    from src.envs.reward_utils import sigma_5min_tramo
    ruta = ruta_tercio(tercio)
    s5 = [sigma_5min_tramo(ticker, t, ruta) for t in ("apertura", "media_jornada", "cierre")]
    info = json.loads(ruta.read_text(encoding="utf-8"))["tickers_info"][ticker]
    return ParametrosImpacto(sigma_dia_bps=float(sum(s5) / 3 * math.sqrt(BARRAS_5MIN_DIA) * 1e4),
                             volumen_dia=float(info["volumen_diario"]["mediana"]),
                             y=CRITERIO["impacto"]["y"], tau_min=CRITERIO["impacto"]["tau_min"])


# ---------------------------------------------------------------------------
# Una meta-orden con una regla fija
# ---------------------------------------------------------------------------

def correr_regla(orden: Dict, seed: int, alfa_idx: int, tercio: str, redes: Dict) -> Dict:
    import torch
    from scripts.colab import evaluar_sistema_ps as ev
    from src.analysis.execution_metrics import evaluate_episode
    from src.envs.maestro_ejecutor_protocol import MaestroEjecutorEnv
    from src.models.networks_factory import make_executor_policy_fn

    semilla_orden = int(seed) + int(orden.get("semilla", 0))
    acum = ev._Acumulador()
    torch.manual_seed(semilla_orden)
    fabrica = ev._factory_pareada(fabrica_tercio(orden["ticker"], tercio), semilla_orden,
                                  ev.periodo_inicio(orden["tramo_inicio"]), acum,
                                  impacto_tercio(orden["ticker"], tercio))
    env = MaestroEjecutorEnv(meta_orden_quantity=int(orden["cantidad"]),
                             datos_historicos=ev.datos_desde(orden["tramo_inicio"]),
                             executor_env_factory=fabrica,
                             executor_policy_fn=make_executor_policy_fn(redes, deterministic=False),
                             completar_al_cierre=CRITERIO["completar_al_cierre"])
    env.reset()
    done, n = False, 0
    while not done:
        _, _, done, _ = env.step((int(alfa_idx), CRITERIO["ventana_idx"]))
        n += 1
    env.close()
    p_prom = acum.monto / acum.q if acum.q > 0 else acum.p_ref
    m = evaluate_episode(q_total=float(orden["cantidad"]), q_executed=acum.q, p_referencia=acum.p_ref,
                         p_promedio_ejecutado=p_prom)
    return {"orden": orden["id"], "ticker": orden["ticker"], "tramo_inicio": orden["tramo_inicio"], "seed": int(seed),
            "tercio": tercio, "alfa_idx": int(alfa_idx), "n_decisiones": n,
            "slippage_bps": float(m["slippage_bps"]), "execution_rate": float(m["execution_rate"])}


# ---------------------------------------------------------------------------
# Criterio
# ---------------------------------------------------------------------------

def _ic(d: np.ndarray, n_boot: int, semilla: int, nivel: float):
    medias = np.random.default_rng(semilla).choice(d, size=(n_boot, len(d)), replace=True).mean(axis=1)
    lo, hi = np.percentile(medias, [(1 - nivel) / 2 * 100, (1 + nivel) / 2 * 100])
    return float(lo), float(hi)


def evaluar(corridas: Sequence[Dict], criterio: Dict = CRITERIO) -> Dict:
    from src.envs.maestro_ejecutor_protocol import ALPHA_VALUES
    costo = {(c["tercio"], c["alfa_idx"], c["orden"], c["seed"]): c["slippage_bps"] for c in corridas}
    cumpl = {(c["tercio"], c["alfa_idx"], c["orden"], c["seed"]): c["execution_rate"] for c in corridas}
    claves = sorted({(c["orden"], c["seed"]) for c in corridas})
    kw = dict(n_boot=criterio["n_boot"], semilla=criterio["semilla_boot"], nivel=criterio["nivel"])
    tabla, mejor, admisible = {}, {}, {}
    for t in criterio["tercios"]:
        tabla[t], admisible[t] = {}, set()
        for a in criterio["alfa_idx"]:
            v = np.array([costo[(t, a, o, s)] for o, s in claves])
            completas = float(np.mean([cumpl[(t, a, o, s)] >= criterio["cumplimiento_min"] for o, s in claves]))
            ok = completas >= criterio["fraccion_completas_min"]
            if ok:
                admisible[t].add(a)
            tabla[t][str(ALPHA_VALUES[a])] = {"costo_medio_bps": float(v.mean()), "fraccion_completas": completas,
                                              "admisible": ok, "n": int(len(v))}
        mejor[t] = min(admisible[t], key=lambda a: tabla[t][str(ALPHA_VALUES[a])]["costo_medio_bps"],
                       default=None)
    base = {"tabla": tabla, "n_corridas": len(corridas), "criterio": criterio,
            "mejor_alfa": {t: (ALPHA_VALUES[a] if a is not None else None) for t, a in mejor.items()}}
    if mejor["bajo"] is None or mejor["alto"] is None:
        return {"veredicto": NO_EVALUABLE, "comparaciones": {}, **base}
    comparaciones = {}
    for propio, otro in (("bajo", "alto"), ("alto", "bajo")):
        a_p, a_o = mejor[propio], mejor[otro]
        d = np.array([costo[(propio, a_o, o, s)] - costo[(propio, a_p, o, s)] for o, s in claves])
        lo, hi = _ic(d, **kw) if a_p != a_o else (0.0, 0.0)
        otra_admisible = a_o in admisible[propio]
        comparaciones[propio] = {"alfa_propia": ALPHA_VALUES[a_p], "alfa_del_otro": ALPHA_VALUES[a_o],
                                 "alfa_del_otro_admisible_aqui": otra_admisible,
                                 "sobrecosto_medio_bps": float(d.mean()), "ic_bajo": lo, "ic_alto": hi,
                                 "cumple": bool(a_p != a_o and (not otra_admisible or lo > 0))}
    distintas = mejor["bajo"] != mejor["alto"]
    veredicto = SIGUE if distintas and all(c["cumple"] for c in comparaciones.values()) else SE_DETIENE
    return {"veredicto": veredicto, "comparaciones": comparaciones, **base}


# ---------------------------------------------------------------------------
# Ejecución
# ---------------------------------------------------------------------------

def cargar_ordenes(ids: Optional[Sequence[str]] = None) -> List[Dict]:
    ordenes = json.loads(META_ORDENES.read_text(encoding="utf-8"))["meta_ordenes"]
    return [o for o in ordenes if not ids or o["id"] in ids]


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ckpt-dir", required=True, help="carpeta con ejecutor_apertura/media_jornada/cierre.pt")
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    ap.add_argument("--ordenes", nargs="*", default=None, help="solo para probar; el criterio usa las 10")
    ap.add_argument("--semillas", type=int, default=None, help="solo para probar; el criterio usa 10")
    args = ap.parse_args(list(argv) if argv is not None else None)

    from scripts.colab import evaluar_sistema_ps as ev
    ckpt = Path(args.ckpt_dir)
    _, redes = ev.cargar_redes(None, {t: str(ckpt / f"ejecutor_{t}.pt")
                                      for t in ("apertura", "media_jornada", "cierre")})
    ordenes = cargar_ordenes(args.ordenes)
    semillas = CRITERIO["semillas"][:args.semillas] if args.semillas else CRITERIO["semillas"]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    ruta = args.out_dir / "corridas.json"
    hechas = {}
    if ruta.exists():
        hechas = {(c["tercio"], c["alfa_idx"], c["orden"], c["seed"]): c
                  for c in json.loads(ruta.read_text(encoding="utf-8"))["corridas"]}
    t0 = time.time()
    for o in ordenes:
        for t in CRITERIO["tercios"]:
            for s in semillas:
                for a in CRITERIO["alfa_idx"]:
                    if (t, a, o["id"], s) not in hechas:
                        hechas[(t, a, o["id"], s)] = correr_regla(o, s, a, t, redes)
        _guardar(ruta, {"criterio": CRITERIO, "corridas": list(hechas.values())})
        print(f"{o['id']} listo ({len(hechas)} corridas, {time.time() - t0:.0f} s)", flush=True)
    completo = args.ordenes is None and args.semillas is None
    if completo:
        res = evaluar(list(hechas.values()))
        _guardar(args.out_dir / "resultado.json", res)
        print(json.dumps({k: res[k] for k in ("veredicto", "mejor_alfa", "comparaciones")},
                         ensure_ascii=False, indent=1))
    return 0


def _guardar(ruta: Path, payload: Dict) -> None:
    with open(ruta, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1, ensure_ascii=False)
        fh.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())
