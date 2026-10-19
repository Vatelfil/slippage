# Validación formal del simulador (tarea 2.2.5)

**Elaborado por:** Paolo Sepúlveda (PS) con apoyo de Claude Code. **Pendiente de revisión por:** Benjamín Farias (BF), responsable de la calibración de `rmsc04` (2.2.4).
**Activo:** ECL · **Snapshot real:** 2026-08-23 · **Semillas simuladas:** 30 por tramo · **Fecha:** 2026-10-19

## 1. Veredicto

**NO VÁLIDO según el criterio del plan.** Criterios fijados antes de ver los datos:

| Criterio | Qué exige | Cumple |
|---|---|:---:|
| A. Literal del plan | Todos los p de KS y Mann–Whitney, por tramo, mayores que α = 0,05 | no |
| B. Forma | KS con muestras estandarizadas, p > α en los 3 tramos | no |
| C. Efecto | \|g de Hedges\| < 0,5 en los 3 tramos | sí |
| D. Patrón | Volatilidad máxima en la apertura y volumen por vela creciente | sí |

- El KS crudo rechaza en 3 de 3 tramos (apertura, media_jornada, cierre).

## 2. KS de 2 muestras sobre los retornos de 5 min

| Tramo | n sim | n real | D | p | D crítico | D / D crít. | Rechaza | p (estandarizado) |
|---|---:|---:|---:|---:|---:|---:|:---:|---:|
| apertura | 690 | 245 | 0,168 | < 0,0001 | 0,101 | 1,66 | sí | < 0,0001 |
| media_jornada | 900 | 478 | 0,171 | < 0,0001 | 0,077 | 2,22 | sí | < 0,0001 |
| cierre | 690 | 525 | 0,146 | < 0,0001 | 0,079 | 1,85 | sí | < 0,0001 |

## 3. Escala de los retornos: Mann–Whitney sobre |retorno| y Brown–Forsythe

| Tramo | p Mann–Whitney | g de Hedges | Efecto | Mediana \|r\| sim (bps) | Mediana \|r\| real (bps) | p Brown–Forsythe | Desvío sim / real |
|---|---:|---:|---|---:|---:|---:|---:|
| apertura | < 0,0001 | 0,28 | pequeno | 25,3 | 10,0 | 0,0002 | 1,05 |
| media_jornada | < 0,0001 | 0,20 | pequeno | 21,4 | 12,3 | 0,0004 | 1,04 |
| cierre | < 0,0001 | 0,22 | pequeno | 21,4 | 11,4 | 0,0001 | 1,01 |

## 4. Valores por semilla frente al valor real

El valor real es un único número, así que cada fila compara las semillas contra ese objetivo con Wilcoxon de 1 muestra.

| Tramo | Magnitud | Media sim | Objetivo real | Sesgo (%) | IC 95 % de la media | p |
|---|---|---:|---:|---:|---|---:|
| apertura | Volatilidad 5 min (bps) | 41,0 | 41,8 | -1,9 | [37,4; 44,5] | 0,503 |
| apertura | Volumen mediano por vela | 4008 | 5001 | -19,9 | [3925; 4090] | < 0,0001 |
| apertura | Participación de volumen | 0,297 | 0,172 | 72,9 | [0,291; 0,302] | < 0,0001 |
| media_jornada | Volatilidad 5 min (bps) | 34,5 | 35,2 | -1,8 | [31,3; 37,7] | 0,465 |
| media_jornada | Volumen mediano por vela | 4019 | 6629 | -39,4 | [3954; 4085] | < 0,0001 |
| media_jornada | Participación de volumen | 0,377 | 0,332 | 13,6 | [0,373; 0,382] | < 0,0001 |
| cierre | Volatilidad 5 min (bps) | 34,9 | 36,2 | -3,6 | [32,4; 37,4] | 0,124 |
| cierre | Volumen mediano por vela | 4558 | 7998 | -43,0 | [4459; 4657] | < 0,0001 |
| cierre | Participación de volumen | 0,326 | 0,438 | -25,6 | [0,322; 0,330] | < 0,0001 |

