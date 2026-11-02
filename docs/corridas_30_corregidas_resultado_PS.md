# 3.1.3: resultado oficial de las 30 corridas, con la corrección del cierre (31 de octubre)

**Elaborado por:** PS con apoyo de Claude Code.

**Datos:**
- `data/colab_resultados/corridas_30_completa/A/` y `B/`: el sistema con la corrección.
- `tabla/`: tabla, corridas, agregados y gráfico de cajas, armados en Colab con `scripts/consolidar_resultados_3_2_2.py`.

Los cuadernos `Colab_30corridas_corregidas_A` y `_B` los corrió PS en Colab con ABIDES. TWAP y VWAP son los de `data/colab_resultados/corridas_30/`: la corrección no los cambia.

**Este es el resultado oficial de la 3.1.3.** La versión sin la corrección queda como registro en `docs/corridas_30_resultado_PS.md`. La corrección está explicada en `docs/correccion_cierre_PS.md`.

## 1. Diseño

- **Sistema final:** Maestro entrenado (Poisson, 2.000 jornadas, λ = 0,02) y Ejecutor PPO `rimit` s1000.
  - Se evalúa muestreando la política, con impacto acumulado.
  - Usa `--completar-al-cierre`: la última decisión del día asigna todo lo que falta.
- **30 corridas:** 10 meta-órdenes (FALABELLA, COPEC y ECL; 4 en la apertura, 3 en media jornada y 3 en el cierre) × 3 semillas.
- **Comparación:** TWAP y VWAP, con las mismas órdenes, semillas e impacto.
- **Costo:** slippage en bps contra el precio de llegada.
- **Estadística:** diferencias pareadas por orden y semilla, con IC 95 % por bootstrap, Wilcoxon y t-test.
- **Escenario:** liquidez media.

## 2. Resultado

| Estrategia | Media (bps) | Mediana | Desv. estándar | Mejor | Peor | Cumplimiento |
|---|---:|---:|---:|---:|---:|---:|
| **Sistema final** | **35,8** | 38,5 | **90,8** | −232,9 | 183,6 | **1,00** (mínimo 0,97) |
| TWAP | 58,0 | 81,8 | 140,5 | −278,6 | 365,8 | 1,00 |
| VWAP | 61,0 | 83,9 | 148,8 | −278,6 | 391,9 | 1,00 |

| Diferencia pareada (30 pares) | bps (IC 95 %) | % | p Wilcoxon | p t-test |
|---|---|---:|---:|---:|
| **Sistema − TWAP** | **−22,1 [−50,0; +4,4]** | −38 % | 0,10 | 0,13 |
| **Sistema − VWAP** | **−25,1 [−56,9; +5,0]** | −41 % | 0,13 | 0,14 |

- El sistema cuesta menos que TWAP en **20 de 30 pares**. La mediana de la diferencia es −18,5 bps.
- **Ranking por costo medio:** sistema < TWAP < VWAP.

### Por meta-orden (media de 3 semillas, bps)

| Orden | Acción, tramo | Sistema | Sin la corrección | TWAP | Sistema − TWAP | Gana el sistema | Cumplimiento mínimo |
|---|---|---:|---:|---:|---:|---:|---:|
| MO-01 | FALABELLA, apertura | 28,3 | 28,3 | 11,3 | +17,0 | 1 de 3 | 1,00 |
| MO-02 | COPEC, apertura | 38,4 | 38,4 | 93,2 | −54,8 | 3 de 3 | 1,00 |
| MO-03 | COPEC, apertura | 25,1 | 25,1 | 42,6 | −17,5 | 3 de 3 | 1,00 |
| MO-04 | ECL, apertura | 30,5 | 30,5 | 41,4 | −10,9 | 2 de 3 | 1,00 |
| MO-05 | COPEC, media jornada | 39,9 | 40,0 | 41,3 | −1,5 | 2 de 3 | 1,00 |
| MO-06 | ECL, media jornada | 146,3 | 146,3 | 255,7 | −109,4 | 2 de 3 | 1,00 |
| MO-07 | ECL, media jornada | 50,8 | 50,7 | 49,1 | +1,7 | 2 de 3 | 1,00 |
| MO-08 | FALABELLA, cierre | 43,7 | 41,4 | 73,9 | −30,2 | 2 de 3 | **0,97** (antes 0,92) |
| MO-09 | FALABELLA, cierre | −8,3 | −14,7 | 8,7 | −17,0 | 2 de 3 | **0,98** (antes 0,91) |
| MO-10 | FALABELLA, cierre | −36,2 | −40,6 | −37,2 | +1,0 | 1 de 3 | **1,00** (antes 0,92) |

### Pruebas de robustez (cálculo aparte, bootstrap con 10.000 remuestreos)

| Subconjunto | n | Sistema − TWAP (IC 95 %) | p Wilcoxon |
|---|---:|---|---:|
| Todas | 30 | −22,1 [−50,0; +4,4] | 0,10 |
| Sin MO-06 (la diferencia más grande) | 27 | −12,5 [−34,6; +11,6] | 0,14 |
| Solo las órdenes del cierre | 9 | −15,4 [−43,1; +15,1] | 0,50 |

## 3. Qué cambió con la corrección

- **Cumplimiento:** las órdenes del cierre pasaron de 0,91–0,93 a 0,97–1,00. Todas las corridas cumplen ahora el mínimo del 95 %.
- **Costo en el cierre:** subió un poco (de 2 a 6 bps por orden), porque el sistema compra ahora el 6 a 8 % que antes quedaba sin comprar. Esta versión es la comparación justa contra TWAP y VWAP.
- **Las demás órdenes no cambian** (diferencias de menos de 1 bps).
- **Resultado global:** pasa de −23,5 a −22,1 bps contra TWAP. La conclusión es la misma.
- **Detalle:** en dos corridas (MO-08 s2 y MO-09 s3), el Ejecutor no alcanzó a comprar todo en la última ventana. Por eso el mínimo es 0,97 y no 1,00.

## 4. Conclusión

1. **En promedio, el sistema es más barato que TWAP (−22 bps, 38 %) y que VWAP (−25 bps, 41 %). Con 30 corridas, la diferencia no es significativa al 5 %:** los intervalos incluyen el 0 y p ≈ 0,10–0,14.
2. **El sistema es más estable:** su desviación es 91 bps, contra 140 de TWAP y 149 de VWAP, y su peor día costó la mitad. Evita los días muy caros y aprovecha menos los muy baratos.
3. **La ventaja depende en parte de una orden.** Sin MO-06, la diferencia baja a −12,5 bps.
4. **De dónde viene la ventaja (hipótesis, no medida):** el Ejecutor PPO solo no le gana a TWAP con límite (+1 bps en 300 semillas). La diferencia vendría sobre todo de cómo el Maestro reparte la compra en el día.

## 5. Qué significa para el Título I

- **La 3.1.3 está cumplida:** 30 corridas, media, desviación, IC 95 %, Wilcoxon, t-test y gráfico de cajas contra TWAP y VWAP, con todas las órdenes completas.
- **Frase para el informe:** "En 30 corridas en ABIDES, el sistema redujo el costo medio en 22 bps (38 %) respecto de TWAP, con IC 95 % de −50 a +4 bps (Wilcoxon p = 0,10). La diferencia no es significativa con 30 corridas; el sistema mostró además menor variabilidad entre jornadas."
- **Sprint 7:** con 90 corridas por escenario y la variación medida (≈ 79 bps en la diferencia), el IC sería de unos ±16 bps. Si el efecto se mantiene, ahí podría salir significativo. Hay que usar `--completar-al-cierre`.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
