# Guía de gráficos del proyecto

**Para qué sirve:** explicar cada gráfico que hay en el repositorio: qué muestra, cómo leerlo, de dónde salen los datos, qué conclusión permite sacar y qué no. **Regla:** todo PR que agregue un gráfico agrega su entrada aquí (ver `docs/bitacora_cambios_PS.md`).

**Elaborado por:** PS con apoyo de Claude Code (uso autorizado por la universidad), 22 de octubre de 2026. Las descripciones se hicieron mirando cada imagen y contrastando las cifras con los documentos de cada tarea.

**Glosario mínimo:** *bps* = puntos base (1 bps = 0,01 %). *IS* = Implementation Shortfall (costo de ejecutar frente al precio de referencia). *Tramo* = apertura (09:30–11:00 o 11:30 según el módulo), media jornada, cierre (14:00–16:00). *Semilla* = número que fija el azar de una simulación.

## 1. Datos y mercado real (sprints 2 y 3)

### `results/sprint2/FALABELLA_volumen_intradiario.png`
- **Qué muestra:** volumen promedio por vela de 5 minutos de FALABELLA a lo largo del día (eje X: hora; eje Y: acciones).
- **Cómo leerlo:** los picos aislados marcan velas con mucho volumen (alrededor de las 10:30, 11:30, 12:30, 14:30 y 15:30); el mayor es el de las 15:55, donde se fusionó la subasta de cierre.
- **Datos:** snapshot del 23 de agosto de 2026, pipeline de limpieza (BF).
- **Conclusión:** sirve de control de calidad del pipeline: el máximo en 15:55 es coherente con la fusión de la subasta de cierre en esa vela.
- **Límite:** es un promedio sobre 60 días; los picos dependen de pocos días.

### `results/sprint2/FALABELLA_volatilidad_intradiario.png`
- **Qué muestra:** desviación estándar promedio del precio de cierre por vela de 5 minutos (en pesos).
- **Cómo leerlo:** la volatilidad empieza alta (cerca de 19 pesos) y cae durante la mañana hasta cerca de 9 pesos; sube al final del día.
- **Datos:** mismo snapshot. **Conclusión:** la volatilidad es mayor en la apertura que en la media jornada.

### `results/sprint3/FALABELLA_perfil_30min.png` y `results/sprint3/tierA_perfil_30min.png`
- **Qué muestran:** ocho perfiles por bloques de 30 minutos: tres estimadores del spread (Roll, rango máximo–mínimo y Corwin–Schultz), el de Abdi–Ranaldo, volatilidad de 5 minutos, dos razones de spread sobre volatilidad y volumen mediano por vela. La primera figura es FALABELLA; la segunda, la mediana de los tickers de cobertura alta (tier A).
- **Cómo leerlos:** cada línea es un snapshot distinto (23 de agosto, 27 de septiembre y 27 de septiembre desde el 1 de septiembre); la franja gris es la media jornada.
- **Conclusión:** los spreads son mayores en la apertura y decrecen durante el día (forma de "L"), de forma consistente entre snapshots.
- **Límite:** son proxies calculados desde velas de 5 minutos, no el spread cotizado; no hay datos de Nivel 2.

### `data/analysis/perfil_mercado_ipsa_real.png`
- **Qué muestra:** tres paneles de barras por tramo: spread relativo promedio, volatilidad promedio y volumen promedio por vela, para los 30 tickers del IPSA.
- **Cómo leerlo:** spread 0,138 % (apertura), 0,112 % (media jornada) y 0,128 % (cierre); volatilidad 0,00251, 0,00156 y 0,00151; volumen 396.765, 456.967 y 698.419 acciones por vela.
- **Datos y script:** 140.400 observaciones del snapshot del 23 de septiembre; `PYTHONPATH=. python src/analysis/market_validation.py`.
- **Conclusión:** el patrón no es en "U": el spread y la volatilidad decrecen en el día y el volumen crece hacia el cierre.
- **Límite:** el spread es un proxy (rango máximo–mínimo de la vela).

