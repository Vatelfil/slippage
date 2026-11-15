# 90 corridas (3.2.1): resultado de la profundidad del market maker ×0,25, parte de MR (14 de noviembre)

**Quién:** MR la corrió en Colab (`Colab_90corridas_alta_A` y `_B`, rama `main`) y la revisó con apoyo de Claude Code.
**Datos:** `data/colab_resultados/corridas_90/alta/`, correspondientes a los JSON y tablas del zip `corridas_90_alta.zip`.

**Nombre del escenario:** en los archivos y cuadernos se llama `alta` (`mm_pov` ×0,25 en `data/scenarios/escenarios_liquidez_v3.json`). Desde el C-6c se informa como **profundidad del market maker ×0,25**, conforme a la desviación 10 (`docs/c6c_confirmacion_v3_BF.md`).

**Cierre de las 90 corridas:** con esta entrega se completan las tres profundidades (×4 de BF, ×1 de PS y ×0,25 de MR). La consolidación global 3.2.2 queda lista para la comparación estadística final 3.2.3 (`docs/plan_analisis_3_2_3_PS.md`).

---

## 1. Revisión del zip y control de calidad

- Hay 30 corridas pareadas por estrategia (sistema, TWAP y VWAP): 10 órdenes × semillas 4, 5 y 6 (90 corridas en total).
- No hay duplicados ni corridas con error.
- **La firma confirma lo acordado:**
  - `escenario` = `alta` con factor 0,25 sobre `mm_pov`, y `factor_tamano` = 1,0;
  - impacto acumulado ($y = 0,5$, $\tau = 120\text{ min}$);
  - corrección del cierre (`--completar-al-cierre`) y modo muestreo en el sistema;
  - `semilla_inicial` = 4 y `seed_red` = 1000;
  - Checkpoints idénticos a los de la media y baja, desde `sistema_final/maestro/`.
- **Cumplimiento:**
  - El sistema promedia 99,8 % de cumplimiento (solo MO-08 semilla 4 queda levemente bajo el umbral con 94,7 %);
  - TWAP y VWAP quedan en 87,1 % en MO-09 con semilla 4, idéntico a las profundidades ×4 y ×1 por determinismo del día fijado por la semilla.

---

## 2. Resultado del Escenario (Profundidad ×0,25)

| | Sistema | TWAP | VWAP |
|---|---|---|---|
| **Costo medio (bps)** | 69,19 | 65,33 | 64,79 |
| **Mediana (bps)** | 50,16 | 56,33 | 50,96 |
| **Desviación estándar (bps)** | 130,84 | 143,58 | 144,32 |

| Comparación | n | Dif. media (bps) | IC 95 % bootstrap | Wilcoxon p | t-test p | Dif. % | Ranking |
|---|---|---|---|---|---|---|---|
| **Sistema − TWAP** | 30 | +3,87 | [−16,56; 25,30] | 0,871 | 0,731 | +5,9 % | VWAP < TWAP < Sistema |
| **Sistema − VWAP** | 30 | +4,41 | [−20,42; 30,85] | 0,824 | 0,747 | +6,8 % | VWAP < TWAP < Sistema |

*Nota: IC 95 % por bootstrap pareado con 3.000 remuestreos (semilla 0).*

- **Lectura:** en este escenario de profundidad reducida del market maker (alta liquidez), TWAP y VWAP tienen un costo medio ligeramente menor que el sistema (+3,87 bps), pero el IC 95 % incluye ampliamente el 0 y el test de Wilcoxon ($p = 0,871$) no muestra diferencia estadísticamente significativa.

---

## 3. Consolidación Global de las 90 Corridas (Tarea 3.2.2)

Con las tres profundidades integradas mediante `scripts/consolidar_resultados_3_2_2.py`:

| Bloque | Profundidad MM | n | Sistema (bps) | TWAP (bps) | VWAP (bps) | Dif. vs TWAP (bps) | IC 95 % | Wilcoxon p | Ranking |
|---|---|---|---|---|---|---|---|---|---|
| **×4** (BF) | `baja` | 30 | 59,51 | 70,05 | 69,15 | −10,53 | [−33,09; 11,79] | 0,440 | Sistema < VWAP < TWAP |
| **×1** (PS) | `media` | 30 | 47,11 | 50,48 | 51,30 | −3,37 | [−26,15; 19,63] | 0,626 | Sistema < TWAP < VWAP |
| **×0,25** (MR) | `alta` | 30 | 69,19 | 65,33 | 64,79 | +3,87 | [−16,56; 25,30] | 0,871 | VWAP < TWAP < Sistema |
| **Global** | **Todas** | **90** | **58,61** | **61,95** | **61,75** | **−3,34** | **[−15,69; 9,67]** | **0,386** | **Sistema < VWAP < TWAP** |
| Global sin días < 95 % | Todas | 86 | 59,60 | 62,85 | 62,64 | −3,25 | [−16,56; 10,48] | 0,422 | Sistema < VWAP < TWAP |

### Conclusiones de la integración:
1. En el conjunto de las 90 corridas pareadas, **el sistema PPO jerárquico es en promedio 3,34 bps más barato que TWAP y 3,14 bps más barato que VWAP**.
2. Al igual que en cada escenario individual, el intervalo de confianza global incluye el 0 ([−15,69; 9,67] bps) y no alcanza significancia estadística formal bajo Wilcoxon ($p = 0,386$).
3. Quedan habilitados formalmente los tests globales de la 3.2.3 (Kruskal-Wallis y Friedman entre escenarios de profundidad).
