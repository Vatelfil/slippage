const pptxgen = require('pptxgenjs');
const fs = require('fs');
const path = require('path');
const SK = 'C:/Users/Shepu/AppData/Local/Packages/Claude_pzs8sxrjxfjjc/LocalCache/Roaming/Claude/local-agent-mode-sessions/skills-plugin/0fd035e1-2c2d-4ca8-abe9-fbcad8cc10a7/22453e8c-f3d6-4e97-b55f-5cfec9fa4c02/skills/pptx';
const { applyTheme } = require(SK + '/scripts/apply_theme.js');
const OUT = process.argv[2] || 'deck.pptx';
const IMG = (f) => path.join(__dirname, 'img', f);

const THEME = {
  name: 'Titulo II UTEM',
  headFontFace: 'Cambria',
  bodyFontFace: 'Calibri',
  colors: {
    dk1: '1A1F3C', lt1: 'FFFFFF', dk2: '1E2761', lt2: 'EEF2FA',
    accent1: '1E2761', accent2: '5A6B9C', accent3: 'E8A33D', accent4: '2E8B6E', accent5: 'C8553D', accent6: '9FB0DC',
    hlink: '1E2761', folHlink: '5A6B9C',
  },
};
const NAVY = '1E2761', ICE = 'EEF2FA', MUTED = '5A6B9C', AMBER = 'E8A33D', GREEN = '2E8B6E', LIGHT = '9FB0DC', INK = '1A1F3C';

const pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = 'Título II: avance hasta el Sprint 4';
pres.author = 'Paolo Sepúlveda, Mauricio Reynoso, Benjamín Farias';
const C = pres.SchemeColor;

const FOOT = 'Título II · Coordinación de Agentes para la Mitigación del Slippage (IPSA) · UTEM';
pres.defineSlideMaster({
  title: 'PORTADA', background: { color: NAVY },
  objects: [
    { placeholder: { options: { name: 'title', type: 'title', x: 0.7, y: 1.5, w: 8.6, h: 1.5, fontFace: 'Cambria', fontSize: 34, bold: true, color: C.background1, align: 'left', valign: 'top' }, text: '' } },
    { placeholder: { options: { name: 'body', type: 'body', x: 0.7, y: 3.15, w: 8.6, h: 1.0, fontFace: 'Calibri', fontSize: 18, color: C.background2, align: 'left', valign: 'top' }, text: '' } },
  ],
});
pres.defineSlideMaster({
  title: 'CONTENIDO', background: { color: 'FFFFFF' },
  objects: [
    { placeholder: { options: { name: 'title', type: 'title', x: 0.5, y: 0.28, w: 9.0, h: 0.75, fontFace: 'Cambria', fontSize: 30, bold: true, color: C.text2, align: 'left', valign: 'middle' }, text: '' } },
    { text: { text: FOOT, options: { x: 0.5, y: 5.28, w: 8.2, h: 0.25, fontSize: 9, color: C.accent2, fontFace: 'Calibri', margin: 0 } } },
  ],
  slideNumber: { x: 9.0, y: 5.28, w: 0.5, h: 0.25, fontSize: 9, color: C.accent2, fontFace: 'Calibri' },
});

// ------------------------------------------------------------ utilidades
const warns = [];
function estLines(text, wIn, sizePt, bold) {
  const cw = sizePt * (bold ? 0.53 : 0.49) / 72;
  const per = Math.max(1, Math.floor(wIn / cw));
  return String(text).split('\n').reduce((a, ln) => a + Math.max(1, Math.ceil(ln.length / per)), 0);
}
function check(tag, texts, wIn, hIn, sizePt, bold, spaceAfterPt = 0) {
  const lines = texts.reduce((a, t) => a + estLines(t, wIn, sizePt, bold), 0);
  const h = lines * sizePt * 1.22 / 72 + texts.length * spaceAfterPt / 72;
  if (h > hIn + 0.02) warns.push(`${tag}: alto estimado ${h.toFixed(2)} > ${hIn.toFixed(2)}`);
}
function addTitle(s, t) { s.addText(t, { placeholder: 'title' }); }
function bullets(s, name, items, o) {
  const size = o.size || 14;
  check(name, items.map((i) => (typeof i === 'string' ? i : i.t)), o.w - 0.45, o.h, size, false, o.gap ?? 6);
  s.addText(items.map((it, i) => {
    const t = typeof it === 'string' ? it : it.t;
    return { text: t, options: { bullet: true, breakLine: i < items.length - 1, bold: !!(it && it.b) } };
  }), { x: o.x, y: o.y, w: o.w, h: o.h, fontSize: size, color: C.text1, fontFace: 'Calibri', valign: 'top', paraSpaceAfter: o.gap ?? 6, isTextBox: true, objectName: name });
}
function card(s, name, o) {
  s.addShape(pres.ShapeType.roundRect, { x: o.x, y: o.y, w: o.w, h: o.h, fill: { color: o.fill || ICE }, line: { color: o.fill || ICE, width: 0 }, rectRadius: 0.08, objectName: name + '_fondo' });
  const th = o.th ?? 0.4;
  s.addText(o.title, { x: o.x + 0.15, y: o.y + 0.08, w: o.w - 0.3, h: th, fontSize: o.tsize || 15, bold: true, color: o.tcolor || C.text2, fontFace: 'Cambria', valign: 'middle', margin: 0, isTextBox: true, objectName: name + '_titulo' });
  const size = o.size || 13;
  check(name, Array.isArray(o.body) ? o.body : [o.body], o.w - 0.3, o.h - th - 0.2, size, false, 3);
  if (Array.isArray(o.body)) {
    s.addText(o.body.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < o.body.length - 1 } })), { x: o.x + 0.15, y: o.y + th + 0.1, w: o.w - 0.3, h: o.h - th - 0.2, fontSize: size, color: C.text1, fontFace: 'Calibri', valign: 'top', paraSpaceAfter: 3, margin: 0, isTextBox: true, objectName: name + '_texto' });
  } else {
    s.addText(o.body, { x: o.x + 0.15, y: o.y + th + 0.1, w: o.w - 0.3, h: o.h - th - 0.2, fontSize: size, color: C.text1, fontFace: 'Calibri', valign: 'top', margin: 0, isTextBox: true, objectName: name + '_texto' });
  }
}
function stat(s, name, o) {
  s.addText(o.big, { x: o.x, y: o.y, w: o.w, h: 0.75, fontSize: o.size || 40, bold: true, color: o.color || C.text2, fontFace: 'Cambria', align: 'left', valign: 'middle', margin: 0, isTextBox: true, objectName: name + '_valor' });
  s.addText(o.label, { x: o.x, y: o.y + 0.75, w: o.w, h: o.lh || 0.55, fontSize: 12, color: C.text1, fontFace: 'Calibri', align: 'left', valign: 'top', margin: 0, isTextBox: true, objectName: name + '_texto' });
}
function img(s, name, file, x, y, maxW, maxH, alt) {
  const b = fs.readFileSync(IMG(file));
  const w = b.readUInt32BE(16), h = b.readUInt32BE(20);
  let W = maxW, H = W * h / w;
  if (H > maxH) { H = maxH; W = H * w / h; }
  s.addImage({ path: IMG(file), x: x + (maxW - W) / 2, y: y + (maxH - H) / 2, w: W, h: H, altText: alt, objectName: name });
}
const WHO = { MR: 'MR', BF: 'BF', PS: 'PS' };
function sprintTable(s, name, rows) {
  const W = [1.95, 3.55, 2.35, 1.15];
  const head = ['Tarea', 'Qué se hizo', 'Para qué', 'Quién'].map((t) => ({ text: t, options: { bold: true, color: 'FFFFFF', fill: { color: NAVY }, fontSize: 12, fontFace: 'Calibri', valign: 'middle' } }));
  const rh = Math.min(0.75, 3.55 / rows.length);
  const body = rows.map((r, i) => r.map((t, j) => ({ text: t, options: { fontSize: 12, fontFace: 'Calibri', color: INK, bold: j === 0 || j === 3, fill: { color: i % 2 ? 'F4F6FB' : 'FFFFFF' }, valign: 'middle' } })));
  rows.forEach((r, i) => { check(`${name} fila ${i + 1} col2`, [r[1]], W[1] - 0.2, rh, 12, false); check(`${name} fila ${i + 1} col3`, [r[2]], W[2] - 0.2, rh, 12, false); check(`${name} fila ${i + 1} col1`, [r[0]], W[0] - 0.2, rh, 12, true); });
  s.addTable([head, ...body], { x: 0.5, y: 1.2, w: 9.0, colW: W, border: { type: 'solid', pt: 0.5, color: 'C9D3EA' }, rowH: [0.34, ...rows.map(() => rh)], margin: 0.06, objectName: name });
}

