# Resultados del Desbloqueo — 23 septiembre 2026

Ejecución de `PLAN_DESBLOQUEO_23SEP.md`. Todo esto son **borradores/correcciones para que Mauricio y Benjamin revisen y ajusten** — no reemplazan su trabajo ni su criterio, pero dejan al equipo con menos bloqueos de los que tenía esta mañana.

**Rama:** `fix/desbloqueo-abides-poc` (commits locales, sin push, según lo pedido).

---

## 1. `Dockerfile` de ABIDES-Gym — corregido con datos verificados

Verifiqué contra el repositorio real (`https://github.com/jpmorganchase/abides-jpmc-public`, vía su README e `install.sh`/`requirements.txt`):

- La URL que usaba el Dockerfile (`abides-jpmc.git`) **no existe**; la correcta es `abides-jpmc-public`.
- Las versiones pineadas eran incorrectas: el repo real fija `gym==0.18.0`, `numpy==1.22.0`, `ray[rllib]==1.7.0`, `pomegranate==0.14.5` (no `0.21.0`/`1.23.5`/`2.2.0`/`0.14.8` como decía el Dockerfile anterior).
- `setuptools==65.5.0` (el valor anterior) **contradecía la propia mitigación** descrita en `docs/diagnostico_dependencias.md` (que pide setuptools <58 para conservar soporte 2to3).
- El método de instalación real no es `pip install git+...#subdirectory=X` (nunca fue válido para estos subpaquetes) sino clonar el repo completo y correr `python setup.py install` en `abides-core` → `abides-markets` → `abides-gym`, en ese orden — así quedó reescrito.
- `docs/diagnostico_dependencias.md` actualizado con estos mismos datos verificados, y con la nota de que el repo **fue archivado (read-only) el 2 de junio de 2025**.

⚠️ **No pude construir ni ejecutar esta imagen** (no hay Docker en este entorno). Mauricio debe construirla y confirmar si compila.

## 2. `test_abides.py` — nombre de entorno real, no adivinado

> **CORRECCIÓN 27 sept:** lo que sigue estaba mal. `"markets-execution-v0"` SÍ existe (es el entorno de ejecución de órdenes); solo `"rmc-v0"` no existe. Verificado en `abides_gym/__init__.py` del repo oficial. `test_abides.py` ya usa `markets-execution-v0`.

(Texto original, incorrecto:) La versión anterior probaba `"markets-execution-v0"` y `"rmc-v0"`, ninguno de los cuales existe según el README oficial.

⚠️ **Tampoco pude ejecutar este script** (ABIDES-Gym no está instalado aquí). Mauricio debe correrlo dentro del contenedor y confirmar.

## 3. `MaestroEnv` — resuelto el choque continuo/discreto con `MasterActorCritic`

Este sí lo pude resolver y **verificar de punta a punta**:

- Agregué `MaestroDiscreteActionSpace` (`Discrete(40)`) a `src/envs/spaces.py`, con `decode()`/`encode()` consistentes con `ALPHA_VALUES`/`VENTANA_MIN_VALUES` de `maestro_ejecutor_protocol.py`.
- `MaestroEnv.action_space` ahora usa ese espacio (antes era `Box` continuo).
- Agregué también `EjecutorActionSpace.decode_flat()`/`encode_flat()` (con `np.unravel_index`/`np.ravel_multi_index`) para el mismo problema en el Ejecutor (240 acciones aplanadas ↔ `MultiDiscrete([3,10,8])`).
- **Probado:** round-trip encode/decode para los 240 valores del Ejecutor; y el flujo completo `MasterActorCritic.get_action_and_value() → MaestroEnv.step()` y `ExecutorActorCritic.get_action_and_value() → decode_flat() → EjecutorEnv.step()` corriendo sin errores.

## 4. `ppo_update()` + training loop completo — borrador de referencia

Implementé en el notebook (`notebooks/Training_PPO_Sprint4_PS.ipynb`):
- `ppo_update()`: objetivo PPO clipeado (L_CLIP) + value loss (MSE) + entropy bonus, con normalización de advantages y grad clipping.
- `run_ppo_epochs()`: corre las épocas/minibatches sobre el buffer.
- Training loop completo (celda 24): rollout del Maestro y de los 3 Ejecutores → GAE (con `gamma`=0.99 para el Maestro y el nuevo `gamma_ejecutor`=0.95 para los Ejecutores, tal como fija el Título I) → PPO updates → `log_metrics()` → `save_checkpoint()`.

**Verificado ejecutando el notebook completo** (config reducido solo para la prueba: `rollout_steps=32`, `total_timesteps=64`) de punta a punta sin errores. La entropía inicial registrada (~3.686) coincide con `ln(40)≈3.689` — la política arranca casi uniforme, como corresponde antes de entrenar. Los losses de policy/value son números reales, no los ceros del stub anterior.

