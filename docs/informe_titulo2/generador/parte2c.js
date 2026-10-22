// Contenido nuevo de la Parte II al cierre del Sprint 4 (22 oct 2026): calibracion de rmsc04, recompensas,
// validacion formal del simulador, PPO, pruebas, resultados, discusion y conclusiones.
const L = require('./lib');
const { AlignmentType } = require('docx');
const FIG = (f) => `${__dirname}/fig/${f}`;
const { H2, H3, P, B, FORMULA, table, tabCaption, chip, callout, GAP, figure } = L;
const C = AlignmentType.CENTER;

// ---------------------------------------------------------------- 5.5 (cierre)
function sec55tail() {
  const k = [];
  k.push(callout('Estado al cierre del sprint 4', 'Las redes reales ya están conectadas al orquestador: la fábrica `make_hierarchy()` crea el Maestro y los tres Ejecutores, y `make_executor_policy_fn()` entrega a cada tramo su propia red (corrección que agregó la revisión de BF el 18 de octubre, porque sin ella el orquestador usaba una sola red para los tres tramos). Con esto, `maestro_policy` y `executor_policy` dejan de ser reemplazos aleatorios y pasan a ser las políticas aprendidas con PPO (PR #20). Lo que sigue pendiente es **entrenarlas** de forma completa (sprints 5 y 6).', 'info'));
  k.push(GAP());
  return k;
}

// ---------------------------------------------------------------- 5.7 PPO
function sec57() {
  const k = [];
  k.push(H2('5.7 Algoritmo PPO (tarea 2.2.1)'));
  k.push(P('El PPO (Schulman et al., 2017) se implementó en PyTorch para ambos niveles de la jerarquía (responsable: Mauricio Reynoso, PR #20). La actualización de la política maximiza el objetivo recortado L_CLIP, que limita cuánto puede cambiar la política en cada paso, junto con la pérdida del crítico (error cuadrático medio del valor) y una bonificación de entropía que mantiene la exploración. Las ventajas se calculan con GAE (estimación generalizada de ventaja) con un buffer de experiencias que respeta los límites entre episodios.'));
  k.push(...B([
    '**Recolección:** el agente juega episodios completos y guarda estado, acción, log-probabilidad, recompensa y valor en un buffer.',
    '**Ventajas:** GAE con γ y λ configurables (γ = 0,95 en los Ejecutores y 0,99 en el Maestro).',
    '**Optimización:** varias épocas sobre minibatches, con recorte del gradiente y registro de la divergencia KL y de la fracción de actualizaciones recortadas.',
    '**Registro:** cada actualización deja pérdidas del actor y del crítico, entropía, retorno medio, KL y fracción recortada en un CSV, y se guardan puntos de control periódicos.',
  ]));
  k.push(P('Dos ajustes de Paolo Sepúlveda sobre esa implementación facilitaron su uso: `torch` se importa solo cuando se usa (para que los módulos de análisis y las pruebas que no entrenan no dependan de él) y las semillas quedan fijadas para que una corrida sea reproducible. Un corredor de prueba corta (`experiments/test_ppo_short_run.py`) verifica que el ciclo completo corre y registra métricas.'));
  k.push(tabCaption('Hiperparámetros usados en las corridas de PPO del sprint 4 (fase 2 de la elección de β).'));
  k.push(table(['Parámetro', 'Valor', 'Parámetro', 'Valor'], [
    ['Tasa de aprendizaje', '3 × 10⁻⁴', 'Épocas por actualización', '4'],
    ['γ (Ejecutores)', '0,95', 'Tamaño de minibatch', '64'],
    ['λ de GAE', '0,95', 'Episodios por actualización', '10'],
    ['Clip ε', '0,2', 'Coef. de entropía', '0,01'],
    ['Coef. del crítico', '0,5', 'Norma máxima del gradiente', '0,5'],
  ], [2500, 2000, 2700, 1826], { aligns: [AlignmentType.LEFT, C, AlignmentType.LEFT, C] }));
  k.push(GAP());
  k.push(callout('Alcance', 'El sprint 4 pedía **implementar** el PPO (2.2.1), no entrenar el sistema completo. El ajuste de hiperparámetros corresponde al sprint 6 (tareas 3.1.x). Los valores de la tabla son iniciales y se usaron para entrenar un Ejecutor durante la elección de β (sección 5.9).', 'info'));
  return k;
}

