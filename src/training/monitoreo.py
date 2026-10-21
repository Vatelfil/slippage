"""Monitoreo y registro de metricas de entrenamiento (tarea 3.1.4, Sprint 6).

BORRADOR elaborado por PS con apoyo de Claude Code (adelanto del Sprint 6).

El entrenador PPO (`PPOTrainer`, MR) guarda por cada actualizacion: perdidas, entropia, KL, fraccion recortada y
retorno medio. NO guarda lo que importa para ejecutar una orden: el costo (slippage) y el cumplimiento de cada
episodio, ni que hace la politica (cuanto espera). En el entrenamiento inicial de la 2.3.5 la red aprendio a
"esperar" y eso solo se vio al evaluar (docs/entrenamiento_inicial_2.3.5.md).

Este modulo agrega esa informacion SIN tocar el entrenador: envuelve la fabrica de entornos que recibe
`train_executor_episodes`. Cada episodio deja una fila en un CSV con:

    episodio, seed, tramo, pasos, retorno, q_ejecutado, cumplimiento, slippage_bps,
    pct_espera, pct_mercado, pct_limite_compra

y `evaluar_alertas` revisa esas filas (y las de las actualizaciones PPO) con reglas que salen de lo ocurrido:
politica que se concentra en esperar, cumplimiento bajo, valores no finitos, entropia colapsada, KL o recorte altos.

Uso:

    monitor = MonitorEntrenamiento("<carpeta>/monitoreo_episodios.csv", seed_base=trainer.seed)
    trainer.train_executor_episodes(env_factory=monitor.envolver(factory), ...)
"""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np

N_ACCIONES = 240                       # 3 tipos x 10 volumenes x 8 niveles (EjecutorActionSpace)
ENTROPIA_MAXIMA = math.log(N_ACCIONES)  # entropia de una politica uniforme
ORDEN_LIMIT_BUY, ORDEN_LIMIT_SELL, ORDEN_MARKET = 0, 1, 2   # indices de spaces.ORDER_TYPES
# LIMIT_SELL no se usa: el proyecto solo modela compra y el puente (abides_bridge) y el simulador Poisson lo tratan
# como "esperar" (no envian ninguna orden).

COLUMNAS_EPISODIO = ["episodio", "seed", "tramo", "pasos", "retorno", "q_ejecutado", "cumplimiento",
                     "slippage_bps", "pct_espera", "pct_mercado", "pct_limite_compra"]


def _leer_p_ref(info: Dict[str, Any]) -> Optional[float]:
    """P_referencia en CLP desde el info de reset (Poisson: `p_referencia`; ABIDES: `entry_price` en unidades de cuenta)."""
    if info.get("p_referencia") is not None:
        return float(info["p_referencia"])
    if info.get("entry_price") is not None:
        return float(info["entry_price"]) / float(info.get("unidades_por_clp", 1.0))
    return None


class _EntornoMonitoreado:
    """Envuelve un entorno del Ejecutor: reenvia todo y acumula lo necesario para la fila del episodio."""

    def __init__(self, env: Any, monitor: "MonitorEntrenamiento", kw: Dict[str, Any]):
        self._env, self._monitor, self._kw = env, monitor, kw
        self._pasos: List[Dict[str, float]] = []
        self._acciones: List[int] = []
        self._retorno = 0.0
        self._p_ref: Optional[float] = None
        self._registrado = False

    def reset(self, *args, **kwargs):
        obs, info = self._env.reset(*args, **kwargs)
        self._p_ref = _leer_p_ref(info)
        self._pasos, self._acciones, self._retorno, self._registrado = [], [], 0.0, False
        return obs, info

    def step(self, action):
        obs, r, done, trunc, info = self._env.step(action)
        from src.experiments import beta_sweep as bs   # import tardio: evita ciclos al importar el modulo
        self._pasos.append(bs.step_record(info))
        self._acciones.append(int(np.asarray(action).reshape(-1)[0]))   # el entorno recibe [tipo_de_orden, bucket, nivel]
        self._retorno += float(r)
        return obs, r, done, trunc, info

    def close(self):
        if not self._registrado and self._pasos:
            self._registrado = True
            self._monitor._registrar(self._kw, self._pasos, self._acciones, self._retorno, self._p_ref)
        return self._env.close()

    def __getattr__(self, nombre):   # cualquier otro atributo (action_space, etc.) viene del entorno real
        return getattr(self._env, nombre)


