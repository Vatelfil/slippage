# Capítulo 9. Conclusiones y trabajo futuro

**Tarea:** 4.2.1 (Sprint 9). **Autor:** PS, con apoyo de Claude Code. **Versión:** borrador avanzado del 15 de noviembre de 2026.

**Numeración:** es el Capítulo 9 de la estructura del informe final del Título I. El capítulo de análisis (tarea 4.1.3, «Capítulo 7» en el Excel) es el Capítulo 8 de esa estructura: `docs/capitulo8_analisis_PS.md`.

**Estado:** completo. El hallazgo H6 (tamaño) incluye la prueba de tendencia de la 3.2.4 (MR), verificada por PS.

**Convención:** cada afirmación estadística indica la prueba, el n y el valor p. El detalle de cómo se calculó está en el capítulo de análisis, que se cita por sección.

---

## 9.1 Síntesis del trabajo

El proyecto diseñó, implementó y evaluó un sistema de coordinación de agentes con aprendizaje por refuerzo para ejecutar meta-órdenes de gran volumen en acciones del IPSA. El sistema tiene dos niveles:

- **Agente Maestro:** cada 30 minutos decide qué fracción de lo pendiente comprar (α entre 5 % y 50 %) y en qué ventana (1, 5, 10 o 15 minutos). Usa un estado S_M de 7 variables y 40 acciones discretas.
- **Agentes Ejecutores:** dentro de cada ventana deciden el tipo de orden, el volumen y el nivel de precio en el libro de órdenes. Usan un estado S_E de 27 variables y 240 acciones discretas.

**Entrenamiento:**
- Los dos niveles se entrenaron con PPO en PyTorch y se coordinan con un protocolo CTDE de asignación y reporte.
- El Ejecutor se inicializó imitando a TWAP con órdenes límite y luego se refinó con PPO.
- El Maestro se entrenó en un simulador de Poisson calibrado con datos del IPSA (2.000 jornadas), con los Ejecutores fijos.

**Evaluación:**
- Se hizo en ABIDES-Gym con la configuración RMSC04 calibrada para FALABELLA, COPEC y ECL, con impacto acumulado entre ventanas.
- Se usaron 90 corridas pareadas contra TWAP y VWAP: 3 profundidades del market maker × 10 meta-órdenes × 3 semillas no usadas en el desarrollo.
- El análisis estadístico se registró antes de ver los datos.

## 9.2 Cumplimiento de los objetivos

| Objetivo del Título I | Estado | Evidencia |
|---|---|---|
| **General:** diseñar y desarrollar un sistema de coordinación de agentes con RL para mitigar el slippage en el IPSA | **Cumplido en diseño y desarrollo.** La mitigación se evaluó: el costo medio no bajó de forma significativa, pero sí la variabilidad, y la capa de Ejecutores sí reduce el costo | Sistema funcionando en ABIDES; capítulo 8 |
| **1.** Construir un entorno de simulación del LOB de la Bolsa de Santiago | **Cumplido** | Poisson calibrado (2.1.3); RMSC04 calibrado (2.2.4) y validado (2.2.5) |
| **2.** Diseñar la arquitectura jerárquica Maestro + Ejecutores con PPO | **Cumplido**, con una red de Ejecutor usada en los tres tramos (desviación 8) | Tareas 2.1.1, 2.1.2, 2.3.1 y 2.3.2 |
| **3.** Definir una recompensa que minimice el implementation shortfall | **Cumplido**: R_M y R_E implementadas y calibradas (λ = 0,02; β = 0,0062) | Tareas 2.2.2, 2.2.3 y 3.1.1 |
| **4.** Evaluar el sistema contra TWAP y VWAP con métricas de costo | **Cumplido**: 30 corridas (3.1.3) y 90 corridas (3.2.3), con pruebas no paramétricas pareadas | Capítulo 8, sección 8.3 |

## 9.3 Respuesta a la pregunta del proyecto

El Título I plantea verificar si el sistema reduce el costo de ejecución frente a las estrategias tradicionales, y en qué medida, sin fijar un umbral.