### `results/sprint3/FALABELLA_poisson_por_tramo.png`
- **Qué muestra:** arriba, para cada tramo, el histograma de los retornos de 5 minutos observados (azul) frente a los simulados con Poisson (naranja), con el estadístico KS y su valor p. Abajo, los parámetros: llegadas por paso de 30 segundos (λ⁺ compras y λ⁻ ventas), θ (cancelaciones, proxy de persistencia) y los proxies de spread (Roll y rango máximo–mínimo).
- **Cómo leerlo:** si las dos formas coincidieran, el valor p sería alto; aquí el KS es 0,100, 0,116 y 0,114 con p muy pequeños (2,2e-08, 3,5e-15, 7,5e-12). Los datos reales tienen una barra muy alta en cero y colas más pesadas.
- **Datos y script:** snapshot del 23 de agosto; `src/envs/calibration_poisson.py`.
- **Conclusión:** los parámetros sirven como intensidades de entrada del simulador, no como generador directo de retornos de 5 minutos.

## 2. Arquitectura y ciclo (sprints 2 y 3)

### `docs/informe_titulo2/generador/fig/arquitectura.png`
- **Qué muestra:** el Agente Maestro (observa S_M, 7 variables, decide cada 30 minutos α y ventana), los tres Ejecutores (apertura, media jornada, cierre; observan S_E, 27 variables, actúan cada 30 segundos) y el mercado simulado (ABIDES-Gym o Poisson), con los mensajes ASIGNAR y REPORTE.
- **Cómo leerlo:** de arriba abajo: el Maestro asigna al Ejecutor del tramo, el Ejecutor envía órdenes al mercado y devuelve el reporte.

### `docs/diagrama_ciclo_reset_step.png`
- **Qué muestra:** diagrama de flujo del ciclo de un episodio: `env.reset()`, carga de datos, inicialización de ABIDES-Gym, cálculo de S_M, decisión del Maestro, mensaje ASIGNAR, bucle del Ejecutor durante `ventana_min × 2` pasos, mensaje REPORTE, actualización del inventario, avance de 30 minutos y, a las 16:00, cálculo de R_M terminal y cierre.
- **Cómo leerlo:** los rombos son decisiones (¿terminó la jornada?, ¿se completó la ventana?).

## 3. Benchmarks (sprints 4 y 5)

### `data/analysis/benchmarks_twap_vwap.png`
- **Qué muestra:** izquierda, cajas del IS de TWAP y VWAP en 10 corridas; derecha, el IS de cada una de las 10 meta-órdenes (misma semilla) para ambas estrategias.
- **Cómo leerlo:** TWAP queda entre 36.700 y 37.300 pesos y VWAP entre 35.300 y 35.900; las líneas no se cruzan: VWAP es mejor en las 10.
- **Datos y script:** 10 meta-órdenes de 5.000 acciones de FALABELLA con el simulador de Poisson; `PYTHONPATH=. python src/analysis/benchmarks.py`. Resultado: VWAP cuesta 3,8 % menos (Wilcoxon p = 0,00195).
- **Límite:** simulador de Poisson, no ABIDES; órdenes de un solo tamaño.

### `data/analysis/benchmarks_meta_ordenes.png` (rama `feature/ps-sprint5-final-v2`)
- **Qué muestra:** slippage medio (bps) de TWAP y VWAP para cada una de las 10 meta-órdenes oficiales (100.000 acciones), con el error estándar entre semillas como barras de error.
- **Cómo leerlo:** MO-06 (ECL en media jornada) es la más cara (más de 300 bps); MO-01 y MO-08 (FALABELLA) quedan cerca de cero o con barras muy anchas, es decir, mucho ruido entre semillas. En las órdenes de cierre (MO-08 a MO-10) TWAP y VWAP son idénticos.
- **Datos y script:** `data/colab_resultados/benchmarks_meta_ordenes_abides.json`; `scripts/analizar_benchmarks_meta_ordenes.py`.
- **Conclusión:** con solo 2 semillas, TWAP y VWAP no se distinguen de forma clara; lo más informativo es el cumplimiento de las órdenes (ver `docs/benchmarks_2.3.4_PS.md`).

