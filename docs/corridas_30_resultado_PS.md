# 3.1.3: resultado de las 30 corridas de evaluación (30 de octubre)

**Elaborado por:** PS con apoyo de Claude Code.

**Datos:**
- `data/colab_resultados/corridas_30/bloque_1/` a `bloque_4/`: los JSON crudos.
- `tabla_final/`: la tabla, las corridas, los agregados y el gráfico de cajas que arma el cuaderno `Colab_30corridas_bloque4` con los cuatro bloques.

Los cuatro cuadernos los corrió PS en Colab con ABIDES. La tabla la genera `scripts/consolidar_resultados_3_2_2.py`. Los avances parciales están en `docs/corridas_30_avance_PS.md`.

> **Corrección pendiente (31 oct):** la causa del cumplimiento bajo en el cierre ya se encontró y se corrigió (`docs/correccion_cierre_PS.md`). Las corridas del sistema se repiten con la corrección en `Colab_30corridas_corregidas_A` y `_B`. Este documento queda como la versión **sin corrección**.

## 1. Diseño

- **Sistema evaluado:** el sistema final, elegido con reglas fijadas antes de ver estas corridas.
  - Maestro: entrenado en Poisson con 2.000 jornadas y λ = 0,02.
  - Ejecutor PPO: `rimit` s1000.
  - Se evalúa muestreando la política, con impacto acumulado entre ventanas.
- **Comparación:** TWAP y VWAP en las mismas órdenes, semillas e impacto.
- **30 corridas:** 10 meta-órdenes (MO-01 a MO-10, de `data/meta_ordenes/meta_ordenes_v2_candidata.json`) × 3 semillas.
  - Acciones: FALABELLA, COPEC y ECL.
  - Tramos de inicio: 4 órdenes en la apertura, 3 en media jornada y 3 en el cierre.
- **Costo:** slippage en bps contra el precio de llegada (menos es mejor).
- **Estadística:** diferencias pareadas por orden y semilla, con IC 95 % por bootstrap, Wilcoxon y t-test.
- **Escenario:** liquidez media. Los escenarios baja y alta van en el Sprint 7.

## 2. Resultado

| Estrategia | Media (bps) | Mediana | Desv. estándar | Mejor | Peor | Cumplimiento |
|---|---:|---:|---:|---:|---:|---:|
| **Sistema final** | **34,5** | 38,2 | **88,5** | −223,9 | 183,0 | 0,98 |
| TWAP | 58,0 | 81,8 | 140,5 | −278,6 | 365,8 | 1,00 |
| VWAP | 61,0 | 83,9 | 148,8 | −278,6 | 391,9 | 1,00 |

| Diferencia pareada (30 pares) | bps (IC 95 %) | % | p Wilcoxon | p t-test |
|---|---|---:|---:|---:|
| **Sistema − TWAP** | **−23,5 [−51,3; +3,8]** | −40 % | 0,08 | 0,12 |
| **Sistema − VWAP** | **−26,4 [−58,2; +4,1]** | −43 % | 0,10 | 0,12 |

- El sistema cuesta menos que TWAP en **21 de 30 pares**. La mediana de la diferencia es −19,2 bps.
- **Ranking por costo medio:** sistema < TWAP < VWAP.

### Por meta-orden (media de 3 semillas, bps)

| Orden | Acción, tramo | Sistema | TWAP | Sistema − TWAP | Gana el sistema | Cumplimiento del sistema |
|---|---|---:|---:|---:|---:|---:|
| MO-01 | FALABELLA, apertura | 28,3 | 11,3 | +17,0 | 1 de 3 | 1,00 |
| MO-02 | COPEC, apertura | 38,4 | 93,2 | −54,8 | 3 de 3 | 1,00 |
| MO-03 | COPEC, apertura | 25,1 | 42,6 | −17,5 | 3 de 3 | 1,00 |
| MO-04 | ECL, apertura | 30,5 | 41,4 | −10,9 | 2 de 3 | 1,00 |
| MO-05 | COPEC, media jornada | 40,0 | 41,3 | −1,4 | 2 de 3 | 1,00 |
| MO-06 | ECL, media jornada | 146,3 | 255,7 | −109,4 | 2 de 3 | 1,00 |
| MO-07 | ECL, media jornada | 50,7 | 49,1 | +1,6 | 2 de 3 | 1,00 |
| MO-08 | FALABELLA, cierre | 41,4 | 73,9 | −32,5 | 2 de 3 | **0,92** |
| MO-09 | FALABELLA, cierre | −14,7 | 8,7 | −23,4 | 2 de 3 | **0,91** |
| MO-10 | FALABELLA, cierre | −40,6 | −37,2 | −3,4 | 2 de 3 | **0,92** |

