"""Arma el informe final del Título II (Word) con la estructura y el formato del Título I.

- Plantilla y capítulos 1 a 3: el Word del Título I (estilos, portada y textos del anteproyecto).
- Capítulos 4 a 9 y Anexo A: los Markdown de cada responsable en `docs/` (se convierten sin cambiar su texto,
  salvo la cabecera de metadatos: tarea, autor, versión, numeración).
- Textos nuevos (resumen, partes del capítulo 1 y 3, anexos B y C): `textos/`.

Uso:
    python docs/informe_titulo2/final/build_informe_final.py --plantilla "<Word del Título I>" --salida <archivo.docx>
"""
import argparse
import copy
import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[2]
TEXTOS = AQUI / 'textos'
PLANTILLA_DEF = r'D:/claude agente/TÍTULO I_ Coordinación de Agentes para la Mitigación del _Slippage_.docx'
VERDE_CLARO = 'E2EFDA'
GRIS_BORDE = 'A6A6A6'

# ----------------------------------------------------------------------------------------------
# LaTeX simple -> segmentos (texto, vertical) con sub/superíndices
# ----------------------------------------------------------------------------------------------
SIMBOLOS = {
    r'\times': '×', r'\cdot': '·', r'\approx': '≈', r'\to': '→', r'\rightarrow': '→', r'\implies': '⇒',
    r'\in': '∈', r'\le': '≤', r'\leq': '≤', r'\ge': '≥', r'\geq': '≥', r'\neq': '≠', r'\pm': '±',
    r'\dots': '…', r'\ldots': '…', r'\cdots': '⋯', r'\infty': '∞', r'\sum': 'Σ', r'\prod': 'Π',
    r'\partial': '∂', r'\mid': '|', r'\sim': '~', r'\propto': '∝', r'\nabla': '∇',
    r'\alpha': 'α', r'\beta': 'β', r'\gamma': 'γ', r'\delta': 'δ', r'\epsilon': 'ε', r'\varepsilon': 'ε',
    r'\theta': 'θ', r'\lambda': 'λ', r'\mu': 'μ', r'\pi': 'π', r'\rho': 'ρ', r'\sigma': 'σ', r'\tau': 'τ',
    r'\phi': 'φ', r'\varphi': 'φ', r'\psi': 'ψ', r'\omega': 'ω', r'\eta': 'η', r'\kappa': 'κ', r'\xi': 'ξ',
    r'\Delta': 'Δ', r'\Gamma': 'Γ', r'\Sigma': 'Σ', r'\Pi': 'Π', r'\Omega': 'Ω', r'\Lambda': 'Λ',
    r'\max': 'max', r'\min': 'min', r'\log': 'log', r'\ln': 'ln', r'\exp': 'exp', r'\top': 'ᵀ',
    r'\quad': '  ', r'\qquad': '    ', r'\;': ' ', r'\,': ' ', r'\:': ' ', r'\!': '', r'\ ': ' ',
    r'\%': '%', r'\_': '_', r'\{': '{', r'\}': '}', r'\#': '#', r'\&': '&',
    r'\bigl': '', r'\bigr': '', r'\Bigl': '', r'\Bigr': '', r'\left': '', r'\right': '', r'\big': '', r'\Big': '',
}
BB = {'R': 'ℝ', 'E': '𝔼', 'N': 'ℕ', 'Z': 'ℤ'}


def _grupo(s, i):
    """Devuelve (contenido, fin) del grupo {..} que empieza en s[i] == '{'."""
    prof = 0
    for j in range(i, len(s)):
        if s[j] == '{':
            prof += 1
        elif s[j] == '}':
            prof -= 1
            if prof == 0:
                return s[i + 1:j], j + 1
    return s[i + 1:], len(s)


def _comando_con_arg(s, cmd, fn):
    while True:
        k = s.find(cmd + '{')
        if k < 0:
            return s
        arg, fin = _grupo(s, k + len(cmd))
        s = s[:k] + fn(arg) + s[fin:]


def _prepro(s):
    s = s.replace('{,}', ',').replace('{.}', '.')
    for c in (r'\text', r'\mathrm', r'\operatorname', r'\textbf', r'\mathbf', r'\boldsymbol', r'\textit', r'\mathit'):
        s = _comando_con_arg(s, c, lambda a: a)
    s = _comando_con_arg(s, r'\mathbb', lambda a: BB.get(a.strip(), a))
    s = _comando_con_arg(s, r'\mathcal', lambda a: a)
    s = _comando_con_arg(s, r'\hat', lambda a: a + '\u0302')
    s = _comando_con_arg(s, r'\bar', lambda a: a + '\u0304')
    s = _comando_con_arg(s, r'\tilde', lambda a: a + '\u0303')
    s = _comando_con_arg(s, r'\sqrt', lambda a: '√(' + a + ')')

    def frac(s):
        while True:
            k = s.find(r'\frac{')
            if k < 0:
                return s
            a, f1 = _grupo(s, k + 5)
            b, f2 = _grupo(s, f1) if f1 < len(s) and s[f1] == '{' else ('', f1)
            pa = a if re.fullmatch(r'[\w.,]+', a) else '(' + a + ')'
            pb = b if re.fullmatch(r'[\w.,]+', b) else '(' + b + ')'
            s = s[:k] + pa + '/' + pb + s[f2:]
    s = frac(s)
    for k in sorted(SIMBOLOS, key=len, reverse=True):
        if re.fullmatch(r'\\[a-zA-Z]+', k):
            s = re.sub(re.escape(k) + r'(?![a-zA-Z])', lambda m, v=SIMBOLOS[k]: v, s)
        else:
            s = s.replace(k, SIMBOLOS[k])
    s = re.sub(r'\\([a-zA-Z]+)', r'\1', s)  # comando desconocido: deja el nombre
    return s


