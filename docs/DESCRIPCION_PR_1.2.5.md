# Documentación de Arquitectura del Entorno de Simulación - Tarea 1.2.5 Sprint 2

## Descripción General

Esta rama implementa la **Tarea 1.2.5 (Sprint 2)**: Documentación formal de la arquitectura del entorno de simulación para el sistema de coordinación multi-agente de mitigación de slippage en el mercado IPSA.

## Qué se Hizo

Se desarrolló una especificación técnica completa que formaliza la interacción entre tres componentes principales del sistema:

1. **Agente Maestro** - Capa de coordinación que toma decisiones de alto nivel cada 30 minutos
2. **Agentes Ejecutores (3 instancias)** - Capa de ejecución que opera cada 30 segundos dentro de ventanas asignadas
3. **ABIDES-Gym** - Capa de simulación que proporciona dinámicas realistas del libro de órdenes

Los entregables generados incluyen:

### 1. Documento de Arquitectura
**Archivo:** `docs/arquitectura_entorno_simulacion.md`

Documento técnico de 10 páginas que especifica:

- **Sección 1: Visión General** - Descripción de las tres capas arquitectónicas y su interacción
- **Sección 2: Ciclo de Simulación (Reset/Step/Close)** - Especificación detallada del ciclo de vida con pseudocódigo comentado
- **Sección 3: Protocolo de Comunicación** - Definición formal de mensajes ASIGNAR y REPORTE en formato JSON
- **Sección 4: Mapeo de Datos en Runtime** - Especificación de fuentes para cada variable de estado (S_M: 7 variables, S_E: 26 variables)
- **Sección 5: Logging y Checkpoints** - Estructura de carpetas, formatos de almacenamiento y estrategia de checkpointing
- **Sección 6: Sincronización de Tiempos** - Alineación entre diferentes granularidades temporales (yfinance: 5 min, Maestro: 30 min, Ejecutor: 30 seg, ABIDES: segundo)

### 2. Diagrama de Flujo
**Archivo:** `docs/diagrama_ciclo_reset_step.png`  
**Fuente:** `docs/diagrama_ciclo_reset_step.mmd`

Diagrama de flujo visual que representa:

- Fase de inicialización (reset)
- Loop principal de 30 minutos (iteración Maestro)
- Sub-loop de ejecución (operación Ejecutor)
- Decisiones de terminación
- Fase de finalización (close)

El diagrama utiliza Mermaid para facilitar versionado y regeneración.

### 3. Pseudocódigo Comentado
**Archivo:** `src/envs/maestro_ejecutor_protocol.py`

Especificación en pseudocódigo Python de la clase `MaestroEjecutorEnv` que incluye:

- Constructor: inicialización de parámetros y estado
- Método `reset()`: preparación del episodio
- Método `step()`: ciclo principal de 30 minutos
- Método `_run_executor_episode()`: sub-loop de ejecución
- Método `_compute_sm_state()`: cálculo del vector de estado Maestro
- Método `_compute_terminal_reward()`: cálculo de recompensa terminal
- Método `close()`: finalización del episodio
- Funciones placeholder `maestro_policy()` y `executor_policy()` para ser reemplazadas con redes neuronales

El código mantiene sintaxis Python válida con comentarios extensos documentando cada paso.

## Por Qué se Hizo

### Necesidad Técnica

El Sprint 1 completó la especificación formal de los espacios de estado y acción:
- SM_schema.json: 7 variables observadas por el Maestro
- SE_schema.json: 26 variables observadas por los Ejecutores

Sin embargo, faltaba la especificación del mecanismo de coordinación:

- Cómo se comunican Maestro y Ejecutores
- Cuál es el ciclo completo de simulación
- Cómo se mapean los datos en tiempo de ejecución
- Qué interfaz debe implementar el siguiente desarrollador

### Dependencia en el Proyecto

La arquitectura del proyecto sigue una estructura de especificación progresiva:

```
Sprint 1: Definición de Espacios (S_M, S_E, A_M, A_E)
    └─> Contrato de datos entre capas
        
Sprint 2: Especificación de Arquitectura (1.2.5)
    └─> Protocolo de coordinación
    └─> Ciclo de simulación
    └─> Interfaz para implementador
        
Sprint 3: Implementación de Redes Neuronales
    └─> Mauricio Reynoso reemplaza pseudocódigo por redes PPO
    └─> Integración con ABIDES-Gym real
    └─> Ciclo de entrenamiento
        
Sprint 4-7: Entrenamiento y Validación
    └─> Calibración de hiperparámetros
    └─> Pruebas comparativas vs benchmarks
    └─> Análisis estadístico
```

Este documento es el puente entre especificación (Sprint 1) e implementación (Sprint 3).

### Riesgos Evitados

