# Control de la 3.2.3: aporte del Maestro y de los Ejecutores

Entradas: `/content/drive/MyDrive/slippage_colab/resultados/corridas_90/media/A`, `/content/drive/MyDrive/slippage_colab/resultados/corridas_90/media/B`, `/content/drive/MyDrive/slippage_colab/resultados/control_reglas/media/A`, `/content/drive/MyDrive/slippage_colab/resultados/control_reglas/media/B`.

Diferencia en bps, pareada por escenario, orden y semilla. **Negativa = la primera estrategia cuesta menos.** IC 95 % por bootstrap. Wilcoxon con corrección de Holm sobre las tres comparaciones.

| Comparación | Pregunta | n | Dif. media | IC 95 % | Wilcoxon p | p (Holm) | d de Cohen | Gana la primera |
|---|---|---|---|---|---|---|---|---|
| Regla fija − sistema | ¿El Maestro hace algo distinto de «α = 0,5 siempre»? | 30 | -2.66 | [-12.16; 2.91] | 0.500 | 1.000 | -0.11 (despreciable) | 1/30 |
| Sistema − regla uniforme | Aporte del calendario del Maestro (mismos Ejecutores) | 30 | 12.00 | [-10.59; 34.54] | 0.503 | 1.000 | 0.18 (despreciable) | 16/30 |
| Regla uniforme − TWAP | Aporte de los Ejecutores (mismo calendario que TWAP) | 30 | -15.37 | [-20.35; -10.32] | 0.000 | 0.000 | -1.08 (grande) | 26/30 |

**Regla fija igual al sistema:** 25 de 30 corridas salen idénticas (son las órdenes en que el Maestro eligió α = 0,5 y 15 min en todas sus decisiones).

## Descomposición de la diferencia con TWAP

| | bps |
|---|---|
| Sistema − TWAP (total) | -3.37 |
| … por el calendario del Maestro (sistema − uniforme) | 12.00 |
| … por los Ejecutores (uniforme − TWAP) | -15.37 |

n = 30. La suma cuadra: sí.

**Aporte del calendario según el día** (descriptivo): cuando el precio subió (TWAP ≥ 0, n = 20) fue -24.49 bps; cuando bajó (TWAP < 0, n = 10) fue 85.00 bps.
