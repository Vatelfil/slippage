# Decisiones de BF para la Sprint Review del 6 de noviembre

**Fecha:** 2 de noviembre de 2026. **Decide:** BF. La última es una propuesta que decide el equipo.

| # | Decisión | Respuesta | Estado |
|---|---|---|---|
| 1 | D1: tamaño de las meta-órdenes | **v2** | Decidida (ratifica la del 22 oct) |
| 2 | D3: riesgo de R_E sobre lo ejecutado (0) o lo pendiente (A) | **0** | Decidida por la regla del 29 oct |
| 3 | Escenarios de liquidez v3 (desviación 10) | **Aceptada**, con la confirmación C-6c | **C-6c (5 nov): NO CONFIRMADA.** Se informa como profundidad del market maker ×4 / ×1 / ×0,25 (`docs/c6c_confirmacion_v3_BF.md`) |
| 4 | Factor tamaño en las 90 corridas (desviación 12) | **Diseño en estrella** | Propuesta: la decide el equipo el 6 nov |

## 1. D1 = v2

- **Qué es:** cada orden es el 10 % del volumen del día simulado de su activo; si parte en el cierre, el 5 %.
- **Evidencia:** con TWAP en ABIDES (2.3.4, 2 semillas por orden), la v2 deja 10 de 10 órdenes ejecutables y 19 de 20 corridas sobre el 95 %. MO-10 queda en el borde (90,2 % y 100 %).
- **Por qué no rehace nada:** la candidata de PS, que usaron la 3.1.3 y las 90 corridas, coincide con la v2 oficial en los seis campos que leen los evaluadores. La firma de las corridas no depende del archivo (`docs/meta_ordenes_2.3.3.md`, sección 8).

| Alternativa descartada | Por qué | Costo de elegirla |
|---|---|---|
| v1 (100 000 acciones fijas) | TWAP completa solo 5 de las 10 órdenes: se compararían costos de órdenes que nadie termina | Repetir la 3.1.3 y las 90 corridas |

## 2. D3 = 0

- **Regla, fijada el 29 de octubre antes de ver los datos corregidos** (`docs/revision_opus_PS.md`, sección 6): la opción A reemplaza a la 0 solo si cumple dos condiciones:
  - (a) completa la orden con argmax en más redes;
  - (b) no cuesta más de +1 bps (límite superior del IC).
- **Resultado con la recompensa corregida**, misma semilla de red, 300 semillas de evaluación (`docs/reeval_300_mid_resultado_PS.md`):
  - las dos opciones completan el 100 % con argmax, así que (a) no se cumple;
  - A − 0 = **−0,60 bps [−1,04; −0,16]**.
- **BF retira su propuesta del 22 de octubre** de pasar a la A. La sostenía un cumplimiento con argmax de 0,000 / 1,000 / 0,904, medido con la recompensa con falla H1.
- **El −0,60 bps no aplica al sistema final.** Se midió en redes con `mid_decision`. El Ejecutor elegido (`rimit__d3_opcion0_s1000`, 5,68 bps en 300 semillas, cumplimiento 1,000) es imitación + PPO con la recompensa de llegada, y la opción A nunca se probó así.

| Alternativa descartada | Costo de elegirla |
|---|---|
| Opción A | En cadena, porque el Maestro se entrenó con el Ejecutor elegido:<br>1. recalcular β\* y la fase 2 por tramo (≈ 1–2 h de apertura, ≈ 47 min de media jornada y ≈ 108 min de cierre);<br>2. reentrenar el Ejecutor con imitación y la A (≈ 35 min por red, al menos 2 redes);<br>3. reevaluar con 300 semillas (≈ 70 min) y volver a elegir;<br>4. reentrenar el Maestro;<br>5. repetir la 3.1.3, la liquidez media (2 × 3 h) y el control de PS (2 × 2 h).<br>**Más de 10 h de Colab a seis semanas del examen**, para ganar como mucho 0,6 bps frente a ≈ 40 bps de dispersión entre jornadas. Además agrega una desviación del Título I |

**Qué se declara (R6):** la regla original se aplicó sobre evidencia inválida (H1). Se reemplazó por una regla fijada antes de los datos corregidos.

