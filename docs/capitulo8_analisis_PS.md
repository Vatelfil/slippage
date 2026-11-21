# Capítulo 8. Discusión y análisis crítico de los resultados

**Tarea:** 4.1.3 (Sprint 8, «Capítulo 7 Análisis» en `plan-desarrollo-titulo-2.xlsx`). **Autor:** PS, con apoyo de Claude Code. **Versión:** 15 de noviembre de 2026.

**Numeración:** sigue la estructura del informe final del Título I (9 capítulos), donde el análisis es el Capítulo 8 y las Conclusiones el 9. El Excel lo llama «Capítulo 7» porque numera solo los capítulos asignados en el Título II.

**Estado:**
- Completo con las 90 corridas, el control y el Maestro v2.
- **Estado:** completo. La sección 8.6.3 (tamaño) incluye la prueba de tendencia de la 3.2.4 (MR) y la 8.6.2 (tramo) quedó confirmada por ella.

**Convención:**
- Costo = implementation shortfall en puntos base (bps) contra el precio de llegada.
- Diferencia = costo del sistema − costo de la referencia, en la misma corrida. **Negativa = el sistema cuesta menos.**
- Cada resultado de estadística inferencial indica la prueba, el n, el valor p y cómo se calculó.

---

## 8.1 Objetivo del capítulo

El objetivo específico 4 del Título I pide evaluar el sistema contra TWAP y VWAP con métricas de reducción de costo. La etapa 6 pide determinar en qué medida el sistema reduce el slippage y qué limitaciones conserva. Este capítulo interpreta los resultados del capítulo de Resultados (BF, 4.1.2) con ese fin. Responde cuatro preguntas:

1. ¿El sistema cuesta menos que TWAP y VWAP, y con qué certeza estadística? (8.3)
2. ¿De qué depende la diferencia: del día, de la profundidad del mercado, del tramo o del tamaño de la orden? (8.4 y 8.6)
3. ¿Qué aporta cada nivel de la arquitectura, el Maestro y los Ejecutores? (8.5)
4. ¿Qué limitaciones tiene el resultado, qué implica en la práctica y cuánto cuesta cada alternativa? (8.7 y 8.8)

## 8.2 Método estadístico

### 8.2.1 Plan registrado antes de ver los datos

El plan de análisis (`docs/plan_analisis_3_2_3_PS.md`) se escribió el 31 de octubre, antes de correr las 90 corridas. Fija la medida, la prueba principal, las pruebas secundarias y la robustez. Lo que se agregó después de ver datos se marca como **exploratorio** en este capítulo.

### 8.2.2 Diseño

- **Unidad de análisis:** una corrida, es decir, una meta-orden ejecutada en un día simulado.
- **Factores:**
  - 10 meta-órdenes (FALABELLA, COPEC y ECL, que parten en apertura, media jornada o cierre);
  - 3 semillas (4, 5 y 6);
  - 3 profundidades del market maker (`mm_pov` ×4, ×1 y ×0,25).
  - En total, 90 corridas por estrategia.
- **Pareo:** el sistema, TWAP y VWAP se ejecutan en el mismo día simulado (misma profundidad, orden y semilla). Por eso se comparan las diferencias por corrida y no las medias de grupos independientes.
- **Días nuevos:** las semillas 4 a 6 no se usaron en el desarrollo. Las semillas 1 a 3 de la primera evaluación (3.1.3) sirvieron para detectar y corregir el problema del cierre (desviación 11).
- **Nombre de los escenarios:** se planificaron como liquidez baja, media y alta. La confirmación C-6c (BF) no validó esa interpretación, así que se informan como profundidad del market maker (desviación 10).

### 8.2.3 Pruebas

| Uso | Prueba | Por qué |
|---|---|---|
| **Principal:** ¿el sistema cuesta menos que TWAP? | Wilcoxon de rangos con signo, pareado, bilateral, α = 0,05 | Los costos tienen colas largas (en la 3.1.3, una sola orden movía la media de −12,5 a −22 bps). Wilcoxon usa rangos, así que una corrida extrema no domina |
| Complemento | t pareado | Solo si Shapiro-Wilk no rechaza la normalidad de las diferencias |
| Tamaño del efecto | Diferencia media con IC 95 % por bootstrap pareado (3.000 remuestreos, percentil); d de Cohen pareado; correlación biserial de rangos r | El Título I no fija un umbral de reducción, así que la conclusión se da con el intervalo |
| Por escenario | Wilcoxon en cada profundidad, con corrección de Holm (3 pruebas) | Controla el error por comparaciones múltiples |
| ¿Depende de la profundidad? | Kruskal-Wallis sobre las diferencias, con épsilon² | Compara tres grupos sin suponer normalidad |
| Control de bloques | Friedman (bloques orden × semilla) | Los mismos días se repiten en las tres profundidades |
| Entre pares de escenarios | Mann-Whitney U con Holm | Solo se interpreta si Kruskal-Wallis es significativo |

