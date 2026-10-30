# Monitoreo del entrenamiento (tarea 3.1.4)

**Borrador elaborado por:** PS con apoyo de Claude Code. Panel generado con `scripts/monitorear_entrenamiento.py`.

![Curvas de las corridas](../3_1_2/monitoreo.png)

## Resumen por corrida

| Corrida | Actualizaciones | Episodios registrados | Entropía final (% del máximo) | KL máximo | Cumplimiento final | Pasos en espera (final) | Alertas |
|---|---:|---:|---:|---:|---:|---:|---|
| lr0.003_minibatch_size128_epochs16_clip_ratio0.102_gae_lambda0.961_s1000 | 100 | 1000 | 62,7 % | 0,02393 | 0,991 | 43 % | 0 críticas, 2 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.102_gae_lambda0.961_s2000 | 100 | 1000 | 34,0 % | 0,04365 | 0,991 | 27 % | 0 críticas, 3 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.117_gae_lambda0.988_s1000 | 100 | 1000 | 52,0 % | 0,02683 | 0,997 | 18 % | 0 críticas, 1 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.117_gae_lambda0.988_s2000 | 100 | 1000 | 60,0 % | 0,02243 | 0,999 | 18 % | 0 críticas, 1 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.129_gae_lambda0.933_s1000 | 100 | 1000 | 44,4 % | 0,02337 | 1,000 | 24 % | 0 críticas, 1 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.129_gae_lambda0.933_s2000 | 100 | 1000 | 22,4 % | 0,04039 | 0,999 | 12 % | 0 críticas, 2 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.134_gae_lambda0.984_s1000 | 100 | 1000 | 63,2 % | 0,03423 | 0,997 | 23 % | 0 críticas, 1 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.134_gae_lambda0.984_s2000 | 100 | 1000 | 55,0 % | 0,02654 | 0,994 | 25 % | 0 críticas, 1 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.137_gae_lambda0.936_s1000 | 100 | 1000 | 43,4 % | 0,04292 | 1,000 | 17 % | 0 críticas, 1 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.137_gae_lambda0.936_s2000 | 100 | 1000 | 35,4 % | 0,02490 | 0,996 | 8 % | 0 críticas, 2 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.158_gae_lambda0.944_s1000 | 100 | 1000 | 37,8 % | 0,02865 | 0,999 | 13 % | 0 críticas, 1 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.158_gae_lambda0.944_s2000 | 100 | 1000 | 38,5 % | 0,02836 | 0,995 | 26 % | 0 críticas, 2 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.16_gae_lambda0.911_s1000 | 100 | 1000 | 31,8 % | 0,02837 | 0,966 | 41 % | 0 críticas, 2 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.16_gae_lambda0.911_s2000 | 100 | 1000 | 45,5 % | 0,06472 | 1,000 | 20 % | 0 críticas, 1 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.194_gae_lambda0.925_s1000 | 100 | 1000 | 38,5 % | 0,03345 | 1,000 | 19 % | 0 críticas, 1 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.194_gae_lambda0.925_s2000 | 100 | 1000 | 11,2 % | 0,04309 | 0,858 | 43 % | 1 críticas, 2 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.195_gae_lambda0.932_s1000 | 100 | 1000 | 40,3 % | 0,03298 | 1,000 | 18 % | 0 críticas, 1 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.195_gae_lambda0.932_s2000 | 100 | 1000 | 43,8 % | 0,02396 | 0,991 | 26 % | 0 críticas, 1 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.199_gae_lambda0.964_s1000 | 100 | 1000 | 58,7 % | 0,02965 | 0,997 | 20 % | 0 críticas, 1 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.199_gae_lambda0.964_s2000 | 100 | 1000 | 22,5 % | 0,02969 | 1,000 | 3 % | 0 críticas, 2 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.207_gae_lambda0.926_s1000 | 100 | 1000 | 13,9 % | 0,03159 | 0,996 | 16 % | 0 críticas, 2 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.207_gae_lambda0.926_s2000 | 100 | 1000 | 21,4 % | 0,03161 | 0,996 | 8 % | 0 críticas, 2 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.212_gae_lambda0.902_s1000 | 100 | 1000 | 38,7 % | 0,04396 | 0,933 | 44 % | 1 críticas, 2 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.212_gae_lambda0.902_s2000 | 100 | 1000 | 2,4 % | 0,02708 | 1,000 | 0 % | 0 críticas, 2 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.219_gae_lambda0.915_s1000 | 100 | 1000 | 38,0 % | 0,04503 | 1,000 | 10 % | 0 críticas, 2 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.219_gae_lambda0.915_s2000 | 100 | 1000 | 29,9 % | 0,03874 | 1,000 | 32 % | 0 críticas, 2 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.21_gae_lambda0.925_s1000 | 100 | 1000 | 25,6 % | 0,03020 | 0,980 | 34 % | 0 críticas, 2 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.21_gae_lambda0.925_s2000 | 100 | 1000 | 57,4 % | 0,03828 | 0,993 | 36 % | 0 críticas, 1 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.21_gae_lambda0.936_s1000 | 100 | 1000 | 24,0 % | 0,02979 | 0,995 | 25 % | 0 críticas, 2 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.21_gae_lambda0.936_s2000 | 100 | 1000 | 30,3 % | 0,03619 | 0,990 | 22 % | 0 críticas, 2 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.229_gae_lambda0.947_s1000 | 100 | 1000 | 49,1 % | 0,02857 | 0,997 | 16 % | 0 críticas, 1 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.229_gae_lambda0.947_s2000 | 100 | 1000 | 36,6 % | 0,02896 | 0,991 | 27 % | 0 críticas, 2 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.237_gae_lambda0.908_s1000 | 100 | 1000 | 39,7 % | 0,03109 | 0,996 | 21 % | 0 críticas, 2 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.237_gae_lambda0.908_s2000 | 100 | 1000 | 0,0 % | 0,03398 | 0,000 | 100 % | 2 críticas, 3 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.239_gae_lambda0.973_s1000 | 100 | 1000 | 29,2 % | 0,05058 | 1,000 | 4 % | 0 críticas, 2 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.239_gae_lambda0.973_s2000 | 100 | 1000 | 29,3 % | 0,06371 | 1,000 | 9 % | 0 críticas, 2 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.249_gae_lambda0.907_s1000 | 100 | 1000 | 31,0 % | 0,02290 | 0,995 | 16 % | 0 críticas, 2 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.249_gae_lambda0.907_s2000 | 100 | 1000 | 12,1 % | 0,03436 | 1,000 | 7 % | 0 críticas, 2 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.262_gae_lambda0.932_s1000 | 100 | 1000 | 43,2 % | 0,03072 | 0,999 | 17 % | 0 críticas, 1 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.262_gae_lambda0.932_s2000 | 100 | 1000 | 49,6 % | 0,03295 | 0,997 | 20 % | 0 críticas, 1 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.276_gae_lambda0.947_s1000 | 100 | 1000 | 43,4 % | 0,03120 | 0,996 | 24 % | 0 críticas, 2 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.276_gae_lambda0.947_s2000 | 100 | 1000 | 35,9 % | 0,03103 | 0,984 | 16 % | 0 críticas, 2 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.278_gae_lambda0.919_s1000 | 100 | 1000 | 32,4 % | 0,03204 | 0,980 | 36 % | 0 críticas, 2 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.278_gae_lambda0.919_s2000 | 100 | 1000 | 34,7 % | 0,03311 | 0,999 | 12 % | 0 críticas, 1 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.289_gae_lambda1_s1000 | 100 | 1000 | 38,1 % | 0,02271 | 0,998 | 14 % | 0 críticas, 2 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.289_gae_lambda1_s2000 | 100 | 1000 | 62,4 % | 0,03508 | 0,997 | 36 % | 0 críticas, 1 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.295_gae_lambda0.98_s1000 | 100 | 1000 | 61,9 % | 0,03329 | 0,999 | 25 % | 0 críticas, 1 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.295_gae_lambda0.98_s2000 | 100 | 1000 | 47,5 % | 0,03593 | 1,000 | 20 % | 0 críticas, 1 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.2_gae_lambda0.95_s1000 | 100 | 1000 | 31,1 % | 0,03045 | 0,999 | 6 % | 0 críticas, 2 avisos |
| lr0.003_minibatch_size128_epochs16_clip_ratio0.2_gae_lambda0.95_s2000 | 100 | 1000 | 18,2 % | 0,04227 | 0,999 | 6 % | 0 críticas, 2 avisos |

