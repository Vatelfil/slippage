import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import Canvas, PAL

c = Canvas(200, 132, (20, 13.2))
c.title("1", "Arquitectura del sistema y flujo de datos: de los datos reales a la evaluación",
        "Los datos reales solo calibran el simulador; los agentes aprenden dentro del mercado simulado")

W, GAP, X0, TOP = 31, 9, 5, 106.5
xs = [X0 + i * (W + GAP) for i in range(5)]
heads = [("1 · Datos de mercado reales", "teal", "se ejecuta en el PC"),
         ("2 · Calibración y validación", "teal", "se ejecuta en el PC"),
         ("3 · Entorno simulado", "purple", "Colab (ABIDES) o PC (Poisson)"),
         ("4 · Sistema multiagente", "coral", "PC (pruebas) o Colab"),
         ("5 · Entrenamiento y evaluación", "blue", "Colab (entrenar), PC (analizar)")]
HY = TOP + 8
HH = 0
for x, (t, col, sub) in zip(xs, heads):
    _, _, _, HH = c.box(x, HY, W, t, [], col, tfs=11.5, title_align="center", lw=2.0, sub=sub)

yh = HY - HH / 2
for i, lab in enumerate(["estadísticos", "JSON", "S_E  ⇄  A_E", "episodios"]):
    xa, xb = xs[i] + W + 0.6, xs[i + 1] - 0.6
    c.arrow((xa, yh), (xb, yh), lw=2.4, ms=18)
    c.label((xa + xb) / 2, yh + 2.6, lab, fs=8.5, bg=False)

# puente: features reales -> Maestro
c.poly_arrow([(xs[0] + W / 2, HY + 0.2), (xs[0] + W / 2, 121.2), (xs[3] + W / 2, 121.2), (xs[3] + W / 2, HY + 0.4)],
             color=PAL["teal"][1], lw=2.2, ls=(0, (5, 3)))
c.label((xs[1] + xs[2] + W) / 2 + 0.5, 121.2, "volatilidad y vol_promedio reales  →  S_M del Maestro", fs=10, color=PAL["teal"][2])

GP = 2.2


def stack(x, items, y=HY - HH - 2.2):
    for title, lines, col in items:
        _, yt, _, h = c.box(x, y, W, title, lines, col, fs=10, tfs=11)
        y -= h + GP
    return y