**Cómo se calcula el Wilcoxon:**
1. Se ordenan las n diferencias por su valor absoluto.
2. Se suman los rangos de las negativas y los de las positivas.
3. El valor p es la probabilidad de obtener un desequilibrio igual o mayor entre esas sumas si el sistema y TWAP costaran lo mismo.

**Cómo se calcula Holm:**
1. Se ordenan los p de menor a mayor.
2. El menor se multiplica por 3, el siguiente por 2 y el último por 1.
3. Se mantiene el orden: un p corregido nunca queda menor que el anterior.

**Herramienta:** `scripts/comparacion_estadistica_3_2_3.py`. Los resultados completos están en `docs/comparacion_estadistica_3_2_3_PS.md` y `data/analysis/3_2_3/`.

## 8.3 Significancia estadística de la reducción de costo

### 8.3.1 Resultado principal: 90 corridas

| Referencia | n | Diferencia media (bps) | IC 95 % | Wilcoxon p | t p | Shapiro p | d de Cohen | r | Gana el sistema |
|---|---|---|---|---|---|---|---|---|---|
| **TWAP** | 90 | **−3,34** | [−15,69; 9,67] | **0,386** | 0,621 | 0,286 | −0,05 | −0,11 | 46 de 90 |
| **VWAP** | 90 | **−3,14** | [−17,50; 11,87] | **0,393** | 0,684 | 0,165 | −0,04 | −0,10 | 48 de 90 |

**Costo medio:** sistema 58,61 bps; TWAP 61,95; VWAP 61,75.

**Interpretación:**
- El sistema costó en promedio 3,34 bps menos que TWAP, una reducción relativa del 5,4 %.
- La diferencia **no es estadísticamente significativa** (Wilcoxon p = 0,386).
- El efecto es despreciable (d = −0,05) y el sistema gana en la mitad de las corridas (46 de 90).
- Shapiro-Wilk no rechaza la normalidad (p = 0,286), así que el t pareado también es válido, y coincide (p = 0,621).

**Lo que permite y lo que no permite concluir el IC:**
- **No permite** concluir que el sistema reduzca el costo: con 90 días simulados no se pudo demostrar una reducción.
- Esto **no equivale** a demostrar que no la hay.
- **Sí permite** descartar, con un 95 % de confianza, ventajas medias mayores que 15,7 bps y desventajas mayores que 9,7 bps.
- En particular, la ventaja de −22 bps que sugería la primera evaluación queda fuera del intervalo.

### 8.3.2 Resultado por profundidad del market maker

| Profundidad | n | Sistema − TWAP | IC 95 % | Wilcoxon p | p (Holm) | Sistema − VWAP | p (Holm) |
|---|---|---|---|---|---|---|---|
| ×4 | 30 | −10,53 | [−33,09; 11,79] | 0,440 | 1,000 | −9,64 | 1,000 |
| ×1 | 30 | −3,37 | [−26,15; 19,63] | 0,626 | 1,000 | −4,19 | 1,000 |
| ×0,25 | 30 | +3,87 | [−16,56; 25,30] | 0,871 | 1,000 | +4,41 | 1,000 |

- Ninguna profundidad muestra una diferencia significativa.
- En ×0,25, Shapiro-Wilk rechaza la normalidad (p = 0,010 frente a TWAP), así que ahí solo vale Wilcoxon, que de todos modos es la prueba principal.
- Con 30 corridas por escenario, el plan ya anticipaba que difícilmente saldría significativo (sección 5 del plan).

### 8.3.3 Robustez

| Variante (registrada en el plan) | n | Sistema − TWAP | IC 95 % | Wilcoxon p |
|---|---|---|---|---|
| Sin MO-06 (la orden que más pesó en la 3.1.3) | 81 | −3,42 | [−16,97; 10,58] | 0,456 |
| Promedio por orden y semilla entre profundidades | 30 | −3,34 | [−22,43; 16,72] | 0,641 |
| Costo ajustado (30 bps por acción no ejecutada) | 90 | −3,53 | [−15,93; 9,47] | 0,381 |

- **Promedio por orden y semilla:** controla que las 90 no sean del todo independientes, porque la misma orden y semilla aparecen en las tres profundidades.
- **Costo ajustado:** se aplica porque algunas corridas no completaron la orden. El sistema queda con 94,7 % en MO-08, semilla 4, en ×0,25. TWAP y VWAP quedan con 87,1 % en MO-09, semilla 4, en las tres profundidades.
- Ninguna variante cambia la conclusión.

