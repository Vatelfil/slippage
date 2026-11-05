# Maestro v2: el Maestro mira el mercado simulado (4 de noviembre)

**Quién:** PS, con apoyo de Claude Code. Es una mejora que **se presenta aparte**: el resultado oficial de la 3.2.3 sigue siendo el del sistema del Sprint 6, con las 90 corridas.

## Qué estaba mal

Revisando el código (`docs/qa_sistema_media_90_PS.md` y la revisión del 4 de noviembre) aparecieron tres problemas:

1. **El Maestro no veía el mercado.**
   - `volatilidad` y `vol_promedio` entraban con un valor fijo (0,002 y 0,2), tanto al entrenar (`tabla_desde` en `src/training/maestro_trainer.py`) como al evaluar (`VOL_CONSTANTE` en `scripts/colab/evaluar_sistema_ps.py`).
   - `OBI_agregado` valía 0 desde el Sprint 2.
   - Los datos reales de la 1.2.2 (BF) existen, pero son de la Bolsa real, no del mercado simulado en que compra el Maestro. Además, al promediarse por hora le habrían dado casi la misma información que la hora.
2. **El Maestro se entrenó sin la corrección del cierre**, así que aprendió a comprar siempre el máximo (α = 0,5 en el 98 % de las decisiones).
3. **`n_slices` partía en 0 sobre 13** aunque la orden empezara a las 14:00.

Los valores fijos de los puntos 1 y 2 estaban en borradores de PS y Claude Code del Sprint 6, escritos para que el sistema corriera. Quedaron como «límite conocido» en el encabezado del evaluador, pero no se marcaron como algo pendiente que había que decidir.

## Qué se cambió

Todo está detrás de opciones que vienen apagadas por defecto, así que lo anterior se reproduce igual.

| Opción | Dónde | Qué hace |
|---|---|---|
| `sm_mercado` | `MaestroEjecutorEnv` | Después de cada ventana resume lo que vio el Ejecutor (sus S_E): **volatilidad**, la desviación de P_mid en bps dividida por 50; **profundidad**, el volumen medio de los 10 niveles del libro, en `vol_promedio`; y **desbalance**, el OBI_t medio, en `OBI_agregado`. En la siguiente decisión el Maestro ve esos tres valores. Además, `n_slices` se cuenta sobre las decisiones que tiene esa orden |
| `completar_al_cierre` | `ConfigJornada` | La corrección del cierre se aplica también al entrenar |
| `--sm-mercado`, `--completar-al-cierre` | `scripts/entrenar_maestro.py` | Activan lo anterior |
| `--sm-mercado` | `scripts/colab/evaluar_sistema_ps.py` | Evalúa con S_M medido (va con el Maestro v2) |
| `--referencias` | `scripts/comparacion_estadistica_3_2_3.py` | Permite comparar el Maestro v2 con el anterior: `--referencias PPO_sistema TWAP VWAP` |

**Por qué medirlo así:** es información del mismo mercado en que se compra, y la conoce el sistema en el momento de decidir (sale de la ventana anterior, no del futuro). Cambia el contrato de S_M (`SM_schema.json` dice yfinance), así que se declara como desviación.

## Cómo se corre

- **Cuaderno:** `notebooks/Colab_maestro_v2.ipynb`. «Ejecutar todas», ≈ 3 h.
  - Entrena 2.000 jornadas en Poisson, con λ = 0,02, impacto, inicio sorteado y los mismos Ejecutores del sistema final (≈ 40 min; una jornada tarda ≈ 1 s).
  - Evalúa en ABIDES la liquidez media con las semillas 4 a 6, las mismas de las 90 corridas.
- **Comparación:** Maestro v2 contra el Maestro anterior, TWAP y VWAP, en los mismos días. También muestra cómo se reparten las decisiones del Maestro nuevo.
- **Prueba corta local** (60 jornadas, Ejecutores sin entrenar): corre en 76 s y el α medio queda en ≈ 4,4 (≈ 25 %), no pegado en el máximo. No sirve como resultado: solo muestra que el arreglo funciona.

## Qué falta

- Correr el cuaderno (PS) y analizar el zip `maestro_v2_media.zip`.
- Que MR revise el borrador, porque el entrenamiento es su tarea (2.3.2 y 3.1.1).
- Si el Maestro v2 se usa en el informe, presentarlo como una versión mejorada, con su propia comparación, sin reemplazar el resultado oficial.
