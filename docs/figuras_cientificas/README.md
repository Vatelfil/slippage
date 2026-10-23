# Figuras científicas del proyecto (para informes y presentaciones)

**Elaborado por:** PS con apoyo de Claude Code (uso autorizado por la universidad), 23 de octubre de 2026. **Pendiente de revisión por:** MR y BF (cada figura resume su parte del sistema).

Cuatro figuras de formato artículo que explican el proyecto completo, de los datos reales a la evaluación. Cada una existe en **PNG** (4000 × 2640 px, listo para diapositivas) y en **PDF vectorial** (para el informe; se puede ampliar sin perder calidad). Todas las cifras salen del código, los esquemas JSON y los resultados del repositorio; ninguna se dibujó a mano.

| Figura | Archivo | Qué responde |
|---|---|---|
| 1 | `fig1_arquitectura` | ¿Cómo se conecta todo? De los datos reales a la evaluación, y dónde corre cada pieza (PC, GitHub, Colab, Drive) |
| 2 | `fig2_formulacion` | ¿Cómo interactúan los agentes en el tiempo? Jornada, ciclo Maestro–Ejecutor, especificación de cada proceso de decisión y mensajes del protocolo |
| 3 | `fig3_espacios` | ¿Qué ve, qué decide y cómo se premia cada agente? S_M, S_E, A_M, A_E, R_M y R_E, con el origen de cada variable |
| 4 | `fig4_diseno_experimental` | ¿Cómo se evalúa? Protocolo, las 10 meta-órdenes, reparto de TWAP y VWAP, resultado actual de las referencias y métricas |

## Cómo leer cada figura

### Figura 1: arquitectura y flujo de datos
- **Cinco columnas, de izquierda a derecha:** (1) datos reales de yfinance y su limpieza; (2) calibración y validación; (3) entorno simulado; (4) sistema multiagente; (5) entrenamiento y evaluación. Las flechas de arriba dicen qué viaja de una columna a la siguiente.
- **La flecha punteada verde** muestra el único dato real que llega directo a un agente: `volatilidad` y `vol_promedio` del Maestro. Todo lo que ve el Ejecutor viene del simulador.
- **Franja inferior:** dónde vive cada pieza. El código se escribe en el PC, GitHub lo guarda, Colab lo clona y corre ABIDES, y Drive guarda los resultados, que se descargan a mano.
- **Idea central:** los datos reales **calibran** el simulador (parámetros por activo y tramo); los agentes **aprenden dentro del simulador**.

### Figura 2: formulación jerárquica
- **(a)** Una jornada de 09:30 a 16:00 con los tres tramos de los Ejecutores y, debajo, cómo ve el tramo el Maestro. El recuadro rojo es la discrepancia D5 (11:00 frente a 11:30). Los 13 círculos son las decisiones del Maestro; el zoom muestra que dentro de cada decisión el Ejecutor opera solo `2v` pasos de 30 s.
- **(b)** Los seis pasos del ciclo: el Maestro observa y elige (α, v); ASIGNAR; el Ejecutor opera contra el mercado simulado; REPORTE; el Maestro actualiza y repite.
- **(c)** Especificación de MDP_M y MDP_E: estados, acciones, recompensas, factor de descuento y red.
- **(d)** Campos de los mensajes ASIGNAR y REPORTE.

### Figura 3: estados, acciones y recompensas
- **(a) y (b):** cada variable con su rango y su origen (color): verde azulado = dato real de yfinance, morado = simulador, gris = interno del entorno, ámbar = hora. En (b) se ve cómo se reparten las 27 variables de S_E y un esquema del libro de órdenes (5 niveles por lado, P_mid, spread y OBI).
- **(c):** las 40 acciones del Maestro como una cuadrícula α × ventana, con su índice plano.
- **(d):** las 240 acciones del Ejecutor como tres cuadrículas (tipo de orden × fracción × nivel de precio). LIMIT_SELL equivale a esperar.
- **(e):** fórmulas de R_M y R_E y la variante D3.

### Figura 4: diseño experimental
- **(a)** Protocolo en cinco pasos y su estado (hecho, pendiente, listo en script).
- **(b)** Las 10 meta-órdenes con su tamaño en v1 (100.000 acciones) y en v2 (10 % del día y 5 % en el cierre), y su semilla.
- **(c)** Cómo reparten la misma orden TWAP y VWAP (calculado con `schedule_desde` y el perfil de volumen del repositorio).
- **(d)** Slippage medio de TWAP y VWAP por orden (archivo v2, ABIDES, 2 semillas; barras de error = error estándar entre semillas).
- **(e)** Métricas, pruebas estadísticas, criterios, semillas e hipótesis del Título I.

## Fuentes de las cifras
| Figura | Fuente |
|---|---|
| 1 | `Contexto_Agente_Programacion.md` (sección 7), `src/config/market_params.py`, `data/calibration/`, `docs/calibracion_rmsc04_*`, `docs/validacion_formal_2.2.5_PS.md` |
| 2 | `src/envs/maestro_ejecutor_protocol.py`, `src/envs/ctde_protocol.py`, `DESVIACIONES_TITULO1_VS_IMPLEMENTACION.md` (D5) |
| 3 | `docs/schemas/SM_schema.json`, `docs/schemas/SE_schema.json`, `src/envs/spaces.py`, `src/envs/abides_bridge.py`, `src/envs/reward_utils.py`, `src/models/actor_critic.py` |
| 4 | `data/meta_ordenes/meta_ordenes_v1.json` y `meta_ordenes_v2_candidata.json`, `perfil_volumen_v1.csv`, `data/analysis/benchmarks_meta_ordenes_v2.json` |

## Límites y estado de los valores (23 de octubre de 2026)
- **Provisionales:** λ = 0,05 (R_M) y β = 0,0061796 (R_E); se revalidan con entrenamientos reales. La variante D3 de R_E espera la decisión de BF.
- **`OBI_agregado` vale 0** en S_M: falta decidir cómo agregarlo desde los Ejecutores.
- **Figura 4 usa el archivo v2 candidato** (D1 sin decidir); cuando BF decida el tamaño de las órdenes y exista el sistema entrenado, se regenera.
- **A_E** es la versión discretizada (240 acciones) y **S_E** tiene 27 variables; ambas difieren del Título I y están anotadas en `DESVIACIONES_TITULO1_VS_IMPLEMENTACION.md`.
- Los números de agentes del simulador (ruido 250–1000, momentum 3–12) varían según el activo calibrado.

## Cómo regenerarlas
```
cd docs/figuras_cientificas/generador
python fig1.py && python fig2.py && python fig3.py && python fig4.py
```
Requiere `matplotlib`, `numpy` y `pandas`. La figura 4 lee los archivos del repositorio, así que se actualiza sola al cambiar los datos. `lib.py` contiene las funciones de dibujo comunes.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
