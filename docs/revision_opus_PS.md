# Revisión técnica del proyecto (29 de octubre de 2026)

**Elaborado por:** PS con apoyo de Claude Code (modelo Opus; uso de IA autorizado por la universidad). Revisión pedida por PS para saber si el proyecto va bien y buscar fallas. Se revisaron el Título I, el plan de sprints, la especificación, los documentos de los sprints 5 y 6 y el código de entrenamiento, entornos, recompensa y evaluación. **No se modificó código de MR. El parche de la recompensa (parte de BF) queda como borrador para que BF lo revise.**

Cada afirmación lleva su tipo: **medido** (sale de datos o de una prueba corrida), **inferido** (sale de leer el código, sin prueba en ABIDES) o **hipótesis**.

## 0. Actualización del 29 de octubre (noche): qué cambió después de los cuadernos

- **H1 (falla de la recompensa):** el parche se verificó en ABIDES. El precio de referencia es el de la decisión, y la correlación entre recompensa y costo con la política aleatoria pasó de −0,08 a 0,73. Pero las redes entrenadas con él **cuestan más** que su control: +1,55 bps, IC +0,37 a +2,71 (`docs/reeval_300_mid_resultado_PS.md`). La recompensa corregida no mide el costo de esperar. El parche era necesario, pero **no bastó**. Por eso queda como opción y no por defecto.
- **H3 (hipótesis del 10 %):** **no está en el Título I.** Venía de un error en `Contexto_Agente_Programacion.md`. El Título I pide comparar con TWAP y VWAP y verificar si hay reducción (objetivo específico 4). Lo de la precisión (≈ 20 bps detectables con 90 corridas) sigue valiendo como límite del experimento.
- **H4 (tamaños):** resuelto con `--aleatorizar` (rama `feature/ps-evaluador-90-corridas`).
- **H5 (β):** no se revalida, porque la recompensa corregida no quedó por defecto.
- **D3:** cerrada con la regla fijada: **opción 0** (`docs/reeval_300_mid_resultado_PS.md`, sección 5).
- **Ejecutor:** se agrega el arranque por imitación de TWAP límite seguido de PPO, sin cambiar la arquitectura del Título I. El Ejecutor del sistema final se elige con una regla fijada antes (`scripts/elegir_ejecutor_ps.py`).
- **Maestro:** primera prueba en ABIDES en `docs/maestro_abides_primera_prueba_PS.md`.

## 1. Veredicto

1. **El entrenador PPO de MR funciona** (medido): en una prueba trivial aprende la mejor acción en 1.000 episodios.
2. **Hay una falla en la recompensa del Ejecutor en ABIDES** (medido en las corridas e inferido del código). El precio pagado se compara con el precio medio de 30 segundos *después* y no con el precio al decidir. Por eso la recompensa casi no se relaciona con el costo: correlación de 0,04 a 0,22 en las 4 corridas V2. Esto explica por qué el Ejecutor aprendió en Poisson y no en ABIDES.
3. **Hay un segundo problema que la corrección no resuelve:** la mejora posible del Ejecutor (≈ 2 bps) es muy pequeña frente al movimiento del precio (≈ 16,6 bps por episodio).
4. **Riesgo más grande para terminar el Título II:** la hipótesis del 10 % no se puede contrastar tal como está escrita (corregido en la sección 0: ese 10 % no está en el Título I). Con 90 corridas solo se detectan ≈ 20 bps, y el 10 % del costo de TWAP en este escenario es ≈ 0,5 bps. Hay que decidir con la profesora guía cómo se formula, y el Maestro todavía no se entrena.
5. **Vamos a tiempo si:** la corrección se verifica esta semana y MR empieza el bucle del Maestro ya.

## 2. Hallazgos, de más a menos grave

