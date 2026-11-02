# Monitoreo del entrenamiento (tarea 3.1.4)

**Borrador elaborado por:** PS con apoyo de Claude Code. Panel generado con `scripts/monitorear_entrenamiento.py`.

![Curvas de las corridas](../3_1_1/monitoreo.png)

## Resumen por corrida

| Corrida | Actualizaciones | Episodios registrados | Entropía final (% del máximo) | KL máximo | Cumplimiento final | Pasos en espera (final) | Alertas |
|---|---:|---:|---:|---:|---:|---:|---|
| lr0.0001_minibatch_size128_epochs16_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 68,8 % | 0,01035 | 0,997 | 36 % | 0 críticas, 0 avisos |
| lr0.0001_minibatch_size128_epochs16_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 66,5 % | 0,01178 | 0,994 | 35 % | 0 críticas, 0 avisos |
| lr0.0001_minibatch_size128_epochs4_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 79,9 % | 0,00143 | 0,937 | 46 % | 0 críticas, 1 avisos |
| lr0.0001_minibatch_size128_epochs4_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 82,0 % | 0,00363 | 0,998 | 40 % | 0 críticas, 0 avisos |
| lr0.0001_minibatch_size128_epochs8_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 65,2 % | 0,00647 | 0,993 | 20 % | 0 críticas, 0 avisos |
| lr0.0001_minibatch_size128_epochs8_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 63,8 % | 0,00817 | 0,999 | 23 % | 0 críticas, 0 avisos |
| lr0.0001_minibatch_size32_epochs16_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 64,5 % | 0,01118 | 0,998 | 13 % | 0 críticas, 0 avisos |
| lr0.0001_minibatch_size32_epochs16_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 63,6 % | 0,01235 | 0,995 | 32 % | 0 críticas, 0 avisos |
| lr0.0001_minibatch_size32_epochs4_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 72,4 % | 0,00676 | 0,997 | 27 % | 0 críticas, 0 avisos |
| lr0.0001_minibatch_size32_epochs4_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 65,2 % | 0,00756 | 0,995 | 21 % | 0 críticas, 0 avisos |
| lr0.0001_minibatch_size32_epochs8_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 65,8 % | 0,01016 | 0,998 | 29 % | 0 críticas, 0 avisos |
| lr0.0001_minibatch_size32_epochs8_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 67,5 % | 0,01134 | 0,997 | 22 % | 0 críticas, 0 avisos |
| lr0.0001_minibatch_size64_epochs16_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 68,0 % | 0,01032 | 0,998 | 23 % | 0 críticas, 0 avisos |
| lr0.0001_minibatch_size64_epochs16_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 68,8 % | 0,01209 | 0,999 | 22 % | 0 críticas, 0 avisos |
| lr0.0001_minibatch_size64_epochs4_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 56,5 % | 0,00395 | 0,995 | 26 % | 0 críticas, 0 avisos |
| lr0.0001_minibatch_size64_epochs4_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 64,9 % | 0,00742 | 0,994 | 25 % | 0 críticas, 0 avisos |
| lr0.0001_minibatch_size64_epochs8_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 70,6 % | 0,00823 | 0,996 | 27 % | 0 críticas, 0 avisos |
| lr0.0001_minibatch_size64_epochs8_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 65,4 % | 0,01005 | 0,998 | 17 % | 0 críticas, 0 avisos |
| lr0.0003_minibatch_size128_epochs16_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 69,1 % | 0,01244 | 0,993 | 33 % | 0 críticas, 0 avisos |
| lr0.0003_minibatch_size128_epochs16_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 64,8 % | 0,01364 | 0,995 | 34 % | 0 críticas, 0 avisos |
| lr0.0003_minibatch_size128_epochs4_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 66,2 % | 0,00611 | 0,994 | 17 % | 0 críticas, 0 avisos |
| lr0.0003_minibatch_size128_epochs4_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 57,1 % | 0,00703 | 0,995 | 20 % | 0 críticas, 0 avisos |
| lr0.0003_minibatch_size128_epochs8_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 62,7 % | 0,01337 | 0,997 | 27 % | 0 críticas, 0 avisos |
| lr0.0003_minibatch_size128_epochs8_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 67,4 % | 0,01171 | 0,994 | 28 % | 0 críticas, 0 avisos |
| lr0.0003_minibatch_size32_epochs16_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 62,0 % | 0,01052 | 0,997 | 20 % | 0 críticas, 0 avisos |
| lr0.0003_minibatch_size32_epochs16_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 66,0 % | 0,01108 | 0,995 | 20 % | 0 críticas, 0 avisos |
| lr0.0003_minibatch_size32_epochs4_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 70,8 % | 0,01132 | 0,996 | 29 % | 0 críticas, 0 avisos |
| lr0.0003_minibatch_size32_epochs4_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 61,2 % | 0,01152 | 0,998 | 23 % | 0 críticas, 0 avisos |
| lr0.0003_minibatch_size32_epochs8_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 62,0 % | 0,01052 | 0,997 | 20 % | 0 críticas, 0 avisos |
| lr0.0003_minibatch_size32_epochs8_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 65,8 % | 0,01125 | 0,997 | 20 % | 0 críticas, 0 avisos |
| lr0.0003_minibatch_size64_epochs16_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 76,8 % | 0,01225 | 0,999 | 24 % | 0 críticas, 0 avisos |
| lr0.0003_minibatch_size64_epochs16_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 43,7 % | 0,01056 | 0,998 | 18 % | 0 críticas, 0 avisos |
| lr0.0003_minibatch_size64_epochs4_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 68,4 % | 0,01175 | 0,998 | 19 % | 0 críticas, 0 avisos |
| lr0.0003_minibatch_size64_epochs4_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 56,2 % | 0,00983 | 0,993 | 20 % | 0 críticas, 0 avisos |
| lr0.0003_minibatch_size64_epochs8_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 64,2 % | 0,01179 | 0,996 | 29 % | 0 críticas, 0 avisos |
| lr0.0003_minibatch_size64_epochs8_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 67,0 % | 0,01558 | 0,997 | 22 % | 0 críticas, 0 avisos |
| lr0.001_minibatch_size128_epochs16_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 63,2 % | 0,01382 | 0,992 | 36 % | 0 críticas, 0 avisos |
| lr0.001_minibatch_size128_epochs16_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 49,9 % | 0,01595 | 0,992 | 27 % | 0 críticas, 0 avisos |
| lr0.001_minibatch_size128_epochs4_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 66,6 % | 0,01372 | 0,997 | 21 % | 0 críticas, 0 avisos |
| lr0.001_minibatch_size128_epochs4_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 42,6 % | 0,01350 | 0,998 | 34 % | 0 críticas, 0 avisos |
| lr0.001_minibatch_size128_epochs8_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 43,0 % | 0,01337 | 1,000 | 12 % | 0 críticas, 0 avisos |
| lr0.001_minibatch_size128_epochs8_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 46,5 % | 0,01595 | 0,997 | 12 % | 0 críticas, 0 avisos |
| lr0.001_minibatch_size32_epochs16_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 51,9 % | 0,01328 | 0,993 | 22 % | 0 críticas, 0 avisos |
| lr0.001_minibatch_size32_epochs16_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 65,2 % | 0,01600 | 0,998 | 31 % | 0 críticas, 0 avisos |
| lr0.001_minibatch_size32_epochs4_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 51,9 % | 0,01328 | 0,993 | 22 % | 0 críticas, 0 avisos |
| lr0.001_minibatch_size32_epochs4_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 65,2 % | 0,01600 | 0,998 | 31 % | 0 críticas, 0 avisos |
| lr0.001_minibatch_size32_epochs8_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 51,9 % | 0,01328 | 0,993 | 22 % | 0 críticas, 0 avisos |
| lr0.001_minibatch_size32_epochs8_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 65,2 % | 0,01600 | 0,998 | 31 % | 0 críticas, 0 avisos |
| lr0.001_minibatch_size64_epochs16_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 47,4 % | 0,01869 | 0,998 | 13 % | 0 críticas, 0 avisos |
| lr0.001_minibatch_size64_epochs16_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 50,1 % | 0,01435 | 0,996 | 20 % | 0 críticas, 0 avisos |
| lr0.001_minibatch_size64_epochs4_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 42,0 % | 0,01376 | 0,995 | 13 % | 0 críticas, 0 avisos |
| lr0.001_minibatch_size64_epochs4_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 50,0 % | 0,02439 | 0,997 | 19 % | 0 críticas, 1 avisos |
| lr0.001_minibatch_size64_epochs8_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 47,4 % | 0,01869 | 0,998 | 13 % | 0 críticas, 0 avisos |
| lr0.001_minibatch_size64_epochs8_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 50,1 % | 0,01435 | 0,996 | 20 % | 0 críticas, 0 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 31,1 % | 0,03045 | 0,999 | 6 % | 0 críticas, 2 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 18,2 % | 0,04227 | 0,999 | 6 % | 0 críticas, 2 avisos |
| lr0.003_minibatch_size128_epochs4_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 45,8 % | 0,03045 | 0,998 | 17 % | 0 críticas, 1 avisos |
| lr0.003_minibatch_size128_epochs4_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 45,2 % | 0,03908 | 0,998 | 19 % | 0 críticas, 1 avisos |
| lr0.003_minibatch_size128_epochs8_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 31,1 % | 0,03045 | 0,999 | 6 % | 0 críticas, 2 avisos |
| lr0.003_minibatch_size128_epochs8_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 18,2 % | 0,04227 | 0,999 | 6 % | 0 críticas, 2 avisos |
| lr0.003_minibatch_size32_epochs16_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 46,6 % | 0,05917 | 0,995 | 24 % | 0 críticas, 1 avisos |
| lr0.003_minibatch_size32_epochs16_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 0,0 % | 0,05243 | 0,000 | 100 % | 2 críticas, 3 avisos |
| lr0.003_minibatch_size32_epochs4_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 46,6 % | 0,05917 | 0,995 | 24 % | 0 críticas, 1 avisos |
| lr0.003_minibatch_size32_epochs4_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 0,0 % | 0,05243 | 0,000 | 100 % | 2 críticas, 3 avisos |
| lr0.003_minibatch_size32_epochs8_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 46,6 % | 0,05917 | 0,995 | 24 % | 0 críticas, 1 avisos |
| lr0.003_minibatch_size32_epochs8_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 0,0 % | 0,05243 | 0,000 | 100 % | 2 críticas, 3 avisos |
| lr0.003_minibatch_size64_epochs16_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 22,1 % | 0,03170 | 1,000 | 21 % | 0 críticas, 2 avisos |
| lr0.003_minibatch_size64_epochs16_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 31,2 % | 0,03012 | 0,989 | 6 % | 0 críticas, 2 avisos |
| lr0.003_minibatch_size64_epochs4_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 22,1 % | 0,03170 | 1,000 | 21 % | 0 críticas, 2 avisos |
| lr0.003_minibatch_size64_epochs4_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 31,2 % | 0,03012 | 0,989 | 6 % | 0 críticas, 2 avisos |
| lr0.003_minibatch_size64_epochs8_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 22,1 % | 0,03170 | 1,000 | 21 % | 0 críticas, 2 avisos |
| lr0.003_minibatch_size64_epochs8_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 31,2 % | 0,03012 | 0,989 | 6 % | 0 críticas, 2 avisos |

