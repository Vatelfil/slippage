# Sprint 4 (28 sep – 9 oct 2026): qué se hizo

Documento de seguimiento interno del equipo. Elaborado por PS con apoyo de Claude Code el 10 oct 2026; pendiente de revisión por BF y MR. No es parte del informe formal.

Estados usados: **Hecho** · **Hecho con límite demostrado** (se ejecutó y midió; el resultado no alcanza el criterio ideal y queda documentado por qué) · **Pasa al Sprint 5 por diseño** (se decidió no hacerlo ahora, con el costo medido).

## Tareas del sprint

| Tarea | Responsable | Estado | Qué hay |
|---|---|---|---|
| 2.2.1 PPO: L_CLIP y GAE | MR | Hecho | Redes y política reales conectadas al orquestador (`maestro_policy`, `executor_policy`); PR #20. PS: `torch` se importa solo al usarlo y semilla reproducible. |
| 2.2.2 Recompensa del Maestro | MR | Hecho con límite | λ = 0,05 elegido por escala con política **sin entrenar**. Provisional: revalidar al entrenar (Sprint 5–6). |
| 2.2.3 Recompensa de los Ejecutores | BF (+PS) | Hecho con límite | σ² causal normalizada y escala común (BF). Fase 2 con PPO en ABIDES, tramo apertura (PS): **β = 0,0061796** (0,1·β\*), provisional. |
| 2.2.4 Calibración de `rmsc04` | BF (+PS) | Hecho con límite | Calibración por tramo y validación con 30 semillas (BF). Sondeo de megashocks (PS): no mejora. |
| 2.2.5 Validación del simulador | PS | Hecho con límite | Validación formal con 30 semillas por tramo, antes y después de calibrar. |
| 2.1.2 Redes de los 3 Ejecutores (de Sprint 3) | BF | Hecho (por PS), por ratificar | Fábrica `make_hierarchy()` y nota de la cabeza totalmente discreta. |
| 2.3.4 Benchmarks TWAP/VWAP (adelantada de Sprint 5) | PS | Hecho | PR #19; TWAP 36.932 CLP de IS frente a VWAP 35.569. |

## Resultados clave

**2.2.5. El simulador calibrado NO es válido según el criterio literal del plan** (todos los p de KS y Mann–Whitney > 0,05):
- El KS crudo rechaza en los 3 tramos (apertura y cierre por muy poco: D/D crítico 1,10 y 1,03; media jornada claro: 1,75). Con la corrección de Holm solo sigue rechazando media jornada.
- La **escala** de los retornos coincide (desvío sim/real entre 0,89 y 0,98; tamaño de efecto trivial) y el **patrón entre tramos** también.
- El **volumen por vela** simulado es mayor que el real: +49 % apertura, +22 % media jornada, +5 % cierre.
- La volatilidad simulada queda 8–14 % bajo el objetivo; el spread simulado (≈ 0,17 bps) queda decenas de veces bajo el real (4–35 bps): el IS absoluto en ABIDES está subestimado, pero la **comparación entre políticas sigue siendo válida**.
- Frente al simulador de fábrica la mejora es grande (D del KS de 0,28–0,32 a 0,07–0,10).
- Informe completo: `docs/validacion_formal_2.2.5_PS.md`.

**2.2.4, megashocks.** Con el megashock por defecto casi no ocurren saltos. Al hacerlos más frecuentes la curtosis explota (17–175 frente a 3–6 reales) y el D empeora. Regla fijada antes de ver datos: ningún candidato la cumple. Se conserva la configuración de BF.

**2.2.3, β.** En la apertura solo 0,1·β\* completa el 95 % de la orden. Con 0,3× se ejecuta el 34 % y con 1× la red no opera: R_E castiga el riesgo en proporción a lo **ejecutado**, así que no ejecutar sale gratis. La diferencia de slippage entre 0,1× y β = 0 (4,71 frente a 5,12 bps) está dentro del error estándar, y TWAP con límite (4,06 bps) iguala o supera a las redes con este entrenamiento corto. Informe: `docs/beta_fase2_apertura_PS.md`.

## Correcciones de errores propios durante el sprint

- `PoissonLOBSimulator.execute_limit_buy` tenía el nivel de precio invertido (el nivel 0 llenaba siempre). Corregido, y `NIVEL_PASIVO["poisson"]` pasa a 0. El barrido de β en Poisson hecho antes queda obsoleto.
- `find_latest_clean_combined` fallaba con carpetas sin parquet. Corregido (PR #21).
- La corrida de β falló al imprimir cuando una política no ejecutaba nada. Corregido.

## Pasa al Sprint 5 por diseño

- β en media jornada y cierre: cada episodio debe simular desde la apertura; un β tarda ≈ 2 h en media jornada. Hay que reutilizar el calentamiento de la simulación o reducir episodios.
- Bajar el volumen simulado (grilla de actividad por debajo de 1000 agentes) y decidir sobre el spread.
- Decidir si R_E mide el riesgo sobre lo ejecutado o sobre el inventario pendiente (decisión de diseño de BF con MR y PS).
- Revalidar λ del Maestro con entrenamiento real.
- Unificar el corte de tramos (S_M a las 11:00, Ejecutores a las 11:30).

No era del Sprint 4 (solo como aclaración): el entrenamiento PPO completo de los 3 Ejecutores y del Maestro corresponde a los Sprints 5–6 (tarea 3.1.x). El Sprint 4 pedía implementar el PPO (2.2.1), no entrenarlo.

## Dónde está cada cosa

| Tema | Archivo |
|---|---|
| Informe de validación formal | `docs/validacion_formal_2.2.5_PS.md`; datos en `data/colab_resultados/` y `data/analysis/validacion_formal_2_2_5.*` |
| Fase 2 de β | `docs/beta_fase2_apertura_PS.md`; código `src/experiments/beta_phase2.py` |
| Sondeo de megashocks | `src/experiments/megashock_probe.py`; script `scripts/colab/megashock_probe_ps.py` |
| Fábrica de redes | `src/models/networks_factory.py`; `docs/desviaciones_2.1.2.md` |
| Instrucciones para las IA de BF y MR | `PROMPT_PARA_BENJAMIN_CIERRE_SPRINT4.md`, `PROMPT_PARA_MAURICIO_CIERRE_SPRINT4.md` |
