# Calibración de `rmsc04` para COPEC (P4, Sprint 5)

**Elaborado por:** PS con apoyo de Claude Code, 18 oct 2026. **Pendiente de revisión por:** BF. Mismo procedimiento que FALABELLA (`docs/calibracion_rmsc04_2.2.4_BF.md`): base, grilla de 27 configuraciones con 3 semillas, refinamiento y validación con 10 semillas. Archivo: `data/calibration/rmsc04_ipsa_COPEC_2026-08-23.json` (se carga con `load_abides_kwargs` y `make_calibrated_env_factory(..., ticker="COPEC")`).

## 1. Configuración elegida

`num_noise_agents = 250`, `lambda_a = 1,425e-12`, `mm_pov = 0,025`, `mm_window_size = 90`, `mm_level_spacing = 0,1`; `r_bar = 61300` (décimos de CLP) y `fund_vol` por tramo (0,000356 apertura, 0,000240 media jornada, 0,000277 cierre).

Se usó una grilla con **menos actividad** que la estándar (250, 500 y 1000 agentes; `scripts/colab/grid_specs/p4_copec_ecl_actividad_baja.json`), porque el volumen real por vela de COPEC (4.210 / 5.525 / 7.472 acciones) es menor que el de FALABELLA y con 1000 agentes el simulador producía más de 10 mil. La mejor configuración con 1000 agentes quedó en el sexto lugar (pérdida 9,0 frente a 4,8); la ganadora usa 250.

## 2. Resultado de la validación (10 semillas)

| Tramo | Volatilidad sim / objetivo (bps) | Volumen por vela sim / objetivo | Spread sim (bps) | KS D | D / D crítico | Curtosis sim / real |
|---|---|---|---|---:|---:|---|
| Apertura | 27,1 / 31,8 | 3.700 / 4.210 | 0,62 | 0,245 | 2,40 | 0,98 / 9,81 |
| Media jornada | 27,7 / 21,4 | 3.814 / 5.525 | 1,04 | 0,262 | 3,01 | 1,33 / 4,22 |
| Cierre | 28,9 / 24,8 | 4.078 / 7.472 | 1,02 | 0,310 | 3,14 | 1,46 / 47,06 |

Pérdida de búsqueda 4,84; pérdida de validación 5,91. Rankings entre tramos: el volumen por vela crece de la apertura al cierre (coincide); la volatilidad máxima **no** cae en la apertura (no coincide).

## 3. Lectura

- **Escala:** la volatilidad simulada queda a menos de 30 % del objetivo en los tres tramos (15 % por debajo en la apertura, 29 % y 17 % por encima en media jornada y cierre) y el volumen por vela queda entre 12 % y 45 % por debajo del real; con la configuración estándar habría quedado entre 1,6 y 2,5 veces por encima.
- **Forma:** el KS rechaza con claridad (D / D crítico entre 2,4 y 3,1; en FALABELLA fue entre 1,0 y 1,75). COPEC tiene colas muy pesadas en los datos reales (curtosis de 4 a 47) y el simulador no las reproduce (curtosis ≈ 1).
- **Spread:** 0,6 a 1,0 bps frente a 2,6 a 3,1 (Corwin-Schultz) y 21 a 31 (Roll): queda muy por debajo, el mismo límite que FALABELLA.
- **Uso:** sirve para comparar políticas en COPEC, no para afirmar niveles absolutos de slippage.

## 4. Pendiente

- Validación formal de 30 semillas por tramo (`scripts/colab/validacion_2_2_5_ps.py --ticker COPEC`), con pruebas de Mann-Whitney, Kruskal-Wallis y tamaño de efecto.
- Los JSON de la grilla y del refinamiento están en Drive (`slippage_colab/resultados/p4/`); no se versionan por tamaño.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
