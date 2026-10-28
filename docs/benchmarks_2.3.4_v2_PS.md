# Benchmarks TWAP y VWAP sobre las meta-órdenes (tarea 2.3.4)

**Elaborado por:** PS con apoyo de Claude Code. **Pendiente de revisión por:** BF y MR.
**Entorno:** abides · **Órdenes:** 10 · **Fecha:** 2026-10-23

Cada orden se reparte desde su tramo de inicio hasta el cierre con la política ingenua de mercado (TWAP: partes iguales; VWAP: proporcional al volumen histórico por tramo). IS = (P_prom − P_ref) × Q; slippage en bps sobre P_ref.

_Archivo ensamblado de varias tandas con tamaños distintos (`scripts/ensamblar_benchmarks_meta_ordenes.py`); las órdenes conservan su semilla._

## 1. Resultados por orden

| Orden | Activo | Inicio | Cantidad | Estrategia | n | IS medio (CLP) | Slippage medio (bps) | EE (bps) | Cumplimiento |
|---|---|---|---:|---|---:|---:|---:|---:|---:|
| MO-01 | FALABELLA | apertura | 88.300 | TWAP | 2 | -404.484 | -7,68 | 23,66 | 1,000 |
| MO-01 | FALABELLA | apertura | 88.300 | VWAP | 2 | -819.433 | -15,55 | 25,08 | 0,990 |
| MO-02 | COPEC | apertura | 29.100 | TWAP | 2 | 1.677.153 | 94,02 | 19,94 | 1,000 |
| MO-02 | COPEC | apertura | 29.100 | VWAP | 2 | 1.967.518 | 110,30 | 19,52 | 1,000 |
| MO-03 | COPEC | apertura | 29.100 | TWAP | 2 | 700.869 | 39,29 | 31,27 | 1,000 |
| MO-03 | COPEC | apertura | 29.100 | VWAP | 2 | 542.848 | 30,43 | 30,52 | 1,000 |
| MO-04 | ECL | apertura | 32.100 | TWAP | 2 | 313.478 | 54,25 | 38,55 | 1,000 |
| MO-04 | ECL | apertura | 32.100 | VWAP | 2 | 318.780 | 55,17 | 38,73 | 1,000 |
| MO-05 | COPEC | media_jornada | 29.100 | TWAP | 2 | 1.761.396 | 98,92 | 36,06 | 1,000 |
| MO-05 | COPEC | media_jornada | 29.100 | VWAP | 2 | 2.073.742 | 116,46 | 39,94 | 1,000 |
| MO-06 | ECL | media_jornada | 32.100 | TWAP | 2 | 1.754.485 | 310,24 | 32,42 | 1,000 |
| MO-06 | ECL | media_jornada | 32.100 | VWAP | 2 | 1.982.786 | 350,49 | 18,14 | 1,000 |
| MO-07 | ECL | media_jornada | 32.100 | TWAP | 2 | 786.747 | 137,66 | 32,70 | 1,000 |
| MO-07 | ECL | media_jornada | 32.100 | VWAP | 2 | 830.475 | 145,30 | 31,14 | 1,000 |
| MO-08 | FALABELLA | cierre | 44.100 | TWAP | 2 | 1.158.553 | 46,29 | 127,56 | 1,000 |
| MO-08 | FALABELLA | cierre | 44.100 | VWAP | 2 | 1.158.553 | 46,29 | 127,56 | 1,000 |
| MO-09 | FALABELLA | cierre | 44.100 | TWAP | 2 | 3.691.130 | 141,26 | 37,21 | 1,000 |
| MO-09 | FALABELLA | cierre | 44.100 | VWAP | 2 | 3.691.130 | 141,26 | 37,21 | 1,000 |
| MO-10 | FALABELLA | cierre | 44.100 | TWAP | 2 | 1.794.572 | 68,09 | 13,26 | 0,951 |
| MO-10 | FALABELLA | cierre | 44.100 | VWAP | 2 | 1.794.572 | 68,09 | 13,26 | 0,951 |

## 2. TWAP frente a VWAP