### 8.3.4 Por qué la primera evaluación sugería una ventaja mayor

En la 3.1.3 (profundidad ×1, semillas 1–3, n = 30), el sistema costó −22,15 bps frente a TWAP (IC [−50,01; 4,43], Wilcoxon p = 0,096). En las 90 corridas, la misma comparación en ×1 con las semillas 4–6 da −3,37 bps. **Esta diferencia es variabilidad entre días, no un cambio del sistema:**
- La desviación estándar de las diferencias por corrida es de 78,7 bps en la 3.1.3 y de 67,5 bps en ×1 de las 90. Con 30 corridas, el error estándar de la media es de unos 12 a 14 bps, así que dos muestras de 30 pueden diferir en 20 bps por azar.
- **Prueba de que vienen de la misma distribución:** Mann-Whitney U entre las 30 diferencias de la 3.1.3 y las 30 de ×1, p = 0,395 (exploratorio). No hay evidencia de que difieran.
- **Lección metodológica:** haber evaluado en días nuevos evitó informar como resultado un efecto que era en parte favorable por azar.

## 8.4 Comparación con TWAP y VWAP: de qué depende la diferencia

### 8.4.1 Dirección del precio durante el día

La ventaja del sistema depende sobre todo de cómo se mueve el precio ese día. Se usa el costo de TWAP como indicador del movimiento: un costo positivo significa que el precio subió mientras se compraba.

| Medida (90 corridas, exploratorio) | Valor |
|---|---|
| Correlación de Spearman entre (sistema − TWAP) y el costo de TWAP | ρ = −0,78, p = 1,5·10⁻¹⁹ |
| Correlación de Pearson | r = −0,70, p = 1,5·10⁻¹⁴ |
| Días en que el precio subió (TWAP ≥ 0), n = 63 | El sistema ahorra 30,5 bps en promedio |
| Días en que el precio bajó (TWAP < 0), n = 27 | El sistema cuesta 60,0 bps más en promedio |

**Cómo se calcula la correlación de Spearman:**
- Se reemplazan los valores por sus rangos y se mide la correlación entre los rangos.
- El valor p prueba si ρ = 0 con la aproximación t de n − 2 grados de libertad.

**Interpretación:**
- La correlación se repite en cada profundidad: −0,77 en ×4, −0,78 en ×1 y −0,54 en ×0,25.
- La causa es el calendario del Maestro (8.5.1): compra una parte grande de lo pendiente al comienzo de cada media hora, así que concentra la compra temprano. Comprar temprano conviene si el precio sube y perjudica si baja.
- La ventaja media del sistema es, en buena parte, el balance entre días que suben y días que bajan en la muestra.

### 8.4.2 Variabilidad del costo entre días

| Grupo | Ref. | n | Desv. sistema | Desv. referencia | Razón | IC 95 % de la razón | Pitman-Morgan p |
|---|---|---|---|---|---|---|---|
| Total | TWAP | 90 | 118,8 | 154,6 | 0,77 | [0,69; 0,84] | 4,8·10⁻⁹ |
| Total | VWAP | 90 | 118,8 | 160,1 | 0,74 | [0,66; 0,81] | 2,4·10⁻⁹ |
| ×4 | TWAP | 30 | 113,0 | 155,3 | 0,73 | [0,61; 0,85] | 6,5·10⁻⁵ |
| ×1 | TWAP | 30 | 114,8 | 159,4 | 0,72 | [0,60; 0,79] | 4,7·10⁻⁵ |
| ×0,25 | TWAP | 30 | 130,8 | 153,5 | 0,85 | [0,69; 0,97] | 0,038 |

**Cómo se calcula la prueba de Pitman-Morgan** (exploratoria, no estaba en el plan):
- Compara las varianzas de dos mediciones pareadas.
- En cada corrida se calculan la suma S = sistema + TWAP y la resta D = sistema − TWAP.
- Si las varianzas fueran iguales, la correlación entre S y D sería 0.
- La correlación observada r se convierte en t = r·√((n − 2)/(1 − r²)), con n − 2 grados de libertad.
- El IC de la razón de desviaciones sale de un bootstrap pareado de 10.000 remuestreos.

**Interpretación:**
- El costo del sistema varía entre un 15 % y un 28 % menos que el de TWAP. La diferencia es significativa en el total y en cada profundidad.
- Ya se había visto en la 3.1.3 (razón 0,65, p = 8·10⁻⁵, n = 30).
- Para un operador, una menor dispersión reduce el riesgo de ejecución, aunque el costo medio sea parecido. El sistema evita los días muy caros y también aprovecha menos los muy baratos.

