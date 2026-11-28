# Capítulo 6: Entrenamiento y experimentación (4.1.2)

**Autor:** Mauricio Reynoso (MR), Sprint 8 (tarea 4.1.2). Revisión del 28 de noviembre de 2026 (PS, con apoyo de Claude Code, a partir de las observaciones del equipo): títulos en formato oración, sin nombres de archivos ni de código, una sola explicación del efecto de la profundidad y nueva sección 6.5 con la metodología de evaluación estadística (antes en el Capítulo 8). Pendiente de revisión por MR.
**Figuras:** curvas de aprendizaje del Ejecutor y del Maestro.

---

## 6.1 Montaje experimental y calibración del entorno

### 6.1.1 Simulador y escenarios de profundidad del market maker

La evaluación se ejecuta sobre el simulador de microestructura **ABIDES** (configuración RMSC04), calibrado por el método de momentos simulados con datos intradía de **FALABELLA, COPEC y ECL** (*snapshot* del 23 de agosto de 2026; Capítulo 5, sección 5.5).

Para estudiar la sensibilidad del sistema a distintas condiciones de mercado, se escaló la profundidad de cotización del *market maker* (`mm_pov`, desviación 10):
- **Profundidad ×4:** el market maker pone en cada nivel cuatro veces más volumen que en la calibración base.
- **Profundidad ×1:** calibración base.
- **Profundidad ×0,25:** el market maker pone un cuarto del volumen base.

En una prueba de confirmación previa a la evaluación, con 60 semillas nuevas (FALABELLA, apertura, compra a mercado de 5.000 acciones), comprar a mercado costó 25,05 bps con ×4, 18,36 con ×1 y 10,81 con ×0,25: **con más profundidad del market maker, la compra a mercado resultó más cara**, al contrario de lo esperado (la explicación probable está en el Capítulo 5, sección 5.5). El contraste ×1 − ×0,25 excluyó el 0 (+7,56 bps, IC 95 % [+3,07; +14,77]), pero ×4 − ×1 no lo excluyó (+6,69 bps, IC 95 % [−2,59; +13,77]). Como el criterio fijado antes de la prueba exigía que ambos lo excluyeran, los escenarios no se interpretan como liquidez baja, media y alta, sino estrictamente como **profundidad del market maker ×4, ×1 y ×0,25**.

### 6.1.2 Meta-órdenes, diseño en estrella y protocolo pareado

* **Meta-órdenes:** 10 órdenes de compra (MO-01 a MO-10) en **FALABELLA, COPEC y ECL**, que parten en los tres tramos horarios (**apertura**, **media jornada** y **cierre**). El tamaño base equivale al **10 % del volumen diario** (5 % en las órdenes que parten en el cierre, para que sean ejecutables).
* **Semillas nuevas:** se evaluaron las semillas 4, 5 y 6, independientes de las semillas 1, 2 y 3 de la primera evaluación y de las semillas 5001–5300 usadas para elegir el Ejecutor. El bloque principal suma **3 profundidades × 10 órdenes × 3 semillas = 90 corridas pareadas por estrategia** (270 ejecuciones en total).
* **Eje de tamaño en estrella (desviación 12):** para estudiar el tamaño sin multiplicar el diseño a 810 corridas, se fijó la profundidad ×1 y se agregaron dos tamaños: **0,5** (5 % del volumen diario; 2,5 % en el cierre) y **1,5** (15 %; 7,5 % en el cierre). Son 60 corridas pareadas más por estrategia (180 ejecuciones), para un total de **450 ejecuciones**.
* **Terminología:** en este informe, *corrida* es una meta-orden ejecutada en un día simulado por una estrategia; *corridas pareadas* son las tres estrategias ejecutando la misma orden el mismo día.
* **Condiciones de comparabilidad:** el sistema PPO (en modo de muestreo y con barrido al cierre) y las referencias **TWAP** y **VWAP** (que compran con órdenes a mercado) comparten las semillas de mercado por ventana, el *snapshot* y el impacto acumulado entre ventanas ($Y = 0{,}5$, $\tau = 120$ min).

---

## 6.2 Experimentación y convergencia de los Agentes Ejecutores

### 6.2.1 Alternativas probadas y selección con 300 semillas

En ABIDES (apertura, FALABELLA, sub-orden de 1.000 acciones, ventana de 15 min) se compararon cuatro familias de entrenamiento PPO sobre 300 semillas independientes (5001–5300, evaluación estocástica):

