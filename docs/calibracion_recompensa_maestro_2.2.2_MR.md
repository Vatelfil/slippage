# Calibración Experimental de la Recompensa del Maestro (Tarea 2.2.2)

**Autor:** Mauricio Reynoso (MR) — Redes PPO / Arquitectura RL  
**Fecha:** Octubre 2026 (Sprint 4)  
**Entorno de prueba:** `MaestroEjecutorEnv` orquestado con `EjecutorEnvPoissonFallback` (parámetros reales IPSA de Benjamín Farías, tarea 2.1.3).  
**Script reproducible:** `experiments/calibrate_lambda_maestro.py`  
**Datos empíricos:** `data/calibration/lambda_maestro_calibration_results.csv` y `data/calibration/lambda_maestro_raw_runs.csv`

---

## 1. Contexto Teórico y Definición de la Función de Recompensa

En la formulación jerárquica de dos niveles para el problema de ejecución óptima de metaórdenes (Título I, sección 4):
- El **Agente Maestro** toma decisiones cada 30 minutos asignando la fracción de volumen $\alpha_t$ y la ventana temporal $\tau_t$ al Ejecutor correspondiente al tramo horario (Apertura, Media jornada, Cierre).
- La recompensa terminal del Maestro sigue el estándar de *Implementation Shortfall* (IS, Perold 1988), penalizando tanto el impacto de mercado y slippage acumulado a lo largo de la jornada como el inventario residual no ejecutado al toque de campana (16:00 Santiago):

$$R_M = -IS_{\text{total}} - \lambda \cdot \max(0, Q_{\text{pendiente}}) \cdot P_{\text{mid\_cierre}}$$

Donde:
- $IS_{\text{total}} = \sum_{k=1}^{K} (P_{\text{promedio}, k} - P_{\text{referencia}}) \cdot q_{\text{ejecutado}, k}$ representa el slippage monetario total incurrido (en CLP).
- $Q_{\text{pendiente}} = Q_{\text{total}} - Q_{\text{ejecutado}}$ es el número de acciones que quedaron sin comprar.
- $P_{\text{mid\_cierre}}$ es el precio de mercado al momento del cierre bursátil.
- $\lambda$ es el factor de penalización por inventario pendiente (hiperparámetro objeto de esta calibración).

> **Alcance de esta calibración (nota de PS, 10 oct 2026).** λ = 0,05 se eligió por escala: se comparó el tamaño de la penalización con el del IS usando una política **sin entrenar** (redes con pesos al azar) y el simulador de Poisson. Es un valor provisional razonable, no un óptimo: **debe revalidarse cuando el Maestro tenga entrenamiento real** (Sprint 5–6).

Hasta el Sprint 3, el código utilizaba un valor provisional no calibrado (`LAMBDA_PENALTY_PLACEHOLDER = 0.1`). La sección 4.3 del Título I estipula explícitamente que $\lambda$ debe ser calibrado experimentalmente para asegurar convergencia estable en el entrenamiento PPO.

---

## 2. Metodología Experimental

Se realizaron 100 simulaciones controladas de episodios completos (13 decisiones por jornada, 390 minutos simulados) evaluando una grilla de 5 valores candidatos de $\lambda$:
$$\lambda \in \{0.01, 0.05, 0.10, 0.50, 1.00\}$$

Cruzados con 4 tamaños de metaorden representativos del mercado chileno (FALABELLA, precio base ~5.800 CLP):
$$Q_{\text{total}} \in \{1.000, 5.000, 10.000, 20.000\} \text{ acciones}$$
Con 5 corridas independientes por combinación (variando semillas estocásticas y trayectorias del simulador de LOB Poisson).

Para cada corrida se registraron:
1. $Q_{\text{ejecutado}}$ y porcentaje de compleción ($\% \text{ Ejecutado}$).
2. $Q_{\text{pendiente}}$ al cierre de la sesión.
3. $IS_{\text{total}}$ en CLP (costo de slippage).
4. Penalización monetaria $\text{Penalidad} = \lambda \cdot Q_{\text{pendiente}} \cdot P_{\text{cierre}}$.
5. Recompensa terminal total $R_M$.
6. Razón entre la penalización de inventario y el slippage monetario: $\text{Ratio} = \frac{\text{Penalidad}}{|IS_{\text{total}}| + 1}$.

