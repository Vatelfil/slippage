# Registro Oficial de Desviaciones: Título I vs. Implementación

**Documento elaborado por:** Mauricio Reynoso (MR), con aportes de Benjamín Farías (BF) y Paolo Sepúlveda (PS).  
**Última actualización:** Sprint 5 (Octubre 2026).  
**Propósito:** Registrar de manera explícita, auditable y fundamentada cualquier discrepancia entre las especificaciones iniciales del Título I y la implementación real del código en el repositorio `slippage`.

---

## 1. Discrepancia en el Corte de Tramos Intradía: 11:00 ($S_M$) frente a 11:30 (Ejecutores) [P9 / D5]

### 1.1 Descripción de la Discrepancia
Existe una diferencia en la delimitación horaria entre el tramo de "Apertura" y "Media jornada":
- **En el vector de estado del Maestro ($S_M$):** La variable `sesion` (índice 6 de $S_M \in \mathbb{R}^7$, implementada en `src/features/build_sm_features.py` y registrada en `docs/schemas/SM_schema.json`) utiliza los siguientes intervalos basados en la hora entera:
  - Apertura: `[09:30, 11:00)` $\to$ `sesion = 0.0`
  - Media jornada: `[11:00, 14:00)` $\to$ `sesion = 0.5`
  - Cierre: `[14:00, 16:00]` $\to$ `sesion = 1.0`
- **En los Agentes Ejecutores y Calibración:** Los contratos de tramos tácticos (`TRAMOS_EJECUTOR` en `src/config/market_params.py`, calibración RMSC04 en `src/analysis/intraday_profile.py` y `docs/schemas/SE_schema.json`) definen:
  - Apertura: `09:30 - 11:30` (120 minutos, 24 velas de 5 min)
  - Media jornada: `11:30 - 14:00` (150 minutos, 30 velas de 5 min)
  - Cierre: `14:00 - 16:00` (120 minutos, 24 velas de 5 min)

### 1.2 Impacto Práctico
En la media hora comprendida entre las **11:00 y las 11:30**, el Agente Maestro observa en su vector $S_M$ que la jornada ha entrado en régimen de media jornada (`sesion = 0.5`), pero el mensaje `ASIGNAR` se despacha al Ejecutor de `apertura`, quien continúa operando bajo las condiciones de microestructura de apertura.

### 1.3 Decisión Adoptada (Decisión D5 - Opción A)
**Se ratifica la Opción A: Mantener ambos cortes y documentar formalmente la discrepancia.**

**Justificación técnica:**
1. Modificar $S_M$ para cortar a las 11:30 requeriría re-ejecutar el pipeline completo de ingeniería de variables de datos históricos (tarea 1.2.2), regenerar los DataFrames procesados en `data/processed/sm_features_*`, recalcular las matrices de correlación y los escaladores, e invalidar los esquemas congelados en el Sprint 1.
2. Desde la perspectiva de aprendizaje por refuerzo, que el Maestro observe un valor continuo o intermedio en la variable temporal previa a la transición no perjudica la convergencia de la política estratégica, pues $S_M$ cuenta con la variable $\tau_t$ (minutos transcurridos normalizados) que provee una señal temporal continua y suave.
3. Se acuerda mantener esta configuración durante los Sprints 5 y 6. La unificación estricta de ambos relojes a las 11:30 queda catalogada como una mejora estética opcional sujeta a disponibilidad de tiempo previo a la entrega final.

---

## 2. Cabeza de Política del Ejecutor: Categórica Discreta vs. Híbrida [2.1.2]

### 2.1 Descripción
El documento del Título I mencionaba conceptualmente una cabeza de política híbrida: discreta para el tipo de orden y continua (e.g. Gaussiana) para la fracción de volumen o precio.

### 2.2 Implementación
En `src/models/actor_critic.py` (`ExecutorActorCritic`) y `src/models/networks_factory.py`, la política táctica se implementa de manera **totalmente discreta** mediante una única cabeza lineal que proyecta la última capa oculta (256 neuronas) a 240 logits correspondientes a las combinaciones posibles de:
$$\text{Acciones} = 3 \text{ (tipo de orden)} \times 10 \text{ (niveles de volumen)} \times 8 \text{ (offsets de precio)} = 240$$