// ================================================================ DIAPOSITIVAS
pres.addSection({ title: 'Introducción' });
// 1 portada
let s = pres.addSlide({ masterName: 'PORTADA', sectionTitle: 'Introducción' });
s.addText('Coordinación de Agentes para la Mitigación del Slippage en el IPSA', { placeholder: 'title' });
s.addText([{ text: 'Trabajo de Título II: avance hasta el cierre del Sprint 4', options: { breakLine: true, bold: true } }, { text: 'Mauricio Reynoso · Benjamín Farias · Paolo Sepúlveda', options: { breakLine: true } }, { text: 'Profesor guía: Juan Pablo Argerstein · UTEM, 22 de octubre de 2026', options: {} }], { placeholder: 'body' });
s.addNotes('PRESENTACIÓN GRUPAL. Cómo usar este PPT para estudiar: cada diapositiva tiene un guion en las notas con (1) qué decir, (2) datos clave y (3) preguntas probables. Duración sugerida: 15 a 20 minutos.\n\nApertura (30 segundos): "Presentamos el avance del Título II hasta el cierre del Sprint 4. Vamos a mostrar qué se hizo, para qué se hizo y quién lo hizo, siguiendo el plan de hitos y sprints del Título I."\n\nAntecedentes: el proyecto es de tres integrantes: Mauricio Reynoso (redes y PPO), Benjamín Farias (datos y calibración) y Paolo Sepúlveda (arquitectura del entorno, validación y benchmarks). El profesor guía es Juan Pablo Argerstein.');

// 2 el proyecto
s = pres.addSlide({ masterName: 'CONTENIDO', sectionTitle: 'Introducción' });
addTitle(s, 'El proyecto: qué y para qué');
card(s, 'problema', { x: 0.5, y: 1.2, w: 2.95, h: 1.75, title: 'El problema', body: 'Al ejecutar una orden grande en el IPSA, el precio se mueve en contra (slippage) y encarece la operación.', size: 13 });
card(s, 'solucion', { x: 0.5, y: 3.1, w: 2.95, h: 1.95, title: 'La solución', body: 'Dos niveles de agentes: un Maestro decide cuánto y cuándo; tres Ejecutores (apertura, media jornada, cierre) deciden cómo operar. Aprenden con PPO.', size: 13 });
img(s, 'arquitectura', 'arquitectura.png', 3.6, 1.2, 5.9, 2.55, 'Arquitectura: Maestro, Ejecutores y mercado simulado');
s.addText('Objetivo: reducir el Implementation Shortfall frente a TWAP y VWAP, en un simulador calibrado con datos reales.', { x: 3.6, y: 3.85, w: 5.9, h: 0.55, fontSize: 14, bold: true, color: C.text2, fontFace: 'Calibri', margin: 0, valign: 'top', isTextBox: true, objectName: 'objetivo_general' });
check('objetivo_general', ['Objetivo: reducir el Implementation Shortfall frente a TWAP y VWAP, en un simulador calibrado con datos reales.'], 5.9, 0.55, 14, true);
s.addText('Los cuatro objetivos específicos: simulador de alta fidelidad · arquitectura jerárquica con PPO · recompensa que minimice el IS · evaluación frente a TWAP y VWAP.', { x: 3.6, y: 4.4, w: 5.9, h: 0.65, fontSize: 12, color: C.accent2, fontFace: 'Calibri', margin: 0, valign: 'top', isTextBox: true, objectName: 'objetivos_especificos' });
check('objetivos_especificos', ['Los cuatro objetivos específicos: simulador de alta fidelidad · arquitectura jerárquica con PPO · recompensa que minimice el IS · evaluación frente a TWAP y VWAP.'], 5.9, 0.65, 12, false);
s.addNotes('QUÉ Y PARA QUÉ. Slippage es la diferencia entre el precio que esperamos al decidir una compra y el precio promedio que realmente pagamos al ejecutarla. En una orden grande, cada parte que compramos mueve el precio y la siguiente sale más cara. En el IPSA esto importa porque el libro de órdenes es de liquidez fina.\n\nLa propuesta (Título I, sección 4.2): una jerarquía de agentes. El MAESTRO trabaja cada 30 minutos: decide qué fracción del inventario restante asignar al siguiente tramo y en cuántos minutos ejecutarla. Los EJECUTORES (uno por tramo horario: apertura, media jornada y cierre) trabajan cada 30 segundos y eligen tipo de orden, volumen y nivel de precio. Ambos aprenden con PPO (Proximal Policy Optimization), un algoritmo de aprendizaje por refuerzo estable.\n\nPara medir el éxito usamos el Implementation Shortfall: (precio promedio ejecutado menos precio de referencia) por cantidad. Se compara con TWAP (reparto uniforme en el tiempo) y VWAP (reparto proporcional al volumen histórico). La hipótesis es una reducción de al menos 10% con significancia estadística.\n\nComo no se puede experimentar en el mercado real, todo ocurre en un simulador (ABIDES-Gym de JP Morgan y un simulador propio de Poisson) calibrado con datos reales.');

