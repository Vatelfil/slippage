# Distribución de la recompensa R_E (2.2.3)

**Elaborado por:** PS con apoyo de Claude Code. **Pendiente de revisión por:** BF.

Fuente: `beta_sweep_abides_2026-10-10.json` (políticas heurísticas en ABIDES calibrado; 20 episodios por tramo y política). β\* = 0,0618 (1/CLP). R_E por episodio en CLP por acción del slice (escala `por_accion_slice`, slice de 1000 acciones).

| Tramo | β | n | Media | Desvío | Asimetría | Curtosis (exceso) | p05 | p50 | p95 | % fuera de ±3σ |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| apertura | 0,0×β* | 60 | -1,175 | 2,756 | -3,25 | 14,82 | -5,049 | -0,657 | 0,895 | 1,7 |
| apertura | 0,1×β* | 60 | -1,386 | 2,768 | -3,25 | 14,71 | -5,303 | -0,785 | 0,607 | 1,7 |
| apertura | 0,3×β* | 60 | -1,810 | 2,797 | -3,23 | 14,40 | -5,811 | -1,069 | 0,144 | 1,7 |
| apertura | 1,0×β* | 60 | -3,291 | 2,942 | -3,01 | 12,48 | -7,588 | -2,598 | -0,374 | 1,7 |
| media_jornada | 0,0×β* | 60 | -0,744 | 1,903 | -0,88 | 3,39 | -3,937 | -0,318 | 1,572 | 3,3 |
| media_jornada | 0,1×β* | 60 | -0,878 | 1,918 | -0,87 | 3,23 | -4,352 | -0,442 | 1,471 | 1,7 |
| media_jornada | 0,3×β* | 60 | -1,147 | 1,971 | -0,88 | 2,87 | -5,697 | -0,666 | 1,269 | 1,7 |
| media_jornada | 1,0×β* | 60 | -2,087 | 2,356 | -1,20 | 2,88 | -6,581 | -1,520 | 0,563 | 1,7 |
| cierre | 0,0×β* | 60 | -0,083 | 1,183 | -0,45 | 2,61 | -1,956 | -0,015 | 1,404 | 1,7 |
| cierre | 0,1×β* | 60 | -0,173 | 1,188 | -0,46 | 2,53 | -2,048 | -0,066 | 1,311 | 1,7 |
| cierre | 0,3×β* | 60 | -0,355 | 1,206 | -0,48 | 2,24 | -2,231 | -0,216 | 1,125 | 1,7 |
| cierre | 1,0×β* | 60 | -0,988 | 1,364 | -0,80 | 1,51 | -3,123 | -0,737 | 0,472 | 1,7 |

## Lectura

- La escala de R_E cambia mucho entre tramos (el desvío baja de la apertura al cierre) y la apertura tiene colas muy pesadas y asimétricas (curtosis en exceso ≈ 15, asimetría ≈ −3): sin normalizar, unos pocos episodios dominan el gradiente y un mismo coeficiente de aprendizaje no sirve igual para los tres Ejecutores. Media jornada y cierre son más moderados.
- El término de riesgo aumenta con β pero, con la fórmula actual, solo depende de lo ejecutado: con β alto la recompensa total de operar es peor que la de no operar (ver `docs/beta_fase2_apertura_PS.md`).
- El normalizador móvil deja la salida dentro de [-1, 1] en todos los casos: **sí**.
- Los episodios son pocos (20 por tramo y política); los cuantiles extremos son indicativos.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
