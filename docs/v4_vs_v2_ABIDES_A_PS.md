# V4 (recompensa contra el precio de llegada) frente a V2 y al control, en ABIDES

**Elaborado por:** PS con apoyo de Claude Code (uso autorizado por la universidad). Describe; no decide.

Política muestreando, mismas semillas de evaluación y misma semilla de red en las tres columnas. V2 = recompensa original + penalización 30 bps + γ = 1; V4 = recompensa contra el precio de llegada + penalización 30 bps + γ = 1. Diferencias: negativas = V4 cuesta menos.

| Semilla de red | Cumplimiento V4 | Slippage V4 (bps) | Slippage V2 (bps) | Control (bps) | V4 − control (bps) | p | V4 − V2 (bps) | p | V2 − control (bps) | p |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1000 | 1,000 | 6,25 | 6,47 | 8,72 | -2,47 | 0,025 | -0,22 | 0,858 | -2,25 | 0,221 |
| 2000 | 1,001 | 8,77 | 6,71 | 8,89 | -0,12 | 0,613 | 2,05 | 0,259 | -2,17 | 0,166 |

- **V4 frente al control:** 2 de 2 redes cuestan menos; diferencia media -1,29 bps (prueba de signos entre redes, p = 0,500; es una guía, las redes comparten diseño y entorno).
- **V4 frente a V2:** 1 de 2 redes cuestan menos; diferencia media 0,92 bps.
- **V2 frente al control** (las redes que tienen V2 y control con las mismas semillas): 2 de 2 cuestan menos; diferencia media -2,21 bps.
- **Cumplimiento V4 (muestreando):** media 1,001, mínimo 1,000.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
