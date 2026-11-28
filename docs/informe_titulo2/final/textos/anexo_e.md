Este anexo explica cómo se calcula cada prueba estadística usada en los capítulos 5 a 8. Todas se aplicaron con la librería SciPy de Python.

## E.1 Wilcoxon de rangos con signo (prueba principal)

Compara dos estrategias medidas en los mismos días (Wilcoxon, 1945), sin suponer que las diferencias siguen una distribución normal.

1. Se calcula la diferencia de costo de cada día (por ejemplo, sistema − TWAP).
2. Se ordenan las n diferencias por su valor absoluto y se les asigna un rango (1 a la menor).
3. Se suman por separado los rangos de las diferencias negativas y los de las positivas.
4. El valor p es la probabilidad de obtener un desequilibrio igual o mayor entre esas dos sumas si las dos estrategias costaran lo mismo. Se usa la versión bilateral, con α = 0,05.

## E.2 Corrección de Holm

Cuando se hacen varias pruebas a la vez, aumenta la probabilidad de encontrar una diferencia por azar. Holm (1979) corrige los valores p:

1. Se ordenan los k valores p de menor a mayor.
2. El menor se multiplica por k, el siguiente por k − 1, y así hasta el último, que se multiplica por 1.
3. Se mantiene el orden: un p corregido nunca queda menor que el anterior, ni mayor que 1.

## E.3 Intervalo de confianza por bootstrap pareado

Se basa en el remuestreo de Efron (1979).

1. Se toman las n diferencias por día.
2. Se generan miles de muestras nuevas (3.000 o 10.000) eligiendo n diferencias al azar con reposición.
3. Se calcula la media de cada muestra.
4. El IC 95 % va del percentil 2,5 al percentil 97,5 de esas medias.

## E.4 t pareado y Shapiro-Wilk

El t pareado compara la media de las diferencias con cero suponiendo normalidad. Solo se usa como complemento cuando la prueba de Shapiro-Wilk (Shapiro y Wilk, 1965) no rechaza que las diferencias sean normales (p > 0,05).

## E.5 Tamaño del efecto

- **d de Cohen pareado:** media de las diferencias dividida por su desviación estándar. Como referencia, 0,2 es un efecto pequeño, 0,5 mediano y 0,8 grande (Cohen, 1988).
- **Correlación biserial de rangos r:** versión del tamaño del efecto para Wilcoxon; va de −1 a 1.

## E.6 Correlación de Spearman

Mide la asociación monótona entre dos variables (Spearman, 1904).

1. Se reemplaza cada valor por su rango.
2. Se calcula la correlación de Pearson entre los rangos (ρ, entre −1 y 1).
3. El valor p prueba si ρ = 0 con la aproximación t de n − 2 grados de libertad.

## E.7 Pitman-Morgan (varianzas de datos pareados)

Compara la variabilidad de dos estrategias medidas en los mismos días (Pitman, 1939; Morgan, 1939).

1. En cada día se calculan la suma S = sistema + TWAP y la resta D = sistema − TWAP.
2. Si las dos varianzas fueran iguales, la correlación entre S y D sería 0.
3. La correlación observada r se convierte en t = r·√((n − 2)/(1 − r²)), con n − 2 grados de libertad, y se obtiene el valor p.
4. El IC de la razón de desviaciones se obtiene por bootstrap pareado de 10.000 remuestreos.

## E.8 Kruskal-Wallis y Mann-Whitney

Kruskal-Wallis (Kruskal y Wallis, 1952) compara tres o más grupos sin suponer normalidad: se ordenan todas las observaciones juntas y se compara el rango medio de cada grupo con el esperado si todas vinieran de la misma distribución. Mann-Whitney (Mann y Whitney, 1947) hace lo mismo para dos grupos independientes.

## E.9 Friedman y Page (datos en bloques)

Se usan cuando los mismos días se repiten en varias condiciones (tres profundidades o tres tamaños).

1. Dentro de cada día se ordenan las condiciones (rango 1 a 3) según la diferencia sistema − TWAP.
2. **Friedman** (1937) prueba si los rangos medios de las condiciones difieren.
3. **Page** prueba algo más específico: si los rangos siguen un orden esperado (por ejemplo, que la diferencia baje al crecer el tamaño). Por eso tiene más potencia que Friedman cuando hay una tendencia (Page, 1963).

## E.10 Kolmogórov-Smirnov (validación del simulador)

Compara dos distribuciones completas, por ejemplo los retornos simulados y los reales. Mide la distancia máxima D entre sus funciones de distribución acumulada y calcula la probabilidad de una distancia así si ambas muestras vinieran de la misma distribución. Con muestras muy grandes detecta diferencias pequeñas, por eso se informa también la razón entre D y su valor crítico.