## Alertas

**lr0.003_minibatch_size128_epochs16_clip_ratio0.102_gae_lambda0.961_s1000**

- **AVISO** `KL_ALTO`: KL maximo 0.0239 (> 0.02).
- **AVISO** `RECORTE_ALTO`: Fraccion recortada media 0.33 (> 0.3): las actualizaciones son demasiado grandes.
- **INFO** `ENTROPIA_BAJA`: Entropia al 64 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.003_minibatch_size128_epochs16_clip_ratio0.102_gae_lambda0.961_s2000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 35 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0436 (> 0.02).
- **AVISO** `RECORTE_ALTO`: Fraccion recortada media 0.30 (> 0.3): las actualizaciones son demasiado grandes.

**lr0.003_minibatch_size128_epochs16_clip_ratio0.117_gae_lambda0.988_s1000**

- **AVISO** `KL_ALTO`: KL maximo 0.0268 (> 0.02).
- **INFO** `ENTROPIA_BAJA`: Entropia al 58 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.003_minibatch_size128_epochs16_clip_ratio0.117_gae_lambda0.988_s2000**

- **AVISO** `KL_ALTO`: KL maximo 0.0224 (> 0.02).
- **INFO** `ENTROPIA_BAJA`: Entropia al 55 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.003_minibatch_size128_epochs16_clip_ratio0.129_gae_lambda0.933_s1000**

