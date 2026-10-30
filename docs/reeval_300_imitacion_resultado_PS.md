# Reevaluación con 300 semillas de los Ejecutores con imitación (30 de octubre)

**Elaborado por:** PS con apoyo de Claude Code. **Datos:** `data/colab_resultados/reeval_300_imitacion/`, del cuaderno `Colab_reevaluacion_imitacion_300`, corrido por PS en Colab con ABIDES. **Tabla completa:** `docs/reeval_300_imitacion_ABIDES_PS.md`, generada con `scripts/analizar_reeval_mid_ps.py`. Todas las redes se evalúan muestreando su política, en las mismas 300 semillas (5001 a 5300).

## 1. Falta una red

La carpeta trae `rimit` con la semilla 1000, pero **no la red `rimit` con la semilla 2000**, que es la red B ajustada con PPO. La reevaluación busca `rimit/d3_opcion0_s2000/checkpoints_apertura/checkpoint_last.pt` en Drive. Si no la encontró, ese archivo no estaba cuando corrió el cuaderno. Puede ser porque Drive todavía no sincronizaba lo que dejó el cuaderno B (inferido; no hay registro que lo confirme).

**Qué hacer:** comprobar que el archivo exista en Drive y volver a correr `Colab_reevaluacion_imitacion_300`. El script salta lo que ya está hecho, así que solo evalúa esa red (≈ 12 min). Hay que hacerlo **antes** de `Colab_sistema_final`: con 15 semillas, la red B muestreando fue la más barata (2,35 bps).

## 2. Resultado (300 semillas)

| Red | Slippage (bps) | Cumplimiento | − su control, IC 95 % | − TWAP límite, IC 95 % |
|---|---:|---:|---|---|
| **Imitación + PPO, s1000** | **5,68** | 1,000 | −1,30 [−3,22; +0,66] (p = 0,095) | **+1,03 [+0,11; +1,88]** |
| Solo imitación, s1000 (no compite) | 5,77 | 0,993 | −1,21 [−2,96; +0,59] | +1,12 [+0,26; +2,00] |
| Solo imitación, s2000 (no compite) | 5,13 | 0,984 | −1,88 [−3,70; +0,07] | +0,47 [−0,23; +1,17] |
| Mejor red anterior (V2, s3000) | 6,50 | 1,000 | −0,58 [−1,91; +0,72] | +1,85 [−0,21; +3,80] |
| Recompensa corregida (6 redes) | 7,09 a 9,48 | 1,000 | +1,55 en promedio (peor) | +2,4 a +4,8 |
| TWAP límite (referencia) | 4,65 | 0,989 | — | — |

## 3. Lectura

- **La imitación es lo mejor medido hasta ahora para un Ejecutor PPO.** La red s1000 cuesta 5,68 bps: 0,8 bps menos que la mejor red anterior y 1,3 bps menos que su red sin entrenar. Esta última diferencia no alcanza a ser significativa (p = 0,095).
- **Todavía no le gana a TWAP límite:** queda 1,03 bps por encima, y esa diferencia sí es significativa. Parte de ella viene de que la red compra el 100 % y TWAP el 98,9 %.
- **PPO casi no cambia lo copiado** (5,77 → 5,68 bps). Con la tasa de aprendizaje baja que se usó, el ajuste es chico.
- **La red solo imitada s2000 empata con TWAP** (+0,47, IC que incluye el 0), pero no compite: no pasó por PPO, y el Título I pide Ejecutores PPO. Su versión con PPO es la que falta (sección 1).
- **Elección con la regla fijada:** con lo que hay, gana la red de imitación + PPO s1000 (`scripts/elegir_ejecutor_ps.py`). Se confirma cuando esté la red s2000.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
