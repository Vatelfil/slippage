const L = require('./lib');
const { AlignmentType } = require('docx');
const FIG = (f) => `${__dirname}/fig/${f}`;
const { H1, H2, H3, P, B, N, FORMULA, table, tabCaption, chip, callout, GAP, figure } = L;
const C2 = require('./parte2c');
const D2 = require('./parte2d');
const C = AlignmentType.CENTER;

module.exports = function parte2b() {
  const k = [];

  // ====================================================================
  // CAPITULO 5
  // ====================================================================
  k.push(L.PB());
  k.push(H1('Capítulo 5. Implementación del sistema'));
  k.push(P('El prototipo está escrito en Python. Cada componente vive en un módulo del repositorio y tiene pruebas automáticas (sección 6.4). Este capítulo describe qué hace cada uno, cómo se verificó y dónde están sus límites actuales.'));

  // ---- 5.1
  k.push(H2('5.1 Pipeline de datos'));
  k.push(P('El pipeline se compone de tres scripts: `download_ohlcv.py` (descarga), `clean_ohlcv.py` (limpieza) y `build_sm_features.py` (variables del Maestro), todos con interfaz de línea de comandos y con la fecha del snapshot como parámetro. Los pasos de limpieza y construcción de variables son deterministas dado un archivo de entrada fijo, lo que permite reproducir las cifras reportadas. Se verificó con 13 pruebas automáticas y con controles visuales: el perfil de volumen intradiario de FALABELLA muestra su máximo en la vela de las 15:55, coherente con la fusión de la subasta de cierre en esa vela.'));
  k.push(...figure(FIG('FALABELLA_volumen_intradiario.png'), 'Perfil intradiario de volumen de FALABELLA (control de calidad del pipeline).', 520, 220));

  // ---- 5.2
  k.push(H2('5.2 Espacios de estado y de acción (Gymnasium)'));
  k.push(P('Los espacios se formalizaron como clases de Gymnasium en el módulo `spaces.py`. Los rangos y las dimensiones no están escritos en el código: se cargan en tiempo de ejecución desde los esquemas versionados (`SM_schema.json` y `SE_schema.json`), de modo que un cambio de contrato se hace en el esquema y no en el código. El módulo ofrece:'));
  k.push(...B([
    '`MaestroSpace` y `EjecutorSpace`: espacios de observación de tipo Box (7 y 27 dimensiones).',
    '`MaestroDiscreteActionSpace`: espacio Discrete(40) con conversión entre el índice plano y el par (fracción, ventana).',
    '`EjecutorActionSpace`: espacio MultiDiscrete([3, 10, 8]) con `decode_flat` y `encode_flat`, que traducen entre el índice plano 0–239 que produce la red y los tres componentes de la acción.',
  ]));
  k.push(P('Estas conversiones resolvieron un desajuste real detectado durante la integración: el entorno del Maestro tenía originalmente una acción continua, mientras que la red del Maestro produce una acción discreta de 40 valores. Con el espacio discreto y las funciones de conversión, la acción muestreada por la red se decodifica correctamente en el entorno.'));

  // ---- 5.3
  k.push(H2('5.3 Calibración de Poisson y simulador liviano'));
  k.push(P('Siguiendo a Cont, Stoikov y Talreja (2010) y la sección 4.3.3 de la Parte I, la llegada de órdenes al libro se describe con tres intensidades: λ⁺ (órdenes de compra), λ⁻ (órdenes de venta) y θ (cancelaciones), expresadas por paso de 30 segundos. Se estimó un triple por cada ticker y tramo horario (90 combinaciones) sobre el snapshot de agosto:'));
  k.push(...B([
    '**λ⁺ y λ⁻** se estiman a partir del volumen firmado de cada vela. El signo se obtiene del cuerpo de la vela (cierre menos apertura), con la regla del tick como respaldo; el volumen se winsoriza en el percentil 99 y se divide por un tamaño medio de orden supuesto (un nocional fijo de un millón de pesos por orden, porque la fuente no entrega el número de transacciones).',
    '**θ** se aproxima por la persistencia del rango máximo–mínimo entre velas consecutivas (autocorrelación de orden 1), ya que sin Nivel 2 no se observan cancelaciones.',
    'Se excluyen las velas imputadas y la vela de las 15:55 (subasta de cierre).',
  ]));
  k.push(tabCaption('Parámetros calibrados para FALABELLA (órdenes y cancelaciones por paso de 30 segundos).'));
  k.push(table(['Tramo', 'λ⁺', 'λ⁻', 'θ', 'Estadístico KS', 'Roll (pb)'], [
    ['Apertura', '5,369', '5,126', '0,135', '0,100', '35,3'],
    ['Media jornada', '5,294', '5,511', '0,110', '0,116', '23,8'],
    ['Cierre', '6,400', '5,811', '0,100', '0,114', '20,6'],
  ], [2100, 1300, 1300, 1300, 1700, 1326], { aligns: [AlignmentType.LEFT, C, C, C, C, C] }));
  k.push(...figure(FIG('FALABELLA_poisson_por_tramo.png'), 'Calibración de Poisson de FALABELLA por tramo horario (retornos simulados frente a observados).', 540, 330));
  k.push(P('**Validación.** Un test de Kolmogorov–Smirnov compara 5.000 retornos simulados con los observados. En los 90 pares ticker × tramo se rechaza al 5 % que ambas muestras provengan de la misma distribución (el mayor valor p es 0,0074); la mediana del estadístico es 0,178 en apertura, 0,172 en media jornada y 0,169 en cierre, con el mejor ajuste en SQM-B y el peor en IAM. La causa visible es que los retornos observados concentran mucha masa exactamente en cero y tienen colas más pesadas que la suma de 10 pasos de Poisson. El criterio fijado en el plan (valor p mayor que 0,05) no se cumple en ningún caso, y se reporta tal cual. La conclusión es que λ y θ calibrados sirven como **intensidades de entrada** del simulador, no como generador directo de retornos de 5 minutos.'));
  k.push(P('**Alternativa liviana.** Con esos parámetros se construyó un simulador de libro de 5 niveles por lado (`PoissonLOBSimulator`) cuya dinámica depende de λ⁺, λ⁻ y θ del ticker y tramo elegidos. Su cálculo de ejecución a mercado se verificó contra el ejemplo del Título I: comprar 8.000 acciones consumiendo 2.000 a $5.800, 5.500 a $5.810 y 500 a $5.820 da un precio promedio de $5.808,125. Este simulador se usa como entorno de prueba local y como Ejecutor de los benchmarks; no reemplaza a ABIDES-Gym como entorno final.'));
  k.push(callout('Limitaciones de la calibración', 'Sin Nivel 2, el signo del volumen, θ y el spread son aproximaciones construidas desde velas de 5 minutos, diez veces más gruesas que el paso del Ejecutor. Los 15 tickers de tier B concentran los parámetros menos confiables. Además, el snapshot termina el 21 de agosto de 2026, antes de la transición del IPSA a MSCI (1 de septiembre de 2026): los parámetros representan el régimen previo y conviene recalibrarlos antes de la evaluación final.', 'mid'));

  // ---- 5.4
  k.push(H2('5.4 Integración con ABIDES-Gym'));
  k.push(P('ABIDES-Gym (JP Morgan) es el simulador de libro de órdenes que propone la Parte I. Su entorno de ejecución de órdenes (`markets-execution-v0`) usa un formato propio de 3 acciones y unas 8 variables de estado, por lo que se construyó un adaptador (`ExecutionEnv27` y `EjecutorEnvAbides`) que lo conecta con el contrato de 27 variables y 240 acciones del proyecto. La lógica de traducción vive en un módulo independiente (`abides_bridge.py`) que no importa ABIDES y por eso puede probarse en cualquier equipo.'));
  k.push(tabCaption('Traducción de las acciones del Ejecutor a órdenes de ABIDES-Gym.'));
  k.push(table(['Tipo de orden', 'Efecto en ABIDES-Gym'], [
    ['Mercado', 'Cancela las órdenes vigentes y envía una orden de mercado por (fracción × inventario pendiente).'],
    ['Compra límite', 'Cancela las órdenes vigentes y envía una orden límite a (mejor oferta de compra + nivel × 1 centavo); el nivel 0 es pasivo y el 7 el más agresivo.'],
    ['Venta límite', 'Se interpreta como esperar (el proyecto solo modela compras).'],
  ], [2200, 6826]));
  k.push(GAP());
  k.push(P('Cada Ejecutor arranca en la hora real de su tramo y avanza en pasos de 30 segundos. La penalización por orden incompleta que ABIDES incluye de fábrica se anula, porque en este diseño esa función la cumple el parámetro λ de la recompensa del Maestro.'));
  k.push(P('**Verificación.** Una corrida de un episodio por tramo con acciones aleatorias, ejecutada con ABIDES-Gym real, terminó sin errores en los tres tramos:'));
  k.push(tabCaption('Episodios de prueba contra ABIDES-Gym (política aleatoria, meta de 500 acciones).'));
  k.push(table(['Tramo', 'Pasos', 'Recompensa total', 'Acciones ejecutadas'], [
    ['Apertura', '10', '−3,625', '494 / 500'],
    ['Media jornada', '10', '−4,810', '491 / 500'],
    ['Cierre', '6', '0,853', '500 / 500 (orden completa)'],
  ], [2400, 1400, 2400, 2826], { aligns: [AlignmentType.LEFT, C, C, C] }));
  k.push(GAP());
  k.push(P('Esta prueba solo demuestra que el circuito completo funciona; con una política aleatoria las recompensas no tienen valor evaluativo. Durante la puesta en marcha aparecieron dificultades concretas, que quedan registradas por su valor para quien reproduzca el trabajo:'));
  k.push(tabCaption('Problemas encontrados al integrar ABIDES-Gym y su solución.'));
  k.push(table(['Problema', 'Causa', 'Solución'], [
    ['Conflicto de versiones al instalar', 'ABIDES-Gym exige Python 3.9, gym 0.18.0 y numpy 1.22.0; instalaciones por separado hacían que ray y otras librerías actualizaran numpy y gym sin aviso.', 'Un único comando de instalación con todas las versiones fijadas, ray[tune] en lugar de ray[rllib] y un entorno Python 3.9 aislado (condacolab) en Google Colab.'],
    ['Error en la forma del estado crudo', 'Los decoradores de preprocesamiento del entorno padre no se aplicaban a los métodos redefinidos en la subclase.', 'Volver a declarar los decoradores como atributos de la subclase y aplicarlos a cada método redefinido.'],
    ['Falla de validación interna', 'ABIDES reformatea el estado como matriz de 27 × 1 y el espacio de observación declaraba 27.', 'Declarar el espacio con forma (27, 1).'],
  ], [2100, 3500, 3426], { size: 18 }));
  k.push(GAP());
  k.push(callout('Pendiente de verificar', 'Que el libro de la configuración `rmsc04` entregue al menos 5 niveles reales por lado (si trae menos, el vector se rellena con ceros) y la disponibilidad del método de semilla del entorno. Además, ABIDES-Gym es un repositorio archivado desde junio de 2025, sin soporte activo.', 'mid'));

  // ---- 5.5
  k.push(H2('5.5 Orquestador Maestro–Ejecutor'));
  k.push(P('La clase `MaestroEjecutorEnv` implementa el ciclo descrito en la sección 4.1 con la interfaz estándar `reset`, `step` y `close`. En cada paso construye el mensaje ASIGNAR, crea un entorno de Ejecutor nuevo para la ventana asignada, lo hace operar hasta completar la ventana y arma el REPORTE con la cantidad ejecutada, el precio promedio y el slippage parcial. Al final de la jornada calcula la recompensa terminal R_M del capítulo 3.'));
  k.push(P('El tipo de Ejecutor se inyecta como parámetro (`executor_env_factory`): puede ser el adaptador de ABIDES-Gym o el simulador de Poisson, sin cambiar el orquestador. Las variables de volatilidad y volumen promedio de S_M se leen de las variables ya calculadas por el pipeline de datos. Una prueba de humo ejecuta un episodio completo contra el simulador de Poisson y verifica que el inventario ejecutado se actualiza y que la recompensa terminal es un número finito.'));
  k.push(...C2.sec55tail());

  // ---- 5.6
  k.push(H2('5.6 Métricas de ejecución y comparación estadística'));
  k.push(P('El módulo de métricas implementa la medida principal del proyecto, el Implementation Shortfall: IS_total = (P_ejecución_promedio − P_referencia) × Q_total, donde P_referencia es el precio medio al momento de la decisión (arrival price). Reproduce el ejemplo de la Parte I: una compra de 8.000 acciones con precio inicial de $5.800 y precio promedio cercano a $5.808 arroja un costo del orden de $64.000.'));
  k.push(tabCaption('Funciones de evaluación disponibles.'));
  k.push(table(['Función', 'Para qué sirve'], [
    ['implementation_shortfall, slippage_bps, pct_cumplimiento', 'Costo en pesos, costo relativo en puntos base y fracción de la meta-orden ejecutada.'],
    ['evaluate_episode', 'Las tres métricas anteriores de un episodio, en el formato del resumen de episodio.'],
    ['compare_strategies', 'Compara dos muestras independientes: elige entre t-test de Welch y Mann–Whitney según la prueba de normalidad de Shapiro–Wilk.'],
    ['compare_paired', 'Compara dos estrategias sobre las mismas corridas con la prueba de Wilcoxon de rangos con signo y el tamaño de efecto d de Cohen pareado.'],
    ['compare_groups_kruskal', 'Compara tres o más estrategias con Kruskal–Wallis y, si resulta significativo, pruebas por pares (Mann–Whitney) con corrección de Bonferroni.'],
  ], [3300, 5726], { size: 18 }));
  k.push(GAP());

  // ---- 5.7 a 5.9 (cierre del sprint 4)
  k.push(...C2.sec57());
  k.push(...C2.sec58());
  k.push(...C2.sec59());

  // ====================================================================
  // CAPITULO 6
  // ====================================================================
  k.push(L.PB());
  k.push(H1('Capítulo 6. Experimentación y validación'));

  k.push(...C2.sec61());

  k.push(H2('6.2 Benchmarks TWAP y VWAP (tarea 2.3.4)'));
  k.push(P('Los benchmarks siguen las definiciones de la sección 4.1.4 de la Parte I. **TWAP** reparte la meta-orden en partes iguales a lo largo del tiempo (Q/T por periodo), ignorando las condiciones de liquidez. **VWAP** la reparte en proporción al perfil histórico de volumen. Se implementaron sobre los 13 periodos de 30 minutos de la jornada:'));
  k.push(...B([
    'TWAP asigna 1/13 de la orden (7,7 %) a cada periodo.',
    'VWAP pondera cada periodo por el volumen promedio real del IPSA en su tramo (datos de la sección 3.2): 5,9 % de la orden por periodo de apertura, 6,8 % por periodo de media jornada y 10,4 % por periodo de cierre.',
    'Dentro de cada periodo ambos ejecutan con una política deliberadamente simple: orden de mercado por todo el volumen asignado, sin táctica, coherente con la descripción de estas estrategias como reglas fijas.',
    'Se ejecutan sobre el mismo Ejecutor (simulador de Poisson calibrado) y se miden con las mismas métricas que usará el sistema PPO. Corren fuera del Maestro porque sus fracciones son continuas y no calzan con las 10 fracciones discretas de la red (decisión 6, sección 4.3).',
  ]));
  k.push(P('Se ejecutaron 10 meta-órdenes de prueba (5.000 acciones de FALABELLA, con 10 semillas distintas del simulador, de modo que cada estrategia se evalúa sobre las mismas 10 realizaciones de mercado):'));
  k.push(tabCaption('Implementation Shortfall de TWAP y VWAP (10 corridas pareadas, simulador de Poisson).'));
  k.push(table(['Estrategia', 'IS medio (pesos)', 'Desviación estándar'], [
    ['TWAP', '36.932', '189'],
    ['VWAP', '35.569', '211'],
  ], [3000, 3000, 3026], { aligns: [AlignmentType.LEFT, C, C] }));
  k.push(...figure(FIG('benchmarks_twap_vwap.png'), 'Implementation Shortfall de TWAP y VWAP: distribución por estrategia y valor por meta-orden.', 560, 260));
  k.push(P('VWAP tuvo menor costo que TWAP en promedio (3,8 % menos), y en las 10 corridas. La prueba de Wilcoxon de rangos con signo da p = 0,00195 (el mínimo posible con 10 pares, cuando todas las diferencias tienen el mismo signo) y el d de Cohen pareado es −21,1 (negativo porque la primera estrategia, TWAP, tuvo peor costo). Un tamaño de efecto tan grande se explica por la poca varianza entre corridas del simulador de Poisson (desviación de unos 200 pesos frente a una diferencia de medias de unos 1.360); con el ruido de ABIDES-Gym se espera un efecto menor, aunque la dirección debería mantenerse.'));
  k.push(P('Para la tesis, la lectura relevante es que **VWAP es el benchmark más exigente**: es contra él que el sistema PPO deberá demostrar la reducción de al menos 10 % que plantea la Parte I.'));
  k.push(callout('Limitaciones', 'Corrido contra el simulador de Poisson y no contra ABIDES-Gym, por lo que los valores absolutos no son comparables con jornadas reales. Las 10 meta-órdenes son semillas de un mismo tamaño y no las meta-órdenes oficiales de la tarea 2.3.3; el código se volverá a correr con ellas cuando estén definidas. Un TWAP o VWAP profesional podría además usar órdenes límite, algo que no se modeló.', 'mid'));

  k.push(H2('6.3 Metodología de la evaluación final'));
  k.push(P('La hipótesis del proyecto es que el sistema PPO reduce el Implementation Shortfall en al menos 10 % respecto de TWAP y VWAP con significancia estadística (α = 0,05). El plan contempla dos etapas de evaluación:'));
  k.push(...B([
    '**30 corridas con hiperparámetros ajustados** (sprint 6), con semillas distintas: media, desviación estándar e intervalo de confianza del 95 % del IS, con comparación frente a los benchmarks.',
    '**90 corridas de evaluación estadística** (sprint 7): 30 escenarios parametrizados de baja, media y alta liquidez, con 3 réplicas cada uno, para medir la robustez del sistema frente a condiciones distintas.',
  ]));
  k.push(P('Para comparar resultados se usarán las funciones de la sección 5.6: Wilcoxon para muestras pareadas (mismas corridas con distintas estrategias), Kruskal–Wallis con pruebas por pares y corrección de Bonferroni para comparar PPO, TWAP y VWAP a la vez, y el d de Cohen para reportar la magnitud del efecto además de su significancia.'));

  k.push(...C2.sec64());
  k.push(...C2.sec65());

  k.push(...D2.cap7());
  k.push(...D2.cap8());
  k.push(...D2.cap9());

  return k;
};
