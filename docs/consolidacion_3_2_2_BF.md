# Consolidación de resultados 3.2.2 (12 de noviembre; completa el 15 de noviembre)

**Responsable:** BF (3.2.2, Sprint 7). El borrador del script es de PS (29 oct); BF lo revisó y lo amplió como dueño.
**Script:** `scripts/consolidar_resultados_3_2_2.py`. **Salidas:** `data/analysis/3_2_2/`. **Tests:** `tests/test_consolidar_resultados_3_2_2.py`.

**Estado: completa.** Tiene las tres profundidades del market maker:
- ×4, de BF (PR #51);
- ×1, de PS;
- ×0,25, de MR (PR #57).

Tiene también los tamaños 0,5 (BF, PR #56) y 1,5 (MR, PR #59). Son 450 corridas. El 20 nov se verificó que el comando de la sección 7 reproduce exacto todo `data/analysis/3_2_2/` desde los JSON de main.

## 1. Qué pide la tarea y qué hay

| Criterio de terminado (Tareas del Sprint 7) | Dónde está |
|---|---|
| Revisar y aprobar el borrador de PS | Revisado; ampliado en las secciones 3 a 5 (PR #54) |
| Correrlo con las 90 | Las 90 por estrategia: ×4, ×1 y ×0,25, con 30 cada una |
| Tabla matriz por escenario en CSV y LaTeX: IS del sistema, TWAP y VWAP, diferencia %, ranking | `tabla_90.{csv,md,tex}` (crudo) y `tabla_90_ajustado.*` |
| Media, mediana, peor y mejor | `agregados_por_escenario.csv` (y `agregados.csv`, global de tamaño 1) |
| Chequeo de calidad: 90 corridas leídas, sin duplicados, cumplimiento informado | `calidad.{json,md}`: OK |
| Probado con las 30 del Sprint 6 | Sección 6 |

## 2. Criterios (fijados por BF el 12 nov, antes de consolidar las 90)

1. **Costo:** se informa el **crudo** y el **ajustado** (+30 bps por acción no ejecutada), como pide `docs/plan_analisis_3_2_3_PS.md` y como en la 3.1.3. El ajuste es débil: si el slippage supera 30 bps, dejar saldo sigue saliendo barato. Por eso el crudo es la tabla principal.
2. **Corridas bajo el 95 % de cumplimiento:** se mantienen, se listan en el chequeo de calidad y se agrega una fila de robustez sin esos días. Repetirlas da lo mismo, porque la semilla fija el día.
3. **Diferencia %:** cociente de medias, 100 × media(sistema − referencia) / |media(referencia)|. El promedio de % por corrida no sirve, porque hay costos negativos (hasta −405 bps).
4. **Tamaños (desviación 12):** van en una tabla aparte (`tabla_tamanos.*`). La tabla global usa solo el tamaño 1, para no contar dos veces la ×1.

**Nombres:** desde el C-6c, los escenarios se informan como **profundidad del market maker ×4 / ×1 / ×0,25** (desviación 10). Los archivos siguen usando `baja`, `media` y `alta`; la tabla agrega la columna `profundidad_mm`.

## 3. Cómo se calcula el costo de cada corrida

El script no recalcula nada: usa el `slippage_bps` que guarda cada evaluador, calculado por `evaluate_episode` (`src/analysis/execution_metrics.py`, función `slippage_bps`, líneas 50–57): (precio medio ejecutado − precio de llegada) / precio de llegada × 10.000. Positivo = costo. Las diferencias son pareadas por día (escenario, orden y semilla), con IC 95 % por bootstrap (3.000 remuestreos, semilla 0), Wilcoxon y t pareados.

## 4. Chequeo de calidad: OK

| Bloque | Corridas por estrategia | Días pareados | Duplicados | Errores | Bajo 95 % |
|---|---|---|---|---|---|
| ×4 (`baja`) | 30 / 30 / 30 | 30 | 0 | 0 | MO-09 s4: TWAP y VWAP 87,1 % |
| ×1 (`media`) | 30 / 30 / 30 | 30 | 0 | 0 | MO-09 s4: TWAP y VWAP 87,1 % |
| ×0,25 (`alta`) | 30 / 30 / 30 | 30 | 0 | 0 | MO-08 s4: **sistema 94,7 %**; MO-09 s4: TWAP y VWAP 87,1 % |
| ×1, tamaño 0,5 | 30 / 30 / 30 | 30 | 0 | 0 | Ninguna |
| ×1, tamaño 1,5 | 30 / 30 / 30 | 30 | 0 | 0 | **Sistema:** MO-08 s4 82,9 %, MO-08 s6 93,9 %, MO-09 s4 78,4 % y MO-09 s5 93,3 %. **TWAP:** MO-09 s4 83,1 %. **VWAP:** MO-09 s4 83,1 % y MO-06 s6 94,5 % |

Son 450 corridas.

**El sistema no completa siempre.**
- **Tamaño 1:** completa el 100 % con la ×4. El mínimo es 98,6 % con la ×1 y 94,7 % con la ×0,25.
- **Tamaño 1,5:** queda bajo el 95 % en 4 días de cierre de FALABELLA, con un mínimo de 78,4 %. En esos días completa menos que TWAP.

## 5. Resultados

### 5.1 Por profundidad y global (slippage crudo, tamaño 1)

| Bloque | n | Sistema | TWAP | VWAP | Sistema − TWAP | IC 95 % | Wilcoxon p | Dif. % | Sistema − VWAP | IC 95 % | Ranking |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ×4 | 30 | 59,51 | 70,05 | 69,15 | −10,53 | [−33,09; 11,79] | 0,44 | −15,0 % | −9,64 | [−33,76; 14,52] | Sistema < VWAP < TWAP |
| ×1 | 30 | 47,11 | 50,48 | 51,30 | −3,37 | [−26,15; 19,63] | 0,63 | −6,7 % | −4,19 | [−30,31; 22,11] | Sistema < TWAP < VWAP |
| ×0,25 | 30 | 69,19 | 65,33 | 64,79 | +3,87 | [−16,56; 25,30] | 0,87 | +5,9 % | +4,41 | [−20,42; 30,85] | VWAP < TWAP < Sistema |
| **Global** | 90 | 58,61 | 61,95 | 61,75 | **−3,34** | [−15,69; 9,67] | 0,39 | −5,4 % | −3,14 | [−17,50; 11,87] | Sistema < VWAP < TWAP |
| Global sin días bajo 95 % | 86 | 59,60 | 62,85 | 62,64 | −3,25 | [−16,56; 10,48] | 0,42 | −5,2 % | −3,04 | [−18,02; 12,77] | Sistema < VWAP < TWAP |

- **Con el costo ajustado** (`tabla_90_ajustado.*`), la global queda en −3,53 [−15,93; 9,47] contra TWAP y −3,06 contra VWAP. Corrige el −3,31 / −2,99 que decía este documento el 14 nov.
- **Lectura:**
  - En promedio, el sistema cuesta 3,3 bps menos que TWAP en las 90, pero el IC incluye el 0.
  - La ventaja se achica al bajar la profundidad del market maker: −10,5 con ×4, −3,4 con ×1 y +3,9 con ×0,25.
  - Ningún IC excluye el 0.
  - Las pruebas formales entre escenarios (Kruskal-Wallis, Friedman, Holm) están en la 3.2.3 de PS (`docs/comparacion_estadistica_3_2_3_PS.md`).

### 5.2 Por estrategia (`agregados_por_escenario.csv`, tamaño 1)

| Profundidad | Estrategia | Media | Mediana | Peor | Mejor | Cumplimiento mínimo |
|---|---|---|---|---|---|---|
| ×4 | Sistema | 59,51 | 32,45 | 344,51 | −263,04 | 1,000 |
| ×4 | TWAP | 70,05 | 44,74 | 522,69 | −323,03 | 0,871 |
| ×4 | VWAP | 69,15 | 43,90 | 522,69 | −323,03 | 0,871 |
| ×1 | Sistema | 47,11 | 38,04 | 285,58 | −311,76 | 0,986 |
| ×1 | TWAP | 50,48 | 38,13 | 386,76 | −377,94 | 0,871 |
| ×1 | VWAP | 51,30 | 38,84 | 386,76 | −377,94 | 0,871 |
| ×0,25 | Sistema | 69,19 | 50,16 | 404,54 | −324,75 | 0,947 |
| ×0,25 | TWAP | 65,33 | 56,33 | 376,10 | −329,12 | 0,871 |
| ×0,25 | VWAP | 64,79 | 50,96 | 402,45 | −329,12 | 0,871 |
| **Las 90** | Sistema | 58,61 | 40,10 | 404,54 | −324,75 | 0,947 |
| **Las 90** | TWAP | 61,95 | 45,10 | 522,69 | −377,94 | 0,871 |
| **Las 90** | VWAP | 61,75 | 45,94 | 522,69 | −377,94 | 0,871 |

### 5.3 Eje de tamaño (`tabla_tamanos.*`, profundidad ×1)

| Tamaño | n | Sistema | TWAP | VWAP | Sistema − TWAP | IC 95 % | Wilcoxon p | Sistema − VWAP | Ranking |
|---|---|---|---|---|---|---|---|---|---|
| 0,5 (BF) | 30 | 38,63 | 36,43 | 36,68 | +2,20 | [−20,84; 25,72] | 0,95 | +1,95 | TWAP < VWAP < Sistema |
| 1 (PS) | 30 | 47,11 | 50,48 | 51,30 | −3,37 | [−26,15; 19,63] | 0,63 | −4,19 | Sistema < TWAP < VWAP |
| 1,5 (MR) | 30 | 51,75 | 59,63 | 60,75 | −7,88 | [−25,03; 9,47] | 0,37 | −8,99 | Sistema < TWAP < VWAP |

- **Las tres estrategias cuestan más con la orden más grande,** pero TWAP y VWAP suben más que el sistema. Por eso, sistema − TWAP pasa de +2,20 a −3,37 y a −7,88. Ningún IC excluye el 0.
- **Costo ajustado:** con 1,5, −6,66 [−23,78; 10,99].
- **Descriptivo, calculado el 20 nov y fuera del plan:** con el tamaño 1,5, sin los 5 días bajo el 95 %, sistema − TWAP = **−5,06** [−23,50; 14,76] (n = 25).
  - Parte de la ventaja con 1,5 viene de días en que el sistema deja saldo sin ejecutar. El ajuste de +30 bps no lo corrige (criterio 1).
  - La tendencia por tamaño se mantiene, pero más débil.
- Detalle en `docs/tamanos_media_f05_resultado_BF.md` y `docs/tamanos_media_f15_resultado_MR.md`. El contraste de tendencia es de la 3.2.4 (MR).

### 5.4 Por tramo y por activo (descriptivo; NO está en el plan de análisis)

| Corte (las 90, tamaño 1) | n | Sistema − TWAP | IC 95 % | Gana el sistema |
|---|---|---|---|---|
| Apertura | 36 | +14,77 | [−3,09; 33,28] | 15/36 |
| Media jornada | 27 | +3,94 | [−20,75; 29,93] | 12/27 |
| Cierre | 27 | **−34,78** | [−56,12; −14,93] | 19/27 |
| FALABELLA | 36 | −32,17 | [−48,54; −17,51] | 26/36 |
| COPEC | 27 | +32,85 | [+10,30; +54,80] | 5/27 |
| ECL | 27 | −1,11 | [−25,16; 24,05] | 15/27 |

- **Tramo y activo están confundidos.** Las tres órdenes de cierre son de FALABELLA (MO-08 a MO-10), así que buena parte del «FALABELLA −32» es el efecto del cierre. COPEC no tiene órdenes de cierre.
- **El cierre favorece al sistema en parte por diseño:** el sistema tiene corrección del cierre y los benchmarks no.
- Son 6 cortes sin corrección por comparaciones múltiples y elegidos sin plan previo. Sirven para la discusión (capítulo 8 de PS), no para concluir.

## 6. Validación

- **Con las 30 corridas del Sprint 6** (`corridas_30_completa`, con los benchmarks de `corridas_30/bloque_1..4`), `tabla_maestra.md` sale **idéntica** a la publicada. Los CSV solo difieren en el decimal 16. `corridas.csv` agrega la columna `factor_liquidez`.
- **La 3.2.3 de PS** (`scripts/comparacion_estadistica_3_2_3.py`) da los mismos números con el `corridas.csv` nuevo: solo cambian el título y la ruta de entrada.
- **Reproducción completa (20 nov):** el comando de la sección 7 sobre `origin/main` (`3641290`) regenera los 24 archivos de `data/analysis/3_2_2/` idénticos a los versionados.
- Los cuadernos que llaman al script (`Colab_90corridas_*`, `Colab_30corridas_*`, `Colab_tamanos_media_BF`) siguen funcionando: la tabla maestra no cambia y lo nuevo son archivos adicionales.

## 7. Cómo volver a correrla (un solo comando)

```bash
python scripts/consolidar_resultados_3_2_2.py \
  --entradas data/colab_resultados/corridas_90/baja/A data/colab_resultados/corridas_90/baja/B \
             data/colab_resultados/corridas_90/media/A data/colab_resultados/corridas_90/media/B \
             data/colab_resultados/corridas_90/alta/A data/colab_resultados/corridas_90/alta/B \
             data/colab_resultados/tamanos/media_f0.5/A data/colab_resultados/tamanos/media_f0.5/B \
             data/colab_resultados/tamanos/media_f1.5/A data/colab_resultados/tamanos/media_f1.5/B \
  --sistema PPO_sistema --ajustado-bps 30 --out-dir data/analysis/3_2_2
python -m pytest tests/test_consolidar_resultados_3_2_2.py -q
```

## 8. Límites

- **Poca potencia.** La desviación estándar de las diferencias pareadas sistema − TWAP es ≈ 61–68 bps por bloque. Con 80 % de potencia y α = 0,05 se detectarían diferencias de unos 31–35 bps por bloque (n = 30) y de unos 19 bps en la global (n = 90). Las diferencias observadas (−3 a −11 bps) están muy por debajo.
- **Corridas bajo el 95 %:** están en la tabla principal y la fila de robustez muestra que no cambian la conclusión global. En el tamaño 1,5 sí cambian la magnitud (sección 5.3).
- **Cambio del 13 nov:** con varios tamaños en las entradas, `agregados.csv`, «Por estrategia» de `tabla_maestra.md` y `cajas.png` usan solo el tamaño 1 (criterio 4). Con un solo tamaño, como en los cuadernos, no cambia nada.
- **Las cajas:** `cajas.png` junta las tres profundidades. Las cajas por profundidad están en `corridas_90/*/tabla/cajas.png`, cada una con su propia escala.
- **Los cortes** por tramo y activo son descriptivos y están confundidos entre sí (sección 5.4).
- **Registro:** la bitácora del proyecto (`docs/bitacora_cambios_PS.md`) es de PS. Este cambio se registra aquí y en el HANDOFF.

---

Elaborado por BF con apoyo de Claude Code (uso de IA autorizado por la universidad).
