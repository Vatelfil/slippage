# 1.2.3 Prueba de concepto de ABIDES-Gym: evidencia

> **Borrador** elaborado por PS con apoyo de Claude Code el 15 oct 2026; pendiente de revisión del equipo. El plan pedía el notebook `notebooks/mauricio/poc_abides_gym.ipynb`; ese archivo no está en el repositorio. Este documento reúne la evidencia que cubre la tarea y deja a quien corresponda decidir si basta o si se sube además el notebook.

## 1. Qué pedía la tarea

ABIDES-Gym funcionando en Python 3.9, una simulación de un día completo de `rmsc04` y la verificación de la forma del estado del Ejecutor.

## 2. Evidencia disponible en el repositorio

| Requisito | Evidencia |
|---|---|
| ABIDES-Gym instalado en Python 3.9 | Receta y verificación de versiones en `notebooks/Colab_Sprint4_BF.ipynb` y `docs/dependencias_resueltas.md` (celdas 1 a 5). La salida esperada `0.18.0 1.22.0 1.2.4 0.29.1 1.7.0` se obtuvo en Colab el 30 sept y el 10 oct de 2026 |
| Prueba de humo | `src/envs/test_abides.py` termina con "ABIDES-Gym es funcional" (ejecutada en Colab el 10 oct; recompensa -0,25 en un paso de ejemplo) |
| Un episodio del Ejecutor en los 3 tramos | `src/envs/test_abides_ejecutor.py` |
| Día completo de `rmsc04` | Corridas de la validación 2.2.5: 90 jornadas por modo, de 66 a 117 s cada una (`data/colab_resultados/validacion_2_2_5_*.json`) |
| Forma de S_E | **27 dimensiones** (el plan decía 26; se amplió a 27 en la formalización de espacios, tarea 2.1.4). Verificada en `tests/test_abides_bridge.py` y en `src/envs/abides_bridge.py` (`OBS_DIM = 27`) |

## 3. Diferencias con el plan

- El notebook con el nombre del plan no existe; la receta quedó repartida en `notebooks/Colab_Sprint4_BF.ipynb` y en este documento.
- S_E tiene 27 variables, no 26 (documentado en `docs/schemas/SE_schema.json`).

## 4. Estado

"Hecho con evidencia equivalente". Para cerrar sin dudas, el equipo decide una de dos cosas: aceptar esta evidencia, o agregar el notebook `notebooks/poc_abides_gym.ipynb` con las celdas 1 a 8 de la receta y una corrida de un día completo.
