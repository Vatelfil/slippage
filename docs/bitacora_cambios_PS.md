# Bitácora de cambios de PS (qué se hizo en el PC, por qué y quién)

**Para qué sirve:** dejar por escrito, para consulta futura, qué contiene cada PR o rama que sale del PC de PS, por qué se hizo y quién lo hizo. **Regla:** cada PR nuevo agrega su entrada aquí (y, si trae gráficos, su explicación en `docs/guia_graficos.md`).

**Cómo se trabaja:**
- El código y los análisis se escriben en el PC de PS (`D:\claude agente\slippage`) con apoyo de Claude Code (uso autorizado por la universidad), en ramas aisladas (`git worktree`) y con pruebas automáticas (`pytest`) antes de subir.
- Las corridas pesadas las ejecuta PS en Google Colab (receta de `docs/dependencias_resueltas.md`); los resultados quedan en Drive (`slippage_colab/resultados/...`) y se copian al repositorio en `data/colab_resultados/`.
- **Autoría:** salvo que se indique otra cosa, "PS" = Paolo Sepúlveda con apoyo de Claude Code. Las partes de MR (Mauricio Reynoso) y BF (Benjamín Farias) las escriben ellos; los borradores que PS preparó para ellos se marcan como **borrador de PS para MR/BF** y quedan pendientes de su revisión.
- GitHub rechaza nuevos commits en ramas ya subidas: una corrección posterior va en una rama nueva con sufijo `-v2`. Por eso hay ramas antiguas que quedan **obsoletas** (ver la sección 3).

## 1. PR integrados a `main` (del 27 de PR en adelante)

### PR #27, `feature/ps-cierre-sprint4`, 10 de octubre: cierre del Sprint 4
- **Quién:** PS. Incluye el arreglo de MR/PS sobre `torch` y la semilla de λ.
- **Qué:** reúne siete ramas: validación formal del simulador con 30 semillas por tramo (2.2.5); fase 2 de la elección de β con PPO en la apertura (β = 0,0061796, provisional); fábrica de redes de los tres Ejecutores (2.1.2); corrección del nivel de precio de las órdenes límite del simulador de Poisson; sondeo de megashocks (2.2.4); `torch` se importa solo al usarlo y la calibración de λ es reproducible (MR/PS); el log de evaluación ya no falla si la política no ejecuta; documento "qué se hizo en el Sprint 4".
- **Por qué:** dejar el Sprint 4 cerrado con evidencia y límites escritos antes del Sprint 5.
- **Archivos clave:** `docs/validacion_formal_2.2.5_PS.md`, `docs/beta_fase2_apertura_PS.md`, `docs/sprint4_que_se_hizo.md`, `src/models/networks_factory.py`.
- **Resultado:** el simulador calibrado no es válido según el criterio literal (el KS rechaza) pero la escala y el patrón entre tramos coinciden; β = 0,0061796.

### PR #28, `feature/ps-sprint5-fase0-v2`, 10 de octubre: fase 0 del Sprint 5
- **Quién:** PS.
- **Qué:** normalizador móvil de R_E (salida dentro de [−1, 1]); opción de cobrar el riesgo sobre el inventario pendiente (`riesgo_sobre="pendiente"`, apagada por defecto); distribución de R_E; nota de decisión D3; corredor de benchmarks sobre meta-órdenes; configuración base de `rmsc04` para COPEC y ECL.
- **Por qué:** dejar listo lo que no dependía de otros antes de que empezara el Sprint 5.
- **Archivos clave:** `src/envs/reward_utils.py`, `docs/distribucion_recompensa_2.2.3_PS.md`, `scripts/colab/benchmarks_meta_ordenes_ps.py`.

### PR #29, `feature/ps-sprint5-riesgo-pendiente-sweeps`, 10 de octubre
- **Quién:** PS.
- **Qué:** el barrido y la fase 2 de β aceptan `--riesgo-sobre pendiente`.
- **Por qué:** poder probar la opción A de D3 sin tocar la opción por defecto.

### PR #30, `feature/ps-sprint5-t4-analisis`, 14 de octubre
- **Quién:** PS.
- **Qué:** propuesta de R_E fiel al Título I (opción 0 con regla de vigilancia), plan del Sprint 5 actualizado, grilla para COPEC y ECL, análisis de los benchmarks sobre meta-órdenes y corredor tolerante al BOM de Windows.
- **Por qué:** la decisión D3 tenía plazo el 14 de octubre; sin respuesta de BF rige la propuesta de PS.
- **Archivos clave:** `docs/decision_RE_para_BF.md`, `scripts/analizar_benchmarks_meta_ordenes.py`.

### PR #35, `feature/ps-p4-copec-calibracion`, 18 de octubre
- **Quién:** PS. **Qué:** primera calibración de `rmsc04` para COPEC (grilla de actividad baja, refinamiento, 10 semillas).
- **Estado:** reemplazada por el PR #36 (la calibración tenía corridas desbocadas).

### PR #36, `feature/ps-cierre-s1-s4-y-calibracion-copec-ecl`, 19 de octubre
- **Quién:** PS.
- **Qué:** calibración de COPEC y ECL sin corridas desbocadas (3 agentes de momentum en vez de 12 y `fund_vol` ajustado por tramo); validación formal con 30 semillas de ambos activos; corrección de `tick_labels` (error de compatibilidad de matplotlib detectado por BF); acta de cierre de los sprints 1 a 4.
- **Por qué:** con 250 agentes de ruido, los 12 de momentum desestabilizaban el mercado (en ECL, 9, 13 y 13 de 30 corridas con movimientos de más de 10 %); había que dejar tres activos calibrados antes del congelamiento del simulador (19 de octubre, 18:00).
- **Archivos clave:** `docs/calibracion_rmsc04_COPEC_ECL_P4_PS.md`, `docs/validacion_formal_2.2.5_COPEC_PS.md`, `docs/validacion_formal_2.2.5_ECL_PS.md`, `docs/acta_cierre_sprints_1_a_4.md`, `data/calibration/rmsc04_ipsa_{COPEC,ECL}_2026-08-23.json`.
- **Resultado:** 0 de 30 corridas desbocadas en los tres tramos; el KS sigue rechazando (límite declarado).

### PR #37, `feature/ps-p5-beta-media-cierre`, 19 de octubre
- **Quién:** PS.
- **Qué:** fase 2 de β en media jornada y cierre (FALABELLA, 100 episodios y 15 semillas de evaluación por valor).
- **Por qué:** la tarea P5 del plan: β solo estaba calibrado en la apertura.
- **Resultado:** solo 0,1 × β∗ cumple el 95 % de la orden en los tres tramos; se propone un β común de 0,1 × β∗ (decisión de BF). TWAP con límite iguala o supera a las redes con este entrenamiento corto.
- **Archivo clave:** `docs/beta_fase2_media_cierre_PS.md`.

### PR #39, `feature/ps-borrador-bf-t5-resultados`, 20 de octubre
- **Quién:** **borrador de PS para BF** (tarea 2.3.5). **Qué:** script de entrenamiento inicial del Ejecutor (100 episodios), script de análisis, informe y figura.
- **Por qué:** BF y MR están en práctica profesional y no tienen tiempo; PS dejó el trabajo listo para su revisión.
- **Estado:** el resultado de 100 episodios quedó superado por la rama `final-v2` (sección 2).

### PR #41, `feature/ps-borrador-mr-t1-t2-evidencia-abides-v2`, 21 de octubre
- **Quién:** **borrador de PS para MR** (tareas 2.3.1 y 2.3.2); el arreglo de unidades lo hizo **MR**.
- **Qué:** enlaces relativos en los documentos de MR, ejemplo del ciclo PPO con el entorno calibrado y evidencia con ABIDES real (2 mensajes CTDE válidos; entrenador de 4 episodios y reanudación sin NaN). PS observó que el REPORTE traía precios en décimos de peso sin convertir; **MR lo resolvió** (conversión a CLP con `unidades_por_clp`).
- **Archivos clave:** `docs/protocolo_ctde_2.3.1.md`, `docs/ciclo_ppo_2.3.2.md`, `scripts/colab/evidencia_ctde_ppo_abides_ps.py`.

## 2. Ramas listas, pendientes de PR o de merge

