El problema que aborda el proyecto es el de un inversionista institucional que debe comprar una meta-orden de Q acciones de una acción del IPSA dentro de una jornada bursátil (09:30 a 16:00). En la evaluación, la meta-orden equivale al 10 % del volumen diario de la acción, o al 5 % si parte en el tramo de cierre. Comprar rápido reduce el riesgo de que el precio se mueva durante la jornada, pero aumenta el impacto en el libro de órdenes; comprar lento reduce el impacto, pero expone la orden al movimiento del precio y al riesgo de no completarla.

El costo se mide con el *implementation shortfall* en puntos base (bps) contra el precio de llegada: (precio medio ejecutado − precio de llegada) / precio de llegada × 10.000. Un valor positivo es un costo.

La ejecución es una secuencia de decisiones en la que cada compra cambia el estado del mercado y de la orden pendiente. Por eso se formula como un proceso de decisión de Markov (MDP) jerárquico, con un nivel que planifica la jornada y otro que ejecuta dentro de cada ventana. La formulación completa, con sus espacios de estado, acciones y recompensas, está en el Capítulo 4.

El entorno del IPSA impone tres condiciones al diseño, que se desarrollan en las secciones siguientes:

1. **Liquidez reducida y patrones intradiarios** (sección 2.1), que hacen que el costo dependa del momento de la ejecución.
2. **Ausencia de datos de Nivel 2 del libro de órdenes** de libre acceso, que obliga a entrenar y evaluar en simuladores calibrados con datos agregados.
3. **Una ventana corta de datos intradiarios gratuitos** (60 días en velas de 5 minutos), que obliga a trabajar con *snapshots* fechados.
