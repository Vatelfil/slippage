# Plan Detallado - Sprint 4: Training PPO (PS)

**Período:** 28 septiembre - 9 octubre 2026  
**Responsable:** Paolo Sepúlveda (PS)  
**Estado:** Ready to start (con dependencias de Mauricio/Benjamín)

---

## 🎯 Objetivo General

Implementar el loop de training PPO completo para el sistema multi-agente (Maestro + 3 Ejecutores), validar convergencia, y generar análisis de desempeño contra el mercado IPSA.

---

## 📋 Tareas

### **Tarea 3.1.1: Training Loop PPO Completo** (24 horas)

**Entrada:**
- Redes Actor-Critic de Mauricio (2.1.1/2.1.2) → `src/models/actor_critic.py`
- Espacios Gymnasium de PS (2.1.4) → `src/envs/spaces.py` ✅
- Parámetros Poisson (2.1.3) → `data/poisson_params_calibrated.json` ✅
- Skeleton de Colab → `notebooks/Training_PPO_Sprint4_PS.ipynb`

**Qué implementar:**

1. **Rollout completo** (recolecci ón de experiencias)
   ```python
   # Para cada episodio:
   # 1. Reset Maestro + 3 Ejecutores
   # 2. Maestro decide alpha_t ∈ [0,1]
   # 3. Cada Ejecutor toma acción (order_type, volume, price_level)
   # 4. ABIDES simula mercado, retorna nuevas observaciones + rewards
   # 5. Guardar (obs, action, reward, value, done) en buffer
   ```

2. **Compute Advantages (GAE)**
   ```python
   # Generalized Advantage Estimation
   # gae_t = delta_t + gamma * lambda * gae_{t+1}
   # advantage = gae
   # return = gae + value_t
   ```

3. **PPO Loss**
   ```python
   # Policy loss (clipped):
   # L^CLIP = -E[min(r_t * A_t, clip(r_t, 1±ε) * A_t)]
   #
   # Value loss:
   # L^V = E[(V(s) - R)^2]
   #
   # Entropy regularization:
   # L^ENT = -β * E[entropy(π)]
   #
   # Total: L = L^CLIP + c1 * L^V + c2 * L^ENT
   ```

4. **Update Loop**
   ```python
   # For each epoch_per_update:
   #   For each minibatch:
   #     Compute loss, backward, optimizer.step()
   ```

**Deliverable:**
- Training loop funcionando end-to-end
- Logs de loss/returns/entropy cada N steps
- Checkpoints cada `checkpoint_interval`

**Horas:** 24

---

### **Tarea 3.1.2: Validación Episodios Maestro** (16 horas)

**Entrada:**
- Training loop funcionando (3.1.1)
- Episodios de training recolectados

**Qué validar:**

1. **Convergencia de política Maestro**
   ```
   Métrica: return_maestro ↗ (debe crecer)
   Threshold: mean_return > initial_return después de 100k timesteps
   ```

2. **Distribución de alpha_t**
   ```
   Gráfico: histograma de acciones Maestro por step
   Expectativa: diversidad en primeros steps, concentración después (convergencia)
   ```

3. **Value function accuracy**
   ```
   Métrica: correlation(V(s), actual_return)
   Threshold: r² > 0.7
   ```

**Horas:** 16

---

### **Tarea 3.1.3: Validación Episodios Ejecutores** (16 horas)

**Entrada:**
- Training loop funcionando (3.1.1)
- Episodios de los 3 Ejecutores

**Qué validar:**

1. **Convergencia por Ejecutor**
   ```
   Métrica: return_ejecutor_i para i ∈ {Apertura, Media, Cierre}
   Expectativa: cada uno converge independientemente (paralelismo)
   ```

2. **Distribución de acciones (order_type, volume, price_level)**
   ```
   Gráfico: 3 heatmaps (uno por Ejecutor)
   Fila: step del episodio (0-30)
   Columna: acción (0-239, porque 3×10×8=240)
   Color: frecuencia
   Expectativa: convergencia a estrategia clara
   ```

3. **Slippage por Ejecutor**
   ```
   Métrica: Implementation Shortfall = (P_mid - P_execution) * qty
   Expectativa: IS disminuye con training (mejor ejecución)
   ```

**Horas:** 16

---

### **Tarea 3.1.4: Logging y Checkpoints** (12 horas)

**Entrada:**
- Training loop con métricas (3.1.1)

**Qué implementar:**

1. **TensorBoard logging** (recomendado para Colab)
   ```python
   from torch.utils.tensorboard import SummaryWriter
   writer.add_scalar('maestro/return', R, global_step)
   writer.add_scalar('maestro/loss/policy', L_clip, global_step)
   writer.add_scalar('maestro/loss/value', L_v, global_step)
   writer.add_scalar('maestro/entropy', H, global_step)
   # Idem para ejecutores
   ```

2. **Checkpointing**
   ```python
   # Cada checkpoint_interval (100k timesteps):
   # - Guardar pesos de todas las redes
   # - Guardar optimizer states
   # - Guardar train_stats (para resumir training)
   # - Guardar config (para reproducibilidad)
   ```

3. **CSV logging** (para análisis posterior)
   ```
   timestep, maestro_return, maestro_loss, ejecutor0_return, ejecutor1_return, ...
   ```

**Horas:** 12

---

