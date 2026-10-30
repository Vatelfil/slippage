# Ejecutor con arranque por imitación: primer resultado (15 semillas)

**Elaborado por:** PS con apoyo de Claude Code, 29 de octubre de 2026. **Datos:** `data/colab_resultados/rimit/d3_opcion0_s1000/` y `d3_opcion0_s2000/` (cuadernos `Colab_imitacion_A` y `_B`, corridos por PS en Colab con ABIDES). Los checkpoints quedan en Drive (`slippage_colab/resultados/rimit` y `rimit_bc`); los usa el cuaderno de reevaluación.

## 1. Qué se corrió

- **Red:** Ejecutor PPO de apertura (FALABELLA, 1.000 acciones por ventana de 15 min), semillas de red 1000 y 2000.
- **Paso 1, imitación:** la red copia a TWAP con órdenes límite durante 100 episodios (3.000 pares estado-acción). Exactitud de la copia: 0,93 (A) y 0,92 (B).
- **Paso 2, PPO:** 1.000 episodios con la recompensa de precio de llegada, penalización de 30 bps por lo no comprado y γ = 1. Tasa de aprendizaje baja (0,0001) y entropía baja (0,001), para no deshacer lo copiado.
- **Evaluación:** 15 semillas de mercado (las mismas de siempre, desde la 5001), con argmax y muestreando.

## 2. Resultado

| Red | Slippage (bps) | Cumplimiento | Red − TWAP límite, IC 95 % | Wilcoxon p |
|---|---:|---:|---|---:|
| A (s1000), argmax | 3,26 | 0,990 | +1,48 [+0,18; +2,86] | 0,107 |
| B (s2000), argmax | 3,40 | 0,991 | +1,62 [+0,33; +3,07] | 0,084 |
| A (s1000), muestreando | 6,76 | 1,000 | +4,98 [+2,31; +7,96] | 0,004 |
| B (s2000), muestreando | 2,35 | 1,000 | +0,57 [−1,52; +2,63] | 0,804 |
| TWAP límite (referencia) | 1,78 | 0,971 | — | — |

**Comparación con las redes anteriores, en las mismas 15 semillas:** las redes con la recompensa corregida (`rmid`) quedaban entre +3,8 y +5,8 bps sobre TWAP límite. Con imitación, las dos redes con argmax quedan en ≈ +1,5 bps: unos 3 bps más baratas.

## 3. Lectura

- **Mejora clara frente a lo anterior.** La red ahora parte de la mejor política medida y PPO no la deshace: el cumplimiento sigue sobre el 95 % y el costo baja respecto de todas las redes entrenadas antes.
- **Todavía no le gana a TWAP límite.** Queda ≈ 1,5 bps por encima. Esa diferencia no es significativa con 15 semillas (p ≈ 0,1). TWAP límite completa el 97 % y las redes el 99 %: parte de la diferencia viene de comprar lo que TWAP deja sin comprar.
- **La red B muestreando** empata con TWAP (+0,57, IC que incluye el 0). Con 15 semillas no se puede saber si es real o es ruido.
- **Decisión:** ninguna todavía. Con 15 semillas el error estándar es de ≈ 4,6 bps. La reevaluación con 300 semillas (`Colab_reevaluacion_imitacion_300`) decide, y después la regla fijada elige el Ejecutor del sistema final (`scripts/elegir_ejecutor_ps.py`).
- **Nota sobre la red B sin entrenar:** con argmax no compra nada (cumplimiento 0). Es esperable: una red al azar con argmax repite siempre la misma acción, y en esa semilla esa acción es esperar. No afecta al resultado entrenado.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
