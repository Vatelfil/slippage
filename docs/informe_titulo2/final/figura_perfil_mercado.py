"""Redibuja la figura del perfil intradiario del IPSA (Capítulo 3) con ejes rotulados en español.

Los valores son los de la tabla de la sección 3.5 (30 tickers, velas de 5 minutos, snapshot de septiembre de 2026),
calculados en el informe de avance de octubre.
"""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


def es(v, dec):
    """Número con formato chileno: coma decimal y punto de miles."""
    t = f'{v:,.{dec}f}'
    return t.replace(',', '§').replace('.', ',').replace('§', '.')

TRAMOS = ['Apertura\n09:30–11:00', 'Media jornada\n11:00–14:00', 'Cierre\n14:00–16:00']
PANELES = [
    ('Spread relativo', [0.138, 0.112, 0.128], 'Spread (% del precio)', 3),
    ('Volatilidad', [0.00251, 0.00156, 0.00151], 'Desv. estándar del retorno\nentre velas de 5 min', 5),
    ('Volumen', [396765, 456967, 698419], 'Acciones transadas\npor vela de 5 min', 0),
]
COLORES = ['#548235', '#A9D18E', '#385723']


def main(salida=Path(__file__).resolve().parent / 'recursos/perfil_mercado_ipsa_real.png'):
    fig, axs = plt.subplots(1, 3, figsize=(12, 4.2))
    for ax, (titulo, vals, ylab, dec) in zip(axs, PANELES):
        barras = ax.bar(TRAMOS, vals, color=COLORES)
        ax.set_title(titulo, fontsize=11)
        ax.set_ylabel(ylab, fontsize=9.5)
        ax.set_xlabel('Tramo horario', fontsize=9.5)
        ax.tick_params(axis='x', labelsize=8.5)
        ax.grid(axis='y', alpha=0.3)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _, d=dec: es(x, min(d, 4) if d else 0)))
        ax.set_ylim(0, max(vals) * 1.18)
        for b, v in zip(barras, vals):
            ax.text(b.get_x() + b.get_width() / 2, v * 1.02, es(v, dec) + (' %' if dec == 3 else ''), ha='center', va='bottom', fontsize=8.5)
    fig.suptitle('Perfil intradiario del IPSA: 30 acciones, velas de 5 minutos, 60 días', fontsize=12)
    fig.tight_layout()
    fig.savefig(salida, dpi=170)
    print(salida)


if __name__ == '__main__':
    main()
