# Diagnóstico y Mitigación de Conflictos de Dependencias: ABIDES-Gym

Al intentar integrar **ABIDES-Gym** en un entorno moderno para simulaciones de *Reinforcement Learning* (RL) y *Limit Order Books* (LOB), surgen comúnmente varios conflictos de dependencias debidos a la rápida evolución del ecosistema de IA y Python.

A continuación, se detalla un diagnóstico de los conflictos más comunes (especialmente con `gym`, `ray` y `pomegranate`) y la estrategia de mitigación empleada mediante el contenedor aislado en Python 3.9.

## 1. Conflicto con `gym` (OpenAI Gym)

### Diagnóstico
*   **Problema:** ABIDES-Gym y muchas librerías de RL antiguas fueron escritas utilizando la API clásica de `gym` (versiones `0.21.0` o anteriores). En la versión `0.26.0` y posteriores (y su transición a `gymnasium`), la API de la función `step()` cambió de devolver 4 valores `(obs, reward, done, info)` a 5 valores `(obs, reward, terminated, truncated, info)`. Además, la función `reset()` ahora devuelve `(obs, info)` en lugar de solo `obs`.
*   **Impacto:** Instalar la última versión de `gym` (o `gymnasium`) rompe los entornos de ABIDES que no han sido actualizados, produciendo errores de desempaquetado de tuplas (*ValueError: too many values to unpack*).

### Mitigación
*   **Fijar la versión de Gym:** Forzar la instalación de `gym==0.21.0`.
*   **Versión de Python:** Python 3.9 es ideal porque versiones más recientes de Python (3.11+) tienen problemas de compatibilidad en la compilación de `gym==0.21.0` debido a la herramienta `setuptools`.

## 2. Conflicto con `ray` / `rllib`

### Diagnóstico
*   **Problema:** `ray[rllib]` tiene una matriz de compatibilidad estricta tanto con la versión de Python, con la versión de `gym`, y con librerías de red (como `grpcio` o `protobuf`). Versiones muy recientes de `ray` (3.x) eliminaron soporte nativo para `gym==0.21.0` o requieren `gymnasium`.
*   **Impacto:** Fallos en la serialización de entornos, errores de inicialización de los workers o incompatibilidad directa en la API de los entornos de RL.

### Mitigación
*   **Versión de Ray probada:** Utilizar una versión estable de Ray (por ejemplo, `ray[rllib]==2.2.0` o la última versión de 1.x dependiendo de las customizaciones) que mantenga retrocompatibilidad con `gym==0.21.0` y Python 3.9.
*   Se instalarán en el contenedor base comprobando la sintaxis del algoritmo PPO (actor-crítico).

## 3. Conflicto con `pomegranate`

### Diagnóstico
*   **Problema:** `pomegranate` (usado frecuentemente en ABIDES para modelos probabilísticos o Hidden Markov Models para simular agentes de fondo) está altamente optimizado con **Cython**. En sus versiones más antiguas (`0.14.x`), la instalación falla drásticamente si no encuentra `numpy` y `cython` preinstalados en el entorno antes de compilar sus binarios C. Además, es incompatible con `numpy>=1.24.0` donde se removieron ciertos alias numéricos.
*   **Impacto:** Error en la etapa de `Building wheel for pomegranate` o *ImportError* al ejecutar simulaciones de background de ABIDES.

### Mitigación
*   **Instalación secuencial y pin de Numpy:**
    1. Instalar y fijar `numpy<1.24.0` (ej: `numpy==1.23.5`) y `cython`.
    2. Instalar `pomegranate==0.14.8` *después* de numpy/cython para que el build se complete correctamente en el contenedor Docker.

## 4. Conflictos menores adicionales (Pandas y PyArrow)

### Diagnóstico
Las versiones recientes de `pandas` deprecación de `append()` (usado a menudo en logs de ABIDES) y obligan al uso de `pd.concat()`. `pyarrow` también suele presentar desajustes de versiones si los binarios no pre-existen para ciertas arquitecturas.

### Mitigación
Aislar la corrida experimental en el contenedor Docker asegura que cualquier parche necesario al código fuente de ABIDES (como reemplazar `append()` con `concat()`) se pueda probar sin destruir el entorno local base del usuario.

## Resumen del Entorno de Prueba (Docker)

**Corrección (23 sept 2026, PS):** las versiones listadas originalmente en esta sección (`gym==0.21.0`, `numpy==1.23.5`, `ray[rllib]==2.2.0`, `pomegranate==0.14.8`) no coincidían con las que el propio repositorio oficial de ABIDES-Gym fija en su `requirements.txt`. Verificado contra `https://github.com/jpmorganchase/abides-jpmc-public` (repo real — el `Dockerfile` anterior apuntaba además a una URL de repo inexistente, `abides-jpmc.git`):

