# Consolidación 3.2.2

Sistema: `PPO_sistema`. Diferencias pareadas por día (escenario, orden y semilla); IC 95 % por bootstrap (3.000 remuestreos, semilla 0); diferencia % = 100 × media(sistema − referencia) / |media(referencia)|. Corridas leídas: 450 de 20 archivos.

## Chequeo de calidad

**Veredicto: OK.** Corridas leídas: 450. Errores: 0.

| escenario | factor_tamano | corridas por estrategia | esperadas | días pareados | duplicados | bajo 95% | ok |
|---|---|---|---|---|---|---|---|
| alta | 1 | PPO_sistema 30, TWAP 30, VWAP 30 | 30 | 30 | 0 | MO-08 s4 PPO_sistema 0.947; MO-09 s4 TWAP 0.871; MO-09 s4 VWAP 0.871 | sí |
| baja | 1 | PPO_sistema 30, TWAP 30, VWAP 30 | 30 | 30 | 0 | MO-09 s4 TWAP 0.871; MO-09 s4 VWAP 0.871 | sí |
| media | 0.5 | PPO_sistema 30, TWAP 30, VWAP 30 | 30 | 30 | 0 | ninguna | sí |
| media | 1 | PPO_sistema 30, TWAP 30, VWAP 30 | 30 | 30 | 0 | MO-09 s4 TWAP 0.871; MO-09 s4 VWAP 0.871 | sí |
| media | 1.5 | PPO_sistema 30, TWAP 30, VWAP 30 | 30 | 30 | 0 | MO-06 s6 VWAP 0.945; MO-08 s4 PPO_sistema 0.829; MO-08 s6 PPO_sistema 0.939; MO-09 s4 PPO_sistema 0.784; MO-09 s4 TWAP 0.831; MO-09 s4 VWAP 0.831; MO-09 s5 PPO_sistema 0.933 | sí |

## Tamaño 1 por profundidad del market maker (slippage crudo contra el precio de llegada)

| bloque | profundidad_mm | n_pares | IS_PPO_sistema | IS_TWAP | IS_VWAP | sd_PPO_sistema | dif_vs_TWAP_bps | dif_vs_TWAP_ic | p_wilcoxon_vs_TWAP | p_ttest_vs_TWAP | dif_vs_TWAP_pct | dif_vs_VWAP_bps | dif_vs_VWAP_ic | p_wilcoxon_vs_VWAP | p_ttest_vs_VWAP | dif_vs_VWAP_pct | ranking |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| alta | ×0,25 | 30 | 69.19 | 65.33 | 64.79 | 130.84 | 3.87 | [-16.56; 25.30] | 0.87 | 0.73 | 5.92 | 4.41 | [-20.42; 30.85] | 0.82 | 0.75 | 6.80 | VWAP < TWAP < PPO_sistema |
| baja | ×4 | 30 | 59.51 | 70.05 | 69.15 | 113.05 | -10.53 | [-33.09; 11.79] | 0.44 | 0.38 | -15.04 | -9.64 | [-33.76; 14.52] | 0.40 | 0.46 | -13.93 | PPO_sistema < VWAP < TWAP |
| media | ×1 | 30 | 47.11 | 50.48 | 51.30 | 114.81 | -3.37 | [-26.15; 19.63] | 0.63 | 0.79 | -6.67 | -4.19 | [-30.31; 22.11] | 0.61 | 0.77 | -8.16 | PPO_sistema < TWAP < VWAP |
| global | todas | 90 | 58.61 | 61.95 | 61.75 | 118.83 | -3.34 | [-15.69; 9.67] | 0.39 | 0.62 | -5.40 | -3.14 | [-17.50; 11.87] | 0.39 | 0.68 | -5.08 | PPO_sistema < VWAP < TWAP |
| global sin días bajo 95% | todas | 86 | 59.60 | 62.85 | 62.64 | 121.37 | -3.25 | [-16.56; 10.48] | 0.42 | 0.65 | -5.18 | -3.04 | [-18.02; 12.77] | 0.43 | 0.71 | -4.85 | PPO_sistema < VWAP < TWAP |

## Eje de tamaño (slippage crudo contra el precio de llegada)