pres.addSection({ title: 'Plan' });
// 3 hitos
s = pres.addSlide({ masterName: 'CONTENIDO', sectionTitle: 'Plan' });
addTitle(s, 'Hitos del plan del Título I');
{
  const hd = ['Hito', 'Qué pide el Título I', 'Periodo', 'Sprints', 'Estado'].map((t) => ({ text: t, options: { bold: true, color: 'FFFFFF', fill: { color: NAVY }, fontSize: 12, fontFace: 'Calibri', valign: 'middle' } }));
  const mk = (t, fill, bold) => ({ text: t, options: { fontSize: 11, fontFace: 'Calibri', color: INK, bold: !!bold, fill: { color: fill }, valign: 'middle' } });
  const done = (t) => ({ text: t, options: { fontSize: 11, fontFace: 'Calibri', color: 'FFFFFF', bold: true, fill: { color: GREEN }, valign: 'middle', align: 'center' } });
  const prog = (t) => ({ text: t, options: { fontSize: 11, fontFace: 'Calibri', color: INK, bold: true, fill: { color: AMBER }, valign: 'middle', align: 'center' } });
  const pend = (t) => ({ text: t, options: { fontSize: 11, fontFace: 'Calibri', color: INK, bold: true, fill: { color: 'D6DDEE' }, valign: 'middle', align: 'center' } });
  const rows = [
    ['H1–H4', 'Título I: estado del arte, arquitectura de IA, diseño del simulador y defensa', '1.er semestre 2026', '—', done('Completado')],
    ['H5', 'Construcción del entorno de simulación: simulador en Python y datos históricos', '17 ago – 11 sep', '1 y 2', done('Completado')],
    ['H6', 'Desarrollo y entrenamiento de agentes: redes, PPO, recompensas, integración', '14 sep – 23 oct', '3, 4 y 5', prog('Sprints 3–4 listos; 5 en curso')],
    ['H7', 'Validación y pruebas de desempeño: ajuste de hiperparámetros y comparación con TWAP y VWAP', '26 oct – 20 nov', '6 y 7', pend('Pendiente')],
    ['H8', 'Memoria y examen de título: informe final y defensa', '23 nov – 18 dic', '8 y 9', pend('Pendiente')],
  ];
  const body = rows.map((r, i) => [mk(r[0], i % 2 ? 'F4F6FB' : 'FFFFFF', true), mk(r[1], i % 2 ? 'F4F6FB' : 'FFFFFF'), mk(r[2], i % 2 ? 'F4F6FB' : 'FFFFFF'), mk(r[3], i % 2 ? 'F4F6FB' : 'FFFFFF'), r[4]]);
  rows.forEach((r, i) => check(`hitos fila ${i + 1}`, [r[1]], 3.9 - 0.2, 0.7, 11, false));
  s.addTable([hd, ...body], { x: 0.5, y: 1.2, w: 9.0, colW: [0.8, 3.9, 1.5, 0.85, 1.95], border: { type: 'solid', pt: 0.5, color: 'C9D3EA' }, rowH: [0.34, 0.6, 0.6, 0.7, 0.7, 0.6], margin: 0.06, objectName: 'tabla_hitos' });
  s.addText('Metodología Scrum (Título I, sección 10.1): sprints de 2 semanas, sprint planning y revisión al cierre de cada uno.', { x: 0.5, y: 4.85, w: 9.0, h: 0.35, fontSize: 12, color: C.accent2, fontFace: 'Calibri', margin: 0, isTextBox: true, objectName: 'nota_scrum' });
}
s.addNotes('El Título I (sección 10.2) definió cuatro hitos para el primer semestre (H1 a H4: estado del arte, arquitectura de IA, diseño del simulador y defensa) y cuatro para el segundo (H5 a H8). Esos hitos se tradujeron en nueve sprints de dos semanas con metodología Scrum.\n\nH5, Construcción del entorno de simulación (sprints 1 y 2, 17 agosto a 11 septiembre): simulador y datos históricos. Completado.\nH6, Desarrollo y entrenamiento de agentes (sprints 3, 4 y 5, 14 septiembre a 23 octubre): redes, PPO, recompensas e integración. Los sprints 3 y 4 están cerrados; el 5 termina este viernes 23 de octubre.\nH7, Validación y pruebas de desempeño (sprints 6 y 7, 26 octubre a 20 noviembre): ajuste de hiperparámetros y comparación estadística con TWAP y VWAP.\nH8, Memoria y examen de título (sprints 8 y 9, 23 noviembre a 18 diciembre).\n\nHoy presentamos los sprints 1 a 4, es decir, todo H5 y la primera parte de H6.');

// 4 Gantt
s = pres.addSlide({ masterName: 'CONTENIDO', sectionTitle: 'Plan' });
addTitle(s, 'Carta Gantt: hitos y sprints');
{
  const d0 = new Date(2026, 7, 17), d1 = new Date(2026, 11, 19);
  const gx0 = 2.55, gx1 = 9.5, gy = 1.55;
  const X = (d) => gx0 + (d - d0) / (d1 - d0) * (gx1 - gx0);
  const dt = (m, d) => new Date(2026, m - 1, d);
  // meses
  const months = [['Ago', dt(8, 17), dt(9, 1)], ['Sep', dt(9, 1), dt(10, 1)], ['Oct', dt(10, 1), dt(11, 1)], ['Nov', dt(11, 1), dt(12, 1)], ['Dic', dt(12, 1), dt(12, 19)]];
  months.forEach(([n, a, b], i) => {
    s.addShape(pres.ShapeType.rect, { x: X(a), y: 1.2, w: X(b) - X(a), h: 0.3, fill: { color: i % 2 ? 'DDE6F7' : 'EEF2FA' }, line: { color: 'FFFFFF', width: 0.75 }, objectName: 'mes_' + n });
    s.addText(n + ' 2026', { x: X(a), y: 1.2, w: X(b) - X(a), h: 0.3, fontSize: 11, bold: true, color: C.text2, align: 'center', valign: 'middle', margin: 0, fontFace: 'Calibri', isTextBox: true, objectName: 'mes_txt_' + n });
  });
  const rows = [
    { h: 'H5 Entorno de simulación', sp: [['S1', dt(8, 17), dt(8, 28), 'ok'], ['S2', dt(8, 31), dt(9, 11), 'ok']], hito: dt(9, 11), hl: '11 sep' },
    { h: 'H6 Agentes y entrenamiento', sp: [['S3', dt(9, 14), dt(9, 25), 'ok'], ['S4', dt(9, 28), dt(10, 9), 'ok'], ['S5', dt(10, 12), dt(10, 23), 'cur']], hito: dt(10, 23), hl: '23 oct' },
    { h: 'H7 Validación y desempeño', sp: [['S6', dt(10, 26), dt(11, 6), 'pen'], ['S7', dt(11, 9), dt(11, 20), 'pen']], hito: dt(11, 20), hl: '20 nov' },
    { h: 'H8 Memoria y examen', sp: [['S8', dt(11, 23), dt(12, 4), 'pen'], ['S9', dt(12, 7), dt(12, 18), 'pen']], hito: dt(12, 18), hl: '18 dic' },
  ];
  const rh = 0.72;
  rows.forEach((r, i) => {
    const y = gy + 0.12 + i * rh;
    s.addShape(pres.ShapeType.rect, { x: 0.5, y: y - 0.08, w: 9.0, h: rh - 0.04, fill: { color: i % 2 ? 'FFFFFF' : 'F7F9FD' }, line: { color: 'FFFFFF', width: 0 }, objectName: 'fila_' + i });
    s.addText(r.h, { x: 0.55, y: y, w: 1.95, h: 0.5, fontSize: 12, bold: true, color: C.text2, valign: 'middle', margin: 0, fontFace: 'Calibri', isTextBox: true, objectName: 'hito_nombre_' + i });
    r.sp.forEach(([n, a, b, st]) => {
      const fill = st === 'ok' ? NAVY : st === 'cur' ? AMBER : 'C9D3EA';
      const col = st === 'ok' ? 'FFFFFF' : INK;
      s.addShape(pres.ShapeType.roundRect, { x: X(a), y: y + 0.02, w: X(new Date(b.getTime() + 86400000)) - X(a), h: 0.42, fill: { color: fill }, line: { color: fill, width: 0 }, rectRadius: 0.05, objectName: 'barra_' + n });
      s.addText(n, { x: X(a), y: y + 0.02, w: X(new Date(b.getTime() + 86400000)) - X(a), h: 0.42, fontSize: 12, bold: true, color: col, align: 'center', valign: 'middle', margin: 0, fontFace: 'Calibri', isTextBox: true, objectName: 'barra_txt_' + n });
    });
    s.addShape(pres.ShapeType.diamond, { x: X(r.hito) - 0.09 + 0.02, y: y + 0.5, w: 0.18, h: 0.18, fill: { color: 'C8553D' }, line: { color: 'C8553D', width: 0 }, objectName: 'hito_' + i });
    s.addText(r.hl, { x: X(r.hito) - 1.02, y: y + 0.48, w: 0.82, h: 0.22, fontSize: 10, color: C.accent2, align: 'right', valign: 'middle', margin: 0, fontFace: 'Calibri', isTextBox: true, objectName: 'hito_fecha_' + i });
  });
  // hoy
  const xh = X(dt(10, 22));
  s.addShape(pres.ShapeType.line, { x: xh, y: 1.5, w: 0, h: 3.2, line: { color: 'C8553D', width: 1.25, dashType: 'dash' }, objectName: 'linea_hoy' });
  s.addText('Hoy · 22 oct', { x: xh - 0.7, y: 4.72, w: 1.4, h: 0.22, fontSize: 10, bold: true, color: 'C8553D', align: 'center', margin: 0, fontFace: 'Calibri', isTextBox: true, objectName: 'hoy_texto' });
  // leyenda
  const lg = [['Completado', NAVY], ['En curso', AMBER], ['Pendiente', 'C9D3EA']];
  lg.forEach(([t, c], i) => {
    s.addShape(pres.ShapeType.roundRect, { x: 0.55 + i * 1.55, y: 5.0, w: 0.28, h: 0.18, fill: { color: c }, line: { color: c, width: 0 }, rectRadius: 0.03, objectName: 'leyenda_' + i });
    s.addText(t, { x: 0.9 + i * 1.55, y: 4.98, w: 1.2, h: 0.22, fontSize: 10, color: C.text1, margin: 0, valign: 'middle', fontFace: 'Calibri', isTextBox: true, objectName: 'leyenda_txt_' + i });
  });
  s.addShape(pres.ShapeType.diamond, { x: 5.3, y: 5.0, w: 0.18, h: 0.18, fill: { color: 'C8553D' }, line: { color: 'C8553D', width: 0 }, objectName: 'leyenda_hito' });
  s.addText('Cierre del hito', { x: 5.55, y: 4.98, w: 1.5, h: 0.22, fontSize: 10, color: C.text1, margin: 0, valign: 'middle', fontFace: 'Calibri', isTextBox: true, objectName: 'leyenda_hito_txt' });
}
s.addNotes('LECTURA DE LA CARTA GANTT. Cada fila es un hito del Título I (H5 a H8) y cada barra es un sprint de dos semanas. Los rombos rojos marcan el cierre del hito (11 sep, 23 oct, 20 nov y 18 dic). La línea punteada es hoy, 22 de octubre.\n\nAzul oscuro: sprints cerrados (1, 2, 3 y 4). Ámbar: sprint 5, en curso, que termina el viernes 23 (integración CTDE, ciclo de entrenamiento, meta-órdenes y primer entrenamiento). Gris: sprints pendientes (6 y 7 de validación; 8 y 9 de memoria y defensa).\n\nMensaje: el proyecto va al día con el plan. El primer semestre (H1 a H4) cubrió el Título I.\n\nSi preguntan por el avance en horas: el plan de Título II suma 604 horas; hay 216 cerradas (sprints 3 y 4 completos más los benchmarks adelantados), alrededor de 36%, mientras que el tiempo transcurrido desde el sprint 3 es cercano a 40%. Las horas del sprint 5 se suman al cerrarlo.');

