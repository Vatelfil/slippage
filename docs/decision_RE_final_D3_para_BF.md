# Decisión final de R_E (D3) para BF: revisión del 23 de octubre

**Elaborado por:** PS con apoyo de Claude Code (uso autorizado por la universidad), 23 de octubre de 2026. **Para:** BF (decide), con MR y PS. **Continúa:** `docs/decision_RE_para_BF.md` (decisión del 14 de octubre). **Si no hay decisión, rige la opción 0** (regla del plan). **Actualizado el 23 de octubre por la tarde con 10 redes de 100 episodios: ver la sección 7. Actualizado el 25 de octubre con 6 redes de 1.000 episodios: la sección 8 ajusta de nuevo la recomendación.**

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

## 7. Actualización del 23 de octubre (tarde): 10 redes de 100 episodios

Se repitió el entrenamiento inicial (100 episodios, apertura, FALABELLA, evaluación con las 15 semillas 5001 a 5015) con 5 semillas de red por opción: 1000, 2000, 3000, 4000 y 6000. Detalle completo en `docs/estabilidad_D3_PS.md`; datos en `data/colab_resultados/d3_estabilidad/`.

| Opción | Redes | Disparan la regla (cumplimiento con argmax < 95 %) | Cumplimiento con argmax | Cumplimiento muestreando |
|---|---:|---:|---|---:|
| 0 (riesgo sobre lo ejecutado) | 5 | **2** (semilla 1000: 0,904; semilla 4000: 0,646) | 0,646 a 0,996 | 1,000 en las 5 |
| A (riesgo sobre lo pendiente) | 5 | **1** (semilla 2000: 0,115) | 0,115 a 1,000 | 1,000 en las 5 |

Lo que muestra:

1. **La regla no distingue entre las dos opciones.** Se dispara en 2 de 5 redes con la opción 0 y en 1 de 5 con la A (prueba exacta de Fisher, p = 1,000). La opción A **también** incumple en una red, así que pasar a la A no garantiza el cumplimiento.
2. **Ninguna de las 10 redes aprendió una política concentrada.** Tras 100 episodios la entropía queda entre el 99,6 % y el 99,9 % del máximo en todas. El argmax de una distribución casi uniforme depende de diferencias mínimas, así que el resultado con argmax es sensible a los pesos iniciales. Lo confirma la red **sin entrenar**: con la semilla 2000 ya cumplía 0,000 y con la 4000 cumplía 0,893, antes de entrenar.
3. **Muestreando la política, las 10 redes ejecutan la orden completa** (cumplimiento 1,000).
4. **La corrida es reproducible.** La opción 0 con la semilla 1000 dio 0,904 de cumplimiento y 2,04 bps, igual que la repetición sin cortes del Sprint 5, en otra sesión de Colab. Un entrenamiento sin cortes da el mismo resultado.
5. **Costo (slippage).** Ninguna red se distingue de la red sin entrenar (p entre 0,15 y 0,89 por red). Esa comparación usa un control evaluado con argmax; falta el control muestreado (`scripts/colab/control_muestreado_ps.py`, unos minutos de Colab) para que sea una comparación justa.
6. **Dónde sí aparece el problema de esperar:** en la corrida de 1.000 episodios con la opción 0 (una sola red), la entropía bajó al 80 % del máximo y el cumplimiento con argmax fue 0,000; con la opción A fue 1,000 (una sola red). Es el régimen en que las dos opciones podrían diferir, y solo hay una red por opción.

### Qué cambia en la recomendación de PS

- **Ya no se recomienda pasar a la opción A por la regla de 100 episodios**, porque con 100 episodios la regla mide el azar del argmax sobre una política casi uniforme y la propia opción A la incumple.
- **Recomendación: "D3: esperar", con una comparación dirigida:** 3 semillas de red por opción con **1.000 episodios** (6 corridas de ≈ 40 minutos; ≈ 2 horas repartidas en dos cuadernos de Colab), evaluando siempre con argmax y con muestreo, con el control muestreado de la red sin entrenar y con el monitoreo del Sprint 6 activo. Decisión propuesta: dentro de la primera semana del Sprint 6.
- **Mientras tanto rige la opción 0 con vigilancia**, y la vigilancia se informa con las dos evaluaciones (argmax y muestreada).
- Respuesta pedida a BF: **"D3: esperar"** (propuesta), **"D3: 0"** o **"D3: A"**.

## 8. Actualización del 25 de octubre: 6 redes de 1.000 episodios (3 por opción)

Con 1.000 episodios (semillas de red 1000, 2000 y 3000; la 1000 viene del Sprint 5) las políticas ya se concentran, a diferencia de los 100 episodios de la sección 7. Detalle en `docs/estabilidad_D3_1000ep_PS.md`; datos en `data/colab_resultados/d3_1000ep/`.

| Opción | Semilla | Cumplimiento con argmax | Cumplimiento muestreando | Entropía final | Pasos en espera (primeros 100 → últimos 100 episodios) |
|---|---:|---:|---:|---:|---|
| 0 | 1000 | **0,000** | 0,9996 | 80 % | — |
| 0 | 2000 | 1,000 | 1,000 | 35 % | 30 % → 11 % |
| 0 | 3000 | 0,989 | 1,000 | 82 % | 31 % → **32 %** |
| A | 1000 | 1,000 | 1,000 | — | — |
| A | 2000 | 1,000 | 1,000 | 71 % | 30 % → 8 % |
| A | 3000 | 1,000 | 1,000 | 39 % | 31 % → 6 % |

Lo que muestra:

1. **La regla de cumplimiento se dispara en 1 de 3 redes con la opción 0 y en 0 de 3 con la A.** Con 3 redes por opción (Fisher p = 1,000) es una tendencia, no una prueba.
2. **La opción A reduce la conducta de esperar:** los pasos en espera bajan de ≈ 30 % a 6–8 % en las dos redes con A. Con la opción 0 bajan a 11 % en una red, pero en otra se quedan en 32 %: esperar no cuesta con la opción 0, y una de las dos redes lo conserva.
3. **El entrenamiento corrige la conducta inicial.** La red sin entrenar de la semilla 2000 tenía cumplimiento 0,000 con argmax (elige esperar); tras 1.000 episodios queda en 1,000 con las dos opciones.
4. **Costo:** el slippage muestreando promedia 6,61 bps con la opción 0 y 5,31 bps con la A, del orden del de la red sin entrenar (≈ 6 bps, evaluada con argmax); `twap_limit_medio` sigue siendo mucho mejor (≈ 1,8 bps). Con 1.000 episodios **no hay mejora de costo** con ninguna opción. Falta el control de la red sin entrenar muestreando la política (`control_muestreado_ps.py`) para una comparación justa.

### Recomendación revisada de PS (la decide BF)

- **Inclinación: "D3: A"**, porque la regla original solo se dispara con la opción 0 (1 de 3 frente a 0 de 3) y la opción A reduce la espera en las dos redes en que se midió. Con la salvedad de que son 3 redes por opción.
- **Costo de adoptarla:** recalcular β∗ y repetir la fase 2 de β (varias horas de Colab; sección 5). Antes de hacerlo conviene esperar el control muestreado, que confirma si el costo no empeora.
- **Si BF prefiere no cambiar:** "D3: 0", con la vigilancia informada con argmax y con muestreo y el monitoreo del Sprint 6 activo (la alerta de espera alta detecta la red que se queda esperando).
- Respuesta pedida: **"D3: A"**, **"D3: 0"** o **"D3: esperar"** (esperar el control muestreado).

🤖 Generado con [Claude Code](https://claude.com/claude-code)
