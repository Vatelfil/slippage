# Tabla maestra 3.2.2

Costo: slippage contra el precio de llegada. Sistema: `PPO_sistema`. Diferencias pareadas por orden y semilla; IC 95 % por bootstrap. Corridas leídas: 90 de 4 archivos.

## Por escenario y tamaño

| escenario | factor_tamano | n_pares | IS_PPO_sistema | IS_TWAP | IS_VWAP | sd_PPO_sistema | dif_vs_TWAP_bps | dif_vs_TWAP_ic | p_wilcoxon_vs_TWAP | p_ttest_vs_TWAP | dif_vs_TWAP_pct | dif_vs_VWAP_bps | dif_vs_VWAP_ic | p_wilcoxon_vs_VWAP | p_ttest_vs_VWAP | dif_vs_VWAP_pct | ranking |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| media | 0.50 | 30 | 38.63 | 36.43 | 36.68 | 107.99 | 2.20 | [-20.84; 25.72] | 0.95 | 0.86 | 6.04 | 1.95 | [-23.95; 28.71] | 0.95 | 0.89 | 5.32 | TWAP < VWAP < PPO_sistema |

## Por estrategia

| estrategia | n | media | mediana | peor | mejor | cumplimiento_medio |
|---|---|---|---|---|---|---|
| PPO_sistema | 30 | 38.63 | 25.40 | 266.97 | -292.92 | 1.00 |
| TWAP | 30 | 36.43 | 30.11 | 358.44 | -404.89 | 1.00 |
| VWAP | 30 | 36.68 | 36.04 | 359.29 | -404.89 | 1.00 |
