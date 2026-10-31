# Corrección: el sistema no completaba las órdenes que empiezan al cierre (31 de octubre)

**Elaborado por:** PS con apoyo de Claude Code. **Archivos:**
- `src/envs/maestro_ejecutor_protocol.py`: opción `completar_al_cierre`.
- `scripts/colab/evaluar_sistema_ps.py`: opción `--completar-al-cierre`.
- `tests/test_maestro_ejecutor_protocol.py`: 3 pruebas nuevas.
- `notebooks/Colab_30corridas_corregidas_A.ipynb` y `_B.ipynb`.

## 1. El problema

En las 30 corridas (`docs/corridas_30_resultado_PS.md`), las tres órdenes que empiezan al cierre (MO-08, MO-09 y MO-10) quedaron con un cumplimiento de 0,91 a 0,93. El mínimo fijado es 0,95.

## 2. La causa (revisada en el código)

No es un error de aprendizaje del Maestro: es un tope de cómo está definida su acción.

- El Maestro decide cada 30 minutos qué fracción **de lo que falta** asigna: α ∈ {0,05; 0,10; …; 0,50}.
- Una orden que empieza a las 14:00 tiene **4 decisiones** antes de las 16:00 (14:00, 14:30, 15:00 y 15:30).
- Aunque asigne siempre el máximo, queda sin asignar 0,5⁴ = 6,25 %. **El tope es 93,75 %.**
- En las 9 corridas del cierre, **el Maestro eligió α = 0,50 en las 4 decisiones**. Hizo lo máximo que le permitía su acción. El Ejecutor compró casi todo lo asignado: de 91 a 93 % sobre un tope de 93,75 %.

En la apertura (13 decisiones) y en media jornada (10), el tope es mayor al 99,9 %, por eso ahí el cumplimiento sí fue de 1,00.

## 3. La corrección

Con `completar_al_cierre`, **la última decisión del día (15:30) asigna todo lo que falta** (α = 1), sea cual sea la acción del Maestro. Las decisiones anteriores no cambian.

- **Por qué es válido:** el Título I exige completar la orden en la jornada. TWAP y VWAP también terminan la orden en el último tramo. Barrer lo pendiente al final es la regla habitual en ejecución algorítmica.
- **Por defecto está apagada**, para que se puedan reproducir los resultados anteriores. Se activa con `--completar-al-cierre`.
- **El Maestro no se vuelve a entrenar.** La regla solo cambia la última acción, y en esa acción el Maestro ya elegía el máximo. Si en el Sprint 7 se vuelve a entrenar, conviene hacerlo con la regla activada.
- **Límite:** el Ejecutor puede no comprar todo lo que se le asigna en su ventana. En Poisson, con redes sin entrenar, MO-08 subió de 0,69–0,71 a 0,89–1,00 de cumplimiento. Con las redes entrenadas en ABIDES se espera ≈ 0,99. Lo confirma la repetición de las corridas.

## 4. Pruebas

- `test_sin_completar_al_cierre_el_tope_es_93_75`: sin la regla, una orden de 14:00 con α = 0,5 en cada decisión llega a 93,75 %.
- `test_completar_al_cierre_asigna_todo_en_la_ultima_decision`: con la regla, llega al 100 %.
- `test_completar_al_cierre_no_cambia_las_decisiones_anteriores`.

## 5. Qué hay que correr

Hay que repetir **solo el sistema** en las 30 corridas, con las mismas redes, semillas e impacto. Se usan los cuadernos `Colab_30corridas_corregidas_A` y `_B`, al mismo tiempo, ≈ 1 h cada uno. TWAP y VWAP no cambian y se reutilizan. El resultado reemplaza al de `docs/corridas_30_resultado_PS.md` como versión oficial de la 3.1.3. La versión sin la corrección queda como registro.

**Resultado (31 oct):** el cumplimiento de las órdenes del cierre subió de 0,91–0,93 a 0,97–1,00. Las demás órdenes no cambiaron. El sistema contra TWAP queda en −22,1 bps [−50,0; +4,4]. Ver `docs/corridas_30_corregidas_resultado_PS.md`.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
