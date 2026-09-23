FROM python:3.9.18-slim

WORKDIR /workspace

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git \
        build-essential \
        cmake \
    && rm -rf /var/lib/apt/lists/*

# --- ABIDES-Gym (JP Morgan) ---
# Corregido 23 sept 2026 (PS): la version anterior de este Dockerfile apuntaba
# a un repo inexistente ("abides-jpmc.git") e instalaba versiones de gym/numpy/
# ray/pomegranate que NO coinciden con las pineadas por el propio repo oficial.
# Verificado contra https://github.com/jpmorganchase/abides-jpmc-public
# (repo REAL, archivado/read-only desde jun-2025) y su install.sh/requirements.txt:
#   gym==0.18.0, numpy==1.22.0, pandas==1.2.4, ray[rllib]==1.7.0,
#   pomegranate==0.14.5, scipy==1.10.0, coloredlogs==15.0.1, psutil==5.8.0,
#   tqdm==4.61.1
# El repo NO se instala via "pip install git+...#subdirectory=X" (eso nunca
# funciono porque abides-core/abides-markets/abides-gym no son paquetes PyPI
# independientes con un pyproject.toml en la raiz del subdirectorio pensado
# para esa sintaxis) - el metodo oficial es clonar el repo completo y correr
# `python setup.py install` en cada subcarpeta, en este orden.
#
# NOTA IMPORTANTE: no se pudo construir ni probar esta imagen en el entorno
# donde se hizo esta correccion (sin Docker disponible). Los datos de arriba
# estan verificados contra el README/install.sh/requirements.txt reales del
# repo, pero la instalacion COMPLETA (compilacion de pomegranate con Cython,
# etc.) sigue sin confirmarse de punta a punta. Mauricio debe construir esta
# imagen y reportar si algo falla.

RUN pip install pip==23.3.2 setuptools==57.5.0 wheel==0.38.4
# setuptools<58 es necesario (soporte 2to3) para paquetes viejos como gym==0.18.0;
# la version anterior de este Dockerfile pineaba setuptools==65.5.0, que
# CONTRADECIA la propia mitigacion descrita en docs/diagnostico_dependencias.md.

RUN pip install "numpy==1.22.0" cython
RUN pip install "gym==0.18.0" "pandas==1.2.4" "scipy==1.10.0" \
        "coloredlogs==15.0.1" "psutil==5.8.0" "tqdm==4.61.1"
RUN pip install "pomegranate==0.14.5"
RUN pip install "ray[rllib]==1.7.0"

RUN git clone https://github.com/jpmorganchase/abides-jpmc-public.git /tmp/abides-jpmc-public \
    && cd /tmp/abides-jpmc-public/abides-core && python setup.py install \
    && cd /tmp/abides-jpmc-public/abides-markets && python setup.py install \
    && cd /tmp/abides-jpmc-public/abides-gym && python setup.py install \
    && rm -rf /tmp/abides-jpmc-public

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["bash"]
