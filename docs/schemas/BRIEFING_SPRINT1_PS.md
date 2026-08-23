# 📋 BRIEFING EJECUTIVO — SPRINT 1
## Coordinación de Agentes para la Mitigación del Slippage (IPSA)
### Análisis del Estado: Tarea de Paolo Sepúlveda (PS)
**Fecha:** 22 de agosto de 2026 | **Sprint:** 1 (17–28 ago) | **Estado:** ✅ COMPLETADO

---

## 1. RESUMEN EJECUTIVO

### Proyecto
**"Coordinación de Agentes para la Mitigación del Slippage (IPSA)"** — Sistema de aprendizaje por refuerzo (RL) multi-agente jerárquico para minimizar el *slippage* (diferencia entre precio esperado y precio real ejecutado) en órdenes bursátiles del mercado accionario chileno.

- **Institución:** Universidad Tecnológica Metropolitana (UTEM)
- **Programa:** Título II
- **Hipótesis:** Reducir el implementation shortfall (IS) en ≥10% vs TWAP y VWAP bajo simulación histórica
- **Tecnología:** Python 3.9.18, PyTorch 2.2.0, Gymnasium 0.29.1, ABIDES-Gym (JPMorgan)

---

## 2. TAREA DE PS — SPRINT 1 ✅

### Identificación
- **ID:** 1.1.4
- **Nombre:** *Definición formal de los vectores de estado S_M y S_E*
- **Responsable:** Paolo Sepúlveda (PS)
- **Fechas:** 17–28 agosto 2026
- **Estado:** **✅ COMPLETADO**

### ¿Se cumplió la tarea?
**SÍ. Totalmente completada.**

La tarea requería formalizar los esquemas del vector de estado del **Agente Maestro** (S_M, 7 dimensiones) y los **Agentes Ejecutores** (S_E, 26 dimensiones) de forma que pudieran ser consumidos por otros miembros del equipo en posteriores sprints.

---

## 3. QUÉ SE HIZO — ENTREGABLES

### 3.1 Documentación Técnica Formal (Contexto_Agente_Programacion.md)

**📄 Archivo:** `Contexto_Agente_Programacion.md` (457 líneas)

Documento maestro que define la **arquitectura completa del proyecto** desde primeros principios:

#### Contenidos clave:

1. **Sección 1–3:** Introducción, problema de slippage, solución propuesta
   - Qué es el slippage: ejemplo numérico con FALABELLA (movimiento de precio por orden grande)
   - Limitaciones de estrategias clásicas: TWAP, VWAP

2. **Sección 4: Agente Maestro (MDP_M)**
   - **Vector de estado S_M:** 7 variables de entrada
     - `q_t`: fracción de inventario no ejecutado
     - `tau_t`: fracción de tiempo transcurrido (09:30–16:00)
     - `n_slices`: número de decisiones emitidas / 13
     - `volatilidad`: desviación estándar rolling(6) del precio de cierre
     - `vol_promedio`: volumen promedio rolling(6)
     - `OBI_agregado`: imbalance del libro de órdenes (pendiente integración ABIDES-Gym)
     - `sesion`: tramo horario codificado (apertura=0, media=0.5, cierre=1)
   
   - **Espacio de acción A_M:** MultiDiscrete[10, 4] = 40 combinaciones
     - `alpha_t`: fracción de inventario a ejecutar {0.05, 0.10, …, 0.50}
     - `ventana_min`: duración de ventana {1, 5, 10, 15} minutos
   
   - **Recompensa R_M:** terminal/sparse
     - Formula: `R_M = -IS_total - λ·max(0, Q_pendiente)·P_mid_cierre`
     - Penaliza implementation shortfall e inventario no ejecutado al cierre

