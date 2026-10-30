# Sprint 6 (26 oct – 6 nov 2026): qué se hizo

Documento de cierre del Sprint 6 (tarea 3.1.5, Sprint Review), elaborado por PS con apoyo de Claude Code (uso de IA autorizado por la universidad).
- **Última actualización:** 29 de octubre de 2026 (noche).
- **Pendiente:** se completa con los resultados de los cuadernos de cierre (sección 5) y cada fila la confirma su responsable en la reunión del viernes 6 de noviembre.
- **Referencia:** el Título I. La «hipótesis del 10 %» que aparecía antes era un error de un documento de contexto: el Título I pide comparar con TWAP y VWAP y verificar si hay reducción, sin umbral.

Estados: **Hecho** · **Hecho con límite** · **En Colab** (código listo, falta el resultado del cuaderno) · **Pasa al Sprint 7**.

> **Condición de cierre:** una tarea queda cerrada cuando su código está en `main` mediante un PR mergeado. Orden de las ramas en la sección 7.
> **Asignación:** el Excel pone 3.1.3 a PS y 3.1.4 a BF; la especificación detallada lo hace al revés. Este documento sigue la especificación y anota los dos nombres, para que el grupo lo confirme.

## 1. Tareas del sprint

| Tarea | Responsable | Estado | Qué hay | Dónde | Confirma |
|---|---|---|---|---|---|
| **3.1.1** Tasa de aprendizaje, lote y épocas del PPO | MR (borrador de PS) | Hecho con límite | Barrido de 36 configuraciones × 2 redes en Poisson, con regla fijada antes. Gana tasa 0,003, lote 128, 16 épocas (−2,62 bps frente a la red inicial; la configuración de siempre, −2,43). La mejora es chica. **Límite:** medido en Poisson; en ABIDES no se aplicó todavía | `docs/barrido_hiperparametros_resultado_PS.md`, `data/barrido_hp/3_1_1/` | MR |
| **3.1.2** Clipping ε y λ de GAE | MR (borrador de PS) | Hecho con límite | 25 combinaciones aleatorias partiendo del ganador de la 3.1.1. Ninguna mejora con claridad: **se mantienen ε = 0,2 y λ = 0,95**. Las combinaciones con λ ≈ 0,90 no completan la orden. Mismo límite | `data/barrido_hp/3_1_2/` | MR |
| **3.1.3** Corridas de evaluación (30 corridas del sistema contra TWAP y VWAP, con media, desviación, IC 95 %, Wilcoxon, t-test y gráfico de cajas) | BF (PS según el Excel) | En Colab | Sistema final (Maestro y Ejecutor PPO), 10 meta-órdenes × 3 semillas, con impacto acumulado. Evaluadores, consolidador y cuadernos listos y probados en Poisson | `notebooks/Colab_30corridas_bloque1` a `4`, `scripts/consolidar_resultados_3_2_2.py` | BF / PS |
| **3.1.4** Monitoreo y registro de métricas | PS (BF según el Excel) | Hecho | Monitor por episodio y panel, con alertas calibradas en 27 corridas reales. **Conectado al barrido de MR:** hubo alertas críticas en 6 de 122 redes, que son justo las que no completan la orden. Se cerró el límite anterior | `src/training/monitoreo.py`, `docs/guia_alertas_monitoreo_PS.md`, `data/barrido_hp/*/monitoreo.md` | PS |
| **3.1.5** Sprint Review | Los tres | Este documento | — | — | Los tres |
| **P10** Revalidar λ del Maestro | MR (borrador de PS) | Hecho con límite | En Poisson, con el Maestro entrenado, λ = 0,05 deja al Maestro 1,8 bps sobre TWAP y λ = 0,02 lo deja empatado (+0,36 bps, IC −0,08 a +0,83). El sistema final usa λ = 0,02. **Límite:** Poisson | `docs/maestro_primer_entrenamiento_PS.md`, `scripts/revalidar_lambda_maestro.py` | MR |

## 2. Lo que se construyó en el sprint (además de las tareas)

| Qué | Para qué | Dónde | Estado |
|---|---|---|---|
| Bucle de entrenamiento del Maestro (Ejecutores fijos, R_M en bps, inicio en los tres tramos) | El Maestro no se entrenaba | `src/training/maestro_trainer.py`, `scripts/entrenar_maestro.py` | Hecho (borrador para MR) |
| Impacto acumulado entre ventanas | Que el Maestro tenga algo que coordinar; se aplica igual a TWAP/VWAP | `src/envs/impacto_acumulado.py`, desviación 7 | Hecho (supuesto declarado) |
| Checkpoint con estado aleatorio | Que reanudar dé lo mismo que no cortar | `src/training/ppo_trainer.py` | Hecho (borrador para MR) |
| Escenarios de liquidez, C-6 y C-6b | Base de las 90 corridas del Sprint 7 | `src/envs/escenarios_liquidez.py`, `docs/c6_liquidez_resultado_PS.md` | v1 dio REVISAR; v2 en Colab |
| Revisión técnica y corrección de la recompensa en ABIDES (`mid_decision`) | Saber por qué el Ejecutor no aprendía | `docs/revision_opus_PS.md`, `docs/reeval_300_mid_resultado_PS.md` | Hecho; la corrección no bajó el costo y queda como opción |
| Arranque por imitación del Ejecutor | Que el Ejecutor PPO parta de la mejor política medida | `--imitar` en `scripts/colab/entrenamiento_inicial_ps.py` | En Colab |
| Regla para elegir el Ejecutor del sistema final | Elegir sin mirar las 30 corridas | `scripts/elegir_ejecutor_ps.py` | Hecho |
| Prueba de cordura del PPO | Descartar un error del entrenador | `scripts/prueba_cordura_ppo_ps.py` | Hecho: el PPO aprende |

