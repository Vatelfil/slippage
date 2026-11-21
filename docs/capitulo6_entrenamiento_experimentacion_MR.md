# Capítulo 6: Entrenamiento y Experimentación (4.1.2)

**Autor:** Mauricio Reynoso (MR) — Sprint 8 (Tarea 4.1.2, en coordinación con `docs/capitulo7_figuras_tablas_BF.md` y `docs/informe_titulo2_ensamblado_borrador.md`).  
**Figuras generadas:** `data/analysis/cap6_MR/curvas_maestro.png` y `data/analysis/cap6_MR/curvas_ejecutor.png` (`scripts/figuras_entrenamiento_cap6_MR.py`).  
**Nota de coordinación:** Este capítulo documenta el montaje experimental completo, el proceso de entrenamiento, la selección de políticas y la convergencia de ambos niveles del sistema jerárquico. El desempeño comparativo final de las $450$ corridas en el Capítulo 7 remite a las tablas elaboradas en `data/analysis/capitulo7_BF/` y al análisis inferencial del Capítulo 8 (`docs/capitulo8_analisis_PS.md`).

---

## 6.1 Montaje Experimental y Calibración del Entorno

### 6.1.1 Calibración del Simulador `rmsc04` y Escenarios de Profundidad (C-6c)
La evaluación experimental se ejecuta sobre el simulador de microestructura **ABIDES** (`rmsc04`), calibrado por el método de momentos simulados sobre datos intradía del mercado chileno (IPSA: **FALABELLA, COPEC y ECL**, *snapshot* `2026-08-23`).

Para estudiar la sensibilidad del algoritmo ante distintas condiciones de liquidez, se escaló el parámetro de profundidad de cotización del *market maker* (`mm_pov`, Desviación 10) en `data/scenarios/escenarios_liquidez_v3.json`:
- **Profundidad $\times 4$** (`baja` en nombres internos de archivo): mayor volumen cotizado por el *market maker*, lo que en el experimento exploratorio C-6b resultó en un costo de ejecución a mercado de $25{,}05\text{ bps}$ en el control C-6c.
- **Profundidad $\times 1$** (`media`): calibración base ($18{,}36\text{ bps}$ en C-6c).
- **Profundidad $\times 0{,}25$** (`alta`): menor participación del *market maker* ($10{,}81\text{ bps}$ en C-6c).

En la prueba confirmatoria independiente **C-6c** ($60$ semillas nuevas `8101–8160` en FALABELLA apertura, `docs/c6c_confirmacion_v3_BF.md`), el contraste $\times 1 - \times 0{,}25$ excluyó el $0$ ($+7{,}56\text{ bps}$, IC 95 % $[+3{,}07; +14{,}77]$), pero $\times 4 - \times 1$ no lo excluyó ($+6{,}69\text{ bps}$, IC 95 % $[-2{,}59; +13{,}77]$). Por rigor metodológico (Regla 4), los escenarios se informan estrictamente como **profundidad del market maker $\times 4$, $\times 1$ y $\times 0{,}25$**.

### 6.1.2 Conjunto de Meta-Órdenes, Diseño en Estrella y Protocolo Pareado
* **Meta-órdenes (`meta_ordenes_v2_candidata.json`, tarea 2.3.3):** $10$ órdenes institucionales (`MO-01` a `MO-10`) distribuidas entre **FALABELLA, COPEC y ECL** en tres tramos horarios de inicio (**apertura**, **media jornada** y **cierre**). El tamaño base equivale al **$10\%$ del volumen diario simulado** ($5\%$ en órdenes que inician en el cierre, Decisión D1).
* **Semillas disjuntas:** Se evaluaron las semillas `4, 5 y 6` (completamente independientes de las semillas `1, 2 y 3` usadas en la evaluación preliminar del Sprint 6 y de las semillas `5001–5300` de selección de Ejecutores). El total del bloque principal suma **$3\text{ profundidades} \times 10\text{ órdenes} \times 3\text{ semillas} = 90\text{ corridas pareadas por estrategia}$** ($270$ ejecuciones).
* **Eje de tamaño en estrella (Desviación 12):** Para evaluar la sensibilidad al tamaño sin multiplicar el diseño a $810$ corridas, se fijó la profundidad $\times 1$ y se añadieron factores de tamaño **$0{,}5$** ($5\%$ del volumen diario; $2{,}5\%$ al cierre, corrido por BF) y **$1{,}5$** ($15\%$ diario; $7{,}5\%$ al cierre, corrido por MR), sumando $60$ corridas pareadas por estrategia ($180$ ejecuciones adicionales, totalizando **$450$ corridas registradas**).
* **Condiciones de comparabilidad:** El sistema `PPO_sistema` (`seed_red = 1000`, modo `muestreo`, regla `--completar-al-cierre`) y los referentes **TWAP** y **VWAP** (ejecución mediante órdenes a mercado) comparten idénticas semillas de mercado por ventana, *snapshot* e impacto acumulado entre ventanas ($Y = 0{,}5, \tau = 120\text{ min}$).