3. **Sección 5: Agentes Ejecutores (MDP_E)**
   - **Vector de estado S_E:** 26 variables (4 subgrupos)
     - 3 variables privadas (q_slice, q_pendiente, tau_slice)
     - 10 variables del lado comprador del LOB (bid_precios + bid_volumenes, 5 niveles)
     - 10 variables del lado vendedor del LOB (ask_precios + ask_volumenes, 5 niveles)
     - 4 variables de mercado (spread, OBI, tasa_ordenes, P_mid)
   
   - **Espacio de acción A_E:** Dict híbrido (discreto + continuo)
     - `tipo_orden`: {mercado, límite, esperar}
     - `volumen_frac`: Box[0,1] fracción a ejecutar
     - `nivel_precio`: {mejor_bid, bid-1, bid-2, P_mid}
   
   - **Recompensa R_E:** densa (cada 30 seg)
     - Formula: `R_E = (P_mid_t - P_ejec_t)·q_ejec - β·σ²_precio·q_ejec`
     - Premia ejecutar mejor que mid, penaliza riesgo temporal

4. **Sección 6–7:** Algoritmo PPO, parámetros técnicos
5. **Sección 8:** Plan de desarrollo por sprints (Hitos 5–8)
6. **Sección 9–14:** Roles, tareas de Paolo, estructura repo, contratos de datos, métricas

---

### 3.2 Esquemas JSON Formales (Gymnasium-compatible)

#### **Archivo 1:** `docs/schemas/SM_schema.json` (115 líneas)

Especificación JSON del Agente Maestro:

```json
{
  "$schema_name": "SM_schema",
  "$version": "1.0.0",
  "$owner": "Paolo Sepúlveda (PS)",
  "$sprint": "Sprint 1 - Tarea 1.1.4",
  "$date": "2026-08-22",
  "gymnasium_space": {
    "type": "Box",
    "shape": [7],
    "dtype": "float32",
    "low":  [0.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0],
    "high": [1.0, 1.0, 1.0, 1.0, 1.0,  1.0, 1.0]
  },
  "variables": [
    { "index": 0, "name": "q_t", "range": [0.0, 1.0], "source": "Interno", ... },
    { "index": 1, "name": "tau_t", "range": [0.0, 1.0], "source": "Timestamp (yfinance)", ... },
    ...
  ],
  "action_space": {
    "type": "MultiDiscrete",
    "dims": [10, 4],
    "total_combinations": 40,
    "dimensions": [
      { "name": "alpha_t", "values": [0.05, 0.10, ..., 0.50] },
      { "name": "ventana_min", "values": [1, 5, 10, 15] }
    ]
  },
  "consumers": [
    { "role": "MR", "task": "2.1.1", "use": "Red Actor-Crítico del Maestro" },
    { "role": "BF", "task": "1.2.2", "use": "Pipeline de features" }
  ]
}
```

**Consumidores designados:**
- **Mauricio Reynoso (MR):** Arquitectura de red neuronal (Task 2.1.1)
- **Benjamin Farias (BF):** Pipeline de cálculo de features (Task 1.2.2)

#### **Archivo 2:** `docs/schemas/SE_schema.json` (57 líneas)

Especificación JSON de los Agentes Ejecutores (análogo, 26 dimensiones):

```json
{
  "$schema_name": "SE_schema",
  "$version": "1.0.0",
  "$owner": "Paolo Sepúlveda (PS)",
  "gymnasium_space": {
    "type": "Box",
    "shape": [26],
    "dtype": "float32",
    "low_by_group": {
      "privado": [0.0, 0.0, 0.0],
      "bid_precios": [0.0, 0.0, 0.0, 0.0, 0.0],
      ...
    }
  },
  "variables": [
    { "index": 0, "name": "q_slice", "range": [0.0, 1.0], "source": "Agente Maestro", ... },
    { "index": "3-7", "name": "bid_precios", "range": [0.0, 1.0], "dim": 5, "source": "ABIDES-Gym", ... },
    ...
  ],
  "action_space": {
    "type": "Dict",
    "fields": [
      { "name": "tipo_orden", "space": "Discrete(3)" },
      { "name": "volumen_frac", "space": "Box(0.0, 1.0, shape=(1,))" },
      { "name": "nivel_precio", "space": "Discrete(4)" }
    ]
  }
}
```

