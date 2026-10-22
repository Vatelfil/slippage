const fs = require('fs');
const path = require('path');
const {
  Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell, WidthType,
  ShadingType, BorderStyle, ImageRun, ExternalHyperlink, PageBreak, VerticalAlign,
} = require('docx');

const NAVY = '1E2761';
const MUTED = '5A6B9C';
const ICE = 'DDE6F7';
const AMBERBG = 'FFF3D1';
const GREENBG = 'DDF1E0';
const REDBG = 'F9DAD5';
const GRID = 'B8C2DC';
const FONT = 'Calibri';
const CODE_FONT = 'Courier New';
const CONTENT_W = 9026; // A4 con margenes de 1" (DXA)

// ---------- texto con formato en linea: `codigo`, **negrita**, *cursiva* ----------
function inline(text, base = {}) {
  const out = [];
  const parts = String(text).split(/(`[^`]+`|\*\*[^*]+\*\*|\*[^*\s][^*]*\*)/g);
  for (const part of parts) {
    if (!part) continue;
    if (part.startsWith('`') && part.endsWith('`')) {
      out.push(new TextRun({ ...base, text: part.slice(1, -1), font: CODE_FONT, size: (base.size || 22) - 2 }));
    } else if (part.startsWith('**') && part.endsWith('**')) {
      out.push(new TextRun({ ...base, text: part.slice(2, -2), bold: true }));
    } else if (part.startsWith('*') && part.endsWith('*') && part.length > 2) {
      out.push(new TextRun({ ...base, text: part.slice(1, -1), italics: true }));
    } else {
      out.push(new TextRun({ ...base, text: part }));
    }
  }
  return out;
}

const H = (level, text) => new Paragraph({
  heading: [HeadingLevel.HEADING_1, HeadingLevel.HEADING_1, HeadingLevel.HEADING_2, HeadingLevel.HEADING_3, HeadingLevel.HEADING_4][level],
  children: [new TextRun({ text })],
});
const H1 = (t) => H(1, t);
const H2 = (t) => H(2, t);
const H3 = (t) => H(3, t);
const H4 = (t) => H(4, t);

const P = (text, opts = {}) => new Paragraph({
  alignment: opts.align || AlignmentType.JUSTIFIED,
  spacing: { after: opts.after ?? 120, line: 276, before: opts.before || 0 },
  keepNext: !!opts.keepNext,
  children: inline(text, opts.run || {}),
});

const B = (items, ref = 'bullet') => items.map((t) => new Paragraph({
  numbering: { reference: ref, level: 0 },
  alignment: AlignmentType.JUSTIFIED,
  spacing: { after: 60, line: 276 },
  children: inline(t),
}));

const N = (items, ref) => items.map((t) => new Paragraph({
  numbering: { reference: ref, level: 0 },
  alignment: AlignmentType.JUSTIFIED,
  spacing: { after: 60, line: 276 },
  children: inline(t),
}));

const FORMULA = (text) => new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { before: 80, after: 140 },
  children: [new TextRun({ text, font: 'Cambria Math', italics: true, size: 23 })],
});

const PB = () => new Paragraph({ children: [new PageBreak()] });

// ---------- tablas ----------
const border = { style: BorderStyle.SINGLE, size: 4, color: GRID };
const borders = { top: border, bottom: border, left: border, right: border };

function cell(content, width, o = {}) {
  const obj = (content !== null && typeof content === 'object') ? content : {};
  const lines = String(obj.t ?? (typeof content === 'string' ? content : '')).split('\n');
  const fill = obj.fill || o.fill;
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    borders,
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    shading: fill ? { fill, type: ShadingType.CLEAR, color: 'auto' } : undefined,
    children: lines.map((ln) => new Paragraph({
      alignment: obj.align || o.align || AlignmentType.LEFT,
      keepNext: !!o.keepNext,
      spacing: { after: 20 },
      children: inline(ln, { size: o.size || 19, bold: o.bold || obj.bold, color: o.color }),
    })),
  });
}

function table(headers, rows, widths, o = {}) {
  const total = widths.reduce((a, b) => a + b, 0);
  const keep = rows.length <= 9;
  const head = new TableRow({
    tableHeader: true, cantSplit: true,
    children: headers.map((h, i) => cell(h, widths[i], { fill: NAVY, bold: true, color: 'FFFFFF', size: o.size || 19, keepNext: true })),
  });
  const body = rows.map((r, ri) => new TableRow({
    cantSplit: true,
    children: r.map((c, i) => cell(c, widths[i], {
      keepNext: keep && ri < rows.length - 1,
      size: o.size || 19,
      fill: (o.zebra !== false && ri % 2 === 1) ? 'F4F6FB' : undefined,
      align: o.aligns ? o.aligns[i] : undefined,
    })),
  }));
  return new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: widths, rows: [head, ...body] });
}

const STATUS = {
  ok: { fill: GREENBG },
  mid: { fill: AMBERBG },
  pend: { fill: REDBG },
};
const chip = (text, kind) => ({ t: text, fill: STATUS[kind].fill, bold: true, align: AlignmentType.CENTER });

function callout(title, text, kind = 'mid') {
  const fill = kind === 'ok' ? GREENBG : kind === 'pend' ? REDBG : kind === 'info' ? ICE : AMBERBG;
  const kids = [];
  if (title) kids.push(new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: title, bold: true, color: NAVY, size: 22 })] }));
  for (const ln of String(text).split('\n')) {
    kids.push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, keepNext: true, spacing: { after: 60, line: 264 }, children: inline(ln, { size: 21 }) }));
  }
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [CONTENT_W],
    rows: [new TableRow({ cantSplit: true, children: [new TableCell({
      width: { size: CONTENT_W, type: WidthType.DXA },
      borders, margins: { top: 100, bottom: 100, left: 160, right: 160 },
      shading: { fill, type: ShadingType.CLEAR, color: 'auto' },
      children: kids,
    })] })],
  });
}

const GAP = () => new Paragraph({ spacing: { after: 100 }, children: [] });

// ---------- captions y figuras ----------
const counters = { tab: 0, fig: 0 };
const tabCaption = (text) => new Paragraph({
  keepNext: true, alignment: AlignmentType.LEFT, spacing: { before: 160, after: 80 },
  children: [new TextRun({ text: `Tabla II-${++counters.tab}. `, bold: true, color: NAVY, size: 20 }), new TextRun({ text, size: 20, color: NAVY })],
});
const figCaption = (text) => new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { before: 60, after: 200 },
  children: [new TextRun({ text: `Figura II-${++counters.fig}. `, bold: true, color: NAVY, size: 20 }), new TextRun({ text, size: 20, color: NAVY })],
});

function pngSize(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}
function figure(file, caption, maxW = 600, maxH = 560) {
  const { w, h } = pngSize(file);
  let W = Math.min(maxW, w);
  let Hh = Math.round(W * h / w);
  if (Hh > maxH) { Hh = maxH; W = Math.round(Hh * w / h); }
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 40 },
      children: [new ImageRun({ type: 'png', data: fs.readFileSync(file), transformation: { width: W, height: Hh },
        altText: { title: caption, description: caption, name: path.basename(file) } })] }),
    figCaption(caption),
  ];
}

module.exports = {
  NAVY, MUTED, ICE, GRID, FONT, CODE_FONT, CONTENT_W, AMBERBG, GREENBG, REDBG,
  inline, H, H1, H2, H3, H4, P, B, N, FORMULA, PB, table, cell, chip, callout, GAP,
  tabCaption, figCaption, figure, pngSize, counters,
};