| escenario | profundidad_mm | factor_tamano | n_pares | IS_PPO_sistema | IS_TWAP | IS_VWAP | sd_PPO_sistema | dif_vs_TWAP_bps | dif_vs_TWAP_ic | p_wilcoxon_vs_TWAP | p_ttest_vs_TWAP | dif_vs_TWAP_pct | dif_vs_VWAP_bps | dif_vs_VWAP_ic | p_wilcoxon_vs_VWAP | p_ttest_vs_VWAP | dif_vs_VWAP_pct | ranking |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| media | ×1 | 0.50 | 30 | 38.63 | 36.43 | 36.68 | 107.99 | 2.20 | [-20.84; 25.72] | 0.95 | 0.86 | 6.04 | 1.95 | [-23.95; 28.71] | 0.95 | 0.89 | 5.32 | TWAP < VWAP < PPO_sistema |
| media | ×1 | 1.00 | 30 | 47.11 | 50.48 | 51.30 | 114.81 | -3.37 | [-26.15; 19.63] | 0.63 | 0.79 | -6.67 | -4.19 | [-30.31; 22.11] | 0.61 | 0.77 | -8.16 | PPO_sistema < TWAP < VWAP |
| media | ×1 | 1.50 | 30 | 51.75 | 59.63 | 60.75 | 127.75 | -7.88 | [-25.03; 9.47] | 0.37 | 0.41 | -13.22 | -8.99 | [-29.82; 11.44] | 0.35 | 0.42 | -14.81 | PPO_sistema < TWAP < VWAP |

## Tamaño 1 por profundidad del market maker (costo ajustado: slippage × cumplimiento + 30 × (1 − cumplimiento))

| bloque | profundidad_mm | n_pares | IS_PPO_sistema | IS_TWAP | IS_VWAP | sd_PPO_sistema | dif_vs_TWAP_bps | dif_vs_TWAP_ic | p_wilcoxon_vs_TWAP | p_ttest_vs_TWAP | dif_vs_TWAP_pct | dif_vs_VWAP_bps | dif_vs_VWAP_ic | p_wilcoxon_vs_VWAP | p_ttest_vs_VWAP | dif_vs_VWAP_pct | ranking |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| alta | ×0,25 | 30 | 68.71 | 65.48 | 64.65 | 129.68 | 3.23 | [-17.00; 24.75] | 0.84 | 0.77 | 4.94 | 4.06 | [-20.56; 30.32] | 0.81 | 0.76 | 6.28 | VWAP < TWAP < PPO_sistema |
| baja | ×4 | 30 | 59.52 | 70.03 | 68.90 | 113.05 | -10.52 | [-33.05; 11.81] | 0.45 | 0.38 | -15.02 | -9.39 | [-33.50; 14.74] | 0.44 | 0.47 | -13.62 | PPO_sistema < VWAP < TWAP |
| media | ×1 | 30 | 47.18 | 50.48 | 51.04 | 114.71 | -3.30 | [-26.08; 19.69] | 0.63 | 0.79 | -6.53 | -3.86 | [-29.96; 22.18] | 0.61 | 0.78 | -7.56 | PPO_sistema < TWAP < VWAP |
| global | todas | 90 | 58.47 | 62.00 | 61.53 | 118.36 | -3.53 | [-15.93; 9.47] | 0.38 | 0.60 | -5.69 | -3.06 | [-17.36; 11.88] | 0.40 | 0.69 | -4.97 | PPO_sistema < VWAP < TWAP |
| global sin días bajo 95% | todas | 86 | 59.47 | 62.85 | 62.36 | 120.90 | -3.38 | [-16.68; 10.43] | 0.42 | 0.63 | -5.37 | -2.89 | [-17.83; 12.93] | 0.44 | 0.72 | -4.63 | PPO_sistema < VWAP < TWAP |

## Eje de tamaño (costo ajustado: slippage × cumplimiento + 30 × (1 − cumplimiento))

