# Benchmarks TWAP y VWAP sobre las meta-órdenes (tarea 2.3.4)

**Elaborado por:** PS con apoyo de Claude Code. **Pendiente de revisión por:** BF y MR.
**Entorno:** abides · **Órdenes:** 10 · **Fecha:** 2026-10-20

Cada orden se reparte desde su tramo de inicio hasta el cierre con la política ingenua de mercado (TWAP: partes iguales; VWAP: proporcional al volumen histórico por tramo). IS = (P_prom − P_ref) × Q; slippage en bps sobre P_ref.

## 1. Resultados por orden

| Orden | Activo | Inicio | Cantidad | Estrategia | n | IS medio (CLP) | Slippage medio (bps) | EE (bps) | Cumplimiento |
|---|---|---|---:|---|---:|---:|---:|---:|---:|
| MO-01 | FALABELLA | apertura | 100.000 | TWAP | 2 | -411.894 | -6,90 | 23,35 | 0,998 |
| MO-01 | FALABELLA | apertura | 100.000 | VWAP | 2 | -818.121 | -13,71 | 23,29 | 0,985 |
| MO-02 | COPEC | apertura | 100.000 | TWAP | 2 | 6.771.824 | 110,47 | 16,12 | 0,925 |
| MO-02 | COPEC | apertura | 100.000 | VWAP | 2 | 7.592.983 | 123,87 | 12,76 | 0,936 |
| MO-03 | COPEC | apertura | 100.000 | TWAP | 2 | 3.340.540 | 54,49 | 33,40 | 0,983 |
| MO-03 | COPEC | apertura | 100.000 | VWAP | 2 | 2.765.231 | 45,11 | 31,17 | 0,968 |
| MO-04 | ECL | apertura | 100.000 | TWAP | 2 | 1.136.935 | 63,16 | 31,04 | 0,966 |
| MO-04 | ECL | apertura | 100.000 | VWAP | 2 | 1.194.227 | 66,35 | 42,54 | 0,971 |
| MO-05 | COPEC | media_jornada | 100.000 | TWAP | 2 | 6.589.760 | 107,69 | 34,72 | 0,962 |
| MO-05 | COPEC | media_jornada | 100.000 | VWAP | 2 | 7.246.069 | 118,42 | 37,13 | 0,955 |
| MO-06 | ECL | media_jornada | 100.000 | TWAP | 2 | 5.543.718 | 314,76 | 47,79 | 0,940 |
| MO-06 | ECL | media_jornada | 100.000 | VWAP | 2 | 5.931.968 | 336,77 | 45,86 | 0,913 |
| MO-07 | ECL | media_jornada | 100.000 | TWAP | 2 | 2.558.572 | 143,73 | 40,43 | 0,941 |
| MO-07 | ECL | media_jornada | 100.000 | VWAP | 2 | 2.839.438 | 159,49 | 39,33 | 0,953 |
| MO-08 | FALABELLA | cierre | 100.000 | TWAP | 2 | 2.507.020 | 44,31 | 129,80 | 1,000 |
| MO-08 | FALABELLA | cierre | 100.000 | VWAP | 2 | 2.507.020 | 44,31 | 129,80 | 1,000 |
| MO-09 | FALABELLA | cierre | 100.000 | TWAP | 2 | 7.653.878 | 129,31 | 49,14 | 0,896 |
| MO-09 | FALABELLA | cierre | 100.000 | VWAP | 2 | 7.653.878 | 129,31 | 49,14 | 0,896 |
| MO-10 | FALABELLA | cierre | 100.000 | TWAP | 2 | 3.898.368 | 65,22 | 16,99 | 0,845 |
| MO-10 | FALABELLA | cierre | 100.000 | VWAP | 2 | 3.898.368 | 65,22 | 16,99 | 0,845 |

## 2. TWAP frente a VWAP

| Orden | TWAP (bps) | VWAP (bps) | TWAP − VWAP (bps) | ¿Idénticas? |
|---|---:|---:|---:|:---:|
| MO-01 | -6,90 | -13,71 | 6,80 | no |
| MO-02 | 110,47 | 123,87 | -13,40 | no |
| MO-03 | 54,49 | 45,11 | 9,38 | no |
| MO-04 | 63,16 | 66,35 | -3,18 | no |
| MO-05 | 107,69 | 118,42 | -10,73 | no |
| MO-06 | 314,76 | 336,77 | -22,01 | no |
| MO-07 | 143,73 | 159,49 | -15,76 | no |
| MO-08 | 44,31 | 44,31 | 0,00 | sí |
| MO-09 | 129,31 | 129,31 | 0,00 | sí |
| MO-10 | 65,22 | 65,22 | 0,00 | sí |

