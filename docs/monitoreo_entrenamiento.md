# Monitoreo del entrenamiento (tarea 3.1.4)

**Borrador elaborado por:** PS con apoyo de Claude Code. Panel generado con `scripts/monitorear_entrenamiento.py`.

![Curvas de las corridas](../data/analysis/monitoreo_entrenamiento.png)

## Resumen por corrida

| Corrida | Actualizaciones | Episodios registrados | Entropía final (% del máximo) | KL máximo | Cumplimiento final | Pasos en espera (final) | Alertas |
|---|---:|---:|---:|---:|---:|---:|---|
| 100 episodios, opción 0 | 10 | — | 99,9 % | 0,00012 | — | — | 0 críticas, 0 avisos |
| 1000 episodios, opción 0 | 100 | — | 80,1 % | 0,00438 | — | — | 1 críticas, 1 avisos |

## Alertas

**100 episodios, opción 0**

- Sin alertas.

**1000 episodios, opción 0**

- **CRITICA** `ARGMAX_DISTINTO_DE_MUESTREO`: Cumplimiento 0.000 con argmax y 1.000 muestreando: la evaluacion determinista no representa la politica entrenada.
- **AVISO** `ENTROPIA_BAJA`: Entropia al 80 % del maximo: la politica se esta concentrando; evaluar tambien con muestreo y no solo con argmax.
- **INFO** `PICO_PERDIDA_CRITICO`: Pico de la perdida del critico (33.3, mediana 0.86).

## Cómo leerlo

- **Entropía:** una política uniforme sobre las 240 acciones tiene 5,48 nats. Una caída fuerte significa que la política se concentra; conviene evaluar también con muestreo y no solo con argmax (ver `docs/entrenamiento_inicial_2.3.5.md`).
- **Pasos en espera:** acciones `LIMIT_SELL`, que el puente de ABIDES y el simulador Poisson tratan como «esperar».
- Sin el CSV de monitoreo por episodio solo se muestran las curvas del entrenador; el costo y el cumplimiento por episodio se registran con `MonitorEntrenamiento` (`src/training/monitoreo.py`).

🤖 Generado con [Claude Code](https://claude.com/claude-code)