class MonitorEntrenamiento:
    """Registra una fila por episodio en `csv_path` (se agrega al final, asi que sobrevive a cortes y reanudaciones).

    `seed_base`: semilla del entrenador. El entrenador crea el episodio k con `seed = seed_base + k`, asi que
    `episodio = seed - seed_base` coincide con el `episodio` del CSV del entrenador. Sin `seed_base` se numera por orden.
    """

    def __init__(self, csv_path: Union[str, Path], seed_base: Optional[int] = None):
        self.csv_path = Path(csv_path)
        self.seed_base = seed_base
        self._n = 0
        if self.csv_path.exists():
            self._n = len(leer_episodios(self.csv_path))

    def envolver(self, env_factory: Callable) -> Callable:
        def factory(*args, **kw):
            return _EntornoMonitoreado(env_factory(*args, **kw), self, kw)
        return factory

    def _registrar(self, kw: Dict[str, Any], pasos: Sequence[Dict[str, float]], acciones: Sequence[int],
                   retorno: float, p_ref: Optional[float]) -> None:
        from src.experiments import beta_sweep as bs

        q_slice = float(kw.get("q_slice", 0.0))
        p_ref = p_ref if p_ref is not None else float(pasos[0]["p_mid"])
        resumen = bs.summarize_episode(pasos, q_slice, p_ref)
        tipos = np.array(acciones)   # tipo de orden de cada paso
        self._n += 1
        seed = kw.get("seed")
        episodio = (int(seed) - self.seed_base) if (self.seed_base is not None and seed is not None) else self._n
        fila = {"episodio": episodio, "seed": "" if seed is None else int(seed), "tramo": kw.get("executor_id", ""),
                "pasos": len(pasos), "retorno": retorno, "q_ejecutado": resumen["q_ejecutado"],
                "cumplimiento": resumen["cumplimiento"],
                "slippage_bps": "" if resumen["slippage_bps"] is None else resumen["slippage_bps"],
                "pct_espera": float(np.mean(tipos == ORDEN_LIMIT_SELL)),
                "pct_mercado": float(np.mean(tipos == ORDEN_MARKET)),
                "pct_limite_compra": float(np.mean(tipos == ORDEN_LIMIT_BUY))}
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        nuevo = not self.csv_path.exists()
        with open(self.csv_path, "a", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=COLUMNAS_EPISODIO)
            if nuevo:
                w.writeheader()
            w.writerow(fila)


# ---------------------------------------------------------------------------
# Lectura
# ---------------------------------------------------------------------------

def _num(x: str) -> float:
    return float("nan") if x in ("", None) else float(x)


def leer_episodios(path: Union[str, Path]) -> List[Dict[str, float]]:
    """Filas del monitoreo por episodio; si un episodio aparece repetido (corte y reanudacion) queda la ultima fila."""
    with open(path, "r", encoding="utf-8-sig") as fh:
        filas = [{k: (v if k == "tramo" else _num(v)) for k, v in f.items()} for f in csv.DictReader(fh)]
    por_ep: Dict[float, Dict[str, float]] = {}
    for f in filas:
        por_ep[f["episodio"]] = f
    return [por_ep[k] for k in sorted(por_ep)]


def leer_actualizaciones(path: Union[str, Path]) -> List[Dict[str, float]]:
    """Filas del CSV del entrenador (una por actualizacion PPO)."""
    with open(path, "r", encoding="utf-8-sig") as fh:
        return [{k: _num(v) for k, v in f.items()} for f in csv.DictReader(fh)]


# ---------------------------------------------------------------------------
# Alertas
# ---------------------------------------------------------------------------

@dataclass
class Umbrales:
    ventana: int = 50                    # episodios (o actualizaciones) de la ventana final
    cumplimiento_min: float = 0.95       # regla de D3
    cumplimiento_critico: float = 0.50
    espera_alta: float = 0.50            # fraccion de pasos que "esperan"
    espera_subida: float = 0.20          # aumento entre la primera y la ultima ventana
    entropia_aviso: float = 0.90         # fraccion de la entropia maxima
    entropia_critica: float = 0.60
    kl_max: float = 0.02                 # el objetivo del entrenador es 0,015
    recorte_max: float = 0.30
    pico_perdida_critico: float = 20.0   # veces la mediana de la perdida del critico
    brecha_argmax: float = 0.20          # |cumplimiento argmax - muestreado|


@dataclass
class Alerta:
    nivel: str     # "CRITICA", "AVISO" o "INFO"
    codigo: str
    mensaje: str
    datos: Dict[str, Any] = field(default_factory=dict)


def _media(filas: Sequence[Dict[str, float]], clave: str) -> float:
    v = np.array([f[clave] for f in filas if clave in f], dtype=float)
    v = v[np.isfinite(v)]
    return float(v.mean()) if len(v) else float("nan")


