# Calibración de las alertas del monitoreo (tarea 3.1.4)

**Elaborado por:** PS con apoyo de Claude Code (uso autorizado por la universidad). Sprint 6. Se genera con `scripts/calibrar_monitoreo_ps.py`.

Las alertas de `src/training/monitoreo.py` se escribieron mirando lo que pasó en la 2.3.5. Aquí se prueban con 26 corridas cuyo resultado ya se conoce (10 malas, 12 neutrales y 4 buenas; ver el encabezado de `scripts/calibrar_monitoreo_ps.py`). La etiqueta sale de la evaluación de cada corrida, nunca de las alertas. **Una buena alerta avisa en las malas y casi nunca en las buenas.**

## 1. Qué se encontró con los umbrales originales

| Alerta | Malas que avisan | Neutrales que avisan | **Buenas que avisan (falsas alarmas)** |
|---|---:|---:|---:|
| `CUMPLIMIENTO_BAJO` | 0 de 10 | 0 de 12 | **1 de 4** |
| `CUMPLIMIENTO_CRITICO` | 6 de 10 | 0 de 12 | **0 de 4** |
| `ENTROPIA_BAJA` | 2 de 10 | 0 de 12 | **2 de 4** |
| `ENTROPIA_COLAPSADA` | 8 de 10 | 2 de 12 | **2 de 4** |
| `ESPERA_ALTA` | 6 de 10 | 0 de 12 | **0 de 4** |
| `ESPERA_EN_AUMENTO` | 6 de 10 | 0 de 12 | **0 de 4** |
| `PICO_PERDIDA_CRITICO` | 6 de 10 | 3 de 12 | **4 de 4** |
| `SIN_MEJORA` | 2 de 10 | 5 de 12 | **0 de 4** |

- **`ENTROPIA_COLAPSADA` daba falsas alarmas:** la entropía de las corridas buenas queda entre el 50 % y el 69 % del máximo, igual que la de varias malas, así que por sí sola no distingue.
- **`PICO_PERDIDA_CRITICO` no separaba nada:** con una penalización terminal el crítico tiene picos grandes en las corridas buenas (400 a 1.000 veces la mediana) y no en las malas (10 a 60).
- **Faltaba una alerta para el problema de fondo:** en las corridas de 1.000 episodios de ABIDES la recompensa mejora (45 % a 96 %) y el costo no, y solo avisaban las de entropía.

## 2. Cambios

| Cambio | Antes | Ahora | Por qué |
|---|---|---|---|
| `ENTROPIA_COLAPSADA` | crítica por debajo del 60 % de la entropía máxima | **aviso** por debajo del 40 %; crítica solo si además hay espera alta o incumplimiento | La entropía baja no es mala por sí sola |
| `ENTROPIA_BAJA` | aviso por debajo del 90 % | **informativa** | Se concentra toda política que aprende: avisaba en las 4 corridas buenas |
| `PICO_PERDIDA_CRITICO` | 20 veces la mediana | 1.000 veces (sigue siendo informativa) | Con penalización terminal los picos son normales |
| **`RECOMPENSA_SUBE_COSTO_NO` (nueva)** | no existía | aviso si el retorno medio mejora ≥ 40 % y el slippage baja menos de 1,5 bps; ventanas de 100 episodios y mínimo de 200 | Detecta la red que optimiza la recompensa y no el costo |

## 3. Resultado con los umbrales calibrados

| Alerta | Malas que avisan | Neutrales que avisan | **Buenas que avisan (falsas alarmas)** |
|---|---:|---:|---:|
| `CUMPLIMIENTO_BAJO` | 0 de 10 | 0 de 12 | **1 de 4** |
| `CUMPLIMIENTO_CRITICO` | 6 de 10 | 0 de 12 | **0 de 4** |
| `ENTROPIA_BAJA` | 6 de 10 | 2 de 12 | **4 de 4** |
| `ENTROPIA_COLAPSADA` | 4 de 10 | 0 de 12 | **0 de 4** |
| `ESPERA_ALTA` | 6 de 10 | 0 de 12 | **0 de 4** |
| `ESPERA_EN_AUMENTO` | 6 de 10 | 0 de 12 | **0 de 4** |
| `PICO_PERDIDA_CRITICO` | 0 de 10 | 2 de 12 | **0 de 4** |
| `RECOMPENSA_SUBE_COSTO_NO` | 7 de 10 | 0 de 12 | **0 de 4** |
| `SIN_MEJORA` | 2 de 10 | 5 de 12 | **0 de 4** |

## 4. Cifras que sustentan los umbrales