El `Dockerfile` actualizado establece:
*   `python:3.9.18-slim`
*   `numpy==1.22.0` y `cython` (instalados primero)
*   `gym==0.18.0`
*   `pandas==1.2.4`, `scipy==1.10.0`, `coloredlogs==15.0.1`, `psutil==5.8.0`, `tqdm==4.61.1`
*   `pomegranate==0.14.5`
*   `ray[rllib]==1.7.0`
*   `setuptools==57.5.0` (no 65.5.0 — debe ser **menor a 58** para conservar soporte 2to3, tal como esta misma sección 5 recomienda; la versión anterior del Dockerfile se contradecía a sí misma en este punto)
*   Instalación de ABIDES-Gym: `git clone` del repo completo + `python setup.py install` en `abides-core`, `abides-markets`, `abides-gym` (en ese orden) — el método real documentado en `install.sh` del repo oficial, no `pip install git+...#subdirectory=X` (que nunca fue una forma válida de instalar estos subpaquetes)

⚠️ **Nota de alcance:** esta corrección se hizo sin Docker disponible en el entorno donde se aplicó, por lo que las versiones están verificadas contra la documentación oficial pero la construcción completa de la imagen (compilación de `pomegranate` con Cython, etc.) sigue sin confirmarse de punta a punta. Mauricio debe construir la imagen y reportar cualquier fallo.

⚠️ **El repositorio `abides-jpmc-public` fue archivado (read-only) el 2 de junio de 2025** — no habrá más actualizaciones/parches upstream; cualquier bug futuro debe resolverse con forks o parches locales.

Esto provee un *sandbox* estable y predecible donde los agentes CTDE y PPO podrán ejecutarse interactuando con el LOB sin fallos repentinos de infraestructura.

## 5. Conflicto Directo de ABIDES-Gym con Python 3.9+

### Diagn�stico
La instalaci�n base de abides-gym a veces requiere dependencias antiguas que entran en conflicto con setuptools >= 58.0.0 (ya que elimin� el soporte de 2to3). Adem�s, algunos paquetes subyacentes requieren CMake y compiladores en Linux para construir extensiones C++ en las que se basa la simulaci�n del Order Book.

### Mitigaci�n Aplicada
En el Dockerfile se introdujo la instalaci�n de uild-essential, cmake, y la degradaci�n (downgrade) o fijaci�n de setuptools y wheel, previo a instalar las bibliotecas requeridas. Esto permite que pip resuelva e instale los binarios correctos de ABIDES-Gym bajo Python 3.9.18 de manera fluida y sin arrojar errores de 'Failed building wheel'.

### Ajuste Adicional de Pip
Al construir el contenedor, la instalación de gym==0.21.0 también falla si la versión de pip es >= 24.1 debido a metadatos mal formados en el setup original de gym (un paréntesis faltante). La solución implementada en el Dockerfile fue instalar pip==23.3.2 explícitamente.

## ACTUALIZACIÓN (29 sept 2026, PS): por qué NO se migró a Gymnasium

Se intentó (28 sept, Mauricio, `fix/arreglos-dependencias`) migrar `test_abides.py`/`maestro_env.py`/`ejecutor_env.py` a `gymnasium` + `shimmy==1.3.0` como capa de compatibilidad, para evitar instalar el `gym` viejo. **Esto no funciona**: ABIDES-Gym importa `gym` directamente en su propio código fuente (`abides_gym/__init__.py`, `markets_execution_environment_v0.py` — verificado leyendo el código real del paquete), no a través de una capa que `shimmy` pueda interceptar desde afuera. `shimmy` envuelve un entorno ya creado con `gym` viejo para exponerlo con la API de `gymnasium`; no hace que el paquete `abides_gym` deje de necesitar `gym` internamente. Sin `gym==0.18.0` instalado, `import abides_gym` falla de entrada.

**Lo que sí funciona (verificado con éxito real el 29 sept, en Colab vía `condacolab`):** instalar `gym==0.18.0` (no `gymnasium`) junto con `numpy==1.22.0`, en un **solo comando `pip install`** con todas las versiones pinneadas a la vez — instalarlas en comandos separados hace que paquetes posteriores (sobre todo `ray[rllib]`) sobreescriban silenciosamente `numpy`/`gym` a versiones más nuevas e incompatibles. Además, usar `ray[tune]==1.7.0` en vez de `ray[rllib]==1.7.0` evita que se instalen `matplotlib`/`scikit-image` modernos (que exigen `numpy>=1.23`, en conflicto directo con el `numpy==1.22.0` que pide ABIDES). Ver `DIAGNOSTICO_COLAB_MAURICIO_29SEP.md` para la receta completa paso a paso, ya probada.
