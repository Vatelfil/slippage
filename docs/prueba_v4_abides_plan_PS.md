# Prueba V4 en ABIDES: recompensa contra el precio de llegada (qué se prepara y cómo leer el resultado)

**Elaborado por:** PS con apoyo de Claude Code (uso autorizado por la universidad), 26 de octubre de 2026. **No actualiza el Título II.** Es una prueba de PS en el entorno de pruebas; no modifica archivos de MR ni de BF.

## 1. Para qué

La confirmación en ABIDES de la penalización con γ = 1 (`docs/confirmacion_abides_penalizacion_resultado_PS.md`) evitó que la red se quedara esperando (cumplimiento ≈ 1,0) pero no bajó el costo: +3,0 bps sobre la red sin entrenar, 0 de 4 redes mejores. La recompensa original (R_E) compara cada compra con el precio medio de ese instante, así que **no ve cuánto cuesta llenarse tarde** cuando el precio sube.

La variante **V4** cambia solo eso: la recompensa de cada compra es lo que cuesta frente al **precio de llegada** de la orden (el mismo punto de comparación con el que se mide el slippage), y mantiene la penalización de 30 bps por lo no comprado y γ = 1. Hipótesis: si la recompensa ve el costo real, la red dejará de preferir órdenes que se llenan tarde.

## 2. Qué se prepara (nada de esto se corrió todavía)

- `scripts/colab/entrenamiento_inicial_ps.py`: opción nueva `--recompensa is_llegada` (por defecto `original`, así las corridas anteriores no cambian). Solo entra a la firma de la corrida cuando se usa.
- `notebooks/Colab_V4_ABIDES_A.ipynb` (semillas de red 1000 y 2000) y `Colab_V4_ABIDES_B.ipynb` (3000 y 4000): celdas 1 a 9 de preparación, dos entrenamientos de 1.000 episodios con 40 semillas de evaluación, el control (misma red sin entrenar, muestreando, en esas mismas 40 semillas) y el zip final. Cada cuaderno escribe en su carpeta de Drive (`v4_pen30_g1_A` y `v4_pen30_g1_B`).
- `scripts/comparar_v4_vs_v2_ps.py`: compara por semilla de red V4, V2 (la confirmación anterior) y el control, en las mismas semillas de evaluación.
- Tiempo: unos **120 minutos por cuaderno** (los dos corren a la vez en Colab gratis).

## 3. Cómo se lee el resultado

| Resultado | Qué significa | Qué se haría |
|---|---|---|
| V4 cuesta **menos** que el control en la mayoría de las redes y mantiene cumplimiento ≈ 1 | La recompensa original no veía el costo de llenarse tarde; la propuesta a BF y MR pasa a incluir también este cambio en R_E | Preparar la propuesta ampliada (borrador para BF y MR) y repetir con más episodios |
| V4 cuesta **igual que V2** (≈ +3 bps sobre el control) | El problema no es la recompensa: la política sigue casi uniforme tras 1.000 episodios, o ABIDES necesita mucho más entrenamiento | Probar más episodios y otros hiperparámetros con MR, y declarar el límite |
| V4 cuesta **más** o pierde cumplimiento | Esa recompensa no sirve con este presupuesto | Dejarlo documentado como descartado |

Con 40 semillas de evaluación se detectan diferencias de unos 4 bps o más entre una red y el control; con menos de eso, el resultado es solo orientativo.

## 4. Cómo verificarlo cuando lleguen los zip

```bash
python scripts/comparar_v4_vs_v2_ps.py --v4-dir <carpeta_con_los_zip_descomprimidos> --out-md docs/v4_vs_v2_ABIDES_PS.md --out-png data/analysis/v4_vs_v2_ABIDES.png
python scripts/monitorear_entrenamiento.py --dir <carpeta_con_los_zip_descomprimidos>
PYTHONPATH=. python -m pytest tests/test_comparar_v4_vs_v2.py tests/test_variantes_recompensa.py
```

🤖 Generado con [Claude Code](https://claude.com/claude-code)
