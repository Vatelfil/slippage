# Cuadernos de Colab para cerrar el Sprint 6 (orden y qué devolver)

**Elaborado por:** PS con apoyo de Claude Code, 29 de octubre de 2026. Todos bajan la rama `feature/ps-cierre-sprint6` (celda 7) y guardan en `slippage_colab/resultados`. Si un cuaderno se corta, se vuelve a ejecutar entero: retoma donde quedó. Colab gratis permite dos a la vez.

| Paso | Cuaderno | Qué hace | Necesita antes | Tiempo | Devolver |
|---|---|---|---|---|---|
| 1 | `Colab_imitacion_A.ipynb` y `Colab_imitacion_B.ipynb` (juntos) | Ejecutor PPO que parte copiando a TWAP límite y se ajusta con PPO (semillas 1000 y 2000) | — | ≈ 1 h 15 min cada uno | `rimit_A.zip`, `rimit_B.zip` (**hecho**, 29 de octubre) |
| 2 | `Colab_reevaluacion_imitacion_300.ipynb` | Reevalúa esas redes (y las solo imitadas) en las 300 semillas | Paso 1 | ≈ 50 min | `reeval_300_imitacion.zip` (**hecho** el 30 oct; la red s2000 faltó dos veces: ver paso 3b) |
| 2b | `Colab_C6b_liquidez_mm_BF.ipynb` (junto con el paso 2) | Escenarios de liquidez v2 (solo el market maker) | — | ≈ 1 h 20 min | `c6b_liquidez.zip` (**hecho** el 30 oct) |
| 3 | `Colab_sistema_final.ipynb` | Elige el Ejecutor con la regla y entrena el Maestro (λ = 0,02, impacto) | Paso 2 | ≈ 1 h | `sistema_final.zip` (**hecho** el 30 oct, con la red s1000) |
| 3b | `Colab_reeval_red_B.ipynb` | Busca la red s2000 en Drive (o pide subirla), la reevalúa y vuelve a aplicar la regla; si gana, rehace el Maestro | Paso 3 | ≈ 15–30 min | `reeval_red_B.zip` (**hecho** el 30 oct: 5,98 bps, la elección no cambia) |
| 4 | `Colab_30corridas_bloque1.ipynb` … `bloque4.ipynb` (de a dos) | 3.1.3: sistema final, TWAP y VWAP en 10 meta-órdenes × 3 semillas, con impacto | Paso 3 | bloques 1 y 2 ≈ 3 h 25 min; 3 y 4 ≈ 2 h 15 min | `corridas_30_bloque4.zip` (el último trae todos los bloques y la tabla). **Bloques 1 a 3 hechos** el 30 oct; falta el 4 |

**Tiempo de reloj total:** ≈ 9 horas, corriendo de a dos. Si falta tiempo, los bloques del paso 4 se pueden correr con `--seeds 2` (20 corridas en vez de 30), avisándolo en el informe.

**Si algo falla:** manda la última pantalla con el error. La celda 7 debe mostrar un commit y un número mayor que 0. Si muestra 0, el cuaderno bajó una rama equivocada.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
