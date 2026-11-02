# Tabla maestra 3.2.2

Costo: slippage contra el precio de llegada. Sistema: `PPO_sistema`. Diferencias pareadas por orden y semilla; IC 95 % por bootstrap. Corridas leídas: 90 de 6 archivos.

## Por escenario y tamaño

| escenario | factor_tamano | n_pares | IS_PPO_sistema | IS_TWAP | IS_VWAP | sd_PPO_sistema | dif_vs_TWAP_bps | dif_vs_TWAP_ic | p_wilcoxon_vs_TWAP | p_ttest_vs_TWAP | dif_vs_TWAP_pct | dif_vs_VWAP_bps | dif_vs_VWAP_ic | p_wilcoxon_vs_VWAP | p_ttest_vs_VWAP | dif_vs_VWAP_pct | ranking |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| media | 1.00 | 30 | 35.84 | 57.99 | 60.97 | 90.77 | -22.15 | [-50.01; 4.43] | 0.10 | 0.13 | -38.19 | -25.13 | [-56.91; 5.04] | 0.13 | 0.14 | -41.21 | PPO_sistema < TWAP < VWAP |

## Por estrategia

| estrategia | n | media | mediana | peor | mejor | cumplimiento_medio |
|---|---|---|---|---|---|---|
| PPO_sistema | 30 | 35.84 | 38.47 | 183.62 | -232.92 | 1.00 |
| TWAP | 30 | 57.99 | 81.80 | 365.82 | -278.58 | 1.00 |
| VWAP | 30 | 60.97 | 83.87 | 391.89 | -278.58 | 1.00 |