### `feature/ps-sprint5-final-v2`: T3, T4 y T5 completos (borradores de PS para BF)
- **Quién:** PS con apoyo de Claude Code; corridas de Colab ejecutadas por PS. Pendiente de revisión de BF.
- **Qué:**
  - **T3 (2.3.3), meta-órdenes:** generador reproducible, las 10 órdenes (100.000 acciones; FALABELLA 4, COPEC 3, ECL 3; apertura 4, media jornada 3, cierre 3), perfil de volumen y documento con las decisiones D1, D2 y D5.
  - **T4 (2.3.4), benchmarks:** TWAP y VWAP con 2 semillas sobre las 10 órdenes, con 100.000 acciones, con 10 % del volumen del día y con 5 % solo en el cierre. Informe de ejecutabilidad (criterio: TWAP completa al menos el 95 %).
  - **T5 (2.3.5), entrenamiento inicial:** 100 y 1.000 episodios con la opción 0, 1.000 con la opción A, diagnóstico de la política y repetición de 100 episodios sin cortes.
- **Por qué:** la tarea era de BF, pero BF no tenía tiempo; PS la dejó lista para que solo revise y decida.
- **Archivos clave:** `scripts/generar_meta_ordenes.py`, `data/meta_ordenes/meta_ordenes_v1.json`, `docs/meta_ordenes_2.3.3.md`, `docs/benchmarks_2.3.4_PS.md`, `docs/entrenamiento_inicial_2.3.5.md`, `data/colab_resultados/` (benchmarks y t5_*).
- **Resultados:**
  - Ejecutabilidad con TWAP: 5 de 10 órdenes con 100.000 acciones; 8 de 10 con 10 % del día; 3 de 3 de cierre con 5 %.
  - La red entrenada con la opción 0 aprende a esperar cuando se evalúa con argmax (cumplimiento 0,000); con la opción A, el argmax ejecuta (1,000); ninguna corrida mejora el slippage de la red sin entrenar de forma significativa.
  - Hallazgo de reproducibilidad: reanudar un entrenamiento desde un checkpoint cambia los resultados (el checkpoint no guarda el estado aleatorio).
- **Cómo reproducir:** `python scripts/analizar_benchmarks_meta_ordenes.py --resultados data/colab_resultados/benchmarks_meta_ordenes_abides.json --alternativas "B 10 %=data/colab_resultados/benchmarks_meta_ordenes_abides_pct10.json"`; `python scripts/analizar_entrenamiento_inicial.py --estado data/colab_resultados/t5_1000ep_opcion0.json --csv data/colab_resultados/t5_1000ep_opcion0.csv`.

### `feature/ps-sprint6-adelanto-3-1-4`: Sprint 6 adelantado
- **Quién:** PS con apoyo de Claude Code. **Qué:** `src/training/monitoreo.py` (registro por episodio y alertas, sin modificar el entrenador), `scripts/monitorear_entrenamiento.py` (panel de varias corridas), `scripts/comparar_sistema_vs_benchmarks.py` (comparación pareada con intervalo de confianza, para las tareas 3.2.3 y 3.2.4), opción `--pct-dia-cierre` en el generador de órdenes y `docs/plan_accion_PS_sprint6.md`.
- **Por qué:** 3.1.4 (monitoreo y registro de métricas) es tarea de PS en el Sprint 6; el comparador adelanta el Sprint 7. El monitoreo nació de lo que se vio en T5 (la red aprendió a esperar y solo se notó al evaluar).
- **Se apoya en:** la rama `feature/ps-sprint5-t3-t4-t5-sobre-main`; mergear después de `final-v2`.
- **Cómo verificar:** `python -m pytest tests/test_monitoreo.py tests/test_comparar_sistema_vs_benchmarks.py -q`.

### `feature/ps-informe-titulo2-sprint4-v2`: informe de Título II y presentación
- **Quién:** PS con apoyo de Claude Code; contenido de los tres integrantes (fuentes: acta de cierre, documentos por tarea y registro histórico de MR).
- **Qué:** informe Word (Parte I del Título I sin cambios y Parte II actualizada hasta el cierre del Sprint 4), su generador (`docs/informe_titulo2/generador`) y la presentación grupal (`docs/informe_titulo2/ppt`).
- **Por qué:** entrega y presentación del 22 de octubre; el documento se seguirá actualizando con cada sprint.
- **Profesora guía:** Ana Rosa Moya Beltrán.
- **Cómo regenerar el informe:** `cd docs/informe_titulo2/generador && npm install && node build.js ../Informe_Titulo_II_Avance_AAAA-MM-DD.docx`.

### `feature/ps-sprint6-plan-ejecucion-y-bitacora`: esta rama
- **Quién:** PS con apoyo de Claude Code. **Qué:** `docs/plan_ejecucion_PS_sprint6.md` (qué se puede hacer, qué está bloqueado y qué correr en Colab), esta bitácora y `docs/guia_graficos.md`.
- **Por qué:** pedido de PS el 22 de octubre: dejar trazabilidad de cada PR y los gráficos explicados.

### `feature/ps-sprint6-ejecucion-parte-ps`: ejecución de la parte de PS sin Colab (23 de octubre)
- **Quién:** PS con apoyo de Claude Code. Los borradores para BF y MR están marcados en cada documento; nada de lo que es de ellos se modificó.
- **Qué:**
  - `docs/sprint5_que_se_hizo.md` (A2): cierre del Sprint 5 en el formato del Sprint 4 (tareas T1 a T5 y P1 a P10, con estado, PR y quién confirma).
  - `docs/decision_RE_final_D3_para_BF.md` (A3): memo para BF con la evidencia de D3, tres opciones, recomendación de PS, costo de pasar a la opción A y el formato de respuesta.
  - E1, archivo candidato de D1: `data/meta_ordenes/meta_ordenes_v2_candidata.json` (10 % del día y 5 % en el cierre; `generar_meta_ordenes.py` ahora acepta `--version`), `scripts/ensamblar_benchmarks_meta_ordenes.py` (une tandas de benchmarks con tamaños distintos, validando cantidades y semillas) y el resultado `data/colab_resultados/benchmarks_meta_ordenes_abides_v2.json` con su análisis `docs/benchmarks_2.3.4_v2_PS.md`. **No se corrió nada en Colab:** se ensamblaron las corridas que ya existían.
  - C1/C2, estabilidad de D3: `scripts/colab/d3_estabilidad_ps.py` (5 semillas de red por opción de R_E, 100 episodios cada una, reanudable) y `scripts/analizar_estabilidad_D3.py` (tabla, Fisher, Wilcoxon contra la red sin entrenar y figura). Probados con Poisson; **falta correrlo en Colab (C-2).**
  - D1/D2, evaluador del sistema: `scripts/colab/evaluar_sistema_ps.py` corre Maestro + 3 Ejecutores sobre las 10 meta-órdenes y deja el resultado en el formato de los benchmarks (`estrategia = "PPO"` o `"PPO_sin_entrenar"`), con las mismas semillas de mercado que TWAP/VWAP para que el pareo sea válido. Probado con Poisson; **falta correrlo con ABIDES (C-3).**
  - B2: `scripts/monitorear_entrenamiento.py` ahora acepta `--dir` (descubre una corrida por subcarpeta) y `--out-json` (resumen por corrida con métricas y alertas).
  - G1: esqueleto de `docs/sprint6_que_se_hizo.md`.
- **Por qué:** orden de PS del 23 de octubre ("adelanta mi parte") a partir de `docs/plan_ejecucion_PS_sprint6.md`: dejar listo todo lo que no depende de Colab ni de decisiones de BF y MR, y que las corridas de Colab queden en celdas simples.
- **Archivos clave:** los listados arriba y las pruebas `tests/test_ensamblar_benchmarks.py`, `tests/test_evaluar_sistema.py`, `tests/test_estabilidad_d3.py` y `tests/test_monitoreo.py`.
- **Resultado:** con 10 % del día (apertura y media jornada) y 5 % en el cierre, las 10 órdenes son ejecutables (19 de 20 corridas llegan al 95 %; MO-10 con 90,2 % en una semilla y 100 % en la otra). TWAP − VWAP = −6,59 bps, sin diferencia significativa (Wilcoxon p = 0,297).
- **Cómo reproducir o verificar:** `PYTHONPATH=. python -m pytest tests -q`; el archivo v2 se regenera con `scripts/ensamblar_benchmarks_meta_ordenes.py` (ver su docstring) y su análisis con `scripts/analizar_benchmarks_meta_ordenes.py --resultados data/colab_resultados/benchmarks_meta_ordenes_abides_v2.json --out-json data/analysis/benchmarks_meta_ordenes_v2.json --out-png data/analysis/benchmarks_meta_ordenes_v2.png --out-md docs/benchmarks_2.3.4_v2_PS.md`.
- **Gráficos:** `data/analysis/benchmarks_meta_ordenes_v2.png` y, cuando se corra C-2, `data/analysis/estabilidad_D3.png` (entradas en `docs/guia_graficos.md`).

