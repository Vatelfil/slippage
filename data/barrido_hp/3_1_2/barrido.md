# Barrido de hiperparámetros, fase 3.1.2 (Poisson)

BORRADOR de PS para MR. Diferencia = costo de la red entrenada − costo de su red inicial, pareada por semilla de evaluación (negativo es mejor). Regla fijada antes de ver los datos (ver el JSON de la rejilla).

**Decisión:** Sin mejora clara frente a la configuración de referencia: se mantiene la de referencia.

| Configuración | Diferencia (bps) | IC 95 % | Cumplimiento | Redes |
|---|---:|---|---:|---:|
| `lr0.003_minibatch_size128_epochs16_clip_ratio0.207_gae_lambda0.926` | -2.63 | [-2.85; -2.41] | 0.989 | 2 |
| `lr0.003_minibatch_size128_epochs16_clip_ratio0.2_gae_lambda0.95` | -2.62 | [-2.80; -2.45] | 0.999 | 2 |
| `lr0.003_minibatch_size128_epochs16_clip_ratio0.276_gae_lambda0.947` | -2.59 | [-2.80; -2.38] | 0.994 | 2 |
| `lr0.003_minibatch_size128_epochs16_clip_ratio0.262_gae_lambda0.932` | -2.58 | [-2.75; -2.39] | 0.990 | 2 |
| `lr0.003_minibatch_size128_epochs16_clip_ratio0.134_gae_lambda0.984` | -2.55 | [-2.76; -2.34] | 0.992 | 2 |
| `lr0.003_minibatch_size128_epochs16_clip_ratio0.158_gae_lambda0.944` | -2.55 | [-2.76; -2.33] | 1.000 | 2 |
| `lr0.003_minibatch_size128_epochs16_clip_ratio0.289_gae_lambda1` | -2.55 | [-2.72; -2.37] | 0.997 | 2 |
| `lr0.003_minibatch_size128_epochs16_clip_ratio0.295_gae_lambda0.98` | -2.54 | [-2.71; -2.37] | 0.999 | 2 |
| `lr0.003_minibatch_size128_epochs16_clip_ratio0.278_gae_lambda0.919` | -2.53 | [-2.71; -2.35] | 0.991 | 2 |
| `lr0.003_minibatch_size128_epochs16_clip_ratio0.249_gae_lambda0.907` | -2.51 | [-2.69; -2.33] | 0.992 | 2 |
| `lr0.003_minibatch_size128_epochs16_clip_ratio0.137_gae_lambda0.936` | -2.51 | [-2.71; -2.31] | 1.000 | 2 |
| `lr0.003_minibatch_size128_epochs16_clip_ratio0.199_gae_lambda0.964` | -2.51 | [-2.69; -2.32] | 0.998 | 2 |
| `lr0.003_minibatch_size128_epochs16_clip_ratio0.117_gae_lambda0.988` | -2.50 | [-2.70; -2.30] | 0.997 | 2 |
| `lr0.003_minibatch_size128_epochs16_clip_ratio0.212_gae_lambda0.902` | -2.50 | [-2.73; -2.28] | 0.997 | 2 |
| `lr0.003_minibatch_size128_epochs16_clip_ratio0.219_gae_lambda0.915` | -2.50 | [-2.67; -2.34] | 1.000 | 2 |
| `lr0.003_minibatch_size128_epochs16_clip_ratio0.21_gae_lambda0.936` | -2.48 | [-2.66; -2.30] | 1.000 | 2 |
| `lr0.003_minibatch_size128_epochs16_clip_ratio0.129_gae_lambda0.933` | -2.48 | [-2.69; -2.28] | 1.000 | 2 |
| `lr0.003_minibatch_size128_epochs16_clip_ratio0.195_gae_lambda0.932` | -2.48 | [-2.69; -2.27] | 0.993 | 2 |
| `lr0.003_minibatch_size128_epochs16_clip_ratio0.229_gae_lambda0.947` | -2.45 | [-2.64; -2.26] | 0.997 | 2 |
| `lr0.003_minibatch_size128_epochs16_clip_ratio0.16_gae_lambda0.911` | -2.44 | [-2.63; -2.24] | 0.997 | 2 |
| `lr0.003_minibatch_size128_epochs16_clip_ratio0.102_gae_lambda0.961` | -2.38 | [-2.58; -2.16] | 0.998 | 2 |
| `lr0.003_minibatch_size128_epochs16_clip_ratio0.194_gae_lambda0.925` | -2.14 | [-2.36; -1.90] | 0.886 | 2 |
| `lr0.003_minibatch_size128_epochs16_clip_ratio0.21_gae_lambda0.925` | -2.08 | [-2.37; -1.79] | 0.975 | 2 |
| `lr0.003_minibatch_size128_epochs16_clip_ratio0.239_gae_lambda0.973` | -1.81 | [-2.09; -1.55] | 1.000 | 2 |
| `lr0.003_minibatch_size128_epochs16_clip_ratio0.237_gae_lambda0.908` | -0.76 | [-1.30; -0.19] | 0.496 | 2 |
