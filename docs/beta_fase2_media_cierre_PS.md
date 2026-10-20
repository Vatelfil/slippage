# Fase 2 de la elección de β (tarea 2.2.3, P5): media jornada y cierre

**Elaborado por:** Paolo Sepúlveda (PS) con apoyo de Claude Code, 19 oct 2026. **Pendiente de revisión por:** Benjamín Farias (BF), según el plan del Sprint 5 (P5), y Mauricio Reynoso (MR).

Completa `docs/beta_fase2_apertura_PS.md`. Corrida en Colab el 19 oct 2026 (ABIDES calibrado, FALABELLA, snapshot 2026-08-23, `rmsc04_ipsa_FALABELLA_2026-08-23.json`). β\* = 0,0618 (barrido de BF en ABIDES). PPO con la implementación de MR y los mismos hiperparámetros de la apertura (γ 0,95; λ GAE 0,95; lr 3e-4; clip 0,2; entropía 0,01; 4 épocas; minilote 64; 10 episodios por actualización).

**Diferencia con la apertura:** aquí se usaron **100 episodios de entrenamiento y 15 semillas de evaluación por β** (en la apertura fueron 300 y 30), como fija el plan por tiempo de máquina. Los tres tramos no son idénticos en presupuesto. Semillas de entrenamiento 1001–1100 y de evaluación 5001–5015, iguales para todos los β.

## 1. Resultados

### Media jornada

| β | Múltiplo | Slippage medio (bps) | Error estándar | Cumplimiento | Peso del riesgo |
|---|---|---:|---:|---:|---:|
| 0,00000 | 0× (control) | 5,13 | 3,05 | 1,000 | 0,000 |
| 0,00618 | 0,1× | 2,88 | 1,05 | 1,000 | 0,060 |
| 0,01854 | 0,3× | 2,93 | 0,96 | 1,000 | 0,201 |
| 0,06180 | 1× | 3,20 | 1,08 | 1,000 | 0,263 |

| Política de referencia (mismas semillas) | Slippage medio (bps) | Cumplimiento |
|---|---:|---:|
| agresiva_market | 3,38 | 1,000 |
| twap_limit_medio | 7,42 | 0,999 |
| pasiva_limit | 12,66 | 1,000 |

### Cierre

| β | Múltiplo | Slippage medio (bps) | Error estándar | Cumplimiento | Peso del riesgo |
|---|---|---:|---:|---:|---:|
| 0,00000 | 0× (control) | 2,54 | 1,82 | 0,991 | 0,000 |
| 0,00618 | 0,1× | 2,23 | 1,67 | 0,989 | 0,056 |
| 0,01854 | 0,3× | 2,94 | 3,66 | 0,996 | 0,235 |
| 0,06180 | 1× | 2,23 | 0,75 | 1,000 | 0,479 |

| Política de referencia (mismas semillas) | Slippage medio (bps) | Cumplimiento |
|---|---:|---:|
| agresiva_market | 2,99 | 1,000 |
| twap_limit_medio | 0,05 | 0,998 |
| pasiva_limit | 6,15 | 1,000 |

### Resumen de los tres tramos (apertura: ver `docs/beta_fase2_apertura_PS.md`)

| Tramo | Cumplimiento con 0,1× | con 0,3× | con 1× |
|---|---:|---:|---:|
| Apertura | 1,000 | 0,341 | 0,000 |
| Media jornada | 1,000 | 1,000 | 1,000 |
| Cierre | 0,989 | 0,996 | 1,000 |

## 2. Regla de selección (fijada antes de ver los datos) y resultado

Candidatos 0,1 / 0,3 / 1 × β\*; el control β = 0 es solo referencia. Se exige cumplimiento ≥ 95 % de la orden. Entre los que cumplen, se elige el de menor slippage si el Wilcoxon pareado con el siguiente da p < 0,05; si no, el valor central 0,3 × β\*.

- **Media jornada:** los tres candidatos cumplen y la diferencia entre el mejor y el siguiente no es significativa (p = 0,67). Por la regla: **0,3× = 0,01854**.
- **Cierre:** igual (p = 0,93). Por la regla: **0,3× = 0,01854**.
- **Apertura** (documento anterior): solo 0,1× cumple el 95 %. Por la regla: **0,1× = 0,0061796**.

