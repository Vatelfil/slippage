# Meta-órdenes de prueba (tarea 2.3.3)

**Responsable:** Benjamín Farias (BF). **Estado:** Hecho con límite demostrado, aprobado por BF el 22 de octubre de 2026. Las 10 órdenes son ejecutables en promedio, pero MO-10 queda en el borde del criterio: una de sus dos semillas completa solo el 90,2 % (media 95,1 %), y con 2 semillas por orden no se puede asegurar que su media siga sobre el 95 % con más semillas (sección 6). **Revisión cruzada (sección 8 del plan):** PS (método y números) y MR (que corra con el orquestador).

> **Actualización del 2 de noviembre:** BF ratifica **D1 = v2**. La v2 es la versión oficial, y la candidata de PS que usaron la 3.1.3 y las 90 corridas es equivalente en todo lo que leen los evaluadores. Esas corridas siguen válidas y no hay que repetirlas (sección 8).

## 1. Qué hay

| Archivo | Qué es |
|---|---|
| `data/meta_ordenes/meta_ordenes_v2.json` | **Las 10 meta-órdenes oficiales** (decisión D1 de BF). Es lo que se usa para evaluar desde ahora. |
| `data/meta_ordenes/meta_ordenes_v1.json` | Versión histórica de 100 000 acciones por orden. Es la que leyó la corrida base de la 2.3.4; se conserva sin cambios. |
| `data/meta_ordenes/meta_ordenes_v2_candidata.json` | Equivalente operativo de la v2, generado por PS el 23 de octubre (`c6118de`). Es el que leen los cuadernos de la 3.1.3 y de las 90 corridas. Trae las mismas 10 órdenes, sin los campos reales (sección 8). |
| `scripts/generar_meta_ordenes.py` | Generador reproducible y sin azar. Sin argumentos escribe la versión oficial. Las órdenes no se escriben a mano. |
| `scripts/validar_meta_ordenes.py` | Cruza cada orden con las corridas de TWAP ya hechas en ABIDES y escribe `data/analysis/validacion_meta_ordenes_2.3.3.json`. |
| `tests/test_generar_meta_ordenes.py`, `tests/test_validar_meta_ordenes.py` | Esquema, reparto 4/3/3, que el archivo oficial coincide con el que genera el script, campos nuevos, sha256 de la calibración y trazabilidad de la validación. |

Las 10 órdenes se **reservan para evaluar** (T4 y siguientes). El entrenamiento (2.3.5) no las usa.

## 2. Decisión D1: tamaño de las órdenes

**Decisión de BF:** cada orden es un porcentaje del volumen del día simulado de su activo: **10 % para las siete órdenes de apertura y media jornada, y 5 % para las tres de cierre de FALABELLA**. El reparto (FALABELLA 4, COPEC 3, ECL 3; apertura 4, media jornada 3, cierre 3) y las semillas (9000 + 10·i) no cambian.

**Por qué.** El criterio del plan para la 2.3.3 se fijó antes de ver datos: una orden es ejecutable si TWAP completa al menos el 95 % en el simulador congelado. Con ese criterio, las corridas de la 2.3.4 en ABIDES (20 de octubre de 2026, 2 semillas por orden) dieron:

| Tamaño | Órdenes ejecutables (media de TWAP ≥ 95 %) | Corridas ≥ 95 % | Qué falla |
|---|---:|---:|---|
| 100 000 acciones (opción A del plan, v1) | **5 de 10** | 11 de 20 | MO-02 (92,5 %), MO-06 (94,0 %), MO-07 (94,1 %), MO-09 (89,6 %), MO-10 (84,5 %) |
| 10 % del día simulado | **8 de 10** | 17 de 20 | Solo FALABELLA al cierre: MO-09 (93,2 %) y MO-10 (87,4 %) |
| 5 % del día, solo las 3 de cierre | **3 de 3** | 5 de 6 | MO-10 en el borde (90,2 % y 100 %) |