| # | Qué es | Dónde | Cómo se comprobó | Consecuencia | De quién |
|---|---|---|---|---|---|
| H1 | R_E en ABIDES compara el precio pagado con el P_mid del despertar **siguiente**, que ya incluye el alza de la propia compra y 30 s de movimiento. En Poisson se usa el P_mid **de la decisión** | `src/envs/abides_ejecutor_env.py:144-150` (`raw_state_to_reward`) frente a `src/envs/fallback_poisson_env.py:148` (`p_mid_before`) | Lectura del código; prueba unitaria (comprar 1 CLP sobre el precio de decisión da **+1** en vez de **−1**); en las corridas V2 la correlación entre el retorno del episodio y el costo es de 0,04 a 0,22 (medido, 4.000 episodios) | El Ejecutor en ABIDES se entrenó con una señal casi sin relación con lo que se evalúa. Afecta a todas las corridas de ABIDES con la recompensa original (Sprint 5, D3, V2) | BF (R_E, 2.2.3) |
| H2 | La parte del costo que controla el Ejecutor es muy chica frente al ruido. Desviación del costo por episodio: 16,6 bps. El tipo de orden (mercado, límite o esperar) explica el 0,00 % de esa variación. Diferencia entre la mejor heurística y la política aleatoria: ≈ 2 bps | `data/colab_resultados/conf_pen30_g1/`, `v4_pen30_g1_*/` (`monitoreo_episodios.csv`) | Medido: regresión sobre 8.000 episodios. Prueba de cordura con el mismo nivel de señal/ruido: 1.000 episodios no aprenden nada y 20.000 llegan a medias (sección 3.2) | Con la recompensa contra el precio de llegada (V4) el ruido entra entero; con 1.000 episodios no se puede aprender. Corregir H1 debería sacar la mayor parte del ruido de la recompensa (**hipótesis**, se verifica en Colab) | Todos (diseño) |
| H3 | La hipótesis del 10 % no es contrastable con 90 corridas (corregido: el 10 % no está en el Título I; ver sección 0) | Título I (hipótesis), `docs/informe_sprint6_PS.md` sección 7 | Medido: TWAP límite cuesta 4,65 bps en el escenario de la reevaluación, así que el 10 % son ≈ 0,5 bps; la diferencia mínima detectable con 90 corridas es ≈ 20 bps | Aunque el sistema mejore, el resultado no podría confirmar la hipótesis tal como está escrita | PS con el grupo y la profesora guía |
| H4 | El Ejecutor solo se entrena con 1.000 acciones y 15 minutos, pero el Maestro le pedirá de 1.000 a 20.000 acciones y ventanas de 1 a 15 minutos | `scripts/colab/entrenamiento_inicial_ps.py` (`--q-slice 1000`, `--ventana-min 15`) frente a `src/experiments/variantes_recompensa.py:42-43` | Inferido del código | Al entrenar el Maestro, el Ejecutor trabajará en tamaños que nunca vio. Con órdenes grandes el impacto pesa más y la táctica importa más (**hipótesis**) | MR y BF |
| H5 | β* salió del barrido de BF en ABIDES, cuyo término de precio tiene la falla H1 | `src/config/market_params.py:84-92` | Inferido | β ya está marcado como provisional; con la recompensa corregida hay que revalidarlo | BF |
| H6 | La entropía «80 % a 87 % del máximo» exagera lo uniforme de la política. De las 240 acciones, las 80 de «LIMIT_SELL» son todas «esperar», y en las 80 de mercado el nivel de precio no cambia nada; en la práctica hay 91 acciones distintas | `src/envs/abides_bridge.py:157-177`, `src/envs/spaces.py:311-363` | Inferido del código | La métrica del monitoreo hay que leerla con cuidado; se puede corregir calculando la entropía sobre acciones efectivas | PS (monitoreo) |
| H7 | Las semillas de entrenamiento de una red de semilla *s* son *s*+1 a *s*+1.000 y las de evaluación son 5.001 a 5.300. Con las semillas usadas (1.000 a 4.000) no se cruzan, pero una red con semilla ≥ 4.001 entrenaría sobre semillas de evaluación | `src/training/ppo_trainer.py:335` | Medido en el código | Riesgo de fuga en corridas futuras; basta con no usar semillas de red entre 4.001 y 5.300 | MR / PS |
| H8 | El checkpoint no guarda el estado aleatorio: reanudar cambia los resultados (ya conocido) | `src/training/ppo_trainer.py:283-299` | Ya documentado en el Sprint 5 | Reproducibilidad de corridas cortadas | MR |
| H9 | D3 lleva dos semanas sin respuesta, y la evidencia que tenía se midió con la recompensa con falla | `docs/decision_RE_final_D3_para_BF.md` | — | Ver la sección 6: propuesta para cerrarla con datos nuevos | BF |

