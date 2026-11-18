# 3.2.3 con costo ajustado (30 bps por lo no ejecutado)

Sistema: `PPO_sistema`. Corridas leídas: 270. Entradas: `data/colab_resultados/corridas_90/baja`, `data/colab_resultados/corridas_90/media`, `data/colab_resultados/corridas_90/alta`.

Diferencia = costo del sistema − costo de la referencia, en bps, pareada por escenario, orden y semilla. **Negativa = el sistema cuesta menos.** IC 95 % por bootstrap. Shapiro p ≥ 0,05: no se rechaza la normalidad de las diferencias (el t-test es válido). d de Cohen pareado: 0,2 pequeño, 0,5 mediano, 0,8 grande. r: correlación biserial de rangos (−1 = el sistema siempre más barato). Significativo: Wilcoxon (con Holm cuando hay varios escenarios) < 0,05.

## Tabla de p-valores y efectos

| Grupo | Ref. | n | Dif. media | IC 95 % | Dif. % | Shapiro p | Wilcoxon p | Wilcoxon p (Holm) | t p | d de Cohen | r | Gana el sistema | Signif. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Total (principal)** | TWAP | 90 | -3.53 | [-15.93; 9.47] | -5.7 % | 0.267 | 0.381 | — | 0.602 | -0.06 (despreciable) | -0.11 | 46/90 | no |
| Profundidad ×4 | TWAP | 30 | -10.52 | [-33.05; 11.81] | -15.0 % | 0.928 | 0.452 | 1.000 | 0.382 | -0.16 (despreciable) | -0.16 | 15/30 | no |
| Profundidad ×1 | TWAP | 30 | -3.30 | [-26.08; 19.69] | -6.5 % | 0.900 | 0.626 | 1.000 | 0.791 | -0.05 (despreciable) | -0.11 | 16/30 | no |
| Profundidad ×0,25 | TWAP | 30 | 3.23 | [-17.00; 24.75] | 4.9 % | 0.008 | 0.839 | 1.000 | 0.773 | 0.05 (despreciable) | -0.05 | 15/30 | no |
| Total sin MO-06 | TWAP | 81 | -3.62 | [-17.07; 10.31] | -8.2 % | 0.728 | 0.450 | — | 0.607 | -0.06 (despreciable) | -0.10 | 41/81 | no |
| Promedio por orden y semilla | TWAP | 30 | -3.53 | [-22.71; 16.59] | -5.7 % | 0.377 | 0.626 | — | 0.743 | -0.06 (despreciable) | -0.11 | 16/30 | no |
| **Total (principal)** | VWAP | 90 | -3.06 | [-17.36; 11.88] | -5.0 % | 0.134 | 0.397 | — | 0.691 | -0.04 (despreciable) | -0.10 | 47/90 | no |
| Profundidad ×4 | VWAP | 30 | -9.39 | [-33.50; 14.74] | -13.6 % | 0.838 | 0.440 | 1.000 | 0.467 | -0.13 (despreciable) | -0.17 | 15/30 | no |
| Profundidad ×1 | VWAP | 30 | -3.86 | [-29.96; 22.18] | -7.6 % | 0.839 | 0.612 | 1.000 | 0.784 | -0.05 (despreciable) | -0.11 | 17/30 | no |
| Profundidad ×0,25 | VWAP | 30 | 4.06 | [-20.56; 30.32] | 6.3 % | 0.016 | 0.808 | 1.000 | 0.765 | 0.06 (despreciable) | -0.05 | 15/30 | no |
| Total sin MO-06 | VWAP | 81 | -3.86 | [-19.02; 12.19] | -8.7 % | 0.471 | 0.417 | — | 0.628 | -0.05 (despreciable) | -0.10 | 42/81 | no |
| Promedio por orden y semilla | VWAP | 30 | -3.06 | [-24.95; 19.67] | -5.0 % | 0.147 | 0.570 | — | 0.805 | -0.05 (despreciable) | -0.12 | 17/30 | no |

## Entre escenarios (¿la ventaja depende de la profundidad del market maker?)

**TWAP.** Kruskal-Wallis H = 0.10, p = 0.950, épsilon² = -0.022. Friedman (bloques orden × semilla: 30): p = 0.497.

| Escenarios | U | p | p (Holm) | r |
|---|---|---|---|---|
| profundidad ×4 vs profundidad ×1 | 435.0 | 0.830 | 1.000 | 0.03 |
| profundidad ×4 vs profundidad ×0,25 | 430.0 | 0.773 | 1.000 | 0.04 |
| profundidad ×1 vs profundidad ×0,25 | 441.0 | 0.900 | 1.000 | 0.02 |

**VWAP.** Kruskal-Wallis H = 0.06, p = 0.971, épsilon² = -0.022. Friedman (bloques orden × semilla: 30): p = 0.356.

| Escenarios | U | p | p (Holm) | r |
|---|---|---|---|---|
| profundidad ×4 vs profundidad ×1 | 443.0 | 0.923 | 1.000 | 0.02 |
| profundidad ×4 vs profundidad ×0,25 | 436.0 | 0.842 | 1.000 | 0.03 |
| profundidad ×1 vs profundidad ×0,25 | 437.0 | 0.853 | 1.000 | 0.03 |

