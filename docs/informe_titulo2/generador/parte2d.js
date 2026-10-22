// Capitulos 7 a 9 y anexos A y B al cierre del Sprint 4 (22 oct 2026).
const L = require('./lib');
const { AlignmentType } = require('docx');
const FIG = (f) => `${__dirname}/fig/${f}`;
const { H1, H2, P, B, table, tabCaption, chip, callout, GAP, figure } = L;
const C = AlignmentType.CENTER;

function cap7() {
  const k = [];
  k.push(L.PB());
  k.push(H1('Capítulo 7. Resultados y evaluación'));
  k.push(P('Este capítulo reúne los resultados disponibles al cierre del sprint 4. La comparación central del proyecto, el sistema PPO frente a TWAP y VWAP, todavía no puede reportarse: depende del entrenamiento completo (sprints 5 y 6) y de la evaluación estadística (sprint 7).'));
  k.push(tabCaption('Resultados disponibles al 22 de octubre de 2026 (cierre del sprint 4).'));
  k.push(table(['Resultado', 'Valor principal', 'Sección'], [
    ['Perfil intradiario del IPSA', 'Spread relativo 0,138 % (apertura), 0,112 % (media jornada) y 0,128 % (cierre): patrón decreciente, no en "U".', '3.2'],
    ['Calibración de Poisson (2.1.3)', '90 de 90 pares ticker × tramo rechazan el KS al 5 %; los parámetros sirven como intensidades de entrada, no como generador de retornos.', '5.3'],
    ['Integración con ABIDES-Gym', 'Episodios completos en los 3 tramos; adaptador al formato de 27 variables y 240 acciones.', '5.4'],
    ['Calibración de rmsc04 (2.2.4)', 'FALABELLA: volatilidad dentro del 10 % del objetivo; KS rechaza en 2 de 3 tramos; volumen hasta 49 % sobre el real; spread 20 a 100 veces menor.', '5.8'],
    ['Calibración de COPEC y ECL', 'Con 3 agentes de momentum, 0 de 30 corridas desbocadas en los tres tramos (antes hasta 13 de 30); KS rechaza.', '5.8'],
    ['Recompensa del Maestro (2.2.2)', 'λ = 0,05 (penalización de 1,06 veces el slippage); provisional.', '5.9'],
    ['Recompensa de los Ejecutores (2.2.3)', 'β = 0,0061796 (0,1 × β∗), único valor que completa el 95 % de la orden en la apertura; provisional.', '5.9'],
    ['Validación formal del simulador (2.2.5)', 'No válido según el criterio literal (KS rechaza); escala y patrón entre tramos coinciden; la distancia D baja de 0,28–0,32 a 0,07–0,10 al calibrar.', '6.1'],
    ['TWAP frente a VWAP (2.3.4)', 'IS medio de 36.932 frente a 35.569 pesos; Wilcoxon p = 0,00195.', '6.2'],
  ], [2700, 5326, 1000], { aligns: [AlignmentType.LEFT, AlignmentType.LEFT, C], size: 18 }));
  k.push(GAP());
  k.push(callout('Resultado principal pendiente', 'Comparación del sistema PPO frente a TWAP y VWAP: Implementation Shortfall, porcentaje de reducción, significancia y tamaño de efecto, en los 30 escenarios de liquidez. Se completará con los sprints 5 al 7.', 'pend'));
  return k;
}

