# Plan de análisis de la 3.2.3 (comparación estadística)

**Quién:** PS, con apoyo de Claude Code. **Fecha:** 31 de octubre de 2026, **antes** de correr las 90 corridas del Sprint 7.

## Para qué sirve este documento

Fija de antemano qué test responde la pregunta de la tesis, con qué nivel de significancia y qué se informa pase lo que pase. Así nadie puede decir que se eligió, después de ver los datos, el test que daba mejor resultado.

Si algo de este plan se cambia después de ver las 90, se declara como desviación y se informan los dos resultados.

## 1. Datos

- **Corridas:** 3 escenarios de liquidez (baja, media y alta, según la versión que acepte BF) × 10 meta-órdenes × 3 semillas = 90 corridas.
- **Estrategias:** el sistema (Maestro + Ejecutores, `PPO_sistema`, con `--completar-al-cierre` e impacto acumulado), TWAP y VWAP.
- **Pareo:** las tres estrategias usan el mismo día simulado (escenario, orden y semilla).
- **Costo:** slippage contra el precio de llegada, en bps (`slippage_bps`).
- **Requisito:** todas las corridas deben tener un cumplimiento ≥ 95 %. Si alguna queda bajo ese nivel, se repite. Si no se puede repetir, se informa con el costo ajustado (`--penalizacion-bps 30`, como en la 3.1.3).

## 2. Pregunta principal (la que responde la tesis)

**¿El sistema cuesta menos que TWAP?**

| Qué | Definición |
|---|---|
| Medida | Diferencia por corrida: costo del sistema − costo de TWAP. Negativa = el sistema cuesta menos |
| Muestra | Las 90 diferencias pareadas, de los tres escenarios juntos |
| Test principal | **Wilcoxon de rangos con signo**, pareado y bilateral. No supone normalidad |
| Nivel | α = 0,05 |
| Complemento | t-test pareado, que se usa si el Shapiro-Wilk de las diferencias no rechaza la normalidad (p ≥ 0,05) |
| Efecto | Diferencia media con IC 95 % por bootstrap (3.000 remuestreos), d de Cohen pareado y correlación biserial de rangos (r) |
| Conclusión | Se informa la reducción medida con su intervalo, **sin umbral fijo**, porque el Título I no fija un 10 % |

**Contra VWAP:** se hace el mismo análisis, como pregunta secundaria.

**Por qué Wilcoxon y no solo el t-test:**
- Los costos tienen colas largas: en la 3.1.3, una orden (MO-06) movía el promedio de −12,5 a −22 bps.
- Wilcoxon compara rangos, así que una sola corrida extrema no lo domina.

## 3. Preguntas secundarias

| Pregunta | Test | Corrección |
|---|---|---|
| ¿El sistema gana en cada liquidez? | Wilcoxon por escenario (30 corridas cada uno) | Holm (3 comparaciones) |
| ¿La ventaja depende de la liquidez? | **Kruskal-Wallis** sobre las diferencias de los tres escenarios, con épsilon² como efecto | — |
| Si Kruskal-Wallis sale significativo: ¿entre qué escenarios? | **Mann-Whitney U** por pares, con r como efecto | Holm |
| Control del anterior | Friedman, porque las mismas órdenes y semillas se repiten en cada escenario (bloques) | — |

Los tres tests que pide el Excel (Wilcoxon, Mann-Whitney y Kruskal-Wallis) quedan cubiertos. Cada uno se usa donde corresponde: Wilcoxon para datos pareados, y Kruskal-Wallis y Mann-Whitney para comparar escenarios.

## 4. Robustez (se informan siempre, no reemplazan al principal)

1. **Sin MO-06:** la orden que más pesó en la 3.1.3.
2. **Promedio por orden y semilla:** la misma orden aparece en los tres escenarios, así que las 90 no son del todo independientes. Se promedia cada orden y semilla entre escenarios (30 valores) y se repite el Wilcoxon.
3. **Costo ajustado** con 30 bps por acción no ejecutada, solo si alguna corrida queda incompleta.

