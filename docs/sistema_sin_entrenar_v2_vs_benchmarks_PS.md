# Sistema Maestro-Ejecutores frente a TWAP y VWAP (tareas 3.2.3 y 3.2.4)

**Borrador elaborado por:** PS con apoyo de Claude Code. **Sistema comparado:** PPO_sin_entrenar · **Fecha:** 2026-10-25

Diferencia = slippage del sistema − slippage del benchmark, en bps, pareada por orden y semilla (negativa = el sistema cuesta menos). IC 95 % por bootstrap sobre las diferencias.

## 1. Resumen por tamaño de orden

| Comparación | Benchmark | Celdas | Dif. media (bps) | IC 95 % | Wilcoxon p (celdas) | Wilcoxon p (órdenes) | Lectura |
|---|---|---:|---:|---|---:|---:|---|
| v2 candidata (10 % del día; 5 % en el cierre) | TWAP | 20 | 16,53 | [-15,91; 49,84] | 0,430 | 0,375 | sin diferencia clara (IC95 % incluye 0) |
| v2 candidata (10 % del día; 5 % en el cierre) | VWAP | 20 | 9,94 | [-22,52; 41,50] | 0,729 | 0,695 | sin diferencia clara (IC95 % incluye 0) |

## 2. Detalle: v2 candidata (10 % del día; 5 % en el cierre)

### PPO_sin_entrenar frente a TWAP

Celdas comunes: 20 (sin ejecución en alguna de las dos: 0).

| Grupo | Celdas | Dif. media (bps) | IC 95 % | Sistema mejor en |
|---|---:|---:|---|---:|
| Tramo: apertura | 8 | 18,85 | [-18,34; 61,65] | 50 % |
| Tramo: cierre | 6 | -21,51 | [-51,22; 7,17] | 67 % |
| Tramo: media_jornada | 6 | 51,48 | [-35,33; 127,20] | 33 % |
| Activo: COPEC | 6 | 35,91 | [7,53; 64,24] | 17 % |
| Activo: ECL | 6 | 53,11 | [-37,75; 133,15] | 50 % |
| Activo: FALABELLA | 8 | -25,44 | [-50,13; -1,10] | 75 % |

Cumplimiento medio: sistema 66,3 %, TWAP 99,5 %. **El sistema queda bajo el 95 %: la comparación de costo no es equivalente.**

### PPO_sin_entrenar frente a VWAP

Celdas comunes: 20 (sin ejecución en alguna de las dos: 0).

| Grupo | Celdas | Dif. media (bps) | IC 95 % | Sistema mejor en |
|---|---:|---:|---|---:|
| Tramo: apertura | 8 | 18,73 | [-20,18; 63,06] | 62 % |
| Tramo: cierre | 6 | -21,51 | [-51,22; 7,17] | 67 % |
| Tramo: media_jornada | 6 | 29,67 | [-55,82; 101,15] | 33 % |
| Activo: COPEC | 6 | 27,59 | [-5,28; 60,10] | 33 % |
| Activo: ECL | 6 | 36,84 | [-58,52; 111,30] | 50 % |
| Activo: FALABELLA | 8 | -23,47 | [-48,65; 0,43] | 75 % |

Cumplimiento medio: sistema 66,3 %, VWAP 99,4 %. **El sistema queda bajo el 95 %: la comparación de costo no es equivalente.**

## 3. Limitaciones

- Las semillas de una misma orden se parecen entre sí (mismo día simulado): por eso se informa también el Wilcoxon por orden, que usa una media por orden y es más conservador.
- El slippage de una corrida solo cuenta lo ejecutado: con cumplimiento menor que 100 % el costo de lo no ejecutado no entra.
- Para que el pareo sea válido el sistema debe evaluarse con las mismas semillas que los benchmarks.
- El slippage absoluto en ABIDES no es el real (ver `docs/validacion_formal_2.2.5_PS.md`); la comparación relativa sí es informativa.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
