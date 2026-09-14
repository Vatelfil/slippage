# Sprint 4: Tarea 3.1.4 (Logging) + 3.1.5 (Análisis de Convergencia)

**Responsable:** Paolo Sepúlveda (PS)  
**Período:** 13 septiembre 2026  
**Estado:** ✅ COMPLETADO (3.1.4 + 3.1.5)  
**Clasificación para Tesis:** Capítulos 2-3 ("Training PPO Multi-Agente" + "Convergencia de Políticas")

---

## QUÉ SE IMPLEMENTÓ

### Tarea 3.1.4: Logging y Checkpointing

**Ubicación:** `notebooks/Training_PPO_Sprint4_PS.ipynb` (secciones 8, 9, 10)

#### 1. **TensorBoard Logging** (para visualización en tiempo real)
```python
from torch.utils.tensorboard import SummaryWriter

writer = SummaryWriter(log_dir)

# Cada N timesteps:
writer.add_scalar('maestro/return', R_maestro, global_step)
writer.add_scalar('maestro/loss/policy', L_policy, global_step)
writer.add_scalar('maestro/loss/value', L_value, global_step)
writer.add_scalar('maestro/entropy', H_entropy, global_step)

for i in range(3):
    writer.add_scalar(f'ejecutor{i}/return', R_ejecutor[i], global_step)
```

**Beneficio:** 
- Graficar métricas en tiempo real (no esperar a fin del training)
- Detectar divergencia temprano
- Comparar runs diferentes lado a lado

#### 2. **CSV Logging** (para análisis posterior)
```csv
step, maestro_return, maestro_loss_policy, maestro_loss_value, maestro_entropy, ejecutor0_return, ejecutor1_return, ejecutor2_return
0, -10.23, 0.45, 0.12, 0.89, -5.1, -4.9, -5.2
100, -8.45, 0.38, 0.10, 0.82, -3.2, -3.5, -3.1
...
```

**Beneficio:**
- Análisis fuera de línea (excel, pandas, R)
- Disponible incluso si TensorBoard no carga
- Fácil de versionar en git

#### 3. **Checkpointing** (guardar/cargar estados)
```python
checkpoint = {
    'step': global_step,
    'timestamp': datetime.isoformat(),
    'maestro_state_dict': maestro_actor_critic.state_dict(),
    'maestro_optimizer': maestro_optimizer.state_dict(),
    'ejecutor_state_dicts': [ac.state_dict() for ac in ejecutor_actor_critics],
    'ejecutor_optimizers': [opt.state_dict() for opt in ejecutor_optimizers],
    'config': config,  # para reproducibilidad
    'train_stats': train_stats,  # métricas acumuladas
}
torch.save(checkpoint, f'checkpoints/checkpoint_{step:06d}.pt')
```

**Beneficio:**
- Pausar/reanudar training (Colab timeout)
- Exportar modelo entrenado
- Reproducibilidad exacta (misma config)

#### 4. **Logging de Configuración**
```python
# config.json guardado automáticamente
{
    "hidden_dim": 128,
    "learning_rate": 3e-4,
    "gamma": 0.99,
    "clip_ratio": 0.2,
    "entropy_coef": 0.01,
    "total_timesteps": 1_000_000,
    ...
}
```

**Beneficio:** Rastrear qué hiperparámetros se usaron en cada run.

---

### Tarea 3.1.5: Análisis de Convergencia

**Ubicaciones:**
- Clase: `src/analysis/convergence_analysis.py`
- Notebook: `notebooks/Analysis_Sprint4.ipynb`
- Template de resultados: `ANALYSIS_RESULTS.md`

#### 1. **Clase `ConvergenceAnalyzer`**

```python
analyzer = ConvergenceAnalyzer(csv_path='logs/ppo_xxx/metrics.csv')
```

**Métodos disponibles:**

| Método | Entrada | Salida | Propósito |
|--------|---------|--------|-----------|
| `plot_returns()` | csv_path, window | Figura matplotlib | Gráfico de retornos suavizados (media móvil) |
| `plot_losses()` | csv_path | Figura matplotlib | 3 subplots (policy loss, value loss, entropy) |
| `compute_stability()` | window | (steps, stds) | Estabilidad: std de returns en ventanas móviles |
| `compute_improvement_factor()` | baseline_return | float | (final_return - baseline) / baseline |
| `statistical_test()` | csv_path | dict | Regresión: slope, R², p-value (¿hay trend?) |

