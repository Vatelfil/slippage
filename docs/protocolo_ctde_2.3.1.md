# Protocolo de Comunicación Desacoplada CTDE Maestro-Ejecutores (Tarea 2.3.1)

**Elaborado por:** Mauricio Reynoso (MR)  
**Fecha:** Octubre 2026 (Sprint 5)  
**Revisión:** Paolo Sepúlveda (PS) y Benjamín Farías (BF)  
**Código fuente:** [`src/envs/ctde_protocol.py`](../src/envs/ctde_protocol.py), [`src/envs/maestro_ejecutor_protocol.py`](../src/envs/maestro_ejecutor_protocol.py)  
**Esquemas formales:** [`docs/schemas/protocolo_asignar_schema.json`](schemas/protocolo_asignar_schema.json), [`docs/schemas/protocolo_reporte_schema.json`](schemas/protocolo_reporte_schema.json)  
**Batería de pruebas:** [`tests/test_ctde_protocol.py`](../tests/test_ctde_protocol.py)

---

## 1. Propósito y Arquitectura CTDE

El paradigma **Centralized Training with Decentralized Execution (CTDE)** adoptado en el Título I (sección 4) establece una jerarquía de dos niveles para mitigar el slippage e impacto de mercado:
1. **Nivel Estratégico (Agente Maestro):** Observa el estado macroeconómico y de inventario global $S_M \in \mathbb{R}^7$ cada 30 minutos de jornada, decidiendo la fracción $\alpha_t \in [0.05, 0.50]$ y el horizonte táctico $\tau_t \in \{1, 5, 10, 15\}$ minutos.
2. **Nivel Táctico (3 Agentes Ejecutores Especializados):**
   - **Apertura (09:30 - 11:30):** Absorbe volatilidad inicial y alta actividad.
   - **Media jornada (11:30 - 14:00):** Opera en régimen de liquidez estable y spread estrecho.
   - **Cierre (14:00 - 16:00):** Liquida inventario residual previo al toque de campana.

Para garantizar desacoplamiento estricto, la comunicación no ocurre mediante llamadas a métodos acoplados o variables globales, sino a través de **mensajes estructurados en JSON** mediados por un canal de mensajería (`CanalComunicacionCTDE`), con validación de contrato por esquema formal.

---

## 2. Contratos de Mensajería JSON

### 2.1 Mensaje ASIGNAR (Maestro $\to$ Ejecutor)
El Maestro deposita una directiva de ejecución al inicio de cada ventana de 30 minutos:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "tipo": "asignar",
  "ejecutor_id": "apertura",
  "ventana_min": 5,
  "fraccion_meta_orden": 0.10,
  "q_asignado": 1000.0,
  "hora_inicio": "09:30:00",
  "timestamp_inicio": "2026-09-29T09:30:00"
}
```

**Campos obligatorios:**
- `tipo`: Constante `"asignar"`.
- `ejecutor_id`: Identificador del agente táctico (`"apertura"`, `"media_jornada"` o `"cierre"`).
- `ventana_min`: Duración táctica de la orden en minutos (valores válidos: 1, 5, 10, 15).
- `fraccion_meta_orden`: Fracción asignada $\alpha_t \in [0.0, 1.0]$.
- `q_asignado`: Cantidad exacta de acciones a ejecutar en la ventana ($q_{\text{slice}} = \alpha_t \cdot Q_{\text{pendiente}}$).
- `hora_inicio`: Hora local de inicio (formato `HH:MM:SS`).
- `timestamp_inicio`: Marca temporal completa ISO 8601.

### 2.2 Mensaje REPORTE (Ejecutor $\to$ Maestro)
Tras concluir los pasos tácticos de 30 segundos (o agotar el volumen asignado), el Ejecutor emite su informe de ejecución:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "tipo": "reporte",
  "ejecutor_id": "apertura",
  "q_ejecutado": 1000.0,
  "p_promedio": 5824.50,
  "slippage_parcial": 24500.0,
  "q_pendiente": 0.0,
  "pasos_usados": 10,
  "razon_termino": "inventario_agotado",
  "hora_fin": "09:35:00",
  "timestamp_fin": "2026-09-29T09:35:00"
}
```

