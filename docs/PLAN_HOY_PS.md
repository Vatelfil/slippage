# Plan HOY - Sábado 13 Sept - PS (Sin bloqueadores)

**Objetivo:** Completar 3.1.4 + 3.1.5 (tu parte Sprint 4) COMPLETAMENTE implementadas.

**Status:** Benjamín en proceso, pero TÚ NO ESTÁS BLOQUEADO.

---

## ✅ QUE PUEDES HACER YA (no depende de otros)

### **TAREA A: Implementar Logging Completo (3.1.4)** - 6 horas

**Archivo a editar:** `notebooks/Training_PPO_Sprint4_PS.ipynb`

**Qué hacer:**

#### 1. **TensorBoard + CSV Logging** (2 horas)
```python
# En el training loop:

from torch.utils.tensorboard import SummaryWriter
import csv
from datetime import datetime

# Setup
log_dir = f"logs/ppo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
writer = SummaryWriter(log_dir)
csv_file = f"{log_dir}/metrics.csv"

# Durante training:
def log_metrics(step, maestro_return, maestro_loss, ejecutor_returns, ejecutor_losses):
    # TensorBoard
    writer.add_scalar('maestro/return', maestro_return, step)
    writer.add_scalar('maestro/loss/policy', maestro_loss['policy'], step)
    writer.add_scalar('maestro/loss/value', maestro_loss['value'], step)
    writer.add_scalar('maestro/entropy', maestro_loss['entropy'], step)
    
    for i, (ret, loss) in enumerate(zip(ejecutor_returns, ejecutor_losses)):
        writer.add_scalar(f'ejecutor{i}/return', ret, step)
        writer.add_scalar(f'ejecutor{i}/loss', loss, step)
    
    # CSV
    with open(csv_file, 'a', newline='') as f:
        writer_csv = csv.writer(f)
        writer_csv.writerow([
            step, maestro_return,
            maestro_loss['policy'], maestro_loss['value'], maestro_loss['entropy'],
            *ejecutor_returns,
        ])

# Llamar cada N steps
log_metrics(step, R_m, L_m, Rs_e, Ls_e)
```

#### 2. **Checkpointing Completo** (2 horas)
```python
def save_checkpoint(step, checkpoint_dir='checkpoints'):
    checkpoint = {
        'step': step,
        'timestamp': datetime.now().isoformat(),
        
        # Redes (cuando Mauricio entregue)
        'maestro_state_dict': maestro_actor_critic.state_dict(),
        'maestro_optimizer': maestro_optimizer.state_dict(),
        'ejecutor_state_dicts': [ac.state_dict() for ac in ejecutor_actor_critics],
        'ejecutor_optimizers': [opt.state_dict() for opt in ejecutor_optimizers],
        
        # Config (para reproducibilidad)
        'config': config,
        
        # Métricas hasta ahora
        'train_stats': {
            'maestro_returns': list(train_stats['maestro_return']),
            'ejecutor_returns': [list(r) for r in train_stats['ejecutor_return']],
            'losses': train_stats['losses'],
        }
    }
    
    path = f"{checkpoint_dir}/checkpoint_{step:06d}.pt"
    torch.save(checkpoint, path)
    print(f"✓ Checkpoint: {path}")

# En training loop: llamar cada checkpoint_interval
if step % config['checkpoint_interval'] == 0:
    save_checkpoint(step)

# Para resumir training después:
def load_checkpoint(path):
    checkpoint = torch.load(path)
    maestro_actor_critic.load_state_dict(checkpoint['maestro_state_dict'])
    maestro_optimizer.load_state_dict(checkpoint['maestro_optimizer'])
    # ... etc
    return checkpoint['step']
```

#### 3. **Logging de Hiperparámetros** (1 hora)
```python
def log_config(config, log_dir):
    with open(f"{log_dir}/config.json", 'w') as f:
        json.dump(config, f, indent=2)
    
    # También log en TensorBoard
    writer.add_text('config', json.dumps(config, indent=2))

log_config(config, log_dir)
```