**Consumidores:**
- **Mauricio Reynoso (MR):** 3 redes Actor-Crítico para ejecutores (Task 2.1.2)
- **Benjamin Farias (BF):** Integración ABIDES-Gym y calibración RMSC04 (Task 1.2.3)

---

### 3.3 Documentación de Diseño Ejecutivo

**📄 Archivo:** `docs/sprint1_esquema_vectores_PS.docx`

Documento ejecutivo Word que sintetiza los esquemas para circulación entre stakeholders.

---

## 4. ARQUITECTURA FORMALIZADA

### 4.1 Jerarquía Multi-Agente

```
                    ┌─────────────────┐
                    │  AGENTE MAESTRO │  
                    │  (PPO, γ=0.99)  │  Decide cada 30 min:
                    │   S_M (7 dims)  │  - Fracción α_t a ejecutar
                    │   A_M (40 comb.)│  - Duración ventana
                    └────────┬────────┘
                             │ q_slice + ventana_min
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
      ┌──────────┐  ┌──────────┐  ┌──────────┐
      │Ejecutor 1│  │Ejecutor 2│  │Ejecutor 3│  Ejecutan cada 30 seg:
      │Apertura  │  │Media jorn│  │  Cierre  │  - Tipo de orden (mercado/límite/esperar)
      │09:30-11:30│ │11:30-14:00│ │14:00-16:00  - Volumen a ejecutar
      │(PPO,γ=0.95)│(PPO,γ=0.95)│(PPO,γ=0.95)   - Nivel de precio objetivo
      │S_E(26)  │  │S_E(26)  │  │S_E(26)  │
      └──────────┘  └──────────┘  └──────────┘
              │              │              │
              └──────────────┴──────────────┘
                             │
                    ┌────────▼────────┐
                    │   LOB simulado  │  ABIDES-Gym
                    │  (RMSC04)       │  (JPMorgan)
                    └─────────────────┘
```

### 4.2 Ciclo de Coordinación (CTDE — Centralized Training, Decentralized Execution)

1. **Maestro** observa S_M → emite acción (α_t, ventana_min)
2. **Maestro** envía q_slice al **Ejecutor activo** del tramo
3. **Ejecutor** decide tipo de orden, volumen, nivel cada 30 seg sobre S_E
4. **Ejecutor** reporta q_ejecutado, P_promedio al finalizar ventana
5. **Maestro** actualiza inventario; recibe R_M al cierre (16:00)

### 4.3 Contratos de Datos

| De | A | Qué | Cuándo | Responsable |
|---|---|---|---|---|
| Pipeline | Maestro | DF[timestamp, close, vol, volatilidad, ...] | Inicio episodio | BF |
| Maestro | Ejecutor | q_slice, ventana_min | Cada 30 min | MR |
| ABIDES-Gym | Ejecutor | S_E (26 vars) | Cada 30 seg | BF |
| Ejecutor | Maestro | q_ejecutado, P_promedio | Fin ventana | MR |
| Entorno | Maestro | R_M (terminal) | Cierre (16:00) | MR |

---

## 5. DEFINICIÓN FORMAL DE VECTORES

### Vector de Estado del Maestro: S_M (7 dimensiones)

| # | Variable | Tipo | Rango | Fórmula / Fuente | Descripción |
|---|---|---|---|---|---|
| 0 | q_t | float32 | [0, 1] | (Q_total - Q_ejecutado) / Q_total | Fracción de inventario sin ejecutar |
| 1 | tau_t | float32 | [0, 1] | (t - 09:30) / 390 min | Progreso de tiempo en jornada |
| 2 | n_slices | float32 | [0, 1] | slices_enviados / 13 | Decisiones emitidas / máximo esperado |
| 3 | volatilidad | float32 | [0, 1] | rolling(6).std() [Close] normXX | Vol. precio (ventana móvil) |
| 4 | vol_promedio | float32 | [0, 1] | rolling(6).mean() [Volume] norm | Vol. transacción (ventana móvil) |
| 5 | OBI_agregado | float32 | [-1, 1] | (V_bid - V_ask) / (V_bid + V_ask) | Imbalance libro órdenes (ABIDES) |
| 6 | sesion | float32 | [0, 1] | {0=Apertura, 0.5=Media, 1=Cierre} | Tramo horario |