### 8.4.3 Profundidad del market maker

- **Kruskal-Wallis** sobre las diferencias sistema − TWAP de las tres profundidades: H = 0,14, p = 0,930, épsilon² = −0,021.
  - Cómo se calcula: se ordenan las 90 diferencias juntas y se compara el rango medio de cada grupo con el esperado si todos vinieran de la misma distribución.
- **Friedman** (control, 30 bloques orden × semilla): p = 0,393.
- **Frente a VWAP:** Kruskal-Wallis p = 0,963 y Friedman p = 0,273.
- **No hay evidencia** de que la ventaja dependa de la profundidad.
- La tendencia descriptiva (−10,5 en ×4, −3,4 en ×1, +3,9 en ×0,25) no es significativa.
- Esto concuerda con el C-6c: en este simulador, `mm_pov` cambia poco el costo de TWAP con órdenes límite.

## 8.5 Aporte de cada nivel de la arquitectura

### 8.5.1 El Maestro aprendió un calendario casi fijo

| Profundidad | Decisiones | Acción más frecuente | Frecuencia |
|---|---|---|---|
| ×4 | 282 | α = 0,50, ventana de 15 min | 272 (96,5 %) |
| ×1 | 282 | α = 0,50, ventana de 15 min | 275 (97,5 %) |
| ×0,25 | 282 | α = 0,40, ventana de 15 min | 204 (72,3 %) |

En la práctica, la política del Maestro equivale a «comprar la mitad de lo que falta cada media hora». La revisión del código (`docs/qa_sistema_media_90_PS.md` y `docs/maestro_v2_PS.md`) encontró tres causas:

1. **Se entrenó sin la corrección del cierre.**
   - Las órdenes que parten a las 14:00 no podían completarse en el entrenamiento, y lo pendiente se castigaba con λ.
   - La manera más directa de reducir esa penalización es comprar rápido.
2. **Su estado S_M no tenía información de mercado** (desviación 13).
   - La volatilidad y la actividad entraban como constantes (0,002 y 0,2), y el desbalance del libro (OBI) valía 0.
   - El Maestro solo veía lo que falta, la hora y sus decisiones previas.
3. **Las ventanas de 30 minutos son mercados independientes.** No hay una tendencia del día que el Maestro pueda aprender a anticipar.

### 8.5.2 Control con reglas fijas: separación del aporte

Para separar el aporte del Maestro y el de los Ejecutores, se reemplazó al Maestro por dos reglas, manteniendo los mismos Ejecutores, órdenes y semillas (profundidad ×1, n = 30 pares, `docs/control_reglas_3_2_3_resultado_PS.md`). Se registró antes de correrlo (`docs/control_reglas_3_2_3_PS.md`).

| Comparación | Pregunta | Diferencia (bps) | IC 95 % | Wilcoxon p (Holm, 3 pruebas) | d de Cohen | Gana la primera |
|---|---|---|---|---|---|---|
| Regla fija − sistema | ¿El Maestro hace algo distinto de α = 0,5 siempre? | −2,66 | [−12,16; 2,91] | 1,000 | −0,11 | 1 de 30 |
| Sistema − regla uniforme | Aporte del calendario del Maestro | +12,00 | [−10,59; 34,54] | 1,000 | 0,18 | 16 de 30 |
| Regla uniforme − TWAP | Aporte de los Ejecutores | **−15,37** | **[−20,35; −10,32]** | **7,0·10⁻⁶** | **−1,08** | **26 de 30** |

**Lectura:**
- **Descomposición exacta, corrida por corrida:** sistema − TWAP (−3,37) = calendario (+12,00) + Ejecutores (−15,37).
- **Regla fija contra el sistema:** 25 de 30 corridas son idénticas. Eso confirma que la simulación es determinista y que el Maestro equivale a la regla fija.
- **Ejecutores:** con el mismo calendario que TWAP, cuestan 15,37 bps menos. El efecto es grande (d = −1,08) y significativo después de Holm (p = 7,0·10⁻⁶).
- **Calendario del Maestro:** no aporta en promedio (+12,00 bps, p = 1,0). Depende de la dirección del día:
  - ahorra 24,5 bps en los días que suben (n = 20);
  - cuesta 85,0 bps más en los que bajan (n = 10).
  - Esta división es descriptiva, sin prueba.
- **Robustez:** con el costo ajustado por lo no ejecutado (30 bps), la conclusión no cambia. Ejecutores: −15,25 bps, p (Holm) = 7,0·10⁻⁶.