⚠️ **Las recompensas son 0.0** porque `MaestroEnv`/`EjecutorEnv` siguen siendo stubs sin ABIDES real — así que las curvas de retorno saldrán planas hasta que el punto 1-2 (ABIDES real) esté resuelto. Esto está documentado explícitamente en el propio notebook para que nadie lo confunda con un bug del logging (que sí está probado con datos sintéticos desde la Tarea 3.1.5).

Este es un **borrador**: Mauricio debe revisar hiperparámetros, la falta de vectorización real (`num_envs=4` está en `config` pero el loop de referencia corre 1 env por agente en serie), y decidir si esta es la forma en que quiere estructurar su Tarea 3.1.1 o prefiere rehacerla.

## 5. Datos reales de IPSA — pipeline completo corrido con éxito

Esto no lo esperaba poder resolver, pero el entorno sí tenía acceso a internet:

1. `python src/data/download_ohlcv.py` → **84,987 filas reales** de las 30 acciones del IPSA (yfinance, 5 min, 60 días) en `data/raw/ohlcv_5m_2026-09-23/`.
2. `python src/data/clean_ohlcv.py` → limpieza real (140,400 filas finales) en `data/processed/clean_5m_2026-09-23/`, con 15 tickers Tier A (cobertura ≥60%) y 15 Tier B.
3. `python src/features/build_sm_features.py` → features S_M (tau_t, volatilidad, vol_promedio, sesión) reales en `data/processed/sm_features_2026-09-23/`.
4. Calibración Poisson sobre datos reales (`scripts/run_poisson_calibration_real.py`, script nuevo que escribí para esto — ver punto 5b) → `data/poisson_params_calibrated.json` con datos **reales**, no sintéticos.

**Hallazgo adicional:** el loader de `calibration_poisson.py` (`load_clean_data`) esperaba archivos `<TICKER>_clean.parquet`, pero `clean_ohlcv.py` los guarda como `<TICKER>.parquet` (sin sufijo `_clean`) — otra discrepancia de contrato entre componentes, análoga a la de MaestroEnv/MasterActorCritic. No decidí unilateralmente cuál convención debe "ganar"; escribí `scripts/run_poisson_calibration_real.py` como un driver que carga los parquet reales directamente, sin tocar ninguno de los dos archivos. Benjamin/Mauricio deberían acordar y unificar el nombre de archivo.

**Resultado honesto de la calibración (no maquillado):** 0 de 15 tickers Tier A pasaron el test KS (p-value > 0.05) — el modelo de Poisson simple no captura la dinámica real de los retornos del IPSA (colas pesadas, clustering de volatilidad). Esto es información de calibración legítima para reportar en la tesis (el propio módulo de Mauricio anticipaba esta posibilidad en su docstring), no un error del script.

⚠️ **Los datos crudos/limpios (parquet) no se subieron a git** — siguen excluidos por `.gitignore` (`data/raw/*`, `data/processed/*`), respetando la convención ya existente del equipo. Solo se commitean los JSON de resumen (`data/poisson_params_calibrated.json` y el detalle por ticker), que ya no son sintéticos.

**Para reproducir en otra máquina:** correr en orden `download_ohlcv.py` → `clean_ohlcv.py` → `build_sm_features.py` → `scripts/run_poisson_calibration_real.py`. Los tres primeros son de Benjamin y ya funcionan (los corrí tal cual, sin tocarlos).

---

## Resumen de archivos tocados

| Archivo | Qué cambió |
|---|---|
| `Dockerfile` | Reescrito con URL/versiones reales verificadas contra el repo oficial |
| `docs/diagnostico_dependencias.md` | Corregido con las mismas versiones reales |
| `src/envs/test_abides.py` | Corregido dos veces; entorno correcto: `markets-execution-v0` (ver corrección 27 sept) |
| `src/envs/spaces.py` | + `MaestroDiscreteActionSpace`, + `EjecutorActionSpace.decode_flat/encode_flat` |
| `src/envs/maestro_env.py` | `action_space` ahora `Discrete(40)`, compatible con `MasterActorCritic` |
| `notebooks/Training_PPO_Sprint4_PS.ipynb` | `ppo_update()` real, training loop completo, ambos verificados por ejecución |
| `scripts/run_poisson_calibration_real.py` | Nuevo — calibra Poisson sobre datos reales (no sintéticos) |
| `data/poisson_params_calibrated.json` + `..._por_ticker.json` | Regenerados con datos reales |

## Lo que sigue sin poder resolverse desde este entorno

- Construir y correr el Dockerfile de verdad (sin Docker aquí).
- ~~Confirmar el entorno correcto~~ Resuelto 27 sept: es `markets-execution-v0`.
- Integrar ABIDES-Gym de verdad en `MaestroEnv`/`EjecutorEnv` (siguen siendo stubs) — el training loop del punto 4 ya está listo para recibir recompensas reales en cuanto eso exista.