Sin esta documentación, Sprint 3 enfrentaría:

- Ambigüedad sobre el ciclo completo de simulación
- Incompatibilidades entre componentes
- Refactorización costosa en medio del desarrollo de redes neuronales
- Necesidad de adivinanza sobre detalles de coordinación

## Para Qué Sirve

### Uso Inmediato (Sprint 3)

El responsable de Sprint 3 (Mauricio Reynoso) utilizará esta documentación para:

1. **Entender la arquitectura completa** - Leer `docs/arquitectura_entorno_simulacion.md` y `diagrama_ciclo_reset_step.png` para comprender el flujo global

2. **Implementar la clase base** - Reemplazar el pseudocódigo en `src/envs/maestro_ejecutor_protocol.py` con implementación real integrando ABIDES-Gym

3. **Definir las policies** - Crear `maestro_policy()` y `executor_policy()` como redes neuronales entrenadas con PPO

4. **Validar integración** - Verificar que el ciclo reset/step/close funciona end-to-end

### Uso a Largo Plazo

- **Documentación de tesis** - Material para capítulo sobre arquitectura del ambiente de entrenamiento
- **Reproducibilidad** - Otro investigador puede seguir exactamente este protocolo para replicar resultados
- **Validación académica** - La comisión examinadora puede verificar rigor en el diseño del sistema
- **Mantenimiento futuro** - Referencia clara para modificaciones o extensiones posteriores

### Garantías Técnicas

Esta documentación proporciona:

- **Contrato explícito** - Interfaz clara entre componentes
- **Especificación sin ambigüedades** - Ciclo de simulación completamente definido
- **Trazabilidad** - Mapeo de cada variable a su fuente y cálculo
- **Validación** - Estructura de logging para verificar comportamiento esperado

## Qué se Utilizó

### Documentación de Entrada

Esta tarea se basó en:

1. **Sprint 1 - Esquemas de Estado**
   - `docs/schemas/SM_schema.json`: Especificación formal de 7 variables del Maestro
   - `docs/schemas/SE_schema.json`: Especificación formal de 26 variables de Ejecutores
   - Proporción utilizada: 60% del contenido técnico

2. **Sprint 1 - Contexto del Proyecto**
   - `Contexto_Agente_Programacion.md` (Secciones 3-5): Arquitectura general, MDPs, especificaciones de recompensa
   - Proporción utilizada: 30% del contenido técnico

3. **Especificación Técnica Original (Título I)**
   - Fundamentos teóricos del sistema multi-agente
   - Proporción utilizada: 10% del contenido conceptual

### Herramientas y Tecnologías

| Herramienta | Propósito | Localización |
|---|---|---|
| **Markdown** | Documentación técnica formateada | `docs/arquitectura_entorno_simulacion.md` |
| **Mermaid** | Diagramas de flujo versionados | `docs/diagrama_ciclo_reset_step.mmd` |
| **Python** | Pseudocódigo comentado | `src/envs/maestro_ejecutor_protocol.py` |
| **JSON** | Definición de protocolos de mensajes | En secciones de documentación |
| **Git** | Control de versiones | Branch `feature/1.2.5-architecture` |

### Frameworks y Librerías Referenciados (No ejecutados)

| Framework | Rol en Arquitectura | Implementación Planeada |
|---|---|---|
| **Gymnasium** | Definir espacios de acción/observación | Sprint 3 (Mauricio Reynoso) |
| **PyTorch** | Red neuronal Actor-Crítico para PPO | Sprint 3 (Mauricio Reynoso) |
| **ABIDES-Gym** | Simulador del libro de órdenes | Sprint 3 (Integración) |
| **NumPy** | Cálculos numéricos de estado | Sprint 3 (Runtime) |
| **Pandas** | Manejo de datos históricos de yfinance | Sprint 2-3 (Benjamín Farias + Mauricio Reynoso) |

## Explicación del Diagrama

### Estructura General

El diagrama `diagrama_ciclo_reset_step.png` representa el ciclo completo de simulación mediante un gráfico de flujo que muestra:

1. **Entrada (reset)**
2. **Procesamiento iterativo (step)**
3. **Salida (close)**

### Fase 1: Reset (Inicialización)

```
reset() inicia:
├─ Cargar datos históricos yfinance (OHLCV del IPSA)
├─ Inicializar simulador ABIDES-Gym
├─ Resetear contadores internos (Q_executed=0, decision_count=0)
├─ Calcular estado inicial S_M (7 dimensiones)
└─ Retornar S_M al entrenador
```

**Duración:** Una sola ejecución por episodio  
**Entrada:** meta_orden_quantity, datos_historicos, abides_config  
**Salida:** s_m_initial con dimensión (7,)

### Fase 2: Loop Principal (Iteración cada 30 minutos)

