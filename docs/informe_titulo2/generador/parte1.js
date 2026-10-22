// Convierte el contenido del Titulo I (extraido a parte1.json) en elementos docx,
// SIN modificar el texto: solo se unifica el formato visual.
const {
  Paragraph, TextRun, ExternalHyperlink, AlignmentType, LevelFormat, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, VerticalAlign,
} = require('docx');
const L = require('./lib');

const FIRST = 53;   // "1. NOMBRE DEL TEMA"
const LAST = 561;   // ultima entrada de la bibliografia

function runsFor(p, base = {}) {
  const out = [];
  for (const r of p.runs) {
    if (r.x) continue;
    const opts = { ...base };
    if (r.b) opts.bold = true;
    if (r.i) opts.italics = true;
    if (r.u) opts.underline = {};
    if (r.va === 'superscript') opts.superScript = true;
    if (r.va === 'subscript') opts.subScript = true;
    const pieces = r.t.replace(/\t/g, ' ').split('\n');
    const mk = (txt, i) => new TextRun({ ...opts, text: txt, break: i > 0 ? 1 : 0 });
    if (r.link && !r.link.startsWith('#')) {
      out.push(new ExternalHyperlink({
        link: r.link,
        children: pieces.map((t, i) => new TextRun({ ...opts, text: t, break: i > 0 ? 1 : 0, color: '0563C1', underline: {} })),
      }));
    } else {
      pieces.forEach((t, i) => out.push(mk(t, i)));
    }
  }
  return out;
}

function stripBullet(runs) {
  const out = runs.map((r) => ({ ...r }));
  for (const r of out) {
    if (!r.t) continue;
    r.t = r.t.replace(/^[\s••]+/, '');
    if (r.t) break;
  }
  return out.filter((r, i) => r.t || r.x);
}
const plain = (p) => p.runs.filter((r) => !r.x).map((r) => r.t).join('');

function convert(blocks) {
  const kids = [];
  const listFmt = {}; // numId -> fmt
  let h1 = 0;

  for (let i = FIRST; i <= LAST; i++) {
    const b = blocks[i];
    if (b.k === 'tbl') { kids.push(L.GAP(), tableFrom(b), L.GAP()); continue; }
    const text = plain(b).trim();
    const st = b.style.toLowerCase();

    if (st.startsWith('heading')) {
      if (!text) continue;
      if (st === 'heading 5') { // leyendas de tabla
        kids.push(new Paragraph({ alignment: AlignmentType.LEFT, keepNext: true, spacing: { before: 160, after: 80 },
          children: [new TextRun({ text, bold: true, size: 20, color: L.NAVY })] }));
        continue;
      }
      if (st === 'heading 1' && b.num) { h1 += 1; kids.push(L.H(1, `${h1}. ${text}`)); continue; }
      if (/^\d+\.\d+\.\d+/.test(text)) { kids.push(L.H(3, text)); continue; }
      if (/^\d+\.\d+/.test(text)) { kids.push(L.H(2, text)); continue; }
      kids.push(L.H(4, text));
      continue;
    }

    if (!text) continue; // se descartan parrafos vacios (el espaciado lo da el estilo)

    if (!b.num && /^[••]\s*/.test(text)) { // vinetas escritas como texto en el original
      const rs = runsFor({ runs: stripBullet(b.runs) });
      kids.push(new Paragraph({ numbering: { reference: 'bullet', level: 0 }, alignment: AlignmentType.JUSTIFIED,
        spacing: { after: 60, line: 276 }, children: rs }));
      continue;
    }

    if (b.num) {
      const id = b.num.id;
      listFmt[id] = b.num.fmt;
      const ref = b.num.fmt === 'bullet' ? 'bullet' : (b.num.fmt === 'lowerLetter' ? `alpha_${id}` : `dec_${id}`);
      kids.push(new Paragraph({
        numbering: { reference: ref, level: 0 }, alignment: AlignmentType.JUSTIFIED,
        spacing: { after: 60, line: 276 }, children: runsFor(b),
      }));
      continue;
    }

    const align = b.jc === 'center' ? AlignmentType.CENTER : (b.jc === 'both' ? AlignmentType.JUSTIFIED : AlignmentType.LEFT);
    kids.push(new Paragraph({ alignment: align, spacing: { after: 120, line: 276 }, children: runsFor(b) }));
  }

  const numbering = [];
  for (const [id, fmt] of Object.entries(listFmt)) {
    if (fmt === 'bullet') continue;
    numbering.push({
      reference: fmt === 'lowerLetter' ? `alpha_${id}` : `dec_${id}`,
      levels: [{ level: 0, format: fmt === 'lowerLetter' ? LevelFormat.LOWER_LETTER : LevelFormat.DECIMAL,
        text: fmt === 'lowerLetter' ? '%1)' : '%1.', alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } } }],
    });
  }
  return { children: kids, numbering };
}

function tableFrom(t) {
  const nCols = Math.max(...t.rows.map((r) => r.length));
  const lens = Array(nCols).fill(6);
  t.rows.forEach((r) => r.forEach((c, ci) => {
    const len = c.map((p) => plain(p)).join(' ').length;
    lens[ci] = Math.max(lens[ci], Math.min(len, 60));
  }));
  const sum = lens.reduce((a, b) => a + b, 0);
  let widths = lens.map((l) => Math.max(900, Math.round((l / sum) * L.CONTENT_W)));
  const diff = L.CONTENT_W - widths.reduce((a, b) => a + b, 0);
  widths[widths.indexOf(Math.max(...widths))] += diff;

  const rows = t.rows.map((r0, ri) => new TableRow({
    tableHeader: ri === 0, cantSplit: true,
    children: r0.concat(Array(nCols - r0.length).fill([])).map((c, ci) => {
      const head = ri === 0;
      const paras = c.filter((p, k) => plain(p).trim() || k === 0).map((p) => new Paragraph({
        alignment: AlignmentType.LEFT, spacing: { after: 20 },
        children: runsFor(p, { size: 19, ...(head ? { bold: true, color: 'FFFFFF' } : {}) }),
      }));
      return new TableCell({
        width: { size: widths[ci], type: WidthType.DXA },
        borders: { top: { style: 'single', size: 4, color: L.GRID }, bottom: { style: 'single', size: 4, color: L.GRID },
          left: { style: 'single', size: 4, color: L.GRID }, right: { style: 'single', size: 4, color: L.GRID } },
        verticalAlign: VerticalAlign.CENTER,
        margins: { top: 60, bottom: 60, left: 100, right: 100 },
        shading: head ? { fill: L.NAVY, type: ShadingType.CLEAR, color: 'auto' } : (ri % 2 === 0 ? { fill: 'F4F6FB', type: ShadingType.CLEAR, color: 'auto' } : undefined),
        children: paras.length ? paras : [new Paragraph({ children: [] })],
      });
    }),
  }));
  // completar filas cortas
  return new Table({ width: { size: L.CONTENT_W, type: WidthType.DXA }, columnWidths: widths, rows });
}

module.exports = { convert, plain, FIRST };
