"""
Protocolo de Coordinación Maestro <-> Ejecutores <-> ABIDES-Gym
================================================================

Tarea 1.2.5 (Sprint 2) - Paolo Sepulveda (PS)
Especificacion de referencia para Mauricio Reynoso (MR).

*** BASE PARCIALMENTE CONECTADA (29 sept 2026, PS) - NO ES TU TAREA TERMINADA ***
Antes este archivo era pseudocodigo puro. Ahora `_run_executor_episode()` usa
de verdad un entorno de Ejecutor real (ABIDES-Gym o el fallback de Poisson,
inyectable via `executor_env_factory`) en vez de placeholders -- eso deja
lista la "plomeria" de coordinacion. Lo que SIGUE siendo tuyo, sin tocar:
    - `maestro_policy()` / `executor_policy()`: siguen lanzando
      NotImplementedError. Son tus redes PPO entrenadas (tareas 2.1.1/2.1.2),
      no las voy a inventar.
    - `LAMBDA_PENALTY_PLACEHOLDER` / la calibracion de R_M: sigue en 0.1
      sin calibrar (tarea 2.2.2), no lo cambie.
    - El Maestro no tiene su propia conexion a ABIDES (no existe un "ABIDES
      del Maestro" -- el Maestro orquesta a los Ejecutores, que si hablan con
      ABIDES; ver docs/arquitectura_entorno_simulacion.md). Si esa premisa no
      te sirve, es una decision tuya cambiarla, no la reescribi por mi cuenta.

Probado (con el fallback de Poisson, que comparte la misma interfaz que
EjecutorEnvAbides -- ver tests/test_maestro_ejecutor_protocol.py): el loop de
coordinacion corre un episodio completo sin crashear, actualiza Q_executed,
y calcula R_M con numeros reales (no placeholders). NO probado con ABIDES-Gym
real (correrlo requiere el entorno de Colab, ver
DIAGNOSTICO_COLAB_MAURICIO_29SEP.md); para eso, pasar
`executor_env_factory=EjecutorEnvAbides` (de src/envs/abides_ejecutor_env.py).

Contratos de datos que este archivo respeta y NO redefine
(cualquier cambio a estos rangos/dimensiones debe pasar por Sprint 1
y actualizar los JSON correspondientes):
    - docs/schemas/SM_schema.json  -> vector S_M, 7 variables, Box([7,])
    - docs/schemas/SE_schema.json  -> vector S_E, 27 variables, Box([27,])
"""

from __future__ import annotations

import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from typing import TYPE_CHECKING, Callable, Optional

import numpy as np
import pandas as pd

from src.envs.spaces import EjecutorActionSpace
if TYPE_CHECKING:  # torch se importa solo al usar las redes (el orquestador corre sin torch)
    from src.models.actor_critic import MasterActorCritic, ExecutorActorCritic

# Constantes fijadas por los esquemas de Sprint 1 (SM_schema.json / SE_schema.json).
# No cambiar aqui: si estos valores cambian, deben cambiar primero los JSON.
ALPHA_VALUES = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
VENTANA_MIN_VALUES = [1, 5, 10, 15]
MAX_DECISIONES_MAESTRO = 13  # 390 min / 30 min
JORNADA_INICIO = "09:30"
JORNADA_FIN = "16:00"
JORNADA_DURACION_MIN = 390

# Calibracion experimental (Sprint 4, tarea 2.2.2 - Mauricio Reynoso).
# Penalizacion por inventario no ejecutado al cierre: lambda * Q_pendiente * P_mid_cierre.
LAMBDA_PENALTY = 0.05             # Calibrado por escala con politica SIN entrenar; revalidar al entrenar (Sprint 5-6)
LAMBDA_PENALTY_PLACEHOLDER = LAMBDA_PENALTY  # Mantiene compatibilidad hacia atras
BETA_RISK_PLACEHOLDER = 0.0       # beta: aversion al riesgo temporal (usado por el Ejecutor)


