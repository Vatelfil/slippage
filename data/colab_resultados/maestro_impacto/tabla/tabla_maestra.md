# Tabla maestra 3.2.2

Costo: slippage contra el precio de llegada. Sistema: `PPO_maestro`. Diferencias pareadas por orden y semilla; IC 95 % por bootstrap. Corridas leídas: 16 de 3 archivos.

## Por escenario y tamaño

| escenario | factor_tamano | n_pares | IS_PPO_maestro | IS_PPO_maestro_sin_entrenar | IS_TWAP | IS_VWAP | dif_vs_TWAP_bps | dif_vs_TWAP_ic | dif_vs_TWAP_pct | dif_vs_VWAP_bps | dif_vs_VWAP_ic | dif_vs_VWAP_pct | ranking |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| media | 1.00 | 4 | 54.33 | 44.95 | 57.75 | 61.96 | -3.42 | [-43.70; 36.87] | -5.92 | -7.63 | [-60.04; 44.79] | -12.31 | PPO_maestro_sin_entrenar < PPO_maestro < TWAP < VWAP |

## Por estrategia

| estrategia | n | media | mediana | peor | mejor | cumplimiento_medio |
|---|---|---|---|---|---|---|
| PPO_maestro | 4 | 54.33 | 43.60 | 109.33 | 20.79 | 1.00 |
| PPO_maestro_sin_entrenar | 4 | 44.95 | 34.69 | 121.73 | -11.32 | 0.97 |
| TWAP | 4 | 57.75 | 59.61 | 128.74 | -16.98 | 1.00 |
| VWAP | 4 | 61.96 | 64.71 | 144.65 | -26.25 | 0.99 |
