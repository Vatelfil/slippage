# Capítulo 8. Discusión y análisis crítico de los resultados

**Tarea:** 4.1.3 (Sprint 8). **Autor:** PS, con apoyo de Claude Code. **Versión:** 28 de noviembre de 2026. Reorganizado según las observaciones del equipo: el método estadístico pasó al Capítulo 6 (sección 6.5) y al Anexo E, las cifras de resultados quedan en el Capítulo 7 y este capítulo solo las interpreta.

**Convención:**
- Costo = *implementation shortfall* en puntos base (bps) contra el precio de llegada.
- Diferencia = costo del sistema − costo de la referencia, en la misma corrida. **Negativa = el sistema cuesta menos.**
- Cada resultado de estadística inferencial indica la prueba, el n y el valor p. El procedimiento de cada prueba está en el Anexo E.

---

## 8.1 Objetivo del capítulo

El cuarto objetivo específico del Título I pide evaluar el sistema contra TWAP y VWAP con métricas de reducción de costo, y la última etapa de la metodología pide determinar en qué medida el sistema reduce el slippage y qué limitaciones conserva. Este capítulo interpreta los resultados del Capítulo 7 con ese fin. Responde cuatro preguntas: si el sistema cuesta menos que TWAP y VWAP, y con qué certeza (sección 8.2); de qué depende la diferencia (secciones 8.3 y 8.5); qué aporta cada nivel de la arquitectura (sección 8.4); y qué limitaciones tiene el resultado, qué implica en la práctica y cuánto cuesta cada alternativa (secciones 8.6 y 8.7).

## 8.2 Significancia de la reducción de costo

### 8.2.1 Resultado principal

En las 90 corridas pareadas, el sistema costó en promedio 3,34 bps menos que TWAP, una reducción relativa del 5,4 % (Capítulo 7, sección 7.3). Esa diferencia **no es estadísticamente significativa** (Wilcoxon de rangos con signo, n = 90, p = 0,386), el efecto es despreciable (d de Cohen = −0,05) y el sistema fue más barato en 46 de los 90 días. El resultado frente a VWAP es el mismo (−3,14 bps, p = 0,393).

El intervalo de confianza permite precisar qué se puede y qué no se puede concluir. No permite afirmar que el sistema reduzca el costo: con 90 días simulados no se pudo demostrar una reducción, lo que no equivale a demostrar que no la hay. Sí permite descartar, con un 95 % de confianza, ventajas medias mayores que 15,7 bps y desventajas mayores que 9,7 bps. En particular, la ventaja de −22 bps que sugería la primera evaluación queda fuera del intervalo (sección 8.2.4).

Figura: `data/analysis/figuras_4_1_4/histograma_diferencias_90.png` (Distribución de las 90 diferencias sistema − TWAP, con la prueba de Wilcoxon y la de Shapiro-Wilk).

### 8.2.2 Resultado por profundidad del market maker

Separando por escenario, la diferencia frente a TWAP va de −10,53 bps con ×4 a +3,87 con ×0,25 (Capítulo 7, sección 7.4), pero ninguna profundidad muestra una diferencia significativa: con la corrección de Holm, los tres valores p corregidos valen 1,0. Con 30 corridas por escenario, el plan de análisis ya anticipaba que difícilmente saldría significativo (Anexo D). La sección 8.3.3 discute si la diferencia depende de la profundidad.

### 8.2.3 Robustez

Las tres variantes registradas en el plan (sin la orden MO-06, promediando por orden y semilla, y con el costo ajustado por lo no ejecutado) dejan la diferencia entre −3,34 y −3,53 bps, sin significancia (Capítulo 7, sección 7.6). La conclusión no depende de una orden en particular, de la dependencia entre corridas ni del cumplimiento incompleto.

### 8.2.4 Por qué la primera evaluación sugería una ventaja mayor

En la primera evaluación (profundidad ×1, semillas 1 a 3, n = 30), el sistema costó −22,15 bps frente a TWAP (IC 95 % [−50,01; 4,43], Wilcoxon p = 0,096). En la evaluación final, la misma comparación en ×1 con las semillas 4 a 6 da −3,37 bps. La diferencia entre ambas se explica por la variabilidad entre días y no por un cambio del sistema. La desviación estándar de las diferencias por corrida es de 78,7 bps en la primera evaluación y de 67,5 bps en ×1 de la final; con 30 corridas, el error estándar de la media es de unos 12 a 14 bps, de modo que dos muestras de 30 pueden diferir en 20 bps por azar. Una prueba de Mann-Whitney entre las 30 diferencias de cada evaluación no muestra evidencia de que provengan de distribuciones distintas (p = 0,395; exploratorio).