stack(xs[0], [
    ("Fuente", ["yfinance: 30 acciones del IPSA (.SN)", "Velas de 5 minutos (OHLCV)", "Activos usados: FALABELLA, COPEC y ECL",
                "Copias versionadas por fecha (snapshots)"], "teal"),
    ("Limpieza", ["UTC → America/Santiago", "Filtro horario 09:30–16:00", "Relleno de nulos hacia adelante",
                  "Subasta de cierre fusionada (vela 15:55)"], "teal"),
    ("Variables derivadas", ["volatilidad: desviación móvil de 6 velas", "vol_promedio: volumen medio móvil de 6 velas",
                             "Normalización MinMax a [0, 1]", "sesión y τ_t a partir de la hora"], "teal"),
])
stack(xs[1], [
    ("Calibración de ABIDES (rmsc04)", ["r_bar: precio mediano real", "fund_vol: volatilidad del valor fundamental",
                                        "Nº de agentes de ruido y λ_a; agentes de momentum",
                                        "Market maker: ventana, POV, espaciado", "Salida: un JSON por activo y tramo"], "teal"),
    ("Calibración de Poisson", ["λ⁺ y λ⁻ (llegada de órdenes) y θ (cancelación)", "90 pares activo × tramo",
                                "Tamaño medio de orden: 1 millón de CLP"], "teal"),
    ("Validación estadística (2.2.5)", ["KS, Mann–Whitney, Kruskal–Wallis y d de Cohen",
                                        "Compara spread, volatilidad y volumen simulados con los reales",
                                        "Resultado: el KS rechaza; volatilidad a −7 % … +1 % de la real (COPEC, ECL)",
                                        "Límites documentados"], "amber"),
])
stack(xs[2], [
    ("ABIDES-Gym (rmsc04)", ["Libro de órdenes limitado (LOB) de 5 niveles",
                                          "1 exchange, 2 market makers, 102 agentes de valor",
                                          "Agentes de ruido (250–1000) y de momentum (3–12), según el activo",
                                          "Paso de decisión: 30 segundos"], "purple"),
    ("Simulador de Poisson (liviano)", ["Llegadas y cancelaciones por proceso de Poisson",
                                                    "Corre en el PC, sin ABIDES",
                                                    "Pruebas y primeros benchmarks"], "purple"),
    ("Puente Ejecutor–ABIDES", ["Acción [tipo, volumen, nivel] → orden de mercado o límite",
                                "Libro de 5 niveles → vector S_E de 27 variables",
                                "Precios en décimos de peso → CLP"], "purple"),
])
stack(xs[3], [
    ("Maestro (1 agente)", ["Ve S_M (7 variables); decide A_M (40 opciones)", "Cada 30 min: fracción α de lo pendiente y ventana",
                            "Red actor-crítico 256–256, γ = 0,99", "Premio R_M solo al final de la jornada"], "coral"),
    ("Ejecutores (3, uno por tramo)", ["Ven S_E (27); deciden A_E (240 opciones)", "Cada 30 s, dentro de la ventana asignada",
                                               "Redes independientes 256–256, γ = 0,95", "Premio R_E en cada paso",
                                               "Apertura · Media jornada · Cierre"], "coral"),
    ("Coordinación (protocolo CTDE)", ["ASIGNAR: tramo, ventana, α y cantidad", "REPORTE: ejecutado, precio medio, pendiente",
                                          "Mensajes validados con esquemas JSON"], "coral"),
])
stack(xs[4], [
    ("Entrenamiento PPO", ["Ventaja GAE (λ = 0,95); recorte ε = 0,2", "Tasa 3·10⁻⁴, 4 épocas, minibatch 64",
                           "10 episodios por actualización", "Semillas de entrenamiento desde 1001"], "blue"),
    ("Monitoreo", ["Retorno, cumplimiento y slippage por episodio", "Entropía, KL y fracción recortada",
                   "Alertas (p. ej., política que «espera»)"], "blue"),
    ("Evaluación", ["10 meta-órdenes con semillas pareadas", "Referencias: TWAP y VWAP",
                    "IS, slippage (bps) y cumplimiento", "Wilcoxon pareado; IC 95 % por bootstrap"], "blue"),
    ("Hipótesis del Título I", ["IS del sistema al menos 10 % menor que el de TWAP y VWAP"], "gray"),
])

# franja de infraestructura
c.panel(4, 29, 192, 22.5, "Infraestructura: dónde vive cada pieza", "amber", fs=12.5)
iw, ig = 44, 4.3
items = [("PC con Claude Code", ["Escribe código y pruebas (pytest)", "Calibra con los datos reales", "Analiza resultados y genera figuras"]),
         ("GitHub (Vatelfil/slippage)", ["Código, JSON de calibración y meta-órdenes", "Ramas y pull requests", "Entrada de Colab (clona la rama)"]),
         ("Google Colab (CPU)", ["Entorno abides: Python 3.9, torch 1.13.1", "Corre ABIDES y el entrenamiento PPO",
                                  "Cuadernos Jupyter (.ipynb); 2 sesiones"]),
         ("Google Drive", ["Guarda resultados (JSON, CSV, checkpoints)", "Descarga manual al Escritorio",
                           "Se copia a data/colab_resultados del repo"])]
for i, (t, ls) in enumerate(items):
    c.box(6 + i * (iw + ig), 24, iw, t, ls, "amber", fs=10, tfs=11)
for i in range(3):
    xa = 6 + i * (iw + ig) + iw
    c.arrow((xa + 0.2, 17.6), (xa + ig - 0.2, 17.6), lw=2, ms=14)

c.footer("PC: datos reales, calibración, pruebas y análisis. Colab: simulación ABIDES y entrenamiento. Drive: transporte de resultados. "
         "El simulador de Poisson permite ensayar todo el flujo en el PC sin ABIDES.", y=2.6)
c.save("fig1_arquitectura")
print("ok")