## 5. Qué esperar (calculado con la 3.1.3)

Con las 30 corridas de la 3.1.3, la desviación de las diferencias (sistema − TWAP) es de 78,7 bps.

| Si la ventaja real es… | Margen con 30 corridas | Probabilidad de que salga significativo con 30 | Margen con 90 | Probabilidad con 90 |
|---|---|---|---|---|
| −22 bps (lo medido en la 3.1.3) | ±28 | 34 % | **±16** | **76 %** |
| −12,5 bps (lo medido sin MO-06) | ±28 | 14 % | ±16 | 33 % |

**Cómo leerlo:**
- Si la ventaja real se parece a la medida, con 90 corridas lo más probable es que el test principal salga significativo, pero no es seguro (3 de 4 veces).
- Si la ventaja real es más chica, como sin MO-06, lo más probable es que no salga significativo, aunque el promedio siga a favor del sistema.
- **Por escenario** (30 cada uno), es esperable que no salga significativo. Eso no es una falla: es el tamaño de la muestra.
- Por eso la conclusión se escribe **con el intervalo**, no con un sí o no: por ejemplo, «el sistema redujo el costo en X bps (IC 95 % [a; b])».

## 6. Prueba del método con las 30 corridas de la 3.1.3

Se programó `scripts/comparacion_estadistica_3_2_3.py` y se probó con las 30 corridas oficiales de la 3.1.3. Esto es solo un ensayo: el resultado de la 3.2.3 es el de las 90. Los números calzan con el resultado oficial (`docs/corridas_30_corregidas_resultado_PS.md`).

| Comparación | n | Dif. media (bps) | IC 95 % | Shapiro p | Wilcoxon p | t p | d de Cohen | r | Gana el sistema |
|---|---|---|---|---|---|---|---|---|---|
| Sistema − TWAP | 30 | −22,15 | [−50,01; 4,43] | 0,42 | 0,096 | 0,134 | −0,28 (pequeño) | −0,35 | 20 de 30 |
| Sistema − TWAP, sin MO-06 | 27 | −12,46 | [−34,11; 11,00] | 0,057 | 0,141 | 0,306 | −0,20 (pequeño) | −0,33 | 18 de 27 |
| Sistema − VWAP | 30 | −25,13 | [−56,91; 5,04] | 0,34 | 0,129 | 0,136 | −0,28 (pequeño) | −0,32 | 20 de 30 |

**Normalidad (paso 1 del Excel):**
- Shapiro-Wilk no rechaza la normalidad de las diferencias (p = 0,42 contra TWAP y 0,34 contra VWAP).
- El gráfico Q-Q muestra los puntos cerca de la recta, con las dos colas un poco más largas.
- Sin MO-06, el p queda en el límite (0,057).
- **Decisión:** se mantiene Wilcoxon como test principal y el t-test como complemento. La normalidad se vuelve a revisar con las 90.

**Archivos del ensayo:** `data/analysis/3_2_3_prueba_30/`, que contiene `tabla_p_valores.md`, `comparacion_3_2_3.json`, `qq_diferencias.png`, `bosque_diferencias.png` y `diferencias_por_escenario.png`. La explicación está en `docs/guia_graficos.md`.

## 7. Cómo se corre con las 90

Con los JSON de las tres liquideces, o con el `corridas.csv` que arma BF en la 3.2.2:

```
python scripts/comparacion_estadistica_3_2_3.py \
    --entradas data/colab_resultados/corridas_90 \
    --sistema PPO_sistema --out-dir data/analysis/3_2_3 \
    --out-md docs/comparacion_estadistica_3_2_3_PS.md --titulo "Comparación estadística 3.2.3 (90 corridas)"
```

Con eso se obtienen la tabla de p-valores (total, por escenario con Holm, sin MO-06 y promediado), Kruskal-Wallis, Mann-Whitney y Friedman entre escenarios, y los tres gráficos.