### 2.3 Justificación
1. **Compatibilidad:** El entorno Gym del Ejecutor expone `MultiDiscrete([3, 10, 8])` decodificado por `EjecutorActionSpace.decode_flat()`.
2. **Estabilidad PPO:** Distribuciones híbridas (categórica + continua) exigen balancear coeficientes de entropía heterogéneos y suelen sufrir colapso de varianza o gradientes nulos en las fronteras de volumen $[0, 1]$.
3. **Costo:** 240 logits conllevan solo $\approx 61{,}6\text{k}$ parámetros adicionales, resultando computacionalmente rápido y estable.

---

## 3. Calibración de la Penalización $\lambda$ del Maestro [2.2.2 / P10]

### 3.1 Descripción
La función de recompensa terminal del Maestro sigue la formulación de Implementation Shortfall (IS):
$$R_M = -IS_{\text{total}} - \lambda \cdot \max(0, Q_{\text{pendiente}}) \cdot P_{\text{mid\_cierre}}$$

### 3.2 Estado de Calibración
El valor $\lambda = 0{,}05$ fue calibrado experimentalmente en el Sprint 4 mediante una **calibración por balance de escala** utilizando políticas sin entrenar sobre el simulador Poisson. Este valor es **provisional** y referencial para asegurar que la penalización por inventario residual tenga un ratio $\approx 1{,}06\times$ respecto al slippage sin causar explosiones de gradiente en la función crítica.

### 3.3 Plan de Revalidación (P10)
Conforme a la ficha P10, una vez completado el primer entrenamiento real del Maestro en el Sprint 5/6 (tarea 2.3.5), se repetirá el análisis con la política entrenada para confirmar o ajustar el valor óptimo definitivo de $\lambda$.

---

## 4. Función de Recompensa del Ejecutor $R_E$ y Aversión al Riesgo $\beta$ [2.2.3 / D3]

### 4.1 Descripción
La recompensa por paso del Ejecutor en el Título I se define como:
$$R_E = (P_{\text{mid}} - P_{\text{ejec}}) \cdot q - \beta \cdot \sigma^2 \cdot q$$

### 4.2 Desviación y Diagnóstico
En la fase 2 de calibración de $\beta$ se observó que multiplicar el término de penalización de riesgo por la cantidad ejecutada $q$ genera el incentivo perverso de **no operar** ($q = 0 \implies R_E = 0$).

### 4.3 Tratamiento en Sprint 5
Se fijó $\beta = 0{,}1 \times \beta^*$ como valor provisional operativo seguro (cumplimiento del 100%), mientras se adopta la Decisión D3 sobre evaluar el riesgo respecto al inventario pendiente o mantener la regla de vigilancia en el entrenamiento formal.


---

## 5. Unidad de Cuenta en ABIDES frente al Protocolo CTDE [2.3.1 / Decisión de Unidades]

### 5.1 Descripción
El simulador ABIDES calibrado para el mercado chileno (tarea 2.2.4) opera internamente en **décimos de CLP** (`unidad_cuenta = "decimos"`, donde 1 CLP = 10 unidades de simulación) para aproximar el tick size mínimo, mientras que el Título I, el simulador Poisson y las recompensas del Maestro ($IS_{\text{total}}$ y $R_M$) están formuladas en **CLP**.

### 5.2 Decisión y Solución Adoptada (MR, 21 oct 2026)
Se acordó no alterar los esquemas JSON ni crear una nueva abstracción redundante, adoptando la solución canónica ya provista por `BridgeConfig.unidades_por_clp`:
- El orquestador `MaestroEjecutorEnv` convierte automáticamente los precios de entrada (`entry_price`) y precios de ejecución de ABIDES a CLP dividiendo por `unidades_por_clp` (10 en la calibración oficial).
- Como resultado, el mensaje `REPORTE`, el slippage acumulado, el $IS_{\text{total}}$ y la recompensa $R_M$ del Maestro se computan y registran estrictamente en **CLP**, manteniendo intacta la escala de calibración de $\lambda = 0{,}05$.

---

## 6. Factor de descuento del Ejecutor: γ_E = 1 en vez de 0,95 [PROPUESTA de PS para MR, 29 oct 2026]

### 6.1 Descripción
El Título I fija γ_E = 0,95. Con ese valor, un costo al final de una ventana de 30 pasos se ve desde el inicio multiplicado por 0,95²⁹ ≈ 0,23, y la red aprende a esperar (97 % a 99 % de los pasos en Poisson; `docs/diagnostico_recompensa_PS.md`).

