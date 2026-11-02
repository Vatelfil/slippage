import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import textwrap
from matplotlib.patches import Rectangle, FancyBboxPatch
from lib import Canvas, PAL, TEXT, MUTED

c = Canvas(200, 132, (20, 13.2))
c.title("3", "Espacios de estado, acción y recompensa de los dos niveles de agentes",
        "Qué ve cada agente, qué puede decidir y cómo se le premia; el color indica el origen de cada dato")

SRC = {"real": "teal", "sim": "purple", "int": "gray", "hora": "amber"}
SRC_TXT = {"real": "yfinance (real)", "sim": "simulador", "int": "interno", "hora": "hora"}


def rect(x, y, w, h, col, lw=1.0, fill=None, z=2):
    f, e, t = PAL[col]
    c.ax.add_patch(Rectangle((x, y), w, h, fc=fill or f, ec=e, lw=lw, zorder=z))


# ------------------------------------------------------------------ (a) S_M
c.text(4, 119.4, "(a)  Estado del Maestro S_M: 7 variables", fs=13, weight="bold")
cols = [("#", 5.0), ("Variable", 8.4), ("Rango", 30.0), ("Origen", 41.5), ("Definición", 63.5)]
y = 115.6
c.ax.add_patch(Rectangle((4, y - 3.8), 94, 3.8, fc="#E8E6DC", ec=PAL["gray"][1], lw=1.0, zorder=2))
for name, x in cols:
    c.text(x, y - 1.9, name, fs=9.6, weight="bold", zorder=3)
rows = [("0", "q_t", "[0, 1]", "int", "Fracción pendiente: (Q_total − Q_ejec) / Q_total"),
        ("1", "τ_t", "[0, 1]", "hora", "Hora del día: (t − 09:30) / 390 min"),
        ("2", "n_slices", "[0, 1]", "int", "Decisiones ya tomadas / 13"),
        ("3", "volatilidad", "[0, 1]", "real", "Desviación móvil (6 velas) del cierre, MinMax"),
        ("4", "vol_promedio", "[0, 1]", "real", "Media móvil (6 velas) del volumen, MinMax"),
        ("5", "OBI_agregado", "[−1, 1]", "sim", "(V_bid − V_ask) / (V_bid + V_ask); hoy vale 0 (pendiente)"),
        ("6", "sesión", "{0; 0,5; 1}", "hora", "Apertura, media jornada o cierre (corte a las 11:00 y 14:00)")]
rh = 6.3
for i, (n, v, r, s, d) in enumerate(rows):
    yy = y - 3.8 - (i + 1) * rh
    c.ax.add_patch(Rectangle((4, yy), 94, rh, fc="white" if i % 2 == 0 else "#FAF9F5", ec="#D3D1C7", lw=0.6, zorder=1))
    c.text(5, yy + rh / 2, n, fs=9.6, color=MUTED, zorder=3)
    c.text(8.4, yy + rh / 2, v, fs=10, weight="bold", zorder=3)
    c.text(30, yy + rh / 2, r, fs=9.6, zorder=3)
    fill, edge, ttxt = PAL[SRC[s]]
    c.ax.add_patch(FancyBboxPatch((41.3, yy + 1.1), 19.5, rh - 2.2, boxstyle="round,pad=0,rounding_size=1.0", fc=fill, ec=edge, lw=1.0, zorder=3))
    c.text(41.3 + 9.75, yy + rh / 2, SRC_TXT[s], fs=8.8, color=ttxt, ha="center", weight="bold", zorder=4)
    lines = textwrap.wrap(d, 47)
    for j, ln in enumerate(lines):
        c.text(63.5, yy + rh / 2 + (len(lines) - 1) * 0.95 - j * 1.9, ln, fs=8.8, zorder=3)

# ------------------------------------------------------------------ (b) S_E
BX = 102
c.text(BX, 119.4, "(b)  Estado del Ejecutor S_E: 27 variables", fs=13, weight="bold")
groups = [("int", 3, "propias"), ("sim", 5, "precios de compra"), ("sim", 5, "volúmenes de compra"),
          ("sim", 5, "precios de venta"), ("sim", 5, "volúmenes de venta"), ("sim", 4, "mercado")]
cw = 94 / 27
col_for = ["gray", "blue", "blue", "coral", "coral", "purple"]
x = BX
yb = 109.4
idx = 0
for (s, n, nm), col in zip(groups, col_for):
    for k in range(n):
        rect(x + k * cw, yb, cw, 4.2, col, lw=0.9, fill=PAL[col][0])
        c.text(x + k * cw + cw / 2, yb + 2.1, str(idx), fs=7.4, color=PAL[col][2], ha="center", zorder=3)
        idx += 1
    rect(x, yb, n * cw, 4.2, col, lw=1.8, fill="none", z=3)
    x += n * cw
glab = [(0, 3, "propias", "gray"), (3, 13, "libro de compra (bid)", "blue"), (13, 23, "libro de venta (ask)", "coral"), (23, 27, "mercado", "purple")]
for a, b, nm, col in glab:
    c.text(BX + (a + b) / 2 * cw, yb + 6.3, nm, fs=9, color=PAL[col][2], weight="bold", ha="center")
