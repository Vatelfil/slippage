# ¿Por qué el Maestro usa siempre α = 0,5? Reglas fijas por tipo de día (11 de noviembre)

**Responsable:** BF (extensión de la 2.1.3; viabilidad de reentrenar el Maestro). **Se publica el 22 nov** porque el Capítulo 6 (MR, sección 6.3.1) lo cita. El 11 nov no se subió porque el resultado no cambiaba nada en el sistema.
**Scripts:** `src/envs/calibration_poisson_tercios.py` (calibración) y `scripts/prueba_reglas_fijas_tercios_bf.py` (prueba). **Salidas:** `data/calibration/poisson_tercios/` y `data/analysis/reglas_fijas_tercios_BF/`. **Tests:** `tests/test_calibration_poisson_tercios.py` y `tests/test_prueba_reglas_fijas_tercios.py`.

## 1. Pregunta

El Maestro entrenado elige casi siempre α = 0,5 («comprar el 50 % de lo que falta») con ventana de 15 min (`docs/sistema_final_resultado_PS.md`). ¿Es un defecto del entrenamiento, que se arreglaría reentrenando con días de actividad variada, o es la mejor regla aunque cambie el tipo de día?

**Idea de la prueba:** si la mejor regla fija es la misma en días de poca y de mucha actividad, ningún Maestro puede ganar adaptándose al tipo de día, y reentrenar no sirve.

## 2. Datos: Poisson por tercios de volumen diario

- **Días:** la unión de los snapshots 2026-08-23, 2026-09-27 y **2026-11-11** (descargado para esta prueba), con 115 días por activo.
  - Si un día se repite, se toma de la descarga más reciente.
  - Se excluye el día de cada descarga, porque sus velas no son definitivas.
- **Tercios:** por activo, según el volumen del día completo: 39 días bajos, 38 medios y 38 altos.
- **Estimación:** la de la 2.1.3 (`calibrate_tramo`), por tramo. Los archivos tienen nombres fuera del patrón `poisson_params_*.json` a propósito, para no reemplazar a la calibración oficial.

| Activo | Volumen mediano: bajo / medio / alto | λ alto / λ bajo (apertura · media jornada · cierre) | Volatilidad alto − bajo |
|---|---|---|---|
| FALABELLA | 0,77 / 1,20 / 1,74 millones | ×2,6 · ×2,5 · ×2,4 | +1,7 a +4,2 bps; excluye el 0 solo en media jornada |
| COPEC | 0,40 / 0,66 / 0,93 millones | ×2,4 · ×2,3 · ×2,0 | −6,6 a +7,9 bps; excluye el 0 solo en apertura (−6,6) |
| ECL | 0,24 / 0,55 / 1,05 millones | ×3,7 · ×2,9 · ×2,6 | −8,1 a +7,0 bps; excluye el 0 en media jornada (+7,0) y cierre (−8,1) |

Los días altos tienen entre 2,0 y 3,7 veces más llegadas de órdenes, y los 9 IC excluyen el 0. **La volatilidad no tiene un patrón consistente:** cambia de signo según el activo y el tramo.

## 3. Prueba: reglas fijas por tercio

- **Reglas:** α ∈ {10, 20, 30, 40, 50 %} de lo que falta, con ventana de 15 min (la que eligen los dos Maestros) y corrección del cierre.
- **Órdenes:** las 10 meta-órdenes v2, con su tamaño en acciones, así que la misma orden pesa más en un día flojo.
- **Ejecutores:** los del sistema final, en modo muestreo.
- **Impacto:** acumulado con la σ y el volumen del mismo tercio (y = 0,5, τ = 120 min).
- **Tamaño:** 10 semillas (101–110) × 10 órdenes × 5 reglas × 3 tercios = **1.500 corridas**, pareadas: las cinco reglas ven el mismo mercado.

**Criterio, fijado antes de correr** (`CRITERIO` en el script):
- **SIGUE** (vale la pena reentrenar) si la mejor α admisible del tercio bajo y la del alto son distintas, y si en cada uno de esos tercios la α del otro es peor que la propia: no es admisible, o cuesta más con un IC 95 % pareado cuyo límite inferior es > 0.
- **SE DETIENE** en cualquier otro caso.
- Una regla es **admisible** en un tercio si al menos el 95 % de sus corridas ejecuta al menos el 95 % de la orden.

**Cambio declarado (11 nov, antes de la corrida completa y después de una prueba de 30 corridas):** la versión inicial comparaba solo el slippage. Con α bajo la orden no se completaba (MO-08 al 83 %) y dejar saldo parecía barato. BF eligió exigir que la regla complete, que es el requisito de cumplimiento del plan de la 3.2.3, en lugar del costo ajustado de +30 bps.

## 4. Resultado: SE DETIENE

| α | Bajo: costo (bps) / completan | Medio | Alto |
|---|---|---|---|
| 10 % | 24,30 / 67 % | 22,49 / 64 % | 20,30 / 66 % |
| 20 % | 25,62 / 77 % | 23,76 / 73 % | 21,45 / 75 % |
| 30 % | 25,82 / **96 %** | 24,25 / 94 % | 21,68 / 92 % |
| 40 % | 25,37 / **99 %** | 24,24 / **98 %** | 21,40 / **99 %** |
| **50 %** | **24,53 / 100 %** | **23,89 / 100 %** | **20,89 / 100 %** |

En negrita, las reglas admisibles (≥ 95 % de las corridas completan).

- **La mejor regla admisible es α = 0,5 en los tres tercios.** Como la del tercio bajo y la del alto son la misma, el criterio da **SE DETIENE**: una sola regla fija sirve para todos los tipos de día, y no se reentrena el Maestro.
- **Las reglas lentas** (10 y 20 %) parecen más baratas, pero un tercio de sus corridas no completa la orden. Es el mismo problema de la 3.2.2: lo que no se ejecuta no tiene costo.
- **Lo que explica el α = 0,5 del Maestro:** es la mejor regla fija con este mercado y estos Ejecutores, no un defecto del entrenamiento.

## 5. Límites

- **α = 0,5 es el máximo del espacio de acciones** del Maestro (`ALPHA_VALUES` llega a 0,50). El óptimo está en el borde, así que no se sabe si comprar más rápido sería todavía mejor; el diseño no lo permite. Se informa como límite, no como óptimo absoluto.
- **Mercado Poisson, no ABIDES:** es el mismo simulador con que se entrenó el Maestro.
- **Solo ventana de 15 min y reglas fijas:** no descarta que una política que cambie α durante el día gane algo. Sí descarta que convenga una regla distinta según el tipo de día.
- **Snapshot 2026-11-11:** se versionan los reportes; los datos están en `backups/snapshot_2026-11-11.zip`, en Drive (`slippage_colab/`).

## 6. Dónde se usa

- **Capítulo 6 (MR), sección 6.3.1:** explica el colapso de entropía del Maestro oficial hacia α = 0,5.
- **Capítulo 8 (PS):** puede citarse en la discusión de por qué el control de reglas no encuentra aporte del calendario del Maestro.

---

Elaborado por BF con apoyo de Claude Code (uso de IA autorizado por la universidad).
