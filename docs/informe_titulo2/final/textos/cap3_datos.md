## 3.4 Datos de mercado utilizados

Los datos provienen de Yahoo Finance mediante la librería `yfinance`: velas OHLCV (apertura, máximo, mínimo, cierre y volumen) de 5 minutos para las 30 acciones del IPSA (tickers con sufijo `.SN`). La fuente solo entrega los últimos 60 días en esa resolución, por lo que el pipeline se ejecuta sobre *snapshots* fechados. El del 23 de agosto de 2026 (ventana del 28 de mayo al 21 de agosto) se usó para calibrar el modelo de Poisson y entrenar el sistema; los posteriores se usaron en la caracterización de mercado, en los benchmarks y en pruebas complementarias.

El pipeline tiene cuatro etapas, cada una con su script y sus pruebas automáticas:

1. **Validación y descarga.** Se verifica que los 30 tickers respondan y se descargan las velas de 5 minutos, registrando un manifiesto con los parámetros de la descarga.
2. **Limpieza.** Se filtra la sesión de 09:30 a 15:55 (hora de Santiago), se reindexa cada día a una grilla fija de 78 velas, se imputan las velas sin transacción (relleno hacia adelante y hacia atrás) marcándolas con `is_imputed`, y se fusiona la vela de las 16:00 (subasta de cierre) con la de las 15:55.
3. **Normalización.** Se aplica MinMaxScaler por ticker. Las columnas sin normalizar (en pesos y número de acciones) se conservan, porque los cálculos en unidades reales (implementation shortfall, calibración de Poisson) deben usarlas.
4. **Variables del Maestro.** Se calculan la volatilidad (desviación estándar móvil de 6 velas), el volumen promedio móvil y la sesión, que alimentan el vector de estado S_M.

Como medida de calidad se define la **cobertura pre-relleno**: la fracción de velas teóricas en que hubo al menos una transacción real. Los tickers con cobertura de al menos 60 % se clasifican como *tier* A y el resto como *tier* B.

| Indicador | Valor |
|---|---|
| Tickers procesados | 30 (todos responden en Yahoo Finance) |
| Días hábiles por ticker | 60 (2026-05-28 a 2026-08-21), sin días descartados |
| Velas por ticker (78 por día) | 4.680; total 140.400 filas |
| Clasificación | 15 tickers *tier* A y 15 *tier* B (umbral de 60 % de cobertura) |
| Mayor cobertura | LTM: 96,65 % |
| Menor cobertura | IAM: 19,66 % |
| Activo representativo (FALABELLA) | *Tier* A, cobertura 92,93 %; 7,20 % de velas imputadas |

**Limitaciones de los datos:** no incluyen el libro de órdenes de Nivel 2, de modo que el spread, la profundidad y las cancelaciones solo pueden aproximarse a partir de velas de 5 minutos. Además, la ventana de 60 días que entrega la fuente es corta y no puede volver a descargarse una vez que pasa; los archivos de cada *snapshot* se conservan aparte del repositorio.

## 3.5 Comportamiento intradiario del mercado real

El Título I anticipa que el mercado chileno concentra actividad y profundidad en la apertura y el cierre, y que la media jornada presenta spreads más amplios. Para contrastarlo se caracterizó el mercado por tramo horario sobre los 30 tickers (140.400 observaciones del *snapshot* de septiembre). Como el libro de órdenes no está disponible, el spread se aproxima con el rango máximo–mínimo de cada vela, expresado como porcentaje del precio de cierre.

| Tramo | Spread relativo (%) | Volatilidad (desv. est. de retornos) | Volumen promedio por vela (acciones) |
|---|---|---|---|
| Apertura (09:30–11:00) | 0,138 | 0,00251 | 396.765 |
| Media jornada (11:00–14:00) | 0,112 | 0,00156 | 456.967 |
| Cierre (14:00–16:00) | 0,128 | 0,00151 | 698.419 |

Figura: `docs/informe_titulo2/final/recursos/perfil_mercado_ipsa_real.png` (Spread relativo, volatilidad y volumen promedio por tramo horario, datos reales del IPSA).

Tres observaciones se desprenden de la tabla:

- **El spread es mayor en la apertura, no en la media jornada.** La media jornada es el tramo de menor spread (0,112 %). El patrón es decreciente a lo largo del día (forma de «L»), distinto de la forma de «U» que sugería la hipótesis inicial.
- **La volatilidad decrece de la apertura a la media jornada y se mantiene baja en el cierre**, sin el repunte de cierre que describe la literatura clásica.
- **El volumen crece hacia el cierre** (de 396.765 a 698.419 acciones por vela), en lugar de mostrar el patrón alto–bajo–alto esperado.

Este resultado fue confirmado de forma independiente por la calibración de Poisson, que usa otro *snapshot* y otra metodología (estimador de Roll, 1984, y rango máximo–mínimo, con winsorización) y llega a la misma conclusión: en el conjunto de los 30 tickers, el rango máximo–mínimo solo es mayor en la media jornada que en la apertura y el cierre en 1 caso de 30. Una explicación plausible es el patrón de «L» frecuente en mercados de liquidez fina, aunque con datos de 5 minutos y sin Nivel 2 no puede descartarse que parte del efecto sea un artefacto del proxy usado.

Esta caracterización usa los cortes de la variable `sesion` del vector S_M (11:00 y 14:00), mientras que los Ejecutores definen la apertura hasta las 11:30. La diferencia está registrada como desviación 1 (Anexo A) y no altera la dirección de las conclusiones.
