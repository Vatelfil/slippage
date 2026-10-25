import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from matplotlib.patches import FancyBboxPatch, Rectangle
from lib import Canvas, PAL, TEXT, MUTED

c = Canvas(200, 132, (20, 13.2))
c.title("2", "Formulación jerárquica: ciclo temporal, especificación de los agentes y protocolo de coordinación",
        "Un Maestro decide cuánto y en qué ventana; tres Ejecutores deciden cómo operar cada ventana en el mercado simulado")

# ---------------------------------------------------------------- (a) linea de tiempo
c.text(5, 118.4, "(a)  Una jornada bursátil (09:30–16:00, 390 min)", fs=13, weight="bold")
X0, X1 = 26, 190
mx = lambda m: X0 + (X1 - X0) * m / 390.0   # minutos desde las 09:30 -> x

def band(m0, m1, y, h, col, label, fs=10, hatch=None):
    fill, edge, ttxt = PAL[col]
    c.ax.add_patch(Rectangle((mx(m0), y), mx(m1) - mx(m0), h, fc=fill, ec=edge, lw=1.4, hatch=hatch, zorder=2))
    c.text((mx(m0) + mx(m1)) / 2, y + h / 2, label, fs=fs, color=ttxt, weight="bold", ha="center", zorder=3)

c.text(X0 - 1, 113.4, "Ejecutor activo", fs=9.5, ha="right", color=MUTED)
band(0, 120, 111.2, 4.4, "teal", "Ejecutor 1 · Apertura")
band(120, 270, 111.2, 4.4, "purple", "Ejecutor 2 · Media jornada")
band(270, 390, 111.2, 4.4, "coral", "Ejecutor 3 · Cierre")
c.text(X0 - 1, 107.4, "sesión en S_M", fs=9.5, ha="right", color=MUTED)
band(0, 90, 105.2, 4.4, "teal", "apertura (hasta 11:00)", fs=9.5)
band(90, 270, 105.2, 4.4, "purple", "media jornada (11:00–14:00)", fs=9.5)
band(270, 390, 105.2, 4.4, "coral", "cierre (desde 14:00)", fs=9.5)
c.ax.add_patch(Rectangle((mx(90), 105.2), mx(120) - mx(90), 10.4, fc="none", ec="#A32D2D", lw=2.0, ls=(0, (4, 2)), zorder=4))
c.text(mx(120) + 1.5, 117.6, "◄ 11:00–11:30: el Maestro ve «media jornada» y el Ejecutor sigue en apertura (D5)", fs=9.2, color="#791F1F", ha="left", style="italic")

# eje de tiempo y decisiones del Maestro
ya = 100.4
c.ax.plot([X0, X1], [ya, ya], color=TEXT, lw=1.6, zorder=3)
for k in range(14):
    m = 30 * k
    c.ax.plot([mx(m), mx(m)], [ya - 0.7, ya + 0.7], color=TEXT, lw=1.4, zorder=3)
    hh, mm = divmod(9 * 60 + 30 + m, 60)
    c.text(mx(m), ya - 2.2, f"{hh:02d}:{mm:02d}", fs=8.2, ha="center", color=MUTED)
    if k < 13:
        c.ax.plot([mx(m)], [ya + 2.6], "o", color=PAL["coral"][1], ms=9, zorder=5)
        c.text(mx(m), ya + 2.6, str(k + 1), fs=6.6, color="white", ha="center", weight="bold", zorder=6)
c.text(X0 - 1, ya + 2.6, "Decisión del Maestro", fs=9.5, ha="right", color=PAL["coral"][2], weight="bold")
c.text(X1 + 1, ya, "t", fs=10, color=MUTED)