## 3. Resultados clave (medidos)

1. **El PPO funciona.** En una prueba simple aprende la mejor acción en 1.000 episodios (de 0,33 a 0,999). Con el ruido de ABIDES, 1.000 episodios no alcanzan (0,34) y 20.000 llegan a 0,64.
2. **Ejecutor en ABIDES, con 300 semillas:** ninguna recompensa probada le gana a la misma red sin entrenar:
   - V2: −0,19 bps;
   - V4: −0,11 bps;
   - recompensa corregida: +1,55 bps (peor).

   TWAP con órdenes límite cuesta ≈ 2,3 bps menos que cualquier red.
3. **La recompensa en ABIDES tenía una falla** (medía contra el precio de 30 s después). Se corrigió y la red cambió de conducta (dejó de comprar a mercado), pero empeoró el costo, porque esa recompensa no mide el costo de esperar.
4. **Maestro:** en Poisson aprende a completar la orden (cumplimiento de 0,96 a 0,999). Con λ = 0,02 y 2.000 jornadas empata con TWAP. En ABIDES (4 corridas) no se distingue de TWAP (−3,4 bps, IC −44 a +37): el costo de una jornada lo domina hacia dónde se mueve el precio ese día.
5. **Hiperparámetros:** en Poisson casi cualquier configuración razonable llega al mismo nivel. La tasa alta con lote chico colapsa, y el monitoreo lo detecta.
6. **Precisión:** la desviación del costo entre jornadas en ABIDES es ≈ 40 bps. Con 30 corridas, el IC de la diferencia con TWAP quedará en ≈ ±15 bps.

## 4. Decisiones

| Decisión | Estado | Qué se aplicó |
|---|---|---|
| D1: tamaño de las meta-órdenes | Por defecto (BF puede cambiarlo) | v2: 10 % del volumen del día (5 % si parte en el cierre); 10 de 10 órdenes ejecutables |
| D3: R_E opción 0 u opción A | Cerrada con la regla fijada | **Opción 0**: las dos completan el 100 % con argmax; la A cuesta 0,60 bps menos, pero eso no basta según la regla |
| γ_E = 1 y penalización de 30 bps | Propuesta (desviación 6) | Se usan en los entrenamientos del Ejecutor |
| λ del Maestro | Revalidado en Poisson | 0,02 en el sistema final (MR puede cambiarlo) |
| Recompensa corregida (`mid_decision`) | Opción, no por defecto | Empeora el costo en ABIDES |
| Ejecutor del sistema final | Regla fijada | La red PPO más barata en 300 semillas que cumpla al menos el 95 % (sin heurísticas ni redes solo imitadas) |
| Escenarios de liquidez | v1 REVISAR; v2 en Colab | Si el C-6b da OK, la v2 queda para el Sprint 7 |

## 5. Lo que falta correr en Colab para cerrar (orden en `docs/LEEME_COLAB_CIERRE_SPRINT6.md`)

1. `Colab_imitacion_A` y `_B` → `Colab_reevaluacion_imitacion_300` (y en paralelo `Colab_C6b_liquidez_mm_BF`).
2. `Colab_sistema_final`.
3. `Colab_30corridas_bloque1` a `4` (3.1.3).

Cuando lleguen los resultados se completan las filas 3.1.3 y el resultado del Ejecutor con imitación.

## 6. Qué pasa al Sprint 7

- 3.2.1 a 3.2.4 (90 corridas por escenario, consolidación, comparación estadística y sensibilidad): el código está listo y probado; falta el escenario de liquidez validado (C-6b).
- Ejecutores propios para media jornada y cierre (desviación 8).
- Aplicar en ABIDES los hiperparámetros del barrido, si MR los aprueba.

## 7. Ramas (todas sin PR; orden de merge)

1. `feature/ps-revision-opus-v2`
2. `feature/ps-evaluador-90-corridas`
3. `feature/ps-borrador-bf-liquidez`
4. `feature/ps-borrador-mr-maestro`
5. `feature/ps-borrador-bf-c6b-mm`
6. `feature/ps-cierre-sprint6`
7. `feature/ps-cierre-sprint6-b` (barrido y este documento)

Cada una contiene a la anterior. No borrar `feature/ps-revision-opus` ni `feature/ps-cierre-sprint6` mientras haya cuadernos que las usen.

## 8. Dónde está cada cosa

| Qué | Dónde |
|---|---|
| Informe del Sprint 6 para el Título II | `docs/informe_sprint6_PS.md` |
| Revisión técnica | `docs/revision_opus_PS.md` |
| Bitácora de cada rama | `docs/bitacora_cambios_PS.md` |
| Explicación de cada gráfico | `docs/guia_graficos.md` |
| Desviaciones respecto del Título I | `DESVIACIONES_TITULO1_VS_IMPLEMENTACION.md` |
| Guías para MR y BF | `docs/LEEME_MR.md`, `docs/LEEME_BF.md` |

🤖 Generado con [Claude Code](https://claude.com/claude-code)