- Diferencia media TWAP − VWAP: **-4,89 bps** (n = 10 órdenes; 7 con calendarios distintos).
- Wilcoxon pareado sobre las órdenes con calendarios distintos: p = 0,156; no se rechaza la igualdad con α = 0,05.

## 3. Ejecutabilidad de las meta-órdenes (criterio de T3)

Una orden es ejecutable si TWAP completa al menos el 95 % (`execution_rate`). Se informa el cumplimiento de cada semilla y su media.

| Orden | Activo | Inicio | Acciones | Cumplimiento por semilla | Media | Corridas ≥ umbral | ¿Ejecutable? |
|---|---|---|---:|---|---:|---:|:---:|
| MO-01 | FALABELLA | apertura | 100.000 | 100,0 % · 99,6 % | 99,8 % | 2/2 | sí |
| MO-02 | COPEC | apertura | 100.000 | 95,6 % · 89,5 % | 92,5 % | 1/2 | no |
| MO-03 | COPEC | apertura | 100.000 | 99,9 % · 96,7 % | 98,3 % | 2/2 | sí |
| MO-04 | ECL | apertura | 100.000 | 94,7 % · 98,5 % | 96,6 % | 1/2 | sí |
| MO-05 | COPEC | media_jornada | 100.000 | 94,2 % · 98,2 % | 96,2 % | 1/2 | sí |
| MO-06 | ECL | media_jornada | 100.000 | 88,6 % · 99,4 % | 94,0 % | 1/2 | no |
| MO-07 | ECL | media_jornada | 100.000 | 89,8 % · 98,5 % | 94,1 % | 1/2 | no |
| MO-08 | FALABELLA | cierre | 100.000 | 100,0 % · 100,0 % | 100,0 % | 2/2 | sí |
| MO-09 | FALABELLA | cierre | 100.000 | 89,4 % · 89,9 % | 89,6 % | 0/2 | no |
| MO-10 | FALABELLA | cierre | 100.000 | 75,3 % · 93,6 % | 84,5 % | 0/2 | no |

- **5 de 10 órdenes** son ejecutables en promedio; 11 de 20 corridas llegan al umbral.

**Comparación con la opción B de D1 (10 % del volumen del día):**

| Orden | Activo | Inicio | Acciones (A) | Media A | Acciones (B) | Media B | ¿Ejecutable B? |
|---|---|---|---:|---:|---:|---:|:---:|
| MO-01 | FALABELLA | apertura | 100.000 | 99,8 % | 88.300 | 100,0 % | sí |
| MO-02 | COPEC | apertura | 100.000 | 92,5 % | 29.100 | 100,0 % | sí |
| MO-03 | COPEC | apertura | 100.000 | 98,3 % | 29.100 | 100,0 % | sí |
| MO-04 | ECL | apertura | 100.000 | 96,6 % | 32.100 | 100,0 % | sí |
| MO-05 | COPEC | media_jornada | 100.000 | 96,2 % | 29.100 | 100,0 % | sí |
| MO-06 | ECL | media_jornada | 100.000 | 94,0 % | 32.100 | 100,0 % | sí |
| MO-07 | ECL | media_jornada | 100.000 | 94,1 % | 32.100 | 100,0 % | sí |
| MO-08 | FALABELLA | cierre | 100.000 | 100,0 % | 88.300 | 100,0 % | sí |
| MO-09 | FALABELLA | cierre | 100.000 | 89,6 % | 88.300 | 94,5 % | no |
| MO-10 | FALABELLA | cierre | 100.000 | 84,5 % | 88.300 | 78,6 % | no |

- Con la opción B, **8 de 10 órdenes** son ejecutables (8 de 10 corridas); con la A, 5 de 10. Semillas por orden: A = 2, B = 1.

## 4. Limitaciones

- Las órdenes que empiezan en el cierre tienen un TWAP y un VWAP idénticos: el perfil de volumen se calcula por tramo y dentro de un tramo los periodos pesan igual.
- Pocas semillas por orden (ver n): los errores estándar son amplios y el slippage absoluto en ABIDES está subestimado porque el spread simulado es mucho menor que el real (ver `docs/validacion_formal_2.2.5_PS.md`); la comparación entre estrategias sigue siendo válida.
- Una jornada completa son 13 periodos independientes (un entorno nuevo por periodo, igual que el orquestador).
- El IS se calcula sobre lo ejecutado: cuando el cumplimiento es menor que 100 %, el costo de lo que no se ejecutó no entra, y comparar estrategias con cumplimientos distintos tiene ese sesgo.
- Cada periodo usa un entorno nuevo y lo que no se ejecuta en un periodo no se traslada al siguiente; es una causa probable del cumplimiento incompleto (no comprobada).

🤖 Generado con [Claude Code](https://claude.com/claude-code)