**Lo que se revisó y está bien:**
- **PPO:** GAE con frontera de episodio, normalización de ventajas, recorte, signos de las pérdidas, recorte de gradiente y parada por KL (medido con la prueba de cordura).
- **Control:** la misma red inicial que el entrenamiento.
- **Pareo:** heurísticas, control y redes se evalúan en las mismas semillas.
- **Slippage de evaluación:** se calcula contra el precio de llegada con los mismos datos para todas las estrategias, así que no lo afecta H1.

## 3. La falla principal: prueba y parche

### 3.1 Qué pasa

En cada paso, ABIDES arma primero el estado y después la recompensa del despertar siguiente. `raw_state_to_reward` toma el P_mid de **ese** despertar. Cuando el Ejecutor compra a mercado, su propia compra sube el precio, y la recompensa `(P_mid_después − P_pagado)` le sale menos negativa, o incluso positiva. Además, 30 s de movimiento del mercado entran como ruido en cada paso. En Poisson se usa el P_mid antes de ejecutar, y ahí el entrenamiento sí aprendió (5 de 5 redes llegaron a la mejor heurística).

### 3.2 Pruebas

| Prueba | Antes | Después |
|---|---|---|
| Unitaria: comprar 1.000 acciones a 101 CLP con P_mid de decisión 100 y P_mid siguiente 102 (`tests/test_mid_decision.py`) | R_E = **+1,0** CLP por acción (premia comprar caro) | R_E = **−1,0** |
| Correlación entre el retorno del episodio y el costo, corridas V2 en ABIDES (medido, 4 × 1.000 episodios) | 0,04 a 0,22 | por medir en Colab (cuaderno de verificación) |
| Prueba de cordura del PPO de MR (`scripts/prueba_cordura_ppo_ps.py`, sin cambios en el código de MR): probabilidad de elegir la acción buena, partiendo de 0,33 | — | sin ruido: 0,999 en 1.000 episodios; señal/ruido 1: 0,67; señal/ruido 0,3: 0,37 (1.000) y 0,97 (20.000); como ABIDES (0,12): 0,34 (1.000) y 0,64 (20.000) |

### 3.3 El parche (BORRADOR de PS para BF)

- `src/envs/abides_bridge.py`: `ExecutorRewardState.step` acepta `mid_decision`. Si llega, el término de precio se mide contra ese valor, y se registra en `info["p_ref_precio_clp"]`.
- `src/envs/abides_ejecutor_env.py`: opción `mid_decision=False`. Con `True`, el entorno guarda el P_mid que vio el agente y lo pasa a la recompensa del paso siguiente.
- `scripts/colab/entrenamiento_inicial_ps.py`: opción `--mid-decision`, que solo entra en la firma de la corrida si se usa.
- **Apagado por defecto:** las corridas anteriores no cambian. Si BF lo acepta, lo correcto es dejarlo encendido por defecto en la 2.2.3.
- Falta comprobar en ABIDES el supuesto de que el estado se arma antes que la recompensa. Lo comprueba `scripts/colab/verificar_mid_decision_ps.py`: en el paso 1 el precio de referencia debe ser el de entrada, y en el paso *k*, el P_mid del paso *k* − 1.

## 4. Qué hay que repetir

| Qué | Por qué | Cuaderno | Tiempo |
|---|---|---|---|
| Verificación del parche (no entrena) | Confirmar en ABIDES el precio usado y que la recompensa se relaciona con el costo | Paso 1 de `notebooks/Colab_mid_decision_A.ipynb` (y de B) | ≈ 5 min |
| 4 redes V2 con el parche (opción 0, semillas 1.000 a 4.000) | Ver si el Ejecutor aprende con la recompensa corregida | `Colab_mid_decision_A.ipynb` y `_B.ipynb`, en paralelo | ≈ 2 h 45 min cada cuaderno |
| 2 redes con la opción A y el parche (semillas 1.000 y 2.000) | Cerrar D3 con datos válidos (sección 6) | Incluidas en A y B | (incluido) |
| Reevaluación con 300 semillas de las 6 redes | Comparar con el control y TWAP con precisión de ±1 bps | `notebooks/Colab_reevaluacion_mid_decision_300.ipynb` (reutiliza control y heurísticas de `reeval_300`) | ≈ 70 min (+25 min opcional, V4 3.000 y 4.000) |
| **No se repiten:** Sprint 5 (T5), D3 de 100 y 1.000 episodios, V2 anterior | Quedan como historia con una nota «medido con la recompensa de ABIDES con falla» | — | — |
| Revalidar β (H5) | Solo si el parche funciona | Por preparar | ≈ 2 h por β |

