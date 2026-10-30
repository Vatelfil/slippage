# Informe del Sprint 6 (26 oct – 6 nov 2026): trabajo de PS

> **Nota del 29 de octubre (revisión):** los entrenamientos en ABIDES de este documento usaron una recompensa del Ejecutor que compara el precio pagado con el precio medio de 30 segundos *después* de la compra, no con el de la decisión (falla H1 de `docs/revision_opus_PS.md`). Esa recompensa casi no se relaciona con el costo, así que lo que aquí se concluye sobre si el entrenamiento mejora el costo no debe usarse para decidir. El slippage medido, el cumplimiento y los benchmarks sí son válidos: no dependen de la recompensa.

**Elaborado por:** PS con apoyo de Claude Code (uso de IA autorizado por la universidad; debe declararse en el informe). **Fecha de corte:** 26 de octubre de 2026. **Uso previsto:** material para redactar después el documento de Título II. **No actualiza el informe de Título II ahora**; este archivo es la fuente que se copia cuando corresponda.

Todo lo que dice «medido» sale de archivos del repositorio (rutas en la sección 9). Lo que dice «hipótesis» no está probado.

## 1. Resumen

1. La tarea oficial de PS en el Sprint 6 es **3.1.4, monitoreo de métricas de entrenamiento**. Está hecha y calibrada con 27 corridas reales; falta conectarla a las corridas de MR y que el PR llegue a `main`.
2. PS además investigó **por qué entrenar al Ejecutor no bajaba el costo**. Causa encontrada: la recompensa no obliga a completar la orden y el descuento γ = 0,95 hace que un costo al final de la ventana se vea cuatro veces más barato, así que la red aprende a esperar. Arreglo probado: **penalización de 30 bps por acción sin comprar y γ = 1**.
3. En ABIDES el arreglo **hace que la red complete la orden, pero no baja el costo**: con 300 semillas de evaluación, ninguna de las 8 redes entrenadas se distingue de la misma red sin entrenar (diferencia media −0,08 bps, IC 95 % de −0,98 a +0,77). Los resultados previos con 15 y 40 semillas eran ruido del precio.
4. La mejor heurística (TWAP con órdenes límite) cuesta ≈ 2 bps menos que la red, entrenada o no, en el escenario medido (FALABELLA, apertura).
5. **Límite de precisión del experimento:** con las 90 corridas previstas solo se detectaría una diferencia de ≈ 20 bps contra TWAP/VWAP (desviación pareada ≈ 70 bps por celda, con el sistema sin entrenar). Hay que recalcularlo con el primer sistema entrenado y discutir con la profesora guía cómo se redacta la hipótesis.
6. Sigue pendiente lo que pertenece a MR (bucle de entrenamiento del Maestro, ajuste de hiperparámetros) y a BF (decisiones D1 y D3, niveles de liquidez). Se dejó un plan para que lleguen, ejecuten y revisen (`docs/plan_dejar_listo_MR_y_BF_PS.md`).

## 1b. Actualización del 29 de octubre (para la redacción del Título II)

