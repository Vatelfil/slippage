# Resultado de la reevaluación con 300 semillas (ABIDES, FALABELLA, apertura)

**Elaborado por:** PS con apoyo de Claude Code (uso autorizado por la universidad). Describe lo medido; las decisiones son del grupo.
**Fecha:** 26 de octubre de 2026. **Datos:** `data/colab_resultados/reeval_300/` (8 redes, 4 controles, 3 heurísticas). **Tabla completa:** `docs/reeval_300_ABIDES_PS.md`. **Figura:** `data/analysis/reeval_300_ABIDES.png`.

## 1. En una frase

Con 300 semillas de evaluación, **ninguna de las 8 redes entrenadas cuesta distinto a la misma red sin entrenar**: las diferencias van de −0,6 a +1,0 bps y todos los intervalos de confianza incluyen el 0. Entrenar 1.000 episodios en ABIDES, con cualquiera de las tres recompensas, **no cambió el costo de forma medible**. Los "+3 bps" (15 semillas) y "−2,4 bps" (40 semillas) de los informes anteriores eran ruido del precio.

## 2. Qué se hizo

- Se evaluaron en **las mismas 300 semillas** (5001 a 5300) 8 redes ya entrenadas, el control de cada semilla de red (la red sin entrenar muestreando su política) y las tres heurísticas.
- Redes: 4 de V2 (recompensa original + penalización 30 bps + γ = 1; semillas 1000 a 4000), 2 de V4 (recompensa contra el precio de llegada + penalización + γ = 1; semillas 1000 y 2000) y 2 redes antiguas sin arreglo (γ = 0,95; semillas 2000 y 3000). Las otras redes antiguas y las V4 de las semillas 3000 y 4000 no entraron (ver sección 6).
- Se usó el cuaderno `Cuaderno_reevaluacion_300_ABIDES.ipynb` en Colab. No entrena nada: solo evalúa checkpoints guardados.

## 3. Resultado

| Qué se compara | Diferencia media (bps) | IC 95 % | Lectura |
|---|---:|---|---|
| 8 redes juntas − su control (promedio por semilla de evaluación) | −0,08 | [−0,98; +0,77] | Sin efecto medible (Wilcoxon p = 0,79) |
| V2 (4 redes), promedio de las diferencias | −0,19 | cada red: IC de ±1,2 aprox., todos con el 0 dentro | Sin efecto |
| V4 (2 redes), promedio de las diferencias | −0,21 | cada red: IC de ±0,6 aprox., con el 0 dentro | Sin efecto |
| Original sin arreglo (2 redes) | +0,26 | con el 0 dentro | Sin efecto |
| Control − TWAP límite (4 controles) | +2,3 a +2,4 | IC con el 0 fuera (límite inferior 0,3 a 0,5) | La política sin entrenar cuesta ≈ 2 bps más que TWAP |
| Redes − TWAP límite (8 redes) | +1,9 a +3,3 | 6 de 8 con el 0 fuera | Igual que el control: ≈ 2 bps sobre TWAP |

Slippage medio en las 300 semillas: redes entre 6,5 y 8,0 bps, control ≈ 7,0, TWAP límite 4,65 (cumplimiento 0,989), agresiva 9,8, pasiva 10,1.

- **V2 contra V4:** no hay diferencia (−0,19 frente a −0,21 bps). La recompensa contra el precio de llegada no aporta nada medible.
- **Cumplimiento:** todas las redes completan la orden (1,000) al muestrear la política. Eso cubre el problema de esperar, pero el costo no mejora, y las redes antiguas sin arreglo también completan al muestrear (el colapso a esperar aparece al evaluar con argmax).
- **Qué se puede descartar:** con 300 semillas el IC de una red mide ±1,2 bps y el de las 8 juntas ±0,9. Si entrenar redujo el costo, lo hizo en **menos de ≈ 1 bps**, muy lejos de los 3 a 6 bps que habría que ver para justificar el proyecto.

## 4. Por qué los resultados anteriores se contradecían