**Por qué los Ejecutores ahorran frente a TWAP:**
- El TWAP de referencia compra con órdenes a mercado y cruza el spread en cada compra. Los Ejecutores usan órdenes límite.
- En la reevaluación de 300 semillas en una ventana (`docs/reeval_300_imitacion_resultado_PS.md`), el Ejecutor elegido costó 5,68 bps, contra 4,65 de un TWAP **con órdenes límite**. Es decir, quedó 1,03 bps más caro (IC 95 % [0,11; 1,88]).
- La lectura más probable es que el ahorro de 15 bps viene de no cruzar el spread, y que frente a un TWAP con órdenes límite la ventaja sería cercana a 0. Esta lectura no se probó con las 90, porque el TWAP con límite no se corrió en ellas.

### 8.5.3 Maestro corregido (Maestro v2)

Para comprobar si las causas de 8.5.1 explicaban el resultado, se entrenó una versión corregida (`docs/maestro_v2_resultado_PS.md`):
- su estado mide la volatilidad, la profundidad y el desbalance en el mercado simulado;
- se entrena con la corrección del cierre;
- n_slices se cuenta por orden.

**Resultado** (profundidad ×1, n = 30 pares):

| Medida | Valor |
|---|---|
| Acción más frecuente | α = 0,40 en el 74 % de las decisiones (ya no 0,50) |
| Costo medio | 46,3 bps (Maestro original: 47,1) |
| v2 − Maestro original | −0,85 bps [−9,97; 8,25], Wilcoxon p = 0,855 |
| v2 − TWAP | −4,21 bps [−23,71; 16,11], Wilcoxon p = 0,556 |

**Interpretación:**
- La corrección cambió la política, pero no el costo.
- Incluso con información de mercado, el Maestro sigue eligiendo casi una regla fija. En este entorno, el calendario no tiene de dónde sacar ventaja, porque las ventanas son independientes (limitación L1).

### 8.5.4 Síntesis

- La reducción de costo **viene de la capa de Ejecutores**: significativa y con un efecto grande frente a TWAP a mercado.
- El Maestro, en su forma actual, **agrega variabilidad** que depende del día y compensa lo que ahorran los Ejecutores.
- Por eso el sistema completo no supera a TWAP de forma significativa, aunque sí es más estable.

## 8.6 Sensibilidad

### 8.6.1 Hiperparámetros del entrenamiento

- En el barrido de hiperparámetros (3.1.1 y 3.1.2, `docs/barrido_hiperparametros_resultado_PS.md`), unas 30 configuraciones quedaron entre −2,4 y −2,6 bps.
- La mejor mejoró ≈ 0,2 bps sobre la configuración por defecto, dentro del error.
- Se mantuvieron λ = 0,02 y la configuración por defecto. El resultado es poco sensible a los hiperparámetros probados.

### 8.6.2 Tramo de inicio de la orden (exploratorio)

> **Confirmado por la 3.2.4 (MR, `docs/sensibilidad_3_2_4_MR.md`):** obtiene los mismos valores con las mismas 90 corridas (Kruskal-Wallis H = 8,98, p = 0,0112; cierre −34,78 bps, Wilcoxon p Holm = 0,0089). Sigue siendo exploratorio y con tramo y activo confundidos.

| Tramo | n | Sistema − TWAP media | Mediana | IC 95 % | Wilcoxon p | p (Holm, 3 tramos) |
|---|---|---|---|---|---|---|
| Apertura | 36 | +14,77 | +10,73 | [−3,71; 33,71] | 0,300 | 0,600 |
| Media jornada | 27 | +3,94 | +16,72 | [−21,87; 29,96] | 0,953 | 0,953 |
| **Cierre** | 27 | **−34,78** | **−37,99** | **[−55,40; −15,18]** | **0,003** | **0,009** |

- **Kruskal-Wallis entre tramos:** H = 8,98, p = 0,011. La diferencia sí depende del tramo.
- **Lectura:** el sistema solo es más barato de forma significativa en las órdenes que parten en el cierre.
- **Confusión con la dirección del día:**
  - En las órdenes de cierre, el precio subió en el 81 % de los días, y TWAP costó en promedio 68,4 bps.
  - En la apertura subió en el 56 % de los días, con un costo medio de TWAP de 14,3 bps.
  - Con este diseño no se puede separar el efecto del tramo del de la dirección del día (8.4.1). Comprar rápido en un tramo corto que sube favorece al calendario del Maestro.
- **Cómo se calculó:**
  - Wilcoxon de rangos con signo en cada tramo sobre las diferencias pareadas, con Holm para 3 pruebas;
  - IC por bootstrap de 10.000 remuestreos;
  - Kruskal-Wallis entre los tres grupos.
  - Script: `scripts/figuras_capitulo7_PS.py`. Datos: `data/analysis/cap7/cifras_capitulo7.json`. Figura: `diferencia_por_tramo.png`.

