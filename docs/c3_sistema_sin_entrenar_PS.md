# C-3: primera evaluación del sistema completo (redes sin entrenar) sobre las 10 meta-órdenes

**Elaborado por:** PS con apoyo de Claude Code (uso autorizado por la universidad), 25 de octubre de 2026. **Pendiente de revisión por:** MR (redes y entrenamiento) y BF (meta-órdenes).

## 1. Qué se hizo
Se corrió `scripts/colab/evaluar_sistema_ps.py` con ABIDES calibrado sobre las 10 meta-órdenes del archivo candidato v2 (`meta_ordenes_v2_candidata.json`), con el Maestro y los tres Ejecutores **sin entrenar** y política determinista (argmax), con las semillas 1 y 2 de los benchmarks. Se hizo en dos cuadernos de Colab (órdenes MO-01 a MO-05 y MO-06 a MO-10) y una prueba corta (MO-08, semilla 1). Datos en `data/colab_resultados/c3_sistema/`.

## 2. Qué se validó
1. **El flujo completo funciona con ABIDES real:** Maestro → mensaje ASIGNAR → Ejecutor → mercado simulado → REPORTE → Maestro, durante 4 a 13 decisiones por orden, sin errores (20 de 20 corridas).
2. **El pareo con los benchmarks es válido:** el precio de referencia del sistema coincide con el de TWAP y VWAP en las 20 corridas (misma semilla de mercado).
3. **Tiempo:** entre 117 y 386 s por corrida; unos 40 minutos por cada mitad.

## 3. Un error encontrado y corregido
Las redes sin entrenar se creaban **sin semilla**: cada proceso generaba pesos distintos. La misma orden y semilla (MO-08, semilla 1) dio decisiones y resultados diferentes en dos sesiones (cumplimiento 0,830 frente a 0,754). Consecuencia: las dos mitades (MO-01 a 05 y MO-06 a 10) usaron **redes distintas** y no forman un único sistema.

**Corrección:** `evaluar_sistema_ps.py` ahora fija los pesos iniciales con `--seed-red` (por defecto 1000) y lo anota en la firma del archivo; hay pruebas que verifican que dos procesos dan la misma corrida. Hay que repetir la corrida (ver sección 5). Con checkpoints entrenados no hay problema, porque los pesos vienen del archivo.

## 4. Resultado preliminar y por qué NO se puede leer como una ventaja
Con las dos redes distintas, el sistema sin entrenar aparece 43 bps más barato que TWAP y 50 bps más barato que VWAP (ver `docs/sistema_sin_entrenar_vs_benchmarks_PS.md`). **No es una ventaja real:**
- El sistema sin entrenar ejecuta solo el **88,5 %** de la orden en promedio (TWAP y VWAP, 99,5 %). El slippage cuenta solo lo ejecutado, así que lo que queda sin comprar no entra en el costo.
- Usa órdenes límite pasivas, que se ejecutan al azar y con mejor precio cuando se ejecutan.

**Lección para la comparación final (3.2.3):** el costo en bps no basta; hay que compararlo junto con el cumplimiento y con una medida que valore lo no ejecutado (por ejemplo, el IS completo con el precio de cierre para lo pendiente, o R_M). Hoy los archivos no guardan el precio de cierre; conviene registrarlo en los benchmarks y en el evaluador antes de la comparación definitiva. Es una decisión de diseño para el equipo.

## 5. Qué sigue
- Repetir la evaluación con la semilla de red fija (dos cuadernos, ≈ 40 min cada uno).
- Definir con BF y MR la medida de costo que incluye lo no ejecutado.
- Cuando existan redes entrenadas, usar `--ckpt-maestro` y `--ckpt-ejecutor`.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
