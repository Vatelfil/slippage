# Prueba de la 3.2.3 con las 30 corridas de la 3.1.3

Sistema: `PPO_sistema`. Corridas leídas: 90. Entradas: `data/colab_resultados/corridas_30_completa/tabla/corridas.csv`.

Diferencia = costo del sistema − costo de la referencia, en bps, pareada por escenario, orden y semilla. **Negativa = el sistema cuesta menos.** IC 95 % por bootstrap. Shapiro p ≥ 0,05: no se rechaza la normalidad de las diferencias (el t-test es válido). d de Cohen pareado: 0,2 pequeño, 0,5 mediano, 0,8 grande. r: correlación biserial de rangos (−1 = el sistema siempre más barato). Significativo: Wilcoxon (con Holm cuando hay varios escenarios) < 0,05.

## Tabla de p-valores y efectos

| Grupo | Ref. | n | Dif. media | IC 95 % | Dif. % | Shapiro p | Wilcoxon p | Wilcoxon p (Holm) | t p | d de Cohen | r | Gana el sistema | Signif. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Total (principal)** | TWAP | 30 | -22.15 | [-50.01; 4.43] | -38.2 % | 0.422 | 0.096 | — | 0.134 | -0.28 (pequeño) | -0.35 | 20/30 | no |
| Total sin MO-06 | TWAP | 27 | -12.46 | [-34.11; 11.00] | -34.6 % | 0.057 | 0.141 | — | 0.306 | -0.20 (pequeño) | -0.33 | 18/27 | no |
| Promedio por orden y semilla | TWAP | 30 | -22.15 | [-50.01; 4.43] | -38.2 % | 0.422 | 0.096 | — | 0.134 | -0.28 (pequeño) | -0.35 | 20/30 | no |
| **Total (principal)** | VWAP | 30 | -25.13 | [-56.91; 5.04] | -41.2 % | 0.340 | 0.129 | — | 0.136 | -0.28 (pequeño) | -0.32 | 20/30 | no |
| Total sin MO-06 | VWAP | 27 | -13.06 | [-37.24; 13.12] | -35.7 % | 0.139 | 0.185 | — | 0.333 | -0.19 (despreciable) | -0.30 | 18/27 | no |
| Promedio por orden y semilla | VWAP | 30 | -25.13 | [-56.91; 5.04] | -41.2 % | 0.340 | 0.129 | — | 0.136 | -0.28 (pequeño) | -0.32 | 20/30 | no |

## Entre escenarios (¿la ventaja depende de la liquidez?)

Hay un solo escenario en los datos: Kruskal-Wallis, Mann-Whitney y Friedman se calculan cuando estén las tres liquideces.

