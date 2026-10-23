"""Panel de monitoreo del entrenamiento (tarea 3.1.4, Sprint 6): curvas, comparacion de corridas y alertas.

BORRADOR elaborado por PS con apoyo de Claude Code (adelanto del Sprint 6).

Lee, por corrida, el CSV del entrenador (una fila por actualizacion PPO) y, si existe, el CSV de monitoreo por
episodio (`src/training/monitoreo.py`: costo, cumplimiento y fraccion de pasos en espera). Genera:
  - una figura con las curvas de todas las corridas juntas (para comparar hiperparametros o la opcion 0 y A de R_E),
  - un informe markdown con las alertas de cada corrida (`evaluar_alertas`).

    python scripts/monitorear_entrenamiento.py \
        --corrida "opcion 0=data/colab_resultados/t5_1000ep_opcion0.csv" \
        --corrida "opcion A=carpeta/entrenamiento_apertura.csv,carpeta/monitoreo_episodios.csv" \
        --estado "opcion 0=data/colab_resultados/t5_1000ep_opcion0.json" \
        --out-png docs/monitoreo.png --out-md docs/monitoreo.md

Para varias corridas guardadas en subcarpetas (por ejemplo las de `scripts/colab/d3_estabilidad_ps.py`), `--dir CARPETA` las
descubre solas: cada subcarpeta con un `entrenamiento_<tramo>.csv` es una corrida, y se usan su `monitoreo_episodios.csv` y su
`entrenamiento_inicial_<tramo>.json` si existen. `--out-json` deja el resumen por corrida (metricas y alertas) para la Sprint Review.

Formato de `--corrida`: ETIQUETA=actualizaciones.csv[,episodios.csv]. `--estado` (opcional, repetible): ETIQUETA=estado.json
de `entrenamiento_inicial_ps.py`, para comparar el cumplimiento con argmax y con la politica muestreada.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.training.monitoreo import (ENTROPIA_MAXIMA, Alerta, Umbrales, evaluar_alertas, leer_actualizaciones,  # noqa: E402
                                    leer_episodios)


def _par(valor: str) -> Tuple[str, str]:
    etiqueta, sep, resto = valor.partition("=")
    if not sep or not etiqueta or not resto:
        raise argparse.ArgumentTypeError(f"se esperaba ETIQUETA=ruta, llego {valor!r}")
    return etiqueta, resto


def _media_movil(x: Sequence[float], k: int) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    out = np.full(len(x), np.nan)
    for i in range(len(x)):
        v = x[max(0, i - k + 1): i + 1]
        v = v[np.isfinite(v)]
        if len(v):
            out[i] = v.mean()
    return out


def figura(corridas: Dict[str, Dict], ruta: Path, ventana: int = 20) -> Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(2, 4, figsize=(18, 7.5))
    paneles_ep = [(ax[0, 0], "retorno", "Retorno (por episodio, media móvil; sin monitoreo: media por actualización)", None),
                  (ax[0, 1], "slippage_bps", "Slippage por episodio, bps (media móvil)", None),
                  (ax[0, 2], "cumplimiento", "Cumplimiento (media móvil)", (0, 1.05)),
                  (ax[0, 3], "pct_espera", "Fracción de pasos en espera (media móvil)", (0, 1.05))]
    paneles_up = [(ax[1, 0], "entropia", "Entropía de la política (nats)"),
                  (ax[1, 1], "kl", "Divergencia KL"),
                  (ax[1, 2], "loss_critic", "Pérdida del crítico"),
                  (ax[1, 3], "clip_fraction", "Fracción recortada")]
    for etiqueta, c in corridas.items():
        eps, ups = c.get("episodios"), c.get("actualizaciones")
        if eps:
            x = [f["episodio"] for f in eps]
            for a, clave, titulo, lim in paneles_ep:
                a.plot(x, _media_movil([f[clave] for f in eps], ventana), label=etiqueta)
        if ups and not eps and "reward_mean" in ups[0]:   # sin monitoreo por episodio: al menos el retorno medio del entrenador
            ax[0, 0].plot([f["episodio"] for f in ups], [f["reward_mean"] for f in ups], marker="o", ms=2.5, lw=1, label=etiqueta)
        if ups:
            x = [f["episodio"] for f in ups]
            for a, clave, titulo in paneles_up:
                if clave in ups[0]:
                    a.plot(x, [f[clave] for f in ups], marker="o", ms=2.5, lw=1, label=etiqueta)
    hay_episodios = any(c.get("episodios") for c in corridas.values())
    for a, clave, titulo, lim in paneles_ep:
        a.set_title(titulo, fontsize=9)
        if not hay_episodios and clave != "retorno":
            a.text(0.5, 0.5, "Sin CSV de monitoreo por episodio\n(ver src/training/monitoreo.py)", ha="center", va="center",
                   transform=a.transAxes, fontsize=9, color="gray")
        if lim:
            a.set_ylim(*lim)
        if clave == "cumplimiento":
            a.axhline(0.95, color="gray", ls="--", lw=0.8)
    for a, clave, titulo in paneles_up:
        a.set_title(titulo, fontsize=9)
        if clave == "entropia":
            a.axhline(ENTROPIA_MAXIMA, color="gray", ls="--", lw=0.8)
        if clave in ("kl", "loss_critic"):
            a.set_yscale("log")
    for a in ax.ravel():
        a.set_xlabel("episodio")
        a.grid(alpha=0.3)
    h, lab = ax[1, 0].get_legend_handles_labels()
    if not h:
        h, lab = ax[0, 0].get_legend_handles_labels()
    if h:
        fig.legend(h, lab, loc="upper center", ncol=max(1, len(lab)), fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return ruta


def _coma(x: float, d: int = 3) -> str:
    return f"{x:.{d}f}".replace(".", ",")


def informe(corridas: Dict[str, Dict], alertas: Dict[str, List[Alerta]], png_rel: str) -> str:
    L = ["# Monitoreo del entrenamiento (tarea 3.1.4)", "",
         "**Borrador elaborado por:** PS con apoyo de Claude Code. Panel generado con `scripts/monitorear_entrenamiento.py`.", "",
         f"![Curvas de las corridas]({png_rel})", "",
         "## Resumen por corrida", "",
         "| Corrida | Actualizaciones | Episodios registrados | Entropía final (% del máximo) | KL máximo | Cumplimiento final | Pasos en espera (final) | Alertas |",
         "|---|---:|---:|---:|---:|---:|---:|---|"]
    for etiqueta, c in corridas.items():
        ups, eps = c.get("actualizaciones") or [], c.get("episodios") or []
        ent = f"{100 * ups[-1]['entropia'] / ENTROPIA_MAXIMA:.1f} %".replace(".", ",") if ups and "entropia" in ups[-1] else "—"
        kl = _coma(max(f["kl"] for f in ups), 5) if ups and "kl" in ups[0] else "—"
        n = max(1, min(50, len(eps) // 2)) if eps else 0
        cump = _coma(float(np.nanmean([f["cumplimiento"] for f in eps[-n:]]))) if eps else "—"
        esp = f"{100 * np.nanmean([f['pct_espera'] for f in eps[-n:]]):.0f} %" if eps else "—"
        crit = sum(a.nivel == "CRITICA" for a in alertas[etiqueta])
        av = sum(a.nivel == "AVISO" for a in alertas[etiqueta])
        L.append(f"| {etiqueta} | {len(ups)} | {len(eps) or '—'} | {ent} | {kl} | {cump} | {esp} | {crit} críticas, {av} avisos |")
    L += ["", "## Alertas", ""]
    orden = {"CRITICA": 0, "AVISO": 1, "INFO": 2}
    for etiqueta, lista in alertas.items():
        L += [f"**{etiqueta}**", ""]
        if not lista:
            L += ["- Sin alertas.", ""]
            continue
        for a in sorted(lista, key=lambda a: orden[a.nivel]):
            L.append(f"- **{a.nivel}** `{a.codigo}`: {a.mensaje}")
        L.append("")
    L += ["## Cómo leerlo", "",
          "- **Entropía:** una política uniforme sobre las 240 acciones tiene 5,48 nats. Una caída fuerte significa que la política se concentra; "
          "conviene evaluar también con muestreo y no solo con argmax (ver `docs/entrenamiento_inicial_2.3.5.md`).",
          "- **Pasos en espera:** acciones `LIMIT_SELL`, que el puente de ABIDES y el simulador Poisson tratan como «esperar».",
          "- Sin el CSV de monitoreo por episodio solo se muestran las curvas del entrenador; el costo y el cumplimiento por episodio "
          "se registran con `MonitorEntrenamiento` (`src/training/monitoreo.py`).", "",
          "🤖 Generado con [Claude Code](https://claude.com/claude-code)", ""]
    return "\n".join(L)


def descubrir(carpeta: Path) -> List[Tuple[str, str, Optional[str], Optional[str]]]:
    """(etiqueta, actualizaciones.csv, episodios.csv | None, estado.json | None) de cada subcarpeta con un entrenamiento."""
    out = []
    for sub in sorted(p for p in Path(carpeta).iterdir() if p.is_dir()):
        csvs = sorted(sub.glob("entrenamiento_*.csv"))
        if not csvs:
            continue
        ep, est = sub / "monitoreo_episodios.csv", sorted(sub.glob("entrenamiento_inicial_*.json"))
        out.append((sub.name, str(csvs[0]), str(ep) if ep.exists() else None, str(est[0]) if est else None))
    return out


def resumen_json(corridas: Dict[str, Dict], alertas: Dict[str, List[Alerta]]) -> Dict:
    """Metricas finales y alertas por corrida, en un diccionario serializable."""
    out: Dict = {}
    for etiqueta, c in corridas.items():
        ups, eps = c.get("actualizaciones") or [], c.get("episodios") or []
        n = max(1, min(50, len(eps) // 2)) if eps else 0
        out[etiqueta] = {
            "actualizaciones": len(ups), "episodios_registrados": len(eps),
            "entropia_final_pct_max": round(100 * ups[-1]["entropia"] / ENTROPIA_MAXIMA, 2) if ups and "entropia" in ups[-1] else None,
            "kl_maximo": float(max(f["kl"] for f in ups)) if ups and "kl" in ups[0] else None,
            "cumplimiento_final": float(np.nanmean([f["cumplimiento"] for f in eps[-n:]])) if eps else None,
            "pct_espera_final": float(np.nanmean([f["pct_espera"] for f in eps[-n:]])) if eps else None,
            "alertas": [{"nivel": a.nivel, "codigo": a.codigo, "mensaje": a.mensaje} for a in alertas[etiqueta]],
            "criticas": sum(a.nivel == "CRITICA" for a in alertas[etiqueta]),
            "avisos": sum(a.nivel == "AVISO" for a in alertas[etiqueta])}
    return out


def main(argv: Optional[Sequence[str]] = None) -> Path:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--corrida", action="append", type=_par, default=[], metavar="ETIQUETA=ACTUALIZACIONES.csv[,EPISODIOS.csv]")
    ap.add_argument("--dir", default=None, help="carpeta con una subcarpeta por corrida (se descubren sus CSV y su estado)")
    ap.add_argument("--out-json", default=None, help="resumen por corrida (metricas y alertas) en JSON")
    ap.add_argument("--estado", action="append", type=_par, default=[], metavar="ETIQUETA=ESTADO.json")
    ap.add_argument("--ventana", type=int, default=20, help="ventana de la media movil de las curvas por episodio")
    ap.add_argument("--out-png", default=str(REPO_ROOT / "data/analysis/monitoreo_entrenamiento.png"))
    ap.add_argument("--out-md", default=str(REPO_ROOT / "docs/monitoreo_entrenamiento.md"))
    args = ap.parse_args(argv)

    corridas_args = list(args.corrida)
    estados_args = list(args.estado)
    if args.dir:
        for etiqueta, act, ep, est in descubrir(Path(args.dir)):
            corridas_args.append((etiqueta, act + ("," + ep if ep else "")))
            if est:
                estados_args.append((etiqueta, est))
    if not corridas_args:
        ap.error("falta --corrida o --dir con corridas")
    estados: Dict[str, Dict] = {}
    for etiqueta, ruta in estados_args:
        with open(ruta, "r", encoding="utf-8-sig") as fh:
            estados[etiqueta] = json.load(fh)
    corridas: Dict[str, Dict] = {}
    alertas: Dict[str, List[Alerta]] = {}
    for etiqueta, ruta in corridas_args:
        partes = ruta.split(",")
        c: Dict = {"actualizaciones": leer_actualizaciones(partes[0])}
        if len(partes) > 1 and partes[1]:
            c["episodios"] = leer_episodios(partes[1])
        corridas[etiqueta] = c
        alertas[etiqueta] = evaluar_alertas(c.get("episodios") or [], c["actualizaciones"], estados.get(etiqueta), Umbrales())
    png = figura(corridas, Path(args.out_png), args.ventana)
    try:
        png_rel = "../" + Path(png).resolve().relative_to(Path(args.out_md).resolve().parent.parent).as_posix()
    except ValueError:
        png_rel = Path(png).name
    Path(args.out_md).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_md).write_text(informe(corridas, alertas, png_rel), encoding="utf-8")
    if args.out_json:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(resumen_json(corridas, alertas), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for etiqueta, lista in alertas.items():
        print(f"== {etiqueta}")
        print("\n".join(f"  [{a.nivel}] {a.codigo}: {a.mensaje}" for a in lista) or "  Sin alertas.")
    print(f"Figura: {png}\nInforme: {args.out_md}")
    return Path(args.out_md)


if __name__ == "__main__":
    main()