pres.addSection({ title: 'Sprint 1 y 2' });
// 5 Sprint 1
s = pres.addSlide({ masterName: 'CONTENIDO', sectionTitle: 'Sprint 1 y 2' });
addTitle(s, 'Sprint 1 (17–28 ago): alistamiento');
sprintTable(s, 'tabla_sprint1', [
  ['1.1.1 Planificación y backlog', 'Plan de 9 sprints y 604 horas, con tareas, responsables y criterios (Excel del plan).', 'Ordenar el trabajo y repartir la carga entre los tres', 'Equipo'],
  ['1.1.2 Entorno y repositorio', 'Repositorio en GitHub, ramas por tarea y revisión de pull requests, guía de contribución.', 'Trabajar en paralelo con trazabilidad', 'MR'],
  ['1.1.3 Descarga de datos', 'Velas de 5 min de las 30 acciones del IPSA (yfinance), con manifiesto y reporte de calidad.', 'Tener datos reales para calibrar y validar', 'BF'],
  ['1.1.4 Vectores S_M y S_E', 'Esquemas JSON: estado del Maestro (7 variables) y de los Ejecutores (27 variables).', 'Fijar el contrato entre datos, entorno y redes', 'PS'],
  ['1.1.5 Sprint Review', 'Revisión de lo entregado y ajuste del plan.', 'Cerrar el sprint con evidencia', 'Equipo'],
]);
s.addNotes('SPRINT 1: ALISTAMIENTO. Objetivo: dejar listo el terreno para construir.\n\n1.1.1 Planificación (equipo): el plan de Título II quedó en un Excel con 9 sprints y 604 horas: Mauricio 196, Benjamín 188, Paolo 196 y 24 de equipo.\n1.1.2 Entorno y repositorio (Mauricio): repositorio en GitHub, flujo de ramas por tarea y pull requests. Permite que los tres trabajen en paralelo y que todo cambio quede registrado.\n1.1.3 Descarga de datos (Benjamín): velas OHLCV de 5 minutos de las 30 acciones del IPSA con yfinance. Importante: la fuente solo entrega 60 días en esa resolución, por eso el pipeline trabaja con "snapshots" fechados (el principal es el del 23 de agosto de 2026).\n1.1.4 Vectores de estado (Paolo): se definió formalmente qué observa cada agente. El Maestro observa 7 variables (inventario restante, hora, número de decisiones, volatilidad, volumen promedio, desbalance del libro y tramo) y cada Ejecutor 27 (3 privadas, 5 niveles de precio y volumen por lado del libro, spread, desbalance, tasa de órdenes y precio medio). Se dejaron en archivos JSON (SM_schema.json y SE_schema.json) para que el código lea las dimensiones desde ahí. Un dato: el esquema inicial decía 26 variables; al contarlas se corrigió a 27 y el código calcula la dimensión desde la lista.\n\nPara qué: sin datos, sin repositorio y sin un contrato de estado y acción, no se puede construir el simulador ni las redes.');

// 6 Sprint 2
s = pres.addSlide({ masterName: 'CONTENIDO', sectionTitle: 'Sprint 1 y 2' });
addTitle(s, 'Sprint 2 (31 ago–11 sep): datos y entorno');
sprintTable(s, 'tabla_sprint2', [
  ['1.2.1 Limpieza de datos', 'Grilla fija de 78 velas por día, imputación marcada, fusión de la subasta de cierre y normalización.', 'Datos homogéneos para el simulador', 'BF'],
  ['1.2.2 Variables del Maestro', 'Volatilidad, volumen promedio y tramo horario calculados desde las velas.', 'Alimentar el estado S_M del Maestro', 'BF'],
  ['1.2.3 Prueba de ABIDES-Gym', 'Prueba de concepto del simulador de libro de órdenes de JP Morgan.', 'Confirmar que sirve como entorno final', 'MR'],
  ['1.2.4 Dependencias', 'Receta de instalación (Python 3.9, versiones fijadas) y lista congelada de paquetes.', 'Que cualquiera reproduzca el entorno en Colab', 'MR'],
  ['1.2.5 Arquitectura del entorno', 'Tres capas (Maestro, Ejecutores, simulación), ciclo reset/step y mensajes ASIGNAR/REPORTE.', 'Definir cómo se conectan los componentes antes de programarlos', 'PS'],
]);
s.addNotes('SPRINT 2: PIPELINE DE DATOS Y ENTORNO. Objetivo: tener datos limpios y comprobar que el simulador funciona.\n\n1.2.1 Limpieza (Benjamín): se filtra la sesión de 09:30 a 15:55, cada día se reindexa a 78 velas, las velas sin transacción se imputan y quedan marcadas (is_imputed), y la vela de las 16:00 (subasta de cierre) se fusiona con la de 15:55. Se normaliza con MinMax por ticker, conservando las columnas en unidades reales. Resultado del snapshot de agosto: 30 tickers, 60 días, 4.680 velas por ticker; 15 tickers de cobertura alta (tier A) y 15 de baja (tier B). FALABELLA tiene 92,9% de cobertura.\n1.2.2 Variables del Maestro (Benjamín): volatilidad (desviación móvil de 6 velas), volumen promedio móvil y tramo.\n1.2.3 y 1.2.4 (Mauricio): ABIDES-Gym es difícil de instalar (repositorio archivado, exige Python 3.9, gym 0.18 y numpy 1.22). Se documentó una receta que funciona en Google Colab y se congelaron las versiones.\n1.2.5 Arquitectura (Paolo): documento de diseño con tres capas: coordinación (Maestro), ejecución (tres Ejecutores) y simulación. Un episodio es una jornada y se repite: reset, el Maestro decide, se envía el mensaje ASIGNAR al Ejecutor del tramo, el Ejecutor opera y devuelve REPORTE, se avanza el reloj 30 minutos. Conviven tres escalas de tiempo: velas de 5 minutos, decisiones del Maestro cada 30 minutos y del Ejecutor cada 30 segundos.\n\nPara qué: los datos alimentan la calibración; ABIDES-Gym es el simulador final; y el diseño evita contradicciones al implementar.');

