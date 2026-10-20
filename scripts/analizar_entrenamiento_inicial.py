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
from scipy import stats

N_ACCIONES = 240  # tamano del espacio de acciones del Ejecutor (3 tipos x 10 volumenes x 8 niveles)

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


def comparacion_pareada(estado: Dict, clave: str = "evaluacion_entrenada") -> List[Dict]:
    """Red entrenada frente a cada alternativa, pareado por semilla de evaluacion (misma jornada simulada)."""
    if clave not in estado:
        return []
    tr = np.asarray(estado[clave]["slippage_por_semilla"], dtype=float)
    if not np.isfinite(tr).all():   # la red entrenada no ejecuto nada en alguna semilla: no hay slippage que comparar
        return []
    otras = {"Red sin entrenar (control)": estado["evaluacion_sin_entrenar"]}
    otras.update({f"Referencia: {k}": v for k, v in estado.get("referencias", {}).items()})
    filas = []
    for nombre, e in otras.items():
        x = np.asarray(e["slippage_por_semilla"], dtype=float)
        d = tr - x
        w = stats.wilcoxon(tr, x) if np.any(d != 0) else None
        filas.append({"contra": nombre, "dif_media": float(d.mean()),
                      "ee": float(d.std(ddof=1) / np.sqrt(len(d))), "p_wilcoxon": None if w is None else float(w.pvalue)})
    return filas


def lectura(estado: Dict, filas: List[Dict[str, float]]) -> List[str]:
    """Frases de la seccion 5, armadas con las cifras de la corrida (no se transcriben a mano)."""
    comp = {c["contra"]: c for c in comparacion_pareada(estado)}
    if not comp:
        ev = estado["evaluacion_entrenada"]
        est = estado.get("evaluacion_entrenada_estocastica")
        extra = []
        if est:
            cm = {c["contra"]: c for c in comparacion_pareada(estado, "evaluacion_entrenada_estocastica")}
            ctrl_m = cm.get("Red sin entrenar (control)")
            extra = [f"- **Muestreando la política (como al entrenar) sí se ejecuta:** cumplimiento {_f(est.get('cumplimiento_medio'), 3)} y slippage {_f(est.get('slippage_bps_medio'))} bps "
                     f"(EE {_f(est.get('slippage_bps_ee'))}), frente a {_f(estado['evaluacion_sin_entrenar'].get('slippage_bps_medio'))} bps de la red sin entrenar"
                     + (f" (diferencia pareada {_f(ctrl_m['dif_media'])} bps, p = {_f(ctrl_m['p_wilcoxon'], 3)})." if ctrl_m else ".")
                     + " La evaluación con argmax y la política que se entrena son cosas distintas: el argmax puede caer en una acción que no hace nada."]
        return extra + [f"- **La red entrenada no ejecutó la orden en la evaluación:** cumplimiento medio {_f(ev.get('cumplimiento_medio'), 3)} y sin slippage medible en las {ev.get('n')} semillas. "
                "Con la política determinista (argmax) la red no llega a ejecutar nada; por eso no hay comparación pareada.",
                f"- **Entropía de la política:** {_f(filas[-1]['entropia'], 4)} frente a {_f(math.log(N_ACCIONES), 4)} de una política uniforme "
                f"({_f(100 * filas[-1]['entropia'] / math.log(N_ACCIONES), 1)} % del máximo): la política se concentró.",
                "- **D3:** el cumplimiento de la red entrenada es " + _f(estado.get("vigilancia_D3", {}).get("cumplimiento_medio"), 3)
                + ", por debajo del 95 %; la regla del plan indica pasar a la opción A (riesgo sobre lo pendiente). La decisión es de BF."]
    ctrl = comp["Red sin entrenar (control)"]
    ent_rel = filas[-1]["entropia"] / math.log(N_ACCIONES)
    sig = lambda c: c["p_wilcoxon"] is not None and c["p_wilcoxon"] < 0.05
    tr, sin = estado["evaluacion_entrenada"], estado["evaluacion_sin_entrenar"]
    out = [
        f"- **El ciclo completo funciona con ABIDES:** {estado.get('episodios_entrenados')} episodios en {_f(estado.get('segundos_entrenamiento', 0.0) / 60, 1)} min, "
        "sin valores no finitos, con checkpoint, CSV y evaluación en semillas nuevas.",
        f"- **No hay evidencia de que la red haya aprendido todavía.** La red entrenada tiene {_f(tr['slippage_bps_medio'])} bps frente a {_f(sin['slippage_bps_medio'])} bps de la red sin entrenar, "
        f"pero la diferencia pareada ({_f(ctrl['dif_media'])} bps, p = {_f(ctrl['p_wilcoxon'], 3)}) "
        + ("es significativa." if sig(ctrl) else "no es significativa con 15 semillas."),
        f"- **Las actualizaciones fueron muy pequeñas:** KL máximo {_f(max(r['kl'] for r in filas), 5)}, fracción recortada {_f(max(r['clip_fraction'] for r in filas), 2)} y entropía al {_f(100 * ent_rel, 2)} % del máximo. "
        "La política sigue siendo casi uniforme; con 10 actualizaciones PPO no se esperaba otra cosa.",
        f"- **Frente a las referencias:** " + "; ".join(
            f"{k.replace('Referencia: ', '')}: {_f(v['dif_media'])} bps (p = {_f(v['p_wilcoxon'], 3)}{', significativa' if sig(v) else ''})"
            for k, v in comp.items() if k.startswith("Referencia")) + ".",
        "- **Qué sugiere:** el resultado sirve para validar el pipeline, no para comparar políticas. Como el entrenamiento es barato "
        f"({_f(estado.get('segundos_entrenamiento', 0.0) / 60, 1)} min por 100 episodios), conviene repetirlo con muchos más episodios (por ejemplo 1.000) antes de sacar conclusiones sobre R_E.",
        "- **D3:** el cumplimiento de la red entrenada es " + _f(estado.get("vigilancia_D3", {}).get("cumplimiento_medio"), 3)
        + "; la regla del plan no obliga a pasar a la opción A."]
    return out


