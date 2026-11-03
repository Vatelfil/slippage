"""Confirmación C-6c de los escenarios de liquidez v3 (desviación 10). BF, 2 nov 2026, con apoyo de Claude Code.

El criterio se fijó el 2 de noviembre ANTES de correr el C-6c (R6; `DESVIACIONES_TITULO1_VS_IMPLEMENTACION.md`, sección 10):
comprar 5.000 acciones a mercado en FALABELLA, apertura, ventana de 15 minutos, 60 semillas nuevas (8101 a 8160). La v3 queda
CONFIRMADA si baja − media > 0 y media − alta > 0, las dos con IC 95 % bootstrap pareado por semilla (10.000 remuestreos,
percentil, semilla 0) que excluya el 0 y con los 60 pares completos. Si no, los escenarios se informan como «profundidad del
market maker ×4 / ×1 / ×0,25», sin nombres de liquidez.

Lee el JSON que escribe `scripts/colab/c6_escenarios_liquidez_bf.py` (de PS, no se modifica). No usa su `veredicto`: ese
veredicto pide IC > 0 solo en baja − media y en media − alta le basta con que la media sea ≥ 0.

Los escenarios se identifican por su FACTOR de `mm_pov` (baja = ×4, media = ×1, alta = ×0,25), no por el nombre. Así el mismo
cálculo se puede aplicar, solo como lectura, al C-6b (que usó los nombres de la v2, al revés).
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence

import numpy as np

CRITERIO: Dict = {
    "heuristica": "agresiva_market",
    "q_slice": 5000,
    "entorno": "abides",
    "ticker": "FALABELLA",
    "tramo": "apertura",
    "ventana_min": 15,
    "seed_base": 8100,
    "n_semillas": 60,
    "claves_abides": ["mm_pov"],
    "factores": {"baja": 4.0, "media": 1.0, "alta": 0.25},
    "n_boot": 10000,
    "semilla_boot": 0,
    "nivel": 0.95,
}

CONFIRMADA = "CONFIRMADA"
NO_CONFIRMADA = "NO CONFIRMADA"
NO_EVALUABLE = "NO EVALUABLE"

NOMBRES_SIN_LIQUIDEZ = {"baja": "mm_pov ×4", "media": "mm_pov ×1", "alta": "mm_pov ×0,25"}


def semillas(criterio: Dict = CRITERIO) -> List[int]:
    """Semillas que usa el script del C-6 con `--seed-base` y `--n-semillas`: seed_base + 1, ..., seed_base + n."""
    return [int(criterio["seed_base"]) + i for i in range(1, int(criterio["n_semillas"]) + 1)]


def diferencia_pareada(a: Sequence[Optional[float]], b: Sequence[Optional[float]], n_boot: int = 10000,
                       semilla: int = 0, nivel: float = 0.95) -> Dict:
    """a − b por semilla (misma posición = misma semilla) con IC bootstrap por percentil. Las semillas sin dato en
    alguno de los dos se descartan y se cuentan en `n_descartadas`."""
    if len(a) != len(b):
        raise ValueError(f"las dos listas deben tener una entrada por semilla ({len(a)} != {len(b)})")
    d = [float(x) - float(y) for x, y in zip(a, b)
         if x is not None and y is not None and math.isfinite(float(x)) and math.isfinite(float(y))]
    out = {"n": len(d), "n_descartadas": len(a) - len(d), "media": float("nan"), "ic_bajo": float("nan"),
           "ic_alto": float("nan"), "n_boot": int(n_boot), "semilla_boot": int(semilla), "nivel": float(nivel)}
    if len(d) < 2:
        return out
    arr = np.asarray(d, dtype=float)
    rng = np.random.default_rng(semilla)
    medias = arr[rng.integers(0, len(arr), size=(int(n_boot), len(arr)))].mean(axis=1)
    cola = 100.0 * (1.0 - nivel) / 2.0
    out.update({"media": float(arr.mean()), "ic_bajo": float(np.percentile(medias, cola)),
                "ic_alto": float(np.percentile(medias, 100.0 - cola))})
    return out


def problemas_de_firma(firma: Dict, criterio: Dict = CRITERIO) -> List[str]:
    """Lo que no coincide entre la firma del JSON y el criterio fijado (vacío si todo coincide)."""
    p = []
    for k in ("entorno", "ticker", "tramo", "ventana_min", "seed_base", "n_semillas"):
        if firma.get(k) != criterio[k]:
            p.append(f"{k}: {firma.get(k)!r} (se esperaba {criterio[k]!r})")
    if int(criterio["q_slice"]) not in (firma.get("tamanos") or []):
        p.append(f"tamanos: {firma.get('tamanos')!r} no incluye {criterio['q_slice']}")
    if list(firma.get("claves_abides") or []) != list(criterio["claves_abides"]):
        p.append(f"claves_abides: {firma.get('claves_abides')!r} (se esperaba {criterio['claves_abides']!r})")
    factores = sorted(float(f) for f in (firma.get("escenarios") or {}).values())
    if factores != sorted(float(f) for f in criterio["factores"].values()):
        p.append(f"factores de los escenarios: {factores} (se esperaba {sorted(criterio['factores'].values())})")
    return p


def _resultado_por_factor(resultados: Dict[str, Dict], factor: float, heuristica: str, q: int) -> Optional[Dict]:
    for r in resultados.values():
        if (r.get("heuristica") == heuristica and int(r.get("q_slice", -1)) == q
                and math.isclose(float(r.get("factor", float("nan"))), factor)):
            return r
    return None


def evaluar(datos: Dict, criterio: Dict = CRITERIO) -> Dict:
    """Aplica el criterio al JSON del C-6 (claves `firma` y `resultados`). Devuelve el veredicto y la tabla."""
    problemas = problemas_de_firma(datos.get("firma", {}), criterio)
    h, q, n_esp = criterio["heuristica"], int(criterio["q_slice"]), int(criterio["n_semillas"])
    filas: Dict[str, Dict] = {}
    for nombre, factor in criterio["factores"].items():
        r = _resultado_por_factor(datos.get("resultados", {}), float(factor), h, q)
        if r is None:
            problemas.append(f"falta {h} con {q} acciones en el factor ×{factor:g} ({nombre})")
            continue
        por = list(r.get("slippage_por_semilla") or [])
        if len(por) != n_esp:
            problemas.append(f"{nombre} (×{factor:g}): {len(por)} semillas (se esperaban {n_esp})")
        filas[nombre] = {"factor": float(factor), "nombre_en_json": r.get("escenario"),
                         "costo_medio_bps": r.get("slippage_bps_medio"), "cumplimiento": r.get("cumplimiento_medio"),
                         "por_semilla": por}
    res: Dict = {"criterio": {k: v for k, v in criterio.items()}, "problemas": problemas,
                 "escenarios": {k: {kk: vv for kk, vv in v.items() if kk != "por_semilla"} for k, v in filas.items()}}
    if set(filas) != set(criterio["factores"]) or any(len(f["por_semilla"]) != n_esp for f in filas.values()):
        res.update({"veredicto": NO_EVALUABLE, "texto": "No se puede aplicar el criterio: " + "; ".join(problemas)})
        return res
    kw = {"n_boot": criterio["n_boot"], "semilla": criterio["semilla_boot"], "nivel": criterio["nivel"]}
    comps = {"baja_menos_media": diferencia_pareada(filas["baja"]["por_semilla"], filas["media"]["por_semilla"], **kw),
             "media_menos_alta": diferencia_pareada(filas["media"]["por_semilla"], filas["alta"]["por_semilla"], **kw)}
    for c in comps.values():
        c["cumple"] = bool(c["n"] == n_esp and c["media"] > 0 and c["ic_bajo"] > 0)
    res["comparaciones"] = comps
    incompletos = [k for k, c in comps.items() if c["n"] != n_esp]
    if incompletos:
        problemas.append("pares incompletos en " + ", ".join(f"{k} ({comps[k]['n']} de {n_esp})" for k in incompletos))
    if problemas:
        res.update({"veredicto": NO_EVALUABLE, "texto": "No se puede aplicar el criterio: " + "; ".join(problemas)})
    elif all(c["cumple"] for c in comps.values()):
        res.update({"veredicto": CONFIRMADA,
                    "texto": "La v3 queda confirmada: con la compra a mercado, baja cuesta más que media y media más "
                             "que alta, con los dos IC 95 % sobre 0."})
    else:
        fallan = [k for k, c in comps.items() if not c["cumple"]]
        res.update({"veredicto": NO_CONFIRMADA,
                    "texto": "No se confirma (" + ", ".join(fallan) + " no excluye el 0 por arriba). Los escenarios se "
                             "informan como profundidad del market maker ×4 / ×1 / ×0,25, sin nombres de liquidez."})
    return res


def _num(x: Optional[float]) -> str:
    """Número con signo y coma decimal (diferencias en bps)."""
    if x is None or not math.isfinite(float(x)):
        return "—"
    return f"{float(x):+.2f}".replace(".", ",")


def _bps(x: Optional[float]) -> str:
    if x is None or not math.isfinite(float(x)):
        return "—"
    return f"{float(x):.2f}".replace(".", ",")


def tabla_md(res: Dict) -> str:
    """Tabla escenario → costo medio → diferencia pareada → IC → cumple / no cumple, en Markdown."""
    esc, comps = res.get("escenarios", {}), res.get("comparaciones", {})
    lineas = ["| Escenario | Factor `mm_pov` | Costo medio (bps) | Diferencia pareada | Media (bps) | IC 95 % | n | ¿Cumple? |",
              "|---|---:|---:|---|---:|---|---:|:---:|"]
    pares = {"baja": ("baja_menos_media", "baja − media"), "media": ("media_menos_alta", "media − alta")}
    for nombre in ("baja", "media", "alta"):
        e = esc.get(nombre, {})
        clave, etiqueta = pares.get(nombre, (None, ""))
        c = comps.get(clave, {}) if clave else {}
        ic = f"[{_num(c.get('ic_bajo'))}; {_num(c.get('ic_alto'))}]" if c else ""
        cumple = ("sí" if c.get("cumple") else "no") if c else ""
        factor = f"{e.get('factor', float('nan')):g}".replace(".", ",")
        lineas.append(f"| {nombre} | ×{factor} | {_bps(e.get('costo_medio_bps'))} | {etiqueta} | "
                      f"{_num(c.get('media')) if c else ''} | {ic} | {c.get('n', '') if c else ''} | {cumple} |")
    lineas.append("")
    lineas.append(f"**Veredicto: {res.get('veredicto')}.** {res.get('texto', '')}")
    return "\n".join(lineas) + "\n"
