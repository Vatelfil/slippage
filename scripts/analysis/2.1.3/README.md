# Scripts auxiliares de la tarea 2.1.3 (BF)

Copiados tal cual desde el scratchpad de la sesión del 2026-09-26 para dejar trazabilidad; no forman parte del pipeline. Se ejecutan desde la raíz del repo y usan el snapshot 2026-08-23.

- `eda.py`: EDA por tramo de un ticker (`python scripts/analysis/2.1.3/eda.py FALABELLA`): velas imputadas, volumen, signo, rango HL, Roll y AR(1) del HL.
- `summary.py`: resumen de `data/calibration/poisson_params_2026-08-23.json` (métodos adoptados, p-valores, hecho estilizado y tabla por ticker).
- `show.py`: muestra las estimaciones directa y MLE-proxy de un ticker desde ese JSON (`python scripts/analysis/2.1.3/show.py FALABELLA`).
- `patch_center.py`: parche único ya aplicado a `src/envs/calibration_poisson.py` (commit 6e3b823), que agregó el centrado del KS; no volver a ejecutar.