**Ejemplo de uso:**
```python
# Cargar logs
analyzer = ConvergenceAnalyzer('logs/ppo_20260913_120000/metrics.csv')

# Plots
fig1 = analyzer.plot_returns(window=100)
fig2 = analyzer.plot_losses()
fig1.savefig('returns.png')
fig2.savefig('losses.png')

# Análisis estadístico
stats = analyzer.statistical_test()
print(f"Slope: {stats['slope']:.6f}")
print(f"R²: {stats['r_squared']:.4f}")
print(f"P-value: {stats['p_value']:.4f}")
print(f"¿Convergencia significativa?: {stats['significant']}")

# Estabilidad
steps, stds = analyzer.compute_stability(window=5000)
# steps: array de timesteps
# stds: array de std en cada ventana (debe decrecer)

# Mejora vs baseline
improvement = analyzer.compute_improvement_factor(baseline_return=0)
```

#### 2. **Notebook `Analysis_Sprint4.ipynb`**

Flujo completo:
1. Load CSV desde logs
2. Instancia `ConvergenceAnalyzer`
3. Genera plots (returns, losses)
4. Statistical test
5. Stability analysis
6. Exporta resulados a markdown

**Ejecutable end-to-end:** Ya probado con datos sintéticos.

#### 3. **Template `ANALYSIS_RESULTS.md`**

Estructura para documentar resultados:
```markdown
# Análisis Sprint 4 - Resultados

## 1. Convergencia
- Slope: _(pendiente)_
- R²: _(pendiente)_
- P-value: _(pendiente)_
- Conclusión: _(pendiente)_

## 2. Estabilidad
- Std inicial: _(pendiente)_
- Std final: _(pendiente)_
- Trend: _(pendiente)_

## 3. Interpretabilidad
- Maestro: ¿qué aprende?
- Ejecutores: preferencias de acciones
- Correlación con features de mercado

## 4. Generalization
- Training vs validation
- Stress testing (volatilidad ↑, spread ↑)

## 5. Recomendaciones Sprint 5
- (rellenar después de análisis)
```

**Por qué template?** Para no mezclar resultados sintéticos de prueba con resultados reales de tesis.

---

## POR QUÉ SE IMPLEMENTÓ ASÍ

### Logging (3.1.4)

**Decisión 1: TensorBoard + CSV (no solo uno)**
- **Razón:** TensorBoard es visual (detectar problemas), CSV es analítico (reproducible)
- **Beneficio:** Cobertura tanto para debugging como para análisis

**Decisión 2: Guardar config.json**
- **Razón:** Reproducibilidad exacta (tesis requiere "mismo experimento = mismo resultado")
- **Beneficio:** Versioning automático de hiperparámetros

**Decisión 3: Checkpoints cada N steps (no solo al final)**
- **Razón:** Colab puede timeout o GPU crash
- **Beneficio:** No perder horas de training

### Análisis (3.1.5)

**Decisión 1: Clase reutilizable (no scripts ad-hoc)**
- **Razón:** Múltiples runs, múltiples datasets
- **Beneficio:** Mismo análisis para todos (consistencia)

**Decisión 2: Statistical test (no solo plots visuales)**
- **Razón:** "La convergencia se ve bien" ≠ "p < 0.05"
- **Beneficio:** Rigor científico para tesis

**Decisión 3: Estabilidad (std en ventanas móviles)**
- **Razón:** "El final es estable" pero ¿el principio también?
- **Beneficio:** Detectar divergencia temprana

---

## PARA QUÉ SE NECESITA (CONTRIBUCIÓN A TESIS)

### Capítulo 2: "Training PPO Multi-Agente"

**Secciones que este código permite escribir:**

1. **"2.1 Setup de Logging"**
   ```
   Describir TensorBoard, CSV, checkpoints.
   Justificar por qué cada uno.
   Incluir código real (del notebook).
   ```

2. **"2.2 Reproducibilidad"**
   ```
   Explicar cómo config.json garantiza replicabilidad.
   Mostrar ejemplo: mismo seed → mismo resultado.
   ```

3. **"2.3 Monitoreo en Tiempo Real"**
   ```
   Gráficos de TensorBoard en el documento.
   Cómo detectar divergencia/inestabilidad.
   ```

### Capítulo 3: "Convergencia de Políticas"

**Secciones que este código permite escribir:**

1. **"3.1 Análisis de Retornos"**
   ```
   Gráfico: returns vs timesteps.
   Media móvil (window=100).
   Interpretación: ¿converge? ¿cuántos pasos?
   ```

2. **"3.2 Estabilidad"**
   ```
   Gráfico: std(returns) en ventanas.
   Expectativa: debe decrecer.
   Implicación: política es más predecible.
   ```

3. **"3.3 Validación Estadística"**
   ```
   Test de regresión: slope, R², p-value.
   Resultado: ¿hay trend significativo (p<0.05)?
   Conclusión: convergencia demostrada o no.
   ```

4. **"3.4 Interpretabilidad"**
   ```
   ¿Qué aprende Maestro?
   ¿Qué aprende cada Ejecutor?
   Correlación con features de mercado (vol, spread, OBI).
   ```

