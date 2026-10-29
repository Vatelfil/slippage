# Primer entrenamiento del Maestro (Poisson, 29 de octubre)

**Elaborado por:** PS con apoyo de Claude Code (borrador para MR). Todo se midió en el PC con el simulador de Poisson y es **orientativo**: no reemplaza la evaluación en ABIDES (`notebooks/Colab_Maestro_MR.ipynb`).

## Qué se hizo

- Orden de 30.000 acciones de FALABELLA desde las 09:30.
- Ejecutores fijos, sin entrenar, muestreando su política.
- Maestro entrenado con `scripts/entrenar_maestro.py` (PPO de MR, γ = 0,99).
- Evaluación en 30 jornadas con semillas distintas de las de entrenamiento.
- Comparación contra el mismo Maestro sin entrenar y contra TWAP/VWAP en el mismo mercado, porque las semillas por ventana coinciden (`scripts/comparar_maestro_vs_twap_ps.py`).
- Impacto acumulado entre ventanas con Y = 0,5 y τ = 120 min, que es un supuesto.

Datos: `data/maestro/primer_entrenamiento_29oct/`.

## Resultados

| Corrida | R_M (bps): entrenado − sin entrenar | Cumplimiento (sin entrenar → entrenado) | IS del Maestro − TWAP (bps) | IS del Maestro − VWAP (bps) |
|---|---|---|---|---|
| Sin impacto, λ = 0,05, 400 jornadas | +17,1 [+10,1; +26,9] | 0,959 → 0,9995 | +4,18 [+3,98; +4,38] | +4,96 [+4,78; +5,16] |
| Con impacto, λ = 0,05, 400 jornadas | +17,3 [+10,7; +26,9] | 0,959 → 0,999 | +2,85 [+2,55; +3,15] | +3,61 [+3,29; +3,91] |
| Con impacto, λ = 0,05, 2.000 jornadas | +18,2 [+11,5; +27,8] | 0,959 → 0,999 | +1,82 [+1,34; +2,28] | +2,58 [+2,10; +3,04] |
| Con impacto, λ = 0,02, 2.000 jornadas | +6,7 [+4,2; +10,1] | 0,959 → 0,994 | **+0,36 [−0,08; +0,83]** | +1,12 [+0,67; +1,60] |

Referencia: el Maestro sin entrenar empata con TWAP con impacto (+0,06 bps), pero deja sin comprar el 4 % de la orden.

## Lectura

1. **El bucle funciona y el Maestro aprende.** Mejora su recompensa en todas las corridas, sobre todo porque aprende a completar la orden.
2. **Aprende a completar comprando más rápido, y eso cuesta.** Con λ = 0,05 cada acción sin comprar vale 500 bps, mucho más que el IS. La política sube α y paga más que TWAP, que también completa (99,97 %).
3. **Entrenar más ayuda:** de +2,85 a +1,82 bps contra TWAP al pasar de 400 a 2.000 jornadas.
4. **Bajar λ a 0,02 ayuda más:** el Maestro empata con TWAP (+0,36 bps, IC con el 0) y cumple el 99,4 %. Con λ = 0,02, la penalización del Maestro sin entrenar pesa entre un tercio y la mitad del IS (`scripts/revalidar_lambda_maestro.py`), dentro del rango de la 2.2.2.
5. **Todavía no le gana a TWAP.** Hipótesis, no probada: con Ejecutores entrenados con la recompensa corregida, un estado del Maestro con información real (`OBI_agregado` sigue en 0) y más jornadas, podría mejorar.

## Qué falta (para MR)

- Decidir λ (0,05 de la 2.2.2 o 0,02 de esta revalidación) y si se entrena más (5.000 jornadas ≈ 2 h en el PC).
- Correr el cuaderno del Maestro en ABIDES.
- Repetir con Ejecutores entrenados cuando el cuaderno `Colab_mid_decision` muestre que aprenden.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