### `feature/ps-sprint6-d3-estabilidad-resultados`: resultados de la estabilidad de D3 (C-2) y control muestreado (23 de octubre)
- **Quién:** PS con apoyo de Claude Code. La decisión de D3 es de BF; el memo le deja la evidencia.
- **Qué:**
  - `data/colab_resultados/d3_estabilidad/`: las 10 corridas de Colab (5 semillas de red × opción 0 y A, 100 episodios; JSON y CSV, sin checkpoints).
  - `docs/estabilidad_D3_PS.md` y `data/analysis/estabilidad_D3.{json,png}`: tabla, Fisher, Wilcoxon y figura (informe generado por `scripts/analizar_estabilidad_D3.py`).
  - `docs/monitoreo_d3_estabilidad.md` y `data/analysis/monitoreo_d3_estabilidad.{json,png}`: panel de monitoreo con las 10 corridas (valida el monitoreo con ABIDES real).
  - `docs/decision_RE_final_D3_para_BF.md`: nueva sección 7 con la evidencia y la recomendación revisada ("D3: esperar", con 1.000 episodios × 3 semillas por opción).
  - `scripts/colab/control_muestreado_ps.py` (nuevo) y su integración en el analizador: evalúa la red sin entrenar muestreando la política, para comparar entrenada y control en igualdad de condiciones.
  - `scripts/colab/entrenamiento_inicial_ps.py`: el mensaje de vigilancia ya no dice "se mantiene la opción 0" en corridas con la opción A (solo cambia el texto).
- **Por qué:** continuar el plan de PS (C1 y C2) con los resultados que trajo PS desde Colab, y dar a BF evidencia para decidir D3.
- **Archivos clave:** los listados arriba y `tests/test_estabilidad_d3.py`.
- **Resultado:** la regla (cumplimiento con argmax < 95 %) se dispara en 2 de 5 redes con la opción 0 y en 1 de 5 con la A (Fisher p = 1,0); con muestreo las 10 cumplen. Las 10 redes siguen con entropía de 99,6 % a 99,9 % del máximo: con 100 episodios el argmax mide el azar de una política casi uniforme (la red sin entrenar de la semilla 2000 ya cumple 0,000). La opción 0 con la semilla 1000 reproduce 0,904 de la repetición del Sprint 5.
- **Cómo reproducir o verificar:** `python scripts/analizar_estabilidad_D3.py --dir data/colab_resultados/d3_estabilidad` y `python scripts/monitorear_entrenamiento.py --dir data/colab_resultados/d3_estabilidad --out-json data/analysis/monitoreo_d3_estabilidad.json --out-png data/analysis/monitoreo_d3_estabilidad.png --out-md docs/monitoreo_d3_estabilidad.md`.
- **Gráficos:** entradas en `docs/guia_graficos.md` (`estabilidad_D3.png` y `monitoreo_d3_estabilidad.png`).
### `feature/ps-figuras-cientificas`: cuatro figuras científicas del proyecto (23 de octubre)
- **Quién:** PS con apoyo de Claude Code. Resumen de lo que hacen MR y BF; ellos revisan los valores de su parte.
- **Qué:** `docs/figuras_cientificas/`: cuatro figuras (PNG de 4000 × 2640 px y PDF vectorial), su generador (`generador/lib.py`, `fig1.py` a `fig4.py`) y un `README.md` que explica cómo leerlas y de dónde sale cada cifra.
- **Por qué:** PS necesitaba material de formato artículo para presentaciones e informes que explique el proyecto completo (datos reales, calibración, simulación, agentes, variables y evaluación) y que sirva a quien no conoce el proyecto.
- **Archivos clave:** `docs/figuras_cientificas/README.md`, `fig1_arquitectura`, `fig2_formulacion`, `fig3_espacios`, `fig4_diseno_experimental`.
- **Resultado:** la figura 4 usa datos reales del repositorio (benchmarks v2: 10 de 10 órdenes ejecutables; TWAP − VWAP = −6,59 bps, p = 0,297). Las demás resumen la formulación del proyecto, con λ y β marcados como provisionales.
- **Cómo reproducir o verificar:** `cd docs/figuras_cientificas/generador && python fig1.py && python fig2.py && python fig3.py && python fig4.py`.
- **Gráficos:** explicados en `docs/figuras_cientificas/README.md` y en la sección 8 de `docs/guia_graficos.md`.

### `feature/ps-sprint6-c3-sistema-sin-entrenar`: primera evaluación del sistema completo (25 de octubre)
- **Quién:** PS con apoyo de Claude Code.
- **Qué:** `data/colab_resultados/c3_sistema/` (resultados de las dos mitades de Colab y la prueba corta), `docs/c3_sistema_sin_entrenar_PS.md` (qué se validó, el error encontrado y qué sigue), `docs/sistema_sin_entrenar_vs_benchmarks_PS.md` y `data/analysis/sistema_sin_entrenar_vs_benchmarks.{json,png}` (comparación con TWAP y VWAP), y la corrección de `scripts/colab/evaluar_sistema_ps.py` (`--seed-red`) con sus pruebas.
- **Por qué:** tarea C-3 / D2 del plan de PS: validar con ABIDES el flujo completo Maestro–Ejecutores y obtener un primer punto de comparación.
- **Resultado:** el flujo funciona (20 de 20 corridas) y el pareo con los benchmarks es válido (mismo precio de referencia en 20 de 20). Se encontró que las redes sin entrenar se creaban sin semilla (dos sesiones daban resultados distintos), ya corregido. El «ahorro» de 43 bps frente a TWAP no es real: el sistema sin entrenar solo ejecuta el 88,5 % de la orden.
- **Cómo reproducir o verificar:** `PYTHONPATH=. python scripts/comparar_sistema_vs_benchmarks.py --comparacion "v2=data/colab_resultados/benchmarks_meta_ordenes_abides_v2.json,data/colab_resultados/c3_sistema/sistema_PPO_sin_entrenar_argmax_10ordenes_dos_redes.json" --nombre-sistema PPO_sin_entrenar`.
- **Gráficos:** entrada en `docs/guia_graficos.md` (`sistema_sin_entrenar_vs_benchmarks.png`).

### `feature/ps-sprint6-d3-1000ep-resultados`: D3 con 1.000 episodios (25 de octubre)
- **Quién:** PS con apoyo de Claude Code. La decisión de D3 es de BF.
- **Qué:** `data/colab_resultados/d3_1000ep/` (6 redes de 1.000 episodios: 3 semillas × opción 0 y A; la semilla 1000 viene del Sprint 5), `docs/estabilidad_D3_1000ep_PS.md` y `data/analysis/estabilidad_D3_1000ep.{json,png}` (informe y figura), `docs/monitoreo_d3_1000ep.md` y `data/analysis/monitoreo_d3_1000ep.{json,png}` (panel de monitoreo), sección 8 del memo `docs/decision_RE_final_D3_para_BF.md` y una extensión de `scripts/analizar_estabilidad_D3.py` (episodios, entropía final y fracción de pasos en espera por red).
- **Por qué:** la comparación con 100 episodios no distinguía las opciones porque las políticas seguían casi uniformes; con 1.000 episodios ya se concentran y la evidencia es más informativa.
- **Resultado:** la regla de cumplimiento se dispara en 1 de 3 redes con la opción 0 y en 0 de 3 con la A; la opción A baja los pasos en espera de ≈ 30 % a 6–8 %, mientras que la 0 los deja en 11 % y 32 %; el costo no mejora con ninguna opción. La recomendación de PS se inclina por «D3: A», con la salvedad de que son 3 redes por opción y falta el control muestreado.
- **Cómo reproducir o verificar:** `python scripts/analizar_estabilidad_D3.py --dir data/colab_resultados/d3_1000ep --out-json data/analysis/estabilidad_D3_1000ep.json --out-png data/analysis/estabilidad_D3_1000ep.png --out-md docs/estabilidad_D3_1000ep_PS.md`.
- **Gráficos:** entradas en `docs/guia_graficos.md` (`estabilidad_D3_1000ep.png` y `monitoreo_d3_1000ep.png`).

