# Experimentos para arreglar el entrenamiento del Ejecutor: resumen

**Elaborado por:** PS con apoyo de Claude Code (uso autorizado por la universidad), 25 de octubre de 2026. **Pendiente de revisión por:** BF (R_E, 2.2.3) y MR (entrenador PPO, 2.3.2). Los cambios están en un envoltorio de pruebas y no modifican el código de ninguno de los dos.

Continúa a `docs/diagnostico_recompensa_PS.md` (qué falla y por qué). Los resultados completos de cada etapa están en `docs/experimentos_recompensa_A_PS.md`, `docs/experimentos_recompensa_A2_PS.md` y `docs/experimentos_recompensa_B_PS.md`.

## 1. Qué se hizo

- **Dónde:** simulador de Poisson en el PC (1.000 episodios entrenan en cerca de un minuto). Una prueba así no sirve para el costo absoluto, pero sí para ver qué hace aprender a la red.
- **Qué se probó:** 11 variantes de la recompensa o del cierre de la ventana (etapas A y A2) y 4 ajustes adicionales sobre la mejor (etapa B). Cada una con 5 semillas de red y 1.000 episodios.
- **Cómo se evaluó:** 50 semillas nuevas, política muestreando (como se entrena), en tres tamaños de orden. Todas las filas, incluidas las heurísticas, se miden con la misma regla: lo que no se compra por voluntad propia se liquida a mercado, así el costo de dejar cosas pendientes siempre cuenta.
- **Criterio para dar por buena una red** (5.000 acciones, 15 min): (1) cumple la orden por su cuenta (≥ 90 %), (2) no se queda esperando (≤ 50 % de los pasos) y (3) cuesta menos que su propia red inicial (Wilcoxon pareado, p < 0,05). Una variante funciona si 4 de sus 5 redes lo cumplen.
- **Tamaño de entrenamiento:** 5.000 acciones, porque con 1.000 el simulador de Poisson no distingue estrategias (todas cuestan ≈ 18 bps) y no hay nada que aprender.

## 2. Resultado principal (5.000 acciones, 15 minutos)

| Variante | Slippage (bps) | Cumplimiento voluntario | Pasos en espera | Redes que cumplen los tres criterios |
|---|---:|---:|---:|---:|
| Red inicial (sin entrenar, muestreando) | 20,26 | 1,00 | 30 % | — |
| **V0** recompensa original, γ = 0,95 (lo de hoy) | 21,48 | 0,05 | 99 % | 0 de 5 |
| V0 con γ = 1 | 21,44 | 0,05 | 98 % | 0 de 5 |
| V2 penalización de 30 bps, γ = 0,95 | 21,24 | 0,14 | 89 % | 0 de 5 |
| V2b penalización de 100 bps, γ = 0,95 | 19,21 | 0,95 | 51 % | 4 de 5 |
| V1 liquidación forzada, **γ = 1** | 17,97 | 0,95 | 38 % | **5 de 5** |
| **V2 penalización de 30 bps, γ = 1** | **17,92** | 0,99 | 19 % | **5 de 5** |
| V2b penalización de 100 bps, γ = 1 | 17,98 | 1,00 | 17 % | **5 de 5** |
| V3 IS frente al precio de llegada + liquidación, γ = 1 | 17,91 | 0,99 | 30 % | **5 de 5** |
| V4 IS frente al precio de llegada + penalización, γ = 1 | 17,96 | 1,00 | 24 % | **5 de 5** |
| V5 costo de espera denso (100 bps), γ = 1 | 20,38 | 1,00 | 4 % | 1 de 5 |
| *Referencia: TWAP con órdenes límite (mejor heurística)* | *17,91* | *0,98* | *0 %* | — |
| *Referencia: mercado agresiva* | *20,93* | *1,00* | *0 %* | — |
| *Referencia: esperar siempre* | *21,53* | *0,00* | *100 %* | — |

## 3. Qué se aprendió

