# Sistema Maestro-Ejecutores frente a TWAP y VWAP (tareas 3.2.3 y 3.2.4)

**Borrador elaborado por:** PS con apoyo de Claude Code. **Sistema comparado:** PPO_sin_entrenar · **Fecha:** 2026-10-25

Diferencia = slippage del sistema − slippage del benchmark, en bps, pareada por orden y semilla (negativa = el sistema cuesta menos). IC 95 % por bootstrap sobre las diferencias.

## 1. Resumen por tamaño de orden

| Comparación | Benchmark | Celdas | Dif. media (bps) | IC 95 % | Wilcoxon p (celdas) | Wilcoxon p (órdenes) | Lectura |
|---|---|---:|---:|---|---:|---:|---|
| v2 candidata (10 % del día; 5 % en el cierre) | TWAP | 20 | -43,47 | [-72,30; -20,21] | 0,000 | 0,002 | el sistema cuesta menos (IC95 % bajo 0) |
| v2 candidata (10 % del día; 5 % en el cierre) | VWAP | 20 | -50,06 | [-84,29; -23,27] | 0,000 | 0,004 | el sistema cuesta menos (IC95 % bajo 0) |

## 2. Detalle: v2 candidata (10 % del día; 5 % en el cierre)

### PPO_sin_entrenar frente a TWAP

Celdas comunes: 20 (sin ejecución en alguna de las dos: 0).

| Grupo | Celdas | Dif. media (bps) | IC 95 % | Sistema mejor en |
|---|---:|---:|---|---:|
| Tramo: apertura | 8 | -14,43 | [-26,39; -3,92] | 75 % |
| Tramo: cierre | 6 | -33,17 | [-58,41; -3,15] | 83 % |
| Tramo: media_jornada | 6 | -92,50 | [-162,60; -35,13] | 83 % |
| Activo: COPEC | 6 | -20,92 | [-35,04; -6,76] | 67 % |
| Activo: ECL | 6 | -88,65 | [-154,80; -25,66] | 83 % |
| Activo: FALABELLA | 8 | -26,50 | [-48,21; -4,47] | 88 % |

Cumplimiento medio: sistema 88,5 %, TWAP 99,5 %. **El sistema queda bajo el 95 %: la comparación de costo no es equivalente.**

### PPO_sin_entrenar frente a VWAP

Celdas comunes: 20 (sin ejecución en alguna de las dos: 0).

| Grupo | Celdas | Dif. media (bps) | IC 95 % | Sistema mejor en |
|---|---:|---:|---|---:|
| Tramo: apertura | 8 | -14,55 | [-24,61; -4,75] | 75 % |
| Tramo: cierre | 6 | -33,17 | [-58,41; -3,71] | 83 % |
| Tramo: media_jornada | 6 | -114,31 | [-196,77; -46,84] | 100 % |
| Activo: COPEC | 6 | -29,24 | [-41,19; -18,38] | 100 % |
| Activo: ECL | 6 | -104,92 | [-192,23; -28,18] | 83 % |
| Activo: FALABELLA | 8 | -24,54 | [-47,21; -1,77] | 75 % |

Cumplimiento medio: sistema 88,5 %, VWAP 99,4 %. **El sistema queda bajo el 95 %: la comparación de costo no es equivalente.**

## 3. Limitaciones

- Las semillas de una misma orden se parecen entre sí (mismo día simulado): por eso se informa también el Wilcoxon por orden, que usa una media por orden y es más conservador.
- El slippage de una corrida solo cuenta lo ejecutado: con cumplimiento menor que 100 % el costo de lo no ejecutado no entra.
- Para que el pareo sea válido el sistema debe evaluarse con las mismas semillas que los benchmarks.
- El slippage absoluto en ABIDES no es el real (ver `docs/validacion_formal_2.2.5_PS.md`); la comparación relativa sí es informativa.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