**Campos obligatorios:**
- `tipo`: Constante `"reporte"`.
- `ejecutor_id`: Tramo del ejecutor que operó.
- `q_ejecutado`: Volumen acumulado ejecutado en la ventana ($q_{\text{ejec}} \le q_{\text{slice}}$).
- `p_promedio`: Precio promedio ponderado por volumen (VWAP táctico obtenido).
- `slippage_parcial`: Costo de slippage acumulado en CLP frente al precio de referencia inicial ($IS_{\text{parcial}} = (P_{\text{promedio}} - P_{\text{ref}}) \cdot q_{\text{ejec}}$). Se expresa siempre en CLP; si el simulador subyacente opera en otra unidad de cuenta (como ABIDES en décimos de CLP), el orquestador convierte automáticamente los precios dividiendo por `unidades_por_clp` (ver §3.1).
- `q_pendiente`: Acciones no ejecutadas del slice ($q_{\text{slice}} - q_{\text{ejec}}$).
- `pasos_usados`: Cantidad de pasos de 30 s ejecutados (máximo $2 \times \text{ventana\_min}$).
- `razon_termino`: Causa de finalización (`"ventana_completada"` o `"inventario_agotado"`).
- `timestamp_fin`: Marca temporal de término ISO 8601.

---

## 3. Ejemplo de Log de Auditoría Completo (Meta-Orden de 5.000 acciones)

A continuación se muestra un extracto del log generado por el canal (`CanalComunicacionCTDE.guardar_log`) en una corrida controlada de jornada completa con el **simulador de Poisson** (`EjecutorEnvPoissonFallback`, el entorno por defecto del orquestador), no con ABIDES-Gym:

```json
[
  {
    "direccion": "Maestro -> Ejecutor",
    "payload": {
      "tipo": "asignar",
      "ejecutor_id": "apertura",
      "ventana_min": 5,
      "fraccion_meta_orden": 0.1,
      "q_asignado": 500.0,
      "hora_inicio": "09:30:00",
      "timestamp_inicio": "2026-09-29 09:30:00"
    }
  },
  {
    "direccion": "Ejecutor -> Maestro",
    "payload": {
      "tipo": "reporte",
      "ejecutor_id": "apertura",
      "q_ejecutado": 500.0,
      "p_promedio": 5800.0,
      "slippage_parcial": 0.0,
      "q_pendiente": 0.0,
      "pasos_usados": 10,
      "razon_termino": "inventario_agotado",
      "hora_fin": "09:35:00",
      "timestamp_fin": "2026-09-29 09:35:00"
    }
  },
  {
    "direccion": "Maestro -> Ejecutor",
    "payload": {
      "tipo": "asignar",
      "ejecutor_id": "apertura",
      "ventana_min": 5,
      "fraccion_meta_orden": 0.1,
      "q_asignado": 450.0,
      "hora_inicio": "10:00:00",
      "timestamp_inicio": "2026-09-29 10:00:00"
    }
  },
  {
    "direccion": "Ejecutor -> Maestro",
    "payload": {
      "tipo": "reporte",
      "ejecutor_id": "apertura",
      "q_ejecutado": 450.0,
      "p_promedio": 5801.2,
      "slippage_parcial": 540.0,
      "q_pendiente": 0.0,
      "pasos_usados": 10,
      "razon_termino": "inventario_agotado",
      "hora_fin": "10:05:00",
      "timestamp_fin": "2026-09-29 10:05:00"
    }
  }
]
```

### 3.1 Log de una ventana con ABIDES-Gym (Colab, 20 oct 2026)

