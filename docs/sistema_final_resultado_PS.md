# Sistema final del Sprint 6: Ejecutor elegido y Maestro entrenado (30 de octubre)

**Elaborado por:** PS con apoyo de Claude Code. **Datos:** `data/colab_resultados/sistema_final/`, del cuaderno `Colab_sistema_final` corrido por PS en Colab.

## 1. Ejecutor elegido con la regla

- **Regla:** la red PPO de menor slippage en las 300 semillas que complete al menos el 95 %.
- **Elegida:** `rimit__d3_opcion0_s1000` (imitación + PPO), con 5,68 bps y cumplimiento de 1,000. Le siguen dos redes V2 con 6,50 y 6,52 bps.
- **Falta una candidata:** la red B de imitación + PPO (semilla 2000) no entró, porque la reevaluación no encontró su archivo en Drive. PS confirmó que el archivo existe: semilla 2000, 1.000 episodios, tasa 0,0001.
- **Qué se hace:** el cuaderno `notebooks/Colab_reeval_red_B.ipynb` la busca, la reevalúa y vuelve a aplicar la regla. Si gana la B, guarda el Maestro anterior en `sistema_final/maestro_con_<red anterior>` y lo vuelve a entrenar con la B.

## 2. Maestro (Poisson, 2.000 jornadas, λ = 0,02, impacto acumulado, inicio sorteado entre los tres tramos)

Evaluación en 30 jornadas (semillas 90001 a 90030), orden de 88.300 acciones:

| | Sin entrenar | Entrenado | Entrenado − sin entrenar (IC 95 %) |
|---|---:|---:|---|
| Cumplimiento | 0,733 | **0,976** | — |
| R_M (bps) | −72,1 | −30,7 | **+41,4 [+29,8; +54,6]** |
| Slippage (bps) | 23,9 | 26,3 | +2,4 [+1,7; +3,2] |

- **El Maestro aprende a completar la orden:** pasa del 73 % al 98 %.
- **Paga un poco más por acción (+2,4 bps), porque compra más.** R_M, que castiga lo que queda sin comprar, mejora 41 bps.
- **λ:** con λ = 0,02 la penalización es el 19 % del costo, dentro del rango 10–100 % fijado (`maestro/lambda.json`).
- **Límite:** el Maestro se entrenó en Poisson. Las 30 corridas lo evalúan en ABIDES.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
