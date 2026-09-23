# Plan de Desbloqueo — 23 septiembre 2026

**Objetivo:** avanzar en los 3 puntos bloqueantes identificados en `DIAGNOSTICO_Y_PLAN_23SEP.md`, aunque formalmente sean responsabilidad de Mauricio y Benjamin — como borradores/propuestas que ellos revisan y ajustan, no como su entrega oficial.

## Ítems y factibilidad

| # | Ítem | Dueño formal | ¿Lo puedo avanzar yo? | Cómo |
|---|---|---|---|---|
| 1 | `Dockerfile` clona el repo ABIDES equivocado (`abides-jpmc` en vez de `abides-jpmc-public`) | Mauricio | ✅ Sí, es un fix concreto y verificable | Corregir la URL, confirmar contra el repo real de GitHub |
| 2 | `MaestroEnv` (continuo) incompatible con `MasterActorCritic` (discreto, 40 acciones) | Mauricio | ✅ Sí — yo definí el contrato original (`SM_schema.json`/`MaestroActionSpace`), tengo el contexto completo | Agregar el espacio discreto de 40 acciones a `MaestroEnv`, con el decode `idx -> (alpha_idx, ventana_idx)` ya definido en `maestro_ejecutor_protocol.py` |
| 3 | `ppo_update()` es un stub (celda 16) y el training loop completo no existe (celda 24) | Mauricio (Tarea 3.1.1) | ✅ Parcial — puedo dar una implementación de referencia correcta (PPO clip + GAE + rollout), **como borrador para que él la revise/ajuste**, no como su entrega final | Implementar usando `RolloutBuffer`, `get_action_and_value()` (ya agregado), y los envs stub — corre end-to-end sin ABIDES real |
| 4 | ABIDES-Gym instalado y funcionando de verdad | Mauricio/Benjamin | ⚠️ Limitado — este entorno no tiene Docker ni puede compilar las extensiones C++ de ABIDES en un tiempo razonable | Solo puedo: verificar la URL/estructura real del repo, y dejar `test_abides.py` con nombres de entorno correctos si logro confirmarlos vía documentación pública; la instalación real queda pendiente de correr en la máquina/Docker de Mauricio |
| 5 | Datos reales IPSA limpios (`data/processed/`) | Benjamin | ⚠️ Intento acotado — si hay acceso a internet desde este entorno, correr `src/data/download_ohlcv.py` yo mismo generaría datos reales utilizables | Probar la descarga; si no hay acceso o falla, reportarlo tal cual, sin inventar datos |

## Orden de ejecución

1. Corregir `Dockerfile` (ítem 1) — rápido, bajo riesgo.
2. Actualizar `MaestroEnv` para exponer el espacio discreto de 40 acciones, manteniendo compatibilidad hacia atrás donde se pueda (ítem 2).
3. Implementar `ppo_update()` real + training loop completo en el notebook, como borrador claramente marcado (ítem 3).
4. Intentar verificar el repo/env-ids reales de ABIDES-Gym y, si es posible, correr el pipeline de datos real de Benjamin (ítems 4 y 5) — reportar resultado honesto, no forzar si el entorno no lo permite.
5. Documentar todo en un `RESULTADOS_DESBLOQUEO_23SEP.md` con qué quedó resuelto, qué quedó como borrador pendiente de revisión, y qué sigue sin poder resolverse desde este entorno.

**Nota:** todo lo de este plan se hace en la rama local `fix/desbloqueo-abides-poc`, con commits locales únicamente (sin push), tal como se me pidió.
