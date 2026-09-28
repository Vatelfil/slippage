"""Logica PURA (sin importar ABIDES) para conectar ABIDES-Gym a nuestro
EjecutorEnv: construir el vector S_E de 27 dims, traducir nuestras 240 acciones
a ordenes de ABIDES y calcular R_E.

Se separa de `abides_ejecutor_env.py` a proposito: este modulo se puede probar
en cualquier maquina con datos falsos (ver tests/test_abides_bridge.py); el otro
necesita ABIDES-Gym instalado.

Base: codigo real de `SubGymMarketsExecutionEnv_v0`
(jpmorganchase/abides-jpmc-public, abides-gym/abides_gym/envs/
markets_execution_environment_v0.py), de donde salen la estructura de
`raw_state` (parsed_mkt_data.bids/asks/last_transaction, internal_data.holdings/
mkt_open/current_time/inter_wakeup_executed_orders) y el formato de ordenes
({"type": "MKT"|"LMT"|"CCL_ALL", "direction", "size", "limit_price"}).

Precios de ABIDES: enteros en centavos. Todo se normaliza respecto del precio
de entrada, asi que la escala absoluta no importa.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Sequence, Tuple

import numpy as np

N_LEVELS = 5
OBS_DIM = 27  # SE_schema.json: privado 3 + bid 10 + ask 10 + mercado 4


@dataclass
class BridgeConfig:
    """Constantes de normalizacion. Son heuristicas explicitas (no medidas):
    ajustar cuando se calibre rmsc04 con parametros del IPSA (tarea 2.2.4)."""
    price_band: float = 0.05      # precios normalizados en +/-5% del precio de entrada
    volume_cap: float = 2000.0    # volumen por nivel que se satura en 1.0
    q_slice_cap: float = 10_000.0  # tamano de slice que se satura en 1.0
    spread_cap_frac: float = 0.02  # spread que se satura en 1.0 (2% del precio)
    tick: int = 1                 # tick de ABIDES: 1 centavo


# ---------------------------------------------------------------------------
# Helpers de forma: raw_state puede traer buffers (lista de snapshots) o el
# ultimo valor, segun los decoradores de la clase base. Se acepta ambos.
# ---------------------------------------------------------------------------

def last_scalar(x: Any) -> float:
    if isinstance(x, (list, tuple, np.ndarray)):
        return x[-1]
    return x


def last_snapshot(buf: Sequence) -> List:
    """Devuelve el ultimo snapshot del libro: lista de [precio, cantidad]."""
    if len(buf) == 0:
        return []
    first = buf[0]
    is_level = (isinstance(first, (list, tuple, np.ndarray)) and len(first) == 2
                and np.isscalar(first[0]))
    return list(buf) if is_level else list(buf[-1])


def last_orders(x: Any) -> List:
    """Ordenes ejecutadas entre dos despertares (objetos con fill_price y quantity)."""
    if x is None or len(x) == 0:
        return []
    return list(x[-1]) if isinstance(x[0], (list, tuple)) else list(x)


def book_side(snapshot: Sequence, n: int = N_LEVELS) -> Tuple[np.ndarray, np.ndarray]:
    """(precios, volumenes) de los mejores `n` niveles, rellenando con 0 si hay menos."""
    prices = np.zeros(n, dtype=np.float64)
    vols = np.zeros(n, dtype=np.float64)
    for i, level in enumerate(list(snapshot)[:n]):
        prices[i], vols[i] = level[0], level[1]
    return prices, vols


def mid_price(bids: Sequence, asks: Sequence, last_transaction: float) -> float:
    """Igual a markets_agent_utils.get_mid_price: usa la ultima transaccion si falta un lado."""
    if len(bids) > 0 and len(asks) > 0:
        return (bids[0][0] + asks[0][0]) / 2.0
    return float(last_transaction)


# ---------------------------------------------------------------------------
# Observacion S_E (27 dims), en el orden EXACTO de SE_schema.json
# ---------------------------------------------------------------------------

def build_observation(bids: Sequence, asks: Sequence, last_transaction: float,
                      entry_price: float, parent_size: float, remaining: float,
                      time_pct: float, cfg: BridgeConfig = BridgeConfig()) -> np.ndarray:
    """[q_slice, q_pendiente, tau_slice, bid_precios(5), bid_volumenes(5),
    ask_precios(5), ask_volumenes(5), spread_t, OBI_t, tasa_ordenes, P_mid]."""
    lo = entry_price * (1.0 - cfg.price_band)
    width = entry_price * 2.0 * cfg.price_band

    def norm_p(p):
        return np.clip((np.asarray(p, dtype=np.float64) - lo) / width, 0.0, 1.0)

    def norm_v(v):
        return np.clip(np.asarray(v, dtype=np.float64) / cfg.volume_cap, 0.0, 1.0)

    bid_p, bid_v = book_side(bids)
    ask_p, ask_v = book_side(asks)
    mid = mid_price(bids, asks, last_transaction)

    best_bid = bids[0][0] if len(bids) > 0 else mid
    best_ask = asks[0][0] if len(asks) > 0 else mid
    spread = best_ask - best_bid

    tot_b, tot_a = bid_v.sum(), ask_v.sum()
    obi = (tot_b - tot_a) / (tot_b + tot_a) if (tot_b + tot_a) > 0 else 0.0

    privado = [
        np.clip(parent_size / cfg.q_slice_cap, 0.0, 1.0),
        np.clip(remaining / max(parent_size, 1e-9), 0.0, 1.0),
        np.clip(time_pct, 0.0, 1.0),
    ]
    # tasa_ordenes: ABIDES no la expone directamente en raw_state. PLACEHOLDER 0.0
    # (igual que OBI_agregado en S_M antes de tener ABIDES). Pendiente: derivarla
    # del numero de actualizaciones del libro / transacciones entre despertares.
    mercado = [
        np.clip(spread / (entry_price * cfg.spread_cap_frac), 0.0, 1.0),
        np.clip(obi, -1.0, 1.0),
        0.0,
        float(norm_p(mid)),
    ]
    obs = np.concatenate([privado, norm_p(bid_p), norm_v(bid_v),
                          norm_p(ask_p), norm_v(ask_v), mercado]).astype(np.float32)
    assert obs.shape == (OBS_DIM,), obs.shape
    return obs


# ---------------------------------------------------------------------------
# Acciones: nuestras [order_type, volume_bucket, price_level] -> ordenes ABIDES
# ---------------------------------------------------------------------------

ORDER_MARKET, ORDER_LIMIT_BUY, ORDER_LIMIT_SELL = 2, 0, 1  # indices de spaces.ORDER_TYPES
VOLUME_FRACS = np.linspace(0.1, 1.0, 10)  # igual a EjecutorActionSpace._volume_bucket_values


def map_action_to_abides_orders(action: Sequence[int], remaining: float, best_bid: float,
                                best_ask: float, direction: str = "BUY",
                                cfg: BridgeConfig = BridgeConfig()) -> List[Dict[str, Any]]:
    """PROPUESTA de traduccion (decision de diseno, revisar):

    - MARKET      -> CCL_ALL + MKT por `frac * remaining` acciones.
    - LIMIT_BUY   -> CCL_ALL + LMT a `best_bid + price_level * tick` (nivel 0 = pasivo,
                     nivel 7 = mas agresivo, hasta cruzar el spread).
    - LIMIT_SELL  -> [] (esperar): el proyecto solo modela COMPRA.
    Ordenes en ABIDES tienen `size` entero >= 1; se acota a `remaining`.
    """
    order_type, volume_bucket, price_level = (int(a) for a in np.asarray(action).reshape(-1)[:3])
    size = int(min(max(1, round(VOLUME_FRACS[volume_bucket] * remaining)), max(int(remaining), 0)))
    if size <= 0 or order_type == ORDER_LIMIT_SELL:
        return []
    if order_type == ORDER_MARKET:
        return [{"type": "CCL_ALL"},
                {"type": "MKT", "direction": direction, "size": size}]
    limit_price = int(best_bid + price_level * cfg.tick)
    return [{"type": "CCL_ALL"},
            {"type": "LMT", "direction": direction, "size": size, "limit_price": limit_price}]


# ---------------------------------------------------------------------------
# Recompensa R_E = (P_mid - P_ejec) * q_ejec - beta * sigma^2 * q_ejec
# ---------------------------------------------------------------------------

def step_reward(executed_orders: Sequence, mid: float, parent_size: float,
                beta: float = 0.0, sigma2: float = 0.0) -> float:
    """R_E de un paso, dividido por `parent_size` (igual que la clase base de ABIDES,
    para mantener la escala acotada: unidades = centavos por accion de la orden).
    `beta` sigue PENDIENTE de calibracion (Sprint 4): 0.0 explicito, no inventado."""
    total = 0.0
    for o in executed_orders:
        q = float(o.quantity)
        total += (mid - float(o.fill_price)) * q - beta * sigma2 * q
    return total / max(parent_size, 1e-9)