**Respuesta:**
- En las 90 corridas pareadas, el sistema costó en promedio **3,34 bps menos que TWAP** (IC 95 % [−15,69; 9,67]; Wilcoxon de rangos con signo, n = 90, p = 0,386).
- Frente a VWAP costó **3,14 bps menos** (p = 0,393).
- **La reducción no es estadísticamente significativa.** Con los datos disponibles no se puede afirmar que el sistema reduzca el costo medio, ni que lo aumente.
- El intervalo descarta, con un 95 % de confianza, ventajas medias mayores que 15,7 bps y desventajas mayores que 9,7 bps.

**Dos resultados complementan esta respuesta:**
1. **El sistema es más estable.** La desviación estándar de su costo entre días es un 23 % menor que la de TWAP (razón 0,77, IC 95 % [0,69; 0,84]; Pitman-Morgan, n = 90, p = 4,8·10⁻⁹; análisis exploratorio).
2. **La capa de Ejecutores reduce el costo.** Con el mismo calendario que TWAP, los Ejecutores PPO cuestan 15,37 bps menos (IC 95 % [−20,35; −10,32]; Wilcoxon con Holm, n = 30, p = 7,0·10⁻⁶; d de Cohen = −1,08). El calendario aprendido por el Maestro no aporta (+12,00 bps, p = 1,0).

**En síntesis:** la arquitectura funciona y uno de sus niveles aporta valor medible, pero la coordinación entre los dos niveles no produjo una ventaja significativa sobre TWAP en el costo medio.

## 9.4 Hallazgos principales

1. **H1. El sistema es viable.** Ejecuta las meta-órdenes con un cumplimiento medio del 99,8 % en un simulador calibrado del IPSA, con un costo medio comparable al de TWAP y VWAP (58,6 bps contra 62,0 y 61,8).

2. **H2. La ventaja depende del día, no de la profundidad del mercado.**
   - La diferencia sistema − TWAP se correlaciona con el movimiento del precio: Spearman ρ = −0,78, n = 90, p = 1,5·10⁻¹⁹.
   - El sistema ahorra 30,5 bps en promedio los días que suben y pierde 60,0 bps los que bajan.
   - La ventaja no cambia entre profundidades: Kruskal-Wallis p = 0,930.

3. **H3. El Maestro aprendió un calendario casi fijo.**
   - Elige α = 0,5 con ventana de 15 minutos en el 96–98 % de las decisiones (profundidades ×4 y ×1).
   - La causa es el diseño del entrenamiento: sin corrección del cierre, sin información de mercado en S_M y con ventanas independientes.
   - La versión corregida (Maestro v2) cambió la política (α = 0,4 en el 74 % de los casos) sin cambiar el costo: −0,85 bps frente al original, Wilcoxon n = 30, p = 0,855.

4. **H4. Los Ejecutores PPO superan a TWAP a mercado.** El efecto es grande (−15,4 bps, d = −1,08). Su origen más probable es el uso de órdenes límite: frente a un TWAP con órdenes límite, el Ejecutor quedó ≈ 1 bps más caro en la reevaluación de 300 semillas (IC 95 % [0,11; 1,88]).

5. **H5. El sistema es más estable que TWAP y VWAP** (Pitman-Morgan p < 10⁻⁸). Evita los días muy caros y aprovecha menos los muy baratos. Es un resultado exploratorio, que también se observó en la primera evaluación (p = 8·10⁻⁵, n = 30).

6. **H6. Con órdenes más grandes, la ventaja del sistema tiende a crecer; la tendencia es significativa en el orden, no en la magnitud.**
   - En profundidad ×1 (n = 30 días por tamaño), sistema − TWAP fue +2,2 bps con el factor 0,5, −3,4 con 1 y −7,9 con 1,5. Ningún punto es significativo por sí solo (Wilcoxon p = 0,95; 0,63 y 0,37).
   - Dentro de cada día, la ventaja sigue el orden del tamaño: Friedman Q = 6,47, p = 0,039 (3.2.4, MR) y Page L = 379, p = 0,007 (PS).
   - La magnitud del cambio de 0,5 a 1,5 (−10,1 bps) no es significativa (Wilcoxon p = 0,164).
   - Es exploratorio. Con 1,5, parte del efecto viene de días que no completaron (sin ellos: −5,1 bps, n = 25; Friedman p = 0,048) y el Maestro opera fuera del tamaño de entrenamiento.

