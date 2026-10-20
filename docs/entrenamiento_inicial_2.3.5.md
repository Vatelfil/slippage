# Entrenamiento inicial de validación del Ejecutor (tarea 2.3.5)

**Borrador elaborado por:** Paolo Sepúlveda (PS) con apoyo de Claude Code. **Pendiente de revisión por:** Benjamín Farias (BF), responsable de la 2.3.5, y Mauricio Reynoso (MR, entrenador PPO). Lo que BF no acepte se cambia o se descarta; nada aquí está cerrado hasta su revisión.

## 1. Qué se hizo

Se entrenó un Ejecutor con el entrenador PPO de MR (`PPOTrainer`, 2.3.2) durante **100 episodios** sobre ABIDES calibrado (FALABELLA, tramo apertura, `rmsc04_ipsa_FALABELLA_2026-08-23.json`), con `q_slice` = 1000 acciones y ventana de 15 minutos. Recompensa: R_E según el Título I con β = 0,0061796 (opción 0 de D3). Semillas de entrenamiento 1001–1100; evaluación en 15 semillas nuevas (5001–5015). No se usaron las 10 meta-órdenes oficiales.

Hiperparámetros (los mismos de la fase 2 de β): γ 0,95; λ GAE 0,95; lr 3e-4; clip 0,2; entropía 0,01; coeficiente de valor 0,5; 4 épocas; minilote 64; 10 episodios por actualización.

## 2. Curvas de entrenamiento

![Curvas del entrenamiento](../data/analysis/entrenamiento_inicial_2.3.5.png)

- **Actualizaciones registradas:** 10 (una cada 10 episodios). **Valores no finitos (NaN o infinito) en el CSV:** 0.
- **Retorno medio:** -2,000 en el primer tercio y -1,034 en el último. **Pérdida del crítico:** 3,201 y 1,884.
- **KL máximo:** 0,00012 (el objetivo del entrenador es 0,015; la actualización se corta si lo supera 1,5 veces).
- **Entropía:** de 5,4793 a 5,4754; una política uniforme sobre las 240 acciones tiene 5,4806. La política final conserva el 99,90 % de la entropía máxima, es decir, sigue siendo casi uniforme.
- **Tiempo de entrenamiento:** 3,4 min.

## 3. Evaluación (semillas nuevas, política determinista)

| Política | Slippage medio (bps) | Error estándar | Cumplimiento |
|---|---:|---:|---:|
| Red entrenada | 3,28 | 2,45 | 1,000 |
| Red sin entrenar (control) | 6,02 | 4,68 | 1,000 |
| Referencia: agresiva_market | 10,45 | 4,39 | 1,000 |
| Referencia: twap_limit_medio | 1,78 | 4,58 | 0,971 |
| Referencia: pasiva_limit | 7,88 | 4,69 | 1,000 |

Comparación pareada por semilla (red entrenada menos cada alternativa; negativo = la red entrenada tiene menos slippage):

| Contra | Diferencia media (bps) | Error estándar | p (Wilcoxon) |
|---|---:|---:|---:|
| Red sin entrenar (control) | -2,74 | 3,64 | 0,762 |
| Referencia: agresiva_market | -7,17 | 3,27 | 0,030 |
| Referencia: twap_limit_medio | 1,50 | 3,10 | 0,421 |
| Referencia: pasiva_limit | -4,60 | 3,46 | 0,135 |

## 4. Regla de vigilancia de D3

Cumplimiento medio de la red entrenada: **1,000** (umbral 0,95). El cumplimiento de la red entrenada es >= 95 %: se mantiene la opcion 0 de D3. La decisión final de R_E se revisa el viernes 23 de octubre y es de BF.

## 5. Lectura preliminar de PS (BF debe confirmar, corregir o reemplazar)

- **El ciclo completo funciona con ABIDES:** 100 episodios en 3,4 min, sin valores no finitos, con checkpoint, CSV y evaluación en semillas nuevas.
- **No hay evidencia de que la red haya aprendido todavía.** La red entrenada tiene 3,28 bps frente a 6,02 bps de la red sin entrenar, pero la diferencia pareada (-2,74 bps, p = 0,762) no es significativa con 15 semillas.
- **Las actualizaciones fueron muy pequeñas:** KL máximo 0,00012, fracción recortada 0,00 y entropía al 99,90 % del máximo. La política sigue siendo casi uniforme; con 10 actualizaciones PPO no se esperaba otra cosa.
- **Frente a las referencias:** agresiva_market: -7,17 bps (p = 0,030, significativa); twap_limit_medio: 1,50 bps (p = 0,421); pasiva_limit: -4,60 bps (p = 0,135).
- **Qué sugiere:** el resultado sirve para validar el pipeline, no para comparar políticas. Como el entrenamiento es barato (3,4 min por 100 episodios), conviene repetirlo con muchos más episodios (por ejemplo 1.000) antes de sacar conclusiones sobre R_E.
- **D3:** el cumplimiento de la red entrenada es 1,000; la regla del plan no obliga a pasar a la opción A.

## 6. Limitaciones

- Entrenamiento corto (100 episodios) y una sola semilla de red: el resultado es indicativo, no concluyente.
- Solo FALABELLA y un tramo; no incluye a COPEC ni a ECL.
- La evaluación usa 15 semillas: el error estándar es grande frente a las diferencias entre políticas.

## 7. Cómo reproducir

En Colab, con el entorno preparado (`docs/dependencias_resueltas.md`, con `torch==1.13.1+cpu`):

```bash
PYTHONPATH=. python scripts/colab/entrenamiento_inicial_ps.py \
    --calibrated-json data/calibration/rmsc04_ipsa_FALABELLA_2026-08-23.json --out-dir <carpeta_de_drive>/t5_entrenamiento \
    --tramo apertura --episodes 100 --ventana-min 15 --max-minutes 150
```

El script es reanudable. Luego `python scripts/analizar_entrenamiento_inicial.py --estado <json> --csv <csv>` regenera este informe.

🤖 Generado con [Claude Code](https://claude.com/claude-code)