La lección metodológica es que evaluar en días nuevos, con el análisis registrado antes, evitó informar como resultado un efecto que era en parte favorable por azar.

## 8.3 Comparación con TWAP y VWAP: de qué depende la diferencia

### 8.3.1 Dirección del precio durante el día

La ventaja del sistema depende sobre todo de cómo se mueve el precio ese día. Como indicador del movimiento se usa el costo de TWAP: un costo positivo significa que el precio subió mientras se compraba.

**Tabla.** Relación entre la diferencia sistema − TWAP y la dirección del precio durante el día (90 corridas, exploratorio).

| Medida (90 corridas, exploratorio) | Valor |
|---|---|
| Correlación de Spearman entre (sistema − TWAP) y el costo de TWAP | ρ = −0,78, p = 1,5·10⁻¹⁹ |
| Correlación de Pearson | r = −0,70, p = 1,5·10⁻¹⁴ |
| Días en que el precio subió (TWAP ≥ 0), n = 63 | El sistema ahorra 30,5 bps en promedio |
| Días en que el precio bajó (TWAP < 0), n = 27 | El sistema cuesta 60,0 bps más en promedio |

La correlación se repite en cada profundidad (−0,77 en ×4, −0,78 en ×1 y −0,54 en ×0,25). La causa es el calendario del Maestro (sección 8.4.1): compra una parte grande de lo pendiente al comienzo de cada media hora, así que concentra la compra temprano. Comprar temprano conviene si el precio sube después y perjudica si baja. La ventaja media del sistema es, en buena parte, el balance entre los días que suben y los que bajan en la muestra.

### 8.3.2 Variabilidad del costo entre días

**Tabla.** Desviación estándar del costo del sistema y de las referencias, con la prueba de Pitman-Morgan para varianzas pareadas (exploratorio).

| Grupo | Ref. | n | Desv. sistema | Desv. referencia | Razón | IC 95 % de la razón | Pitman-Morgan p |
|---|---|---|---|---|---|---|---|
| Total | TWAP | 90 | 118,8 | 154,6 | 0,77 | [0,69; 0,84] | 4,8·10⁻⁹ |
| Total | VWAP | 90 | 118,8 | 160,1 | 0,74 | [0,66; 0,81] | 2,4·10⁻⁹ |
| ×4 | TWAP | 30 | 113,0 | 155,3 | 0,73 | [0,61; 0,85] | 6,5·10⁻⁵ |
| ×1 | TWAP | 30 | 114,8 | 159,4 | 0,72 | [0,60; 0,79] | 4,7·10⁻⁵ |
| ×0,25 | TWAP | 30 | 130,8 | 153,5 | 0,85 | [0,69; 0,97] | 0,038 |

Aunque el costo medio es parecido, el del sistema varía entre un 15 % y un 28 % menos que el de TWAP, y la diferencia es significativa en el total y en cada profundidad. Este análisis no estaba en el plan, pero el mismo patrón ya había aparecido en la primera evaluación (razón 0,65, p = 8·10⁻⁵, n = 30). Para un operador, una menor dispersión reduce el riesgo de ejecución aunque el costo medio sea similar: el sistema evita los días muy caros, y también aprovecha menos los muy baratos.

Figura: `data/analysis/figuras_4_1_4/costo_por_estrategia_varianzas.png` (Costo por estrategia y prueba de varianzas pareadas de Pitman-Morgan, n = 90).

### 8.3.3 Profundidad del market maker

No hay evidencia de que la ventaja dependa de la profundidad del market maker (Kruskal-Wallis, H = 0,14, p = 0,930; Friedman con 30 bloques, p = 0,393; frente a VWAP, p = 0,963 y 0,273). La tendencia descriptiva (−10,5 bps en ×4, −3,4 en ×1 y +3,9 en ×0,25) no es significativa.

Esto es coherente con lo que se sabe del simulador (Capítulo 5, sección 5.5): la profundidad del market maker cambia bastante el costo de **comprar a mercado** (más profundidad, compra a mercado más cara), pero casi no cambia el costo de comprar con **órdenes límite**. Como los Ejecutores compran casi siempre con órdenes límite (Capítulo 6, sección 6.2.2), el costo del sistema responde poco a la profundidad, y la diferencia con TWAP queda dominada por la dirección del precio de cada día.

