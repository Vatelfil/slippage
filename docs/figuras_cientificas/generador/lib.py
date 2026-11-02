"""Utilidades de dibujo para las figuras cientificas del proyecto (matplotlib, sin dependencias extra).

Cada figura usa un lienzo de 200 x 125 unidades (1 unidad = 0,1 pulgada con figsize 20 x 12,5).
"""
from __future__ import annotations

import textwrap
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

plt.rcParams.update({"font.family": "DejaVu Sans", "mathtext.fontset": "dejavusans", "axes.unicode_minus": False})

# (relleno, borde, texto del titulo)
PAL = {
    "teal": ("#E1F5EE", "#0F6E56", "#085041"),
    "purple": ("#EEEDFE", "#534AB7", "#3C3489"),
    "coral": ("#FAECE7", "#993C1D", "#712B13"),
    "blue": ("#E6F1FB", "#185FA5", "#0C447C"),
    "amber": ("#FAEEDA", "#854F0B", "#633806"),
    "gray": ("#F1EFE8", "#5F5E5A", "#2C2C2A"),
    "green": ("#EAF3DE", "#3B6D11", "#27500A"),
    "red": ("#FCEBEB", "#A32D2D", "#791F1F"),
    "pink": ("#FBEAF0", "#993556", "#72243E"),
}
TEXT = "#2C2C2A"
MUTED = "#5F5E5A"