**Espacio Gymnasium:** `Box(low=[0,0,0,0,0,-1,0], high=[1,1,1,1,1,1,1], dtype=float32)`

**Espacio de acción:** `MultiDiscrete([10, 4])` → 40 combinaciones
- alpha_t ∈ {0.05, 0.10, 0.15, ..., 0.50} (10 opciones)
- ventana_min ∈ {1, 5, 10, 15} (4 opciones)

---

### Vector de Estado de Ejecutores: S_E (26 dimensiones)

Subdivido en 4 grupos:

#### Grupo 1: Privado (3 dims)
| # | Variable | Rango | Fuente | Descripción |
|---|---|---|---|---|
| 0 | q_slice | [0, 1] | Maestro | Cantidad asignada (normalizada) |
| 1 | q_pendiente | [0, 1] | Interno | Fracción de slice sin ejecutar |
| 2 | tau_slice | [0, 1] | Interno | Progreso dentro de ventana asignada |

#### Grupo 2: Lado Comprador (10 dims)
| # | Variable | Rango | Fuente | Descripción |
|---|---|---|---|---|
| 3–7 | bid_precios | [0, 1] | ABIDES LOB L2 | Precios de 5 mejores niveles bid |
| 8–12 | bid_volumenes | [0, 1] | ABIDES LOB L2 | Volúmenes en esos 5 niveles |

#### Grupo 3: Lado Vendedor (10 dims)
| # | Variable | Rango | Fuente | Descripción |
|---|---|---|---|---|
| 13–17 | ask_precios | [0, 1] | ABIDES LOB L2 | Precios de 5 mejores niveles ask |
| 18–22 | ask_volumenes | [0, 1] | ABIDES LOB L2 | Volúmenes en esos 5 niveles |

#### Grupo 4: Mercado (4 dims)
| # | Variable | Rango | Fuente | Descripción |
|---|---|---|---|---|
| 23 | spread_t | [0, 1] | ABIDES | Spread bid-ask normalizado |
| 24 | OBI_t | [-1, 1] | ABIDES | Imbalance instantáneo |
| 25 | tasa_ordenes | [0, 1] | ABIDES | Tasa de llegada de órdenes (últimos 30s) |
| 26 | P_mid | [0, 1] | ABIDES | Precio mid = (ask¹ + bid¹) / 2 |

**Espacio Gymnasium:** `Box(shape=(26,), dtype=float32)` con límites por grupo

**Espacio de acción:** `Dict`
```python
{
  'tipo_orden': Discrete(3),              # 0=mercado, 1=límite, 2=esperar
  'volumen_frac': Box(0, 1, shape=(1,)),  # Fracción de slice
  'nivel_precio': Discrete(4)             # 0=best_bid, 1=bid-1, 2=bid-2, 3=P_mid
}
```

---

## 6. FUENTES DE DATOS IDENTIFICADAS

### Nivel 1 (Maestro): Datos Históricos OHLCV
- **Fuente:** yfinance (gratuito)
- **Activos:** 30 acciones del IPSA (ej: FALABELLA.SN, COPEC.SN, SQM-B.SN)
- **Período:** 60 días hábiles recientes
- **Intervalo:** 5 minutos
- **Preprocesamiento:** Forward fill, normalización MinMaxScaler

