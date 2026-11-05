# Maestro v2: resultado en la liquidez media (5 de noviembre)

**Quién:** PS corrió `notebooks/Colab_maestro_v2.ipynb`; el análisis lo hizo Claude Code. **Datos:** `data/colab_resultados/maestro_v2/`.

Es una mejora que **se presenta aparte**. El resultado oficial de la 3.2.3 sigue siendo el del sistema del Sprint 6, con las 90 corridas. Qué se cambió y por qué está en `docs/maestro_v2_PS.md`.

## En una frase

El arreglo funciona: el Maestro ahora mira el mercado y ya no elige siempre el máximo. Pero el costo casi no cambia: cuesta lo mismo que el Maestro anterior y sigue sin diferencia estadística con TWAP y VWAP.

## Entrenamiento (2.000 jornadas en Poisson)

| | Sin entrenar | Entrenado |
|---|---|---|
| R_M (bps) | −55,1 | −27,5 |
| Cumplimiento | 83 % | 99,6 % |
| Slippage (bps) | 24,5 | 26,8 |

- El Maestro aprende: R_M mejora en +27,6 bps (IC 95 % [17,1; 39,8]).
- Lo que más mejora es el cumplimiento: termina casi todas las órdenes. A cambio, el slippage sube 2,3 bps.

## Qué decide ahora el Maestro (282 decisiones, 30 corridas)

| α (porcentaje de lo que falta) | Maestro anterior | Maestro v2 |
|---|---|---|
| 50 % | 276 (98 %) | 0 |
| 40 % | — | 210 (74 %) |
| 35 % | — | 13 (5 %) |
| 20 % | — | 56 (20 %) |
| 10 % o 45 % | — | 3 (1 %) |

- **Ventana:** la de 15 pasos en 266 de 282 decisiones (94 %), como antes.
- Ya no está pegado en el máximo, y en las 10 órdenes mezcla 40 % y 20 %.
- Aun así, sigue siendo casi una regla fija («compra 40 % de lo que falta»). La información del mercado cambia poco sus decisiones.

## Costo frente al Maestro anterior, TWAP y VWAP

Son los mismos 10 pedidos con las semillas 4 a 6, es decir, los mismos días que las 90 corridas, en la liquidez media. La diferencia se calcula como v2 − referencia, en bps. **Negativa = v2 cuesta menos.**

| Contra | Dif. media | IC 95 % | Wilcoxon p | Gana v2 | Significativo |
|---|---|---|---|---|---|
| Maestro anterior (PPO_sistema) | −0,85 | [−9,97; 8,25] | 0,855 | 15/30 | no |
| TWAP | −4,21 | [−23,71; 16,11] | 0,556 | 18/30 | no |
| VWAP | −5,04 | [−28,40; 19,13] | 0,556 | 19/30 | no |

- **Costo medio:** v2 46,3 bps; Maestro anterior 47,1; TWAP 50,5; VWAP 51,3.
- Frente a TWAP la ventaja pasa de −3,37 (Maestro anterior) a −4,21 bps. Va en la misma dirección, es un poco mayor y sigue sin ser significativa.
- d de Cohen despreciable en las tres comparaciones. Shapiro no rechaza la normalidad, y el t-test da lo mismo.

## Detalle a tener en cuenta

- **MO-08, semilla 4:** el cumplimiento quedó en 93,6 %, bajo el 95 %. Por eso la celda 14 del cuaderno no dice «LISTO».
- Las otras 29 corridas superan el 95 %.
- No hace falta repetirla: con la misma semilla daría lo mismo.
- Se informa tal cual. El efecto en la media es pequeño (una corrida de 30).

## Qué significa para el informe

1. **El problema de diseño quedó corregido.** El Maestro ahora ve volatilidad, profundidad y desbalance medidos en el mercado simulado, y se entrenó con la corrección del cierre. Esto responde la desviación 12.
2. **No cambia la conclusión.** El sistema es competitivo con TWAP y VWAP (cuesta un poco menos en promedio), pero la diferencia no es estadísticamente significativa en la liquidez media.
3. **Por qué no mejora más:** el Maestro sigue eligiendo casi siempre la misma combinación. Eso apunta a que el beneficio viene sobre todo de los Ejecutores y del ritmo general, y no de reaccionar al mercado.
   - La prueba de control (`Colab_control_reglas_media_A/B`, pendiente) lo puede confirmar.
   - Para el trabajo futuro: más jornadas de entrenamiento, entrenar el Maestro en ABIDES y no solo en Poisson, o una señal de mercado más fuerte.
4. **Recomendación:** dejar el Maestro del Sprint 6 como resultado oficial y presentar el v2 en una subsección («versión corregida del Maestro»), con esta tabla.

## Cómo reproducir

```
python scripts/comparacion_estadistica_3_2_3.py --entradas data/colab_resultados/corridas_90/media/A data/colab_resultados/corridas_90/media/B data/colab_resultados/maestro_v2/eval_media --sistema PPO_sistema_v2 --referencias PPO_sistema TWAP VWAP --out-dir salida_v2
```