// ---------------------------------------------------------------- 5.8 rmsc04
function sec58() {
  const k = [];
  k.push(H2('5.8 Calibración de rmsc04 con datos del IPSA (tarea 2.2.4)'));
  k.push(P('`rmsc04` es la configuración de referencia de ABIDES-Gym: un mercado de fondo con 1.000 agentes de ruido, 102 de valor, 12 de momentum y 2 creadores de mercado, cuyos parámetros por defecto describen una acción genérica de 1.000 dólares. La tarea 2.2.4 (responsable: Benjamín Farias; plantilla inicial de Paolo Sepúlveda) ajusta esos parámetros para que el mercado simulado **aproxime**, con datos reales de FALABELLA (snapshot del 23 de agosto de 2026), los objetivos que dejó la calibración de Poisson: volatilidad de 5 minutos, volumen por vela y participación de cada tramo en el volumen del día.'));
  k.push(tabCaption('Origen de los parámetros de rmsc04 calibrados.'));
  k.push(table(['Parámetro', 'Valor y fuente'], [
    ['`r_bar` (nivel de precio)', 'Mediana de los precios de cierre del snapshot (5.969,75 pesos), expresada en décimos de peso para que el tick del simulador (1 unidad) coincida con el incremento mínimo observado (0,1 pesos).'],
    ['`fund_vol` (volatilidad del valor fundamental)', 'Derivada por tramo del desvío de los retornos de 5 minutos (3,70e-4, 2,43e-4 y 2,27e-4 en apertura, media jornada y cierre). Corrige un error de unidades de la configuración inicial: el oráculo mide el tiempo en nanosegundos.'],
    ['`kappa_oracle`', 'Valor por defecto. Un test de razón de varianzas mostró reversión en los retornos de 5 minutos, pero con la forma del rebote entre precios de compra y venta y no la de un fundamental que revierte.'],
    ['`megashock_*`', 'Valor por defecto: no actúan dentro de una jornada.'],
    ['`mm_pov`, `mm_window_size`, `mm_level_spacing`, `num_noise_agents`, `lambda_a`', 'Se buscan por simulación (método de momentos simulado), porque sin Nivel 2 no hay dato directo de la liquidez del creador de mercado ni de la actividad de los agentes.'],
  ], [3000, 6026], { size: 18 }));
  k.push(GAP());
  k.push(P('**Búsqueda.** Una grilla de 27 combinaciones con 3 semillas por tramo, un refinamiento local y una validación con **30 semillas nuevas** por tramo (101 a 130). La regla de adopción y la función de pérdida se fijaron antes de ver los datos. La primera validación con 10 semillas no rechazaba ningún tramo, pero era falta de potencia estadística (el umbral D crítico valía 0,085 a 0,098 con 230 a 300 retornos); por eso se amplió a 30 semillas antes de dar el resultado por bueno.'));
  k.push(tabCaption('Prueba de Kolmogorov–Smirnov de los retornos de 5 minutos simulados frente a los reales (FALABELLA, 30 semillas por tramo).'));
  k.push(table(['Tramo', 'n sim / n real', 'D', 'p', 'D / D crítico', 'Rechaza al 5 %'], [
    ['Apertura', '690 / 1.111', '0,064', '0,058', '0,97', 'No (al borde)'],
    ['Media jornada', '900 / 1.690', '0,074', '0,003', '1,32', 'Sí'],
    ['Cierre', '690 / 1.252', '0,099', '0,0003', '1,54', 'Sí'],
  ], [2000, 1700, 1000, 1200, 1500, 1626], { aligns: [AlignmentType.LEFT, C, C, C, C, C] }));
  k.push(...figure(FIG('rmsc04_volatilidad.png'), 'Volatilidad de 5 minutos simulada y real de FALABELLA con la calibración (promedio de 30 semillas por tramo).', 440, 260));
  k.push(P('La volatilidad quedó dentro de un 10 % del objetivo en los tres tramos. El KS rechaza en media jornada y cierre, de modo que la meta del plan (p mayor que 0,05) no se cumple en dos de tres tramos; aun así, la distancia máxima entre distribuciones (D de 0,06 a 0,10) es menor o igual que la del modelo de Poisson calibrado en la etapa anterior (D de 0,09 a 0,12), es decir, el simulador **aproxima** la distribución de retornos pero no se puede afirmar que sea la misma.'));
  k.push(tabCaption('Momentos simulados frente al objetivo real (FALABELLA; apertura / media jornada / cierre).'));
  k.push(table(['Magnitud', 'Simulado / objetivo', 'Lectura'], [
    ['Volatilidad de 5 min (bps)', '34,0 / 34,0 · 20,0 / 22,3 · 20,5 / 20,9', 'Dentro del 10 % en los tres tramos'],
    ['Volumen mediano por vela', '11.268 / 7.576 · 11.471 / 9.396 · 12.399 / 11.964', 'Sobre el real: +49 %, +22 % y +4 %'],
    ['Spread mediano (bps)', '0,23 · 0,17 · 0,17 frente a 4 a 35 en los proxies reales', 'Entre 20 y 100 veces menor: límite principal'],
    ['Volatilidad máxima en la apertura', 'Se cumple (por construcción: `fund_vol` por tramo)', 'El volumen creciente (+10 % frente a +58 % real) no se reproduce'],
  ], [2600, 3900, 2526], { size: 18 }));
  k.push(GAP());
  k.push(P('**Grilla de actividad hacia abajo (18 de octubre).** Como el volumen simulado quedaba por encima del real, se probó bajar la actividad (100 %, 75 %, 50 % y 25 % de los agentes de ruido y de su tasa de llegada). Con la regla fijada antes de ver los datos (volatilidad a ±15 % en los tres tramos y ningún tramo sobre 200 bps), **ningún nivel se adopta**: el de 75 % empata con el control al quitar el spread, el de 50 % triplica la volatilidad de la tarde y el de 25 % rompe el mercado. El volumen alto en la apertura queda como **límite demostrado**: en rmsc04 el flujo de los agentes de valor sostiene a la vez el volumen y la volatilidad.'));
  k.push(P('**Megashocks.** Un sondeo adicional (Paolo Sepúlveda) probó hacer más frecuentes los saltos del valor fundamental para acercar las colas de los retornos. Con el valor por defecto casi no ocurren saltos; al aumentarlos, la curtosis simulada explota (17 a 175 frente a 3 a 6 reales) y la distancia del KS empeora. Ningún candidato cumple la regla de adopción y se conserva la configuración de Benjamín.'));
  k.push(H3('Extensión a COPEC y ECL'));
  k.push(P('La calibración se replicó para COPEC y ECL (Paolo Sepúlveda, PR #36, 19 de octubre). La grilla de actividad baja dejaba 12 agentes de momentum por defecto, que con solo 250 agentes de ruido desestabilizaban el mercado: en ECL, 9, 13 y 13 de 30 corridas (por tramo) tenían movimientos de más de 10 % del precio en un tramo. Un diagnóstico de un cambio por vez mostró que el problema no era el creador de mercado ni el valor fundamental, sino el momentum: sin esos agentes, 0 de 5 corridas se desbocaban. Se fijaron **3 agentes de momentum** (la misma proporción que FALABELLA: 12 con 1.000 de ruido), 500 agentes de ruido y un ajuste de `fund_vol` por tramo.'));
  k.push(tabCaption('Resultado de la calibración de COPEC y ECL (30 semillas por tramo; apertura / media jornada / cierre).'));
  k.push(table(['', 'COPEC', 'ECL'], [
    ['Corridas desbocadas (30 semillas)', '0 / 0 / 0 (antes 0 / 7 / 7)', '0 / 0 / 0 (antes 9 / 13 / 13)'],
    ['Volatilidad simulada frente a real (bps)', '32,1 / 19,8 / 24,6 frente a 31,8 / 21,4 / 24,8', '41,0 / 34,5 / 34,9 frente a 41,8 / 35,2 / 36,2'],
    ['KS, D / D crítico', '1,43 / 1,75 / 2,40', '1,66 / 2,22 / 1,85'],
    ['Tamaño de efecto (g de Hedges)', '0,18 / 0,11 / 0,27', '0,28 / 0,20 / 0,22'],
    ['Volumen por vela frente al real', '−15 % / −35 % / −45 %', '−20 % / −39 % / −43 %'],
    ['Veredicto formal (criterio literal del plan)', chip('NO VÁLIDO', 'mid'), chip('NO VÁLIDO', 'mid')],
  ], [3300, 2900, 2826], { size: 18 }));
  k.push(GAP());
  k.push(callout('Límites de la calibración (se declaran)', '**1.** El spread simulado (de 1 a 2 ticks, entre 0,2 y 1,1 bps) es mucho menor que los proxies reales: el costo absoluto de ejecución queda subestimado, aunque la comparación **relativa** entre estrategias sigue siendo informativa. **2.** El KS rechaza en dos de tres tramos en FALABELLA y en los seis de COPEC y ECL. **3.** El volumen alto en la apertura queda como límite demostrado. **4.** `fund_vol` es constante por tramo. **5.** Un solo régimen de mercado (previo a la transición del IPSA a MSCI) y, en COPEC y ECL, el ajuste de `fund_vol` se calculó con las mismas semillas con las que se validó, por lo que la cercanía de la volatilidad es en parte por construcción.', 'mid'));
  k.push(GAP());
  return k;
}