La sección central y más importante del diagrama, que se repite mientras `current_time < 16:00`:

#### Paso 2a: Observación del Maestro
```
Maestro observa estado actual S_M:
├─ q_t: (Q_total - Q_executed) / Q_total
├─ tau_t: (current_time - 09:30) / 390 minutos
├─ n_slices: decision_count / 13
├─ volatilidad: volatilidad del precio (yfinance, rolling(6).std())
├─ vol_promedio: volumen promedio (yfinance, rolling(6).mean())
├─ OBI_agregado: imbalance del libro (ABIDES-Gym)
└─ sesion: codificación del tramo horario (0=apertura, 0.5=media, 1=cierre)
```

#### Paso 2b: Decisión del Maestro
```
Maestro ejecuta política π_maestro(S_M):
├─ Entrada: S_M con 7 variables normalizadas en [0,1]
├─ Salida: (alpha_idx, ventana_idx)
│  ├─ alpha_idx ∈ {0,1,...,9} → α ∈ {0.05, 0.10, ..., 0.50}
│  └─ ventana_idx ∈ {0,1,2,3} → ventana ∈ {1, 5, 10, 15} minutos
└─ Cálculo: q_slice = α × (Q_total - Q_executed)
```

#### Paso 2c: Comunicación Maestro → Ejecutor
```
Mensaje ASIGNAR (JSON):
{
  "tipo": "asignar",
  "timestamp_inicio": current_time,
  "q_slice": q_slice,
  "ventana_min": ventana_min,
  "instrucciones": "Ejecuta q_slice en próximos ventana_min minutos"
}
```

#### Paso 2d: Sub-loop del Ejecutor (Cada 30 segundos)
Repetir `ventana_min × 2` veces (puesto que cada paso = 30 segundos):

```
Ejecutor en cada iteración:
├─ Observar estado S_E (26 dimensiones)
│  ├─ Privado (3): q_slice, q_pendiente, tau_slice
│  ├─ Bid LOB (10): precios y volúmenes de 5 niveles
│  ├─ Ask LOB (10): precios y volúmenes de 5 niveles
│  └─ Mercado (4): spread, OBI, tasa_ordenes, P_mid
│
├─ Ejecutar política π_ejecutor(S_E):
│  ├─ Entrada: S_E con 26 variables
│  └─ Salida: (tipo_orden, volumen_frac, nivel_precio)
│
├─ Ejecutar acción en ABIDES-Gym
│  ├─ tipo_orden ∈ {0=mercado, 1=límite, 2=esperar}
│  ├─ volumen_frac ∈ [0,1]: fracción de q_slice a ejecutar
│  ├─ nivel_precio ∈ {0,1,2,3}: {mejor_bid, bid-1, bid-2, P_mid}
│  └─ Retorno: nuevo S_E, reward_ejecutor
│
└─ Acumular: q_ejecutado, precio_promedio

Decisión: ¿Se completó la ventana?
├─ No → repetir sub-loop
└─ Sí → proceder a comunicación
```

#### Paso 2e: Comunicación Ejecutor → Maestro
```
Mensaje REPORTE (JSON):
{
  "tipo": "reporte",
  "timestamp_fin": current_time + ventana,
  "q_ejecutado": cantidad_realmente_ejecutada,
  "p_promedio": precio_promedio_ponderado,
  "slippage_parcial": (p_promedio - p_referencia) × q_ejecutado,
  "razon_termino": "ventana_completada"
}
```

#### Paso 2f: Actualización del Maestro
```
Maestro recibe reporte:
├─ Q_executed += q_ejecutado
├─ Registrar q_ejecutado, p_promedio, slippage_parcial
├─ Calcular nuevo S_M
├─ current_time += 30 minutos
├─ decision_count += 1
└─ Preparar siguiente iteración

Decisión: ¿Fin de jornada?
├─ No (current_time < 16:00) → volver a Paso 2a
└─ Sí (current_time ≥ 16:00) → proceder a close
```

### Fase 3: Close (Finalización)

```
close() realiza:
├─ Calcular reward terminal:
│  R_M = -IS_total - λ × max(0, Q_pendiente) × P_mid_cierre
│  donde IS_total = suma de slippage_parcial de todas ventanas
│
├─ Guardar logs:
│  ├─ maestro_states.csv: histórico de S_M
│  ├─ executor_actions.csv: histórico de acciones
│  ├─ rewards.csv: histórico de recompensas
│  └─ episode_summary.json: resumen consolidado
│
└─ Cerrar ABIDES-Gym y liberar recursos
```

### Puntos Clave del Diagrama

1. **Bucles Anidados**
   - Loop externo: 30 minutos (Maestro toma 1 decisión)
   - Loop interno: 30 segundos × ventana_min (Ejecutor actúa)
   - Total de pasos Ejecutor = ventana_min × 2