### `data/analysis/benchmarks_meta_ordenes_v2.png` (rama `feature/ps-sprint6-ejecucion-parte-ps`)
- **Qué muestra:** lo mismo que `benchmarks_meta_ordenes.png`, pero para el archivo candidato v2 (10 % del volumen del día en apertura y media jornada, 5 % en el cierre): slippage medio (bps) de TWAP y VWAP por meta-orden, con el error estándar entre semillas.
- **Cómo leerlo:** las órdenes de ECL en media jornada son las más caras (MO-06, 310 bps con TWAP), como con 100.000 acciones; COPEC y ECL cuestan más que FALABELLA en apertura. En las tres órdenes de cierre (MO-08 a MO-10) TWAP y VWAP coinciden porque queda un solo tramo. Las barras de MO-08 son muy anchas: con 2 semillas el ruido es grande.
- **Datos y script:** `data/colab_resultados/benchmarks_meta_ordenes_abides_v2.json` (ensamblado con `scripts/ensamblar_benchmarks_meta_ordenes.py`); `scripts/analizar_benchmarks_meta_ordenes.py`. Análisis completo en `docs/benchmarks_2.3.4_v2_PS.md`.
- **Conclusión:** las 10 órdenes son ejecutables (19 de 20 corridas llegan al 95 %), TWAP − VWAP = −6,59 bps y no es significativo (p = 0,297). Es la base de comparación si BF elige la opción de D1 con 10 % y 5 %.

### `data/analysis/estabilidad_D3.png` (rama `feature/ps-sprint6-d3-estabilidad-resultados`)
- **Qué muestra:** el cumplimiento de la orden de cada red entrenada (un punto por semilla de red), separado por opción de R_E: punto lleno = evaluación con argmax, punto vacío = evaluación muestreando la política. La línea punteada es el umbral de 95 % de la regla de D3.
- **Cómo leerlo:** si los puntos llenos de la opción 0 quedan bajo la línea en varias semillas y los de la opción A quedan arriba, la regla se dispara por la opción y no por una red en particular. Un punto vacío arriba con el lleno abajo significa "la red ejecuta al muestrearla, pero con argmax elige esperar".
- **Datos y script:** `d3_opcion*_s*/entrenamiento_inicial_apertura.json` que deja `scripts/colab/d3_estabilidad_ps.py`; `scripts/analizar_estabilidad_D3.py` (informe en `docs/estabilidad_D3_PS.md`).
- **Límite:** 5 redes por opción; la comparación entre opciones es descriptiva.
- **Resultado (23 de octubre):** con la opción 0 dos de cinco redes incumplen (semillas 1000 y 4000: 0,904 y 0,646); con la A, una de cinco (semilla 2000: 0,115). Con muestreo, las diez cumplen. No hay diferencia entre opciones (Fisher p = 1,0).

### `data/analysis/monitoreo_d3_estabilidad.png` (misma rama)
- **Qué muestra:** el panel de monitoreo con las diez corridas juntas (cinco por opción): retorno, slippage, cumplimiento y pasos en espera por episodio, y entropía, KL, pérdida del crítico y fracción recortada por actualización.
- **Cómo leerlo:** el cumplimiento queda en 1,0 durante todo el entrenamiento (política muestreada) y la entropía solo baja de 5,48 a ≈ 5,46 nats (99,6 % a 99,9 % del máximo): tras 100 episodios las redes siguen casi uniformes, por eso el argmax es inestable. La fracción recortada es 0 y la KL ronda 10⁻⁴: actualizaciones muy pequeñas.
- **Datos y script:** `data/colab_resultados/d3_estabilidad/`; `scripts/monitorear_entrenamiento.py --dir …`; alertas en `docs/monitoreo_d3_estabilidad.md`. Es además la validación del monitoreo con ABIDES real.

## 4. Validación del simulador (sprint 4)

### `data/analysis/validacion_formal_2_2_5.png` (FALABELLA), `..._COPEC.png` y `..._ECL.png`
- **Qué muestran:** arriba, la distribución acumulada (CDF) de los retornos de 5 minutos por tramo: real (azul oscuro), simulado calibrado (amarillo) y, en FALABELLA, simulado de fábrica (azul claro). Abajo, cajas del valor absoluto del retorno (real, calibrado y de fábrica).
- **Cómo leerlos:** cuanto más pegadas están las curvas, más se parece el simulador al mercado. El simulador de fábrica es casi una línea vertical (retornos muy pequeños); el calibrado sigue a la curva real. La distancia máxima entre curvas es el estadístico D del KS (FALABELLA: 0,073, 0,098 y 0,066).
- **Datos y script:** 30 semillas por tramo; `src/analysis/validacion_formal.py` y `scripts/colab/validacion_2_2_5_ps.py`; informes `docs/validacion_formal_2.2.5*_PS.md`.
- **Conclusión:** la calibración acerca el simulador al mercado (D baja de 0,28–0,32 a 0,07–0,10), pero con el criterio literal del plan el KS rechaza.
- **Límite:** un solo activo por figura; valores agrupados de varios días.