pres.addSection({ title: 'Sprint 3' });
// 7 Sprint 3
s = pres.addSlide({ masterName: 'CONTENIDO', sectionTitle: 'Sprint 3' });
addTitle(s, 'Sprint 3 (14–25 sep): redes y espacios');
sprintTable(s, 'tabla_sprint3', [
  ['2.1.1 Red del Maestro', 'Red Actor-Crítico en PyTorch: 7 entradas, 40 acciones, dos capas de 256 neuronas.', 'Decidir cuánto y cuándo ejecutar cada 30 minutos', 'MR'],
  ['2.1.2 Redes de los Ejecutores', 'Tres redes, una por tramo: 27 entradas y 240 acciones; fábrica que las crea y conecta.', 'Decidir cómo ejecutar cada 30 segundos', 'BF'],
  ['2.1.3 Calibración de Poisson', 'Intensidades de llegada λ⁺, λ⁻ y θ por activo y tramo (90 combinaciones) y simulador de libro liviano.', 'Simular el mercado sin depender de ABIDES', 'PS / BF'],
  ['2.1.4 Espacios Gymnasium', 'S_M, S_E, A_M (40) y A_E (240) como espacios Gymnasium, con conversión de índices.', 'Que redes y entornos hablen el mismo formato', 'PS'],
  ['2.1.5 Sprint Review', 'Revisión del sprint y de las desviaciones de diseño.', 'Cerrar con las decisiones documentadas', 'Equipo'],
]);
s.addNotes('SPRINT 3: REDES ACTOR-CRÍTICO, POISSON Y ESPACIOS. Objetivo: construir las piezas que el algoritmo de aprendizaje va a usar.\n\n2.1.1 Red del Maestro (Mauricio): Actor-Crítico con un tronco compartido de dos capas de 256 neuronas y dos cabezas: el actor entrega 40 logits (10 fracciones por 4 ventanas) y el crítico un valor. Desviación documentada respecto del Excel (que pedía 64 neuronas, Xavier y Dropout): se usaron 256 y una sola cabeza discreta.\n2.1.2 Redes de los Ejecutores (Benjamín responsable; fábrica make_hierarchy): tres redes, una por tramo, con 27 entradas y 240 salidas. Es totalmente discreta en vez de híbrida; quedó documentada y ratificada en la revisión del cierre.\n2.1.3 Calibración de Poisson (Paolo y Benjamín): la llegada de órdenes se modela con tres intensidades por paso de 30 segundos: λ+ (compras), λ− (ventas) y θ (cancelaciones), estimadas por cada ticker y tramo. Con esos parámetros se construyó un simulador de libro de 5 niveles por lado. Verificación: comprar 8.000 acciones consumiendo 2.000 a $5.800, 5.500 a $5.810 y 500 a $5.820 da un precio promedio de $5.808,125, igual al ejemplo del Título I. Límite: el test KS rechaza en los 90 pares ticker-tramo; por eso se usa como intensidad de entrada y como entorno de prueba, no como generador final.\n2.1.4 Espacios Gymnasium (Paolo): el Maestro tiene Discrete(40) y el Ejecutor MultiDiscrete([3, 10, 8]) = 240 acciones; las funciones decode_flat y encode_flat traducen el índice que produce la red al formato del entorno. Los rangos se cargan desde los esquemas JSON.\n\nPara qué: las redes necesitan entradas y salidas bien definidas y un entorno estándar donde jugar.');

// 8 caracterización del mercado
s = pres.addSlide({ masterName: 'CONTENIDO', sectionTitle: 'Sprint 3' });
addTitle(s, 'Cómo se comporta el IPSA en el día');
img(s, 'perfil_mercado', 'perfil_mercado_ipsa_real.png', 0.5, 1.15, 9.0, 2.4, 'Spread, volatilidad y volumen por tramo horario del IPSA');
card(s, 'hallazgo_spread', { x: 0.5, y: 3.7, w: 2.9, h: 1.4, title: 'Spread', body: '0,138 % en la apertura, 0,112 % en media jornada y 0,128 % en el cierre.', size: 13 });
card(s, 'hallazgo_vol', { x: 3.55, y: 3.7, w: 2.9, h: 1.4, title: 'Volatilidad', body: 'Decrece de la apertura a la media jornada y se mantiene baja en el cierre.', size: 13 });
card(s, 'hallazgo_volumen', { x: 6.6, y: 3.7, w: 2.9, h: 1.4, title: 'Volumen por vela', body: 'Crece hacia el cierre: de 396.765 a 698.419 acciones.', size: 13 });
s.addNotes('PARA QUÉ: contrastar con datos reales lo que el Título I anticipaba. Se caracterizó el mercado por tramo sobre los 30 tickers (140.400 observaciones) con el snapshot de septiembre. Como no hay libro de órdenes real de Nivel 2, el spread se aproxima con el rango máximo-mínimo de cada vela.\n\nHallazgo: el patrón no es en "U" sino decreciente (forma de "L"): el spread es mayor en la apertura, no en la media jornada; la volatilidad decrece y no repunta en el cierre; el volumen crece hacia el cierre. Dos análisis independientes (esta caracterización y la calibración de Poisson, que usa otro snapshot y otra metodología) llegan a la misma conclusión.\n\nConsecuencia para el proyecto: es una hipótesis para el entrenamiento (un agente eficiente podría asignar menos volumen donde el spread es mayor), no un resultado. Quién: Paolo, con apoyo de la calibración de Benjamín.\n\nSi preguntan por la limitación: sin Nivel 2 el spread es un proxy; podría haber parte de artefacto.');

pres.addSection({ title: 'Sprint 4' });
// 9 Sprint 4a
s = pres.addSlide({ masterName: 'CONTENIDO', sectionTitle: 'Sprint 4' });
addTitle(s, 'Sprint 4 (28 sep–9 oct): PPO y recompensas');
sprintTable(s, 'tabla_sprint4a', [
  ['2.2.1 PPO: L_CLIP y GAE', 'Algoritmo PPO con recorte, ventajas GAE, registro de métricas y puntos de control.', 'Algoritmo con el que aprenden los agentes', 'MR'],
  ['2.2.2 Recompensa del Maestro', 'Calibración de λ con 100 simulaciones: λ = 0,05 (penalización ≈ 1 vez el costo).', 'Que complete la orden sin desestabilizar el entrenamiento', 'MR'],
  ['2.2.3 Recompensa de los Ejecutores', 'Varianza causal normalizada y barrido de β; fase 2 con PPO en ABIDES: β = 0,0061796.', 'Equilibrar costo de ejecución y riesgo', 'BF / PS'],
  ['2.3.4 TWAP y VWAP (adelanto)', 'Dos estrategias de referencia ejecutadas sobre 10 meta-órdenes pareadas.', 'Línea base que el sistema debe superar', 'PS'],
]);
s.addNotes('SPRINT 4, PRIMERA PARTE: ALGORITMO Y RECOMPENSAS.\n\n2.2.1 PPO (Mauricio): implementación de la función objetivo recortada L_CLIP, ventajas con GAE, pérdida del crítico y bonificación de entropía; deja un CSV por actualización (pérdidas, entropía, KL) y puntos de control. Paolo ajustó que torch se importe solo al usarlo y que las semillas sean reproducibles.\n2.2.2 Recompensa del Maestro (Mauricio): R_M = menos el costo total menos λ por el inventario no ejecutado al cierre. Se probaron λ de 0,01 a 1,0 en 100 simulaciones. Con λ bajo conviene dejar acciones sin comprar; con λ alto la penalización domina y desestabiliza al crítico. Con λ = 0,05 la penalización equivale a 1,06 veces el costo. Es una calibración por escala, provisional: se revalida cuando el Maestro tenga entrenamiento real.\n2.2.3 Recompensa de los Ejecutores (Benjamín y Paolo): R_E = (precio medio menos precio de ejecución) por cantidad, menos β por varianza del precio por cantidad. Benjamín definió la varianza como causal (solo usa precios pasados) y normalizada, y calculó β* (0,0618 en ABIDES). Paolo hizo la fase 2: entrenó un Ejecutor con PPO durante 300 episodios por valor de β y lo evaluó con 30 semillas. Solo con 0,1 por β* se completa el 95% de la orden: β = 0,0061796.\n2.3.4 Benchmarks (Paolo, adelantado del sprint 5 porque no dependía de otras tareas).\n\nPara qué: sin una recompensa bien escalada el agente no aprende lo que queremos.');