#### 4. **Logging de Video (bonus)** (1 hora, opcional)
```python
def record_episode_video(env, actor_critic, episode_num, log_dir):
    """Grabar un episodio para visualización."""
    frames = []
    obs, _ = env.reset()
    done = False
    
    while not done:
        with torch.no_grad():
            action, _, _, _ = actor_critic.get_action_and_value(
                torch.FloatTensor(obs).to(device)
            )
        
        obs, reward, done, truncated, info = env.step(action.cpu().numpy())
        # frames.append(render_frame(...))  # si env tiene rendering
    
    # Guardar como video
    # imageio.mimsave(f"{log_dir}/episode_{episode_num}.mp4", frames)

# Llamar cada eval_interval
if step % config['eval_interval'] == 0:
    record_episode_video(maestro_env, maestro_actor_critic, step, log_dir)
```

**Deliverable:** 
- Colab con logging completo
- Carpeta `logs/` con estructura clara
- CSV con métricas (para análisis después)

---

### **TAREA B: Implementar Análisis de Convergencia (3.1.5)** - 14 horas

**Archivo a crear:** `src/analysis/convergence_analysis.py` + notebook para plots

#### 1. **Función de Análisis Básica** (4 horas)
```python
# src/analysis/convergence_analysis.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

class ConvergenceAnalyzer:
    def __init__(self, csv_path):
        self.df = pd.read_csv(csv_path)
        self.step = self.df['step'].values
    
    def plot_returns(self, window=100):
        """Retorna suavizadas (media móvil)."""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Maestro
        maestro_ret = self.df['maestro_return'].rolling(window).mean()
        ax.plot(self.step, maestro_ret, label='Maestro', linewidth=2)
        
        # Ejecutores
        for i in range(3):
            col = f'ejecutor{i}_return'
            if col in self.df.columns:
                ret = self.df[col].rolling(window).mean()
                ax.plot(self.step, ret, label=f'Ejecutor {i}', linewidth=2)
        
        ax.set_xlabel('Timestep')
        ax.set_ylabel('Return (media móvil)')
        ax.set_title(f'Convergencia de Returns (window={window})')
        ax.legend()
        ax.grid(True, alpha=0.3)
        return fig
    
    def plot_losses(self):
        """Pérdidas (policy, value, entropy)."""
        fig, axes = plt.subplots(1, 3, figsize=(15, 4))
        
        # Policy loss
        axes[0].plot(self.step, self.df['maestro_loss_policy'])
        axes[0].set_title('Policy Loss (Maestro)')
        axes[0].set_ylabel('Loss')
        axes[0].grid(True, alpha=0.3)
        
        # Value loss
        axes[1].plot(self.step, self.df['maestro_loss_value'])
        axes[1].set_title('Value Loss (Maestro)')
        axes[1].set_ylabel('Loss')
        axes[1].grid(True, alpha=0.3)
        
        # Entropy
        axes[2].plot(self.step, self.df['maestro_entropy'])
        axes[2].set_title('Entropy (Maestro)')
        axes[2].set_ylabel('Entropy')
        axes[2].grid(True, alpha=0.3)
        
        for ax in axes:
            ax.set_xlabel('Timestep')
        
        plt.tight_layout()
        return fig
    
    def compute_stability(self, window=5000):
        """Estabilidad: std de returns en ventanas."""
        stds = []
        steps = []
        
        for i in range(0, len(self.df), window):
            segment = self.df.iloc[i:i+window]['maestro_return']
            if len(segment) > 0:
                stds.append(segment.std())
                steps.append(self.df.iloc[i]['step'])
        
        return np.array(steps), np.array(stds)
    
    def compute_improvement_factor(self, baseline_return=0):
        """Mejora vs baseline."""
        final_return = self.df['maestro_return'].iloc[-1]
        return final_return / (baseline_return + 1e-6)
    
    def statistical_test(self):
        """Test: ¿hay trend significativo en returns?"""
        x = np.arange(len(self.df))
        y = self.df['maestro_return'].values
        
        slope, intercept, r, p, se = stats.linregress(x, y)
        
        return {
            'slope': slope,
            'r_squared': r**2,
            'p_value': p,
            'significant': p < 0.05,
        }

# Uso:
analyzer = ConvergenceAnalyzer('logs/ppo_xxx/metrics.csv')
fig1 = analyzer.plot_returns(window=100)
fig2 = analyzer.plot_losses()
steps, stds = analyzer.compute_stability()
improvement = analyzer.compute_improvement_factor(baseline_return=0)
stats_test = analyzer.statistical_test()
```