## Alertas

**lr0.0001_minibatch_size128_epochs16_clip_ratio0.2_gae_lambda0.95_s1000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 73 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.0001_minibatch_size128_epochs16_clip_ratio0.2_gae_lambda0.95_s2000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 66 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.0001_minibatch_size128_epochs4_clip_ratio0.2_gae_lambda0.95_s1000**

- **AVISO** `CUMPLIMIENTO_BAJO`: Cumplimiento medio 0.937 en los ultimos 50 episodios (< 0.95): regla de vigilancia de D3.
- **INFO** `ENTROPIA_BAJA`: Entropia al 79 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.0001_minibatch_size128_epochs4_clip_ratio0.2_gae_lambda0.95_s2000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 80 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.0001_minibatch_size128_epochs8_clip_ratio0.2_gae_lambda0.95_s1000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 61 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.0001_minibatch_size128_epochs8_clip_ratio0.2_gae_lambda0.95_s2000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 64 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.0001_minibatch_size32_epochs16_clip_ratio0.2_gae_lambda0.95_s1000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 68 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.0001_minibatch_size32_epochs16_clip_ratio0.2_gae_lambda0.95_s2000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 60 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.0001_minibatch_size32_epochs4_clip_ratio0.2_gae_lambda0.95_s1000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 72 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.0001_minibatch_size32_epochs4_clip_ratio0.2_gae_lambda0.95_s2000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 61 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.0001_minibatch_size32_epochs8_clip_ratio0.2_gae_lambda0.95_s1000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 66 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.0001_minibatch_size32_epochs8_clip_ratio0.2_gae_lambda0.95_s2000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 65 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.0001_minibatch_size64_epochs16_clip_ratio0.2_gae_lambda0.95_s1000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 68 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.0001_minibatch_size64_epochs16_clip_ratio0.2_gae_lambda0.95_s2000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 68 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.0001_minibatch_size64_epochs4_clip_ratio0.2_gae_lambda0.95_s1000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 59 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.0001_minibatch_size64_epochs4_clip_ratio0.2_gae_lambda0.95_s2000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 65 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.0001_minibatch_size64_epochs8_clip_ratio0.2_gae_lambda0.95_s1000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 72 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.0001_minibatch_size64_epochs8_clip_ratio0.2_gae_lambda0.95_s2000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 68 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.0003_minibatch_size128_epochs16_clip_ratio0.2_gae_lambda0.95_s1000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 69 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.0003_minibatch_size128_epochs16_clip_ratio0.2_gae_lambda0.95_s2000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 67 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.0003_minibatch_size128_epochs4_clip_ratio0.2_gae_lambda0.95_s1000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 60 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.0003_minibatch_size128_epochs4_clip_ratio0.2_gae_lambda0.95_s2000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 57 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.0003_minibatch_size128_epochs8_clip_ratio0.2_gae_lambda0.95_s1000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 68 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.0003_minibatch_size128_epochs8_clip_ratio0.2_gae_lambda0.95_s2000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 66 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.0003_minibatch_size32_epochs16_clip_ratio0.2_gae_lambda0.95_s1000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 60 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.0003_minibatch_size32_epochs16_clip_ratio0.2_gae_lambda0.95_s2000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 66 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.0003_minibatch_size32_epochs4_clip_ratio0.2_gae_lambda0.95_s1000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 72 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.0003_minibatch_size32_epochs4_clip_ratio0.2_gae_lambda0.95_s2000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 60 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.0003_minibatch_size32_epochs8_clip_ratio0.2_gae_lambda0.95_s1000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 60 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.0003_minibatch_size32_epochs8_clip_ratio0.2_gae_lambda0.95_s2000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 67 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.0003_minibatch_size64_epochs16_clip_ratio0.2_gae_lambda0.95_s1000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 74 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.0003_minibatch_size64_epochs16_clip_ratio0.2_gae_lambda0.95_s2000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 46 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.0003_minibatch_size64_epochs4_clip_ratio0.2_gae_lambda0.95_s1000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 69 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.0003_minibatch_size64_epochs4_clip_ratio0.2_gae_lambda0.95_s2000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 51 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.0003_minibatch_size64_epochs8_clip_ratio0.2_gae_lambda0.95_s1000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 68 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.0003_minibatch_size64_epochs8_clip_ratio0.2_gae_lambda0.95_s2000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 67 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.001_minibatch_size128_epochs16_clip_ratio0.2_gae_lambda0.95_s1000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 62 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.001_minibatch_size128_epochs16_clip_ratio0.2_gae_lambda0.95_s2000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 52 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.001_minibatch_size128_epochs4_clip_ratio0.2_gae_lambda0.95_s1000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 64 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.001_minibatch_size128_epochs4_clip_ratio0.2_gae_lambda0.95_s2000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 47 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.001_minibatch_size128_epochs8_clip_ratio0.2_gae_lambda0.95_s1000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 41 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.001_minibatch_size128_epochs8_clip_ratio0.2_gae_lambda0.95_s2000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 44 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.001_minibatch_size32_epochs16_clip_ratio0.2_gae_lambda0.95_s1000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 56 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.001_minibatch_size32_epochs16_clip_ratio0.2_gae_lambda0.95_s2000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 65 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.001_minibatch_size32_epochs4_clip_ratio0.2_gae_lambda0.95_s1000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 56 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.001_minibatch_size32_epochs4_clip_ratio0.2_gae_lambda0.95_s2000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 65 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.001_minibatch_size32_epochs8_clip_ratio0.2_gae_lambda0.95_s1000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 56 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.001_minibatch_size32_epochs8_clip_ratio0.2_gae_lambda0.95_s2000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 65 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.001_minibatch_size64_epochs16_clip_ratio0.2_gae_lambda0.95_s1000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 48 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.001_minibatch_size64_epochs16_clip_ratio0.2_gae_lambda0.95_s2000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 52 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.001_minibatch_size64_epochs4_clip_ratio0.2_gae_lambda0.95_s1000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 44 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.001_minibatch_size64_epochs4_clip_ratio0.2_gae_lambda0.95_s2000**

