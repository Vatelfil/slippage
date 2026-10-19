# Validación formal del simulador (tarea 2.2.5)

**Elaborado por:** Paolo Sepúlveda (PS) con apoyo de Claude Code. **Pendiente de revisión por:** Benjamín Farias (BF), responsable de la calibración de `rmsc04` (2.2.4).
**Activo:** COPEC · **Snapshot real:** 2026-08-23 · **Semillas simuladas:** 30 por tramo · **Fecha:** 2026-10-19

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
| apertura | 690 | 780 | 0,101 | 0,0010 | 0,071 | 1,43 | sí | 0,0014 |
| media_jornada | 900 | 1294 | 0,103 | < 0,0001 | 0,059 | 1,75 | sí | < 0,0001 |
| cierre | 690 | 1072 | 0,159 | < 0,0001 | 0,066 | 2,40 | sí | < 0,0001 |

## 3. Escala de los retornos: Mann–Whitney sobre |retorno| y Brown–Forsythe

| Tramo | p Mann–Whitney | g de Hedges | Efecto | Mediana \|r\| sim (bps) | Mediana \|r\| real (bps) | p Brown–Forsythe | Desvío sim / real |
|---|---:|---:|---|---:|---:|---:|---:|
| apertura | < 0,0001 | 0,18 | trivial | 16,9 | 12,5 | 0,0007 | 1,11 |
| media_jornada | < 0,0001 | 0,11 | trivial | 11,0 | 7,9 | 0,0097 | 0,98 |
| cierre | < 0,0001 | 0,27 | pequeno | 14,0 | 7,1 | < 0,0001 | 1,06 |

## 4. Valores por semilla frente al valor real

El valor real es un único número, así que cada fila compara las semillas contra ese objetivo con Wilcoxon de 1 muestra.

| Tramo | Magnitud | Media sim | Objetivo real | Sesgo (%) | IC 95 % de la media | p |
|---|---|---:|---:|---:|---|---:|
| apertura | Volatilidad 5 min (bps) | 32,1 | 31,8 | 0,8 | [28,4; 35,8] | 0,968 |
| apertura | Volumen mediano por vela | 3580 | 4210 | -15,0 | [3450; 3710] | < 0,0001 |
| apertura | Participación de volumen | 0,294 | 0,200 | 46,9 | [0,289; 0,299] | < 0,0001 |
| media_jornada | Volatilidad 5 min (bps) | 19,8 | 21,4 | -7,4 | [18,3; 21,4] | 0,031 |
| media_jornada | Volumen mediano por vela | 3615 | 5525 | -34,6 | [3533; 3697] | < 0,0001 |
| media_jornada | Participación de volumen | 0,376 | 0,358 | 4,9 | [0,370; 0,382] | < 0,0001 |
| cierre | Volatilidad 5 min (bps) | 24,6 | 24,8 | -0,4 | [21,9; 27,3] | 0,371 |
| cierre | Volumen mediano por vela | 4133 | 7472 | -44,7 | [4053; 4212] | < 0,0001 |
| cierre | Participación de volumen | 0,330 | 0,359 | -8,0 | [0,325; 0,336] | < 0,0001 |

## 5. Patrón entre tramos (Kruskal–Wallis sobre |retorno|)

| Fuente | H | p | Mediana \|r\| apertura (bps) | media jornada | cierre |
|---|---:|---:|---:|---:|---:|
| real | 44,3 | < 0,0001 | 12,5 | 7,9 | 7,1 |
| simulado | 59,5 | < 0,0001 | 16,9 | 11,0 | 14,0 |

- Volatilidad máxima en la apertura: **sí** (por construcción: `fund_vol` se fija por tramo).
- Volumen por vela creciente de apertura a cierre: **sí**.

## 6. Spread (sin prueba de hipótesis)

El spread simulado es cotizado y los reales son proxies de velas de 5 min, así que solo se verifica si cae dentro del rango de los cuatro proxies.

| Tramo | Spread simulado (bps) | Rango real (bps) | Dentro | Veces por debajo del mínimo real |
|---|---:|---|:---:|---:|
| apertura | 0,34 | [2,6; 31,1] | no | 8 |
| media_jornada | 0,33 | [2,7; 20,8] | no | 8 |
| cierre | 0,33 | [3,1; 22,4] | no | 9 |

## 8. Corrección por comparaciones múltiples (Holm)

| Prueba | p crudo | p ajustado (Holm) | ¿Rechaza tras ajustar? |
|---|---:|---:|:---:|
| apertura · brown_forsythe | 0,0007 | 0,0049 | sí |
| apertura · ks | 0,0010 | 0,0058 | sí |
| apertura · ks_estandarizado | 0,0014 | 0,0069 | sí |
| apertura · mannwhitney | < 0,0001 | < 0,0001 | sí |
| apertura · participacion | < 0,0001 | < 0,0001 | sí |
| apertura · volatilidad | 0,968 | 0,968 | no |
| apertura · volumen_vela | < 0,0001 | < 0,0001 | sí |
| cierre · brown_forsythe | < 0,0001 | < 0,0001 | sí |
| cierre · ks | < 0,0001 | < 0,0001 | sí |
| cierre · ks_estandarizado | < 0,0001 | < 0,0001 | sí |
| cierre · mannwhitney | < 0,0001 | < 0,0001 | sí |
| cierre · participacion | < 0,0001 | < 0,0001 | sí |
| cierre · volatilidad | 0,371 | 0,741 | no |
| cierre · volumen_vela | < 0,0001 | < 0,0001 | sí |
| media_jornada · brown_forsythe | 0,0097 | 0,039 | sí |
| media_jornada · ks | < 0,0001 | 0,0002 | sí |
| media_jornada · ks_estandarizado | < 0,0001 | 0,0004 | sí |
| media_jornada · mannwhitney | < 0,0001 | < 0,0001 | sí |
| media_jornada · participacion | < 0,0001 | < 0,0001 | sí |
| media_jornada · volatilidad | 0,031 | 0,093 | no |
| media_jornada · volumen_vela | < 0,0001 | < 0,0001 | sí |

## 9. Limitaciones

- Las pruebas por semilla (sección 4) tienen poca potencia con pocas semillas; el KS y Mann–Whitney sobre la muestra agrupada tienen mucha: con miles de retornos rechazan diferencias pequeñas. Por eso se reportan también el tamaño de efecto y el D/D crítico.
- Los retornos reales y simulados vienen agrupados de varios días: no son estrictamente independientes.
- El valor real de volatilidad, volumen por vela y participación es un único número (no hay muestra diaria real versionada), por eso se usa una prueba de 1 muestra.
- El spread no admite prueba de hipótesis (magnitudes distintas) y el simulador queda decenas de veces por debajo de los proxies reales; el IS absoluto en ABIDES queda subestimado, aunque la comparación entre políticas sigue siendo válida.
- Un solo activo (COPEC) y un solo régimen (previo a la transición del IPSA a MSCI, 1 de septiembre de 2026).

🤖 Generado con [Claude Code](https://claude.com/claude-code)