1. **La recompensa original no basta.** Sin nada que obligue a completar la orden, la red converge a esperar (V0, también con γ = 1).
2. **El factor de descuento γ = 0,95 también es un problema.** Un costo que llega al final de una ventana de 30 pasos se ve desde el principio multiplicado por 0,95²⁹ ≈ 0,23, así que parece cuatro veces más barato de lo que es y la red lo posterga. Con la misma penalización de 30 bps, γ = 0,95 da 0 de 5 redes buenas y γ = 1 da 5 de 5.
3. **Con las dos correcciones juntas (algo que obligue a completar y γ = 1), la red llega al nivel de la mejor heurística.** En las 5 redes el costo queda en 17,9 a 18,0 bps frente a 17,91 del TWAP con órdenes límite y 20,26 de la red inicial: 2,3 bps menos, con cumplimiento de 0,95 a 1,00. Entrenadas con 5.000 acciones, también bajan el costo con 20.000 (V2: 19,68 frente a 21,13 de la red inicial y 19,31 del TWAP límite).
4. **Liquidar a la fuerza o penalizar da el mismo resultado.** Entre V1, V2, V3 y V4 (con γ = 1) las diferencias son de 0,06 bps. Se prefiere la **penalización**: se aplica con solo leer el `info` del entorno, así que funciona tal cual en ABIDES, mientras que la liquidación necesita tocar el simulador.
5. **El costo de espera denso (V5, V6) elimina la espera pero no baja el costo.** Con 100 bps repartidos en la ventana, la red compra enseguida con órdenes de mercado (76 % a 88 %) y queda en 20,4 bps, al nivel de la política agresiva. Puede que el valor sea demasiado alto; no se probaron valores menores.
6. **Los ajustes adicionales de la etapa B no mejoran la base** (V2 con γ = 1: 17,92 bps, 5 de 5):
   - tamaños y ventanas aleatorios: 20,04 bps, solo 1 de 5 redes buenas (con 1.000 episodios la variedad dificulta aprender);
   - hiperparámetros alternativos: 18,18 bps, 5 de 5;
   - arranque por imitación de la mejor heurística: 18,13 bps, 5 de 5;
   - los tres juntos: 19,66 bps, 4 de 5.
7. **A 1.000 acciones el simulador de Poisson no deja nada que aprender:** las variantes que sí operan y todas las heurísticas cuestan entre 17,7 y 18,3 bps; no hay margen para mejorar.

## 4. Límites

- Es el simulador de Poisson: no tiene impacto de precio ni tendencia y una orden límite que se llena paga lo mismo que una de mercado. Los resultados explican **por qué** la red hacía lo que hacía; **no** garantizan el mismo tamaño de mejora en ABIDES. La confirmación en ABIDES ya se corrió (26 de octubre): el arreglo evita la espera (cumplimiento ≈ 1,0). Sobre el costo, con 15 semillas parecía peor que el control (+3,0 bps) pero con 40 pasa a −2,2 bps (no significativo): **sin conclusión hasta reevaluar con 150 semillas**; ver `docs/v4_abides_resultado_parcial_A_PS.md`.
- Cinco semillas de red por variante y 1.000 episodios.
- Solo se probaron penalizaciones de 30 y 100 bps y un costo de espera de 100 bps.
- No incluye al Maestro: el Ejecutor se entrenó solo, con tamaños fijos.

## 5. Recomendación

1. Entrenar el Ejecutor con **γ = 1** y una **penalización terminal de 30 bps por cada acción del slice sin comprar** (propuesta detallada en `docs/propuesta_cambio_RE_para_BF_y_MR.md`).
2. **Confirmación en ABIDES: hecha** (4 semillas de 1.000 episodios; cumplimiento ≈ 1,0). El costo frente al control **no está resuelto**: +3,0 bps con 15 semillas, −2,2 bps con 40 (no significativo). Siguiente paso: reevaluar todas las redes con 150 semillas (`notebooks/Colab_reevaluacion_150_ABIDES.ipynb`); detalle en `docs/v4_abides_resultado_parcial_A_PS.md`.
3. Medir todo contra la red inicial muestreando y contra la mejor heurística.
4. Después de la confirmación, entrenar el Maestro sobre estos Ejecutores y repetir la evaluación del sistema completo.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
