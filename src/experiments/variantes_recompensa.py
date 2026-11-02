"""Variantes de la recompensa y del cierre de ventana del Ejecutor (BORRADOR de PS para BF y MR).

Por qué existe este módulo
--------------------------
Con la recompensa actual (R_E de la 2.2.3) las redes aprenden a no operar: en Poisson llegan a esperar el 97-100 % de los
pasos, y en ABIDES la recompensa de entrenamiento sube mientras el slippage frente al precio de llegada no baja. Las causas
que encontramos están en `docs/diagnostico_recompensa_PS.md`. Aquí se prueban los arreglos sin tocar los entornos de BF ni
el entrenador de MR: todo vive en un envoltorio (`EntornoVariante`) que se activa con banderas y deja el comportamiento
original intacto cuando todas están apagadas.

Qué se puede cambiar
--------------------
- ``liquidar_al_final``: lo que no se compró al terminar la ventana se compra a mercado, pagando lo que cueste barrer el
  libro. Así esperar deja de ser gratis: dejar todo para el final sale caro.
- ``penalizacion_bps``: castigo por cada acción pendiente al terminar la ventana (en bps del precio de llegada, por acción
  del slice). Es la alternativa blanda a liquidar.
- ``costo_espera_bps``: costo denso por tener inventario pendiente, paso a paso (si no se compra nada en toda la ventana
  suma ese total en bps). A diferencia de la penalización, que llega una sola vez al final, no depende del factor de
  descuento. Es la versión práctica del término de riesgo sobre lo pendiente (opción A de D3).
- ``recompensa="is_llegada"``: en vez de comparar con el precio medio de cada instante (R_E original), compara con el precio
  de llegada, que es lo mismo que mide la evaluación (implementation shortfall).
- ``aleatorizar``: en cada episodio el tamaño del slice y la ventana se sortean entre los valores que de verdad usará el
  Maestro, para que la red no entrene solo con 1.000 acciones y 15 minutos.

Nota técnica: la penalización, el costo de espera y la recompensa de IS solo leen el `info` del entorno, así que sirven
también con ABIDES (se leen igual que en los benchmarks, ver `src/analysis/benchmarks.py`). La liquidación forzada necesita
el simulador por dentro (`_sim`) y por ahora solo existe para Poisson. Es aceptable para un borrador de pruebas; si BF
decide adoptar alguna variante, lo correcto es llevarla al entorno y a la 2.2.3.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

from src.analysis.benchmarks import _leer_paso, _leer_reset
from src.config.market_params import BETA_RIESGO_EJECUTOR

# Valores que el Maestro puede pedir (docs/schemas/SM_schema.json): ventana en minutos y tamaños de slice típicos de las
# meta-órdenes (con 10 % del día una orden de 30.000 acciones asigna entre 5 % y 50 % de lo pendiente por decisión).
VENTANAS_MAESTRO = (1, 5, 10, 15)
Q_SLICE_MAESTRO = (1000, 2000, 5000, 10000, 20000)

# Tope de pasos extra para liquidar el remanente. Cada paso deja que el libro se rellene antes de volver a comprar.
MAX_PASOS_LIQUIDACION = 10

LIMIT_SELL_IDX = 1   # índice de LIMIT_SELL en EjecutorActionSpace: el proyecto solo compra, así que equivale a esperar
LIMIT_BUY_IDX, MARKET_IDX = 0, 2


@dataclass(frozen=True)
class Variante:
    nombre: str
    recompensa: str = "original"          # "original" | "is_llegada"
    liquidar_al_final: bool = False
    penalizacion_bps: float = 0.0
    costo_espera_bps: float = 0.0         # costo denso de tener inventario pendiente (ver `_costo_espera`)
    aleatorizar: bool = False

    def descripcion(self) -> str:
        partes = [f"recompensa {self.recompensa}"]
        if self.liquidar_al_final:
            partes.append("liquidación forzada al final")
        if self.penalizacion_bps:
            partes.append(f"penalización {self.penalizacion_bps:g} bps por acción pendiente")
        if self.costo_espera_bps:
            partes.append(f"costo de espera {self.costo_espera_bps:g} bps repartido en la ventana")
        if self.aleatorizar:
            partes.append("tamaño y ventana aleatorios")
        return ", ".join(partes)


# Variantes de la etapa A (solo cambian la recompensa o el cierre) y la de control.
V0 = Variante("V0_original")
V1 = Variante("V1_liquidacion", liquidar_al_final=True)
V2 = Variante("V2_penalizacion", penalizacion_bps=30.0)
V3 = Variante("V3_is_liquidacion", recompensa="is_llegada", liquidar_al_final=True)
V4 = Variante("V4_is_penalizacion", recompensa="is_llegada", penalizacion_bps=30.0)
ETAPA_A = (V0, V1, V2, V3, V4)
# Etapa A2: se agregan una penalización más fuerte y el costo de espera denso.
V2B = Variante("V2b_penalizacion100", penalizacion_bps=100.0)
V5 = Variante("V5_costo_espera", costo_espera_bps=100.0)
V6 = Variante("V6_is_costo_espera", recompensa="is_llegada", costo_espera_bps=100.0)


class EntornoVariante:
    """Envuelve un `EjecutorEnvPoissonFallback` y aplica la variante a la recompensa y al cierre de la ventana."""

    def __init__(self, env, variante: Variante):
        self.env = env
        self.variante = variante
        self.max_steps = env.max_steps
        # Poisson guarda q_slice; el entorno de ABIDES lo guarda dentro (parent_order_size)
        q = getattr(env, "q_slice", None)
        self.q_slice = float(q if q is not None else env._inner.parent_order_size)
        self._pendiente_actual = self.q_slice
        self._p_ref = 0.0
        self.pasos: List[Tuple[float, float]] = []      # (cantidad, precio) de cada compra, incluida la liquidación
        self.acciones_tipo: List[int] = []
        self.q_liquidado = 0.0
        self.recompensa_total = 0.0
        self.recompensa_liq = 0.0       # lo que valió liquidar, por separado de lo que vio el agente

    # --- ciclo de vida -------------------------------------------------
    def reset(self, *args, **kwargs):
        obs, info = self.env.reset(*args, **kwargs)
        self._p_ref = _leer_reset(info)
        self._pendiente_actual = self.q_slice
        self.pasos, self.acciones_tipo = [], []
        self.q_liquidado, self.recompensa_total, self.recompensa_liq = 0.0, 0.0, 0.0
        return obs, info

    def close(self):
        if hasattr(self.env, "close"):
            self.env.close()

    def __getattr__(self, nombre):       # lo que no define el envoltorio lo resuelve el entorno
        return getattr(self.env, nombre)

    # --- paso ----------------------------------------------------------
    def step(self, action):
        obs, r, done, trunc, info = self.env.step(action)
        done = bool(done or trunc)
        a = np.asarray(action).reshape(-1)
        self.acciones_tipo.append(int(a[0]))
        q, p = _leer_paso(info, self._p_ref)
        pend = info.get("q_pendiente", info.get("remaining"))     # Poisson: q_pendiente; ABIDES: remaining
        self._pendiente_actual = float(pend) if pend is not None else self._pendiente_actual
        if q > 0:
            self.pasos.append((q, p))
        if self.variante.recompensa == "is_llegada":
            # Lo que cuesta comprar frente al precio de llegada, por acción del slice; lo que no se compra no cuesta nada
            # todavía (eso lo cobra la liquidación o la penalización al cierre).
            r = -(p - self._p_ref) * q / self.q_slice if q > 0 else 0.0
        if self.variante.costo_espera_bps and self.q_slice > 0:
            r -= self._costo_espera()
        if done and self._pendiente_actual > 0:
            r += self._cierre()
        self.recompensa_total += float(r)
        info = dict(info)
        info["q_liquidado"] = self.q_liquidado
        return obs, float(r), done, False, info

    # --- cierre de la ventana ------------------------------------------
    def liquidar(self) -> Tuple[float, float]:
        """Compra a mercado lo que queda pendiente, barriendo el libro durante hasta MAX_PASOS_LIQUIDACION pasos.
        Devuelve (cantidad, costo de la recompensa por acción del slice) según la recompensa de la variante."""
        if not hasattr(self.env, "_sim"):
            raise NotImplementedError("la liquidación forzada solo está implementada para el simulador de Poisson")
        sim = self.env._sim
        total_q, recompensa = 0.0, 0.0
        for _ in range(MAX_PASOS_LIQUIDACION):
            pendiente = self.env.q_pendiente
            if pendiente <= 0:
                break
            sim.advance()
            q, p = sim.execute_market_buy(pendiente)
            if q <= 0:
                continue
            self.env.q_pendiente = max(pendiente - q, 0.0)
            self._pendiente_actual = self.env.q_pendiente
            self.pasos.append((q, p))
            total_q += q
            if self.variante.recompensa == "is_llegada":
                recompensa -= (p - self._p_ref) * q / self.q_slice
            else:
                recompensa += (sim.mid_price - p) * q / self.q_slice
        self.q_liquidado += total_q
        self.recompensa_liq += recompensa
        return total_q, recompensa

    def _costo_espera(self) -> float:
        """Costo de un paso con inventario pendiente: kappa (en bps del precio de llegada) repartido en los pasos de la
        ventana y proporcional a la fracción del slice que sigue sin comprar. Se calcula con lo pendiente después del paso."""
        kappa = self.variante.costo_espera_bps * 1e-4 * self._p_ref
        return kappa * (self._pendiente_actual / self.q_slice) / max(self.max_steps, 1)

    def _cierre(self) -> float:
        extra = 0.0
        if self.variante.liquidar_al_final:
            _, extra = self.liquidar()
        if self.variante.penalizacion_bps and self._pendiente_actual > 0:
            # eta en CLP por acción pendiente, proporcional al precio de llegada
            eta = self.variante.penalizacion_bps * 1e-4 * self._p_ref
            extra -= eta * self._pendiente_actual / self.q_slice
        return extra

    # --- resumen de un episodio ----------------------------------------
    def resumen(self) -> Dict[str, float]:
        q = float(sum(x for x, _ in self.pasos))
        notional = float(sum(x * p for x, p in self.pasos))
        p_prom = notional / q if q > 0 else float("nan")
        tipos = np.asarray(self.acciones_tipo)
        n = max(len(tipos), 1)
        return {
            "q_ejecutado": q, "q_liquidado": self.q_liquidado,
            "cumplimiento_total": q / self.q_slice,
            "cumplimiento_voluntario": (q - self.q_liquidado) / self.q_slice,
            "slippage_bps": (p_prom - self._p_ref) / self._p_ref * 1e4 if q > 0 else float("nan"),
            "pct_espera": float((tipos == LIMIT_SELL_IDX).sum()) / n,
            "pct_mercado": float((tipos == MARKET_IDX).sum()) / n,
            "pct_limite": float((tipos == LIMIT_BUY_IDX).sum()) / n,
            "retorno": self.recompensa_total,
            "retorno_liquidacion": self.recompensa_liq,
        }


# --------------------------------------------------------------------------
# Fábricas de entorno
# --------------------------------------------------------------------------

def _entorno_base(tramo: str, q_slice: float, ventana_min: int, seed: int, ticker: str, beta: float, riesgo_sobre: str):
    from src.envs.fallback_poisson_env import EjecutorEnvPoissonFallback
    return EjecutorEnvPoissonFallback(executor_id=tramo, q_slice=q_slice, ventana_min=ventana_min, seed=seed,
                                      ticker=ticker, beta=beta, riesgo_sobre=riesgo_sobre)


def fabrica_entrenamiento(variante: Variante, ticker: str = "FALABELLA", beta: float = BETA_RIESGO_EJECUTOR,
                          riesgo_sobre: str = "ejecutado", registro: Optional[List[Dict[str, float]]] = None,
                          semilla_sorteo: int = 0) -> Callable:
    """Fábrica con la firma que usa `PPOTrainer.train_executor_episodes`. Si se pasa `registro`, al terminar cada episodio
    se agrega el resumen del episodio (retorno, cumplimiento, pasos en espera, slippage)."""
    rng = np.random.default_rng(semilla_sorteo)
    ultimo: Dict[str, Any] = {"env": None}

    def cerrar_anterior() -> None:
        env = ultimo["env"]
        if env is not None and registro is not None and env.pasos is not None:
            registro.append(env.resumen())
        ultimo["env"] = None

    def fabrica(executor_id="apertura", q_slice=1000, ventana_min=15, seed=0, **_):
        cerrar_anterior()                      # el entrenador crea el entorno siguiente al terminar el anterior
        if variante.aleatorizar:
            q_slice = int(rng.choice(Q_SLICE_MAESTRO))
            ventana_min = int(rng.choice(VENTANAS_MAESTRO))
        base = _entorno_base(executor_id, q_slice, ventana_min, seed, ticker, beta, riesgo_sobre)
        env = EntornoVariante(base, variante)
        ultimo["env"] = env
        return env

    fabrica.cerrar = cerrar_anterior            # para volcar el último episodio al terminar el entrenamiento
    return fabrica


# --------------------------------------------------------------------------
# Evaluación común a todas las variantes
# --------------------------------------------------------------------------

def _politica_red(net, muestrear: bool, semilla: int):
    import torch
    from src.envs.spaces import EjecutorActionSpace
    espacio = EjecutorActionSpace()
    gen = torch.Generator().manual_seed(int(semilla))

    def politica(obs, paso, max_pasos):
        with torch.no_grad():
            logits, _ = net(torch.as_tensor(obs, dtype=torch.float32).unsqueeze(0))
            if muestrear:
                # generador propio por semilla: el resultado no depende del estado global de torch
                idx = int(torch.multinomial(torch.softmax(logits, dim=-1), 1, generator=gen).item())
            else:
                idx = int(torch.argmax(logits, dim=-1).item())
        return espacio.decode_flat(idx)

    return politica


def _politica_heuristica(nombre: str):
    from src.experiments import beta_sweep as bs
    funcion = bs.POLITICAS[nombre]
    nivel = bs.NIVEL_PASIVO["poisson"]
    return lambda obs, paso, max_pasos: funcion(paso, max_pasos, nivel)


def evaluar(politica_factory: Callable[[int], Callable], semillas: Sequence[int], q_slice: int = 1000,
            ventana_min: int = 15, tramo: str = "apertura", ticker: str = "FALABELLA",
            beta: float = 0.0) -> List[Dict[str, float]]:
    """Corre la política en semillas de evaluación y mide cada episodio igual para todos: lo no comprado voluntariamente se
    liquida a mercado, de modo que el slippage incluye el costo de dejar cosas pendientes y los cumplimientos son
    comparables entre variantes y heurísticas. Devuelve un resumen por semilla."""
    salida = []
    for s in semillas:
        base = _entorno_base(tramo, q_slice, ventana_min, int(s), ticker, beta, "ejecutado")
        env = EntornoVariante(base, Variante("evaluacion"))
        obs, _ = env.reset()
        politica = politica_factory(int(s))
        paso, done = 0, False
        while not done:
            obs, _, done, _, _ = env.step(politica(obs, paso, env.max_steps))
            paso += 1
        if env.env.q_pendiente > 0:
            env.liquidar()
        salida.append(env.resumen())
    return salida


def evaluar_red(net, semillas: Sequence[int], muestrear: bool, **kw) -> List[Dict[str, float]]:
    return evaluar(lambda s: _politica_red(net, muestrear, s), semillas, **kw)


def evaluar_heuristica(nombre: str, semillas: Sequence[int], **kw) -> List[Dict[str, float]]:
    return evaluar(lambda s: _politica_heuristica(nombre), semillas, **kw)


def promedios(resumenes: Sequence[Dict[str, float]]) -> Dict[str, float]:
    """Media de cada métrica entre semillas (se ignoran los NaN, p. ej. episodios sin compras)."""
    claves = resumenes[0].keys()
    return {k: float(np.nanmean([r[k] for r in resumenes])) if not all(np.isnan(r[k]) for r in resumenes) else float("nan")
            for k in claves}