| Alternativa de entrenamiento del Ejecutor | Episodios | Costo medio en 300 semillas (bps) | Cumplimiento medio | Diferencia frente a TWAP límite [IC 95 %] | Costo computacional (Colab CPU) |
|---|---|---|---|---|---|
| **Imitación + PPO (semilla 1000, elegido)** | 100 de imitación + 1.000 de PPO | **5,68** | **1,000** | +1,03 [+0,11; +1,88] | ≈ 57 min (3.437,5 s medidos) |
| Imitación + PPO (semilla 2000) | 100 de imitación + 1.000 de PPO | 5,98 | 1,000 | +1,32 [+0,56; +2,09] | ≈ 57 min |
| Solo imitación (semilla 2000, sin PPO; descartada) | 100 de imitación | 5,13 | 0,984 | +0,47 [−0,23; +1,17] | ≈ 5 min |
| Mejor red PPO pura anterior (semilla 3000) | 1.000 de PPO | 6,50 | 1,000 | +1,85 [−0,21; +3,80] | ≈ 55 min |
| Recompensa corregida sin imitación (6 redes) | 1.000 de PPO | 7,09 a 9,48 | 1,000 | +2,4 a +4,8 | ≈ 55 min cada una |
| *Referencia:* TWAP con órdenes límite | — | 4,65 | 0,989 | — | < 1 min |

* **Justificación de la selección:** la inicialización por clonación de comportamiento sobre un TWAP con órdenes límite (100 episodios, 3.000 pares estado-acción, exactitud del 92,97 %) seguida de ajuste fino con PPO (tasa de aprendizaje $10^{-4}$, recorte 0,2, $\gamma_E = 1{,}0$, $\beta = 0{,}0061796$) obtuvo el menor costo entre las redes PPO válidas (5,68 bps; −1,30 bps respecto de su control sin entrenar, p = 0,095) con 100 % de cumplimiento. La variante de solo imitación se descartó por no incorporar aprendizaje por refuerzo y por su menor cumplimiento (98,4 %).

### 6.2.2 Convergencia del Ejecutor elegido

En la Figura `data/analysis/cap6_MR/curvas_ejecutor.png` se observa la trayectoria de aprendizaje durante los 1.000 episodios de ajuste PPO en ABIDES:
- **Estabilidad de las actualizaciones:** la divergencia KL aproximada se mantuvo acotada (máximo 0,0095), lo que indica pasos de gradiente suaves, sin colapso de la política.
- **Entropía y cumplimiento:** la entropía bajó de 1,242 a 0,667, mientras el cumplimiento pasó de 99,51 % en los primeros 50 episodios a **100,0 %** en los últimos 50.
- **Composición de las acciones aprendidas:** en los últimos 50 episodios, el Ejecutor usó **93,7 % de órdenes límite de compra**, **2,1 % de órdenes a mercado** y **4,2 % de espera**. Esto explica su capacidad para capturar el spread frente a referencias que compran a mercado.

---

## 6.3 Entrenamiento y convergencia del Agente Maestro

Con los pesos del Ejecutor fijos y replicados en los tres tramos, se entrenó el Agente Maestro en el simulador de **Poisson** durante **2.000 jornadas completas** (88.300 acciones de FALABELLA, $\lambda = 0{,}02$, $\gamma_M = 0{,}99$, tasa de aprendizaje $3 \times 10^{-4}$).

### 6.3.1 Convergencia del Maestro del sistema final frente al Maestro v2

La Figura `data/analysis/cap6_MR/curvas_maestro.png` compara las curvas de entrenamiento del Maestro del sistema final y de la variante exploratoria Maestro v2, que mide las variables de mercado en el simulador (desviación 13). Las recompensas están en bps del valor de la orden (Capítulo 4, sección 4.3.1):

| Métrica de entrenamiento y validación (30 semillas, 90001–90030) | Maestro del sistema final | Maestro v2 |
|---|---|---|
| **Pérdida del crítico (episodio 10 → 2.000)** | 2.634,23 → 1,31 | 1.863,23 → 3,85 |
| **Entropía de la política (episodio 10 → 2.000)** | 3,686 → **0,205** | 3,686 → **0,849** |
| **KL máxima por actualización** | 0,0194 | 0,0129 |
| **Recompensa $R_M$ (sin entrenar → entrenado)** | −72,09 → −30,67 bps (+41,42; IC [+29,83; +54,61]) | −55,10 → −27,50 bps (+27,60; IC [+17,1; +39,8]) |
| **Cumplimiento en validación (sin entrenar → entrenado)** | 73,25 % → 97,57 % | 83,00 % → 99,60 % |
| **Política dominante** | α = 0,50 con ventana de 15 min (96–98 %) | α = 0,40 (74 %) y α = 0,20 (20 %) |

