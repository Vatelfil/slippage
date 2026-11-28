## 3.6 Criterios de validación del simulador

Antes de calibrar, el Título I fijó que el simulador se compararía con los datos reales del IPSA en cuatro aspectos:
- la distribución del spread por tramo horario;
- el perfil de volumen intradiario;
- la autocorrelación de los retornos del precio medio, para verificar que el simulador no introduce dependencias artificiales;
- los hechos estilizados del libro de órdenes: colas gruesas en los retornos, agrupamiento de la volatilidad y reversión del spread (Gould et al., 2013).

En el desarrollo, estos criterios se concretaron en pruebas por tramo sobre los retornos de 5 minutos (Kolmogórov-Smirnov y Mann-Whitney), el tamaño del efecto, el patrón intradiario de volatilidad y volumen, y la comparación del spread. El primer criterio suponía que el spread se ensancha en la media jornada; los datos reales lo refutaron (sección 3.5), así que se evaluó el patrón observado. Los resultados de la validación están en el Capítulo 5, sección 5.6.