// ---------------------------------------------------------------- 5.9 recompensas
function sec59() {
  const k = [];
  k.push(H2('5.9 Funciones de recompensa calibradas (tareas 2.2.2 y 2.2.3)'));
  k.push(H3('Recompensa del Maestro: calibración de λ (tarea 2.2.2)'));
  k.push(P('La recompensa terminal del Maestro es R_M = −IS_total − λ · max(0, Q_pendiente) · P_mid_cierre. El coeficiente λ penaliza el inventario que queda sin ejecutar al cierre. Mauricio Reynoso evaluó cinco valores (λ ∈ {0,01; 0,05; 0,10; 0,50; 1,00}) en 100 simulaciones de jornadas completas (13 decisiones), con cuatro tamaños de meta-orden (1.000 a 20.000 acciones) y 5 corridas por combinación, sobre el simulador de Poisson con los parámetros reales del IPSA.'));
  k.push(tabCaption('Calibración de λ del Maestro (promedio de las simulaciones por valor de λ).'));
  k.push(table(['λ', 'Q pendiente (media)', 'IS medio (pesos)', 'Penalización media (pesos)', 'Desv. est. de R_M', 'Penalización / IS'], [
    ['0,01', '370', '79.775', '21.495', '85.914', '0,23×'],
    [{ t: '0,05', bold: true }, '349', '79.317', '101.233', '179.975', { t: '1,06×', bold: true }],
    ['0,10 (anterior)', '366', '80.446', '212.460', '340.232', '2,34×'],
    ['0,50', '199', '82.885', '577.903', '811.476', '6,18×'],
    ['1,00', '310', '83.721', '1.798.185', '2.330.449', '20,79×'],
  ], [1300, 1500, 1500, 1800, 1500, 1426], { aligns: [AlignmentType.LEFT, C, C, C, C, C], size: 18 }));
  k.push(...figure(FIG('lambda_maestro.png'), 'Razón entre la penalización por inventario y el slippage para cada λ (escala logarítmica).', 400, 240));
  k.push(P('Con λ bajo (0,01) la penalización equivale a solo el 23 % del slippage y al agente le conviene dejar acciones sin comprar para evitar cruzar el spread; con λ alto (0,50 o más) la penalización domina la recompensa y las desviaciones de R_M son tan grandes que desestabilizarían el entrenamiento del crítico. Se fijó **λ = 0,05**, donde la penalización y el costo tienen la misma escala (1,06 veces). **Es provisional:** se calibró por escala con una política sin entrenar y debe revalidarse cuando el Maestro tenga entrenamiento real.'));
  k.push(H3('Recompensa de los Ejecutores (tarea 2.2.3)'));
  k.push(P('La recompensa de los Ejecutores sigue la fórmula del Título I, R_E = (P_mid − P_ejec) · q_ejec − β · σ²_precio · q_ejec. Benjamín Farias definió σ²_precio como la varianza muestral del precio medio en una ventana móvil de 20 pasos (10 minutos) **causal** (en el paso t solo usa precios observados hasta t − 1; una prueba aplica un salto de precio en t = 25 y comprueba que σ² no cambia hasta t = 26) y **normalizada por el largo de la ventana**, de modo que estima la varianza del cambio de precio en un paso. La recompensa se expresa en pesos por acción del slice. Antes de esta tarea el término de riesgo valía cero en los dos entornos.'));
  k.push(P('Con 60 episodios por tramo, la distribución de R_E (análisis de Paolo Sepúlveda) muestra una escala muy distinta entre tramos (el desvío baja de 2,8 en la apertura a 1,2 en el cierre) y colas pesadas y asimétricas en la apertura (asimetría cercana a −3 y curtosis en exceso de 15). Sin normalizar, pocos episodios dominarían el gradiente y un mismo coeficiente de aprendizaje no serviría igual para los tres Ejecutores; por eso se usa un normalizador móvil que deja la salida dentro de [−1, 1].'));
  k.push(P('**Elección de β.** Se hizo en dos fases. En la fase 1 (Benjamín Farias) se calculó β∗, el valor con el que el riesgo y el costo de precio pesan lo mismo en el agregado: 0,0618 con políticas heurísticas en ABIDES calibrado (0,6077 en el simulador de Poisson, que no sirve para calibrar el nivel de β porque su β∗ depende del prior de σ²). En la fase 2 (Paolo Sepúlveda) se entrenó un Ejecutor con PPO en ABIDES calibrado, tramo de apertura, durante 300 episodios por valor de β y se evaluó con 30 semillas nuevas.'));
  k.push(tabCaption('Fase 2 de la elección de β (PPO en ABIDES, apertura, 30 semillas de evaluación).'));
  k.push(table(['β', 'Múltiplo de β∗', 'Slippage medio (bps)', 'Error estándar', 'Orden completada'], [
    ['0,00000', '0× (control)', '5,12', '3,47', '97,3 %'],
    [{ t: '0,00618', bold: true }, { t: '0,1×', bold: true }, '4,71', '2,79', { t: '100 %', bold: true }],
    ['0,01854', '0,3×', '5,77', '2,42', '34,1 %'],
    ['0,06180', '1×', 'sin ejecuciones', '—', '0 %'],
  ], [1400, 1800, 2100, 1700, 2026], { aligns: [AlignmentType.LEFT, C, C, C, C], size: 18 }));
  k.push(...figure(FIG('beta_fase2_apertura.png'), 'Slippage y cumplimiento de la orden para cada β (apertura). La línea punteada del cumplimiento marca el umbral de 95 %.', 540, 250));
  k.push(P('La regla de selección se fijó antes de ver los datos: se exige que se complete al menos el 95 % de la orden y, entre los valores que cumplen, se elige el de menor slippage si el Wilcoxon pareado lo respalda. Solo 0,1 × β∗ cumple, y queda **β = 0,0061796**. Dos hallazgos acotan ese resultado:'));
  k.push(...B([
    '**Con β alto, la red aprende a no operar.** Como el término de riesgo se cobra sobre lo ejecutado, no ejecutar sale gratis: con 0,3× se completa el 34 % de la orden y con 1× la red no opera. No es un error de código sino una propiedad de la fórmula del Título I.',
    '**La diferencia con el control es pequeña** (4,71 frente a 5,12 bps, dentro del error estándar) y TWAP con órdenes límite (4,06 bps) iguala o supera a las redes con este entrenamiento corto. El PPO todavía no demuestra ventaja sobre el benchmark simple.',
  ]));
  k.push(callout('Decisión D3 (qué mide el término de riesgo)', 'Se evaluaron cuatro opciones frente al Título I. Rige la **opción 0**: se mantiene la fórmula del Título I con β = 0,0061796, con una **regla de vigilancia** fijada de antemano: si en el entrenamiento inicial (2.3.5) el cumplimiento de la orden baja del 95 %, se pasa a la opción A (riesgo sobre el inventario pendiente, ya implementada y apagada por defecto) y se declara como desviación justificada con datos. La revisión final se hace al cierre del sprint 5. β es **provisional**: solo se calibró en la apertura, con una semilla de red.', 'info'));
  k.push(GAP());
  return k;
}

