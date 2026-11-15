# Tabla maestra 3.2.2

Costo: slippage contra el precio de llegada. Sistema: `PPO_sistema`. Diferencias pareadas por orden y semilla; IC 95 % por bootstrap. Corridas leídas: 90 de 4 archivos.

## Por escenario y tamaño

| escenario | factor_tamano | n_pares | IS_PPO_sistema | IS_TWAP | IS_VWAP | sd_PPO_sistema | dif_vs_TWAP_bps | dif_vs_TWAP_ic | p_wilcoxon_vs_TWAP | p_ttest_vs_TWAP | dif_vs_TWAP_pct | dif_vs_VWAP_bps | dif_vs_VWAP_ic | p_wilcoxon_vs_VWAP | p_ttest_vs_VWAP | dif_vs_VWAP_pct | ranking |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| alta | 1.00 | 30 | 69.19 | 65.33 | 64.79 | 130.84 | 3.87 | [-16.56; 25.30] | 0.87 | 0.73 | 5.92 | 4.41 | [-20.42; 30.85] | 0.82 | 0.75 | 6.80 | VWAP < TWAP < PPO_sistema |

## Por estrategia

| estrategia | n | media | mediana | peor | mejor | cumplimiento_medio |
|---|---|---|---|---|---|---|
| PPO_sistema | 30 | 69.19 | 50.16 | 404.54 | -324.75 | 1.00 |
| TWAP | 30 | 65.33 | 56.33 | 376.10 | -329.12 | 0.99 |
| VWAP | 30 | 64.79 | 50.96 | 402.45 | -329.12 | 0.99 |