// 10 Sprint 4b
s = pres.addSlide({ masterName: 'CONTENIDO', sectionTitle: 'Sprint 4' });
addTitle(s, 'Sprint 4: el simulador y su validación');
sprintTable(s, 'tabla_sprint4b', [
  ['2.2.4 Calibración de rmsc04', 'Parámetros de ABIDES ajustados con datos de FALABELLA (grilla, refinamiento y 30 semillas).', 'Que el mercado simulado se parezca al IPSA', 'BF'],
  ['Extensión a COPEC y ECL', 'Mismo método en otros dos activos; se ajustó la proporción de agentes de momentum.', 'Contar con tres activos calibrados', 'PS'],
  ['2.2.5 Validación del simulador', 'Pruebas KS, Mann–Whitney y Kruskal–Wallis con 30 semillas por tramo, antes y después de calibrar.', 'Medir cuánto se parece al mercado real', 'PS'],
  ['Cierre de los sprints 1 a 4', 'Acta de cierre, revisión cruzada y entregables menores integrados al repositorio.', 'Dejar cuatro sprints cerrados con evidencia', 'Equipo'],
]);
s.addNotes('SPRINT 4, SEGUNDA PARTE: EL SIMULADOR.\n\n2.2.4 Calibración de rmsc04 (Benjamín): rmsc04 es la configuración de referencia de ABIDES-Gym (1.000 agentes de ruido, 102 de valor, 12 de momentum y 2 creadores de mercado), pensada para una acción genérica de 1.000 dólares. Se ajustó con FALABELLA: nivel de precio, volatilidad del valor fundamental por tramo (corrigiendo un error de unidades del oráculo) y, por búsqueda en grilla, los parámetros del creador de mercado y la actividad. Se validó con 30 semillas nuevas por tramo. Resultado: volatilidad dentro del 10% del objetivo en los tres tramos.\nExtensión a COPEC y ECL (Paolo): al calibrar con menos agentes de ruido aparecieron corridas desbocadas; el diagnóstico mostró que los 12 agentes de momentum por defecto desestabilizaban el mercado. Con 3 agentes de momentum (la misma proporción que FALABELLA) hubo 0 de 30 corridas desbocadas en los tres tramos.\n2.2.5 Validación formal (Paolo): criterios fijados antes de ver los datos; ver la siguiente diapositiva.\n\nPara qué: los resultados del entrenamiento solo se pueden interpretar si se sabe cuánto se parece el simulador al mercado.');

// 11 validación
s = pres.addSlide({ masterName: 'CONTENIDO', sectionTitle: 'Sprint 4' });
addTitle(s, 'Validación: la calibración acerca el simulador');
s.addChart(pres.charts.BAR, [
  { name: 'Antes de calibrar', labels: ['Apertura', 'Media jornada', 'Cierre'], values: [0.324, 0.279, 0.275] },
  { name: 'Calibrado', labels: ['Apertura', 'Media jornada', 'Cierre'], values: [0.073, 0.098, 0.066] },
], { x: 0.5, y: 1.15, w: 5.0, h: 3.9, barDir: 'col', chartColors: [LIGHT, NAVY], showLegend: true, legendPos: 'b', legendFontSize: 11, legendFontFace: '+mn-lt', legendColor: INK,
  showTitle: true, title: 'Distancia D del test KS (menor es mejor)', titleFontSize: 12, titleColor: INK, titleFontFace: '+mn-lt',
  showValue: true, dataLabelPosition: 'outEnd', dataLabelFormatCode: '0.000', dataLabelFontSize: 10, dataLabelColor: INK, dataLabelFontFace: '+mn-lt',
  catAxisLabelFontSize: 11, catAxisLabelColor: INK, catAxisLabelFontFace: '+mn-lt', valAxisLabelFontSize: 10, valAxisLabelColor: INK, valAxisLabelFontFace: '+mn-lt',
  valAxisMinVal: 0, valAxisMaxVal: 0.4, valGridLine: { color: 'E3E8F4', size: 0.5 }, catGridLine: { style: 'none' } });
card(s, 'valid_si', { x: 5.7, y: 1.2, w: 3.8, h: 1.75, title: 'Lo que sí coincide', body: ['Escala de los retornos (desvío 0,89 a 0,98 del real)', 'Patrón entre tramos', 'Tamaño de efecto trivial'], size: 12, fill: 'E3F2EC', tcolor: '1F6F55' });
card(s, 'valid_no', { x: 5.7, y: 3.1, w: 3.8, h: 1.95, title: 'Límites declarados', body: ['El KS rechaza con miles de retornos', 'Volumen por vela: +49 %, +22 %, +5 %', 'Spread 0,17 bps frente a 4–35 bps reales'], size: 12, fill: 'FBEFD9', tcolor: '8A5A00' });
check('valid_si', ['Escala de los retornos (desvío 0,89 a 0,98 del real)', 'Patrón entre tramos', 'Tamaño de efecto trivial'], 3.5, 1.75 - 0.6, 12, false, 3);
s.addNotes('RESULTADO CLAVE DE LA VALIDACIÓN (tarea 2.2.5, Paolo). Se compararon los retornos de 5 minutos simulados (30 semillas por tramo) con los reales de FALABELLA, antes y después de calibrar. El estadístico D del KS es la mayor distancia entre las dos distribuciones: antes 0,28 a 0,32; después 0,07 a 0,10. Es decir, la calibración acerca el simulador entre 3 y 4 veces.\n\nVeredicto formal: con el criterio literal del plan (todos los p mayores que 0,05) el simulador calibrado NO es válido, porque el KS crudo rechaza en los tres tramos (por muy poco en apertura y cierre, con D/D crítico de 1,10 y 1,03; con claridad en media jornada, 1,75). Pero la escala de los retornos coincide (desvío simulado/real entre 0,89 y 0,98, tamaño de efecto g de Hedges trivial) y el patrón entre tramos también.\n\nLímites: el KS con miles de retornos agrupados detecta diferencias pequeñas, por eso se reportan también el tamaño del efecto y D/D crítico; el volumen por vela simulado es 49%, 22% y 5% mayor que el real; el spread simulado (0,17 bps, un tick) queda mucho bajo los proxies reales (4 a 35 bps).\n\nQué significa para la tesis: el costo absoluto en el simulador queda subestimado, pero la comparación entre estrategias bajo las mismas condiciones sigue siendo informativa. Es una tarea "hecha con límite": se ejecutó, se midió y el límite quedó escrito con su causa.');

