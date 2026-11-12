# Consolidación 3.2.2

Sistema: `PPO_sistema`. Diferencias pareadas por día (escenario, orden y semilla); IC 95 % por bootstrap (3.000 remuestreos, semilla 0); diferencia % = 100 × media(sistema − referencia) / |media(referencia)|. Corridas leídas: 180 de 8 archivos.

## Chequeo de calidad

**Veredicto: OK.** Corridas leídas: 180. Errores: 0.

| escenario | factor_tamano | corridas por estrategia | esperadas | días pareados | duplicados | bajo 95% | ok |
|---|---|---|---|---|---|---|---|
| baja | 1 | PPO_sistema 30, TWAP 30, VWAP 30 | 30 | 30 | 0 | MO-09 s4 TWAP 0.871; MO-09 s4 VWAP 0.871 | sí |
| media | 1 | PPO_sistema 30, TWAP 30, VWAP 30 | 30 | 30 | 0 | MO-09 s4 TWAP 0.871; MO-09 s4 VWAP 0.871 | sí |

## Tamaño 1 por profundidad del market maker (slippage crudo contra el precio de llegada)

| bloque | profundidad_mm | n_pares | IS_PPO_sistema | IS_TWAP | IS_VWAP | sd_PPO_sistema | dif_vs_TWAP_bps | dif_vs_TWAP_ic | p_wilcoxon_vs_TWAP | p_ttest_vs_TWAP | dif_vs_TWAP_pct | dif_vs_VWAP_bps | dif_vs_VWAP_ic | p_wilcoxon_vs_VWAP | p_ttest_vs_VWAP | dif_vs_VWAP_pct | ranking |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baja | ×4 | 30 | 59.51 | 70.05 | 69.15 | 113.05 | -10.53 | [-33.09; 11.79] | 0.44 | 0.38 | -15.04 | -9.64 | [-33.76; 14.52] | 0.40 | 0.46 | -13.93 | PPO_sistema < VWAP < TWAP |
| media | ×1 | 30 | 47.11 | 50.48 | 51.30 | 114.81 | -3.37 | [-26.15; 19.63] | 0.63 | 0.79 | -6.67 | -4.19 | [-30.31; 22.11] | 0.61 | 0.77 | -8.16 | PPO_sistema < TWAP < VWAP |
| global | todas | 60 | 53.31 | 60.26 | 60.23 | 113.14 | -6.95 | [-23.01; 9.35] | 0.36 | 0.42 | -11.53 | -6.91 | [-24.47; 11.19] | 0.36 | 0.46 | -11.48 | PPO_sistema < VWAP < TWAP |
| global sin días bajo 95% | todas | 58 | 53.68 | 61.24 | 61.20 | 115.09 | -7.56 | [-23.79; 9.59] | 0.34 | 0.39 | -12.35 | -7.52 | [-25.45; 11.39] | 0.34 | 0.44 | -12.29 | PPO_sistema < VWAP < TWAP |

## Tamaño 1 por profundidad del market maker (costo ajustado: slippage × cumplimiento + 30 × (1 − cumplimiento))

| bloque | profundidad_mm | n_pares | IS_PPO_sistema | IS_TWAP | IS_VWAP | sd_PPO_sistema | dif_vs_TWAP_bps | dif_vs_TWAP_ic | p_wilcoxon_vs_TWAP | p_ttest_vs_TWAP | dif_vs_TWAP_pct | dif_vs_VWAP_bps | dif_vs_VWAP_ic | p_wilcoxon_vs_VWAP | p_ttest_vs_VWAP | dif_vs_VWAP_pct | ranking |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baja | ×4 | 30 | 59.52 | 70.03 | 68.90 | 113.05 | -10.52 | [-33.05; 11.81] | 0.45 | 0.38 | -15.02 | -9.39 | [-33.50; 14.74] | 0.44 | 0.47 | -13.62 | PPO_sistema < VWAP < TWAP |
| media | ×1 | 30 | 47.18 | 50.48 | 51.04 | 114.71 | -3.30 | [-26.08; 19.69] | 0.63 | 0.79 | -6.53 | -3.86 | [-29.96; 22.18] | 0.61 | 0.78 | -7.56 | PPO_sistema < TWAP < VWAP |
| global | todas | 60 | 53.35 | 60.26 | 59.97 | 113.08 | -6.91 | [-23.01; 9.39] | 0.37 | 0.42 | -11.46 | -6.62 | [-24.19; 11.48] | 0.37 | 0.48 | -11.04 | PPO_sistema < VWAP < TWAP |
| global sin días bajo 95% | todas | 58 | 53.71 | 61.24 | 60.94 | 115.03 | -7.53 | [-23.78; 9.59] | 0.34 | 0.39 | -12.29 | -7.23 | [-24.97; 11.68] | 0.35 | 0.46 | -11.87 | PPO_sistema < VWAP < TWAP |

