# Resultado de la recompensa corregida en ABIDES (300 semillas) y cierre de D3

**Elaborado por:** PS con apoyo de Claude Code, 29 de octubre de 2026. Describe lo medido; las decisiones son del grupo. **Datos:** `data/colab_resultados/rmid/` (entrenamiento) y `data/colab_resultados/reeval_300_mid/` (reevaluación). **Tabla generada:** `docs/reeval_300_mid_ABIDES_PS.md` (`scripts/analizar_reeval_mid_ps.py`).

## 1. En una frase

La corrección de la recompensa (`mid_decision`) **sí cambió lo que aprende la red**, pero el resultado es que **cuesta más** que la misma red sin entrenar: +1,55 bps, IC 95 % de +0,37 a +2,71. Ninguna de las cuatro recompensas probadas logra que el Ejecutor le gane a su red sin entrenar en ABIDES, y TWAP con órdenes límite sigue ≈ 2,3 bps más barato que cualquier red.

## 2. Qué se midió

| Grupo (redes) | Red − su control (bps), IC 95 % | Wilcoxon |
|---|---|---|
| V2: original + penalización + γ = 1 (4) | −0,19 [−1,25; +0,82] | p = 0,97 |
| V4: precio de llegada + penalización + γ = 1 (4) | −0,11 [−0,61; +0,36] | p = 0,28 |
| Original, γ = 0,95 (2) | +0,26 [−0,90; +1,41] | p = 0,52 |
| **Recompensa corregida, opción 0 (4)** | **+1,55 [+0,37; +2,71]** | **p = 0,001** |
| Recompensa corregida, opción A (2) | +0,57 [−0,70; +1,78] | p = 0,13 |

Referencias en las mismas semillas: TWAP límite 4,65 bps; controles ≈ 7,0; agresiva 9,83; pasiva 10,08.

En el entrenamiento, la verificación dio OK: el precio de referencia es el de la decisión (desfase 0), y la correlación entre recompensa y costo, con la política aleatoria, pasó de −0,08 a 0,73. Las redes dejaron de comprar a mercado (de 33 % a 2–13 % de los pasos) y todas completan la orden con argmax.

## 3. Por qué empeoró (inferido, no probado)

- La recompensa corregida mide bien lo que cuesta cada compra frente al precio que había al decidir.
- **No mide cuánto sube el precio mientras la red espera.** En estas simulaciones el precio sube en promedio durante la ventana. La red aprende a esperar con órdenes límite y termina comprando más caro que si repartiera parejo.
- La correlación de 0,73 se midió con una política aleatoria. Cuando la red aprende a esperar, la recompensa deja de seguir el costo total. Esto corrige lo que dije en `docs/revision_opus_PS.md`: el parche era necesario, pero no bastaba.
- La única recompensa que incluye el costo de esperar es la del precio de llegada (V4). Esa es demasiado ruidosa para aprender en 1.000 episodios (prueba de cordura, `data/analysis/prueba_cordura_ppo.txt`).

## 4. Qué se hace ahora

- **`mid_decision` no queda por defecto.** Sigue como opción, documentada.
- **Ejecutor:** se prueba un arranque por imitación de TWAP límite seguido de un ajuste con PPO con la recompensa de llegada (`notebooks/Colab_imitacion_A/B.ipynb`). La red sigue siendo el Ejecutor PPO del Título I; solo cambia el punto de partida.
- **El Ejecutor del sistema final** se elige con una regla fijada antes (`scripts/elegir_ejecutor_ps.py`): la red PPO más barata en las 300 semillas que cumpla al menos el 95 %. Las heurísticas no compiten.

## 5. D3 (opción 0 u opción A) con la regla fijada

| Comparación (misma semilla de red) | A − 0 (bps), IC 95 % |
|---|---|
| Semilla 1000 | −1,79 [−2,50; −1,12] |
| Semilla 2000 | +0,60 [−0,06; +1,25] |
| Las dos juntas | −0,60 [−1,04; −0,16] |

La regla (`docs/revision_opus_PS.md`, sección 6) pedía dos condiciones para pasar a la opción A:
- **(a) que complete más órdenes con argmax:** no se cumple, porque las dos opciones completan el 100 %.
- **(b) que no cueste más de +1 bps:** sí se cumple.

**Resultado de la regla: se queda la opción 0** (fórmula del Título I).

Nota para BF: medida por costo, la A es menos mala (−0,60 bps), pero como todas las redes con la recompensa corregida cuestan más que su control, D3 no cambia la conclusión práctica. Si BF prefiere la A por esta razón, la regla le permite cambiarlo.

## 6. Límites

- Un solo ticker (FALABELLA), tramo de apertura y slice de 1.000 acciones.
- Pocas redes por grupo (2 a 4).
- La explicación de la sección 3 es una inferencia a partir de la conducta medida (menos órdenes a mercado, más espera) y del aumento del costo. No se aisló con un experimento.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