// ---------------------------------------------------------------- 6.1 validacion formal
function sec61() {
  const k = [];
  k.push(H2('6.1 Validación estadística del simulador (tarea 2.2.5)'));
  k.push(P('El objetivo es comprobar si el simulador calibrado reproduce características del mercado real. Paolo Sepúlveda realizó la validación formal sobre FALABELLA con **30 semillas simuladas por tramo**, comparando los retornos de 5 minutos simulados con los reales, antes y después de calibrar. Los criterios se fijaron antes de ver los datos:'));
  k.push(tabCaption('Criterios de validación y resultado (FALABELLA, simulador calibrado).'));
  k.push(table(['Criterio', 'Qué exige', 'Resultado'], [
    ['A. Literal del plan', 'Todos los p de KS y Mann–Whitney, por tramo, mayores que 0,05', chip('NO CUMPLE', 'pend')],
    ['B. Forma', 'KS con muestras estandarizadas, p mayor que 0,05 en los 3 tramos', chip('NO CUMPLE', 'pend')],
    ['C. Efecto', '|g de Hedges| menor que 0,5 en los 3 tramos', chip('CUMPLE', 'ok')],
    ['D. Patrón', 'Volatilidad máxima en la apertura y volumen por vela creciente', chip('CUMPLE', 'ok')],
  ], [2300, 4900, 1826], { size: 18 }));
  k.push(GAP());
  k.push(P('**Veredicto: el simulador calibrado NO es válido según el criterio literal del plan.** El KS crudo rechaza en los tres tramos (por muy poco en apertura y cierre, con D / D crítico de 1,10 y 1,03, y con claridad en media jornada, 1,75); tras la corrección de Holm por comparaciones múltiples solo sigue rechazando media jornada. En cambio, la **escala** de los retornos coincide (desvío simulado sobre real de 0,89 a 0,98, tamaño de efecto trivial) y también el **patrón entre tramos**.'));
  k.push(tabCaption('KS de dos muestras sobre los retornos de 5 minutos y tamaño del efecto (FALABELLA, 30 semillas).'));
  k.push(table(['Tramo', 'D', 'p', 'D / D crítico', 'p Mann–Whitney (|ret.|)', 'g de Hedges', 'Desvío sim. / real'], [
    ['Apertura', '0,073', '0,021', '1,10', '0,086', '0,01', '0,98'],
    ['Media jornada', '0,098', '< 0,0001', '1,75', '0,0061', '−0,03', '0,89'],
    ['Cierre', '0,066', '0,039', '1,03', '0,339', '−0,03', '0,96'],
  ], [1700, 900, 1100, 1300, 1700, 1200, 1126], { aligns: [AlignmentType.LEFT, C, C, C, C, C, C], size: 18 }));
  k.push(...figure(FIG('validacion_formal_2_2_5.png'), 'Validación formal del simulador de FALABELLA: comparación de retornos simulados y reales por tramo (30 semillas).', 580, 310));
  k.push(tabCaption('Antes y después de calibrar (estadístico D del KS).'));
  k.push(table(['Tramo', 'D antes', 'D después', 'g antes', 'g después'], [
    ['Apertura', '0,324', '0,073', '−0,98', '0,01'],
    ['Media jornada', '0,279', '0,098', '−0,86', '−0,03'],
    ['Cierre', '0,275', '0,066', '−0,92', '−0,03'],
  ], [2400, 1700, 1700, 1600, 1626], { aligns: [AlignmentType.LEFT, C, C, C, C], size: 18 }));
  k.push(GAP());
  k.push(P('La calibración mejora la distancia entre distribuciones por un factor de 3 a 4 (D de 0,28 a 0,32 antes frente a 0,07 a 0,10 después), aunque no alcanza el criterio del plan. Los valores por semilla frente al real muestran una volatilidad entre un 8 % y un 14 % bajo el objetivo, y un volumen por vela simulado un 49 %, 22 % y 5 % mayor en apertura, media jornada y cierre. El spread simulado (0,17 bps) queda decenas de veces bajo el rango de los proxies reales (4 a 35 bps): el Implementation Shortfall absoluto en ABIDES-Gym está **subestimado**, pero la comparación entre políticas sigue siendo válida.'));
  k.push(tabCaption('Validación formal de COPEC y ECL (30 semillas, calibración con 3 agentes de momentum).'));
  k.push(table(['Activo y tramo', 'KS: D / D crítico', 'g de Hedges', 'Veredicto'], [
    ['COPEC (apertura / media jornada / cierre)', '1,43 / 1,75 / 2,40', '0,18 / 0,11 / 0,27', chip('NO VÁLIDO', 'mid')],
    ['ECL (apertura / media jornada / cierre)', '1,66 / 2,22 / 1,85', '0,28 / 0,20 / 0,22', chip('NO VÁLIDO', 'mid')],
  ], [3800, 2000, 1700, 1526], { size: 18 }));
  k.push(GAP());
  k.push(callout('Lectura del resultado', 'Que la tarea quede **hecha con límite** significa que se ejecutó y se midió: el simulador calibrado aproxima la escala y el patrón del mercado, pero no pasa el criterio literal del plan. El límite queda escrito con su causa: el KS con miles de retornos agrupados rechaza diferencias pequeñas (por eso se reportan también el tamaño del efecto y el D / D crítico), y el valor real de volatilidad o volumen es un único número, por lo que se usa una prueba de una muestra. Un solo activo por informe y un solo régimen de mercado.', 'info'));
  return k;
}