*Corrida en Colab revisada y ratificada por MR.* Una decisión del Maestro con el entorno `EjecutorEnvAbides` calibrado (FALABELLA, `rmsc04_ipsa_FALABELLA_2026-08-23.json`, vía `make_calibrated_env_factory`): tramo apertura, 10 % de una meta-orden de 10 000 acciones, ventana de 5 minutos. Se intercambiaron 2 mensajes (1 ASIGNAR y 1 REPORTE) y los dos pasaron la validación de esquema. Log completo: [`data/colab_resultados/ctde_log_ventana_abides.json`](../data/colab_resultados/ctde_log_ventana_abides.json); resumen de la corrida (también del entrenador): [`resumen_evidencia_abides.json`](../data/colab_resultados/resumen_evidencia_abides.json). Script: `scripts/colab/evidencia_ctde_ppo_abides_ps.py`.

```json
{"direccion": "Ejecutor -> Maestro",
 "payload": {"ejecutor_id": "apertura", "q_ejecutado": 1000.0, "p_promedio": 5992.6924,
             "slippage_parcial": 22592.399999999907, "q_pendiente": 0.0, "pasos_usados": 7,
             "razon_termino": "inventario_agotado", "hora_fin": "09:35:00", "tipo": "reporte"}}
```

**Resolución de la decisión de unidades (MR, 21 oct 2026):**
Se adopta la opción de **convertir en el protocolo con `unidades_por_clp`** (parámetro ya existente en `BridgeConfig` y en los JSON de calibración de la tarea 2.2.4: 10 en la calibración oficial en décimos de CLP; 100 en la configuración cruda de ABIDES; 1 en Poisson).

**Implementación en el orquestador (`src/envs/maestro_ejecutor_protocol.py`):**
1. Al recibir `info` en `reset()`, el orquestador obtiene `unidades = float(info.get("unidades_por_clp", 1.0))`. Si `P_referencia` no estaba fijado, se calcula como `raw_entry / unidades`, quedando siempre en CLP (~5 969,8 CLP para FALABELLA).
2. En cada paso de ejecución, el precio de ejecución `p_paso` se normaliza a CLP (directo desde `info["p_fill_step_clp"]` que ya viene convertido por `ExecutorRewardState`, o dividiendo por `unidades`).
3. El mensaje `REPORTE` resultante publica `p_promedio` y `slippage_parcial` estrictamente en CLP.
4. Consecuencias positivas:
   - Coherencia total entre simuladores: `IS_total` y $R_M$ tienen la misma escala monetaria en CLP tanto sobre ABIDES como sobre el simulador Poisson.
   - Preservación de la calibración: El hiperparámetro $\lambda = 0{,}05$ de la recompensa del Maestro (tarea 2.2.2) conserva el balance 1:1 entre penalización e `IS_total` para el cual fue diseñado, sin sufrir la distorsión de un factor $	imes 10$ que habría provocado operar en décimos.

---

## 4. Verificación y Resultados de Tests

La suite [`tests/test_ctde_protocol.py`](../tests/test_ctde_protocol.py) valida:
1. `test_mensaje_asignar_roundtrip`: Serialización JSON exacta y deserialización con tipos nativos (`PASSED`).
2. `test_mensaje_reporte_roundtrip`: Validación y serialización completa del reporte táctico (`PASSED`).
3. `test_mensaje_invalido_es_rechazado`: Rechazo estricto de tramos inexistentes, duraciones fuera de $\{1, 5, 10, 15\}$, razones de término inválidas o cantidades negativas (`PASSED`).
4. `test_canal_comunicacion_desacoplado`: Control de estado del buzón (lecturas destructivas sin duplicidad y excepciones ante buzón vacío) (`PASSED`).
5. `test_meta_orden_completa_con_mensajes_validos`: Ejecución integral de meta-orden donde el 100% de los pasos viajan por el canal CTDE y se registran en disco (`PASSED`).
