# Reevaluación de los Ejecutores con muchas semillas de evaluación

**Elaborado por:** PS con apoyo de Claude Code (uso autorizado por la universidad). Describe; no decide.

Todas las redes y su control (la red inicial de la misma semilla, también muestreando la política) se evaluaron en las mismas **300 semillas**. Diferencia = red − control: **negativa significa que la red cuesta menos**. IC = intervalo bootstrap al 95 % de la diferencia media; p = Wilcoxon pareado por semilla de evaluación.

| Grupo | Semilla de red | Episodios | Cumpl. | Slippage red (bps) | Control (bps) | Diferencia media (bps) | IC 95 % | Mediana | Semillas que gana | p |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| Original sin arreglo | 2000 | 1000 | 1,000 | 7,99 | 7,00 | 0,99 | [-0,30; 2,27] | 0,54 | 134 de 300 | 0,044 |
| Original sin arreglo | 3000 | 1000 | 1,000 | 6,61 | 7,08 | -0,47 | [-1,83; 0,91] | -0,50 | 163 de 300 | 0,148 |
| V2 | 1000 | 1000 | 1,000 | 6,52 | 6,98 | -0,46 | [-1,63; 0,68] | 0,09 | 145 de 300 | 0,741 |
| V2 | 2000 | 1000 | 1,000 | 7,48 | 7,00 | 0,47 | [-0,76; 1,75] | -0,30 | 162 de 300 | 0,482 |
| V2 | 3000 | 1000 | 1,000 | 6,50 | 7,08 | -0,58 | [-1,90; 0,70] | 0,05 | 147 de 300 | 0,788 |
| V2 | 4000 | 1000 | 1,000 | 6,81 | 7,01 | -0,20 | [-1,29; 0,94] | -0,11 | 154 de 300 | 0,350 |
| V4 | 1000 | 1000 | 1,000 | 6,82 | 6,98 | -0,16 | [-0,89; 0,59] | -0,08 | 166 de 300 | 0,133 |
| V4 | 2000 | 1000 | 1,000 | 6,75 | 7,00 | -0,25 | [-0,84; 0,33] | 0,00 | 144 de 300 | 0,267 |

## Resumen por grupo

| Grupo | Redes | Diferencia media entre redes (bps) | Redes que cuestan menos | Prueba de signos (p) | Cumplimiento medio |
|---|---:|---:|---:|---:|---:|
| V2: recompensa original + penalización 30 bps + γ = 1 | 4 | -0,19 | 3 de 4 | 0,625 | 1,000 |
| Original sin arreglo (γ = 0,95), opción 0 | 2 | 0,26 | 1 de 2 | 1,000 | 1,000 |
| V4: recompensa contra el precio de llegada + penalización 30 bps + γ = 1 | 2 | -0,21 | 2 de 2 | 0,500 | 1,000 |

La prueba de signos entre redes es solo una guía: las redes de un mismo grupo comparten recompensa y entorno.

## Heurísticas de referencia (mismas semillas)

| Heurística | Slippage (bps) | Cumplimiento |
|---|---:|---:|
| agresiva_market | 9,83 | 1,000 |
| pasiva_limit | 10,08 | 1,000 |
| twap_limit_medio | 4,65 | 0,989 |

🤖 Generado con [Claude Code](https://claude.com/claude-code)