def latex_segmentos(s, vert=None):
    s = _prepro(s) if vert is None else s
    out = []
    buf = ''
    i = 0
    while i < len(s):
        c = s[i]
        if c in '^_':
            if buf:
                out.append((buf, vert)); buf = ''
            v = 'sup' if c == '^' else 'sub'
            if i + 1 < len(s) and s[i + 1] == '{':
                arg, fin = _grupo(s, i + 1)
            else:
                arg, fin = s[i + 1:i + 2], i + 2
            for t, _ in latex_segmentos(arg, vert=v):
                out.append((t, v))
            i = fin
            continue
        if c in '{}':
            i += 1
            continue
        buf += c
        i += 1
    if buf:
        out.append((buf, vert))
    return [(re.sub(r' {2,}', '  ', t), v) for t, v in out if t]


# ----------------------------------------------------------------------------------------------
# Documento
# ----------------------------------------------------------------------------------------------
class Informe:
    def __init__(self, plantilla):
        self.src = Document(plantilla)
        self.doc = Document(plantilla)
        body = self.doc.element.body
        for el in list(body):
            if el.tag != qn('w:sectPr'):
                body.remove(el)
        self.body = body
        self.n_tabla = 0
        self.n_figura = 0
        self.figuras_puestas = set()
        self.estilo_normal = next(s for s in self.doc.styles if s.name == 'normal')
        self._estilo_leyenda()
        self.src_els = list(self.src.element.body.iterchildren())

    # ---------- estilos y utilidades ----------
    def _estilo_leyenda(self):
        from docx.enum.style import WD_STYLE_TYPE
        st = self.doc.styles.add_style('Leyenda informe', WD_STYLE_TYPE.PARAGRAPH)
        st.base_style = self.estilo_normal
        st.font.size = Pt(9.5)
        st.font.italic = True
        st.font.color.rgb = RGBColor(0x40, 0x40, 0x40)
        st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        st.paragraph_format.space_before = Pt(4)
        st.paragraph_format.space_after = Pt(10)

    def p(self, texto='', estilo=None, align=None, **kw):
        par = self.doc.add_paragraph(style=estilo or self.estilo_normal)
        if texto:
            self.inline(par, texto, **kw)
        if align is not None:
            par.alignment = align
        return par

    def h(self, texto, nivel, salto=False):
        if salto:
            self.salto_pagina()
        par = self.doc.add_paragraph(style=f'Heading {nivel}')
        self.inline(par, texto)
        return par

    def salto_pagina(self):
        par = self.doc.add_paragraph(style=self.estilo_normal)
        par.add_run().add_break(WD_BREAK.PAGE)

    def run(self, par, texto, bold=False, italic=False, code=False, vert=None, size=None, color=None):
        r = par.add_run(texto)
        if bold:
            r.bold = True
        if italic:
            r.italic = True
        if code:
            r.font.name = 'Consolas'
            r.font.size = Pt(9)
        if vert == 'sup':
            r.font.superscript = True
        elif vert == 'sub':
            r.font.subscript = True
        if size:
            r.font.size = Pt(size)
        if color:
            r.font.color.rgb = RGBColor.from_string(color)
        return r

    def inline(self, par, texto, size=None, bold=False, italic=False, color=None):
        """Markdown en línea: **negrita**, *cursiva*, `código`, $matemática$, [texto](url)."""
        texto = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1', texto)
        i, buf = 0, ''
        b, it = bold, italic
        tachado = False

        def flush():
            nonlocal buf
            if buf:
                r = self.run(par, buf, bold=b, italic=it, size=size, color=color)
                if tachado:
                    r.font.strike = True
                buf = ''
        while i < len(texto):
            if texto.startswith('`', i):
                j = texto.find('`', i + 1)
                if j > i:
                    flush()
                    contenido = texto[i + 1:j]
                    ref = self.ref_figura(contenido)
                    if ref:
                        self.run(par, ref, bold=b, italic=it, size=size, color=color)
                    else:
                        self.run(par, contenido, bold=b, italic=it, code=True, color=color)
                    i = j + 1
                    continue
            if texto.startswith('$', i) and not texto.startswith('$$', i):
                j = texto.find('$', i + 1)
                if j > i + 1:
                    flush()
                    for t, v in latex_segmentos(texto[i + 1:j]):
                        self.run(par, t, bold=b, italic=it, vert=v, size=size, color=color)
                    i = j + 1
                    continue
            if texto.startswith('**', i):
                flush(); b = not b; i += 2
                continue
            if texto.startswith('~~', i):
                flush(); tachado = not tachado; i += 2
                continue
            if texto[i] == '*' and (it or (i + 1 < len(texto) and texto[i + 1] not in ' *' and texto.find('*', i + 1) > 0)):
                flush(); it = not it; i += 1
                continue
            buf += texto[i]
            i += 1
        flush()

    def campo(self, par, instr, resultado=''):
        def fld(t):
            e = OxmlElement('w:fldChar'); e.set(qn('w:fldCharType'), t); return e
        r1 = par.add_run(); r1._r.append(fld('begin'))
        r2 = par.add_run(); it = OxmlElement('w:instrText'); it.set(qn('xml:space'), 'preserve'); it.text = f' {instr} '; r2._r.append(it)
        r3 = par.add_run(); r3._r.append(fld('separate'))
        par.add_run(resultado)
        r5 = par.add_run(); r5._r.append(fld('end'))

    def leyenda(self, tipo, texto):
        if tipo == 'Tabla':
            self.n_tabla += 1; n = self.n_tabla
        else:
            self.n_figura += 1; n = self.n_figura
        par = self.doc.add_paragraph(style='Leyenda informe')
        self.run(par, f'{tipo} ', bold=True)
        r = par.runs[-1]
        self.campo(par, f'SEQ {tipo} \\* ARABIC', str(n))
        for rr in par.runs[1:]:
            rr.bold = True
        self.run(par, ': ', bold=True)
        self.inline(par, texto.strip().rstrip('.') + '.')
        if tipo == 'Tabla':
            par.paragraph_format.keep_with_next = True
        return n

    # ---------- figuras ----------
    def resolver_png(self, ruta):
        ruta = ruta.strip().strip('`')
        cands = [ROOT / ruta, ROOT / 'data/analysis/cap7' / ruta, ROOT / 'data/analysis/capitulo7_BF' / ruta]
        return next((c for c in cands if c.exists() and c.suffix == '.png'), None)

    def ref_figura(self, contenido):
        if not contenido.endswith('.png'):
            return None
        f = self.resolver_png(contenido)
        if f is None:
            return None
        if f in self.figuras_puestas:
            return None
        return None

    def figura(self, ruta, leyenda, ancho_cm=15.5):
        f = self.resolver_png(str(ruta)) if not isinstance(ruta, Path) else ruta
        if f is None or f in self.figuras_puestas:
            return False
        par = self.doc.add_paragraph(style=self.estilo_normal)
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        par.paragraph_format.keep_with_next = True
        par.add_run().add_picture(str(f), width=Cm(ancho_cm))
        self.leyenda('Figura', leyenda)
        self.figuras_puestas.add(f)
        return True

    # ---------- tablas ----------
    def _bordes(self, tabla):
        tblPr = tabla._tbl.tblPr
        b = OxmlElement('w:tblBorders')
        for lado in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
            e = OxmlElement(f'w:{lado}')
            e.set(qn('w:val'), 'single'); e.set(qn('w:sz'), '4'); e.set(qn('w:space'), '0'); e.set(qn('w:color'), GRIS_BORDE)
            b.append(e)
        tblPr.append(b)

    def _sombra(self, celda, color):
        tcPr = celda._tc.get_or_add_tcPr()
        sh = OxmlElement('w:shd'); sh.set(qn('w:val'), 'clear'); sh.set(qn('w:color'), 'auto'); sh.set(qn('w:fill'), color)
        tcPr.append(sh)

    def tabla(self, encabezado, filas, leyenda):
        self.leyenda('Tabla', leyenda)
        ncol = len(encabezado)
        t = self.doc.add_table(rows=1 + len(filas), cols=ncol)
        self._bordes(t)
        for ri, fila in enumerate([encabezado] + filas):
            fila = (fila + [''] * ncol)[:ncol]
            for ci, txt in enumerate(fila):
                c = t.cell(ri, ci)
                par = c.paragraphs[0]
                par.style = self.estilo_normal
                par.paragraph_format.space_after = Pt(1)
                par.paragraph_format.space_before = Pt(1)
                self.inline(par, txt.strip(), size=8.5, bold=(ri == 0))
                if ri == 0:
                    self._sombra(c, VERDE_CLARO)
        # fila de encabezado se repite en cada página
        trPr = t.rows[0]._tr.get_or_add_trPr()
        e = OxmlElement('w:tblHeader'); e.set(qn('w:val'), 'true'); trPr.append(e)
        self.p('')
        return t

    # ---------- copiar del Título I ----------
    def _txt(self, el):
        return ''.join(t.text or '' for t in el.iter(qn('w:t'))).strip()

    def _estilo(self, el):
        ps = el.find(qn('w:pPr') + '/' + qn('w:pStyle'))
        if ps is None:
            return ''
        sid = ps.get(qn('w:val'))
        for s in self.src.styles:
            if s.style_id == sid:
                return s.name or ''
        return sid

    def _es_titulo(self, el):
        return el.tag == qn('w:p') and self._estilo(el).startswith('Heading')

    def rango(self, inicio, fin=None, incluir_titulos=True):
        """Elementos del Título I después del título que empieza con `inicio` y antes del siguiente título
        de nivel igual o superior (o del que empieza con `fin`)."""
        out, dentro, nivel = [], False, None
        for el in self.src_els:
            if el.tag == qn('w:sectPr'):
                continue
            esT = self._es_titulo(el)
            txt = self._txt(el)
            if not dentro:
                if esT and txt.startswith(inicio):
                    dentro = True
                    nivel = int(re.sub(r'\D', '', self._estilo(el)) or 9)
                continue
            if esT:
                niv = int(re.sub(r'\D', '', self._estilo(el)) or 9)
                if (fin and txt.startswith(fin)) or (not fin and niv <= nivel):
                    break
                if not incluir_titulos:
                    continue
            out.append(el)
        if not dentro:
            raise ValueError(f'No encontré en el Título I: {inicio}')
        return out

    def copiar(self, elementos, leyendas_tablas=(), saltar=()):
        ley = list(leyendas_tablas)
        for el in elementos:
            txt = self._txt(el)
            if el.tag == qn('w:p'):
                if re.match(r'^Tabla [\d.]+:', txt) or any(txt.startswith(s) for s in saltar):
                    continue
                if not txt and not el.findall('.//' + qn('w:drawing')):
                    continue
                nuevo = copy.deepcopy(el)
                if self._es_titulo(el):
                    # los títulos copiados pasan a nivel 3 dentro de la nueva estructura
                    ps = nuevo.find(qn('w:pPr') + '/' + qn('w:pStyle'))
                    h3 = self.doc.styles['Heading 3'].style_id
                    ps.set(qn('w:val'), h3)
                self.body.insert(len(self.body) - 1, nuevo)
            elif el.tag == qn('w:tbl'):
                self.leyenda('Tabla', ley.pop(0) if ley else 'Tabla del Título I')
                self.body.insert(len(self.body) - 1, copy.deepcopy(el))
                self.p('')

    # ---------- Markdown ----------
    def markdown(self, texto, figuras_extra=None, leyendas_fig=None, prefijo_titulos=None, nivel_base=0, titulo_inicial=''):
        figuras_extra = figuras_extra or {}
        leyendas_fig = leyendas_fig or {}
        lineas = texto.replace('\r\n', '\n').split('\n')
        bloques = parse_md(lineas)
        titulo_actual = titulo_inicial
        pendientes = []  # figuras extra a poner al cerrar la sección
        ley_tabla = None
        nivel_actual = 9

        def cerrar_seccion(nuevo_nivel):
            nonlocal pendientes
            restantes = []
            for niv, ruta, ley in pendientes:
                if nuevo_nivel <= niv:
                    self.figura(ruta, ley)
                else:
                    restantes.append((niv, ruta, ley))
            pendientes = restantes

        contador_lista = {}
        for bl in bloques:
            tipo = bl[0]
            if tipo != 'li':
                contador_lista = {}
            if tipo == 'h':
                _, niv, txt = bl
                cerrar_seccion(niv)
                if prefijo_titulos:
                    txt = prefijo_titulos(txt)
                self.h(txt, min(niv + nivel_base, 4))
                titulo_actual = re.sub(r'^[\dA-Z.]+\s+', '', txt)
                for clave, figs in figuras_extra.items():
                    if txt.startswith(clave):
                        for ruta, ley in figs:
                            pendientes.append((niv, ruta, ley))
                continue
            if tipo == 'p':
                txt = bl[1]
                m = re.match(r'^\*\*Tabla [\d.]+\.\*\*\s*(.*)$', txt)
                if m:
                    ley_tabla = re.sub(r'\s*\(`(tab|fig):[^`]*`\)', '', m.group(1))
                    continue
                pngs = re.findall(r'`([^`]+\.png)`', txt)
                if pngs and re.match(r'^(\*\*)?Figura[^`]*', txt) and not re.match(r'^En la Figura|^La Figura', txt):
                    ley = re.sub(r'^(\*\*)?Figura[^:*]*[:.]?(\*\*)?\s*', '', txt)
                    ley = re.sub(r'\(?`[^`]*`(,\s*`[^`]*`)*\)?[.,]?', '', ley).strip(' :.-')
                    ley = ley.strip('() ') or titulo_actual
                    for ruta in pngs:
                        self.figura(ruta, leyendas_fig.get(ruta, ley))
                    continue
                self.p(txt)
                for ruta in pngs:
                    self.figura(ruta, leyendas_fig.get(ruta, titulo_actual))
                continue
            if tipo == 'li':
                _, niv, orden, txt = bl
                for k in list(contador_lista):
                    if k > niv:
                        del contador_lista[k]
                contador_lista[niv] = contador_lista.get(niv, 0) + 1
                marca = f'{contador_lista[niv]}.' if orden else ('•' if niv == 0 else '–')
                par = self.doc.add_paragraph(style=self.estilo_normal)
                pf = par.paragraph_format
                pf.left_indent = Cm(0.75 * (niv + 1))
                pf.first_line_indent = Cm(-0.5)
                pf.space_after = Pt(2)
                self.run(par, marca + '\u00a0')
                self.inline(par, txt)
                pngs = re.findall(r'`([^`]+\.png)`', txt)
                for ruta in pngs:
                    self.figura(ruta, leyendas_fig.get(ruta, titulo_actual))
                continue
            if tipo == 'table':
                _, enc, filas = bl
                self.tabla(enc, filas, ley_tabla or titulo_actual)
                ley_tabla = None
                continue
            if tipo == 'quote':
                par = self.p(bl[1], italic=False)
                par.paragraph_format.left_indent = Cm(0.8)
                par.paragraph_format.right_indent = Cm(0.4)
                self._borde_izq(par)
                continue
            if tipo == 'math':
                par = self.doc.add_paragraph(style=self.estilo_normal)
                par.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for t, v in latex_segmentos(bl[1].strip()):
                    self.run(par, t, vert=v)
                continue
            if tipo == 'code':
                _, lang, txt = bl
                if lang == 'mermaid':
                    png = diagrama_mermaid(txt, AQUI / 'build_tmp')
                    if png:
                        self.figura(png, 'Flujo de coordinación entre el Agente Maestro, el protocolo, el Ejecutor del tramo y el mercado simulado', 15.5)
                    continue
                for linea in txt.split('\n'):
                    par = self.doc.add_paragraph(style=self.estilo_normal)
                    par.paragraph_format.space_after = Pt(0)
                    par.paragraph_format.left_indent = Cm(0.5)
                    self.run(par, linea, code=True)
                self.p('')
        cerrar_seccion(0)

    def _borde_izq(self, par):
        pPr = par._p.get_or_add_pPr()
        bdr = OxmlElement('w:pBdr')
        l = OxmlElement('w:left'); l.set(qn('w:val'), 'single'); l.set(qn('w:sz'), '12'); l.set(qn('w:space'), '8'); l.set(qn('w:color'), '70AD47')
        bdr.append(l); pPr.append(bdr)


