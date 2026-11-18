# 3.2.3: comparación estadística final del sistema contra TWAP y VWAP (15 de noviembre)

**Quién:** PS, con apoyo de Claude Code. **Plan registrado antes de las 90 corridas:** `docs/plan_analisis_3_2_3_PS.md`.
**Datos:** las 90 corridas consolidadas en la 3.2.2 (`data/colab_resultados/corridas_90/{baja,media,alta}`), que corrieron BF (×4), PS (×1) y MR (×0,25).
**Salidas:**
- `data/analysis/3_2_3/`: costo sin ajustar, que es el principal;
- `data/analysis/3_2_3_ajustado/`: 30 bps por acción no ejecutada.

**Nombres de los escenarios:** desde el C-6c (`docs/c6c_confirmacion_v3_BF.md`) se informan como profundidad del market maker: ×4 (archivos `baja`), ×1 (`media`) y ×0,25 (`alta`). Para eso se cambiaron los rótulos de `scripts/comparacion_estadistica_3_2_3.py`; los cálculos no cambian.

## 1. Respuesta a la pregunta principal

**¿El sistema cuesta menos que TWAP?**
- En las 90 corridas pareadas, el sistema costó en promedio **3,34 bps menos que TWAP** (IC 95 % [−15,69; 9,67]). La diferencia **no es estadísticamente significativa**: Wilcoxon p = 0,386.
- Contra VWAP: **−3,14 bps** [−17,50; 11,87], p = 0,393.

**Cómo se calculó:**
- **Diferencia:** costo del sistema − costo de la referencia, en bps, por cada corrida. Se pareó por escenario, orden y semilla: el mismo día simulado para las tres estrategias.
- **Prueba principal:** Wilcoxon de rangos con signo, pareado y bilateral, con α = 0,05.
  - Se ordenan las 90 diferencias por su tamaño absoluto.
  - Se suman los rangos de las negativas y los de las positivas.
  - El p es la probabilidad de un desequilibrio igual o mayor si no hubiera diferencia.
- **Complemento:** t pareado. Se puede usar porque Shapiro-Wilk no rechaza la normalidad (p = 0,286).
- **IC 95 %:** bootstrap pareado de 3.000 remuestreos, por percentil.
- **d de Cohen pareado:** media de las diferencias dividida por su desviación.
- **r:** correlación biserial de rangos.

| Referencia | n | Dif. media | IC 95 % | Shapiro p | Wilcoxon p | t p | d de Cohen | r | Gana el sistema |
|---|---|---|---|---|---|---|---|---|---|
| **TWAP** | 90 | **−3,34** | [−15,69; 9,67] | 0,286 | **0,386** | 0,621 | −0,05 | −0,11 | 46/90 |
| **VWAP** | 90 | **−3,14** | [−17,50; 11,87] | 0,165 | **0,393** | 0,684 | −0,04 | −0,10 | 48/90 |

**Costo medio (bps):** sistema 58,61; TWAP 61,95; VWAP 61,75.

**Lectura:**
- La reducción medida es pequeña (−5,4 % frente a TWAP), con un efecto despreciable (d = −0,05).
- El intervalo es compatible tanto con un ahorro de ≈ 16 bps como con un sobrecosto de ≈ 10 bps.
- El plan anticipaba esto: con una ventaja real menor que la de la 3.1.3, era probable que no saliera significativo (sección 5 del plan).

## 2. Preguntas secundarias

### 2.1 ¿El sistema gana en cada profundidad?

Wilcoxon por escenario (n = 30 cada uno), con corrección de Holm para 3 comparaciones: se multiplica el p más chico por 3, el siguiente por 2 y el último por 1, manteniendo el orden.

