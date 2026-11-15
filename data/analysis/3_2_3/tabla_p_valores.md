# 3.2.3: sistema contra TWAP y VWAP en las 90 corridas

Sistema: `PPO_sistema`. Corridas leídas: 270. Entradas: `data/colab_resultados/corridas_90/baja`, `data/colab_resultados/corridas_90/media`, `data/colab_resultados/corridas_90/alta`.

Diferencia = costo del sistema − costo de la referencia, en bps, pareada por escenario, orden y semilla. **Negativa = el sistema cuesta menos.** IC 95 % por bootstrap. Shapiro p ≥ 0,05: no se rechaza la normalidad de las diferencias (el t-test es válido). d de Cohen pareado: 0,2 pequeño, 0,5 mediano, 0,8 grande. r: correlación biserial de rangos (−1 = el sistema siempre más barato). Significativo: Wilcoxon (con Holm cuando hay varios escenarios) < 0,05.

## Tabla de p-valores y efectos

| Grupo | Ref. | n | Dif. media | IC 95 % | Dif. % | Shapiro p | Wilcoxon p | Wilcoxon p (Holm) | t p | d de Cohen | r | Gana el sistema | Signif. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Total (principal)** | TWAP | 90 | -3.34 | [-15.69; 9.67] | -5.4 % | 0.286 | 0.386 | — | 0.621 | -0.05 (despreciable) | -0.11 | 46/90 | no |
| Profundidad ×4 | TWAP | 30 | -10.53 | [-33.09; 11.79] | -15.0 % | 0.929 | 0.440 | 1.000 | 0.381 | -0.16 (despreciable) | -0.17 | 15/30 | no |
| Profundidad ×1 | TWAP | 30 | -3.37 | [-26.15; 19.63] | -6.7 % | 0.896 | 0.626 | 1.000 | 0.787 | -0.05 (despreciable) | -0.11 | 16/30 | no |
| Profundidad ×0,25 | TWAP | 30 | 3.87 | [-16.56; 25.30] | 5.9 % | 0.010 | 0.871 | 1.000 | 0.731 | 0.06 (despreciable) | -0.04 | 15/30 | no |
| Total sin MO-06 | TWAP | 81 | -3.42 | [-16.97; 10.58] | -7.8 % | 0.753 | 0.456 | — | 0.627 | -0.05 (despreciable) | -0.10 | 41/81 | no |
| Promedio por orden y semilla | TWAP | 30 | -3.34 | [-22.43; 16.72] | -5.4 % | 0.311 | 0.641 | — | 0.755 | -0.06 (despreciable) | -0.10 | 16/30 | no |
| **Total (principal)** | VWAP | 90 | -3.14 | [-17.50; 11.87] | -5.1 % | 0.165 | 0.393 | — | 0.684 | -0.04 (despreciable) | -0.10 | 48/90 | no |
| Profundidad ×4 | VWAP | 30 | -9.64 | [-33.76; 14.52] | -13.9 % | 0.846 | 0.404 | 1.000 | 0.456 | -0.14 (despreciable) | -0.18 | 16/30 | no |
| Profundidad ×1 | VWAP | 30 | -4.19 | [-30.31; 22.11] | -8.2 % | 0.842 | 0.612 | 1.000 | 0.767 | -0.05 (despreciable) | -0.11 | 17/30 | no |
| Profundidad ×0,25 | VWAP | 30 | 4.41 | [-20.42; 30.85] | 6.8 % | 0.022 | 0.824 | 1.000 | 0.747 | 0.06 (despreciable) | -0.05 | 15/30 | no |
| Total sin MO-06 | VWAP | 81 | -3.70 | [-18.83; 12.44] | -8.4 % | 0.511 | 0.419 | — | 0.642 | -0.05 (despreciable) | -0.10 | 42/81 | no |
| Promedio por orden y semilla | VWAP | 30 | -3.14 | [-25.01; 19.74] | -5.1 % | 0.117 | 0.598 | — | 0.800 | -0.05 (despreciable) | -0.11 | 17/30 | no |

## Entre escenarios (¿la ventaja depende de la profundidad del market maker?)

**TWAP.** Kruskal-Wallis H = 0.14, p = 0.930, épsilon² = -0.021. Friedman (bloques orden × semilla: 30): p = 0.393.

| Escenarios | U | p | p (Holm) | r |
|---|---|---|---|---|
| profundidad ×4 vs profundidad ×1 | 435.0 | 0.830 | 1.000 | 0.03 |
| profundidad ×4 vs profundidad ×0,25 | 426.0 | 0.728 | 1.000 | 0.05 |
| profundidad ×1 vs profundidad ×0,25 | 436.0 | 0.842 | 1.000 | 0.03 |

**VWAP.** Kruskal-Wallis H = 0.08, p = 0.963, épsilon² = -0.022. Friedman (bloques orden × semilla: 30): p = 0.273.

| Escenarios | U | p | p (Holm) | r |
|---|---|---|---|---|
| profundidad ×4 vs profundidad ×1 | 443.0 | 0.923 | 1.000 | 0.02 |
| profundidad ×4 vs profundidad ×0,25 | 434.0 | 0.819 | 1.000 | 0.04 |
| profundidad ×1 vs profundidad ×0,25 | 435.0 | 0.830 | 1.000 | 0.03 |

