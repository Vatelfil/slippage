# Diagnóstico y Plan a Seguir — 23 septiembre 2026

**Autor:** Paolo Sepúlveda (PS), con revisión de código asistida por Claude
**Método:** revisión directa del código (`src/`, `notebooks/`, `data/`), no solo de los documentos de planificación (`PLAN_*.md`), porque estos últimos declaran varios ítems como "✅ completado" que no lo están al inspeccionar el código real.

---

## 1. Estado real verificado (código, no planes)

| Componente | Estado real | Evidencia |
|---|---|---|
| `docs/schemas/SM_schema.json` / `SE_schema.json` | ✅ Correctos y en uso activo | `src/envs/spaces.py` los carga dinámicamente en runtime |
| **`SE_schema.json`** | 🐛 **Bug de Sprint 1 (mío, PS)**: declara `gymnasium_space.shape=[26]`, pero la suma real de las dimensiones listadas en `variables`/`low_by_group` es **27** (privado 3 + bid_precios 5 + bid_volumenes 5 + ask_precios 5 + ask_volumenes 5 + [spread_t, OBI_t, tasa_ordenes, P_mid] 4 = 27). El propio `total_dims_breakdown` del JSON tiene el error aritmético. | `src/envs/spaces.py`, líneas 14-28 (`SCHEMA_DIM_WARNING`) — ya construye el espacio con la dimensión real (27) para no perder una variable, pero deja constancia explícita de que el JSON debe corregirse |
| `MaestroEnv` / `EjecutorEnv` (Gymnasium) | ⚠️ Son **stubs**: `reset()`/`step()` devuelven observaciones aleatorias válidas y `reward=0.0` siempre | Docstring de ambos módulos lo dice explícitamente: "Este entorno NO integra ABIDES-Gym" |
| ABIDES-Gym integrado y funcionando | ❌ **No verificado** | `src/envs/test_abides.py` usa la API vieja de `gym` (`gym.make(...)`) con IDs de entorno adivinados (`"markets-execution-v0"`, `"rmc-v0"`) dentro de un `try/except` que nunca se confirmó que pasara con éxito real (no hay log, notebook ni CI que lo pruebe) |
| `Dockerfile` para ABIDES | ⚠️ Probablemente falla | Clona `github.com/jpmorganchase/abides-jpmc.git`, pero el repositorio real citado en el propio Título I (sección 4.3.3.a) es `abides-jpmc-**public**` |
| `src/models/actor_critic.py` (redes de Mauricio) | ⚠️ **Nunca conectadas al notebook de training** | Define `BaseActorCritic` → `MasterActorCritic`/`ExecutorActorCritic`, firma `(obs_dim, action_dim, hidden_sizes=(256,256))`. El notebook (celda 12) en cambio instancia `ActorCritic(obs_dim, action_dim, hidden_dim=..., discrete=bool)` — una clase con **otra firma y otro nombre**, definida localmente en el propio notebook (celda 8, placeholder), sin ningún `import` de `src/models/actor_critic.py` |
| `ppo_update()` (Tarea 3.1.1) | ❌ Stub: retorna `{'policy_loss': 0.0, 'value_loss': 0.0, 'entropy': 0.0}` sin calcular nada | Notebook, celda 16 |
| Training loop completo (rollout + GAE + updates) | ❌ No implementado | Notebook, celda 24: solo un `print` con la lista de TODOs |
| Datos reales IPSA limpios (`data/processed/`) | ❓ Desconocido — no se puede confirmar desde el repo | `data/raw/` y `data/processed/` solo tienen `.gitkeep` (normal, están en `.gitignore`), pero tampoco hay notebook, reporte de calidad de datos, ni gráfico committeado que confirme que Benjamin corrió el pipeline con éxito |
| `data/poisson_params_calibrated.json` | ❌ No existe en el repo | Solo existe el script `src/envs/calibration_poisson.py`; su salida nunca se generó/confirmó |
| Mis tareas 3.1.4 (logging) + 3.1.5 (análisis) | ✅ Completo, probado end-to-end, mergeado | PR #8, `docs/SPRINT4_LOGGING_ANALYSIS_PS.md` |

**Conclusión central:** el training PPO no puede correr hoy, y no es (solo) un problema de datos faltantes de Benjamin — el propio código de entrenamiento (redes reales conectadas, PPO loss, rollout loop) nunca se terminó de ensamblar, pese a que los `PLAN_*.md` marcan varios de estos ítems como resueltos.

---

## 2. Plan a seguir

### 🔴 Bloqueado — depende de otros

1. **Mauricio** — conectar `src/models/actor_critic.py` (las clases reales) al notebook `Training_PPO_Sprint4_PS.ipynb` (celda 12), e implementar `ppo_update()` (celda 16, el objetivo `L_CLIP` + value loss + entropy) y el training loop completo (celda 24: rollout, GAE, updates). Esto es, en esencia, la Tarea 3.1.1 original, y sigue sin terminar.
2. **Mauricio/Benjamin** — verificar de punta a punta que ABIDES-Gym instala y corre: corregir la URL del repo en el `Dockerfile` (`abides-jpmc-public`, no `abides-jpmc`), y reemplazar el smoke test de `test_abides.py` por uno que realmente confirme el nombre de entorno correcto y corra sin `try/except` silencioso.
3. **Benjamin** — confirmar si los datos IPSA limpios existen en su máquina; si es así, subir al menos un `data_quality_report.txt` o notebook que lo demuestre (aunque el CSV pesado quede fuera de git).

### 🟡 Puedo resolver yo ahora (no depende de nadie)

1. Corregir el bug de `SE_schema.json` (`shape` 26 → 27, y el texto de `total_dims_breakdown`), y confirmar que `src/envs/spaces.py` deja de emitir el `SCHEMA_DIM_WARNING`.
2. Actualizar la celda 12 del notebook para importar y usar `MasterActorCritic`/`ExecutorActorCritic` reales de `src/models/actor_critic.py`, en vez de la clase `ActorCritic` inventada — para que al menos no falle por `NameError`/firma incompatible cuando alguien intente correrlo.
3. Enviar a Mauricio y Benjamin un mensaje concreto (archivo + línea, no "¿cómo van?") con los 3 puntos de la sección "Bloqueado" de este documento.

---

## 3. Nota sobre trabajo remoto (23 sept)

Esta sesión se está siguiendo desde otro dispositivo vía Remote Control del propio Claude Code (confirmado por el propio entorno: la sesión indica explícitamente que el usuario puede seguirla desde otro dispositivo y recibir archivos ahí). No hay una forma independiente de verificar el estado exacto del emparejamiento más allá de esa señal del sistema.