| escenario | profundidad_mm | factor_tamano | n_pares | IS_PPO_sistema | IS_TWAP | IS_VWAP | sd_PPO_sistema | dif_vs_TWAP_bps | dif_vs_TWAP_ic | p_wilcoxon_vs_TWAP | p_ttest_vs_TWAP | dif_vs_TWAP_pct | dif_vs_VWAP_bps | dif_vs_VWAP_ic | p_wilcoxon_vs_VWAP | p_ttest_vs_VWAP | dif_vs_VWAP_pct | ranking |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| media | ×1 | 0.50 | 30 | 38.63 | 36.43 | 36.68 | 107.99 | 2.20 | [-20.84; 25.71] | 0.95 | 0.86 | 6.04 | 1.96 | [-23.93; 28.70] | 0.95 | 0.89 | 5.33 | TWAP < VWAP < PPO_sistema |
| media | ×1 | 1.00 | 30 | 47.18 | 50.48 | 51.04 | 114.71 | -3.30 | [-26.08; 19.69] | 0.63 | 0.79 | -6.53 | -3.86 | [-29.96; 22.18] | 0.61 | 0.78 | -7.56 | PPO_sistema < TWAP < VWAP |
| media | ×1 | 1.50 | 30 | 52.60 | 59.27 | 60.03 | 125.29 | -6.66 | [-23.78; 10.99] | 0.38 | 0.48 | -11.24 | -7.42 | [-27.93; 12.88] | 0.36 | 0.50 | -12.36 | PPO_sistema < TWAP < VWAP |

## Por tramo de inicio (slippage crudo, tamaño 1)

| bloque | tramo_inicio | n_pares | IS_PPO_sistema | IS_TWAP | IS_VWAP | sd_PPO_sistema | dif_vs_TWAP_bps | dif_vs_TWAP_ic | p_wilcoxon_vs_TWAP | p_ttest_vs_TWAP | dif_vs_TWAP_pct | dif_vs_VWAP_bps | dif_vs_VWAP_ic | p_wilcoxon_vs_VWAP | p_ttest_vs_VWAP | dif_vs_VWAP_pct | ranking | gana_vs_TWAP | gana_vs_VWAP |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| global | apertura | 36 | 29.12 | 14.35 | 11.72 | 27.45 | 14.77 | [-3.09; 33.28] | 0.30 | 0.13 | 102.97 | 17.41 | [-4.12; 39.57] | 0.29 | 0.14 | 148.55 | VWAP < TWAP < PPO_sistema | 15/36 | 15/36 |
| global | cierre | 27 | 33.64 | 68.42 | 68.42 | 163.91 | -34.78 | [-56.12; -14.93] | 0.00 | 0.00 | -50.84 | -34.78 | [-56.12; -14.93] | 0.00 | 0.00 | -50.84 | PPO_sistema < TWAP < VWAP | 19/27 | 19/27 |
| global | media_jornada | 27 | 122.89 | 118.95 | 121.78 | 119.62 | 3.94 | [-20.75; 29.93] | 0.95 | 0.77 | 3.31 | 1.11 | [-28.64; 31.55] | 0.84 | 0.95 | 0.91 | TWAP < VWAP < PPO_sistema | 12/27 | 14/27 |
| alta | apertura | 12 | 32.48 | 15.99 | 13.20 | 36.50 | 16.49 | [-12.54; 47.46] | 0.42 | 0.33 | 103.13 | 19.28 | [-17.39; 58.42] | 0.52 | 0.36 | 145.99 | VWAP < TWAP < PPO_sistema | 4/12 | 4/12 |
| alta | cierre | 9 | 54.80 | 72.68 | 72.68 | 192.16 | -17.88 | [-35.03; 0.40] | 0.13 | 0.10 | -24.60 | -17.88 | [-35.03; 0.40] | 0.13 | 0.10 | -24.60 | PPO_sistema < TWAP < VWAP | 6/9 | 6/9 |
| alta | media_jornada | 9 | 132.54 | 123.76 | 125.68 | 128.57 | 8.78 | [-40.50; 66.47] | 0.82 | 0.77 | 7.09 | 6.86 | [-55.12; 76.47] | 0.82 | 0.85 | 5.46 | TWAP < VWAP < PPO_sistema | 5/9 | 5/9 |
| baja | apertura | 12 | 27.22 | 15.88 | 13.80 | 20.12 | 11.34 | [-20.02; 45.55] | 0.62 | 0.54 | 71.38 | 13.42 | [-23.66; 53.23] | 0.68 | 0.53 | 97.25 | VWAP < TWAP < PPO_sistema | 5/12 | 5/12 |
| baja | cierre | 9 | 41.28 | 93.40 | 93.40 | 159.34 | -52.11 | [-97.98; -9.94] | 0.07 | 0.06 | -55.80 | -52.11 | [-97.98; -9.94] | 0.07 | 0.06 | -55.80 | PPO_sistema < TWAP < VWAP | 7/9 | 7/9 |
| baja | media_jornada | 9 | 120.81 | 118.91 | 118.70 | 119.23 | 1.89 | [-27.80; 29.46] | 1.00 | 0.91 | 1.59 | 2.10 | [-29.77; 31.14] | 0.82 | 0.90 | 1.77 | VWAP < TWAP < PPO_sistema | 3/9 | 4/9 |
| media | apertura | 12 | 27.67 | 11.17 | 8.15 | 25.35 | 16.49 | [-13.90; 50.33] | 0.68 | 0.36 | 147.63 | 19.52 | [-17.11; 60.40] | 0.57 | 0.37 | 239.55 | VWAP < TWAP < PPO_sistema | 6/12 | 6/12 |
| media | cierre | 9 | 4.83 | 39.18 | 39.18 | 153.30 | -34.35 | [-71.15; 2.69] | 0.13 | 0.12 | -87.67 | -34.35 | [-71.15; 2.69] | 0.13 | 0.12 | -87.67 | PPO_sistema < TWAP < VWAP | 6/9 | 6/9 |
| media | media_jornada | 9 | 115.33 | 114.18 | 120.96 | 124.83 | 1.14 | [-45.74; 50.63] | 1.00 | 0.97 | 1.00 | -5.63 | [-61.98; 52.38] | 1.00 | 0.86 | -4.66 | TWAP < PPO_sistema < VWAP | 4/9 | 5/9 |