- **Revisión técnica:** el PPO funciona (prueba de cordura). La recompensa del Ejecutor en ABIDES medía contra el precio de 30 s después. Se corrigió, pero la versión corregida **empeora** el costo (+1,55 bps frente al control, 300 semillas), porque no mide el costo de esperar. Ninguna de las cuatro recompensas probadas logra que el Ejecutor le gane a su red sin entrenar en ABIDES. Ver `docs/revision_opus_PS.md` y `docs/reeval_300_mid_resultado_PS.md`.
- **Maestro:** bucle de entrenamiento nuevo, impacto acumulado entre ventanas (supuesto declarado) y revalidación de λ. En Poisson, con λ = 0,02, empata con TWAP. En ABIDES, con 4 corridas, no se distingue de TWAP. Ver `docs/maestro_primer_entrenamiento_PS.md` y `docs/maestro_abides_primera_prueba_PS.md`.
- **Hiperparámetros (3.1.1 y 3.1.2):** barrido en Poisson con regla fijada; mejora chica (≈ 0,2 bps). Ver `docs/barrido_hiperparametros_resultado_PS.md`.
- **Ejecutor con imitación:** copia a TWAP límite y después PPO. En 15 semillas, las dos redes quedan ≈ 1,5 bps sobre TWAP límite (antes, entre 3,8 y 5,8), con cumplimiento de 0,99. Con 300 semillas, la red s1000 cuesta 5,68 bps, la mejor red PPO medida, y queda 1,03 bps sobre TWAP límite (IC +0,11 a +1,88). Ver `docs/imitacion_resultado_PS.md` y `docs/reeval_300_imitacion_resultado_PS.md`.
- **Escenarios de liquidez (C-6b):** escalar solo al market maker hace que el pareo funcione, pero más `mm_pov` encarece la compra a mercado. Se propone nombrar los escenarios según el costo medido (v3, desviación 10). Ver `docs/c6_liquidez_resultado_PS.md`, sección 4.
- **D3:** opción 0 por la regla fijada.
- **Sistema final y 30 corridas (3.1.3):** cuadernos listos. El resultado se agrega cuando llegue.
- **Precisión:** el costo de una jornada en ABIDES varía ≈ 40 bps. Con 30 corridas el IC de la diferencia con TWAP será de ≈ ±15 bps. El informe debe presentar la reducción medida con su intervalo, que es lo que pide el Título I (objetivo 4).

## 2. Alcance del sprint

| Tarea | Responsable (según `docs/sprint6_que_se_hizo.md`) | Estado al 26 de octubre |
|---|---|---|
| 3.1.1 Tasa de aprendizaje, lote y épocas del PPO | MR | Por completar |
| 3.1.2 Clipping ε y GAE λ | MR | Por completar |
| 3.1.3 Corridas de evaluación por escenario de liquidez | BF | Por completar (listo el evaluador; faltan los tres niveles de liquidez) |
| **3.1.4 Monitoreo de métricas de entrenamiento** | **PS** | **Hecho con límite** |
| 3.1.5 Sprint Review | Los tres | Borrador (`docs/sprint6_que_se_hizo.md`) |

Observación: el Excel del plan asigna 3.1.3 a PS y 3.1.4 a BF, al revés de la especificación detallada. Hay que confirmar la asignación definitiva con el grupo.

## 3. Tarea 3.1.4: monitoreo del entrenamiento

**Qué es:** registro por episodio (pérdidas, recompensa, costo, cumplimiento, entropía, fracción de pasos en espera) y un conjunto de alertas que avisan cuando el entrenamiento va mal, sin modificar el entrenador (`src/training/monitoreo.py`, `scripts/monitorear_entrenamiento.py`).

**Por qué hacía falta:** en el Sprint 5 la red aprendió a esperar y solo se notó al evaluar. El monitoreo lo habría avisado durante el entrenamiento.

**Calibración:** se probaron las alertas contra 27 corridas con resultado conocido (12 de Poisson generadas a propósito y 15 de ABIDES).

| Hallazgo | Medido |
|---|---|
| Con los umbrales originales, `ENTROPIA_COLAPSADA` avisaba en corridas buenas | 2 de 4 |
| Con los umbrales originales, `PICO_PERDIDA_CRITICO` avisaba en corridas buenas | 4 de 4 |
| Alerta nueva `RECOMPENSA_SUBE_COSTO_NO` (la recompensa mejora y el costo no) | avisa en 7 de 10 corridas malas y en 0 de 4 buenas |
| Entropía baja por sí sola | pasa a nivel informativo (es normal que una política que aprende se concentre) |

El panel dibuja, para cada corrida, una línea con su costo de partida: si la curva no baja de ahí, el costo no mejoró. Guía de lectura: `docs/guia_alertas_monitoreo_PS.md`.

**Límite:** falta conectarlo a las corridas del ajuste de hiperparámetros de MR (dos líneas, con su visto bueno).

## 4. Diagnóstico del entrenamiento del Ejecutor

**Problema:** con 1.000 episodios y la recompensa original, las redes entrenadas cumplían la orden con dificultad y el costo no mejoraba.