## 5. Entrenamiento y monitoreo (sprints 5 y 6)

### `data/analysis/entrenamiento_inicial_2.3.5.png`
- **Qué muestra:** seis paneles del entrenamiento del Ejecutor (1.000 episodios, apertura, opción 0): retorno medio (cada 10 episodios), pérdida del actor, pérdida del crítico, divergencia KL, entropía y fracción recortada.
- **Cómo leerlo:** la entropía baja de 5,48 a 4,39: la política se concentra (con 100 episodios apenas se movía). El retorno medio sube de cerca de −2 a cerca de −1. Los picos aislados de la pérdida del crítico (episodios 430 y 950) coinciden con actualizaciones inestables, pero se recupera. El KL y la fracción recortada crecen con el tiempo, siempre bajo el objetivo del entrenador (KL 0,015).
- **Datos y script:** `data/colab_resultados/t5_1000ep_opcion0.csv`; `scripts/analizar_entrenamiento_inicial.py`.
- **Conclusión:** el entrenamiento es estable (sin valores no finitos), pero que baje la entropía no prueba que el agente ejecute mejor: con argmax elige "esperar" (ver `docs/entrenamiento_inicial_2.3.5.md`).

### `data/analysis/monitoreo_entrenamiento.png` (rama del Sprint 6)
- **Qué muestra:** panel de ocho gráficos para comparar corridas: retorno, slippage por episodio, cumplimiento y fracción de pasos en espera (si hay monitoreo por episodio) y entropía, KL, pérdida del crítico y fracción recortada (del CSV del entrenador). Cada corrida es una línea.
- **Cómo leerlo:** en el ejemplo (100 frente a 1.000 episodios, opción 0) los cuatro paneles de arriba muestran el aviso "sin monitoreo por episodio" porque esas corridas se hicieron antes de existir el registro; la entropía de la corrida de 1.000 episodios baja claramente.
- **Script:** `scripts/monitorear_entrenamiento.py`; informe de alertas en `docs/monitoreo_entrenamiento.md`.

## 6. Gráficos del informe de Título II

Se generan con `docs/informe_titulo2/generador/generar_figuras.py` a partir de cifras ya publicadas en los documentos de cada tarea (no calculan nada nuevo).

| Archivo (en `generador/fig/`) | Qué muestra | Fuente de las cifras |
|---|---|---|
| `lambda_maestro.png` | Razón entre la penalización por inventario y el slippage para cada λ (escala logarítmica); λ = 0,05 queda en 1,06 veces | `docs/calibracion_recompensa_maestro_2.2.2_MR.md` |
| `beta_fase2_apertura.png` | Slippage (con error estándar) y cumplimiento de la orden para cada β; la línea del cumplimiento marca el umbral de 95 % | `docs/beta_fase2_apertura_PS.md` |
| `rmsc04_volatilidad.png` | Volatilidad de 5 minutos simulada y real de FALABELLA por tramo (30 semillas) | `docs/calibracion_rmsc04_2.2.4_BF.md`, sección 8.3 |
| `horas_sprint.png` | Horas planificadas por sprint y horas completadas al 22 de octubre (216 de 604) | `plan-desarrollo-titulo-2.xlsx` y `docs/acta_cierre_sprints_1_a_4.md` |
| `perfil_mercado_ipsa_real.png`, `FALABELLA_poisson_por_tramo.png`, `FALABELLA_volumen_intradiario.png`, `benchmarks_twap_vwap.png`, `validacion_formal_2_2_5.png`, `arquitectura.png` | Copias de las figuras descritas en las secciones 1 a 4 | Ver arriba |

## 7. Gráficos de la presentación grupal (`docs/informe_titulo2/ppt/deck.js`)

- **Carta Gantt (diapositiva 4):** una fila por hito del Título I (H5 a H8); cada barra es un sprint de dos semanas; azul oscuro = completado, ámbar = en curso, gris = pendiente; los rombos rojos son el cierre de cada hito y la línea punteada es la fecha de la presentación (22 de octubre). Fechas: sprints 1 a 9 del plan (17 de agosto al 18 de diciembre de 2026).
- **Distancia D del KS antes y después de calibrar (diapositiva 11):** barras por tramo; valores de `docs/validacion_formal_2.2.5_PS.md`, sección 7.
- **IS de TWAP y VWAP (diapositiva 12):** 36.932 y 35.569 pesos; `docs/benchmarks_2.3.4_PS.md`.

