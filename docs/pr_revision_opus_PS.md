# PR: revisión técnica y corrección de la recompensa del Ejecutor en ABIDES

**Rama:** `feature/ps-revision-opus` · **Fecha:** 29 de octubre de 2026 · **Elaborado por:** PS con apoyo de Claude Code (Opus; uso de IA autorizado por la universidad).

**Título del PR:**

```
Revisión técnica: recompensa del Ejecutor en ABIDES medida contra el precio de la decisión
```

## Qué es este PR

Revisión técnica del proyecto pedida por PS (29 de octubre) y corrección de una falla en la recompensa del Ejecutor en ABIDES. El informe completo está en `docs/revision_opus_PS.md`.

## Qué se encontró

- **El entrenador PPO funciona.** En una prueba simple aprende la mejor acción en 1.000 episodios (de 0,33 a 0,999). Script: `scripts/prueba_cordura_ppo_ps.py`.
- **Falla en R_E con ABIDES:** el precio pagado se comparaba con el precio medio de 30 segundos *después* de la compra, que ya incluye el alza que provoca la propia compra. En Poisson se usa el precio de la decisión. Por eso, en las corridas V2 la recompensa casi no se relaciona con el costo (correlación 0,04 a 0,22) y una compra cara podía salir premiada.
- **Ruido:** el costo por episodio varía ≈ 16,6 bps y la mejora alcanzable por el Ejecutor es de ≈ 2 bps. Con ese ruido, 1.000 episodios no alcanzan para aprender (prueba de cordura).

## Qué cambia

- Opción `mid_decision` en `src/envs/abides_bridge.py` y `src/envs/abides_ejecutor_env.py`, y `--mid-decision` en `scripts/colab/entrenamiento_inicial_ps.py`. **Apagada por defecto:** las corridas anteriores no cambian.
- `scripts/colab/verificar_mid_decision_ps.py`: verifica el parche en ABIDES antes de entrenar.
- Cuadernos `notebooks/Colab_mid_decision_A.ipynb` y `_B.ipynb` (4 redes con la opción 0 y 2 con la opción A, con la recompensa corregida) y `notebooks/Colab_reevaluacion_mid_decision_300.ipynb`.
- Notas en 10 documentos con resultados de ABIDES: lo que concluían sobre si entrenar mejora el costo se midió con la recompensa con falla. El slippage, el cumplimiento y los benchmarks siguen siendo válidos.
- Sección 10 del memo de D3: forma de cerrar la decisión con la recompensa corregida.
- Pruebas nuevas en `tests/test_mid_decision.py`.

## Cómo verificar

```bash
PYTHONPATH=. python -m pytest tests -q
```

Pasan 359 pruebas; la única falla es la conocida, que necesita el parquet de mercado.

## Límites

- El parche está probado en el PC con datos de prueba. En ABIDES falta correr el cuaderno de verificación.
- Que la red aprenda con la recompensa corregida es una hipótesis hasta tener la reevaluación con 300 semillas.

Uso de IA (Claude Code) autorizado por la universidad.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
