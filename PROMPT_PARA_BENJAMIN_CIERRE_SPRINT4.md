# Prompt para Benjamín — Cierre del Sprint 4 (10 oct 2026)

Copia todo lo que está bajo la línea y pégalo en tu sesión de Claude Code (o la IA que uses), parado dentro de tu clon de `slippage`, después de `git pull origin main`.

Documento elaborado por Paolo Sepúlveda (PS) con apoyo de Claude Code. Todo lo que dice "PS hizo" está en ramas ya subidas y pendiente de tu revisión: tú eres el responsable de 2.1.2, 2.2.3 y 2.2.4 y tienes que poder defenderlas.

---

## Contexto

Trabajo de título UTEM: sistema jerárquico de RL (PPO) con un Maestro y 3 Ejecutores sobre ABIDES-Gym (`rmsc04`); el simulador de Poisson es solo el plan B (Título I, 4.3.3). Equipo: Mauricio Reynoso (MR, redes/PPO), Benjamín Farias (BF, datos/calibración), Paolo Sepúlveda (PS, validación/documentación).

El Sprint 4 terminaba el 9 de octubre y PS decidió cerrar lo pendiente de todos para no arrastrarlo al Sprint 5 (12–23 oct). Por eso hay ramas de PS que tocan tus tareas. **Léelas antes de mergear; si algo te parece mal, corrígelo o avísale a PS.**

Reglas del repo: `main` está protegida; no se puede actualizar una rama ya subida (usa un nombre nuevo en cada push, por ejemplo `-v2`) y se abre PR por la web. Antes de subir: `python -m pytest -q` (hoy en main: 187 passed, 8 skipped).

## 1. Ramas de PS que debes revisar

| Rama | Qué trae | Qué te toca |
|---|---|---|
| `feature/ps-2.2.5-informe-final` | Informe de la validación formal 2.2.5 con 30 semillas por tramo (`docs/validacion_formal_2.2.5_PS.md`) y los JSON de las corridas en `data/colab_resultados/` | Leer los resultados (sección 2) y aceptar o discutir las conclusiones |
| `fix/ps-poisson-nivel-limite` | Corrige `PoissonLOBSimulator.execute_limit_buy`: el nivel de precio estaba invertido (0 llenaba siempre). Cambia `NIVEL_PASIVO["poisson"]` de 7 a 0 en `src/experiments/beta_sweep.py` | Confirmar el cambio. **Tu barrido `data/calibration/beta_sweep_poisson_2026-10-09.json` quedó con la convención antigua: regenerarlo o marcarlo como obsoleto** |
| `feature/ps-2.1.2-fabrica-redes` | `src/models/networks_factory.py` (Maestro + 3 Ejecutores independientes) y `docs/desviaciones_2.1.2.md` | **La 2.1.2 es tuya.** Ratificar o corregir. Decidir si se mantiene la cabeza totalmente discreta (240 logits) en vez de la híbrida del Título I |
| `feature/ps-2.2.3-beta-fase2-v2` | Fase 2 de la elección de β con PPO en ABIDES (`src/experiments/beta_phase2.py`, `scripts/colab/beta_fase2_ppo.py`) | Revisar la regla de selección (fijada antes de ver datos) y los resultados (sección 3) |
| `feature/ps-2.2.4-megashock-probe` | Sondeo de megashocks para acercar las colas de `rmsc04` a las reales (`src/experiments/megashock_probe.py`) | Ver la regla de adopción y, si un candidato la cumple, validarlo con 30 semillas por tramo |

Nota: la rama de los megashocks está construida sobre `feature/ps-2.2.5-validacion-formal-v2`, así que su PR arrastra esos cambios.

## 2. Resultado de la validación formal (2.2.5): lo que implica para tu 2.2.4

Con 30 semillas por tramo y 3 tramos, el simulador calibrado queda **NO VÁLIDO según el criterio literal del plan** (todos los p de KS y Mann–Whitney > 0,05):

