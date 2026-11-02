"""Figura 4: diseño experimental y evaluación. Lee las meta-órdenes y los resultados de benchmarks del repositorio."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle

sys.path.insert(0, str(Path(__file__).resolve().parent))
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from lib import Canvas, PAL, TEXT, MUTED  # noqa: E402
from src.analysis.benchmarks import schedule_desde, periodo_inicio  # noqa: E402


def cargar(p):
    with open(REPO / p, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


v1 = cargar("data/meta_ordenes/meta_ordenes_v1.json")["meta_ordenes"]
v2 = cargar("data/meta_ordenes/meta_ordenes_v2_candidata.json")["meta_ordenes"]
b2 = cargar("data/analysis/benchmarks_meta_ordenes_v2.json")
perfil = pd.read_csv(REPO / "data/meta_ordenes/perfil_volumen_v1.csv", index_col=0)

c = Canvas(200, 132, (20, 13.2))
c.title("4", "Diseño experimental y evaluación frente a TWAP y VWAP",
        "Mismas meta-órdenes y mismas semillas de mercado para las referencias y para el sistema, de modo que la comparación sea pareada")

fmt = lambda n: f"{int(n):,}".replace(",", ".")

# ------------------------------------------------------------------ (a) flujo
c.text(4, 118.8, "(a)  Protocolo", fs=13, weight="bold")
steps = [("1 · Meta-órdenes", "teal", ["10 órdenes de compra (3 activos, 3 tramos)", "semilla de orden = 9000 + 10 · i", "reservadas: no se usan para entrenar"], "hecho"),
         ("2 · Referencias TWAP y VWAP", "gray", ["ABIDES calibrado, órdenes de mercado", "ventana de 15 min por período", "2 semillas por orden (40 corridas)"], "hecho"),
         ("3 · Sistema Maestro + Ejecutores", "coral", ["mismas órdenes y semillas de mercado", "redes entrenadas con PPO", "hoy: solo redes sin entrenar (control)"], "pendiente"),
         ("4 · Comparación pareada", "blue", ["diferencia sistema − referencia (bps)", "Wilcoxon, t pareada, IC 95 % bootstrap", "por orden × semilla y por orden"], "listo (script)"),
         ("5 · Sensibilidad", "purple", ["por tamaño de orden", "por tramo de inicio y por activo", "hipótesis: reducción del IS ≥ 10 %"], "listo (script)")]
bw, gap = 34.6, 4.6
for i, (t, col, ls, st) in enumerate(steps):
    x = 4 + i * (bw + gap)
    _, _, _, h = c.box(x, 115.2, bw, t, ls, col, fs=9.2, tfs=10.4, pad=1.4)
    fill, edge, ttxt = PAL[col]
    stc = {"hecho": "green", "pendiente": "amber", "listo (script)": "blue"}[st]
    c.badge(x + 1.4, 115.2 - h - 2.4, st, color=stc, fs=8.6)
    if i < 4:
        c.arrow((x + bw + 0.4, 115.2 - h / 2), (x + bw + gap - 0.4, 115.2 - h / 2), lw=2.2, ms=14)

# ------------------------------------------------------------------ (b) tabla de meta-ordenes
TY = 91.0
c.text(4, TY + 2.6, "(b)  Las 10 meta-órdenes (v1 oficial en el repositorio; v2 candidata a decisión D1)", fs=12, weight="bold")
cols = [("ID", 5.0, "left"), ("Activo", 14.2, "left"), ("Inicio", 31.0, "left"), ("v1: acciones", 66.5, "right"),
        ("v2: acciones (% del día)", 71.0, "left"), ("Semilla", 96.0, "left")]
c.ax.add_patch(Rectangle((4, TY - 4.0), 100, 4.0, fc="#E8E6DC", ec=PAL["gray"][1], lw=1.0, zorder=2))
for nm, x, ha in cols:
    c.text(x, TY - 2.0, nm, fs=8.8, weight="bold", ha=ha, zorder=3)
colr = {"apertura": "teal", "media_jornada": "purple", "cierre": "coral"}
rh = 4.55
for i, (a, b) in enumerate(zip(v1, v2)):
    yy = TY - 4.0 - (i + 1) * rh
    c.ax.add_patch(Rectangle((4, yy), 100, rh, fc="white" if i % 2 == 0 else "#FAF9F5", ec="#D3D1C7", lw=0.6, zorder=1))
    col = colr[a["tramo_inicio"]]
    c.ax.add_patch(Rectangle((4, yy), 1.1, rh, fc=PAL[col][1], ec="none", zorder=3))
    c.text(6.4, yy + rh / 2, a["id"], fs=9, weight="bold", zorder=3)
    c.text(14.2, yy + rh / 2, a["ticker"], fs=9, zorder=3)
    nm = {"apertura": "apertura", "media_jornada": "media jornada", "cierre": "cierre"}[a["tramo_inicio"]]
    c.text(31.0, yy + rh / 2, f"{nm} {a['hora_inicio']}", fs=9, color=PAL[col][2], zorder=3)
    c.text(66.5, yy + rh / 2, fmt(a["cantidad"]), fs=9, ha="right", zorder=3)
    c.text(71.0, yy + rh / 2, f"{fmt(b['cantidad'])}  ({b['pct_volumen_dia']:.0f} %)", fs=9, zorder=3)
    c.text(96.0, yy + rh / 2, str(a["semilla"]), fs=9, color=MUTED, zorder=3)
yend = TY - 4.0 - 10 * rh
c.text(4, yend - 2.0, "Cada corrida usa semilla = semilla de la orden + índice de réplica (1, 2, …); el simulador suma además el período.", fs=8.4, color=MUTED, style="italic")
c.text(4, yend - 4.2, "Volumen del día: mediana de 30 jornadas simuladas con la calibración vigente de cada activo.", fs=8.4, color=MUTED, style="italic")

# ------------------------------------------------------------------ (c) reparto TWAP / VWAP
CX = 110
c.text(CX, TY + 2.6, "(c)  Cómo reparten la orden las referencias (MO-05 v2: 29.100 acciones desde las 11:00)", fs=12, weight="bold")
p0 = periodo_inicio("media_jornada")
tw = schedule_desde("TWAP", 29100, p0)
vw = schedule_desde("VWAP", 29100, p0, perfil)
nper = len(tw) - p0
x0, x1, yb = CX + 9, 194, 70.5
sc = 14.0 / max(max(tw), max(vw))
c.ax.plot([x0 - 1, x1], [yb, yb], color=TEXT, lw=1.2, zorder=3)
bwid = (x1 - x0) / nper
for k in range(nper):
    p = p0 + k
    hh, mm = divmod(9 * 60 + 30 + 30 * p, 60)
    xx = x0 + k * bwid
    c.ax.add_patch(Rectangle((xx + 0.25, yb), bwid * 0.42, tw[p] * sc, fc=PAL["blue"][0], ec=PAL["blue"][1], lw=1.0, zorder=2))
    c.ax.add_patch(Rectangle((xx + 0.25 + bwid * 0.46, yb), bwid * 0.42, vw[p] * sc, fc=PAL["amber"][0], ec=PAL["amber"][1], lw=1.0, zorder=2))
    c.text(xx + bwid / 2, yb - 1.5, f"{hh:02d}:{mm:02d}", fs=7.6, ha="center", color=MUTED)
c.text(CX, yb + 7, "acciones\npor período", fs=8, color=MUTED, ha="left", va="center")
for xlab, y, v, col in [(x0 + 0.4, yb + tw[p0] * sc + 1.2, tw[p0], "blue")]:
    c.text(xlab, y, f"TWAP: {fmt(round(v))}", fs=8, color=PAL[col][2], weight="bold", ha="left")
c.text(x0 + 4.9 * bwid, yb + vw[p0 + 7] * sc + 1.4, f"VWAP: {fmt(round(vw[p0 + 7]))} (cierre)", fs=8, color=PAL["amber"][2], weight="bold", ha="center")
c.text(x0 + 0.4 + 0.5 * bwid, yb + vw[p0] * sc + 1.2, f"{fmt(round(vw[p0]))}", fs=8, color=PAL["amber"][2], weight="bold", ha="left")
lx = x1 - 26
c.ax.add_patch(Rectangle((CX + 1, 89.4), 2, 1.6, fc=PAL["blue"][0], ec=PAL["blue"][1], lw=1.0))
c.text(CX + 4, 90.2, "TWAP: partes iguales por período de 30 min", fs=8.6)
c.ax.add_patch(Rectangle((CX + 1, 87.2), 2, 1.6, fc=PAL["amber"][0], ec=PAL["amber"][1], lw=1.0))
c.text(CX + 4, 88.0, "VWAP: proporcional al volumen histórico de cada tramo", fs=8.6)

# ------------------------------------------------------------------ (d) resultados preliminares de las referencias
c.text(CX, 62.6, "(d)  Resultado actual de las referencias (archivo v2, ABIDES, 2 semillas por orden)", fs=12, weight="bold")
tab = b2["tabla"]
ids = [o["id"] for o in v2]
data = {(r["orden"], r["estrategia"]): r for r in tab}
yb2, top = 43.2, 59.0
smax = max(data[(i, e)]["slippage_bps_medio"] + (data[(i, e)]["slippage_bps_ee"] or 0) for i in ids for e in ("TWAP", "VWAP"))
smin = min(data[(i, e)]["slippage_bps_medio"] - (data[(i, e)]["slippage_bps_ee"] or 0) for i in ids for e in ("TWAP", "VWAP"))
scale = (top - 45.5) / smax
yb2 = 45.5 + (-smin) * scale * 0.9 + 0.2
scale = (top - yb2) / smax
x0, x1 = CX + 9, 194
gw = (x1 - x0) / 10
c.ax.plot([x0 - 1, x1], [yb2, yb2], color=TEXT, lw=1.2, zorder=3)
for k, i in enumerate(ids):
    xx = x0 + k * gw
    for j, (e, col) in enumerate([("TWAP", "blue"), ("VWAP", "amber")]):
        r = data[(i, e)]
        v, ee = r["slippage_bps_medio"], r["slippage_bps_ee"] or 0
        bx = xx + 0.5 + j * (gw * 0.44)
        h = v * scale
        c.ax.add_patch(Rectangle((bx, yb2), gw * 0.4, h, fc=PAL[col][0], ec=PAL[col][1], lw=1.0, zorder=2))
        xm = bx + gw * 0.2
        c.ax.plot([xm, xm], [yb2 + (v - ee) * scale, yb2 + (v + ee) * scale], color=TEXT, lw=0.9, zorder=4)
    tr = {"apertura": "A", "media_jornada": "M", "cierre": "C"}[[o for o in v2 if o["id"] == i][0]["tramo_inicio"]]
    c.text(xx + gw / 2, yb2 - (-smin) * scale - 1.9 if smin < 0 else yb2 - 1.9, i[-2:], fs=8, ha="center", color=MUTED)
for tv in (0, 100, 200, 300):
    ytk = yb2 + tv * scale
    if tv:
        c.ax.plot([x0 - 1, x1], [ytk, ytk], color="#D3D1C7", lw=0.7, zorder=1)
    c.text(x0 - 2.0, ytk, str(tv), fs=7.8, color=MUTED, ha="right")
c.text(CX, 60.0, "slippage (bps)", fs=8.2, color=MUTED, ha="left")
c.text(x0, 38.6, "MO-01 … MO-10 (apertura 01–04, media jornada 05–07, cierre 08–10); barras de error: error estándar entre semillas", fs=8, color=MUTED, ha="left")
c.text(x0, 36.4, "En las órdenes de cierre (08–10) TWAP y VWAP coinciden: queda un solo tramo.", fs=8, color=MUTED, ha="left")
comp = b2.get("comparacion", {})
ej = b2.get("ejecutabilidad", {})
c.box(CX, 33.6, 86, "Lectura", [
    "10 de 10 órdenes ejecutables: TWAP completa al menos el 95 % (19 de 20 corridas lo logran)",
    "TWAP − VWAP = −6,59 bps; Wilcoxon p = 0,297: sin diferencia significativa con 2 semillas",
    "Es la línea base que debe batir el sistema entrenado"], "gray", fs=8.6, tfs=9.8, pad=1.3)

# ------------------------------------------------------------------ (e) metricas y estadistica
c.text(4, 31.6, "(e)  Métricas y estadística", fs=12, weight="bold")
c.box(4, 29.0, 49, "Métricas por corrida", [
    "IS = (P̄_ejec − P_ref) · Q_total",
    "Slippage (bps) = (P̄_ejec − P_ref) / P_ref · 10⁴",
    "Cumplimiento = Q_ejec / Q_total",
    "Positivo = costo (solo compras)"], "blue", fs=8.6, tfs=9.8, pad=1.3)
c.box(55, 29.0, 52, "Pruebas estadísticas", [
    "Diferencia sistema − referencia, pareada",
    "Wilcoxon y t pareada por orden × semilla",
    "Wilcoxon sobre medias por orden",
    "IC 95 % por bootstrap (10.000 réplicas)"], "blue", fs=8.6, tfs=9.8, pad=1.3)
c.box(CX, 21.4, 86, "Criterios, semillas e hipótesis", [
    "Orden ejecutable: el TWAP completa al menos el 95 % (media de semillas)",
    "Semillas: referencias y sistema 1–2 más la de cada orden; evaluación de redes del Ejecutor 5001–5015; entrenamiento desde 1001",
    "Hipótesis del Título I: IS del sistema al menos 10 % menor que el de TWAP y VWAP"], "amber", fs=8.6, tfs=9.8, pad=1.3)
c.footer("Estado al 23 de octubre de 2026: las referencias están medidas; falta el sistema entrenado (el entrenamiento completo del Maestro y de los Ejecutores es el trabajo de los sprints 6 y 7).", y=2.6)
c.save("fig4_diseno_experimental")
print("ok")
