# Texto del PR del Sprint 6 de PS

**Título:**

```
Sprint 6 (PS): monitoreo del entrenamiento, diagnóstico de la recompensa y reevaluación con 300 semillas
```

**Descripción (copiar desde la línea siguiente):**

---

## Qué es este PR

Reúne en un solo PR todo el trabajo de PS del Sprint 6 (26 de octubre al 6 de noviembre), que antes estaba repartido en 20 ramas `feature/ps-…` encadenadas. Se fusionó con `main` al 26 de octubre (PR #41 incluido) sin conflictos. **No modifica archivos de tareas de MR ni de BF**; lo que les toca está como documento para revisar.

Informe completo: `docs/informe_sprint6_PS.md`. Estado del sprint por tarea: `docs/sprint6_que_se_hizo.md`. Bitácora de cada rama: `docs/bitacora_cambios_PS.md`.

## Tarea oficial de PS: 3.1.4 monitoreo de métricas

- Registro por episodio y alertas de entrenamiento (`src/training/monitoreo.py`, `scripts/monitorear_entrenamiento.py`), sin tocar el entrenador.
- Alertas calibradas con 27 corridas de resultado conocido. Alerta nueva «la recompensa sube y el costo no»: avisa en 7 de 10 corridas malas y en 0 de 4 buenas. Guía de lectura en `docs/guia_alertas_monitoreo_PS.md`.
- Límite: falta conectarlo a las corridas de MR (dos líneas, con su visto bueno).

## Hallazgos del sprint

1. **Por qué el Ejecutor entrenado no bajaba el costo:** la recompensa no obliga a completar la orden y γ = 0,95 hace que un costo al final de la ventana se vea cuatro veces más barato, así que la red aprende a esperar (97 % a 99 % de los pasos).
2. **Arreglo probado:** penalización de 30 bps por acción sin comprar y γ = 1. En Poisson baja el costo al nivel de la mejor heurística.
3. **En ABIDES, con 300 semillas de evaluación:** las redes completan la orden (cumplimiento 1,00), **pero no cambian el costo**: ninguna de las 8 redes se distingue de su control (diferencia media −0,08 bps, IC 95 % de −0,98 a +0,77). Las cifras anteriores con 15 y 40 semillas eran ruido del precio; los documentos que las citaban llevan una nota.
4. **Referencia:** la política sin entrenar y las redes cuestan ≈ 2 bps más que TWAP con órdenes límite en el escenario medido (FALABELLA, apertura).
5. **Sistema completo sin entrenar:** cumple el 66,3 % de las órdenes y no se distingue de TWAP en costo; con 300 bps de penalización por lo no comprado es claramente peor, así que la conclusión depende de cómo se valore lo no ejecutado.
6. **Riesgo estadístico:** con 90 corridas solo se detectaría una diferencia de ≈ 20 bps; hay que recalcularlo con el primer sistema entrenado y conversar con la profesora guía cómo se redacta la hipótesis del 10 %.

## Otros aportes (adelantos, no son tareas del Excel)

- Evaluador del sistema completo sobre las 10 meta-órdenes (`scripts/colab/evaluar_sistema_ps.py`) y comparador con costo ajustado por lo no ejecutado.
- Análisis de sensibilidad 3.2.4 listo y probado con datos sintéticos (`scripts/analizar_sensibilidad_3_2_4.py`).
- Estabilidad de D3 con 100 y 1.000 episodios y control muestreado; memo de decisión para BF.
- Archivo candidato de meta-órdenes `v2` con benchmarks ensamblados (10 de 10 ejecutables).
- Cuatro figuras científicas del proyecto (`docs/figuras_cientificas/`).
- Cuadernos de Colab de confirmación, de la prueba V4 y de reevaluación, más los datos descargados (`data/colab_resultados/`).

## Para MR y BF: qué mirar (nada está ejecutado ni decidido por ustedes)

| Para | Qué | Dónde | Tiempo |
|---|---|---|---|
| MR | Propuesta de γ = 1 en el entrenador del Ejecutor | `docs/propuesta_cambio_RE_para_BF_y_MR.md` | 30 min |
| MR | Visto bueno para conectar el monitoreo en sus corridas | `docs/guia_alertas_monitoreo_PS.md` | 15 min |
| MR | Qué borradores de apoyo quiere (bucle del Maestro, barrido de hiperparámetros, λ) | `docs/plan_dejar_listo_MR_y_BF_PS.md`, sección 4 | 30 min |
| BF | Decisiones D3 (R_E) y D1 (tamaño de meta-órdenes), con regla por defecto si no hay respuesta | `docs/decision_RE_final_D3_para_BF.md`, `docs/sprint6_que_se_hizo.md` | 50 min |
| BF | Penalización por lo no comprado en R_E y niveles de liquidez | `docs/propuesta_cambio_RE_para_BF_y_MR.md`, `docs/plan_dejar_listo_MR_y_BF_PS.md`, sección 5 | 1 h |
| Los tres | Asignación definitiva de 3.1.3 y 3.1.4 (el Excel y la especificación difieren) y valor de la penalización por lo no ejecutado | reunión | |

Si algo les parece mal o prefieren hacerlo distinto, se cambia; son propuestas.

## Cómo verificar

```bash
PYTHONPATH=. python -m pytest tests -q
```

La única falla conocida es la que necesita el parquet de mercado, que no está en el repositorio. Resultado de la reevaluación: `python scripts/analizar_reevaluacion_ps.py --dir data/colab_resultados/reeval_300 --out-md docs/reeval_300_ABIDES_PS.md --out-png data/analysis/reeval_300_ABIDES.png`.

## Límites

- Un solo ticker (FALABELLA) y un solo tramo (apertura) en la reevaluación.
- El Maestro aún no se entrena; no hay evidencia de que mejore el costo.
- 1.000 episodios dejan una política casi uniforme; que más episodios lo arreglen es una hipótesis, no está probado.
- Uso de IA (Claude Code) autorizado por la universidad; debe declararse en el informe.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