### `feature/ps-sprint6-c3-v2-y-control`: C-3 con semilla fija y control muestreado (25 de octubre, noche)
- **Quién:** PS con apoyo de Claude Code.
- **Qué:** `data/colab_resultados/c3_sistema_v2/` (evaluador del sistema con la semilla de red fija) y los 5 archivos `control_sin_entrenar_muestreado_s*.json` en `data/colab_resultados/d3_estabilidad/` y `d3_1000ep/`; informes regenerados (`docs/estabilidad_D3_PS.md`, `docs/estabilidad_D3_1000ep_PS.md`, con la tabla del control justo y la prueba de signos), `docs/sistema_sin_entrenar_v2_vs_benchmarks_PS.md` y `data/analysis/sistema_sin_entrenar_v2_vs_benchmarks.{json,png}`; secciones nuevas en `docs/c3_sistema_sin_entrenar_PS.md` y en el memo de D3 (sección 9).
- **Por qué:** cerrar C-3 con una red coherente y completar el control que faltaba para comparar en igualdad de condiciones.
- **Resultado:** el sistema sin entrenar cumple el 66,3 % de las órdenes (apertura 94,6 %, media jornada 76,3 %, cierre 18,5 %) y no se distingue de TWAP en costo (+16,5 bps, p = 0,43); el «ahorro» del primer intento era un artefacto. El control muestreado muestra que una política casi uniforme ya cumple y cuesta ≈ 3 bps: con 100 episodios el entrenamiento casi no cambia nada (−0,39 bps) y con 1.000 episodios las 6 redes cuestan más que el control (+3,08 bps de media, 0 de 6 mejores).
- **Cómo reproducir o verificar:** `python scripts/analizar_estabilidad_D3.py --dir data/colab_resultados/d3_1000ep --out-json data/analysis/estabilidad_D3_1000ep.json --out-png data/analysis/estabilidad_D3_1000ep.png --out-md docs/estabilidad_D3_1000ep_PS.md` y la comparación descrita en `docs/sistema_sin_entrenar_v2_vs_benchmarks_PS.md`.
- **Gráficos:** entrada en `docs/guia_graficos.md` (`sistema_sin_entrenar_v2_vs_benchmarks.png`).

### `feature/ps-investigacion-recompensa`: por qué el entrenamiento no baja el costo y cómo arreglarlo (25–26 de octubre)
- **Quién:** PS con apoyo de Claude Code. Lo que toca partes de BF (R_E) y de MR (entrenador PPO) quedó como **borrador de PS para ellos**; no se modificó ningún archivo de sus tareas.
- **Qué:** diagnóstico (`docs/diagnostico_recompensa_PS.md`), envoltorio con variantes de recompensa y cierre de ventana (`src/experiments/variantes_recompensa.py`, `entrenamiento_variantes.py`), matriz de experimentos en el PC con Poisson (`scripts/experimentos_recompensa_ps.py`, resultados en `data/experimentos_recompensa/` e informes `docs/experimentos_recompensa_*_PS.md`), propuesta para BF y MR (`docs/propuesta_cambio_RE_para_BF_y_MR.md`), opciones `--gamma` y `--penalizacion-bps` en `scripts/colab/entrenamiento_inicial_ps.py` (apagadas por defecto) y dos cuadernos de Colab para confirmar en ABIDES (`notebooks/Colab_confirmacion_ABIDES_A.ipynb` y `_B.ipynb`). Resumen completo en `docs/investigacion_recompensa_que_se_hizo.md`.
- **Por qué:** con 1.000 episodios las redes entrenadas costaban más que la red sin entrenar muestreando (+3 bps); había que saber qué fallaba antes de ajustar hiperparámetros en el Sprint 6.
- **Resultado:** con la recompensa actual la red aprende a esperar (97–99 % de los pasos): nada obliga a completar la orden y el descuento γ = 0,95 hace que un costo al final de la ventana se vea cuatro veces más barato. Una penalización de 30 bps por acción sin comprar junto con γ = 1 hace que 5 de 5 redes cumplan la orden y bajen el costo al nivel de la mejor heurística (17,9 frente a 17,91 bps; red inicial, 20,26). Cada cambio por separado no funciona. Probado solo en Poisson; falta ABIDES.
- **Cómo reproducir o verificar:** `PYTHONPATH=. python -m pytest tests/test_variantes_recompensa.py` y los comandos de la sección 7 de `docs/investigacion_recompensa_que_se_hizo.md`.
- **Gráficos:** entradas en `docs/guia_graficos.md` (`diagnostico_recompensa.png` y `experimentos_recompensa_A/A2/B.png`).

### `feature/ps-sprint6-monitoreo-sensibilidad`: monitoreo calibrado, costo ajustado y sensibilidad 3.2.4 (26 de octubre)
- **Quién:** PS con apoyo de Claude Code. No toca archivos de MR ni de BF.
- **Qué:**
  - **3.1.4 Monitoreo:** alertas calibradas con 27 corridas reales (`scripts/calibrar_monitoreo_ps.py`, `docs/calibracion_monitoreo_PS.md`, corridas de Poisson en `data/calibracion_monitoreo/`), alerta nueva `RECOMPENSA_SUBE_COSTO_NO`, línea de costo de partida en el panel y `docs/guia_alertas_monitoreo_PS.md`.
  - **Costo ajustado por lo no ejecutado:** opción `--penalizaciones-no-ejecutado` en `scripts/comparar_sistema_vs_benchmarks.py` (`docs/sistema_sin_entrenar_v2_ajustado_PS.md` muestra el efecto con el sistema sin entrenar).
  - **3.2.4 Sensibilidad:** `scripts/analizar_sensibilidad_3_2_4.py` (tamaño × tramo × liquidez, Spearman y Kruskal-Wallis, figura), listo para las 90 corridas.
  - `docs/sprint6_que_se_hizo.md` actualizado y `docs/plan2_que_se_hizo.md`.
- **Por qué:** Plan 2 de PS (desarrollo de su parte del Sprint 6) con lo que no depende de Colab ni de los demás.
- **Resultado:** con los umbrales originales, `ENTROPIA_COLAPSADA` daba falsas alarmas en 2 de 4 corridas buenas y `PICO_PERDIDA_CRITICO` en las 4; con los calibrados, las buenas solo tienen avisos informativos y la alerta nueva avisa en 7 de 10 corridas malas y en ninguna buena. El costo ajustado muestra que el sistema sin entrenar parece igual a TWAP con 50–100 bps de penalización por lo no comprado y claramente peor con 300 bps.
- **Cómo reproducir o verificar:** `python scripts/calibrar_monitoreo_ps.py` (cruza alertas y etiquetas; `--generar` vuelve a entrenar las corridas de Poisson) y `PYTHONPATH=. python -m pytest tests/test_monitoreo.py tests/test_calibrar_monitoreo.py tests/test_sensibilidad_3_2_4.py`.
- **Gráficos:** entradas en `docs/guia_graficos.md` (`monitoreo_calibracion.png`, `sistema_sin_entrenar_v2_ajustado.png`).