#### 2. **Análisis de Interpretabilidad** (4 horas)
```python
class InterpretabilityAnalyzer:
    """Entender qué aprende cada agente."""
    
    def analyze_maestro_actions(self, actions_df):
        """¿Cuándo decide split alto (α > 0.7)?"""
        high_alpha = actions_df[actions_df['alpha'] > 0.7]
        
        # Correlación con volatilidad
        corr_vol = high_alpha['volatilidad'].corr(high_alpha['alpha'])
        
        # Correlación con spread
        corr_spread = high_alpha['spread'].corr(high_alpha['alpha'])
        
        return {
            'corr_volatility': corr_vol,
            'corr_spread': corr_spread,
        }
    
    def analyze_ejecutor_actions(self, actions_df, ejecutor_id):
        """Preferencia de order_type por fase."""
        
        # Contar órdenes por tipo
        order_types = ['LIMIT_BUY', 'LIMIT_SELL', 'MARKET']
        counts = {ot: (actions_df['order_type'] == ot).sum() for ot in order_types}
        
        # Normalizar
        probs = {ot: count / sum(counts.values()) for ot, count in counts.items()}
        
        return probs
    
    def plot_action_distribution(self, actions_df, save_path=None):
        """Heatmap: step vs acción."""
        fig, ax = plt.subplots(figsize=(12, 4))
        
        # Histograma 2D
        h, xe, ye = np.histogram2d(
            actions_df['step'], actions_df['action_idx'],
            bins=[30, 240]
        )
        
        im = ax.imshow(h.T, aspect='auto', cmap='YlOrRd', origin='lower')
        ax.set_xlabel('Step')
        ax.set_ylabel('Action Index (0-239)')
        ax.set_title('Distribución de Acciones (heatmap)')
        plt.colorbar(im, ax=ax, label='Frecuencia')
        
        if save_path:
            plt.savefig(save_path, dpi=100, bbox_inches='tight')
        
        return fig
```

#### 3. **Reporte PDF Final** (3 horas)
```python
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, PageBreak, Table, TableStyle
from reportlab.lib import colors

def generate_report_pdf(analyzer, interpretability, save_path='report_sprint4.pdf'):
    doc = SimpleDocTemplate(save_path, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=30,
    )
    elements.append(Paragraph("Reporte Sprint 4 - Training PPO", title_style))
    elements.append(Paragraph("Paolo Sepúlveda (PS) | 13 Septiembre 2026", styles['Normal']))
    elements.append(PageBreak())
    
    # Sección 1: Convergencia
    elements.append(Paragraph("1. Convergencia de Retornos", styles['Heading2']))
    fig = analyzer.plot_returns(window=100)
    fig.savefig('temp_returns.png', dpi=100, bbox_inches='tight')
    elements.append(Image('temp_returns.png', width=500, height=300))
    
    # Sección 2: Losses
    elements.append(PageBreak())
    elements.append(Paragraph("2. Análisis de Pérdidas", styles['Heading2']))
    fig = analyzer.plot_losses()
    fig.savefig('temp_losses.png', dpi=100, bbox_inches='tight')
    elements.append(Image('temp_losses.png', width=500, height=300))
    
    # Sección 3: Métricas
    elements.append(PageBreak())
    elements.append(Paragraph("3. Métricas Finales", styles['Heading2']))
    
    stats_test = analyzer.statistical_test()
    metrics_data = [
        ['Métrica', 'Valor'],
        ['Slope (trend)', f"{stats_test['slope']:.6f}"],
        ['R²', f"{stats_test['r_squared']:.4f}"],
        ['P-value', f"{stats_test['p_value']:.4f}"],
        ['Convergencia significativa?', 'Sí' if stats_test['significant'] else 'No'],
    ]
    
    table = Table(metrics_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    print(f"✓ Reporte guardado: {save_path}")
```