* **Diagnóstico de la caída de entropía del Maestro del sistema final:** la entropía de 0,205 indica que el Maestro convergió a una política casi determinista (α = 0,50, ventana de 15 min). Una prueba complementaria con reglas fijas en el simulador de Poisson, separando días de actividad baja, media y alta (1.500 corridas), mostró que α = 0,50 es la regla fija más barata que completa la orden en los tres tipos de día, dentro de la restricción de no superar el 50 % por ventana. Al incorporar variables de mercado y la regla de cierre durante el entrenamiento (Maestro v2), la entropía se estabilizó en un nivel mayor (0,849) y la política se diversificó, sin cambiar de forma significativa el costo final en ABIDES (−0,85 bps frente al Maestro del sistema final, Wilcoxon p = 0,855).

---

## 6.4 Presupuesto y costo computacional

Toda la experimentación pesada se ejecutó en Google Colab con CPU (Python 3.9), sin GPU, porque ABIDES es un simulador secuencial de eventos discretos:

| Etapa experimental | Corridas o episodios | Duración aproximada en Colab | Justificación |
|---|---|---|---|
| Selección y entrenamiento de los Ejecutores | Más de 12 entrenamientos de 1.000 episodios y reevaluación con 300 semillas | ≈ 15 h acumuladas | Comparar 4 formulaciones de recompensa y de imitación |
| Entrenamiento del Maestro (sistema final y v2) | 2.000 jornadas en Poisson cada uno | ≈ 40 min por modelo | Entrenar en ABIDES requeriría más de 100 h por modelo |
| Evaluación principal (90 corridas en ×4, ×1 y ×0,25) | 270 simulaciones en ABIDES (6 cuadernos) | ≈ 18 h en total (3 h por par en paralelo) | Jornadas completas pareadas |
| Eje de tamaño (0,5 y 1,5 en ×1) | 180 simulaciones en ABIDES (4 cuadernos) | ≈ 12 h en total (3 h por par en paralelo) | Completa el diseño en estrella sin llegar a 810 corridas |
| Control con reglas fijas y Maestro v2 | 90 simulaciones en ABIDES | ≈ 6 h | Separar el aporte del Maestro y de los Ejecutores |

---

## 6.5 Metodología de la evaluación estadística

### 6.5.1 Plan registrado antes de ver los datos

El plan de análisis se escribió el 31 de octubre de 2026, antes de correr las 90 corridas (Anexo D). Fija la medida de costo, la prueba principal, las pruebas secundarias y las variantes de robustez. Todo lo que se agregó después de ver los datos se marca como **exploratorio** en los capítulos 7 y 8.

### 6.5.2 Diseño

- **Unidad de análisis:** una corrida, es decir, una meta-orden ejecutada en un día simulado.
- **Factores:** 10 meta-órdenes, 3 semillas (4, 5 y 6) y 3 profundidades del market maker (×4, ×1 y ×0,25): 90 corridas por estrategia.
- **Pareo:** el sistema, TWAP y VWAP se ejecutan en el mismo día simulado (misma profundidad, orden y semilla). Por eso se comparan las diferencias por corrida y no las medias de grupos independientes.
- **Días nuevos:** las semillas 4 a 6 no se usaron durante el desarrollo. Las semillas 1 a 3 de la primera evaluación sirvieron para detectar y corregir el problema de las órdenes del cierre (desviación 11).

### 6.5.3 Pruebas

| Uso | Prueba | Por qué |
|---|---|---|
| **Principal:** ¿el sistema cuesta menos que TWAP? | Wilcoxon de rangos con signo, pareado, bilateral, α = 0,05 | Los costos tienen colas largas (en la primera evaluación, una sola orden movía la media de −12,5 a −22 bps). Wilcoxon usa rangos, así que una corrida extrema no domina |
| Complemento | t pareado | Solo si Shapiro-Wilk no rechaza la normalidad de las diferencias |
| Tamaño del efecto | Diferencia media con IC 95 % por bootstrap pareado (3.000 remuestreos, percentil); d de Cohen pareado; correlación biserial de rangos r | El Título I no fija un umbral de reducción, así que la conclusión se da con el intervalo |
| Por escenario | Wilcoxon en cada profundidad, con corrección de Holm (3 pruebas) | Controla el error por comparaciones múltiples |
| ¿Depende de la profundidad? | Kruskal-Wallis sobre las diferencias, con épsilon² | Compara tres grupos sin suponer normalidad |
| Control de bloques | Friedman (bloques orden × semilla) | Los mismos días se repiten en las tres profundidades |
| Variabilidad entre días (exploratorio) | Pitman-Morgan para varianzas pareadas | Compara la dispersión de dos estrategias medidas en los mismos días |
| Tendencia con el tamaño (análisis de sensibilidad) | Friedman y Page (tendencia ordenada) | Los mismos 30 días se repiten en los tres tamaños |

El procedimiento de cálculo de cada prueba (Wilcoxon, Holm, Spearman, Pitman-Morgan, Kruskal-Wallis, Friedman y Page) se detalla en el Anexo E.
