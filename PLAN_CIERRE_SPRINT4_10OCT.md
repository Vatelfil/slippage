# Plan de cierre total del Sprint 4

**Fecha:** 10 de octubre de 2026 (el sprint terminó el 9; el Sprint 5 empieza el 12).
**Objetivo:** que no quede ninguna tarea del Sprint 4 abierta. Todo lo hecho aquí lo elabora Paolo con apoyo de Claude Code y queda marcado "pendiente de revisión por el responsable (BF/MR)".

## Qué significa "cerrado"
Cada punto se cierra de una de tres formas, y se dice cuál:
1. **Hecho:** cumple lo que pide el Excel.
2. **Hecho con límite demostrado:** se intentó con evidencia y el criterio no se alcanza por una razón técnica (por ejemplo, p > 0,05 con `rmsc04`). Queda documentado y justificado.
3. **Pasa al Sprint 5 por diseño:** depende de algo que solo existe cuando entrena el sistema (por ejemplo, revalidar λ). Queda en el acta con fecha, no como pendiente del Sprint 4.

## Frentes de trabajo

| # | Frente | Tarea | Qué se entrega | Colab |
|---|---|---|---|---|
| 1 | Validación formal del simulador | 2.2.5 (PS) | `src/analysis/validacion_formal.py`, pruebas, informe `docs/validacion_formal_2.2.5_PS.md` | Corrida A |
| 2 | Elección de β y recompensa del Ejecutor | 2.2.3 (BF) | β fijado en `market_params.py`, normalización a [-1,1], análisis de distribución de R_E, `P_mid` unificado, esquema actualizado | Corrida B |
| 3 | Calibración de `rmsc04` | 2.2.4 (BF) | Intento de megashocks con tiempo límite, nota sobre OBI, documento actualizado | Corrida C |
| 4 | Redes de los Ejecutores | 2.1.2 (BF, Sprint 3) | Fábrica de 3 redes + documento de la desviación | No |
| 5 | Ajustes de la tarea de Mauricio | 2.2.1/2.2.2 (MR) | Semilla en el script de λ, `import torch` perezoso, texto corregido | No |
| 6 | Error del simulador de Poisson | (PS) | Nivel de precio corregido y barrido de β alineado, con pruebas | No |
| 7 | Documentos | (todos) | Acta de cierre; Word, PPT, resumen y desviaciones corregidos (el KS rechaza con 30 semillas) | No |

## Colab (lo que hace Paolo)
Una sola sesión, mismo entorno ABIDES (Python 3.9 con condacolab), `main` clonado, guardando en Google Drive. Todos los scripts son reanudables.
- **Prueba corta:** 1 episodio y 1 semilla para medir tiempos.
- **Corrida A (2.2.5):** 30 semillas nuevas por tramo, con la configuración calibrada y con la de fábrica.
- **Corrida B (2.2.3, fase 2):** entrenamiento PPO corto con 3 valores de β y un control β = 0, en el tramo de apertura. Si es demasiado lento: β provisional = 0,3 × β\* con la regla escrita y revalidación en el Sprint 5 (cierre tipo 3).
- **Corrida C (2.2.4):** sondeo de megashocks, máximo 3 horas de cómputo. Si D no baja de forma clara: cierre tipo 2.

## Criterios de decisión fijados antes de ver datos
- **2.2.5:** veredicto "válido" solo si todos los p > 0,05; se reportan además tamaños de efecto. Si no pasa, se dice.
- **β:** menor Implementation Shortfall con cumplimiento ≥ 95 % y peso del riesgo entre 5 y 80 % (regla del documento de Benjamín).
- **Megashocks:** se adopta solo si el KS baja D en al menos 2 de 3 tramos sin romper la volatilidad (±15 %).

## Orden y calendario
1. **Sábado:** scripts de Colab (A, B, C) y prueba corta. Mientras corre Colab, yo hago los frentes 4, 5, 6 y 7.
2. **Domingo:** corridas A y B en Colab; frente 1 (código y pruebas).
3. **Lunes 12:** integro resultados, cierro 1 y 2, fijo β, actualizo documentos.
4. **Martes 13:** corrida C integrada (o cierre tipo 2), revisión final, acta, PRs.

## PRs (uno por tema, para poder revertir)
PR-1 validación 2.2.5 · PR-2 recompensa y β · PR-3 megashocks (si aplica) · PR-4 Poisson + 2.1.2 + ajustes de Mauricio · PR-5 documentos.

## Riesgos
- Colab se desconecta o ABIDES tarda más de lo previsto: scripts reanudables y límites de tiempo.
- Pocas semillas = poca potencia: se declara en cada informe.
- Cambiar la convención del nivel de precio altera resultados del barrido de β en el simulador de respaldo: se regenera y se avisa en el PR.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
