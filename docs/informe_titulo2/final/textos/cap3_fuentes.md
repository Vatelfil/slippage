## 3.2 Requerimientos de datos del sistema

La arquitectura jerárquica impone requerimientos de datos distintos para cada nivel:
- **Agente Maestro** (decisiones cada 30 minutos): necesita datos intradiarios OHLCV (apertura, máximo, mínimo, cierre y volumen) con resolución de 1 a 30 minutos, que están disponibles de forma gratuita para las acciones del IPSA.
- **Agentes Ejecutores** (pasos de 30 segundos): necesitan datos de Nivel 2 del libro de órdenes, es decir, los mejores niveles de compra y de venta con sus volúmenes, el spread instante a instante y la tasa de llegada de órdenes. En el mercado chileno, estos datos son de acceso limitado y costoso.

Esta diferencia definió dos vías: datos reales intradiarios para el Maestro y para calibrar los simuladores, y simuladores calibrados para entrenar y evaluar a los Ejecutores.

## 3.3 Fuentes de datos evaluadas y decisión

El Título I evaluó varias fuentes de datos reales y sintéticos. La tabla resume cada una y la decisión que se tomó en el desarrollo.

**Tabla.** Fuentes de datos evaluadas en el Título I y decisión adoptada en el desarrollo.

| Fuente | Tipo y resolución | Costo | Decisión en el desarrollo |
|---|---|---|---|
| Yahoo Finance (librería `yfinance` de Python) | Real; velas OHLCV de hasta 1 minuto (las de 5 minutos, solo de los últimos 60 días) | Gratuita | **Usada:** velas de 5 minutos de las 30 acciones del IPSA, en *snapshots* fechados (sección 3.4) |
| Tienda en línea de la Bolsa de Santiago | Real; transacciones diarias e índices, sin Nivel 2 | Pagada | No usada: no aporta resolución intradiaria ni Nivel 2 |
| Investing.com | Real; series diarias | Gratuita | No usada: resolución diaria |
| Banco Central de Chile | Real; series diarias y mensuales del IPSA | Gratuita | No usada: resolución diaria |
| ICE Data Services, Bloomberg o Refinitiv | Real; Nivel 1 y 2 del libro de órdenes | Comercial o por convenio | No usada: sin acceso |
| ABIDES (configuración RMSC04) | Sintética; libro completo con agentes heterogéneos | Gratuita (código abierto) | **Usada:** calibrada con datos del IPSA; simulador de la evaluación (Capítulo 5) |
| Modelo de Poisson de llegada de órdenes | Sintética; libro paramétrico | Implementación propia | **Usada:** calibrada por tramo horario; simulador de entrenamiento del Maestro (Capítulo 5) |
| TRADES-LOB | Sintética; acciones estadounidenses | Gratuita | No usada: no corresponde al mercado chileno |