## Por tramo de inicio (slippage crudo, tamaño 1)

| bloque | tramo_inicio | n_pares | IS_PPO_sistema | IS_TWAP | IS_VWAP | sd_PPO_sistema | dif_vs_TWAP_bps | dif_vs_TWAP_ic | p_wilcoxon_vs_TWAP | p_ttest_vs_TWAP | dif_vs_TWAP_pct | dif_vs_VWAP_bps | dif_vs_VWAP_ic | p_wilcoxon_vs_VWAP | p_ttest_vs_VWAP | dif_vs_VWAP_pct | ranking | gana_vs_TWAP | gana_vs_VWAP |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| global | apertura | 24 | 27.44 | 13.53 | 10.97 | 22.38 | 13.92 | [-8.33; 36.98] | 0.49 | 0.26 | 102.87 | 16.47 | [-9.92; 43.64] | 0.47 | 0.27 | 150.08 | VWAP < TWAP < PPO_sistema | 11/24 | 11/24 |
| global | cierre | 18 | 23.06 | 66.29 | 66.29 | 152.84 | -43.23 | [-73.25; -14.50] | 0.01 | 0.01 | -65.22 | -43.23 | [-73.25; -14.50] | 0.01 | 0.01 | -65.22 | PPO_sistema < TWAP < VWAP | 13/18 | 13/18 |
| global | media_jornada | 18 | 118.07 | 116.55 | 119.83 | 118.45 | 1.52 | [-26.13; 29.65] | 0.97 | 0.92 | 1.30 | -1.76 | [-33.33; 29.64] | 0.90 | 0.92 | -1.47 | TWAP < PPO_sistema < VWAP | 7/18 | 9/18 |
| baja | apertura | 12 | 27.22 | 15.88 | 13.80 | 20.12 | 11.34 | [-20.02; 45.55] | 0.62 | 0.54 | 71.38 | 13.42 | [-23.66; 53.23] | 0.68 | 0.53 | 97.25 | VWAP < TWAP < PPO_sistema | 5/12 | 5/12 |
| baja | cierre | 9 | 41.28 | 93.40 | 93.40 | 159.34 | -52.11 | [-97.98; -9.94] | 0.07 | 0.06 | -55.80 | -52.11 | [-97.98; -9.94] | 0.07 | 0.06 | -55.80 | PPO_sistema < TWAP < VWAP | 7/9 | 7/9 |
| baja | media_jornada | 9 | 120.81 | 118.91 | 118.70 | 119.23 | 1.89 | [-27.80; 29.46] | 1.00 | 0.91 | 1.59 | 2.10 | [-29.77; 31.14] | 0.82 | 0.90 | 1.77 | VWAP < TWAP < PPO_sistema | 3/9 | 4/9 |
| media | apertura | 12 | 27.67 | 11.17 | 8.15 | 25.35 | 16.49 | [-13.90; 50.33] | 0.68 | 0.36 | 147.63 | 19.52 | [-17.11; 60.40] | 0.57 | 0.37 | 239.55 | VWAP < TWAP < PPO_sistema | 6/12 | 6/12 |
| media | cierre | 9 | 4.83 | 39.18 | 39.18 | 153.30 | -34.35 | [-71.15; 2.69] | 0.13 | 0.12 | -87.67 | -34.35 | [-71.15; 2.69] | 0.13 | 0.12 | -87.67 | PPO_sistema < TWAP < VWAP | 6/9 | 6/9 |
| media | media_jornada | 9 | 115.33 | 114.18 | 120.96 | 124.83 | 1.14 | [-45.74; 50.63] | 1.00 | 0.97 | 1.00 | -5.63 | [-61.98; 52.38] | 1.00 | 0.86 | -4.66 | TWAP < PPO_sistema < VWAP | 4/9 | 5/9 |

## Por activo (slippage crudo, tamaño 1)

