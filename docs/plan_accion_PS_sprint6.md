# Plan de acción de PS para el Sprint 6 (26 oct – 6 nov 2026)

**Borrador elaborado por:** Paolo Sepúlveda (PS) con apoyo de Claude Code, 20 oct 2026. Sprint 6: **ajuste de hiperparámetros**.

> **Qué es firme y qué no.** Las filas del Sprint 6 del Excel del plan (`plan-desarrollo-titulo-2.xlsx`) vienen vacías: solo traen el ID. Las tareas y los responsables salen de `ESPECIFICACION_DETALLADA_TAREAS.md` y de `Contexto_Agente_Programacion.md`. El plan detallado del Sprint 6 (como el de Sprint 5) se debe confirmar en la reunión de arranque del 26 de octubre.

## 1. Qué pide el Sprint 6

| ID | Tarea | Responsable | Tu parte |
|---|---|---|---|
| 3.1.1 | Ajuste de tasa de aprendizaje, tamaño de lote y épocas del PPO | MR | Apoyo: que cada corrida deje registro comparable (ver 3.1.4) |
| 3.1.2 | Ajuste del clipping ε y del GAE λ | MR | Igual que arriba |
| 3.1.3 | Corridas de evaluación por escenario de liquidez | BF | Apoyo en análisis si lo pide |
| **3.1.4** | **Monitoreo y registro de métricas de entrenamiento** (curvas de recompensa, implementation shortfall por episodio) | **PS** | **Tarea tuya** |
| 3.1.5 | Sprint Review | Los tres | Documento `docs/sprint6_que_se_hizo.md` (como `sprint5_que_se_hizo.md`) |

Arrastres del Sprint 5 que caen en este sprint: **P10** (revalidar λ del Maestro con un entrenamiento real, MR, ≈ 4 h, primera semana), y las decisiones **D1** (tamaño de las meta-órdenes) y **D3** (R_E: opción 0 o A), que son de BF.

## 2. Qué se adelantó ya (rama `feature/ps-sprint6-adelanto-3-1-4`)

| Archivo | Para qué sirve |
|---|---|
| `src/training/monitoreo.py` | `MonitorEntrenamiento`: envuelve la fábrica de entornos del entrenador y deja **una fila por episodio** (retorno, `q_ejecutado`, **cumplimiento**, **slippage en bps**, fracción de pasos en espera, en mercado y en límite de compra). **No modifica** el entrenador de MR. Incluye `evaluar_alertas` |
| `scripts/monitorear_entrenamiento.py` | Panel: curvas de **varias corridas juntas** (retorno, slippage, cumplimiento, espera, entropía, KL, pérdida del crítico, recorte) y un informe de alertas por corrida |
| `scripts/colab/entrenamiento_inicial_ps.py` | Ahora escribe `monitoreo_episodios.csv` en cada corrida (se apaga con `--sin-monitoreo`) |
| `scripts/comparar_sistema_vs_benchmarks.py` | **Adelanto del Sprint 7 (3.2.3 y 3.2.4):** compara el sistema con TWAP y VWAP, pareado por orden y semilla (IC 95 % por bootstrap, Wilcoxon por celda y por orden, desglose por tramo y activo, tabla por tamaño de orden) |
| `scripts/generar_meta_ordenes.py` | Nueva opción `--pct-dia-cierre` para la combinación de D1 propuesta (10 % del día, 5 % en el cierre) |
| `tests/test_monitoreo.py`, `tests/test_comparar_sistema_vs_benchmarks.py` | Pruebas (Poisson, sin ABIDES) |

### Alertas del monitoreo y por qué existen

Salen de lo que pasó en el entrenamiento inicial (2.3.5), donde la red aprendió a esperar y solo se vio al evaluar:

| Código | Qué detecta | Origen |
|---|---|---|
| `ESPERA_ALTA`, `ESPERA_EN_AUMENTO` | La política se concentra en «esperar» (`LIMIT_SELL`) | Opción 0 de R_E: esperar no cuesta |
| `CUMPLIMIENTO_BAJO`, `CUMPLIMIENTO_CRITICO` | Cumplimiento medio < 95 % (regla de D3) o < 50 % | Regla de vigilancia de D3 |
| `ARGMAX_DISTINTO_DE_MUESTREO` | El cumplimiento con argmax difiere del muestreado en más de 0,2 | Evaluación determinista con 0 de cumplimiento |
| `ENTROPIA_BAJA`, `ENTROPIA_COLAPSADA` | Entropía bajo el 90 % o el 60 % del máximo (5,48 nats) | Entropía al 80 % en la corrida de 1.000 episodios |
| `NO_FINITO`, `KL_ALTO`, `RECORTE_ALTO`, `PICO_PERDIDA_CRITICO`, `SIN_MEJORA` | Salud de la optimización PPO | Buenas prácticas del PPO |

Con las corridas ya hechas (solo el CSV del entrenador y el JSON de estado), el panel ya señala los problemas conocidos de la corrida de 1.000 episodios con opción 0 (`ENTROPIA_BAJA` y `ARGMAX_DISTINTO_DE_MUESTREO`).