Total de Colab ahora: ≈ 4 h si A y B corren en paralelo (Colab gratis permite dos cuadernos).

## 5. Plan de los próximos 10 días (29 de octubre al 7 de noviembre)

| Días | PS | MR | BF |
|---|---|---|---|
| Jue 29 – vie 30 oct | Subir la rama (con OK), mandar el mensaje a BF y correr los cuadernos A y B | Leer H1 y H4 (15 min). Empezar el bucle del Maestro (M1 del plan), que no depende del parche | Revisar el parche (30 min) y decir si lo acepta |
| Sáb 31 oct – lun 2 nov | Reevaluación con 300 semillas y análisis: ¿la red aprende con el parche? | Bucle del Maestro: entrenar en Poisson y evaluar en ABIDES | Si acepta, dejar `mid_decision` encendido por defecto en la 2.2.3 |
| Mar 3 nov | Aplicar la regla de D3 si BF no respondió (sección 6) | Integrar el monitoreo en sus corridas (dos líneas) | Responder D1 y D3 (último día propuesto) |
| Mié 4 – jue 5 nov | Si la red aprende: preparar la revalidación de β y el entrenamiento con tamaños variables (H4). Si no aprende: redactar el resultado negativo y la decisión de 5.000+ episodios | Primeras corridas del Maestro con el Ejecutor corregido | Definir los tres niveles de liquidez (desbloquea las 90 corridas) |
| Vie 6 nov | Sprint Review | Sprint Review | Sprint Review |
| Todo el periodo | Proponer a la profesora guía cómo formular la hipótesis del 10 % (H3): intervalo de confianza pareado o no inferioridad | — | — |

## 6. Cómo cerrar D3 sin esperar más

La evidencia anterior de D3 se midió con la recompensa con falla (H1), así que no sirve para decidir. Los cuadernos nuevos entrenan, con el parche, las dos opciones sobre las **mismas semillas de entrenamiento** (opción 0 y opción A en las semillas 1.000 y 2.000). Así la comparación queda pareada.

**Regla propuesta, fijada antes de ver los resultados:**
1. Se queda la **opción 0** (la fórmula del Título I) salvo que la opción A cumpla las dos condiciones:
   - (a) cumple la orden con argmax (≥ 95 %) en más redes que la opción 0;
   - (b) no cuesta más: el límite superior del IC 95 % de la diferencia A − 0, en las 300 semillas, es menor que +1 bps.
2. Si empatan, se queda la opción 0, porque no obliga a declarar otra desviación del Título I. La penalización por lo no comprado ya cumple el papel que se buscaba con la opción A: evitar la espera.

**Plazo:** BF puede cambiar la regla o decidir otra cosa hasta el **martes 3 de noviembre**. Si no responde, PS la aplica con los resultados y la presenta en la Sprint Review del 6 de noviembre como «regla por defecto aplicada», sin decidir por BF lo que BF quiera revisar después.

## 7. Cómo verificar

```bash
PYTHONPATH=. python -m pytest tests/test_mid_decision.py tests/test_abides_bridge.py -q
```

La prueba de cordura del PPO se repite con `python scripts/prueba_cordura_ppo_ps.py` (≈ 11 minutos en el PC; resultado guardado en `data/analysis/prueba_cordura_ppo.txt`). El análisis de señal y ruido de la sección 2 (H2) sale de los `monitoreo_episodios.csv` de `data/colab_resultados/conf_pen30_g1/` y `v4_pen30_g1_*/`.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
