"""Evaluacion del sistema completo Maestro + 3 Ejecutores sobre las meta-ordenes (insumo de 3.2.3) -- Colab.

BORRADOR elaborado por PS con apoyo de Claude Code (adelanto del Sprint 6: el evaluador queda listo y probado antes de
tener las redes entrenadas). Pendiente de revision por MR (redes y entrenamiento) y BF (meta-ordenes).

Corre cada meta-orden con el Maestro y los Ejecutores y deja el resultado en el MISMO formato que
`scripts/colab/benchmarks_meta_ordenes_ps.py`, con `estrategia` = el nombre del sistema (por defecto "PPO"), de modo que
`scripts/comparar_sistema_vs_benchmarks.py` lo lea sin cambios:

    PYTHONPATH=. python scripts/colab/evaluar_sistema_ps.py \
        --meta-ordenes data/meta_ordenes/meta_ordenes_v2_candidata.json \
        --entorno abides --seeds 2 --out-dir <carpeta_de_drive> --max-minutes 150
    # con redes entrenadas:  --ckpt-maestro maestro.pt --ckpt-ejecutor apertura=a.pt --ckpt-ejecutor media_jornada=m.pt ...

Para que el pareo con TWAP/VWAP sea valido (mismas ordenes, mismas semillas):
  - la semilla de mercado de cada periodo es la de los benchmarks: `(seed + semilla_orden) * 1000 + periodo`;
  - el precio de referencia y el precio medio se leen con las mismas funciones que los benchmarks
    (`_leer_reset`, `_leer_paso`), no con el reporte interno de `MaestroEjecutorEnv` (que en ABIDES usa best_ask);
  - la orden empieza en su tramo de inicio: el reloj del Maestro parte de la hora de ese tramo, no de las 09:30.

Sin `--ckpt-*` se usan redes SIN entrenar (control; el nombre queda "PPO_sin_entrenar"). Con `--modo muestreo` la politica se
muestrea (como en el entrenamiento) en vez de tomar el argmax.

Limites conocidos:
  - Las variables `volatilidad` y `vol_promedio` de S_M valen una constante a menos que se pase `--datos-sm`
    (tabla con indice horario y esas dos columnas, salida de la tarea 1.2.2).
  - `n_slices` de S_M parte en 0 aunque la orden empiece a mitad de jornada.
  - Reanudable: guarda tras cada corrida.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.analysis.benchmarks import _leer_paso, _leer_reset, periodo_inicio  # noqa: E402
from src.analysis.execution_metrics import evaluate_episode  # noqa: E402
from src.envs.rmsc04_search import load_resumable, save_json  # noqa: E402

TRAMOS = ("apertura", "media_jornada", "cierre")
SEED_RED = 1000          # semilla de los pesos iniciales cuando no hay checkpoint (misma para todas las sesiones)
VOL_CONSTANTE = 0.002   # volatilidad y vol_promedio de S_M si no se pasan datos (constantes, no informan al Maestro)
VOLP_CONSTANTE = 0.2


def hora_inicio(tramo_inicio: str) -> str:
    """Hora (HH:MM) de inicio de una orden: 09:30 + 30 min por periodo (apertura 09:30, media 11:00, cierre 14:00)."""
    minutos = 9 * 60 + 30 + 30 * periodo_inicio(tramo_inicio)
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


def datos_desde(tramo_inicio: str, datos_sm: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Tabla de S_M cuyo primer indice es la hora de inicio de la orden (el entorno parte de `index[0]`)."""
    ini = hora_inicio(tramo_inicio)
    dia = "2026-09-29"
    idx = pd.date_range(f"{dia} {ini}", f"{dia} 16:00", freq="5min")
    if datos_sm is None:
        return pd.DataFrame({"volatilidad": VOL_CONSTANTE, "vol_promedio": VOLP_CONSTANTE}, index=idx)
    hh = datos_sm.index.strftime("%H:%M")
    # misma hora del dia en la tabla de entrada; se re-indexa a un dia fijo para que el entorno la use
    base = datos_sm.groupby(hh)[["volatilidad", "vol_promedio"]].mean()
    out = pd.DataFrame(index=idx)
    for col, const in (("volatilidad", VOL_CONSTANTE), ("vol_promedio", VOLP_CONSTANTE)):
        out[col] = [float(base[col].get(t.strftime("%H:%M"), const)) for t in idx]
    return out


