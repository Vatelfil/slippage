# Control de la 3.2.3: qué aporta el Maestro y qué aportan los Ejecutores

**Quién:** PS, con apoyo de Claude Code. **Fecha:** 1 de noviembre de 2026, **antes** de correr el control.
**Tipo:** análisis agregado al plan (`docs/plan_analisis_3_2_3_PS.md`) **después** de ver la liquidez media de las 90 corridas.
- Se declara como cambio del plan.
- No reemplaza al test principal: el resultado de la 3.2.3 sigue siendo sistema contra TWAP en las 90 corridas.

## Por qué se agrega

- En la liquidez media, el Maestro eligió α = 0,5 y 15 minutos en el 98 % de sus decisiones (`docs/qa_sistema_media_90_PS.md`).
- Surge una pregunta que la comisión probablemente haga: **¿el Maestro aporta algo más que un calendario fijo?** También interesa saber cuánto de la diferencia con TWAP viene del Maestro (cuándo comprar) y cuánto de los Ejecutores (cómo comprar dentro de cada ventana).

**Qué no cambia:**
- No se reentrena nada.
- No se repite ninguna de las 90 corridas.
- Nadie del grupo tiene que rehacer su parte.

## Qué se corre

Son las mismas órdenes, semillas (4, 5 y 6), liquidez (media de la v3), impacto, corrección del cierre y Ejecutores que las 90. Lo único que cambia es quién decide en el nivel del Maestro:

| Estrategia | Quién decide cuánto y cuándo | Quién compra dentro de la ventana |
|---|---|---|
| `PPO_sistema` (ya corrida) | Maestro PPO entrenado | Ejecutores PPO |
| `Regla_fija` (nueva) | Siempre α = 0,5 y 15 min | Ejecutores PPO |
| `Regla_uniforme` (nueva) | Partes iguales cada media hora, 15 min (el calendario de TWAP) | Ejecutores PPO |
| `TWAP` (ya corrida) | Partes iguales cada media hora, 15 min | Regla de TWAP |

**Detalle técnico del pareo:**
- Con `--regla`, la red del Maestro se sigue consultando y su acción se descarta. Así, la secuencia aleatoria de los Ejecutores es la misma que en la corrida del sistema.
- Cuando la regla coincide con lo que eligió el Maestro, la corrida sale idéntica. Está probado en `tests/test_reglas_control_3_2_3.py`.

## Qué se compara

| # | Comparación | Pregunta |
|---|---|---|
| 1 | Regla fija − sistema | ¿El Maestro hace algo distinto de «α = 0,5 siempre»? |
| 2 | Sistema − regla uniforme | Aporte del **calendario** del Maestro, con los mismos Ejecutores |
| 3 | Regla uniforme − TWAP | Aporte de los **Ejecutores**, con el mismo calendario |

- **Estadística:** Wilcoxon pareado con corrección de Holm para las tres comparaciones, IC 95 % por bootstrap y d de Cohen.
- **Descomposición exacta:** sistema − TWAP = (2) + (3), corrida por corrida.

## Qué se espera (escrito antes de ver el control)

1. **Regla fija ≈ sistema.** En la media, 25 de las 30 corridas tienen al Maestro eligiendo α = 0,5 y 15 minutos en todas sus decisiones. Esas 25 deberían salir **idénticas**. Si no salen idénticas, hay algo no determinista en la simulación, y eso también se informa.
2. **El calendario del Maestro (2) depende del día:**
   - gana cuando el precio sube y pierde cuando baja;
   - en promedio puede quedar cerca de 0, con mucha dispersión.
3. **Los Ejecutores (3)** son la parte con más chance de mostrar una ventaja estable. Comparan contra TWAP dentro de la misma ventana, así que el movimiento del día les afecta poco y la dispersión debería ser menor.

**Cómo se usa en la tesis (capítulo 7):**
- Si (1) se cumple, se informa que el Maestro aprendió un calendario fijo y se explica la causa: el entrenamiento sin la corrección del cierre y un S_M sin información de mercado.
- El aporte de los Ejecutores (3) se informa como resultado propio de la arquitectura.

## Cómo se corre

- **Cuadernos:** `notebooks/Colab_control_reglas_media_A.ipynb` y `_B.ipynb`. Los corre PS, los dos en paralelo, ≈ 2 h cada uno.
- **Salida:** `control_reglas_media.zip`.
- **Análisis:**

```
python scripts/control_reglas_3_2_3.py \
    --entradas data/colab_resultados/corridas_90/media <carpeta del control> \
    --out-dir data/analysis/3_2_3_control --out-md docs/control_reglas_3_2_3_resultado_PS.md
```

- **Si sobra Colab:** se puede correr lo mismo en baja y alta, cambiando `ESCENARIO` en la celda 10. Es opcional.
