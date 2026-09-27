"""Simulador de LOB simplificado basado en el modelo de Poisson calibrado
por Benjamin (tarea 2.1.3, `docs/calibracion_poisson_2.1.3_BF.md`).

*** REEMPLAZO TEMPORAL — LEER ANTES DE USAR ***
Este modulo existe SOLO porque Mauricio no ha podido confirmar si ABIDES-Gym
instala (ver PENDIENTE_MAURICIO.md) y el training no puede avanzar con
reward=0.0 indefinidamente. Es exactamente la alternativa que el Titulo I
(seccion 4.3.3.c) ya contemplaba: "modelo de Poisson (alternativa liviana)...
mas facil de calibrar con datos escasos y completamente implementable en
Python con NumPy y SciPy". No reemplaza a ABIDES-Gym como entrega final del
proyecto -- en cuanto Mauricio confirme que ABIDES funciona, este modulo y
`fallback_poisson_env.py` deben eliminarse (ver REEMPLAZO_TEMPORAL_POISSON.md
para la lista exacta de archivos a borrar/revertir).

Que hace: mantiene un libro de ordenes (LOB) sintetico de 5 niveles por lado
(bid/ask), cuya dinamica esta gobernada por los parametros Poisson REALES
calibrados por Benjamin (lambda_plus, lambda_minus, theta) por ticker y tramo
horario. No es ABIDES-Gym (no modela agentes heterogeneos, colas de ordenes
individuales, ni el protocolo ITCH/OUCH) -- es deliberadamente mas simple,
tal como el Titulo I describe esta alternativa.

Fuente de parametros: `data/calibration/poisson_params_<fecha>.json`
(salida real de `src/envs/calibration_poisson.py --all`, tarea 2.1.3 de BF).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CALIBRATION_DIR = REPO_ROOT / "data" / "calibration"

N_LEVELS = 5  # niveles por lado, igual que SE_schema.json (bid_precios/bid_volumenes, 5 c/u)


def find_latest_calibration(calibration_dir: Path = DEFAULT_CALIBRATION_DIR) -> Path:
    """Encuentra el `poisson_params_<fecha>.json` real mas reciente (excluye demo/)."""
    candidates = sorted(
        p for p in calibration_dir.glob("poisson_params_*.json") if p.is_file()
    )
    if not candidates:
        raise FileNotFoundError(
            f"No se encontro ningun poisson_params_*.json real en {calibration_dir}. "
            "Correr primero: python -m src.envs.calibration_poisson --snapshot <fecha> --all"
        )
    return candidates[-1]


def load_calibrated_params(ticker: str, tramo: str,
                            calibration_path: Optional[Path] = None) -> Dict:
    """Carga (lambda_plus, lambda_minus, theta, avg_order_size, spread_roll_bps)
    para un ticker y tramo desde el JSON real de Benjamin.

    Args:
        ticker: sin sufijo .SN (ej. "FALABELLA"), como estan las llaves del JSON.
        tramo: "apertura" | "media_jornada" | "cierre".
    """
    path = calibration_path or find_latest_calibration()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    ticker_key = ticker.replace(".SN", "").upper()
    if ticker_key not in data["params"]:
        raise KeyError(
            f"Ticker '{ticker_key}' no esta en {path}. Disponibles: "
            f"{list(data['params'].keys())}"
        )
    if tramo not in data["params"][ticker_key]:
        raise KeyError(f"Tramo '{tramo}' no esta calibrado para {ticker_key}.")

    params = data["params"][ticker_key][tramo]
    info = data["tickers_info"].get(ticker_key, {})
    return {
        "lambda_plus": params["lambda_plus"],
        "lambda_minus": params["lambda_minus"],
        "theta": params["theta"],
        "avg_order_size": params.get("avg_order_size", info.get("avg_order_size", 100.0)),
        "spread_roll_bps": params.get("spread_roll_bps", 20.0),
        "hl_range_bps": params.get("hl_range_bps", 20.0),
        "calibration_path": str(path),
        "ticker": ticker_key,
        "tramo": tramo,
    }


class PoissonLOBSimulator:
    """LOB sintetico de 5 niveles por lado, gobernado por un proceso de Poisson
    calibrado con datos reales del IPSA (Benjamin, tarea 2.1.3).

    Un "paso" de este simulador = 30 segundos, exactamente la cadencia del
    Agente Ejecutor -- las tasas lambda_plus/lambda_minus/theta ya estan
    calibradas en esa unidad ("ordenes por paso de 30 s", ver
    docs/calibracion_poisson_2.1.3_BF.md, seccion 3.1), asi que no hace falta
    reescalarlas.

    Limitaciones explicitas (no se ocultan):
    - El espaciado entre niveles y la distribucion de volumen por nivel son
      heuristicas razonables, no estimadas de datos reales de Nivel 2 (que no
      existen para el IPSA, ver Titulo I 4.3.2.e).
    - El "drift" del precio medio ante desbalance de flujo es un modelo
      simplificado (no un LOB completo con colas de ordenes).
    """

    def __init__(self, ticker: str, tramo: str, calibration_path: Optional[Path] = None,
                 seed: Optional[int] = None):
        self.calib = load_calibrated_params(ticker, tramo, calibration_path)
        self.rng = np.random.default_rng(seed)

        # Tick size: fraccion pequena del spread tipico (evita niveles degenerados).
        self._spread_bps = max(self.calib["spread_roll_bps"], 1.0)
        self._avg_order_size = max(self.calib["avg_order_size"], 1.0)

        self.mid_price: float = 0.0
        self.bid_prices = np.zeros(N_LEVELS)
        self.bid_volumes = np.zeros(N_LEVELS)
        self.ask_prices = np.zeros(N_LEVELS)
        self.ask_volumes = np.zeros(N_LEVELS)
        self._last_n_orders = 0  # N+ + N- del ultimo step, para tasa_ordenes

    # ------------------------------------------------------------------
    def reset(self, p_referencia: float) -> None:
        """Inicializa el libro centrado en `p_referencia` (arrival price)."""
        self.mid_price = float(p_referencia)
        self._rebuild_book()
        self._last_n_orders = 0

    def _rebuild_book(self) -> None:
        """Reconstruye bid/ask desde `self.mid_price`, con espaciado y volumen
        heuristicos (ver docstring de clase, limitaciones)."""
        half_spread = self.mid_price * (self._spread_bps / 2) / 10_000
        tick = max(half_spread / N_LEVELS, self.mid_price * 1e-5)

        level_idx = np.arange(N_LEVELS)
        self.bid_prices = self.mid_price - half_spread - level_idx * tick
        self.ask_prices = self.mid_price + half_spread + level_idx * tick

        # Volumen: mayor en el mejor nivel, decae geometricamente (~ Gould et al. 2013,
        # citado en Titulo I, forma cualitativa tipica de un LOB real).
        decay = 0.6
        base_volume = self._avg_order_size * self.rng.uniform(3.0, 8.0, size=N_LEVELS)
        weights = decay ** level_idx
        self.bid_volumes = np.round(base_volume * weights)
        self.ask_volumes = np.round(base_volume * weights * self.rng.uniform(0.8, 1.2, size=N_LEVELS))
        self.bid_volumes = np.maximum(self.bid_volumes, 1.0)
        self.ask_volumes = np.maximum(self.ask_volumes, 1.0)

    # ------------------------------------------------------------------
    def advance(self) -> None:
        """Avanza la dinamica de mercado un paso (30 s): llegada de ordenes
        Poisson, drift del precio medio, y refill/deplecion del libro."""
        lam_plus = self.calib["lambda_plus"]
        lam_minus = self.calib["lambda_minus"]
        theta = self.calib["theta"]

        n_buy = self.rng.poisson(lam_plus)
        n_sell = self.rng.poisson(lam_minus)
        n_cancel = self.rng.poisson(theta)
        self._last_n_orders = n_buy + n_sell

        # Drift del mid: desbalance neto empuja el precio, amortiguado por cancelaciones
        # (misma logica cualitativa que PoissonLOBModel.generate_events en
        # calibration_poisson.py, pero aplicada al PRECIO del libro, no a un
        # retorno aislado).
        tick = self.mid_price * 1e-5
        net = (n_buy - n_sell) / (1.0 + n_cancel)
        self.mid_price = max(self.mid_price + net * tick, tick)

        self._rebuild_book()

    # ------------------------------------------------------------------
    def execute_market_buy(self, quantity: float) -> Tuple[float, float]:
        """Ejecuta una orden de MERCADO de compra: barre el lado ask desde el
        mejor precio, tal como el ejemplo de Contexto_Agente_Programacion.md
        (seccion 2): 2000@5800 + 5500@5810 + 500@5820.

        Returns:
            (cantidad_ejecutada, precio_promedio_ponderado). Si no hay
            liquidez suficiente en los 5 niveles, ejecuta lo que haya
            disponible (cantidad_ejecutada < quantity).
        """
        remaining = float(quantity)
        filled = 0.0
        notional = 0.0

        for level in range(N_LEVELS):
            if remaining <= 0:
                break
            available = self.ask_volumes[level]
            take = min(remaining, available)
            if take <= 0:
                continue
            notional += take * self.ask_prices[level]
            filled += take
            remaining -= take
            self.ask_volumes[level] -= take

        avg_price = (notional / filled) if filled > 0 else float(self.ask_prices[0])
        return filled, avg_price

    def execute_limit_buy(self, quantity: float, price_level: int) -> Tuple[float, float]:
        """Ejecuta una orden LIMITE de compra en `price_level` (0=mejor bid,
        mas alto=mas lejos/mas agresivo hacia el ask, ver EjecutorActionSpace).

        Aproximacion (sin colas de ordenes reales): la probabilidad de llenado
        decae con la distancia al mejor ask -- un nivel agresivo (cerca o
        cruzando el spread) tiene alta probabilidad de llenarse este mismo
        paso; uno pasivo (cerca del propio bid) tiene baja probabilidad.
        """
        # price_level in [0,7] (EjecutorActionSpace.N_PRICE_LEVELS=8); lo mapeamos
        # a una probabilidad de fill decreciente 0 (agresivo) -> 7 (pasivo).
        fill_prob = max(0.05, 1.0 - price_level / 8.0)
        if self.rng.uniform() > fill_prob:
            return 0.0, float(self.mid_price)  # no se llena este paso
        # Si se llena, se llena como si fuera un market buy pequeno (mismo mecanismo).
        return self.execute_market_buy(quantity)

    # ------------------------------------------------------------------
    def get_market_features(self) -> Dict[str, float]:
        """spread_t, OBI_t, tasa_ordenes, P_mid -- ver SE_schema.json."""
        spread = float(self.ask_prices[0] - self.bid_prices[0])
        bid_vol = float(self.bid_volumes.sum())
        ask_vol = float(self.ask_volumes.sum())
        obi = (bid_vol - ask_vol) / (bid_vol + ask_vol) if (bid_vol + ask_vol) > 0 else 0.0
        # tasa_ordenes normalizada: referencia = 3x (lambda_plus+lambda_minus) esperado,
        # para que un valor "tipico" caiga cerca de 0.33 y picos altos se acerquen a 1.0.
        expected_orders = self.calib["lambda_plus"] + self.calib["lambda_minus"]
        tasa_ordenes = min(self._last_n_orders / (3 * max(expected_orders, 1e-6)), 1.0)
        return {
            "spread_t": spread,
            "OBI_t": obi,
            "tasa_ordenes": tasa_ordenes,
            "P_mid": float(self.mid_price),
        }
