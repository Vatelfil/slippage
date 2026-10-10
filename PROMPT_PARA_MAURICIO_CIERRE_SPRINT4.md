# Prompt para Mauricio — Cierre del Sprint 4 (10 oct 2026)

Copia todo lo que está bajo la línea y pégalo en tu sesión de Claude Code (o la IA que uses), parado dentro de tu clon de `slippage`, después de `git pull origin main`.

Documento elaborado por Paolo Sepúlveda (PS) con apoyo de Claude Code. Lo que dice "PS hizo" está en ramas ya subidas y pendiente de tu revisión.

---

## Contexto

Trabajo de título UTEM: sistema jerárquico de RL (PPO) con un Maestro y 3 Ejecutores sobre ABIDES-Gym (`rmsc04`); el simulador de Poisson es solo el plan B. Tú eres el responsable de las redes y el PPO (2.2.1 y 2.2.2, entregadas en el PR #20). El Sprint 4 terminaba el 9 de octubre y PS cerró lo pendiente de todos para no arrastrarlo al Sprint 5 (12–23 oct).

Reglas del repo: `main` está protegida; no se puede actualizar una rama ya subida (usa un nombre nuevo en cada push) y se abre PR por la web. Antes de subir: `python -m pytest -q` (hoy en main: 187 passed, 8 skipped).

## 1. Cosas de PS que usan o tocan lo tuyo

| Rama | Qué trae | Qué te toca |
|---|---|---|
| `feature/ps-2.1.2-fabrica-redes` | `src/models/networks_factory.py`: `make_master_network()`, `make_executor_networks()` (3 instancias independientes: apertura, media jornada, cierre) y `make_hierarchy()`. Nota en `docs/desviaciones_2.1.2.md` | Verificar que respeta tu `ExecutorActorCritic`/`MasterActorCritic` (7→40 y 27→240) y opinar sobre dejar la cabeza totalmente discreta |
| `feature/ps-2.2.3-beta-fase2-v2` | `src/experiments/beta_phase2.py`: entrena un Ejecutor por cada β con **tu** `RolloutBuffer` y `ppo_update` (de `experiments/test_ppo_short_run.py`) y `ExecutorActorCritic`. Hiperparámetros: gamma 0,95, GAE 0,95, lr 3e-4, clip 0,2, entropía 0,01, 4 épocas, minibatch 64, 10 episodios por actualización | Revisar que el uso de tu PPO sea correcto y que esos hiperparámetros te parezcan razonables |
| `fix/ps-poisson-nivel-limite` | Corrige el nivel de precio de `PoissonLOBSimulator.execute_limit_buy` (estaba invertido) | Solo informarte: afecta a quien use el fallback de Poisson |

## 2. Resultado que te afecta (fase 2 de β, 2.2.3)

Con PPO en ABIDES calibrado (tramo apertura, 300 episodios por β):

| β | Slippage (bps) | Cumplimiento |
|---|---:|---:|
| 0 (control) | 5,12 | 0,973 |
| 0,1×β\* | 4,71 | 1,000 |
| 0,3×β\* | 5,77 | 0,341 |
| 1×β\* | sin ejecuciones | 0 |

Con β alto la red aprende a **no operar**: R_E = (P_mid − P_ejec)·q − β·σ²·q penaliza el riesgo en proporción a lo ejecutado, así que no ejecutar sale gratis. Esto toca el diseño de la recompensa y también al Maestro, así que conviene que lo converses con BF (dueño de la 2.2.3): ¿el riesgo debería medirse sobre el inventario **pendiente**? PS no lo cambió.

## 3. Pendientes menores de tu parte: PS ya los hizo (rama `fix/ps-mr-torch-perezoso-y-semilla`, falta que los revises)

Los 4 puntos de abajo quedaron hechos en esa rama con tests; revisa que estés de acuerdo y mergea. Se dejan descritos para que sepas qué cambió.

1. **Semilla de torch en `experiments/calibrate_lambda_maestro.py`:** hoy usa `np.random.default_rng(seed)` pero no fija `torch.manual_seed(seed)`, así que las políticas sin entrenar no son reproducibles entre corridas. Agregar `torch.manual_seed(seed)` al inicio de `run_lambda_experiments`.
2. **`import torch` perezoso en `src/envs/maestro_ejecutor_protocol.py`** (hoy línea 40, a nivel de módulo): moverlo dentro de las funciones que lo usan, para que el orquestador se pueda importar en entornos sin torch (por ejemplo el entorno `abides` de Colab).
3. **Redacción de la calibración de λ:** el documento debe decir "calibración por escala con política sin entrenar; **revalidar al entrenar**" (λ = 0,05 es provisional). No es una calibración definitiva.
4. **Tests** para los puntos 1 y 2 (por ejemplo: dos corridas con la misma semilla dan el mismo resultado; `import src.envs.maestro_ejecutor_protocol` no importa torch hasta que se usa).

## 4. Para el Sprint 5 (tareas tuyas, no urgentes hoy)

- Revalidar λ cuando el Maestro tenga entrenamiento real (Sprint 5–6).
- Entrenamiento PPO completo de los 3 Ejecutores y del Maestro cuando BF cierre β y la calibración.
- Decidir con BF/PS si el corte entre apertura y media jornada se unifica: S_M corta a las 11:00 y los Ejecutores a las 11:30 (discrepancia documentada en `src/config/market_params.py`).

## 5. Qué NO hacer

- No cambies `src/analysis/` ni los informes de PS sin avisarle.
- No presentes como final nada de lo de PS: todo es "elaborado por PS con apoyo de Claude Code, pendiente de revisión".

## 6. Lista corta

- [ ] Revisar las ramas `feature/ps-2.1.2-fabrica-redes` y `feature/ps-2.2.3-beta-fase2-v2`.
- [ ] Hacer los 4 pendientes menores de la sección 3 (una rama nueva, un PR).
- [ ] Conversar con BF el punto de diseño de R_E (sección 2).