| Profundidad | Ref. | Dif. media | IC 95 % | Shapiro p | Wilcoxon p | p (Holm) | d | Gana el sistema |
|---|---|---|---|---|---|---|---|---|
| ×4 | TWAP | −10,53 | [−33,09; 11,79] | 0,929 | 0,440 | 1,000 | −0,16 | 15/30 |
| ×1 | TWAP | −3,37 | [−26,15; 19,63] | 0,896 | 0,626 | 1,000 | −0,05 | 16/30 |
| ×0,25 | TWAP | +3,87 | [−16,56; 25,30] | 0,010 | 0,871 | 1,000 | 0,06 | 15/30 |
| ×4 | VWAP | −9,64 | [−33,76; 14,52] | 0,846 | 0,404 | 1,000 | −0,14 | 16/30 |
| ×1 | VWAP | −4,19 | [−30,31; 22,11] | 0,842 | 0,612 | 1,000 | −0,05 | 17/30 |
| ×0,25 | VWAP | +4,41 | [−20,42; 30,85] | 0,022 | 0,824 | 1,000 | 0,06 | 15/30 |

- No es significativo en ninguna profundidad.
- En ×0,25, Shapiro rechaza la normalidad (p = 0,010 y 0,022), así que ahí solo vale Wilcoxon. De todos modos, es la prueba principal.

### 2.2 ¿La ventaja depende de la profundidad del market maker?

- **Kruskal-Wallis:** compara las diferencias de los tres escenarios por rangos.
  - TWAP: H = 0,14, **p = 0,930**, épsilon² = −0,021;
  - VWAP: H = 0,08, **p = 0,963**.
- **Friedman** (control, con bloques orden × semilla, n = 30 bloques, porque los mismos días se repiten en cada escenario): TWAP p = 0,393; VWAP p = 0,273.
- **Mann-Whitney U por pares:** como el plan indica, solo se interpreta si Kruskal-Wallis sale significativo. Igual se informa: todos los p (Holm) = 1,000 (`tabla_p_valores.md`).
- **Conclusión:** no hay evidencia de que la ventaja cambie con la profundidad. La tendencia descriptiva (−10,5 en ×4, −3,4 en ×1, +3,9 en ×0,25) no es significativa.

## 3. Robustez (registrada en el plan)

| Variante | Ref. | n | Dif. media | IC 95 % | Wilcoxon p |
|---|---|---|---|---|---|
| Sin MO-06 | TWAP | 81 | −3,42 | [−16,97; 10,58] | 0,456 |
| Promedio por orden y semilla (las 90 no son independientes) | TWAP | 30 | −3,34 | [−22,43; 16,72] | 0,641 |
| Costo ajustado (30 bps por acción no ejecutada) | TWAP | 90 | −3,53 | [−15,93; 9,47] | 0,381 |
| Sin MO-06 | VWAP | 81 | −3,70 | [−18,83; 12,44] | 0,419 |
| Promedio por orden y semilla | VWAP | 30 | −3,14 | [−25,01; 19,74] | 0,598 |
| Costo ajustado | VWAP | 90 | −3,06 | [−17,36; 11,88] | 0,397 |

- **Por qué se aplica el costo ajustado:**
  - el sistema queda bajo 95 % de cumplimiento en MO-08, semilla 4 (×0,25: 94,7 %);
  - TWAP y VWAP quedan en 87,1 % en MO-09, semilla 4, en las tres profundidades.
- Con el ajuste, la conclusión no cambia.
- Por eso esos días no se repitieron: con la misma semilla saldrían iguales, por determinismo.

## 4. Análisis adicionales (no registrados en el plan; se informan como exploratorios)

### 4.1 Estabilidad: el sistema varía menos entre días

**Prueba:** Pitman-Morgan, para comparar varianzas en datos pareados.
- En cada corrida se calculan la suma y la resta (sistema ± referencia).
- Si las dos estrategias tuvieran la misma varianza, la correlación entre la suma y la resta sería 0.
- Esa correlación se convierte en t = r·√((n−2)/(1−r²)), con n − 2 grados de libertad.
- **IC de la razón de desviaciones:** bootstrap pareado de 10.000 remuestreos.

