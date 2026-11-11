# Tabla maestra 3.2.2

Costo: slippage contra el precio de llegada. Sistema: `PPO_sistema`. Diferencias pareadas por orden y semilla; IC 95 % por bootstrap. Corridas leídas: 90 de 4 archivos.

## Por escenario y tamaño

| escenario | factor_tamano | n_pares | IS_PPO_sistema | IS_TWAP | IS_VWAP | sd_PPO_sistema | dif_vs_TWAP_bps | dif_vs_TWAP_ic | p_wilcoxon_vs_TWAP | p_ttest_vs_TWAP | dif_vs_TWAP_pct | dif_vs_VWAP_bps | dif_vs_VWAP_ic | p_wilcoxon_vs_VWAP | p_ttest_vs_VWAP | dif_vs_VWAP_pct | ranking |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baja | 1.00 | 30 | 59.51 | 70.05 | 69.15 | 113.05 | -10.53 | [-33.09; 11.79] | 0.44 | 0.38 | -15.04 | -9.64 | [-33.76; 14.52] | 0.40 | 0.46 | -13.93 | PPO_sistema < VWAP < TWAP |

## Por estrategia

| estrategia | n | media | mediana | peor | mejor | cumplimiento_medio |
|---|---|---|---|---|---|---|
| PPO_sistema | 30 | 59.51 | 32.45 | 344.51 | -263.04 | 1.00 |
| TWAP | 30 | 70.05 | 44.74 | 522.69 | -323.03 | 1.00 |
| VWAP | 30 | 69.15 | 43.90 | 522.69 | -323.03 | 0.99 |
