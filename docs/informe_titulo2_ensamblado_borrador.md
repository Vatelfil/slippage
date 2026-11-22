# Informe final del Título II: guía de ensamblado (borrador)

**Preparado por:** PS, con apoyo de Claude Code, el 15 de noviembre de 2026.
**Para qué sirve:** juntar el informe completo cuando cada integrante termine su parte.
- Aquí solo se ordena dónde va cada capítulo, quién lo escribe y en qué estado está.
- **No contiene texto de los capítulos de MR ni de BF:** esos los escribe cada uno.
- El Word del informe no se toca hasta que el grupo decida armarlo.

**Estructura:** la del Título I, sección «Estructura informe final» (9 capítulos). El Excel (`plan-desarrollo-titulo-2.xlsx`) asigna los capítulos con otra numeración; aquí se muestra a qué corresponde cada uno.

---

## 1. Índice, responsables y estado

**Capítulos 1 a 3:** ya los escribieron PS, MR y BF en conjunto en el Título I. El reparto por sprints empieza en el Capítulo 4.

| Cap. (Título I) | Título | Tarea en el Excel | Responsable | Archivo | Estado al 15 nov |
|---|---|---|---|---|---|
| 1 | Introducción | — (sale del Título I) | **Equipo (PS, MR y BF)** | Título I: resumen, objetivos y alcances | ✅ Hecho en conjunto (Título I) |
| 2 | Marco teórico y estado del arte | — (sale del Título I) | **Equipo (PS, MR y BF)** | Título I: secciones 4.1 y 4.2.3 | ✅ Hecho en conjunto (Título I) |
| 3 | Definición del problema y análisis del entorno | — (sale del Título I) | **Equipo (PS, MR y BF)** | Título I: secciones 4.1.3 y 4.3, y tarea 1.2.2 (datos) | ✅ Hecho en conjunto (Título I) |
| 4 | Diseño de la solución | 4.1.1 «Cap. 5 Metodología» (MDP, espacios, recompensas, PPO, CTDE) | MR | `docs/capitulo5_metodologia_MR.md` (Parte I) | ✅ Sprint 8 (MR) |
| 5 | Implementación del sistema | 4.1.1 «Cap. 5 Metodología» (simulador calibrado, pseudocódigo) | MR | `docs/capitulo5_metodologia_MR.md` (Parte II) | ✅ Sprint 8 (MR) |
| 6 | Entrenamiento y experimentación | 4.1.2 «Cap. 6 Resultados» (setup experimental, curvas de aprendizaje, convergencia) | MR (4.1.2 reasignada a MR) | `docs/capitulo6_entrenamiento_experimentacion_MR.md` | ✅ Sprint 8 (MR) |
| 7 | Resultados y evaluación | 4.1.2 «Cap. 6 Resultados» (desempeño comparativo, por escenario, robustez) | BF | `docs/capitulo7_resultados_BF.md` (tablas y figura en `data/analysis/capitulo7_BF/`) | ✅ Sprint 8 (BF, 22 nov). Reparto: el 7 informa los resultados; la interpretación estadística va en el 8 |
| 8 | Discusión y análisis crítico | 4.1.3 «Cap. 7 Análisis» | **PS** | `docs/capitulo8_analisis_PS.md` | ✅ Completo (8.6.3 con la 3.2.4 de MR verificada por PS: Friedman p = 0,039, Page p = 0,007) |
| 9 | Conclusiones y trabajo futuro | 4.2.1 | **PS** | `docs/capitulo9_conclusiones_PS.md` | ✅ Completo (H6 con la tendencia significativa en el orden, no en la magnitud) |
| — | Bibliografía | — | Equipo | — | ⏳ Juntar las referencias de cada capítulo |
| — | Anexos: desviaciones del Título I | — | Equipo | `DESVIACIONES_TITULO1_VS_IMPLEMENTACION.md` | ✅ Existe (desviaciones 1 a 14) |

**Nota:** la división de los capítulos 4–5 (MR) y 6–7 (BF) es una propuesta para calzar el Excel con el Título I. MR y BF pueden decidir escribir un solo capítulo cada uno, y entonces el índice se ajusta.

## 2. Tablas y figuras (tarea 4.1.4, Sprint 9)

| Figura o tabla | Capítulo | Aporta | Archivo | Estado |
|---|---|---|---|---|
| Curvas de aprendizaje (loss y reward) y KL del Maestro y del Ejecutor | 6 | MR | `data/analysis/cap6_MR/curvas_maestro.png` y `curvas_ejecutor.png` | ✅ |
| Cajas de costo por profundidad, IS comparativo | 7 | BF | `data/analysis/capitulo7_BF/cajas_profundidad.png` | ✅ |
| Distribución de las diferencias sistema − TWAP (Wilcoxon, Shapiro) | 8 | PS | `data/analysis/figuras_4_1_4/histograma_diferencias_90.png` | ✅ |
| Costo por estrategia con prueba de varianzas (Pitman-Morgan) | 8 | PS | `data/analysis/figuras_4_1_4/costo_por_estrategia_varianzas.png` | ✅ |
| Diferencia media con IC 95 % por grupo (bosque) | 8 | PS | `data/analysis/3_2_3/bosque_diferencias.png` | ✅ |
| Diferencias por profundidad del market maker | 8 | PS | `data/analysis/3_2_3/diferencias_por_escenario.png` | ✅ |
| Q-Q de las diferencias | 8 | PS | `data/analysis/3_2_3/qq_diferencias.png` | ✅ |
| Aporte de cada nivel (control de reglas) | 8 | PS | `data/colab_resultados/control_reglas/media/analisis/control_reglas.png` | ✅ |
| Diferencia por tramo de inicio | 8 | PS | `data/analysis/cap7/diferencia_por_tramo.png` | ✅ (exploratoria) |
| Costo frente al tamaño (0,5 / 1 / 1,5) | 8 | PS / MR | `data/analysis/cap7/costo_vs_tamano.png` y `data/analysis/3_2_4/sensibilidad_tamano.png` | ✅ |

**Criterios para todas las figuras** (profesora, 6 de noviembre):
- título técnico, no una conclusión;
- si muestra una comparación inferencial, indica la prueba, el n y el valor p.

## 3. Puntos que el grupo tiene que decidir antes de ensamblar

1. **Numeración:** usar la del Título I (9 capítulos, como aquí) o la del Excel.
2. **Formato final:** quién pasa los Markdown al Word y con qué plantilla.
3. **Nombres de los escenarios:** en todo el informe se usa «profundidad del market maker ×4 / ×1 / ×0,25» (C-6c, desviación 10).

## 4. Lista de verificación final (antes de entregar)

- [ ] Los 9 capítulos tienen texto final.
- [ ] Las cifras son iguales en todos los capítulos (fuente: `docs/comparacion_estadistica_3_2_3_PS.md` y `data/analysis/3_2_2/`).
- [ ] Cada resultado inferencial tiene su prueba, n, valor p y cómo se calculó.
- [ ] Los títulos de las secciones y las figuras son técnicos.
- [ ] Cada alternativa probada tiene ventajas, desventajas y costos.
- [ ] Las desviaciones del Título I están citadas donde corresponde.
- [x] Las secciones con [PENDIENTE] están completas (8.6.3 y H6, con la 3.2.4 de MR).
- [ ] La bibliografía está unificada.
