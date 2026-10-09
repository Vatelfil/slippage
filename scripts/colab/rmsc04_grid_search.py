"""Busqueda en grilla de RMSC04 (tarea 2.2.4, bloque B) -- corre en Colab.

Para cada combinacion de la grilla (`src/envs/rmsc04_search.GRID_DEFAULT`,
<= 27) simula el dia completo con `--seeds` semillas, mide los momentos por
tramo y calcula la perdida contra `objetivos_validacion[ticker]`.

    PYTHONPATH=. python scripts/colab/rmsc04_grid_search.py \
        --ticker FALABELLA --snapshot 2026-08-23 --seeds 3 --out-dir <dir>

Salida: <out-dir>/rmsc04_grid_<ticker>_<snapshot>.json. Se guarda despues de
cada simulacion; al relanzar el script se saltan las ya guardadas.

`--screen` corre un sondeo barato (un factor por vez, 1 semilla, solo la
apertura) -> rmsc04_screen_<ticker>_<snapshot>.json. `--grid-spec` permite
cambiar los niveles de la grilla sin tocar el codigo.

Entrada: data/calibration/rmsc04_base_<ticker>_<snapshot>.json (bloque A,
versionado; incluye los retornos reales, asi que no se necesitan los .parquet).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.envs import rmsc04_search as rs  # noqa: E402
from src.envs import rmsc04_sim_stats as ss  # noqa: E402
from src.envs.calibrate_rmsc04_ipsa import (  # noqa: E402
    DEFAULT_CALIBRATION_JSON,
    DEFAULT_OUT_DIR,
    KAPPA_ORACLE_RMSC04,
    fund_vol_from_sigma,
    load_abides_kwargs,
)

SCREEN_END_TIME = "11:30:00"


def base_json_path(ticker: str, snapshot: str, base_json: Optional[str] = None) -> Path:
    return Path(base_json) if base_json else DEFAULT_OUT_DIR / f"rmsc04_base_{ticker}_{snapshot}.json"


def load_base(path: Path) -> Dict:
    if not path.exists():
        raise FileNotFoundError(
            f"No existe {path}. Generarlo (en local, con los .parquet) con: "
            "python -m src.envs.calibrate_rmsc04_ipsa --ticker <T> --snapshot <fecha>")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def day_kwargs(base: Dict, base_path: Path) -> Dict:
    """Config de fondo para simular el dia completo: la del bloque A con el
    `fund_vol` de la volatilidad del dia (ver `rmsc04_search.loss`)."""
    kw = dict(load_abides_kwargs(base_path)["apertura"])
    reales = {t: base["por_tramo"][t]["retornos_reales_5min"] for t in ss.TRAMO_NAMES}
    sigma_dia_bps = rs.pooled_sigma_bps(reales)
    kw["fund_vol"] = fund_vol_from_sigma(
        sigma_dia_bps / 1e4, kw["r_bar"], kw.get("kappa_oracle", KAPPA_ORACLE_RMSC04))
    return {"kwargs": kw, "sigma_dia_bps": sigma_dia_bps}


def run_configs(configs: List[Dict], kwargs_base: Dict, seeds: Sequence[int], end_time: str,
                estado: Dict, out_path: Path, evaluar: Callable[[Dict], Dict],
                reintentar_errores: bool = False,
                simular: Optional[Callable[[Dict, int, str], Dict]] = None) -> None:
    """Corre las simulaciones pendientes y guarda tras cada una. `simular`
    permite inyectar un simulador falso en los tests."""
    simular = simular or ss.simulate_moments
    total = len(configs)
    for i, cfg in enumerate(configs, 1):
        entrada = estado["resultados"].setdefault(
            cfg["id"], {"params": cfg["params"], "niveles": cfg.get("niveles"), "corridas": {}})
        pendientes = rs.seeds_pendientes(entrada, seeds, reintentar_errores)
        if not pendientes and "perdida" in entrada:
            print(f"[{i}/{total}] {cfg['id']}: ya guardada, se salta", flush=True)
            continue
        for seed in pendientes:
            t0 = time.time()
            try:
                mom = simular({**kwargs_base, **cfg["params"]}, seed, end_time)
                corrida = {"momentos": mom}
            except Exception as e:  # una configuracion que falla no detiene la grilla
                corrida = {"error": f"{type(e).__name__}: {e}"}
            corrida["segundos"] = round(time.time() - t0, 1)
            entrada["corridas"][str(seed)] = corrida
            print(f"[{i}/{total}] {cfg['id']} seed={seed}: {corrida['segundos']:.0f}s"
                  + (f" ERROR {corrida['error']}" if "error" in corrida else ""), flush=True)
            rs.save_json(out_path, estado)
        runs = [c["momentos"] for c in entrada["corridas"].values() if "momentos" in c]
        entrada["n_errores"] = sum(1 for c in entrada["corridas"].values() if "error" in c)
        entrada["completa"] = (len(rs.seeds_pendientes(entrada, seeds)) == 0
                               and entrada["n_errores"] == 0 and len(runs) > 0)
        if runs:
            pooled = ss.pool_moments(runs)
            entrada["momentos"] = ss.strip_returns(pooled)
            entrada["perdida"] = evaluar(pooled)
        rs.save_json(out_path, estado)


def print_ranking(estado: Dict, n: int = 10) -> None:
    filas = [(v["perdida"]["total"], k, v) for k, v in estado["resultados"].items() if v.get("perdida")]
    filas.sort(key=lambda x: x[0])
    print("\nperdida  rank_fallidos  spread_med_bps(a/m/c)  vol_bps(a/m/c)  vol_vela(a/m/c)  config")
    for total, k, v in filas[:n]:
        m = v["momentos"]

        def tr(key, fmt):
            return "/".join(fmt.format(m[t][key]) if m[t].get(key) is not None else "-"
                            for t in ss.TRAMO_NAMES)

        print(f"{total:7.3f}  {v['perdida']['n_rankings_fallidos']:^13d}  "
              f"{tr('spread_mediano_bps', '{:.2f}'):21s}  {tr('volatilidad_bps', '{:.1f}'):14s}  "
              f"{tr('volumen_mediano_vela', '{:.0f}'):15s}  {k}")


def main(argv: Optional[Sequence[str]] = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--ticker", default="FALABELLA")
    ap.add_argument("--snapshot", default="2026-08-23")
    ap.add_argument("--seeds", type=int, default=3, help="numero de semillas por configuracion (1..N)")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--base-json", default=None)
    ap.add_argument("--calibration-json", default=str(DEFAULT_CALIBRATION_JSON))
    ap.add_argument("--grid-spec", default=None, help="JSON con {factor: [niveles]} para reemplazar la grilla")
    ap.add_argument("--screen", action="store_true", help="corre solo el sondeo de sensibilidad")
    ap.add_argument("--max-configs", type=int, default=rs.MAX_COMBINACIONES)
    ap.add_argument("--retry-errors", action="store_true")
    args = ap.parse_args(argv)

    base_path = base_json_path(args.ticker, args.snapshot, args.base_json)
    base = load_base(base_path)
    dia = day_kwargs(base, base_path)
    objetivos = rs.load_targets(args.calibration_json, args.ticker)["por_tramo"]
    spec = rs.GRID_DEFAULT
    if args.grid_spec:
        with open(args.grid_spec, "r", encoding="utf-8") as f:
            spec = json.load(f)

    out_dir = Path(args.out_dir)
    firma = {"ticker": args.ticker, "snapshot": args.snapshot, "kwargs_base": dia["kwargs"],
             "sigma_dia_bps": dia["sigma_dia_bps"], "grid_spec": spec}

    def evaluar(pooled: Dict) -> Dict:
        return rs.loss(pooled, objetivos, vol_ref_unica_bps=dia["sigma_dia_bps"])

    if args.screen:
        configs, seeds, end_time = rs.build_screen(spec), [1], SCREEN_END_TIME
        out_path = out_dir / f"rmsc04_screen_{args.ticker}_{args.snapshot}.json"
        firma.update({"modo": "screen", "end_time": end_time})
    else:
        configs = rs.build_grid(spec, args.max_configs)
        seeds, end_time = list(range(1, args.seeds + 1)), "16:00:00"
        out_path = out_dir / f"rmsc04_grid_{args.ticker}_{args.snapshot}.json"
        firma.update({"modo": "grid", "end_time": end_time})

    estado = rs.load_resumable(out_path, firma)
    estado["objetivos_por_tramo"] = objetivos
    estado["semillas"] = sorted(set(estado.get("semillas", [])) | set(seeds))
    print(f"{len(configs)} configuraciones x {len(seeds)} semillas, hasta {end_time} -> {out_path}", flush=True)
    run_configs(configs, dia["kwargs"], seeds, end_time, estado, out_path, evaluar, args.retry_errors)
    estado["mejor"] = rs.best_config(estado["resultados"])
    rs.save_json(out_path, estado)
    print_ranking(estado)
    print(f"\nMejor: {estado['mejor']}\nGuardado: {out_path}")


if __name__ == "__main__":
    main()