El precio se mueve entre −25 y +75 bps según la semilla de evaluación, para todas las estrategias. La diferencia red − control por semilla tiene una desviación de 10 a 12 bps, así que con 15 semillas el error es de ±6 bps y con 40, de ±3,5. Los números de esas muestras (+3,0 y −2,4 bps) eran compatibles con el 0 desde el principio; con 300 semillas se confirma. Ya estaba advertido en `docs/v4_abides_resultado_parcial_A_PS.md`.

## 5. Qué significa para el proyecto (para discutir, no decidido)

1. **El efecto de la penalización y de γ = 1 es sobre el cumplimiento, no sobre el costo.** La propuesta a BF y MR (`docs/propuesta_cambio_RE_para_BF_y_MR.md`) sigue siendo útil para que el Ejecutor complete la orden con argmax, pero no se puede decir que baje el slippage en ABIDES.
2. **Con 1.000 episodios la red casi no aprende nada útil.** Era la hipótesis de `docs/v4_abides_resultado_parcial_A_PS.md` (política casi uniforme, entropía final de 80 a 87 %). Esto es coherente con lo medido, pero **no está probado** que más episodios lo arreglen. Es una hipótesis.
3. **La comparación honesta hoy:** en este escenario, TWAP límite cuesta ≈ 2 bps menos que la red (entrenada o no). Hay que decirlo así en el informe; y el escenario es un solo ticker y una sola apertura.
4. **Caminos posibles** (no se ha hecho ninguno):
   - **Más episodios** (5.000 a 10.000). En Colab 1.000 episodios tomaron ≈ 25 minutos de entrenamiento (en V4 cuaderno B), así que 5.000 serían ≈ 2 horas por red. Haría falta repetir con 300 semillas de evaluación (≈ 2 a 3 horas).
   - **Reducir el ruido del aprendizaje**, p. ej. que la recompensa mida la diferencia contra TWAP en la misma semilla (el precio común se cancela). Es un cambio de diseño que le toca a BF (recompensa) y MR (entrenamiento).
   - **Aceptar el resultado para el Ejecutor individual** y concentrar el trabajo en lo que aporta el Maestro, dejando este hallazgo como resultado negativo documentado.
5. **Para el informe:** reportar siempre el IC con 300 semillas; los resultados con 15 o 40 semillas no deben usarse como evidencia. (El informe de Título II no se toca ahora; esto queda en md.)

## 6. Qué no entró y límites

- **V4, semillas 3000 y 4000** (cuaderno B): se entrenaron después de lanzar la reevaluación y no están en las 300 semillas. Con 40 semillas (`data/colab_resultados/v4_pen30_g1_B/`) dan −1,13 y −0,20 bps frente a su control (Wilcoxon p = 0,89 y 0,27), sin diferencia. Su entrenamiento: cumplimiento al muestrear 1,00 en ambas; con argmax 0,80 en la 3000 y 1,00 en la 4000 (el argmax de una política casi uniforme no es fiable). Para sumarlas a las 300 semillas hay que volver a ejecutar la celda de evaluación del cuaderno de reevaluación (≈ 20 a 40 minutos; solo hace lo que falta).
- **Redes antiguas:** solo entraron 2 de las 4 por las dos carpetas `d3_1000ep` de Drive.
- Un solo ticker (FALABELLA), un solo tramo (apertura), una sola `q_slice` de 1.000. No se puede generalizar a otros escenarios.
- El cumplimiento de TWAP límite es 0,989, no 1: su slippage se calcula sobre lo ejecutado.
- La prueba de signos entre redes es solo una guía, porque las redes de un grupo comparten entorno y recompensa.

## 7. Cómo verificarlo

```bash
python scripts/analizar_reevaluacion_ps.py --dir data/colab_resultados/reeval_300 --out-md docs/reeval_300_ABIDES_PS.md --out-png data/analysis/reeval_300_ABIDES.png
PYTHONPATH=. python -m pytest tests/test_analizar_reevaluacion.py
```

Las filas "control − TWAP" y "8 redes juntas" se calcularon con un script aparte (bootstrap de 3.000 remuestreos sobre las diferencias por semilla), que no está en el repositorio; la tabla de `docs/reeval_300_ABIDES_PS.md` sí se regenera con el comando de arriba.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