## 3. Propuesta (pendiente de revisión por BF): un β común, 0,1× = 0,0061796

El plan dice "valor elegido por tramo (o uno común si no se distinguen)". Se propone **un β común de 0,0061796**, es decir, **no cambiar `BETA_RIESGO_EJECUTOR`** (`src/config/market_params.py`):

1. Es el **único candidato que cumple el 95 % de la orden en los tres tramos** (1,000 / 1,000 / 0,989). Con 0,3× la apertura se queda en 0,341.
2. En media jornada y cierre **ningún β se distingue de otro** (las diferencias de slippage son mucho menores que el error estándar), así que no hay razón estadística para subir a 0,3×.
3. No exige cambios de código ni repetir corridas.

**Alternativa (regla al pie de la letra):** 0,1× en apertura y 0,3× en media jornada y cierre. Exigiría un β por tramo en el código del Ejecutor y no se apoya en una diferencia observada. Queda a decisión de BF.

## 4. Lectura honesta

- **Los β no se distinguen** en media jornada ni en cierre. En el cierre el 0,3× tiene incluso el mayor error estándar (3,66 bps).
- **TWAP con órdenes límite iguala o supera a las redes en dos de los tres tramos:** apertura (4,06 frente a 4,71 bps del 0,1×) y cierre (0,05 frente a 2,2–2,9 bps). Solo en media jornada las redes lo superan (2,9 frente a 7,4 bps). El PPO con este entrenamiento corto todavía no demuestra ventaja sobre el benchmark simple.
- **Sobre la decisión D3:** en la apertura, con β alto la red aprendía a no ejecutar (0,3×: 34 %; 1×: 0 %). En media jornada y cierre el 1× completa entre el 99 % y el 100 % de la orden. El problema de "no operar" aparece en la apertura y no en los otros dos tramos con este presupuesto. No cambia la propuesta de la opción 0, pero conviene tenerlo presente al revisar D3.
- **El episodio de entrenamiento 34 del cierre** (semilla 1034) tiene un retorno de −65 en los cuatro β: es una propiedad de esa semilla, no del β.

## 5. Limitaciones

- **Entrenamiento corto** (100 episodios): el resultado es indicativo.
- **Una sola semilla de red por β:** no se separa el efecto de β del azar del entrenamiento.
- **Solo FALABELLA;** COPEC y ECL (calibración nueva) no se probaron aquí.
- **Presupuesto menor que en la apertura** (100 episodios y 15 semillas frente a 300 y 30).
- **Corrida interrumpida en media jornada:** los β 0×, 0,1× y 0,3× se guardaron en una sesión anterior y el 1× se reentrenó en una sesión nueva, con las mismas semillas y la misma configuración (misma firma del archivo de resultados).
- **Tiempo de máquina**, útil para planificar el Sprint 6: ~47 min por β en media jornada y ~108 min por β en el cierre (entrenamiento más evaluación).

## 6. Archivos y cómo reproducir

- `data/colab_resultados/beta_fase2_media_jornada_2026-10-19.json` y `beta_fase2_cierre_2026-10-19.json`: resultados completos (historial de entrenamiento, episodios de evaluación, referencias y selección).
- En Colab, con el entorno preparado (condacolab, entorno `abides`, ABIDES, `torch==1.13.1+cpu` y el repositorio):

```bash
PYTHONPATH=. python scripts/colab/beta_fase2_ppo.py \
    --calibrated-json data/calibration/rmsc04_ipsa_FALABELLA_2026-08-23.json \
    --out-dir <carpeta_de_drive>/p5_beta --tramo media_jornada \
    --episodes 100 --eval-seeds 15 --fecha 2026-10-19 --max-minutes 150
```

(para el cierre: `--tramo cierre --max-minutes 420`). El script es reanudable y guarda tras cada β. Con `torch` ausente falla de inmediato: se instala aparte (`docs/dependencias_resueltas.md`).

🤖 Generado con [Claude Code](https://claude.com/claude-code)
