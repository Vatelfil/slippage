# Hoja de decisiones D1 y D3 (para BF)

**Elaborado por:** PS con apoyo de Claude Code, 29 de octubre de 2026. **Decide:** BF. **Plazo propuesto:** martes 3 de noviembre. Si no hay respuesta, PS aplica la respuesta por defecto y la presenta en la Sprint Review del 6 de noviembre como «regla por defecto aplicada». BF puede cambiarla después.

Para responder basta con copiar una línea: `D1: v2` o `D1: v1`, y `D3: regla` o `D3: 0` o `D3: A`.

## D1. Tamaño de las meta-órdenes

| Opción | Qué es | A favor | En contra |
|---|---|---|---|
| v1 | 100.000 acciones fijas por orden (`data/meta_ordenes/meta_ordenes_v1.json`) | Es lo que se definió primero | TWAP completa solo 5 de las 10 órdenes: se comparan órdenes que nadie pudo terminar |
| **v2 (por defecto)** | 10 % del volumen del día simulado de cada activo; 5 % si la orden parte en el cierre (`data/meta_ordenes/meta_ordenes_v2_candidata.json`) | 10 de 10 órdenes ejecutables (`docs/benchmarks_2.3.4_v2_PS.md`); el tamaño relativo al volumen es la medida estándar y es la que usa el impacto acumulado del Maestro | Hay que dejar claro en el informe que el tamaño es relativo |

**Los tres tamaños de la 3.2.1:** con la v2 y `--factor-tamano 0.5 / 1 / 1.5` quedan en 5 %, 10 % y 15 % del volumen del día (en el cierre, la mitad).

## D3. Cómo calcula el riesgo la recompensa del Ejecutor

| Opción | Qué es |
|---|---|
| 0 | Riesgo sobre lo ejecutado (fórmula del Título I) |
| A | Riesgo sobre lo pendiente |
| **regla (por defecto)** | Se decide con los cuadernos `Colab_mid_decision_A/B` (recompensa corregida, mismas semillas para las dos opciones). Se queda la **opción 0**, salvo que la A cumpla la orden con argmax (≥ 95 %) en más redes **y** no cueste más: el límite superior del IC 95 % de la diferencia A − 0, en 300 semillas, debe ser menor que +1 bps |

**Por qué la propuesta es la opción 0:**
- La opción A existía para que la red no se quedara esperando. La penalización por lo no comprado ya lo resuelve: en ABIDES las redes completan la orden (cumplimiento ≈ 1,0).
- La opción 0 no obliga a declarar otra desviación del Título I.
- La evidencia anterior que favorecía la A se midió con la recompensa con falla (`docs/revision_opus_PS.md`, H1), así que no sirve para decidir.

## Resultado de D3 (29 de octubre, noche)

Con la recompensa corregida, en las mismas semillas:
- **Opción A − opción 0:** −0,60 bps (IC −1,04 a −0,16).
- **Condición (a), completar más órdenes con argmax:** no se cumple; las dos completan el 100 %.
- **Respuesta por defecto que da la regla:** **D3: 0**.

Por costo, la A es algo menos mala, pero todas las redes con esa recompensa cuestan más que su control (`docs/reeval_300_mid_resultado_PS.md`). BF puede cambiarla.

## Qué cambia según la respuesta

- **D1:** solo el archivo de meta-órdenes que se pasa a los evaluadores (`--meta-ordenes`). El código ya acepta las dos versiones.
- **D3:** el `--riesgo-sobre` de los entrenamientos (`ejecutado` para la 0, `pendiente` para la A).

## Respuesta de BF (2 de noviembre de 2026)

**D1: v2**

**D3: 0**

**D1.**
- Se confirma lo que BF decidió el 22 de octubre (`docs/meta_ordenes_2.3.3.md`, secciones 2 y 8). Esa rama no llegó a `main`, y por eso aquí aparecía como respuesta por defecto.
- Con 100 000 acciones (v1), TWAP completa solo 5 de las 10 órdenes. Con la v2 completa 10 de 10 (19 de 20 corridas sobre el 95 %); MO-10 queda en el borde (90,2 % y 100 %).
- La v2 oficial (`meta_ordenes_v2.json`) y la candidata de PS coinciden en los seis campos que leen los evaluadores (`id`, `ticker`, `tramo_inicio`, `cantidad`, `semilla`, `volumen_dia_simulado`). La firma de las corridas no depende del archivo. La 3.1.3 y las 90 corridas quedan válidas sin repetir nada.

**D3.**
- Se aplica la regla fijada el 29 de octubre, antes de ver los datos corregidos.
- Con la recompensa corregida, las dos opciones completan el 100 % con argmax: no se cumple la condición (a). A − 0 = −0,60 bps (IC −1,04 a −0,16).
- **BF retira su propuesta del 22 de octubre** de pasar a la opción A (`docs/entrenamiento_inicial_2.3.5.md`, sección 4). Esa propuesta se apoyaba en un cumplimiento con argmax de 0,000 / 1,000 / 0,904, medido con la recompensa con falla H1 (`docs/revision_opus_PS.md`).
- **El −0,60 bps no aplica al sistema final.** Se midió en redes entrenadas con `mid_decision`, no en el tipo de Ejecutor que se usa. El Ejecutor elegido (`rimit__d3_opcion0_s1000`) es imitación + PPO con la recompensa de llegada, y la opción A nunca se probó con imitación.
- **Costo de pasar a la A:** recalcular β\*, reentrenar y volver a elegir el Ejecutor, reentrenar el Maestro (se entrenó con ese Ejecutor) y repetir la 3.1.3 y las 90 corridas: más de 10 horas de Colab. A cambio se ganarían como mucho 0,6 bps, frente a una dispersión de ≈ 40 bps entre jornadas.
- **Se declara (R6):** la regla de vigilancia original se aplicó el 22 de octubre sobre evidencia inválida. Se reemplazó por una regla fijada antes de los datos corregidos.

Resumen de las decisiones del sprint: `docs/decisiones_sprint6_BF.md`.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