## 3. Escenarios v3: aceptados con confirmación

- **Qué es:** solo se escala `mm_pov`, y cada escenario se nombra según cuánto cuesta barrer el libro:
  - baja = ×4;
  - media = ×1;
  - alta = ×0,25.

  Es la misma idea de las medidas de iliquidez por impacto en el precio (Kyle, Amihud).
- **Evidencia del C-6b:** comprar 5.000 acciones a mercado (60 semillas desde la 8001) cuesta 11,75 bps con ×0,25, 14,65 con ×1 y 24,15 con ×4.
- **Debilidades:**
  1. el orden se eligió mirando ese resultado;
  2. la confirmación prevista con las semillas de las 90 no existe, porque esos cuadernos no corren la compra a mercado;
  3. es contraintuitivo: más market maker da más costo, y en la calibración subir `mm_pov` duplicaba el volumen.
- **Confirmación C-6c, criterio fijado hoy antes de correr:**
  - mismo script del C-6b, con la v3 y 60 semillas nuevas (8101–8160);
  - **CONFIRMADA** si baja − media > 0 **y** media − alta > 0, las dos con IC 95 % bootstrap pareado (10.000 remuestreos) que excluya el 0;
  - si no se cumple, los escenarios se informan como «profundidad del market maker ×4 / ×1 / ×0,25», sin nombres de liquidez;
  - lo verifica `scripts/confirmar_v3_c6c.py`. El veredicto del script de PS no sirve: en media − alta solo pide que la media sea ≥ 0.
- **No bloquea nada:** las corridas dependen del factor, no del nombre. La liquidez baja se corre en paralelo.

| Alternativa descartada | Costo |
|---|---|
| Calibrar los escenarios con días reales del IPSA de baja y alta liquidez | Elegir días, recalibrar rmsc04 y volver a validar (2.2.4/2.2.5). No cabe antes de las 90 |
| Rechazar la v3 y quedarse con la v2 (baja = ×0,25) | El C-6b mostró lo contrario: la «baja» costaría menos que la «media» |

## 4. Factor tamaño: propuesta de diseño en estrella

- **Qué pasa:**
  - el Título I §7.1 pide **3 liquideces × 3 tamaños × 10 semillas**;
  - se corre **3 liquideces × 10 órdenes × 3 semillas**, con `factor_tamano` = 1 en todas;
  - la **3.2.4 por tamaño se queda sin datos**.
- **Propuesta:** agregar la liquidez media con `--factor-tamano 0.5` y `1.5`, con las mismas 10 órdenes y semillas 4–6. Junto con la media ×1 de PS quedan:
  - un eje de tamaño (5 % / 10 % / 15 % del día; en el cierre, 2,5 / 5 / 7,5 %);
  - un eje de liquidez (baja / media / alta con ×1).

  Son 4 cuadernos de ≈ 3 h (`notebooks/Colab_tamanos_media_BF.ipynb`). BF corre el 0,5; el 1,5, quien tenga Colab libre.
- **Lo que hay que declarar:**
  - el Maestro se entrenó con un solo tamaño (10 % y 5 % del día, en Poisson), así que 0,5 y 1,5 quedan fuera de lo que vio y 1,5 es una extrapolación;
  - con ×1,5, las órdenes de cierre son el 23 % de lo que queda del día y es probable que TWAP no complete alguna: se informa también el costo ajustado (`--penalizacion-bps 30`);
  - se propone después de ver la liquidez media, aunque no usa esos resultados.

| Alternativa | Costo | Qué deja |
|---|---|---|
| Mínima: declarar la desviación 12 y nada más | 0 | La 3.2.4 solo por tramo y por liquidez; la pregunta queda abierta ante la comisión |
| Factorial completo 3 × 3 | ≈ 12 cuadernos más (≈ 36 h) | Interacción tamaño × liquidez. No cabe en el Sprint 7 |

**Se pide al equipo:** aprobar o rechazar el diseño en estrella y decidir quién corre el 1,5.

---

Elaborado por BF con apoyo de Claude Code (uso de IA autorizado por la universidad).
