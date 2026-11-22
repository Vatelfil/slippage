# Capítulo 7, «Resultados y evaluación»: figuras y tablas (20 de noviembre)

**Responsable:** BF (4.1.2, Sprint 8). **Script:** `scripts/figuras_tablas_capitulo7_BF.py`. **Salidas:** `data/analysis/capitulo7_BF/`. **Tests:** `tests/test_figuras_tablas_capitulo7_BF.py`.

Son los dos pendientes de la sección 3.1 de `docs/review_sprint7_BF.md`: la figura de cajas 3 × 3 con el mismo eje y la tabla LaTeX para el informe. Se agregó también la tabla de cumplimiento.

## 1. Qué hay

| Archivo | Qué muestra | Fuente |
|---|---|---|
| `cajas_profundidad.png` | Costo por corrida en las 3 profundidades × 3 estrategias, con tamaño 1 y el mismo eje y. Cada panel indica n, sistema − TWAP y su p de Wilcoxon (criterio de la profesora, 6 nov; agregado el 22 nov) | `3_2_2/corridas.csv` y `3_2_2/tabla_90.csv` |
| `tabla_profundidad.{tex,md}` | IS por estrategia, sistema − TWAP y sistema − VWAP con IC 95 % y p de Wilcoxon, por profundidad, global y global sin días bajo el 95 % | `3_2_2/tabla_90.csv` |
| `tabla_tamanos.{tex,md}` | Lo mismo para el eje de tamaño (0,5 / 1 / 1,5) con profundidad ×1 | `3_2_2/tabla_tamanos.csv` |
| `tabla_cumplimiento.{tex,md}` | Cumplimiento mínimo y corridas que llegan al 95 %, por bloque y estrategia | `3_2_2/corridas.csv` |
| `tabla_estrategias.{tex,md}` (22 nov) | Media, mediana, desviación, peor, mejor y cumplimiento mínimo por profundidad y estrategia | `3_2_2/corridas.csv` |
| `cifras_capitulo7_BF.json` (22 nov) | Las cifras que cita el texto del capítulo: días ganados, variantes del tamaño 1,5 y cortes | `3_2_2/` (mismo bootstrap y Wilcoxon que la 3.2.2) |

- **No hay cálculos estadísticos nuevos.** Las cifras se copian de las salidas de la 3.2.2 y solo cambia el formato: coma decimal, filas en el orden ×4 / ×1 / ×0,25 y `$\times$` y `$-$` en vez de caracteres Unicode. Un test verifica que coinciden.
- **Lo que se calcula aquí, a partir de `corridas.csv`:**
  - los conteos de cumplimiento;
  - la distribución por estrategia (media, mediana, desviación, peor y mejor);
  - los días ganados;
  - la variante del tamaño 1,5 sin días bajo el 95 %.

  Se usan el mismo bootstrap y el mismo Wilcoxon que la 3.2.2, importados de su script.

## 2. Cómo usarlo en el informe

```latex
% en el preámbulo: \usepackage{graphicx} (las tablas no necesitan paquetes extra)
\input{data/analysis/capitulo7_BF/tabla_profundidad.tex}
\input{data/analysis/capitulo7_BF/tabla_tamanos.tex}
\input{data/analysis/capitulo7_BF/tabla_cumplimiento.tex}
\input{data/analysis/capitulo7_BF/tabla_estrategias.tex}

\begin{figure}[htbp]
  \centering
  \includegraphics[width=\textwidth]{data/analysis/capitulo7_BF/cajas_profundidad.png}
  \caption{Costo por corrida (slippage contra el precio de llegada, bps) según la profundidad del market maker,
  tamaño 1. Caja: cuartiles; línea: mediana; rombo: media; bigotes: 1,5 veces el rango intercuartil; círculos:
  corridas fuera de los bigotes. 30 corridas por caja (10 órdenes $\times$ 3 semillas).}
  \label{fig:cajas_profundidad}
\end{figure}
```

Las tablas no se editan a mano. Si cambia la 3.2.2, se vuelve a correr:

```bash
python scripts/figuras_tablas_capitulo7_BF.py
python -m pytest tests/test_figuras_tablas_capitulo7_BF.py -q
```

## 3. Decisiones de formato

- **Colores:** los mismos de las figuras de PS para el capítulo 8 (`scripts/figuras_estadisticas_4_1_4_PS.py` y `scripts/figuras_capitulo7_PS.py`): sistema verde `#0B6E64`, TWAP gris `#7A7A7A` y VWAP ocre `#B07D2B`. Así cada estrategia tiene el mismo color en todo el informe.
  - El validador de paletas marca que el gris y el ocre se parecen (ΔE 12,4) y que el verde y el gris se confunden con protanopía (ΔE 6,6).
  - Por eso **el color nunca va solo**: cada caja lleva el nombre de la estrategia y su media debajo, y el orden es siempre el mismo. En blanco y negro la figura se sigue leyendo.
- **Mismo eje en los tres paneles**, para comparar profundidades. Los valores extremos (de −378 a +523 bps) se muestran como círculos, sin cortar el eje.
- **La leyenda va en el `\caption`** y no dentro de la figura, para que se ajuste al ancho de la página.

## 4. Estado (22 nov)

1. **El texto:** hecho, en `docs/capitulo7_resultados_BF.md`.
2. **Coordinar con PS:** hecho. El 7 informa y el 8 interpreta, y el 7 remite a las secciones 8.3, 8.4.2, 8.4.3, 8.6.2 y 8.6.3.
3. **La figura del costo según el tamaño con los tres puntos:** hecha por PS en el PR #63 (`data/analysis/cap7/costo_vs_tamano.png`).

---

Elaborado por BF con apoyo de Claude Code (uso de IA autorizado por la universidad).
