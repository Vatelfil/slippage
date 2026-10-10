"""Parametros de mercado compartidos (tareas 2.1.3, 2.1.3b, 2.2.4, 2.2.5, 2.3.3).

Fuente unica para los supuestos de microestructura que hoy usan la
calibracion Poisson (`src/envs/calibration_poisson.py`), el analisis
intradiario (`src/analysis/intraday_profile.py`) y la generacion de
meta-ordenes (`src/experiments/meta_orders.py`). Cambiar un valor aqui cambia
los resultados de todos esos modulos: recalibrar y regenerar los JSON de
`data/calibration/` despues de hacerlo.

Autor: Benjamin Farias (BF).
"""
from __future__ import annotations

from typing import Dict, List, Tuple

# Zona horaria de la sesion (Bolsa de Santiago). Todos los cortes horarios de
# este modulo son hora local America/Santiago (tz-aware, incluye DST).
SANTIAGO_TZ = "America/Santiago"

# Tramos de los Agentes Ejecutores (docs/arquitectura_entorno_simulacion.md
# seccion 3.1; docs/schemas/SE_schema.json). Intervalos [inicio, fin), salvo
# el ultimo, que incluye las 16:00.
TRAMOS_EJECUTOR: Tuple[Tuple[str, str, str], ...] = (
    ("apertura", "09:30", "11:30"),
    ("media_jornada", "11:30", "14:00"),
    ("cierre", "14:00", "16:00"),
)

# Cortes por HORA EXACTA de la variable `sesion` de S_M (indice 6), copiados
# de SESSION_CUTOFFS_HOUR en src/features/build_sm_features.py (que NO lee
# este modulo: no se modifico ese script). DISCREPANCIA CONOCIDA, pendiente
# para el Sprint Review: S_M corta apertura/media_jornada a las 11:00
# ([9,11), [11,14), [14,16]; arquitectura seccion 4.1), mientras que los
# Ejecutores (TRAMOS_EJECUTOR) cortan a las 11:30. Entre 11:00 y 11:30 el
# Maestro ve `sesion`=media_jornada y el Ejecutor sigue en apertura. Si se
# unifican, cambiar ambos lugares a la vez y regenerar sm_features_*.
SESION_SM_CUTOFFS: Dict[str, List[int]] = {
    "apertura": [9, 11],
    "media_jornada": [11, 14],
    "cierre": [14, 16],
}

# Resolucion de los datos y paso de decision del Ejecutor.
STEP_SECONDS = 30
BAR_MINUTES = 5
STEPS_PER_BAR = BAR_MINUTES * 60 // STEP_SECONDS  # = 10

# Nocional medio por orden (CLP) del flujo de ordenes de fondo. yfinance no
# entrega numero de transacciones, asi que el tamano medio de orden es un
# supuesto; ver ORDER_SIZE_POLICY.
AVG_ORDER_NOTIONAL_CLP = 1_000_000

# Politica para convertir AVG_ORDER_NOTIONAL_CLP en acciones por ticker.
# - metodo "nocional_fijo": avg_order_size = round(notional / precio_ref),
#   con minimo `minimo_acciones`.
# - precio_ref = mediana de close_raw de las velas observadas
#   (is_imputed=False) del snapshot completo, INCLUIDA la vela de subasta
#   (se calcula antes de excluirla; asi lo hace calibration_poisson.py desde
#   la 2.1.3 y se conserva para no cambiar sus resultados).
# - Consecuencia: lambda (ordenes por paso) escala como 1/avg_order_size; las
#   razones entre tramos no dependen de esta politica. Si RMSC04/ABIDES usa
#   otro tamano de orden, reescalar lambda por avg_order_size / q_simulador.
# - Override: `--avg-order-size` (acciones, igual para todos los tickers) o
#   `--order-notional-clp` en la CLI de calibration_poisson.
ORDER_SIZE_POLICY: Dict[str, object] = {
    "metodo": "nocional_fijo",
    "notional_clp": AVG_ORDER_NOTIONAL_CLP,
    "precio_referencia": "mediana(close_raw) de velas observadas del snapshot, subasta incluida",
    "redondeo": "round",
    "minimo_acciones": 1,
}

# Vela en la que clean_ohlcv.py (1.2.1) fusiona la subasta de cierre
# (CLOSING_AUCTION_NOTE). Su volumen proviene de un mecanismo de subasta, no
# del flujo continuo que modela el proceso de Poisson ni del que puede
# capturar el Ejecutor, por lo que queda EXCLUIDA por defecto.
CLOSING_AUCTION_BAR = "15:55"
INCLUDE_CLOSING_AUCTION = False


# --- Recompensa de los Ejecutores (tarea 2.2.3) ---------------------------
# R_E = (P_mid - P_ejec) q_ejec - beta sigma2_precio q_ejec. Ver
# src/envs/reward_utils.py y docs/recompensa_ejecutores_2.2.3_BF.md.
#
# beta (aversion al riesgo, en 1/CLP) = 0,1 x beta* (beta* = 0,0618 del barrido
# de BF en ABIDES). Elegido en la fase 2 (PPO, tramo apertura, 300 episodios,
# 30 semillas de evaluacion; ver docs/beta_fase2_apertura_PS.md): es el unico
# de 0,1/0,3/1 x beta* que cumple el 95 % de la orden. VALOR PROVISIONAL: una
# sola semilla de red, solo apertura y la diferencia con beta = 0 esta dentro
# del error estandar. Revalidar en el Sprint 5 (media jornada y cierre cuestan
# ~2 h por beta en Colab). Con beta alto la red aprende a no operar.
BETA_RIESGO_EJECUTOR = 0.0061796
# Ventana movil causal de sigma2_precio, en pasos de decision (20 x 30 s =
# 10 min), y minimo de puntos antes de dejar el prior del tramo. sigma2 es la
# varianza del nivel del P_mid en la ventana por 6 / (n + 1), que estima la
# varianza de un paso (ver src/envs/reward_utils.py).
VENTANA_SIGMA2_PASOS = 20
SIGMA2_MIN_PUNTOS = 5
# Escala de R_E, comun a los dos entornos del Ejecutor (decision del
# 2026-10-09: CLP por accion del slice):
#   "por_accion_slice": R_E / q_slice, en CLP por accion del slice asignado.
#   "bruta": R_E en CLP.
ESCALAS_RECOMPENSA: Tuple[str, ...] = ("por_accion_slice", "bruta")
ESCALA_RECOMPENSA_EJECUTOR = "por_accion_slice"


def avg_order_size_from_price(median_price: float,
                              notional_clp: float = AVG_ORDER_NOTIONAL_CLP) -> float:
    """Tamano medio de orden en acciones segun ORDER_SIZE_POLICY."""
    return float(max(ORDER_SIZE_POLICY["minimo_acciones"], round(notional_clp / median_price)))