- **AVISO** `KL_ALTO`: KL maximo 0.0244 (> 0.02).
- **INFO** `ENTROPIA_BAJA`: Entropia al 54 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.001_minibatch_size64_epochs8_clip_ratio0.2_gae_lambda0.95_s1000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 48 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.001_minibatch_size64_epochs8_clip_ratio0.2_gae_lambda0.95_s2000**

- **INFO** `ENTROPIA_BAJA`: Entropia al 52 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.003_minibatch_size128_epochs16_clip_ratio0.2_gae_lambda0.95_s1000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 36 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0304 (> 0.02).

**lr0.003_minibatch_size128_epochs16_clip_ratio0.2_gae_lambda0.95_s2000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 23 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0423 (> 0.02).

**lr0.003_minibatch_size128_epochs4_clip_ratio0.2_gae_lambda0.95_s1000**

- **AVISO** `KL_ALTO`: KL maximo 0.0304 (> 0.02).
- **INFO** `ENTROPIA_BAJA`: Entropia al 47 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.003_minibatch_size128_epochs4_clip_ratio0.2_gae_lambda0.95_s2000**

- **AVISO** `KL_ALTO`: KL maximo 0.0391 (> 0.02).
- **INFO** `ENTROPIA_BAJA`: Entropia al 52 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.003_minibatch_size128_epochs8_clip_ratio0.2_gae_lambda0.95_s1000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 36 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0304 (> 0.02).

