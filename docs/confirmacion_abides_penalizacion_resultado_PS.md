# Confirmación en ABIDES de la penalización terminal con γ = 1: resultado

**Elaborado por:** PS con apoyo de Claude Code (uso autorizado por la universidad), 26 de octubre de 2026. **No actualiza el Título II**: deja el material listo para cuando se actualice.

Continúa a `docs/experimentos_recompensa_PS.md` (que probó el arreglo en el simulador de Poisson) y a `docs/propuesta_cambio_RE_para_BF_y_MR.md`. Las tablas completas, generadas con `scripts/analizar_estabilidad_D3.py`, están en `docs/conf_pen30_g1_ABIDES_PS.md` y el panel de monitoreo en `docs/monitoreo_conf_pen30_g1.md`.

## 1. Qué se corrió

- **Dónde:** Colab, ABIDES (`rmsc04`), dos cuadernos (`Colab_confirmacion_ABIDES_A.ipynb` y `_B.ipynb`), unos 110 minutos cada uno.
- **Qué:** el Ejecutor con la opción 0 de D3, **γ = 1** y **penalización de 30 bps** por cada acción del slice sin comprar al terminar la ventana. 4 semillas de red (1000, 2000, 3000, 4000), 1.000 episodios y 40 semillas de evaluación.
- **Datos:** `data/colab_resultados/conf_pen30_g1/` (los controles sin entrenar muestreando están en los `control_s*.json`).
- **Cómo se compara:** la red entrenada muestreando contra la **misma red sin entrenar también muestreando**, en las mismas semillas de evaluación (las primeras 15, que son las que tiene el control; la diferencia es pareada).

## 2. Resultado

| Semilla de red | Cumplimiento (muestreando) | Slippage entrenada (bps, 40 semillas) | Diferencia con el control (bps, 15 semillas) | p (Wilcoxon pareado) |
|---:|---:|---:|---:|---:|
| 1000 | 1,000 | 6,47 | +2,17 | 0,42 |
| 2000 | 0,999 | 6,71 | +2,28 | 0,45 |
| 3000 | 1,000 | 5,32 | +2,62 | 0,49 |
| 4000 | 1,001 | 6,89 | +5,02 | 0,055 |
| **Media** | **1,000** | **6,35** | **+3,02** | prueba de signos entre redes: p = 0,125 |

Referencias en las mismas condiciones: red sin entrenar muestreando ≈ 2,6–3,0 bps, TWAP límite 2,80 bps, agresiva 10,42 bps y pasiva 10,19 bps.

**En una frase:** el arreglo evita que la red se quede esperando, pero **no baja el costo respecto de la red sin entrenar** (0 de 4 redes mejores; sumando las 10 redes de 1.000 episodios que se han entrenado en ABIDES, 0 de 10).

## 3. Qué sí funcionó y qué no

**Funcionó (comportamiento):**
- Cumplimiento ≈ 1,0 con la política muestreada en las 4 redes; la espera al final del entrenamiento quedó entre 20 % y 40 % (con la recompensa anterior llegaba a casi 100 % en Poisson).
- El retorno de entrenamiento mejoró alrededor de 50 %: la red sí aprendió algo de lo que se le pidió.

**No funcionó (costo):**
- El costo sigue unos 3 bps sobre el control. Con 15 semillas pareadas y una desviación de la diferencia de ≈ 9 bps, solo se detectarían diferencias de unos 5 bps o más; por eso los p individuales no son significativos. Lo que sí se ve es que las 4 diferencias tienen el mismo signo.
- Alertas del monitoreo (`docs/monitoreo_conf_pen30_g1.md`): `RECOMPENSA_SUBE_COSTO_NO` (aviso) en las semillas 2000 y 3000, donde el retorno sube 49 % y 78 % y el slippage de entrenamiento baja solo 0,6 y 1,3 bps; `ARGMAX_DISTINTO_DE_MUESTREO` (crítica) en la semilla 2000, donde con argmax no compra nada; `ENTROPIA_BAJA` (informativa) en las cuatro, con entropía final de 80–87 %, es decir, la política sigue siendo casi uniforme.

## 4. Qué significa para lo que se había dicho

- La conclusión de Poisson («5 de 5 redes buenas, 17,9 frente a 17,91 bps») **se mantiene como diagnóstico** (explica por qué la red se quedaba esperando), pero **no se traslada a ABIDES como mejora de costo**. Ese simulador no tiene tendencia ni impacto de precio, y una orden límite que se llena paga lo mismo que una de mercado; en ABIDES eso no es cierto.
- Una posible explicación (**hipótesis, no probada**): para cumplir sin pagar la penalización, la red aprendió a usar más órdenes límite de compra (46–69 % de los pasos al final), que en ABIDES se llenan tarde y a peor precio cuando el precio sube. Si la recompensa actual (R_E) no compara contra el precio de llegada, no vería ese costo; eso se puede comprobar con la prueba 1 de la sección 5.
- La propuesta a BF y MR (`docs/propuesta_cambio_RE_para_BF_y_MR.md`) queda como **necesaria pero no suficiente**: sirve para que el Ejecutor complete la orden, no para que gaste menos.

## 5. Qué se podría probar a continuación (requiere Colab; solo si se decide)

| # | Prueba | Qué responde | Costo aproximado |
|---|---|---|---|
| 1 | Recompensa de **slippage contra el precio de llegada** (variante V4 de `src/experiments/variantes_recompensa.py`) con penalización 30 y γ = 1 | Si el problema es que la recompensa no ve el costo de llenarse tarde | 2 cuadernos de Colab de ≈ 110 min, más agregar una opción al script de Colab |
| 2 | Más episodios (3.000–5.000) con la misma recompensa | Si la política casi uniforme (entropía 80–87 %) necesita simplemente más entrenamiento | ≈ 5–6 h de Colab por semilla; solo vale la pena después de la prueba 1 |
| 3 | Más semillas de evaluación (≈ 75 para detectar 3 bps) | Aclarar si el +3 bps es real o ruido | Las mismas redes se pueden reevaluar; ≈ 30 min por cuaderno |

Recomendación: la prueba 1 (y, de pasada, la 3 con las redes ya entrenadas). Se avisa antes de ejecutar nada en Colab.

## 6. Cómo verificarlo

```bash
python scripts/analizar_estabilidad_D3.py --dir data/colab_resultados/conf_pen30_g1 --out-json data/analysis/conf_pen30_g1.json --out-png data/analysis/conf_pen30_g1.png --out-md docs/conf_pen30_g1_ABIDES_PS.md
python scripts/monitorear_entrenamiento.py --dir data/colab_resultados/conf_pen30_g1
```

🤖 Generado con [Claude Code](https://claude.com/claude-code)
