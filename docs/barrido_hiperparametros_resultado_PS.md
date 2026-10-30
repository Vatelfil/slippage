# Barrido de hiperparámetros del Ejecutor (3.1.1 y 3.1.2): resultado

**Elaborado por:** PS con apoyo de Claude Code, 29 de octubre de 2026. Borrador para MR, que decide si adopta el resultado. **Datos:** `data/barrido_hp/3_1_1/` y `3_1_2/` (un JSON por red, `analisis.json`, `barrido.md`, `barrido.png` y el monitoreo). **Rejilla y regla:** `scripts/colab/grid_specs/hiperparametros_ejecutor_mr.json`, fijadas antes de correr.

## 1. Qué se corrió

- **Dónde y con qué:** en el PC, con el simulador de Poisson (plan B del Título I, sección 4.3.3), penalización de 30 bps por lo no comprado y γ = 1.
- **Tamaño de cada corrida:** 2 redes por configuración, 1.000 episodios cada una. Cada red se evalúa en 30 semillas contra su propia red inicial.
- **3.1.1:** 4 tasas de aprendizaje × 3 tamaños de lote × 3 números de épocas (36 configuraciones, 72 redes).
- **3.1.2:** 25 combinaciones de ε (0,1 a 0,3) y λ de GAE (0,9 a 1,0), partiendo del ganador de la 3.1.1 (50 redes).
- **Monitoreo (3.1.4):** cada red quedó registrada con el monitor.

## 2. Resultado

| Fase | Configuraciones que cumplen ≥ 95 % | Mejor diferencia (bps) | Decisión con la regla |
|---|---:|---|---|
| 3.1.1 | 33 de 36 | −2,62 [−2,80; −2,45] con tasa 0,003, lote 128, 16 épocas | **Gana tasa 0,003, lote 128, 16 épocas.** La configuración de siempre (tasa 0,0003, lote 64, 4 épocas) queda en −2,43 [−2,64; −2,23], fuera del IC del ganador |
| 3.1.2 | 23 de 25 | −2,63 [−2,85; −2,41] (ε = 0,207, λ = 0,926) | **Se mantienen ε = 0,2 y λ de GAE = 0,95.** El IC del mejor incluye a la referencia (−2,62) |

**Configuración resultante:** tasa 0,003, lote 128, 16 épocas, ε = 0,2, λ de GAE = 0,95.

## 3. Lectura

- **La diferencia entre configuraciones es chica.** Unas 30 configuraciones quedan entre −2,4 y −2,6 bps. El ganador mejora ≈ 0,2 bps sobre la de siempre. En Poisson, el entrenamiento llega al nivel de la mejor heurística casi con cualquier configuración razonable.
- **Lo que sí falla es una tasa alta con lote chico.** Con tasa 0,003 y lote 32, una de las dos redes colapsa (cumplimiento 0,000): la regla las excluye. En la 3.1.2, dos combinaciones con λ de GAE bajo (≈ 0,90 a 0,93) tampoco cumplen.
- **El monitoreo avisó justo en esas corridas.** Hubo alertas críticas en 6 de las 122 redes, y son exactamente las que no completan la orden. En las demás no hubo alertas críticas. Es una validación adicional de la 3.1.4.
- **Límite:** es Poisson. En ABIDES el ruido del precio es mucho mayor (`docs/revision_opus_PS.md`, H2), y una tasa de 0,003 podría ser inestable. Por eso el ajuste del Ejecutor con imitación (`Colab_imitacion_A/B`) usa tasa 0,0001, para no deshacer lo copiado, con el resto de los valores de siempre. Aplicar el ganador en ABIDES queda para el Sprint 7, si MR lo aprueba.

## 4. Cómo reproducirlo

```bash
PYTHONPATH=. python scripts/barrido_hiperparametros_mr.py --fase 3.1.1 --out-dir data/barrido_hp
PYTHONPATH=. python scripts/barrido_hiperparametros_mr.py --fase 3.1.2 --out-dir data/barrido_hp
```

Toma ≈ 2,5 h en el PC. Con `--solo-analizar` se rehace solo la tabla.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
