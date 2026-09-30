# Pendiente — Mauricio (Redes + ABIDES-Gym + PPO)

**Para:** Mauricio Reynoso (MR)
**De:** Paolo Sepúlveda (PS), 27 septiembre 2026
**Rama con las correcciones ya hechas:** `fix/desbloqueo-abides-poc` (pídemela si no la tienes — está commiteada, la subo cuando confirmes)

Este documento reemplaza cualquier plan anterior que te haya llegado hoy — encontramos que tenía tareas mal asignadas (te pedía cosas que Benjamín ya hizo, y le asignaba a él cosas que son tuyas). Todo lo de acá está verificado contra el código real del repo, no supuesto.

---

## Contexto rápido: ¿por qué esto es tuyo?

Revisamos el historial de git: la configuración de ABIDES-Gym (`config-entorno-abides-y-modelos-resuelto`, 6 de septiembre) está firmada por ti. Las redes (`src/models/actor_critic.py`) también. El training loop PPO (Tarea 3.1.1 / 2.2.1) es tu área desde el día 1 ("Arquitectura IA"). Por eso esto queda en tu cancha, no en la de Benjamín.

Benjamín, mientras tanto, **ya entregó lo suyo**: datos reales del IPSA limpios y la calibración Poisson por tramo horario (`docs/calibracion_poisson_2.1.3_BF.md`), con metodología rigurosa, tests, y limitaciones documentadas con honestidad. No necesita nada de ti para eso.

---

## 1. ABIDES-Gym: instalar y confirmar que funciona (bloqueador #1)

**Qué encontramos:** el `Dockerfile` apuntaba a un repositorio de ABIDES-Gym que no existe (`abides-jpmc.git`), y con versiones de `gym`/`numpy`/`ray`/`pomegranate` que no coinciden con las que el repositorio oficial realmente fija.

**Qué ya corregí (verificado contra el README/install.sh/requirements.txt reales de `github.com/jpmorganchase/abides-jpmc-public`):**
- URL correcta del repo.
- Versiones reales: `gym==0.18.0`, `numpy==1.22.0`, `ray[rllib]==1.7.0`, `pomegranate==0.14.5`.
- Método de instalación real: clonar el repo completo y correr `python setup.py install` en `abides-core` → `abides-markets` → `abides-gym` (no `pip install git+...#subdirectory=X`, que nunca fue válido).
- `src/envs/test_abides.py`: **CORRECCIÓN (27 sept):** en la primera versión de este documento te dije que usaras `markets-daily_investor-v0`; eso fue un error mío. El entorno correcto para ejecución de órdenes es `markets-execution-v0` (que ya estaba en tu versión original; verificado en `abides_gym/__init__.py` del repo oficial, que registra solo ese y `daily_investor`). El que no existe es `rmc-v0`. Ya está corregido en el script.

**Lo que me falta a mí (no tengo Docker en mi entorno):** construir la imagen y confirmar que compila. Eso te toca a ti:

```bash
docker build -t slippage .
docker run -it slippage bash
python src/envs/test_abides.py
```

Si `test_abides.py` falla, lista los entornos realmente registrados (deberían ser solo `markets-daily_investor-v0` y `markets-execution-v0`):
```python
import gym, abides_gym
print([k for k in gym.envs.registry.env_specs.keys() if 'markets' in k])
```

⚠️ El repo de ABIDES-Gym **está archivado (read-only) desde junio 2025** — no hay soporte activo, así que cualquier ajuste fino será por tu cuenta o con parches locales.

## 2. Conectar ABIDES real a `MaestroEnv`/`EjecutorEnv` (bloqueador #2)

Ahora mismo `MaestroEnv` y `EjecutorEnv` son *stubs*: `reset()`/`step()` devuelven observaciones aleatorias y `reward=0.0` siempre (así están documentados desde que los creé en Sprint 3 — no es un bug, es intencional hasta que existiera ABIDES). Una vez que el punto 1 funcione, hay que reemplazar esa lógica dummy por llamadas reales a ABIDES-Gym.

**Ya resuelto de mi parte, no lo tienes que rehacer:** encontré y arreglé un choque de arquitectura — `MaestroEnv` tenía un espacio de acción continuo (`Box`), pero `MasterActorCritic` (tu red) produce una acción discreta de 40 valores. Agregué `MaestroDiscreteActionSpace` (en `src/envs/spaces.py`) y actualicé `MaestroEnv` para usarlo — verificado de punta a punta (la red muestrea una acción, el entorno la decodifica a `alpha_t`/`ventana_min` correctamente). Mismo arreglo para el Ejecutor (`EjecutorActionSpace.decode_flat()`, 240 acciones aplanadas ↔ `MultiDiscrete([3,10,8])`).

## 3. Revisar mi borrador de `ppo_update()` + training loop

En `notebooks/Training_PPO_Sprint4_PS.ipynb` (celdas 16 y 24) dejé una implementación completa: objetivo PPO clipeado (L_CLIP) + value loss + entropy, GAE con `gamma`=0.99 (Maestro) / `gamma_ejecutor`=0.95 (Ejecutores, según el Título I), rollout, logging y checkpoints. **La corrí completa y funciona mecánicamente** (probado con config reducido) — pero como los envs siguen siendo stubs, entrena "en el vacío" (recompensas en 0.0, entropía inicial ≈ ln(40), consistente con una política sin entrenar).

Esto es un **borrador para que tú lo revises**, no mi versión final ni la tuya — si prefieres una estructura distinta (por ejemplo, vectorizar con `num_envs=4` de verdad, que dejé pendiente), es tu criterio.

## 4. Sobre el hallazgo de Benjamín (Poisson por tramo)

Puede interesarte para calibrar el `background_config` de ABIDES-Gym o, si el punto 1 se atrasa mucho, como plan B: el Título I (sección 4.3.3.c) menciona el modelo de Poisson como **alternativa liviana** a ABIDES-Gym para simular el LOB. Benjamín ya calibró λ⁺/λ⁻/θ reales por tramo horario — si ABIDES-Gym resulta inviable de instalar, esos parámetros ya están listos para esa alternativa. Avísanos si crees que conviene evaluar ese camino en paralelo.

---

## Resumen de 1 línea

**Bloqueador real:** que ABIDES-Gym compile e instale en tu Docker. Todo lo demás (redes, espacios de acción, PPO) ya está resuelto o en borrador funcional esperando tu revisión.