### 8.6.3 Tamaño de la orden (tres puntos y prueba de tendencia 3.2.4)

> **Prueba de tendencia: tarea 3.2.4 (MR, `docs/sensibilidad_3_2_4_MR.md`), verificada por PS.** Ver «Tendencia con el tamaño» más abajo.

**Datos:** profundidad ×1, las mismas 10 meta-órdenes y semillas 4–6 en los tres tamaños (diseño en estrella, desviación 12). El factor 0,5 lo corrió BF, el 1 PS y el 1,5 MR. Cifras de la 3.2.2 (`data/analysis/3_2_2/tabla_tamanos.md`).

| Factor (volumen del día) | n | Sistema | TWAP | VWAP | Sistema − TWAP | IC 95 % | Wilcoxon p |
|---|---|---|---|---|---|---|---|
| 0,5 (5 %) | 30 | 38,63 | 36,43 | 36,68 | +2,20 | [−20,84; 25,72] | 0,95 |
| 1 (10 %) | 30 | 47,11 | 50,48 | 51,30 | −3,37 | [−26,15; 19,63] | 0,63 |
| 1,5 (15 %) | 30 | 51,75 | 59,63 | 60,75 | −7,88 | [−25,03; 9,47] | 0,37 |

**Cómo se calculó:** en cada tamaño se toma la diferencia sistema − TWAP de cada uno de los 30 días pareados; Wilcoxon de rangos con signo bilateral sobre esas 30 diferencias; IC 95 % por bootstrap de la media.

**Cuánto sube el costo al pasar de 0,5 a 1** (mismos 30 días; Wilcoxon sobre la diferencia de costo de cada día):

| Estrategia | Aumento | IC 95 % | Wilcoxon p |
|---|---|---|---|
| Sistema | +8,48 | [3,57; 12,96] | 7,3·10⁻⁴ |
| TWAP | +14,04 | [10,69; 16,95] | 1,4·10⁻⁶ |
| VWAP | +14,62 | [11,16; 17,59] | 1,0·10⁻⁶ |

**Lectura:**
- El costo sube con el tamaño en las tres estrategias, como predice el impacto en raíz cuadrada. Entre 0,5 y 1,5, TWAP sube 23,2 bps y el sistema 13,1 bps.
- Por eso la diferencia sistema − TWAP pasa de +2,2 a −3,4 y a −7,9 bps. **Ningún punto es significativo por sí solo** (p entre 0,37 y 0,95).
- El cambio de la ventaja entre 0,5 y 1 tampoco es significativo: −5,57 bps [−11,77; 0,26], Wilcoxon n = 30, p = 0,080 (exploratorio).

**Tendencia con el tamaño (3.2.4 de MR, verificada por PS):**

| Prueba | Qué mide | n | Estadístico | p |
|---|---|---|---|---|
| Friedman (3.2.4, MR) | Si la diferencia sistema − TWAP cambia entre los 3 tamaños, comparando dentro de cada día | 30 días | Q = 6,47 | 0,039 |
| Page (PS) | Si la diferencia baja de forma ordenada al crecer el tamaño (prueba de tendencia para niveles ordenados) | 30 días | L = 379 | 0,007 |
| Wilcoxon (PS) | Cuánto cambia la diferencia de 0,5 a 1,5 | 30 días | −10,08 bps [−23,66; 3,11] | 0,164 |
| Friedman sin días bajo 95 % (3.2.4, MR) | Robustez al cumplimiento | 25 días | Q = 6,08 | 0,048 |

**Cómo se calculó:** para cada uno de los 30 días (10 órdenes × semillas 4–6) se toma sistema − TWAP en los tres tamaños. Friedman y Page ordenan esas tres diferencias dentro de cada día (rango 1 a 3) y prueban si los rangos medios difieren (Friedman) o siguen el orden 0,5 > 1 > 1,5 (Page, unilateral). Wilcoxon de rangos con signo sobre la diferencia 1,5 − 0,5 de cada día. Rangos medios: 2,37 (0,5), 1,90 (1) y 1,73 (1,5).

**Lectura:**
- **Hay una tendencia significativa en el orden:** dentro de un mismo día, la ventaja del sistema tiende a ser mayor con órdenes más grandes (Page p = 0,007; Friedman p = 0,039).
- **El tamaño del cambio no es significativo:** de 0,5 a 1,5 la ventaja mejora 10,1 bps en promedio, pero el IC incluye el 0 (Wilcoxon p = 0,164). Solo 12 de 30 días mejoran en los dos pasos.
- **Es exploratorio:** la 3.2.4 hace muchas pruebas sin corrección por multiplicidad, y no estaba en el análisis registrado como prueba principal.
- **Interpretación prudente:** el sistema se degrada menos que TWAP cuando la orden crece, lo que es coherente con que sus Ejecutores usen órdenes límite y no crucen el spread. Pero con 1,5 parte del efecto viene de días que no completaron y el Maestro opera fuera del tamaño con que se entrenó.

