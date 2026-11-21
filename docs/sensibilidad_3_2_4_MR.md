# Análisis de Sensibilidad 3.2.4 (MR, Sprint 8)

**Responsable:** MR (Sprint 8, tarea 3.2.4).  
**Script:** `scripts/sensibilidad_3_2_4_MR.py`.  
**Salidas:** `data/analysis/3_2_4/` (`sensibilidad_3_2_4.json`, `derivadas_tamano.csv`, `derivadas_profundidad.csv`, `sensibilidad_tramo.csv`, y figuras `sensibilidad_{tamano,profundidad,tramo}.png`).  
**Tests:** `tests/test_sensibilidad_3_2_4_MR.py`.  
**Fuente de datos:** `data/analysis/3_2_2/corridas.csv` (450 corridas consolidadas: 90 de profundidad y 60 adicionales del eje de tamaño, todas pareadas por orden y semilla).

---

## 1. Resumen Ejecutivo

1. **Tamaño de la meta-orden (eje en estrella, profundidad ×1, factores 0,5 / 1,0 / 1,5):**
   - El costo crece con el tamaño en las tres estrategias (Friedman $p = 0{,}0017$ en el sistema, $p = 1{,}1\times 10^{-11}$ en TWAP y $p = 3{,}1\times 10^{-10}$ en VWAP).
   - Entre $0{,}5$ y $1{,}5$, la pendiente del sistema es **+13,12 bps por unidad de factor** (IC 95 % $[+0{,}27; +26{,}22]$), menor que la de TWAP (**+23,20 bps**, $[+18{,}22; +27{,}55]$) y VWAP (**+24,06 bps**, $[+18{,}42; +29{,}21]$).
   - **Prueba de tendencia en la ventaja (Sistema − TWAP):** el test pareado de **Friedman** ($n = 30$ días bloqueados en los 3 tamaños) detecta un cambio estadísticamente significativo en la diferencia ($Q = 6{,}47$, **$p = 0{,}0394$**; contra VWAP: $Q = 6{,}07$, **$p = 0{,}0482$**). La ventaja media pasa de $+2{,}20$ a $-3{,}37$ y $-7{,}88\text{ bps}$. En contraste, la correlación de Spearman sin bloqueo ($n = 90$) no alcanza significancia ($\rho = -0{,}049$, $p = 0{,}648$) porque la variabilidad intrínseca de la dirección del mercado entre días eclipsa el efecto del tamaño.
   - **Robustez:** con costo ajustado (+30 bps) Friedman mantiene $p = 0{,}0394$; excluyendo los 5 días con cumplimiento $< 95\%$ ($n = 25$ días completos), Friedman sigue siendo significativo frente a TWAP ($Q = 6{,}08$, $p = 0{,}0478$).

2. **Profundidad del market maker (×0,25 / ×1 / ×4 en tamaño 1,0):**
   - La ventaja del sistema frente a TWAP no depende de forma significativa de la profundidad del market maker: **Kruskal-Wallis** $H = 0{,}145$, **$p = 0{,}930$**; **Friedman** $Q = 1{,}87$, **$p = 0{,}393$**; Spearman $\rho = -0{,}040$, $p = 0{,}706$.

3. **Tramo horario de inicio (90 corridas en tamaño 1,0):**
   - La diferencia Sistema − TWAP sí depende del tramo de inicio (**Kruskal-Wallis** $H = 8{,}98$, **$p = 0{,}0112$**).
   - En el **cierre** ($n = 27$), el sistema ahorra **$-34{,}78\text{ bps}$** frente a TWAP (IC 95 % $[-55{,}45; -15{,}54]$, Wilcoxon $p_{\text{Holm}} = 0{,}0089$), mientras que en **apertura** ($+14{,}77\text{ bps}$, $p_{\text{Holm}} = 0{,}600$) y **media jornada** ($+3{,}94\text{ bps}$, $p_{\text{Holm}} = 0{,}953$) no hay ventaja significativa. Como se advirtió en la 3.2.2, tramo y activo están confundidos (las órdenes de cierre son de FALABELLA).

4. **Volatilidad y spread (límite declarado):**
   - No se variaron como parámetros independientes en ABIDES; la profundidad del market maker (`mm_pov`) modifica indirectamente el spread cotizado.

---

## 2. Sensibilidad al Tamaño de Orden (Profundidad ×1)

**Diseño:** Mismas 10 meta-órdenes × semillas 4–6 ($n = 30$ días por nivel) evaluadas en factor $0{,}5$ (BF), $1{,}0$ (PS) y $1{,}5$ (MR).

### 2.1 Derivadas numéricas ($\partial \text{IS} / \partial \text{factor}$)

