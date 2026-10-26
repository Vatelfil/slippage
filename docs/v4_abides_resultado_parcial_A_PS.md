# Prueba V4 en ABIDES, cuaderno A: resultado parcial y corrección de la conclusión anterior

**Elaborado por:** PS con apoyo de Claude Code (uso autorizado por la universidad), 26 de octubre de 2026. **No actualiza el Título II.** Resultado **parcial**: solo llegó el cuaderno A (semillas de red 1000 y 2000). Tablas generadas con `scripts/comparar_v4_vs_v2_ps.py` en `docs/v4_vs_v2_ABIDES_A_PS.md`.

## 1. Lo más importante: una conclusión anterior hay que corregirla

Hasta ahora todas las comparaciones «red entrenada frente a red sin entrenar» (el control) usaban **15 semillas de evaluación**. Este cuaderno trajo por primera vez el control con **40 semillas**, y al usarlas la comparación cambia de dirección:

| Red (semilla) | Control, primeras 15 semillas | Control, semillas 16 a 40 | V2 − control, primeras 15 | V2 − control, semillas 16 a 40 | V2 − control, las 40 |
|---|---:|---:|---:|---:|---:|
| 1000 | 3,0 bps | 12,2 bps | +2,2 | −4,9 | **−2,25** (24 de 40 semillas mejor; p = 0,22) |
| 2000 | 3,0 bps | 12,4 bps | +2,3 | −4,9 | **−2,17** (26 de 40 mejor; p = 0,17) |

(V2 = recompensa original + penalización de 30 bps + γ = 1, la «confirmación» anterior.)

**Por qué pasa:** en ABIDES el slippage de cada semilla de evaluación lo domina hacia dónde se mueve el precio en esa simulación: hay semillas de −25 bps y de +75 bps **para todas las estrategias** (la heurística TWAP y la red sin entrenar suben y bajan juntas). Las 15 primeras semillas resultaron ser las más tranquilas; en las 25 siguientes el control cuesta 12 bps. La diferencia entre dos estrategias es de 1 a 3 bps, mucho menos que ese ruido (desviación de la diferencia pareada ≈ 9 a 12 bps), así que **con 15 semillas no se puede distinguir una estrategia de otra** y la conclusión depende de qué semillas se tomaron.

**Qué se corrige de lo dicho antes:**
- «La confirmación con penalización y γ = 1 no baja el costo (+3,0 bps, 0 de 4 redes mejores)» era cierto solo para las primeras 15 semillas. Con 40 semillas, las dos redes que se pudieron comparar cuestan **2,2 bps menos** que el control (tendencia a favor, **no significativa**).
- Lo mismo vale para los resultados de las redes de 1.000 episodios con la recompensa original en `docs/decision_RE_final_D3_para_BF.md` (sección 9: «+3,08 bps, 0 de 6»): se midieron en 15 semillas y hay que repetirlos con más.
- Lo que **sí** se mantiene: la red con la recompensa original y γ = 0,95 se queda esperando en Poisson (colapso medido) y la penalización con γ = 1 hace que complete la orden en ABIDES (cumplimiento ≈ 1,0).

Hoy lo honesto es: **no se puede afirmar ni que el entrenamiento mejora el costo ni que lo empeora**. Hace falta evaluar con muchas más semillas (ver sección 4).

## 2. Resultado de V4 (recompensa contra el precio de llegada) en las dos redes del cuaderno A

| Semilla de red | Cumplimiento muestreando | V4 (bps, 40 semillas) | V2 (bps) | Control (bps) | V4 − control | V4 − V2 |
|---:|---:|---:|---:|---:|---|---|
| 1000 | 1,000 | 6,25 | 6,47 | 8,72 | −2,47 (p = 0,025; 26 de 40 mejor) | −0,22 (p = 0,86) |
| 2000 | 1,001 | 8,77 | 6,71 | 8,89 | −0,12 (p = 0,61; 19 de 40 mejor) | +2,05 (p = 0,26) |

- V4 completa la orden igual que V2 (cumplimiento ≈ 1,0 muestreando). Con argmax, la red 2000 cumple 0,925 con slippage 1,2 bps.
- **V4 no se distingue de V2**: una red queda un poco mejor y la otra un poco peor, sin significancia. Con dos redes no hay base para decir que la recompensa contra el precio de llegada ayuda.
- En el entrenamiento el slippage por episodio baja de 5,0 a 3,4 bps (red 1000) y de 7,8 a 7,0 bps (red 2000); la espera se queda en 33–34 %.
- Las referencias en las mismas 40 semillas: TWAP límite 2,80 bps, agresiva 10,42, pasiva 10,19 y la red sin entrenar 8,7–8,9. Ninguna red llega al nivel de TWAP límite.