**Causa (medida en Poisson, visible en ABIDES):**
1. Nada obliga a completar la orden: esperar siempre da la recompensa máxima (cero). La red llega a esperar entre el 97 % y el 99 % de los pasos.
2. Con γ = 0,95, un costo al final de la ventana de 30 pasos se ve multiplicado por 0,95²⁹ ≈ 0,23: casi cuatro veces más barato que pagarlo al inicio.

**Arreglo probado en Poisson:** penalización de 30 bps por acción sin comprar al terminar la ventana, y γ = 1. Con ambos, 5 de 5 redes cumplen la orden y llegan al costo de la mejor heurística (17,9 bps frente a 17,91 de TWAP límite; la red inicial, 20,26). Cada cambio por separado no funciona (0 de 5). Otras variantes (arranque por imitación, costo de espera de 100 bps, tamaños aleatorios) no mejoraron la base.

**Declaración necesaria:** γ = 1 se aparta del Título I (γ_E = 0,95); debe anotarse en `DESVIACIONES_TITULO1_VS_IMPLEMENTACION.md` si se adopta.

## 5. Lo medido en ABIDES

### 5.1 Sistema completo sin entrenar (C-3)

Flujo Maestro–Ejecutores sobre las 10 meta-órdenes, mismas semillas de mercado que TWAP y VWAP (pareo válido en 20 de 20 corridas).

- Cumple el 66,3 % de las órdenes (apertura 94,6 %; media jornada 76,3 %; cierre 18,5 %).
- En costo no se distingue de TWAP (+16,5 bps, p = 0,43).
- Con costo ajustado por lo no ejecutado: con 50 a 100 bps de penalización por acción sin comprar sigue sin distinguirse de TWAP; con 300 bps es 83 bps peor. **La conclusión depende de cómo se valore lo no ejecutado**, que es una decisión del grupo.
- Un «ahorro» de 43 bps frente a TWAP en el primer intento era un artefacto (el sistema solo ejecutaba el 88,5 % de la orden) y se descartó. También se encontró y corrigió que las redes sin entrenar se creaban sin semilla.

### 5.2 Estabilidad de la decisión D3 (opción 0 u opción A de R_E)

- 100 episodios, 10 redes: la regla de vigilancia (cumplimiento con argmax < 95 %) se dispara en 2 de 5 redes con la opción 0 y 1 de 5 con la A (Fisher p = 1,0). Las 10 redes siguen con entropía de 99,6 % a 99,9 % del máximo: el argmax de una política casi uniforme mide el azar.
- 1.000 episodios, 6 redes: se dispara en 1 de 3 con la opción 0 y 0 de 3 con la A; la opción A baja los pasos en espera de ≈ 30 % a 6–8 %. La decisión es de BF; la evidencia favorece la A solo por robustez del cumplimiento, no por costo.

### 5.3 Reevaluación con 300 semillas (resultado principal)

Se evaluaron en las mismas 300 semillas (5001 a 5300): 8 redes ya entrenadas, el control de cada una (la misma red sin entrenar, muestreando su política) y 3 heurísticas.

| Comparación | Diferencia media (bps) | IC 95 % | Lectura |
|---|---:|---|---|
| 8 redes juntas − su control | −0,08 | [−0,98; +0,77] | Sin efecto medible (Wilcoxon p = 0,79) |
| Cada red − su control | −0,6 a +1,0 | todos con el 0 | Sin efecto |
| V2 − V4 (promedios) | −0,19 frente a −0,21 | | La recompensa contra el precio de llegada no aporta |
| Control − TWAP límite | +2,3 a +2,4 | 0 fuera | La política sin entrenar cuesta ≈ 2 bps más que TWAP |
| Redes − TWAP límite | +1,9 a +3,3 | 6 de 8 con el 0 fuera | Igual que el control |

(V2 = recompensa original + penalización 30 bps + γ = 1. V4 = recompensa contra el precio de llegada + penalización + γ = 1. Redes antiguas: γ = 0,95 sin penalización.)

