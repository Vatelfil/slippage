# Tabla maestra 3.2.2

Costo: slippage contra el precio de llegada. Sistema: `PPO_sistema`. Diferencias pareadas por orden y semilla; IC 95 % por bootstrap. Corridas leídas: 180 de 8 archivos.

## Por escenario y tamaño

| escenario | factor_tamano | n_pares | IS_PPO_sistema | IS_TWAP | IS_VWAP | sd_PPO_sistema | dif_vs_TWAP_bps | dif_vs_TWAP_ic | p_wilcoxon_vs_TWAP | p_ttest_vs_TWAP | dif_vs_TWAP_pct | dif_vs_VWAP_bps | dif_vs_VWAP_ic | p_wilcoxon_vs_VWAP | p_ttest_vs_VWAP | dif_vs_VWAP_pct | ranking |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baja | 1.00 | 30 | 59.51 | 70.05 | 69.15 | 113.05 | -10.53 | [-33.09; 11.79] | 0.44 | 0.38 | -15.04 | -9.64 | [-33.76; 14.52] | 0.40 | 0.46 | -13.93 | PPO_sistema < VWAP < TWAP |
| media | 1.00 | 30 | 47.11 | 50.48 | 51.30 | 114.81 | -3.37 | [-26.15; 19.63] | 0.63 | 0.79 | -6.67 | -4.19 | [-30.31; 22.11] | 0.61 | 0.77 | -8.16 | PPO_sistema < TWAP < VWAP |

## Por estrategia

| estrategia | n | media | mediana | peor | mejor | cumplimiento_medio |
|---|---|---|---|---|---|---|
| PPO_sistema | 60 | 53.31 | 36.17 | 344.51 | -311.76 | 1.00 |
| TWAP | 60 | 60.26 | 40.19 | 522.69 | -377.94 | 1.00 |
| VWAP | 60 | 60.23 | 40.87 | 522.69 | -377.94 | 0.99 |
