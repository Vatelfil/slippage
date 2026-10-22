const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, AlignmentType, LevelFormat, HeadingLevel, ImageRun, Header, Footer,
  PageNumber, TableOfContents, PageBreak, Table, TableRow, TableCell, WidthType, BorderStyle, ShadingType,
  StyleLevel, SectionType,
} = require('docx');
const L = require('./lib');
const P1 = require('./parte1');
const parte2a = require('./parte2a');
const parte2b = require('./parte2b');
const anexos = require('./anexos');

const blocks = JSON.parse(fs.readFileSync(path.join(__dirname, 'parte1.json'), 'utf8'));
const OUT = process.argv[2] || path.join(__dirname, 'Informe_Titulo_II_Avance.docx');
const FECHA = '22 de octubre de 2026 (cierre del sprint 4)';

const nb = (o) => ({ style: BorderStyle.NONE, size: 0, color: 'FFFFFF' });
const noBorders = { top: nb(), bottom: nb(), left: nb(), right: nb() };

// ---------------- PORTADA ----------------
const logo = fs.readFileSync(path.join(__dirname, 'logo.png'));
const projectTitle = P1.plain(blocks[54]).trim().replace(/^["“”]+/, '').replace(/["“”.\s]+$/, '');

function coverCell(lines, w) {
  return new TableCell({
    width: { size: w, type: WidthType.DXA }, borders: noBorders,
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: lines.map(([t, o = {}]) => new Paragraph({ spacing: { after: 40 }, children: [new TextRun({ text: t, size: 21, ...o })] })),
  });
}
const teamTable = new Table({
  width: { size: L.CONTENT_W, type: WidthType.DXA }, columnWidths: [4300, 4726],
  rows: [new TableRow({ children: [
    coverCell([['PROFESORA GUÍA', { bold: true, color: L.NAVY }], ['Ana Rosa Moya Beltrán']], 4300),
    coverCell([['ESTUDIANTES', { bold: true, color: L.NAVY }], ['Paolo Sepúlveda Parraguez'], ['Mauricio Reynoso Ruiz'], ['Benjamín Farias'], ['psepulvedap@utem.cl · mreynoso@utem.cl · bfarias@utem.cl', { color: L.MUTED, size: 18 }]], 4726),
  ] })],
});

const cover = [
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 200, after: 300 }, children: [
    new ImageRun({ type: 'png', data: logo, transformation: { width: 360, height: Math.round(360 * 297 / 1295) },
      altText: { title: 'Logo UTEM', description: 'Logo de la Universidad Tecnológica Metropolitana', name: 'logo' } })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 40 }, children: [new TextRun({ text: 'Facultad de Ingeniería', size: 24 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 900 }, children: [new TextRun({ text: 'Escuela de Informática y Computación', size: 24 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 }, children: [new TextRun({ text: 'INFORME DE DESARROLLO', bold: true, size: 44, color: L.NAVY })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 500 }, children: [new TextRun({ text: 'TRABAJO DE TÍTULO II', bold: true, size: 32, color: L.MUTED })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 700, line: 300 }, indent: { left: 400, right: 400 },
    children: [new TextRun({ text: projectTitle, italics: true, size: 26 })] }),
  teamTable,
  new Paragraph({ spacing: { before: 700, after: 40 }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: `Avance al ${FECHA}`, bold: true, size: 24, color: L.NAVY })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 0 }, children: [new TextRun({ text: 'Documento vivo: se actualiza al cierre de cada sprint. Esta versión cubre los sprints 1 a 4.', italics: true, size: 20, color: L.MUTED })] }),
];

// ---------------- INDICE ----------------
const tocBlock = [
  new Paragraph({ spacing: { after: 200 }, children: [new TextRun({ text: 'Índice de contenidos', bold: true, size: 32, color: L.NAVY })] }),
  new TableOfContents('Índice de contenidos', { hyperlink: true, headingStyleRange: '1-3' }),
  new Paragraph({ spacing: { before: 200 }, children: [new TextRun({ text: 'Si el índice aparece vacío o desactualizado, haga clic derecho sobre él y elija «Actualizar campo», o presione F9.', italics: true, size: 18, color: L.MUTED })] }),
];

