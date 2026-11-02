# Guía de las alertas del monitoreo de entrenamiento

**Elaborado por:** PS con apoyo de Claude Code (uso autorizado por la universidad). Tarea 3.1.4 del Sprint 6. **Para:** quien lance un entrenamiento (MR, BF, PS) y quiera saber qué significa cada alerta y qué hacer.

Las alertas las calcula `evaluar_alertas` (`src/training/monitoreo.py`) y las muestra el panel (`scripts/monitorear_entrenamiento.py`). Los umbrales se calibraron con 27 corridas cuyo resultado ya se conocía (`docs/calibracion_monitoreo_PS.md`).

## Cómo usarlo

1. Entrenar con el monitoreo activado (`entrenamiento_inicial_ps.py` lo hace por defecto; para el entrenador de MR, ver «Integración» más abajo).
2. Mirar el panel de las corridas juntas:
   ```
   python scripts/monitorear_entrenamiento.py --dir <carpeta con una subcarpeta por corrida> --out-md informe.md --out-png panel.png
   ```
3. Leer primero las alertas **críticas** y los **avisos**; las **informativas** son contexto.

## Qué significa cada alerta

| Alerta | Nivel | Qué detecta | Umbral | Qué hacer | Cómo se comportó en la calibración |
|---|---|---|---|---|---|
| `RECOMPENSA_SUBE_COSTO_NO` | Aviso | El retorno medio mejora y el slippage no baja: la red puede estar optimizando la recompensa y no el costo | Retorno ≥ 40 % mejor y costo menos de 1,5 bps mejor (ventanas de 100 episodios; mínimo 200) | Revisar la recompensa: ¿premia algo que la evaluación no mide? ¿Obliga a completar la orden? Comparar con la red inicial muestreando | Avisó en 7 de 10 corridas malas y en 0 de 4 buenas |
| `ESPERA_ALTA` | Aviso | La política espera en más de la mitad de los pasos | > 50 % de los pasos | Ver si esperar sale gratis en la recompensa | 6 de 10 malas; 0 de 4 buenas |
| `ESPERA_EN_AUMENTO` | Aviso | La fracción de espera sube entre el inicio y el final | Sube más de 20 puntos | Igual que arriba; es el aviso temprano | 6 de 10 malas; 0 de 4 buenas |
| `CUMPLIMIENTO_CRITICO` | Crítica | La red no completa la orden | Cumplimiento medio < 50 % en los últimos episodios | Detener el entrenamiento: algo está mal en la recompensa | 6 de 10 malas; 0 de 4 buenas |
| `CUMPLIMIENTO_BAJO` | Aviso | Cumplimiento por debajo de la regla de D3 | < 95 % | Mirar también el cumplimiento muestreando. Con variantes que liquidan lo no comprado, el cumplimiento voluntario puede quedar en 94 % a 96 % sin que haya problema | 1 de 4 buenas (liquidación forzada) |
| `ENTROPIA_COLAPSADA` | Aviso; **crítica** si además hay espera alta o incumplimiento | La política casi no explora | Entropía < 40 % del máximo | Mirar si coincide con espera alta o incumplimiento | 4 de 10 malas; 0 de 4 buenas |
| `ARGMAX_DISTINTO_DE_MUESTREO` | Crítica | El cumplimiento con argmax y muestreando difieren mucho | Diferencia > 0,20 | Evaluar siempre con muestreo además de argmax | Detectó los casos extremos de D3 |
| `KL_ALTO`, `RECORTE_ALTO` | Aviso | Las actualizaciones de PPO son demasiado grandes | KL > 0,02; recorte > 30 % | Bajar la tasa de aprendizaje o aumentar el lote | Sin casos en las corridas calibradas |
| `NO_FINITO` | Crítica | Hay NaN o infinitos en las pérdidas | — | Detener y revisar la recompensa y las observaciones | Sin casos |
| `ENTROPIA_BAJA` | Informativa | La política se está concentrando | < 90 % del máximo | Nada por sí sola: toda política que aprende se concentra | Avisó en las 4 buenas, así que no se usa para decidir |
| `PICO_PERDIDA_CRITICO` | Informativa | Pico grande de la pérdida del crítico | > 1.000 veces la mediana | Mirar si coincide con episodios de penalización | Sin valor para separar buenas de malas |
| `SIN_MEJORA` | Informativa | El retorno medio no mejora | — | Esperar más episodios | Ruido en corridas cortas |

## Qué mirar en el panel

- **Slippage (arriba, segunda columna):** la línea punteada de cada corrida es el costo de partida (promedio de los primeros 100 episodios, con la política casi inicial). **Si la curva no baja de esa línea, el costo no mejoró**, aunque la recompensa sí lo haga.
- **Retorno (arriba, primera columna):** si sube mucho y el slippage no baja, es lo que avisa `RECOMPENSA_SUBE_COSTO_NO`.
- **Pasos en espera y cumplimiento:** una corrida buena queda con espera moderada y cumplimiento cercano a 1; una mala se va a 100 % de espera.
- **Entropía:** bajar es normal; lo que importa es si va acompañada de espera alta o incumplimiento.

## Integración en el entrenador de MR (sin modificarlo)

El monitor envuelve la fábrica de entornos, así que no cambia el entrenador:

```python
from src.training.monitoreo import MonitorEntrenamiento
monitor = MonitorEntrenamiento("monitoreo_episodios.csv", seed_base=semilla)
trainer.train_executor_episodes(env_factory=monitor.envolver(mi_fabrica), n_episodes=..., csv_path="entrenamiento_apertura.csv", ...)
```

Con el CSV del entrenador (`csv_path`) y el de monitoreo en la misma carpeta, el panel los toma juntos.

## Límites

- Calibrado con 12 corridas de Poisson y 15 de ABIDES; con las corridas de la confirmación en ABIDES se revisará.
- La alerta `RECOMPENSA_SUBE_COSTO_NO` necesita al menos 200 episodios; con menos, el slippage por episodio es demasiado ruidoso.
- Un aviso no prueba que la corrida sea mala: señala dónde mirar.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