## 5. Patrón entre tramos (Kruskal–Wallis sobre |retorno|)

| Fuente | H | p | Mediana \|r\| apertura (bps) | media jornada | cierre |
|---|---:|---:|---:|---:|---:|
| real | 0,5 | 0,780 | 10,0 | 12,3 | 11,4 |
| simulado | 12,6 | 0,0019 | 25,3 | 21,4 | 21,4 |

- Volatilidad máxima en la apertura: **sí** (por construcción: `fund_vol` se fija por tramo).
- Volumen por vela creciente de apertura a cierre: **sí**.

## 6. Spread (sin prueba de hipótesis)

El spread simulado es cotizado y los reales son proxies de velas de 5 min, así que solo se verifica si cae dentro del rango de los cuatro proxies.

| Tramo | Spread simulado (bps) | Rango real (bps) | Dentro | Veces por debajo del mínimo real |
|---|---:|---|:---:|---:|
| apertura | 1,10 | [0,4; 27,1] | sí | — |
| media_jornada | 1,06 | [2,7; 31,8] | no | 3 |
| cierre | 0,59 | [2,8; 31,0] | no | 5 |

## 8. Corrección por comparaciones múltiples (Holm)

| Prueba | p crudo | p ajustado (Holm) | ¿Rechaza tras ajustar? |
|---|---:|---:|:---:|
| apertura · brown_forsythe | 0,0002 | 0,0009 | sí |
| apertura · ks | < 0,0001 | 0,0004 | sí |
| apertura · ks_estandarizado | < 0,0001 | 0,0004 | sí |
| apertura · mannwhitney | < 0,0001 | < 0,0001 | sí |
| apertura · participacion | < 0,0001 | < 0,0001 | sí |
| apertura · volatilidad | 0,503 | 0,929 | no |
| apertura · volumen_vela | < 0,0001 | < 0,0001 | sí |
| cierre · brown_forsythe | 0,0001 | 0,0009 | sí |
| cierre · ks | < 0,0001 | < 0,0001 | sí |
| cierre · ks_estandarizado | < 0,0001 | < 0,0001 | sí |
| cierre · mannwhitney | < 0,0001 | < 0,0001 | sí |
| cierre · participacion | < 0,0001 | < 0,0001 | sí |
| cierre · volatilidad | 0,124 | 0,372 | no |
| cierre · volumen_vela | < 0,0001 | < 0,0001 | sí |
| media_jornada · brown_forsythe | 0,0004 | 0,0014 | sí |
| media_jornada · ks | < 0,0001 | < 0,0001 | sí |
| media_jornada · ks_estandarizado | < 0,0001 | < 0,0001 | sí |
| media_jornada · mannwhitney | < 0,0001 | < 0,0001 | sí |
| media_jornada · participacion | < 0,0001 | < 0,0001 | sí |
| media_jornada · volatilidad | 0,465 | 0,929 | no |
| media_jornada · volumen_vela | < 0,0001 | < 0,0001 | sí |

## 9. Limitaciones

- Las pruebas por semilla (sección 4) tienen poca potencia con pocas semillas; el KS y Mann–Whitney sobre la muestra agrupada tienen mucha: con miles de retornos rechazan diferencias pequeñas. Por eso se reportan también el tamaño de efecto y el D/D crítico.
- Los retornos reales y simulados vienen agrupados de varios días: no son estrictamente independientes.
- El valor real de volatilidad, volumen por vela y participación es un único número (no hay muestra diaria real versionada), por eso se usa una prueba de 1 muestra.
- El spread no admite prueba de hipótesis (magnitudes distintas) y el simulador queda decenas de veces por debajo de los proxies reales; el IS absoluto en ABIDES queda subestimado, aunque la comparación entre políticas sigue siendo válida.
- Un solo activo (ECL) y un solo régimen (previo a la transición del IPSA a MSCI, 1 de septiembre de 2026).

🤖 Generado con [Claude Code](https://claude.com/claude-code)