- **AVISO** `KL_ALTO`: KL maximo 0.0234 (> 0.02).
- **INFO** `ENTROPIA_BAJA`: Entropia al 43 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.003_minibatch_size128_epochs16_clip_ratio0.129_gae_lambda0.933_s2000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 23 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0404 (> 0.02).

**lr0.003_minibatch_size128_epochs16_clip_ratio0.134_gae_lambda0.984_s1000**

- **AVISO** `KL_ALTO`: KL maximo 0.0342 (> 0.02).
- **INFO** `ENTROPIA_BAJA`: Entropia al 61 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.003_minibatch_size128_epochs16_clip_ratio0.134_gae_lambda0.984_s2000**

- **AVISO** `KL_ALTO`: KL maximo 0.0265 (> 0.02).
- **INFO** `ENTROPIA_BAJA`: Entropia al 57 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.003_minibatch_size128_epochs16_clip_ratio0.137_gae_lambda0.936_s1000**

- **AVISO** `KL_ALTO`: KL maximo 0.0429 (> 0.02).
- **INFO** `ENTROPIA_BAJA`: Entropia al 46 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.003_minibatch_size128_epochs16_clip_ratio0.137_gae_lambda0.936_s2000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 39 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0249 (> 0.02).

**lr0.003_minibatch_size128_epochs16_clip_ratio0.158_gae_lambda0.944_s1000**

- **AVISO** `KL_ALTO`: KL maximo 0.0286 (> 0.02).
- **INFO** `ENTROPIA_BAJA`: Entropia al 42 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.003_minibatch_size128_epochs16_clip_ratio0.158_gae_lambda0.944_s2000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 38 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0284 (> 0.02).

**lr0.003_minibatch_size128_epochs16_clip_ratio0.16_gae_lambda0.911_s1000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 37 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0284 (> 0.02).

**lr0.003_minibatch_size128_epochs16_clip_ratio0.16_gae_lambda0.911_s2000**

- **AVISO** `KL_ALTO`: KL maximo 0.0647 (> 0.02).
- **INFO** `ENTROPIA_BAJA`: Entropia al 47 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.003_minibatch_size128_epochs16_clip_ratio0.194_gae_lambda0.925_s1000**

- **AVISO** `KL_ALTO`: KL maximo 0.0334 (> 0.02).
- **INFO** `ENTROPIA_BAJA`: Entropia al 51 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.003_minibatch_size128_epochs16_clip_ratio0.194_gae_lambda0.925_s2000**

- **CRITICA** `ENTROPIA_COLAPSADA`: Entropia al 14 % del maximo: la politica casi no explora.
- **AVISO** `CUMPLIMIENTO_BAJO`: Cumplimiento medio 0.858 en los ultimos 50 episodios (< 0.95): regla de vigilancia de D3.
- **AVISO** `KL_ALTO`: KL maximo 0.0431 (> 0.02).

