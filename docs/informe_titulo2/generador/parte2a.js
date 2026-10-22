const L = require('./lib');
const { AlignmentType } = require('docx');
const FIG = (f) => `${__dirname}/fig/${f}`;
const { H1, H2, H3, H4, P, B, N, FORMULA, table, tabCaption, chip, callout, GAP, figure } = L;

module.exports = function parte2a() {
  const k = [];

  // ====================================================================
  // ESTADO GENERAL
  // ====================================================================
  k.push(H1('Estado general del proyecto'));
  k.push(P('Esta segunda parte documenta el desarrollo del sistema propuesto en el anteproyecto (Parte I). Se redactó a partir del repositorio del proyecto (github.com/Vatelfil/slippage), de los reportes versionados y de los resultados de las pruebas ejecutadas hasta el cierre del sprint 4 (acta de cierre del 19 de octubre de 2026 y documentos del repositorio al 22 de octubre). Cada afirmación sobre el funcionamiento del sistema se respalda en código, datos o pruebas que existen en el repositorio; lo que todavía no existe se declara expresamente como pendiente.'));
  k.push(P('El proyecto sigue la metodología Scrum con nueve sprints. Los sprints 1 y 2 (alistamiento, pipeline de datos y especificación del entorno) correspondieron a la fase de anteproyecto; los sprints 3 al 9 forman el Título II. A la fecha, los sprints 1 al 4 están cerrados: de las 19 tareas, 10 se cerraron cumpliendo su criterio, 6 quedaron *hechas con límite demostrado* (se ejecutaron y midieron, y el límite está escrito con su causa) y 3 entregables menores se cerraron en el PR de cierre. Una tarea del sprint 5 (benchmarks TWAP y VWAP) se adelantó porque no dependía de otras entregas. El resto del sprint 5, que está en curso, queda fuera de este informe.'));

  k.push(callout('Cómo leer esta parte', 'Los capítulos siguen la estructura del informe final definida en la sección 9 de la Parte I (capítulos 3 al 9). Las secciones o resultados que aún no existen aparecen en recuadros de color y se identifican como **pendientes**; no se reemplazan por estimaciones. Las tablas y figuras de esta parte se numeran con el prefijo II (por ejemplo, Tabla II-1).', 'info'));
  k.push(GAP());
  k.push(tabCaption('Estado de los componentes del sistema al cierre del sprint 4 (22 de octubre de 2026).'));
  k.push(table(['Componente', 'Estado', 'Detalle'], [
    ['Pipeline de datos del IPSA (limpieza y variables)', chip('COMPLETADO', 'ok'), '30 tickers, velas de 5 minutos, pruebas automáticas.'],
    ['Formalización de espacios de estado y acción', chip('COMPLETADO', 'ok'), 'S_M (7), S_E (27), A_M (40) y A_E (240) como espacios Gymnasium.'],
    ['Calibración de Poisson por ticker y tramo', chip('COMPLETADO', 'ok'), 'λ⁺, λ⁻ y θ para 30 tickers × 3 tramos; el KS rechaza (límite documentado).'],
    ['Simulador de Poisson (alternativa liviana)', chip('COMPLETADO', 'ok'), 'Entorno de prueba local, sin depender de ABIDES; corregido el nivel de precio de las órdenes límite.'],
    ['Integración con ABIDES-Gym (Ejecutor)', chip('COMPLETADO', 'ok'), 'Adaptador, fábrica calibrada y episodios completos en los 3 tramos.'],
    ['Orquestador Maestro–Ejecutor y redes Actor-Crítico', chip('COMPLETADO', 'ok'), 'Redes reales conectadas (PR #20); falta entrenarlas de forma completa (sprints 5 y 6).'],
    ['Algoritmo PPO (L_CLIP y GAE)', chip('COMPLETADO', 'ok'), 'Implementado y probado en corridas cortas (tarea 2.2.1).'],
    ['Métricas de ejecución y comparación estadística', chip('COMPLETADO', 'ok'), 'Implementation Shortfall y pruebas Wilcoxon, Kruskal–Wallis y d de Cohen.'],
    ['Benchmarks TWAP y VWAP', chip('COMPLETADO', 'ok'), 'Tarea del sprint 5 adelantada; resultados en el capítulo 6.'],
    ['Calibración de rmsc04 con datos del IPSA', chip('HECHO CON LÍMITE', 'mid'), 'FALABELLA, COPEC y ECL; el KS rechaza; volumen alto y spread bajo como límites.'],
    ['Validación estadística del simulador', chip('HECHO CON LÍMITE', 'mid'), 'Validación formal con 30 semillas: no válido según el criterio literal.'],
    ['Recompensas calibradas (λ y β)', chip('HECHO CON LÍMITE', 'mid'), 'λ = 0,05 y β = 0,0061796, ambos provisionales (β solo en la apertura).'],
    ['Entrenamiento PPO completo y evaluación final', chip('PENDIENTE', 'pend'), 'Sprints 5 al 7 del plan.'],
  ], [3000, 1550, 4476], { size: 18 }));

  // ====================================================================
  // CAPITULO 3
  // ====================================================================
  k.push(L.PB());
  k.push(H1('Capítulo 3. Definición del problema y análisis del entorno'));
  k.push(P('Este capítulo describe los datos de mercado sobre los que se construye el sistema, el comportamiento intradiario observado del IPSA y la formalización del problema de ejecución como un proceso de decisión de Markov (MDP) jerárquico.'));

  // ---- 3.1 Datos
  k.push(H2('3.1 Datos de mercado utilizados'));
  k.push(P('Los datos provienen de Yahoo Finance mediante la librería `yfinance`: velas OHLCV (apertura, máximo, mínimo, cierre y volumen) de 5 minutos para las 30 acciones del IPSA (tickers con sufijo `.SN`). La fuente solo entrega los últimos 60 días en esa resolución, por lo que el pipeline se ejecuta sobre *snapshots* fechados. Se usan dos: el del 23 de agosto de 2026 (ventana del 28 de mayo al 21 de agosto), sobre el que se calibró el modelo de Poisson, y el del 23 de septiembre de 2026 (30 de junio al 23 de septiembre), usado en la caracterización de mercado y en los benchmarks.'));
  k.push(P('El pipeline tiene cuatro etapas, cada una con su script y sus pruebas automáticas:'));
  k.push(...N([
    '**Validación y descarga.** Se verifica que los 30 tickers respondan y se descargan las velas de 5 minutos, registrando un manifiesto con los parámetros de la descarga.',
    '**Limpieza (tarea 1.2.1).** Se filtra la sesión de 09:30 a 15:55 (hora de Santiago), se reindexa cada día a una grilla fija de 78 velas, se imputan las velas sin transacción (relleno hacia adelante y hacia atrás) marcándolas con `is_imputed`, y se fusiona la vela de las 16:00 (subasta de cierre) con la de las 15:55.',
    '**Normalización.** Se aplica MinMaxScaler por ticker. Las columnas sin normalizar (`*_raw`, en pesos y número de acciones) se conservan, porque los cálculos en unidades reales (Implementation Shortfall, calibración de Poisson) deben usarlas.',
    '**Variables del Maestro (tarea 1.2.2).** Se calculan la volatilidad (desviación estándar móvil de 6 velas), el volumen promedio móvil y la sesión, que alimentan el vector de estado S_M.',
  ], 'dec_p2_pipeline'));
  k.push(P('Como medida de calidad se define la **cobertura pre-relleno**: la fracción de velas teóricas en que hubo al menos una transacción real. Los tickers con cobertura de al menos 60 % se clasifican como tier A y el resto como tier B.'));

  k.push(tabCaption('Resumen de calidad del snapshot del 23 de agosto de 2026 (fuente: reporte de limpieza versionado).'));
  k.push(table(['Indicador', 'Valor'], [
    ['Tickers procesados', '30 (todos responden en Yahoo Finance)'],
    ['Días hábiles por ticker', '60 (2026-05-28 a 2026-08-21), sin días descartados'],
    ['Velas por ticker (78 por día)', '4.680; total 140.400 filas'],
    ['Clasificación', '15 tickers tier A y 15 tier B (umbral de 60 % de cobertura)'],
    ['Mayor cobertura', 'LTM: 96,65 %'],
    ['Menor cobertura', 'IAM: 19,66 %'],
    ['Activo representativo (FALABELLA)', 'Tier A, cobertura 92,93 %; 7,20 % de velas imputadas'],
  ], [3600, 5426]));
  k.push(GAP());
  k.push(callout('Limitaciones de los datos', 'Los datos no incluyen el libro de órdenes de Nivel 2: spread, profundidad y cancelaciones solo pueden aproximarse a partir de velas de 5 minutos. Además, la ventana de 60 días que entrega la fuente es corta y no puede volver a descargarse una vez que pasa; los parquet de cada snapshot se conservan localmente y no en el repositorio.', 'mid'));

  // ---- 3.2 Caracterizacion
  k.push(H2('3.2 Comportamiento intradiario del mercado real'));
  k.push(P('El Título I anticipa que el mercado chileno concentra actividad y profundidad en la apertura y el cierre, y que la media jornada presenta spreads más amplios. Para contrastarlo se caracterizó el mercado por tramo horario sobre los 30 tickers (140.400 observaciones del snapshot de septiembre). Como el libro de órdenes no está disponible, el spread se aproxima con el rango máximo–mínimo de cada vela, expresado como porcentaje del precio de cierre.'));
  k.push(tabCaption('Perfil intradiario del IPSA (30 tickers, velas de 5 minutos).'));
  k.push(table(['Tramo', 'Spread relativo (%)', 'Volatilidad (desv. est. de retornos)', 'Volumen promedio por vela (acciones)'], [
    ['Apertura (09:30–11:00)', '0,138', '0,00251', '396.765'],
    ['Media jornada (11:00–14:00)', '0,112', '0,00156', '456.967'],
    ['Cierre (14:00–16:00)', '0,128', '0,00151', '698.419'],
  ], [2700, 1800, 2400, 2126], { aligns: [AlignmentType.LEFT, AlignmentType.CENTER, AlignmentType.CENTER, AlignmentType.CENTER] }));
  k.push(...figure(FIG('perfil_mercado_ipsa_real.png'), 'Spread relativo, volatilidad y volumen promedio por tramo horario (datos reales del IPSA).', 600, 300));
  k.push(P('Tres observaciones se desprenden de la tabla:'));
  k.push(...B([
    '**El spread es mayor en la apertura, no en la media jornada.** La media jornada es el tramo de menor spread (0,112 %). El patrón es decreciente a lo largo del día (forma de "L"), distinto de la forma de "U" que sugería la hipótesis inicial.',
    '**La volatilidad decrece de la apertura a la media jornada y se mantiene baja en el cierre**, sin el repunte de cierre que describe la literatura clásica.',
    '**El volumen crece hacia el cierre** (de 396.765 a 698.419 acciones por vela), en lugar de mostrar el patrón alto–bajo–alto esperado.',
  ]));
  k.push(P('Este resultado no se ajustó para calzar con la hipótesis. Fue confirmado de forma independiente por la calibración de Poisson (sección 5.3), que usa otro snapshot, otra metodología (estimador de Roll y rango máximo–mínimo, con winsorización) y llega a la misma conclusión: en el conjunto de los 30 tickers el rango máximo–mínimo solo es mayor en la media jornada que en la apertura y el cierre en 1 caso de 30. Una explicación plausible es el patrón de "L" frecuente en mercados de liquidez fina, aunque con datos de 5 minutos y sin Nivel 2 no puede descartarse que parte del efecto sea un artefacto del proxy usado.'));
  k.push(callout('Nota sobre los tramos horarios', 'Esta caracterización usa los cortes de la variable `sesion` del vector S_M (11:00 y 14:00). Los Ejecutores y la calibración de Poisson definen la apertura hasta las 11:30. Ambas definiciones están documentadas y unificarlas es una tarea de revisión pendiente; no altera las conclusiones de dirección (el spread decrece a lo largo del día en ambos casos).', 'info'));

  // ---- 3.3 Formalizacion
  k.push(H2('3.3 Formalización del problema como MDP jerárquico'));
  k.push(P('El problema se modela como dos procesos de decisión acoplados, siguiendo la sección 4.2 de la Parte I: un Agente Maestro que decide cada 30 minutos cuánto y durante cuánto tiempo ejecutar, y tres Agentes Ejecutores (apertura, media jornada y cierre) que deciden cada 30 segundos cómo ejecutar el volumen asignado. Los factores de descuento son γ_M = 0,99 para el Maestro y γ_E = 0,95 para los Ejecutores. La jornada completa (09:30 a 16:00, 390 minutos) equivale a un máximo de 13 decisiones del Maestro.'));

  k.push(H3('3.3.1 Estado del Maestro (S_M, 7 variables)'));
  k.push(tabCaption('Vector de estado del Agente Maestro (todas las variables normalizadas).'));
  k.push(table(['Variable', 'Rango', 'Fuente', 'Descripción'], [
    ['q_t', '[0, 1]', 'Interna', 'Fracción de la meta-orden aún sin ejecutar.'],
    ['tau_t', '[0, 1]', 'Reloj', 'Fracción transcurrida de la jornada (09:30–16:00).'],
    ['n_slices', '[0, 1]', 'Interna', 'Decisiones emitidas respecto del máximo de 13.'],
    ['volatilidad', '[0, 1]', 'yfinance', 'Volatilidad del precio de cierre, ventana móvil de 6 velas.'],
    ['vol_promedio', '[0, 1]', 'yfinance', 'Volumen promedio, ventana móvil de 6 velas.'],
    ['OBI_agregado', '[-1, 1]', 'Simulador', 'Desbalance entre volumen comprador y vendedor del libro. Hoy vale 0,0 (ver nota).'],
    ['sesion', '[0, 1]', 'Reloj', 'Tramo horario: 0,0 apertura, 0,5 media jornada, 1,0 cierre.'],
  ], [1700, 1000, 1300, 5026]));
  k.push(GAP());
  k.push(P('La variable `OBI_agregado` se mantiene en 0,0 de forma deliberada: el Maestro no tiene conexión propia al simulador, y definir cómo agregarla a partir de los tres Ejecutores es una decisión de diseño abierta que no se tomó por defecto.'));

  k.push(H3('3.3.2 Acción del Maestro (A_M, 40 combinaciones)'));
  k.push(P('La acción es discreta y combina dos decisiones: la fracción del inventario restante que se asigna al siguiente tramo, α_t ∈ {0,05; 0,10; …; 0,50} (10 valores), y la ventana de ejecución, ventana_min ∈ {1, 5, 10, 15} minutos (4 valores). El espacio resultante es MultiDiscrete([10, 4]), equivalente a 40 acciones planas. La cantidad asignada es q_slice = α_t × (Q_total − Q_ejecutado).'));

  k.push(H3('3.3.3 Estado del Ejecutor (S_E, 27 variables)'));
  k.push(tabCaption('Vector de estado de cada Agente Ejecutor.'));
  k.push(table(['Grupo', 'Variables', 'Dim.'], [
    ['Privado', 'q_slice, q_pendiente, tau_slice', '3'],
    ['Libro de compra (bid)', 'Precios y volúmenes de los 5 mejores niveles', '10'],
    ['Libro de venta (ask)', 'Precios y volúmenes de los 5 mejores niveles', '10'],
    ['Mercado', 'spread_t, OBI_t, tasa_ordenes, P_mid', '4'],
    [{ t: 'Total', bold: true }, '', { t: '27', bold: true }],
  ], [2400, 5626, 1000], { aligns: [AlignmentType.LEFT, AlignmentType.LEFT, AlignmentType.CENTER] }));
  k.push(GAP());
  k.push(P('Las variables enumeradas en la Parte I (3 privadas, 5 niveles de precio y volumen por lado, spread, desbalance, tasa de llegada y precio medio) suman 27. El esquema inicial del sprint 1 declaraba 26 por un error de conteo, que se corrigió el 23 de septiembre; el código calcula la dimensión a partir de las variables listadas, de modo que no puede volver a divergir sin advertencia.'));

  k.push(H3('3.3.4 Acción del Ejecutor (A_E, 240 combinaciones)'));
  k.push(P('Cada 30 segundos el Ejecutor elige un tipo de orden (compra límite, venta límite o mercado), qué fracción de su inventario pendiente enviar (10 niveles, de 0,1 a 1,0) y a qué nivel de precio colocarla (8 niveles, del más pasivo al más agresivo). El espacio es MultiDiscrete([3, 10, 8]), equivalente a 240 acciones planas. Como el proyecto solo modela compras, la venta límite se interpreta como esperar.'));

  k.push(H3('3.3.5 Funciones de recompensa'));
  k.push(P('La métrica objetivo es el Implementation Shortfall (Perold, 1988), definido en la sección 4.1.3 de la Parte I. Las recompensas de cada nivel son:'));
  k.push(FORMULA('R_M = − IS_total − λ · max(0, Q_pendiente) · P_mid_cierre'));
  k.push(FORMULA('R_E = (P_mid,t − P_ejec,t) · q_ejec − β · σ²_precio · q_ejec'));
  k.push(P('R_M es una recompensa dispersa que se entrega solo al final de la jornada, y R_E es densa, una por cada paso de 30 segundos. Los coeficientes λ (penalización por inventario sin ejecutar) y β (aversión al riesgo) se calibraron experimentalmente en el sprint 4: λ = 0,05 y β = 0,0061796, ambos provisionales (sección 5.9).'));

  // ====================================================================
  // CAPITULO 4
  // ====================================================================
  k.push(L.PB());
  k.push(H1('Capítulo 4. Diseño de la solución'));
  k.push(H2('4.1 Arquitectura del sistema'));
  k.push(P('El sistema se organiza en tres capas: coordinación (Maestro), ejecución (tres Ejecutores) y simulación (ABIDES-Gym o el simulador de Poisson). La figura siguiente resume el flujo.'));
  k.push(...figure(FIG('arquitectura.png'), 'Arquitectura del sistema y flujo de mensajes entre el Maestro, los Ejecutores y el mercado simulado.', 560, 420));
  k.push(P('Un episodio corresponde a una jornada bursátil y se desarrolla así:'));
  k.push(...N([
    '`reset()`: se fija el reloj en las 09:30, se reinician los contadores (inventario ejecutado, número de decisiones) y se calcula el estado inicial S_M.',
    'El Maestro observa S_M y decide (α_t, ventana_min). El entorno calcula q_slice y envía un mensaje **ASIGNAR** al Ejecutor cuyo tramo horario coincide con la hora actual.',
    'El Ejecutor opera durante ventana_min × 2 pasos de 30 segundos, observando S_E y enviando órdenes al mercado simulado.',
    'Al terminar la ventana, el Ejecutor devuelve un mensaje **REPORTE**. El entorno actualiza el inventario ejecutado, avanza el reloj 30 minutos y recalcula S_M.',
    'Se repite hasta las 16:00. Al final se calcula la recompensa terminal R_M y se guardan los registros del episodio.',
  ], 'dec_p2_ciclo'));

  k.push(tabCaption('Contenido de los mensajes entre el Maestro y el Ejecutor activo.'));
  k.push(table(['Mensaje', 'Campo', 'Significado'], [
    ['ASIGNAR (Maestro → Ejecutor)', 'q_slice', 'Cantidad de acciones asignada a la ventana (no una fracción).'],
    ['', 'ventana_min', 'Duración de la ventana: 1, 5, 10 o 15 minutos.'],
    ['', 'timestamp_inicio', 'Instante de inicio de la ventana.'],
    ['REPORTE (Ejecutor → Maestro)', 'q_ejecutado', 'Acciones realmente ejecutadas (puede ser menor que q_slice).'],
    ['', 'p_promedio', 'Precio promedio ponderado por volumen de la ventana.'],
    ['', 'slippage_parcial', '(p_promedio − P_referencia) × q_ejecutado, en pesos.'],
    ['', 'razon_termino', 'Ventana completada o inventario agotado.'],
  ], [2700, 2000, 4326]));
  k.push(GAP());
  k.push(P('Tres escalas de tiempo conviven en cada episodio: las velas históricas de 5 minutos (6 por decisión del Maestro), las decisiones del Maestro cada 30 minutos (13 por jornada) y las del Ejecutor cada 30 segundos. El simulador puede avanzar a nivel de segundo, pero el Ejecutor solo lo consulta cada 30 segundos.'));

  k.push(H2('4.2 Redes Actor-Crítico'));
  k.push(P('Tanto el Maestro como los Ejecutores usan una red Actor-Crítico implementada en PyTorch con un tronco compartido: dos capas ocultas de 256 neuronas con activación ReLU, de las que salen dos cabezas lineales. La cabeza del actor entrega los logits de una distribución categórica sobre las acciones; la del crítico entrega un valor escalar V(s). La política se muestrea con `torch.distributions.Categorical`.'));
  k.push(tabCaption('Dimensiones de las redes Actor-Crítico.'));
  k.push(table(['Red', 'Entrada', 'Salida del actor', 'Salida del crítico'], [
    ['Maestro (MasterActorCritic)', '7 (S_M)', '40 logits (10 fracciones × 4 ventanas)', '1'],
    ['Ejecutor (ExecutorActorCritic)', '27 (S_E)', '240 logits (3 × 10 × 8)', '1'],
  ], [2800, 1400, 3200, 1626]));
  k.push(GAP());
  k.push(P('Que ambas redes tengan una única cabeza categórica obligó a definir las conversiones entre el índice plano que produce la red y el formato que espera cada entorno (decisión 3 de la sección 4.3). Dos desviaciones respecto de la especificación original del plan quedaron documentadas: la red del Maestro usa 256 neuronas por capa (el plan indicaba 64), sin inicialización de Xavier ni Dropout y con una sola cabeza de 40 salidas, y las redes de los Ejecutores son totalmente discretas (240 salidas) con 27 entradas en vez de 26. La fábrica `make_hierarchy()` crea el Maestro y los tres Ejecutores. Los hiperparámetros de arquitectura (tamaño y profundidad) se ajustarán en el sprint 6.'));

  k.push(H2('4.3 Decisiones de diseño y su justificación'));
  k.push(P('Durante el desarrollo se tomaron decisiones que condicionan el resto del trabajo. La tabla siguiente las resume, con las alternativas consideradas y la razón de cada elección.'));
  k.push(tabCaption('Decisiones de diseño principales.'));
  k.push(table(['Decisión', 'Alternativas', 'Justificación'], [
    ['**1.** Extender ABIDES-Gym mediante un adaptador que habla el formato del proyecto (27 variables y 240 acciones).',
     'Reducir el diseño del proyecto al formato nativo de ABIDES-Gym (3 acciones y unas 8 variables).',
     'Mantiene la fidelidad al diseño aprobado en la Parte I en lugar de simplificarlo por comodidad técnica. Costo: hay que traducir acciones y estados (sección 5.4).'],
    ['**2.** Construir un simulador de Poisson como alternativa liviana, calibrado con datos reales, y usarlo como entorno de prueba.',
     'Esperar a que ABIDES-Gym estuviera instalado para continuar.',
     'ABIDES-Gym es difícil de instalar (repositorio archivado, versiones muy específicas). Con el simulador se evitó bloquear el desarrollo; es la alternativa que el propio Título I (sección 4.3.3) contemplaba.'],
    ['**3.** Usar una cabeza categórica única en cada red y convertir índices planos con `decode_flat` y `encode_flat`.',
     'Cabezas separadas por componente de la acción (tipo, volumen, precio).',
     'Una distribución categórica única es más simple de entrenar con PPO y de analizar (entropía, probabilidades). Se pierde la factorización por componente.'],
    ['**4.** Discretizar completamente la acción del Ejecutor (MultiDiscrete([3, 10, 8])).',
     'Acción híbrida: tipo y precio discretos, volumen continuo (Parte I).',
     'Es consistente con la cabeza categórica única y evita mezclar distribuciones discretas y continuas. El volumen queda en 10 niveles de 0,1 a 1,0.'],
    ['**5.** Interpretar la venta límite como esperar.',
     'Modelar ventas.',
     'El proyecto solo modela compras de meta-órdenes; así el espacio de acción conserva su forma sin agregar un comportamiento fuera de alcance.'],
    ['**6.** Ejecutar TWAP y VWAP fuera del Maestro, como reglas simples.',
     'Forzarlos a usar las 10 fracciones discretas del Maestro.',
     'La discretización introduciría un error ajeno a la definición clásica (fracciones continuas de Q/T). Reutilizan el mismo Ejecutor y las mismas métricas, de modo que la comparación sigue siendo directa.'],
    ['**7.** Dejar λ y β como parámetros por calibrar, sin fijar un valor provisional.',
     'Adoptar valores razonables de la literatura.',
     'El Título I establece que se calibran experimentalmente. Fijarlos antes de tener corridas reales sesgaría los resultados.'],
    ['**8.** Validar el simulador comparando la forma del spread entre tramos, no su magnitud.',
     'Comparar valores absolutos.',
     'El simulador aún no está calibrado al IPSA y sus valores están normalizados; las magnitudes no son comparables todavía.'],
    ['**9.** Calibrar Poisson excluyendo la subasta de cierre y winsorizando el volumen en el percentil 99.',
     'Usar todo el volumen observado.',
     'Las operaciones en bloque y la subasta no son flujo continuo de órdenes; sin winsorizar, λ⁺ de apertura de FALABELLA pasa de 5,37 a 29,06.'],
    ['**10.** Mantener la fórmula de R_E del Título I con un β pequeño y una regla de vigilancia (decisión D3).',
     'Cobrar el riesgo sobre el inventario pendiente; apagar el término de riesgo (β = 0); agregar un premio por cumplimiento.',
     'Es la opción más fiel al Título I y la calibración muestra que el riesgo solo puede pesar poco (con β alto la red deja de operar). La opción de riesgo sobre lo pendiente queda implementada y se activa si el cumplimiento baja del 95 %.'],
    ['**11.** Fijar las reglas de adopción y los criterios de validación antes de ver los datos, y reportar los resultados desfavorables.',
     'Ajustar el criterio después de ver los resultados.',
     'Evita el sesgo de elegir lo que luce bien. Gracias a esto, la grilla de actividad baja y los megashocks se descartaron con una regla explícita y los límites del simulador quedaron escritos.'],
    ['**12.** En COPEC y ECL usar 3 agentes de momentum en vez de 12 y ajustar `fund_vol` por tramo.',
     'Mantener los 12 agentes por defecto; apagar el momentum.',
     'Con 250 a 500 agentes de ruido los 12 de momentum desestabilizaban el mercado; 3 mantiene la proporción de FALABELLA y conserva el volumen que aporta el momentum.'],
  ], [3000, 2400, 3626], { size: 18 }));
  k.push(GAP());

  return k;
};
