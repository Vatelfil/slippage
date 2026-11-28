## 2.1 El mercado accionario chileno y el índice IPSA

El mercado bursátil chileno opera a través de la Bolsa de Santiago, y su segmento más relevante está representado por el índice IPSA (Índice de Precio Selectivo de Acciones). El índice agrupa a las acciones de mayor capitalización bursátil y mayor liquidez del país, por lo que es el principal referente del desempeño de la renta variable nacional. Su composición se revisa trimestralmente (marzo, junio, septiembre y diciembre) según la presencia bursátil, el volumen promedio diario transado y la capitalización ajustada, con un límite del 15 % de ponderación por componente y del 25 % por grupo económico. Desde el 1 de septiembre de 2026, la administración del índice pasó a MSCI; los datos usados en este trabajo son anteriores a ese cambio.

El mercado chileno tiene una liquidez estructuralmente más baja que la de bolsas globales como la NYSE o el NASDAQ. Entre 2010 y 2015, los montos transados en la Bolsa de Santiago cayeron más de un 56 %, lo que muestra la sensibilidad del mercado local a factores macroeconómicos y geopolíticos. Esta liquidez reducida tiene una consecuencia directa sobre el problema que aborda este trabajo: mientras menor es la profundidad del libro de órdenes, mayor es el impacto en el precio de una orden de gran volumen, y con ello el slippage. Por eso el IPSA es un entorno exigente para la ejecución de órdenes de gran volumen.

Otro fenómeno reciente es el cambio en la composición de los inversionistas. Según el Instituto de Finanzas Internacionales (IIF, 2026), desde 2023 los hogares, principalmente a través de fondos mutuos, reemplazaron a los inversionistas extranjeros y a las AFP como compradores marginales de acciones en la Bolsa de Santiago. Esto hace al mercado más sensible a la liquidez doméstica y a la confianza local, lo que puede aumentar la volatilidad intradiaria en momentos de estrés.

Además, el IPSA tiene patrones intradiarios de liquidez. La negociación continua se extiende de 09:30 a 16:00 en horario de invierno (17:00 en verano), después de una subasta de apertura entre las 09:00 y las 09:25 (Bolsa de Santiago, 2024). El Título I suponía que la mayor actividad y profundidad se concentraban entre las 09:30 y las 11:30 y entre las 14:00 y las 16:00, con spreads más amplios en la media jornada; los datos de este trabajo confirman que el volumen crece hacia el cierre, pero muestran que el spread es mayor en la apertura (Capítulo 3, sección 3.5). Conocer estos patrones es un insumo para diseñar una estrategia de ejecución.

## 2.2 El libro de órdenes (Limit Order Book, LOB)

El mecanismo central de un mercado bursátil electrónico es el libro de órdenes de precio límite (*limit order book*, LOB): una estructura de datos dinámica que registra en tiempo real todas las intenciones de compra (*bids*) y de venta (*asks*), a distintos niveles de precio, que aún no se han ejecutado ni cancelado.

Los participantes interactúan con el libro mediante dos tipos de órdenes. Las **órdenes de mercado** (*market orders*) compran o venden de inmediato al mejor precio disponible: consumen liquidez del libro y generan un impacto directo en el precio. Las **órdenes límite** (*limit orders*) fijan un precio máximo de compra o mínimo de venta; si no hay contraparte disponible, quedan en el libro a la espera de ejecución o cancelación, y por lo tanto aportan liquidez. La diferencia entre el mejor precio de venta y el mejor precio de compra es el **spread bid-ask**, el indicador más directo del costo de la liquidez inmediata.

Según Glosten y Milgrom (1985), el spread surge de la selección adversa: los creadores de mercado lo amplían para compensar el riesgo de transar con agentes mejor informados. La literatura de microestructura ha estudiado cómo la información se incorpora al precio a través de las transacciones (Kyle, 1985; Hasbrouck, 1991) y cómo los participantes eligen entre órdenes límite y de mercado según el estado del libro (Parlour, 1998; Roşu, 2009; Gould et al., 2013).

El libro se organiza así:
- El lado comprador (*bid*) lista las órdenes de compra de mayor a menor precio. El mejor *bid* es el precio máximo que alguien está dispuesto a pagar en ese instante.
- El lado vendedor (*ask*) lista las órdenes de venta de menor a mayor precio. El mejor *ask* es el precio mínimo al que alguien está dispuesto a vender.
- La diferencia entre el mejor *ask* y el mejor *bid* es el spread.

Cuando un participante envía una orden de mercado, esta consume las órdenes límite del lado contrario, comenzando por el mejor precio. Si su volumen supera lo ofrecido en el mejor nivel, la ejecución avanza hacia los niveles siguientes y empeora el precio promedio. Este fenómeno es la causa directa del slippage.

