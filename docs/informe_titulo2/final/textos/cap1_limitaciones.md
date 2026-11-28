El proyecto se desarrolló dentro de restricciones de diseño definidas desde el Título I. Las limitaciones que se derivan de los resultados se discuten en el Capítulo 8 (sección 8.6).

1. **Sin ejecución en tiempo real.** El alcance fue investigativo y de desarrollo de software. El sistema no se conecta a corredoras ni envía órdenes reales a la Bolsa de Santiago; todas las pruebas se hicieron en simulación.
2. **Universo limitado al IPSA.** El trabajo se circunscribe a acciones del IPSA. No considera otros mercados, renta fija, divisas ni criptomonedas. La evaluación usó tres acciones: FALABELLA, COPEC y ECL.
3. **Dependencia de la calidad de los datos.** Sin datos de Nivel 2 del libro de órdenes, los simuladores se calibraron con velas de 5 minutos, lo que limita la fidelidad con que reproducen el mercado real, en particular el spread.
4. **Sin predicción de eventos extremos.** El sistema no está diseñado para crisis financieras, estallidos sociales u otros eventos que alteren la microestructura del mercado de forma drástica. Los datos usados cubren unos 60 días de mercado, sin periodos de estrés severo.
5. **Sin módulo de cumplimiento normativo.** El prototipo no verifica en tiempo real el cumplimiento de la regulación de la Comisión para el Mercado Financiero (CMF, 2024).
6. **Una meta-orden a la vez.** El sistema ejecuta una meta-orden de un solo activo en cada jornada. La coordinación de varias órdenes simultáneas sobre distintos activos queda fuera del alcance.
