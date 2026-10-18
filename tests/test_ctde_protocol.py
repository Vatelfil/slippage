"""Pruebas del Protocolo de Mensajeria CTDE Maestro-Ejecutores (Tarea 2.3.1).

Verifica:
  1. Ida y vuelta de serializacion/deserializacion JSON de ASIGNAR y REPORTE.
  2. Rechazo de mensajes invalidos o que violen el esquema.
  3. Desacoplamiento y funcionamiento del buzon CanalComunicacionCTDE.
  4. Una meta-orden completa corriendo de punta a punta intercambiando unicamente
     mensajes validos en JSON.
"""
import pytest
import numpy as np
import pandas as pd

from src.envs.ctde_protocol import (
    CanalComunicacionCTDE,
    MensajeAsignar,
    MensajeReporte,
    ValidationError,
    validar_mensaje_asignar,
    validar_mensaje_reporte,
)
from src.envs.maestro_ejecutor_protocol import MaestroEjecutorEnv


def test_mensaje_asignar_roundtrip():
    msg = MensajeAsignar(
        ejecutor_id="apertura",
        ventana_min=10,
        fraccion_meta_orden=0.15,
        q_asignado=1500.0,
        hora_inicio="09:30:00",
        timestamp_inicio="2026-09-29T09:30:00",
    )
    d = msg.to_dict()
    assert d["tipo"] == "asignar"
    assert d["ejecutor_id"] == "apertura"
    assert d["ventana_min"] == 10

    # JSON roundtrip
    s = msg.to_json()
    msg2 = MensajeAsignar.from_json(s)
    assert msg == msg2


def test_mensaje_reporte_roundtrip():
    msg = MensajeReporte(
        ejecutor_id="media_jornada",
        q_ejecutado=1200.0,
        p_promedio=5820.5,
        slippage_parcial=450.0,
        q_pendiente=300.0,
        pasos_usados=20,
        razon_termino="ventana_completada",
        hora_fin="11:40:00",
        timestamp_fin="2026-09-29T11:40:00",
    )
    d = msg.to_dict()
    assert d["tipo"] == "reporte"
    assert d["pasos_usados"] == 20
    assert d["razon_termino"] == "ventana_completada"

    s = msg.to_json()
    msg2 = MensajeReporte.from_json(s)
    assert msg == msg2


def test_mensaje_invalido_es_rechazado():
    # ejecutor_id invalido
    with pytest.raises(ValidationError):
        MensajeAsignar(
            ejecutor_id="madrugada",  # no existe
            ventana_min=5,
            fraccion_meta_orden=0.1,
            q_asignado=100.0,
            hora_inicio="09:30:00",
            timestamp_inicio="2026-09-29T09:30:00",
        )

    # ventana_min invalida (no es 1, 5, 10, 15)
    with pytest.raises(ValidationError):
        MensajeAsignar(
            ejecutor_id="apertura",
            ventana_min=7,  # invalida
            fraccion_meta_orden=0.1,
            q_asignado=100.0,
            hora_inicio="09:30:00",
            timestamp_inicio="2026-09-29T09:30:00",
        )

    # q_asignado negativo
    with pytest.raises(ValidationError):
        MensajeAsignar(
            ejecutor_id="apertura",
            ventana_min=5,
            fraccion_meta_orden=0.1,
            q_asignado=-50.0,
            hora_inicio="09:30:00",
            timestamp_inicio="2026-09-29T09:30:00",
        )

    # razon_termino invalida en REPORTE
    with pytest.raises(ValidationError):
        MensajeReporte(
            ejecutor_id="cierre",
            q_ejecutado=100.0,
            p_promedio=5800.0,
            slippage_parcial=0.0,
            q_pendiente=0.0,
            pasos_usados=10,
            razon_termino="error_inesperado",  # invalido
            timestamp_fin="2026-09-29T16:00:00",
        )


def test_canal_comunicacion_desacoplado():
    canal = CanalComunicacionCTDE()
    assert not canal.tiene_asignacion_pendiente()
    assert not canal.tiene_reporte_pendiente()

    # No se puede recibir sin haber enviado
    with pytest.raises(RuntimeError):
        canal.recibir_asignacion()

    msg_asig = MensajeAsignar(
        ejecutor_id="apertura",
        ventana_min=5,
        fraccion_meta_orden=0.1,
        q_asignado=500.0,
        hora_inicio="09:30:00",
        timestamp_inicio="2026-09-29T09:30:00",
    )
    canal.enviar_asignacion(msg_asig)
    assert canal.tiene_asignacion_pendiente()

    recibido = canal.recibir_asignacion()
    assert recibido.q_asignado == 500.0
    assert not canal.tiene_asignacion_pendiente()

    msg_rep = MensajeReporte(
        ejecutor_id="apertura",
        q_ejecutado=500.0,
        p_promedio=5800.0,
        slippage_parcial=20.0,
        q_pendiente=0.0,
        pasos_usados=10,
        razon_termino="inventario_agotado",
        timestamp_fin="2026-09-29T09:35:00",
    )
    canal.enviar_reporte(msg_rep)
    assert canal.tiene_reporte_pendiente()

    rep_recibido = canal.recibir_reporte()
    assert rep_recibido.q_ejecutado == 500.0
    assert not canal.tiene_reporte_pendiente()

    hist = canal.obtener_historial()
    assert len(hist) == 2
    assert hist[0]["direccion"] == "Maestro -> Ejecutor"
    assert hist[1]["direccion"] == "Ejecutor -> Maestro"


def test_meta_orden_completa_con_mensajes_validos(tmp_path):
    idx = pd.date_range("2026-09-29 09:30", "2026-09-29 16:00", freq="5min")
    rng = np.random.default_rng(42)
    datos = pd.DataFrame(
        {"volatilidad": rng.uniform(0.001, 0.003, len(idx)),
         "vol_promedio": rng.uniform(0.1, 0.3, len(idx))},
        index=idx,
    )

    env = MaestroEjecutorEnv(
        meta_orden_quantity=5_000,
        datos_historicos=datos,
    )
    s_m = env.reset()
    assert s_m.shape == (7,)

    done = False
    pasos_maestro = 0
    while not done and pasos_maestro < 20:
        # accion fija de prueba (10% de volumen, ventana de 5 min)
        s_m, r_m, done, info = env.step((1, 1))
        pasos_maestro += 1

    env.close()

    hist = env.canal.obtener_historial()
    assert len(hist) == pasos_maestro * 2  # 1 ASIGNAR + 1 REPORTE por paso
    for entry in hist:
        payload = entry["payload"]
        if entry["direccion"] == "Maestro -> Ejecutor":
            validar_mensaje_asignar(payload)
        else:
            validar_mensaje_reporte(payload)

    # Verificar guardado del log
    log_file = tmp_path / "ctde_run_log.json"
    env.canal.guardar_log(log_file)
    assert log_file.exists()
    assert log_file.stat().st_size > 0