Figura: `data/analysis/3_2_3/diferencias_por_escenario.png` (Diferencias sistema − TWAP por profundidad del market maker, n = 30 por profundidad).

## 8.4 Aporte de cada nivel de la arquitectura

### 8.4.1 El Maestro aprendió un calendario casi fijo

**Tabla.** Acción más frecuente del Maestro en la evaluación final, por profundidad del market maker.

| Profundidad | Decisiones | Acción más frecuente | Frecuencia |
|---|---|---|---|
| ×4 | 282 | α = 0,50, ventana de 15 min | 272 (96,5 %) |
| ×1 | 282 | α = 0,50, ventana de 15 min | 275 (97,5 %) |
| ×0,25 | 282 | α = 0,40, ventana de 15 min | 204 (72,3 %) |

En la práctica, la política del Maestro equivale a «comprar la mitad de lo que falta cada media hora». La revisión del entrenamiento encontró tres causas. Primero, se entrenó sin la corrección del cierre: las órdenes que parten a las 14:00 no podían completarse y lo pendiente se castigaba, así que la manera más directa de reducir esa penalización era comprar rápido. Segundo, su estado no tenía información de mercado (desviación 13): la volatilidad y la actividad entraban como constantes y el desbalance del libro valía cero, de modo que el Maestro solo veía lo que faltaba, la hora y sus decisiones previas. Tercero, las ventanas de 30 minutos son mercados independientes, sin una tendencia del día que el Maestro pudiera aprender a anticipar.

Una prueba complementaria, en el mismo simulador de Poisson con que se entrenó el Maestro, comparó reglas fijas de α = 10 % a 50 % (ventana de 15 min) en días de actividad baja, media y alta (1.500 corridas pareadas). Entre las reglas que completan la orden en al menos el 95 % de las corridas, la más barata fue α = 0,5 en los tres tipos de día (24,5; 23,9 y 20,9 bps); las reglas más lentas parecían baratas solo porque no completaban la orden. Por lo tanto, α = 0,5 es la mejor regla fija en el mercado de entrenamiento del Maestro, y no un error del entrenamiento. Esto también explica por qué el control con reglas fijas (sección 8.4.2) no encuentra aporte del calendario. Su límite es que 0,5 es el máximo del espacio de acciones: el óptimo está en el borde, y no se sabe si comprar todavía más rápido sería mejor.

### 8.4.2 Control con reglas fijas: separación del aporte

Para separar el aporte del Maestro y el de los Ejecutores, se reemplazó al Maestro por dos reglas fijas, manteniendo los mismos Ejecutores, órdenes y semillas (profundidad ×1, n = 30 pares). El control se registró antes de correrlo.

**Tabla.** Control con reglas fijas: aporte del calendario del Maestro y de la capa de Ejecutores (profundidad ×1, n = 30, Wilcoxon con Holm por 3 pruebas).

| Comparación | Pregunta | Diferencia (bps) | IC 95 % | Wilcoxon p (Holm) | d de Cohen | Gana la primera |
|---|---|---|---|---|---|---|
| Regla fija − sistema | ¿El Maestro hace algo distinto de α = 0,5 siempre? | −2,66 | [−12,16; 2,91] | 1,000 | −0,11 | 1 de 30 |
| Sistema − regla uniforme | Aporte del calendario del Maestro | +12,00 | [−10,59; 34,54] | 1,000 | 0,18 | 16 de 30 |
| Regla uniforme − TWAP | Aporte de los Ejecutores | **−15,37** | **[−20,35; −10,32]** | **7,0·10⁻⁶** | **−1,08** | **26 de 30** |

La descomposición es exacta, corrida por corrida: la diferencia sistema − TWAP (−3,37 bps) es la suma del aporte del calendario (+12,00) y del de los Ejecutores (−15,37). La regla fija α = 0,5 da exactamente el mismo resultado que el sistema en 25 de 30 corridas, lo que confirma que el Maestro equivale a esa regla. Con el mismo calendario que TWAP, los Ejecutores cuestan 15,37 bps menos, un efecto grande (d = −1,08) y significativo después de Holm (p = 7,0·10⁻⁶). El calendario del Maestro, en cambio, no aporta en promedio (+12,00 bps, p = 1,0) y depende de la dirección del día: ahorra 24,5 bps en los días que suben (n = 20) y cuesta 85,0 bps más en los que bajan (n = 10), una división descriptiva, sin prueba. Con el costo ajustado por lo no ejecutado, la conclusión no cambia (Ejecutores: −15,25 bps, p de Holm = 7,0·10⁻⁶).

