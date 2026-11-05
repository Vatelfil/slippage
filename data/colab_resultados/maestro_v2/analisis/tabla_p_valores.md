# Maestro v2 en la liquidez media

Sistema: `PPO_sistema_v2`. Corridas leídas: 120. Entradas: `/content/drive/MyDrive/slippage_colab/resultados/corridas_90/media/A`, `/content/drive/MyDrive/slippage_colab/resultados/corridas_90/media/B`, `/content/drive/MyDrive/slippage_colab/resultados/maestro_v2/eval_media`.

Diferencia = costo del sistema − costo de la referencia, en bps, pareada por escenario, orden y semilla. **Negativa = el sistema cuesta menos.** IC 95 % por bootstrap. Shapiro p ≥ 0,05: no se rechaza la normalidad de las diferencias (el t-test es válido). d de Cohen pareado: 0,2 pequeño, 0,5 mediano, 0,8 grande. r: correlación biserial de rangos (−1 = el sistema siempre más barato). Significativo: Wilcoxon (con Holm cuando hay varios escenarios) < 0,05.

## Tabla de p-valores y efectos

| Grupo | Ref. | n | Dif. media | IC 95 % | Dif. % | Shapiro p | Wilcoxon p | Wilcoxon p (Holm) | t p | d de Cohen | r | Gana el sistema | Signif. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Total (principal)** | PPO_sistema | 30 | -0.85 | [-9.97; 8.25] | -1.8 % | 0.675 | 0.855 | — | 0.856 | -0.03 (despreciable) | -0.04 | 15/30 | no |
| Total sin MO-06 | PPO_sistema | 27 | 2.29 | [-6.04; 11.37] | 7.5 % | 0.501 | 0.804 | — | 0.613 | 0.10 (despreciable) | 0.06 | 13/27 | no |
| Promedio por orden y semilla | PPO_sistema | 30 | -0.85 | [-9.97; 8.25] | -1.8 % | 0.675 | 0.855 | — | 0.856 | -0.03 (despreciable) | -0.04 | 15/30 | no |
| **Total (principal)** | TWAP | 30 | -4.21 | [-23.71; 16.11] | -8.3 % | 0.459 | 0.556 | — | 0.695 | -0.07 (despreciable) | -0.13 | 18/30 | no |
| Total sin MO-06 | TWAP | 27 | -2.84 | [-22.67; 18.42] | -8.0 % | 0.249 | 0.594 | — | 0.791 | -0.05 (despreciable) | -0.12 | 16/27 | no |
| Promedio por orden y semilla | TWAP | 30 | -4.21 | [-23.71; 16.11] | -8.3 % | 0.459 | 0.556 | — | 0.695 | -0.07 (despreciable) | -0.13 | 18/30 | no |
| **Total (principal)** | VWAP | 30 | -5.04 | [-28.40; 19.13] | -9.8 % | 0.829 | 0.556 | — | 0.692 | -0.07 (despreciable) | -0.13 | 19/30 | no |
| Total sin MO-06 | VWAP | 27 | -3.70 | [-26.90; 21.31] | -10.2 % | 0.522 | 0.611 | — | 0.768 | -0.06 (despreciable) | -0.12 | 17/27 | no |
| Promedio por orden y semilla | VWAP | 30 | -5.04 | [-28.40; 19.13] | -9.8 % | 0.829 | 0.556 | — | 0.692 | -0.07 (despreciable) | -0.13 | 19/30 | no |

## Entre escenarios (¿la ventaja depende de la liquidez?)

Hay un solo escenario en los datos: Kruskal-Wallis, Mann-Whitney y Friedman se calculan cuando estén las tres liquideces.

