# Cómo contribuir al proyecto

> **Borrador** elaborado por PS con apoyo de Claude Code el 15 oct 2026 para cerrar la tarea 1.1.2; pendiente de revisión del equipo.

Proyecto de título UTEM: sistema jerárquico de aprendizaje por refuerzo (un Maestro y tres Ejecutores, PPO) sobre ABIDES-Gym para reducir el slippage en el IPSA. Equipo: Mauricio Reynoso (MR), Benjamín Farias (BF) y Paolo Sepúlveda (PS).

## 1. Flujo de trabajo con Git

1. La rama `main` está **protegida**: no se sube directo. Todo entra por Pull Request.
2. Partir siempre de `main` actualizado: `git checkout main && git pull origin main`.
3. Una rama por tema, con nombre nuevo cada vez que se sube: `feature/<iniciales>-<tarea>-<tema>` o `fix/<iniciales>-<tema>` (por ejemplo `feature/ps-2.3.4-benchmarks`). GitHub no deja actualizar una rama ya subida: si hay que agregar cambios, usar un nombre nuevo (`-v2`).
4. Un PR por tema, con título claro y un texto que diga qué cambia, qué resultado dio (con números), qué queda como límite y a quién se pide revisión.
5. Todo PR lo revisa al menos otra persona del equipo antes de mergear (plazo de 24 horas; si no responde, se mergea con la aprobación de otro integrante).
6. Antes de subir: `python -m pytest -q` debe pasar.

## 2. Estructura del repositorio

| Carpeta | Contenido |
|---|---|
| `src/` | Código: entornos (`envs/`), redes (`models/`), análisis (`analysis/`), experimentos (`experiments/`) |
| `scripts/` y `scripts/colab/` | Programas de línea de comandos; los de `colab/` corren en Colab con ABIDES |
| `tests/` | Pruebas automáticas (pytest) |
| `data/calibration/` | Calibraciones y resultados versionados (JSON) |
| `data/colab_resultados/` | Resultados de corridas de Colab que se versionan |
| `data/raw/`, `data/processed/` | Datos del IPSA; los `.parquet` **no se suben** a GitHub |
| `docs/` | Documentación técnica, un archivo por tarea |
| `notebooks/` | Cuadernos de Colab y de análisis |

## 3. Documentación

- Cada tarea deja un archivo en `docs/` que dice qué se hizo, cómo se corre y qué resultado dio (con números).
- Todo documento termina con quién lo elaboró y quién debe revisarlo ("elaborado por X con apoyo de Y, pendiente de revisión por Z").
- Las desviaciones respecto del Título I se anotan en `DESVIACIONES_TITULO1_VS_IMPLEMENTACION.md`.
- Una tarea se da por cerrada solo cuando se cumplen los entregables del Excel `plan-desarrollo-titulo-2.xlsx`, o cuando el límite queda demostrado y escrito (estado "hecho con límite").

## 4. Entornos y ejecución

- **Análisis local:** `requirements.txt` (Python reciente; pandas, scipy, pytest).
- **ABIDES (simulador principal):** requiere Python 3.9 con versiones fijadas; se corre en Colab. Receta y versiones en `docs/dependencias_resueltas.md` y `requirements-locked.txt`.
- Los scripts de Colab son reanudables y guardan el avance en Drive; se lanzan con `conda run --no-capture-output -n abides env PYTHONPATH=. python scripts/colab/<script>.py ...`.

## 5. Convenciones de código

- Python con tipos donde aporte claridad; funciones puras cuando se pueda (la lógica sin ABIDES va aparte del pegamento con ABIDES, para poder probarla localmente).
- Nombres en español para conceptos del dominio (tramo, cumplimiento, meta-orden) y en inglés para la infraestructura estándar.
- Las semillas se fijan siempre y se registran en el resultado.
- Los criterios de decisión se escriben **antes** de ver los datos; los resultados negativos se reportan como tales.
- Mensajes de commit con la tarea entre paréntesis, por ejemplo `feat(2.3.4): ...`.