La explicación más probable del ahorro de los Ejecutores es el tipo de orden. El TWAP de referencia compra con órdenes a mercado y cruza el spread en cada compra, mientras que los Ejecutores usan órdenes límite en el 94 % de los casos. En la reevaluación con 300 semillas en una ventana, el Ejecutor elegido costó 5,68 bps contra 4,65 de un TWAP **con órdenes límite**, es decir, 1,03 bps más caro (IC 95 % [0,11; 1,88]). Por lo tanto, frente a un TWAP con órdenes límite la ventaja sería probablemente cercana a cero. Esta lectura no se probó en la evaluación final, porque el TWAP con órdenes límite no se corrió en ella.

Figura: `data/colab_resultados/control_reglas/media/analisis/control_reglas.png` (Aporte de cada nivel en el control con reglas fijas, profundidad ×1, n = 30).

### 8.4.3 Maestro corregido (Maestro v2)

Para comprobar si las causas de la sección 8.4.1 explicaban el resultado, se entrenó una versión corregida del Maestro: su estado mide la volatilidad, la profundidad y el desbalance en el mercado simulado, se entrena con la corrección del cierre y cuenta sus decisiones por orden.

**Tabla.** Resultado del Maestro v2 frente al Maestro del sistema final y a TWAP (profundidad ×1, n = 30 pares).

| Medida | Valor |
|---|---|
| Acción más frecuente | α = 0,40 en el 74 % de las decisiones (ya no 0,50) |
| Costo medio | 46,3 bps (Maestro del sistema final: 47,1) |
| v2 − Maestro del sistema final | −0,85 bps [−9,97; 8,25], Wilcoxon p = 0,855 |
| v2 − TWAP | −4,21 bps [−23,71; 16,11], Wilcoxon p = 0,556 |

La corrección cambió la política, pero no el costo. Incluso con información de mercado, el Maestro sigue eligiendo casi una regla fija: en este entorno, el calendario no tiene de dónde sacar ventaja, porque las ventanas son independientes (limitación L1).

### 8.4.4 Síntesis

La reducción de costo viene de la capa de Ejecutores, que es significativa y tiene un efecto grande frente a TWAP a mercado. El Maestro, en su forma actual, agrega una variabilidad que depende del día y compensa lo que ahorran los Ejecutores. Por eso el sistema completo no supera a TWAP de forma significativa, aunque sí es más estable.

## 8.5 Sensibilidad

### 8.5.1 Hiperparámetros del entrenamiento

En el barrido de hiperparámetros del Maestro y de los Ejecutores, unas 30 configuraciones quedaron entre −2,4 y −2,6 bps, y la mejor mejoró unos 0,2 bps sobre la configuración por defecto, dentro del error. Se mantuvieron λ = 0,02 y la configuración por defecto: el resultado es poco sensible a los hiperparámetros probados.

### 8.5.2 Tramo de inicio de la orden (exploratorio)

La diferencia sistema − TWAP sí depende del tramo en que parte la orden (Kruskal-Wallis, H = 8,98, p = 0,011; Capítulo 7, sección 7.7): el sistema es más barato de forma significativa solo en las órdenes que parten en el cierre (−34,78 bps, Wilcoxon con Holm, p = 0,009). Este resultado debe leerse con cuidado por tres razones. Primero, el tramo y el activo están confundidos: las tres órdenes de cierre son de FALABELLA. Segundo, el tramo está confundido con la dirección del día: en las órdenes de cierre el precio subió en el 81 % de los días (TWAP costó en promedio 68,4 bps), contra el 56 % en la apertura (14,3 bps), y comprar rápido en un tramo corto que sube favorece al calendario del Maestro (sección 8.3.1). Tercero, el sistema tiene la corrección del cierre y las referencias no.

Figura: `data/analysis/cap7/diferencia_por_tramo.png` (Diferencia sistema − TWAP por tramo de inicio de la orden, 90 corridas, con Kruskal-Wallis y Wilcoxon con Holm).

### 8.5.3 Tamaño de la orden

Las tres estrategias cuestan más con órdenes más grandes, como predice el impacto en raíz cuadrada, pero TWAP sube más rápido que el sistema: entre el tamaño 0,5 y el 1,5, TWAP sube 23,2 bps y el sistema 13,1 bps (Capítulo 7, sección 7.5). Por eso la diferencia sistema − TWAP pasa de +2,2 a −3,4 y a −7,9 bps, aunque ningún punto es significativo por sí solo (p entre 0,37 y 0,95).