def evaluar_alertas(episodios: Sequence[Dict[str, float]] = (), actualizaciones: Sequence[Dict[str, float]] = (),
                    evaluacion: Optional[Dict[str, Any]] = None, umbrales: Optional[Umbrales] = None) -> List[Alerta]:
    """Revisa un entrenamiento. `episodios`: `leer_episodios`; `actualizaciones`: `leer_actualizaciones`;
    `evaluacion`: estado JSON de `entrenamiento_inicial_ps.py` (compara argmax y politica muestreada)."""
    u = umbrales or Umbrales()
    out: List[Alerta] = []

    # 1) valores no finitos en las actualizaciones (el slippage de un episodio sin ejecuciones es NaN a proposito)
    malos = [f.get("episodio") for f in actualizaciones if any(not math.isfinite(v) for v in f.values())]
    if malos:
        out.append(Alerta("CRITICA", "NO_FINITO", f"Valores no finitos en {len(malos)} actualizaciones (primera: episodio {malos[0]:.0f}).",
                          {"episodios": malos[:10]}))

    # 2) lo que hace la politica y si cumple la orden
    if len(episodios) >= 2:
        n = min(u.ventana, max(1, len(episodios) // 2))
        ini, fin = episodios[:n], episodios[-n:]
        cump = _media(fin, "cumplimiento")
        if cump < u.cumplimiento_critico:
            out.append(Alerta("CRITICA", "CUMPLIMIENTO_CRITICO", f"Cumplimiento medio {cump:.3f} en los ultimos {n} episodios (< {u.cumplimiento_critico}).", {"cumplimiento": cump}))
        elif cump < u.cumplimiento_min:
            out.append(Alerta("AVISO", "CUMPLIMIENTO_BAJO", f"Cumplimiento medio {cump:.3f} en los ultimos {n} episodios (< {u.cumplimiento_min}): regla de vigilancia de D3.", {"cumplimiento": cump}))
        esp_f, esp_i = _media(fin, "pct_espera"), _media(ini, "pct_espera")
        if esp_f > u.espera_alta:
            out.append(Alerta("AVISO", "ESPERA_ALTA", f"La politica espera en el {100 * esp_f:.0f} % de los pasos (ultimos {n} episodios).", {"pct_espera": esp_f}))
        if esp_f - esp_i > u.espera_subida:
            out.append(Alerta("AVISO", "ESPERA_EN_AUMENTO", f"La fraccion de pasos en espera subio de {100 * esp_i:.0f} % a {100 * esp_f:.0f} %: la politica puede estar aprendiendo a no ejecutar (R_E sin costo por esperar).", {"inicio": esp_i, "final": esp_f}))
        if len(episodios) >= 2 * u.ventana and math.isfinite(_media(fin, "retorno")) and _media(fin, "retorno") <= _media(ini, "retorno"):
            out.append(Alerta("INFO", "SIN_MEJORA", f"El retorno medio no mejora: {_media(ini, 'retorno'):.2f} (primeros {n}) frente a {_media(fin, 'retorno'):.2f} (ultimos {n}).", {}))

    # 3) estado de la optimizacion PPO
    if actualizaciones:
        ultimas = list(actualizaciones)[-max(1, min(u.ventana // 10, len(actualizaciones))):]
        ent = _media(ultimas, "entropia")
        if math.isfinite(ent):
            rel = ent / ENTROPIA_MAXIMA
            if rel < u.entropia_critica:
                out.append(Alerta("CRITICA", "ENTROPIA_COLAPSADA", f"Entropia al {100 * rel:.0f} % del maximo: la politica casi no explora.", {"relativa": rel}))
            elif rel < u.entropia_aviso:
                out.append(Alerta("AVISO", "ENTROPIA_BAJA", f"Entropia al {100 * rel:.0f} % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.", {"relativa": rel}))
        kl = max((f["kl"] for f in actualizaciones if "kl" in f and math.isfinite(f["kl"])), default=float("nan"))
        if kl > u.kl_max:
            out.append(Alerta("AVISO", "KL_ALTO", f"KL maximo {kl:.4f} (> {u.kl_max}).", {"kl_max": kl}))
        rec = _media(ultimas, "clip_fraction")
        if rec > u.recorte_max:
            out.append(Alerta("AVISO", "RECORTE_ALTO", f"Fraccion recortada media {rec:.2f} (> {u.recorte_max}): las actualizaciones son demasiado grandes.", {"clip": rec}))
        lc = np.array([f["loss_critic"] for f in actualizaciones if "loss_critic" in f and math.isfinite(f["loss_critic"])])
        if len(lc) >= 5 and lc.max() > u.pico_perdida_critico * max(float(np.median(lc)), 1e-9):
            out.append(Alerta("INFO", "PICO_PERDIDA_CRITICO", f"Pico de la perdida del critico ({lc.max():.1f}, mediana {np.median(lc):.2f}).", {}))

    # 4) argmax frente a politica muestreada (estado JSON de la 2.3.5)
    if evaluacion:
        det = (evaluacion.get("evaluacion_entrenada") or {}).get("cumplimiento_medio")
        est = (evaluacion.get("evaluacion_entrenada_estocastica") or {}).get("cumplimiento_medio")
        if det is not None and est is not None and abs(det - est) > u.brecha_argmax:
            out.append(Alerta("CRITICA", "ARGMAX_DISTINTO_DE_MUESTREO", f"Cumplimiento {det:.3f} con argmax y {est:.3f} muestreando: la evaluacion determinista no representa la politica entrenada.", {"argmax": det, "muestreada": est}))
    return out


def resumen_alertas(alertas: Sequence[Alerta]) -> str:
    if not alertas:
        return "Sin alertas."
    orden = {"CRITICA": 0, "AVISO": 1, "INFO": 2}
    return "\n".join(f"[{a.nivel}] {a.codigo}: {a.mensaje}" for a in sorted(alertas, key=lambda a: orden[a.nivel]))