Con 100 000 acciones las órdenes de COPEC y ECL son el 31–49 % del volumen que queda en el simulador y la mitad no se completa. Con 10 % solo fallan las de cierre, porque en el cierre queda poco volumen: 88 300 acciones son el 31 % de lo que queda. Con 5 % para esas tres, **las 10 órdenes son ejecutables** (sección 4). Las cifras salen de `scripts/validar_meta_ordenes.py` (`resumen_por_fuente`) y las fija un test.

**Desviación respecto del plan.** El plan fijaba D1 para el 13 de octubre, con la opción A (100 000 acciones) por defecto y la B (porcentaje del volumen) como sensibilidad del Sprint 7. La decisión final se toma el 22 de octubre y **los tamaños (10 % y 5 %) se eligieron después de ver las corridas de validación**. Lo que sí se fijó antes de ver datos es el criterio de aceptación (≥ 95 % con TWAP). Se declara como desviación (regla R6). La v1 de 100 000 queda disponible para la sensibilidad por tamaño (3.2.4).

## 3. Las 10 órdenes oficiales (`meta_ordenes_v2.json`)

| Id | Activo | Tramo | Hora | Acciones | % del día simulado | % de lo que queda hasta el cierre | % del ADV real | Semilla |
|---|---|---|---|---:|---:|---:|---:|---:|
| MO-01 | FALABELLA | apertura | 09:30 | 88 300 | 10,0 % | 10,0 % | 6,32 % | 9010 |
| MO-02 | COPEC | apertura | 09:30 | 29 100 | 10,0 % | 10,0 % | 4,17 % | 9020 |
| MO-03 | COPEC | apertura | 09:30 | 29 100 | 10,0 % | 10,0 % | 4,17 % | 9030 |
| MO-04 | ECL | apertura | 09:30 | 32 100 | 10,0 % | 10,0 % | 6,95 % | 9040 |
| MO-05 | COPEC | media jornada | 11:00 | 29 100 | 10,0 % | 14,3 % | 4,17 % | 9050 |
| MO-06 | ECL | media jornada | 11:00 | 32 100 | 10,0 % | 14,2 % | 6,95 % | 9060 |
| MO-07 | ECL | media jornada | 11:00 | 32 100 | 10,0 % | 14,2 % | 6,95 % | 9070 |
| MO-08 | FALABELLA | cierre | 14:00 | 44 100 | 5,0 % | 15,4 % | 3,16 % | 9080 |
| MO-09 | FALABELLA | cierre | 14:00 | 44 100 | 5,0 % | 15,4 % | 3,16 % | 9090 |
| MO-10 | FALABELLA | cierre | 14:00 | 44 100 | 5,0 % | 15,4 % | 3,16 % | 9100 |

Datos por activo:

| Activo | Volumen del día simulado | ADV real sin subasta (60 días) | Simulado / real | `p_referencia` (r_bar, CLP) | `p_referencia_real` (CLP) | Diferencia |
|---|---:|---:|---:|---:|---:|---:|
| FALABELLA | 882 768 | 1 396 100 | 63 % | 5 969,8 | 5 976,4 | +0,11 % |
| COPEC | 290 721 | 697 623 | 42 % | 6 130,0 | 6 140,0 | +0,16 % |
| ECL | 321 093 | 461 911 | 70 % | 1 800,0 | 1 825,0 | +1,39 % |