| Serie | Tramo | $\Delta \text{IS}$ medio (bps) | IC 95 % bootstrap | Pendiente (bps / +1,0 factor) | IC 95 % pendiente | Wilcoxon $p$ |
|---|---|---|---|---|---|---|
| **Sistema PPO** | $0{,}5 \to 1{,}0$ | $+8{,}48$ | $[+3{,}57; +12{,}96]$ | $+16{,}96$ | $[+7{,}14; +25{,}92]$ | $7{,}3\times 10^{-4}$ |
| **Sistema PPO** | $1{,}0 \to 1{,}5$ | $+4{,}64$ | $[-6{,}39; +15{,}92]$ | $+9{,}27$ | $[-12{,}78; +31{,}85]$ | $0{,}465$ |
| **Sistema PPO** | **$0{,}5 \to 1{,}5$** | **$+13{,}12$** | **$[+0{,}27; +26{,}22]$** | **$+13{,}12$** | **$[+0{,}27; +26{,}22]$** | **$0{,}052$** |
| **TWAP** | $0{,}5 \to 1{,}0$ | $+14{,}04$ | $[+10{,}69; +16{,}95]$ | $+28{,}09$ | $[+21{,}38; +33{,}90]$ | $1{,}4\times 10^{-6}$ |
| **TWAP** | $1{,}0 \to 1{,}5$ | $+9{,}15$ | $[+7{,}10; +11{,}24]$ | $+18{,}31$ | $[+14{,}20; +22{,}48]$ | $8{,}0\times 10^{-8}$ |
| **TWAP** | **$0{,}5 \to 1{,}5$** | **$+23{,}20$** | **$[+18{,}22; +27{,}55]$** | **$+23{,}20$** | **$[+18{,}22; +27{,}55]$** | **$3{,}9\times 10^{-7}$** |
| **VWAP** | $0{,}5 \to 1{,}5$ | $+24{,}06$ | $[+18{,}42; +29{,}21]$ | $+24{,}06$ | $[+18{,}42; +29{,}21]$ | $3{,}1\times 10^{-7}$ |
| **Sistema − TWAP** | $0{,}5 \to 1{,}0$ | $-5{,}57$ | $[-11{,}77; +0{,}26]$ | $-11{,}13$ | $[-23{,}54; +0{,}51]$ | $0{,}080$ |
| **Sistema − TWAP** | $1{,}0 \to 1{,}5$ | $-4{,}52$ | $[-15{,}53; +6{,}30]$ | $-9{,}03$ | $[-31{,}06; +12{,}61]$ | $0{,}360$ |
| **Sistema − TWAP** | **$0{,}5 \to 1{,}5$** | **$-10{,}08$** | **$[-23{,}66; +3{,}11]$** | **$-10{,}08$** | **$[-23{,}66; +3{,}11]$** | **$0{,}164$** |
| **Sistema − VWAP** | $0{,}5 \to 1{,}5$ | $-10{,}95$ | $[-25{,}02; +2{,}69]$ | $-10{,}95$ | $[-25{,}02; +2{,}69]$ | $0{,}096$ |

### 2.2 Pruebas formales de tendencia y robustez

| Serie / Variante | $n$ bloques | Friedman $Q$ | Friedman $p$ | Spearman $\rho$ ($n$) | Spearman $p$ |
|---|---|---|---|---|---|
| **Sistema − TWAP (crudo)** | 30 | $6{,}47$ | **$0{,}0394$** | $-0{,}049$ ($90$) | $0{,}648$ |
| **Sistema − VWAP (crudo)** | 30 | $6{,}07$ | **$0{,}0482$** | $-0{,}049$ ($90$) | $0{,}645$ |
| **Sistema − TWAP (ajustado +30 bps)** | 30 | $6{,}47$ | **$0{,}0394$** | $-0{,}049$ ($90$) | $0{,}648$ |
| **Sistema − TWAP (solo cumpl. $\ge 95\%$)** | 25 | $6{,}08$ | **$0{,}0478$** | $-0{,}064$ ($75$) | $0{,}585$ |
| **Sistema − VWAP (solo cumpl. $\ge 95\%$)** | 25 | $5{,}36$ | $0{,}0686$ | $-0{,}062$ ($75$) | $0{,}598$ |

* **Interpretación técnica:** El análisis por bloques pareados (Friedman) es el test adecuado porque las tres condiciones comparten exactamente los mismos 30 días simulados. Muestra que la ventaja relativa del sistema frente a TWAP cambia de manera estadísticamente significativa al variar el tamaño ($p = 0{,}0394$), pasando de una ligera desventaja en órdenes pequeñas ($+2{,}20\text{ bps}$ en $0{,}5$) a un ahorro creciente en órdenes grandes ($-7{,}88\text{ bps}$ en $1{,}5$), manteniéndose la significancia incluso al excluir los 5 días con cumplimiento bajo $95\%$ ($p = 0{,}0478$).