**Tabla.** Estructura simplificada de un libro de órdenes para una acción del IPSA (ejemplo ilustrativo; elaboración propia).

| Lado | Precio (CLP) | Volumen (acciones) | Tipo | Descripción |
|---|---|---|---|---|
| Ask 3 | 5.820 | 3.000 | Venta | Precio límite |
| Ask 2 | 5.810 | 5.500 | Venta | Precio límite |
| Ask 1 (mejor ask) | 5.800 | 2.000 | Venta | Mejor oferta de venta |
| Spread | 10 CLP (0,17 %) | | | |
| Bid 1 (mejor bid) | 5.790 | 4.000 | Compra | Mejor oferta de compra |
| Bid 2 | 5.780 | 6.000 | Compra | Precio límite |
| Bid 3 | 5.770 | 8.500 | Compra | Precio límite |

## 2.3 El slippage y el implementation shortfall

El slippage (deslizamiento de precio) es el costo adicional que paga un inversionista cuando ejecuta una orden cuyo volumen supera la liquidez disponible en los mejores niveles del libro. Con el libro de la tabla anterior, si un fondo compra 8.000 acciones con una única orden de mercado, obtiene 2.000 acciones a 5.800 CLP, 5.500 a 5.810 y 500 a 5.820. El precio promedio resulta de unos 5.808 CLP por acción frente al precio inicial de 5.800: una diferencia de 8 CLP por acción que, multiplicada por 8.000 acciones, suma 64.000 CLP. En operaciones institucionales de decenas de miles de acciones, el costo acumulado puede llegar a millones de pesos.

Perold (1988) formalizó este costo con el *implementation shortfall* (IS): la diferencia entre el precio al que se decidió invertir y el precio efectivamente pagado. Lo descompuso en cuatro componentes:
- **Costo de demora:** la diferencia entre el precio de decisión y el precio al enviar la orden.
- **Costos explícitos:** las comisiones.
- **Impacto de mercado:** la diferencia entre el precio de ejecución efectivo y el precio al inicio de la ejecución.
- **Costo de oportunidad:** el costo de las acciones que no se ejecutaron dentro del horizonte definido.

El IS es la métrica estándar de la industria para evaluar la calidad de ejecución, y por eso es la medida de costo que el sistema busca minimizar.

El impacto tiene dos componentes. El **impacto temporal** se disipa a medida que el libro se repone y puede reducirse fraccionando y distribuyendo las órdenes en el tiempo. El **impacto permanente** persiste, porque refleja información incorporada al precio: una compra grande indica al mercado que hay un agente dispuesto a pagar más, y los demás participantes ajustan sus expectativas al alza. Almgren y Chriss (2001) formularon la minimización del costo total como la optimización de una trayectoria de ejecución, con un dilema central: ejecutar rápido reduce el riesgo de que el precio se mueva, pero aumenta el impacto; ejecutar lento reduce el impacto, pero aumenta ese riesgo. Almgren (2003) extendió el modelo a funciones de impacto no lineales. La evidencia empírica muestra que el impacto crece aproximadamente con la raíz cuadrada del tamaño relativo de la orden (Almgren et al., 2005) y decae en el tiempo (Bouchaud et al., 2004).

En el IPSA, con un libro estructuralmente menos profundo que el de los mercados globales, la recuperación del libro después de una compra grande puede tardar minutos. Por eso los inversionistas institucionales necesitan fraccionar sus órdenes de forma inteligente.

## 2.4 Estrategias tradicionales de ejecución y sus limitaciones

Antes del uso de la inteligencia artificial, los algoritmos de ejecución más usados en la industria eran TWAP, VWAP y las estrategias basadas en el *implementation shortfall*. Son un avance respecto de la ejecución manual, pero comparten una limitación: se basan en reglas predefinidas o en modelos estáticos y no aprenden de las condiciones del mercado.

- **TWAP** (*Time Weighted Average Price*): reparte la orden en partes iguales a lo largo del tiempo, ejecutando Q/T acciones en cada periodo. Es simple y predecible, pero no considera la liquidez: compra lo mismo cuando el libro es profundo y cuando no lo es, e ignora los patrones intradiarios.
- **VWAP** (*Volume Weighted Average Price*): sigue el perfil histórico de volumen y compra más en los periodos de mayor actividad. Es más elaborado que TWAP, pero usa patrones pasados y no reacciona a cambios no observados antes. Kato (2016) mostró que VWAP es óptima bajo ciertas condiciones del modelo de Almgren y Chriss (2001). Sin embargo, el perfil histórico es solo una estimación del futuro, que puede cambiar en días de alta volatilidad, y si muchos participantes siguen VWAP a la vez, todos compran en las mismas horas y presionan el precio.
- **Estrategias adaptativas (IS):** ajustan la velocidad de ejecución según las condiciones del mercado en tiempo real para minimizar el costo total. Son más adaptables, pero requieren una calibración más compleja y suponen formas funcionales del impacto que pueden no capturar la microestructura del IPSA.