**lr0.003_minibatch_size128_epochs8_clip_ratio0.2_gae_lambda0.95_s2000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 23 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0423 (> 0.02).

**lr0.003_minibatch_size32_epochs16_clip_ratio0.2_gae_lambda0.95_s1000**

- **AVISO** `KL_ALTO`: KL maximo 0.0592 (> 0.02).
- **INFO** `ENTROPIA_BAJA`: Entropia al 51 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.003_minibatch_size32_epochs16_clip_ratio0.2_gae_lambda0.95_s2000**

- **CRITICA** `CUMPLIMIENTO_CRITICO`: Cumplimiento medio 0.000 en los ultimos 50 episodios (< 0.5).
- **CRITICA** `ENTROPIA_COLAPSADA`: Entropia al 0 % del maximo: la politica casi no explora.
- **AVISO** `ESPERA_ALTA`: La politica espera en el 100 % de los pasos (ultimos 50 episodios).
- **AVISO** `ESPERA_EN_AUMENTO`: La fraccion de pasos en espera subio de 29 % a 100 %: la politica puede estar aprendiendo a no ejecutar (R_E sin costo por esperar).
- **AVISO** `KL_ALTO`: KL maximo 0.0524 (> 0.02).
- **INFO** `SIN_MEJORA`: El retorno medio no mejora: -11.69 (primeros 50) frente a -17.40 (ultimos 50).