// 12 β y benchmarks
s = pres.addSlide({ masterName: 'CONTENIDO', sectionTitle: 'Sprint 4' });
addTitle(s, 'Recompensa y benchmarks: resultados');
img(s, 'beta_fase2', 'beta_fase2_apertura.png', 0.5, 1.2, 5.1, 2.1, 'Slippage y cumplimiento para cada valor de beta');
s.addText('Elección de β (apertura, 300 episodios por valor): solo 0,1 × β∗ completa el 95 % de la orden. Con β mayor, no operar sale gratis.', { x: 0.5, y: 3.4, w: 5.1, h: 0.95, fontSize: 13, color: C.text1, fontFace: 'Calibri', valign: 'top', margin: 0, isTextBox: true, objectName: 'texto_beta' });
check('texto_beta', ['Elección de β (apertura, 300 episodios por valor): solo 0,1 × β∗ completa el 95 % de la orden. Con β mayor, no operar sale gratis.'], 5.1, 0.95, 13, false);
s.addText('Regla fijada antes de ver los datos; β = 0,0061796 es provisional.', { x: 0.5, y: 4.4, w: 5.1, h: 0.5, fontSize: 12, italic: true, color: C.accent2, fontFace: 'Calibri', valign: 'top', margin: 0, isTextBox: true, objectName: 'nota_beta' });
s.addChart(pres.charts.BAR, [{ name: 'Implementation Shortfall medio (pesos)', labels: ['TWAP', 'VWAP'], values: [36932, 35569] }], {
  x: 5.8, y: 1.15, w: 3.7, h: 2.9, barDir: 'col', chartColors: [NAVY, LIGHT], showLegend: false, showTitle: true, title: 'IS medio, 10 meta-órdenes (pesos)', titleFontSize: 12, titleColor: INK, titleFontFace: '+mn-lt',
  showValue: true, dataLabelPosition: 'outEnd', dataLabelFormatCode: '#,##0', dataLabelFontSize: 11, dataLabelColor: INK, dataLabelFontFace: '+mn-lt',
  catAxisLabelFontSize: 11, catAxisLabelColor: INK, catAxisLabelFontFace: '+mn-lt', valAxisLabelFontSize: 10, valAxisLabelColor: INK, valAxisLabelFontFace: '+mn-lt', valAxisMinVal: 0, valAxisMaxVal: 45000,
  valGridLine: { color: 'E3E8F4', size: 0.5 }, catGridLine: { style: 'none' }, invertedColors: [LIGHT] });
s.addText('VWAP cuesta 3,8 % menos que TWAP en las 10 corridas (Wilcoxon p = 0,00195).', { x: 5.8, y: 4.1, w: 3.7, h: 0.8, fontSize: 13, bold: true, color: C.text2, fontFace: 'Calibri', valign: 'top', margin: 0, isTextBox: true, objectName: 'texto_bench' });
check('texto_bench', ['VWAP cuesta 3,8 % menos que TWAP en las 10 corridas (Wilcoxon p = 0,00195).'], 3.7, 0.8, 13, true);
s.addNotes('DOS RESULTADOS DE LA RECOMPENSA Y LOS BENCHMARKS.\n\nElección de β (Benjamín calculó β*, Paolo hizo la fase 2 con PPO). Se entrenó un Ejecutor en ABIDES calibrado, tramo de apertura, 300 episodios por valor, y se evaluó con 30 semillas nuevas. Slippage: control (β=0) 5,12 bps con 97% de la orden completada; 0,1×β* 4,71 bps con 100%; 0,3×β* 5,77 bps con solo 34%; 1×β* no ejecuta nada. Explicación: el término de riesgo se cobra sobre lo ejecutado, así que con β alto no operar sale gratis y la red aprende a no operar. La regla de selección se fijó antes de ver los datos (cumplir 95% de la orden y menor slippage): β = 0,0061796. Con la fórmula del Título I el riesgo solo puede pesar poco. Se dejó una regla de vigilancia: si en el entrenamiento inicial del sprint 5 el cumplimiento baja de 95%, se pasa a cobrar el riesgo sobre el inventario pendiente, opción ya implementada. β es provisional (solo apertura, una semilla de red).\n\nBenchmarks TWAP y VWAP (Paolo, adelantados). TWAP reparte la orden en 13 partes iguales (7,7% por periodo); VWAP la reparte según el volumen histórico por tramo (5,9% por periodo de apertura, 6,8% media jornada, 10,4% cierre). Ambos usan órdenes de mercado dentro de cada periodo, sobre el mismo Ejecutor y con las mismas métricas que usará el sistema. Se corrieron 10 meta-órdenes de 5.000 acciones de FALABELLA con 10 semillas. IS medio: TWAP 36.932 pesos, VWAP 35.569. VWAP es mejor en las 10 corridas, Wilcoxon p = 0,00195 (el mínimo con 10 pares). Conclusión: VWAP es el benchmark más exigente y es contra él que el sistema deberá demostrar la reducción de 10%.');

pres.addSection({ title: 'Balance' });
// 13 balance
s = pres.addSlide({ masterName: 'CONTENIDO', sectionTitle: 'Balance' });
addTitle(s, 'Balance de los sprints 1 a 4');
stat(s, 'st_hecho', { x: 0.5, y: 1.2, w: 2.7, big: '10', label: 'tareas cumplen su criterio del plan', color: GREEN });
stat(s, 'st_limite', { x: 3.4, y: 1.2, w: 2.7, big: '6', label: 'hechas con límite demostrado: se midieron y el límite está escrito', color: 'B7791F', lh: 0.8 });
stat(s, 'st_menor', { x: 6.3, y: 1.2, w: 3.2, big: '3', label: 'entregables menores cerrados en el PR de cierre', color: C.text2, lh: 0.8 });
img(s, 'horas', 'horas_sprint.png', 0.5, 2.85, 4.6, 2.3, 'Horas planificadas y completadas por sprint');
card(s, 'avance', { x: 5.3, y: 2.95, w: 4.2, h: 2.1, title: 'Avance en horas', body: ['216 de 604 horas cerradas (≈ 36 %)', 'Sprints 3 y 4 completos y benchmarks adelantados', '263 pruebas automáticas, 255 pasan y 8 se omiten', '25 integraciones a la rama principal'], size: 12 });
check('avance', ['216 de 604 horas cerradas (≈ 36 %)', 'Sprints 3 y 4 completos y benchmarks adelantados', '263 pruebas automáticas, 255 pasan y 8 se omiten', '25 integraciones a la rama principal'], 3.9, 2.1 - 0.6, 13, false, 3);
s.addNotes('BALANCE (según el acta de cierre de los sprints 1 a 4, 19 de octubre). De 19 tareas: 10 cumplen su criterio (Hecho); 6 quedaron "hechas con límite demostrado" (2.1.1, 2.1.2, 2.2.2, 2.2.3, 2.2.4 y 2.2.5): se ejecutaron y se midieron, pero el resultado no alcanza el criterio ideal del plan o hay una desviación de diseño, y el límite quedó escrito con su causa; y 3 entregables menores (guía de contribución, prueba de concepto de ABIDES y lista de dependencias) que se cerraron en el pull request de cierre.\n\nAvance en horas: el plan de Título II suma 604 horas; hay 216 cerradas (sprint 3: 104, sprint 4: 96 y benchmarks adelantados: 16), cerca de 36%. El tiempo transcurrido desde el inicio del sprint 3 es cercano a 40%; las horas del sprint 5 se suman al cierre del sprint 23 de octubre.\n\nCalidad: 263 pruebas automáticas al 19 de octubre (255 pasan y 8 se omiten porque requieren archivos de mercado o ABIDES que solo existen en el entorno donde se generaron). 25 integraciones a la rama principal entre agosto y octubre (registro histórico elaborado por Mauricio).\n\nMensaje: la infraestructura completa para entrenar y evaluar el sistema está lista: datos, espacios, redes, PPO, orquestador, simulador calibrado, recompensas calibradas y benchmarks.');