class MaestroEjecutorEnv:
    """
    Entorno que coordina al Agente Maestro, a los 3 Agentes Ejecutores
    y a ABIDES-Gym, siguiendo la interfaz de Gymnasium (reset/step/close).

    Ejemplo de uso:

        from src.envs.abides_ejecutor_env import EjecutorEnvAbides  # ABIDES real

        env = MaestroEjecutorEnv(
            meta_orden_quantity=10_000,
            datos_historicos=df_sm_features,   # salida de la tarea 1.2.2 (BF), con
                                                # columnas 'volatilidad'/'vol_promedio'
            executor_env_factory=EjecutorEnvAbides,  # o EjecutorEnvPoissonFallback (default)
            executor_env_kwargs={"background_config": "rmsc04"},
        )

        s_m = env.reset()
        done = False
        while not done:
            a_m = maestro_policy(s_m)               # red neuronal en Sprint 3
            s_m, r_m, done, info = env.step(a_m)
        env.close()
    """

    def __init__(self, meta_orden_quantity: int, datos_historicos: Optional[pd.DataFrame] = None,
                 executor_env_factory: Optional[Callable] = None, executor_env_kwargs: Optional[dict] = None,
                 executor_policy_fn: Optional[Callable] = None, lambda_penalty: Optional[float] = None,
                 executor_step_callback: Optional[Callable] = None):
        """
        Args:
            meta_orden_quantity: Q_total, cantidad total de acciones a comprar (ej. 10_000).
            datos_historicos: DataFrame OHLCV de yfinance ya limpio (tarea 1.2.1, BF),
                indexado por timestamp, resolucion 5 min, horario 09:30-16:00 Chile.
                Si es None, se genera un DataFrame sintetico representativo.
            executor_env_factory: clase/funcion que construye el entorno del Ejecutor
                para un tramo dado, con la firma de EjecutorEnv (executor_id, q_slice,
                ventana_min, ...). Usar `EjecutorEnvAbides` (ABIDES-Gym real,
                src/envs/abides_ejecutor_env.py) o `EjecutorEnvPoissonFallback`
                (src/envs/fallback_poisson_env.py) para pruebas sin ABIDES. Si es
                None, usa EjecutorEnvPoissonFallback por defecto (para que el
                orquestador funcione "de fabrica" sin depender de tener ABIDES
                instalado -- cambiar a EjecutorEnvAbides cuando corresponda).
            executor_env_kwargs: kwargs extra para `executor_env_factory` (ej.
                background_config, timestep_duration para EjecutorEnvAbides).
            executor_policy_fn: funcion opcional `s_e -> int` o `(s_e, tramo) -> int / (idx, logp, val)`
                para la politica del Ejecutor. Si es None, usa `executor_policy`.
            lambda_penalty: factor lambda de penalizacion por inventario no ejecutado.
                Si es None, usa LAMBDA_PENALTY.
            executor_step_callback: callback opcional `(tramo, s_e, a_e_idx, log_prob, reward, value, done)`
                llamado en cada transicion de un Ejecutor (util para rollout buffers en PPO).
        """
        self.Q_total = meta_orden_quantity
        self.Q_executed = 0.0

        if datos_historicos is None:
            idx = pd.date_range("2026-09-29 09:30", "2026-09-29 16:00", freq="5min")
            rng = np.random.default_rng(0)
            datos_historicos = pd.DataFrame(
                {"volatilidad": rng.uniform(0.001, 0.003, len(idx)),
                 "vol_promedio": rng.uniform(0.1, 0.3, len(idx))},
                index=idx,
            )
        self.df_yfinance = datos_historicos

        if executor_env_factory is None:
            from src.envs.fallback_poisson_env import EjecutorEnvPoissonFallback
            executor_env_factory = EjecutorEnvPoissonFallback
        self._executor_env_factory = executor_env_factory
        self._executor_env_kwargs = executor_env_kwargs or {}
        self._executor_action_space = EjecutorActionSpace()  # para decode_flat() de las 240 acciones
        self.executor_policy_fn = executor_policy_fn
        self.lambda_penalty = lambda_penalty if lambda_penalty is not None else LAMBDA_PENALTY
        self.executor_step_callback = executor_step_callback

        # Se inicializan de verdad en reset(), no en __init__().
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

        # 2. Resetear contadores.
        self.Q_executed = 0.0
        self.decision_count = 0
        self.executor_reports = []

        # 3. P_referencia (arrival price): el Maestro no tiene su propio ABIDES
        # (ver docstring de modulo), asi que se fija con el primer reporte del
        # Ejecutor en step() -- ver _run_executor_episode(). None aqui es
        # intencional, no un placeholder por completar.
        self.P_referencia = None

        # 4. Calcular S_M inicial.
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
            "tramo": self._tramo_de(self.current_time),  # que Ejecutor de los 3 esta activo
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
        """Finaliza el episodio: guarda logs (seccion 5 del documento).
        Cada `env` del Ejecutor se cierra en `_run_executor_episode()` (uno
        nuevo por decision del Maestro), no hay un ABIDES "del Maestro" que
        cerrar aca -- ver docstring de modulo."""
        self._save_logs()

    @staticmethod
    def _tramo_de(timestamp) -> str:
        """Mapea la hora actual al tramo del Ejecutor activo (mismos limites
        que build_sm_features.py / EjecutorEnv.VALID_EXECUTOR_IDS)."""
        hour = timestamp.hour
        if hour < 11:
            return "apertura"
        if hour < 14:
            return "media_jornada"
        return "cierre"

    # ------------------------------------------------------------------
    # Helpers internos (fase E-F del ciclo: la ventana del Ejecutor)
    # ------------------------------------------------------------------

    def _run_executor_episode(self, msg_asignar: dict) -> dict:
        """
        Simula la ventana de ejecucion asignada a un Ejecutor: un episodio
        completo del `executor_env_factory` inyectado (ABIDES-Gym real o el
        fallback de Poisson), de (ventana_min * 2) pasos de 30 segundos.

        Args:
            msg_asignar: mensaje ASIGNAR construido en step() (incluye "tramo").

        Returns:
            executor_report: mensaje REPORTE (formato en arquitectura_entorno_simulacion.md, seccion 3.2).
        """
        q_slice = msg_asignar["q_slice"]
        ventana_min = msg_asignar["ventana_min"]
        tramo = msg_asignar["tramo"]

        env = self._executor_env_factory(
            executor_id=tramo, q_slice=max(int(round(q_slice)), 1), ventana_min=int(ventana_min),
            **self._executor_env_kwargs,
        )
        s_e, info = env.reset()

        # Primer episodio del dia: no hay P_referencia todavia (el Maestro no
        # tiene su propio ABIDES, ver docstring de modulo) -- se fija aca con
        # lo que el propio Ejecutor reporte como referencia inicial. Duck-typed
        # porque EjecutorEnvAbides e EjecutorEnvPoissonFallback no comparten
        # exactamente las mismas llaves en `info` todavia (ver nota abajo).
        if self.P_referencia is None:
            self.P_referencia = info.get("entry_price") or info.get("p_referencia")

        q_ejecutado_acumulado = 0.0
        monto_acumulado = 0.0  # suma de (precio * cantidad) para promediar despues
        razon_termino = "ventana_completada"
        remaining_prev = float(q_slice)

        done = False
        while not done:
            # a) Politica del Ejecutor: red PPO (tareas 2.1.1/2.1.2).
            #    Debe devolver el indice plano 0-239 (igual que
            #    ExecutorActorCritic.get_action_and_value(), ver src/models/actor_critic.py).
            log_prob_step = 0.0
            value_step = 0.0
            if self.executor_policy_fn is not None:
                try:
                    res = self.executor_policy_fn(s_e, tramo)
                except TypeError:
                    res = self.executor_policy_fn(s_e)
                if isinstance(res, tuple):
                    a_e_idx, log_prob_step, value_step = res
                else:
                    a_e_idx = int(res)
            else:
                a_e_idx = executor_policy(s_e)
            a_e = self._executor_action_space.decode_flat(a_e_idx)

            # b) Ejecutar la accion en el entorno real (ABIDES-Gym o fallback).
            s_e_next, reward, done, truncated, info = env.step(a_e)
            done = done or truncated

            if self.executor_step_callback is not None:
                self.executor_step_callback(tramo, s_e, a_e_idx, log_prob_step, float(reward), value_step, bool(done))
            s_e = s_e_next

            # c) Cantidad ejecutada este paso: NOTA -- EjecutorEnvPoissonFallback
            # expone `info['q_ejecutado_step']` directo; EjecutorEnvAbides (ABIDES
            # real) no tiene ese campo todavia, solo `info['remaining']` -- se
            # deriva de la diferencia. Mauricio: si unificas el formato de `info`
            # entre los dos entornos, esto se simplifica a una sola linea.
            if "q_ejecutado_step" in info:
                q_paso = float(info["q_ejecutado_step"])
                p_paso = float(info.get("p_ejecutado_step", self.P_referencia or 0.0))
            else:
                remaining_now = float(info.get("remaining", remaining_prev))
                q_paso = max(remaining_prev - remaining_now, 0.0)
                remaining_prev = remaining_now
                p_paso = float(info.get("best_ask", self.P_referencia or 0.0))

            if q_paso > 0:
                q_ejecutado_acumulado += q_paso
                monto_acumulado += p_paso * q_paso

            if q_ejecutado_acumulado >= q_slice:
                razon_termino = "inventario_agotado"

        env.close()

        # Precio promedio ponderado por volumen; si no hubo ejecuciones, usar P_referencia.
        if q_ejecutado_acumulado > 0:
            p_promedio = monto_acumulado / q_ejecutado_acumulado
        else:
            p_promedio = self.P_referencia

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

        # OBI_agregado: placeholder 0.0 documentado en SM_schema.json. El Maestro
        # no tiene su propio ABIDES (ver docstring de modulo); si se quiere un
        # valor real, hay que decidir como agregarlo desde los 3 Ejecutores
        # (ej. promedio del OBI_t de cada S_E en su ultimo step) -- es una
        # decision de diseno pendiente, no la tome por mi cuenta.
        s_m[5] = 0.0

        hour = self.current_time.hour
        if 9 <= hour < 11:
            s_m[6] = 0.0  # apertura
        elif 11 <= hour < 14:
            s_m[6] = 0.5  # media jornada
        else:
            s_m[6] = 1.0  # cierre

        return s_m

    def _lookup_yfinance_feature(self, columna: str) -> float:
        """Busca en self.df_yfinance (features S_M ya calculadas por Benjamin,
        tarea 1.2.2 -- ver data/processed/sm_features_<fecha>/) el valor en
        self.current_time. Conectado 29 sept (PS): antes era placeholder fijo
        en 0.0; los archivos reales ya existen localmente
        (data/processed/sm_features_2026-09-23/), asi que quien construya
        `datos_historicos` debe pasar ESE dataframe (con columnas
        'volatilidad'/'vol_promedio' ya calculadas), no el OHLCV crudo de
        yfinance sin procesar."""
        if self.current_time not in self.df_yfinance.index or columna not in self.df_yfinance.columns:
            return 0.0  # fuera de rango de los datos cargados o columna no presente
        valor = self.df_yfinance.loc[self.current_time, columna]
        return float(valor) if pd.notna(valor) else 0.0

    def _is_jornada_terminada(self) -> bool:
        return self.current_time.hour >= 16

    def _compute_terminal_reward(self) -> float:
        """
        R_M = -IS_total - lambda * max(0, Q_pendiente) * P_mid_cierre

        IS_total = suma de slippage_parcial de todos los reportes de la jornada.
        lambda: self.lambda_penalty (calibrado en Sprint 4, tarea 2.2.2).
        """
        IS_total = sum(r["slippage_parcial"] for r in self.executor_reports)
        Q_pendiente = self.Q_total - self.Q_executed
        # P_mid_cierre: se usa el p_promedio del ULTIMO reporte del Ejecutor
        # (viene de un env real ahora, ABIDES o fallback) como proxy del precio
        # de cierre; si no hubo ningun reporte (episodio vacio), cae a P_referencia.
        if self.executor_reports:
            P_mid_cierre = self.executor_reports[-1]["p_promedio"]
        else:
            P_mid_cierre = self.P_referencia

        r_m = -IS_total - self.lambda_penalty * max(0.0, Q_pendiente) * (P_mid_cierre or 0.0)
        return r_m

    def _save_logs(self):
        """
        Persiste maestro_states.csv, executor_states.csv, executor_actions.csv,
        rewards.csv y episode_summary.json segun la estructura definida en
        docs/arquitectura_entorno_simulacion.md, seccion 5.
        """
        pass  # a implementar en Sprint 3


