# Eje de tamaño: factor 0,5 con profundidad ×1 (13 de noviembre)

**Responsable:** BF (desviación 12, diseño en estrella, aprobado el 11 nov). **Cuaderno:** `notebooks/Colab_tamanos_media_BF.ipynb`, partes A (MO-01 a MO-05) y B (MO-06 a MO-10).
**Datos:** `data/colab_resultados/tamanos/media_f0.5/`. **Consolidado en:** `data/analysis/3_2_2/tabla_tamanos.*` (la 3.2.2, `docs/consolidacion_3_2_2_BF.md`).

## 1. Qué es

Son las mismas 10 órdenes y semillas 4–6 que la ×1 de PS (`corridas_90/media`), con cada orden a la mitad (`--factor-tamano 0.5`): el 5 % del volumen del día, o el 2,5 % si parte en el cierre. Junto con la ×1 forman el eje de tamaño. Falta el 1,5 (por asignar; se propuso MR).

## 2. Revisión de las corridas

| Chequeo | Resultado |
|---|---|
| Corridas | 90: 30 del sistema, 30 de TWAP y 30 de VWAP. Sin errores ni duplicados |
| Órdenes y semillas | MO-01 a MO-10 × semillas 4, 5 y 6. Son los mismos 30 días que la ×1 |
| Firma | `escenario` media, `factor_liquidez` 1,0 (profundidad ×1), `factor_tamano` 0,5 en los 4 archivos y en cada corrida |
| Cantidades | Cada orden mide exactamente la mitad que en la ×1 (`Q_total` 0,5 / 1 = 0,500 en los 90 pares) |
| Sistema | Firma igual a la de la ×1: mismo Maestro y Ejecutores (`sistema_final`), `seed_red` 1000, modo muestreo, `completar_al_cierre`, snapshot 2026-08-23, impacto y = 0,5 y τ = 120 min |
| Cumplimiento | Todas las corridas sobre el 95 %. Mínimo: sistema 1,000; TWAP y VWAP 0,993. MO-09 con semilla 4, que con tamaño 1 quedaba en 87,1 %, con 0,5 completa |
| Archivos | UTF-8 sin BOM |

## 3. Resultado (slippage crudo contra el precio de llegada, profundidad ×1)

| Tamaño | n | Sistema | TWAP | VWAP | Sistema − TWAP | IC 95 % | Wilcoxon p | Sistema − VWAP | IC 95 % | Ranking |
|---|---|---|---|---|---|---|---|---|---|---|
| **0,5** | 30 | 38,63 | 36,43 | 36,68 | **+2,20** | [−20,84; 25,72] | 0,95 | +1,95 | [−23,95; 28,71] | TWAP < VWAP < Sistema |
| 1 (PS) | 30 | 47,11 | 50,48 | 51,30 | −3,37 | [−26,15; 19,63] | 0,63 | −4,19 | [−30,31; 22,11] | Sistema < TWAP < VWAP |

- **Con el tamaño 0,5 el sistema no le gana a TWAP ni a VWAP:** cuesta 2,2 bps más en promedio, con un IC que incluye el 0. Con el tamaño 1 tampoco había diferencia significativa (−3,37). Se informa tal cual.
- **El costo ajustado (+30 bps) da lo mismo** (+2,20 y +1,96), porque todas las corridas completan.

### 3.1 Descriptivo, fuera del plan de análisis

Estas cuentas se hicieron después de ver la tabla y no están en `docs/plan_analisis_3_2_3_PS.md`. Sirven para la discusión (capítulo 7) y para la 3.2.4, no para concluir.

| Efecto de pasar del tamaño 1 al 0,5, pareado por orden y semilla | Media | IC 95 % |
|---|---|---|
| Sistema | −8,48 | [−13,01; −3,72] |
| TWAP | −14,04 | [−16,84; −10,59] |
| VWAP | −14,62 | [−17,51; −11,01] |
| (Sistema − TWAP) con 0,5 menos (Sistema − TWAP) con 1 | +5,57 | [−0,44; 11,61] |

- **Una orden más chica cuesta menos para las tres estrategias.** Es lo esperable con el impacto √(q/V).
- **Los benchmarks bajan más que el sistema**, y por eso la ventaja de −3,37 pasa a +2,20. La diferencia entre las dos diferencias queda en el borde (el IC toca el 0).
- **Hipótesis, sin probar:** el Maestro se entrenó con un solo tamaño (10 % y 5 % del día). Con la mitad de la orden, el impacto que su calendario busca evitar pesa menos, y el ruido del precio en el horizonte pesa más.
- **Por tramo, con el tamaño 0,5:**
  - cierre −21,04 [−59,69; 23,08], el sistema gana 7 de 9;
  - apertura +16,33 [−15,53; 51,44], gana 6 de 12;
  - media jornada +6,60, gana 4 de 9.

  Es el mismo patrón que con el tamaño 1, más débil. Tramo y activo siguen confundidos (las órdenes de cierre son todas de FALABELLA).

## 4. Cambio en la consolidación

Con un segundo tamaño en las entradas, `agregados.csv`, la sección «Por estrategia» de `tabla_maestra.md` y `cajas.png` mezclaban las 30 corridas del 0,5 con las 60 del tamaño 1. Se aplicó el **criterio 4 de la 3.2.2**, fijado antes de consolidar (el eje de tamaño va aparte): cuando hay varios tamaños, esas salidas usan solo el tamaño 1 y lo dicen en el título (`base_global` en `scripts/consolidar_resultados_3_2_2.py`). Con un solo tamaño, como en los cuadernos de Colab, no cambia nada. La tabla de las 90 y los cortes ya usaban solo el tamaño 1, así que sus números no se mueven.

## 5. Límites

- **Es un eje de 2 puntos de 3:** falta el 1,5. Con dos tamaños no se puede hablar de tendencia.
- **El tamaño 0,5 queda fuera de lo que vio el Maestro** al entrenarse (desviación 12).
- **30 días y una sola profundidad (×1):** no dice nada de la interacción entre tamaño y profundidad.
- **Las pruebas de la sección 3.1 son descriptivas**, sin corrección por comparaciones múltiples.

---

Elaborado por BF con apoyo de Claude Code (uso de IA autorizado por la universidad).
