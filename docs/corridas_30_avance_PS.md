# 3.1.3: avance de las 30 corridas, bloques 1 a 3 (30 de octubre)

**Elaborado por:** PS con apoyo de Claude Code. **Datos:**
- `data/colab_resultados/corridas_30/bloque_1/` a `bloque_3/`: los JSON crudos.
- `tabla_bloques1a3/`: tabla y gráfico que arma el cuaderno con los tres bloques. Se tomó del zip del bloque 2, el más completo.
- `tabla_bloque1/`: el primer avance, con 9 corridas.

Los cuadernos `Colab_30corridas_bloque1` a `3` los corrió PS en Colab con ABIDES.

> **Superado:** el resultado con las 30 corridas está en `docs/corridas_30_resultado_PS.md`.

**Avance parcial: 24 de 30 corridas (8 meta-órdenes × 3 semillas).** Falta el bloque 4, con MO-09 y MO-10. El resultado de la 3.1.3 se escribe con los cuatro bloques.

## 1. Qué se corrió

- **Sistema final:** Maestro entrenado y Ejecutor `rimit` s1000. Se evalúa muestreando la política, con impacto acumulado.
- **Comparación:** TWAP y VWAP en las mismas órdenes y semillas (1, 2 y 3), con liquidez media.

## 2. Resultado (24 pares)

| Estrategia | Media (bps) | Mediana | Mejor | Peor | Cumplimiento |
|---|---:|---:|---:|---:|---:|
| **Sistema final** | **50,1** | 38,2 | −72,2 | 183,0 | 0,99 |
| TWAP | 76,1 | 81,8 | −173,3 | 365,8 | 1,00 |
| VWAP | 79,8 | 83,9 | −170,3 | 391,9 | 1,00 |

| Diferencia pareada | bps (IC 95 %) | p Wilcoxon | p t-test |
|---|---|---:|---:|
| Sistema − TWAP | −26,0 [−58,4; +6,0] | 0,11 | 0,15 |
| Sistema − VWAP | −29,7 [−66,8; +6,5] | 0,13 | 0,15 |

### Por meta-orden (media de 3 semillas, bps)

| Orden | Acción, tramo | Sistema | TWAP | Sistema − TWAP | Semillas en que gana el sistema |
|---|---|---:|---:|---:|---:|
| MO-01 | FALABELLA, apertura | 28,3 | 11,3 | +17,0 | 1 de 3 |
| MO-02 | COPEC, apertura | 38,4 | 93,2 | −54,8 | 3 de 3 |
| MO-03 | COPEC, apertura | 25,1 | 42,6 | −17,5 | 3 de 3 |
| MO-04 | ECL, apertura | 30,5 | 41,4 | −10,9 | 2 de 3 |
| MO-05 | COPEC, media jornada | 40,0 | 41,3 | −1,4 | 2 de 3 |
| MO-06 | ECL, media jornada | 146,3 | 255,7 | −109,4 | 2 de 3 |
| MO-07 | ECL, media jornada | 50,7 | 49,1 | +1,6 | 2 de 3 |
| MO-08 | FALABELLA, cierre | 41,4 | 73,9 | −32,5 | 2 de 3 |

## 3. Lectura

- **El sistema cuesta menos que TWAP y VWAP en promedio, pero todavía no es significativo.** Es ≈ 26 bps más barato que TWAP (34 %), y gana en 17 de 24 pares. Aun así, los dos intervalos incluyen el 0 (p ≈ 0,11 a 0,15).
- **La dirección se mantiene** del bloque 1 (−18 bps) a los tres bloques (−26 bps). La mediana de la diferencia también es negativa: −19 bps.
- **Una orden pesa mucho.** MO-06 aporta −109 bps. Sin ella, la diferencia baja a −14 bps, con un intervalo de [−40; +16] en un cálculo aparte con bootstrap.
- **La variación es mayor que la supuesta.** La desviación de la diferencia pareada es ≈ 85 bps; se había estimado en ≈ 40. Con 30 pares, el IC quedará en unos ±30 bps. Es probable que la 3.1.3 cierre **sin diferencia significativa**, aunque la dirección favorezca al sistema.
- **Ojo con MO-08 (cierre):** el sistema compra solo el 92 a 93 % de la orden, y TWAP el 100 %. Parte de su ventaja ahí puede venir de comprar menos. Es la única orden que queda bajo el 95 %. El Maestro parece quedarse sin tiempo cuando la orden empieza al cierre (inferido, no revisado en el código).
- **Por qué el sistema es más barato (hipótesis, no medida):** el Maestro reparte la compra distinto que TWAP y evita barrer en los momentos caros. El Ejecutor PPO solo no le gana a TWAP límite (+1 bps en 300 semillas). Por eso la ventaja vendría del reparto del Maestro y no de la ejecución fina.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