## 3. Qué falta

- **Cuaderno B de V4** (semillas 3000 y 4000): da las otras dos redes de V4. Con las dos del cuaderno A solo hay 2 redes por variante.
- **Reevaluación con 300 semillas** (`notebooks/Colab_reevaluacion_300_ABIDES.ipynb`, no entrena): evalúa en las mismas 300 semillas todas las redes ya entrenadas (V2, V4 y las de recompensa original), su control y las heurísticas. La desviación de la diferencia pareada red − control es ≈ 12 bps (no 9, como se estimó antes), así que se necesitan ≈ 120 semillas para detectar 3 bps y ≈ 270 para detectar 2 bps: con 300 semillas se ven diferencias de unos 2 bps (con 150 solo se habrían visto unos 3 bps). Es la prueba que decide si el entrenamiento ayuda; los 40 resultados de aquí son orientativos.

## 3b. Qué se puede decir ya con los datos que hay (sin Colab)

Calculado en el PC con los resultados de 40 semillas ya descargados. Las redes sin entrenar de distintas semillas dan casi lo mismo semilla a semilla (correlación 0,99 entre el control de la red 1000 y el de la 2000), así que para las redes 3000 y 4000, que no tienen control de 40 semillas, se usó el de la 1000 como **sustituto aproximado** (no reemplaza al control propio, que traerá la reevaluación).

| Red | Cuesta menos que el control (bps) | Semillas en que gana | p |
|---|---:|---:|---:|
| V2 1000 | −2,25 | 24 de 40 | 0,22 |
| V2 2000 | −2,01 | 25 de 40 | 0,21 |
| V2 3000 | −3,40 | 26 de 40 | 0,08 |
| V2 4000 | −1,83 | 21 de 40 | 0,38 |
| V4 1000 | −2,47 | 26 de 40 | 0,025 |
| V4 2000 | +0,05 | 22 de 40 | 0,31 |

- **V2 (las 4 redes) queda por debajo del control en todas**, entre 1,8 y 3,4 bps (promedio −2,4 bps; mediana de la diferencia ≈ −1 bps), pero ninguna es significativa por sí sola. Es una tendencia coherente, no una prueba.
- **Frente a TWAP límite** (misma semilla), las redes cuestan entre +2,5 y +6,0 bps más y el control +5,9 bps; ninguna diferencia es significativa. Las redes parecen haber recorrido una parte del camino entre el control y TWAP, pero no lo alcanzan.
- **Con argmax** (elegir siempre la acción más probable) dos redes de V2 y una de V4 no completan la orden bien (cumplimiento 0,00; 0,93; 0,925). Con la política muestreada todas completan. El argmax de una política casi uniforme es poco fiable.
- **Potencia:** la desviación de la diferencia pareada red − control es ≈ 12 bps. Detectar 3 bps con 80 % de potencia pide ≈ 120 semillas; 2 bps, ≈ 270; 1 bps, más de 1.000. Por eso la reevaluación se subió de 150 a 300 semillas.

## 4. Cómo se lee lo que venga

| Resultado de la reevaluación | Lectura |
|---|---|
| Redes de V2 y V4 cuestan menos que el control con IC que no cruza 0 | El arreglo (penalización + γ = 1) sí baja el costo; la propuesta a BF y MR queda respaldada en ABIDES |
| IC cruza 0 y las redes están cerca del control | Con 1.000 episodios el aprendizaje es casi nulo (política casi uniforme, entropía 80–87 %); hace falta más entrenamiento, no otra recompensa |
| V4 mejor que V2 de forma consistente | Sumar la recompensa contra el precio de llegada a la propuesta |

## 5. Cómo verificarlo

```bash
python scripts/comparar_v4_vs_v2_ps.py --v4-dir data/colab_resultados/v4_pen30_g1_A --out-md docs/v4_vs_v2_ABIDES_A_PS.md --out-png data/analysis/v4_vs_v2_ABIDES_A.png
PYTHONPATH=. python -m pytest tests/test_comparar_v4_vs_v2.py tests/test_reevaluar_ejecutores.py tests/test_analizar_reevaluacion.py
```

🤖 Generado con [Claude Code](https://claude.com/claude-code)