// 14 quien hizo que
s = pres.addSlide({ masterName: 'CONTENIDO', sectionTitle: 'Balance' });
addTitle(s, 'Quién hizo qué');
card(s, 'mr', { x: 0.5, y: 1.2, w: 2.9, h: 3.85, title: 'Mauricio Reynoso', size: 14, th: 0.45, body: ['Repositorio y guía de Colab', 'Prueba de ABIDES-Gym y dependencias', 'Red del Maestro', 'PPO: L_CLIP y GAE', 'Recompensa del Maestro (λ = 0,05)'] });
card(s, 'bf', { x: 3.55, y: 1.2, w: 2.9, h: 3.85, title: 'Benjamín Farias', size: 14, th: 0.45, body: ['Descarga y limpieza de datos', 'Variables del Maestro', 'Calibración de Poisson por tramo', 'Redes de los Ejecutores', 'Recompensa de los Ejecutores', 'Calibración de rmsc04 y revisión de cierre'] });
card(s, 'ps', { x: 6.6, y: 1.2, w: 2.9, h: 3.85, title: 'Paolo Sepúlveda', size: 14, th: 0.45, body: ['Vectores S_M y S_E', 'Arquitectura del entorno', 'Espacios Gymnasium y simulador de Poisson', 'Validación formal del simulador', 'Fase 2 de β y benchmarks TWAP/VWAP', 'COPEC y ECL, y cierre de los sprints 1 a 4'] });
check('mr', ['Repositorio y guía de Colab', 'Prueba de ABIDES-Gym y dependencias', 'Red del Maestro', 'PPO: L_CLIP y GAE', 'Recompensa del Maestro (λ = 0,05)'], 2.6, 3.85 - 0.75, 14, false, 3);
check('bf', ['Descarga y limpieza de datos', 'Variables del Maestro', 'Calibración de Poisson por tramo', 'Redes de los Ejecutores', 'Recompensa de los Ejecutores', 'Calibración de rmsc04 y revisión de cierre'], 2.6, 3.85 - 0.75, 14, false, 3);
check('ps', ['Vectores S_M y S_E', 'Arquitectura del entorno', 'Espacios Gymnasium y simulador de Poisson', 'Validación formal del simulador', 'Fase 2 de β y benchmarks TWAP/VWAP', 'COPEC y ECL, y cierre de los sprints 1 a 4'], 2.6, 3.85 - 0.75, 14, false, 3);
s.addNotes('REPARTO DE TRABAJO. Mauricio Reynoso (MR): entorno y repositorio, guía de Colab, prueba de concepto de ABIDES-Gym y dependencias, red del Maestro, PPO con L_CLIP y GAE y calibración de λ.\n\nBenjamín Farias (BF): descarga de datos OHLCV, pipeline de limpieza y variables del Maestro, calibración de Poisson por tramo y su robustez, redes de los Ejecutores, recompensa de los Ejecutores (varianza causal normalizada y barrido de β), calibración de rmsc04 con 30 semillas, grilla de actividad baja y revisión formal del cierre del sprint 4.\n\nPaolo Sepúlveda (PS): vectores de estado, arquitectura del entorno, espacios Gymnasium y simulador de Poisson, sistema de registro y análisis, validación formal con 30 semillas (FALABELLA, COPEC y ECL), fase 2 de la elección de β, benchmarks TWAP y VWAP, sondeo de megashocks, calibración de COPEC y ECL y acta de cierre de los sprints 1 a 4.\n\nLas tareas compartidas (2.1.3, 2.2.3 y 2.2.4) se hicieron en equipo y cada pull request pasó por revisión antes de integrarse a la rama principal.');

// 15 próximos pasos
s = pres.addSlide({ masterName: 'CONTENIDO', sectionTitle: 'Balance' });
addTitle(s, 'Alcance actual y próximos pasos');
card(s, 'limites', { x: 0.5, y: 1.2, w: 4.4, h: 3.85, title: 'Alcance del simulador y de los resultados', size: 14, th: 0.5, tsize: 14, body: ['Aproxima la escala y el patrón del mercado; la distribución de retornos no es idéntica a la real', 'Spread simulado bajo y volumen alto en la apertura: se interpretan resultados relativos entre estrategias', 'λ y β son provisionales (β solo en la apertura)', 'Entrenamiento completo del sistema: sprints 5 y 6'] });
card(s, 'proximos', { x: 5.1, y: 1.2, w: 4.4, h: 3.85, title: 'Lo que viene', size: 14, th: 0.5, tsize: 14, fill: 'E6ECF8', body: ['Sprint 5 (hasta el 23 oct): integración CTDE, ciclo de entrenamiento, meta-órdenes y primer entrenamiento', 'Sprint 6: ajuste de hiperparámetros y evaluación por escenario de liquidez', 'Sprint 7: 90 corridas y comparación estadística con TWAP y VWAP', 'Sprints 8 y 9: memoria y defensa'] });
check('limites', ['Aproxima la escala y el patrón del mercado; la distribución de retornos no es idéntica a la real', 'Spread simulado bajo y volumen alto en la apertura: se interpretan resultados relativos entre estrategias', 'λ y β son provisionales (β solo en la apertura)', 'Entrenamiento completo del sistema: sprints 5 y 6'], 4.1, 3.85 - 0.8, 14, false, 3);
check('proximos', ['Sprint 5 (hasta el 23 oct): integración CTDE, ciclo de entrenamiento, meta-órdenes y primer entrenamiento', 'Sprint 6: ajuste de hiperparámetros y evaluación por escenario de liquidez', 'Sprint 7: 90 corridas y comparación estadística con TWAP y VWAP', 'Sprints 8 y 9: memoria y defensa'], 4.1, 3.85 - 0.8, 14, false, 3);
s.addNotes('CIERRE. Alcance: el simulador calibrado aproxima la escala de los retornos y el patrón entre tramos, pero no reproduce exactamente su distribución, y tiene un spread bajo y un volumen alto en la apertura. Por eso las conclusiones del proyecto se leerán como diferencias entre estrategias bajo las mismas condiciones simuladas. λ y β son provisionales y se revalidan al entrenar.\n\nLo que viene: Sprint 5 (12 a 23 de octubre): integración CTDE (comunicación Maestro-Ejecutores), ciclo de entrenamiento, meta-órdenes oficiales y primer entrenamiento de validación. Sprint 6 (26 octubre a 6 noviembre): ajuste de hiperparámetros, evaluación por escenario de liquidez y monitoreo de métricas. Sprint 7 (9 a 20 noviembre): 90 corridas de evaluación (3 niveles de liquidez, 3 tamaños, 10 semillas) y comparación estadística con TWAP y VWAP. Sprints 8 y 9: redacción de la memoria y defensa ante la comisión.\n\nFrase de cierre sugerida: "Al cierre del Sprint 4 el proyecto cuenta con la infraestructura completa para entrenar y evaluar el sistema, con sus límites medidos y documentados. Gracias."\n\nPreguntas probables y respuestas cortas:\n- ¿Por qué un Maestro y tres Ejecutores? Separa la planificación (cuánto y cuándo) de la ejecución táctica (cómo), y cada tramo horario tiene liquidez distinta.\n- ¿Por qué PPO? Es estable y simple de entrenar con acciones discretas.\n- ¿Por qué dos simuladores? ABIDES-Gym es el entorno final, pero es difícil de instalar y lento; el de Poisson permite probar localmente.\n- ¿Qué significa hecho con límite? Se ejecutó y se midió; el resultado no alcanza el criterio ideal y el límite queda escrito con su causa.\n- ¿Cuándo sabremos si el sistema supera a VWAP? Con las 90 corridas del Sprint 7.\n- ¿Usaron herramientas de IA? Sí, se usó Claude Code como apoyo de programación y redacción, y está declarado en la documentación del repositorio.');

pres.writeFile({ fileName: OUT }).then(async () => {
  await applyTheme(OUT, THEME);
  console.log('escrito', OUT);
  if (warns.length) { console.log('POSIBLES DESBORDES:'); warns.forEach((w) => console.log(' -', w)); } else console.log('sin desbordes estimados');
});