function cap8() {
  const k = [];
  k.push(H1('Capítulo 8. Discusión y análisis crítico'));
  k.push(P('Con la evidencia del sprint 4 se pueden sostener las siguientes lecturas; las que dependen del entrenamiento del sistema quedan señaladas como pendientes.'));
  k.push(...B([
    '**El patrón intradiario del IPSA difiere de la hipótesis inicial.** Dos análisis independientes muestran un spread decreciente a lo largo del día. Si el patrón se sostiene con más datos, un agente eficiente debería asignar menos volumen donde el spread es mayor; es una hipótesis para el entrenamiento, no un resultado.',
    '**El simulador calibrado aproxima la escala y el patrón entre tramos, pero no la distribución.** Con 30 semillas el KS rechaza (el criterio literal del plan no se cumple en ningún activo), aunque la distancia cae de 0,28–0,32 a 0,07–0,10 y los tamaños de efecto son triviales o pequeños. Los límites son concretos y están medidos: spread simulado entre 20 y 100 veces menor que el real, volumen por vela hasta 49 % mayor en la apertura (que bajar la actividad no corrige sin perder la volatilidad) y colas más livianas que las reales.',
    '**El costo absoluto está subestimado, no la comparación relativa.** Como el spread simulado es de uno o dos ticks, el Implementation Shortfall absoluto en ABIDES-Gym es menor que el real. Las conclusiones del proyecto deben leerse como diferencias entre estrategias bajo las mismas condiciones simuladas.',
    '**El diseño de la recompensa condiciona lo que aprende el agente.** Con la fórmula del Título I, el riesgo se cobra solo sobre lo ejecutado y no ejecutar sale gratis: con β alto la red aprende a no operar. Se resolvió con el mayor β que aún completa la orden (0,1 × β∗) y una regla de vigilancia fijada de antemano (cumplimiento menor que 95 % implica pasar al riesgo sobre lo pendiente). Este hallazgo no estaba anticipado en el Título I.',
    '**Los benchmarks simples son exigentes.** VWAP supera a TWAP en costo (3,8 % menos) y, con el entrenamiento corto de la fase 2 de β, TWAP con órdenes límite (4,06 bps) iguala o supera a las redes (4,71 bps). El sistema propuesto deberá superar a VWAP, no solo a TWAP.',
    '**Los resultados desfavorables se reportaron, no se ajustaron.** Las reglas de adopción se fijaron antes de ver los datos; cuando ningún candidato las cumplió (grilla de actividad baja, megashocks) se conservó la configuración y se declaró el límite. La calibración de COPEC y ECL mostró que un parámetro por defecto (12 agentes de momentum) funciona con 1.000 agentes de ruido y desestabiliza el mercado con 250: la causa se aisló con un diagnóstico de un cambio por vez.',
    '**Se mejoró la calidad del código durante el sprint:** se ajustó el nivel de precio de las órdenes límite del simulador de Poisson (y se regeneró el barrido de β), la búsqueda de archivos de mercado admite carpetas sin datos y las corridas de β toleran políticas que no ejecutan.',
    '**La reproducibilidad es un riesgo manejable.** ABIDES-Gym está archivado y exige versiones antiguas; la receta de instalación para Colab, los scripts de cada calibración y las semillas quedaron documentados, y el simulador de Poisson permite seguir probando sin él.',
  ]));
  k.push(callout('Por completar', 'Interpretación del comportamiento aprendido por el Maestro y los Ejecutores, análisis de sensibilidad, fortalezas y debilidades observadas en las corridas de evaluación y discusión de aplicabilidad en contextos reales (sprints 7 y 8).', 'pend'));
  return k;
}