**lr0.003_minibatch_size32_epochs4_clip_ratio0.2_gae_lambda0.95_s1000**

- **AVISO** `KL_ALTO`: KL maximo 0.0592 (> 0.02).
- **INFO** `ENTROPIA_BAJA`: Entropia al 51 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.003_minibatch_size32_epochs4_clip_ratio0.2_gae_lambda0.95_s2000**

- **CRITICA** `CUMPLIMIENTO_CRITICO`: Cumplimiento medio 0.000 en los ultimos 50 episodios (< 0.5).
- **CRITICA** `ENTROPIA_COLAPSADA`: Entropia al 0 % del maximo: la politica casi no explora.
- **AVISO** `ESPERA_ALTA`: La politica espera en el 100 % de los pasos (ultimos 50 episodios).
- **AVISO** `ESPERA_EN_AUMENTO`: La fraccion de pasos en espera subio de 29 % a 100 %: la politica puede estar aprendiendo a no ejecutar (R_E sin costo por esperar).
- **AVISO** `KL_ALTO`: KL maximo 0.0524 (> 0.02).
- **INFO** `SIN_MEJORA`: El retorno medio no mejora: -11.69 (primeros 50) frente a -17.40 (ultimos 50).

**lr0.003_minibatch_size32_epochs8_clip_ratio0.2_gae_lambda0.95_s1000**

