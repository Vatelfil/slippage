# Leeme para MR: borradores del Maestro y del ajuste de hiperparámetros

**Rama:** `feature/ps-borrador-mr-maestro` (BORRADOR de PS para MR, 29 de octubre). Todo está escrito y probado en el PC con Poisson. Las decisiones de diseño son tuyas: cambia lo que quieras o recházalo.

## Qué hay

| # | Qué | Dónde | Tarea |
|---|---|---|---|
| M1 | **Bucle de entrenamiento del Maestro**: módulo nuevo, usa tu `PPOTrainer` con `role="maestro"` y tu `ppo_update` sin cambios. Ejecutores fijos; recompensa R_M pasada a bps | `src/training/maestro_trainer.py`, `scripts/entrenar_maestro.py` | Sprint 6–7 |
| — | **Impacto acumulado entre ventanas** (ver «Decisión de diseño») | `src/envs/impacto_acumulado.py`; opción `--impacto` en los evaluadores | Diseño del Maestro |
| M2 | **Checkpoint con estado aleatorio** (torch, numpy, random): reanudar da exactamente lo mismo que no cortar | `src/training/ppo_trainer.py` (`save_checkpoint`, `load_checkpoint`) | Hallazgo del Sprint 5 |
| M3 | **Barrido de hiperparámetros** 3.1.1 (rejilla lr × minibatch × épocas) y 3.1.2 (25 combinaciones aleatorias de ε y λ de GAE), con regla de selección fijada antes | `scripts/colab/grid_specs/hiperparametros_ejecutor_mr.json`, `scripts/barrido_hiperparametros_mr.py`; `--lr`, `--epochs`, `--minibatch`, `--clip`, `--gae-lambda` en `scripts/colab/entrenamiento_inicial_ps.py` | 3.1.1 y 3.1.2 |
| M4 | **Revalidación de λ** (P10) con la política entrenada | `scripts/revalidar_lambda_maestro.py` | P10 |
| M5 | **γ_E = 1** como valor por defecto del Ejecutor (`GAMMA_EJECUTOR`) y su registro como desviación | `src/training/ppo_trainer.py`, `DESVIACIONES_TITULO1_VS_IMPLEMENTACION.md` secciones 6 y 7 | — |
| M6 | **Cuaderno del Maestro**: entrena en Poisson y evalúa en ABIDES contra el mismo Maestro sin entrenar y TWAP/VWAP | `notebooks/Colab_Maestro_MR.ipynb` | — |

## Decisión de diseño: impacto acumulado

Hoy `MaestroEjecutorEnv` crea un mercado nuevo en cada ventana. Además, en ABIDES todas las ventanas de un tramo empiezan a la misma hora simulada. Lo que el sistema compra a las 10:00 no encarece lo de las 10:30, así que el Maestro no tiene nada que coordinar.

La propuesta es arrastrar el impacto con la ley de la raíz cuadrada:
- **Fórmula:** impacto = Y · σ_día · √(Q_efectiva / V_día), con decaimiento exponencial entre ventanas.
- **Parámetros:** Y = 0,5 y τ = 120 min, **supuestos de la literatura, no calibrados**.
- **Dónde se aplica:** como un envoltorio del entorno del Ejecutor, igual para el sistema y para TWAP/VWAP. No cambia `maestro_ejecutor_protocol.py`.
- **Por defecto:** viene apagado.
- **Por qué esta opción:** las alternativas son dejarlo como está (el Maestro no aporta) o simular de forma continua en ABIDES (cada ventana del cierre simularía más de 6 h previas, inviable en Colab gratis).

## Primer resultado (Poisson, medido en el PC)

El Maestro aprende a **completar la orden**: el cumplimiento sube de 0,959 a 0,999 y R_M mejora en 17 bps. Lo logra comprando más rápido, y por eso con λ = 0,05 **cuesta más que TWAP** (+2,85 bps con 400 jornadas, +1,82 con 2.000).

Con λ = 0,02 y 2.000 jornadas **empata con TWAP** (+0,36 bps, IC −0,08 a +0,83) y cumple el 99,4 %. Todavía no le gana.

Detalle en `docs/maestro_primer_entrenamiento_PS.md`. La decisión sobre λ es tuya.

## Cinco pasos

1. **Lee la decisión de diseño** de arriba y las secciones 6 y 7 de `DESVIACIONES_TITULO1_VS_IMPLEMENTACION.md` (15 min). Acepta, cambia o rechaza.
2. **Revisa** `src/training/maestro_trainer.py` (Ejecutores fijos, recompensa en bps, semillas) y el cambio de `ppo_trainer.py` (M2 y M5) (40 min).
3. **Corre las pruebas** (≈ 1 min):
   ```bash
   PYTHONPATH=. python -m pytest tests/test_maestro_trainer.py -q
   ```
4. **Barrido de hiperparámetros** en tu PC, solo después de que el cuaderno `Colab_mid_decision` confirme la recompensa corregida (≈ 2 h en Poisson):
   ```bash
   PYTHONPATH=. python scripts/barrido_hiperparametros_mr.py --fase 3.1.1 --out-dir data/barrido_hp
   ```
   Después, la fase 3.1.2 y la confirmación en ABIDES de las dos mejores configuraciones.
5. **Cuaderno del Maestro** en Colab: «Ejecutar todas», ≈ 2 h 30 min.

## Límites

- El impacto acumulado es un supuesto; conviene contrastar Y con dos ventanas seguidas en ABIDES si alcanza el tiempo.
- Los Ejecutores del Maestro están sin entrenar (los entrenados aún no bajan el costo; ver `docs/revision_opus_PS.md`).
- `OBI_agregado` del estado del Maestro sigue en 0 y `volatilidad` y `vol_promedio` son constantes si no se pasa la tabla de la 1.2.2.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
