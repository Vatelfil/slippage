# Slippage — Multi-Agent Reinforcement Learning

Prototipo experimental de coordinación de agentes inteligentes basado en
Aprendizaje por Refuerzo para mitigar el costo por Slippage en la ejecución
simulada de órdenes de gran volumen utilizando datos históricos del mercado IPSA.

## Objetivo

El proyecto busca desarrollar un sistema multiagente jerárquico compuesto por
un Agente Maestro y tres Agentes Ejecutores, utilizando aprendizaje por
refuerzo y PPO para optimizar la ejecución de órdenes.

## Entorno de desarrollo

El proyecto utiliza Docker para garantizar un entorno reproducible.

Tecnologías principales:

- Python 3.9.18
- Docker
- ABIDES-Gym
- PyTorch
- Git
- GitHub

## Estructura del proyecto

```text
slippage/
├── Dockerfile
├── compose.yaml
├── requirements.txt
├── .gitignore
├── .dockerignore
├── src/
├── tests/
├── data/
│   ├── raw/
│   └── processed/
├── experiments/
├── notebooks/
└── results/
```

## Requisitos

- Git
- Docker Desktop
- Python 3.9.18 (dentro del contenedor)

### Construir el entorno

```bash
docker compose build
```

### Iniciar el contenedor

```bash
docker compose run --rm slippage
```

### Verificar Python

Dentro del contenedor, ejecuta:

```bash
python --version
```

Debe mostrar Python 3.9.18.

## Datos

Los datos históricos del mercado IPSA no se almacenan directamente en el repositorio.

**Estructura de datos:**

- **Datos originales:** `data/raw/`
- **Datos procesados:** `data/processed/`