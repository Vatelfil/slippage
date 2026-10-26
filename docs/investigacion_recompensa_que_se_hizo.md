# Investigación del entrenamiento del Ejecutor: qué se hizo y por qué

**Para qué sirve este documento:** dejar registrado, para el resto del Sprint 6 y para actualizar el Título II más adelante, qué se hizo en el PC de PS, por qué, quién lo hizo y qué resultó. **No actualiza el Título II**: solo reúne el material.

**Quién:** PS (Paolo Sepúlveda) con apoyo de Claude Code (uso autorizado por la universidad), 25 y 26 de octubre de 2026. Lo que toca partes de MR (entrenador PPO) o de BF (recompensa) quedó como **borrador de PS para ellos**, sin modificar sus archivos.

## 1. Resumen
- **Problema:** con 1.000 episodios, las redes entrenadas con la recompensa actual cuestan **más** que la misma red sin entrenar (+3 bps; 0 de 6 redes mejores).
- **Causa encontrada:** la red hace lo que la recompensa le pide, no lo que se evalúa. Nada obliga a completar la orden, así que **esperar siempre** da la recompensa máxima (cero); además, el factor de descuento γ = 0,95 hace que un costo al final de la ventana se vea cuatro veces más barato (0,95²⁹ ≈ 0,23).
- **Arreglo que funciona (en el simulador de Poisson):** una **penalización de 30 bps por cada acción sin comprar al terminar la ventana** y **γ = 1**. Con las dos cosas, 5 de 5 redes cumplen la orden y bajan el costo hasta el nivel de la mejor heurística (17,9 frente a 17,91 bps; la red inicial, 20,26). Cada cambio por separado no sirve (0 de 5).
- **Confirmación en ABIDES (26 de octubre):** con la misma penalización y γ = 1 las 4 redes cumplen la orden (cumplimiento ≈ 1,0, espera 20–40 %). Sobre el costo: con 15 semillas de evaluación parecían +3,0 bps peores que el control (0 de 4), pero con 40 semillas las dos redes comparables quedan 2,2 bps mejores (no significativo): el ruido del precio entre semillas tapa la diferencia y **hace falta reevaluar con 300 semillas**. Los resultados anteriores de 15 semillas (incluido el «+3 bps, 0 de 6» del resumen y de la decisión D3) están en revisión. Detalle en `docs/v4_abides_resultado_parcial_A_PS.md`.
- **Falta:** probar en ABIDES la recompensa contra el precio de llegada y que BF y MR revisen la propuesta.

## 2. Por qué se hizo
Al cerrar la comparación de D3 con el control muestreado (red sin entrenar muestreando la política, ≈ 3 bps) se vio que el entrenamiento no mejoraba el costo y que con 1.000 episodios lo empeoraba. Antes de seguir ajustando hiperparámetros (Sprint 6) había que saber **qué** estaba fallando. Se aprobó el plan de investigación el 26 de octubre (fases 0 a 3, todo en el PC, sin Colab).

## 3. Qué se hizo, paso a paso

### Fase 0: diagnóstico formal
- **Reproducir la falla en el PC.** Con el simulador de Poisson, la red con la recompensa actual pasa de esperar ≈ 30 % de los pasos a esperar el 97–99 %, con cumplimiento de 0,02 a 0,07. Una corrida de 1.000 episodios dura cerca de un minuto, así que se pudo probar mucho.
- **Revisar ABIDES.** En las corridas de Colab, la recompensa de entrenamiento mejora (p. ej. de −2,6 a −1,1) pero el slippage no baja, y las órdenes de mercado se reemplazan por órdenes límite pasivas (de 35 % a 82–89 %).
- **Cuántas semillas de evaluación hacen falta.** El desvío de la diferencia pareada es de 9,1 bps en ABIDES: detectar 3 bps necesita ≈ 73 semillas y detectar 1 bps, ≈ 650. Las pruebas en Poisson usan 50 semillas; la confirmación en ABIDES usa 40 y 4 redes.
- **Tamaño de entrenamiento y de uso no coinciden.** Se entrena con 1.000 acciones; en el sistema completo cada ventana compra entre ≈ 250 y ≈ 7.500 acciones (máximo ≈ 27.700).

### Fase 1: auditoría de R_E
Se midió qué recompensa recibe cada estrategia simple frente a su costo real (5.000 acciones, 50 semillas, el remanente se liquida a mercado para que todas sean comparables):

| Estrategia | R_E que ve el agente | Costo real (bps) |
|---|---:|---:|
| Esperar siempre | 0,0 | 21,5 |
| Mercado por todo | −12,4 | 20,9 |
| TWAP con órdenes límite | −10,0 | **17,9** |
| Orden límite pasiva | −7,0 | 21,4 |