### `feature/ps-confirmacion-abides-penalizacion`: confirmación en ABIDES de la penalización terminal (26 de octubre)
- **Quién:** PS con apoyo de Claude Code. No toca archivos de MR ni de BF.
- **Qué:** resultados de los dos cuadernos de Colab (`conf_pen30_g1_A` y `_B`: 4 semillas de red, 1.000 episodios, γ = 1 y penalización de 30 bps) en `data/colab_resultados/conf_pen30_g1/`; informes `docs/conf_pen30_g1_ABIDES_PS.md`, `docs/monitoreo_conf_pen30_g1.md` y `docs/confirmacion_abides_penalizacion_resultado_PS.md`; `scripts/analizar_estabilidad_D3.py` ahora compara red y control sobre las mismas semillas (40 frente a 15); se corrigieron los documentos que daban el arreglo de Poisson por probado.
- **Por qué:** comprobar en ABIDES si lo que arreglaba el entrenamiento en Poisson también baja el costo.
- **Resultado:** evita que la red se quede esperando (cumplimiento ≈ 1,0). Con 15 semillas de evaluación el costo parecía +3,0 bps sobre el control (0 de 4 redes mejores); **corregido después:** con 40 semillas es −2,2 bps (no significativo), ver la entrada de `feature/ps-abides-v4-resultados-A`. El monitoreo avisa `RECOMPENSA_SUBE_COSTO_NO` en 2 de 4 redes, como se calibró.
- **Cómo reproducir o verificar:** `python scripts/analizar_estabilidad_D3.py --dir data/colab_resultados/conf_pen30_g1 …` y `PYTHONPATH=. python -m pytest tests/test_estabilidad_d3.py`.
- **Gráficos:** entradas en `docs/guia_graficos.md` (`conf_pen30_g1.png`, `monitoreo_conf_pen30_g1.png`).

### `feature/ps-abides-recompensa-is-llegada`: cuadernos y herramientas de la prueba V4 en ABIDES (26 de octubre)
- **Quién:** PS con apoyo de Claude Code. No toca archivos de MR ni de BF.
- **Qué:** opción `--recompensa is_llegada` en `scripts/colab/entrenamiento_inicial_ps.py` (por defecto no cambia nada); cuadernos `notebooks/Colab_V4_ABIDES_A.ipynb` y `_B.ipynb`; `scripts/comparar_v4_vs_v2_ps.py` (V4 frente a V2 y al control por semilla de red) con sus tests; `docs/prueba_v4_abides_plan_PS.md` (para qué, cómo leer el resultado).
- **Por qué:** la confirmación anterior evitó la espera pero no bajó el costo; se prueba si la recompensa contra el precio de llegada, que sí ve el costo de llenarse tarde, lo arregla.
- **Resultado:** todavía no hay resultado: los cuadernos están listos y falta correrlos en Colab (≈ 120 min cada uno).
- **Cómo reproducir o verificar:** `PYTHONPATH=. python -m pytest tests/test_comparar_v4_vs_v2.py tests/test_variantes_recompensa.py`.
- **Gráficos:** ninguno todavía; el comparador genera `data/analysis/v4_vs_v2_ABIDES.png` cuando lleguen los zip y se explicará en `docs/guia_graficos.md`.

### `feature/ps-abides-v4-resultados-A`: resultado parcial de V4 (cuaderno A), corrección del control y reevaluación con 300 semillas (26 de octubre, noche)
- **Quién:** PS con apoyo de Claude Code. No toca archivos de MR ni de BF.
- **Qué:** datos del cuaderno A de V4 (`data/colab_resultados/v4_pen30_g1_A/`); `docs/v4_abides_resultado_parcial_A_PS.md` y `docs/v4_vs_v2_ABIDES_A_PS.md`; `scripts/colab/reevaluar_ejecutores_ps.py` y `notebooks/Colab_reevaluacion_300_ABIDES.ipynb` (reevalúan todas las redes con 300 semillas, sin entrenar); `scripts/analizar_reevaluacion_ps.py`; el comparador ahora incluye V2 − control; correcciones en los documentos que daban por cierto el «+3 bps, 0 de 4».
- **Por qué:** el control con 15 semillas era demasiado corto: el slippage por semilla lo domina el movimiento del precio y las 15 primeras semillas eran las más tranquilas. Con las 40 del cuaderno A la conclusión cambió de signo.
- **Resultado:** V4 no se distingue de V2 (−0,22 y +2,05 bps entre redes, no significativo). V2 frente al control: −2,2 bps con 40 semillas (24 y 26 de 40 mejores; p = 0,22 y 0,17). Sin conclusión firme hasta la reevaluación con 300 semillas.
- **Cómo reproducir o verificar:** `PYTHONPATH=. python -m pytest tests/test_comparar_v4_vs_v2.py tests/test_reevaluar_ejecutores.py tests/test_analizar_reevaluacion.py`.
- **Gráficos:** `data/analysis/v4_vs_v2_ABIDES_A.png` explicado en `docs/guia_graficos.md`.

### `feature/ps-abides-v4-resultados-A2`: corrección del cuaderno de reevaluación (26 de octubre, noche)
- **Quién:** PS con apoyo de Claude Code. **Qué:** el cuaderno `notebooks/Colab_reevaluacion_300_ABIDES.ipynb` ya no incluye las redes antiguas en la celda principal, porque en Drive hay dos carpetas llamadas `d3_1000ep` y Colab solo ve una; quedan en una celda opcional aparte. El cuaderno ahora descarga el código de esta rama (la anterior queda con la versión previa).
- **Por qué:** revisión del cuaderno antes de correrlo: se comprobó en Drive que las 4 redes de V2 y las 2 de V4 existen con su `checkpoint_last.pt` y que el reevaluador funciona de punta a punta con una raíz que aún no existe (la de V4 B).
- **Resultado:** sin cambios en los resultados; solo el cuaderno.

### `feature/ps-abides-v4-resultados-A3`: reevaluación con 300 semillas y análisis con los datos existentes (26 de octubre, noche)
- **Quién:** PS con apoyo de Claude Code. No toca archivos de MR ni de BF.
- **Qué:** el cuaderno de reevaluación pasa de 150 a 300 semillas (`notebooks/Colab_reevaluacion_300_ABIDES.ipynb`, carpeta de Drive `reeval_300`, ≈ 100–170 min); sección 3b de `docs/v4_abides_resultado_parcial_A_PS.md` con el análisis de lo que ya se puede decir con los datos de 40 semillas (control sustituto, comparación con TWAP, argmax, potencia).
- **Por qué:** con los datos de 40 semillas la desviación de la diferencia pareada red − control resultó ≈ 12 bps y no 9; con 150 semillas solo se verían diferencias de ≈ 3 bps, y las redes con penalización parecen estar en ≈ −2 bps.
- **Resultado:** las 4 redes de V2 quedan 1,8 a 3,4 bps por debajo del control (usando un control sustituto para 3000 y 4000), ninguna significativa por sí sola. V4 no se distingue de V2. Falta la reevaluación para confirmarlo.
- **Cómo reproducir o verificar:** `PYTHONPATH=. python -m pytest tests/test_reevaluar_ejecutores.py tests/test_analizar_reevaluacion.py`.
- **Gráficos:** ninguno nuevo.

### `feature/ps-reevaluacion-300-resultados`: resultado de la reevaluación con 300 semillas y cuaderno B de V4 (26 de octubre, noche)
- **Quién:** PS con apoyo de Claude Code. No toca archivos de MR ni de BF.
- **Qué:** datos de `reeval_300` (8 redes, 4 controles, 3 heurísticas, 300 semillas) en `data/colab_resultados/reeval_300/`; resultados del cuaderno B de V4 en `data/colab_resultados/v4_pen30_g1_B/`; informes `docs/reeval_300_ABIDES_PS.md` (tabla generada por `scripts/analizar_reevaluacion_ps.py`) y `docs/reeval_300_resultado_PS.md` (lectura y límites); figura `data/analysis/reeval_300_ABIDES.png`. No cambia código.
- **Por qué:** con 15 y 40 semillas el ruido del precio tapaba el efecto de entrenar; con 300 semillas el intervalo de confianza baja a ±1 bps.
- **Resultado:** ninguna de las 8 redes cuesta distinto a su control (diferencias −0,6 a +1,0 bps, todos los IC con el 0; las 8 juntas −0,08 bps, IC [−0,98; +0,77]); V2 ≈ V4; redes y control cuestan ≈ 2 bps más que TWAP límite. Entrenar 1.000 episodios no cambió el costo de forma medible.
- **Cómo reproducir o verificar:** `python scripts/analizar_reevaluacion_ps.py --dir data/colab_resultados/reeval_300 --out-md docs/reeval_300_ABIDES_PS.md --out-png data/analysis/reeval_300_ABIDES.png`.
- **Gráficos:** entrada en `docs/guia_graficos.md` (`reeval_300_ABIDES.png`).

