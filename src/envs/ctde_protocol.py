"""Protocolo de Mensajeria CTDE Maestro-Ejecutores (Tarea 2.3.1).

Elaborado por Mauricio Reynoso (MR).

Define los contratos de comunicacion desacoplada entre el Agente Maestro
(estrategico) y los 3 Agentes Ejecutores (tacticos: apertura, media jornada, cierre):
  1. Mensaje ASIGNAR (Maestro -> Ejecutor): fraccion, q_slice, ventana_min, hora inicio.
  2. Mensaje REPORTE (Ejecutor -> Maestro): q_ejecutado, precio promedio, slippage parcial,
     q_pendiente, pasos usados, razon de termino.
  3. Canal de comunicacion (CanalComunicacionCTDE) que desacopla el paso de mensajes
     e implementa validacion automatica contra los esquemas JSON oficiales.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "docs" / "schemas"
ASIGNAR_SCHEMA_PATH = SCHEMA_DIR / "protocolo_asignar_schema.json"
REPORTE_SCHEMA_PATH = SCHEMA_DIR / "protocolo_reporte_schema.json"

# Carga perezosa de esquemas JSON
_ASIGNAR_SCHEMA: Optional[Dict[str, Any]] = None
_REPORTE_SCHEMA: Optional[Dict[str, Any]] = None


def _get_asignar_schema() -> Dict[str, Any]:
    global _ASIGNAR_SCHEMA
    if _ASIGNAR_SCHEMA is None:
        if ASIGNAR_SCHEMA_PATH.exists():
            with open(ASIGNAR_SCHEMA_PATH, "r", encoding="utf-8") as f:
                _ASIGNAR_SCHEMA = json.load(f)
        else:
            _ASIGNAR_SCHEMA = {}
    return _ASIGNAR_SCHEMA


def _get_reporte_schema() -> Dict[str, Any]:
    global _REPORTE_SCHEMA
    if _REPORTE_SCHEMA is None:
        if REPORTE_SCHEMA_PATH.exists():
            with open(REPORTE_SCHEMA_PATH, "r", encoding="utf-8") as f:
                _REPORTE_SCHEMA = json.load(f)
        else:
            _REPORTE_SCHEMA = {}
    return _REPORTE_SCHEMA


class ValidationError(ValueError):
    """Excepcion lanzada cuando un mensaje no cumple el esquema del protocolo."""
    pass


@dataclass
class MensajeAsignar:
    """Mensaje ASIGNAR enviado por el Maestro al Ejecutor del tramo activo."""
    ejecutor_id: str
    ventana_min: int
    fraccion_meta_orden: float
    q_asignado: float
    hora_inicio: str
    timestamp_inicio: str
    tipo: str = "asignar"

    def __post_init__(self):
        validar_mensaje_asignar(self.to_dict())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: Optional[int] = None) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MensajeAsignar:
        validar_mensaje_asignar(data)
        return cls(
            ejecutor_id=str(data["ejecutor_id"]),
            ventana_min=int(data["ventana_min"]),
            fraccion_meta_orden=float(data["fraccion_meta_orden"]),
            q_asignado=float(data["q_asignado"]),
            hora_inicio=str(data["hora_inicio"]),
            timestamp_inicio=str(data["timestamp_inicio"]),
            tipo=str(data.get("tipo", "asignar")),
        )

    @classmethod
    def from_json(cls, json_str: str) -> MensajeAsignar:
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class MensajeReporte:
    """Mensaje REPORTE emitido por el Ejecutor tras operar durante su ventana."""
    ejecutor_id: str
    q_ejecutado: float
    p_promedio: float
    slippage_parcial: float
    q_pendiente: float
    pasos_usados: int
    razon_termino: str
    timestamp_fin: str
    hora_fin: Optional[str] = None
    tipo: str = "reporte"

    def __post_init__(self):
        validar_mensaje_reporte(self.to_dict())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: Optional[int] = None) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MensajeReporte:
        validar_mensaje_reporte(data)
        return cls(
            ejecutor_id=str(data["ejecutor_id"]),
            q_ejecutado=float(data["q_ejecutado"]),
            p_promedio=float(data["p_promedio"]),
            slippage_parcial=float(data["slippage_parcial"]),
            q_pendiente=float(data["q_pendiente"]),
            pasos_usados=int(data["pasos_usados"]),
            razon_termino=str(data["razon_termino"]),
            timestamp_fin=str(data["timestamp_fin"]),
            hora_fin=str(data["hora_fin"]) if data.get("hora_fin") is not None else None,
            tipo=str(data.get("tipo", "reporte")),
        )

    @classmethod
    def from_json(cls, json_str: str) -> MensajeReporte:
        data = json.loads(json_str)
        return cls.from_dict(data)


def validar_mensaje_asignar(data: Dict[str, Any]) -> None:
    """Valida un diccionario contra el contrato del mensaje ASIGNAR."""
    # 1. Validacion estructural basica
    if data.get("tipo") != "asignar":
        raise ValidationError(f"tipo esperado 'asignar', recibido: {data.get('tipo')}")
    if data.get("ejecutor_id") not in ("apertura", "media_jornada", "cierre"):
        raise ValidationError(f"ejecutor_id invalido: {data.get('ejecutor_id')}")
    if data.get("ventana_min") not in (1, 5, 10, 15):
        raise ValidationError(f"ventana_min invalida: {data.get('ventana_min')}. Debe ser 1, 5, 10 o 15.")
    if not (0.0 <= float(data.get("fraccion_meta_orden", -1.0)) <= 1.0):
        raise ValidationError(f"fraccion_meta_orden fuera de rango [0, 1]: {data.get('fraccion_meta_orden')}")
    if float(data.get("q_asignado", -1.0)) < 0.0:
        raise ValidationError(f"q_asignado no puede ser negativo: {data.get('q_asignado')}")
    if "hora_inicio" not in data or "timestamp_inicio" not in data:
        raise ValidationError("Faltan campos temporales hora_inicio o timestamp_inicio")

    # 2. Validacion formal via jsonschema si esta disponible
    try:
        import jsonschema
        schema = _get_asignar_schema()
        if schema:
            jsonschema.validate(instance=data, schema=schema)
    except ImportError:
        pass
    except Exception as e:
        raise ValidationError(f"Error de validacion contra esquema ASIGNAR: {e}") from e


def validar_mensaje_reporte(data: Dict[str, Any]) -> None:
    """Valida un diccionario contra el contrato del mensaje REPORTE."""
    if data.get("tipo") != "reporte":
        raise ValidationError(f"tipo esperado 'reporte', recibido: {data.get('tipo')}")
    if data.get("ejecutor_id") not in ("apertura", "media_jornada", "cierre"):
        raise ValidationError(f"ejecutor_id invalido: {data.get('ejecutor_id')}")
    if float(data.get("q_ejecutado", -1.0)) < 0.0:
        raise ValidationError(f"q_ejecutado no puede ser negativo: {data.get('q_ejecutado')}")
    if float(data.get("p_promedio", -1.0)) < 0.0:
        raise ValidationError(f"p_promedio no puede ser negativo: {data.get('p_promedio')}")
    if float(data.get("q_pendiente", -1.0)) < 0.0:
        raise ValidationError(f"q_pendiente no puede ser negativo: {data.get('q_pendiente')}")
    if int(data.get("pasos_usados", -1)) < 0:
        raise ValidationError(f"pasos_usados no puede ser negativo: {data.get('pasos_usados')}")
    if data.get("razon_termino") not in ("ventana_completada", "inventario_agotado"):
        raise ValidationError(f"razon_termino invalida: {data.get('razon_termino')}")
    if "timestamp_fin" not in data:
        raise ValidationError("Falta campo temporal obligatorio timestamp_fin")

    try:
        import jsonschema
        schema = _get_reporte_schema()
        if schema:
            jsonschema.validate(instance=data, schema=schema)
    except ImportError:
        pass
    except Exception as e:
        raise ValidationError(f"Error de validacion contra esquema REPORTE: {e}") from e


class CanalComunicacionCTDE:
    """Canal de comunicacion desacoplado (asincronico a nivel logico) entre Maestro y Ejecutores.
    
    Permite intercambiar mensajes estrictamente validados en JSON, manteniendo
    un log de auditoria completo de todas las asignaciones y reportes de la jornada.
    """

    def __init__(self):
        self._buzon_asignar: Optional[str] = None
        self._buzon_reporte: Optional[str] = None
        self._historial_mensajes: List[Dict[str, Any]] = []

    def enviar_asignacion(self, mensaje: Union[MensajeAsignar, Dict[str, Any], str]) -> str:
        """El Maestro deposita un mensaje ASIGNAR en el canal."""
        if isinstance(mensaje, str):
            json_str = mensaje
            data = json.loads(json_str)
        elif isinstance(mensaje, MensajeAsignar):
            json_str = mensaje.to_json()
            data = mensaje.to_dict()
        elif isinstance(mensaje, dict):
            validar_mensaje_asignar(mensaje)
            json_str = json.dumps(mensaje, default=str)
            data = mensaje
        else:
            raise TypeError(f"Tipo de mensaje no soportado: {type(mensaje)}")

        validar_mensaje_asignar(data)
        self._buzon_asignar = json_str
        self._historial_mensajes.append({"direccion": "Maestro -> Ejecutor", "payload": data})
        return json_str

    def recibir_asignacion(self) -> MensajeAsignar:
        """El Ejecutor activo retira la asignacion pendiente del canal."""
        if self._buzon_asignar is None:
            raise RuntimeError("No hay ningun mensaje ASIGNAR pendiente en el canal.")
        json_str = self._buzon_asignar
        self._buzon_asignar = None
        return MensajeAsignar.from_json(json_str)

    def enviar_reporte(self, mensaje: Union[MensajeReporte, Dict[str, Any], str]) -> str:
        """El Ejecutor deposita su mensaje REPORTE en el canal."""
        if isinstance(mensaje, str):
            json_str = mensaje
            data = json.loads(json_str)
        elif isinstance(mensaje, MensajeReporte):
            json_str = mensaje.to_json()
            data = mensaje.to_dict()
        elif isinstance(mensaje, dict):
            validar_mensaje_reporte(mensaje)
            json_str = json.dumps(mensaje, default=str)
            data = mensaje
        else:
            raise TypeError(f"Tipo de mensaje no soportado: {type(mensaje)}")

        validar_mensaje_reporte(data)
        self._buzon_reporte = json_str
        self._historial_mensajes.append({"direccion": "Ejecutor -> Maestro", "payload": data})
        return json_str

    def recibir_reporte(self) -> MensajeReporte:
        """El Maestro retira el reporte emitido por el Ejecutor."""
        if self._buzon_reporte is None:
            raise RuntimeError("No hay ningun mensaje REPORTE pendiente en el canal.")
        json_str = self._buzon_reporte
        self._buzon_reporte = None
        return MensajeReporte.from_json(json_str)

    def tiene_asignacion_pendiente(self) -> bool:
        return self._buzon_asignar is not None

    def tiene_reporte_pendiente(self) -> bool:
        return self._buzon_reporte is not None

    def obtener_historial(self) -> List[Dict[str, Any]]:
        return list(self._historial_mensajes)

    def guardar_log(self, filepath: Union[str, Path]) -> None:
        p = Path(filepath)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(self._historial_mensajes, f, indent=2, default=str)