**Cumplimiento** (advertencia de BF, `data/analysis/capitulo7_BF/tabla_cumplimiento.md`):
- Con el factor 1,5 el sistema no siempre completa la orden: mínimo 78,4 %, y 4 de 30 días bajo el 95 % (órdenes que parten tarde, MO-08 y MO-09). TWAP y VWAP bajan hasta 83,1 %.
- Un día que no completa compra menos y por eso puede parecer más barato. **Prueba de robustez:** sin los 5 días en que alguna estrategia queda bajo el 95 %, sistema − TWAP con 1,5 = −5,06 bps (IC 95 % [−23,50; 14,76] según la 3.2.2; Wilcoxon n = 25, p = 0,51).
- Con el castigo de 30 bps por volumen no ejecutado queda en −6,66 bps (p = 0,38).
- La dirección se mantiene, pero más débil: parte de la ventaja en 1,5 viene de días que no completaron.

**Límites:**
- El Maestro se entrenó con un solo tamaño (factor 1): 0,5 y 1,5 quedan fuera de lo que vio, y 1,5 es una extrapolación.
- El tamaño se midió solo en profundidad ×1: no se sabe si interactúa con la profundidad.

Figura: `data/analysis/cap7/costo_vs_tamano.png` (costo medio de las tres estrategias en los tres tamaños, con sistema − TWAP y su valor p en cada punto).

### 8.6.4 Supuestos que no se variaron

- **Impacto acumulado** (Y = 0,5, τ = 120 min): es un supuesto, no está calibrado.
- **Volatilidad y spread:** no se variaron por separado; la profundidad los cambia solo de forma indirecta.
- Se declaran como límites (8.7).

## 8.7 Limitaciones y análisis crítico

| # | Limitación | Efecto sobre el resultado | Dónde se documenta |
|---|---|---|---|
| L1 | Cada ventana de 30 min es un mercado independiente; solo se unen por el impacto acumulado | El Maestro no tiene una tendencia que anticipar | Desviación 7 |
| L2 | El Maestro original se entrenó sin la corrección del cierre y sin datos de mercado | Calendario casi fijo. El Maestro v2 lo corrige sin cambiar el costo | Desviaciones 11 y 13 |
| L3 | El Maestro se entrenó en Poisson y se evalúa en ABIDES | Posible pérdida al cambiar de simulador | `sistema_final_resultado_PS.md` |
| L4 | La misma red de Ejecutor (apertura) se usa en los tres tramos | Los Ejecutores de media jornada y cierre no están especializados | Desviación 8 |
| L5 | `tasa_ordenes` vale 0 en ABIDES | El Ejecutor ve 26 de sus 27 variables | Desviación 14 |
| L6 | **La referencia TWAP/VWAP compra a mercado; los Ejecutores usan límite** | La ventaja de los Ejecutores puede deberse sobre todo a no cruzar el spread | 8.5.2 |
| L7 | Los escenarios son profundidad del market maker, no liquidez validada | No se puede afirmar nada sobre liquidez real | C-6c, desviación 10 |
| L8 | Tres acciones, 10 órdenes y un día de calibración | Validez externa limitada | Meta-órdenes v2 |
| L9 | Simulación sin operación real | Sin latencia, comisiones ni reacción de participantes reales | Título I |
| L10 | 90 corridas (30 por escenario) | Potencia del 33 % al 76 % según el tamaño real del efecto; por escenario, baja | Plan 3.2.3, sección 5 |
| L11 | Impacto, volatilidad y spread no variados | No se sabe cómo cambia el resultado con otros supuestos | 8.6.4 |

**Análisis crítico:**
- La arquitectura jerárquica de dos niveles con PPO se implementó completa y funciona: ejecuta las órdenes al 99,8 % en promedio, y el resto se ajusta con el costo penalizado.
- La hipótesis de que **coordinar** un planificador y ejecutores reduce el costo frente a TWAP **no se confirmó** con significancia.
- El experimento sí muestra dónde está el valor y dónde no:
  - la capa de ejecución aprende a comprar mejor que la regla ingenua;
  - la capa de planificación no tiene, en este entorno, información ni dinámica de la cual aprender.
- La lección de diseño es que un planificador solo puede aprender lo que el entorno contiene. Si el día simulado no tiene continuidad entre ventanas, ninguna política de calendario puede anticipar el precio.