leg = [("gray", "[0–2]  q_slice, q_pendiente, tau_slice"), ("blue", "[3–12]  5 precios y 5 volúmenes de compra"),
       ("coral", "[13–22]  5 precios y 5 volúmenes de venta"), ("purple", "[23–26]  spread_t, OBI_t, tasa_ordenes, P_mid")]
for i, (col, t) in enumerate(leg):
    xx, yy = BX + (i % 2) * 47.5, 104.4 - (i // 2) * 3.4
    rect(xx, yy - 0.9, 1.8, 1.8, col, lw=0.8)
    c.text(xx + 2.8, yy, t, fs=8.6, zorder=3)

# esquema del libro de ordenes
lx = BX + 22
ymid = 80.0
c.text(BX, 97.1, "Libro de órdenes: 5 niveles por lado (esquema ilustrativo, volúmenes no a escala)", fs=8.8, color=MUTED, style="italic")
ask = [5, 9, 12, 8, 14]
bid = [7, 10, 6, 13, 9]
for i, v in enumerate(ask):
    yy = ymid + 1.1 + i * 2.5
    c.ax.add_patch(Rectangle((lx, yy), v * 1.2, 2.0, fc=PAL["coral"][0], ec=PAL["coral"][1], lw=1.0, zorder=2))
    c.text(lx - 1.0, yy + 1.0, f"ask {i + 1}", fs=7.6, color=PAL["coral"][2], ha="right")
for i, v in enumerate(bid):
    yy = ymid - 1.1 - 2.0 - i * 2.5
    c.ax.add_patch(Rectangle((lx - v * 1.2, yy), v * 1.2, 2.0, fc=PAL["blue"][0], ec=PAL["blue"][1], lw=1.0, zorder=2))
    c.text(lx + 1.0, yy + 1.0, f"bid {i + 1}", fs=7.6, color=PAL["blue"][2], ha="left")
c.ax.plot([lx, lx], [ymid - 14.3, ymid + 13.9], color=TEXT, lw=1.0, zorder=3)
c.ax.plot([lx - 17, lx + 17.5], [ymid, ymid], color=PAL["purple"][1], lw=1.4, ls=(0, (4, 2)), zorder=3)
c.text(lx + 18.6, ymid, "P_mid", fs=8.8, color=PAL["purple"][2], weight="bold")
c.text(lx + 18.6, ymid + 2.2, "spread_t = ask 1 − bid 1", fs=8.2, color=MUTED, ha="left")
c.text(lx + 18.6, ymid - 2.4, "OBI_t = (V_bid − V_ask) / (V_bid + V_ask)", fs=8.2, color=MUTED, ha="left")
c.text(lx + 18.6, ymid - 5.6, "El simulador entrega este estado", fs=8.2, color=PAL["purple"][2], ha="left", style="italic")
c.text(lx + 18.6, ymid - 7.8, "cada 30 s; todo se normaliza a [0, 1]", fs=8.2, color=PAL["purple"][2], ha="left", style="italic")
c.text(lx + 18.6, ymid - 10.0, "(OBI a [−1, 1]).", fs=8.2, color=PAL["purple"][2], ha="left", style="italic")

# ------------------------------------------------------------------ (c) A_M
c.text(4, 62.4, "(c)  Acción del Maestro A_M: 40", fs=13, weight="bold")
gx, gy0, cw2, ch2 = 15, 55.2, 8.4, 3.6
c.text(gx + 2 * cw2, 58.8, "ventana v (min)", fs=9, color=MUTED, ha="center")
for j, v in enumerate([1, 5, 10, 15]):
    c.text(gx + j * cw2 + cw2 / 2, 56.7, str(v), fs=9.2, weight="bold", ha="center")
c.text(5.2, 55.7, "α", fs=10, weight="bold", color=PAL["coral"][2])
import numpy as np
for i in range(10):
    c.text(gx - 1.0, gy0 - i * ch2 - ch2 / 2 - 0.4, f"{5 * (i + 1)} %", fs=8.8, ha="right")
    for j in range(4):
        t = i / 9.0
        r, g, b = (250 - 70 * t) / 255, (236 - 120 * t) / 255, (231 - 130 * t) / 255
        c.ax.add_patch(Rectangle((gx + j * cw2, gy0 - (i + 1) * ch2), cw2, ch2, fc=(r, g, b), ec=PAL["coral"][1], lw=0.7, zorder=2))
        c.text(gx + j * cw2 + cw2 / 2, gy0 - i * ch2 - ch2 / 2, str(4 * i + j), fs=8, ha="center", color=PAL["coral"][2], zorder=3)
c.text(4, 16.6, "α: fracción de lo pendiente que se asigna", fs=8.6, color=MUTED)
c.text(4, 14.0, "Índice plano = 4 · i_α + i_v  (0 … 39)", fs=8.6, color=MUTED)

# ------------------------------------------------------------------ (d) A_E
DX = 58
c.text(DX, 62.4, "(d)  Acción del Ejecutor A_E: 240 = 3 × 10 × 8", fs=13, weight="bold")
types = [("LIMIT_BUY", "blue", "0–79"), ("LIMIT_SELL", "gray", "80–159"), ("MARKET", "coral", "160–239")]
bw, bh, bx0, by0 = 2.55, 2.55, DX + 7, 55.0
trans = ["Orden límite de compra a mejor_bid + nivel · tick (nivel 0 = pasivo)",
         "No envía orden: equivale a esperar (el proyecto solo modela compra)",
         "Orden de mercado por fracción × cantidad pendiente"]
for k, (nm, col, rng) in enumerate(types):
    x0 = bx0 + k * (8 * bw + 3.4)
    c.text(x0 + 4 * bw, 57.9, f"{nm}", fs=9.4, weight="bold", color=PAL[col][2], ha="center")
    c.text(x0 + 4 * bw, 56.4, f"índices {rng}", fs=8.2, color=MUTED, ha="center")
    for i in range(10):
        for j in range(8):
            t = i / 9.0
            fill, edge, _ = PAL[col]
            alpha = 0.25 + 0.75 * t
            base = np.array([int(PAL[col][1][m:m + 2], 16) for m in (1, 3, 5)]) / 255.0
            rgb = 1 - (1 - base) * alpha * 0.6
            c.ax.add_patch(Rectangle((x0 + j * bw, by0 - (i + 1) * bw), bw, bw, fc=tuple(rgb), ec="white", lw=0.5, zorder=2))
    c.ax.add_patch(Rectangle((x0, by0 - 10 * bw), 8 * bw, 10 * bw, fc="none", ec=PAL[col][1], lw=1.6, zorder=3))
    c.text(x0 + 4 * bw, by0 - 10 * bw - 1.6, "nivel de precio 0 … 7", fs=8, color=MUTED, ha="center")
    for ln_i, ln in enumerate(textwrap.wrap(trans[k], 31)):
        c.text(x0, by0 - 10 * bw - 4.0 - ln_i * 1.9, ln, fs=8.4, color=PAL[col][2])
c.text(bx0 - 0.8, by0 - bw / 2, "10 %", fs=8, ha="right")
c.text(bx0 - 0.8, by0 - 10 * bw + bw / 2, "100 %", fs=8, ha="right")
c.text(DX + 0.2, by0 - 5 * bw, "fracción\nde lo pend.", fs=8, color=MUTED, ha="left", va="center")
c.text(DX, 14.0, "Índice plano = 80 · tipo + 8 · fracción + nivel;  la red del Ejecutor tiene 240 salidas (una por combinación)", fs=8.6, color=MUTED)

# ------------------------------------------------------------------ (e) recompensas
RX, RW = 139, 57
c.text(RX, 62.4, "(e)  Recompensas", fs=13, weight="bold")
_, _, _, h = c.box(RX, 59.6, RW, "R_M del Maestro (terminal)", [
    "R_M = −IS_total − λ · máx(0, Q_pend) · P_mid,cierre",
    "IS_total = (P̄_ejec − P_ref) · Q_total",
    "λ = 0,05 (provisional): castiga lo no ejecutado",
    "Solo se entrega al cierre de la jornada"], "coral", fs=9, tfs=10.5, pad=1.4)
y2 = 59.6 - h - 1.8
_, _, _, h2 = c.box(RX, y2, RW, "R_E del Ejecutor (densa, cada 30 s)", [
    "R_E = (P_mid − P_ejec) · q_ejec − β · σ² · q_ejec",
    "1.er término: ahorro frente al precio medio",
    "2.º término: riesgo; σ² con ventana móvil de 20 pasos (10 min)",
    "β = 0,0061796 (0,1 · β∗, provisional)",
    "Escala: pesos por acción del tramo asignado"], "teal", fs=9, tfs=10.5, pad=1.4)
y3 = y2 - h2 - 1.8
c.box(RX, y3, RW, "Variante en estudio (decisión D3)", [
    "Riesgo sobre lo pendiente: −β · σ² · Q_pend",
    "Evita que «esperar» salga gratis",
    "Rige la opción 0 con vigilancia: cumplimiento ≥ 95 %"], "amber", fs=9, tfs=10.5, pad=1.4)

# ------------------------------------------------------------------ leyenda de origen
c.text(4, 9.4, "Origen del dato:", fs=9.6, weight="bold", color=MUTED)
x = 22
for k in ("real", "sim", "int", "hora"):
    fill, edge, ttxt = PAL[SRC[k]]
    c.ax.add_patch(FancyBboxPatch((x, 8.3), 3.4, 2.2, boxstyle="round,pad=0,rounding_size=0.8", fc=fill, ec=edge, lw=1.0, zorder=3))
    c.text(x + 4.6, 9.4, SRC_TXT[k], fs=9.2, color=ttxt)
    x += 30
c.footer("Todas las variables de S_M y S_E se normalizan a [0, 1] (OBI a [−1, 1]) según los esquemas SM_schema.json y SE_schema.json. "
         "A_E es la versión discretizada del Título I (que usaba volumen continuo y 4 niveles de precio).", y=2.6)
c.save("fig3_espacios")
print("ok")
