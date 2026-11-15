# Informe final del Título II: guía de ensamblado (borrador)

**Preparado por:** PS, con apoyo de Claude Code, el 15 de noviembre de 2026.
**Para qué sirve:** juntar el informe completo cuando cada integrante termine su parte.
- Aquí solo se ordena dónde va cada capítulo, quién lo escribe y en qué estado está.
- **No contiene texto de los capítulos de MR ni de BF:** esos los escribe cada uno.
- El Word del informe no se toca hasta que el grupo decida armarlo.

**Estructura:** la del Título I, sección «Estructura informe final» (9 capítulos). El Excel (`plan-desarrollo-titulo-2.xlsx`) asigna los capítulos con otra numeración; aquí se muestra a qué corresponde cada uno.

---

## 1. Índice, responsables y estado

| Cap. (Título I) | Título | Tarea en el Excel | Responsable | Archivo | Estado al 15 nov |
|---|---|---|---|---|---|
| 1 | Introducción | — | **Sin asignar** | — | ⚠️ Por definir (ver sección 3) |
| 2 | Marco teórico y estado del arte | — | **Sin asignar** | — | ⚠️ Por definir. Se puede partir de la sección 4.1 del Título I |
| 3 | Definición del problema y análisis del entorno | — | **Sin asignar** | — | ⚠️ Por definir. Se puede partir de las secciones 4.1 y 4.3 del Título I y de la 1.2.2 (datos) |
| 4 | Diseño de la solución | 4.1.1 «Cap. 5 Metodología» (MDP, espacios, recompensas, PPO, CTDE) | MR | (lo define MR) | ⏳ Sprint 8 |
| 5 | Implementación del sistema | 4.1.1 «Cap. 5 Metodología» (simulador calibrado, pseudocódigo) | MR | (lo define MR) | ⏳ Sprint 8 |
| 6 | Entrenamiento y experimentación | 4.1.2 «Cap. 6 Resultados» (setup experimental, curvas de aprendizaje, convergencia) | BF | (lo define BF) | ⏳ Sprint 8 |
| 7 | Resultados y evaluación | 4.1.2 «Cap. 6 Resultados» (desempeño comparativo, por escenario, robustez) | BF | (lo define BF) | ⏳ Sprint 8 |
| 8 | Discusión y análisis crítico | 4.1.3 «Cap. 7 Análisis» | **PS** | `docs/capitulo8_analisis_PS.md` | ✅ Escrito. Falta 8.6.3 (tamaño; espera el 1,5 y la 3.2.4 de MR) |
| 9 | Conclusiones y trabajo futuro | 4.2.1 | **PS** | `docs/capitulo9_conclusiones_PS.md` | ✅ Borrador avanzado. Falta H6 (tamaño; espera a MR) |
| — | Bibliografía | — | Equipo | — | ⏳ Juntar las referencias de cada capítulo |
| — | Anexos: desviaciones del Título I | — | Equipo | `DESVIACIONES_TITULO1_VS_IMPLEMENTACION.md` | ✅ Existe (desviaciones 1 a 14) |

**Nota:** la división de los capítulos 4–5 (MR) y 6–7 (BF) es una propuesta para calzar el Excel con el Título I. MR y BF pueden decidir escribir un solo capítulo cada uno, y entonces el índice se ajusta.

## 2. Tablas y figuras (tarea 4.1.4, Sprint 9)

| Figura o tabla | Capítulo | Aporta | Archivo | Estado |
|---|---|---|---|---|
| Curvas de aprendizaje (loss y reward) y KL del Maestro y del Ejecutor | 6 | MR | (lo genera MR desde `sistema_final/maestro/entrenamiento_maestro.csv` y `rimit/d3_opcion0_s1000/`) | ⏳ |
| Cajas de costo por escenario, IS comparativo | 7 | BF | `corridas_90/*/tabla/cajas.png` y las de la 3.2.2 | ⏳ (existen versiones de trabajo) |
| Distribución de las diferencias sistema − TWAP (Wilcoxon, Shapiro) | 8 | PS | `data/analysis/figuras_4_1_4/histograma_diferencias_90.png` | ✅ |
| Costo por estrategia con prueba de varianzas (Pitman-Morgan) | 8 | PS | `data/analysis/figuras_4_1_4/costo_por_estrategia_varianzas.png` | ✅ |
| Diferencia media con IC 95 % por grupo (bosque) | 8 | PS | `data/analysis/3_2_3/bosque_diferencias.png` | ✅ |
| Diferencias por profundidad del market maker | 8 | PS | `data/analysis/3_2_3/diferencias_por_escenario.png` | ✅ |
| Q-Q de las diferencias | 8 | PS | `data/analysis/3_2_3/qq_diferencias.png` | ✅ |
| Aporte de cada nivel (control de reglas) | 8 | PS | `data/colab_resultados/control_reglas/media/analisis/control_reglas.png` | ✅ |
| Diferencia por tramo de inicio | 8 | PS | `data/analysis/cap7/diferencia_por_tramo.png` | ✅ (exploratoria) |
| Costo frente al tamaño | 8 | PS / MR | `data/analysis/cap7/costo_vs_tamano_parcial.png` | ⏳ Parcial; se reemplaza con la 3.2.4 de MR |

**Criterios para todas las figuras** (profesora, 6 de noviembre):
- título técnico, no una conclusión;
- si muestra una comparación inferencial, indica la prueba, el n y el valor p.

## 3. Puntos que el grupo tiene que decidir antes de ensamblar

1. **Capítulos 1, 2 y 3 sin responsable.**
   - El Excel no los asigna a nadie: solo asigna el 5 (MR), el 6 (BF), el 7 (PS) y las Conclusiones (PS).
   - Hay que repartirlos o acordar armarlos desde el Título I, que ya tiene ese contenido en las secciones 4.1, 4.2, 4.3 y 5.
2. **Numeración:** usar la del Título I (9 capítulos, como aquí) o la del Excel.
3. **Formato final:** quién pasa los Markdown al Word y con qué plantilla.
4. **Nombres de los escenarios:** en todo el informe se usa «profundidad del market maker ×4 / ×1 / ×0,25» (C-6c, desviación 10).

## 4. Lista de verificación final (antes de entregar)

- [ ] Los 9 capítulos tienen texto final.
- [ ] Las cifras son iguales en todos los capítulos (fuente: `docs/comparacion_estadistica_3_2_3_PS.md` y `data/analysis/3_2_2/`).
- [ ] Cada resultado inferencial tiene su prueba, n, valor p y cómo se calculó.
- [ ] Los títulos de las secciones y las figuras son técnicos.
- [ ] Cada alternativa probada tiene ventajas, desventajas y costos.
- [ ] Las desviaciones del Título I están citadas donde corresponde.
- [ ] Las secciones con [PENDIENTE] están completas (8.6.3 y H6, cuando llegue la 3.2.4).
- [ ] La bibliografía está unificada.
