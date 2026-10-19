# Decisión D3: ¿qué hacemos con el término de riesgo de R_E?

**Elaborado por:** PS con apoyo de Claude Code. **Para:** BF (responsable de la 2.2.3), con MR y PS. **Fecha límite de la decisión:** miércoles 14 de octubre, 18:00. **Si no hay respuesta rige la propuesta de PS (opción 0, abajo).**

## Resolución (14 de octubre de 2026, 18:00)

No hubo respuesta de BF dentro del plazo. Por lo acordado, **rige la opción 0**: se mantiene la fórmula del Título I, β = 0,0061796 y la regla de vigilancia (si en la 2.3.5 el cumplimiento de la orden baja del 95 %, se pasa a la opción A). No hay cambios de código. La revisión final es el viernes 23 de octubre. BF puede objetar antes del congelamiento del simulador (lunes 19, 18:00); pasada esa fecha queda firme para el sprint.

## Qué dice el Título I

§4.2.4: `R_E = (P_mid − P_ejec)·q_ejec − β·σ²·q_ejec`, con `q_ejec` la cantidad **ejecutada en el paso**, el segundo término como penalización de "riesgo temporal" y β como "coeficiente de aversión al riesgo (calibrar en el Sprint 4)". Es decir: la fórmula incluye el riesgo sobre lo ejecutado y pide **calibrar β**. Que la orden se complete es trabajo del Maestro (penalización λ·Q_pendiente al final), no del Ejecutor.

## Qué mostró la calibración (fase 2 de β, PPO en ABIDES, apertura, 300 episodios por β, 30 semillas de evaluación)

| β | Slippage (bps) | Orden completada |
|---|---:|---:|
| 0 (control) | 5,12 | 97 % |
| 0,1 × β\* | 4,71 | 100 % |
| 0,3 × β\* | 5,77 | 34 % |
| 1 × β\* | no ejecutó nada | 0 % |

Con β alto la red aprende a **no operar**: el castigo solo existe cuando ejecuta, así que no operar sale gratis. No es un error de código: es una propiedad de la fórmula del Título I. Dice cuánto riesgo se puede cobrar: **poco**. Con 0,1 × β\* el término de riesgo pesa alrededor de un 7 % de R_E y la red sigue completando la orden. Es la calibración que el Título I pedía.

Límites de esa calibración: una sola semilla de red, solo el tramo apertura y la diferencia de slippage con β = 0 (4,71 frente a 5,12 bps) está dentro del error estándar.

## La propuesta de PS (opción 0, la más fiel al Título I)

1. **Mantener la fórmula del Título I sin cambios.**
2. **Mantener β = 0,0061796** (0,1 × β\*), que ya está en `market_params.py`. Es la calibración que pide el Título I: el β más grande que no impide completar la orden.
3. Declarar el límite (término de riesgo débil; una semilla; solo apertura).
4. **Regla de vigilancia fijada antes de ver datos:** en el entrenamiento inicial (2.3.5) se mide el cumplimiento de la orden. Si baja del 95 %, se pasa a la opción A, que ya está implementada y probada en `main` (`riesgo_sobre="pendiente"`), y se anota como desviación del Título I **justificada con datos**.
5. **Revisión al final del Sprint 5 (viernes 23 de octubre):** con los resultados de la 2.3.5 se confirma si se mantiene la opción 0 o se cambia a la A.

## Las demás opciones, frente al Título I

| Opción | Qué es | Frente al Título I |
|---|---|---|
| 0 (propuesta) | Fórmula igual, β = 0,0061796, con regla de vigilancia | Fiel: calibra β como se pedía |
| A | Riesgo sobre el inventario pendiente: `R_E,t = (P_mid − P_ejec)·q_t − β·σ²_t·Q_pend,t` | Cambia lo que significa `q`: desviación que hay que justificar. Hay que recalcular β\* y repetir la fase 2 (≈ 1–2 h de Colab) |
| B | Fórmula igual con β = 0 | Mantiene la fórmula escrita pero apaga el término de riesgo; peor que la opción 0 |
| C | β = 0,1 × β\* más premio o castigo de cumplimiento | Agrega un término que el Título I no tiene |

## Estado del código

- La opción A está implementada y apagada por defecto en `reward_utils.py`, el fallback de Poisson, `abides_bridge.py` y `abides_ejecutor_env.py`, y en el barrido (`beta_sweep.py`) y la fase 2 (`beta_fase2_ppo.py --riesgo-sobre pendiente --beta-star ...`). La parte de ABIDES falta probarla en Colab.
- Con la opción 0 no hay que cambiar nada en el código.

## Qué se pide a BF

Responder en el grupo con una línea: **"D3: 0"** (confirmar la propuesta), **"D3: A"**, **"D3: B"** o **"D3: C"**.
