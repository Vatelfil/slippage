const L = require('./lib');
const { AlignmentType, Paragraph, TextRun, ShadingType } = require('docx');
const FIG = (f) => `${__dirname}/fig/${f}`;
const { H1, H2, P, B, table, tabCaption, chip, callout, GAP, figure } = L;
const D2 = require('./parte2d');
const C = AlignmentType.CENTER;

const CODE = (lines) => lines.map((ln) => new Paragraph({
  spacing: { after: 0, line: 252 },
  shading: { type: ShadingType.CLEAR, fill: 'F1F3F8', color: 'auto' },
  indent: { left: 240, right: 240 },
  children: [new TextRun({ text: ln || ' ', font: L.CODE_FONT, size: 18 })],
}));

module.exports = function anexos() {
  const k = [];

  k.push(...D2.anexoA());
  k.push(...D2.anexoB());

  // ================= ANEXO C =================
  k.push(H1('Anexo C. Glosario'));
  k.push(tabCaption('Términos usados en este informe.'));
  k.push(table(['Término', 'Significado'], [
    ['IPSA', 'Índice de las 30 acciones más transadas de la Bolsa de Santiago.'],
    ['Libro de órdenes (LOB)', 'Lista de órdenes de compra y venta pendientes, ordenadas por precio.'],
    ['Spread', 'Diferencia entre el mejor precio de venta y el mejor de compra; costo inmediato de operar.'],
    ['Slippage', 'Diferencia entre el precio esperado de una orden y el que realmente se paga al ejecutarla.'],
    ['Implementation Shortfall (IS)', 'Costo total de ejecutar frente al precio de referencia al momento de decidir: (precio promedio − precio de referencia) × cantidad.'],
    ['Meta-orden', 'Orden grande que se fracciona en varias más pequeñas a lo largo del día.'],
    ['Tramo', 'Franja horaria de la jornada (apertura, media jornada, cierre).'],
    ['TWAP / VWAP', 'Estrategias clásicas: reparto uniforme en el tiempo / reparto proporcional al volumen histórico.'],
    ['Aprendizaje por refuerzo', 'Método en que un agente aprende probando acciones y recibiendo recompensas.'],
    ['PPO', 'Proximal Policy Optimization: algoritmo de aprendizaje por refuerzo que limita cuánto cambia la política en cada actualización.'],
    ['Actor-Crítico', 'Red con dos salidas: el actor elige acciones y el crítico estima el valor de cada estado.'],
    ['GAE', 'Estimación generalizada de ventaja: forma de calcular cuánto mejor fue una acción que lo esperado.'],
    ['CTDE', 'Entrenamiento centralizado con ejecución descentralizada: los agentes comparten información al entrenarse y actúan solos después.'],
    ['Gymnasium', 'Librería estándar de Python para definir entornos de aprendizaje por refuerzo.'],
    ['ABIDES-Gym', 'Simulador de mercado con libro de órdenes, desarrollado por JP Morgan, con interfaz tipo Gym.'],
    ['Proceso de Poisson', 'Modelo de llegadas aleatorias a tasa media constante; aquí describe la llegada de órdenes.'],
    ['OBI', 'Order Book Imbalance: desbalance entre el volumen de compra y de venta del libro.'],
    ['Winsorización', 'Limitar los valores extremos a un percentil para que no distorsionen un promedio.'],
    ['Snapshot', 'Descarga de datos fechada, que fija la ventana de tiempo analizada.'],
    ['Test de Kolmogorov–Smirnov (KS)', 'Prueba que compara si dos muestras provienen de la misma distribución.'],
    ['Wilcoxon, Mann–Whitney, Kruskal–Wallis', 'Pruebas estadísticas no paramétricas: muestras pareadas, dos muestras independientes y tres o más grupos, respectivamente.'],
    ['d de Cohen', 'Medida del tamaño de un efecto: cuántas desviaciones estándar separan dos grupos.'],
  ], [3000, 6026], { size: 18 }));
  k.push(GAP());

  // ================= ANEXO D =================
  k.push(L.PB());
  k.push(H1('Anexo D. Repositorio y reproducibilidad'));
  k.push(P('Todo el código, los datos derivados y los reportes están en el repositorio del proyecto (github.com/Vatelfil/slippage). Los archivos de datos de mercado (parquet) no se versionan; los scripts los regeneran. Las carpetas principales son:'));
  k.push(...B([
    '`src/data`, `src/features`: descarga, limpieza y variables del Maestro.',
    '`src/envs`: espacios, entornos, calibración de Poisson, simulador, adaptador de ABIDES-Gym y orquestador.',
    '`src/models`: redes Actor-Crítico. `src/analysis`: métricas, validación del simulador y benchmarks.',
    '`docs`: esquemas de estado, arquitectura del entorno, calibración de Poisson y evidencia del pipeline. `tests`: pruebas automáticas.',
  ]));
  k.push(P('Comandos principales (desde la raíz del repositorio):', { keepNext: true }));
  k.push(...CODE([
    '# pruebas automáticas',
    'python -m pytest -q',
    '',
    '# calibración de Poisson (snapshot indicado)',
    'python -m src.envs.calibration_poisson --snapshot 2026-08-23 --all',
    '',
    '# caracterización del mercado y benchmarks TWAP/VWAP',
    'PYTHONPATH=. python src/analysis/market_validation.py',
    'PYTHONPATH=. python src/analysis/benchmarks.py',
  ]));
  k.push(GAP());
  k.push(P('La integración con ABIDES-Gym solo funciona en un entorno Python 3.9 con las versiones fijadas; la receta de instalación para Google Colab está en el documento de diagnóstico del repositorio.'));

  // ================= REFERENCIAS ADICIONALES =================
  k.push(H1('Referencias adicionales de la Parte II'));
  k.push(P('Se suman a la bibliografía de la Parte I.'));
  const refs = [
    'Amrouni, S., Moulin, A., Vann, J., Vyetrenko, S., Balch, T., & Veloso, M. (2021). ABIDES-Gym: Gym environments for multi-agent discrete event simulation and application to financial markets. En Proceedings of the Second ACM International Conference on AI in Finance (ICAIF ’21).',
    'Cohen, J. (1988). Statistical power analysis for the behavioral sciences (2.ª ed.). Lawrence Erlbaum Associates.',
    'Kruskal, W. H., & Wallis, W. A. (1952). Use of ranks in one-criterion variance analysis. Journal of the American Statistical Association, 47(260), 583–621.',
    'Mann, H. B., & Whitney, D. R. (1947). On a test of whether one of two random variables is stochastically larger than the other. The Annals of Mathematical Statistics, 18(1), 50–60.',
    'Roll, R. (1984). A simple implicit measure of the effective bid-ask spread in an efficient market. Journal of Finance, 39(4), 1127–1139.',
    'Schulman, J., Moritz, P., Levine, S., Jordan, M., & Abbeel, P. (2016). High-dimensional continuous control using generalized advantage estimation. En International Conference on Learning Representations (ICLR 2016). arXiv:1506.02438.',
    'Wilcoxon, F. (1945). Individual comparisons by ranking methods. Biometrics Bulletin, 1(6), 80–83.',
  ];
  for (const r of refs) {
    k.push(new Paragraph({ alignment: AlignmentType.LEFT, spacing: { after: 100, line: 264 }, indent: { left: 480, hanging: 480 }, children: L.inline(r, { size: 21 }) }));
  }
  return k;
};
