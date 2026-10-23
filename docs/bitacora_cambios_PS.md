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