- KS crudo: rechaza en los 3 tramos. Apertura y cierre quedan casi en el borde (D/D crítico 1,10 y 1,03); media jornada rechaza claro (1,75). Con la corrección de Holm, el KS crudo solo sigue rechazando en media jornada.
- Escala de los retornos: coincide (desvío sim/real entre 0,89 y 0,98; g de Hedges trivial). El patrón entre tramos (apertura más volátil, volumen creciente) también coincide.
- **Volumen mediano por vela demasiado alto**: +49 % en apertura, +22 % en media jornada, +5 % en cierre. Tu grilla `actividad` tenía los niveles 1000/2000/4000 agentes y el elegido fue el más bajo, así que el mínimo de la grilla sigue quedando alto.
- Volatilidad simulada entre 8 y 14 % bajo el objetivo real.
- Spread simulado ≈ 0,17 bps frente a 4–35 bps reales: sigue decenas de veces por debajo.
- Frente al simulador de fábrica la mejora es grande (D baja de 0,28–0,32 a 0,07–0,10).

**Lo que te pido en la 2.2.4 (Sprint 5, o ahora si alcanzas):**
1. Extender la grilla de actividad hacia abajo (por ejemplo `num_noise_agents` 500 y 250, con `lambda_a` escalado en la misma proporción) y ver si el volumen por vela baja al real sin romper la volatilidad.
2. Decidir sobre el spread: o se acepta como límite documentado, o se prueba `mm_window_size` fijo (30–90 ticks ≈ 5–15 bps, ya está en tu grilla `mm_liquidez`) y se mide el costo en los demás momentos.
3. Mirar el resultado de los megashocks (corrida C de PS). Regla fijada antes de los datos: se adopta un candidato solo si baja el D estandarizado medio al menos un 15 % respecto del megashock por defecto y la volatilidad del cierre queda a ±15 % del objetivo. Si ninguno la cumple, la tarea se cierra diciendo que los megashocks no resuelven la diferencia de colas.
4. No es obligatorio que pase el KS: es válido cerrar con "límite demostrado" si queda medido y documentado.

## 3. Resultado de la fase 2 de β (2.2.3)

Corrida con PPO en ABIDES calibrado, tramo `apertura`, 300 episodios de entrenamiento por β, 30 semillas de evaluación, β\* = 0,0618 (de tu barrido en ABIDES):

| β | Slippage (bps) | Cumplimiento |
|---|---:|---:|
| 0 (control) | 5,12 | 0,973 |
| 0,1×β\* | 4,71 | 1,000 |
| 0,3×β\* | 5,77 | 0,341 |
| 1×β\* | sin ejecuciones | 0 |

- Regla fijada antes de los datos: candidatos 0,1/0,3/1×β\*; cumplimiento ≥ 95 %; menor slippage si Wilcoxon pareado da p < 0,05, si no el central 0,3×β\*. Solo 0,1×β\* cumple el cumplimiento, así que queda como único candidato (β ≈ 0,0062), **provisional**: una sola semilla de red, un solo tramo, diferencia pequeña frente al control.
- **Hallazgo de diseño que tienes que decidir tú (con MR y PS):** con β alto la red aprende a **no operar**. La fórmula R_E = (P_mid − P_ejec)·q − β·σ²·q castiga el riesgo en proporción a lo **ejecutado**, así que no ejecutar sale gratis. Si el riesgo debe medirse sobre la cantidad **pendiente** (inventario expuesto), es un cambio de definición de R_E. PS no lo cambió.
- Falta repetir en `media_jornada` y `cierre` y fijar `BETA_RIESGO_EJECUTOR` en `src/config/market_params.py` (hoy 0). PS lo hace cuando terminen las corridas, a menos que prefieras hacerlo tú.

## 4. Qué NO hacer

- No cambies `src/analysis/` ni los informes de PS sin avisarle (son de él).
- No presentes como resultado final nada de esta lista: todo es "elaborado por PS con apoyo de Claude Code, pendiente de revisión por BF".

## 5. Lista corta de lo que le falta a tu parte

- [ ] Revisar y mergear (o corregir) las 5 ramas de la sección 1.
- [ ] Regenerar o marcar obsoleto el barrido de β en Poisson.
- [ ] 2.2.4: grilla de actividad hacia abajo, decisión sobre spread, resultado de megashocks.
- [ ] 2.2.3: decisión sobre qué mide el riesgo en R_E (ejecutado o pendiente) y β definitivo.
- [ ] 2.1.2: ratificar la fábrica de redes y su nota de desviación.
