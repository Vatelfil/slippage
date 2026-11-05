# C-6c: confirmación de los escenarios v3 (5 de noviembre)

**Responsable:** BF. Corrido en Colab el 5 de noviembre con `notebooks/Colab_C6c_confirmacion_v3_BF.ipynb` (rama `feature/bf-sprint7-cuadernos`, commit `f7670e2`).

**Datos:**
- `data/colab_resultados/c6c_liquidez/c6c_liquidez.json`: la corrida;
- `data/colab_resultados/c6c_liquidez/c6c_confirmacion_v3.json`: el criterio aplicado.

## 1. En una frase

**La v3 NO queda confirmada.**
- El orden de los costos se repite: ×4 > ×1 > ×0,25.
- Pero el escalón entre ×4 y ×1 no excluye el 0 con el criterio fijado.
- Como se acordó, los escenarios se informan como **profundidad del market maker ×4 / ×1 / ×0,25**, sin los nombres «baja», «media» y «alta».

## 2. Qué se corrió

- **Criterio, fijado el 2 de noviembre antes de correr** (`DESVIACIONES_TITULO1_VS_IMPLEMENTACION.md`, sección 10): compra a mercado (`agresiva_market`) de 5.000 acciones, FALABELLA, apertura, ventana de 15 minutos.
- **Semillas:** 60 nuevas, de la 8101 a la 8160, distintas de las del C-6b.
- **Firma del JSON:** coincide con el criterio en entorno, activo, tramo, tamaño, ventana, semillas, factores (×4 / ×1 / ×0,25) y parámetro escalado (`mm_pov`).
- **Cumplimiento:** 1,000 en todas las compras a mercado.
- **Verificación local:** se volvió a aplicar el criterio sobre el JSON del zip con `scripts/confirmar_v3_c6c.py`. Da los mismos números que Colab.

## 3. Resultado con el criterio fijado

| Escenario v3 | `mm_pov` | Costo medio (bps) | Diferencia pareada | Media (bps) | IC 95 % (bootstrap, 10.000) | n | ¿Cumple? |
|---|---:|---:|---|---:|---|---:|:---:|
| baja | ×4 | 25,05 | baja − media | +6,69 | [−2,59; +13,77] | 60 | **no** |
| media | ×1 | 18,36 | media − alta | +7,56 | [+3,07; +14,77] | 60 | sí |
| alta | ×0,25 | 10,81 | | | | | |

**Veredicto: NO CONFIRMADA.**
- Para confirmar se exigían las dos diferencias con un IC sobre 0, y baja − media no lo cumple.
- El veredicto propio de `c6_escenarios_liquidez_bf.py` también da REVISAR.

**TWAP con órdenes límite (informativo, no decide):** baja − media = −0,81 bps [−2,68; +0,98] y media − alta = +0,42 [−1,20; +2,04]. Igual que en el C-6b, no cambia entre escenarios.

### Comparación con el C-6b (semillas 8001–8060, con las que se eligió el orden)

| | ×4 − ×1 | ×1 − ×0,25 |
|---|---|---|
| C-6b | +9,50 [+5,27; +15,22] | +2,90 [+0,67; +5,89] |
| C-6c | +6,69 [−2,59; +13,77] | +7,56 [+3,07; +14,77] |

- Las cuatro medias son positivas: el orden de los costos se repite.
- Lo que no se repite es la precisión del escalón ×4 − ×1.

## 4. Lectura posterior (después de ver los datos; NO cambia el veredicto)

Esta sección se agregó después de ver los resultados. Se informa para explicar el veredicto, no para reemplazarlo (R6).

| Medida (×4 − ×1) | Valor |
|---|---|
| Semillas con diferencia positiva | 47 de 60 |
| Mediana | +6,42 bps |
| Desviación entre semillas | 32,9 bps (en el C-6b, 20,3) |
| Wilcoxon pareado, 60 semillas | p = 1,7·10⁻⁷ |
| Prueba de signos | p = 1,2·10⁻⁵ |

- **Un solo día extremo mueve la media.** En la semilla 8121, comprar a mercado con ×1 costó 222,1 bps, contra 21,4 con ×4 y 41,6 con ×0,25. Esa semilla da −200,8 bps en ×4 − ×1 y +180,5 en ×1 − ×0,25.
- **Sin esa semilla** (59 pares):
  - ×4 − ×1 = +10,20 [+5,44; +15,08];
  - ×1 − ×0,25 = +4,63 [+2,72; +7,31].
- **Lectura:** el orden ×4 > ×1 > ×0,25 aparece en la gran mayoría de los días. Lo que falla es la media, porque el criterio usa la media y esta es sensible a un día extremo.
- **Por qué no cambia el veredicto:** el criterio se fijó con la media, antes de ver los datos. Quitar una semilla, o cambiar a la mediana o a Wilcoxon, después de ver el resultado sería elegir la prueba que da el resultado deseado.

## 5. Qué cambia

1. **Las 90 corridas no se ven afectadas.** Corren con el factor de `mm_pov`, no con el nombre. Los cuadernos y el JSON de la v3 siguen usando las etiquetas `baja`, `media` y `alta` como nombres de archivo.
2. **En el informe, las tablas y la 3.2.3**, los escenarios se nombran «profundidad del market maker ×4 / ×1 / ×0,25».
   - La pregunta «¿la ventaja depende de la liquidez?» del plan de análisis (`docs/plan_analisis_3_2_3_PS.md`) pasa a ser «¿depende de la profundidad del market maker?».
   - Se puede mencionar que, en la compra a mercado, más profundidad del market maker se asoció a un costo mayor en la mayoría de los días (sección 4, análisis posterior), pero no como escenarios de liquidez validados.
3. **Desviación 10:** pasa a «aceptada por BF; no confirmada por el C-6c».
4. **Límite para el informe:** el Título I pide escenarios de liquidez baja, media y alta. Lo que se evalúa es la profundidad del market maker de rmsc04. Calibrar escenarios con días reales del IPSA de baja y alta liquidez queda como trabajo futuro.

## 6. Cómo reproducir

```bash
python scripts/confirmar_v3_c6c.py --entrada data/colab_resultados/c6c_liquidez/c6c_liquidez.json
python -m pytest tests/test_confirmacion_v3.py -q
```

---

Elaborado por BF con apoyo de Claude Code (uso de IA autorizado por la universidad).
