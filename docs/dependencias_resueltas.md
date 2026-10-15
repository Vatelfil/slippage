# Dependencias resueltas: entorno de ABIDES-Gym (tarea 1.2.4)

> **Borrador** elaborado por PS con apoyo de Claude Code el 15 oct 2026; pendiente de revisión del equipo. Complementa a `docs/diagnostico_dependencias.md` (diagnóstico teórico con Docker) con **lo que realmente funcionó** en Colab, probado el 30 sept y el 10 oct de 2026.

## 1. Dos entornos distintos

| Entorno | Para qué | Archivo de versiones |
|---|---|---|
| Análisis local (Python reciente) | Análisis estadístico, pruebas, documentos | `requirements.txt` |
| ABIDES (Python 3.9, conda `abides`) | Simulador, calibración, entrenamiento | `requirements-locked.txt` |

No se mezclan: ABIDES-Gym exige versiones antiguas (gym 0.18.0, numpy 1.22.0) que rompen el entorno de análisis.

## 2. Receta probada (Colab)

1. `pip install "condacolab<0.2"` y `condacolab.install()` (reinicia el entorno a propósito). Se fija `<0.2` porque la 0.2 cambia el método de instalación y rompe la receta.
2. `conda create -n abides python=3.9`.
3. Dependencias **en pasos** (no en un solo `pip install`):
   - `pip==23.3.2 setuptools==57.5.0 wheel==0.38.4`
   - `cython<3 numpy==1.22.0`
   - `gym==0.18.0` con `--no-build-isolation --no-deps`
   - resto: `cloudpickle<1.7 pyglet<=1.5.0 Pillow<10 pandas==1.2.4 scipy==1.10.0 coloredlogs==15.0.1 psutil==5.8.0 tqdm==4.61.1 pomegranate==0.14.5 ray[tune]==1.7.0 protobuf==3.20.3 pyarrow==11.0.0 matplotlib==3.5.3 pytest`
   - `gymnasium==0.29.1 importlib-metadata>=4.8 farama-notifications` con `--no-deps`
4. ABIDES desde el repositorio oficial: `abides-core`, `abides-markets` y `abides-gym` con `setup.py install`.
5. Verificación: debe imprimir `0.18.0 1.22.0 1.2.4 0.29.1 1.7.0` (gym, numpy, pandas, gymnasium, ray).
6. Torch solo hace falta para entrenar (`torch==1.13.1+cpu`); la calibración y la validación no lo usan.
7. Todo lo que usa ABIDES se ejecuta con `conda run --no-capture-output -n abides env PYTHONPATH=. python ...`: el kernel del cuaderno no es Python 3.9.

## 3. Matriz de conflictos y solución real

| Conflicto | Síntoma | Solución aplicada |
|---|---|---|
| `gym==0.18.0` pide `Pillow<=7.2.0` | No hay rueda para Python 3.9 | Instalar `gym` con `--no-deps` y usar `Pillow<10` (solo se usa para render); el aviso de pip es esperado |
| `opencv-python>=3.` de gym 0.18.0 | pip y setuptools modernos lo rechazan | Fijar `pip==23.3.2` y `setuptools==57.5.0` antes (en un paso aparte) |
| `ray==1.7.0` no importa con `protobuf>=4` | `ImportError` al cargar ray | `protobuf==3.20.3` |
| `pomegranate==0.14.5` | Falla al compilar sin Cython y numpy previos | Instalar `cython<3` y `numpy==1.22.0` **antes** |
| `condacolab>=0.2` | Cambia el método de instalación | Fijar `condacolab<0.2` |
| `gym` y `gymnasium` conviven | API distinta de `step()` (4 frente a 5 valores) | ABIDES usa `gym` 0.18.0; el adaptador `EjecutorEnvAbides` traduce a la API de `gymnasium` |
| Kernel de Colab no es Python 3.9 | Importaciones fallan en el cuaderno | Ejecutar siempre con `conda run -n abides` |

## 4. Prueba de funcionamiento

- `src/envs/test_abides.py`: smoke test de ABIDES-Gym (termina con "ABIDES-Gym es funcional").
- `src/envs/test_abides_ejecutor.py`: un episodio completo del Ejecutor en los 3 tramos.
- Corridas de referencia: una jornada completa de `rmsc04` tarda entre 1 y 2 minutos.

## 5. Estado

El archivo `requirements-locked.txt` tiene los pines de la receta. La lista completa de paquetes (`pip freeze`) se genera en Colab con la celda de la sección 6 de este documento y se reemplaza en el archivo.

## 6. Cómo regenerar el `pip freeze` completo

En un cuaderno de Colab con el entorno `abides` ya instalado:

```python
!conda run -n abides python --version
!conda run -n abides python -m pip freeze > /content/drive/MyDrive/slippage_colab/resultados/requirements-locked_abides.txt
!conda list -n abides --export > /content/drive/MyDrive/slippage_colab/resultados/conda_export_abides.txt
```