### Nivel 2 (Ejecutores): Nivel 2 del Libro de Órdenes (LOB)
- **Fuente:** ABIDES-Gym (simulador JPMorgan, open source)
- **Configuración:** RMSC04 (1 Exchange, 2 Market Makers, 102 Value Agents, etc.)
- **Calibración:** Parámetros IPSA (spread, tick, perfil de volumen)
- **Alternativa:** Modelo Poisson sintético (λ+, λ−, θ) validado académicamente

---

## 7. MÉTRICAS DE ÉXITO

### Métrica Principal
**Implementation Shortfall (IS):**
```
IS = (P_ejecución_promedio - P_referencia) × Q_total
```
- Objetivo: Reducir ≥10% vs TWAP y VWAP

### Métricas Secundarias
- Slippage promedio por jornada
- % cumplimiento de meta-orden
- Volatilidad de ejecución
- Tiempo promedio de ejecución

### Diseño Experimental
- 90 corridas de prueba (3 liquidez × 3 tamaños × 10 semillas)
- Tamaños: pequeña (1K), mediana (5K), grande (20K) acciones
- Escenarios: apertura, media jornada, cierre
- Benchmark: TWAP, VWAP

---

## 8. RIESGOS Y NOTAS TÉCNICAS

### Python 3.9.18 es obligatorio
- ABIDES-Gym tiene dependencias específicas para Python 3.9.x
- Usar entorno virtual aislado
- Incompatible con Python 3.10+

### Conflictos de Dependencias Conocidos
- `gym` vs `gymnasium` (ya solucionado con Gymnasium 0.29.1)
- `ray` y `pomegranate` requieren contenedor Docker o conda aislado
- Sprint 2 incluye tarea 1.2.4 (MR) para resolver

### OBI Agregado (S_M[5])
- Proviene de ABIDES-Gym, **no de yfinance**
- Durante Sprint 1: usar 0.0 como placeholder
- Se integra completamente en Sprint 2 (tarea 1.2.3–1.2.4)

---

## 9. TAREAS SIGUIENTES (SPRINT 2: 31 ago – 11 sep)

### Para Paolo (PS)
**Tarea 1.2.5:** *Documentación técnica de la arquitectura del entorno de simulación*
- Detallar el ciclo de reset/step en Gymnasium
- Documentar interfaz entre Maestro y Ejecutores
- Especificar formato de logs y checkpoints

### Para Mauricio (MR)
- **1.2.3:** Prueba de concepto ABIDES-Gym (contenedor Python 3.9)
- **1.2.4:** Diagnóstico de conflictos de dependencias

### Para Benjamin (BF)
- **1.2.1:** Limpieza y preprocesamiento de datos IPSA
- **1.2.2:** Cálculo de features del vector S_M

---

## 10. ESTADO DEL REPOSITORIO

### Estructura Actual
```
D:\claude agente\
├── Contexto_Agente_Programacion.md     (457 líneas) ← MAESTRO
├── docs/
│   ├── sprint1_esquema_vectores_PS.docx
│   └── schemas/
│       ├── SM_schema.json              (115 líneas) ✅
│       └── SE_schema.json              (57 líneas)  ✅
├── package.json                         (para tooling)
├── package-lock.json
├── Plan_Desarrollo_Titulo_II_Scrum.xlsx (roadmap)
└── scripts/
    └── gen_sprint1_doc.js              (generador)
```

**Nota:** No es aún un repositorio Git. Debe crearse en GitHub como `slippage-agents` (privado).

---

## 11. CHECKLIST DE COMPLETUD — TAREA 1.1.4

| Entregable | Estado | Archivo/Ref |
|---|---|---|
| ✅ Documentación maestro del proyecto | Completado | Contexto_Agente_Programacion.md |
| ✅ Definición S_M (7 variables) | Completado | SM_schema.json, Contexto §4 |
| ✅ Definición S_E (26 variables) | Completado | SE_schema.json, Contexto §5 |
| ✅ Espacios Gymnasium formales | Completado | JSON schemas (Box, MultiDiscrete, Dict) |
| ✅ Acciones A_M (40 combinaciones) | Completado | SM_schema.json |
| ✅ Acciones A_E (híbrido) | Completado | SE_schema.json |
| ✅ Recompensas R_M y R_E | Completado | Contexto §4.3, §5.3 |
| ✅ Traceabilidad de consumidores | Completado | Campos "consumers" en JSON |
| ✅ Referencias a datos y fuentes | Completado | Contexto §7 |
| ✅ Documentación ejecutiva | Completado | sprint1_esquema_vectores_PS.docx |