El orden se invierte: la estrategia que más recompensa recibe (esperar) es de las que más cuestan, y la límite pasiva parece mejor que el TWAP en R_E y es peor en la realidad.

### Fase 2: arreglos candidatos
Todos viven en `src/experiments/variantes_recompensa.py` (envoltorio con banderas apagadas por defecto; con todas apagadas la recompensa es idéntica a la original, hay prueba):
- **Liquidación forzada** del remanente al final de la ventana (solo Poisson).
- **Penalización terminal** por acción pendiente.
- **Recompensa de IS** frente al precio de llegada (lo que mide la evaluación).
- **Costo de espera denso** paso a paso.
- **Tamaños y ventanas aleatorios**, **hiperparámetros alternativos** y **arranque por imitación** de la mejor heurística.
- **γ = 1** (en `ConfigPPO`).

### Fase 3: matriz de experimentos
Tres etapas con 5 semillas de red y 1.000 episodios por variante, en paralelo (`scripts/experimentos_recompensa_ps.py`):
- **Etapa A** (5 variantes): ninguna funciona; todas terminan esperando. La liquidación y la penalización no alcanzan con γ = 0,95. De ahí salió la sospecha del descuento.
- **Etapa A2** (11 variantes): γ = 1 con las variantes anteriores, penalización de 100 bps y costo de espera. **Cinco variantes funcionan 5 de 5.**
- **Etapa B** (4 ajustes sobre la mejor): ninguno mejora la base.

## 4. Resultados (5.000 acciones, 15 minutos, 50 semillas de evaluación)

| Variante | Slippage (bps) | Cumplimiento voluntario | Pasos en espera | Redes buenas |
|---|---:|---:|---:|---:|
| Red inicial | 20,26 | 1,00 | 30 % | — |
| Recompensa actual (γ = 0,95) | 21,48 | 0,05 | 99 % | 0 de 5 |
| Recompensa actual con γ = 1 | 21,44 | 0,05 | 98 % | 0 de 5 |
| Penalización 30 bps, γ = 0,95 | 21,24 | 0,14 | 89 % | 0 de 5 |
| **Penalización 30 bps, γ = 1** | **17,92** | 0,99 | 19 % | **5 de 5** |
| Liquidación forzada, γ = 1 | 17,97 | 0,95 | 38 % | 5 de 5 |
| Penalización 100 bps, γ = 1 | 17,98 | 1,00 | 17 % | 5 de 5 |
| Costo de espera denso (100 bps), γ = 1 | 20,38 | 1,00 | 4 % | 1 de 5 |
| Penalización 30 bps, γ = 1, tamaños aleatorios | 20,04 | 1,00 | 20 % | 1 de 5 |
| Penalización 30 bps, γ = 1, hiperparámetros alternativos | 18,18 | 1,00 | 31 % | 5 de 5 |
| Penalización 30 bps, γ = 1, arranque por imitación | 18,13 | 1,00 | 23 % | 5 de 5 |
| *TWAP con órdenes límite (mejor heurística)* | *17,91* | *0,98* | *0 %* | — |

También bajan el costo con 20.000 acciones (penalización 30 bps, γ = 1: 19,68 frente a 21,13 de la red inicial y 19,31 del TWAP límite). Con 1.000 acciones el simulador no distingue estrategias (todo ≈ 17,7 a 18,3 bps).

## 5. Gráficos explicados

### `data/analysis/diagnostico_recompensa.png` (cuatro paneles)
- **(a)** Porcentaje de pasos en espera durante el entrenamiento con la recompensa actual en Poisson (cuatro corridas). Sube de ≈ 30 % a ≈ 98 %: la red aprende a no operar.
- **(b)** Corridas de ABIDES: la recompensa (verde) sube y el slippage (marrón) no baja.
- **(c)** Recompensa R_E que ve el agente en cada estrategia simple: «esperar siempre» tiene 0, el máximo, y la límite pasiva parece mejor que el TWAP límite.
- **(d)** Costo real de las mismas estrategias: «esperar siempre» y la límite pasiva son de las más caras, y el TWAP límite es el más barato. Comparando (c) y (d) se ve que la recompensa y el costo ordenan distinto.