function cap9() {
  const k = [];
  k.push(H1('Capítulo 9. Conclusiones y trabajo futuro'));
  k.push(H2('9.1 Cumplimiento de los objetivos específicos (estado actual)'));
  k.push(tabCaption('Estado de los objetivos específicos de la Parte I al cierre del sprint 4.'));
  k.push(table(['Objetivo específico', 'Estado', 'Evidencia o faltante'], [
    ['Modelar un entorno de simulación de alta fidelidad del LOB', chip('PARCIAL', 'mid'), 'ABIDES-Gym integrado y calibrado con FALABELLA, COPEC y ECL, más un simulador de Poisson; no pasa el criterio literal de validación. Límites declarados: spread y volumen.'],
    ['Implementar la arquitectura jerárquica con PPO en PyTorch', chip('PARCIAL', 'mid'), 'Arquitectura, redes, espacios, orquestador y PPO implementados y conectados; falta el entrenamiento completo (sprints 5 y 6).'],
    ['Desarrollar la función de recompensa que minimice el Implementation Shortfall', chip('PARCIAL', 'mid'), 'R_M y R_E implementadas y calibradas (λ = 0,05; β = 0,0061796), ambas provisionales; β solo en la apertura.'],
    ['Evaluar el sistema frente a TWAP y VWAP', chip('PARCIAL', 'mid'), 'Benchmarks y herramientas estadísticas listos; falta el sistema entrenado para compararlo.'],
  ], [3300, 1500, 4226], { size: 18 }));
  k.push(GAP());
  k.push(H2('9.2 Conclusiones'));
  k.push(P('Al cierre del sprint 4 se cuenta con la infraestructura completa para entrenar y evaluar el sistema: datos, espacios formales, redes, algoritmo PPO, orquestador, simulador calibrado, recompensas calibradas y benchmarks. De las 19 tareas de los sprints 1 a 4, 10 se cerraron cumpliendo su criterio, 6 quedaron **hechas con límite demostrado** (se ejecutaron y se midieron, con el límite y su causa escritos) y 3 entregables menores se cerraron en el PR de cierre. Las conclusiones finales (hipótesis probada o refutada, hallazgos principales e impacto esperado) se redactan en el sprint 9.'));
  k.push(H2('9.3 Trabajo futuro identificado hasta ahora'));
  k.push(...B([
    'Calibrar β también en media jornada y cierre, y revisar la decisión D3 con los resultados del entrenamiento inicial.',
    'Revalidar λ del Maestro con un entrenamiento real y ajustar los hiperparámetros del PPO (sprint 6).',
    'Reducir el volumen simulado y estudiar cómo ampliar el spread sin perder volatilidad, o declarar el límite en la evaluación final.',
    'Recalibrar los parámetros con un snapshot posterior a la transición del IPSA a MSCI y, si se logra acceso institucional, con datos de Nivel 2.',
    'Unificar el corte de los tramos horarios (11:00 en el Maestro y 11:30 en los Ejecutores) en todos los módulos.',
    'Incorporar órdenes límite en los benchmarks y evaluar el efecto de distintos tamaños de meta-orden.',
  ]));
  return k;
}

