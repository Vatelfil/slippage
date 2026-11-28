# Capítulo 7. Resultados y evaluación

**Tarea:** 4.1.2 (Sprint 8, «Cap. 6 Resultados» en `plan-desarrollo-titulo-2.xlsx`). **Autor:** BF, con apoyo de Claude Code. **Versión:** 22 de noviembre de 2026. Revisión del 28 de noviembre (PS, con apoyo de Claude Code, a partir de las observaciones del equipo): sin iniciales ni códigos internos, con todas las cifras de resultados en este capítulo (el Capítulo 8 solo las interpreta). Pendiente de revisión por BF.

**Numeración:** sigue la estructura del Título I (9 capítulos), como `docs/informe_titulo2_ensamblado_borrador.md`. El montaje experimental y el entrenamiento están en el Capítulo 6 (MR); la interpretación estadística, en el Capítulo 8 (PS).

**Reparto con el Capítulo 8** (propuesto por BF el 20 nov): este capítulo **informa** los resultados (tablas, figura, cumplimiento y variantes). El Capítulo 8 los **interpreta**: significancia y tamaño del efecto (8.3), de qué depende la diferencia (8.4), aporte de cada nivel (8.5), sensibilidad (8.6) y limitaciones (8.7).

**Convención** (la misma del Capítulo 8):
- **Costo:** slippage contra el precio de llegada, en puntos base (bps): (precio medio ejecutado − precio de llegada) / precio de llegada × 10.000. Positivo = costo.
- **Diferencia:** costo del sistema − costo de la referencia en el mismo día simulado (misma profundidad, orden y semilla). **Negativa = el sistema cuesta menos.**
- **Pruebas:** cada resultado inferencial indica la prueba, el n y el valor p. Los IC 95 % son de bootstrap pareado (3.000 remuestreos, semilla 0) y las pruebas son de Wilcoxon de rangos con signo pareado, las mismas de la consolidación de resultados. La metodología está en el Capítulo 6, sección 6.5.

---

## 7.1 Qué se evaluó

**Tabla.** Bloques de la evaluación final: profundidad del market maker, tamaño de la orden y corridas por estrategia.

| Bloque | Profundidad del market maker | Tamaño de la orden | Corridas por estrategia |
|---|---|---|---|
| Principal | ×4, ×1 y ×0,25 | 1 (10 % del volumen del día; 5 % si parte en el cierre) | 90 = 3 × 10 órdenes × 3 semillas |
| Eje de tamaño | ×1 | 0,5 y 1,5 | 30 + 30 |

- **Estrategias:** el sistema jerárquico (Maestro + Ejecutores PPO), TWAP y VWAP. Los tres compran la misma orden en el mismo día simulado.
- **Total: 450 ejecuciones**, 150 corridas por estrategia. El detalle del montaje (meta-órdenes, semillas, configuración del sistema, impacto) está en el Capítulo 6, sección 6.1.
- **Fuente única de las cifras:** la consolidación de los resultados de las 450 ejecuciones. Las tablas y la figura se generan con un script a partir de esa consolidación, sin recalcular las pruebas, y se reproducen con los pasos del Anexo C.

## 7.2 Calidad de las corridas y cumplimiento

**Chequeo de calidad de la consolidación: correcto.**
- Se leyeron 450 corridas, sin errores ni duplicados.
- Los cinco bloques tienen 30 días pareados por estrategia.

**Tabla 7.1.** Cumplimiento de la orden (acciones ejecutadas / acciones de la orden): el mínimo por bloque y las corridas que llegan al 95 % .

| Bloque | Sistema: mínimo / ≥ 95 % | TWAP: mínimo / ≥ 95 % | VWAP: mínimo / ≥ 95 % |
|---|---|---|---|
| ×4, tamaño 1 | 100,0 % / 30 de 30 | 87,1 % / 29 de 30 | 87,1 % / 29 de 30 |
| ×1, tamaño 1 | 98,6 % / 30 de 30 | 87,1 % / 29 de 30 | 87,1 % / 29 de 30 |
| ×0,25, tamaño 1 | 94,7 % / 29 de 30 | 87,1 % / 29 de 30 | 87,1 % / 29 de 30 |
| ×1, tamaño 0,5 | 100,0 % / 30 de 30 | 99,3 % / 30 de 30 | 99,3 % / 30 de 30 |
| ×1, tamaño 1,5 | 78,4 % / 26 de 30 | 83,1 % / 29 de 30 | 83,1 % / 28 de 30 |

