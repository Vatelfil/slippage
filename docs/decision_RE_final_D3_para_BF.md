# Decisión final de R_E (D3) para BF: revisión del 23 de octubre

**Elaborado por:** PS con apoyo de Claude Code (uso autorizado por la universidad), 23 de octubre de 2026. **Para:** BF (decide), con MR y PS. **Continúa:** `docs/decision_RE_para_BF.md` (decisión del 14 de octubre). **Si no hay decisión, rige la opción 0** (regla del plan).

## 1. Qué se había acordado

Opción 0: mantener la fórmula del Título I (riesgo cobrado sobre lo **ejecutado**) con β = 0,0061796 y una **regla de vigilancia fijada antes de ver los datos**: *en el entrenamiento inicial (2.3.5), si el cumplimiento de la orden baja del 95 %, se pasa a la opción A* (riesgo sobre el inventario **pendiente**, ya implementada y apagada por defecto), anotándolo como desviación del Título I justificada con datos. La revisión final es hoy.

## 2. Evidencia disponible

Evaluación con 15 semillas nuevas (5001 a 5015), FALABELLA, apertura. "Argmax" es la evaluación del plan (acción más probable); "muestreada" usa la política como se entrena.

| Corrida | R_E | Cumplimiento con argmax | Slippage con argmax (bps) | Cumplimiento muestreada |
|---|---|---:|---:|---:|
| 100 episodios (reanudada desde el episodio 30) | opción 0 | 1,000 | 3,28 | — |
| 100 episodios (repetición sin cortes) | opción 0 | **0,904** | 2,04 | 1,000 |
| 1.000 episodios | opción 0 | **0,000** | sin ejecuciones | 0,9996 |
| 1.000 episodios | opción A | 1,000 | 5,91 | 1,000 |
| Red sin entrenar (control) | — | 1,000 | 6,02 | — |

Lo que muestra:

1. **Con la opción 0, la regla se dispara en 2 de 3 corridas.** El 1,000 de la primera corrida viene de un entrenamiento que se reanudó desde el episodio 30; reanudar cambia los resultados (el checkpoint no guarda el estado aleatorio), así que ese dato no es comparable con los otros dos.
2. **Con argmax, la red entrenada con la opción 0 elige "esperar"** (`LIMIT_SELL`, que el puente de ABIDES traduce a no enviar orden). Muestreando la política sí ejecuta.
3. **Con la opción A, el argmax ejecuta toda la orden** y el slippage es comparable (5,91 bps frente a 6,02 de la red sin entrenar; muestreada, 4,60 bps).
4. **Ninguna corrida se distingue de la red sin entrenar en slippage** (p entre 0,36 y 0,80, Wilcoxon pareado). La opción A mejora el cumplimiento, no el costo.

**Límites de esta evidencia:** una sola red por corrida; una sola corrida de la opción A; la opción A se probó con el mismo β (0,0061796), sin recalcular β∗; solo apertura y FALABELLA.

## 3. Opciones para decidir

| Opción | Qué implica | Frente al Título I | Frente a la regla del 14 de octubre |
|---|---|---|---|
| **1. Pasar a la opción A** | Riesgo sobre lo pendiente; recalcular β∗ y repetir la fase 2 (varias horas de Colab); anotar la desviación | Cambia lo que significa `q` en R_E: desviación que se justifica con los datos de arriba | La aplica tal como estaba escrita (la evaluación del plan es con argmax) |
| **2. Mantener la opción 0** | Sin cambios de código; se declara que con argmax la red aprende a esperar y que el cumplimiento se vigila muestreando | Fiel al Título I | Habría que **cambiar la regla después de ver los datos** (evaluar con muestreo en vez de argmax), lo que va contra la regla R6 del plan; solo se justifica si se declara |
| **3. Esperar 5 semillas de red por opción** | 10 corridas de 100 episodios (≈ 70 minutos de Colab, ≈ 35 en dos cuadernos) para medir cuán estable es la regla | Sin cambio inmediato | Se aplicaría con evidencia más sólida |

## 4. Recomendación de PS (la decide BF)

- Aplicar la regla **como se escribió** (opción 1), porque se fijó antes de ver los datos y con argmax se dispara en 2 de 3 corridas; es lo que pide R6.
- Si hoy no se puede decidir, hacer la **opción 3** durante la próxima semana y decidir el lunes 26, con rigor y sin cambios de código mientras tanto (rige la opción 0).
- En cualquier caso, **evaluar siempre con argmax y con muestreo** y mantener el monitoreo del Sprint 6, que avisa cuando ambas evaluaciones difieren.

## 5. Costo de pasar a la opción A

| Paso | Dónde | Costo |
|---|---|---|
| Activar `riesgo_sobre="pendiente"` por defecto (hoy se pasa por línea de comandos con `--riesgo-sobre pendiente`) | `src/config/market_params.py` (constante `RIESGO_SOBRE_EJECUTOR`) | Cambio de una línea y revisar las pruebas |
| Recalcular β∗ con la opción A (`beta_star_from_episodes(..., base="pendiente")` en `src/experiments/beta_sweep.py`) | Si los episodios del barrido ya guardan σ²·Q_pendiente, en el PC; si no, repetir el barrido en Colab | Hasta 1 a 2 h de Colab, según `docs/decision_RE_para_BF.md` |
| Repetir la fase 2 de β | Colab, por tramo | Varias horas (≈ 47 min por β en media jornada y ≈ 108 min en el cierre en las corridas del Sprint 5) |
| Documentar la desviación | `DESVIACIONES_TITULO1_VS_IMPLEMENTACION.md` y `docs/decision_RE_para_BF.md` | 1 h |

## 6. Qué se pide a BF

Responder en el grupo con una línea: **"D3: 0"** (mantener la opción 0), **"D3: A"** (pasar a la opción A) o **"D3: esperar"** (hacer la comparación de 5 semillas y decidir el lunes 26).

🤖 Generado con [Claude Code](https://claude.com/claude-code)