| Grupo | Ref. | n | Desv. sistema | Desv. ref. | Razón | IC 95 % razón | p |
|---|---|---|---|---|---|---|---|
| **Total** | TWAP | 90 | 118,8 | 154,6 | **0,77** | [0,69; 0,84] | **4,8·10⁻⁹** |
| **Total** | VWAP | 90 | 118,8 | 160,1 | **0,74** | [0,66; 0,81] | **2,4·10⁻⁹** |
| ×4 | TWAP | 30 | 113,0 | 155,3 | 0,73 | [0,61; 0,85] | 6,5·10⁻⁵ |
| ×1 | TWAP | 30 | 114,8 | 159,4 | 0,72 | [0,60; 0,79] | 4,7·10⁻⁵ |
| ×0,25 | TWAP | 30 | 130,8 | 153,5 | 0,85 | [0,69; 0,97] | 0,038 |

**Lectura:** el costo del sistema varía entre un 15 % y un 28 % menos que el de TWAP. La diferencia es significativa en el total y en cada profundidad. Es la misma conclusión que en la 3.1.3, ahora con 90 corridas.

**Corrección menor a la 3.2.2:** en `docs/corridas_90_alta_resultado_MR.md`, la desviación de TWAP y VWAP en ×0,25 figura como 143,58 y 144,32. Los datos (`alta/tabla/corridas.csv`) dan 153,53 y 160,84. La del sistema (130,84) coincide. No afecta ninguna prueba.

### 4.2 De dónde viene la diferencia

Resultado del control en ×1 (`docs/control_reglas_3_2_3_resultado_PS.md`):
- **Ejecutores** (regla uniforme − TWAP): −15,37 bps [−20,35; −10,32], Wilcoxon p (Holm) = 7,0·10⁻⁶, d = −1,08.
- **Calendario del Maestro:** +12,00 bps, p (Holm) = 1,000.
- **Lectura:** el Maestro del Sprint 6 compensa con su calendario lo que ahorran los Ejecutores.
- El **Maestro v2** (`docs/maestro_v2_resultado_PS.md`) da casi el mismo costo que el original: −0,85 bps, p = 0,855.

## 5. Conclusión para el informe (capítulo 7)

> En las 90 corridas pareadas (3 profundidades del market maker × 10 meta-órdenes × 3 semillas), el sistema jerárquico redujo el implementation shortfall en 3,34 bps frente a TWAP (IC 95 % [−15,69; 9,67]; Wilcoxon p = 0,386) y en 3,14 bps frente a VWAP (p = 0,393). La reducción no es estadísticamente significativa y no depende de la profundidad (Kruskal-Wallis p = 0,930). El sistema sí fue significativamente más estable: su desviación entre días fue un 23 % menor que la de TWAP (Pitman-Morgan p = 4,8·10⁻⁹, análisis exploratorio). El control en profundidad ×1 muestra que la capa de Ejecutores reduce el costo 15,4 bps frente a TWAP (p Holm = 7·10⁻⁶), mientras que el calendario aprendido por el Maestro no aporta.

**Límites que se declaran:**
1. El TWAP de referencia compra con órdenes a mercado y los Ejecutores usan órdenes límite.
2. Los escenarios no son liquidez validada, sino profundidad del market maker (C-6c).
3. El Maestro se entrenó en Poisson y se evalúa en ABIDES.
4. Las 90 comparten órdenes y semillas entre escenarios. Eso se controló con el promedio por orden y semilla.

## 6. Cómo reproducir

```
C=data/colab_resultados/corridas_90
python scripts/comparacion_estadistica_3_2_3.py --entradas $C/baja $C/media $C/alta --sistema PPO_sistema --out-dir data/analysis/3_2_3
python scripts/comparacion_estadistica_3_2_3.py --entradas $C/baja $C/media $C/alta --sistema PPO_sistema --penalizacion-bps 30 --out-dir data/analysis/3_2_3_ajustado
```

**Gráficos** (`data/analysis/3_2_3/`, explicados en `docs/guia_graficos.md`):
- `bosque_diferencias.png`;
- `diferencias_por_escenario.png`;
- `qq_diferencias.png`.