**Conclusión:** Tarea 1.1.4 **100% completada**.

---

## 12. RECOMENDACIONES PARA LOS PRÓXIMOS SPRINTS

### Inmediato (Sprint 2)
1. **Crear repositorio GitHub privado** `slippage-agents`
2. **MR:** Resolver conflictos ABIDES-Gym en contenedor Python 3.9
3. **BF:** Implementar pipeline de yfinance con las features definidas en S_M
4. **PS:** Documentar ciclo de simulación y protocolo de comunicación Maestro–Ejecutores

### Corto plazo (Sprint 3–4)
1. **MR:** Implementar redes Actor-Crítico en PyTorch según schemas
2. **BF:** Calibrar distribuciones Poisson para LOB sintético
3. **PS:** Validar que datos históricos se adapten a los rangos [0,1] de S_M

### Mediano plazo (Sprint 6–7)
1. Ciclos de entrenamiento iterativos
2. Monitoreo de métricas (IS, slippage)
3. Comparativa estadística PPO vs TWAP vs VWAP

---

## 13. DOCUMENTOS CLAVE

| Documento | Formato | Ubicación | Propósito |
|---|---|---|---|
| Contexto Agente Programación | Markdown | `Contexto_Agente_Programacion.md` | Especificación técnica maestro |
| SM Schema | JSON | `docs/schemas/SM_schema.json` | Contrato S_M para Maestro |
| SE Schema | JSON | `docs/schemas/SE_schema.json` | Contrato S_E para Ejecutores |
| Sprint 1 Esquema Vectores | DOCX | `docs/sprint1_esquema_vectores_PS.docx` | Resumen ejecutivo |
| Plan Scrum | XLSX | `Plan_Desarrollo_Titulo_II_Scrum.xlsx` | Roadmap general |
| Título I (Entregable anterior) | DOCX | `TÍTULO I_ Coordinación...docx` | Fundamentos teóricos |

---

## 14. CONCLUSIONES

### ✅ Sprint 1 Completado

Paolo Sepúlveda (PS) **completó exitosamente** la tarea 1.1.4 de Sprint 1:

1. **Definición formal** de los vectores de estado S_M (7 dims) y S_E (26 dims)
2. **Especificación Gymnasium-compatible** en JSON con tipos, rangos, fuentes
3. **Documentación técnica** que sirve como contrato para MR (redes NN) y BF (pipeline datos)
4. **Trazabilidad completa** entre esquemas y tareas consumidoras en Sprints posteriores

### Calidad de Entregables

- ✅ **Precisión técnica:** Definiciones alineadas con literatura RL y Gymnasium
- ✅ **Completud:** Todos los campos requeridos documentados (tipo, rango, fórmula, fuente)
- ✅ **Interoperabilidad:** Consumidores (MR, BF) pueden implementar directamente desde JSON
- ✅ **Escalabilidad:** Estructura permite extensiones futuras (nuevas variables, espacios)

### Próximos Hitos

- **Sprint 2 (31 ago–11 sep):** Pipeline datos + ABIDES-Gym
- **Sprint 3 (14–25 sep):** Redes Actor-Crítico
- **Sprint 4 (28 sep–9 oct):** Algoritmo PPO + calibración
- **Hito 7 (26 oct–20 nov):** Validación comparativa vs benchmarks
- **Hito 8 (23 nov–18 dic):** Redacción de informe y defensa

---

**Documento preparado:** 22 de agosto de 2026 | **Por:** Sistema de análisis | **Para:** Equipo UTEM