- **Volumen del día simulado:** mediana de 30 jornadas de la validación 2.2.5 con la calibración vigente (`data/colab_resultados/validacion_2_2_5_despues_*.json`). "Lo que queda hasta el cierre" suma los tramos desde el de inicio hasta el cierre. Es una aproximación: los tramos de la calibración cortan a las 11:30 y la orden de media jornada arranca a las 11:00 (D5).
- **ADV real:** mediana, sobre los 60 días del snapshot 2026-08-23, del volumen diario sin la vela de subasta de las 15:55. Se calcula con `load_daily_volume` y `meta_orders_for_ticker` de `src/experiments/meta_orders.py` (no se duplica). El parquet `data/processed/clean_5m_2026-08-23/<ACTIVO>.parquet` no se versiona. Sin él, el generador deja estos campos en null y avisa qué archivo falta.
- Las órdenes son el **3–7 % del ADV real**. El volumen del día simulado está entre 30 y 58 % bajo el real, así que las mismas órdenes pesan más en el simulador que en el mercado real.
- **Semillas:** `semilla = 9000 + 10·índice`. El runner suma la semilla de cada corrida (1, 2, …). Son distintas de las de calibración (100–300), entrenamiento (1000 en adelante) y evaluación de β (5000).
- **Cabecera de trazabilidad** (`generacion`): comando que reproduce el archivo, commit del generador (`0b481f2`) y sha256 de cada archivo de calibración usado (contenido normalizado a fin de línea LF, el mismo que guarda git, para que coincida en Windows y en Linux), más el id del blob de git, que se verifica con `git rev-parse <commit>:<ruta>`:

| Calibración | sha256 (LF) | Blob de git | Último commit que la tocó |
|---|---|---|---|
| `rmsc04_ipsa_FALABELLA_2026-08-23.json` | `56758a5e…a60d0e54` | `c0b2143` | `a7d3d68`, 9 oct 2026 |
| `rmsc04_ipsa_COPEC_2026-08-23.json` | `6d90272b…7898dca7` | `e4bda29` | `6492cdc`, 19 oct 2026 00:19 |
| `rmsc04_ipsa_ECL_2026-08-23.json` | `d1360dfe…a9a72b66` | `4a7df4d` | `6492cdc`, 19 oct 2026 00:19 |

Ningún commit tocó `data/calibration/rmsc04_*` después del congelamiento (19 de octubre, 18:00): `git log --since=2026-10-19T18:00-03:00 -- 'data/calibration/rmsc04_*'` no devuelve nada.

## 4. Validación de ejecutabilidad (paso 5 del plan)

No se corrió nada nuevo. Para cada orden oficial se buscó, en las corridas versionadas de la 2.3.4 (`benchmarks_meta_ordenes_abides_pct10.json` y `..._pct05_cierre.json`), la corrida de TWAP con el mismo id, activo, tramo y cantidad. **Las 10 calzan exactamente**: ninguna queda sin validar.

| Id | Activo | Tramo | Acciones | Fuente | Semillas efectivas | Cumplimiento TWAP por semilla | Media | ¿Ejecutable? |
|---|---|---|---:|---|---|---|---:|:---:|
| MO-01 | FALABELLA | apertura | 88 300 | pct10 | 9011 · 9012 | 100,0 % · 100,0 % | 100,0 % | sí |
| MO-02 | COPEC | apertura | 29 100 | pct10 | 9021 · 9022 | 100,0 % · 100,0 % | 100,0 % | sí |
| MO-03 | COPEC | apertura | 29 100 | pct10 | 9031 · 9032 | 100,0 % · 100,0 % | 100,0 % | sí |
| MO-04 | ECL | apertura | 32 100 | pct10 | 9041 · 9042 | 100,0 % · 100,0 % | 100,0 % | sí |
| MO-05 | COPEC | media jornada | 29 100 | pct10 | 9051 · 9052 | 100,0 % · 100,0 % | 100,0 % | sí |
| MO-06 | ECL | media jornada | 32 100 | pct10 | 9061 · 9062 | 100,0 % · 100,0 % | 100,0 % | sí |
| MO-07 | ECL | media jornada | 32 100 | pct10 | 9071 · 9072 | 100,0 % · 100,0 % | 100,0 % | sí |
| MO-08 | FALABELLA | cierre | 44 100 | pct05_cierre | 9081 · 9082 | 100,0 % · 100,0 % | 100,0 % | sí |
| MO-09 | FALABELLA | cierre | 44 100 | pct05_cierre | 9091 · 9092 | 100,0 % · 100,0 % | 100,0 % | sí |
| MO-10 | FALABELLA | cierre | 44 100 | pct05_cierre | 9101 · 9102 | **90,2 %** · 100,0 % | **95,1 %** | sí, en el borde |