function anexoA() {
  const k = [];
  k.push(L.PB());
  k.push(H1('Anexo A. Gestión del proyecto'));
  k.push(H2('A.1 Calendario de sprints'));
  k.push(tabCaption('Calendario y estado de los sprints (metodología Scrum).'));
  k.push(table(['Sprint', 'Periodo', 'Foco', 'Estado'], [
    ['1', '17–28 ago 2026', 'Alistamiento: entorno, datos y esquemas de estado', chip('COMPLETADO', 'ok')],
    ['2', '31 ago–11 sep', 'Pipeline de datos, PoC de ABIDES-Gym y arquitectura del entorno', chip('COMPLETADO', 'ok')],
    ['3', '14–25 sep', 'Redes Actor-Crítico, calibración de Poisson, espacios Gymnasium', chip('COMPLETADO', 'ok')],
    ['4', '28 sep–9 oct (cierre formal el 19 oct)', 'PPO, funciones de recompensa, calibración de rmsc04, validación del simulador', chip('COMPLETADO', 'ok')],
    ['5', '12–23 oct', 'Integración CTDE, ciclo de entrenamiento, meta-órdenes (fuera de este informe)', chip('EN CURSO', 'mid')],
    ['6', '26 oct–6 nov', 'Ajuste de hiperparámetros y corridas de evaluación', chip('PENDIENTE', 'pend')],
    ['7', '9–20 nov', 'Evaluación estadística (90 corridas) y comparación', chip('PENDIENTE', 'pend')],
    ['8', '23 nov–4 dic', 'Redacción de capítulos de la tesis', chip('PENDIENTE', 'pend')],
    ['9', 'Dic 2026 (por confirmar)', 'Conclusiones y defensa ante la comisión', chip('PENDIENTE', 'pend')],
  ], [900, 2400, 4026, 1700], { aligns: [C, AlignmentType.LEFT, AlignmentType.LEFT, C] }));
  k.push(P('La tarea 2.3.4 (benchmarks TWAP y VWAP), planificada para el sprint 5, se adelantó y está completa.', { run: { size: 18 }, after: 160 }));

  k.push(H2('A.2 Avance frente al plan'));
  k.push(P('El plan de Título II (sprints 3 al 9) suma 604 horas. Están cerradas **216**: el sprint 3 completo (104 horas), el sprint 4 completo (96 horas, de las cuales cuatro tareas quedaron hechas con límite demostrado) y la tarea 2.3.4 (16 horas), que se adelantó. Eso equivale a un avance de aproximadamente **36 %** medido en horas de tareas cerradas. El tiempo transcurrido desde el inicio del sprint 3 es de unos 38 días sobre un total cercano a 95 (hasta mediados de diciembre), alrededor de 40 %. El avance acompaña el calendario: las horas del sprint 5, que termina el 23 de octubre, se sumarán al cierre de ese sprint.'));
  k.push(...figure(FIG('horas_sprint.png'), 'Horas planificadas por sprint y horas completadas al 22 de octubre de 2026.', 480, 240));

  k.push(H2('A.3 Responsabilidades y contribuciones'));
  k.push(tabCaption('Distribución de las 604 horas del plan por responsable.'));
  k.push(table(['Integrante', 'Horas', 'Áreas principales'], [
    ['Mauricio Reynoso (MR)', '196', 'Redes Actor-Crítico, PPO (L_CLIP y GAE), recompensa del Maestro, integración CTDE y entrenamiento, análisis de sensibilidad.'],
    ['Benjamín Farias (BF)', '188', 'Pipeline de datos, calibración de Poisson y de rmsc04, recompensa de los Ejecutores, meta-órdenes, monitoreo y consolidación de resultados.'],
    ['Paolo Sepúlveda (PS)', '196', 'Espacios Gymnasium, validación del simulador, benchmarks, evaluación estadística y redacción de análisis y conclusiones.'],
    ['Equipo', '24', 'Tablas y figuras comparativas, defensa.'],
  ], [2700, 1000, 5326], { aligns: [AlignmentType.LEFT, C, AlignmentType.LEFT] }));
  k.push(GAP());
  k.push(tabCaption('Contribuciones por integrante en los sprints 1 a 4 (autoría según el registro de ramas y pull requests integrados a main).'));
  k.push(table(['Integrante', 'Contribuciones'], [
    ['**Mauricio Reynoso (MR)**', 'Entorno y repositorio (PR #1); guía de Colab y seguridad de tokens (PR #11 y #12); arreglo de dependencias y prueba de concepto de ABIDES-Gym (PR #13 y la integración de la configuración de ABIDES); primera red Actor-Crítico (2.1.1); implementación del PPO con L_CLIP y GAE y calibración de λ = 0,05 (2.2.1 y 2.2.2, PR #20); formalización del carácter provisional de λ y semillas reproducibles (PR #33).'],
    ['**Benjamín Farias (BF)**', 'Descarga de datos OHLCV del IPSA (PR #2); pipeline de limpieza y variables del Maestro (PR #4); calibración de Poisson por tramos y su robustez (PR #9 y #10, 2.1.3); calibración de rmsc04 con datos del IPSA y su validación con 30 semillas (PR #22, #23 y #26, 2.2.4); recompensa de los Ejecutores con σ² causal normalizada (PR #25, 2.2.3); ratificación de las redes de los Ejecutores y revisión formal del cierre del sprint 4, con la grilla de actividad baja (PR #32).'],
    ['**Paolo Sepúlveda (PS)**', 'Vectores de estado S_M y S_E (1.1.4); arquitectura del entorno de simulación (1.2.5, PR #3); espacios Gymnasium y simulador de Poisson de libro de órdenes (2.1.4, PR #6); sistema de registro y análisis de entrenamiento (PR #8); base de validación del simulador (PR #18); benchmarks TWAP y VWAP (2.3.4, PR #19); validación formal con 30 semillas (2.2.5), fase 2 de la elección de β, análisis de la distribución de R_E, sondeo de megashocks y fábrica de redes de los Ejecutores (2.1.2) en el cierre del sprint 4 (PR #27); calibración y validación de COPEC y ECL y cierre de los sprints 1 a 4 (PR #36).'],
  ], [2200, 6826], { size: 18 }));
  k.push(GAP());
  k.push(P('El inventario completo de ramas y pull requests (25 integraciones a main entre agosto y octubre de 2026, con archivos y líneas modificadas) está en el documento *Registro histórico de cambios y ramas en la rama principal (Sprints 1 a 4)*, elaborado por Mauricio Reynoso. El equipo trabajó con ramas temáticas y revisión de pull requests antes de integrar a main.'));

  k.push(H2('A.4 Estado de las tareas de los sprints 1 al 4'));
  k.push(tabCaption('Tareas de los sprints 1 al 4 y su estado, según el acta de cierre (19 de octubre de 2026).'));
  k.push(table(['ID', 'Tarea', 'Resp.', 'Estado'], [
    ['1.1.1', 'Planificación y backlog', 'Equipo', chip('HECHO', 'ok')],
    ['1.1.2', 'Entorno y repositorio', 'MR', chip('HECHO', 'ok')],
    ['1.1.3', 'Descarga de datos OHLCV', 'BF', chip('HECHO', 'ok')],
    ['1.1.4', 'Vectores de estado S_M y S_E', 'PS', chip('HECHO', 'ok')],
    ['1.1.5', 'Sprint Review', 'Equipo', chip('HECHO', 'ok')],
    ['1.2.1', 'Limpieza de datos', 'BF', chip('HECHO', 'ok')],
    ['1.2.2', 'Variables del Maestro (S_M)', 'BF', chip('HECHO', 'ok')],
    ['1.2.3', 'Prueba de concepto de ABIDES-Gym', 'MR', chip('HECHO', 'ok')],
    ['1.2.4', 'Dependencias y entorno', 'MR', chip('HECHO', 'ok')],
    ['1.2.5', 'Arquitectura del entorno', 'PS', chip('HECHO', 'ok')],
    ['2.1.1', 'Red Actor-Crítico del Maestro', 'MR', chip('HECHO CON LÍMITE', 'mid')],
    ['2.1.2', 'Redes de los Ejecutores', 'BF', chip('HECHO CON LÍMITE', 'mid')],
    ['2.1.3', 'Calibración de Poisson del libro de órdenes', 'PS / BF', chip('HECHO', 'ok')],
    ['2.1.4', 'Formalización de espacios Gymnasium', 'PS', chip('HECHO', 'ok')],
    ['2.2.1', 'Implementación de L_CLIP y GAE', 'MR', chip('HECHO', 'ok')],
    ['2.2.2', 'Función de recompensa del Maestro', 'MR', chip('HECHO CON LÍMITE', 'mid')],
    ['2.2.3', 'Función de recompensa de los Ejecutores', 'BF', chip('HECHO CON LÍMITE', 'mid')],
    ['2.2.4', 'Calibración de rmsc04 con el IPSA', 'BF', chip('HECHO CON LÍMITE', 'mid')],
    ['2.2.5', 'Validación estadística del simulador', 'PS', chip('HECHO CON LÍMITE', 'mid')],
    ['2.3.4', 'Benchmarks TWAP y VWAP (adelantada del sprint 5)', 'PS', chip('HECHO', 'ok')],
  ], [900, 4600, 1300, 2226], { aligns: [C, AlignmentType.LEFT, C, C], size: 18 }));
  k.push(P('**Hecho con límite** significa que la tarea se ejecutó y se midió, pero el resultado no alcanza el criterio del plan o hay una desviación de diseño; el límite está escrito con su causa y con la fecha de revisión. Los límites son: 2.1.1 y 2.1.2 (arquitectura distinta de la especificación del Excel: 256 neuronas y una cabeza discreta; desviaciones documentadas y ratificada la de los Ejecutores), 2.2.2 y 2.2.3 (λ y β provisionales), 2.2.4 (KS rechaza y volumen alto) y 2.2.5 (simulador no válido según el criterio literal).', { run: { size: 18 }, after: 160, before: 100 }));
  k.push(GAP());

  k.push(H2('A.5 Uso de herramientas de apoyo'));
  k.push(P('El equipo utilizó Claude Code (Anthropic) como asistente de programación, análisis y redacción. Los documentos del repositorio lo declaran en su encabezado y quedan sujetos a la revisión de quien corresponde; las cifras de este informe provienen de archivos versionados en el repositorio y se contrastaron contra ellos antes de entregar.'));
  return k;
}

