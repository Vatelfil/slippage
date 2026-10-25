# Plan 2 (desarrollo de la parte de PS en el Sprint 6): qué se hizo

**Quién:** PS con apoyo de Claude Code (uso autorizado por la universidad), 26 de octubre de 2026. No se modificó ningún archivo de MR ni de BF. **No actualiza el Título II.**

## Qué incluía y qué se hizo

| Parte | Estado | Qué hay |
|---|---|---|
| **3.1.4 Monitoreo**: calibrar las alertas con corridas reales | Hecho | `scripts/calibrar_monitoreo_ps.py` cruza las alertas con 27 corridas de resultado conocido (12 de Poisson generadas en el PC y 15 de ABIDES). Informe en `docs/calibracion_monitoreo_PS.md` |
| 3.1.4: alerta nueva «la recompensa sube y el costo no» | Hecho | `RECOMPENSA_SUBE_COSTO_NO` en `src/training/monitoreo.py` (retorno ≥ 40 % mejor y costo menos de 1,5 bps mejor, ventanas de 100 episodios, mínimo 200) |
| 3.1.4: línea de costo de partida en el panel | Hecho | `scripts/monitorear_entrenamiento.py` |
| 3.1.4: guía de alertas | Hecho | `docs/guia_alertas_monitoreo_PS.md` (qué significa cada una, qué hacer, cómo se comportó) |
| Costo ajustado por lo no ejecutado | Hecho | `--penalizaciones-no-ejecutado` en la comparación contra TWAP y VWAP |
| 3.2.4 Sensibilidad por tamaño, tramo y liquidez | Hecho (listo para las 90 corridas) | `scripts/analizar_sensibilidad_3_2_4.py` |
| 3.1.5 Sprint Review | Actualizado | `docs/sprint6_que_se_hizo.md` |
| Integrar el monitoreo en las corridas de MR | **No se hizo**: requiere su visto bueno | Instrucciones en la guía de alertas |
| Escenarios de liquidez y evaluador de las 90 corridas | **No se hizo**: dependen de que BF defina los tres niveles de liquidez | La sensibilidad ya está lista para recibirlos |
| Actualizar el informe del Título II | **No se hizo** (decisión de PS: se hace más adelante) | `docs/investigacion_recompensa_que_se_hizo.md` tiene notas para esa actualización |

## Resultados que importan

1. **Las alertas originales daban falsas alarmas.** `ENTROPIA_COLAPSADA` avisaba en 2 de 4 corridas buenas (su entropía queda entre el 50 % y el 69 % del máximo, igual que varias malas) y `PICO_PERDIDA_CRITICO` en las 4 (con penalización terminal los picos del crítico son normales). Faltaba además una alerta para el problema de fondo.
2. **Con los umbrales calibrados:** las corridas buenas solo tienen avisos informativos; `RECOMPENSA_SUBE_COSTO_NO` avisa en 7 de 10 corridas malas y en ninguna buena (ni en las 12 neutrales); la entropía baja pasó a informativa y la colapsada solo es crítica si además hay espera alta o incumplimiento.
3. **El costo ajustado cambia la conclusión de la comparación.** El sistema sin entrenar parece igual a TWAP con una penalización de 50 a 100 bps por lo no comprado y claramente peor (+83 bps) con 300 bps. La penalización es un supuesto del equipo, por eso se informan varios valores.
4. **El panel muestra por qué el retorno solo engaña:** en las corridas con la recompensa actual el retorno sube hasta casi 0 porque la red deja de operar.

## Cómo reproducirlo

```
python scripts/calibrar_monitoreo_ps.py --generar     # entrena las 12 corridas de Poisson (≈ 5 min)
python scripts/calibrar_monitoreo_ps.py               # cruza alertas y etiquetas
python scripts/monitorear_entrenamiento.py --dir data/calibracion_monitoreo --out-png data/analysis/monitoreo_calibracion.png
python scripts/comparar_sistema_vs_benchmarks.py --comparacion "v2=BENCH.json,SISTEMA.json" --penalizaciones-no-ejecutado 50 100 300
PYTHONPATH=. python -m pytest tests/test_monitoreo.py tests/test_calibrar_monitoreo.py tests/test_sensibilidad_3_2_4.py
```

## Qué sigue
- Pedir a MR el visto bueno para integrar el monitoreo en sus corridas y mostrarle la guía de alertas.
- Confirmar el arreglo del Ejecutor en ABIDES (Colab) y revisar los umbrales con esas corridas.
- Cuando BF defina la liquidez y haya un sistema entrenado: correr la comparación (3.2.3) y la sensibilidad (3.2.4).

🤖 Generado con [Claude Code](https://claude.com/claude-code)