### `data/analysis/sistema_sin_entrenar_vs_benchmarks.png` (rama `feature/ps-sprint6-c3-sistema-sin-entrenar`)
- **Qué muestra:** la diferencia de slippage (sistema sin entrenar − referencia, en bps) frente a TWAP y VWAP, con su intervalo de confianza del 95 %: el punto grueso es el total de las 20 celdas (orden × semilla) y los finos son los desgloses por tramo de inicio.
- **Cómo leerlo:** todos los intervalos quedan a la izquierda del cero, es decir, el sistema parece costar menos. **No es una ventaja real:** el sistema sin entrenar ejecuta solo el 88,5 % de la orden y el slippage no cuenta lo que no se compró. Sirve para validar el flujo, no para concluir.
- **Datos y script:** `data/colab_resultados/c3_sistema/` y `scripts/comparar_sistema_vs_benchmarks.py`; contexto en `docs/c3_sistema_sin_entrenar_PS.md`.

### `data/analysis/estabilidad_D3_1000ep.png` y `monitoreo_d3_1000ep.png` (rama `feature/ps-sprint6-d3-1000ep-resultados`)
- **`estabilidad_D3_1000ep.png`:** igual que la figura de 100 episodios, pero con redes de 1.000 episodios (3 por opción): punto lleno = cumplimiento con argmax, punto vacío = cumplimiento muestreando; la línea punteada es el 95 %. Se ve un solo punto bajo la línea, de la opción 0 (semilla 1000, cumplimiento 0,000).
- **`monitoreo_d3_1000ep.png`:** panel de monitoreo con las redes de 1.000 episodios que tienen CSV (5 de 6; falta el de la opción A, semilla 1000). La entropía baja mucho más que en 100 episodios (de 5,48 a entre 1,9 y 4,7 nats) y la fracción de pasos en espera cae en casi todas las redes. Las alertas de entropía colapsada (por debajo del 60 % del máximo) aparecen en dos redes (opción 0 semilla 2000 y opción A semilla 3000); en ambas el cumplimiento sigue en 1,0, así que la política se concentró en acciones que ejecutan.
- **Datos y script:** `data/colab_resultados/d3_1000ep/`; `scripts/analizar_estabilidad_D3.py` y `scripts/monitorear_entrenamiento.py --dir …`; alertas en `docs/monitoreo_d3_1000ep.md`.
## 8. Figuras científicas del proyecto (`docs/figuras_cientificas/`)

Cuatro figuras de formato artículo para informes y presentaciones; la explicación detallada de cada una, las fuentes de las cifras y los límites están en `docs/figuras_cientificas/README.md`.

| Archivo | Qué muestra | Cómo leerlo |
|---|---|---|
| `fig1_arquitectura` | Flujo completo: datos reales → calibración → simulador → agentes → entrenamiento y evaluación, y dónde corre cada pieza | De izquierda a derecha; los datos reales solo calibran el simulador, y los agentes aprenden dentro de él |
| `fig2_formulacion` | La jornada, el ciclo Maestro–Ejecutor, la especificación de los dos procesos de decisión y los mensajes del protocolo | El zoom de la parte (a) muestra que el Ejecutor opera solo 2v pasos de cada decisión de 30 minutos |
| `fig3_espacios` | Las 7 variables de S_M, las 27 de S_E, las 40 acciones del Maestro, las 240 del Ejecutor y las dos recompensas | El color de cada variable indica su origen: real, simulador, interno u hora |
| `fig4_diseno_experimental` | Protocolo, las 10 meta-órdenes (v1 y v2), el reparto de TWAP y VWAP y el resultado actual de las referencias | Las barras de la parte (d) son el slippage medio por orden con su error estándar entre semillas |

### `data/analysis/sistema_sin_entrenar_v2_vs_benchmarks.png` (rama `feature/ps-sprint6-c3-v2-y-control`)
- **Qué muestra:** igual que `sistema_sin_entrenar_vs_benchmarks.png`, pero con la red sin entrenar fija en las dos mitades: diferencia de slippage (sistema − referencia, en bps) frente a TWAP y VWAP, con el intervalo de confianza del 95 %.
- **Cómo leerlo:** los intervalos ahora incluyen el cero (frente a TWAP, +16,5 bps con IC de −15,9 a +49,8): no hay diferencia clara. Además el sistema ejecuta solo el 66 % de la orden, así que el costo no es comparable. Este gráfico reemplaza al del primer intento, cuyo «ahorro» de 43 bps era un artefacto.
- **Datos y script:** `data/colab_resultados/c3_sistema_v2/` y `scripts/comparar_sistema_vs_benchmarks.py`.