def seccion_diagnostico(diag: Optional[Dict]) -> List[str]:
    if not diag:
        return []
    L = ["", f"### Diagnóstico de la política (checkpoint del episodio {diag.get('episodio_checkpoint')})", "",
         "Tres episodios de evaluación; `scripts/colab/diagnostico_politica_entrenada_ps.py` imprime las acciones paso a paso.", "",
         "| Modo | Cumplimiento medio | Acciones más usadas (todas las semillas) |", "|---|---:|---|"]
    for modo in ("determinista", "estocastico"):
        d = diag.get(modo)
        if not d:
            continue
        cont: Dict[str, int] = {}
        for e in d["episodios"]:
            for k, v in e["acciones"].items():
                cont[k] = cont.get(k, 0) + v
        top = ", ".join(f"`{k.replace(chr(124), ' / ')}` ×{v}" for k, v in sorted(cont.items(), key=lambda kv: -kv[1])[:3])
        L.append(f"| {modo} | {_f(d['cumplimiento_medio'], 3)} | {top} |")
    L += ["", "En el puente de ABIDES, `LIMIT_SELL` se traduce a «esperar» (el proyecto solo modela compra): no envía ninguna orden "
          "(`src/envs/abides_bridge.py`, `map_action_to_abides_orders`).", ""]
    return L