### `feature/ps-plan-dejar-listo-mr-bf`: plan para que MR y BF solo lleguen, ejecuten y revisen (26 de octubre, noche)
- **Quién:** PS con apoyo de Claude Code. **Estado:** solo plan; no se escribió ni modificó código de MR ni de BF.
- **Qué:** `docs/plan_dejar_listo_MR_y_BF_PS.md`: aclara qué es el Plan 1 (arreglar el problema crítico, hecho) y el Plan 2 (desarrollo de la parte de PS, ejecutado en lo adelantable); lista, por persona, lo que PS puede dejar escrito (bucle del Maestro, barrido de hiperparámetros, revalidación de λ, parche de γ = 1 para MR; escenarios de liquidez, consolidador, parche de penalización en R_E y hoja de decisiones D1/D3 para BF), con tiempos de revisión, calendario y riesgo estadístico de las 90 corridas.
- **Por qué:** pedido de PS: que MR y BF lleguen, ejecuten y revisen en vez de programar desde cero.
- **Resultado:** ≈ 28 h de trabajo de PS a repartir en una semana y ≈ 4 h de revisión entre MR y BF. Falta que el grupo diga cuáles borradores quiere.

### `feature/ps-sprint6-completo`: PR único del Sprint 6 de PS (26 de octubre, noche)
- **Quién:** PS con apoyo de Claude Code. No toca archivos de tareas de MR ni de BF.
- **Qué:** reúne en un solo PR las 20 ramas `feature/ps-…` del Sprint 6 anteriores (están encadenadas, cada una contiene a la anterior) y se fusionó con `main` al 26 de octubre (PR #41 incluido, sin conflictos). Agrega `docs/informe_sprint6_PS.md` (informe para el Título II), el texto del PR (`docs/pr_sprint6_PS.md`), notas de «300 semillas» en los documentos que citaban cifras de 15 o 40 semillas (`diagnostico_recompensa_PS.md`, `estabilidad_D3_1000ep_PS.md`, `decision_RE_final_D3_para_BF.md`, `investigacion_recompensa_que_se_hizo.md`, `propuesta_cambio_RE_para_BF_y_MR.md`) y la actualización de `docs/sprint6_que_se_hizo.md` con el resultado de las 300 semillas y una tabla de lo que MR y BF deben revisar.
- **Por qué:** pedido de PS: subir su parte completa del Sprint 6 para que MR y BF vean lo que les corresponde. Con un solo PR ya no importa el orden de merge de las ramas anteriores.
- **Resultado:** ver `docs/informe_sprint6_PS.md`. Las ramas anteriores quedan como respaldo y se pueden cerrar tras el merge.
- **Cómo verificar:** `PYTHONPATH=. python -m pytest tests -q` (la única falla conocida es la que necesita el parquet de mercado).
- **Gráficos:** ninguno nuevo; los anteriores están explicados en `docs/guia_graficos.md`.

### `feature/ps-revision-opus`: revisión técnica y corrección de la recompensa del Ejecutor en ABIDES (29 de octubre)
- **Quién:** PS con apoyo de Claude Code (Opus). El parche de R_E es un **BORRADOR de PS para BF** (apagado por defecto); no se tocó código de MR.
- **Qué:** `docs/revision_opus_PS.md` (veredicto, 9 hallazgos, plan de 10 días y regla para cerrar D3); opción `mid_decision` en `src/envs/abides_bridge.py` y `src/envs/abides_ejecutor_env.py`, y `--mid-decision` en `scripts/colab/entrenamiento_inicial_ps.py`; `scripts/colab/verificar_mid_decision_ps.py`; cuadernos `notebooks/Colab_mid_decision_A.ipynb`, `_B.ipynb` y `Colab_reevaluacion_mid_decision_300.ipynb`; prueba de cordura del PPO `scripts/prueba_cordura_ppo_ps.py` (resultado en `data/analysis/prueba_cordura_ppo.txt`); `tests/test_mid_decision.py`; nota en 10 documentos con resultados de ABIDES y sección 10 del memo de D3.
- **Por qué:** pedido de PS: revisar si el proyecto va bien y buscar la falla de fondo. En ABIDES la recompensa comparaba el precio pagado con el precio medio de 30 s *después* (en Poisson, con el de la decisión), y la recompensa casi no se relacionaba con el costo.
- **Resultado:** el PPO de MR aprende en una prueba trivial (0,33 → 0,999 en 1.000 episodios); en las corridas V2 la correlación entre recompensa y costo es de 0,04 a 0,22; con el parche, comprar 1 CLP sobre el precio de decisión pasa de +1 a −1. Falta verificar en ABIDES (cuadernos listos).
- **Cómo reproducir o verificar:** `PYTHONPATH=. python -m pytest tests/test_mid_decision.py tests/test_abides_bridge.py -q` y `python scripts/prueba_cordura_ppo_ps.py`.
- **Gráficos:** ninguno nuevo.

### `feature/ps-evaluador-90-corridas`: arreglos del evaluador y tamaños variables en el entrenamiento (29 de octubre)
- **Quién:** PS con apoyo de Claude Code. Solo toca scripts de PS.
- **Qué:** `scripts/colab/evaluar_sistema_ps.py` carga los checkpoints de `PPOTrainer` (clave `model_state_dict`; antes buscaba `model` y una red entrenada no habría cargado); `scripts/colab/entrenamiento_inicial_ps.py` acepta `--aleatorizar` (tamaño de 1.000 a 20.000 acciones y ventana de 1 a 15 min sorteados por episodio, con la semilla del episodio para que reanudar dé lo mismo); pruebas en `tests/test_evaluador_90_corridas.py`.
- **Por qué:** hallazgo H4 de `docs/revision_opus_PS.md` (el Ejecutor solo veía 1.000 acciones y 15 min) y la carga de checkpoints, necesaria para evaluar redes entrenadas.
- **Resultado:** sin cambios en el comportamiento por defecto.
- **Cómo verificar:** `PYTHONPATH=. python -m pytest tests/test_evaluador_90_corridas.py -q`.
- **Gráficos:** ninguno.

### `feature/ps-borrador-bf-liquidez`: BORRADOR de PS para BF, escenarios de liquidez, consolidador y hoja D1/D3 (29 de octubre)
- **Quién:** PS con apoyo de Claude Code. **Borrador para BF:** no modifica los entornos ni la recompensa de BF; los escenarios se aplican desde afuera.
- **Qué:** `src/envs/escenarios_liquidez.py` y `data/scenarios/escenarios_liquidez_v1.json` (0,5×, 1× y 2×; en ABIDES `num_noise_agents`, `lambda_a`, `mm_pov`; en Poisson, la profundidad del libro); `--escenario` y `--factor-tamano` en `scripts/colab/evaluar_sistema_ps.py` y `scripts/colab/benchmarks_meta_ordenes_ps.py`; `scripts/colab/c6_escenarios_liquidez_bf.py` y `notebooks/Colab_C6_escenarios_liquidez_BF.ipynb`; `scripts/consolidar_resultados_3_2_2.py`; `docs/hoja_decisiones_D1_D3_BF.md`; `docs/LEEME_BF.md`; pruebas en `tests/test_escenarios_liquidez.py`.
- **Por qué:** pedido de PS: dejar el código de BF escrito para que solo revise, decida y corra Colab (tareas 3.1.3 y 3.2.2, decisiones D1 y D3 pendientes desde hace dos semanas).
- **Resultado:** en Poisson (30 semillas), comprar 1.000 acciones a mercado cuesta 2,5 bps más con liquidez baja (IC 95 % de 2,3 a 2,7) y 0,7 bps menos con liquidez alta: el C-6 da OK. Falta confirmarlo en ABIDES.
- **Cómo verificar:** `PYTHONPATH=. python -m pytest tests/test_escenarios_liquidez.py -q`.
- **Gráficos:** ninguno.

### `feature/ps-borrador-mr-maestro`: BORRADOR de PS para MR, bucle del Maestro, impacto acumulado, checkpoint, γ, barrido y λ (29 de octubre)
- **Quién:** PS con apoyo de Claude Code. **Borrador para MR:** el único archivo de MR que cambia es `src/training/ppo_trainer.py` (estado aleatorio en el checkpoint y `GAMMA_EJECUTOR = 1.0`); lo demás son módulos nuevos.
- **Qué:** `src/training/maestro_trainer.py` y `scripts/entrenar_maestro.py` (M1); `src/envs/impacto_acumulado.py` y `--impacto` en los dos evaluadores (diseño del Maestro, opción 2); estado aleatorio en el checkpoint (M2); barrido de hiperparámetros con regla fijada (`scripts/barrido_hiperparametros_mr.py`, `scripts/colab/grid_specs/hiperparametros_ejecutor_mr.json`, opciones de hiperparámetros en `entrenamiento_inicial_ps.py`) (M3); `scripts/revalidar_lambda_maestro.py` (M4); γ_E = 1 y secciones 6 y 7 de `DESVIACIONES_TITULO1_VS_IMPLEMENTACION.md` (M5); `notebooks/Colab_Maestro_MR.ipynb` (M6); `scripts/comparar_maestro_vs_twap_ps.py`; `docs/maestro_primer_entrenamiento_PS.md`; `docs/LEEME_MR.md`; datos en `data/maestro/primer_entrenamiento_29oct/`; pruebas en `tests/test_maestro_trainer.py`.
- **Por qué:** pedido de PS: dejar el código de MR escrito para que solo revise, decida y corra Colab. El Maestro no tenía bucle de entrenamiento y, sin impacto entre ventanas, no tenía nada que coordinar.
- **Resultado (Poisson):** el Maestro aprende a completar la orden (cumplimiento de 0,959 a 0,999). Con λ = 0,05 cuesta más que TWAP (+1,82 bps con 2.000 jornadas); con λ = 0,02 empata (+0,36 bps, IC −0,08 a +0,83). Reanudar desde un checkpoint ahora da los mismos pesos que no cortar.
- **Cómo verificar:** `PYTHONPATH=. python -m pytest tests/test_maestro_trainer.py -q`.
- **Gráficos:** el barrido genera `barrido.png` en su carpeta de salida; se explicará en `docs/guia_graficos.md` cuando se corra.

### `feature/ps-borrador-bf-c6b-mm`: resultado del C-6 y escenarios v2 que escalan solo al market maker (29 de octubre)
- **Quién:** PS con apoyo de Claude Code. Borrador para BF; no toca los entornos.
- **Qué:** resultado del C-6 en `data/colab_resultados/c6_liquidez/` y `docs/c6_liquidez_resultado_PS.md`; `data/scenarios/escenarios_liquidez_v2.json` (solo `mm_pov`, 0,25×, 1× y 4×, criterio fijado antes de correr); `claves_abides` y `criterio_c6` en `src/envs/escenarios_liquidez.py`, en los dos evaluadores y en el C-6; cuaderno `notebooks/Colab_C6b_liquidez_mm_BF.ipynb` (60 semillas).
- **Por qué:** el C-6 dio REVISAR. Con la v1, comprar a mercado no cambió entre escenarios y los IC fueron de ±5 a ±10 bps: escalar agentes mezcla liquidez con volatilidad y rompe el pareo por semilla. PS pidió arreglarlo sin esperar a BF.
- **Resultado:** la v1 solo distingue con órdenes pasivas (TWAP límite con liquidez baja: +7,9 bps, IC +0,7 a +13,9). Falta correr el C-6b.
- **Cómo verificar:** `PYTHONPATH=. python -m pytest tests/test_escenarios_liquidez.py -q`.
- **Gráficos:** ninguno.

### `feature/ps-cierre-sprint6`: cierre del Sprint 6, resultados de Colab, Ejecutor con imitación, sistema final y 30 corridas (29 de octubre)
- **Quién:** PS con apoyo de Claude Code (Opus). Lo que toca partes de MR (Maestro, barrido) y BF (D3) sigue como borrador para ellos.
- **Qué:**
  - Resultados de Colab guardados: `data/colab_resultados/reeval_300_mid/`, `rmid/`, `maestro_impacto/`.
  - Informes: `docs/reeval_300_mid_resultado_PS.md` (con su tabla `docs/reeval_300_mid_ABIDES_PS.md`, generada por `scripts/analizar_reeval_mid_ps.py`) y `docs/maestro_abides_primera_prueba_PS.md`.
  - D3 cerrada con la regla (opción 0) en la hoja y en el memo.
  - Ejecutor: arranque por imitación (`--imitar`, `--guardar-imitacion` en `entrenamiento_inicial_ps.py`).
  - Sistema final: regla para elegir el Ejecutor (`scripts/elegir_ejecutor_ps.py`, excluye heurísticas y redes solo imitadas); Maestro con Ejecutor entrenado (`--ckpt-ejecutor`) y con inicio en los tres tramos (`--inicio-aleatorio`).
  - Consolidador con desviación, Wilcoxon, t-test y gráfico de cajas, que salta los bloques que faltan.
  - Monitoreo conectado al barrido de hiperparámetros.
  - Corrección de la «hipótesis del 10 %» (no está en el Título I) y desviaciones 8 y 9.
  - Cuadernos: `Colab_imitacion_A/B`, `Colab_reevaluacion_imitacion_300`, `Colab_sistema_final`, `Colab_30corridas_bloque1` a `4`; orden en `docs/LEEME_COLAB_CIERRE_SPRINT6.md`.
  - Pruebas en `tests/test_cierre_sprint6.py`.
- **Por qué:** pedido de PS: dejar completo el Sprint 6 guiándose por el Título I. La recompensa corregida empeoró el costo (+1,55 bps frente al control) y el Título I exige Ejecutores PPO, así que se prueba la imitación y se elige el mejor Ejecutor PPO con una regla fijada antes.
- **Resultado:** la cadena completa (imitación → reevaluación → elección → Maestro → 30 corridas → tabla) se probó en Poisson en el PC. Los números de ABIDES llegan con los cuadernos.
- **Cómo verificar:** `PYTHONPATH=. python -m pytest tests/test_cierre_sprint6.py tests/test_maestro_trainer.py tests/test_escenarios_liquidez.py -q`.
- **Gráficos:** `cajas.png` y `barrido.png`, explicados en `docs/guia_graficos.md`.

### `feature/ps-cierre-sprint6-b`: resultado del barrido de hiperparámetros y documento del Sprint 6 (29 de octubre, noche)
- **Quién:** PS con apoyo de Claude Code. Borrador para MR en lo que toca a la 3.1.1 y la 3.1.2.
- **Qué:** resultados del barrido en `data/barrido_hp/3_1_1/` y `3_1_2/` (con su monitoreo); `docs/barrido_hiperparametros_resultado_PS.md`; corrección del analizador del barrido (en la 3.1.2 la referencia es el ganador de la 3.1.1, no la configuración de siempre); `docs/sprint6_que_se_hizo.md` reescrito; sección 1b de `docs/informe_sprint6_PS.md`.
- **Por qué:** cerrar el Sprint 6 con lo medido.
- **Resultado:**
  - 3.1.1: gana tasa 0,003, lote 128, 16 épocas (−2,62 bps frente a −2,43 de la configuración de siempre).
  - 3.1.2: se mantienen ε = 0,2 y λ = 0,95.
  - El monitoreo marcó alertas críticas justo en las 6 redes que no completan la orden.
- **Cómo verificar:** `PYTHONPATH=. python scripts/barrido_hiperparametros_mr.py --fase 3.1.2 --out-dir data/barrido_hp --solo-analizar`.
- **Gráficos:** `data/barrido_hp/*/barrido.png` y `monitoreo.png`, explicados en `docs/guia_graficos.md`.

### `feature/ps-cierre-sprint6-c`: resultado del Ejecutor con imitación (29 de octubre, noche)
- **Quién:** PS con apoyo de Claude Code. PS corrió los cuadernos en Colab.
- **Qué:** resultados de `Colab_imitacion_A` y `_B` en `data/colab_resultados/rimit/` y análisis en `docs/imitacion_resultado_PS.md`. Se actualizaron `docs/sprint6_que_se_hizo.md`, `docs/informe_sprint6_PS.md` y `docs/LEEME_COLAB_CIERRE_SPRINT6.md`.
- **Por qué:** paso 1 del cierre del Sprint 6.
- **Resultado:** en 15 semillas, las dos redes con argmax quedan en +1,48 y +1,62 bps sobre TWAP límite, con cumplimiento de 0,99. Las redes anteriores quedaban entre +3,8 y +5,8 en las mismas semillas. Falta la reevaluación con 300 semillas.
- **Cómo verificar:** leer `resultados.evaluacion_entrenada` en `data/colab_resultados/rimit/*/entrenamiento_inicial_apertura.json`.
- **Gráficos:** no hay.

### `feature/ps-resultados-30oct`: reevaluación con imitación y C-6b (30 de octubre)
- **Quién:** PS con apoyo de Claude Code. PS corrió los cuadernos en Colab. Los escenarios v3 son **borrador de PS para BF**.
- **Qué:**
  - resultados en `data/colab_resultados/reeval_300_imitacion/` y `c6b_liquidez/`;
  - `docs/reeval_300_imitacion_resultado_PS.md` y la tabla `docs/reeval_300_imitacion_ABIDES_PS.md`;
  - sección 4 de `docs/c6_liquidez_resultado_PS.md`;
  - `data/scenarios/escenarios_liquidez_v3.json`, con su prueba, y la desviación 10;
  - el analizador de la reevaluación separa los grupos de imitación;
  - actualización de `docs/sprint6_que_se_hizo.md`, `docs/informe_sprint6_PS.md` y `docs/LEEME_COLAB_CIERRE_SPRINT6.md`.
- **Por qué:** paso 2 del cierre del Sprint 6.
- **Resultado:**
  - la red de imitación + PPO s1000 cuesta 5,68 bps en 300 semillas, la mejor red PPO medida, y queda +1,03 bps sobre TWAP límite;
  - falta la red s2000, que no se encontró en Drive;
  - en el C-6b, más `mm_pov` encarece la compra a mercado (11,7 → 24,2 bps), con el pareo funcionando.
- **Cómo verificar:** `PYTHONPATH=. python scripts/analizar_reeval_mid_ps.py --dir data/colab_resultados/reeval_300_imitacion`; `python -m pytest tests/test_escenarios_liquidez.py -q`.
- **Agregado después, en la misma rama:**
  - resultado del sistema final en `data/colab_resultados/sistema_final/` y `docs/sistema_final_resultado_PS.md`: Ejecutor s1000; el Maestro completa el 97,6 % de la orden (antes, 73 %);
  - cuaderno `notebooks/Colab_reeval_red_B.ipynb`, que encuentra y reevalúa la red s2000 y rehace el Maestro si esa red gana.
- **Gráficos:** no hay.

### `feature/ps-resultados-30oct-c`: red B reevaluada y bloque 1 de las 30 corridas (30 de octubre, noche)
- **Quién:** PS con apoyo de Claude Code. PS corrió `Colab_reeval_red_B` y `Colab_30corridas_bloque1` en Colab.
- **Qué:**
  - `data/colab_resultados/reeval_300_imitacion/red_rimit__d3_opcion0_s2000.json` y la tabla regenerada `docs/reeval_300_imitacion_ABIDES_PS.md`;
  - `data/colab_resultados/sistema_final_revision/ejecutor_elegido.json` (la regla aplicada otra vez);
  - `data/colab_resultados/corridas_30/bloque_1/` y `tabla_bloque1/`, con el avance en `docs/corridas_30_avance_bloque1_PS.md` (renombrado después a `docs/corridas_30_avance_PS.md`);
  - actualización de `docs/reeval_300_imitacion_resultado_PS.md`, `docs/sistema_final_resultado_PS.md`, `docs/sprint6_que_se_hizo.md`, `docs/informe_sprint6_PS.md`, `docs/LEEME_COLAB_CIERRE_SPRINT6.md` y `docs/guia_graficos.md`.
- **Por qué:** pasos 3b y 4 del cierre del Sprint 6.
- **Resultado:**
  - la red s2000 cuesta 5,98 bps, más que la s1000 (5,68): el Ejecutor elegido y el Maestro no cambian;
  - bloque 1 (9 pares): sistema − TWAP −18,4 bps [−38,9; +3,3] y sistema − VWAP −18,7 [−44,5; +8,0]. Todavía no se distingue.
- **Cómo verificar:** `PYTHONPATH=. python scripts/analizar_reeval_mid_ps.py --dir data/colab_resultados/reeval_300_imitacion`.
- **Gráficos:** `tabla_bloque1/cajas.png` (ver `docs/guia_graficos.md`).

### `feature/ps-resultados-30oct-d`: bloques 2 y 3 de las 30 corridas (30 de octubre, noche)
- **Quién:** PS con apoyo de Claude Code. PS corrió `Colab_30corridas_bloque2` y `3` en Colab.
- **Qué:**
  - `data/colab_resultados/corridas_30/bloque_2/`, `bloque_3/` y `tabla_bloques1a3/`. La tabla se tomó del zip del bloque 2, porque en el del bloque 3 los benchmarks del bloque 2 estaban incompletos;
  - el avance pasa a `docs/corridas_30_avance_PS.md`, con el desglose por orden;
  - actualización de `docs/sprint6_que_se_hizo.md`, `docs/informe_sprint6_PS.md`, `docs/LEEME_COLAB_CIERRE_SPRINT6.md` y `docs/guia_graficos.md`.
- **Por qué:** paso 4 del cierre del Sprint 6.
- **Resultado:**
  - con 24 pares, sistema − TWAP −26,0 bps [−58,4; +6,0] y sistema − VWAP −29,7 [−66,8; +6,5]; el sistema gana 17 de 24 pares, pero todavía sin significancia;
  - la desviación de la diferencia es ≈ 85 bps, más de lo estimado;
  - en MO-08 (cierre) el sistema compra solo el 93 %.
- **Cómo verificar:** abrir `data/colab_resultados/corridas_30/tabla_bloques1a3/tabla_maestra.md`.
- **Gráficos:** `tabla_bloques1a3/cajas.png` (ver `docs/guia_graficos.md`).

## 3. Ramas obsoletas (no usar)

| Rama | Reemplazada por |
|---|---|
| `feature/ps-borrador-bf-t3-meta-ordenes` y `...-v2` | `feature/ps-sprint5-final-v2` |
| `feature/ps-borrador-bf-t5-entrenamiento` | `feature/ps-sprint5-final-v2` (y PR #39 para los 100 episodios) |
| `feature/ps-t4-benchmarks-resultados` | `feature/ps-sprint5-final-v2` |
| `feature/ps-sprint5-borrador-bf-final` | `feature/ps-sprint5-final-v2` |
| `feature/ps-sprint5-t3-t4-t5-sobre-main` | Base de la rama del Sprint 6; el contenido definitivo del Sprint 5 está en `final-v2` |
| `feature/ps-informe-titulo2-sprint4` | `feature/ps-informe-titulo2-sprint4-v2` |
| `feature/ps-borrador-mr-t1-t2-evidencia-abides` | PR #41 |

## 4. Plantilla para entradas nuevas

```
### PR #N, `rama`, fecha: título corto
- **Quién:** (PS / MR / BF; "borrador de PS para X" si lo revisa otro)
- **Qué:** (cambios concretos)
- **Por qué:** (la razón: tarea del plan, hallazgo, decisión)
- **Archivos clave:** (rutas)
- **Resultado:** (cifras o conclusión principal)
- **Cómo reproducir o verificar:** (comando)
- **Gráficos:** (si hay, entrada en docs/guia_graficos.md)
```

🤖 Generado con [Claude Code](https://claude.com/claude-code)

### `feature/ps-plan-borradores-mr-bf`: plan de borradores para MR y BF (22 de octubre)
- **Quién:** PS con apoyo de Claude Code. **Qué:** `docs/plan_borradores_para_MR_y_BF_sprint6.md`: qué borradores de programación se pueden dejar listos para Mauricio (bucle del Maestro, checkpoint con estado aleatorio, barrido de hiperparámetros, revalidación de λ) y Benjamín (escenarios de liquidez, consolidador), más un evaluador compartido. **Estado:** solo plan, sin ejecutar.
- **Por qué:** MR y BF tienen poco tiempo; así solo aceptan o modifican en lugar de programar y probar desde cero.
