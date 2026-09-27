# Instalación y Ejecución de ABIDES-Gym en Google Colab

Debido a restricciones de ciberseguridad y requisitos de estabilidad (evitar caídas de red que interrumpan los túneles locales), la arquitectura recomendada es **instalar y ejecutar el simulador ABIDES-Gym directamente dentro de Google Colab**, junto al entrenamiento del modelo.

Esta aproximación asegura baja latencia entre el agente de RL y el entorno simulado, además de evitar la necesidad de exponer puertos locales.

## Desafío de Versiones: Forzar Python 3.9 en Colab
Google Colab suele actualizar su entorno base a versiones recientes de Python (3.10 o superior). Dado que ABIDES-Gym puede tener problemas de compatibilidad con versiones nuevas, el primer paso es forzar al entorno de Colab a utilizar **Python 3.9**.

### Paso 1: Configurar Python 3.9 como predeterminado
Crea una celda de código al principio de tu Google Colab y ejecuta el siguiente bloque. Esto instalará Python 3.9 usando el gestor de paquetes de Ubuntu (`apt`), forzará al sistema a usarlo por defecto e instalará `pip` para esa versión.

```bash
# Instalar dependencias de Python 3.9
!sudo apt-get update -y
!sudo apt-get install python3.9 python3.9-dev python3.9-distutils libpython3.9-dev -y

# Actualizar las alternativas del sistema para que python3 apunte a python3.9
!sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1
!sudo update-alternatives --set python3 /usr/bin/python3.9

# Descargar e instalar pip específico para Python 3.9
!curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
!python3.9 get-pip.py

# Verificar que la versión sea correcta (Debería imprimir Python 3.9.x)
!python3 --version
```

### Paso 2: Importar el código del proyecto
Tienes dos opciones para llevar el código de tu proyecto (`slippage` / `ABIDES-Gym`) a Colab:

**Opción A: Clonar desde un repositorio Git (Recomendado)**
Si tu código está alojado en GitHub/GitLab:
```bash
!git clone <URL_DE_TU_REPOSITORIO>
%cd <NOMBRE_DE_LA_CARPETA_CLONADA>
```

**Opción B: Montar Google Drive**
Si subes tu carpeta del proyecto a Google Drive para mantener los cambios sincronizados:
```python
from google.colab import drive
drive.mount('/content/drive')
# Reemplaza la ruta por la ubicación real en tu Drive
%cd /content/drive/MyDrive/ruta_a_tu_proyecto/
```

### Paso 3: Instalar ABIDES-Gym y Dependencias
Una vez posicionado en el directorio del proyecto donde se encuentre el archivo `setup.py` o `requirements.txt`, ejecuta:

```bash
# Si es un paquete instalable
!pip install -e .

# Opcionalmente, instalar requerimientos adicionales si los hay
!pip install -r requirements.txt
```

### Paso 4: Comprobación del entorno
Puedes validar que el entorno se carga correctamente con un simple script de prueba dentro de una celda:

```python
import gym
import abides_gym

# Crear una instancia del entorno de prueba
env = gym.make("markets-v0")
obs = env.reset()
print("¡Entorno cargado exitosamente! Observación inicial:", obs)
```

## Solución de Problemas Comunes en Colab
* **Celdas fallando con sintaxis inválida:** Asegúrate de que las celdas con comandos de terminal empiecen con `!` (ej. `!pip install...`) y las de cambio de directorio con `%` (ej. `%cd`).
* **Error de paquetes de sistema en ABIDES:** Si ABIDES-gym requiere alguna biblioteca en C++ adicional para compilar, puedes agregar la instalación de dicho paquete en el primer bloque `apt-get` (por ejemplo, `build-essential`).