const partDivider = (kicker, title, desc) => [
  new Paragraph({ children: [new PageBreak()] }),
  new Paragraph({ spacing: { before: 3200, after: 120 }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: kicker, bold: true, size: 28, color: L.MUTED })] }),
  new Paragraph({ heading: HeadingLevel.HEADING_1, alignment: AlignmentType.CENTER, spacing: { before: 0, after: 300 }, children: [new TextRun({ text: title, size: 52, bold: true, color: L.NAVY })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 0, line: 300 }, indent: { left: 900, right: 900 }, children: [new TextRun({ text: desc, size: 24, italics: true, color: L.MUTED })] }),
  new Paragraph({ children: [new PageBreak()] }),
];

const p1 = P1.convert(blocks);

const body = [
  ...tocBlock,
  ...partDivider('PARTE I', 'Anteproyecto de título', 'Reproduce, sin modificaciones de contenido, el anteproyecto presentado en el Título I: problema, arquitectura propuesta, datos, objetivos, metodología y plan de trabajo.'),
  ...p1.children,
  ...partDivider('PARTE II', 'Desarrollo', 'Documenta lo construido, probado y medido durante los sprints 1 a 4: datos, diseño, implementación, validación y resultados parciales. Lo que aún no existe se declara como pendiente.'),
  ...parte2a(),
  ...parte2b(),
  ...anexos(),
];

// ---------------- DOCUMENTO ----------------
const bulletCfg = {
  reference: 'bullet',
  levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT,
    style: { paragraph: { indent: { left: 720, hanging: 360 } } } }],
};
const decCfg = (ref) => ({
  reference: ref,
  levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT,
    style: { paragraph: { indent: { left: 720, hanging: 360 } } } }],
});

const heading = (id, name, size, o = {}) => ({
  id, name, basedOn: 'Normal', next: 'Normal', quickFormat: true,
  run: { font: L.FONT, size, bold: true, color: L.NAVY, italics: !!o.italics },
  paragraph: { spacing: { before: o.before, after: o.after }, keepNext: true, outlineLevel: o.level },
});

const doc = new Document({
  creator: 'Paolo Sepúlveda, Mauricio Reynoso, Benjamín Farias',
  title: 'Informe de Desarrollo — Título II: Coordinación de Agentes para la Mitigación del Slippage (IPSA)',
  description: 'Anteproyecto (Parte I) y desarrollo (Parte II)',
  features: { updateFields: true },
  styles: {
    default: { document: { run: { font: L.FONT, size: 22 } } },
    paragraphStyles: [
      heading('Heading1', 'Heading 1', 32, { before: 360, after: 160, level: 0 }),
      heading('Heading2', 'Heading 2', 27, { before: 280, after: 120, level: 1 }),
      heading('Heading3', 'Heading 3', 24, { before: 220, after: 100, level: 2 }),
      heading('Heading4', 'Heading 4', 22, { before: 180, after: 80, level: 3, italics: true }),
    ],
  },
  numbering: { config: [bulletCfg, decCfg('dec_p2_pipeline'), decCfg('dec_p2_ciclo'), ...p1.numbering] },
  sections: [
    {
      properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
      children: cover,
    },
    {
      properties: {
        type: SectionType.NEXT_PAGE,
        page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, right: 1440, bottom: 1300, left: 1440 }, pageNumbers: { start: 1 } },
      },
      headers: { default: new Header({ children: [new Paragraph({
        alignment: AlignmentType.RIGHT,
        border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: L.GRID, space: 4 } },
        children: [new TextRun({ text: 'Informe de Desarrollo · Título II · Mitigación del Slippage en el IPSA', size: 17, color: L.MUTED })] })] }) },
      footers: { default: new Footer({ children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: 'UTEM · Escuela de Informática y Computación   |   Página ', size: 17, color: L.MUTED }),
          new TextRun({ children: [PageNumber.CURRENT], size: 17, color: L.MUTED })] })] }) },
      children: body,
    },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUT, buf);
  console.log('escrito', OUT, Math.round(buf.length / 1024), 'KB');
});
