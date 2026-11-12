# Consolidación de resultados 3.2.2 (12 de noviembre)

**Responsable:** BF (3.2.2, Sprint 7). El borrador del script es de PS (29 oct); BF lo revisó y lo amplió como dueño.
**Script:** `scripts/consolidar_resultados_3_2_2.py`. **Salidas:** `data/analysis/3_2_2/`. **Tests:** `tests/test_consolidar_resultados_3_2_2.py`.

**Estado: hecha con dos de las tres profundidades (×4 y ×1).** Falta la ×0,25 (MR). Cuando llegue, la consolidación se vuelve a correr con el comando de la sección 7, sin cambiar nada.

## 1. Qué pide la tarea y qué hay

| Criterio de terminado (Tareas del Sprint 7) | Dónde está |
|---|---|
| Revisar y aprobar el borrador de PS | Revisado; ampliado en las secciones 3 a 5 |
| Correrlo con las 90 | Con 60 de las 90 por estrategia (×4 y ×1). Falta la ×0,25 |
| Tabla matriz por escenario en CSV y LaTeX: IS del sistema, TWAP y VWAP, diferencia %, ranking | `tabla_90.{csv,md,tex}` (crudo) y `tabla_90_ajustado.*` |
| Media, mediana, peor y mejor | `agregados_por_escenario.csv` (y `agregados.csv`, global) |
| Chequeo de calidad: corridas leídas, sin duplicados, cumplimiento informado | `calidad.{json,md}` |
| Probado con las 30 del Sprint 6 | Sección 6 |

## 2. Criterios (fijados por BF el 12 nov, antes de consolidar las 90)

1. **Costo:** se informa el **crudo** y el **ajustado** (+30 bps por acción no ejecutada), como pide `docs/plan_analisis_3_2_3_PS.md` y como en la 3.1.3. El ajuste es débil: si el slippage supera 30 bps, dejar saldo sigue saliendo barato. Por eso el crudo es la tabla principal.
2. **Corridas bajo el 95 % de cumplimiento:** se mantienen, se listan en el chequeo de calidad y se agrega una fila de robustez sin esos días. Repetirlas da lo mismo, porque la semilla fija el día.
3. **Diferencia %:** cociente de medias, 100 × media(sistema − referencia) / |media(referencia)|. El promedio de % por corrida no sirve, porque hay costos negativos (hasta −378 bps).
4. **Tamaños (desviación 12):** en una tabla aparte (`tabla_tamanos.*`). La tabla global usa solo el tamaño 1, para no contar dos veces la ×1.

**Nombres:** desde el C-6c, los escenarios se informan como **profundidad del market maker ×4 / ×1 / ×0,25** (desviación 10). Los archivos siguen usando `baja`, `media` y `alta`; la tabla agrega la columna `profundidad_mm`.

## 3. Cómo se calcula el costo de cada corrida

El script no recalcula nada: usa el `slippage_bps` que guarda cada evaluador, calculado por `evaluate_episode` (`src/analysis/execution_metrics.py`, función `slippage_bps`, líneas 50–57): (precio medio ejecutado − precio de llegada) / precio de llegada × 10.000. Positivo = costo. Las diferencias son pareadas por día (escenario, orden y semilla), con IC 95 % por bootstrap (3.000 remuestreos, semilla 0), Wilcoxon y t pareados.

## 4. Chequeo de calidad: OK

| Profundidad | Corridas por estrategia | Días pareados | Duplicados | Errores | Bajo 95 % |
|---|---|---|---|---|---|
| ×4 (`baja`) | 30 / 30 / 30 | 30 | 0 | 0 | MO-09 semilla 4: TWAP y VWAP 87,1 % |
| ×1 (`media`) | 30 / 30 / 30 | 30 | 0 | 0 | MO-09 semilla 4: TWAP y VWAP 87,1 % |

El sistema completa siempre (mínimo 98,6 %, en ×1).

## 5. Resultados

### 5.1 Por profundidad y global (slippage crudo, tamaño 1)

| Bloque | n | Sistema | TWAP | VWAP | Sistema − TWAP | IC 95 % | Wilcoxon p | Dif. % | Sistema − VWAP | IC 95 % | Ranking |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ×4 | 30 | 59,51 | 70,05 | 69,15 | −10,53 | [−33,09; 11,79] | 0,44 | −15,0 % | −9,64 | [−33,76; 14,52] | Sistema < VWAP < TWAP |
| ×1 | 30 | 47,11 | 50,48 | 51,30 | −3,37 | [−26,15; 19,63] | 0,63 | −6,7 % | −4,19 | [−30,31; 22,11] | Sistema < TWAP < VWAP |
| **Global** | 60 | 53,31 | 60,26 | 60,23 | **−6,95** | [−23,01; 9,35] | 0,36 | −11,5 % | −6,91 | [−24,47; 11,19] | Sistema < VWAP < TWAP |
| Global sin días bajo 95 % | 58 | 53,68 | 61,24 | 61,20 | −7,56 | [−23,79; 9,59] | 0,34 | −12,4 % | −7,52 | [−25,45; 11,39] | Sistema < VWAP < TWAP |

