# Eje de tamaño: factor 1,5 con profundidad ×1 (15 de noviembre)

**Responsable:** MR (desviación 12, diseño en estrella, asignado por BF el 12 nov). **Cuaderno:** `notebooks/Colab_tamanos_media_BF.ipynb`, partes A (MO-01 a MO-05) y B (MO-06 a MO-10) con `FACTOR_TAMANO = 1.5`.
**Datos:** `data/colab_resultados/tamanos/media_f1.5/`. **Consolidado en:** `data/analysis/3_2_2/tabla_tamanos.*` (la 3.2.2, `docs/consolidacion_3_2_2_BF.md`).

## 1. Qué es

Son las mismas 10 órdenes y semillas 4–6 que la ×1 de PS (`corridas_90/media`), multiplicadas por `--factor-tamano 1.5`: el 15 % del volumen del día, o el 7,5 % si parte en el cierre. Junto con el 0,5 (BF) y el 1,0 (PS) completan los tres puntos del eje de tamaño en profundidad ×1 (diseño en estrella).

## 2. Revisión de las corridas

| Chequeo | Resultado |
|---|---|
| Corridas | 90: 30 del sistema, 30 de TWAP y 30 de VWAP. Sin errores ni duplicados |
| Órdenes y semillas | MO-01 a MO-10 × semillas 4, 5 y 6. Son los mismos 30 días que la ×1 y el 0,5 |
| Firma | `escenario` media, `factor_liquidez` 1,0 (profundidad ×1), `factor_tamano` 1,5 en los 4 archivos y en cada corrida |
| Sistema | Firma igual a la de la ×1: mismo Maestro y Ejecutores (`sistema_final`), `seed_red` 1000, modo muestreo, `completar_al_cierre`, snapshot 2026-08-23, impacto $y = 0{,}5$ y $\tau = 120\text{ min}$ |
| Cumplimiento | Promedio: sistema 98 %, TWAP 99 %, VWAP 99 %. Siete corridas quedan bajo 95 % en órdenes de cierre (`MO-06` VWAP s6: 0,945; `MO-08` PPO s4: 0,829 y s6: 0,939; `MO-09` PPO s4: 0,784 y s5: 0,933; `MO-09` TWAP y VWAP s4: 0,831). Es esperable porque al cierre las órdenes representan ≈ 23 % del volumen restante; no se repiten y se informan también con el costo ajustado |

## 3. Resultado (slippage crudo y ajustado, profundidad ×1)

| Tamaño | n | Sistema | TWAP | VWAP | Sistema − TWAP | IC 95 % | Wilcoxon p | Sistema − VWAP | IC 95 % | Ranking |
|---|---|---|---|---|---|---|---|---|---|---|
| 0,5 (BF) | 30 | 38,63 | 36,43 | 36,68 | +2,20 | [−20,84; 25,72] | 0,95 | +1,95 | [−23,95; 28,71] | TWAP < VWAP < Sistema |
| 1,0 (PS) | 30 | 47,11 | 50,48 | 51,30 | −3,37 | [−26,15; 19,63] | 0,63 | −4,19 | [−30,31; 22,11] | Sistema < TWAP < VWAP |
| **1,5 (MR)** | **30** | **51,75** | **59,63** | **60,75** | **−7,88** | **[−25,03; 9,47]** | **0,37** | **−8,99** | **[−29,82; 11,44]** | **Sistema < TWAP < VWAP** |

* **Con el costo ajustado (+30 bps por volumen no ejecutado):** en el tamaño 1,5 el sistema pasa a 52,60 bps, TWAP a 59,27 bps y VWAP a 60,03 bps (`tabla_tamanos_ajustado.*`). La diferencia sigue siendo favorable al sistema: **−6,66 bps** frente a TWAP ([−23,78; 10,99], Wilcoxon $p = 0{,}38$) y **−7,42 bps** frente a VWAP ([−27,93; 12,88], $p = 0{,}36$).
* **Lectura del eje completo (0,5 → 1,0 → 1,5):**
  * A medida que crece el tamaño de la meta-orden (del 5 % al 15 % del volumen diario), el costo de las tres estrategias aumenta, como predice la ley de impacto de mercado ($\sqrt{q/V}$).
  * Sin embargo, el costo de TWAP y VWAP crece más rápido (+23,20 y +24,07 bps entre 0,5 y 1,5) que el del sistema PPO (+13,12 bps), por lo que la ventaja relativa del sistema mejora de forma monótona: **+2,20 → −3,37 → −7,88 bps** frente a TWAP.
  * Con $n = 30$ días, el IC 95 % en 1,5 aún incluye el 0 ($p = 0{,}37$), y el contraste formal de tendencia sobre este eje corresponde a la tarea 3.2.4 (análisis de sensibilidad).

## 4. Límites

- **Extrapolación:** el Maestro se entrenó con un solo tamaño (10 % y 5 % del día), por lo que el factor 1,5 queda fuera de su distribución de entrenamiento (desviación 12).
- **Cumplimiento en el cierre:** en órdenes de cierre con factor 1,5, la participación llega al ≈ 23 % del volumen remanente del tramo, lo que explica las caídas bajo 95 % tanto en el sistema como en TWAP/VWAP.
- **Sin interacción tamaño × profundidad:** este eje se mide solo en profundidad ×1 (diseño en estrella).