- **AVISO** `KL_ALTO`: KL maximo 0.0592 (> 0.02).
- **INFO** `ENTROPIA_BAJA`: Entropia al 51 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.003_minibatch_size32_epochs8_clip_ratio0.2_gae_lambda0.95_s2000**

- **CRITICA** `CUMPLIMIENTO_CRITICO`: Cumplimiento medio 0.000 en los ultimos 50 episodios (< 0.5).
- **CRITICA** `ENTROPIA_COLAPSADA`: Entropia al 0 % del maximo: la politica casi no explora.
- **AVISO** `ESPERA_ALTA`: La politica espera en el 100 % de los pasos (ultimos 50 episodios).
- **AVISO** `ESPERA_EN_AUMENTO`: La fraccion de pasos en espera subio de 29 % a 100 %: la politica puede estar aprendiendo a no ejecutar (R_E sin costo por esperar).
- **AVISO** `KL_ALTO`: KL maximo 0.0524 (> 0.02).
- **INFO** `SIN_MEJORA`: El retorno medio no mejora: -11.69 (primeros 50) frente a -17.40 (ultimos 50).

**lr0.003_minibatch_size64_epochs16_clip_ratio0.2_gae_lambda0.95_s1000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 22 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0317 (> 0.02).

**lr0.003_minibatch_size64_epochs16_clip_ratio0.2_gae_lambda0.95_s2000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 37 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0301 (> 0.02).

**lr0.003_minibatch_size64_epochs4_clip_ratio0.2_gae_lambda0.95_s1000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 22 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0317 (> 0.02).

**lr0.003_minibatch_size64_epochs4_clip_ratio0.2_gae_lambda0.95_s2000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 37 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0301 (> 0.02).

**lr0.003_minibatch_size64_epochs8_clip_ratio0.2_gae_lambda0.95_s1000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 22 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0317 (> 0.02).

**lr0.003_minibatch_size64_epochs8_clip_ratio0.2_gae_lambda0.95_s2000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 37 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0301 (> 0.02).

## Cómo leerlo

- **Entropía:** una política uniforme sobre las 240 acciones tiene 5,48 nats. Una caída fuerte significa que la política se concentra; conviene evaluar también con muestreo y no solo con argmax (ver `docs/entrenamiento_inicial_2.3.5.md`).
- **Pasos en espera:** acciones `LIMIT_SELL`, que el puente de ABIDES y el simulador Poisson tratan como «esperar».
- Sin el CSV de monitoreo por episodio solo se muestran las curvas del entrenador; el costo y el cumplimiento por episodio se registran con `MonitorEntrenamiento` (`src/training/monitoreo.py`).

🤖 Generado con [Claude Code](https://claude.com/claude-code)