- **Con el costo ajustado** (`tabla_90_ajustado.*`) casi nada cambia: global −6,91 contra TWAP y −6,62 contra VWAP.
- **Lectura:** en promedio el sistema cuesta menos que TWAP y VWAP en las dos profundidades, pero ningún IC excluye el 0. El test principal de la 3.2.3 (las 90 juntas, Wilcoxon) lo hace PS cuando esté la ×0,25.

### 5.2 Por estrategia (`agregados_por_escenario.csv`)

| Profundidad | Estrategia | Media | Mediana | Peor | Mejor | Cumplimiento mínimo |
|---|---|---|---|---|---|---|
| ×4 | Sistema | 59,51 | 32,45 | 344,51 | −263,04 | 1,000 |
| ×4 | TWAP | 70,05 | 44,74 | 522,69 | −323,03 | 0,871 |
| ×4 | VWAP | 69,15 | 43,90 | 522,69 | −323,03 | 0,871 |
| ×1 | Sistema | 47,11 | 38,04 | 285,58 | −311,76 | 0,986 |
| ×1 | TWAP | 50,48 | 38,13 | 386,76 | −377,94 | 0,871 |
| ×1 | VWAP | 51,30 | 38,84 | 386,76 | −377,94 | 0,871 |

### 5.3 Por tramo y por activo (descriptivo; NO está en el plan de análisis)

| Corte (×4 y ×1 juntas) | n | Sistema − TWAP | IC 95 % | Gana el sistema |
|---|---|---|---|---|
| Apertura | 24 | +13,92 | [−8,33; 36,98] | 11/24 |
| Media jornada | 18 | +1,52 | [−26,13; 29,65] | 7/18 |
| Cierre | 18 | **−43,23** | [−73,25; −14,50] | 13/18 |
| FALABELLA | 24 | −38,09 | [−61,12; −15,96] | 18/24 |
| COPEC | 18 | +28,71 | [+0,26; +55,78] | 4/18 |
| ECL | 18 | −1,09 | [−27,37; 26,95] | 9/18 |

- **Tramo y activo están confundidos.** Las tres órdenes de cierre son de FALABELLA (MO-08 a MO-10), así que buena parte del «FALABELLA −38» es el efecto del cierre. COPEC no tiene órdenes de cierre.
- **El cierre favorece al sistema en parte por diseño:** el sistema tiene corrección del cierre y los benchmarks no.
- Son 6 cortes sin corrección por comparaciones múltiples y elegidos sin plan previo. Sirven para la discusión del capítulo 7, no para concluir.

## 6. Validación

- **Con las 30 corridas del Sprint 6** (`corridas_30_completa`, con los benchmarks de `corridas_30/bloque_1..4`), `tabla_maestra.md` sale **idéntica** a la publicada. Los CSV solo difieren en el decimal 16. `corridas.csv` agrega la columna `factor_liquidez`.
- **La 3.2.3 de PS** (`scripts/comparacion_estadistica_3_2_3.py`) da los mismos números con el `corridas.csv` nuevo: solo cambian el título y la ruta de entrada.
- Los cuadernos que llaman al script (`Colab_90corridas_*`, `Colab_30corridas_*`, `Colab_tamanos_media_BF`) siguen funcionando: la tabla maestra no cambia y lo nuevo son archivos adicionales.

## 7. Cómo volver a correrla (un solo comando)

Cuando llegue la ×0,25 de MR, o los tamaños, basta con dejar los JSON en su carpeta y correr lo mismo. Las carpetas que todavía no existen se saltan.

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

**Para PS:** la 3.2.3 se puede correr ya sobre `data/analysis/3_2_2/corridas.csv`. Con la ×0,25 se completan Kruskal-Wallis, Mann-Whitney y Friedman.

## 8. Límites

- Faltan la ×0,25 (30 corridas por estrategia) y los tamaños 0,5 y 1,5. Hasta entonces, la «global» es de 60 días, no de 90.
- Las corridas bajo el 95 % son solo de los benchmarks (MO-09 semilla 4). Están en la tabla principal y la fila de robustez muestra que no cambian la conclusión.
- Los cortes por tramo y activo son descriptivos y están confundidos entre sí (sección 5.3).
- La bitácora del proyecto (`docs/bitacora_cambios_PS.md`) es de PS. Este cambio se registra aquí y en el HANDOFF.

---

Elaborado por BF con apoyo de Claude Code (uso de IA autorizado por la universidad).