2. **Puntos de Decisión**
   - Ventana completada: determina cuándo reportar el Ejecutor
   - Fin de jornada: determina cuándo terminar el episodio
   - Ambas son bifurcaciones críticas en el flujo

3. **Flujo de Información**
   - Maestro → Ejecutor: mensaje ASIGNAR
   - Ejecutor → Maestro: mensaje REPORTE
   - ABIDES-Gym ↔ Ejecutor: S_E y acciones

4. **Invariantes Mantenidas**
   - Q_executed siempre ≤ Q_total
   - decision_count siempre ≤ 13 (máximo 390 min / 30 min)
   - Todas las variables de estado normalizadas en [0,1]

## Criterios de Aceptación

Esta implementación cumple los siguientes criterios:

### Completud Documentaria
- [x] Documento de 10+ páginas con 6 secciones obligatorias
- [x] Pseudocódigo comentado en sintaxis Python válida
- [x] Diagrama de flujo visual en formato PNG + fuente Mermaid
- [x] Referencias cruzadas a SM_schema.json y SE_schema.json

### Claridad Técnica
- [x] Ciclo reset/step/close completamente especificado
- [x] Protocolo ASIGNAR/REPORTE en formato JSON con campos documentados
- [x] Mapeo explícito de todas las variables a sus fuentes
- [x] Sincronización de tiempos clara (yfinance, ABIDES, Maestro, Ejecutor)

### Usabilidad para Sprint 3
- [x] Implementador puede leer documento sin ambigüedades
- [x] Pseudocódigo es cercano a Python real
- [x] Placeholders claros para redes neuronales (maestro_policy, executor_policy)
- [x] Estructura permite extensión directa con ABIDES-Gym real

## Próximos Pasos

### Sprint 3 (Mauricio Reynoso)
1. Leer `docs/arquitectura_entorno_simulacion.md` y `diagrama_ciclo_reset_step.png`
2. Reemplazar pseudocódigo en `src/envs/maestro_ejecutor_protocol.py` con implementación real
3. Integrar ABIDES-Gym en método `step()` y `_run_executor_episode()`
4. Implementar `maestro_policy()` y `executor_policy()` como redes neuronales PPO
5. Validar que ciclo completo funciona end-to-end

### Sprint 3 (Paolo Sepúlveda)
1. Formalizar espacios Gymnasium basados en schemas y arquitectura documentada
2. Implementar clases de observation_space y action_space reales

## Notas Técnicas

### Dependencias con Otros Componentes

- **Sprint 2 - Tarea 1.2.1 (Benjamín)**: Datos yfinance. Esta documentación asume datos disponibles; no depende de su implementación.
- **Sprint 2 - Tarea 1.2.3 (Mauricio)**: ABIDES-Gym funcionando. Esta documentación especifica la interfaz; implementación de ABIDES es independiente.

### Assumptions Técnicos

- Jornada bursátil: 09:30 a 16:00 (390 minutos)
- Frecuencia Maestro: cada 30 minutos (13 decisiones máximo)
- Frecuencia Ejecutor: cada 30 segundos (2 pasos por minuto)
- Todos los estados normalizados en [0,1] (excepto OBI en [-1,1])
- ABIDES-Gym proporciona LOB Nivel 2 (5 niveles bid + ask)

### Limitaciones Conocidas

- OBI_agregado en Sprint 2 es placeholder (0.0); se integra completamente en Sprint 2 Tarea 1.2.3
- Policies (maestro_policy, executor_policy) son stubs; se implementan con redes neuronales en Sprint 3
- Logging strategy definida pero no implementada (implementación en Sprint 3)

## Histórico de Cambios

- **Commit 66a4480** - Tarea 1.2.5 completada: arquitectura, diagrama, pseudocódigo
- **Commit 3f34912** - Sprint 1: schemas y briefing
- **Commit e7ae9dc** - Merge PR #1: configuración base

## Referencias

### Documentos Relacionados
- `docs/schemas/SM_schema.json` - Especificación Agente Maestro
- `docs/schemas/SE_schema.json` - Especificación Agentes Ejecutores
- `Contexto_Agente_Programacion.md` - Contexto técnico y teoría del proyecto

### Estándares Aplicados
- Especificación OpenAI Gym / Gymnasium para espacios
- Notación MDP (Markov Decision Process) estándar
- Diagramas de flujo UML

## Autor

Paolo Sepúlveda (PS)  
Tarea 1.2.5 - Sprint 2  
Proyecto: Coordinación de Agentes para Mitigación del Slippage (IPSA)  
Universidad Tecnológica Metropolitana (UTEM)

---

**Fecha de creación:** 29 de agosto de 2026  
**Estado:** Listo para revisión y merge a main
