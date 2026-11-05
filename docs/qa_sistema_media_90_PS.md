# Revisión (QA) del sistema tras la liquidez media de las 90 corridas

**Quién:** PS, con apoyo de Claude Code. **Fecha:** 1 de noviembre de 2026.
**Qué es:** solo una revisión. No se cambió código. Se usaron los 30 resultados de la liquidez media (semillas 4 a 6) y el código de las ramas `feature/ps-3-2-1-cuadernos` y `main`.

## Resultado que se quiere explicar

| | Sistema | TWAP | VWAP |
|---|---|---|---|
| Costo medio (bps) | 47,1 | 50,5 | 51,3 |

- La diferencia contra TWAP es −3,4 bps [−26; 20], con p = 0,63. En la 3.1.3 era −22 bps.
- El sistema gana 16 de 30.

## Hallazgo 1: el Maestro siempre hace lo mismo (es un calendario fijo)

- En 276 de 282 decisiones (98 %) eligió **α = 0,5** (el máximo: la mitad de lo que falta) y la **ventana de 15 minutos** (la máxima).
- Por eso compra ≈ 45 % en la primera media hora, ≈ 70 % en la primera hora y ≈ 90 % en dos horas, en todas las órdenes y todos los días.
- Que elija siempre el extremo de las opciones indica que, si pudiera, iría aún más rápido.

**Consecuencia:** en la práctica, el sistema se comporta como la regla «compra la mitad de lo que falta cada media hora». No se adapta al día.

## Hallazgo 2: el resultado depende de si el precio sube o baja, no de una decisión

- Hay una correlación de −0,78 entre la ventaja del sistema y el costo de TWAP.
- **Días en que TWAP salió caro (el precio subió), 20 días:** el sistema ahorra en promedio **39 bps**, porque compró temprano.
- **Días en que TWAP salió barato (el precio bajó), 10 días:** el sistema pierde en promedio **68 bps**, porque ya había comprado.

**Consecuencia:** el resultado depende de cuántos días «suben» o «bajan» en la muestra. Eso explica por qué con las semillas 1 a 3 se obtuvo −22 bps y con las 4 a 6, −3 bps.

## Por qué pasa (causas encontradas en el código)

| # | Causa | Dónde | Efecto |
|---|---|---|---|
| C1 | **El Maestro se entrenó sin la corrección del cierre.** `crear_jornada` no pasa `completar_al_cierre`, así que en el entrenamiento las órdenes que parten a las 14:00 no podían completarse (máximo 93,75 %) y eso se castigaba con λ. La corrección se agregó después, solo en la evaluación | `src/training/maestro_trainer.py`, `crear_jornada` | Aprendió a comprar lo más rápido posible para no quedar con saldo. Es la causa más probable del α = 0,5 |
| C2 | **El Maestro no ve el mercado.** `volatilidad` y `vol_promedio` son constantes (no se pasa `--datos-sm`) y el OBI agregado vale 0 | `evaluar_sistema_ps.py` (`VOL_CONSTANTE`) y `_compute_sm_state` | Solo ve el tiempo y lo que falta. Aunque quisiera, no puede reaccionar a cómo va el día |
| C3 | **Cada ventana de 30 minutos es un mercado nuevo e independiente.** El precio no sigue un camino continuo durante el día; lo único que une las ventanas es el impacto acumulado, que es un supuesto | `MaestroEjecutorEnv` y desviación 7 | No hay tendencia que se pueda predecir. Que el día «suba» o «baje» es azar entre ventanas, así que ningún Maestro podría anticiparlo |
| C4 | **Se entrenó en Poisson y se evalúa en ABIDES** | `docs/sistema_final_resultado_PS.md` | Lo aprendido en Poisson puede no servir igual en ABIDES |
| C5 | **El mismo Ejecutor de apertura se usa en los tres tramos** | Desviación 8 | El ahorro en la ejecución fina podría ser menor en media jornada y cierre |

## Detalles menores

- **TWAP y VWAP no completan al cierre.** En MO-09 con semilla 4 quedaron en 87 %. Ahí su costo está subestimado; se informa con el costo ajustado (+30 bps por acción faltante).
- **En MO-08 a MO-10 (órdenes de cierre), VWAP = TWAP exacto.** El perfil de volumen es plano en ese tramo. No es un error, pero conviene decirlo.
- **`n_slices` parte en 0** aunque la orden empiece a media jornada (límite ya documentado).
- **Corte de tramos:** a las 11:00 en S_M y a las 11:30 en los Ejecutores (desviación 1).

## Mejoras posibles (de más a menos valor), y de quién son

| # | Mejora | Costo | De quién | Comentario |
|---|---|---|---|---|
| M1 | **Reentrenar el Maestro con `completar_al_cierre=True`** | Bajo: en Poisson se entrena rápido. Después habría que repetir las corridas | MR (entrenamiento) | Ataca C1. Lo esperable es que deje de ir siempre al máximo y reparta mejor |
| M2 | **Prueba de control: la regla «α = 0,5 fijo»** contra el sistema, en las mismas semillas | Bajo | PS (análisis) | Si cuestan lo mismo, el Maestro no aporta más que un calendario. Es un dato importante para el capítulo 7 |
| M3 | **Darle información de mercado al Maestro**: volatilidad real (`--datos-sm`), OBI agregado y cuánto se movió el precio desde la llegada | Medio: S_M es un contrato del Sprint 1, así que cambiarlo es una desviación | MR + BF | Ataca C2. Sin C3 resuelto, ayuda poco |
| M4 | **Mercado continuo durante el día** (o al menos con tendencia entre ventanas) | Alto | Equipo | Ataca C3. Probablemente sea trabajo futuro |
| M5 | **Ejecutores propios para media jornada y cierre** | Alto (ABIDES lento) | MR | Desviación 8, ya planteada como límite |

**Regla importante:** cualquier mejora hecha después de ver las 90 se declara como cambio y se informa **aparte**. El resultado oficial de la 3.2.3 sigue siendo el del sistema actual, como dice el plan de análisis.