# zoom de la primera ventana
zx0, zx1, zy = X0, X1, 90.4
c.ax.plot([mx(0), zx0], [ya - 4.2, zy + 3.4], color=MUTED, lw=1.0, ls=":", zorder=1)
c.ax.plot([mx(30), zx1], [ya - 4.2, zy + 3.4], color=MUTED, lw=1.0, ls=":", zorder=1)
c.text(5, 93.4, "Zoom de una decisión\n(30 min = 60 pasos de 30 s)", fs=9.5, weight="bold", color=PAL["coral"][2], va="center")
nsteps, v_steps = 60, 20
sw = (zx1 - zx0) / nsteps
for i in range(nsteps):
    on = i < v_steps
    fill, edge, _ = PAL["coral"] if on else PAL["gray"]
    c.ax.add_patch(Rectangle((zx0 + i * sw, zy), sw, 3.4, fc=fill if on else "#FAFAF7", ec=edge, lw=0.7, zorder=2))
c.text(zx0, zy - 2.0, "▲ el Ejecutor opera 2v pasos (aquí v = 10 min → 20 pasos)", fs=9.6, color=PAL["coral"][2], weight="bold", ha="left")
c.text(zx0 + (v_steps + (nsteps - v_steps) / 2) * sw, zy - 2.0, "▲ sin operar hasta la próxima decisión", fs=9.6, color=MUTED, ha="center", style="italic")
c.text(zx1, zy - 4.8, "v ∈ {1, 5, 10, 15} min  →  2, 10, 20 o 30 pasos", fs=9.2, color=MUTED, ha="right")

# ---------------------------------------------------------------- (b) ciclo de interaccion
c.text(5, 83.2, "(b)  Ciclo de interacción", fs=13, weight="bold")
BX, BW = 8, 96
_, _, _, h1 = c.box(BX, 79.4, BW, "Agente Maestro", [
    "① Observa S_M(t): fracción pendiente, hora, volatilidad, volumen y sesión",
    "② Elige (α_t, v) ∈ A_M y calcula q_slice = α_t · (Q_total − Q_ejec)"], "coral", fs=10)
y1b = 79.4 - h1
_, _, _, h2 = c.box(BX, y1b - 10.5, BW, "Agente Ejecutor del tramo activo", [
    "④ Cada 30 s, hasta 2v pasos o hasta agotar q_slice:",
    "observa S_E (libro de órdenes) → elige a ∈ A_E → recibe R_E"], "teal", fs=10)
y2b = y1b - 10.5 - h2
_, _, _, h3 = c.box(BX, y2b - 9, BW, "Mercado simulado (ABIDES calibrado o Poisson)", [
    "Ejecuta la orden contra el libro y devuelve el nuevo estado y las ejecuciones"], "purple", fs=10)
y3b = y2b - 9 - h3
# flechas verticales
xa, xb = BX + 28, BX + BW - 28
c.arrow((xa, y1b - 0.2), (xa, y1b - 10.3), lw=2.2)
c.label(xa + 1.0, y1b - 5.2, "③ ASIGNAR", fs=9.5, color=PAL["coral"][2], ha="left")
c.arrow((xb, y1b - 10.3), (xb, y1b - 0.2), lw=2.2, color=PAL["teal"][1])
c.label(xb - 1.0, y1b - 5.2, "⑤ REPORTE", fs=9.5, color=PAL["teal"][2], ha="right")
c.arrow((xa, y2b - 0.2), (xa, y2b - 8.8), lw=2.2)
c.label(xa + 1.0, y2b - 4.5, "orden: [tipo, volumen, nivel]", fs=9.5, ha="left")
c.arrow((xb, y2b - 8.8), (xb, y2b - 0.2), lw=2.2, color=PAL["purple"][1])
c.label(xb - 1.0, y2b - 4.5, "S_E′ y ejecuciones", fs=9.5, color=PAL["purple"][2], ha="right")
# bucle del Maestro
c.poly_arrow([(BX + 0.0, y1b + 2.5), (BX - 3.0, y1b + 2.5), (BX - 3.0, 79.4 - 5.5), (BX + 0.0, 79.4 - 5.5)], lw=2.0, color=PAL["coral"][1])
c.text(BX + BW / 2, y3b - 3.2,
       "⑥ El Maestro suma lo ejecutado a Q_ejec, avanza 30 min y repite hasta las 16:00 (máx. 13 decisiones); al cerrar recibe R_M.",
       fs=9.6, color=PAL["coral"][2], ha="center", weight="bold")