**Tabla.** Comparación de las principales estrategias tradicionales de ejecución algorítmica (elaboración propia basada en Almgren y Chriss, 2001, y Kato, 2016).

| Característica | TWAP | VWAP | IS / adaptativa |
|---|---|---|---|
| Referencia | Promedio ponderado por tiempo | Promedio ponderado por volumen | Diferencia frente al precio de decisión |
| Complejidad | Baja: tasa constante | Media: requiere un perfil de volumen | Alta: optimización dinámica |
| Adaptabilidad | Nula: tasa fija | Baja: sigue el volumen histórico | Alta: reacciona al mercado en tiempo real |
| Riesgo de *timing* | Alto: ignora la liquidez | Moderado: depende del perfil histórico | Bajo si se gestiona correctamente |
| Uso típico | Mercados ilíquidos, órdenes pequeñas | Ejecución institucional en renta variable | Ejecución de alto volumen con control de costos |
| Principal limitación | No aprovecha los patrones de liquidez | Perfil incierto en días atípicos | Implementación compleja; requiere calibración |

Las estrategias estáticas son, además, predecibles: un participante que repite TWAP o VWAP puede ser detectado por otros, que anticipan sus órdenes (*front-running*). El sistema propuesto en el Título I busca cubrir esa brecha con una política que se adapta a las condiciones del mercado.

## 2.5 Aprendizaje por refuerzo multiagente aplicado a la ejecución

La solución propuesta se basa en el aprendizaje por refuerzo multiagente (MARL) con una estructura jerárquica que separa la planificación de largo plazo de la ejecución de corto plazo. A diferencia de los algoritmos estáticos, combina una visión de la jornada completa con decisiones tácticas que reaccionan a la microestructura local.

El antecedente principal es el trabajo de Nevmyvaka et al. (2006), la primera aplicación a gran escala del aprendizaje por refuerzo a la ejecución óptima, que reportó mejoras frente a estrategias de referencia. Trabajos posteriores usaron redes profundas: Ning et al. (2021) con *Deep Q-Networks* y Lin y Beling (2020) con PPO, ambos con mejoras frente a los métodos tradicionales incluso con datos escasos y recompensas dispersas. Kolm y Ritter (2019) mostraron la utilidad del enfoque en otros problemas financieros, como la cobertura de derivados. Estos resultados son el antecedente del proyecto, pero se obtuvieron en otros mercados y con otras referencias; el Capítulo 8 (sección 8.6) vuelve sobre ellos a la luz de los resultados de este trabajo.

Dos ideas sostienen la arquitectura de este trabajo. La primera es el **aprendizaje por refuerzo jerárquico**: un agente de alto nivel decide objetivos de mediano plazo (cuánto comprar en la siguiente media hora) y agentes de bajo nivel deciden las acciones concretas para cumplirlos (qué orden enviar al libro). Esto divide un problema de horizonte largo en dos problemas más cortos y entrenables. La segunda es el **entrenamiento centralizado con ejecución descentralizada (CTDE)**: durante el entrenamiento se usa información global para estimar el valor de las acciones, pero en la ejecución cada agente decide solo con su propia información. Lowe et al. (2017) formalizaron este esquema con críticos centralizados, y Rashid et al. (2018) lo extendieron con la factorización de la función de valor (QMIX). En ejecución de órdenes, Karpe et al. (2020) entrenaron agentes en un libro de órdenes simulado con ABIDES, y Fang et al. (2023) coordinaron varios agentes que ejecutan órdenes en paralelo.

## 2.6 Proximal Policy Optimization (PPO)

PPO (Schulman et al., 2017) es el algoritmo de aprendizaje del sistema. Es un método de gradiente de política (*policy gradient*): aprende directamente la política $\pi_\theta(a \mid s)$, la función que asigna a cada estado una distribución de probabilidad sobre las acciones. A diferencia de los métodos basados en valor como DQN, los métodos de gradiente de política se adaptan bien a espacios de acción grandes o mixtos; en la implementación final, ambos niveles usan espacios discretos (Capítulo 4, sección 4.2).

Su predecesor, TRPO (*Trust Region Policy Optimization*), introdujo la idea de limitar cuánto cambia la política entre iteraciones para evitar inestabilidad, pero es costoso porque requiere cálculos de segundo orden. PPO logra un efecto similar con un mecanismo más simple: recorta (*clip*) el objetivo para restringir el cambio de la política en cada actualización.

### Objetivo recortado de PPO

PPO maximiza en cada iteración la siguiente función objetivo:

$$L^{\text{CLIP}}(\theta) = \mathbb{E}_t \bigl[ \min\bigl( r_t(\theta) \, A_t,\; \text{clip}(r_t(\theta), 1-\epsilon, 1+\epsilon) \, A_t \bigr) \bigr]$$

- $r_t(\theta) = \pi_\theta(a_t \mid s_t) / \pi_{\theta_{\text{old}}}(a_t \mid s_t)$: razón entre la probabilidad de la acción con la política nueva y con la anterior. Mide cuánto cambió la política.
- $A_t$ (ventaja): se estima con *Generalized Advantage Estimation* (GAE; Schulman et al., 2016). Mide cuánto mejor fue la acción que lo esperado en ese estado: si $A_t > 0$ fue mejor, y si $A_t < 0$ fue peor.
- $\epsilon \in [0{,}1; 0{,}2]$: parámetro de recorte. Limita $r_t(\theta)$ al rango $[1-\epsilon, 1+\epsilon]$ e impide actualizaciones demasiado bruscas.

El recorte es importante en un mercado de baja liquidez, donde una actualización brusca podría llevar al agente a comportamientos erráticos ante cambios de liquidez.

### Arquitectura Actor-Crítico

PPO usa una arquitectura actor-crítico: dos funciones que se entrenan a la vez. El actor ($\pi_\theta$) aprende qué acción tomar en cada estado, y el crítico ($V_\phi$) estima el valor esperado de cada estado, que sirve de referencia para calcular la ventaja. Esta separación hace el aprendizaje más estable que los métodos puramente basados en valor o puramente basados en política.

**Tabla.** Parámetros de PPO y su relevancia para el entrenamiento en el IPSA (elaboración propia).

| Parámetro de PPO | Descripción | Relevancia para el IPSA |
|---|---|---|
| ε (recorte) | Rango permitido de cambio de la política por iteración | Previene decisiones erráticas ante la volatilidad del libro |
| γ (descuento) | Peso de las recompensas futuras frente a las inmediatas | Alto en el Maestro (0,99). El Título I proponía 0,95 en los Ejecutores; la implementación final usa 1,0 (desviación 6) |
| λ de GAE | Equilibrio entre sesgo y varianza en la estimación de la ventaja | Reduce el ruido de las recompensas del mercado |
| Tamaño de lote | Muestras por actualización de la política | Un lote mayor da más estabilidad en mercados ruidosos |
| Número de épocas | Pasadas sobre el mismo lote de experiencia | Se calibra para evitar el sobreajuste |

## 2.7 Simulación de mercados y datos sintéticos

Los datos de Nivel 2 del libro de órdenes del mercado chileno son de acceso restringido o costoso. Por eso el proyecto entrenó y evaluó los agentes en simuladores calibrados con datos reales, una estrategia habitual en la literatura (Nevmyvaka et al., 2006; Karpe et al., 2020; Byrd et al., 2020).

### ABIDES y ABIDES-Gym

ABIDES (*Agent-Based Interactive Discrete Event Simulation*) es el simulador de mercado de referencia en la investigación de aprendizaje por refuerzo para *trading*. Fue desarrollado por Byrd et al. (2020) y es mantenido por J.P. Morgan como proyecto de código abierto. Modela un libro de órdenes completo con agentes heterogéneos (creadores de mercado, agentes de valor, de momentum y de ruido). Su extensión ABIDES-Gym (Amrouni et al., 2021) ofrece una interfaz compatible con Gym, lo que permite conectarlo directamente con el entrenamiento PPO. Su configuración RMSC04 incluye un agente de bolsa, 2 creadores de mercado, 102 agentes de valor, 12 de momentum y 1.000 de ruido, y tiene licencia BSD de 3 cláusulas, libre para uso académico. Es el simulador de la evaluación final de este trabajo.

### Modelo de Poisson de llegada de órdenes

Como alternativa más liviana, el libro puede simularse con el modelo de llegada de órdenes de Cont, Stoikov y Talreja (2010), que describe su dinámica como un proceso estocástico en el que las órdenes límite de compra, de venta y las cancelaciones llegan según tasas de Poisson ($\lambda^+$, $\lambda^-$, $\theta$) calibradas con datos. Su ventaja frente a ABIDES es una menor complejidad computacional, una calibración más simple con datos escasos y una implementación directa en Python. En este trabajo se usó para entrenar al Maestro.

### Otras alternativas consideradas

El Título I consideró también conjuntos de datos sintéticos generados con modelos de difusión, como TRADES-LOB (Berti et al., 2025), y simuladores acelerados en GPU (Frey et al., 2023) y basados en modelos (França y Jaimungal, 2022). No se usaron, porque no corresponden al mercado chileno y el proyecto pudo calibrar ABIDES y el modelo de Poisson con datos del IPSA.
