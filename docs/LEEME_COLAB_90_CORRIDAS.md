# Cuadernos de las 90 corridas (3.2.1, Sprint 7)

**Preparados por:** PS, con apoyo de Claude Code, el 31 de octubre de 2026. Preparar los cuadernos es la parte de PS en la 3.2.1.

**Antes de correrlos** hay que confirmar en la reunión dos cosas:
- **Escenarios v3:** los decide BF.
- **Semillas 4, 5 y 6:** las deciden los tres.

Si se decide otra cosa, se cambia **un solo valor** en la celda 10 de cada cuaderno.

## Qué hay

| Cuaderno | Quién lo corre | Qué corre | Duración |
|---|---|---|---|
| `Colab_90corridas_prueba.ipynb` | PS (lunes 9) | MO-01, semilla 4, en las tres liquideces: sistema, TWAP y VWAP (9 corridas). Solo comprueba que todo funciona | ≈ 25 min |
| `Colab_90corridas_baja_A` y `_B` | BF | Liquidez baja (`mm_pov` ×4) | ≈ 3 h cada uno, en paralelo |
| `Colab_90corridas_media_A` y `_B` | PS | Liquidez media (la calibración actual) | ≈ 3 h cada uno, en paralelo |
| `Colab_90corridas_alta_A` y `_B` | MR | Liquidez alta (`mm_pov` ×0,25) | ≈ 3 h cada uno, en paralelo |

**Partes:** A corre MO-01 a MO-05 y B corre MO-06 a MO-10, cada una con 3 semillas. Cada parte son 15 corridas del sistema y 30 de TWAP y VWAP.

**Total:** 3 escenarios × 10 órdenes × 3 semillas = **90 corridas por estrategia**.

## Configuración, igual en todos

- **Sistema final:** Maestro y Ejecutores de `sistema_final/maestro/` en Drive, los mismos de la 3.1.3.
- **Opciones:** `--modo muestreo`, `--impacto` y `--completar-al-cierre`.
- **TWAP y VWAP:** mismas órdenes, semillas, escenario e impacto.
- **Escenarios:** `data/scenarios/escenarios_liquidez_v3.json`.
- **Semillas 4, 5 y 6** (`--semilla-inicial 4`):
  - Son distintas de las de la 3.1.3 (1, 2 y 3), así que las 90 son datos nuevos.
  - Con la semilla de cada orden (9010, 9020, ...) no se repite ningún día simulado, ni entre órdenes ni con la 3.1.3. Lo revisa una prueba.

## Cómo se usan

1. Abre los dos cuadernos de tu escenario (A y B) en dos pestañas, y en cada uno usa «Entorno de ejecución → Ejecutar todas».
2. La celda 1 reinicia el entorno: el aviso de «sesión fallada» es normal.
3. Si Colab se corta, vuelve a «Ejecutar todas»: las corridas retoman donde quedaron.
4. La **celda 13** debe decir **LISTO**: 15 corridas del sistema, 15 de TWAP, 15 de VWAP, todas con cumplimiento ≥ 0,95.
5. El cuaderno que termina último arma la tabla del escenario (celda 14) y el zip `corridas_90_<escenario>.zip` (celda 15).
6. Ese zip se manda al grupo. **BF** junta los tres (3.2.2) y **PS** hace la comparación estadística (3.2.3).

**Necesitas:** la carpeta `slippage_colab/resultados/sistema_final/maestro/` en tu Drive. Si no la tienes, pídesela a PS.

## Dónde quedan los resultados

En Drive, dentro de `slippage_colab/resultados/`:
- `corridas_90/<escenario>/A/` y `B/`, con 2 JSON por parte;
- `corridas_90/<escenario>/tabla/`;
- `corridas_90_<escenario>.zip`.

En el repositorio van a `data/colab_resultados/corridas_90/`.