### 6.2 Propuesta
γ_E = 1 junto con la penalización por lo no comprado al cerrar la ventana. Con las dos cosas, en Poisson 5 de 5 redes completan la orden y llegan al costo de la mejor heurística; cada cambio por separado no sirve (`docs/investigacion_recompensa_que_se_hizo.md`). En ABIDES completan la orden; el efecto sobre el costo se está midiendo con la recompensa corregida (`docs/revision_opus_PS.md`). Se aplica con `GAMMA_EJECUTOR` en `src/training/ppo_trainer.py` (rama `feature/ps-borrador-mr-maestro`). **Estado: pendiente de que MR la acepte.**

---

## 7. Impacto acumulado entre ventanas del Maestro [PROPUESTA de PS para MR, 29 oct 2026]

### 7.1 Descripción
`MaestroEjecutorEnv` crea un mercado nuevo e independiente para cada ventana, y en ABIDES todas las ventanas de un tramo empiezan a la misma hora simulada. Lo comprado en una ventana no afecta el precio de las siguientes, así que el Maestro no tiene un dilema de coordinación (el Título I lo presenta como el que reparte la orden para no mover el precio).

### 7.2 Propuesta
Arrastrar el impacto con la ley de la raíz cuadrada y decaimiento exponencial (`src/envs/impacto_acumulado.py`): impacto = Y · σ_día · √(Q_efectiva / V_día), con Y = 0,5 y τ = 120 min como **supuestos de la literatura, no calibrados**. Se aplica igual al sistema y a TWAP/VWAP (`--impacto` en los dos evaluadores), así que la comparación sigue siendo pareada. Hay que declararlo en el informe como supuesto del modelo y, si alcanza el tiempo, contrastar Y con dos ventanas seguidas en ABIDES. **Estado: pendiente de que MR la acepte.**

---

## 8. Un mismo Ejecutor entrenado para los tres tramos en la evaluación del Sprint 6 [PS, 29 oct 2026]

### 8.1 Descripción
El Título I prevé un Ejecutor por tramo (apertura, media jornada y cierre). Todos los Ejecutores entrenados hasta ahora son de apertura, porque entrenar en ABIDES los tramos posteriores es mucho más lento: cada episodio simula desde las 09:30.

### 8.2 Tratamiento
En el sistema final del Sprint 6 (`notebooks/Colab_sistema_final.ipynb`) la misma red de apertura, elegida con la regla de `scripts/elegir_ejecutor_ps.py`, se usa en los tres tramos. Las tres siguen siendo instancias separadas del mismo tipo de red PPO. Entrenar redes propias para media jornada y cierre queda para el Sprint 7 si alcanza el tiempo.

---

## 9. Arranque por imitación del Ejecutor (método de entrenamiento, no cambia la arquitectura) [PS, 29 oct 2026]

El Ejecutor PPO puede partir copiando a TWAP con órdenes límite (`--imitar twap_limit_medio`) y después se ajusta con PPO. Se mantienen la red, el espacio de acción y la recompensa del Título I; solo cambia el punto de partida de los pesos. Se declara en la metodología porque, si esa red resulta elegida, su desempeño depende de esa inicialización.

---

## 10. Escenarios de liquidez definidos por el costo medido (v3) [PROPUESTA de PS para BF, 30 oct 2026]

El Título I pide evaluar en escenarios de liquidez baja, media y alta. En ABIDES se usa el tamaño de las cotizaciones del market maker (`mm_pov`) para generarlos. En el C-6b, subir `mm_pov` **encareció** la compra a mercado (`docs/c6_liquidez_resultado_PS.md`, sección 4). La v3 asigna los nombres según ese costo: baja = ×4, alta = ×0,25. El orden se eligió mirando el resultado, así que se declara y se confirma con las semillas de las 90 corridas del Sprint 7. **Estado: pendiente de que BF la acepte.**

---

## 11. Barrido final en la última decisión del Maestro [PS, 31 oct 2026]

El Título I define la acción del Maestro como la fracción α ∈ [0,05; 0,50] de lo que falta. Con esa acción, una orden que empieza a las 14:00 (4 decisiones) no puede pasar del 93,75 %. Se agrega la opción `completar_al_cierre`: en la última decisión del día, α = 1. Las demás decisiones siguen la acción del Título I. Se usa en la versión corregida de las 30 corridas (`docs/correccion_cierre_PS.md`). **Estado:** aplicada por PS; el Maestro (de MR) no se modifica.