def parse_md(lineas):
    bloques, i = [], 0
    par = []

    def cerrar_par():
        nonlocal par
        if par:
            bloques.append(('p', ' '.join(s.strip() for s in par)))
            par = []
    while i < len(lineas):
        l = lineas[i]
        s = l.strip()
        if not s:
            cerrar_par(); i += 1; continue
        if s.startswith('```'):
            cerrar_par()
            lang = s[3:].strip()
            j = i + 1; cod = []
            while j < len(lineas) and not lineas[j].strip().startswith('```'):
                cod.append(lineas[j]); j += 1
            bloques.append(('code', lang, '\n'.join(cod)))
            i = j + 1; continue
        if s.startswith('$$'):
            cerrar_par()
            if s.endswith('$$') and len(s) > 4:
                bloques.append(('math', s[2:-2])); i += 1; continue
            j = i + 1; m = [s[2:]]
            while j < len(lineas) and '$$' not in lineas[j]:
                m.append(lineas[j]); j += 1
            if j < len(lineas):
                m.append(lineas[j].replace('$$', ''))
            bloques.append(('math', ' '.join(m))); i = j + 1; continue
        if re.match(r'^#{1,6}\s', s):
            cerrar_par()
            niv = len(s) - len(s.lstrip('#'))
            bloques.append(('h', niv, s.lstrip('#').strip())); i += 1; continue
        if re.match(r'^(-{3,}|\*{3,}|_{3,})$', s):
            cerrar_par(); i += 1; continue
        if s.startswith('|') and i + 1 < len(lineas) and re.match(r'^\s*\|?\s*:?-{2,}', lineas[i + 1]):
            cerrar_par()
            enc = split_fila(s)
            j = i + 2; filas = []
            while j < len(lineas) and lineas[j].strip().startswith('|'):
                filas.append(split_fila(lineas[j].strip())); j += 1
            bloques.append(('table', enc, filas)); i = j; continue
        if s.startswith('>'):
            cerrar_par()
            q = []
            while i < len(lineas) and lineas[i].strip().startswith('>'):
                q.append(lineas[i].strip()[1:].strip()); i += 1
            bloques.append(('quote', ' '.join(q))); continue
        m = re.match(r'^(\s*)([-*+]|\d+[.)])\s+(.*)$', l)
        if m:
            cerrar_par()
            sangria = len(m.group(1).replace('\t', '    '))
            niv = min(sangria // 2, 3)
            orden = m.group(2)[0].isdigit()
            txt = [m.group(3)]
            j = i + 1
            while j < len(lineas):
                lj = lineas[j]
                if not lj.strip():
                    break
                if re.match(r'^\s*([-*+]|\d+[.)])\s+', lj) or lj.strip().startswith(('|', '#', '>', '```', '$$')):
                    break
                if len(lj) - len(lj.lstrip()) == 0 and not lj.startswith(' '):
                    break
                txt.append(lj.strip()); j += 1
            bloques.append(('li', niv, orden, ' '.join(txt))); i = j; continue
        par.append(l); i += 1
    cerrar_par()
    return bloques


def split_fila(s):
    s = s.strip()
    if s.startswith('|'):
        s = s[1:]
    if s.endswith('|'):
        s = s[:-1]
    celdas, buf, en_math, en_code = [], '', False, False
    for ch in s:
        if ch == '`':
            en_code = not en_code
        if ch == '$' and not en_code:
            en_math = not en_math
        if ch == '|' and not en_math and not en_code:
            celdas.append(buf); buf = ''
        else:
            buf += ch
    celdas.append(buf)
    return [c.strip() for c in celdas]


def diagrama_mermaid(txt, carpeta):
    """Dibuja un flowchart LR de Mermaid simple (nodos en orden de aparición, flechas con etiqueta)."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch
    nodos, orden, aristas = {}, [], []
    for linea in txt.split('\n'):
        for m in re.finditer(r'(\w+)\["([^"]+)"\]', linea):
            if m.group(1) not in nodos:
                nodos[m.group(1)] = m.group(2).replace('\\n', '\n'); orden.append(m.group(1))
        m = re.match(r'\s*(\w+)(?:\[[^\]]*\])?\s*-->\|"([^"]*)"\|\s*(\w+)', linea)
        if m:
            aristas.append((m.group(1), m.group(3), m.group(2)))
    if len(orden) < 2:
        return None
    carpeta.mkdir(exist_ok=True)
    fig, ax = plt.subplots(figsize=(10.5, 4.6))
    ax.set_xlim(0, 4 * len(orden)); ax.set_ylim(0, 6); ax.axis('off')
    pos = {n: (2 + 4 * k, 3) for k, n in enumerate(orden)}
    for n, (x, y) in pos.items():
        ax.add_patch(FancyBboxPatch((x - 1.8, y - 0.95), 3.6, 1.9, boxstyle='round,pad=0.05,rounding_size=0.15',
                                    fc='#E2EFDA', ec='#548235', lw=1.5))
        ax.text(x, y, nodos[n], ha='center', va='center', fontsize=10.5)
    for a, b, et in aristas:
        (xa, _), (xb, _) = pos[a], pos[b]
        ida = xb > xa
        y = 4.15 if ida else 1.85
        x1, x2 = (xa + 0.9, xb - 0.9) if ida else (xa - 0.9, xb + 0.9)
        ax.annotate('', xy=(x2, y), xytext=(x1, y), arrowprops=dict(arrowstyle='-|>', color='#385723' if ida else '#7F7F7F', lw=1.4))
        ax.text((x1 + x2) / 2, y + (0.45 if ida else -0.45), et.replace('\\n', '\n'), ha='center', va='center', fontsize=9,
                color='#385723' if ida else '#595959')
    out = carpeta / 'diagrama_mermaid_cap4.png'
    fig.tight_layout(); fig.savefig(out, dpi=170); plt.close(fig)
    return out


def limpiar_md(texto):
    """Quita la cabecera de metadatos (entre el título y la primera línea ---), salvo el bloque «Convención»."""
    lineas = texto.replace('\r\n', '\n').split('\n')
    if lineas and lineas[0].startswith('# '):
        lineas = lineas[1:]
    try:
        k = next(i for i, l in enumerate(lineas[:40]) if l.strip() == '---')
    except StopIteration:
        k = -1
    cab, resto = (lineas[:k], lineas[k + 1:]) if k >= 0 else ([], lineas)
    conservar, dentro = [], False
    for l in cab:
        if l.startswith('**Convención'):
            dentro = True
        elif l.startswith('**') and dentro:
            dentro = False
        if dentro:
            conservar.append(l)
    resto = [l for l in resto if not l.startswith('Elaborado por')]
    return '\n'.join(conservar + [''] + resto)


def leer(p):
    return Path(p).read_text(encoding='utf-8')


# ----------------------------------------------------------------------------------------------
def construir(plantilla, salida, fecha):
    I = Informe(plantilla)
    d = I.doc

    # ---------------- PORTADA ----------------
    logo = AQUI / 'recursos/logo.png'
    par = I.p(align=WD_ALIGN_PARAGRAPH.CENTER)
    par.add_run().add_picture(str(logo), width=Cm(9))
    I.p('Facultad de Ingeniería', align=WD_ALIGN_PARAGRAPH.CENTER)
    I.p('Escuela de Informática y Computación', align=WD_ALIGN_PARAGRAPH.CENTER)
    for _ in range(3):
        I.p('')
    t = d.add_paragraph('INFORME FINAL', style='Title'); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    t = d.add_paragraph('TRABAJO DE TÍTULO II', style='Title'); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    I.p('')
    tema = I._txt(I.rango('NOMBRE DEL TEMA')[0]).strip('"“”. ')
    I.p(tema, align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size=13)
    for _ in range(3):
        I.p('')
    portada = d.add_table(rows=3, cols=2)
    datos = [('PROFESORA GUÍA', 'ESTUDIANTES'),
             ('Ana Rosa Moya Beltrán', 'Paolo Sepúlveda Parraguez\nMauricio Reynoso Ruiz\nBenjamín Farias'),
             ('amoya@utem.cl', 'psepulvedap@utem.cl\nmreynoso@utem.cl\nbfarias@utem.cl')]
    for ri, fila in enumerate(datos):
        for ci, txt in enumerate(fila):
            c = portada.cell(ri, ci)
            c.paragraphs[0].style = I.estilo_normal
            for k, linea in enumerate(txt.split('\n')):
                pp = c.paragraphs[0] if k == 0 else c.add_paragraph(style=I.estilo_normal)
                I.run(pp, linea, bold=(ri == 0))
    I.p('')
    I.p(f'Santiago, {fecha}', align=WD_ALIGN_PARAGRAPH.CENTER)
    I.p('Borrador para revisión del equipo', align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, color='7F7F7F')

    # ---------------- ÍNDICES ----------------
    I.salto_pagina()
    d.add_paragraph('Índice', style='Subtitle')
    I.campo(I.p(), 'TOC \\o "1-3" \\h \\z \\u', 'Clic derecho sobre este texto y «Actualizar campo» para generar el índice.')
    I.salto_pagina()
    d.add_paragraph('Índice de tablas', style='Subtitle')
    I.campo(I.p(), 'TOC \\h \\z \\c "Tabla"', 'Clic derecho y «Actualizar campo».')
    d.add_paragraph('Índice de figuras', style='Subtitle')
    I.campo(I.p(), 'TOC \\h \\z \\c "Figura"', 'Clic derecho y «Actualizar campo».')

    # ---------------- PRELIMINARES ----------------
    I.h('NOMBRE DEL TEMA', 1, salto=True)
    I.copiar(I.rango('NOMBRE DEL TEMA'))
    I.h('RESUMEN', 1)
    I.markdown(leer(TEXTOS / 'resumen.md'))
    I.h('PALABRAS CLAVE', 1)
    I.copiar(I.rango('PALABRAS CLAVE'))

    # ---------------- CAPÍTULO 1 ----------------
    I.h('CAPÍTULO 1: INTRODUCCIÓN', 1, salto=True)
    I.h('1.1 Contexto y motivación', 2)
    I.markdown(leer(TEXTOS / 'cap1_contexto.md'))
    I.h('1.2 Objetivos', 2)
    I.h('1.2.1 Objetivo general', 3)
    I.copiar(I.rango('5.1 OBJETIVO GENERAL'))
    I.h('1.2.2 Objetivos específicos', 3)
    I.copiar(I.rango('5.2 OBJETIVOS ESPEC'))
    I.h('1.3 Alcances', 2)
    I.copiar(I.rango('6.1 ALCANCES'))
    I.h('1.4 Limitaciones', 2)
    I.copiar(I.rango('6.2 LIMITACIONES'))
    I.p('Los cambios respecto de lo planificado en el Título I están registrados en el Anexo A (desviaciones).')
    I.h('1.5 Metodología de trabajo', 2)
    I.markdown(leer(TEXTOS / 'cap1_metodologia.md'))
    I.h('1.6 Estructura del informe', 2)
    I.p('El informe sigue la estructura de nueve capítulos definida en el Título I:')
    I.copiar(I.rango('ESTRUCTURA INFORME FINAL'), saltar=('El informe final del proyecto se organizará',))

    # ---------------- CAPÍTULO 2 ----------------
    I.h('CAPÍTULO 2: MARCO TEÓRICO Y ESTADO DEL ARTE', 1, salto=True)
    I.h('2.1 El mercado accionario chileno y el índice IPSA', 2)
    I.copiar(I.rango('4.1.1'))
    I.h('2.2 El libro de órdenes (Limit Order Book, LOB)', 2)
    I.copiar(I.rango('4.1.2'), leyendas_tablas=['Estructura simplificada de un libro de órdenes (LOB) para una acción del IPSA. Elaboración propia'])
    I.h('2.3 El slippage y el implementation shortfall', 2)
    I.copiar(I.rango('4.1.3'))
    I.h('2.4 Estrategias tradicionales de ejecución y sus limitaciones', 2)
    I.copiar(I.rango('4.1.4'), leyendas_tablas=['Comparación de las principales estrategias tradicionales de ejecución algorítmica. Elaboración propia basada en Almgren y Chriss (2001) y Kato (2016)'])
    I.h('2.5 Aprendizaje por refuerzo multiagente aplicado a la ejecución', 2)
    I.copiar(I.rango('4.2 Descripción', fin='4.2.1'))
    I.h('2.6 Proximal Policy Optimization (PPO)', 2)
    I.copiar(I.rango('4.2.3'), leyendas_tablas=['Parámetros del algoritmo PPO y su relevancia para el entrenamiento en el mercado IPSA. Elaboración propia'])
    I.h('2.7 Simulación de mercados y datos sintéticos', 2)
    I.copiar(I.rango('4.3.3'))

    # ---------------- CAPÍTULO 3 ----------------
    I.h('CAPÍTULO 3: DEFINICIÓN DEL PROBLEMA Y ANÁLISIS DEL ENTORNO', 1, salto=True)
    I.h('3.1 El problema de ejecución de meta-órdenes en el IPSA', 2)
    I.markdown(leer(TEXTOS / 'cap3_problema.md'))
    I.h('3.2 Requerimientos de datos del sistema', 2)
    I.copiar(I.rango('4.3 Datos de Entrenamiento', fin='4.3.1'))
    I.copiar(I.rango('4.3.1'))
    I.h('3.3 Fuentes de datos evaluadas', 2)
    I.copiar(I.rango('4.3.2'))
    I.markdown(leer(TEXTOS / 'cap3_datos.md'))
    I.h('3.6 Plan de adquisición y uso de datos', 2)
    I.copiar(I.rango('4.3.4'), leyendas_tablas=['Plan de adquisición y uso de datos por prioridad y agente (Título I). Elaboración propia'])
    I.h('3.7 Criterios de validación del simulador', 2)
    I.copiar(I.rango('4.3.5'))
    I.p('Los resultados de esta validación y de la calibración de los simuladores están en los capítulos 5 y 6.')

    # ---------------- CAPÍTULOS 4 A 9 ----------------
    met = limpiar_md(leer(ROOT / 'docs/capitulo5_metodologia_MR.md'))
    parte1, parte2 = re.split(r'^# Parte II.*$', met, maxsplit=1, flags=re.M)
    parte1 = re.sub(r'^# Parte I .*$', '', parte1, flags=re.M)
    I.h('CAPÍTULO 4: DISEÑO DE LA SOLUCIÓN', 1, salto=True)
    I.markdown(parte1)
    I.h('CAPÍTULO 5: IMPLEMENTACIÓN DEL SISTEMA', 1, salto=True)
    I.markdown(parte2)

    I.h('CAPÍTULO 6: ENTRENAMIENTO Y EXPERIMENTACIÓN', 1, salto=True)
    cap6 = limpiar_md(leer(ROOT / 'docs/capitulo6_entrenamiento_experimentacion_MR.md'))
    ley6 = dict(re.findall(r'^\d+\.\s+`([^`]+\.png)`:\s*(.+)$', cap6, flags=re.M))
    I.markdown(cap6, leyendas_fig=ley6)

    I.h('CAPÍTULO 7: RESULTADOS Y EVALUACIÓN', 1, salto=True)
    I.markdown(limpiar_md(leer(ROOT / 'docs/capitulo7_resultados_BF.md')))

    I.h('CAPÍTULO 8: DISCUSIÓN Y ANÁLISIS CRÍTICO', 1, salto=True)
    extra8 = {
        '8.2.3': [('data/analysis/3_2_3/qq_diferencias.png', 'Gráfico Q-Q de las 90 diferencias sistema − TWAP frente a la distribución normal')],
        '8.3.1': [('data/analysis/figuras_4_1_4/histograma_diferencias_90.png', 'Distribución de las 90 diferencias sistema − TWAP, con la prueba de Wilcoxon y la de Shapiro-Wilk'),
                  ('data/analysis/3_2_3/bosque_diferencias.png', 'Diferencia media sistema − TWAP y sistema − VWAP con IC 95 % por grupo')],
        '8.3.2': [('data/analysis/3_2_3/diferencias_por_escenario.png', 'Diferencias sistema − TWAP por profundidad del market maker (n = 30 por profundidad)')],
        '8.4.2': [('data/analysis/figuras_4_1_4/costo_por_estrategia_varianzas.png', 'Costo por estrategia y prueba de varianzas pareadas de Pitman-Morgan (n = 90)')],
        '8.5.2': [('data/colab_resultados/control_reglas/media/analisis/control_reglas.png', 'Aporte de cada nivel en el control con reglas fijas (profundidad ×1, n = 30)')],
    }
    ley8 = {'diferencia_por_tramo.png': 'Diferencia sistema − TWAP por tramo de inicio de la orden, 90 corridas (Kruskal-Wallis y Wilcoxon con Holm)'}
    I.markdown(limpiar_md(leer(ROOT / 'docs/capitulo8_analisis_PS.md')), figuras_extra=extra8, leyendas_fig=ley8)

    I.h('CAPÍTULO 9: CONCLUSIONES Y TRABAJO FUTURO', 1, salto=True)
    I.markdown(limpiar_md(leer(ROOT / 'docs/capitulo9_conclusiones_PS.md')))

    # ---------------- BIBLIOGRAFÍA ----------------
    I.h('BIBLIOGRAFÍA', 1, salto=True)
    vistos, biblio = set(), []
    for el in I.rango('BIBLIOGRAF', fin='AVANCES'):
        txt = I._txt(el)
        if txt in vistos:
            continue
        vistos.add(txt); biblio.append(el)
    I.copiar(biblio)
    I.markdown(leer(TEXTOS / 'bibliografia_adicional.md'))

    # ---------------- ANEXOS ----------------
    I.h('ANEXO A: DESVIACIONES RESPECTO DEL TÍTULO I', 1, salto=True)
    I.p('Registro oficial de las diferencias entre lo especificado en el Título I y lo implementado, mantenido por el equipo durante el desarrollo (`DESVIACIONES_TITULO1_VS_IMPLEMENTACION.md`).')

    def pref_anexo(t):
        return re.sub(r'^(\d+)(\.\d+)*\.?\s', lambda m: 'A.' + m.group(0).rstrip('. ') + ' ', t)
    I.markdown(limpiar_md(leer(ROOT / 'DESVIACIONES_TITULO1_VS_IMPLEMENTACION.md')), prefijo_titulos=pref_anexo)
    I.h('ANEXO B: RESPONSABLES Y CONTRIBUCIONES', 1, salto=True)
    I.markdown(leer(TEXTOS / 'anexo_b.md'), titulo_inicial='Responsables por capítulo')
    I.h('ANEXO C: REPOSITORIO Y REPRODUCIBILIDAD', 1, salto=True)
    I.markdown(leer(TEXTOS / 'anexo_c.md'), titulo_inicial='Ubicación de los componentes en el repositorio')

    # ---------------- pie de página con número y actualización de campos ----------------
    sec = d.sections[0]
    pie = sec.footer.paragraphs[0] if sec.footer.paragraphs else sec.footer.add_paragraph()
    pie.alignment = WD_ALIGN_PARAGRAPH.CENTER
    I.campo(pie, 'PAGE', '1')
    settings = d.settings.element
    uf = OxmlElement('w:updateFields'); uf.set(qn('w:val'), 'true'); settings.append(uf)
    for tag in ('w:embedTrueTypeFonts', 'w:saveSubsetFonts', 'w:embedSystemFonts'):
        for e in settings.findall(qn(tag)):
            settings.remove(e)  # sin fuentes incrustadas: el archivo queda liviano

    salida = Path(salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    d.save(salida)
    print(f'OK: {salida} | tablas {I.n_tabla} | figuras {I.n_figura}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--plantilla', default=PLANTILLA_DEF)
    ap.add_argument('--salida', default=str(ROOT / 'docs/informe_titulo2/Informe_Final_Titulo_II_borrador.docx'))
    ap.add_argument('--fecha', default='noviembre de 2026')
    a = ap.parse_args()
    construir(a.plantilla, a.salida, a.fecha)
