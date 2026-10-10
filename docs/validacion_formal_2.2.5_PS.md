# Validación formal del simulador (tarea 2.2.5)

**Elaborado por:** Paolo Sepúlveda (PS) con apoyo de Claude Code. **Pendiente de revisión por:** Benjamín Farias (BF), responsable de la calibración de `rmsc04` (2.2.4).
**Activo:** FALABELLA · **Snapshot real:** 2026-08-23 · **Semillas simuladas:** 30 por tramo · **Fecha:** 2026-10-10

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
| apertura | 690 | 1111 | 0,073 | 0,021 | 0,066 | 1,10 | sí | 0,0029 |
| media_jornada | 900 | 1690 | 0,098 | < 0,0001 | 0,056 | 1,75 | sí | 0,0001 |
| cierre | 690 | 1252 | 0,066 | 0,039 | 0,064 | 1,03 | sí | 0,0024 |

## 3. Escala de los retornos: Mann–Whitney sobre |retorno| y Brown–Forsythe

| Tramo | p Mann–Whitney | g de Hedges | Efecto | Mediana \|r\| sim (bps) | Mediana \|r\| real (bps) | p Brown–Forsythe | Desvío sim / real |
|---|---:|---:|---|---:|---:|---:|---:|
| apertura | 0,086 | 0,01 | trivial | 13,6 | 15,4 | 0,871 | 0,98 |
| media_jornada | 0,0061 | -0,03 | trivial | 8,8 | 8,8 | 0,499 | 0,89 |
| cierre | 0,339 | -0,03 | trivial | 8,1 | 9,2 | 0,491 | 0,96 |

## 4. Valores por semilla frente al valor real

El valor real es un único número, así que cada fila compara las semillas contra ese objetivo con Wilcoxon de 1 muestra.

| Tramo | Magnitud | Media sim | Objetivo real | Sesgo (%) | IC 95 % de la media | p |
|---|---|---:|---:|---:|---|---:|
| apertura | Volatilidad 5 min (bps) | 31,2 | 34,0 | -8,1 | [28,6; 33,8] | 0,033 |
| apertura | Volumen mediano por vela | 11322 | 7576 | 49,5 | [11137; 11507] | < 0,0001 |
| apertura | Participación de volumen | 0,284 | 0,249 | 14,4 | [0,282; 0,287] | < 0,0001 |
| media_jornada | Volatilidad 5 min (bps) | 19,3 | 22,3 | -13,6 | [18,3; 20,3] | < 0,0001 |
| media_jornada | Volumen mediano por vela | 11503 | 9396 | 22,4 | [11334; 11673] | < 0,0001 |
| media_jornada | Participación de volumen | 0,390 | 0,381 | 2,3 | [0,387; 0,393] | < 0,0001 |
| cierre | Volatilidad 5 min (bps) | 18,8 | 20,9 | -10,1 | [16,9; 20,6] | 0,026 |
| cierre | Volumen mediano por vela | 12522 | 11964 | 4,7 | [12391; 12652] | < 0,0001 |
| cierre | Participación de volumen | 0,326 | 0,309 | 5,5 | [0,323; 0,329] | < 0,0001 |

## 5. Patrón entre tramos (Kruskal–Wallis sobre |retorno|)

| Fuente | H | p | Mediana \|r\| apertura (bps) | media jornada | cierre |
|---|---:|---:|---:|---:|---:|
| real | 80,1 | < 0,0001 | 15,4 | 8,8 | 9,2 |
| simulado | 80,1 | < 0,0001 | 13,6 | 8,8 | 8,1 |

- Volatilidad máxima en la apertura: **sí** (por construcción: `fund_vol` se fija por tramo).
- Volumen por vela creciente de apertura a cierre: **sí**.

## 6. Spread (sin prueba de hipótesis)

El spread simulado es cotizado y los reales son proxies de velas de 5 min, así que solo se verifica si cae dentro del rango de los cuatro proxies.