def informe(estado: Dict, filas: List[Dict[str, float]], png_rel: str, diag: Optional[Dict] = None) -> str:
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
        f"- **Entropía:** de {_f(filas[0]['entropia'], 4)} a {_f(filas[-1]['entropia'], 4)}; una política uniforme sobre las {N_ACCIONES} acciones tiene {_f(math.log(N_ACCIONES), 4)}. "
        f"La política final conserva el {_f(100 * filas[-1]['entropia'] / math.log(N_ACCIONES), 2)} % de la entropía máxima"
        + (", es decir, sigue siendo casi uniforme." if filas[-1]['entropia'] / math.log(N_ACCIONES) > 0.99 else ", es decir, se fue concentrando en algunas acciones."),
        f"- **Tiempo de entrenamiento:** {_f(estado.get('segundos_entrenamiento', 0.0) / 60, 1)} min.", "",
        "## 3. Evaluación (semillas nuevas, política determinista)", "",
        "| Política | Slippage medio (bps) | Error estándar | Cumplimiento |", "|---|---:|---:|---:|",
        fila("Red entrenada (política determinista, argmax)", ev)]
    if estado.get("evaluacion_entrenada_estocastica"):
        L.append(fila("Red entrenada (política muestreada, como al entrenar)", estado["evaluacion_entrenada_estocastica"]))
    L += [fila("Red sin entrenar (control, argmax)", sin)]
    for nombre, e in refs.items():
        L.append(fila(f"Referencia: {nombre}", e))
    clave_par = "evaluacion_entrenada" if comparacion_pareada(estado) else "evaluacion_entrenada_estocastica"
    pareada = comparacion_pareada(estado, clave_par)
    if pareada:
        cual = "política determinista" if clave_par == "evaluacion_entrenada" else "política muestreada"
        L += ["", f"Comparación pareada por semilla (red entrenada con {cual} menos cada alternativa; negativo = la red entrenada tiene menos slippage):", "",
          "| Contra | Diferencia media (bps) | Error estándar | p (Wilcoxon) |", "|---|---:|---:|---:|"]
        for c in pareada:
            L.append(f"| {c['contra']} | {_f(c['dif_media'])} | {_f(c['ee'])} | {_f(c['p_wilcoxon'], 3)} |")
    L += seccion_diagnostico(diag)
    L += ["", "## 4. Regla de vigilancia de D3", "",
          f"Cumplimiento medio de la red entrenada: **{_f(vig.get('cumplimiento_medio'), 3)}** (umbral {_f(vig.get('umbral'), 2)}). {vig.get('texto', '')} "
          "La decisión final de R_E se revisa el viernes 23 de octubre y es de BF.", "",
          "## 5. Lectura preliminar de PS (BF debe confirmar, corregir o reemplazar)", ""] + lectura(estado, filas) + [""]
    L += [
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
    ap.add_argument("--diagnostico", default=None, help="opcional: diagnostico_politica.json del diagnostico de la politica")
    ap.add_argument("--out-md", default=str(REPO_ROOT / "docs/entrenamiento_inicial_2.3.5.md"))
    ap.add_argument("--out-png", default=str(REPO_ROOT / "data/analysis/entrenamiento_inicial_2.3.5.png"))
    args = ap.parse_args(argv)
    with open(args.estado, "r", encoding="utf-8-sig") as fh:
        estado = json.load(fh)
    filas = leer_csv(Path(args.csv))
    if not filas:
        raise SystemExit("El CSV no tiene filas.")
    diag = None
    if args.diagnostico:
        with open(args.diagnostico, "r", encoding="utf-8-sig") as fh:
            diag = json.load(fh)
    png = figura(filas, Path(args.out_png), f"Entrenamiento inicial del Ejecutor ({estado['firma']['ticker']}, {estado['firma']['tramo']})")
    try:
        png_rel = Path(png).resolve().relative_to(Path(args.out_md).resolve().parent.parent).as_posix()
        png_rel = "../" + png_rel
    except ValueError:
        png_rel = Path(png).name
    Path(args.out_md).write_text(informe(estado, filas, png_rel, diag), encoding="utf-8")
    print(f"Informe: {args.out_md}\nFigura: {png}")


if __name__ == "__main__":
    main()