---

## 6.2 Experimentación y Convergencia de los Agentes Ejecutores

### 6.2.1 Alternativas Probadas y Selección sobre 300 Semillas
Durante la experimentación táctica en ABIDES (`apertura`, FALABELLA, $q_{\text{slice}} = 1.000$ acciones, $T_w = 15\text{ min}$), se compararon cuatro familias de entrenamiento PPO sobre $300$ semillas independientes (`5001–5300`, evaluación estocástica, `docs/reeval_300_imitacion_resultado_PS.md`):

| Alternativa de entrenamiento (Ejecutor) | Episodios | Costo medio en 300 sem. (bps) | Cumplimiento medio | Diferencia vs. TWAP límite [IC 95 %] | Costo computacional estimado (Colab CPU) |
|---|---|---|---|---|---|
| **Imitación `twap_limit_medio` + PPO (`s1000`, elegido)** | 100 imit. + 1.000 PPO | **5,68** | **1,000** | $+1{,}03\text{ [+0,11; +1,88]}$ | $\approx 57\text{ min}$ ($3.437{,}5\text{ s}$) |
| Imitación `twap_limit_medio` + PPO (`s2000`) | 100 imit. + 1.000 PPO | 5,98 | 1,000 | $+1{,}32\text{ [+0,56; +2,09]}$ | $\approx 57\text{ min}$ |
| Solo imitación (`s2000`, sin PPO; descartada) | 100 imit. | 5,13 | 0,984 | $+0{,}47\text{ [-0,23; +1,17]}$ | $\approx 5\text{ min}$ |
| Mejor red PPO pura anterior (`V2 s3000`) | 1.000 PPO | 6,50 | 1,000 | $+1{,}85\text{ [-0,21; +3,80]}$ | $\approx 55\text{ min}$ |
| Recompensa corregida sin imitación (6 redes) | 1.000 PPO | 7,09 – 9,48 | 1,000 | $+2{,}4\text{ a }+4{,}8$ | $\approx 55\text{ min c/u}$ |
| *Referencia:* TWAP con órdenes límite | — | 4,65 | 0,989 | — | $< 1\text{ min}$ |

* **Justificación de la selección:** La inicialización mediante clonación de comportamiento sobre `twap_limit_medio` ($100$ episodios, $3.000$ pares estado-acción, exactitud del **$92{,}97\%$**) seguida de ajuste fino con PPO ($\text{lr} = 10^{-4}$, $\text{clip} = 0{,}2$, $\gamma_E = 1{,}0$, $\beta = 0{,}0061796$) obtuvo el menor slippage entre las redes PPO válidas ($5{,}68\text{ bps}$, $-1{,}30\text{ bps}$ respecto a su control sin entrenar, $p = 0{,}095$) garantizando $100\%$ de cumplimiento. La variante `solo imitación` fue descartada por no incorporar optimización RL y por presentar menor cumplimiento ($98{,}4\%$).

### 6.2.2 Convergencia del Ejecutor Elegido (`rimit/d3_opcion0_s1000`)
En la Figura `data/analysis/cap6_MR/curvas_ejecutor.png` se observa la trayectoria de aprendizaje durante los $1.000$ episodios de ajuste PPO en ABIDES:
- **Estabilidad de actualizaciones:** La divergencia KL aproximada se mantuvo estrictamente acotada ($\text{KL}_{\max} = 0{,}0095$), evidenciando pasos de gradiente suaves sin colapso de política.
- **Evolución de entropía y cumplimiento:** La entropía decreció de $1{,}242$ a $0{,}667$, mientras el cumplimiento en monitoreo pasó de $99{,}51\%$ en los primeros $50$ episodios a **$100{,}0\%$** en los últimos $50$.
- **Composición táctica aprendida:** En el tramo final del entrenamiento (últimos $50$ episodios), el Ejecutor estabilizó una mezcla dominada por **$93{,}7\%$ de órdenes límite de compra**, **$2{,}1\%$ de órdenes a mercado** y **$4{,}2\%$ de espera (`HOLD`)**, explicando su capacidad para capturar el spread frente a benchmarks agresivos a mercado.

---

## 6.3 Entrenamiento y Convergencia del Agente Maestro

Con los pesos del Ejecutor congelados y replicados en los tres tramos (`ejecutor_apertura.pt`, `ejecutor_media_jornada.pt`, `ejecutor_cierre.pt`), se entrenó el Agente Maestro en el simulador estocástico **Poisson** durante **$2.000$ jornadas completas** (`Q_total = 88.300` acciones de FALABELLA, $\lambda = 0{,}02$, $\gamma_M = 0{,}99$, $\text{lr} = 3\times 10^{-4}$).

### 6.3.1 Convergencia del Maestro Oficial (`sistema_final`) vs. Maestro v2
La Figura `data/analysis/cap6_MR/curvas_maestro.png` contrasta las curvas de entrenamiento del Maestro oficial del Sprint 6 y de la variante exploratoria Maestro v2 (Desviación 13):

