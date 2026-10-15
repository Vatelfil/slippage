# Acta de cierre de los Sprints 1 a 4

**Borrador** elaborado por PS con apoyo de Claude Code el 15 de octubre de 2026, a partir del repositorio (rama `main`), los documentos de avance y el Excel `plan-desarrollo-titulo-2.xlsx`. Cada fila debe ser confirmada por quien corresponde (columna "Confirma"). Lo que no se objete antes del **viernes 17 de octubre** queda como está escrito.

## Estados

| Estado | Significa |
|---|---|
| **Hecho** | Cumple los entregables y el criterio del plan |
| **Hecho con límite** | Se ejecutó y se midió; el resultado no alcanza el criterio del plan o hay una desviación; el límite está escrito y tiene fecha de revisión |
| **Por cerrar** | Falta un entregable menor (archivo o documento); ya hay borrador en `main` o en el PR de cierre |

## Sprint 1 (17 al 28 de agosto)

| Tarea | Estado | Qué queda abierto / evidencia | Confirma |
|---|---|---|---|
| 1.1.1 Planificación y backlog | Hecho | Plan en `plan-desarrollo-titulo-2.xlsx` | Equipo |
| 1.1.2 Entorno y repositorio | **Por cerrar** | Falta `CONTRIBUTING.md` (borrador en este PR) | MR |
| 1.1.3 Descarga de datos OHLCV | Hecho | `data/raw/` con manifiestos y reportes de calidad | BF |
| 1.1.4 Vectores S_M y S_E | Hecho | `docs/schemas/SM_schema.json` y `SE_schema.json` | PS |
| 1.1.5 Sprint Review | Hecho | Según `AVANCES_SPRINTS_1_2.md` | Equipo |

## Sprint 2 (31 de agosto al 11 de septiembre)

| Tarea | Estado | Qué queda abierto / evidencia | Confirma |
|---|---|---|---|
| 1.2.1 Limpieza de datos | Hecho | `data/processed/clean_5m_*` y `docs/evidencia_pipeline_datos_BF.md` | BF |
| 1.2.2 Features de S_M | Hecho | `src/features/build_sm_features.py` y `tests/test_pipeline_sm.py` | BF |
| 1.2.3 PoC de ABIDES-Gym | **Por cerrar** | Falta el notebook del plan; evidencia equivalente en `docs/poc_abides_gym_1.2.3.md` | MR |
| 1.2.4 Dependencias | **Por cerrar** | Faltaban `requirements-locked.txt` y `docs/dependencias_resueltas.md`; quedaron escritos en este PR con el `pip freeze` completo del 15 oct (56 paquetes) | MR |
| 1.2.5 Arquitectura del entorno | Hecho | `docs/arquitectura_entorno_simulacion.md` | PS |

## Sprint 3

| Tarea | Estado | Qué queda abierto / evidencia | Confirma |
|---|---|---|---|
| 2.1.1 Red del Maestro | **Hecho con límite** | No sigue la especificación del Excel (256 neuronas, sin Xavier ni Dropout, una cabeza de 40 salidas). Desviación en `docs/desviaciones_2.1.1.md`; pruebas en `tests/test_actor_critic.py`. El equipo decide si se acepta o se alinea | MR |
| 2.1.2 Redes de los Ejecutores | **Hecho con límite** | Fábrica en `src/models/networks_factory.py` (PS) y desviación en `docs/desviaciones_2.1.2.md`: totalmente discreta en vez de híbrida, 27 entradas en vez de 26. Falta la ratificación de su responsable | BF |
| 2.1.3 Calibración de Poisson | Hecho | `data/calibration/poisson_params_2026-08-23.json` y `docs/calibracion_poisson_2.1.3_BF.md` | PS |
| 2.1.4 Espacios de Gymnasium | Hecho | `src/envs/spaces.py` | PS |

## Sprint 4

| Tarea | Estado | Qué queda abierto / evidencia | Confirma |
|---|---|---|---|
| 2.2.1 PPO (L_CLIP y GAE) | Hecho | PR #20 y `experiments/test_ppo_short_run.py` | MR |
| 2.2.2 Recompensa del Maestro | **Hecho con límite** | λ = 0,05 calibrado por escala con una política sin entrenar; se revalida con el Maestro entrenado (Sprint 6) | MR |
| 2.2.3 Recompensa de los Ejecutores | **Hecho con límite** | β = 0,0062 calibrado solo en la apertura; media jornada y cierre en el Sprint 5. R_E según el Título I con regla de vigilancia (`docs/decision_RE_para_BF.md`), revisión el 23 de octubre | BF |
| 2.2.4 Calibración de `rmsc04` | **Hecho con límite** | El KS rechaza (el plan pedía p > 0,05); el volumen simulado es hasta 49 % mayor que el real. Intento de mejora antes del congelamiento del 19 de octubre | BF |
| 2.2.5 Validación del simulador | **Hecho con límite** | Conclusión "no válido" según el criterio literal; escala y patrón coinciden. Informe `docs/validacion_formal_2.2.5_PS.md` | PS |

## Resumen

- **Hecho:** 10 tareas (de 19 en total).
- **Hecho con límite:** 6 tareas (2.1.1, 2.1.2, 2.2.2, 2.2.3, 2.2.4 y 2.2.5).
- **Por cerrar:** 3 entregables menores (1.1.2, 1.2.3 y 1.2.4), con borrador ya escrito.

## Texto sugerido para confirmar la 2.1.2

> Ratifico la fábrica de redes `src/models/networks_factory.py` y su nota `docs/desviaciones_2.1.2.md` como entrega de la 2.1.2: Ejecutores independientes, cabeza totalmente discreta (240 salidas) y 27 entradas.

## Cómo confirmar

Cada responsable responde por el grupo con "confirmo mis filas" o indica el cambio que pide. Las filas "por cerrar" se cierran al mergear el PR con los borradores y confirmarlos.