### Pruebas de robustez (cálculo aparte, bootstrap con 10.000 remuestreos)

| Subconjunto | n | Sistema − TWAP (IC 95 %) |
|---|---:|---|
| Todas | 30 | −23,5 [−51,3; +3,8] |
| Sin las órdenes del cierre (cumplimiento bajo el 95 %) | 21 | −25,1 [−61,7; +12,3] (Wilcoxon p = 0,16) |
| Sin MO-06 (la diferencia más grande) | 27 | −13,9 [−36,8; +10,6] |

## 3. Conclusión

1. **El sistema es más barato en promedio que TWAP y VWAP, pero con 30 corridas la diferencia no es significativa al 5 %.**
   - Los intervalos incluyen el 0.
   - Wilcoxon da p = 0,08 contra TWAP y 0,10 contra VWAP.
   - La dirección se mantuvo en los tres cortes: −18 bps con 9 corridas, −26 con 24 y −23 con 30.
2. **El sistema varía menos de un día a otro.** Su desviación es 88 bps, contra 140 de TWAP y 149 de VWAP. Evita los días muy caros (su peor día fue 183 bps; el de TWAP, 366) y también aprovecha menos los muy baratos.
3. **El tamaño del efecto es grande, pero incierto.** La reducción puntual es del 40 % respecto de TWAP. Con la variación medida (desviación de la diferencia ≈ 80 bps), harían falta unos 45 pares para que el IC excluya el 0, si la diferencia observada se mantiene. Para tener un 80 % de probabilidad de detectarla, harían falta unos 90. Es una estimación aproximada con la desviación medida.
4. **Defecto encontrado:** en las tres órdenes que empiezan al cierre, el sistema compra solo el 91 a 92 % de la orden. Esto no cumple el umbral del 95 %.
   - Ahí el slippage del sistema no es del todo comparable, porque el costo de la parte que no se compró no entra en la cuenta.
   - Sin esas órdenes el resultado casi no cambia (−25 bps), así que no explica la ventaja. Pero hay que corregirlo antes del Sprint 7.
   - **Causa (revisada después en el código, `docs/correccion_cierre_PS.md`):** con 4 decisiones y α ≤ 0,5, el tope es 93,75 %. El Maestro eligió α = 0,5 en todas.
5. **De dónde viene la ventaja (hipótesis):** el Ejecutor PPO solo no le gana a TWAP con órdenes límite (+1 bps en 300 semillas). Por eso, la diferencia vendría sobre todo de cómo el Maestro reparte la compra en el día.

## 4. Qué significa para el Título I

- **Lo que pide la 3.1.3 está cumplido:** 30 corridas, media, desviación, IC 95 %, Wilcoxon, t-test y gráfico de cajas contra TWAP y VWAP.
- **Para el objetivo de reducir el slippage**, el informe debe decir: "el sistema redujo el costo medio en ≈ 23 bps (40 %) respecto de TWAP, con IC 95 % de −51 a +4 bps; la diferencia no es significativa con 30 corridas". No debe presentarse como una reducción demostrada.
- **Para el Sprint 7:** con 90 corridas por escenario, el IC sería de unos ±17 bps. Si el efecto se mantiene, ahí podría salir significativo. Antes conviene corregir el cumplimiento en el cierre, para que las corridas sean comparables.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