## 8.8 Implicaciones prácticas y costo de las alternativas

### 8.8.1 Lo que el resultado permite y no permite afirmar

- **Permite:** un sistema de dos niveles con PPO puede ejecutar meta-órdenes completas en un simulador calibrado del IPSA, con un costo medio similar al de TWAP y VWAP y una variabilidad significativamente menor.
- **Permite:** la capa de Ejecutores, por sí sola, reduce el costo frente a una ejecución ingenua a mercado.
- **No permite:** afirmar que el sistema completo reduzca el costo de forma consistente, ni que funcione igual en mercado real.
- **Riesgo operativo del calendario aprendido:** comprar temprano es una apuesta implícita a que el precio sube. Un operador debería conocerlo antes de usarlo.

### 8.8.2 Ventajas, desventajas y costos de las alternativas evaluadas

Los costos computacionales corresponden a lo medido en Colab durante el proyecto.

| Alternativa | Ventajas | Desventajas | Costo computacional | Costo económico | Costo operacional |
|---|---|---|---|---|---|
| **TWAP / VWAP a mercado** (referencia) | Sin entrenamiento, transparente, fácil de auditar | Cruza el spread; más variable entre días | Nulo | Nulo | Muy bajo: es una regla fija |
| **Sistema completo** (Maestro + Ejecutores PPO) | Completa la orden; 23 % menos de variabilidad que TWAP (p = 4,8·10⁻⁹) | Sin reducción significativa del costo medio; calendario dependiente del día | Maestro ≈ 40 min de entrenamiento; cada bloque de 15 corridas en ABIDES ≈ 3 h (las 90 corridas: 6 bloques de ≈ 3 h por estrategia, más los benchmarks) | Solo Colab y datos públicos (yfinance); ABIDES es abierto | Alto: mantener dos niveles de redes, monitoreo y reentrenamiento |
| **Solo Ejecutores PPO con calendario uniforme** | −15,4 bps frente a TWAP a mercado (p Holm = 7·10⁻⁶) con el mismo calendario; más simple que el sistema | Ventaja ligada a usar órdenes límite; ≈ +1 bps frente a TWAP con límite | El Ejecutor ya entrenado; evaluar 30 corridas ≈ 2 h | Igual que arriba | Medio: un solo nivel de red |
| **Maestro v2** (con información de mercado) | Corrige el diseño del estado; política menos extrema | Mismo costo que el Maestro original (p = 0,855) | Entrenamiento ≈ 40 min; evaluación ≈ 2 h | Igual que arriba | Alto, como el sistema completo |

**Implicación:** con la evidencia de este trabajo, la alternativa con mejor relación entre beneficio y costo es la **capa de Ejecutores con un calendario simple**. Agregar el Maestro aumenta la complejidad sin un beneficio medible en el costo medio.

## 8.9 Trabajo futuro (detalle en el capítulo de Conclusiones)

1. **Entrenar y evaluar el Maestro en un día continuo** (ABIDES de jornada completa), para que exista una tendencia que aprender.
2. **Comparar contra un TWAP con órdenes límite** en las mismas 90 corridas, para separar el aporte de la política del de usar órdenes límite.
3. **Calibrar escenarios de liquidez con días reales** del IPSA de baja y alta liquidez, en vez de la profundidad del market maker.
4. **Calibrar el impacto** (Y y τ) y variar la volatilidad y el spread.
5. **Especializar los Ejecutores** de media jornada y cierre, y entregar `tasa_ordenes` en ABIDES.

---

## Fuentes de las cifras

| Sección | Documento | Datos |
|---|---|---|
| 8.3, 8.4.3 | `docs/comparacion_estadistica_3_2_3_PS.md` | `data/analysis/3_2_3/`, `3_2_3_ajustado/` |
| 8.3.4 | `docs/corridas_30_corregidas_resultado_PS.md` | `data/colab_resultados/corridas_30_completa/` |
| 8.4.1, 8.6.2, 8.6.3 | Este capítulo (exploratorio) | `data/analysis/cap7/cifras_capitulo7.json` (`scripts/figuras_capitulo7_PS.py`) |
| 8.4.2 | `docs/comparacion_estadistica_3_2_3_PS.md`, sección 4.1 | `corridas_90/*/tabla/corridas.csv` |
| 8.5.2 | `docs/control_reglas_3_2_3_resultado_PS.md` | `data/colab_resultados/control_reglas/media/` |
| 8.5.3 | `docs/maestro_v2_resultado_PS.md` | `data/colab_resultados/maestro_v2/` |
| 8.6.1 | `docs/barrido_hiperparametros_resultado_PS.md` | — |
