# Maestro: primera prueba en ABIDES (cuaderno `Colab_Maestro_MR`)

**Elaborado por:** PS con apoyo de Claude Code, 29 de octubre de 2026. **Datos:** `data/colab_resultados/maestro_impacto/`.

## Qué se corrió

- **Entrenamiento:** Maestro entrenado en Poisson, 1.000 jornadas, λ = 0,05, impacto acumulado, Ejecutores fijos sin entrenar. Se reprodujo lo del PC: el cumplimiento pasa de 0,963 a 0,999 y R_M mejora en 15,2 bps (IC +10,1 a +21,9). El Maestro aprende a comprar rápido (α medio 8 de 9).
- **Evaluación:** en ABIDES con el mismo impacto, 2 meta-órdenes (MO-01 y MO-02) × 2 semillas, comparando con el mismo Maestro sin entrenar y con TWAP/VWAP.

## Resultado

| Estrategia | Costo medio (bps) | Rango | Cumplimiento |
|---|---:|---|---:|
| Maestro entrenado | 54,3 | 20,8 a 109,3 | 1,00 |
| Maestro sin entrenar | 45,0 | −11,3 a 121,7 | 0,97 |
| TWAP | 57,8 | −17,0 a 128,7 | 1,00 |
| VWAP | 62,0 | −26,2 a 144,7 | 0,99 |

Maestro entrenado − TWAP: **−3,4 bps, IC 95 % de −43,7 a +36,9** (4 pares). No se distingue.

## Lectura

- **El camino completo funciona en ABIDES:** entrenamiento, carga de redes, impacto, evaluación y tabla.
- **El resultado de cada jornada lo decide hacia dónde se movió el precio ese día** (inferido de las 4 corridas):
  - En MO-02 el precio subió y comprar rápido le ganó a TWAP (68 y 19 bps).
  - En MO-01 bajó y perdió (43 y 30 bps).
- **La desviación entre jornadas es ≈ 40 bps.** Con 30 corridas el IC quedará en ≈ ±15 bps, así que solo se verán diferencias grandes. Hay que decirlo así en el informe.
- **Para el sistema final** se usa λ = 0,02. Con 30 jornadas en Poisson fue el único λ que empató con TWAP (`docs/maestro_primer_entrenamiento_PS.md`), una evidencia más confiable que estas 4 corridas.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
