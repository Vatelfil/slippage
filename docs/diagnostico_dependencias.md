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
El `Dockerfile` generado para este PoC establece:
*   `python:3.9-slim`
*   `numpy==1.23.5` y `cython` (instalados primero)
*   `gym==0.21.0`
*   `ray[rllib]==2.2.0`
*   `pomegranate==0.14.8`
*   (Otras dependencias provistas en tu `requirements.txt`)

Esto provee un *sandbox* estable y predecible donde los agentes CTDE y PPO podrán ejecutarse interactuando con el LOB sin fallos repentinos de infraestructura.

## 5. Conflicto Directo de ABIDES-Gym con Python 3.9+

### Diagn�stico
La instalaci�n base de abides-gym a veces requiere dependencias antiguas que entran en conflicto con setuptools >= 58.0.0 (ya que elimin� el soporte de 2to3). Adem�s, algunos paquetes subyacentes requieren CMake y compiladores en Linux para construir extensiones C++ en las que se basa la simulaci�n del Order Book.

### Mitigaci�n Aplicada
En el Dockerfile se introdujo la instalaci�n de uild-essential, cmake, y la degradaci�n (downgrade) o fijaci�n de setuptools y wheel, previo a instalar las bibliotecas requeridas. Esto permite que pip resuelva e instale los binarios correctos de ABIDES-Gym bajo Python 3.9.18 de manera fluida y sin arrojar errores de 'Failed building wheel'.

### Ajuste Adicional de Pip
Al construir el contenedor, la instalaci�n de gym==0.21.0 tambi�n falla si la versi�n de pip es >= 24.1 debido a metadatos mal formados en el setup original de gym (un par�ntesis faltante). La soluci�n implementada en el Dockerfile fue instalar pip==23.3.2 expl�citamente.


## ACTUALIZACION: Migracion a Gymnasium (Septiembre 2026)

Debido a la falta de soporte de `gym` para versiones modernas de Python y librerias como NumPy 2.0 (y especialmente para mantener compatibilidad en entornos como Google Colab), el proyecto ha sido migrado para utilizar **Gymnasium**.

*   **Dependencias Actualizadas:** Se ha anadido `gymnasium==0.29.1` a los requerimientos.
*   **Capa de Compatibilidad:** Para mantener la compatibilidad con entornos antiguos que fueron disenados para `gym` (como `abides-gym`), se recomienda el uso de la libreria `shimmy==1.3.0` o adaptar los scripts de inicializacion para mapear la antigua API de `step` y `reset` a la nueva API de Gymnasium.
*   **Codigo:** Se han actualizado los scripts (ej. `test_abides.py`, `maestro_env.py`, `ejecutor_env.py`) para importar `gymnasium as gym` y soportar el retorno de 5 valores en `step()` y 2 valores en `reset()`.
