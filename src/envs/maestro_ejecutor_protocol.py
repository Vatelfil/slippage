"""
Protocolo de Coordinación Maestro <-> Ejecutores <-> ABIDES-Gym
================================================================

Tarea 1.2.5 (Sprint 2) - Paolo Sepulveda (PS)
Especificacion de referencia para Mauricio Reynoso (MR), quien la implementara
en Sprint 3 (tareas 2.1.1, 2.1.2, 2.3.1, 2.3.2).

Este archivo es PSEUDOCODIGO ALTAMENTE COMENTADO, no codigo ejecutable:
las llamadas a ABIDES-Gym, a las politicas RL y al pipeline de datos son
placeholders. El detalle narrativo de cada paso esta en:
    docs/arquitectura_entorno_simulacion.md

Contratos de datos que este archivo respeta y NO redefine
(cualquier cambio a estos rangos/dimensiones debe pasar por Sprint 1
y actualizar los JSON correspondientes):
    - docs/schemas/SM_schema.json  -> vector S_M, 7 variables, Box([7,])
    - docs/schemas/SE_schema.json  -> vector S_E, 26 variables, Box([26,])
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Constantes fijadas por los esquemas de Sprint 1 (SM_schema.json / SE_schema.json).
# No cambiar aqui: si estos valores cambian, deben cambiar primero los JSON.
ALPHA_VALUES = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
VENTANA_MIN_VALUES = [1, 5, 10, 15]
MAX_DECISIONES_MAESTRO = 13  # 390 min / 30 min
JORNADA_INICIO = "09:30"
JORNADA_FIN = "16:00"
JORNADA_DURACION_MIN = 390

# Hiperparametros pendientes de calibracion (Sprint 4, tareas 2.2.2/2.2.3).
# NO fijar un valor final aqui: usar un placeholder explicito.
LAMBDA_PENALTY_PLACEHOLDER = 0.1  # lambda: penalizacion por inventario no ejecutado
BETA_RISK_PLACEHOLDER = 0.0       # beta: aversion al riesgo temporal (usado por el Ejecutor)


class MaestroEjecutorEnv:
    """
    Entorno que coordina al Agente Maestro, a los 3 Agentes Ejecutores
    y a ABIDES-Gym, siguiendo la interfaz de Gymnasium (reset/step/close).

    Ejemplo de uso esperado (Sprint 3):

        env = MaestroEjecutorEnv(
            meta_orden_quantity=10_000,
            datos_historicos=df_yfinance_limpio,   # salida de la tarea 1.2.1 (BF)
            abides_config=RMSC04_CONFIG,            # salida de la tarea 1.2.3/1.2.4 (MR)
        )

        s_m = env.reset()
        done = False
        while not done:
            a_m = maestro_policy(s_m)               # red neuronal en Sprint 3
            s_m, r_m, done, info = env.step(a_m)
        env.close()
    """

    def __init__(self, meta_orden_quantity: int, datos_historicos: pd.DataFrame, abides_config: dict):
        """
        Args:
            meta_orden_quantity: Q_total, cantidad total de acciones a comprar (ej. 10_000).
            datos_historicos: DataFrame OHLCV de yfinance ya limpio (tarea 1.2.1, BF),
                indexado por timestamp, resolucion 5 min, horario 09:30-16:00 Chile.
            abides_config: configuracion RMSC04 para ABIDES-Gym (tarea 1.2.3/1.2.4, MR).
        """
        self.Q_total = meta_orden_quantity
        self.Q_executed = 0.0
        self.df_yfinance = datos_historicos
        self.abides_config = abides_config

        # Se inicializan de verdad en reset(), no en __init__().
        self.abides_env = None
        self.current_time = None
        self.decision_count = 0
        self.executor_reports: list[dict] = []
        self.P_referencia = None  # precio mid de referencia (arrival price), fijado en reset()

    # ------------------------------------------------------------------
    # Ciclo de vida del episodio
    # ------------------------------------------------------------------

    def reset(self) -> np.ndarray:
        """
        Reinicia el episodio (una jornada bursatil completa).

        Returns:
            s_m_initial: vector S_M inicial, shape (7,), dtype float32,
            dentro de los rangos de SM_schema.json.
        """
        # 1. Fijar el reloj al inicio de la jornada.
        self.current_time = self.df_yfinance.index[0]  # 09:30

        # 2. Inicializar ABIDES-Gym con la config RMSC04 (tarea 1.2.3/1.2.4, MR).
        #    self.abides_env = ABIDESGymEnvironment(**self.abides_config)
        #    initial_lob_state = self.abides_env.reset()
        self.abides_env = None  # placeholder: reemplazar por instancia real en Sprint 3

        # 3. Resetear contadores.
        self.Q_executed = 0.0
        self.decision_count = 0
        self.executor_reports = []

        # 4. Fijar precio de referencia (arrival price) = P_mid al inicio de jornada.
        #    self.P_referencia = self.abides_env.get_mid_price()
        self.P_referencia = None  # placeholder

        # 5. Calcular S_M inicial.
        s_m_initial = self._compute_sm_state()

        return s_m_initial

    def step(self, action_maestro: tuple[int, int]):
        """
        Ejecuta una decision del Maestro (30 minutos de tiempo simulado).

        Args:
            action_maestro: (alpha_idx, ventana_idx), salida de MultiDiscrete([10, 4])
                - alpha_idx: indice en ALPHA_VALUES
                - ventana_idx: indice en VENTANA_MIN_VALUES

        Returns:
            (s_m_next, r_m, done, info) - convencion Gymnasium.
        """
        # 1. Decodificar la accion del Maestro (fase B-C del ciclo, ver arquitectura_entorno_simulacion.md).
        alpha_t = ALPHA_VALUES[action_maestro[0]]
        ventana_min = VENTANA_MIN_VALUES[action_maestro[1]]

        # 2. Calcular q_slice (cantidad, no fraccion) para este tramo.
        q_slice = alpha_t * (self.Q_total - self.Q_executed)

        # 3. Construir el mensaje ASIGNAR (formato en arquitectura_entorno_simulacion.md, seccion 3.1).
        msg_asignar = {
            "tipo": "asignar",
            "timestamp_inicio": self.current_time,
            "q_slice": q_slice,
            "ventana_min": ventana_min,
        }

        # 4. El Ejecutor del tramo activo opera durante la ventana asignada.
        executor_report = self._run_executor_episode(msg_asignar)
        self.executor_reports.append(executor_report)

        # 5. Actualizar inventario ejecutado con el REPORTE recibido.
        self.Q_executed += executor_report["q_ejecutado"]

        # 6. Avanzar el reloj y el contador de decisiones del Maestro.
        self.current_time = self.current_time + pd.Timedelta(minutes=30)
        self.decision_count += 1

        # 7. Recalcular S_M.
        s_m_next = self._compute_sm_state()

        # 8. Evaluar termino de jornada.
        done = self._is_jornada_terminada()

        # 9. Recompensa: terminal/sparse (Perold 1988, IS_total). 0.0 en pasos intermedios.
        r_m = self._compute_terminal_reward() if done else 0.0

        info = {
            "decision_count": self.decision_count,
            "Q_executed": self.Q_executed,
            "executor_report": executor_report,
        }

        return s_m_next, r_m, done, info

    def close(self):
        """Finaliza el episodio: cierra ABIDES-Gym y guarda logs (seccion 5 del documento)."""
        # self.abides_env.close()
        self._save_logs()

    # ------------------------------------------------------------------
    # Helpers internos (fase E-F del ciclo: la ventana del Ejecutor)
    # ------------------------------------------------------------------

    def _run_executor_episode(self, msg_asignar: dict) -> dict:
        """
        Simula la ventana de ejecucion asignada a un Ejecutor: un sub-loop
        de (ventana_min * 2) pasos, cada uno de 30 segundos.

        Args:
            msg_asignar: mensaje ASIGNAR construido en step().

        Returns:
            executor_report: mensaje REPORTE (formato en arquitectura_entorno_simulacion.md, seccion 3.2).
        """
        q_slice = msg_asignar["q_slice"]
        ventana_min = msg_asignar["ventana_min"]
        n_pasos = ventana_min * 2  # cada paso = 30 seg

        q_ejecutado_acumulado = 0.0
        monto_acumulado = 0.0  # suma de (precio * cantidad) para promediar despues
        razon_termino = "ventana_completada"

        for step_idx in range(n_pasos):
            # a) Calcular S_E actual: 3 privadas + 23 desde ABIDES-Gym (ver seccion 4.2 del documento).
            tau_slice = step_idx / n_pasos
            q_pendiente = (q_slice - q_ejecutado_acumulado) / q_slice if q_slice > 0 else 0.0
            # s_e_abides = self.abides_env.get_state()  # 23 variables (Bid/Ask LOB + mercado)
            # s_e = np.concatenate([[q_slice, q_pendiente, tau_slice], s_e_abides])
            s_e = None  # placeholder, shape esperado (26,)

            # b) Politica del Ejecutor (Sprint 3: red neuronal entrenada).
            # a_e = executor_policy(s_e)  # (tipo_orden, volumen_frac, nivel_precio)
            a_e = None  # placeholder

            # c) Ejecutar la accion en ABIDES-Gym.
            # resultado = self.abides_env.step(a_e)
            # if resultado["executado"]:
            #     q_ejecutado_acumulado += resultado["cantidad_ejecutada"]
            #     monto_acumulado += resultado["precio_ejecucion"] * resultado["cantidad_ejecutada"]

            # d) Si se agoto el q_slice antes de completar la ventana, terminar antes.
            if q_ejecutado_acumulado >= q_slice:
                razon_termino = "inventario_agotado"
                break

        # Precio promedio ponderado por volumen; si no hubo ejecuciones, usar P_mid vigente.
        if q_ejecutado_acumulado > 0:
            p_promedio = monto_acumulado / q_ejecutado_acumulado
        else:
            # p_promedio = self.abides_env.get_mid_price()
            p_promedio = self.P_referencia  # placeholder razonable mientras no hay ABIDES real

        slippage_parcial = (p_promedio - self.P_referencia) * q_ejecutado_acumulado if self.P_referencia else 0.0

        executor_report = {
            "tipo": "reporte",
            "timestamp_fin": msg_asignar["timestamp_inicio"] + pd.Timedelta(minutes=ventana_min),
            "q_ejecutado": q_ejecutado_acumulado,
            "p_promedio": p_promedio,
            "slippage_parcial": slippage_parcial,
            "razon_termino": razon_termino,
        }
        return executor_report

    # ------------------------------------------------------------------
    # Calculo de S_M y de la recompensa terminal (contrato: SM_schema.json)
    # ------------------------------------------------------------------

    def _compute_sm_state(self) -> np.ndarray:
        """
        Calcula el vector S_M vigente, shape (7,), en el orden fijado por SM_schema.json:
        [q_t, tau_t, n_slices, volatilidad, vol_promedio, OBI_agregado, sesion]
        """
        s_m = np.zeros(7, dtype=np.float32)

        s_m[0] = (self.Q_total - self.Q_executed) / self.Q_total  # q_t
        minutos_transcurridos = (
            self.current_time.hour * 60 + self.current_time.minute - (9 * 60 + 30)
        )
        s_m[1] = minutos_transcurridos / JORNADA_DURACION_MIN  # tau_t
        s_m[2] = self.decision_count / MAX_DECISIONES_MAESTRO  # n_slices

        # volatilidad y vol_promedio: pre-calculados por el pipeline de Benjamin (tarea 1.2.2)
        # sobre self.df_yfinance; aqui solo se indexan por self.current_time.
        s_m[3] = self._lookup_yfinance_feature("volatilidad")
        s_m[4] = self._lookup_yfinance_feature("vol_promedio")

        # OBI_agregado: viene de ABIDES-Gym. Placeholder 0.0 documentado en SM_schema.json
        # mientras ABIDES-Gym no este integrado (tareas 1.2.3/1.2.4).
        s_m[5] = 0.0  # self.abides_env.get_market_imbalance()

        hour = self.current_time.hour
        if 9 <= hour < 11:
            s_m[6] = 0.0  # apertura
        elif 11 <= hour < 14:
            s_m[6] = 0.5  # media jornada
        else:
            s_m[6] = 1.0  # cierre

        return s_m

    def _lookup_yfinance_feature(self, columna: str) -> float:
        """Busca en self.df_yfinance (ya con features calculadas por BF) el valor en self.current_time."""
        # return float(self.df_yfinance.loc[self.current_time, columna])
        return 0.0  # placeholder hasta que exista data/processed/vector_estado_SM_*.csv (tarea 1.2.2)

    def _is_jornada_terminada(self) -> bool:
        return self.current_time.hour >= 16

    def _compute_terminal_reward(self) -> float:
        """
        R_M = -IS_total - lambda * max(0, Q_pendiente) * P_mid_cierre

        IS_total = suma de slippage_parcial de todos los reportes de la jornada.
        lambda: LAMBDA_PENALTY_PLACEHOLDER (se calibra en Sprint 4, tarea 2.2.2).
        """
        IS_total = sum(r["slippage_parcial"] for r in self.executor_reports)
        Q_pendiente = self.Q_total - self.Q_executed
        # P_mid_cierre = self.abides_env.get_mid_price()
        P_mid_cierre = self.P_referencia  # placeholder razonable mientras no hay ABIDES real

        r_m = -IS_total - LAMBDA_PENALTY_PLACEHOLDER * max(0.0, Q_pendiente) * (P_mid_cierre or 0.0)
        return r_m

    def _save_logs(self):
        """
        Persiste maestro_states.csv, executor_states.csv, executor_actions.csv,
        rewards.csv y episode_summary.json segun la estructura definida en
        docs/arquitectura_entorno_simulacion.md, seccion 5.
        """
        pass  # a implementar en Sprint 3


# ----------------------------------------------------------------------
# Politicas (placeholders): en Sprint 3, Mauricio las reemplaza por redes
# neuronales Actor-Critico entrenadas con PPO (tareas 2.1.1 / 2.1.2).
# ----------------------------------------------------------------------

def maestro_policy(s_m: np.ndarray) -> tuple[int, int]:
    """
    Politica del Agente Maestro.

    Args:
        s_m: vector S_M, shape (7,).
    Returns:
        (alpha_idx, ventana_idx) - accion en MultiDiscrete([10, 4]).
    """
    raise NotImplementedError("Sprint 3: reemplazar por red Actor-Critico del Maestro (PPO).")


def executor_policy(s_e: np.ndarray) -> tuple[int, float, int]:
    """
    Politica de un Agente Ejecutor.

    Args:
        s_e: vector S_E, shape (26,).
    Returns:
        (tipo_orden, volumen_frac, nivel_precio) - accion en el espacio hibrido
        Dict({Discrete(3), Box(0,1,(1,)), Discrete(4)}).
    """
    raise NotImplementedError("Sprint 3: reemplazar por red Actor-Critico del Ejecutor (PPO).")
