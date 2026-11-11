# Tabla maestra 3.2.2

Costo: slippage contra el precio de llegada. Sistema: `PPO_sistema`. Diferencias pareadas por orden y semilla; IC 95 % por bootstrap. Corridas leídas: 90 de 4 archivos.

## Por escenario y tamaño

| escenario | factor_tamano | n_pares | IS_PPO_sistema | IS_TWAP | IS_VWAP | sd_PPO_sistema | dif_vs_TWAP_bps | dif_vs_TWAP_ic | p_wilcoxon_vs_TWAP | p_ttest_vs_TWAP | dif_vs_TWAP_pct | dif_vs_VWAP_bps | dif_vs_VWAP_ic | p_wilcoxon_vs_VWAP | p_ttest_vs_VWAP | dif_vs_VWAP_pct | ranking |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| media | 1.00 | 30 | 47.11 | 50.48 | 51.30 | 114.81 | -3.37 | [-26.15; 19.63] | 0.63 | 0.79 | -6.67 | -4.19 | [-30.31; 22.11] | 0.61 | 0.77 | -8.16 | PPO_sistema < TWAP < VWAP |

## Por estrategia

| estrategia | n | media | mediana | peor | mejor | cumplimiento_medio |
|---|---|---|---|---|---|---|
| PPO_sistema | 30 | 47.11 | 38.04 | 285.58 | -311.76 | 1.00 |
| TWAP | 30 | 50.48 | 38.13 | 386.76 | -377.94 | 1.00 |
| VWAP | 30 | 51.30 | 38.84 | 386.76 | -377.94 | 0.99 |