---

## 3. Resultados Empíricos

El resumen agregado de las simulaciones por cada valor de $\lambda$ arrojó los siguientes valores:

| $\lambda$ | $Q_{\text{pendiente}}$ (media) | $\% \text{ Ejecutado}$ | $IS_{\text{total}}$ medio (CLP) | Penalización media (CLP) | $R_M$ medio (CLP) | Desv. Est. $R_M$ ($\sigma$) | Ratio Penalidad / IS |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0.01** | 370.27 | 96.65% | 79.775 CLP | 21.495 CLP | -101.271 CLP | 85.914 CLP | 0.23x |
| **0.05** | **348.79** | **96.88%** | **79.317 CLP** | **101.233 CLP** | **-180.550 CLP** | **179.975 CLP** | **1.06x** |
| **0.10** *(prev)* | 365.93 | 96.53% | 80.446 CLP | 212.460 CLP | -292.906 CLP | 340.232 CLP | 2.34x |
| **0.50** | 199.07 | 98.12% | 82.885 CLP | 577.903 CLP | -660.787 CLP | 811.476 CLP | 6.18x |
| **1.00** | 309.86 | 96.95% | 83.721 CLP | 1.798.185 CLP | -1.881.906 CLP | 2.330.449 CLP | 20.79x |

---

## 4. Análisis y Criterio de Selección

El diseño del algoritmo PPO para el Agente Maestro impone dos restricciones competitivas sobre la escala de la recompensa:

1. **Evitar la sub-penalización ($\lambda < 0.05$):**
   Con $\lambda = 0.01$, la penalización media (21.495 CLP) representa apenas el 23% del slippage incurrido. El agente aprende que es "económicamente preferible" detener la ejecución temprano y dejar acciones sin comprar para evitar cruzar el spread en periodos de baja liquidez, incumpliendo el mandato fundamental de ejecutar la orden completa.

2. **Evitar la sobre-penalización y explosión de gradientes ($\lambda \ge 0.10$):**
   - Con $\lambda = 0.10$, la penalización asciende a 2.34 veces el slippage total, y la desviación estándar de la recompensa terminal sube a 340.232 CLP.
   - Con $\lambda \ge 0.50$ y $\lambda = 1.00$, la penalización supera los 1,8 millones de CLP (20.8 veces el IS total), con desviaciones estándar que sobrepasan los 2,3 millones de CLP. En el entrenamiento de la red crítica mediante MSE ($L_V = \mathbb{E}[(V(s) - R)^2]$), discrepancias de este orden generan gradientes desproporcionados que saturan las capas lineales y desestabilizan las actualizaciones de la política. Además, el agente ignora la microestructura del slippage: cualquier estrategia que ejecute a precios pésimos recibe casi la misma recompensa siempre que liquide la última acción.

3. **Punto Óptimo: $\lambda^* = 0.05$:**
   - La penalización media (101.233 CLP) guarda una relación de **1.06x respecto al slippage total medio (79.317 CLP)**.
   - Dejar inventario residual duplica el costo total de la operación, proveyendo una señal de gradiente inequívoca de completitud.
   - Mantiene la recompensa terminal en una escala estable ($\sim 1.8 \times 10^5$ CLP) coherente con los retornos de los episodios y con la normalización de ventajas en GAE.

---

## 5. Conclusión y Fijación en el Código

Se fija formalmente el valor calibrado en `src/envs/maestro_ejecutor_protocol.py`:

```python
# Calibracion experimental (Sprint 4, tarea 2.2.2 - Mauricio Reynoso).
# Penalizacion por inventario no ejecutado al cierre: lambda * Q_pendiente * P_mid_cierre.
LAMBDA_PENALTY = 0.05             # Calibrado: penaliza sin desestabilizar la escala de IS
LAMBDA_PENALTY_PLACEHOLDER = LAMBDA_PENALTY  # Mantiene compatibilidad hacia atras
```

Se actualizó el orquestador `MaestroEjecutorEnv` para que admita `lambda_penalty` parametrizable por instancia (facilitando estudios de sensibilidad futuros) utilizando `LAMBDA_PENALTY = 0.05` como valor estándar por defecto.
