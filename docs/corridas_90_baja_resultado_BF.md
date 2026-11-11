# 90 corridas (3.2.1): resultado de la profundidad del market maker ×4, parte de BF (11 de noviembre)

**Quién:** BF la corrió en Colab (`Colab_90corridas_baja_A` y `_B`, rama `feature/ps-3-2-1-cuadernos`) y la revisó con apoyo de Claude Code.
**Datos:** `data/colab_resultados/corridas_90/baja/`, que son los JSON y la tabla del zip `corridas_90_baja.zip`.

**Nombre del escenario:** en los archivos y cuadernos se llama `baja` (`mm_pov` ×4 en `data/scenarios/escenarios_liquidez_v3.json`). Desde el C-6c se informa como **profundidad del market maker ×4**, porque la v3 no quedó confirmada como escenario de liquidez (`docs/c6c_confirmacion_v3_BF.md`).

**Es un avance:** el resultado de la 3.2.3 es el de las 90 corridas juntas (×4, ×1 y ×0,25), con los tests del plan de análisis (`docs/plan_analisis_3_2_3_PS.md`). Falta el zip de ×0,25 (MR).

## Revisión del zip

- Hay 30 corridas por estrategia (sistema, TWAP y VWAP): 10 órdenes × semillas 4, 5 y 6.
- Están todas pareadas, sin duplicados ni errores.
- **La firma confirma lo acordado:**
  - `escenario` = `baja` con factor 4,0 sobre `mm_pov`, y `factor_tamano` = 1,0;
  - impacto acumulado (y = 0,5, τ = 120 min);
  - corrección del cierre y modo muestreo en el sistema;
  - `semilla_inicial` = 4 y `seed_red` = 1000.
- **Redes:** las mismas de la liquidez media y de la 3.1.3, desde `sistema_final/maestro/` en Drive.
  - Primeros 16 dígitos del SHA-256:
    - `checkpoint_last.pt`: `04aa2456fb59d7c1`;
    - `ejecutor_apertura.pt`: `3b0bda9283229489`;
    - `ejecutor_media_jornada.pt`: `670414957f150f5e`;
    - `ejecutor_cierre.pt`: `3145ab6f92a833f9`.
  - El registro del entrenamiento que venía con ellas coincide con `data/colab_resultados/sistema_final/maestro/`.
  - No son las de `maestro_v2/`: esas tienen los mismos Ejecutores, pero otro Maestro.
- **Cumplimiento:**
  - el sistema completa la orden en todas las corridas (mínimo 100 %);
  - TWAP y VWAP quedan en 87,1 % en MO-09 con semilla 4, igual que en la media. Los benchmarks no tienen corrección del cierre, y repetirla daría lo mismo porque la semilla fija el día. Por eso se informa también el costo ajustado (`--penalizacion-bps 30`), como dice el plan de análisis.
- **Cómo se corrió:**
  - TWAP y VWAP se corrieron el 5 de noviembre;
  - el sistema se corrió el 11 de noviembre. El 5 se había caído porque las redes no estaban en el Drive de BF.
  - No cambia nada: cada corrida depende solo de la orden, la semilla y el escenario.
- **Tabla:** se reprodujo en local con `scripts/consolidar_resultados_3_2_2.py`. Da la misma tabla; los CSV solo difieren en el decimal 16. Se agregó `tabla_maestra.tex`, que el zip no trae.

## Resultado

| | Sistema | TWAP | VWAP |
|---|---|---|---|
| Costo medio (bps) | 59,5 | 70,0 | 69,1 |
| Mediana (bps) | 32,4 | 44,7 | 43,9 |

| Comparación | n | Dif. media | IC 95 % | Wilcoxon p | d de Cohen | r | Gana el sistema |
|---|---|---|---|---|---|---|---|
| Sistema − TWAP | 30 | −10,53 | [−33,09; 11,79] | 0,440 | −0,16 (despreciable) | −0,17 | 15/30 |
| Sistema − TWAP, costo ajustado | 30 | −10,52 | [−33,05; 11,81] | 0,452 | −0,16 | | 15/30 |
| Sistema − VWAP | 30 | −9,64 | [−33,76; 14,52] | 0,404 | −0,14 | −0,18 | 16/30 |
| Sistema − VWAP, costo ajustado | 30 | −9,39 | [−33,50; 14,74] | 0,440 | −0,13 | | 15/30 |

- IC por bootstrap con 3.000 remuestreos, como en el plan.
- El p de Wilcoxon es sin corregir. La corrección de Holm (3 escenarios) se aplica en la 3.2.3, cuando estén los tres.
- **Lectura:** el sistema cuesta en promedio 10 bps menos, pero gana en la mitad de los días y el IC incluye el 0. Con 30 corridas por escenario el plan ya preveía que no saliera significativo, porque la muestra es pequeña (sección 5 del plan).

## Comparación con la profundidad ×1 (liquidez media de PS)

Mismas órdenes y semillas; solo cambia `mm_pov`.

| | ×1 (PS, 1 nov) | ×4 (BF, 11 nov) |
|---|---|---|
| Sistema / TWAP / VWAP (bps) | 47,1 / 50,5 / 51,3 | 59,5 / 70,0 / 69,1 |
| Sistema − TWAP | −3,37 [−26,15; 19,63], p 0,626 | −10,53 [−33,09; 11,79], p 0,440 |
| Gana el sistema | 16/30 | 15/30 |
| Maestro en α = 0,5 y ventana de 15 min | 275 de 282 decisiones | 272 de 282 |
| Comprado tras 30 min / 1 h / 2 h | 39 % / 65 % / 92 % | 38 % / 63 % / 92 % |
| Correlación (sistema − TWAP, costo de TWAP) | −0,78 | −0,77 |

