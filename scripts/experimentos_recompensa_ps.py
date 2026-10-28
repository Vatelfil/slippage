"""Matriz de experimentos de recompensa (BORRADOR de PS; corre en el PC con el simulador de Poisson, sin Colab).

Entrena cada variante con varias semillas de red y guarda, por corrida, las curvas de entrenamiento y la evaluación en tres
escenarios. Reanudable: si el archivo de una corrida ya existe, se salta.

    # etapa A: solo cambia la recompensa o el cierre de la ventana
    python scripts/experimentos_recompensa_ps.py --etapa A --out-dir data/experimentos_recompensa/etapa_A

    # etapa B: sobre la mejor variante de la A se agregan tamaños aleatorios, otros hiperparámetros y arranque por imitación
    python scripts/experimentos_recompensa_ps.py --etapa B --base V1_liquidacion --out-dir data/experimentos_recompensa/etapa_B

Las corridas son independientes, así que se reparten en procesos (`--procesos`). En el PC de PS, 1.000 episodios entrenan en
cerca de un minuto por corrida.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import replace
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

SEMILLAS_RED = (1000, 2000, 3000, 4000, 6000)    # las mismas del estudio de D3; con 1.000 episodios no pisan las de evaluación


def _catalogo():
    """Todas las variantes de las etapas A y A2 con su configuración de PPO, por nombre (la etapa B parte de una de ellas)."""
    from src.experiments import entrenamiento_variantes as ev
    from src.experiments import variantes_recompensa as vr
    cat = {}
    for v in vr.ETAPA_A:
        cat[v.nombre] = (v, ev.ConfigPPO())
    for v in (vr.V2B, vr.V5, vr.V6):
        cat[v.nombre] = (v, ev.ConfigPPO())
    for v in vr.ETAPA_A + (vr.V2B, vr.V5, vr.V6):
        cat[v.nombre + "_g1"] = (replace(v, nombre=v.nombre + "_g1"), ev.ConfigPPO(gamma=1.0))
    return cat


def variantes_etapa(etapa: str, base: Optional[str]):
    """Devuelve la lista de (variante, ConfigPPO, arranque) de la etapa pedida."""
    from src.experiments import entrenamiento_variantes as ev
    from src.experiments import variantes_recompensa as vr
    if etapa == "A":
        return [(v, ev.ConfigPPO(), None) for v in vr.ETAPA_A]
    if etapa == "A2":
        # Mismas variantes con gamma = 1 (un costo al final de la ventana no se achica al verlo desde el principio), más
        # las dos variantes nuevas con gamma = 0,95 y con gamma = 1.
        g1 = ev.ConfigPPO(gamma=1.0)
        con_g1 = [(replace(v, nombre=v.nombre + "_g1"), g1, None) for v in vr.ETAPA_A + (vr.V2B, vr.V5, vr.V6)]
        nuevas = [(v, ev.ConfigPPO(), None) for v in (vr.V2B, vr.V5, vr.V6)]
        return nuevas + con_g1
    cat = _catalogo()
    if base not in cat:
        raise SystemExit(f"--base debe ser una de {sorted(cat)}")
    b, cfg_b = cat[base]
    hiper = replace(ev.HIPER_ALTERNATIVOS, gamma=cfg_b.gamma)     # los hiperparámetros alternativos conservan el gamma de la base
    return [
        (replace(b, nombre=b.nombre + "+aleatorio", aleatorizar=True), cfg_b, None),
        (replace(b, nombre=b.nombre + "+hiper"), hiper, None),
        (replace(b, nombre=b.nombre + "+imitacion"), cfg_b, "twap_limit_medio"),
        (replace(b, nombre=b.nombre + "+todo", aleatorizar=True), hiper, "twap_limit_medio"),
    ]


def _correr(trabajo: Tuple) -> Tuple[str, float]:
    """Una corrida completa: entrenar, evaluar y escribir el JSON. Se ejecuta en un proceso aparte."""
    import torch
    torch.set_num_threads(1)          # con varios procesos, un hilo por proceso rinde más que pelearse por los núcleos
    from src.experiments import entrenamiento_variantes as ev

    variante, cfg, arranque, semilla, episodios, q_slice, ventana, salida = trabajo
    t0 = time.time()
    red, inicial, registro, exactitud = ev.entrenar(variante, semilla, episodios, q_slice, ventana, cfg, arranque)
    resultado = {
        "variante": variante.nombre, "descripcion": variante.descripcion(), "semilla_red": semilla, "episodios": episodios,
        "q_slice_entrenamiento": q_slice, "ventana_entrenamiento": ventana, "arranque": arranque,
        "exactitud_imitacion": exactitud, "hiperparametros": cfg.__dict__,
        "curvas": ev.curvas(registro), "evaluacion": ev.evaluar_en_escenarios(red, inicial),
        "segundos": round(time.time() - t0, 1),
    }
    Path(salida).write_text(json.dumps(resultado, indent=1, ensure_ascii=False), encoding="utf-8")
    return Path(salida).name, resultado["segundos"]


def main(argv: Optional[Sequence[str]] = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--etapa", choices=["A", "A2", "B"], required=True)
    ap.add_argument("--solo", nargs="*", default=None, help="correr solo estas variantes (por nombre)")
    ap.add_argument("--base", default=None, help="variante de la etapa A sobre la que se construye la B")
    ap.add_argument("--semillas", nargs="+", type=int, default=list(SEMILLAS_RED))
    ap.add_argument("--episodios", type=int, default=1000)
    ap.add_argument("--q-slice", type=int, default=5000, help="tamaño de entrenamiento: con 1.000 acciones el simulador no distingue estrategias")
    ap.add_argument("--ventana-min", type=int, default=15)
    ap.add_argument("--procesos", type=int, default=6)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args(argv)

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    from src.experiments import entrenamiento_variantes as ev

    ref = out / "referencias.json"
    if not ref.exists():
        print("Calculando políticas de referencia…", flush=True)
        ref.write_text(json.dumps(ev.referencias(), indent=1, ensure_ascii=False), encoding="utf-8")

    trabajos = []
    for variante, cfg, arranque in variantes_etapa(args.etapa, args.base):
        if args.solo and variante.nombre not in args.solo:
            continue
        for s in args.semillas:
            salida = out / f"{variante.nombre}_s{s}.json"
            if not salida.exists():
                trabajos.append((variante, cfg, arranque, s, args.episodios, args.q_slice, args.ventana_min, str(salida)))
    print(f"{len(trabajos)} corridas pendientes", flush=True)
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=args.procesos) as pool:
        futuros = [pool.submit(_correr, t) for t in trabajos]
        for i, f in enumerate(as_completed(futuros), 1):
            nombre, seg = f.result()
            print(f"[{i}/{len(trabajos)}] {nombre} ({seg:.0f} s)", flush=True)
    print(f"Listo en {(time.time() - t0) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
