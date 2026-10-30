# Leeme para BF: borradores de la 3.1.3 y la 3.2.2

**Rama:** `feature/ps-borrador-bf-liquidez` (BORRADOR de PS para BF, 29 de octubre). Todo está escrito y probado en el PC con Poisson; nada está decidido por ti. Cambia lo que quieras.

## Qué hay

| Qué | Dónde | Tarea |
|---|---|---|
| Escenarios de liquidez baja, media y alta (factores 0,5×, 1×, 2×: **propuesta, sin validar**) | `data/scenarios/escenarios_liquidez_v1.json`, `src/envs/escenarios_liquidez.py` | 3.1.3 |
| Los evaluadores del sistema y de TWAP/VWAP aceptan `--escenario` y `--factor-tamano` (0,5 / 1 / 1,5 = 5 %, 10 % y 15 % del volumen del día con las órdenes v2) | `scripts/colab/evaluar_sistema_ps.py`, `scripts/colab/benchmarks_meta_ordenes_ps.py` | 3.1.3 y 3.2.1 |
| Prueba C-6: ¿baja liquidez cuesta más? | `scripts/colab/c6_escenarios_liquidez_bf.py`, `notebooks/Colab_C6_escenarios_liquidez_BF.ipynb` | 3.1.3 |
| Consolidador: tabla maestra por escenario y tamaño (CSV, Markdown, LaTeX) | `scripts/consolidar_resultados_3_2_2.py` | 3.2.2 |
| Hoja para responder D1 y D3 | `docs/hoja_decisiones_D1_D3_BF.md` | — |

## Cinco pasos

1. **Responde D1 y D3** en `docs/hoja_decisiones_D1_D3_BF.md` (10 min). Basta con una línea, por ejemplo `D1: v2, D3: regla`.
2. **Revisa los factores** de `data/scenarios/escenarios_liquidez_v1.json` y qué parámetros escala `src/envs/escenarios_liquidez.py` (20 min). En ABIDES se escalan `num_noise_agents`, `lambda_a` y `mm_pov`; en Poisson, solo la profundidad del libro (las tasas de llegada ahí mueven el precio, así que subirlas daría más volatilidad y no más liquidez).
3. **Corre el cuaderno C-6** en Colab: «Ejecutar todas», ≈ 40 min. Debe terminar en **OK**. En Poisson ya da OK: con liquidez baja, comprar 1.000 acciones a mercado cuesta 2,5 bps más (IC 95 % de 2,3 a 2,7).
4. **Prueba el consolidador** con datos de ejemplo:
   ```bash
   PYTHONPATH=. python -m pytest tests/test_escenarios_liquidez.py -q
   ```
5. **Di qué cambiarías** o aprueba el PR.

## Límites que conviene saber

- Los factores no están validados en ABIDES: para eso es el C-6.
- En Poisson, TWAP con órdenes límite casi no cambia entre escenarios (espera en el mejor precio y no barre el libro). El C-6 decide con la compra a mercado.
- La recompensa corregida (`mid_decision`) y la penalización dentro de R_E (2.2.3) **no están aquí**: se dejan para cuando el cuaderno `Colab_mid_decision` confirme el parche (`docs/revision_opus_PS.md`).

🤖 Generado con [Claude Code](https://claude.com/claude-code)
