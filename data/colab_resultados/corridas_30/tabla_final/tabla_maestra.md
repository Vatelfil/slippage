# Tabla maestra 3.2.2

Costo: slippage contra el precio de llegada. Sistema: `PPO_sistema`. Diferencias pareadas por orden y semilla; IC 95 % por bootstrap. Corridas leídas: 90 de 8 archivos.

## Por escenario y tamaño

| escenario | factor_tamano | n_pares | IS_PPO_sistema | IS_TWAP | IS_VWAP | sd_PPO_sistema | dif_vs_TWAP_bps | dif_vs_TWAP_ic | p_wilcoxon_vs_TWAP | p_ttest_vs_TWAP | dif_vs_TWAP_pct | dif_vs_VWAP_bps | dif_vs_VWAP_ic | p_wilcoxon_vs_VWAP | p_ttest_vs_VWAP | dif_vs_VWAP_pct | ranking |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| media | 1.00 | 30 | 34.53 | 57.99 | 60.97 | 88.46 | -23.46 | [-51.31; 3.77] | 0.08 | 0.12 | -40.45 | -26.44 | [-58.21; 4.12] | 0.10 | 0.12 | -43.36 | PPO_sistema < TWAP < VWAP |

## Por estrategia

| estrategia | n | media | mediana | peor | mejor | cumplimiento_medio |
|---|---|---|---|---|---|---|
| PPO_sistema | 30 | 34.53 | 38.16 | 182.97 | -223.87 | 0.98 |
| TWAP | 30 | 57.99 | 81.80 | 365.82 | -278.58 | 1.00 |
| VWAP | 30 | 60.97 | 83.87 | 391.89 | -278.58 | 1.00 |
