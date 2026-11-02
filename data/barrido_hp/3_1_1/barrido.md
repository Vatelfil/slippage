# Barrido de hiperparámetros, fase 3.1.1 (Poisson)

BORRADOR de PS para MR. Diferencia = costo de la red entrenada − costo de su red inicial, pareada por semilla de evaluación (negativo es mejor). Regla fijada antes de ver los datos (ver el JSON de la rejilla).

**Decisión:** Gana lr0.003_minibatch_size128_epochs16_clip_ratio0.2_gae_lambda0.95: su IC no incluye la diferencia de la configuración de referencia.

| Configuración | Diferencia (bps) | IC 95 % | Cumplimiento | Redes |
|---|---:|---|---:|---:|
| `lr0.003_minibatch_size128_epochs16_clip_ratio0.2_gae_lambda0.95` | -2.62 | [-2.80; -2.45] | 0.999 | 2 |
| `lr0.003_minibatch_size128_epochs8_clip_ratio0.2_gae_lambda0.95` | -2.62 | [-2.80; -2.45] | 0.999 | 2 |
| `lr0.003_minibatch_size128_epochs4_clip_ratio0.2_gae_lambda0.95` | -2.60 | [-2.79; -2.42] | 0.997 | 2 |
| `lr0.001_minibatch_size128_epochs8_clip_ratio0.2_gae_lambda0.95` | -2.60 | [-2.80; -2.40] | 0.999 | 2 |
| `lr0.0003_minibatch_size128_epochs4_clip_ratio0.2_gae_lambda0.95` | -2.57 | [-2.75; -2.39] | 0.996 | 2 |
| `lr0.001_minibatch_size32_epochs16_clip_ratio0.2_gae_lambda0.95` | -2.54 | [-2.71; -2.37] | 0.997 | 2 |
| `lr0.001_minibatch_size32_epochs4_clip_ratio0.2_gae_lambda0.95` | -2.54 | [-2.71; -2.37] | 0.997 | 2 |
| `lr0.001_minibatch_size32_epochs8_clip_ratio0.2_gae_lambda0.95` | -2.54 | [-2.71; -2.37] | 0.997 | 2 |
| `lr0.0003_minibatch_size32_epochs8_clip_ratio0.2_gae_lambda0.95` | -2.50 | [-2.69; -2.32] | 0.998 | 2 |
| `lr0.0003_minibatch_size32_epochs16_clip_ratio0.2_gae_lambda0.95` | -2.49 | [-2.67; -2.31] | 0.998 | 2 |
| `lr0.0003_minibatch_size128_epochs8_clip_ratio0.2_gae_lambda0.95` | -2.48 | [-2.68; -2.28] | 0.998 | 2 |
| `lr0.001_minibatch_size64_epochs4_clip_ratio0.2_gae_lambda0.95` | -2.47 | [-2.71; -2.23] | 1.000 | 2 |
| `lr0.0003_minibatch_size32_epochs4_clip_ratio0.2_gae_lambda0.95` | -2.47 | [-2.67; -2.27] | 0.998 | 2 |
| `lr0.0003_minibatch_size64_epochs16_clip_ratio0.2_gae_lambda0.95` | -2.46 | [-2.70; -2.22] | 0.999 | 2 |
| `lr0.003_minibatch_size64_epochs16_clip_ratio0.2_gae_lambda0.95` | -2.45 | [-2.63; -2.26] | 0.988 | 2 |
| `lr0.003_minibatch_size64_epochs4_clip_ratio0.2_gae_lambda0.95` | -2.45 | [-2.63; -2.26] | 0.988 | 2 |
| `lr0.003_minibatch_size64_epochs8_clip_ratio0.2_gae_lambda0.95` | -2.45 | [-2.63; -2.26] | 0.988 | 2 |
| `lr0.001_minibatch_size128_epochs16_clip_ratio0.2_gae_lambda0.95` | -2.45 | [-2.64; -2.25] | 0.996 | 2 |
| `lr0.0001_minibatch_size128_epochs8_clip_ratio0.2_gae_lambda0.95` | -2.44 | [-2.63; -2.25] | 0.997 | 2 |
| `lr0.001_minibatch_size64_epochs16_clip_ratio0.2_gae_lambda0.95` | -2.43 | [-2.67; -2.20] | 1.000 | 2 |
| `lr0.001_minibatch_size64_epochs8_clip_ratio0.2_gae_lambda0.95` | -2.43 | [-2.67; -2.20] | 1.000 | 2 |
| `lr0.0001_minibatch_size64_epochs4_clip_ratio0.2_gae_lambda0.95` | -2.43 | [-2.62; -2.23] | 0.984 | 2 |
| `lr0.0003_minibatch_size64_epochs4_clip_ratio0.2_gae_lambda0.95` | -2.43 | [-2.64; -2.23] | 0.994 | 2 |
| `lr0.0003_minibatch_size64_epochs8_clip_ratio0.2_gae_lambda0.95` | -2.43 | [-2.64; -2.22] | 0.998 | 2 |
| `lr0.001_minibatch_size128_epochs4_clip_ratio0.2_gae_lambda0.95` | -2.42 | [-2.60; -2.23] | 0.998 | 2 |
| `lr0.0001_minibatch_size32_epochs8_clip_ratio0.2_gae_lambda0.95` | -2.41 | [-2.60; -2.21] | 0.998 | 2 |
| `lr0.0001_minibatch_size64_epochs16_clip_ratio0.2_gae_lambda0.95` | -2.35 | [-2.57; -2.13] | 0.998 | 2 |
| `lr0.0001_minibatch_size64_epochs8_clip_ratio0.2_gae_lambda0.95` | -2.34 | [-2.55; -2.13] | 0.997 | 2 |
| `lr0.0001_minibatch_size32_epochs4_clip_ratio0.2_gae_lambda0.95` | -2.30 | [-2.52; -2.08] | 0.994 | 2 |
| `lr0.0003_minibatch_size128_epochs16_clip_ratio0.2_gae_lambda0.95` | -2.27 | [-2.52; -2.01] | 0.992 | 2 |
| `lr0.0001_minibatch_size32_epochs16_clip_ratio0.2_gae_lambda0.95` | -2.13 | [-2.38; -1.89] | 0.998 | 2 |
| `lr0.0001_minibatch_size128_epochs16_clip_ratio0.2_gae_lambda0.95` | -2.07 | [-2.29; -1.85] | 0.996 | 2 |
| `lr0.0001_minibatch_size128_epochs4_clip_ratio0.2_gae_lambda0.95` | -1.41 | [-1.66; -1.16] | 0.959 | 2 |
| `lr0.003_minibatch_size32_epochs16_clip_ratio0.2_gae_lambda0.95` | -0.42 | [-0.89; 0.08] | 0.499 | 2 |
| `lr0.003_minibatch_size32_epochs4_clip_ratio0.2_gae_lambda0.95` | -0.42 | [-0.89; 0.08] | 0.499 | 2 |
| `lr0.003_minibatch_size32_epochs8_clip_ratio0.2_gae_lambda0.95` | -0.42 | [-0.89; 0.08] | 0.499 | 2 |
