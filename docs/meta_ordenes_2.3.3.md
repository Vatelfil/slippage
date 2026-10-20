# Meta-órdenes de prueba (tarea 2.3.3)

**Borrador elaborado por:** Paolo Sepúlveda (PS) con apoyo de Claude Code, 20 oct 2026. **Pendiente de decisión y revisión por:** Benjamín Farias (BF), responsable de la 2.3.3. Todo lo marcado **DECISIÓN BF** se puede cambiar con un comando (sección 5); nada de lo de aquí está cerrado hasta que BF lo apruebe.

## 1. Qué hay

- `data/meta_ordenes/meta_ordenes_v1.json`: las 10 meta-órdenes oficiales (formato que lee `scripts/colab/benchmarks_meta_ordenes_ps.py`).
- `scripts/generar_meta_ordenes.py`: generador reproducible (sin azar). Las órdenes **no se escriben a mano**.
- `tests/test_generar_meta_ordenes.py`: esquema, reparto del plan, horas de inicio, porcentajes y que el archivo versionado coincide con el que genera el script.

Las 10 órdenes se **reservan para evaluar** (T4 y siguientes). El entrenamiento (2.3.5) no las usa.

## 2. Las 10 órdenes

Propuesta con la opción A de D1 (100 000 acciones por orden). La última columna muestra cuánto serían con la opción B (10 % del volumen del día simulado de cada activo).

| Id | Activo | Tramo de inicio | Hora | Acciones | % del volumen del día | % del volumen que queda hasta el cierre | Semilla | Acciones con la opción B |
|---|---|---|---|---:|---:|---:|---:|---:|
| MO-01 | FALABELLA | apertura | 09:30 | 100 000 | 11,3 % | 11,3 % | 9010 | 88 300 |
| MO-02 | COPEC | apertura | 09:30 | 100 000 | 34,4 % | 34,4 % | 9020 | 29 100 |
| MO-03 | COPEC | apertura | 09:30 | 100 000 | 34,4 % | 34,4 % | 9030 | 29 100 |
| MO-04 | ECL | apertura | 09:30 | 100 000 | 31,1 % | 31,1 % | 9040 | 32 100 |
| MO-05 | COPEC | media jornada | 11:00 | 100 000 | 34,4 % | 49,1 % | 9050 | 29 100 |
| MO-06 | ECL | media jornada | 11:00 | 100 000 | 31,1 % | 44,2 % | 9060 | 32 100 |
| MO-07 | ECL | media jornada | 11:00 | 100 000 | 31,1 % | 44,2 % | 9070 | 32 100 |
| MO-08 | FALABELLA | cierre | 14:00 | 100 000 | 11,3 % | 34,9 % | 9080 | 88 300 |
| MO-09 | FALABELLA | cierre | 14:00 | 100 000 | 11,3 % | 34,9 % | 9090 | 88 300 |
| MO-10 | FALABELLA | cierre | 14:00 | 100 000 | 11,3 % | 34,9 % | 9100 | 88 300 |

- **Fecha de referencia:** 2026-08-23 (snapshot de la calibración). **Precio de llegada** (`p_referencia`, CLP por acción): el `r_bar` de la calibración de cada activo.
- **Volumen simulado:** mediana de las 30 jornadas de la validación 2.2.5 con la calibración vigente de cada activo (`data/colab_resultados/validacion_2_2_5_despues_*.json`). "Lo que queda hasta el cierre" suma los tramos desde el de inicio de la orden hasta el cierre; es una aproximación (los tramos de la calibración cortan a las 11:30 y la orden de media jornada arranca a las 11:00).
- **Semillas:** `semilla = 9000 + 10 · índice`; el runner suma la semilla de cada corrida (1, 2, …). Son distintas de las de calibración (100–300), entrenamiento (1000 en adelante) y evaluación de β (5000).

## 3. Decisiones que son de BF

**D1: ¿tamaño de las órdenes?** El plan dice 100 000 acciones (opción A), que es lo que rige si no se decide otra cosa. El plan calculaba que eso era ~10 % del día. Con la calibración nueva de COPEC y ECL no es así: su día simulado es de ~290 000 y ~320 000 acciones.

| Activo | Volumen del día simulado | 100 000 desde apertura | desde media jornada | desde cierre |
|---|---:|---:|---:|---:|
| FALABELLA | 882 768 | 11,3 % | 15,8 % | 34,9 % |
| COPEC | 290 721 | 34,4 % | 49,1 % | 104,3 % |
| ECL | 321 093 | 31,1 % | 44,2 % | 95,8 % |

