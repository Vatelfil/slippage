# Tabla maestra 3.2.2

Costo: slippage contra el precio de llegada. Sistema: `PPO_sistema`. Diferencias pareadas por orden y semilla; IC 95 % por bootstrap. Corridas leídas: 27 de 2 archivos.

## Por escenario y tamaño

| escenario | factor_tamano | n_pares | IS_PPO_sistema | IS_TWAP | IS_VWAP | sd_PPO_sistema | dif_vs_TWAP_bps | dif_vs_TWAP_ic | p_wilcoxon_vs_TWAP | p_ttest_vs_TWAP | dif_vs_TWAP_pct | dif_vs_VWAP_bps | dif_vs_VWAP_ic | p_wilcoxon_vs_VWAP | p_ttest_vs_VWAP | dif_vs_VWAP_pct | ranking |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| media | 1.00 | 9 | 30.58 | 49.01 | 49.23 | 19.31 | -18.43 | [-38.85; 3.29] | 0.13 | 0.15 | -37.60 | -18.65 | [-44.46; 7.96] | 0.25 | 0.23 | -37.88 | PPO_sistema < TWAP < VWAP |

## Por estrategia

| estrategia | n | media | mediana | peor | mejor | cumplimiento_medio |
|---|---|---|---|---|---|---|
| PPO_sistema | 9 | 30.58 | 21.60 | 63.57 | 11.17 | 1.00 |
| TWAP | 9 | 49.01 | 30.42 | 128.74 | -16.98 | 1.00 |
| VWAP | 9 | 49.23 | 24.46 | 144.65 | -26.25 | 1.00 |