7. **H7. Lección metodológica.**
   - La primera evaluación (semillas 1–3) sugería −22 bps (p = 0,096). Con días nuevos, la ventaja fue de −3 bps.
   - Las dos muestras no difieren estadísticamente (Mann-Whitney p = 0,395): era variabilidad entre días.
   - Registrar el análisis antes de ver los datos y evaluar en días nuevos evitó informar como resultado una ventaja que no se sostuvo.

## 9.5 Implicaciones

**Para la investigación:**
- La arquitectura jerárquica con PPO es implementable para el mercado chileno con herramientas abiertas (ABIDES, PyTorch y yfinance).
- El cuello de botella no fue el algoritmo de aprendizaje sino el entorno. Un planificador solo puede aprender lo que el entorno contiene: si las ventanas son mercados independientes, no hay tendencia intradía que anticipar.

**Para un uso práctico:**
- El sistema completo no está listo para operar. Su calendario equivale a una apuesta implícita a que el precio sube.
- La capa de Ejecutores, combinada con un calendario simple, es la alternativa con mejor relación entre beneficio y costo operacional (capítulo 8, sección 8.8.2).
- Su ventaja frente a TWAP a mercado debe compararse primero con un TWAP con órdenes límite.

## 9.6 Limitaciones

El detalle está en el capítulo 8, tabla L1–L11. Las que más condicionan las conclusiones son:

1. Las ventanas de 30 minutos son mercados independientes, unidos solo por un impacto acumulado supuesto (Y = 0,5, τ = 120 min) y no calibrado.
2. La referencia TWAP/VWAP compra a mercado, mientras los Ejecutores usan órdenes límite.
3. Los escenarios corresponden a la profundidad del market maker y no a una liquidez validada con datos reales (C-6c).
4. El Maestro se entrena en Poisson y se evalúa en ABIDES.
5. Se usaron tres acciones, 10 meta-órdenes y 90 días simulados, sin operación real.

## 9.7 Trabajo futuro, ordenado por valor esperado

1. **Comparar contra TWAP con órdenes límite** en las mismas 90 corridas. Es barato (≈ 6 bloques de Colab de ≈ 3 h) y separa el aporte de la política del de usar órdenes límite.
2. **Simular jornadas continuas** en ABIDES, para que el calendario del Maestro tenga una dinámica de la cual aprender, y entrenar al Maestro en ese mismo entorno.
3. **Escenarios de liquidez calibrados con días reales** del IPSA de baja y alta liquidez.
4. **Calibrar el impacto acumulado** (Y y τ) y variar la volatilidad y el spread por separado.
5. **Especializar los Ejecutores** de media jornada y cierre, y entregar `tasa_ordenes` en ABIDES.
6. **Ampliar el universo** a más acciones y días, para ganar potencia estadística: con 90 corridas, la probabilidad de detectar una ventaja de 12,5 bps era de ≈ 33 %.
7. **Entrenar los dos niveles en conjunto**, en vez de fijar los Ejecutores mientras aprende el Maestro.

## 9.8 Declaración de la contribución

Este trabajo entrega:

1. **Un sistema completo y reproducible** de ejecución de meta-órdenes con agentes jerárquicos PPO para el IPSA:
   - simuladores calibrados (Poisson y ABIDES-RMSC04);
   - agentes Maestro y Ejecutores;
   - protocolo de coordinación CTDE;
   - evaluadores pareados;
   - análisis estadístico registrado antes de los datos.
   - Todo está en el repositorio, con pruebas automáticas.
2. **Evidencia de que la capa de ejecución aprendida reduce el costo** frente a una ejecución ingenua (−15,4 bps, p = 7·10⁻⁶) **y de que el sistema reduce la variabilidad del costo** (−23 %, p < 10⁻⁸).
3. **Un diagnóstico de por qué la coordinación no superó a TWAP en el costo medio.** Se acompaña de una lista concreta de qué debe contener el entorno de simulación para que un planificador pueda aportar.

Ese diagnóstico, respaldado por un control experimental y una versión corregida del Maestro, es en sí una contribución: muestra dónde está y dónde no está el valor de coordinar agentes en la ejecución de órdenes.