- **10 de 10 órdenes ejecutables en promedio; 19 de 20 corridas sobre el 95 %.**
- Varias corridas marcan 99,98–99,99 % (redondeadas a 100,0 % en la tabla): les faltan 3–6 acciones por el redondeo del calendario de TWAP, no por falta de liquidez.
- La tabla completa, con la tasa exacta de cada corrida, está en `data/analysis/validacion_meta_ordenes_2.3.3.json`.

## 5. Desviaciones

1. **D1 tomada con datos de validación** (sección 2): tamaños elegidos después de ver las corridas, con el criterio de aceptación fijado de antemano. Tomada el 22 de octubre, con plazo original el 13.
2. **`p_referencia`.** El plan pedía un "precio de referencia". Se mantiene el `r_bar` de la calibración de cada activo, que es lo que tenía el archivo cuando corrió la 2.3.4, y se agrega `p_referencia_real` (mediana de `close_raw` no imputado del snapshot) solo como dato informativo. La diferencia es de +0,11 % (FALABELLA), +0,16 % (COPEC) y +1,39 % (ECL). El IS y el slippage de la 2.3.4 **no usan este campo**: el runner toma como precio de llegada el del primer periodo de cada jornada simulada (`src/analysis/benchmarks.py`, `run_benchmark_episode`).
3. **Validación con 2 semillas por orden, hecha con el runner de la 2.3.4.** El paso 5 del plan pedía correr cada orden con TWAP. Se reutilizaron las corridas de los benchmarks: 2 semillas por orden en vez de 1, con la jornada completa desde el tramo de inicio, en 13 periodos independientes.
4. **Semilla de la orden deducida del id.** Las corridas guardan solo la semilla de la corrida (1, 2), no la de la orden. Como el reparto y la fórmula de semillas no cambiaron entre v1 y v2 (lo comprueba un test), la semilla efectiva es `9000 + 10·i + semilla de la corrida`.
5. **Fechas.** El plan pedía las 10 órdenes el 15 de octubre y la validación el 19, día del congelamiento. Las corridas de validación son del 20 de octubre, sobre la calibración ya congelada (sección 3), y la versión oficial se cierra el 22.
6. **Argumento del generador.** La fracción para el cierre se pide con `--pct-dia-cierre` (implementación de PS, commit `59f4924`), no con el `--pct-cierre` de la especificación de BF. Se adoptó para no duplicar la opción.
7. **Media jornada a las 11:00** (corte del Maestro), no a las 11:30 de la calibración, por coherencia con el orquestador y los benchmarks (D5/P9).

## 6. Límites

- **MO-10 queda en el borde:** 90,2 % y 100 % en sus dos semillas (media 95,1 %). Con 2 semillas la media es aproximada y una de las dos queda bajo el umbral. Si una evaluación posterior con más semillas la deja bajo el 95 %, se informa con su porcentaje; no se cambia en silencio.
- El volumen simulado es el de la calibración: el volumen del día está entre 30 y 58 % bajo el ADV real, y el volumen por vela simulado está 15–45 % bajo el real en COPEC y ECL (`docs/calibracion_rmsc04_COPEC_ECL_P4_PS.md`).
- Una sola fecha de referencia y un solo régimen (previo a la transición del IPSA a MSCI).
- La validación usa solo TWAP, con 13 periodos independientes: lo que no se ejecuta en un periodo no pasa al siguiente.

## 7. Cómo reproducir o cambiar

```bash
python scripts/generar_meta_ordenes.py                                   # versión oficial -> data/meta_ordenes/meta_ordenes_v2.json
python scripts/validar_meta_ordenes.py                                   # tabla de la sección 4 -> data/analysis/validacion_meta_ordenes_2.3.3.json
python scripts/generar_meta_ordenes.py --cantidad 100000 --salida <ruta> # tamaños de la v1 (sensibilidad)
python -m pytest tests/test_generar_meta_ordenes.py tests/test_validar_meta_ordenes.py -q
```