| bloque | ticker | n_pares | IS_PPO_sistema | IS_TWAP | IS_VWAP | sd_PPO_sistema | dif_vs_TWAP_bps | dif_vs_TWAP_ic | p_wilcoxon_vs_TWAP | p_ttest_vs_TWAP | dif_vs_TWAP_pct | dif_vs_VWAP_bps | dif_vs_VWAP_ic | p_wilcoxon_vs_VWAP | p_ttest_vs_VWAP | dif_vs_VWAP_pct | ranking | gana_vs_TWAP | gana_vs_VWAP |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| global | COPEC | 18 | 41.36 | 12.65 | 7.38 | 44.07 | 28.71 | [0.26; 55.78] | 0.03 | 0.07 | 226.96 | 33.98 | [0.33; 65.59] | 0.04 | 0.07 | 460.40 | VWAP < TWAP < PPO_sistema | 4/18 | 4/18 |
| global | ECL | 18 | 104.64 | 105.73 | 109.51 | 122.16 | -1.09 | [-27.37; 26.95] | 0.90 | 0.94 | -1.03 | -4.87 | [-35.56; 26.40] | 0.67 | 0.78 | -4.45 | PPO_sistema < TWAP < VWAP | 9/18 | 11/18 |
| global | FALABELLA | 24 | 23.78 | 61.87 | 62.89 | 131.47 | -38.09 | [-61.12; -15.96] | 0.00 | 0.00 | -61.56 | -39.11 | [-61.84; -16.65] | 0.00 | 0.00 | -62.18 | PPO_sistema < TWAP < VWAP | 18/24 | 18/24 |
| baja | COPEC | 9 | 38.99 | 8.81 | 3.23 | 38.90 | 30.18 | [-3.87; 68.02] | 0.13 | 0.16 | 342.59 | 35.76 | [-3.43; 79.67] | 0.16 | 0.15 | 1107.87 | VWAP < TWAP < PPO_sistema | 2/9 | 2/9 |
| baja | ECL | 9 | 107.97 | 114.43 | 116.27 | 124.86 | -6.47 | [-38.83; 23.52] | 0.91 | 0.72 | -5.65 | -8.30 | [-44.58; 25.59] | 0.65 | 0.68 | -7.14 | PPO_sistema < TWAP < VWAP | 4/9 | 5/9 |
| baja | FALABELLA | 12 | 38.57 | 82.68 | 83.25 | 136.05 | -44.11 | [-78.78; -10.67] | 0.03 | 0.04 | -53.35 | -44.68 | [-79.11; -11.19] | 0.03 | 0.03 | -53.67 | PPO_sistema < TWAP < VWAP | 9/12 | 9/12 |
| media | COPEC | 9 | 43.73 | 16.49 | 11.53 | 51.00 | 27.24 | [-17.64; 70.31] | 0.20 | 0.29 | 165.19 | 32.20 | [-21.79; 84.46] | 0.20 | 0.30 | 279.19 | VWAP < TWAP < PPO_sistema | 2/9 | 2/9 |
| media | ECL | 9 | 101.32 | 97.03 | 102.76 | 126.87 | 4.29 | [-37.98; 51.08] | 0.91 | 0.87 | 4.43 | -1.43 | [-52.24; 52.68] | 0.82 | 0.96 | -1.40 | TWAP < PPO_sistema < VWAP | 5/9 | 6/9 |
| media | FALABELLA | 12 | 9.00 | 41.06 | 42.54 | 130.97 | -32.06 | [-58.85; -4.13] | 0.04 | 0.05 | -78.09 | -33.54 | [-60.33; -5.50] | 0.04 | 0.04 | -78.85 | PPO_sistema < TWAP < VWAP | 9/12 | 9/12 |

## Por estrategia, escenario y tamaño (slippage crudo)

| escenario | factor_tamano | estrategia | n | media | mediana | peor | mejor | cumplimiento_medio | cumplimiento_minimo |
|---|---|---|---|---|---|---|---|---|---|
| baja | 1.00 | PPO_sistema | 30 | 59.51 | 32.45 | 344.51 | -263.04 | 1.00 | 1.00 |
| baja | 1.00 | TWAP | 30 | 70.05 | 44.74 | 522.69 | -323.03 | 1.00 | 0.87 |
| baja | 1.00 | VWAP | 30 | 69.15 | 43.90 | 522.69 | -323.03 | 0.99 | 0.87 |
| media | 1.00 | PPO_sistema | 30 | 47.11 | 38.04 | 285.58 | -311.76 | 1.00 | 0.99 |
| media | 1.00 | TWAP | 30 | 50.48 | 38.13 | 386.76 | -377.94 | 1.00 | 0.87 |
| media | 1.00 | VWAP | 30 | 51.30 | 38.84 | 386.76 | -377.94 | 0.99 | 0.87 |