- Con el mismo conteo, la media da 275 de 282 decisiones. PS informó 276 porque contó también una decisión con α = 0,5 y ventana de 5 min.
- Los porcentajes comprados son el promedio de las 30 corridas con el mismo cálculo en los dos escenarios.
- **Lectura descriptiva, pareada por orden y semilla. NO es el test del plan:** la pregunta «¿depende de la profundidad del market maker?» se responde en la 3.2.3 con Kruskal-Wallis sobre los tres escenarios.

  | ×4 − ×1 | Dif. media (bps) | IC 95 % | Wilcoxon p | Positivas |
  |---|---|---|---|---|
  | Sistema | +12,40 | [−2,28; +28,11] | 0,245 | 17/30 |
  | TWAP | +19,57 | [−2,90; +44,37] | 0,114 | 19/30 |
  | VWAP | +17,85 | [−6,00; +42,84] | 0,129 | 20/30 |
  | Ventaja (sistema − TWAP) | −7,17 | [−19,44; +4,58] | | |

  - Con más profundidad del market maker, las tres estrategias cuestan más. Es la misma dirección del C-6c, pero ningún IC excluye el 0.
  - La ventaja del sistema no cambia de forma clara entre ×1 y ×4.

## Por qué: el sistema se comporta igual que en la media

Se repiten los hallazgos de `docs/qa_sistema_media_90_PS.md`:

- **El Maestro hace siempre lo mismo.** En 272 de 282 decisiones (96,5 %) elige α = 0,5 y la ventana de 15 minutos, los dos máximos (`ALPHA_VALUES` y `VENTANA_MIN_VALUES` en `src/envs/maestro_ejecutor_protocol.py`). Compra ≈ 38 % en la primera media hora, ≈ 63 % en la primera hora y ≈ 92 % en dos horas. No se adapta al escenario: con ×4 hace lo mismo que con ×1.
- **El resultado depende de si el precio sube o baja:**
  - la correlación entre la ventaja y el costo de TWAP es −0,77;
  - en los 22 días en que TWAP salió caro (≥ 0 bps), el sistema ahorra 35,7 bps en promedio;
  - en los 8 en que salió barato, pierde 58,8 bps.
  - Hay 2 días «que suben» más que en la media (22 contra 20).
  - **Eso solo explica casi toda la diferencia entre escenarios.** Con los promedios de ×1 (+39,3 y −68,5 bps) y la mezcla de ×4 (22 y 8 días), la ventaja esperada sería (22 × 39,3 − 8 × 68,5) / 30 ≈ 10,6 bps, prácticamente el −10,5 medido.
  - Por eso, que la diferencia sea −10,5 en ×4 y −3,4 en ×1 no indica que el sistema funcione mejor con más profundidad.
- **Causas:** son las mismas que PS encontró en el código (C1 a C5 de su revisión). La más probable es que el Maestro se entrenó sin la corrección del cierre y aprendió a apurarse. Las mejoras posibles (M1 a M5) también siguen igual, y cualquiera que se haga después de ver las 90 se declara como cambio y se informa aparte.

## Lectura posterior: por tramo (NO está en el plan; no se usa para concluir)

| Tramo de inicio | n | Sistema − TWAP, ×4 | Gana el sistema | Sistema − TWAP, ×1 |
|---|---|---|---|---|
| Apertura (MO-01 a MO-04) | 12 | +11,3 | 5/12 | +16,5 |
| Media jornada (MO-05 a MO-07) | 9 | +1,9 | 3/9 | +1,1 |
| Cierre (MO-08 a MO-10) | 9 | −52,1 | 7/9 | −34,4 |

- El patrón es el mismo en ×1 y ×4: la ventaja promedio viene de las órdenes de cierre, donde el sistema compra temprano y tiene corrección del cierre, mientras que los benchmarks no la tienen.
- MO-03 cuesta ≈ +82 bps más que TWAP en los dos escenarios.
- Esta tabla se armó después de ver los datos. Sirve para la discusión del capítulo 7, no como resultado.

## Archivos

- `data/colab_resultados/corridas_90/baja/A/` y `B/`: los JSON del sistema y de los benchmarks;
- `data/colab_resultados/corridas_90/baja/tabla/`: la tabla maestra (`.md`, `.csv` y `.tex`), los agregados, las corridas y el gráfico de cajas;
- `tests/test_corridas_90_baja.py`: fija el conteo, la firma, el cumplimiento, la tabla y el conteo de decisiones del Maestro.

## Cómo reproducir

```bash
python scripts/consolidar_resultados_3_2_2.py --entradas data/colab_resultados/corridas_90/baja/A data/colab_resultados/corridas_90/baja/B --sistema PPO_sistema --out-dir data/colab_resultados/corridas_90/baja/tabla
python scripts/consolidar_resultados_3_2_2.py --entradas data/colab_resultados/corridas_90/baja/A data/colab_resultados/corridas_90/baja/B --sistema PPO_sistema --penalizacion-bps 30 --out-dir <carpeta_temporal>
python -m pytest tests/test_corridas_90_baja.py -q
```

---

Elaborado por BF con apoyo de Claude Code (uso de IA autorizado por la universidad).
