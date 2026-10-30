# 3.1.3: avance con el bloque 1 de las 30 corridas (30 de octubre)

**Elaborado por:** PS con apoyo de Claude Code. **Datos:** `data/colab_resultados/corridas_30/bloque_1/` (JSON crudos) y `tabla_bloque1/` (tabla y gráfico que arma el cuaderno), del cuaderno `Colab_30corridas_bloque1` corrido por PS en Colab con ABIDES.

**Es un avance parcial:** 9 de las 30 corridas. El resultado de la 3.1.3 se escribe cuando estén los cuatro bloques.

## 1. Qué se corrió

- **Sistema final:** Maestro entrenado y Ejecutor `rimit` s1000. Se evalúa muestreando la política, con impacto acumulado.
- **Comparación:** TWAP y VWAP en las mismas órdenes y semillas.
- **Órdenes:** MO-01 (FALABELLA, 88.300 acciones), MO-02 y MO-03 (COPEC, 29.100). Las tres empiezan en la apertura.
- **Semillas:** 1, 2 y 3, con escenario de liquidez media.
- **Cumplimiento:** 1,00 en las tres estrategias.

## 2. Resultado (9 pares)

| Estrategia | Media (bps) | Mediana | Mejor | Peor |
|---|---:|---:|---:|---:|
| Sistema final | 30,6 | 21,6 | 11,2 | 63,6 |
| TWAP | 49,0 | 30,4 | −17,0 | 128,7 |
| VWAP | 49,2 | 24,5 | −26,2 | 144,7 |

| Diferencia pareada | bps (IC 95 %) | p Wilcoxon | p t-test |
|---|---|---:|---:|
| Sistema − TWAP | −18,4 [−38,9; +3,3] | 0,13 | 0,15 |
| Sistema − VWAP | −18,7 [−44,5; +8,0] | 0,25 | 0,23 |

## 3. Lectura

- **Con 9 pares, el sistema no se distingue de TWAP ni de VWAP:** los dos intervalos incluyen el 0.
- **La media del sistema es más baja** porque evita los peores días de TWAP en COPEC (MO-02: 89, 129 y 62 bps con TWAP, contra 30, 64 y 22 con el sistema). Pero también pierde los días buenos: en MO-01 con la semilla 1, TWAP ganó plata (−17 bps) y el sistema pagó 19.
- **El costo varía mucho entre jornadas** (de −26 a 145 bps), como se esperaba: ≈ 40 bps de desviación.
- **No hay que sacar conclusiones todavía.** Faltan 21 corridas, y en estas 9 todas las órdenes parten en la apertura.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
