# Plan de acción de PS, Sprint 5 (10 – 23 oct 2026)

Elaborado por PS con apoyo de Claude Code. Cubre solo las tareas de PS del documento `Plan_Sprint5_12-23oct2026.docx`: T4, P1, P2 (implementación), P4, P5, P3 (validación), apoyo en T1, P8 y documento de cierre.

Quién hace cada paso: **[C]** Claude Code (código, análisis, documentos) · **[PS]** Paolo (Colab, descargas, avisos al grupo).

## Fase 0: antes de la reunión (sáb 10 – lun 12 oct), sin depender de nadie

| Paso | Qué | Quién | Entrega |
|---|---|---|---|
| 0.1 | P1: normalizador de R_E (media y varianza móviles, rango [-1, 1], apagado por defecto) y script de distribución de R_E con los episodios que ya tenemos | C | `src/envs/reward_utils.py`, `scripts/analizar_distribucion_re.py`, tests |
| 0.2 | P2: dejar lista en el código la opción de riesgo sobre el inventario pendiente (parámetro `riesgo_sobre = "ejecutado" / "pendiente"`, por defecto igual que hoy) para que cuando BF decida solo se cambie el valor | C | `reward_utils.py`, entornos, tests |
| 0.3 | P2: nota de una página para BF con las 3 opciones (A, B, C) y los números de la fase 2 | C | `docs/decision_RE_para_BF.md` |
| 0.4 | P4: bajar el archivo `_combined.parquet` del snapshot 2026-08-23 desde la carpeta de BF en Drive (`TÍTULO 2 / Sprint 3 / clean_5m_2026-08-23`) y dejarlo en `data/processed/clean_5m_2026-08-23/` | PS | archivo local (5 MB) |
| 0.5 | P4: con ese archivo, generar los datos reales base de COPEC y ECL (objetivos y retornos reales; los objetivos ya están en `poisson_params_2026-08-23.json`) | C | `rmsc04_base_COPEC_...json`, `rmsc04_base_ECL_...json` |
| 0.6 | T4: adaptar el runner de benchmarks para leer `meta_ordenes_v1.json` (con el esquema del plan) y probarlo con órdenes de ejemplo | C | `scripts/colab/benchmarks_meta_ordenes_ps.py`, tests |
| 0.7 | Subir todo lo anterior a una rama nueva y avisar | C y PS | PR `feature/ps-sprint5-fase0` |

## Fase 1: semana 1 (mar 13 – vie 16 oct)

| Día | Qué | Quién |
|---|---|---|
| Mar 13 | Reunión de arranque: confirmar asignaciones, tomar D1, D2 y D5. Mandar el mensaje al grupo con el plan | PS |
| Mar 13 | P4: calibración de COPEC y ECL en Colab (sondeo, grilla y refinamiento con `rmsc04_grid_search.py`). Unas 1–2 h de corrida por activo; los pasos de Colab los doy uno a uno | PS (celdas) y C (instrucciones, revisión de resultados) |
| Mié 14 | P8: revisar el PR de cierre del Sprint 4 (la parte de PS ya está) y aprobar los de BF/MR cuando los suban. Esperar la decisión D3 de BF a las 18:00 | PS |
| Mié 14 | P2: con la decisión, fijar el valor de `riesgo_sobre`, actualizar tests y la nota en `DESVIACIONES_TITULO1_VS_IMPLEMENTACION.md` | C |
| Jue 15 | P4: validación con 30 semillas de COPEC y ECL (`validacion_2_2_5_ps.py`, unas 1,5 h por activo) y tabla de resultados | PS (celdas) y C (análisis) |
| Jue 15 | Apoyo en T1: escribir los esquemas JSON de ASIGNAR y REPORTE, la validación y los tests (3 h), cuando MR cierre el diseño del protocolo | C |
| Vie 16 | P1 y P2 entregados (PR). Revisión de la versión de calibración de BF (P3): correr la validación formal de 30 semillas sobre su candidata | PS (celdas) y C |
| Vie 16 | P4 entregado (PR con los JSON de calibración). Aviso a BF para que valide T3 con COPEC y ECL | C y PS |

## Fase 2: semana 2 (lun 19 – vie 23 oct)

| Día | Qué | Quién |
|---|---|---|
| Lun 19 | 18:00 congelamiento del simulador. Verificar que los JSON de calibración quedaron fijos y avisar | PS |
| Mar 20 | T4: correr los benchmarks sobre las 10 meta-órdenes (40 jornadas completas en ABIDES, ≈ 8 min cada una; 5–6 h repartidas en 2 cuadernos) | PS (celdas) |
| Mar 20 | P5: iniciar β en media jornada (100 episodios, 15 semillas de evaluación, ≈ 3 h) en un segundo cuaderno | PS (celdas) |
| Mié 21 | P5: β en cierre (≈ 4–5 h). T4: análisis, tabla de IS por orden y estrategia, gráficos | PS y C |
| Jue 22 | T4 entregada (documento y PR). P5 entregada: tabla de β por tramo con la regla previa y `BETA_RIESGO_EJECUTOR` actualizado | C |
| Vie 23 | Documento de cierre `docs/sprint5_que_se_hizo.md`, PR final y reunión de cierre | C y PS |

## Tiempo tuyo en Colab (estimado)

| Corrida | Cuándo | Tiempo de máquina | Tu tiempo activo |
|---|---|---|---|
| P4 calibración COPEC y ECL | 13–15 oct | 4–6 h | ≈ 30 min (celdas) |
| P4 validación 30 semillas | 15 oct | ≈ 3 h | ≈ 15 min |
| P3 validación de la candidata de BF | 16–19 oct | ≈ 1,5 h | ≈ 15 min |
| T4 benchmarks | 20–21 oct | 5–6 h en 2 cuadernos | ≈ 20 min |
| P5 β media jornada y cierre | 20–22 oct | ≈ 8 h en 2 cuadernos | ≈ 30 min |

Regla: máximo dos cuadernos al mismo tiempo, cada comando con `--max-minutes`, y los resultados se miran en `resultados/` de Drive.

## Qué puede salir mal y qué se hace

- **No hay parquet del 08-23:** usar el del 2026-09-23 (está local), declarar la diferencia de fecha respecto de FALABELLA y avisar a BF.
- **COPEC o ECL no calibran bien el viernes 16:** plan B del documento del sprint (solo FALABELLA con otros tramos y semillas) y se declara como desviación.
- **BF no decide D3 el 14:** rige la opción B (β = 0) y se sigue.
- **MR avisa atraso en T2 el 15:** PS toma checkpoints y CSV (5 h), que se suman a esta lista.
- **Colab se corta:** volver a ejecutar la misma celda; el avance queda en Drive.