### `data/analysis/diagnostico_recompensa.png` y `experimentos_recompensa_A.png`, `_A2.png`, `_B.png` (rama `feature/ps-investigacion-recompensa`)
- **`diagnostico_recompensa.png` (cuatro paneles):** (a) porcentaje de pasos en espera durante el entrenamiento con la recompensa actual en Poisson: sube de ≈ 30 % a ≈ 98 %; (b) corridas de ABIDES: la recompensa sube y el slippage no baja; (c) recompensa R_E que recibe cada estrategia simple (esperar siempre recibe 0, el máximo); (d) costo real de esas mismas estrategias (esperar es de las más caras). La recompensa y el costo ordenan distinto.
- **`experimentos_recompensa_*.png` (tres paneles, una fila por variante):** costo en bps con 5.000 acciones (el eje no parte de cero; la línea gris es la red inicial y la verde, el TWAP con órdenes límite), porcentaje de pasos en espera (línea al 50 %) y cuántas de las 5 redes cumplen los tres criterios (línea en 4).
- **Cómo leerlos:** en `_A2` cinco variantes con γ = 1 llegan a la línea verde (el nivel de la mejor heurística) y cumplen 5 de 5; la recompensa original y el costo de espera denso no. En `_B` ningún ajuste adicional mejora la base.
- **Datos y script:** `data/experimentos_recompensa/` y `scripts/analizar_experimentos_recompensa.py`; contexto en `docs/experimentos_recompensa_PS.md`.

### `data/analysis/monitoreo_calibracion.png` y `sistema_sin_entrenar_v2_ajustado.png` (rama `feature/ps-sprint6-monitoreo-sensibilidad`)
- **`monitoreo_calibracion.png`:** el panel de monitoreo con 12 corridas de Poisson buenas y malas (variantes de recompensa con 2 semillas cada una). Las malas (recompensa actual, penalización con γ = 0,95) muestran el retorno subiendo hasta casi 0 y los pasos en espera yéndose a ≈ 100 %, con cumplimiento cayendo a 0; las buenas (penalización o liquidación con γ = 1) mantienen cumplimiento cercano a 1 y espera moderada. La línea punteada de cada corrida en el panel de slippage es su costo de partida.
- **Cómo leerlo:** el retorno por sí solo engaña (las malas son las que más «mejoran»); hay que mirarlo junto con el cumplimiento, la espera y si el slippage baja de su línea de partida.
- **`sistema_sin_entrenar_v2_ajustado.png`:** igual que los gráficos de comparación con TWAP y VWAP (intervalos de la diferencia de costo), pero con el sistema sin entrenar y el costo del tramo de inicio; el informe `docs/sistema_sin_entrenar_v2_ajustado_PS.md` agrega la tabla del costo ajustado con 50, 100 y 300 bps de penalización por lo no comprado.
- **Datos y script:** `data/calibracion_monitoreo/` y `scripts/monitorear_entrenamiento.py --dir …`; `scripts/comparar_sistema_vs_benchmarks.py`.

### `data/analysis/conf_pen30_g1.png` y `monitoreo_conf_pen30_g1.png` (rama `feature/ps-confirmacion-abides-penalizacion`)
- **`conf_pen30_g1.png`:** las 4 redes entrenadas en ABIDES con penalización de 30 bps y γ = 1, con su cumplimiento de la orden (punto lleno = política argmax, círculo vacío = política muestreada; misma figura que el análisis de estabilidad de D3). Con la política muestreada las cuatro cumplen (≈ 1,0); con argmax una red (semilla 2000) no compra nada (0,0) y otra queda en 0,93: el argmax de una política casi uniforme es arbitrario. El costo no está en esta figura: está en la tabla de `docs/conf_pen30_g1_ABIDES_PS.md`.
- **`monitoreo_conf_pen30_g1.png`:** el panel de monitoreo de esas cuatro corridas (retorno, pasos en espera, entropía, slippage con su línea de partida). El retorno mejora cerca de 50 % pero el slippage casi no baja: es el patrón que avisa la alerta `RECOMPENSA_SUBE_COSTO_NO`. La entropía final de 80–87 % indica que la política sigue siendo casi uniforme.
- **Cómo leerlos:** la mejora del retorno no es mejora del costo; lo que decide es la diferencia de slippage con el control sobre las mismas semillas (con 15 semillas +3,0 bps y 0 de 4 redes mejores; con 40 semillas el signo se invierte, ver `docs/v4_abides_resultado_parcial_A_PS.md`).
- **Datos y script:** `data/colab_resultados/conf_pen30_g1/`; `scripts/analizar_estabilidad_D3.py` y `scripts/monitorear_entrenamiento.py`.