// ---------------------------------------------------------------- 6.4 pruebas
function sec64() {
  const k = [];
  k.push(H2('6.4 Pruebas de software'));
  k.push(P('Al cierre del sprint 4 (integración del PR #36, 19 de octubre) el repositorio incluye **263 pruebas automáticas** (pytest): pasan 255 y 8 se omiten porque requieren archivos de mercado o ABIDES-Gym que solo existen en el entorno donde se generaron. El total incluye 18 pruebas de componentes del sprint 5 que ya estaban integrados en esa fecha (protocolo CTDE, entrenador PPO y meta-órdenes).'));
  k.push(tabCaption('Pruebas automáticas por área al 19 de octubre de 2026.'));
  k.push(table(['Área', 'Pruebas', 'Qué verifica'], [
    ['Pipeline de datos y perfil intradiario', '27', 'Limpieza, variables del Maestro y perfil de volumen por tramo.'],
    ['Poisson (calibración y simulador)', '48', 'Estimación de λ y θ, validación KS, simulador de libro y ejecución a mercado.'],
    ['ABIDES-Gym y calibración de rmsc04', '67', 'Traducción de estados y acciones, momentos simulados, búsqueda en grilla y calibración con datos reales.'],
    ['Recompensas y barrido de β', '45', 'σ² causal, escala, opción de riesgo sobre lo pendiente, barrido y fase 2 de β.'],
    ['Redes, PPO y orquestador', '31', 'Actor-Crítico, fábrica de redes, entrenador PPO y ciclo Maestro–Ejecutor.'],
    ['Validación y benchmarks', '39', 'Validación formal (KS, Mann–Whitney, Holm), corridas, informe, TWAP/VWAP y métricas estadísticas.'],
    ['Otros (copias de seguridad y cuadernos)', '6', 'Snapshots de datos y cuadernos de Colab.'],
    [{ t: 'Total', bold: true }, { t: '263', bold: true }, '255 pasan, 8 omitidas'],
  ], [3300, 1100, 4626], { aligns: [AlignmentType.LEFT, C, AlignmentType.LEFT], size: 18 }));
  k.push(GAP());
  k.push(P('Dos tipos de verificación no están automatizados: la integración con ABIDES-Gym real, que solo corre en el entorno de Colab con Python 3.9 y se verificó manualmente (sección 5.4 y calibraciones de la sección 5.8), y la convergencia del PPO, que requiere el entrenamiento completo del sprint 5.'));
  return k;
}

// ---------------------------------------------------------------- 6.5 entrenamiento
function sec65() {
  const k = [];
  k.push(H2('6.5 Entrenamiento del sistema PPO'));
  k.push(callout('Estado al cierre del sprint 4', 'Se entrenó un Ejecutor (apertura) con PPO durante 300 episodios por valor de β para elegir ese coeficiente (sección 5.9): es un entrenamiento **corto y con un objetivo de calibración**, no el entrenamiento del sistema. El ciclo de entrenamiento jerárquico completo (Maestro y tres Ejecutores) corresponde al sprint 5 (12 al 23 de octubre) y el ajuste de hiperparámetros al sprint 6; ambos quedan fuera de este informe.', 'pend'));
  return k;
}

module.exports = { sec55tail, sec57, sec58, sec59, sec61, sec64, sec65 };