**Resultado:**
- El sistema completa al menos el 95 % de la orden en **145 de 150 corridas**; TWAP en 146 y VWAP en 145.
- **Benchmarks con tamaño 1:** fallan en un solo día, MO-09 con semilla 4, en las tres profundidades (87,1 %).
- **Sistema con tamaño 1:** falla una vez (MO-08, semilla 4, con ×0,25: 94,7 %).
- **Sistema con tamaño 1,5:** queda bajo el 95 % en 4 días, todos órdenes de cierre de FALABELLA (MO-08 y MO-09), con un mínimo de 78,4 %. En esos días completa menos que TWAP.
- **Por qué importa:** las acciones que no se compran no entran al costo, así que un día incompleto parece más barato. La sección 7.6 informa las variantes que corrigen esto.

## 7.3 Desempeño comparativo: las 90 corridas con tamaño 1

**Tabla.** Distribución del costo por estrategia en las 90 corridas con tamaño 1 (bps).

| | n | Sistema | TWAP | VWAP |
|---|---|---|---|---|
| Costo medio (bps) | 90 | **58,61** | 61,95 | 61,75 |
| Costo mediano (bps) | 90 | **40,10** | 45,10 | 45,94 |
| Desviación estándar (bps) | 90 | **118,83** | 154,58 | 160,05 |
| Peor corrida (bps) | 90 | **404,54** | 522,69 | 522,69 |
| Mejor corrida (bps) | 90 | −324,75 | **−377,94** | **−377,94** |

**Tabla.** Diferencias pareadas del sistema frente a TWAP y VWAP en las 90 corridas: media, IC 95 %, Wilcoxon y días ganados.

| Comparación (n = 90 días) | Diferencia media | IC 95 % | Wilcoxon p | Dif. % | Días en que el sistema cuesta menos |
|---|---|---|---|---|---|
| Sistema − TWAP | **−3,34** | [−15,69; 9,67] | 0,39 | −5,4 % | 46 de 90 |
| Sistema − VWAP | **−3,14** | [−17,50; 11,87] | 0,39 | −5,1 % | 48 de 90 |

**Resultado:**
- El sistema tiene el costo medio y mediano más bajos de las tres estrategias, y la menor dispersión.
- La diferencia media con TWAP es −3,34 bps, pero el IC incluye el 0 y el sistema cuesta menos en la mitad de los días (46 de 90). **La reducción no es estadísticamente significativa** (Wilcoxon pareado, n = 90, p = 0,386).
- **Pruebas complementarias:** Shapiro-Wilk no rechaza la normalidad de las diferencias (p = 0,286), y el t pareado coincide (p = 0,621). El tamaño del efecto es despreciable: d de Cohen = −0,05 y correlación biserial de rangos r = −0,11. Frente a VWAP: t pareado p = 0,684, d = −0,04.
- La dispersión menor sí es significativa: desviación 118,8 contra 154,6 bps, razón 0,77, Pitman-Morgan p = 4,8·10⁻⁹, n = 90. Su lectura está en el Capítulo 8, sección 8.3.2.
- El sistema evita las peores corridas de TWAP (peor 404,5 contra 522,7 bps), pero tampoco alcanza sus mejores (−324,8 contra −377,9).
- **Diferencia %:** cociente de medias, 100 × media(sistema − TWAP) / media(TWAP). No se promedian porcentajes por corrida, porque hay costos negativos.

## 7.4 Resultados por profundidad del market maker

**Tabla 7.2.** Costo medio y diferencias pareadas por profundidad, tamaño 1 .

| Profundidad | n | Sistema | TWAP | VWAP | Sist. − TWAP | IC 95 % | p | Sist. − VWAP | IC 95 % | p |
|---|---|---|---|---|---|---|---|---|---|---|
| ×4 | 30 | 59,51 | 70,05 | 69,15 | −10,53 | [−33,09; 11,79] | 0,44 | −9,64 | [−33,76; 14,52] | 0,40 |
| ×1 | 30 | 47,11 | 50,48 | 51,30 | −3,37 | [−26,15; 19,63] | 0,63 | −4,19 | [−30,31; 22,11] | 0,61 |
| ×0,25 | 30 | 69,19 | 65,33 | 64,79 | +3,87 | [−16,56; 25,30] | 0,87 | +4,41 | [−20,42; 30,85] | 0,82 |
| Global | 90 | 58,61 | 61,95 | 61,75 | −3,34 | [−15,69; 9,67] | 0,39 | −3,14 | [−17,50; 11,87] | 0,39 |
| Global sin días bajo 95 % | 86 | 59,60 | 62,85 | 62,64 | −3,25 | [−16,56; 10,48] | 0,42 | −3,04 | [−18,02; 12,77] | 0,43 |