---

## CÓMO USAR

### Fase 1: Training (en Colab)
```python
# Ejecutas notebooks/Training_PPO_Sprint4_PS.ipynb
# ↓
# Genera: logs/ppo_YYYYMMDD_HHMMSS/
#   ├─ metrics.csv
#   ├─ config.json
#   ├─ events (TensorBoard)
#   └─ checkpoints/
#       ├─ checkpoint_100000.pt
#       ├─ checkpoint_200000.pt
#       └─ ...
```

### Fase 2: Análisis (local o Colab)
```python
# Ejecutas notebooks/Analysis_Sprint4.ipynb
# ↓
# Lee: logs/ppo_YYYYMMDD_HHMMSS/metrics.csv
# ↓
# Genera:
#   ├─ logs/ppo_YYYYMMDD_HHMMSS/returns.png
#   ├─ logs/ppo_YYYYMMDD_HHMMSS/losses.png
#   ├─ logs/ppo_YYYYMMDD_HHMMSS/stability.png
#   └─ ANALYSIS_RESULTS.md (completado)
```

### Fase 3: Tesis
```markdown
# Capítulo 2
Incluir screenshots de TensorBoard y config.json.
Código de logging (copiar de Training_PPO_Sprint4_PS.ipynb).

# Capítulo 3
Incluir gráficos (returns.png, losses.png, stability.png).
Incluir tabla de statistical_test() (p-value, R², etc).
Citar ANALYSIS_RESULTS.md.
```

---

## DEPENDENCIAS AGREGADAS

**En `requirements.txt`:**
```
tensorboard      # logging en tiempo real
seaborn          # plots de alta calidad
scipy            # statistical_test (linregress)
reportlab        # PDF generation (opcional)
```

---

## ARCHIVOS MODIFICADOS/CREADOS

| Archivo | Tipo | Status |
|---------|------|--------|
| `notebooks/Training_PPO_Sprint4_PS.ipynb` | Secciones 8-10 | ✏️ Actualizado con logging |
| `src/analysis/convergence_analysis.py` | Nuevo | ✨ Creado + probado |
| `notebooks/Analysis_Sprint4.ipynb` | Nuevo | ✨ Creado + ejecutado |
| `ANALYSIS_RESULTS.md` | Nuevo | ✨ Template listo |
| `requirements.txt` | 4 líneas | ✏️ +tensorboard, seaborn, scipy, reportlab |
| `.gitignore` | 2 líneas | ✏️ +logs/, checkpoints/ |

---

## QUÉ FALTA (NO ES BLOQUERADOR PARA ESTA TAREA)

| Item | Responsable | Cuándo | Impacto |
|------|-------------|--------|--------|
| Datos reales para calibración Poisson (2.1.3) | Benjamín | Cuando entregue `data/processed/` | Necesario para "Capítulo 4: Validación contra IPSA real" |
| Redes de Mauricio (2.1.1/2.1.2) | Mauricio | Lunes 14 | Necesario para **CORRER** el training (ahora solo skeleton) |
| ABIDES integrado (2.1.2) | Benjamín | Lunes 21 | Necesario para simulación realista |

**Nota:** Las tareas 3.1.4 + 3.1.5 están **COMPLETAMENTE INDEPENDIENTES** de lo anterior. El código funciona, está verificado, y listo para cuando Mauricio/Benjamín entreguen.

---

## VERIFICACIÓN Y TESTING

✅ **Tarea 3.1.4 - Logging:**
- Función `log_metrics()` probada ✓
- Función `save_checkpoint()` probada ✓
- CSV generado y legible ✓
- Estructura de directorios creada ✓

✅ **Tarea 3.1.5 - Análisis:**
- `ConvergenceAnalyzer.plot_returns()` probado ✓
- `ConvergenceAnalyzer.plot_losses()` probado ✓
- `ConvergenceAnalyzer.statistical_test()` probado ✓
- Notebook ejecutado end-to-end ✓
- Manejo de errores verificado ✓

---

## CONCLUSIÓN

**Status:** ✅ COMPLETADO

Las Tareas 3.1.4 (Logging) + 3.1.5 (Análisis de Convergencia) de Sprint 4 están **100% implementadas, verificadas y listas para producción**.

El código es:
- 🔧 **Funcional:** Ejecutable ahora, sin esperar a otras tareas
- 📚 **Documentado:** Comentarios en código + markdown
- 🧪 **Testeado:** Probado con datos sintéticos
- 📊 **Reutilizable:** Mismo análisis para múltiples runs
- 📖 **Thesis-ready:** Capítulos 2-3 listos para escribir

**Próximo paso:** Cuando Benjamín entregue datos reales → re-ejecutar calibración Poisson → correr training → análisis final → tesis completa.

