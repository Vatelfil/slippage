"""Calibración de las alertas del monitoreo con corridas reales (tarea 3.1.4; BORRADOR de PS).

Las alertas de `src/training/monitoreo.py` se escribieron mirando lo que pasó en la 2.3.5. Aquí se prueban contra un
conjunto de corridas cuyo resultado ya se conoce, para ver cuáles avisan cuando algo anda mal y cuáles dan falsas alarmas:

  - corridas de Poisson hechas en el PC (con el arreglo, sin él y con variantes intermedias), que se generan aquí con el
    mismo formato de archivos que deja el entrenamiento en ABIDES;
  - corridas de ABIDES que ya están en el repositorio (`data/colab_resultados/d3_1000ep` y `d3_estabilidad`).

Cada corrida lleva una etiqueta («buena», «mala» o «neutral») sacada de su evaluación (ver los informes de experimentos y de
D3), nunca de las propias alertas. El informe cruza etiqueta y alertas.

    python scripts/calibrar_monitoreo_ps.py --generar      # entrena las corridas de Poisson (≈ 5 min)
    python scripts/calibrar_monitoreo_ps.py                # cruza alertas y etiquetas y escribe el informe
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DIR_POISSON = REPO_ROOT / "data/calibracion_monitoreo"
SEMILLAS = (1000, 2000)
# (nombre de la variante, etiqueta según su evaluación en `docs/experimentos_recompensa_*_PS.md`)
CORRIDAS_POISSON: List[Tuple[str, str]] = [
    ("V0_original", "mala"),               # la recompensa de hoy: la red deja de operar
    ("V0_original_g1", "mala"),
    ("V2_penalizacion", "mala"),           # penalización con gamma = 0,95: sigue esperando
    ("V2_penalizacion_g1", "buena"),       # el arreglo propuesto
    ("V1_liquidacion_g1", "buena"),
    ("V5_costo_espera", "neutral"),        # opera pero no baja el costo
]
# Corridas de ABIDES del repositorio. Las de 1.000 episodios cuestan más que la red inicial muestreando (mala); las de 100
# episodios no se distinguen de ella (neutral).
ABIDES = [("data/colab_resultados/d3_1000ep", "mala", 1000), ("data/colab_resultados/d3_estabilidad", "neutral", 100)]


def _entrenar(args):
    import torch
    torch.set_num_threads(1)
    from scripts.experimentos_recompensa_ps import _catalogo
    from src.experiments import entrenamiento_variantes as ev

    nombre, semilla, episodios, etiqueta = args
    variante, cfg = _catalogo()[nombre]
    carpeta = DIR_POISSON / f"{nombre}_s{semilla}"
    carpeta.mkdir(parents=True, exist_ok=True)
    csv_up = carpeta / "entrenamiento_apertura.csv"
    if csv_up.exists():
        csv_up.unlink()
    _, _, registro, _ = ev.entrenar(variante, semilla, episodios, q_slice=5000, cfg=cfg, csv_path=csv_up)
    with open(carpeta / "monitoreo_episodios.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["episodio", "seed", "tramo", "pasos", "retorno", "q_ejecutado", "cumplimiento", "slippage_bps",
                    "pct_espera", "pct_mercado", "pct_limite_compra"])
        for i, r in enumerate(registro, 1):
            w.writerow([i, semilla + i, "apertura", 30, r["retorno"], r["cumplimiento_voluntario"] * 5000, r["cumplimiento_voluntario"],
                        r["slippage_bps"], r["pct_espera"], r["pct_mercado"], r["pct_limite"]])
    (carpeta / "etiqueta.json").write_text(json.dumps({"etiqueta": etiqueta, "variante": nombre, "semilla": semilla,
                                                       "episodios": episodios}), encoding="utf-8")
    return carpeta.name


def generar(episodios: int, procesos: int) -> None:
    DIR_POISSON.mkdir(parents=True, exist_ok=True)
    trabajos = [(n, s, episodios, e) for n, e in CORRIDAS_POISSON for s in SEMILLAS]
    with ProcessPoolExecutor(max_workers=procesos) as pool:
        for nombre in pool.map(_entrenar, trabajos):
            print("listo", nombre, flush=True)


# ---------------------------------------------------------------------------
# Cruce de alertas y etiquetas
# ---------------------------------------------------------------------------

def cargar_corridas() -> List[Dict]:
    from src.training.monitoreo import leer_actualizaciones, leer_episodios
    corridas: List[Dict] = []
    for sub in sorted(DIR_POISSON.glob("*_s*")):
        et = sub / "etiqueta.json"
        if et.exists():
            meta = json.loads(et.read_text(encoding="utf-8"))
            corridas.append({"nombre": sub.name, "origen": "Poisson (PC)", "etiqueta": meta["etiqueta"], "episodios": meta["episodios"],
                             "eps": leer_episodios(sub / "monitoreo_episodios.csv"),
                             "ups": leer_actualizaciones(sub / "entrenamiento_apertura.csv")})
    for ruta, etiqueta, n in ABIDES:
        for sub in sorted((REPO_ROOT / ruta).glob("d3_opcion*_s*")):
            if not (sub / "monitoreo_episodios.csv").exists() or not (sub / "entrenamiento_apertura.csv").exists():
                continue
            eps = leer_episodios(sub / "monitoreo_episodios.csv")
            if len(eps) < 0.9 * n:
                continue
            corridas.append({"nombre": f"ABIDES {sub.name}{' (' + str(n) + ' ep)'}", "origen": "ABIDES (Colab)", "etiqueta": etiqueta,
                             "episodios": n, "eps": eps, "ups": leer_actualizaciones(sub / "entrenamiento_apertura.csv")})
    return corridas


def tabla_alertas(corridas: Sequence[Dict], umbrales=None) -> List[Dict]:
    from src.training.monitoreo import evaluar_alertas
    filas = []
    for c in corridas:
        al = evaluar_alertas(c["eps"], c["ups"], None, umbrales)
        filas.append({"nombre": c["nombre"], "origen": c["origen"], "etiqueta": c["etiqueta"],
                      "alertas": {a.codigo: a.nivel for a in al}})
    return filas


def metricas_por_alerta(filas: Sequence[Dict]) -> Dict[str, Dict[str, int]]:
    """Por código: cuántas corridas de cada etiqueta avisan. Una buena alerta avisa en las malas y casi nunca en las buenas."""
    codigos = sorted({c for f in filas for c in f["alertas"]})
    out = {}
    for c in codigos:
        out[c] = {et: sum(1 for f in filas if f["etiqueta"] == et and c in f["alertas"]) for et in ("mala", "neutral", "buena")}
    totales = {et: sum(1 for f in filas if f["etiqueta"] == et) for et in ("mala", "neutral", "buena")}
    return {"por_alerta": out, "totales": totales}


def cifras_por_corrida(corridas: Sequence[Dict]) -> List[Dict]:
    """Las cantidades con que se eligieron los umbrales de la alerta «la recompensa sube y el costo no» y de la entropía:
    mejora del retorno (fracción del valor inicial), mejora del costo (bps), pico del crítico y entropía final."""
    import math

    def m(f, k):
        v = np.array([x[k] for x in f if k in x], float)
        v = v[np.isfinite(v)]
        return float(v.mean()) if len(v) else float("nan")

    filas = []
    for c in corridas:
        e = c["eps"]
        w = min(100, len(e) // 2)
        ri, rf, si, sf = m(e[:w], "retorno"), m(e[-w:], "retorno"), m(e[:w], "slippage_bps"), m(e[-w:], "slippage_bps")
        lc = np.array([u["loss_critic"] for u in c["ups"] if math.isfinite(u["loss_critic"])])
        ent = float(np.mean([u["entropia"] for u in c["ups"][-5:]])) / math.log(240)
        filas.append({"nombre": c["nombre"], "etiqueta": c["etiqueta"], "ventana": w,
                      "mejora_retorno": (rf - ri) / max(abs(ri), 1e-9), "mejora_costo": si - sf,
                      "pico_critico": float(lc.max() / max(np.median(lc), 1e-9)), "entropia": ent})
    return filas


def _tabla_alertas_md(filas, metr) -> List[str]:
    tot = metr["totales"]
    L = ["| Alerta | Malas que avisan | Neutrales que avisan | **Buenas que avisan (falsas alarmas)** |", "|---|---:|---:|---:|"]
    for c in sorted(metr["por_alerta"]):
        m = metr["por_alerta"][c]
        L.append(f"| `{c}` | {m['mala']} de {tot['mala']} | {m['neutral']} de {tot['neutral']} | **{m['buena']} de {tot['buena']}** |")
    return L


def informe(filas_antes, metr_antes, filas_ahora, metr_ahora, cifras) -> str:
    tot = metr_ahora["totales"]
    f = lambda x, d=2: f"{x:+.{d}f}".replace(".", ",") if np.isfinite(x) else "—"
    L = ["# Calibración de las alertas del monitoreo (tarea 3.1.4)", "",
         "**Elaborado por:** PS con apoyo de Claude Code (uso autorizado por la universidad). Sprint 6. Se genera con `scripts/calibrar_monitoreo_ps.py`.", "",
         f"Las alertas de `src/training/monitoreo.py` se escribieron mirando lo que pasó en la 2.3.5. Aquí se prueban con {len(filas_ahora)} corridas "
         f"cuyo resultado ya se conoce ({tot['mala']} malas, {tot['neutral']} neutrales y {tot['buena']} buenas; ver el encabezado de `scripts/calibrar_monitoreo_ps.py`). "
         "La etiqueta sale de la evaluación de cada corrida, nunca de las alertas. **Una buena alerta avisa en las malas y casi nunca en las buenas.**", "",
         "## 1. Qué se encontró con los umbrales originales", ""] + _tabla_alertas_md(filas_antes, metr_antes) + [
         "", "- **`ENTROPIA_COLAPSADA` daba falsas alarmas:** la entropía de las corridas buenas queda entre el 50 % y el 69 % del máximo, igual que la de varias malas, así que por sí sola no distingue.",
         "- **`PICO_PERDIDA_CRITICO` no separaba nada:** con una penalización terminal el crítico tiene picos grandes en las corridas buenas (400 a 1.000 veces la mediana) y no en las malas (10 a 60).",
         "- **Faltaba una alerta para el problema de fondo:** en las corridas de 1.000 episodios de ABIDES la recompensa mejora (45 % a 96 %) y el costo no, y solo avisaban las de entropía.", "",
         "## 2. Cambios", "",
         "| Cambio | Antes | Ahora | Por qué |", "|---|---|---|---|",
         "| `ENTROPIA_COLAPSADA` | crítica por debajo del 60 % de la entropía máxima | **aviso** por debajo del 40 %; crítica solo si además hay espera alta o incumplimiento | La entropía baja no es mala por sí sola |",
         "| `ENTROPIA_BAJA` | aviso por debajo del 90 % | **informativa** | Se concentra toda política que aprende: avisaba en las 4 corridas buenas |",
         "| `PICO_PERDIDA_CRITICO` | 20 veces la mediana | 1.000 veces (sigue siendo informativa) | Con penalización terminal los picos son normales |",
         "| **`RECOMPENSA_SUBE_COSTO_NO` (nueva)** | no existía | aviso si el retorno medio mejora ≥ 40 % y el slippage baja menos de 1,5 bps; ventanas de 100 episodios y mínimo de 200 | Detecta la red que optimiza la recompensa y no el costo |", "",
         "## 3. Resultado con los umbrales calibrados", ""] + _tabla_alertas_md(filas_ahora, metr_ahora) + [
         "", "## 4. Cifras que sustentan los umbrales", "",
         "Mejora del retorno (fracción del valor inicial) y del costo (bps) entre la primera y la última ventana, pico del crítico (veces la mediana) y entropía final (% del máximo).", "",
         "| Corrida | Etiqueta | Ventana | Mejora del retorno | Mejora del costo (bps) | Pico del crítico | Entropía final |", "|---|---|---:|---:|---:|---:|---:|"]
    orden = {"mala": 0, "neutral": 1, "buena": 2}
    for c in sorted(cifras, key=lambda c: (orden[c["etiqueta"]], c["nombre"])):
        L.append(f"| {c['nombre']} | {c['etiqueta']} | {c['ventana']} | {f(c['mejora_retorno'])} | {f(c['mejora_costo'], 1)} | {c['pico_critico']:.0f} | {100 * c['entropia']:.0f} % |")
    L += ["", "## 5. Detalle de alertas por corrida (umbrales calibrados)", "", "| Corrida | Origen | Etiqueta | Alertas |", "|---|---|---|---|"]
    for r in sorted(filas_ahora, key=lambda r: (orden[r["etiqueta"]], r["nombre"])):
        txt = ", ".join(f"`{c}` ({n.lower()})" for c, n in sorted(r["alertas"].items())) or "—"
        L.append(f"| {r['nombre']} | {r['origen']} | {r['etiqueta']} | {txt} |")
    L += ["", "## 6. Límites", "",
          "- Son pocas corridas (12 de Poisson y 15 de ABIDES) y las etiquetas «mala» de ABIDES vienen de un solo estudio (D3).",
          "- Las corridas de Poisson son más fáciles de calibrar que las de ABIDES; los umbrales de la alerta nueva se confirmarán con las corridas de la confirmación en ABIDES.",
          "- La alerta nueva no avisa en una corrida con la recompensa empeorando (por ejemplo, penalización con γ = 0,95), pero ahí ya avisan las de espera y cumplimiento.", "",
          "🤖 Generado con [Claude Code](https://claude.com/claude-code)", ""]
    return "\n".join(L)


def main(argv: Optional[Sequence[str]] = None) -> Optional[Path]:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--generar", action="store_true", help="entrena las corridas de Poisson y escribe sus archivos")
    ap.add_argument("--episodios", type=int, default=1000)
    ap.add_argument("--procesos", type=int, default=6)
    ap.add_argument("--out-md", default=str(REPO_ROOT / "docs/calibracion_monitoreo_PS.md"))
    ap.add_argument("--out-json", default=str(REPO_ROOT / "data/analysis/calibracion_monitoreo.json"))
    args = ap.parse_args(argv)
    if args.generar:
        generar(args.episodios, args.procesos)
        return None
    from src.training.monitoreo import UMBRALES_ANTERIORES
    corridas = cargar_corridas()
    antes = tabla_alertas(corridas, UMBRALES_ANTERIORES)
    ahora = tabla_alertas(corridas)
    m_antes, m_ahora = metricas_por_alerta(antes), metricas_por_alerta(ahora)
    cifras = cifras_por_corrida(corridas)
    Path(args.out_md).write_text(informe(antes, m_antes, ahora, m_ahora, cifras), encoding="utf-8")
    Path(args.out_json).write_text(json.dumps({"antes": {"filas": antes, "metricas": m_antes}, "ahora": {"filas": ahora, "metricas": m_ahora},
                                               "cifras": cifras}, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Informe: {args.out_md}")
    return Path(args.out_md)


if __name__ == "__main__":
    main()
