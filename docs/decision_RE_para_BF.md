# Decisión D3: ¿qué mide el término de riesgo de R_E?

**Elaborado por:** PS con apoyo de Claude Code. **Para:** BF (responsable de la 2.2.3), con MR y PS. **Fecha límite de la decisión:** miércoles 14 de octubre, 18:00. Si no hay decisión rige la opción B.

## El problema, con números

Fórmula actual: `R_E = (P_mid − P_ejec)·q_ejec − β·σ²·q_ejec`. El riesgo se cobra solo sobre lo **ejecutado**.

En la fase 2 de β (PPO en ABIDES, apertura, 300 episodios por β, 30 semillas de evaluación; `docs/beta_fase2_apertura_PS.md`):

| β | Slippage (bps) | Cumplimiento de la orden |
|---|---:|---:|
| 0 (control) | 5,12 | 0,973 |
| 0,1 × β\* | 4,71 | 1,000 |
| 0,3 × β\* | 5,77 | 0,341 |
| 1 × β\* | sin ejecuciones | 0,000 |

Con β alto la red aprende a **no operar**: si no ejecuta nada, el término de riesgo vale 0 y el de precio también. No operar sale gratis. En el Maestro la penalización λ·Q_pendiente castiga no terminar, pero llega recién al final de la meta-orden y no le llega al Ejecutor.

## Las tres opciones

**A. Riesgo sobre el inventario pendiente.**
`R_E,t = (P_mid − P_ejec)·q_t − β·σ²_t·Q_pend,t` (Q_pend = lo que falta después del paso t).
- Quedarse con la orden sin ejecutar pasa a costar, en cada paso, en proporción a lo que falta y a la varianza reciente. Es la idea de riesgo de inventario de Almgren–Chriss.
- Ya está implementada y apagada por defecto: `riesgo_sobre="pendiente"` en `EjecutorEnvPoissonFallback`, `ExecutorRewardState` y `ExecutionEnv27` (ABIDES), con tests. Falta probar el pegamento con ABIDES en Colab (`src/envs/test_abides_ejecutor.py`).
- Costo: el riesgo se acumula en todos los pasos, no una vez, así que **β\* cambia de escala**. Hay que recalcular β\* con `Σ|precio| / Σ(σ²·Q_pend)` y repetir la fase 2 (aprox. 1 h de Colab para la apertura). Los barridos `step_record` y `summarize_episode` de `beta_sweep.py` necesitan guardar también Q_pend (cambio pequeño).
- Es una desviación de la fórmula del Título I si ahí q es la cantidad ejecutada. Hay que anotarla en `DESVIACIONES_TITULO1_VS_IMPLEMENTACION.md`.

**B. Mantener la fórmula y entrenar con β = 0.**
- Cero trabajo adicional y cero desviación; el control (β = 0) completó el 97 % de la orden con 5,12 bps.
- Pierde el término de riesgo: se declara como "no calibrado, β = 0 en el entrenamiento inicial" y se reevalúa en el Sprint 6.

**C. Mantener β = 0,1·β\* y agregar un bono o penalización de cumplimiento.**
- Funciona, pero agrega un término que no está en el Título I y un hiperparámetro nuevo sin base.

## Recomendación de PS

A si la decisión sale el miércoles 14 y se alcanza a repetir β antes del 20 de octubre; si no, B, para no bloquear la 2.3.5. La razón es que B no entrena nada sobre riesgo y A sí, y el Título I pide ese término.

## Qué cambia en el código según la decisión

| Decisión | Qué hace PS (jueves 15 – viernes 16) |
|---|---|
| A | Fijar `RIESGO_SOBRE_EJECUTOR = "pendiente"` en `market_params.py`, ajustar `beta_sweep.py` para Q_pend, rehacer β\* y la fase 2, actualizar tests y la nota de desviaciones |
| B | Fijar `BETA_RIESGO_EJECUTOR = 0.0` y dejar escrito el límite |
| C | Implementar el bono con un nombre propio y documentarlo |

**Responde en el grupo con una línea:** "D3: A", "D3: B" o "D3: C".