class _Acumulador:
    """Cantidad y monto ejecutados en toda la orden, y el precio de referencia (el del primer periodo)."""

    def __init__(self) -> None:
        self.q = 0.0
        self.monto = 0.0
        self.p_ref: Optional[float] = None


class _Grabador:
    """Envuelve un entorno de Ejecutor y anota lo ejecutado con las mismas funciones que usan los benchmarks."""

    def __init__(self, env, acum: _Acumulador) -> None:
        self._env, self._acum = env, acum

    def reset(self, *a, **k):
        obs, info = self._env.reset(*a, **k)
        p = _leer_reset(info)
        if self._acum.p_ref is None:
            self._acum.p_ref = p
        return obs, info

    def step(self, action):
        res = self._env.step(action)
        q, p = _leer_paso(res[4], self._acum.p_ref)
        if q > 0:
            self._acum.q += q
            self._acum.monto += q * p
        return res

    def __getattr__(self, nombre):
        return getattr(self._env, nombre)


def _factory_pareada(base: Optional[Callable], semilla_orden: int, periodo0: int, acum: _Acumulador) -> Callable:
    """Fabrica de Ejecutores que usa la semilla de mercado de los benchmarks para el periodo correspondiente."""
    contador = {"k": 0}

    def fabrica(executor_id="apertura", q_slice=1000, ventana_min=15, **kw):
        semilla = semilla_orden * 1000 + periodo0 + contador["k"]
        contador["k"] += 1
        if base is None:
            from src.envs.fallback_poisson_env import EjecutorEnvPoissonFallback
            env = EjecutorEnvPoissonFallback(executor_id=executor_id, q_slice=max(q_slice, 1.0), ventana_min=ventana_min,
                                             ticker=kw.pop("ticker", "FALABELLA"), seed=semilla)
        else:
            env = base(executor_id=executor_id, q_slice=int(max(q_slice, 1)), ventana_min=ventana_min, seed=semilla)
        return _Grabador(env, acum)

    return fabrica


def correr_orden(orden: Dict, seed: int, maestro, redes: Dict, base_factory: Optional[Callable], nombre: str,
                 deterministic: bool = True, datos_sm: Optional[pd.DataFrame] = None) -> Dict:
    """Una meta-orden con el sistema completo. Devuelve la corrida en el formato de los benchmarks."""
    import torch
    from src.envs.maestro_ejecutor_protocol import MaestroEjecutorEnv, maestro_policy
    from src.models.networks_factory import make_executor_policy_fn

    semilla_orden = int(seed) + int(orden.get("semilla", 0))
    p0 = periodo_inicio(orden["tramo_inicio"])
    acum = _Acumulador()
    torch.manual_seed(semilla_orden)
    env = MaestroEjecutorEnv(meta_orden_quantity=int(orden["cantidad"]),
                             datos_historicos=datos_desde(orden["tramo_inicio"], datos_sm),
                             executor_env_factory=_factory_pareada(base_factory, semilla_orden, p0, acum),
                             executor_policy_fn=make_executor_policy_fn(redes, deterministic=deterministic))
    s_m, done, r_m, decisiones = env.reset(), False, 0.0, []
    while not done:
        accion = maestro_policy(s_m, model=maestro, deterministic=deterministic)
        s_m, r_m, done, info = env.step(accion)
        decisiones.append({"alpha_idx": int(accion[0]), "ventana_idx": int(accion[1]),
                           "q_ejecutado": float(info["executor_report"]["q_ejecutado"])})
    env.close()
    p_prom = acum.monto / acum.q if acum.q > 0 else acum.p_ref
    m = evaluate_episode(q_total=float(orden["cantidad"]), q_executed=acum.q, p_referencia=acum.p_ref,
                         p_promedio_ejecutado=p_prom)
    return {"orden": orden["id"], "estrategia": nombre, "seed": int(seed), "ticker": orden["ticker"],
            "tramo_inicio": orden["tramo_inicio"], "cantidad": orden["cantidad"],
            "n_decisiones": len(decisiones), "decisiones": decisiones, "R_M": float(r_m),
            **{k: float(v) for k, v in m.items()}}


