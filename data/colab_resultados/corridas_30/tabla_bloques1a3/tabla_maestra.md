# Tabla maestra 3.2.2

Costo: slippage contra el precio de llegada. Sistema: `PPO_sistema`. Diferencias pareadas por orden y semilla; IC 95 % por bootstrap. Corridas leídas: 72 de 6 archivos.

## Por escenario y tamaño

| escenario | factor_tamano | n_pares | IS_PPO_sistema | IS_TWAP | IS_VWAP | sd_PPO_sistema | dif_vs_TWAP_bps | dif_vs_TWAP_ic | p_wilcoxon_vs_TWAP | p_ttest_vs_TWAP | dif_vs_TWAP_pct | dif_vs_VWAP_bps | dif_vs_VWAP_ic | p_wilcoxon_vs_VWAP | p_ttest_vs_VWAP | dif_vs_VWAP_pct | ranking |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| media | 1.00 | 24 | 50.07 | 76.05 | 79.78 | 61.60 | -25.98 | [-58.44; 6.02] | 0.11 | 0.15 | -34.16 | -29.70 | [-66.84; 6.53] | 0.13 | 0.15 | -37.23 | PPO_sistema < TWAP < VWAP |

## Por estrategia

| estrategia | n | media | mediana | peor | mejor | cumplimiento_medio |
|---|---|---|---|---|---|---|
| PPO_sistema | 24 | 50.07 | 38.16 | 182.97 | -72.17 | 0.99 |
| TWAP | 24 | 76.05 | 81.80 | 365.82 | -173.28 | 1.00 |
| VWAP | 24 | 79.78 | 83.87 | 391.89 | -170.25 | 1.00 |
