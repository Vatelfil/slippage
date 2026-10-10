# Fase 2 de la elección de β (tarea 2.2.3), tramo apertura

**Elaborado por:** Paolo Sepúlveda (PS) con apoyo de Claude Code. **Pendiente de revisión por:** Benjamín Farias (BF) y Mauricio Reynoso (MR).
Corrida en Colab el 10 oct 2026 (ABIDES calibrado, FALABELLA, snapshot 2026-08-23). Episodios de entrenamiento por β: 300 · semillas de evaluación: 30 · β\* = 0,0618 (barrido de BF en ABIDES). PPO con la implementación de MR.

## Resultados

| β | Múltiplo | Slippage medio (bps) | Error estándar | Cumplimiento |
|---|---|---:|---:|---:|
| 0,00000 | 0× (control) | 5,12 | 3,47 | 0,973 |
| 0,00618 | 0,1× | 4,71 | 2,79 | 1,000 |
| 0,01854 | 0,3× | 5,77 | 2,42 | 0,341 |
| 0,06180 | 1× | sin ejecuciones | — | 0,000 |

Políticas heurísticas de referencia (mismas semillas):

| Política | Slippage medio (bps) | Cumplimiento |
|---|---:|---:|
| agresiva_market | 9,28 | 1,000 |
| twap_limit_medio | 4,06 | 0,984 |
| pasiva_limit | 8,82 | 1,000 |

## Regla de selección (fijada antes de ver los datos)

Candidatos 0,1 / 0,3 / 1 × β\*; control β = 0 solo como referencia. Se exige cumplimiento ≥ 95 % de la orden. Entre los que cumplen, se elige el de menor slippage si el Wilcoxon pareado con el siguiente da p < 0,05; si no, el valor central 0,3 × β\*.

**Resultado:** solo 0,1 × β\* cumple el 95 %, así que queda como único candidato: **β = 0,0061796**.

## Lectura honesta

- **Con β alto la red aprende a no operar.** Con 0,3× completa solo el 34 % de la orden y con 1× no ejecuta nada. R_E = (P_mid − P_ejec)·q − β·σ²·q castiga el riesgo en proporción a lo ejecutado, así que no ejecutar sale gratis. Si el riesgo debe medirse sobre el inventario pendiente, hay que cambiar la definición de R_E (decisión de BF, con MR y PS).
- **La diferencia entre 0,1× y el control es pequeña** (4,71 frente a 5,12 bps) y está dentro del error estándar (2,8 y 3,5 bps). No se puede afirmar que β = 0,1× mejore el slippage; solo que cumple la orden.
- **La política TWAP con órdenes límite (4,06 bps) iguala o supera a todas las redes entrenadas** con este entrenamiento corto. El PPO no demuestra todavía una ventaja sobre el benchmark simple.
- Una sola semilla de red por β y solo el tramo apertura. Media jornada y cierre quedan para el Sprint 5: cada episodio debe simular desde la apertura y un β tarda unas 2 h en media jornada (se midió el 0×).

## Decisión

`BETA_RIESGO_EJECUTOR = 0,0061796`, **provisional**, hasta revalidar en el Sprint 5.