`p`: Wilcoxon pareado sobre los días del bloque.

**Figura 7.1.** Costo por corrida según la profundidad del market maker, tamaño 1 (`data/analysis/capitulo7_BF/cajas_profundidad.png`, `fig:cajas_profundidad`).
- **Qué muestra:** caja = cuartiles; línea = mediana; rombo = media; bigotes = 1,5 veces el rango intercuartil; círculos = corridas fuera de los bigotes. 30 corridas por caja.
- **Cada panel indica** n, la diferencia sistema − TWAP y su p de Wilcoxon pareado.

**Tabla 7.3.** Distribución del costo por profundidad y estrategia .

| Profundidad | Estrategia | Media | Mediana | Desv. est. | Peor | Mejor | Cumplimiento mínimo |
|---|---|---|---|---|---|---|---|
| ×4 | Sistema | 59,51 | 32,45 | 113,05 | 344,51 | −263,04 | 100,0 % |
| ×4 | TWAP | 70,05 | 44,74 | 155,33 | 522,69 | −323,03 | 87,1 % |
| ×4 | VWAP | 69,15 | 43,90 | 158,06 | 522,69 | −323,03 | 87,1 % |
| ×1 | Sistema | 47,11 | 38,04 | 114,81 | 285,58 | −311,76 | 98,6 % |
| ×1 | TWAP | 50,48 | 38,13 | 159,43 | 386,76 | −377,94 | 87,1 % |
| ×1 | VWAP | 51,30 | 38,84 | 166,09 | 386,76 | −377,94 | 87,1 % |
| ×0,25 | Sistema | 69,19 | 50,16 | 130,84 | 404,54 | −324,75 | 94,7 % |
| ×0,25 | TWAP | 65,33 | 56,33 | 153,53 | 376,10 | −329,12 | 87,1 % |
| ×0,25 | VWAP | 64,79 | 50,96 | 160,84 | 402,45 | −329,12 | 87,1 % |

**Resultado:**
- **Ninguna profundidad muestra una diferencia significativa** (Wilcoxon pareado, n = 30 por profundidad: p = 0,44, 0,63 y 0,87; con la corrección de Holm por 3 pruebas, los tres p corregidos valen 1,0, también frente a VWAP). En ×0,25, Shapiro-Wilk rechaza la normalidad (p = 0,010), así que ahí solo vale Wilcoxon. El sistema cuesta menos que TWAP en 15, 16 y 15 de los 30 días.
- **La diferencia media pasa de −10,53 bps con ×4 a −3,37 con ×1 y a +3,87 con ×0,25.** Con ×0,25 el ranking por media se invierte: VWAP < TWAP < Sistema.
- **Esa tendencia no es significativa:** Kruskal-Wallis sobre las 90 diferencias, H = 0,14, p = 0,930; Friedman con los 30 días como bloques, p = 0,393 (Capítulo 8, sección 8.3.3).
- **Con ×0,25 la media y la mediana del sistema no van en el mismo sentido.** Su media supera a la de TWAP (69,19 contra 65,33), pero su mediana es menor (50,16 contra 56,33). La media del sistema la sube su peor corrida (404,54 bps).
- **El sistema tiene la menor dispersión en las tres profundidades** (desviación 113 a 131 bps, contra 154 a 166 de TWAP y VWAP).

## 7.5 Resultados según el tamaño de la orden (profundidad ×1)

**Tabla 7.4.** Costo medio y diferencias pareadas según el tamaño (factor sobre el 10 % del volumen del día), profundidad ×1 .

