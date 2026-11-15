# Tabla maestra 3.2.2

Costo: slippage contra el precio de llegada. Sistema: `PPO_sistema`. Diferencias pareadas por orden y semilla; IC 95 % por bootstrap. Corridas leídas: 360 de 16 archivos.

## Por escenario y tamaño

| escenario | factor_tamano | n_pares | IS_PPO_sistema | IS_TWAP | IS_VWAP | sd_PPO_sistema | dif_vs_TWAP_bps | dif_vs_TWAP_ic | p_wilcoxon_vs_TWAP | p_ttest_vs_TWAP | dif_vs_TWAP_pct | dif_vs_VWAP_bps | dif_vs_VWAP_ic | p_wilcoxon_vs_VWAP | p_ttest_vs_VWAP | dif_vs_VWAP_pct | ranking |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| alta | 1.00 | 30 | 69.19 | 65.33 | 64.79 | 130.84 | 3.87 | [-16.56; 25.30] | 0.87 | 0.73 | 5.92 | 4.41 | [-20.42; 30.85] | 0.82 | 0.75 | 6.80 | VWAP < TWAP < PPO_sistema |
| baja | 1.00 | 30 | 59.51 | 70.05 | 69.15 | 113.05 | -10.53 | [-33.09; 11.79] | 0.44 | 0.38 | -15.04 | -9.64 | [-33.76; 14.52] | 0.40 | 0.46 | -13.93 | PPO_sistema < VWAP < TWAP |
| media | 0.50 | 30 | 38.63 | 36.43 | 36.68 | 107.99 | 2.20 | [-20.84; 25.72] | 0.95 | 0.86 | 6.04 | 1.95 | [-23.95; 28.71] | 0.95 | 0.89 | 5.32 | TWAP < VWAP < PPO_sistema |
| media | 1.00 | 30 | 47.11 | 50.48 | 51.30 | 114.81 | -3.37 | [-26.15; 19.63] | 0.63 | 0.79 | -6.67 | -4.19 | [-30.31; 22.11] | 0.61 | 0.77 | -8.16 | PPO_sistema < TWAP < VWAP |

## Por estrategia (solo tamaño 1; los otros tamaños van en tabla_tamanos)

| estrategia | n | media | mediana | peor | mejor | cumplimiento_medio |
|---|---|---|---|---|---|---|
| PPO_sistema | 90 | 58.61 | 40.10 | 404.54 | -324.75 | 1.00 |
| TWAP | 90 | 61.95 | 45.10 | 522.69 | -377.94 | 1.00 |
| VWAP | 90 | 61.75 | 45.94 | 522.69 | -377.94 | 0.99 |