## 3. Cronograma propuesto

### Antes del lunes 26 (esta semana)

- [ ] Mergear el PR de Sprint 5 (T3, T4 y T5) y luego el de este adelanto.
- [ ] **Prueba en Colab con ABIDES** del monitoreo (≈ 5 min, 100 episodios): confirma que `monitoreo_episodios.csv` sale bien con el simulador real. Hasta ahora solo se probó con Poisson.
- [ ] Dejar a Mauri las dos líneas que integran el monitoreo a sus corridas (sección 4) y avisarle.

### Semana 1 (26–30 oct)

- [ ] Reunión de arranque: confirmar con MR y BF las tareas 3.1.x y las decisiones D1 y D3.
- [ ] Si BF decide D1: regenerar las órdenes con el generador (`--pct-dia 0.10 --pct-dia-cierre 0.05`), correr los benchmarks con 2 semillas (~65 min por semilla) y actualizar `docs/benchmarks_2.3.4_PS.md`.
- [ ] Si BF decide D3 = opción A: recalcular β* y el barrido de β (P5), que toma varias horas de Colab (~47 min por β en media jornada, ~108 min en el cierre). Se decide con BF.
- [ ] Revisar con MR el criterio de comparación entre corridas del ajuste: mismas semillas de evaluación (5001–5015) y las mismas métricas del panel.

### Semana 2 (2–6 nov)

- [ ] Correr el panel sobre cada corrida del ajuste (MR) y entregar la comparación a MR y BF (tabla, figura y alertas).
- [ ] Redactar `docs/sprint6_que_se_hizo.md` (3.1.5): hecho, hecho con límite, pasa al Sprint 7, cada uno con su razón y el costo medido.

## 4. Cómo se conecta con las corridas de Mauri

Dos líneas en el script de entrenamiento, sin cambiar el entrenador:

```python
from src.training.monitoreo import MonitorEntrenamiento

monitor = MonitorEntrenamiento(out_dir / "monitoreo_episodios.csv", seed_base=trainer.seed)
trainer.train_executor_episodes(env_factory=monitor.envolver(factory), ...)   # el resto igual
```

Luego, para comparar corridas:

```bash
python scripts/monitorear_entrenamiento.py \
    --corrida "lr 3e-4=<carpeta1>/entrenamiento_apertura.csv,<carpeta1>/monitoreo_episodios.csv" \
    --corrida "lr 1e-4=<carpeta2>/entrenamiento_apertura.csv,<carpeta2>/monitoreo_episodios.csv" \
    --estado "lr 3e-4=<carpeta1>/entrenamiento_inicial_apertura.json" \
    --out-png docs/monitoreo.png --out-md docs/monitoreo.md
```

**Límite actual:** el monitoreo cubre el bucle del **Ejecutor** (`train_executor_episodes`). Para el Maestro (R_M, α elegidos) no hay equivalente todavía; se hace cuando MR cierre el entrenamiento del Maestro (P10).

## 5. Preparación del Sprint 7 (3.2.3 y 3.2.4, tuyas)

- El script de comparación ya existe. **Falta el evaluador del sistema:** un runner que corra Maestro + Ejecutores entrenados sobre las 10 meta-órdenes y deje los resultados con el mismo formato que `benchmarks_meta_ordenes_ps.py` (`estrategia = "PPO"`, mismas semillas). Depende de que haya redes entrenadas (MR, BF); son unas 2–3 h de trabajo mío cuando existan.
- **Para 3.2.4 (sensibilidad por tamaño y tramo):** hay benchmarks con 100.000 acciones, 10 % del día y 5 % del día en el cierre. El sistema tendrá que evaluarse con el tamaño que decida BF para D1 y, para la sensibilidad, con uno o dos más.

## 6. Qué no se hace sin que los responsables lo pidan

- Barrer hiperparámetros (3.1.1 y 3.1.2, de MR) ni correr evaluaciones por escenario de liquidez (3.1.3, de BF).
- Cambiar R_E o recalcular β* sin la decisión de BF sobre D3.
- Cambiar el entrenador PPO.

Lo que sí se ofrece: dejarles el registro y las comparaciones listos.

## 7. Riesgos

| Riesgo | Efecto | Qué se hace |
|---|---|---|
| MR y BF no integran el monitoreo en sus corridas | 3.1.4 queda hecha pero sin uso | Dejar la integración en dos líneas y avisar; el panel funciona incluso solo con el CSV del entrenador y el JSON de estado |
| D1 o D3 sin decisión de BF | No se pueden fijar tamaños ni R_E del Sprint 6 | Regir la propuesta documentada por defecto (D1: 10 % del día y 5 % en el cierre; D3: opción 0 con vigilancia) y declararlo |
| La red sigue sin superar a la no entrenada | El ajuste de hiperparámetros no muestra mejoras | El panel lo marca (`SIN_MEJORA`); es un resultado a informar, no un error |
| Tiempo de Colab (sesiones gratuitas) | Retrasos | Corridas reanudables; repartir entre dos cuadernos |

🤖 Generado con [Claude Code](https://claude.com/claude-code)
