# C-6: resultado en ABIDES y cambio a la v2 de los escenarios (29 de octubre)

**Elaborado por:** PS con apoyo de Claude Code (borrador para BF). **Datos:** `data/colab_resultados/c6_liquidez/c6_liquidez.json`. La corrida usó 30 semillas, FALABELLA, apertura y ventana de 15 minutos.

## 1. Resultado con la v1 (se escalan agentes de ruido, de valor y market maker: 0,5×, 1×, 2×)

Veredicto: **REVISAR**.

| Heurística | Acciones | Baja | Media | Alta | Baja − media (IC 95 %) | Media − alta (IC 95 %) |
|---|---:|---:|---:|---:|---|---|
| Todo a mercado | 1.000 | 8,70 | 8,17 | 9,00 | +0,53 [−4,38; +5,05] | −0,84 [−9,63; +6,37] |
| Todo a mercado | 5.000 | 14,55 | 12,72 | 14,94 | +1,83 [−4,61; +7,92] | −2,22 [−11,00; +6,01] |
| TWAP con límite | 1.000 | 5,98 | −1,90 | 0,51 | +7,88 [+0,72; +13,90] | −2,41 [−9,70; +4,62] |
| TWAP con límite | 5.000 | 10,84 | 3,83 | 1,49 | +7,01 [+0,06; +13,36] | +2,34 [−6,10; +10,52] |

(Slippage medio en bps.)

## 2. Lectura

- **Comprar a mercado no cambia entre escenarios**, que era el criterio fijado para el veredicto.
- **TWAP con órdenes límite sí cambia:** con liquidez baja cuesta ≈ 7–8 bps más, porque las órdenes pasivas encuentran menos contraparte.
- **Los intervalos son muy anchos (±5 a ±10 bps).** Al cambiar la cantidad de agentes, la misma semilla deja de ser el mismo mercado, así que el pareo no reduce el ruido. Esto es inferido del código y del ancho de los intervalos.
- **Escalar los agentes de ruido y de valor también cambia cuánto se mueve el precio:** se mezcla liquidez con volatilidad (inferido).
- **Corrección:** el criterio (comprar a mercado) se eligió con lo que se vio en Poisson, donde esa es la heurística sensible. En ABIDES no resultó así.

## 3. Qué se cambió (v2)

- **Qué se escala:** solo `mm_pov`, el tamaño de las cotizaciones del market maker de rmsc04. Cambia la profundidad del libro sin tocar a los demás agentes, así que la misma semilla sigue siendo comparable.
- **Factores:** 0,25×, 1× y 4×, más separados para que el efecto se vea.
- **Semillas:** 60.
- **Criterio, fijado antes de correr:** comprar 5.000 acciones a mercado, que barre varios niveles y es lo que más depende de la profundidad.
- **Dónde queda:** `data/scenarios/escenarios_liquidez_v2.json` (con `claves_abides` y `criterio_c6`), y el cuaderno `notebooks/Colab_C6b_liquidez_mm_BF.ipynb` (≈ 1 h 20 min).
- **Uso:** los evaluadores aceptan `--escenarios-json data/scenarios/escenarios_liquidez_v2.json`.
- **Si el C-6b da REVISAR:** se define la liquidez por el costo de las órdenes pasivas (lo que la v1 sí distinguió), o se calibran escenarios con días reales del IPSA.

## 4. Resultado del C-6b con la v2 (30 de octubre)

**Datos:** `data/colab_resultados/c6b_liquidez/c6b_liquidez.json` (60 semillas, desde la 8001). Se escala solo `mm_pov`: 0,25×, 1× y 4×. Veredicto del script con el criterio fijado: **REVISAR**.

| Heurística | Acciones | mm_pov ×0,25 | ×1 | ×4 | ×0,25 − ×1 (IC 95 %) | ×1 − ×4 (IC 95 %) |
|---|---:|---:|---:|---:|---|---|
| Todo a mercado | 1.000 | 6,31 | 7,58 | 10,57 | −1,27 [−2,54; −0,43] | −2,99 [−5,18; −1,39] |
| **Todo a mercado (criterio)** | **5.000** | **11,75** | **14,65** | **24,15** | **−2,90 [−5,95; −0,68]** | **−9,50 [−15,24; −5,29]** |
| TWAP con límite | 1.000 | 2,44 | 2,80 | 1,14 | −0,36 [−1,73; +0,97] | +1,65 [−0,26; +3,83] |
| TWAP con límite | 5.000 | 7,68 | 6,89 | 6,52 | +0,79 [−0,74; +2,38] | +0,37 [−1,44; +2,23] |

### Lectura

- **El pareo por semilla ahora funciona.** Los intervalos bajaron de ±5–10 bps (v1) a ±1–5 bps. Escalar solo al market maker deja comparable el mismo mercado.
- **El efecto es claro y va en un solo sentido, pero al revés de lo esperado.** Con más `mm_pov`, comprar a mercado cuesta **más**: 11,7 → 14,7 → 24,2 bps con 5.000 acciones. El veredicto es REVISAR porque la v2 suponía que más `mm_pov` era más liquidez.
- **Por qué pasa (inferido, no medido):** en rmsc04 el market maker pone en cada nivel una fracción del volumen del último minuto. Con más `mm_pov`, el market maker negocia más y su cotización sigue más de cerca al precio. Eso puede hacer que el precio reaccione más a una compra grande. En la calibración (`docs/calibracion_rmsc04_2.2.4_BF.md`, §8.1), subir `mm_pov` también duplicaba el volumen.
- **TWAP con órdenes límite casi no cambia entre escenarios** (todos los IC incluyen el 0).

### Qué se propone (v3, borrador para BF)

`data/scenarios/escenarios_liquidez_v3.json`: los **mismos factores**, con los nombres puestos según el costo medido. Baja liquidez = `mm_pov` ×4 (comprar a mercado es más caro), media = ×1 y alta = ×0,25.

- **Por qué es válido:** la liquidez se define por cuánto cuesta barrer el libro, igual que las medidas de iliquidez por impacto en el precio (Kyle, Amihud). No se define por el parámetro interno del simulador.
- **Límite:** el orden se eligió mirando este resultado. Hay que declararlo y confirmarlo con otras semillas: las 90 corridas del Sprint 7 usan semillas distintas, y la heurística a mercado se corre ahí también.
- **Alternativa,** si BF no la acepta: calibrar los escenarios con días reales del IPSA de baja y alta liquidez.
- **Uso:** `--escenarios-json data/scenarios/escenarios_liquidez_v3.json`.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