Una variante distinta de la oficial exige `--salida`, para no sobrescribir la v2. Para usar la versión oficial en los benchmarks, el runner de la 2.3.4 se corre con `--meta-ordenes data/meta_ordenes/meta_ordenes_v2.json` **y en otra `--out-dir`**: el archivo de salida tiene siempre el mismo nombre y, si la firma cambia, el runner empieza de cero y sobrescribe los resultados anteriores.

## 8. Actualización del 2 de noviembre de 2026

### D1 = v2, ratificada

- BF decidió D1 = v2 el 22 de octubre (secciones 2 y 3), pero la rama de ese cierre (`feature/bf-sprint5-cierre`) no llegó a `main`. Por eso los documentos del Sprint 6 registran la v2 como «por defecto» (`docs/sprint6_que_se_hizo.md`, sección 4).
- BF la **ratifica el 2 de noviembre** en `docs/hoja_decisiones_D1_D3_BF.md`. No cambia ningún tamaño ni ninguna semilla.
- **La v1 queda como histórico.** Es lo que leyó la corrida base de la 2.3.4; no se usa para evaluar el sistema.

### La candidata de PS es equivalente a la v2

Verificación del 2 de noviembre (sobre `origin/main` = `87daa21`):

| Qué se comparó | Resultado |
|---|---|
| Número de órdenes | 10 en la v2 y 10 en la candidata |
| `id`, `ticker`, `tramo_inicio`, `cantidad`, `semilla` | **Idénticos** en las 10 órdenes, en el mismo orden |
| Resto de campos comunes (`volumen_dia_simulado`, `pct_volumen_dia`, `hora_inicio`, `p_referencia`, …) | Idénticos |
| Campos que solo están en la v2 | `adv_real_acciones`, `p_referencia_real`, `pct_adv_real` (informativos, sección 3) |

- **Qué leen los evaluadores.** `scripts/colab/evaluar_sistema_ps.py` y `scripts/colab/benchmarks_meta_ordenes_ps.py` (en `main` y en `feature/ps-3-2-3-control-reglas-v2`) solo leen de cada orden `id`, `ticker`, `tramo_inicio`, `cantidad`, `semilla` y `volumen_dia_simulado`. Los seis coinciden.
- **La firma no depende del archivo.** La firma de reanudación se arma con los `id` y las `cantidades`, no con la ruta del archivo. Correr con la v2 o con la candidata da la misma firma y las mismas corridas.
- **Consecuencia:** la 3.1.3 (`docs/corridas_30_corregidas_resultado_PS.md`) y las 90 corridas, que usaron la candidata, **son válidas con D1 = v2 sin repetir nada**. Los cuadernos de PS pueden seguir apuntando a la candidata.

### Calibración

El sha256 (LF) y el blob de git de los tres `rmsc04_ipsa_*_2026-08-23.json` anotados en la cabecera de la v2 **siguen coincidiendo** con los archivos de `main`. El último commit que tocó `data/calibration/rmsc04_*` sigue siendo `6492cdc` (19 de octubre).

### Benchmarks con la v2

`docs/benchmarks_2.3.4_v2_PS.md` (PS, 23 de octubre) ensambla los benchmarks de la 2.3.4 con los tamaños de la v2:
- **10 de 10 órdenes ejecutables** en promedio y 19 de 20 corridas sobre el 95 %, la misma tabla de la sección 4.
- MO-10 sigue en el borde (90,2 % y 100 %; TWAP 0,951).

En la 3.1.3, con `--completar-al-cierre`, el sistema completa MO-10 con un cumplimiento mínimo de 1,00, y las otras dos órdenes de cierre con 0,97 y 0,98 (`docs/corridas_30_corregidas_resultado_PS.md`). El límite de la sección 6 se mantiene para TWAP.

---

Borrador de PS con apoyo de Claude Code; revisado, completado y aprobado por BF con apoyo de Claude Code.