Una orden de 100 000 que parte en el cierre en COPEC o ECL sería el 96–104 % del volumen que queda: no se puede ejecutar. Por eso, con la opción A, **el cierre se asigna a FALABELLA** (35 % de lo que queda). Aun así, las órdenes de COPEC y ECL de 100 000 son el 31–49 % del volumen que queda, lo que significa un impacto de precio muy grande. La opción B (un porcentaje del volumen del día, por ejemplo 10 %) da órdenes de ~29 000–32 000 acciones en COPEC y ECL y ~88 000 en FALABELLA, y es la que menos distorsiona el mercado simulado. El plan dejaba la B como análisis de sensibilidad del Sprint 7.

**D2 / reparto:** FALABELLA 4, COPEC 3, ECL 3; apertura 4, media jornada 3, cierre 3 (lo pedido por el plan), sin repetir activo-tramo-semilla. El reparto concreto está en `REPARTO` de `scripts/generar_meta_ordenes.py` y es un criterio mío: cierre solo en FALABELLA por lo de D1. Un reparto cruzado (cada activo en los tres tramos) exige órdenes más chicas (opción B).

**D5 / hora de media jornada:** el orquestador y el runner parten la media jornada a las 11:00 (corte del Maestro), no a las 11:30 de la calibración. Se mantuvo 11:00 para ser coherente con los benchmarks.

## 4. Validación de ejecutabilidad (paso 5 del plan)

El plan pide correr cada orden con TWAP en el simulador congelado y verificar que se completa al menos el 95 %. Esto lo hace el runner de la 2.3.4 (`execution_rate` de cada corrida de TWAP), así que **se valida con la corrida de benchmarks** y su resultado se informa en `docs/benchmarks_2.3.4_PS.md`. Si alguna orden no llega al 95 % no se cambia en silencio: se reporta como límite demostrado con su porcentaje, y BF decide si baja el tamaño (sección 5).

**Resultado de la validación (corrida de benchmarks en Colab con ABIDES, 20 oct 2026):**

- **Opción A (100 000 acciones), 2 semillas:** solo **5 de 10 órdenes** llegan en promedio al 95 % (11 de 20 corridas). Fallan MO-02 (92,5 %), MO-06 (94,0 %), MO-07 (94,1 %), MO-09 (89,6 %) y MO-10 (84,5 %). El cumplimiento varía mucho entre semillas (MO-10: 75,3 % y 93,6 %), así que con 2 semillas el promedio es aproximado.
- **Opción B (10 % del volumen del día), 1 semilla:** **8 de 10 órdenes** llegan al 95 %. Las 7 órdenes de COPEC, ECL y FALABELLA en apertura cumplen con más de 99,9 %. Fallan las órdenes de FALABELLA en el cierre MO-09 (94,5 %) y MO-10 (78,6 %): en el cierre, 88 300 acciones siguen siendo el 31 % del volumen que queda.
- **Lectura:** con A, las órdenes superan la liquidez del simulador; con B, el problema queda solo en FALABELLA al cierre. Una salida posible es un porcentaje menor para esas tres órdenes (por ejemplo 5 % del día, ~44 100 acciones, 15 % de lo que queda). Esa prueba está pendiente. **La decisión de D1 es de BF.**
- Detalle completo en `docs/benchmarks_2.3.4_PS.md` (sección 3).

## 5. Cómo cambiar algo

```bash
python scripts/generar_meta_ordenes.py                       # versión actual (100 000 por orden)
python scripts/generar_meta_ordenes.py --cantidad 30000      # otro tamaño fijo
python scripts/generar_meta_ordenes.py --pct-dia 0.10        # opción B (10 % del día de cada activo)
python -m pytest tests/test_generar_meta_ordenes.py -q       # el test exige que el archivo versionado coincida con el script
```

Para otro reparto se edita `REPARTO` (el test comprueba que se mantengan 4/3/3 y 4/3/3).

## 6. Limitaciones

- El volumen simulado es el de la calibración (no el real), y el volumen por vela simulado está 15–45 % bajo el real en COPEC y ECL (ver `docs/calibracion_rmsc04_COPEC_ECL_P4_PS.md`).
- Una sola fecha de referencia y un solo régimen (previo a la transición del IPSA a MSCI).
- Con tamaños grandes frente al mercado simulado, el slippage de los benchmarks se dominará por el impacto de la propia orden.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