## Por activo (slippage crudo, tamaño 1)

| bloque | ticker | n_pares | IS_PPO_sistema | IS_TWAP | IS_VWAP | sd_PPO_sistema | dif_vs_TWAP_bps | dif_vs_TWAP_ic | p_wilcoxon_vs_TWAP | p_ttest_vs_TWAP | dif_vs_TWAP_pct | dif_vs_VWAP_bps | dif_vs_VWAP_ic | p_wilcoxon_vs_VWAP | p_ttest_vs_VWAP | dif_vs_VWAP_pct | ranking | gana_vs_TWAP | gana_vs_VWAP |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| global | COPEC | 27 | 42.05 | 9.20 | 2.91 | 49.95 | 32.85 | [10.30; 54.80] | 0.00 | 0.01 | 357.23 | 39.14 | [11.64; 65.79] | 0.00 | 0.01 | 1345.58 | VWAP < TWAP < PPO_sistema | 5/27 | 5/27 |
| global | ECL | 27 | 110.24 | 111.35 | 115.14 | 122.04 | -1.11 | [-25.16; 24.05] | 0.84 | 0.93 | -0.99 | -4.90 | [-33.14; 24.73] | 0.61 | 0.75 | -4.26 | PPO_sistema < TWAP < VWAP | 15/27 | 17/27 |
| global | FALABELLA | 36 | 32.30 | 64.47 | 65.83 | 141.45 | -32.17 | [-48.54; -17.51] | 0.00 | 0.00 | -49.90 | -33.53 | [-49.84; -18.53] | 0.00 | 0.00 | -50.94 | PPO_sistema < TWAP < VWAP | 26/36 | 26/36 |
| alta | COPEC | 9 | 43.44 | 2.29 | -6.03 | 63.08 | 41.15 | [8.46; 76.73] | 0.05 | 0.06 | 1794.37 | 49.47 | [7.73; 95.20] | 0.05 | 0.07 | 820.06 | VWAP < TWAP < PPO_sistema | 1/9 | 1/9 |
| alta | ECL | 9 | 121.43 | 122.58 | 126.39 | 128.38 | -1.14 | [-46.14; 52.67] | 0.91 | 0.97 | -0.93 | -4.96 | [-62.27; 61.45] | 1.00 | 0.88 | -3.93 | PPO_sistema < TWAP < VWAP | 6/9 | 6/9 |
| alta | FALABELLA | 12 | 49.33 | 69.67 | 71.70 | 164.46 | -20.34 | [-37.23; -3.50] | 0.05 | 0.04 | -29.20 | -22.37 | [-41.79; -4.23] | 0.05 | 0.04 | -31.20 | PPO_sistema < TWAP < VWAP | 8/12 | 8/12 |
| baja | COPEC | 9 | 38.99 | 8.81 | 3.23 | 38.90 | 30.18 | [-3.87; 68.02] | 0.13 | 0.16 | 342.59 | 35.76 | [-3.43; 79.67] | 0.16 | 0.15 | 1107.87 | VWAP < TWAP < PPO_sistema | 2/9 | 2/9 |
| baja | ECL | 9 | 107.97 | 114.43 | 116.27 | 124.86 | -6.47 | [-38.83; 23.52] | 0.91 | 0.72 | -5.65 | -8.30 | [-44.58; 25.59] | 0.65 | 0.68 | -7.14 | PPO_sistema < TWAP < VWAP | 4/9 | 5/9 |
| baja | FALABELLA | 12 | 38.57 | 82.68 | 83.25 | 136.05 | -44.11 | [-78.78; -10.67] | 0.03 | 0.04 | -53.35 | -44.68 | [-79.11; -11.19] | 0.03 | 0.03 | -53.67 | PPO_sistema < TWAP < VWAP | 9/12 | 9/12 |
| media | COPEC | 9 | 43.73 | 16.49 | 11.53 | 51.00 | 27.24 | [-17.64; 70.31] | 0.20 | 0.29 | 165.19 | 32.20 | [-21.79; 84.46] | 0.20 | 0.30 | 279.19 | VWAP < TWAP < PPO_sistema | 2/9 | 2/9 |
| media | ECL | 9 | 101.32 | 97.03 | 102.76 | 126.87 | 4.29 | [-37.98; 51.08] | 0.91 | 0.87 | 4.43 | -1.43 | [-52.24; 52.68] | 0.82 | 0.96 | -1.40 | TWAP < PPO_sistema < VWAP | 5/9 | 6/9 |
| media | FALABELLA | 12 | 9.00 | 41.06 | 42.54 | 130.97 | -32.06 | [-58.85; -4.13] | 0.04 | 0.05 | -78.09 | -33.54 | [-60.33; -5.50] | 0.04 | 0.04 | -78.85 | PPO_sistema < TWAP < VWAP | 9/12 | 9/12 |