Mejora del retorno (fracción del valor inicial) y del costo (bps) entre la primera y la última ventana, pico del crítico (veces la mediana) y entropía final (% del máximo).

| Corrida | Etiqueta | Ventana | Mejora del retorno | Mejora del costo (bps) | Pico del crítico | Entropía final |
|---|---|---:|---:|---:|---:|---:|
| ABIDES d3_opcion0_s2000 (1000 ep) | mala | 100 | +0,82 | +0,1 | 10 | 34 % |
| ABIDES d3_opcion0_s3000 (1000 ep) | mala | 100 | +0,45 | +2,0 | 38 | 85 % |
| ABIDES d3_opcionA_s2000 (1000 ep) | mala | 100 | +0,60 | +1,0 | 15 | 67 % |
| ABIDES d3_opcionA_s3000 (1000 ep) | mala | 100 | +0,96 | -0,0 | 58 | 36 % |
| V0_original_g1_s1000 | mala | 100 | +0,96 | +1,1 | 18 | 46 % |
| V0_original_g1_s2000 | mala | 100 | +0,97 | +0,3 | 63 | 37 % |
| V0_original_s1000 | mala | 100 | +0,98 | -0,0 | 16 | 52 % |
| V0_original_s2000 | mala | 100 | +0,97 | +0,1 | 34 | 48 % |
| V2_penalizacion_s1000 | mala | 100 | -0,46 | -0,3 | 28 | 55 % |
| V2_penalizacion_s2000 | mala | 100 | -0,22 | +1,7 | 61 | 40 % |
| ABIDES d3_opcion0_s1000 (100 ep) | neutral | 50 | +0,34 | +6,1 | 10 | 100 % |
| ABIDES d3_opcion0_s2000 (100 ep) | neutral | 50 | -0,24 | -4,7 | 3 | 100 % |
| ABIDES d3_opcion0_s3000 (100 ep) | neutral | 50 | +0,60 | -2,9 | 6 | 100 % |
| ABIDES d3_opcion0_s4000 (100 ep) | neutral | 50 | +0,44 | -3,3 | 3 | 100 % |
| ABIDES d3_opcion0_s6000 (100 ep) | neutral | 50 | -0,55 | +2,5 | 4 | 100 % |
| ABIDES d3_opcionA_s1000 (100 ep) | neutral | 50 | +0,34 | +6,2 | 8 | 100 % |
| ABIDES d3_opcionA_s2000 (100 ep) | neutral | 50 | -0,22 | -4,9 | 3 | 100 % |
| ABIDES d3_opcionA_s3000 (100 ep) | neutral | 50 | -0,02 | +0,0 | 2 | 100 % |
| ABIDES d3_opcionA_s4000 (100 ep) | neutral | 50 | +0,35 | -2,1 | 17 | 100 % |
| ABIDES d3_opcionA_s6000 (100 ep) | neutral | 50 | -1,01 | -0,6 | 27 | 100 % |
| V5_costo_espera_s1000 | neutral | 100 | +0,24 | +0,0 | 1678 | 47 % |
| V5_costo_espera_s2000 | neutral | 100 | +0,26 | +0,5 | 2354 | 55 % |
| V1_liquidacion_g1_s1000 | buena | 100 | +0,11 | +2,1 | 544 | 69 % |
| V1_liquidacion_g1_s2000 | buena | 100 | +0,11 | +2,1 | 824 | 55 % |
| V2_penalizacion_g1_s1000 | buena | 100 | +0,10 | +2,1 | 413 | 67 % |
| V2_penalizacion_g1_s2000 | buena | 100 | +0,11 | +2,2 | 982 | 50 % |

## 5. Detalle de alertas por corrida (umbrales calibrados)