| Orden | TWAP (bps) | VWAP (bps) | TWAP − VWAP (bps) | ¿Idénticas? |
|---|---:|---:|---:|:---:|
| MO-01 | -7,68 | -15,55 | 7,87 | no |
| MO-02 | 94,02 | 110,30 | -16,28 | no |
| MO-03 | 39,29 | 30,43 | 8,86 | no |
| MO-04 | 54,25 | 55,17 | -0,92 | no |
| MO-05 | 98,92 | 116,46 | -17,54 | no |
| MO-06 | 310,24 | 350,49 | -40,25 | no |
| MO-07 | 137,66 | 145,30 | -7,64 | no |
| MO-08 | 46,29 | 46,29 | 0,00 | sí |
| MO-09 | 141,26 | 141,26 | 0,00 | sí |
| MO-10 | 68,09 | 68,09 | 0,00 | sí |

- Diferencia media TWAP − VWAP: **-6,59 bps** (n = 10 órdenes; 7 con calendarios distintos).
- Wilcoxon pareado sobre las órdenes con calendarios distintos: p = 0,297; no se rechaza la igualdad con α = 0,05.

## 3. Ejecutabilidad de las meta-órdenes (criterio de T3)

Una orden es ejecutable si TWAP completa al menos el 95 % (`execution_rate`). Se informa el cumplimiento de cada semilla y su media.

| Orden | Activo | Inicio | Acciones | Cumplimiento por semilla | Media | Corridas ≥ umbral | ¿Ejecutable? |
|---|---|---|---:|---|---:|---:|:---:|
| MO-01 | FALABELLA | apertura | 88.300 | 100,0 % · 100,0 % | 100,0 % | 2/2 | sí |
| MO-02 | COPEC | apertura | 29.100 | 100,0 % · 100,0 % | 100,0 % | 2/2 | sí |
| MO-03 | COPEC | apertura | 29.100 | 100,0 % · 100,0 % | 100,0 % | 2/2 | sí |
| MO-04 | ECL | apertura | 32.100 | 100,0 % · 100,0 % | 100,0 % | 2/2 | sí |
| MO-05 | COPEC | media_jornada | 29.100 | 100,0 % · 100,0 % | 100,0 % | 2/2 | sí |
| MO-06 | ECL | media_jornada | 32.100 | 100,0 % · 100,0 % | 100,0 % | 2/2 | sí |
| MO-07 | ECL | media_jornada | 32.100 | 100,0 % · 100,0 % | 100,0 % | 2/2 | sí |
| MO-08 | FALABELLA | cierre | 44.100 | 100,0 % · 100,0 % | 100,0 % | 2/2 | sí |
| MO-09 | FALABELLA | cierre | 44.100 | 100,0 % · 100,0 % | 100,0 % | 2/2 | sí |
| MO-10 | FALABELLA | cierre | 44.100 | 90,2 % · 100,0 % | 95,1 % | 1/2 | sí |

- **10 de 10 órdenes** son ejecutables en promedio; 19 de 20 corridas llegan al umbral.

## 4. Limitaciones

- Las órdenes que empiezan en el cierre tienen un TWAP y un VWAP idénticos: el perfil de volumen se calcula por tramo y dentro de un tramo los periodos pesan igual.
- Pocas semillas por orden (ver n): los errores estándar son amplios y el slippage absoluto en ABIDES está subestimado porque el spread simulado es mucho menor que el real (ver `docs/validacion_formal_2.2.5_PS.md`); la comparación entre estrategias sigue siendo válida.
- Una jornada completa son 13 periodos independientes (un entorno nuevo por periodo, igual que el orquestador).
- El IS se calcula sobre lo ejecutado: cuando el cumplimiento es menor que 100 %, el costo de lo que no se ejecutó no entra, y comparar estrategias con cumplimientos distintos tiene ese sesgo.
- Cada periodo usa un entorno nuevo y lo que no se ejecuta en un periodo no se traslada al siguiente; es una causa probable del cumplimiento incompleto (no comprobada).

🤖 Generado con [Claude Code](https://claude.com/claude-code)