- Todas las redes completan la orden al muestrear la política (cumplimiento 1,000). Se resolvió el problema de esperar; **el costo no mejoró**.
- Si entrenar redujo el costo, lo hizo en menos de ≈ 1 bps, lejos de los 3 a 6 bps que justificarían el proyecto.
- Slippage medio: redes 6,5 a 8,0 bps; control ≈ 7,0; TWAP límite 4,65 (cumplimiento 0,989); agresiva 9,8; pasiva 10,1.

### 5.4 Por qué los resultados anteriores se contradecían

En ABIDES el slippage de cada semilla lo domina hacia dónde se mueve el precio (entre −25 y +75 bps, igual para todas las estrategias). La diferencia red − control por semilla tiene desviación de 10 a 12 bps, así que con 15 semillas el error es de ±6 bps y con 40, ±3,5. Los «+3,0 bps» (15 semillas) y «−2,4 bps» (40) eran compatibles con cero desde el principio.

Regla práctica: detectar 3 bps con 80 % de potencia pide ≈ 120 semillas pareadas; 2 bps, ≈ 270; 1 bps, más de 1.000.

## 6. Metodología que conviene describir en el Título II

- **Control muestreado:** la referencia justa para una red entrenada es la misma red sin entrenar muestreando su política (no el argmax de una red sin entrenar, que a veces no ejecuta).
- **Pareo por semilla:** todas las estrategias se evalúan sobre las mismas semillas de mercado; se analiza la diferencia por semilla.
- **Intervalos de confianza:** bootstrap de 3.000 remuestreos sobre las diferencias por semilla; Wilcoxon como contraste auxiliar.
- **Costo ajustado por lo no ejecutado:** una orden incompleta no puede parecer más barata; se informan varios valores de penalización (50, 100, 300 bps).
- **Semilla de red fija** para las redes sin entrenar (reproducibilidad).
- **Hallazgo de reproducibilidad (Sprint 5):** reanudar un entrenamiento desde un checkpoint cambia los resultados porque el checkpoint no guarda el estado aleatorio (pendiente para MR).

## 7. Precisión del experimento de 90 corridas

> **Corrección del 29 de octubre:** la «hipótesis del 10 %» no está en el Título I; venía de un error en `Contexto_Agente_Programacion.md`. El Título I pide comparar con TWAP y VWAP y verificar si hay reducción del costo (objetivo específico 4 y sección 7), sin un umbral. Lo que sigue sobre el tamaño de efecto detectable (≈ 20 bps con 90 corridas) vale igual, pero como límite de precisión del experimento, no como hipótesis a contrastar.

El plan de evaluación prevé 90 corridas (3 niveles de liquidez × 3 tamaños × 10 semillas). Con el sistema sin entrenar, la desviación de la diferencia pareada es ≈ 70 bps por celda, de modo que la diferencia mínima detectable con 90 corridas es ≈ 20 bps. Diferencias más chicas que eso no se podrían distinguir del ruido del precio, aunque existan.

Qué se hace (a confirmar con la profesora guía): mantener el pareo por semilla y reportar el IC junto al p-valor, y presentar el resultado como «reducción medida con su intervalo», que es lo que pide el Título I. Recalcular con el sistema entrenado.

## 8. Limitaciones y pendientes

- Un solo ticker (FALABELLA), un solo tramo (apertura) y una sola `q_slice` de 1.000 en la reevaluación; no se generaliza a otros escenarios.
- De las redes V4, las semillas 3000 y 4000 no entraron en las 300 semillas (con 40 semillas: −1,13 y −0,20 bps, sin diferencia); de las redes antiguas solo entraron 2 de 4.
- 1.000 episodios dejan una política casi uniforme (entropía final de 80 % a 87 %). **Hipótesis, no probada:** más episodios (5.000 a 10.000, ≈ 2 horas por red en Colab) o una recompensa pareada contra TWAP en la misma semilla (cancela el precio común) permitirían aprender. Alternativa: aceptar el resultado negativo del Ejecutor solo y concentrar el trabajo en el Maestro.
- El Maestro aún no se entrena: falta el bucle de entrenamiento (MR). No hay evidencia de que mejore el costo.
- Las decisiones D1 (tamaño de las meta-órdenes) y D3 (R_E) de BF siguen sin respuesta; rigen las reglas por defecto de `docs/sprint6_que_se_hizo.md`.
- Los niveles de liquidez no están definidos, por eso no se pueden correr las 90 corridas ni la sensibilidad 3.2.4 (el script está listo y probado con datos sintéticos).

