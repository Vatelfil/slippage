# 90 corridas (3.2.1): resultado de la liquidez media, parte de PS (1 de noviembre)

**Quién:** PS la corrió en Colab (`Colab_90corridas_media_A` y `_B`) y la revisó con apoyo de Claude Code.
**Datos:** `data/colab_resultados/corridas_90/media/`, que son los JSON y la tabla del zip `corridas_90_media.zip`.

**Es un avance:** el resultado de la 3.2.3 es el de las 90 corridas juntas (baja, media y alta), que se analiza cuando lleguen los otros dos zips.

## Revisión del zip

- Hay 30 corridas por estrategia (sistema, TWAP y VWAP): 10 órdenes × semillas 4, 5 y 6.
- Están todas pareadas, sin duplicados ni errores.
- La firma confirma lo acordado: liquidez media de la v3 (factor 1,0), impacto acumulado, corrección del cierre en el sistema y `semilla_inicial` = 4.
- **Cumplimiento:**
  - el sistema completa la orden en todas las corridas (mínimo 98,6 %);
  - TWAP y VWAP quedan en 87 % en MO-09 con semilla 4, porque los benchmarks no tienen corrección del cierre. Repetirla daría lo mismo, ya que la semilla fija el día. Por eso se informa también el costo ajustado (`--penalizacion-bps 30`), como dice el plan de análisis.

## Resultado

| | Sistema | TWAP | VWAP |
|---|---|---|---|
| Costo medio (bps) | 47,1 | 50,5 | 51,3 |

| Comparación | n | Dif. media | IC 95 % | Wilcoxon p | d de Cohen | Gana el sistema |
|---|---|---|---|---|---|---|
| Sistema − TWAP | 30 | −3,37 | [−26,15; 19,63] | 0,626 | −0,05 (despreciable) | 16/30 |
| Sistema − TWAP, costo ajustado | 30 | −3,30 | [−26,08; 19,69] | 0,626 | −0,05 | 16/30 |
| Sistema − VWAP | 30 | −4,19 | [−30,31; 22,11] | 0,612 | −0,05 | 17/30 |

- En la 3.1.3 (semillas 1 a 3), la diferencia contra TWAP fue de −22,15 bps.
- Con días nuevos, la ventaja del sistema casi desaparece.

## Por qué

El detalle está en `docs/qa_sistema_media_90_PS.md`. En resumen:
- **El Maestro hace siempre lo mismo:** elige α = 0,5 y la ventana de 15 minutos en 276 de 282 decisiones, así que compra casi todo en las primeras dos horas.
- **Por eso el resultado depende del día:**
  - cuando el precio sube (TWAP ≥ 0, 20 días), el sistema ahorra 39 bps en promedio;
  - cuando baja (10 días), pierde 68 bps;
  - la correlación entre la ventaja y el costo de TWAP es −0,78.
- **Causa más probable:** el Maestro se entrenó sin la corrección del cierre (`crear_jornada` en `src/training/maestro_trainer.py`) y aprendió a apurarse.

Para medir qué aporta cada nivel, se agregó un control: `docs/control_reglas_3_2_3_PS.md`.
