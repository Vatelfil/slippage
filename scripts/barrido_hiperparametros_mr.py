"""Barrido de hiperparámetros del Ejecutor (tareas 3.1.1 y 3.1.2), en Poisson (BORRADOR de PS para MR, 29 oct 2026).

La rejilla y la regla de selección están en `scripts/colab/grid_specs/hiperparametros_ejecutor_mr.json`, fijadas antes
de ver resultados. Cada configuración se entrena con la penalización por lo no comprado y γ = 1 (la base que funcionó en
Poisson) y se evalúa contra su propia red inicial en las mismas semillas, igual que en la reevaluación de ABIDES.

    PYTHONPATH=. python scripts/barrido_hiperparametros_mr.py --fase 3.1.1 --out-dir data/barrido_hp
    PYTHONPATH=. python scripts/barrido_hiperparametros_mr.py --fase 3.1.2 --out-dir data/barrido_hp
    PYTHONPATH=. python scripts/barrido_hiperparametros_mr.py --fase 3.1.1 --out-dir data/barrido_hp --solo-analizar

Reanudable: cada (configuración, semilla de red) se guarda en su propio JSON y se salta si ya existe. Las mejores
configuraciones se confirman después en ABIDES con `scripts/colab/entrenamiento_inicial_ps.py` (opciones `--lr`,
`--epochs`, `--minibatch`, `--clip`, `--gae-lambda`).
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

GRID = REPO_ROOT / "scripts" / "colab" / "grid_specs" / "hiperparametros_ejecutor_mr.json"
CLAVES = ("lr", "minibatch_size", "epochs", "clip_ratio", "gae_lambda")


def cargar_grid(ruta=GRID) -> Dict:
    return json.loads(Path(ruta).read_text(encoding="utf-8"))


def nombre_config(c: Dict) -> str:
    return "_".join(f"{k}{c[k]:g}" for k in CLAVES)


def configuraciones(grid: Dict, fase: str, base: Optional[Dict] = None) -> List[Dict]:
    """Lista de configuraciones completas de una fase. La 3.1.2 parte del ganador de la 3.1.1 (`base`)."""
    f = grid["fases"][fase]
    base = dict(base or grid["por_defecto"])
    if f["modo"] == "rejilla":
        nombres, valores = zip(*f["parametros"].items())
        return [dict(base, **dict(zip(nombres, combo))) for combo in itertools.product(*valores)]
    rng = np.random.default_rng(int(f["semilla"]))
    out = [dict(base)]                                   # la base siempre entra, para comparar contra ella
    for _ in range(int(f["n"]) - 1):
        c = dict(base)
        for k, (lo, hi) in f["parametros"].items():
            c[k] = round(float(rng.uniform(lo, hi)), 3)
        out.append(c)
    return out


def correr_una(c: Dict, semilla: int, comunes: Dict, carpeta_monitoreo: Optional[Path] = None) -> Dict:
    """Entrena una red con la configuración y la evalúa, junto con su red inicial, en las semillas de evaluación."""
    import copy
    from src.experiments import variantes_recompensa as vr
    from src.training.ppo_trainer import PPOConfig, PPOTrainer

    cfg = PPOConfig(lr=c["lr"], gamma=comunes["gamma"], gae_lambda=c["gae_lambda"], clip_ratio=c["clip_ratio"],
                    entropy_coef=comunes["entropy_coef"], value_coef=0.5, epochs=int(c["epochs"]),
                    minibatch_size=int(c["minibatch_size"]), episodes_per_update=comunes["episodes_per_update"])
    tr = PPOTrainer(role="ejecutor", cfg=cfg, seed=int(semilla), device="cpu")
    inicial = copy.deepcopy(tr.model)
    fabrica = vr.fabrica_entrenamiento(vr.Variante("barrido", penalizacion_bps=comunes["penalizacion_bps"]),
                                       semilla_sorteo=int(semilla))
    csv_entrenador = None
    if carpeta_monitoreo is not None:   # monitoreo de la 3.1.4: una fila por episodio y el CSV del entrenador
        from src.training.monitoreo import MonitorEntrenamiento
        carpeta_monitoreo.mkdir(parents=True, exist_ok=True)
        fabrica = MonitorEntrenamiento(carpeta_monitoreo / "monitoreo_episodios.csv", seed_base=int(semilla)).envolver(fabrica)
        csv_entrenador = carpeta_monitoreo / "entrenamiento_apertura.csv"
    t0 = time.time()
    tr.train_executor_episodes(env_factory=fabrica, n_episodes=int(comunes["episodios"]), q_slice=comunes["q_slice"],
                               ventana_min=comunes["ventana_min"], csv_path=csv_entrenador, log_fn=lambda *_: None)
    seeds = [comunes["eval_seed_base"] + i for i in range(1, comunes["eval_semillas"] + 1)]
    kw = dict(q_slice=comunes["q_slice"], ventana_min=comunes["ventana_min"])
    red = vr.evaluar_red(tr.model, seeds, muestrear=True, **kw)
    ini = vr.evaluar_red(inicial, seeds, muestrear=True, **kw)
    return {"config": c, "semilla_red": int(semilla), "segundos": round(time.time() - t0, 1),
            "slippage_red": [e["slippage_bps"] for e in red], "slippage_inicial": [e["slippage_bps"] for e in ini],
            "cumplimiento_red": float(np.mean([e["cumplimiento_voluntario"] for e in red])),
            "espera_red": float(np.mean([e["pct_espera"] for e in red]))}


def _ic(d: np.ndarray, n_boot: int = 3000):
    m = np.random.default_rng(0).choice(d, size=(n_boot, len(d)), replace=True).mean(axis=1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def analizar(resultados: Sequence[Dict], grid: Dict, referencia: Optional[Dict] = None) -> Dict:
    """Aplica la regla de selección del JSON de la rejilla. `referencia` es la configuración contra la que se exige una
    mejora clara: la por defecto en la 3.1.1 y el ganador de la 3.1.1 (punto de partida) en la 3.1.2."""
    referencia = dict(referencia or grid["por_defecto"])
    por: Dict[str, Dict] = {}
    for r in resultados:
        n = nombre_config(r["config"])
        e = por.setdefault(n, {"config": r["config"], "dif": [], "cumplimiento": [], "semillas": []})
        e["dif"] += [a - b for a, b in zip(r["slippage_red"], r["slippage_inicial"]) if np.isfinite(a) and np.isfinite(b)]
        e["cumplimiento"].append(r["cumplimiento_red"])
        e["semillas"].append(r["semilla_red"])
    filas = []
    for n, e in por.items():
        d = np.array(e["dif"], dtype=float)
        lo, hi = _ic(d) if len(d) > 1 else (float("nan"), float("nan"))
        filas.append({"nombre": n, **e["config"], "dif_media_bps": float(d.mean()) if len(d) else float("nan"),
                      "ic_bajo": lo, "ic_alto": hi, "cumplimiento": float(np.mean(e["cumplimiento"])),
                      "n_semillas_red": len(e["semillas"])})
    filas.sort(key=lambda f: f["dif_media_bps"])
    validas = [f for f in filas if f["cumplimiento"] >= 0.95]
    defecto = next((f for f in filas if all(f[k] == referencia[k] for k in CLAVES)), None)
    if not validas:
        decision = {"ganador": None, "texto": "Ninguna configuración cumple el 95 % de la orden: revisar la rejilla."}
    else:
        g = validas[0]
        if defecto is not None and g is not defecto and defecto in validas \
                and g["ic_bajo"] <= defecto["dif_media_bps"] <= g["ic_alto"]:
            elegido, texto = defecto, "Sin mejora clara frente a la configuración de referencia: se mantiene la de referencia."
        elif g is defecto:
            elegido, texto = g, "La configuración de referencia es la mejor de las que cumplen: se mantiene."
        else:
            elegido = g
            texto = (f"Gana {g['nombre']}: su IC no incluye la diferencia de la configuración de referencia."
                     if defecto in validas else f"Gana {g['nombre']}; la configuración de referencia no cumple el 95 % o no se corrió.")
        decision = {"ganador": elegido["nombre"], "config": {k: elegido[k] for k in CLAVES}, "texto": texto}
    return {"filas": filas, "decision": decision}


def informe_md(an: Dict, fase: str) -> str:
    lineas = [f"# Barrido de hiperparámetros, fase {fase} (Poisson)\n",
              "BORRADOR de PS para MR. Diferencia = costo de la red entrenada − costo de su red inicial, pareada por semilla "
              "de evaluación (negativo es mejor). Regla fijada antes de ver los datos (ver el JSON de la rejilla).\n",
              f"**Decisión:** {an['decision']['texto']}\n",
              "| Configuración | Diferencia (bps) | IC 95 % | Cumplimiento | Redes |", "|---|---:|---|---:|---:|"]
    for f in an["filas"]:
        lineas.append(f"| `{f['nombre']}` | {f['dif_media_bps']:.2f} | [{f['ic_bajo']:.2f}; {f['ic_alto']:.2f}] | "
                      f"{f['cumplimiento']:.3f} | {f['n_semillas_red']} |")
    return "\n".join(lineas) + "\n"


def grafico(an: Dict, ruta: Path, fase: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    filas = an["filas"]
    fig, ax = plt.subplots(figsize=(8, max(3, 0.3 * len(filas))))
    y = np.arange(len(filas))
    m = np.array([f["dif_media_bps"] for f in filas])
    err = np.array([[f["dif_media_bps"] - f["ic_bajo"] for f in filas], [f["ic_alto"] - f["dif_media_bps"] for f in filas]])
    colores = ["#2b6cb0" if f["cumplimiento"] >= 0.95 else "#a0aec0" for f in filas]
    ax.barh(y, m, xerr=err, color=colores, capsize=2)
    ax.axvline(0, color="black", lw=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels([f["nombre"] for f in filas], fontsize=7)
    ax.invert_yaxis()
    ax.set_xlabel("Costo de la red entrenada − red inicial (bps, IC 95 %); gris: cumple < 95 %")
    ax.set_title(f"Barrido de hiperparámetros {fase} (Poisson)")
    fig.tight_layout()
    fig.savefig(ruta, dpi=130)
    plt.close(fig)


def main(argv: Optional[Sequence[str]] = None) -> Dict:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--fase", choices=["3.1.1", "3.1.2"], required=True)
    ap.add_argument("--grid", default=str(GRID))
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--solo-analizar", action="store_true")
    ap.add_argument("--max-configs", type=int, default=None, help="para ensayos cortos")
    ap.add_argument("--episodios", type=int, default=None, help="reemplaza el valor del JSON (ensayos cortos)")
    args = ap.parse_args(argv)

    grid = cargar_grid(args.grid)
    comunes = dict(grid["comunes"])
    if args.episodios:
        comunes["episodios"] = args.episodios
    out = Path(args.out_dir) / args.fase.replace(".", "_")
    out.mkdir(parents=True, exist_ok=True)
    base = None
    if args.fase == "3.1.2":
        previo = Path(args.out_dir) / "3_1_1" / "analisis.json"
        if previo.exists():
            base = json.loads(previo.read_text(encoding="utf-8"))["decision"].get("config")
    configs = configuraciones(grid, args.fase, base)[: args.max_configs]
    if not args.solo_analizar:
        for c in configs:
            for s in comunes["semillas_red"]:
                f = out / f"{nombre_config(c)}_s{s}.json"
                if f.exists():
                    continue
                r = correr_una(c, s, comunes, out / "monitoreo" / f.stem)
                f.write_text(json.dumps(r, ensure_ascii=False) + "\n", encoding="utf-8")
                d = np.nanmean(np.array(r["slippage_red"]) - np.array(r["slippage_inicial"]))
                print(f"{f.stem}: diferencia {d:.2f} bps, cumplimiento {r['cumplimiento_red']:.3f} ({r['segundos']:.0f} s)", flush=True)
    resultados = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(out.glob("lr*_s*.json"))]
    an = analizar(resultados, grid, base)
    an["referencia"] = dict(base or grid["por_defecto"])
    (out / "analisis.json").write_text(json.dumps(an, indent=1, ensure_ascii=False), encoding="utf-8")
    (out / "barrido.md").write_text(informe_md(an, args.fase), encoding="utf-8")
    grafico(an, out / "barrido.png", args.fase)
    print(an["decision"]["texto"])
    return an


if __name__ == "__main__":
    main()
