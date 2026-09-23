# Diagnóstico y Plan a Seguir — 23 septiembre 2026

**Autor:** Paolo Sepúlveda (PS), con revisión de código asistida por Claude
**Método:** revisión directa del código (`src/`, `notebooks/`, `data/`), no solo de los documentos de planificación (`PLAN_*.md`), porque estos últimos declaran varios ítems como "✅ completado" que no lo están al inspeccionar el código real.

---

## 1. Estado real verificado (código, no planes)

| Componente | Estado real | Evidencia |
|---|---|---|
| `docs/schemas/SM_schema.json` / `SE_schema.json` | ✅ Correctos y en uso activo | `src/envs/spaces.py` los carga dinámicamente en runtime |
| ~~`SE_schema.json` shape 26 vs 27~~ | ✅ **Actualización 23 sept: no era un bug vigente.** El schema ya declaraba `shape=[27]` correctamente desde el mismo commit de Sprint 3 (`4e6b323`). Lo que había quedado desactualizado era el docstring/warning de `spaces.py`, que describía el problema como si siguiera activo. Corregido en `b95c9a0`. | `src/envs/spaces.py` |
| `MaestroEnv` / `EjecutorEnv` (Gymnasium) | ⚠️ Siguen siendo **stubs**: `reset()`/`step()` devuelven observaciones aleatorias válidas y `reward=0.0` siempre | Docstring de ambos módulos lo dice explícitamente — **sigue bloqueado, es de Mauricio/Benjamin** |
| ABIDES-Gym integrado y funcionando | ❌ **No verificado** | `src/envs/test_abides.py` usa la API vieja de `gym` (`gym.make(...)`) con IDs de entorno adivinados (`"markets-execution-v0"`, `"rmc-v0"`) dentro de un `try/except` que nunca se confirmó que pasara con éxito real — **sigue bloqueado** |
| `Dockerfile` para ABIDES | ⚠️ Probablemente falla | Clona `github.com/jpmorganchase/abides-jpmc.git`, pero el repositorio real citado en el propio Título I (sección 4.3.3.a) es `abides-jpmc-**public**` — **sigue bloqueado** |
| `src/models/actor_critic.py` (redes de Mauricio) → notebook | ✅ **Resuelto 23 sept** (`b95c9a0`): el notebook ahora importa y usa `MasterActorCritic`/`ExecutorActorCritic` reales; se agregó `BaseActorCritic.get_action_and_value()` (necesario para el rollout, no existía). Verificado ejecutando el notebook (celdas 0-12, sin las de Colab) end-to-end sin errores, y el test propio de Mauricio (`__main__`) sigue pasando intacto. | `notebooks/Training_PPO_Sprint4_PS.ipynb`, `src/models/actor_critic.py` |
| 🆕 Discrepancia de arquitectura Maestro (hallada al conectar las redes) | ⚠️ `MaestroEnv` expone `action_space` **continuo** `Box(0,1,(1,))` (versión simplificada del stub de Sprint 3), pero `MasterActorCritic` implementa el contrato **discreto oficial** `MultiDiscrete([10,4])=40` acciones de `SM_schema.json`. Faltan también los adaptadores índice→acción real para el Maestro (40 → `alpha_idx,ventana_idx`) y el Ejecutor (240 → `order_type,volume_bucket,price_level` vía `np.unravel_index`). El notebook ahora lo advierte explícitamente en vez de ocultarlo. | notebook, celda 10 — **nuevo hallazgo, sigue pendiente, es parte de la Tarea 3.1.1 (Mauricio)** |
| `ppo_update()` (Tarea 3.1.1) | ❌ Stub: retorna `{'policy_loss': 0.0, 'value_loss': 0.0, 'entropy': 0.0}` sin calcular nada | Notebook, celda 16 — **sigue bloqueado** |
| Training loop completo (rollout + GAE + updates) | ❌ No implementado | Notebook, celda 24: solo un `print` con la lista de TODOs — **sigue bloqueado** |
| Datos reales IPSA limpios (`data/processed/`) | ❓ Desconocido — no se puede confirmar desde el repo | `data/raw/` y `data/processed/` solo tienen `.gitkeep` (normal, están en `.gitignore`), pero tampoco hay notebook, reporte de calidad de datos, ni gráfico committeado que confirme que Benjamin corrió el pipeline con éxito — **sigue bloqueado** |
| `data/poisson_params_calibrated.json` | ❌ No existe en el repo | Solo existe el script `src/envs/calibration_poisson.py`; su salida nunca se generó/confirmó — **sigue bloqueado** |
| Mis tareas 3.1.4 (logging) + 3.1.5 (análisis) | ✅ Completo, probado end-to-end, mergeado | PR #8, `docs/SPRINT4_LOGGING_ANALYSIS_PS.md` |

**Conclusión central (actualizada):** el training PPO todavía no puede correr, pero ya no por un problema de conexión de redes (eso quedó resuelto hoy) — falta que Mauricio implemente el PPO loss real y el rollout loop, que alguien resuelva el desajuste continuo/discreto del Maestro, y que ABIDES-Gym quede realmente instalado y probado. Estos tres puntos son de mis compañeros, no míos.

---

## 2. Plan a seguir

### 🔴 Bloqueado — depende de otros (sin cambios respecto al diagnóstico inicial, salvo el nuevo hallazgo)

1. **Mauricio** — implementar `ppo_update()` (celda 16, el objetivo `L_CLIP` + value loss + entropy) y el training loop completo (celda 24: rollout, GAE, updates); y resolver el desajuste continuo/discreto del Maestro (`MaestroEnv` vs `MasterActorCritic`, ver hallazgo nuevo arriba) — actualizando `MaestroEnv` para exponer el espacio discreto de 40 acciones, o agregando un adaptador explícito.
2. **Mauricio/Benjamin** — verificar de punta a punta que ABIDES-Gym instala y corre: corregir la URL del repo en el `Dockerfile` (`abides-jpmc-public`, no `abides-jpmc`), y reemplazar el smoke test de `test_abides.py` por uno que realmente confirme el nombre de entorno correcto y corra sin `try/except` silencioso.
3. **Benjamin** — confirmar si los datos IPSA limpios existen en su máquina; si es así, subir al menos un `data_quality_report.txt` o notebook que lo demuestre (aunque el CSV pesado quede fuera de git).

### ✅ Resuelto por mí hoy (23 sept, commits `97f47f6`, `b95c9a0`)

1. ~~Corregir el bug de `SE_schema.json`~~ — no hacía falta, el schema ya estaba bien; se limpió el docstring de `spaces.py` que decía lo contrario.
2. Conectar `MasterActorCritic`/`ExecutorActorCritic` reales al notebook (celdas 4, 8, 10, 12), agregando el método `get_action_and_value()` que faltaba en `src/models/actor_critic.py`, y dejando explícita (no oculta) la discrepancia continuo/discreto recién descubierta.
3. Mensaje para Mauricio y Benjamin — pendiente, no se ha enviado todavía (ver sección "Bloqueado" arriba con los puntos exactos a comunicarles).

---

## 3. Nota sobre trabajo remoto (23 sept)

Esta sesión se está siguiendo desde otro dispositivo vía Remote Control del propio Claude Code (confirmado por el propio entorno: la sesión indica explícitamente que el usuario puede seguirla desde otro dispositivo y recibir archivos ahí). No hay una forma independiente de verificar el estado exacto del emparejamiento más allá de esa señal del sistema.
