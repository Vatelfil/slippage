# Control de la 3.2.3: resultado en profundidad ×1 (12 de noviembre)

**Quién:** PS corrió `Colab_control_reglas_media_A/B` en Colab; el análisis lo hizo Claude Code.
**Datos:** `data/colab_resultados/control_reglas/media/`.
**Plan registrado antes de correr:** `docs/control_reglas_3_2_3_PS.md`.
**Escenario:** profundidad del market maker ×1 (antes «liquidez media», ver `docs/c6c_confirmacion_v3_BF.md`).

## En una frase

La ventaja del sistema frente a TWAP viene de los **Ejecutores**, no del Maestro:
- **Ejecutores:** con el mismo calendario que TWAP, cuestan 15,4 bps menos (p < 0,001).
- **Calendario del Maestro:** suma +12,0 bps en promedio (no significativo), y depende de si el precio sube o baja ese día.

## Qué se comparó

Son las mismas 30 corridas que las 90 en ×1: 10 órdenes × semillas 4, 5 y 6, con los mismos Ejecutores, impacto y corrección del cierre. Solo cambia quién decide cuánto comprar y cuándo.

| Estrategia | Decide cuánto y cuándo | Compra dentro de la ventana |
|---|---|---|
| PPO_sistema | Maestro PPO | Ejecutores PPO (órdenes límite) |
| Regla_fija | Siempre α = 0,5 y 15 min | Ejecutores PPO |
| Regla_uniforme | Partes iguales cada media hora (el calendario de TWAP) | Ejecutores PPO |
| TWAP | Partes iguales cada media hora | Política ingenua de mercado (`benchmarks_meta_ordenes_ps.py`, 2.3.4) |

## Resultados (costo sin ajustar, n = 30 pares)

Diferencia = primera − segunda, en bps, pareada por orden y semilla. **Negativa = la primera cuesta menos.**

| Comparación | Pregunta | Dif. media | IC 95 % | Wilcoxon p | p (Holm, 3 pruebas) | t pareado p | Shapiro p | d de Cohen | Gana la primera |
|---|---|---|---|---|---|---|---|---|---|
| Regla fija − sistema | ¿El Maestro hace algo distinto de α = 0,5 siempre? | −2,66 | [−12,16; 2,91] | 0,500 | 1,000 | 0,545 | < 0,001 | −0,11 | 1/30 |
| Sistema − regla uniforme | Aporte del calendario del Maestro | +12,00 | [−10,59; 34,54] | 0,503 | 1,000 | 0,331 | 0,653 | 0,18 | 16/30 |
| Regla uniforme − TWAP | Aporte de los Ejecutores | **−15,37** | **[−20,35; −10,32]** | **2,3·10⁻⁶** | **7,0·10⁻⁶** | 2,1·10⁻⁶ | 0,720 | **−1,08 (grande)** | **26/30** |

**Cómo se calculó:**
- **Wilcoxon de rangos con signo:** sobre las 30 diferencias pareadas. Se ordenan por tamaño absoluto y se comparan las sumas de rangos de las positivas y las negativas.
- **Holm:** multiplica el p más chico por 3, el siguiente por 2 y el último por 1, manteniendo el orden. Corrige porque se hicieron 3 pruebas.
- **IC 95 %:** bootstrap pareado de 10.000 remuestreos, por percentil.
- **d de Cohen pareado:** media de las diferencias dividida por su desviación estándar.
- **Shapiro-Wilk:** revisa si las diferencias son normales. En «regla fija − sistema» no lo son, porque 25 diferencias valen exactamente 0. Por eso la prueba principal es Wilcoxon y no el t.

**Descomposición exacta, corrida por corrida (cuadra):**

| | bps |
|---|---|
| Sistema − TWAP (total) | −3,37 |
| … por el calendario del Maestro (sistema − uniforme) | +12,00 |
| … por los Ejecutores (uniforme − TWAP) | −15,37 |

## Robustez: algunas corridas no completaron

- La regla uniforme no completó 9 de sus 30 corridas: el cumplimiento mínimo fue 0,842 (MO-08, semilla 4).
- La regla fija dejó 2 corridas con cumplimiento de 0,986 y 0,999.
- Comprar menos puede abaratar el costo de forma artificial. Por eso se repitió el análisis con el **costo ajustado** (`--penalizacion-bps 30`, como dice `docs/plan_analisis_3_2_3_PS.md`).
- La conclusión no cambia:
  - Ejecutores: −15,25 bps [−20,07; −10,36], Wilcoxon p (Holm) = 7,0·10⁻⁶, d = −1,11;
  - calendario: +11,96 [−10,47; 34,49], p (Holm) = 1,000.

## Frente a lo que se esperaba (registrado el 1 de noviembre)

1. **«Regla fija ≈ sistema, 25 de 30 idénticas»: se cumplió.** Salieron 25 idénticas, lo que confirma que la simulación es determinista. El Maestro del Sprint 6 aprendió, en la práctica, la regla fija.
2. **«El calendario depende del día»: se cumplió.** Es un análisis descriptivo, sin prueba:
   - en los días en que el precio subió (n = 20), el calendario del Maestro ahorró 24,5 bps;
   - en los que bajó (n = 10), costó 85,0 bps más.
   - Comprar rápido (α = 0,5) conviene si el precio sube y perjudica si baja.
3. **«Ejecutores ≈ 0 o un poco más caros que TWAP»: no se cumplió.** Fueron 15,4 bps más baratos. La explicación más probable está en contra de qué TWAP se compara:
   - El TWAP de las 90 corridas compra con **órdenes a mercado**: cruza el spread en cada compra.
   - Los Ejecutores usan **órdenes límite**.
   - La referencia del plan (≈ +1 bps) era contra TWAP **con órdenes límite** (`docs/reeval_300_imitacion_resultado_PS.md`).
   - Entonces, los Ejecutores le ganan a TWAP a mercado más o menos lo que vale no cruzar el spread, y quedan a la par de un TWAP con límite. Es una **lectura**, no se probó aquí: el TWAP con límite no se corrió en las 90.

## Qué significa para la tesis

- **Resultado propio de la arquitectura:** la capa de Ejecutores PPO baja el costo frente a TWAP de forma significativa y con un efecto grande (d ≈ −1,1).
- **El Maestro del Sprint 6 no aporta:** su calendario fijo agrega varianza que depende de la dirección del precio. Eso explica por qué el sistema completo no le gana a TWAP de forma significativa (−3,37 bps, p = 0,626).
- **Coincide con el Maestro v2** (`docs/maestro_v2_resultado_PS.md`): aunque ve el mercado, su costo es casi el mismo.
- **Límite a declarar:** la comparación es contra un TWAP a mercado. Frente a un TWAP con órdenes límite, la ventaja de los Ejecutores probablemente sería cercana a 0.
- **Solo es profundidad ×1.** En ×4 y ×0,25 se puede repetir cambiando `ESCENARIO` en la celda 10. Es opcional.

## Cómo reproducir

```
python scripts/control_reglas_3_2_3.py --entradas data/colab_resultados/corridas_90/media data/colab_resultados/control_reglas/media --out-dir salida_control
python scripts/control_reglas_3_2_3.py --entradas data/colab_resultados/corridas_90/media data/colab_resultados/control_reglas/media --penalizacion-bps 30 --out-dir salida_control_pen
```

Figura: `data/colab_resultados/control_reglas/media/analisis/control_reglas.png`. Muestra una barra por comparación (la diferencia media, con su IC 95 %). Si la línea negra cruza el 0, la diferencia no es significativa. Solo «regla uniforme − TWAP» queda entera bajo el 0.
