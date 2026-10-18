# Revisión de BF del cierre del Sprint 4

**Elaborado por:** BF con apoyo de Claude Code, 18 oct 2026. Responde a `PROMPT_PARA_BENJAMIN_CIERRE_SPRINT4.md`.

## 1. Ramas de PS

Las cinco ramas de la sección 1 del prompt ya estaban en `main` (PR #27, `feature/ps-cierre-sprint4`) cuando se hizo esta revisión, así que se revisó el código mergeado.

| Rama | Revisión |
|---|---|
| `feature/ps-2.2.5-informe-final` | Conclusiones aceptadas: el simulador calibrado no pasa el criterio literal; escala y patrón entre tramos sí calzan; volumen alto y spread bajo son los límites. |
| `fix/ps-poisson-nivel-limite` | Cambio confirmado. El barrido de β en Poisson se regeneró (§2). |
| `feature/ps-2.1.2-fabrica-redes` | Ratificada con una corrección (§4). |
| `feature/ps-2.2.3-beta-fase2-v2` | La regla de selección se fijó antes de ver datos y se aplicó como estaba escrita. Resultado aceptado como provisional. |
| `feature/ps-2.2.4-megashock-probe` | Ningún candidato cumple la regla de adopción. Se cierra: los megashocks no resuelven la diferencia de colas. |

**Error encontrado (para PS):** `src/analysis/validacion_formal.py:366` usa `boxplot(tick_labels=...)`, que existe desde matplotlib 3.9. `requirements.txt` fija `matplotlib==3.8.3`, así que en local fallan `test_validacion_formal.py::test_comparar_antes_despues_y_figuras` y `test_validacion_informe.py::test_pipeline_completo_genera_json_figura_e_informe` (en Colab pasa porque trae una versión más nueva). Arreglo: usar `labels=` o subir la versión fijada. No se tocó porque `src/analysis/` es de PS.

## 2. Barrido de β en Poisson (2.2.3)

Regenerado con el simulador corregido: `data/calibration/beta_sweep_poisson_2026-10-18.json` (20 semillas, nivel pasivo 0). El de 2026-10-09 quedó marcado como obsoleto (clave `obsoleto` en el JSON).

- β\* = 0,6077 (antes 0,5917, +2,7 %). Rango admisible igual: 0,1 a 3 β\*.
- La política pasiva ya no se llena siempre: cumplimiento 80 / 90 / 80 % por tramo (antes 100 / 100 / 95 %).
- La conclusión no cambia: β\* del fallback lo fija el prior de σ², así que el fallback no sirve para calibrar el nivel de β.

Detalle en `docs/recompensa_ejecutores_2.2.3_BF.md` §5.1.

## 3. Decisión D3 (qué mide el riesgo en R_E)

El plazo era el 14 oct y, sin respuesta, rige la opción 0 de PS: fórmula del Título I sin cambios, β = 0,0061796, con la regla de vigilancia (si el cumplimiento baja del 95 % en la 2.3.5, se pasa a la opción A, riesgo sobre lo pendiente). **Pendiente: BF debe confirmarlo en el grupo con "D3: 0" o elegir otra opción.** El β definitivo se fija el 23 oct, con β por tramo (P5) y los resultados de la 2.3.5.

## 4. Redes de los Ejecutores (2.1.2)

Ratificada. Dimensiones verificadas contra los entornos. Se mantiene la cabeza totalmente discreta (240 logits) como desviación declarada.

Corrección: la fábrica no estaba conectada. Sin `executor_policy_fn`, `MaestroEjecutorEnv` usaba una sola red para los tres tramos. Se agregó `make_executor_policy_fn()` en `src/models/networks_factory.py`, con su test. También se corrigió el conteo de parámetros de la nota (61 680 en la cabeza, no ≈ 66 mil). Detalle en `docs/desviaciones_2.1.2.md`.

## 5. Calibración de `rmsc04` (2.2.4)

**Spread: se acepta como límite documentado.** No hace falta probar otra vez `mm_window_size` fijo: el primer sondeo de §8.1 de `docs/calibracion_rmsc04_2.2.4_BF.md` ya lo midió (ventana 30 → 0,50 bps, ventana 90 → 0,34 bps, contra 5,7–35 bps de objetivo). La ventana fija no mueve el spread y sí rompe la volatilidad (14,4 bps con ventana 30). En la grilla de 27, las combinaciones con ventana 30 y 90 tuvieron más pérdida que la ganadora.

**Volumen: grilla de actividad hacia abajo (corrida en Colab el 18 oct).** `scripts/colab/grid_specs/bf_falabella_actividad_baja.json` deja `mm_pov` = 0,005 (la config ganadora) y escala `num_noise_agents` y `lambda_a` juntos por 1 / 0,75 / 0,5 / 0,25 (4 configuraciones). El nivel 1 repite la config calibrada como control.

```bash
PYTHONPATH=. python scripts/colab/rmsc04_grid_search.py --ticker FALABELLA --snapshot 2026-08-23 \
    --seeds 3 --grid-spec scripts/colab/grid_specs/bf_falabella_actividad_baja.json \
    --out-dir <carpeta NUEVA en Drive>
```

La carpeta de salida tiene que ser nueva: el archivo se llama igual que el de la grilla de 27 (`rmsc04_grid_FALABELLA_2026-08-23.json`) y, como la firma no coincide, se sobrescribiría sin aviso.

**Regla de adopción, fijada antes de ver datos:** se adopta el nivel de menor pérdida solo si la volatilidad queda a ±15 % del objetivo en los tres tramos y ningún tramo pasa de 200 bps.

**Resultado (corrida del 18 oct, 4 × 3 semillas):** el nivel de menor pérdida es el control ×1 (9,83), es decir, la config ya calibrada; **no se adopta ningún nivel y no hace falta validar**. ×0,75 baja el exceso de volumen de la apertura de +43 % a +28 %, pero empata con el control sin el spread (0,565 contra 0,573) porque pierde volatilidad; ×0,5 triplica la volatilidad de la tarde y ×0,25 rompe el mercado. **El volumen alto queda como límite demostrado.** Detalle en `docs/calibracion_rmsc04_2.2.4_BF.md` §8.4; datos en `data/calibration/rmsc04_grid_actividad_baja_FALABELLA_2026-08-23.json`.

## 6. Lo que queda pendiente

- [ ] BF: confirmar D3 en el grupo.
- [x] BF: correr la grilla de actividad en Colab y aplicar la regla de §5 (18 oct: límite demostrado).
- [ ] PS: arreglar `tick_labels` o la versión de matplotlib (§1).
- [ ] PS o BF: β en media jornada y cierre (P5, 20–22 oct).