# ----------------------------------------------------------------------
# Politicas PPO conectadas a redes reales (Mauricio Reynoso - Tarea 2.2.1)
# ----------------------------------------------------------------------

_default_master_network: Optional["MasterActorCritic"] = None
_default_executor_network: Optional["ExecutorActorCritic"] = None


def get_default_master_network() -> MasterActorCritic:
    """Instancia singleton de MasterActorCritic para inferencia por defecto."""
    global _default_master_network
    if _default_master_network is None:
        from src.models.actor_critic import MasterActorCritic
        _default_master_network = MasterActorCritic(obs_dim=7)
    return _default_master_network


def get_default_executor_network() -> ExecutorActorCritic:
    """Instancia singleton de ExecutorActorCritic para inferencia por defecto."""
    global _default_executor_network
    if _default_executor_network is None:
        from src.models.actor_critic import ExecutorActorCritic
        _default_executor_network = ExecutorActorCritic(obs_dim=27, action_dim=240)
    return _default_executor_network


def maestro_policy(s_m: np.ndarray, model: Optional[MasterActorCritic] = None, deterministic: bool = False) -> tuple[int, int]:
    """
    Politica del Agente Maestro evaluada con la red real MasterActorCritic (PPO).

    Args:
        s_m: vector S_M, shape (7,) o (1, 7).
        model: red MasterActorCritic opcional. Si es None, usa la red por defecto.
        deterministic: si True, toma argmax de logits. Si False, muestrea de Categorical.
    Returns:
        (alpha_idx, ventana_idx) - accion en MultiDiscrete([10, 4]).
    """
    import torch
    net = model if model is not None else get_default_master_network()
    device = next(net.parameters()).device
    obs = torch.as_tensor(s_m, dtype=torch.float32, device=device)
    if obs.dim() == 1:
        obs = obs.unsqueeze(0)

    with torch.no_grad():
        if deterministic:
            logits, _ = net(obs)
            action_idx = int(torch.argmax(logits, dim=-1).item())
        else:
            action, _, _, _ = net.get_action_and_value(obs)
            action_idx = int(action.item())

    # Decodificacion: 40 logits -> (alpha_idx 0..9, ventana_idx 0..3)
    alpha_idx, ventana_idx = divmod(action_idx, len(VENTANA_MIN_VALUES))
    return int(alpha_idx), int(ventana_idx)


def executor_policy(s_e: np.ndarray, model: Optional[ExecutorActorCritic] = None, deterministic: bool = False) -> int:
    """
    Politica del Agente Ejecutor evaluada con la red real ExecutorActorCritic (PPO).

    Args:
        s_e: vector S_E, shape (27,) o (1, 27).
        model: red ExecutorActorCritic opcional. Si es None, usa la red por defecto.
        deterministic: si True, toma argmax de logits. Si False, muestrea de Categorical.
    Returns:
        indice entero en [0, 240) -- decodificado luego por EjecutorActionSpace.decode_flat().
    """
    import torch
    net = model if model is not None else get_default_executor_network()
    device = next(net.parameters()).device
    obs = torch.as_tensor(s_e, dtype=torch.float32, device=device)
    if obs.dim() == 1:
        obs = obs.unsqueeze(0)

    with torch.no_grad():
        if deterministic:
            logits, _ = net(obs)
            action_idx = int(torch.argmax(logits, dim=-1).item())
        else:
            action, _, _, _ = net.get_action_and_value(obs)
            action_idx = int(action.item())

    return int(action_idx)