| Métrica de entrenamiento / validación (30 sem. `90001–90030`) | Maestro oficial (Sprint 6) | Maestro v2 (`sm_mercado`) |
|---|---|---|
| **Pérdida del crítico (`loss_critic`, ep. $10 \to 2000$)** | $2.634{,}23 \to 1{,}31$ | $1.863{,}23 \to 3{,}85$ |
| **Entropía final $\mathcal{H}(\pi_M)$ (ep. $10 \to 2000$)** | $3{,}686 \to \mathbf{0{,}205}$ | $3{,}686 \to \mathbf{0{,}849}$ |
| **KL máxima por actualización** | $0{,}0194$ | $0{,}0129$ |
| **Recompensa $R_M$ (sin entrenar $\to$ entrenado)** | $-72{,}09 \to -30{,}67\text{ bps}$ ($+41{,}42$ IC $[+29{,}83; +54{,}61]$) | $-55{,}10 \to -27{,}50\text{ bps}$ ($+27{,}60$ IC $[+17{,}1; +39{,}8]$) |
| **Cumplimiento en validación (sin entrenar $\to$ entrenado)** | $73{,}25\% \to 97{,}57\%$ | $83{,}00\% \to 99{,}60\%$ |
| **Política dominante observada** | $\alpha = 0{,}50,\; T_w = 15\text{ min}$ ($96\text{–}98\%$) | $\alpha = 0{,}40$ ($74\%$) y $\alpha = 0{,}20$ ($20\%$) |

* **Diagnóstico del colapso de entropía en el Maestro oficial:** La caída de la entropía hasta $0{,}205$ refleja que el Maestro oficial convergió a una política casi determinística ($\alpha = 0{,}50$, ventana de $15\text{ min}$). Como muestra la experimentación complementaria sobre Poisson por tercios de volumen diario (`feature/bf-poisson-tercios`, $1.500$ corridas), $\alpha = 0{,}50$ es efectivamente la regla fija que minimiza el costo garantizando el cumplimiento bajo la restricción de no exceder $50\%$ por ventana. Al incorporar variables dinámicas del mercado simulado y la regla de cierre durante el entrenamiento (Maestro v2), la entropía se estabilizó en un nivel superior ($0{,}849$), diversificando las asignaciones sin alterar estadísticamente el costo final en ABIDES ($-0{,}85\text{ bps}$ vs. Maestro oficial, Wilcoxon $p = 0{,}855$).

---

## 6.4 Presupuesto y Costo Computacional Total en la Nube

Toda la experimentación pesada se ejecutó en entornos CPU de **Google Colab** (Python 3.9 vía `condacolab`, sin GPU aceleradora dado que ABIDES es un simulador discreto secuencial en CPU):

| Etapa experimental | Cantidad de corridas / episodios | Duración aproximada en Colab | Justificación operativa |
|---|---|---|---|
| Selección y entrenamiento de Ejecutores (`d3_*`, `t5_*`, `rimit`) | $> 12$ corridas de $1.000$ ep. + $300$ sem. de reevaluación | $\approx 15\text{ h}$ acumuladas | Permite comparar 4 formulaciones de recompensa e imitación |
| Entrenamiento del Agente Maestro (`sistema_final` y `v2`) | $2.000$ jornadas en Poisson c/u | $\approx 40\text{ min}$ por modelo ($\approx 13{,}3\text{ min}$ último bloque) | Entrenar en ABIDES requeriría $> 100\text{ h}$ por modelo |
| Evaluación 3.2.1 — 90 corridas ($\times 4, \times 1, \times 0{,}25$) | $270$ simulaciones ABIDES ($6$ cuadernos A/B) | $\approx 18\text{ h}$ totales ($3\text{ h}$ en paralelo por par) | Simulaciones completas de jornada bursátil pareadas |
| Eje de tamaño 3.2.4 ($0{,}5$ y $1{,}5$ en $\times 1$) | $180$ simulaciones ABIDES ($4$ cuadernos A/B) | $\approx 12\text{ h}$ totales ($3\text{ h}$ en paralelo por par) | Completa el diseño en estrella sin explosión combinatoria ($810$ corridas) |
| Control de reglas y Maestro v2 | $90$ simulaciones ABIDES | $\approx 6\text{ h}$ | Ablación de niveles Maestro vs. Ejecutores |

---

## 6.5 Figuras del Capítulo

1. `data/analysis/cap6_MR/curvas_ejecutor.png`: Recompensa media, pérdida del crítico, KL/entropía y composición porcentual de acciones del Ejecutor elegido (`s1000`, $1.000$ episodios).
2. `data/analysis/cap6_MR/curvas_maestro.png`: Evolución de $R_M$, pérdida del crítico (escala logarítmica), entropía y divergencia KL del Maestro oficial frente al Maestro v2 ($2.000$ episodios en Poisson).
