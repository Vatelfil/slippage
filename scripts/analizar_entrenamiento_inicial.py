"""Analisis del entrenamiento inicial del Ejecutor (tarea 2.3.5).

BORRADOR elaborado por PS con apoyo de Claude Code; pendiente de revision por BF.

Lee lo que deja `scripts/colab/entrenamiento_inicial_ps.py` (estado JSON y CSV del entrenador) y genera:
  - una figura con las curvas (perdida del actor y del critico, recompensa media, KL y entropia),
  - un informe markdown con la configuracion, las tablas y la regla de vigilancia de D3.
Las cifras salen de los archivos, no se transcriben.

    python scripts/analizar_entrenamiento_inicial.py \
        --estado data/colab_resultados/entrenamiento_inicial_apertura.json \
        --csv data/colab_resultados/entrenamiento_apertura.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _f(x, d: int = 2) -> str:
    return "—" if x is None or (isinstance(x, float) and not math.isfinite(x)) else f"{x:.{d}f}".replace(".", ",")


def leer_csv(path: Path) -> List[Dict[str, float]]:
    with open(path, "r", encoding="utf-8-sig") as fh:
        return [{k: float(v) for k, v in fila.items()} for fila in csv.DictReader(fh)]


def figura(filas: List[Dict[str, float]], out_png: Path, titulo: str) -> Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ep = [r["episodio"] for r in filas]
    fig, axes = plt.subplots(2, 3, figsize=(13, 6.5))
    series = [("reward_mean", "Retorno medio (10 episodios)"), ("loss_actor", "Pérdida del actor"),
              ("loss_critic", "Pérdida del crítico"), ("kl", "Divergencia KL"),
              ("entropia", "Entropía"), ("clip_fraction", "Fracción recortada")]
    for ax, (k, nombre) in zip(axes.ravel(), series):
        ax.plot(ep, [r[k] for r in filas], marker="o", color="#1E2761")
        ax.set_title(nombre, fontsize=10)
        ax.set_xlabel("episodio")
        ax.grid(alpha=0.3)
    fig.suptitle(titulo)
    fig.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=140, bbox_inches="tight")
    plt.close(fig)
    return out_png


def informe(estado: Dict, filas: List[Dict[str, float]], png_rel: str) -> str:
    f = estado["firma"]
    n = len(filas)
    nan = sum(1 for r in filas for v in r.values() if not math.isfinite(v))
    k = max(1, n // 3)
    r_ini = float(np.mean([r["reward_mean"] for r in filas[:k]]))
    r_fin = float(np.mean([r["reward_mean"] for r in filas[-k:]]))
    la_ini = float(np.mean([r["loss_critic"] for r in filas[:k]]))
    la_fin = float(np.mean([r["loss_critic"] for r in filas[-k:]]))
    kl_max = max(r["kl"] for r in filas)
    ev, sin, refs = estado.get("evaluacion_entrenada", {}), estado.get("evaluacion_sin_entrenar", {}), estado.get("referencias", {})
    vig = estado.get("vigilancia_D3", {})

    def fila(nombre: str, e: Dict) -> str:
        return (f"| {nombre} | {_f(e.get('slippage_bps_medio'))} | {_f(e.get('slippage_bps_ee'))} | "
                f"{_f(e.get('cumplimiento_medio'), 3)} |")

    L = [
        "# Entrenamiento inicial de validación del Ejecutor (tarea 2.3.5)", "",
        "**Borrador elaborado por:** Paolo Sepúlveda (PS) con apoyo de Claude Code. **Pendiente de revisión por:** Benjamín Farias (BF), responsable de la 2.3.5, y Mauricio Reynoso (MR, entrenador PPO). "
        "Lo que BF no acepte se cambia o se descarta; nada aquí está cerrado hasta su revisión.", "",
        "## 1. Qué se hizo", "",
        f"Se entrenó un Ejecutor con el entrenador PPO de MR (`PPOTrainer`, 2.3.2) durante **{estado.get('episodios_entrenados', n * 10)} episodios** sobre ABIDES "
        f"{'calibrado' if f.get('entorno') == 'abides' else '(ensayo con el simulador de Poisson, no con ABIDES)'} ({f['ticker']}, tramo {f['tramo'].replace('_', ' ')}, `{f['calibrated_json']}`), con `q_slice` = {f['q_slice']} acciones y ventana de {f['ventana_min']} minutos. "
        f"Recompensa: R_E según el Título I con β = {_f(f['beta'], 7)} (opción 0 de D3). Semillas de entrenamiento {f['seed'] + 1}–{f['seed'] + f['episodios']}; "
        f"evaluación en {f['eval_seeds']} semillas nuevas ({f['eval_seed_base'] + 1}–{f['eval_seed_base'] + f['eval_seeds']}). No se usaron las 10 meta-órdenes oficiales.", "",
        "Hiperparámetros (los mismos de la fase 2 de β): γ 0,95; λ GAE 0,95; lr 3e-4; clip 0,2; entropía 0,01; coeficiente de valor 0,5; 4 épocas; minilote 64; 10 episodios por actualización.", "",
        "## 2. Curvas de entrenamiento", "",
        f"![Curvas del entrenamiento]({png_rel})", "",
        f"- **Actualizaciones registradas:** {n} (una cada 10 episodios). **Valores no finitos (NaN o infinito) en el CSV:** {nan}.",
        f"- **Retorno medio:** {_f(r_ini, 3)} en el primer tercio y {_f(r_fin, 3)} en el último. **Pérdida del crítico:** {_f(la_ini, 3)} y {_f(la_fin, 3)}.",
        f"- **KL máximo:** {_f(kl_max, 5)} (el objetivo del entrenador es 0,015; la actualización se corta si lo supera 1,5 veces).",
        f"- **Tiempo de entrenamiento:** {_f(estado.get('segundos_entrenamiento', 0.0) / 60, 1)} min.", "",
        "## 3. Evaluación (semillas nuevas, política determinista)", "",
        "| Política | Slippage medio (bps) | Error estándar | Cumplimiento |", "|---|---:|---:|---:|",
        fila("Red entrenada", ev), fila("Red sin entrenar (control)", sin)]
    for nombre, e in refs.items():
        L.append(fila(f"Referencia: {nombre}", e))
    L += ["", "## 4. Regla de vigilancia de D3", "",
          f"Cumplimiento medio de la red entrenada: **{_f(vig.get('cumplimiento_medio'), 3)}** (umbral {_f(vig.get('umbral'), 2)}). {vig.get('texto', '')} "
          "La decisión final de R_E se revisa el viernes 23 de octubre y es de BF.", "",
          "## 5. Hallazgos y problemas (a completar por BF tras revisar)", "",
          "_Esta sección la escribe BF con lo que vea en las curvas y en la tabla. Los números de arriba son los que da la corrida._", "",
          "## 6. Limitaciones", "",
          "- Entrenamiento corto (100 episodios) y una sola semilla de red: el resultado es indicativo, no concluyente.",
          "- Solo FALABELLA y un tramo; no incluye a COPEC ni a ECL.",
          "- La evaluación usa 15 semillas: el error estándar es grande frente a las diferencias entre políticas.", "",
          "## 7. Cómo reproducir", "",
          "En Colab, con el entorno preparado (`docs/dependencias_resueltas.md`, con `torch==1.13.1+cpu`):", "",
          "```bash",
          "PYTHONPATH=. python scripts/colab/entrenamiento_inicial_ps.py \\",
          f"    --calibrated-json data/calibration/{f['calibrated_json']} --out-dir <carpeta_de_drive>/t5_entrenamiento \\",
          f"    --tramo {f['tramo']} --episodes {f['episodios']} --ventana-min {f['ventana_min']} --max-minutes 150",
          "```", "",
          "El script es reanudable. Luego `python scripts/analizar_entrenamiento_inicial.py --estado <json> --csv <csv>` regenera este informe.", "",
          "🤖 Generado con [Claude Code](https://claude.com/claude-code)", ""]
    return "\n".join(L)


def main(argv: Optional[Sequence[str]] = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--estado", required=True)
    ap.add_argument("--csv", required=True)
    ap.add_argument("--out-md", default=str(REPO_ROOT / "docs/entrenamiento_inicial_2.3.5.md"))
    ap.add_argument("--out-png", default=str(REPO_ROOT / "data/analysis/entrenamiento_inicial_2.3.5.png"))
    args = ap.parse_args(argv)
    with open(args.estado, "r", encoding="utf-8-sig") as fh:
        estado = json.load(fh)
    filas = leer_csv(Path(args.csv))
    if not filas:
        raise SystemExit("El CSV no tiene filas.")
    png = figura(filas, Path(args.out_png), f"Entrenamiento inicial del Ejecutor ({estado['firma']['ticker']}, {estado['firma']['tramo']})")
    try:
        png_rel = Path(png).resolve().relative_to(Path(args.out_md).resolve().parent.parent).as_posix()
        png_rel = "../" + png_rel
    except ValueError:
        png_rel = Path(png).name
    Path(args.out_md).write_text(informe(estado, filas, png_rel), encoding="utf-8")
    print(f"Informe: {args.out_md}\nFigura: {png}")


if __name__ == "__main__":
    main()
