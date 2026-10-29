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

🤖 Generado con [Claude Code](https://claude.com/claude-code)