Las pruebas de tendencia distinguen dos cosas. Dentro de un mismo día, la ventaja del sistema tiende a ser mayor con órdenes más grandes, y esa tendencia **en el orden** es significativa (Page, L = 379, n = 30, p = 0,007; Friedman, Q = 6,47, p = 0,039). En cambio, **la magnitud** del cambio no lo es: de 0,5 a 1,5 la ventaja mejora 10,1 bps en promedio, con un intervalo que incluye el cero (Wilcoxon, p = 0,164), y solo 12 de los 30 días mejoran en los dos pasos.

**Tabla.** Pruebas de tendencia de la ventaja del sistema con el tamaño de la orden (30 días como bloques).

| Prueba | Qué mide | n | Estadístico | p |
|---|---|---|---|---|
| Friedman | Si la diferencia sistema − TWAP cambia entre los 3 tamaños, comparando dentro de cada día | 30 días | Q = 6,47 | 0,039 |
| Page | Si la diferencia baja de forma ordenada al crecer el tamaño | 30 días | L = 379 | 0,007 |
| Wilcoxon | Cuánto cambia la diferencia de 0,5 a 1,5 | 30 días | −10,08 bps [−23,66; 3,11] | 0,164 |
| Friedman sin días bajo el 95 % de cumplimiento | Robustez al cumplimiento | 25 días | Q = 6,08 | 0,048 |

La interpretación debe ser prudente. Que el sistema se degrade menos que TWAP cuando la orden crece es coherente con que sus Ejecutores usen órdenes límite y no crucen el spread. Pero el análisis es exploratorio (hace muchas pruebas sin corrección por multiplicidad), con el tamaño 1,5 parte de la ventaja viene de días en que el sistema no completó la orden (sin ellos, la diferencia baja a −5,06 bps, n = 25, p = 0,51), y el Maestro se entrenó con un solo tamaño, de modo que 0,5 y 1,5 son extrapolaciones. Además, el tamaño se midió solo en la profundidad ×1, así que no se sabe si interactúa con la profundidad.

Figura: `data/analysis/cap7/costo_vs_tamano.png` (Costo medio de las tres estrategias en los tres tamaños, con la diferencia sistema − TWAP y su valor p en cada punto).

### 8.5.4 Supuestos que no se variaron

El impacto acumulado entre ventanas (Y = 0,5, τ = 120 min) es un supuesto tomado de la literatura y no está calibrado con datos del IPSA. La volatilidad y el spread no se variaron por separado: la profundidad del market maker los cambia solo de forma indirecta. Ambos se declaran como limitaciones (sección 8.6).

## 8.6 Limitaciones y análisis crítico

**Tabla.** Limitaciones de la evaluación y su efecto sobre el resultado.

| # | Limitación | Efecto sobre el resultado | Dónde se documenta |
|---|---|---|---|
| L1 | Cada ventana de 30 min es un mercado independiente; solo se unen por el impacto acumulado | El Maestro no tiene una tendencia que anticipar | Desviación 7 |
| L2 | El Maestro del sistema final se entrenó sin la corrección del cierre y sin datos de mercado | Calendario casi fijo. El Maestro v2 lo corrige sin cambiar el costo | Desviaciones 11 y 13 |
| L3 | El Maestro se entrenó en Poisson y se evalúa en ABIDES | Posible pérdida al cambiar de simulador | Capítulo 4, sección 4.5 |
| L4 | La misma red de Ejecutor se usa en los tres tramos | Los Ejecutores de media jornada y cierre no están especializados | Desviación 8 |
| L5 | La tasa de llegada de órdenes vale 0 en ABIDES | El Ejecutor ve 26 de sus 27 variables | Desviación 14 |
| L6 | **La referencia TWAP/VWAP compra a mercado; los Ejecutores usan órdenes límite** | La ventaja de los Ejecutores puede deberse sobre todo a no cruzar el spread | Sección 8.4.2 |
| L7 | Los escenarios son profundidades del market maker, no liquidez validada | No se puede afirmar nada sobre días reales de distinta liquidez | Capítulo 6, sección 6.1.1; desviación 10 |
| L8 | El simulador no reproduce el spread real (es entre 25 y 33 veces menor) y no pasa el criterio literal de validación | El costo absoluto queda subestimado; las conclusiones son comparaciones entre estrategias | Capítulo 5, sección 5.6 |
| L9 | Tres acciones, 10 órdenes y un *snapshot* de calibración | Validez externa limitada | Capítulo 6, sección 6.1.2 |
| L10 | Simulación sin operación real | Sin latencia, comisiones ni reacción de participantes reales | Título I |
| L11 | 90 corridas (30 por escenario) | Potencia del 33 % al 76 % según el tamaño real del efecto; por escenario, baja | Anexo D |
| L12 | Impacto, volatilidad y spread no variados | No se sabe cómo cambia el resultado con otros supuestos | Sección 8.5.4 |