### `data/analysis/v4_vs_v2_ABIDES_A.png` (rama `feature/ps-abides-v4-resultados-A`)
- **Qué muestra:** por cada red del cuaderno A (semillas 1000 y 2000), el slippage medio en 40 semillas de evaluación, política muestreada, de tres Ejecutores: la red sin entrenar (control, gris), V2 (recompensa original con penalización y γ = 1, naranja) y V4 (recompensa contra el precio de llegada con penalización y γ = 1, verde). Menos es mejor.
- **Cómo leerlo:** las dos variantes entrenadas quedan por debajo del control en la red 1000, y solo V2 en la 2000; entre V2 y V4 no hay un ganador claro. Son medias sobre 40 semillas en las que el movimiento del precio pesa mucho más que la diferencia entre barras, así que es orientativo; lo decide la reevaluación con 300 semillas (`docs/v4_abides_resultado_parcial_A_PS.md`).
- **Datos y script:** `data/colab_resultados/v4_pen30_g1_A/` y `scripts/comparar_v4_vs_v2_ps.py`.

### `data/analysis/reeval_300_ABIDES.png` (rama `feature/ps-reevaluacion-300-resultados`)
- **Qué muestra:** una fila por red entrenada (grises: original sin arreglo; naranjas: V2; verdes: V4). El punto es la diferencia media de slippage entre la red y su control (la misma red sin entrenar muestreando) en 300 semillas de evaluación; la barra es el intervalo de confianza al 95 %. A la izquierda del 0 la red cuesta menos que el control.
- **Cómo leerlo:** todas las barras cruzan el 0 y los puntos están entre −0,6 y +1 bps. Es decir, ninguna red se distingue del control: entrenar 1.000 episodios no cambió el costo de forma medible. Las barras de V4 son más cortas porque esas dos redes tienen menos variación entre semillas, no porque sean mejores.
- **Datos y script:** `data/colab_resultados/reeval_300/` y `scripts/analizar_reevaluacion_ps.py`; lectura completa en `docs/reeval_300_resultado_PS.md`.

### `barrido.png` del barrido de hiperparámetros (rama `feature/ps-cierre-sprint6`; `data/barrido_hp/3_1_1/` y `3_1_2/`)
- **Qué muestra:** una barra por configuración de hiperparámetros. La barra es la diferencia media de costo entre la red entrenada y su red inicial, en las mismas semillas de evaluación (negativo es mejor), con su IC 95 %. Las barras grises son las configuraciones que no completan el 95 % de la orden y no pueden ganar.
- **Cómo leerlo:** la decisión no es «la barra más baja». La regla fijada antes pide además que el IC del ganador no incluya la diferencia de la configuración por defecto; si la incluye, se queda la de por defecto. El texto de la decisión está en `barrido.md`.
- **Datos y script:** `scripts/barrido_hiperparametros_mr.py` y `scripts/colab/grid_specs/hiperparametros_ejecutor_mr.json`.

### `cajas.png` de las corridas de evaluación 3.1.3 (rama `feature/ps-cierre-sprint6`; `corridas_30/tabla/` en Drive)
- **Qué muestra:** una caja por estrategia (sistema final, TWAP y VWAP) con el costo de cada corrida en bps contra el precio de llegada. La línea es la mediana, el triángulo la media y los puntos sueltos las corridas extremas.
- **Cómo leerlo:** las cajas son anchas porque el costo de una jornada lo domina hacia dónde se movió el precio ese día. La comparación que vale es la pareada, por orden y semilla, de la tabla (`tabla_maestra.md`), no la distancia entre cajas.
- **Datos y script:** `scripts/consolidar_resultados_3_2_2.py`.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