function anexoB() {
  const k = [];
  k.push(L.PB());
  k.push(H1('Anexo B. Riesgos y limitaciones'));
  k.push(tabCaption('Riesgos identificados y su manejo.'));
  k.push(table(['Riesgo o limitación', 'Efecto', 'Manejo'], [
    ['ABIDES-Gym está archivado (junio de 2025) y exige versiones antiguas de Python y librerías.', 'Instalación frágil y sin soporte.', 'Entorno aislado con Python 3.9, receta de instalación documentada y lista de versiones fijadas (`requirements-locked.txt`), y simulador de Poisson como alternativa liviana.'],
    ['Los datos no incluyen Nivel 2.', 'Spread, profundidad y cancelaciones son aproximaciones.', 'ABIDES-Gym provee un libro simulado; se valida escala y patrón y no la magnitud del spread; acceso institucional a Nivel 2 como opción.'],
    ['Ventana de 60 días de la fuente y transición del IPSA a MSCI (1 de septiembre de 2026).', 'Los parámetros pueden quedar desactualizados.', 'Recalibrar con un snapshot posterior antes de la evaluación final.'],
    ['El simulador calibrado no pasa el criterio literal de validación (KS rechaza).', 'Las diferencias entre estrategias podrían depender de rasgos del simulador.', 'Reportar el límite con su causa; comparar siempre estrategias bajo las mismas condiciones simuladas y evaluar con 30 y 90 corridas.'],
    ['Spread simulado muy bajo y volumen alto en la apertura.', 'El Implementation Shortfall absoluto queda subestimado.', 'Interpretar los resultados como relativos entre estrategias; límites declarados en la calibración.'],
    ['Coeficientes λ y β provisionales; β solo calibrado en la apertura y con una semilla de red.', 'Las recompensas pueden requerir ajuste al entrenar.', 'Regla de vigilancia de D3 (cumplimiento menor que 95 %); calibrar β en media jornada y cierre y revalidar λ en los sprints 5 y 6.'],
    ['Con riesgo cobrado solo sobre lo ejecutado, no operar sale gratis.', 'La red puede aprender a no ejecutar.', 'Opción de riesgo sobre lo pendiente ya implementada y lista para activar si se dispara la regla.'],
    ['Cobertura heterogénea: 15 de 30 tickers son de tier B.', 'Parámetros de baja confianza en esos tickers.', 'Usar tickers de tier A y los tres activos calibrados (FALABELLA, COPEC y ECL).'],
    ['Dependencia entre tareas de sprints consecutivos.', 'Un atraso en un sprint retrasa el siguiente.', 'Seguimiento semanal, decisiones con plazo y regla por defecto, y adelanto de tareas independientes (como los benchmarks).'],
    ['Costo computacional de ABIDES-Gym (el tramo de cierre es el más lento: unas 2 horas por valor de β).', 'Limita el número de corridas posibles (30 y 90).', 'Ejecución en Google Colab con corridas reanudables y ajuste del número de episodios según el tiempo disponible.'],
  ], [3100, 2500, 3426], { size: 18 }));
  k.push(GAP());
  return k;
}

module.exports = { cap7, cap8, cap9, anexoA, anexoB };