| Tramo | Spread simulado (bps) | Rango real (bps) | Dentro | Veces por debajo del mínimo real |
|---|---:|---|:---:|---:|
| apertura | 0,17 | [5,7; 35,3] | no | 33 |
| media_jornada | 0,17 | [4,1; 23,8] | no | 25 |
| cierre | 0,17 | [4,9; 20,6] | no | 29 |

## 7. Antes y después de calibrar

| Tramo | D antes | p antes | D después | p después | g antes | g después | ¿D baja? |
|---|---:|---:|---:|---:|---:|---:|:---:|
| apertura | 0,324 | < 0,0001 | 0,073 | 0,021 | -0,98 | 0,01 | sí |
| media_jornada | 0,279 | < 0,0001 | 0,098 | < 0,0001 | -0,86 | -0,03 | sí |
| cierre | 0,275 | < 0,0001 | 0,066 | 0,039 | -0,92 | -0,03 | sí |

- Veredicto del simulador de fábrica: NO VÁLIDO según el criterio del plan.
- Veredicto del simulador calibrado: NO VÁLIDO según el criterio del plan.

## 8. Corrección por comparaciones múltiples (Holm)

| Prueba | p crudo | p ajustado (Holm) | ¿Rechaza tras ajustar? |
|---|---:|---:|:---:|
| apertura · brown_forsythe | 0,871 | 1,000 | no |
| apertura · ks | 0,021 | 0,187 | no |
| apertura · ks_estandarizado | 0,0029 | 0,031 | sí |
| apertura · mannwhitney | 0,086 | 0,432 | no |
| apertura · participacion | < 0,0001 | < 0,0001 | sí |
| apertura · volatilidad | 0,033 | 0,229 | no |
| apertura · volumen_vela | < 0,0001 | < 0,0001 | sí |
| cierre · brown_forsythe | 0,491 | 1,000 | no |
| cierre · ks | 0,039 | 0,234 | no |
| cierre · ks_estandarizado | 0,0024 | 0,028 | sí |
| cierre · mannwhitney | 0,339 | 1,000 | no |
| cierre · participacion | < 0,0001 | < 0,0001 | sí |
| cierre · volatilidad | 0,026 | 0,210 | no |
| cierre · volumen_vela | < 0,0001 | < 0,0001 | sí |
| media_jornada · brown_forsythe | 0,499 | 1,000 | no |
| media_jornada · ks | < 0,0001 | 0,0003 | sí |
| media_jornada · ks_estandarizado | 0,0001 | 0,0016 | sí |
| media_jornada · mannwhitney | 0,0061 | 0,061 | no |
| media_jornada · participacion | < 0,0001 | < 0,0001 | sí |
| media_jornada · volatilidad | < 0,0001 | 0,0001 | sí |
| media_jornada · volumen_vela | < 0,0001 | < 0,0001 | sí |

## 9. Limitaciones

- Las pruebas por semilla (sección 4) tienen poca potencia con pocas semillas; el KS y Mann–Whitney sobre la muestra agrupada tienen mucha: con miles de retornos rechazan diferencias pequeñas. Por eso se reportan también el tamaño de efecto y el D/D crítico.
- Los retornos reales y simulados vienen agrupados de varios días: no son estrictamente independientes.
- El valor real de volatilidad, volumen por vela y participación es un único número (no hay muestra diaria real versionada), por eso se usa una prueba de 1 muestra.
- El spread no admite prueba de hipótesis (magnitudes distintas) y el simulador queda decenas de veces por debajo de los proxies reales; el IS absoluto en ABIDES queda subestimado, aunque la comparación entre políticas sigue siendo válida.
- Un solo activo (FALABELLA) y un solo régimen (previo a la transición del IPSA a MSCI, 1 de septiembre de 2026).

🤖 Generado con [Claude Code](https://claude.com/claude-code)