def pendientes(estado: Dict, ordenes: Sequence[Dict], seeds: Sequence[int], nombre: str) -> List[tuple]:
    hechas = estado.get("corridas", {})
    return [(o["id"], s) for s in seeds for o in ordenes if f"{o['id']}|{nombre}|{s}" not in hechas]


def correr(ordenes: Sequence[Dict], seeds: Sequence[int], estado: Dict, guardar: Callable[[Dict], None],
           maestro, redes: Dict, factory_por_ticker: Callable[[str], Optional[Callable]], nombre: str,
           deterministic: bool = True, datos_sm: Optional[pd.DataFrame] = None,
           presupuesto_s: Optional[float] = None, log: Callable[[str], None] = print) -> bool:
    """Corre lo pendiente. Devuelve True si no queda nada."""
    t_ini = time.time()
    corridas = estado.setdefault("corridas", {})
    por_id = {o["id"]: o for o in ordenes}
    for oid, seed in pendientes(estado, ordenes, seeds, nombre):
        if presupuesto_s is not None and time.time() - t_ini > presupuesto_s:
            log("Presupuesto de tiempo agotado: volver a ejecutar para continuar.")
            return False
        o, clave, t0 = por_id[oid], f"{oid}|{nombre}|{seed}", time.time()
        try:
            c = correr_orden(o, seed, maestro, redes, factory_por_ticker(o["ticker"]), nombre, deterministic, datos_sm)
            c["segundos"] = round(time.time() - t0, 1)
            corridas[clave] = c
            log(f"{clave}: slippage={c['slippage_bps']:.2f} bps cumpl={c['execution_rate']:.3f} ({c['segundos']:.0f}s)")
        except Exception as e:  # una corrida fallida no tumba la sesion
            corridas[clave] = {"orden": oid, "estrategia": nombre, "seed": int(seed), "error": f"{type(e).__name__}: {e}"}
            log(f"{clave}: ERROR {corridas[clave]['error']}")
        guardar(estado)
    return True


def _pesos(ckpt) -> Dict:
    """Pesos de un checkpoint: `PPOTrainer.save_checkpoint` los guarda en `model_state_dict`; otros scripts usaban `model`."""
    for clave in ("model_state_dict", "model"):
        if isinstance(ckpt, dict) and clave in ckpt:
            return ckpt[clave]
    return ckpt


def cargar_redes(ckpt_maestro: Optional[str], ckpt_ejecutores: Dict[str, str], seed_red: int = SEED_RED):
    """(Maestro, {tramo: Ejecutor}); los que no tienen checkpoint quedan con pesos iniciales, FIJADOS por `seed_red`
    (sin esa semilla cada proceso crea redes distintas y dos sesiones no serian comparables)."""
    import torch
    from src.models.networks_factory import make_hierarchy

    torch.manual_seed(int(seed_red))
    maestro, redes = make_hierarchy()
    if ckpt_maestro:
        maestro.load_state_dict(_pesos(torch.load(ckpt_maestro, map_location="cpu")))
    for tramo, ruta in ckpt_ejecutores.items():
        redes[tramo].load_state_dict(_pesos(torch.load(ruta, map_location="cpu")))
    maestro.eval()
    for r in redes.values():
        r.eval()
    return maestro, redes


def _parse_ckpt(valores: Sequence[str]) -> Dict[str, str]:
    out = {}
    for v in valores:
        tramo, sep, ruta = v.partition("=")
        if not sep or tramo not in TRAMOS:
            raise SystemExit(f"--ckpt-ejecutor espera TRAMO=ruta con TRAMO en {TRAMOS}: {v!r}")
        out[tramo] = ruta
    return out