| Corrida | Origen | Etiqueta | Alertas |
|---|---|---|---|
| ABIDES d3_opcion0_s2000 (1000 ep) | ABIDES (Colab) | mala | `ENTROPIA_COLAPSADA` (aviso), `RECOMPENSA_SUBE_COSTO_NO` (aviso) |
| ABIDES d3_opcion0_s3000 (1000 ep) | ABIDES (Colab) | mala | `ENTROPIA_BAJA` (info) |
| ABIDES d3_opcionA_s2000 (1000 ep) | ABIDES (Colab) | mala | `ENTROPIA_BAJA` (info), `RECOMPENSA_SUBE_COSTO_NO` (aviso) |
| ABIDES d3_opcionA_s3000 (1000 ep) | ABIDES (Colab) | mala | `ENTROPIA_COLAPSADA` (aviso), `RECOMPENSA_SUBE_COSTO_NO` (aviso) |
| V0_original_g1_s1000 | Poisson (PC) | mala | `CUMPLIMIENTO_CRITICO` (critica), `ENTROPIA_BAJA` (info), `ESPERA_ALTA` (aviso), `ESPERA_EN_AUMENTO` (aviso), `RECOMPENSA_SUBE_COSTO_NO` (aviso) |
| V0_original_g1_s2000 | Poisson (PC) | mala | `CUMPLIMIENTO_CRITICO` (critica), `ENTROPIA_COLAPSADA` (critica), `ESPERA_ALTA` (aviso), `ESPERA_EN_AUMENTO` (aviso), `RECOMPENSA_SUBE_COSTO_NO` (aviso) |
| V0_original_s1000 | Poisson (PC) | mala | `CUMPLIMIENTO_CRITICO` (critica), `ENTROPIA_BAJA` (info), `ESPERA_ALTA` (aviso), `ESPERA_EN_AUMENTO` (aviso), `RECOMPENSA_SUBE_COSTO_NO` (aviso) |
| V0_original_s2000 | Poisson (PC) | mala | `CUMPLIMIENTO_CRITICO` (critica), `ENTROPIA_BAJA` (info), `ESPERA_ALTA` (aviso), `ESPERA_EN_AUMENTO` (aviso), `RECOMPENSA_SUBE_COSTO_NO` (aviso) |
| V2_penalizacion_s1000 | Poisson (PC) | mala | `CUMPLIMIENTO_CRITICO` (critica), `ENTROPIA_BAJA` (info), `ESPERA_ALTA` (aviso), `ESPERA_EN_AUMENTO` (aviso), `SIN_MEJORA` (info) |
| V2_penalizacion_s2000 | Poisson (PC) | mala | `CUMPLIMIENTO_CRITICO` (critica), `ENTROPIA_COLAPSADA` (critica), `ESPERA_ALTA` (aviso), `ESPERA_EN_AUMENTO` (aviso), `SIN_MEJORA` (info) |
| ABIDES d3_opcion0_s1000 (100 ep) | ABIDES (Colab) | neutral | — |
| ABIDES d3_opcion0_s2000 (100 ep) | ABIDES (Colab) | neutral | `SIN_MEJORA` (info) |
| ABIDES d3_opcion0_s3000 (100 ep) | ABIDES (Colab) | neutral | — |
| ABIDES d3_opcion0_s4000 (100 ep) | ABIDES (Colab) | neutral | — |
| ABIDES d3_opcion0_s6000 (100 ep) | ABIDES (Colab) | neutral | `SIN_MEJORA` (info) |
| ABIDES d3_opcionA_s1000 (100 ep) | ABIDES (Colab) | neutral | — |
| ABIDES d3_opcionA_s2000 (100 ep) | ABIDES (Colab) | neutral | `SIN_MEJORA` (info) |
| ABIDES d3_opcionA_s3000 (100 ep) | ABIDES (Colab) | neutral | `SIN_MEJORA` (info) |
| ABIDES d3_opcionA_s4000 (100 ep) | ABIDES (Colab) | neutral | — |
| ABIDES d3_opcionA_s6000 (100 ep) | ABIDES (Colab) | neutral | `SIN_MEJORA` (info) |
| V5_costo_espera_s1000 | Poisson (PC) | neutral | `ENTROPIA_BAJA` (info), `PICO_PERDIDA_CRITICO` (info) |
| V5_costo_espera_s2000 | Poisson (PC) | neutral | `ENTROPIA_BAJA` (info), `PICO_PERDIDA_CRITICO` (info) |
| V1_liquidacion_g1_s1000 | Poisson (PC) | buena | `ENTROPIA_BAJA` (info) |
| V1_liquidacion_g1_s2000 | Poisson (PC) | buena | `CUMPLIMIENTO_BAJO` (aviso), `ENTROPIA_BAJA` (info) |
| V2_penalizacion_g1_s1000 | Poisson (PC) | buena | `ENTROPIA_BAJA` (info) |
| V2_penalizacion_g1_s2000 | Poisson (PC) | buena | `ENTROPIA_BAJA` (info) |

## 6. Límites

- Son pocas corridas (12 de Poisson y 15 de ABIDES) y las etiquetas «mala» de ABIDES vienen de un solo estudio (D3).
- Las corridas de Poisson son más fáciles de calibrar que las de ABIDES; los umbrales de la alerta nueva se confirmarán con las corridas de la confirmación en ABIDES.
- La alerta nueva no avisa en una corrida con la recompensa empeorando (por ejemplo, penalización con γ = 0,95), pero ahí ya avisan las de espera y cumplimiento.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