## Por estrategia, escenario y tamaño (slippage crudo)

| escenario | factor_tamano | estrategia | n | media | mediana | peor | mejor | cumplimiento_medio | cumplimiento_minimo |
|---|---|---|---|---|---|---|---|---|---|
| alta | 1.00 | PPO_sistema | 30 | 69.19 | 50.16 | 404.54 | -324.75 | 1.00 | 0.95 |
| alta | 1.00 | TWAP | 30 | 65.33 | 56.33 | 376.10 | -329.12 | 0.99 | 0.87 |
| alta | 1.00 | VWAP | 30 | 64.79 | 50.96 | 402.45 | -329.12 | 0.99 | 0.87 |
| baja | 1.00 | PPO_sistema | 30 | 59.51 | 32.45 | 344.51 | -263.04 | 1.00 | 1.00 |
| baja | 1.00 | TWAP | 30 | 70.05 | 44.74 | 522.69 | -323.03 | 1.00 | 0.87 |
| baja | 1.00 | VWAP | 30 | 69.15 | 43.90 | 522.69 | -323.03 | 0.99 | 0.87 |
| media | 0.50 | PPO_sistema | 30 | 38.63 | 25.40 | 266.97 | -292.92 | 1.00 | 1.00 |
| media | 0.50 | TWAP | 30 | 36.43 | 30.11 | 358.44 | -404.89 | 1.00 | 0.99 |
| media | 0.50 | VWAP | 30 | 36.68 | 36.04 | 359.29 | -404.89 | 1.00 | 0.99 |
| media | 1.00 | PPO_sistema | 30 | 47.11 | 38.04 | 285.58 | -311.76 | 1.00 | 0.99 |
| media | 1.00 | TWAP | 30 | 50.48 | 38.13 | 386.76 | -377.94 | 1.00 | 0.87 |
| media | 1.00 | VWAP | 30 | 51.30 | 38.84 | 386.76 | -377.94 | 0.99 | 0.87 |
| media | 1.50 | PPO_sistema | 30 | 51.75 | 52.51 | 349.41 | -310.81 | 0.98 | 0.78 |
| media | 1.50 | TWAP | 30 | 59.63 | 42.98 | 403.03 | -359.38 | 0.99 | 0.83 |
| media | 1.50 | VWAP | 30 | 60.75 | 43.52 | 403.03 | -359.38 | 0.99 | 0.83 |
