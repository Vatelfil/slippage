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

## Qué cambia según la respuesta

- **D1:** solo el archivo de meta-órdenes que se pasa a los evaluadores (`--meta-ordenes`). El código ya acepta las dos versiones.
- **D3:** el `--riesgo-sobre` de los entrenamientos (`ejecutado` para la 0, `pendiente` para la A).

🤖 Generado con [Claude Code](https://claude.com/claude-code)