| Tamaño | n | Sistema | TWAP | VWAP | Sist. − TWAP | IC 95 % | p | Sist. − VWAP | IC 95 % | p |
|---|---|---|---|---|---|---|---|---|---|---|
| 0,5 | 30 | 38,63 | 36,43 | 36,68 | +2,20 | [−20,84; 25,72] | 0,95 | +1,95 | [−23,95; 28,71] | 0,95 |
| 1 | 30 | 47,11 | 50,48 | 51,30 | −3,37 | [−26,15; 19,63] | 0,63 | −4,19 | [−30,31; 22,11] | 0,61 |
| 1,5 | 30 | 51,75 | 59,63 | 60,75 | −7,88 | [−25,03; 9,47] | 0,37 | −8,99 | [−29,82; 11,44] | 0,35 |

**Resultado:**
- **Las tres estrategias cuestan más con la orden más grande.** De 0,5 a 1,5, el sistema sube 13,12 bps, TWAP 23,20 y VWAP 24,06.
- **La diferencia sistema − TWAP** es de +2,20, −3,37 y −7,88 bps. Ninguna es significativa por sí sola (Wilcoxon pareado, n = 30: p = 0,95, 0,63 y 0,37).
- **Prueba de si la diferencia cambia con el tamaño** (análisis de sensibilidad; n = 30 días como bloques):

**Tabla.** Pruebas de tendencia de la diferencia sistema − TWAP con el tamaño de la orden (30 días como bloques).

| Prueba | Qué mide | Estadístico | p |
|---|---|---|---|
| Friedman | Si la diferencia sistema − TWAP cambia entre los 3 tamaños | Q = 6,47 | 0,039 |
| Page | Si la diferencia baja en orden al crecer el tamaño (0,5 > 1 > 1,5) | L = 379 | 0,007 |
| Wilcoxon | Cuánto cambia la diferencia de 0,5 a 1,5 | −10,08 bps [−23,66; 3,11] | 0,164 |

  - **La tendencia es significativa en el orden, pero no en la magnitud:** dentro de cada día, la ventaja del sistema tiende a crecer con el tamaño, pero el cambio de 0,5 a 1,5 no es significativo.
  - Es exploratorio: no era la prueba principal del plan. La lectura está en el Capítulo 8, sección 8.5.3. Sin los 5 días con cumplimiento bajo el 95 %, Friedman sigue siendo significativo (Q = 6,08, n = 25, p = 0,048).
- **Dos advertencias para estas cifras:**
  - el Maestro se entrenó con un solo tamaño (factor 1), así que 0,5 y 1,5 quedan fuera de lo que vio (desviación 12);
  - con 1,5, parte de la ventaja viene de días en que el sistema no completó la orden (sección 7.6).

## 7.6 Robustez

**Tabla.** Variantes de robustez de la diferencia sistema − TWAP (tamaño 1 y tamaño 1,5).

| Variante | n | Sistema − TWAP | IC 95 % | Wilcoxon p |
|---|---|---|---|---|
| **Tamaño 1: principal** (slippage crudo) | 90 | **−3,34** | [−15,69; 9,67] | 0,39 |
| Tamaño 1, sin la orden MO-06 (la que más pesó en la primera evaluación) | 81 | −3,42 | [−16,97; 10,58] | 0,456 |
| Tamaño 1, promedio por orden y semilla entre profundidades | 30 | −3,34 | [−22,43; 16,72] | 0,641 |
| Tamaño 1, costo ajustado (+30 bps por acción no ejecutada) | 90 | −3,53 | [−15,93; 9,47] | 0,38 |
| Tamaño 1, sin días bajo el 95 % | 86 | −3,25 | [−16,56; 10,48] | 0,42 |
| **Tamaño 1,5: principal** | 30 | **−7,88** | [−25,03; 9,47] | 0,37 |
| Tamaño 1,5, costo ajustado (+30 bps) | 30 | −6,66 | [−23,78; 10,99] | 0,38 |
| Tamaño 1,5, sin días bajo el 95 % | 25 | −5,06 | [−23,50; 14,76] | 0,51 |

**Cómo se calcula:**
- **Costo ajustado** = slippage × cumplimiento + 30 × (1 − cumplimiento). Las acciones no ejecutadas se cobran a 30 bps, como en el plan de análisis (Anexo D).
- **Promedio por orden y semilla:** controla que las 90 corridas no sean del todo independientes, porque la misma orden y semilla aparecen en las tres profundidades.
- **«Sin días bajo el 95 %»:** quita los días en que alguna estrategia ejecutó menos del 95 % de la orden.

