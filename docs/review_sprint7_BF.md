# Sprint Review del Sprint 7: parte de BF (20 de noviembre de 2026)

**Sprint 7:** 9 al 20 de noviembre. **Tarea de BF:** 3.2.2, consolidación de las 90 corridas (20 h, 11 al 18 nov). También corrió la profundidad ×4 de la 3.2.1, la desviación 12 con el tamaño 0,5, y revisó α = 0,5 del Maestro.
**Base:** `origin/main` = `3641290` (PR #60). Todas las cifras salen de archivos versionados en main, salvo la sección 5, que es local.

## 1. Resumen en 5 líneas

1. **Profundidad ×4 de las 90 corridas** (PR #51, 11 nov): sistema − TWAP = −10,53 bps [−33,09; 11,79], p = 0,44.
2. **3.2.2 completa** (script y calidad en el PR #54; las 90 con la ×0,25 de MR, PR #57).
   - Son 450 corridas, con la calidad en OK.
   - **Global, n = 90:** sistema − TWAP = **−3,34 bps [−15,69; 9,67], p = 0,39**. Es más barato en promedio, sin diferencia significativa.
   - Se reproduce exacta con un solo comando.
3. **Desviación 12 aprobada** (PR #53). Tamaño 0,5 corrido por BF (PR #56) y 1,5 por MR (PR #59).
   - Sistema − TWAP: +2,20 con 0,5; −3,37 con 1; −7,88 con 1,5.
   - Ningún IC excluye el 0.
4. **α = 0,5 fija del Maestro:** se probaron reglas fijas en días de bajo, medio y alto volumen (1.500 corridas en Poisson, con el snapshot nuevo del 11 nov). La mejor es 0,5 en los tres tipos de día, así que no hace falta reentrenar. Es un experimento local, sin PR.
5. **Advertencias para el informe:**
   - el sistema no siempre completa la orden: mínimo 94,7 % con ×0,25 y 78,4 % con el tamaño 1,5;
   - con ×0,25 la ventaja desaparece (+3,87);
   - con n = 90 solo se detectarían diferencias de unos 19 bps.

## 2. % de Realización para el Excel

| Tarea | % | Evidencia |
|---|---|---|
| **3.2.2** Consolidación de resultados (BF) | **100 %** | Ver la tabla siguiente |

| Criterio de terminado (Tareas del Sprint 7) | Cumplido | Evidencia |
|---|---|---|
| Revisar y aprobar `scripts/consolidar_resultados_3_2_2.py` (borrador de PS) | Sí | PR #54 (12 nov): BF lo amplió como dueño, con 12 tests en `tests/test_consolidar_resultados_3_2_2.py` |
| Correrlo con las 90 | Sí | `data/analysis/3_2_2/`: ×4 (BF), ×1 (PS) y ×0,25 (MR, PR #57), con 30 cada una |
| Tabla matriz por escenario en CSV y LaTeX: IS del sistema, TWAP y VWAP, diferencia %, ranking | Sí | `tabla_90.{csv,md,tex}` y `tabla_90_ajustado.*` |
| Media, mediana, peor y mejor | Sí | `agregados_por_escenario.csv` y `agregados.csv` |
| Chequeo de calidad: 90 corridas leídas, sin duplicados, cumplimiento informado | Sí | `calidad.{json,md}`: OK con 450 corridas, 0 errores y 0 duplicados; las corridas bajo el 95 % se listan |
| Probado con las 30 del Sprint 6 | Sí | La tabla maestra sale idéntica a la publicada (test `test_la_tabla_maestra_de_las_30_corridas_del_sprint_6_no_cambia`) |

**Fechas:**
- **12 nov:** el script queda listo (PR #54). Vencía el 18 nov.
- **14 nov:** se completan las 90 (PR #57). MR corrió el comando de la 3.2.2 con su ×0,25.
- **15 nov:** el eje de tamaño queda completo (PR #59).
- **20 nov:** este PR corrige el doc de la consolidación (sección 4).

**Notas para el Excel:**
- **Numeración de capítulos.** El Excel llama a la 4.1.2 «Cap. 6 Resultados». En la guía de ensamblado de PS (`docs/informe_titulo2_ensamblado_borrador.md`) esa tarea son dos capítulos de BF: el 6, «Entrenamiento y experimentación», y el 7, «Resultados y evaluación». Hay que confirmarlo con el equipo; ver la sección 3.
- **El 1,5 lo corrió MR**, como parte de su 3.2.4. En el documento de tareas del Sprint 7, la 3.2.4 figuraba antes de PS.

**Otros pendientes de BF que se cerraron en el sprint:**

| Pendiente | Estado | Evidencia |
|---|---|---|
| P4 Confirmación C-6c | Hecho (5 nov): **no confirmada**. Los escenarios se informan como profundidad del market maker ×4 / ×1 / ×0,25 | `docs/c6c_confirmacion_v3_BF.md`, desviación 10 |
| P5 Profundidad ×4 de las 90 | Hecho (11 nov) | PR #51, `docs/corridas_90_baja_resultado_BF.md` |
| P6 Desviación 12 (tamaño) | Hecho: aprobada el 11 nov, con el 0,5 corrido el 13 nov | PR #53 y #56, `docs/tamanos_media_f05_resultado_BF.md` |
| P7 3.2.2 | Hecho | Arriba |

## 3. Material de la 3.2.2 para la 4.1.2 (Sprint 8, capítulos 6 y 7)

### 3.1 Capítulo 7, «Resultados y evaluación»: desempeño comparativo, por escenario y robustez

**Lo que ya está:**

| Para el capítulo | Archivo | Comentario |
|---|---|---|
| IS por profundidad y global, con diferencia, IC, p y ranking | `data/analysis/3_2_2/tabla_90.{csv,md,tex}` | Es la tabla principal (slippage crudo) |
| Lo mismo con costo ajustado (+30 bps) | `tabla_90_ajustado.*` | Robustez. Global −3,53 [−15,93; 9,47] |
| Media, mediana, peor, mejor y cumplimiento por estrategia y bloque | `agregados_por_escenario.csv` | En limpio en `docs/consolidacion_3_2_2_BF.md`, sección 5.2 |
| Chequeo de calidad y corridas bajo el 95 % | `calidad.md` | Sale directo como tabla de cumplimiento |
| Eje de tamaño (0,5 / 1 / 1,5) | `tabla_tamanos.*` y `tabla_tamanos_ajustado.*` | Con el descriptivo sin los días bajo el 95 % (consolidación, sección 5.3) |
| Cortes por tramo y activo | `por_tramo.csv` y `por_activo.csv` | Descriptivos y confundidos entre sí. Encajan mejor en el capítulo 8 de PS |
| Cajas por profundidad | `data/colab_resultados/corridas_90/{baja,media,alta}/tabla/cajas.png` | Son versiones de trabajo, cada una con su propia escala |

**Lo que falta:**
1. **Una figura de cajas por profundidad y estrategia con el mismo eje** (3 × 3). La guía de PS se la asigna a BF y la tiene «⏳». Hoy `data/analysis/3_2_2/cajas.png` junta las tres profundidades.
2. **Una tabla LaTeX para el informe.** `tabla_90.tex` no sirve tal cual:
   - tiene 18 columnas con nombres internos (`IS_PPO_sistema`, `dif_vs_TWAP_ic`);
   - usa punto decimal;
   - las filas van en orden alfabético (`alta`, `baja`, `media`);
   - trae el carácter «×», que pdflatex no compila sin configuración.

   Hace falta una versión reducida: profundidad ×4 / ×1 / ×0,25 / global, IS de las tres estrategias, diferencia con IC y p.
3. **Una figura del costo según el tamaño con los tres puntos.** La de PS (`data/analysis/cap7/costo_vs_tamano_parcial.png`) solo tiene 0,5 y 1. Le toca a PS o a MR; hay que avisarles.
4. **Coordinar con PS:** el capítulo 8 (PS) ya interpreta Wilcoxon, Holm, Pitman-Morgan y los cortes. El 7 debería informar los resultados sin repetir esas pruebas.

### 3.2 Capítulo 6, «Entrenamiento y experimentación»: montaje experimental, curvas y convergencia

- **Lo que aporta la 3.2.2: el montaje de la evaluación.**
  - 10 meta-órdenes, cada una el 10 % del volumen del día (el 5 % si parte en el cierre), con semillas 4–6.
  - 3 profundidades del market maker y 3 tamaños en estrella.
  - El sistema `sistema_final`, con `seed_red` 1000, modo muestreo y `completar_al_cierre`.
  - Snapshot 2026-08-23 e impacto y = 0,5, τ = 120 min. Todo esto está en la firma de cada JSON.
- **Lo que no está:** las curvas de aprendizaje y de KL. Según la guía, las genera MR desde `data/colab_resultados/sistema_final/maestro/entrenamiento_maestro.csv` y `data/colab_resultados/rimit/d3_opcion0_s1000/`, y los dos archivos están en el repo. Hay que acordar con MR quién hace las figuras y si el 6 y el 7 quedan como un solo capítulo (la guía lo deja abierto).

## 4. Correcciones que entran en este PR

1. **`docs/consolidacion_3_2_2_BF.md`** quedó desactualizado después de los PR #57 y #59.
   - **Lo que decía:** el estado «falta el 1,5»; calidad y estrategias sin la ×0,25 ni el 1,5; cortes con 60 días; límites de «60 días».
   - **Un número mal:** el costo ajustado global decía −3,31 / −2,99, y `tabla_90_ajustado.csv` dice **−3,53 / −3,06**.
   - **Lo que se hizo:** se reescribió con los números de los archivos. Se agregó la verificación de que todo `data/analysis/3_2_2/` se reproduce exacto desde main.
2. **«El sistema completa siempre»**, que decían la consolidación del 13 nov y la lista de puntos para el capítulo 7, **ya no es cierto.**
   - Con tamaño 1 completa siempre con ×4, y el mínimo es 98,6 % con ×1 y 94,7 % con ×0,25.
   - Con el tamaño 1,5 queda bajo el 95 % en 4 días de cierre de FALABELLA (mínimo 78,4 %), y en esos días completa menos que TWAP.
3. **El tamaño 1,5 sin los días bajo el 95 %** (descriptivo, fuera del plan): sistema − TWAP = −5,06 [−23,50; 14,76], n = 25, contra −7,88 con todos.
   - La tendencia por tamaño se mantiene, pero más débil de lo que dice «mejora de forma monótona» en `docs/tamanos_media_f15_resultado_MR.md`.
   - El ajuste de +30 bps no lo corrige, porque dejar saldo sigue saliendo barato.
4. **`docs/tamanos_media_f05_resultado_BF.md`** y el apartado 12.4 de la **desviación 12**: se agregó el 1,5 y se cerró el estado (diseño en estrella completo).

## 5. Trabajo local sin PR (por decisión de BF)

La rama `feature/bf-poisson-tercios` (`f591abe`, 11 nov) no se subió. Contiene:
- **Snapshot 2026-11-11:** solo los reportes. El respaldo `snapshot_2026-11-11.zip` está en Drive (`slippage_colab/`).
- **Calibración Poisson por tercios de volumen diario:** 115 días por activo. λ del tercio alto es 2,0 a 3,7 veces la del bajo.
- **Reglas fijas α = 10–50 % por tercio:** 1.500 corridas, criterio fijado antes de correr. La mejor α admisible es **0,5 en los tres** (24,5 / 23,9 / 20,9 bps), así que el veredicto es **SE DETIENE**: no se reentrena el Maestro.
- **Cambio de criterio declarado:** se exige que la regla complete la orden. Una prueba de 30 corridas mostró que con α bajo la orden no se completa y parece barata.

Sirve para la discusión del capítulo 8 («¿por qué el Maestro usa siempre α = 0,5?»). Si el equipo lo quiere citar, la rama se sube en un PR aparte.

## 6. Lo que sigue (Sprint 8, 23 nov al 4 dic)

| Qué | Quién | De qué depende |
|---|---|---|
| Capítulo 7: tabla LaTeX reducida y figura de cajas 3 × 3 (sección 3.1, puntos 1 y 2) | BF | Nada: los datos están en main |
| Capítulo 6: montaje experimental y curvas de entrenamiento | BF y MR | Acordar quién hace las curvas |
| Figura del costo según el tamaño con 3 puntos y sección 8.6.3 | PS / MR | La 3.2.4 de MR |
| Decidir si se sube `feature/bf-poisson-tercios` | Equipo | — |

---

Elaborado por BF con apoyo de Claude Code (uso de IA autorizado por la universidad).