### `data/analysis/experimentos_recompensa_A2.png` (y `_A`, `_B`)
Tres paneles con una fila por variante:
- **Izquierda:** costo en bps con 5.000 acciones (el eje no parte de cero: importan unos pocos bps). La línea punteada gris es la red inicial y la verde, el TWAP con órdenes límite. Las barras que llegan a la línea verde son las que alcanzan el nivel de la mejor heurística.
- **Centro:** porcentaje de pasos en espera; la línea punteada marca el 50 %.
- **Derecha:** de las 5 redes de cada variante, cuántas cumplen los tres criterios (cumplir la orden, no esperar y bajar el costo); la línea marca el mínimo de 4.

## 6. Qué falta
1. **Confirmación en ABIDES: hecha** (cumplimiento ≈ 1,0; costo sin resolver: +3,0 bps con 15 semillas, −2,2 bps con 40). **Reevaluar todas las redes con 300 semillas** (`notebooks/Colab_reevaluacion_300_ABIDES.ipynb`, no entrena, ≈ 60–120 min) y, si se quiere, correr el cuaderno B de V4 (recompensa contra el precio de llegada; en el cuaderno A no se distinguió de V2). Ver `docs/v4_abides_resultado_parcial_A_PS.md`.
2. **Revisión de BF y MR** de `docs/propuesta_cambio_RE_para_BF_y_MR.md`: la penalización va a R_E (2.2.3, BF) y γ = 1 al entrenador (2.3.2, MR); γ = 1 se aparta del Título I y hay que declararlo en `DESVIACIONES_TITULO1_VS_IMPLEMENTACION.md`.
3. **Costo de espera denso con valores menores** (no se probó) y más episodios para los tamaños aleatorios.
4. **Maestro:** entrenarlo sobre estos Ejecutores y repetir la evaluación del sistema completo (depende del bucle de entrenamiento del Maestro, de MR).

## 7. Cómo reproducirlo
```
python scripts/diagnostico_recompensa_ps.py                                    # fases 0 y 1 (≈ 4 min)
python scripts/experimentos_recompensa_ps.py --etapa A2 --out-dir data/experimentos_recompensa/etapa_A2
python scripts/experimentos_recompensa_ps.py --etapa B --base V2_penalizacion_g1 --out-dir data/experimentos_recompensa/etapa_B
python scripts/analizar_experimentos_recompensa.py --dir data/experimentos_recompensa/etapa_A2 --etapa A2
PYTHONPATH=. python -m pytest tests/test_variantes_recompensa.py
```

## 8. Archivos nuevos
| Archivo | Para qué |
|---|---|
| `src/experiments/variantes_recompensa.py` | Envoltorio con las variantes de recompensa y la evaluación común |
| `src/experiments/entrenamiento_variantes.py` | Entrenar, imitar, evaluar en tres escenarios |
| `scripts/diagnostico_recompensa_ps.py` | Diagnóstico de las fases 0 y 1 |
| `scripts/experimentos_recompensa_ps.py` | Matriz de experimentos (en paralelo, reanudable) |
| `scripts/analizar_experimentos_recompensa.py` | Informe, figura y criterio por variante |
| `scripts/colab/entrenamiento_inicial_ps.py` | Nuevas opciones `--gamma`, `--penalizacion-bps`, `--costo-espera-bps` |
| `tests/test_variantes_recompensa.py` | 15 pruebas (incluye un entorno de prueba con el formato de ABIDES) |
| `docs/diagnostico_recompensa_PS.md`, `docs/experimentos_recompensa_*_PS.md`, `docs/propuesta_cambio_RE_para_BF_y_MR.md` | Informes y propuesta |
| `notebooks/Colab_confirmacion_ABIDES_A.ipynb` y `_B.ipynb` | Confirmación en Colab |
| `data/experimentos_recompensa/` | Resultados de cada corrida |

## 9. Notas para actualizar el Título II (no se actualizó)
- **Recompensa del Ejecutor (R_E):** agregar que, sin un término que obligue a completar, la política óptima de R_E es no operar; documentar la penalización terminal propuesta.
- **Hiperparámetros:** γ_E = 1,0 propuesto frente a 0,95 del Título I; justificación en la sección 3.
- **Evaluación:** incluir siempre el control de la red sin entrenar muestreando la política y evaluar con suficientes semillas (50 o más).
- **Resultados del Sprint 6:** el hallazgo (el entrenamiento empeoraba el costo), la causa y el arreglo, con la salvedad de que se probó en Poisson y falta ABIDES.
- **Limitaciones:** Poisson no tiene impacto de precio ni tendencia; con 1.000 acciones no distingue estrategias.

## 10. Ramas
`feature/ps-investigacion-recompensa` (esta). Las ramas anteriores del Sprint 6 y su orden de PR están en `docs/bitacora_cambios_PS.md`.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