#### 4. **Documentación de Resultados** (3 horas)
```python
def save_analysis_summary(analyzer, interpretability, save_path='ANALYSIS_RESULTS.md'):
    with open(save_path, 'w') as f:
        f.write("# Análisis Sprint 4 - Resultados\n\n")
        
        # Convergencia
        stats = analyzer.statistical_test()
        f.write("## 1. Convergencia\n\n")
        f.write(f"- Slope: {stats['slope']:.6f}\n")
        f.write(f"- R²: {stats['r_squared']:.4f}\n")
        f.write(f"- P-value: {stats['p_value']:.4f}\n")
        f.write(f"- **Conclusión:** {'Convergencia SIGNIFICATIVA' if stats['significant'] else 'Sin convergencia clara'}\n\n")
        
        # Interpretabilidad Maestro
        f.write("## 2. Estrategia Maestro\n\n")
        interp_m = interpretability.analyze_maestro_actions(...)
        f.write(f"- Correlación alpha ~ volatilidad: {interp_m['corr_volatility']:.3f}\n")
        f.write(f"- Correlación alpha ~ spread: {interp_m['corr_spread']:.3f}\n")
        
        # Recomendaciones
        f.write("\n## 3. Recomendaciones Sprint 5\n\n")
        f.write("- Ajustar learning rate si diverge\n")
        f.write("- Investigar acción repetitiva (falta exploración)\n")
        f.write("- Validar contra datos out-of-sample\n")

save_analysis_summary(analyzer, interpretability)
```

**Deliverable:**
- `src/analysis/convergence_analysis.py` (reutilizable)
- `ANALYSIS_RESULTS.md` (conclusiones)
- `report_sprint4.pdf` (presentable)
- Plots en carpeta `logs/`

---

## 📅 CRONOGRAMA HOY (Sábado 13)

```
09:00-12:00  → TAREA A: Logging (6 horas)
             - TensorBoard + CSV (2h)
             - Checkpointing (2h)
             - Config + Video (2h)

12:00-13:00  → PAUSA/ALMUERZO

13:00-22:00  → TAREA B: Análisis (9 horas)
             - Análisis básico (4h)
             - Interpretabilidad (4h)
             - Reporte PDF (1h)
```

**Total: ~15-16 horas de trabajo SIN dependencias**

---

## ✅ CHECKLIST - FIN DEL DÍA

- [ ] Logging completo en Colab
- [ ] Checkpointing implementado
- [ ] `src/analysis/convergence_analysis.py` creado
- [ ] Análisis de interpretabilidad
- [ ] Reporte PDF generado
- [ ] `ANALYSIS_RESULTS.md` documentado
- [ ] Todo pusheado a repo (feature branch)

---

## 🚀 CUANDO BENJAMÍN ENTREGUE

1. `data/processed/clean_5m_<fecha>/` listo
2. Ejecutas: `python src/envs/calibration_poisson.py`
3. Obtienes: `data/poisson_params_calibrated.json` con λ+, λ−, θ reales
4. Actualizas el Colab con parámetros reales
5. Corres training
6. Ejecutas análisis con datos reales

---

## 💡 VENTAJAS DE HACER ESTO HOY

✅ NO esperas a nadie  
✅ Código reutilizable para múltiples runs  
✅ Cuando Benjamín entregue, solo corres un botón  
✅ Análisis listo para tesis  
✅ Checkpoints para debugging/reanudar training  