## 9. Fuentes (rutas en el repositorio)

| Tema | Documento | Datos o código |
|---|---|---|
| Resumen del sprint | `docs/sprint6_que_se_hizo.md` | |
| Monitoreo | `docs/guia_alertas_monitoreo_PS.md`, `docs/calibracion_monitoreo_PS.md` | `src/training/monitoreo.py`, `scripts/calibrar_monitoreo_ps.py` |
| Diagnóstico de recompensa | `docs/diagnostico_recompensa_PS.md`, `docs/investigacion_recompensa_que_se_hizo.md`, `docs/experimentos_recompensa_PS.md` | `data/experimentos_recompensa/` |
| Propuesta a BF y MR | `docs/propuesta_cambio_RE_para_BF_y_MR.md` | |
| Estabilidad de D3 | `docs/estabilidad_D3_PS.md`, `docs/estabilidad_D3_1000ep_PS.md`, `docs/decision_RE_final_D3_para_BF.md` | `data/colab_resultados/d3_estabilidad/`, `d3_1000ep/` |
| Sistema sin entrenar | `docs/c3_sistema_sin_entrenar_PS.md`, `docs/sistema_sin_entrenar_v2_vs_benchmarks_PS.md` | `data/colab_resultados/c3_sistema_v2/` |
| Confirmación en ABIDES y V4 | `docs/confirmacion_abides_penalizacion_resultado_PS.md`, `docs/v4_abides_resultado_parcial_A_PS.md` | `data/colab_resultados/conf_pen30_g1/`, `v4_pen30_g1_A/`, `v4_pen30_g1_B/` |
| **Reevaluación con 300 semillas** | `docs/reeval_300_resultado_PS.md`, `docs/reeval_300_ABIDES_PS.md` | `data/colab_resultados/reeval_300/`, `scripts/analizar_reevaluacion_ps.py` |
| Sensibilidad 3.2.4 y costo ajustado | `docs/sistema_sin_entrenar_v2_ajustado_PS.md` | `scripts/analizar_sensibilidad_3_2_4.py`, `scripts/comparar_sistema_vs_benchmarks.py` |
| Plan para MR y BF | `docs/plan_dejar_listo_MR_y_BF_PS.md` | |
| Figuras y su explicación | `docs/guia_graficos.md`, `docs/figuras_cientificas/README.md` | `data/analysis/` |
| Bitácora de cada rama | `docs/bitacora_cambios_PS.md` | |

## 10. Texto sugerido para el Título II (cuando se actualice el documento)

> Durante el Sprint 6 se implementó un sistema de monitoreo del entrenamiento con alertas calibradas sobre 27 corridas de resultado conocido. El monitoreo permitió identificar que, con la recompensa original y un factor de descuento de 0,95, el Ejecutor aprendía a esperar. Una penalización de 30 puntos base por acción no ejecutada y un factor de descuento de 1 corrigieron este comportamiento: en ABIDES las redes completan la orden. Sin embargo, una reevaluación pareada con 300 semillas no detectó diferencias de costo entre las redes entrenadas y la misma red sin entrenar (diferencia media −0,08 bps; IC 95 % de −0,98 a +0,77 bps), por lo que el entrenamiento del Ejecutor por sí solo, con 1.000 episodios, no redujo el slippage de forma medible. Estos resultados se presentan como hallazgo negativo y motivan concentrar el trabajo en la coordinación del Maestro y en un entrenamiento más largo. Se utilizó asistencia de IA (Claude Code), conforme a la autorización de la universidad.

**Cuidado al citar:** no usar las cifras de 15 o 40 semillas como evidencia de costo; declarar γ = 1 como desviación del Título I; la comparación con TWAP depende del valor de la penalización por lo no ejecutado.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