Figura: `data/analysis/3_2_4/sensibilidad_tamano.png`.

---

## 3. Sensibilidad a la Profundidad del Market Maker (Tamaño 1,0)

**Diseño:** Mismas 10 meta-órdenes × semillas 4–6 ($n = 30$ días por nivel) en `mm_pov` $\times 0{,}25$ (MR), $\times 1$ (PS) y $\times 4$ (BF). Cada paso cuadruplica la profundidad ($\Delta \log_2 = 2$).

| Serie | Transición | $\Delta \text{IS}$ medio (bps) | IC 95 % bootstrap | Pendiente (bps / $\times 2$ prof.) | Wilcoxon $p$ |
|---|---|---|---|---|---|
| **Sistema PPO** | $\times 0{,}25 \to \times 1$ | $-22{,}08$ | $[-46{,}93; +1{,}44]$ | $-11{,}04$ | $0{,}253$ |
| **Sistema PPO** | $\times 1 \to \times 4$ | $+12{,}40$ | $[-2{,}88; +28{,}17]$ | $+6{,}20$ | $0{,}245$ |
| **Sistema PPO** | $\times 0{,}25 \to \times 4$ | $-9{,}68$ | $[-25{,}06; +5{,}17]$ | $-2{,}42$ | $0{,}404$ |
| **TWAP** | $\times 0{,}25 \to \times 4$ | $+4{,}72$ | $[-18{,}87; +26{,}90]$ | $+1{,}18$ | $0{,}641$ |
| **Sistema − TWAP** | $\times 0{,}25 \to \times 4$ | $-14{,}40$ | $[-35{,}28; +4{,}96]$ | $-3{,}60$ | $0{,}299$ |
| **Sistema − VWAP** | $\times 0{,}25 \to \times 4$ | $-14{,}04$ | $[-36{,}52; +7{,}80]$ | $-3{,}51$ | $0{,}237$ |

* **Pruebas globales en Sistema − TWAP:** Kruskal-Wallis $H = 0{,}145$ ($p = 0{,}930$), Friedman $Q = 1{,}87$ ($p = 0{,}393$), Spearman $\rho = -0{,}040$ ($p = 0{,}706$). No hay evidencia de sensibilidad de la ventaja del sistema frente a la profundidad del market maker.

Figura: `data/analysis/3_2_4/sensibilidad_profundidad.png`.

---

## 4. Sensibilidad al Tramo Horario de Inicio (90 Corridas, Tamaño 1,0)

| Tramo | $n$ | Sistema − TWAP (bps) | Mediana (bps) | IC 95 % bootstrap | Wilcoxon $p$ | $p$ Holm (3 tramos) |
|---|---|---|---|---|---|---|
| **Apertura** | 36 | $+14{,}77$ | $+10{,}73$ | $[-3{,}43; +33{,}50]$ | $0{,}300$ | $0{,}600$ |
| **Media jornada** | 27 | $+3{,}94$ | $+16{,}72$ | $[-21{,}98; +30{,}21]$ | $0{,}953$ | $0{,}953$ |
| **Cierre** | 27 | **$-34{,}78$** | **$-37{,}99$** | **$[-55{,}45; -15{,}54]$** | **$0{,}0030$** | **$0{,}0089$** |

* **Kruskal-Wallis entre tramos:** $H = 8{,}98$, **$p = 0{,}0112$** (tanto frente a TWAP como frente a VWAP). Se confirma exactamente el resultado exploratorio previo de la sección 8.6.2 de PS.

Figura: `data/analysis/3_2_4/sensibilidad_tramo.png`.

---

## 5. Límites Metodológicos Declarados

1. **Extrapolación de tamaño:** El Maestro fue entrenado únicamente con tamaño factor $1{,}0$ ($10\%$ del día; $5\%$ en cierre), por lo que los factores $0{,}5$ y $1{,}5$ están fuera de su distribución de entrenamiento (desviación 12).
2. **Sin interacción tamaño × profundidad:** El diseño en estrella no evalúa tamaños $0{,}5$ ni $1{,}5$ en profundidades $\times 0{,}25$ o $\times 4$.
3. **Volatilidad y spread:** No fueron variados de forma independiente en ABIDES; su análisis queda acotado a la variación indirecta provocada por `mm_pov`.
4. **Confusión tramo–activo:** Las tres órdenes de cierre (MO-08 a MO-10) pertenecen exclusivamente a FALABELLA.