class Canvas:
    def __init__(self, w: float = 200, h: float = 125, figsize: Tuple[float, float] = (20, 12.5)):
        self.w, self.h = w, h
        self.fig = plt.figure(figsize=figsize, facecolor="white")
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, w)
        self.ax.set_ylim(0, h)
        self.ax.axis("off")

    # -- texto -------------------------------------------------------------
    @staticmethod
    def chars(width: float, fs: float) -> int:
        return max(8, int(width / (fs * 0.0775)))

    def text(self, x, y, s, fs=10, color=TEXT, weight="normal", ha="left", va="center", style="normal", **kw):
        return self.ax.text(x, y, s, fontsize=fs, color=color, fontweight=weight, ha=ha, va=va, fontstyle=style, **kw)

    # -- cajas -------------------------------------------------------------
    def box(self, x: float, y_top: float, w: float, title: str, lines: Sequence[str] = (), color: str = "gray",
            fs: float = 10, tfs: float = 11.5, pad: float = 1.6, bullet: bool = True, h: Optional[float] = None,
            title_align: str = "left", sub: Optional[str] = None, lw: float = 1.4, ls: str = "-", alpha_fill: float = 1.0
            ) -> Tuple[float, float, float, float]:
        """Caja con titulo y lineas; la altura se ajusta al texto. Devuelve (x, y_top, w, h)."""
        fill, edge, ttxt = PAL[color]
        n = self.chars(w - 2 * pad - (1.6 if bullet else 0), fs)
        wrapped: List[Tuple[str, bool]] = []
        for ln in lines:
            parts = textwrap.wrap(ln, n, break_long_words=False) or [""]
            for i, p in enumerate(parts):
                wrapped.append((p, i == 0))
        tl = tfs * 0.215
        bl = fs * 0.205
        sub_lines = textwrap.wrap(sub, self.chars(w - 2 * pad, fs - 0.5)) if sub else []
        height = h if h is not None else pad * 2 + tl + 0.3 + (len(sub_lines) * bl * 0.95 if sub_lines else 0) + 0.6 + len(wrapped) * bl
        self.ax.add_patch(FancyBboxPatch((x, y_top - height), w, height, boxstyle="round,pad=0,rounding_size=1.2",
                                         fc=fill, ec=edge, lw=lw, ls=ls, alpha=alpha_fill, zorder=2))
        ty = y_top - pad - tl / 2
        tx = x + pad if title_align == "left" else x + w / 2
        self.text(tx, ty, title, fs=tfs, color=ttxt, weight="bold", ha=title_align, zorder=3)
        cy = ty - tl / 2 - 0.3
        for sline in sub_lines:
            cy -= bl * 0.95
            self.text(tx, cy, sline, fs=fs - 0.5, color=MUTED, ha=title_align, style="italic", zorder=3)
        cy -= 0.6
        for p, first in wrapped:
            cy -= bl
            if bullet:
                if first:
                    self.text(x + pad, cy + bl / 2, "•", fs=fs, color=edge, zorder=3)
                self.text(x + pad + 1.6, cy + bl / 2, p, fs=fs, color=TEXT, zorder=3)
            else:
                self.text(x + pad, cy + bl / 2, p, fs=fs, color=TEXT, zorder=3)
        return x, y_top, w, height

    def panel(self, x, y_top, w, h, title, color="gray", fs=13, ls="--"):
        """Contenedor discontinuo con rotulo (agrupa cajas)."""
        fill, edge, ttxt = PAL[color]
        self.ax.add_patch(FancyBboxPatch((x, y_top - h), w, h, boxstyle="round,pad=0,rounding_size=1.8", fc="none",
                                         ec=edge, lw=1.6, ls=ls, zorder=1))
        self.text(x + 1.8, y_top - 2.4, title, fs=fs, color=ttxt, weight="bold", zorder=3)

    def badge(self, x, y, s, color="gray", fs=9.5, w=None):
        fill, edge, ttxt = PAL[color]
        w = w or (len(s) * fs * 0.075 + 3)
        self.ax.add_patch(FancyBboxPatch((x, y - 1.6), w, 3.2, boxstyle="round,pad=0,rounding_size=1.6", fc=edge, ec=edge, zorder=3))
        self.text(x + w / 2, y, s, fs=fs, color="white", weight="bold", ha="center", zorder=4)
        return w

    # -- flechas -----------------------------------------------------------
    def arrow(self, p0, p1, color="#444441", lw=2.0, ls="-", rad=0.0, both=False, ms=16, z=4):
        style = "<|-|>" if both else "-|>"
        self.ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=style, mutation_scale=ms, lw=lw, color=color, ls=ls,
                                          connectionstyle=f"arc3,rad={rad}", shrinkA=0, shrinkB=0, zorder=z))

    def poly_arrow(self, pts, color="#444441", lw=2.0, ls="-", ms=16, z=4):
        xs, ys = zip(*pts)
        self.ax.plot(xs[:-1], ys[:-1], color=color, lw=lw, ls=ls, zorder=z, solid_capstyle="butt")
        self.arrow(pts[-2], pts[-1], color=color, lw=lw, ls=ls, ms=ms, z=z)

    def label(self, x, y, s, fs=9.5, color=MUTED, ha="center", bg=True):
        t = self.text(x, y, s, fs=fs, color=color, ha=ha, style="italic", zorder=6)
        if bg:
            t.set_bbox(dict(fc="white", ec="none", pad=1.2, alpha=0.95))
        return t

    def title(self, num: str, s: str, sub: Optional[str] = None):
        self.text(4, self.h - 4.2, f"Figura {num}.", fs=20, weight="bold", color=TEXT)
        self.text(4 + 17.5 + len(num) * 1.0, self.h - 4.2, s, fs=20, color=TEXT)
        if sub:
            self.text(4, self.h - 8.6, sub, fs=12, color=MUTED, style="italic")

    def footer(self, s: str, y: float = 2.8, fs: float = 10.5):
        lines = textwrap.wrap(s, int((self.w - 8) / (fs * 0.0835)))
        for i, ln in enumerate(lines):
            self.text(4, y + (len(lines) - 1 - i) * 2.4, ln, fs=fs, color=MUTED, style="italic")

    def save(self, stem: str, dpi: int = 200):
        out = Path(__file__).resolve().parents[1] / stem   # docs/figuras_cientificas/<stem>.(png|pdf)
        self.fig.savefig(f"{out}.png", dpi=dpi, facecolor="white")
        self.fig.savefig(f"{out}.pdf", facecolor="white")
        plt.close(self.fig)