La arquitectura jerárquica de dos niveles con PPO se implementó completa y funciona: ejecuta las órdenes al 99,8 % en promedio, y el resto se ajusta con el costo penalizado. Pero la hipótesis de que coordinar un planificador y ejecutores reduce el costo frente a TWAP no se confirmó con significancia. El experimento sí muestra dónde está el valor y dónde no: la capa de ejecución aprende a comprar mejor que la regla ingenua, mientras que la capa de planificación no tiene, en este entorno, información ni dinámica de la cual aprender.

Esto también matiza la literatura citada en el marco teórico (Capítulo 2, sección 2.5), que reporta ventajas del aprendizaje por refuerzo sobre las estrategias tradicionales. En este trabajo, la ventaja aparece en la capa de ejecución y frente a una referencia que compra a mercado, pero no en la coordinación entre niveles. La lección de diseño es que un planificador solo puede aprender lo que el entorno contiene: si el día simulado no tiene continuidad entre ventanas, ninguna política de calendario puede anticipar el precio.

## 8.7 Implicaciones prácticas y costo de las alternativas

### 8.7.1 Lo que el resultado permite y no permite afirmar

El resultado permite afirmar que un sistema de dos niveles con PPO puede ejecutar meta-órdenes completas en un simulador calibrado del IPSA, con un costo medio similar al de TWAP y VWAP y una variabilidad significativamente menor, y que la capa de Ejecutores, por sí sola, reduce el costo frente a una ejecución ingenua a mercado. No permite afirmar que el sistema completo reduzca el costo de forma consistente, ni que funcione igual en el mercado real. Además, el calendario aprendido tiene un riesgo operativo: comprar temprano es una apuesta implícita a que el precio sube, y un operador debería conocerlo antes de usarlo.

### 8.7.2 Ventajas, desventajas y costos de las alternativas evaluadas

Los costos computacionales corresponden a lo medido en Colab durante el proyecto.

**Tabla.** Ventajas, desventajas y costos (computacional, económico y operacional) de las alternativas evaluadas.

| Alternativa | Ventajas | Desventajas | Costo computacional | Costo económico | Costo operacional |
|---|---|---|---|---|---|
| **TWAP / VWAP a mercado** (referencia) | Sin entrenamiento, transparente, fácil de auditar | Cruza el spread; más variable entre días | Nulo | Nulo | Muy bajo: es una regla fija |
| **Sistema completo** (Maestro + Ejecutores PPO) | Completa la orden; 23 % menos de variabilidad que TWAP (p = 4,8·10⁻⁹) | Sin reducción significativa del costo medio; calendario dependiente del día | Maestro ≈ 40 min de entrenamiento; las 90 corridas ≈ 18 h en Colab | Solo Colab y datos públicos; ABIDES es de código abierto | Alto: mantener dos niveles de redes, monitoreo y reentrenamiento |
| **Solo Ejecutores PPO con calendario uniforme** | −15,4 bps frente a TWAP a mercado (p de Holm = 7·10⁻⁶) con el mismo calendario; más simple que el sistema | Ventaja ligada a usar órdenes límite; ≈ +1 bps frente a TWAP con órdenes límite | El Ejecutor ya entrenado (≈ 57 min); evaluar 30 corridas ≈ 2 h | Igual que arriba | Medio: un solo nivel de red |
| **Maestro v2** (con información de mercado) | Corrige el diseño del estado; política menos extrema | Mismo costo que el Maestro original (p = 0,855) | Entrenamiento ≈ 40 min; evaluación ≈ 2 h | Igual que arriba | Alto, como el sistema completo |

Con la evidencia de este trabajo, la alternativa con mejor relación entre beneficio y costo es la **capa de Ejecutores con un calendario simple**. Agregar el Maestro aumenta la complejidad sin un beneficio medible en el costo medio. El trabajo futuro que se desprende de este análisis está en el Capítulo 9, sección 9.7.