**lr0.003_minibatch_size128_epochs16_clip_ratio0.195_gae_lambda0.932_s1000**

- **AVISO** `KL_ALTO`: KL maximo 0.0330 (> 0.02).
- **INFO** `ENTROPIA_BAJA`: Entropia al 44 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.003_minibatch_size128_epochs16_clip_ratio0.195_gae_lambda0.932_s2000**

- **AVISO** `KL_ALTO`: KL maximo 0.0240 (> 0.02).
- **INFO** `ENTROPIA_BAJA`: Entropia al 41 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.003_minibatch_size128_epochs16_clip_ratio0.199_gae_lambda0.964_s1000**

- **AVISO** `KL_ALTO`: KL maximo 0.0296 (> 0.02).
- **INFO** `ENTROPIA_BAJA`: Entropia al 58 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.003_minibatch_size128_epochs16_clip_ratio0.199_gae_lambda0.964_s2000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 26 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0297 (> 0.02).

**lr0.003_minibatch_size128_epochs16_clip_ratio0.207_gae_lambda0.926_s1000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 16 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0316 (> 0.02).

**lr0.003_minibatch_size128_epochs16_clip_ratio0.207_gae_lambda0.926_s2000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 27 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0316 (> 0.02).

**lr0.003_minibatch_size128_epochs16_clip_ratio0.212_gae_lambda0.902_s1000**

- **CRITICA** `ENTROPIA_COLAPSADA`: Entropia al 33 % del maximo: la politica casi no explora.
- **AVISO** `CUMPLIMIENTO_BAJO`: Cumplimiento medio 0.933 en los ultimos 50 episodios (< 0.95): regla de vigilancia de D3.
- **AVISO** `KL_ALTO`: KL maximo 0.0440 (> 0.02).

**lr0.003_minibatch_size128_epochs16_clip_ratio0.212_gae_lambda0.902_s2000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 3 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0271 (> 0.02).

**lr0.003_minibatch_size128_epochs16_clip_ratio0.219_gae_lambda0.915_s1000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 37 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0450 (> 0.02).

**lr0.003_minibatch_size128_epochs16_clip_ratio0.219_gae_lambda0.915_s2000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 34 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0387 (> 0.02).

**lr0.003_minibatch_size128_epochs16_clip_ratio0.21_gae_lambda0.925_s1000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 28 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0302 (> 0.02).

**lr0.003_minibatch_size128_epochs16_clip_ratio0.21_gae_lambda0.925_s2000**

- **AVISO** `KL_ALTO`: KL maximo 0.0383 (> 0.02).
- **INFO** `ENTROPIA_BAJA`: Entropia al 60 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.003_minibatch_size128_epochs16_clip_ratio0.21_gae_lambda0.936_s1000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 27 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0298 (> 0.02).

**lr0.003_minibatch_size128_epochs16_clip_ratio0.21_gae_lambda0.936_s2000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 32 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0362 (> 0.02).

**lr0.003_minibatch_size128_epochs16_clip_ratio0.229_gae_lambda0.947_s1000**

- **AVISO** `KL_ALTO`: KL maximo 0.0286 (> 0.02).
- **INFO** `ENTROPIA_BAJA`: Entropia al 44 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.003_minibatch_size128_epochs16_clip_ratio0.229_gae_lambda0.947_s2000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 37 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0290 (> 0.02).

**lr0.003_minibatch_size128_epochs16_clip_ratio0.237_gae_lambda0.908_s1000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 38 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0311 (> 0.02).

**lr0.003_minibatch_size128_epochs16_clip_ratio0.237_gae_lambda0.908_s2000**

- **CRITICA** `CUMPLIMIENTO_CRITICO`: Cumplimiento medio 0.000 en los ultimos 50 episodios (< 0.5).
- **CRITICA** `ENTROPIA_COLAPSADA`: Entropia al 0 % del maximo: la politica casi no explora.
- **AVISO** `ESPERA_ALTA`: La politica espera en el 100 % de los pasos (ultimos 50 episodios).
- **AVISO** `ESPERA_EN_AUMENTO`: La fraccion de pasos en espera subio de 30 % a 100 %: la politica puede estar aprendiendo a no ejecutar (R_E sin costo por esperar).
- **AVISO** `KL_ALTO`: KL maximo 0.0340 (> 0.02).
- **INFO** `SIN_MEJORA`: El retorno medio no mejora: -11.73 (primeros 50) frente a -17.40 (ultimos 50).

