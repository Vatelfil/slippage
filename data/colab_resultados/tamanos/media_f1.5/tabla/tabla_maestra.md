# Tabla maestra 3.2.2

Costo: slippage contra el precio de llegada. Sistema: `PPO_sistema`. Diferencias pareadas por orden y semilla; IC 95 % por bootstrap. Corridas leídas: 90 de 4 archivos.

## Por escenario y tamaño

| escenario | factor_tamano | n_pares | IS_PPO_sistema | IS_TWAP | IS_VWAP | sd_PPO_sistema | dif_vs_TWAP_bps | dif_vs_TWAP_ic | p_wilcoxon_vs_TWAP | p_ttest_vs_TWAP | dif_vs_TWAP_pct | dif_vs_VWAP_bps | dif_vs_VWAP_ic | p_wilcoxon_vs_VWAP | p_ttest_vs_VWAP | dif_vs_VWAP_pct | ranking |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| media | 1.50 | 30 | 51.75 | 59.63 | 60.75 | 127.75 | -7.88 | [-25.03; 9.47] | 0.37 | 0.41 | -13.22 | -8.99 | [-29.82; 11.44] | 0.35 | 0.42 | -14.81 | PPO_sistema < TWAP < VWAP |

## Por estrategia

| estrategia | n | media | mediana | peor | mejor | cumplimiento_medio |
|---|---|---|---|---|---|---|
| PPO_sistema | 30 | 51.75 | 52.51 | 349.41 | -310.81 | 0.98 |
| TWAP | 30 | 59.63 | 42.98 | 403.03 | -359.38 | 0.99 |
| VWAP | 30 | 60.75 | 43.52 | 403.03 | -359.38 | 0.99 |