def main(argv: Optional[Sequence[str]] = None) -> Path:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--meta-ordenes", default=str(REPO_ROOT / "data/meta_ordenes/meta_ordenes_v1.json"))
    ap.add_argument("--entorno", choices=["abides", "poisson"], default="abides")
    ap.add_argument("--snapshot", default="2026-08-23")
    ap.add_argument("--calibrated-dir", default=str(REPO_ROOT / "data/calibration"))
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--ordenes", nargs="*", default=None, help="ids a correr (para repartir entre cuadernos)")
    ap.add_argument("--ckpt-maestro", default=None)
    ap.add_argument("--ckpt-ejecutor", action="append", default=[], metavar="TRAMO=ruta")
    ap.add_argument("--seed-red", type=int, default=SEED_RED, help="semilla de los pesos iniciales de las redes sin checkpoint")
    ap.add_argument("--modo", choices=["argmax", "muestreo"], default="argmax")
    ap.add_argument("--nombre", default=None, help="nombre de la estrategia en el archivo (por defecto PPO o PPO_sin_entrenar)")
    ap.add_argument("--datos-sm", default=None, help="CSV con indice horario y columnas volatilidad, vol_promedio")
    ap.add_argument("--max-minutes", type=float, default=None)
    ap.add_argument("--escenario", default=None, help="escenario de liquidez (baja, media, alta; ver data/scenarios); sin la opcion, la calibracion de siempre")
    ap.add_argument("--escenarios-json", default=None)
    ap.add_argument("--factor-tamano", type=float, default=1.0, help="multiplica la cantidad de cada meta-orden (0.5, 1, 1.5)")
    args = ap.parse_args(argv)

    with open(args.meta_ordenes, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    ordenes = data["meta_ordenes"] if isinstance(data, dict) else data
    if args.ordenes:
        ordenes = [o for o in ordenes if o["id"] in set(args.ordenes)]
    # escenario de liquidez y tamaño (3.1.3 / 3.2.1, borrador de PS para BF); sin opciones queda todo como antes
    from src.envs import escenarios_liquidez as el
    ordenes = el.ajustar_ordenes(ordenes, args.factor_tamano)
    factor_liq = el.factor_de(args.escenario, args.escenarios_json)
    ckpts = _parse_ckpt(args.ckpt_ejecutor)
    entrenado = bool(args.ckpt_maestro or ckpts)
    nombre = args.nombre or ("PPO" if entrenado else "PPO_sin_entrenar")
    datos_sm = None
    if args.datos_sm:
        datos_sm = pd.read_csv(args.datos_sm, index_col=0, parse_dates=True)

    maestro, redes = cargar_redes(args.ckpt_maestro, ckpts, args.seed_red)
    factory_por_ticker = el.fabricas_por_ticker(args.entorno, args.calibrated_dir, args.snapshot, factor_liq)

    sufijo = el.sufijo_condicion(args.escenario, args.factor_tamano)
    out = Path(args.out_dir) / f"sistema_meta_ordenes_{args.entorno}_{nombre}_{args.modo}{sufijo}.json"
    firma = {"tarea": "3.2.3-evaluador", "entorno": args.entorno, "snapshot": args.snapshot, "sistema": nombre,
             "modo": args.modo, "ckpt_maestro": args.ckpt_maestro, "ckpt_ejecutores": ckpts, "seed_red": args.seed_red,
             "ordenes": sorted(o["id"] for o in ordenes), "cantidades": {o["id"]: o["cantidad"] for o in ordenes},
             "datos_sm": args.datos_sm}
    if sufijo:
        firma.update({"escenario": args.escenario, "factor_liquidez": factor_liq, "factor_tamano": args.factor_tamano})
    estado = load_resumable(out, firma)
    seeds = list(range(1, args.seeds + 1))
    print(f"{len(pendientes(estado, ordenes, seeds, nombre))} corridas pendientes ({nombre}, {args.modo})", flush=True)
    ok = correr(ordenes, seeds, estado, lambda e: save_json(out, e), maestro, redes, factory_por_ticker, nombre,
                deterministic=args.modo == "argmax", datos_sm=datos_sm,
                presupuesto_s=None if args.max_minutes is None else args.max_minutes * 60)
    for c in estado.get("corridas", {}).values():
        c.setdefault("escenario", args.escenario or "media")
        c.setdefault("factor_tamano", args.factor_tamano)
    save_json(out, estado)
    print(f"Guardado: {out}")
    if not ok:
        print("Quedaron corridas pendientes: vuelve a ejecutar el mismo comando.")
    return out


if __name__ == "__main__":
    main()