# notacion y metricas
_, _, _, hq = c.box(BX, y3b - 6.4, BW, "Cantidades y métricas del episodio", [
    "IS_total = (P̄_ejec − P_ref) · Q_total  (positivo = costo en una compra)",
    "Slippage (bps) = (P̄_ejec − P_ref) / P_ref · 10⁴",
    "Cumplimiento = Q_ejec / Q_total  ·  P_ref = precio medio al inicio de la orden"], "blue", fs=10)

# ---------------------------------------------------------------- (c) especificacion MDP
RX, RW = 110, 85
c.text(RX, 83.2, "(c)  Especificación de los procesos de decisión", fs=13, weight="bold")
_, _, _, hm = c.box(RX, 79.4, RW, "Maestro: MDP_M = (S_M, A_M, P_M, R_M, γ_M, T_M)", [
    "S_M: 7 variables en [0,1], salvo OBI_agregado ∈ [−1,1] (q_t, τ_t, n_slices, volatilidad, vol_promedio, OBI_agregado, sesión)",
    "A_M = MultiDiscrete(10, 4) = 40: α_t ∈ {5 %, …, 50 %} y v ∈ {1, 5, 10, 15} min",
    "R_M = −IS_total − λ · máx(0, Q_pend) · P_mid,cierre (terminal); λ = 0,05 provisional",
    "γ_M = 0,99; horizonte 09:30–16:00; decisión cada 30 min",
    "Red actor-crítico 7 → 256 → 256 → 40 (ReLU)"], "coral", fs=9.8)
y_m = 79.4 - hm - 2.2
_, _, _, he = c.box(RX, y_m, RW, "Ejecutor: MDP_E = (S_E, A_E, P_E, R_E, γ_E, T_E)", [
    "S_E: 27 variables = 3 (propias) + 10 (compra) + 10 (venta) + 4 (mercado)",
    "A_E = MultiDiscrete(3, 10, 8) = 240: tipo de orden × fracción del pendiente (10 %…100 %) × nivel de precio",
    "R_E = (P_mid − P_ejec) · q_ejec − β · σ² · q_ejec (densa, cada 30 s); β = 0,0061796 provisional",
    "γ_E = 0,95; horizonte = ventana v asignada; decisión cada 30 s",
    "Tres redes independientes 27 → 256 → 256 → 240 (ReLU), una por tramo"], "teal", fs=9.8)
y_e = y_m - he - 2.2

# ---------------------------------------------------------------- (d) protocolo
c.text(RX, y_e - 1.4, "(d)  Mensajes del protocolo CTDE", fs=13, weight="bold")
mw = (RW - 2.5) / 2
c.box(RX, y_e - 4.6, mw, "ASIGNAR (Maestro → Ejecutor)", [
    "ejecutor_id (tramo)", "ventana_min  v", "fraccion_meta_orden  α", "q_asignado  q_slice", "hora_inicio, timestamp_inicio"], "coral", fs=9.5, tfs=10.5)
c.box(RX + mw + 2.5, y_e - 4.6, mw, "REPORTE (Ejecutor → Maestro)", [
    "ejecutor_id", "q_ejecutado, q_pendiente", "p_promedio, slippage_parcial", "pasos_usados, razon_termino",
    "hora_fin, timestamp_fin"], "teal", fs=9.5, tfs=10.5)

c.footer("CTDE: entrenamiento centralizado, ejecución descentralizada. ③ y ⑤ son mensajes validados con esquemas JSON. D5: discrepancia de corte entre S_M (11:00) y los Ejecutores (11:30), documentada.", y=2.6)
c.save("fig2_formulacion")
print("ok", y3b, y_e)