### **Tarea 3.1.5: Análisis de Convergencia** (16 horas)

**Entrada:**
- Logs y checkpoints completos (3.1.4)
- Validaciones de 3.1.2/3.1.3

**Qué analizar:**

1. **Curvas de convergencia**
   ```python
   # Gráficos:
   # 1. Returns (Maestro + 3 Ejecutores) vs timesteps
   # 2. Losses (policy, value, entropy) vs timesteps
   # 3. Entropy vs timesteps (debe decrecer → convergencia)
   # 4. Learning rate schedule (si existe)
   ```

2. **Estabilidad**
   ```
   Métrica: std(returns) en ventana [t-5k:t]
   Expectativa: std decrece con training (más estable)
   ```

3. **Generalization**
   ```python
   # Evaluar en:
   # - Datos de training (memorization check)
   # - Datos nuevos (validation set, si existe)
   # - Cambios de mercado (stress test: volatilidad ↑, spread ↑)
   ```

4. **Comparación vs baseline**
   ```
   # Si tenemos baseline (ej: política aleatoria, greedy, etc):
   # Maestro_return / Baseline_return = improvement factor
   ```

5. **Interpretabilidad**
   ```python
   # Para Maestro:
   # - ¿Cuándo decide split alto (α=0.8)?
   # - Correlación con mercado (volatilidad, spread)?
   #
   # Para Ejecutores:
   # - ¿Qué orden_type preferido por fase (Apertura/Media/Cierre)?
   # - ¿Nivel de precio vs spread?
   ```

**Deliverables:**
- Reporte con 5+ gráficos
- JSON con métricas finales
- Recomendaciones para Sprint 5 (ajuste fino)

**Horas:** 16

---

## 📊 Dependencias (BLOQUEADORES)

| Tarea | Bloqueador | Status | ETA |
|-------|-----------|--------|-----|
| 3.1.1 | Redes de Mauricio (2.1.1/2.1.2) | ⏳ EN PROGRESO | Lunes 28 |
| 3.1.1 | ABIDES integration (de Benjamín) | ⏳ EN PROGRESO | Miércoles 30 |
| 3.1.1 | Datos Poisson reales (de Benjamín) | ⏳ OPCIONAL | Viernes 2 |

**Plan B (si bloqueadores no llegan):**
- Usar redes "dummy" (random initialization)
- Usar Ejecutores sin ABIDES (env stubs)
- Usar datos Poisson sintéticos
- Resultado: prueba de concepto, no producción

---

## 🗓️ Cronograma

### **Lunes 28 - Martes 29 (Tarea 3.1.1)**
```
09:00 - Sprint 4 kickoff
        Integrar redes de Mauricio
        Integrar ABIDES
        
14:00 - Training loop PPO en Colab
        Primeros 100k timesteps
        Debug if needed
        
Fin de día: Training loop funcionando
```

### **Miércoles 30 - Jueves 1 (Tareas 3.1.2 y 3.1.3)**
```
Continuación de training (~500k timesteps)
Validación incremental:
- Gráficos de returns cada 50k timesteps
- Check convergencia
```

### **Viernes 2 - Sábado 3 (Tarea 3.1.4)**
```
Logging completo en TensorBoard
Checkpointing cada 100k timesteps
CSV export
```

### **Domingo 4 - Lunes 5 (Tarea 3.1.5)**
```
Análisis final (convergence curves, stability, generalization)
Reporte de métricas
```

---

## 📝 Checklist de Deliverables

- [ ] Training loop PPO funcionando (3.1.1)
- [ ] Gráficos de convergencia Maestro (3.1.2)
- [ ] Gráficos de convergencia Ejecutores (3.1.3)
- [ ] TensorBoard logs (3.1.4)
- [ ] Checkpoints guardados (3.1.4)
- [ ] Reporte de análisis (3.1.5)
- [ ] README con instrucciones para reproducir

---

## 🔧 Tools & Librerías

```python
# Core
torch  # Deep learning
gymnasium  # RL interfaces
numpy, pandas  # Data

# Logging
tensorboard  # SummaryWriter
wandb  # Alternative: Weights & Biases

# Plotting
matplotlib, seaborn  # Análisis

# ABIDES
# (cuando esté disponible de Benjamín)
```

---

## ⚠️ Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|-----------|
| Redes de Mauricio incompletas | MEDIA | Alto | Plan B: usar dummy networks |
| ABIDES muy lento | BAJA | Alto | Usar stub envs for testing |
| Training no converge | MEDIA | Alto | Ajustar hyperparameters (lr, gamma, etc) |
| OOM (memory) en Colab | BAJA | Alto | Reducir batch_size, rollout_steps |

---

## 📞 Contactos / Coordinación

- **Mauricio (Redes):** Confirmar que actor_critic.py lista por Lunes 28
- **Benjamín (ABIDES):** Confirmar integración disponible
- **Benjamín (Datos):** Entregar data/processed/ cuando esté listo (bonus para Poisson real)

---

## 🎓 Contribución a Tesis

Capítulos esperados:
1. **"Training PPO multi-agente con Gymnasium"** - arquitectura, hiperparámetros
2. **"Convergencia de políticas"** - análisis matemático + empírico
3. **"Mitigación de slippage"** - comparación IS antes/después training
4. **"Generalization a cambios de mercado"** - stress testing

