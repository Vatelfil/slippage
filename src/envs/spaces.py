"""Formalizacion en codigo (Gymnasium) de los espacios de observacion y accion
del Agente Maestro y de los Agentes Ejecutores.

Tarea 2.1.4 (Sprint 3, 14-25 sept 2026) - Responsable: Paolo Sepulveda (PS).

Los rangos (low/high), dimensiones y dtype de los observation spaces se cargan
en tiempo de ejecucion desde los contratos de datos versionados por el equipo:
    - docs/schemas/SM_schema.json  (Agente Maestro, S_M)
    - docs/schemas/SE_schema.json  (Agentes Ejecutores, S_E)

No se hardcodean los limites numericos: si el equipo actualiza un schema
(p. ej. al calibrar lambda/beta en Sprint 4), este modulo debe reflejar el
cambio sin tocar codigo, solo el JSON.

NOTA HISTORICA (corregida, 23 sept 2026): SE_schema.json v1.0.0 declaraba
`gymnasium_space.shape=[26]` mientras que la suma real de las dimensiones
listadas en `variables` (y en `low_by_group`) era 27 (privado 3 + bid_precios
5 + bid_volumenes 5 + ask_precios 5 + ask_volumenes 5 + [spread_t, OBI_t,
tasa_ordenes, P_mid] 4 = 27). Esto ya fue corregido en el propio schema
(shape=[27] y `total_dims_breakdown` recalculado). `EjecutorSpace` sigue
calculando `n_dims` a partir de los datos REALES de `variables` en vez de
confiar ciegamente en el campo `shape` declarado, y emite
`EjecutorSpace.SCHEMA_DIM_WARNING` si alguna vez vuelven a divergir (defensa
ante una futura edicion manual inconsistente del JSON), pero no hay
discrepancia activa en la version actual del schema.
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
from gymnasium import spaces

# ---------------------------------------------------------------------------
# Utilidades comunes
# ---------------------------------------------------------------------------

_SCHEMAS_DIR = Path(__file__).resolve().parents[2] / "docs" / "schemas"
SM_SCHEMA_PATH = _SCHEMAS_DIR / "SM_schema.json"
SE_SCHEMA_PATH = _SCHEMAS_DIR / "SE_schema.json"


def _load_schema(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"No se encontro el contrato de datos esperado en '{path}'. "
            "Este modulo requiere docs/schemas/SM_schema.json y "
            "docs/schemas/SE_schema.json (ver Sprint 1, tarea 1.1.4)."
        )
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


_DTYPE_MAP = {
    "float32": np.float32,
    "float64": np.float64,
}


# ---------------------------------------------------------------------------
# 1) MaestroSpace: observation_space del Agente Maestro (S_M), dim 7
# ---------------------------------------------------------------------------

class MaestroSpace:
    """Observation space del Agente Maestro (S_M).

    Se construye leyendo `gymnasium_space` (low/high/shape/dtype) directamente
    desde docs/schemas/SM_schema.json (Sprint 1, tarea 1.1.4). Ver seccion 4.1
    de Contexto_Agente_Programacion.md para el detalle de cada variable:
    q_t, tau_t, n_slices, volatilidad, vol_promedio, OBI_agregado, sesion.
    """

    def __init__(self, schema_path: Path = SM_SCHEMA_PATH):
        self.schema_path = Path(schema_path)
        self.schema = _load_schema(self.schema_path)
        gs = self.schema["gymnasium_space"]

        self.variable_names = [v["name"] for v in self.schema["variables"]]
        low = np.array(gs["low"], dtype=np.float64)
        high = np.array(gs["high"], dtype=np.float64)
        dtype = _DTYPE_MAP.get(gs.get("dtype", "float32"), np.float32)
        shape = tuple(gs["shape"])

        if low.shape[0] != shape[0] or high.shape[0] != shape[0]:
            raise ValueError(
                "SM_schema.json inconsistente: len(low)/len(high) no coincide "
                f"con shape declarado {shape}."
            )
        if low.shape[0] != len(self.variable_names):
            raise ValueError(
                "SM_schema.json inconsistente: numero de variables "
                f"({len(self.variable_names)}) no coincide con shape {shape}."
            )

        self.low = low.astype(dtype)
        self.high = high.astype(dtype)
        self.dtype = dtype
        self.n_dims = shape[0]

        self.space = spaces.Box(low=self.low, high=self.high, shape=shape, dtype=dtype)

    def sample(self) -> np.ndarray:
        """Devuelve una observacion aleatoria valida (uniforme en [low, high])."""
        return self.space.sample()

    def contains(self, obs: np.ndarray) -> bool:
        """Verifica si `obs` pertenece al espacio (shape, dtype y rango)."""
        try:
            obs = np.asarray(obs, dtype=self.dtype)
        except (TypeError, ValueError):
            return False
        return self.space.contains(obs)

    def describe(self) -> Dict[str, Any]:
        """Metadatos legibles (nombre, rango) por indice, para debugging/docs."""
        return {
            i: {"name": name, "low": float(self.low[i]), "high": float(self.high[i])}
            for i, name in enumerate(self.variable_names)
        }

    def __repr__(self) -> str:  # pragma: no cover - solo informativo
        return f"MaestroSpace(shape=({self.n_dims},), vars={self.variable_names})"


# ---------------------------------------------------------------------------
# 2) EjecutorSpace: observation_space de un Agente Ejecutor (S_E)
# ---------------------------------------------------------------------------

class EjecutorSpace:
    """Observation space de un Agente Ejecutor (S_E).

    Se construye leyendo low/high REALES desde docs/schemas/SE_schema.json
    (grupos: privado(3) + bid_precios(5) + bid_volumenes(5) + ask_precios(5)
    + ask_volumenes(5) + [spread_t, OBI_t, tasa_ordenes, P_mid](4)).

    Nota historica: SE_schema.json v1.0.0 declaraba shape=[26] cuando la suma
    real de sus grupos era 27; ya se corrigio en el schema (ver docstring de
    modulo). `n_dims` se calcula igualmente a partir de los datos REALES de
    `variables`, no del campo `shape`, como defensa ante una futura edicion
    manual inconsistente del JSON.
    """

    SCHEMA_DIM_WARNING = (
        "El shape declarado en gymnasium_space.shape no coincide con la suma "
        "real de las dimensiones listadas en 'variables' de SE_schema.json. "
        "EjecutorSpace siempre usa la dimension REAL inferida de 'variables' "
        "para no perder ninguna variable del contrato; corregir el campo "
        "'shape' (y 'total_dims_breakdown') en el schema para que quede "
        "consistente."
    )

    def __init__(self, schema_path: Path = SE_SCHEMA_PATH, warn: bool = True):
        self.schema_path = Path(schema_path)
        self.schema = _load_schema(self.schema_path)
        gs = self.schema["gymnasium_space"]

        low, high, names = self._build_low_high_from_variables(self.schema["variables"])

        declared_shape = tuple(gs.get("shape", [len(low)]))
        self.declared_shape = declared_shape
        self.n_dims = len(low)  # dimension REAL (ver SCHEMA_DIM_WARNING)

        if declared_shape[0] != self.n_dims and warn:
            warnings.warn(self.SCHEMA_DIM_WARNING, RuntimeWarning, stacklevel=2)

        dtype = _DTYPE_MAP.get(gs.get("dtype", "float32"), np.float32)
        self.variable_names = names
        self.low = low.astype(dtype)
        self.high = high.astype(dtype)
        self.dtype = dtype

        self.space = spaces.Box(
            low=self.low, high=self.high, shape=(self.n_dims,), dtype=dtype
        )

    @staticmethod
    def _build_low_high_from_variables(variables):
        """Expande cada entrada de `variables` (que puede describir un grupo
        de `dim` componentes con el mismo `range`) a vectores low/high planos,
        preservando el orden declarado en el schema."""
        low_list = []
        high_list = []
        names = []
        for var in variables:
            dim = var.get("dim", 1)
            lo, hi = var["range"]
            base_name = var["name"]
            for k in range(dim):
                low_list.append(lo)
                high_list.append(hi)
                names.append(base_name if dim == 1 else f"{base_name}_{k}")
        return np.array(low_list, dtype=np.float64), np.array(high_list, dtype=np.float64), names

    def sample(self) -> np.ndarray:
        """Devuelve una observacion aleatoria valida (uniforme en [low, high])."""
        return self.space.sample()

    def contains(self, obs: np.ndarray) -> bool:
        """Verifica si `obs` pertenece al espacio (shape, dtype y rango)."""
        try:
            obs = np.asarray(obs, dtype=self.dtype)
        except (TypeError, ValueError):
            return False
        return self.space.contains(obs)

    def describe(self) -> Dict[str, Any]:
        return {
            i: {"name": name, "low": float(self.low[i]), "high": float(self.high[i])}
            for i, name in enumerate(self.variable_names)
        }

    def __repr__(self) -> str:  # pragma: no cover - solo informativo
        return f"EjecutorSpace(shape=({self.n_dims},), declared_shape={self.declared_shape})"


# ---------------------------------------------------------------------------
# 3) MaestroActionSpace: accion continua alpha_t (version simplificada)
# ---------------------------------------------------------------------------

class MaestroActionSpace:
    """Action space continuo y simplificado del Agente Maestro para la
    formalizacion de bajo nivel pedida en la Tarea 2.1.4: `Box(alpha_t)`,
    alpha_t en [0, 1], shape (1,).

    NOTA: el contrato "oficial" de A_M documentado en SM_schema.json / seccion
    4.1 del contexto es `MultiDiscrete([10, 4])` (alpha_t discretizado en 10
    valores {0.05,...,0.50} x ventana_min en {1,5,10,15}), y se mantiene sin
    cambios (no se esta redefiniendo el contrato de equipo). Esta clase Box
    es una espacio auxiliar/alternativo de accion continua para alpha_t
    (por ejemplo, para pruebas de arquitecturas de red que trabajen en
    espacio continuo antes de discretizar); en el `MaestroEnv` se usa este
    espacio Box tal como lo pide la especificacion de la Tarea 2.1.4.
    """

    def __init__(self):
        self.space = spaces.Box(low=0.0, high=1.0, shape=(1,), dtype=np.float32)

    def sample(self) -> np.ndarray:
        return self.space.sample()

    def contains(self, action: np.ndarray) -> bool:
        return self.space.contains(np.asarray(action, dtype=np.float32))

    def __repr__(self) -> str:  # pragma: no cover
        return "MaestroActionSpace(Box(0.0, 1.0, shape=(1,)))"


# ---------------------------------------------------------------------------
# 3-bis) MaestroDiscreteActionSpace: Discrete(40) -- contrato OFICIAL de A_M
# ---------------------------------------------------------------------------

class MaestroDiscreteActionSpace:
    """Contrato OFICIAL de A_M (SM_schema.json / seccion 4.2 del contexto):
    `MultiDiscrete([10, 4])` = alpha_t discretizado (10 valores) x ventana_min
    (4 valores), aplanado aqui a `Discrete(40)` porque `MasterActorCritic`
    (src/models/actor_critic.py, Mauricio) implementa un unico `actor_head`
    de 40 logits -- no un `MultiDiscrete` real de dos cabezas.

    Agregada 23 sept 2026 (PS) para resolver la discrepancia detectada al
    conectar la red real del Maestro al notebook de training: `MaestroEnv`
    solo exponia `MaestroActionSpace` (continua, Box), incompatible con una
    red que produce un indice discreto 0-39. `MaestroEnv.action_space` ahora
    usa esta clase; `MaestroActionSpace` (Box) se mantiene disponible para
    quien quiera experimentar con una arquitectura de accion continua, pero
    ya no es el espacio por defecto del entorno.

    El orden de codificacion/decodificacion es el mismo que usa
    `src/envs/maestro_ejecutor_protocol.py` (ALPHA_VALUES, VENTANA_MIN_VALUES):
    `idx = alpha_idx * 4 + ventana_idx`.
    """

    ALPHA_VALUES = (0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50)
    VENTANA_MIN_VALUES = (1, 5, 10, 15)
    N = len(ALPHA_VALUES) * len(VENTANA_MIN_VALUES)  # 40

    def __init__(self):
        self.space = spaces.Discrete(self.N)

    def decode(self, action_idx) -> "tuple[float, int]":
        """`idx` (0..39) -> `(alpha_t, ventana_min)` reales."""
        idx = int(np.asarray(action_idx).reshape(-1)[0])
        alpha_idx, ventana_idx = divmod(idx, len(self.VENTANA_MIN_VALUES))
        return self.ALPHA_VALUES[alpha_idx], self.VENTANA_MIN_VALUES[ventana_idx]

    def encode(self, alpha_idx: int, ventana_idx: int) -> int:
        return alpha_idx * len(self.VENTANA_MIN_VALUES) + ventana_idx

    def sample(self):
        return self.space.sample()

    def contains(self, action) -> bool:
        try:
            return self.space.contains(int(np.asarray(action).reshape(-1)[0]))
        except (TypeError, ValueError):
            return False

    def __repr__(self) -> str:  # pragma: no cover
        return f"MaestroDiscreteActionSpace(Discrete({self.N}))"


# ---------------------------------------------------------------------------
# 4) EjecutorActionSpace: MultiDiscrete([3, 10, 8])
# ---------------------------------------------------------------------------

ORDER_TYPES = ("LIMIT_BUY", "LIMIT_SELL", "MARKET")


class EjecutorActionSpace:
    """Action space discreto y "aplanado" del Agente Ejecutor pedido en la
    Tarea 2.1.4: `MultiDiscrete([3, 10, 8])` = (order_type, volume_bucket,
    price_level).

    NOTA: el contrato "oficial" A_E documentado en SE_schema.json / seccion 5
    del contexto es un `Dict` hibrido (tipo_orden: Discrete(3), volumen_frac:
    Box(0,1), nivel_precio: Discrete(4)) y no se modifica. Esta clase
    MultiDiscrete es la version totalmente discretizada pedida
    explicitamente por la especificacion de la Tarea 2.1.4 (util para
    arquitecturas actor-critico puramente discretas); `parse_action` traduce
    la accion aplanada a un diccionario legible equivalente al contrato A_E.
    """

    N_ORDER_TYPES = 3
    N_VOLUME_BUCKETS = 10
    N_PRICE_LEVELS = 8
    N_FLAT = N_ORDER_TYPES * N_VOLUME_BUCKETS * N_PRICE_LEVELS  # 240

    def __init__(self):
        self.space = spaces.MultiDiscrete(
            [self.N_ORDER_TYPES, self.N_VOLUME_BUCKETS, self.N_PRICE_LEVELS]
        )
        # Fracciones de volumen representativas de cada bucket (0..9 -> 0.1..1.0)
        self._volume_bucket_values = np.linspace(0.1, 1.0, self.N_VOLUME_BUCKETS)
        # Niveles de precio 0..7 (0 = mejor precio propio, 7 = mas agresivo/lejano)
        self._price_level_labels = [f"nivel_{i}" for i in range(self.N_PRICE_LEVELS)]

    def sample(self) -> np.ndarray:
        return self.space.sample()

    def contains(self, action) -> bool:
        try:
            action = np.asarray(action, dtype=np.int64)
        except (TypeError, ValueError):
            return False
        return self.space.contains(action)

    def decode_flat(self, flat_idx) -> np.ndarray:
        """Convierte un indice plano (0..239, lo que produce `ExecutorActorCritic`,
        un unico `actor_head` discreto) al array `[order_type, volume_bucket,
        price_level]` que espera `EjecutorEnv.step()` / `self.space`.

        Agregado 23 sept 2026 (PS) por el mismo motivo que
        `MaestroDiscreteActionSpace`: la red real del Ejecutor produce una
        Categorical de `N_FLAT` (240) logits, no un `MultiDiscrete` de 3
        cabezas independientes.
        """
        idx = int(np.asarray(flat_idx).reshape(-1)[0])
        order_type, volume_bucket, price_level = np.unravel_index(
            idx, (self.N_ORDER_TYPES, self.N_VOLUME_BUCKETS, self.N_PRICE_LEVELS)
        )
        return np.array([order_type, volume_bucket, price_level], dtype=np.int64)

    def encode_flat(self, order_type: int, volume_bucket: int, price_level: int) -> int:
        return int(np.ravel_multi_index(
            (order_type, volume_bucket, price_level),
            (self.N_ORDER_TYPES, self.N_VOLUME_BUCKETS, self.N_PRICE_LEVELS),
        ))

    def parse_action(self, action) -> Dict[str, Any]:
        """Traduce una accion `[order_type, volume_bucket, price_level]`
        (enteros) a un diccionario legible.

        Parameters
        ----------
        action : array-like de 3 enteros, dentro de los rangos
            [0, N_ORDER_TYPES), [0, N_VOLUME_BUCKETS), [0, N_PRICE_LEVELS).

        Returns
        -------
        dict con claves: order_type (str), order_type_idx (int),
        volume_frac (float, fraccion del slice en (0, 1]),
        volume_bucket (int), price_level (int), price_level_label (str).
        """
        action = np.asarray(action, dtype=np.int64).reshape(-1)
        if action.shape[0] != 3:
            raise ValueError(f"Se esperaban 3 componentes (order_type, volume_bucket, "
                              f"price_level), se recibieron {action.shape[0]}.")
        order_type_idx, volume_bucket, price_level = (int(a) for a in action)

        if not (0 <= order_type_idx < self.N_ORDER_TYPES):
            raise ValueError(f"order_type_idx={order_type_idx} fuera de rango [0, {self.N_ORDER_TYPES})")
        if not (0 <= volume_bucket < self.N_VOLUME_BUCKETS):
            raise ValueError(f"volume_bucket={volume_bucket} fuera de rango [0, {self.N_VOLUME_BUCKETS})")
        if not (0 <= price_level < self.N_PRICE_LEVELS):
            raise ValueError(f"price_level={price_level} fuera de rango [0, {self.N_PRICE_LEVELS})")

        return {
            "order_type": ORDER_TYPES[order_type_idx],
            "order_type_idx": order_type_idx,
            "volume_bucket": volume_bucket,
            "volume_frac": float(self._volume_bucket_values[volume_bucket]),
            "price_level": price_level,
            "price_level_label": self._price_level_labels[price_level],
        }

    def __repr__(self) -> str:  # pragma: no cover
        return "EjecutorActionSpace(MultiDiscrete([3, 10, 8]))"