**Resultado:**
- **Con tamaño 1, ninguna variante cambia el resultado:** la diferencia queda entre −3,25 y −3,53 bps, sin significancia.
- **Con tamaño 1,5, quitar los 5 días bajo el 95 % baja la ventaja de −7,88 a −5,06 bps.**
- **El costo ajustado no corrige eso:** cobra 30 bps por acción no comprada, menos que el costo medio de comprarla (≈ 50–60 bps), así que dejar saldo sigue saliendo barato.
- Las dos variantes del plan, sin MO-06 y promediando por orden y semilla, tampoco cambian el resultado.

## 7.7 Por tramo de inicio y por activo (descriptivo)

Estos cortes no estaban en el plan de análisis. Se informan como descripción.

**Tabla.** Diferencia sistema − TWAP por tramo de inicio y por activo en las 90 corridas con tamaño 1 (descriptivo).

| Corte (las 90 corridas, tamaño 1) | n | Sistema − TWAP | IC 95 % | Días en que el sistema cuesta menos |
|---|---|---|---|---|
| Apertura | 36 | +14,77 | [−3,09; 33,28] | 15 de 36 |
| Media jornada | 27 | +3,94 | [−20,75; 29,93] | 12 de 27 |
| **Cierre** | 27 | **−34,78** | [−56,12; −14,93] | 19 de 27 |
| FALABELLA | 36 | −32,17 | [−48,54; −17,51] | 26 de 36 |
| COPEC | 27 | +32,85 | [+10,30; +54,80] | 5 de 27 |
| ECL | 27 | −1,11 | [−25,16; 24,05] | 15 de 27 |

- **La ventaja del sistema se concentra en las órdenes de cierre.** El análisis de sensibilidad lo prueba: Kruskal-Wallis entre tramos, H = 8,98, p = 0,011. Por tramo (Wilcoxon con Holm por 3 pruebas): apertura p = 0,300 (Holm 0,600), media jornada p = 0,953 (Holm 0,953) y cierre p = 0,003 (Holm 0,009).
- **Tramo y activo están confundidos:** las tres órdenes de cierre (MO-08 a MO-10) son de FALABELLA, y COPEC no tiene órdenes de cierre. No se puede separar el efecto del cierre del efecto del activo.
- **El cierre favorece al sistema en parte por diseño:** el sistema tiene corrección del cierre y los benchmarks no.
- La lectura de estos cortes está en el Capítulo 8, sección 8.5.2.

## 7.8 Síntesis de los resultados

1. **Cumplimiento:** el sistema completa al menos el 95 % de la orden en 145 de 150 corridas. Las 5 excepciones son órdenes de cierre de FALABELLA, con ×0,25 o con el tamaño 1,5 (mínimo 78,4 %).
2. **Costo:** en las 90 corridas con tamaño 1, el sistema cuesta en promedio 3,34 bps menos que TWAP (58,61 contra 61,95 bps, −5,4 %). La diferencia no es significativa (Wilcoxon pareado, n = 90, p = 0,39) y el sistema gana en 46 de 90 días.
3. **Dispersión:** el costo del sistema varía menos que el de TWAP y VWAP en todas las profundidades. La diferencia es significativa (Pitman-Morgan, n = 90, p = 4,8·10⁻⁹; Capítulo 8, sección 8.3.2).
4. **Profundidad:** la diferencia va de −10,53 bps (×4) a +3,87 (×0,25), sin significancia en ninguna profundidad ni entre ellas.
5. **Tamaño:** todos cuestan más con órdenes más grandes, el sistema menos que TWAP y VWAP. La diferencia va de +2,20 (0,5) a −7,88 (1,5), sin significancia en ningún tamaño. La tendencia es significativa en el orden (Page, n = 30, p = 0,007), pero no en la magnitud (Wilcoxon de 0,5 a 1,5, p = 0,164). Con 1,5, parte de la ventaja viene de días incompletos.
6. **Tramo:** la mayor diferencia está en las órdenes de cierre (−34,78 bps), confundida con el activo (FALABELLA).
7. **Robustez:** con tamaño 1, las variantes de costo ajustado y sin días incompletos no cambian el resultado.

---

Elaborado por BF con apoyo de Claude Code (uso de IA autorizado por la universidad).