**lr0.003_minibatch_size128_epochs16_clip_ratio0.239_gae_lambda0.973_s1000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 23 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0506 (> 0.02).

**lr0.003_minibatch_size128_epochs16_clip_ratio0.239_gae_lambda0.973_s2000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 29 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0637 (> 0.02).

**lr0.003_minibatch_size128_epochs16_clip_ratio0.249_gae_lambda0.907_s1000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 28 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0229 (> 0.02).

**lr0.003_minibatch_size128_epochs16_clip_ratio0.249_gae_lambda0.907_s2000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 13 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0344 (> 0.02).

**lr0.003_minibatch_size128_epochs16_clip_ratio0.262_gae_lambda0.932_s1000**

- **AVISO** `KL_ALTO`: KL maximo 0.0307 (> 0.02).
- **INFO** `ENTROPIA_BAJA`: Entropia al 43 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.003_minibatch_size128_epochs16_clip_ratio0.262_gae_lambda0.932_s2000**

- **AVISO** `KL_ALTO`: KL maximo 0.0330 (> 0.02).
- **INFO** `ENTROPIA_BAJA`: Entropia al 59 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.003_minibatch_size128_epochs16_clip_ratio0.276_gae_lambda0.947_s1000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 37 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0312 (> 0.02).

**lr0.003_minibatch_size128_epochs16_clip_ratio0.276_gae_lambda0.947_s2000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 29 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0310 (> 0.02).

**lr0.003_minibatch_size128_epochs16_clip_ratio0.278_gae_lambda0.919_s1000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 35 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0320 (> 0.02).

**lr0.003_minibatch_size128_epochs16_clip_ratio0.278_gae_lambda0.919_s2000**

- **AVISO** `KL_ALTO`: KL maximo 0.0331 (> 0.02).
- **INFO** `ENTROPIA_BAJA`: Entropia al 40 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.003_minibatch_size128_epochs16_clip_ratio0.289_gae_lambda1_s1000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 39 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0227 (> 0.02).

**lr0.003_minibatch_size128_epochs16_clip_ratio0.289_gae_lambda1_s2000**

- **AVISO** `KL_ALTO`: KL maximo 0.0351 (> 0.02).
- **INFO** `ENTROPIA_BAJA`: Entropia al 61 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.003_minibatch_size128_epochs16_clip_ratio0.295_gae_lambda0.98_s1000**

- **AVISO** `KL_ALTO`: KL maximo 0.0333 (> 0.02).
- **INFO** `ENTROPIA_BAJA`: Entropia al 58 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.003_minibatch_size128_epochs16_clip_ratio0.295_gae_lambda0.98_s2000**

- **AVISO** `KL_ALTO`: KL maximo 0.0359 (> 0.02).
- **INFO** `ENTROPIA_BAJA`: Entropia al 50 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.

**lr0.003_minibatch_size128_epochs16_clip_ratio0.2_gae_lambda0.95_s1000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 36 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0304 (> 0.02).

**lr0.003_minibatch_size128_epochs16_clip_ratio0.2_gae_lambda0.95_s2000**

- **AVISO** `ENTROPIA_COLAPSADA`: Entropia al 23 % del maximo: la politica casi no explora.
- **AVISO** `KL_ALTO`: KL maximo 0.0423 (> 0.02).

## Cómo leerlo

- **Entropía:** una política uniforme sobre las 240 acciones tiene 5,48 nats. Una caída fuerte significa que la política se concentra; conviene evaluar también con muestreo y no solo con argmax (ver `docs/entrenamiento_inicial_2.3.5.md`).
- **Pasos en espera:** acciones `LIMIT_SELL`, que el puente de ABIDES y el simulador Poisson tratan como «esperar».
- Sin el CSV de monitoreo por episodio solo se muestran las curvas del entrenador; el costo y el cumplimiento por episodio se registran con `MonitorEntrenamiento` (`src/training/monitoreo.py`).

🤖 Generado con [Claude Code](https://claude.com/claude-code)
