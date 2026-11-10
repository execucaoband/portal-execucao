// GERADO: apresentação consolidada do administrador (todas as GCs). Uso: node deck_resumo.js resumo_data.json saida.pptx
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const [, , dataPath, outPath] = process.argv;
const DATA = JSON.parse(fs.readFileSync(dataPath, "utf8"));
const GC = "RESULTADO GERAL";
const D = { nome: "Todas as gerências", compromisso: null, supervisores: [], cpi: [], tom: [],
  mensal: DATA.meses.map(m => ({ mes: m, lbl: ["", "janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"][+m.slice(5, 7)], ...DATA.empresa[m] })) };
// ================= identidade =================
const C = {
  red: "D7141E", ink: "1F1F1F", ink2: "404040", muted: "7F7F7F", gray: "8C8C8C", grayL: "BFBFBF",
  line: "D9D9D9", soft: "F4F4F4", white: "FFFFFF", good: "1E8E3E", bad: "C62828", goodBg: "E6F4EA", badBg: "FCE8E6",
};
const F = "Segoe UI", FB = "Segoe UI Semibold";
const MESES = ["", "janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"];
const MES_ATUAL = DATA.meses[DATA.meses.length - 1];
const cap = s => s ? s.charAt(0).toUpperCase() + s.slice(1) : s;
const REF = `${cap(MESES[+MES_ATUAL.slice(5, 7)])} ${MES_ATUAL.slice(0, 4)}`;
const A = p => path.join(__dirname, "assets", p);
const fmt = (v, d = 2) => v == null ? "–" : v.toFixed(d).replace(".", ",");
const sinal = v => v == null ? "–" : (v > 0 ? "+" : "") + fmt(v);

// ================= grade =================
const W = 13.333, X0 = 0.5, CW = W - 2 * X0, G = 0.25;
const Y_STRIP = 1.15, H_STRIP = 1.1, Y_BODY = Y_STRIP + H_STRIP + G, Y_END = 6.75, H_BODY = Y_END - Y_BODY;
const cols = (n, x = X0, w = CW) => { const cw = (w - G * (n - 1)) / n; return Array.from({ length: n }, (_, i) => ({ x: x + i * (cw + G), w: cw })); };
const split = (frac, x = X0, w = CW) => { const a = (w - G) * frac; return [{ x, w: a }, { x: x + a + G, w: w - G - a }]; };

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.title = `Indicadores de Merchandising - ${GC} - ${REF}`;
pres.author = "Planejamento de Merchandising";
pres.theme = { headFontFace: FB, bodyFontFace: F };

const BW = Math.max(1.3, GC.length * 0.105 + 0.35);   // largura do selo vermelho
pres.defineSlideMaster({
  title: "CONTEUDO",
  background: { color: C.white },
  objects: [
    { placeholder: { options: { name: "titulo", type: "title", x: X0, y: 0.35, w: 9.6, h: 0.55, fontFace: FB, fontSize: 26, color: C.ink, align: "left", valign: "middle", margin: 0 }, text: "" } },
    { rect: { x: W - X0 - BW, y: 0.45, w: BW, h: 0.36, fill: { color: C.red }, line: { color: C.red } } },
    { text: { text: GC, options: { x: W - X0 - BW, y: 0.45, w: BW, h: 0.36, fontFace: FB, fontSize: 12, color: C.white, align: "center", valign: "middle", margin: 0 } } },
    { line: { x: X0, y: 6.98, w: CW, h: 0, line: { color: C.line, width: 0.75 } } },
    { text: { text: `Indicadores de Merchandising  |  ${GC}  |  ${REF}`, options: { x: X0, y: 7.03, w: 7, h: 0.3, fontFace: F, fontSize: 9, color: C.muted, margin: 0, valign: "middle" } } },
    { image: { path: A("logos.png"), x: W - X0 - 0.5 - 1.95, y: 7.03, w: 1.95, h: 0.3 } },
  ],
  slideNumber: { x: W - X0 - 0.4, y: 7.03, w: 0.4, h: 0.3, fontFace: F, fontSize: 9, color: C.muted, align: "right" },
});
function novo(titulo, sub) {
  const s = pres.addSlide({ masterName: "CONTEUDO" });
  s.addText(titulo, { placeholder: "titulo" });
  return s;
}

// ================= regra de pontuação (Resumo de indicadores) =================
const PONTOS = { ICE_MIN: 75, ICE: 5000, CPI: 3000, TOM: 2000, PLUS: 1000, INICIO_PLUS: "2026-07" };
function pontuacao(mes, ice, cpi, tom, compromisso) {
  const iceOk = ice == null ? null : ice >= PONTOS.ICE_MIN, cpiOk = cpi == null ? null : cpi.real >= cpi.meta, tomOk = tom == null ? null : tom.realizou === "SIM";
  const plus = compromisso != null && ice != null && mes >= PONTOS.INICIO_PLUS ? ice >= compromisso : null;
  const total = (iceOk ? PONTOS.ICE : 0) + (cpiOk ? PONTOS.CPI : 0) + (tomOk ? PONTOS.TOM : 0) + (plus ? PONTOS.PLUS : 0);
  return { iceOk, cpiOk, tomOk, plus, total };
}

// ================= componentes =================
function kpi(s, b, rotulo, valor, detalhe, tom) {
  const y = Y_STRIP, h = H_STRIP;
  s.addShape(pres.ShapeType.rect, { x: b.x, y, w: b.w, h, fill: { color: C.white }, line: { color: C.line, width: 0.75 } });
  s.addText(rotulo.toUpperCase(), { x: b.x + 0.2, y: y + 0.1, w: b.w - 0.4, h: 0.26, fontFace: FB, fontSize: 10, color: C.muted, margin: 0, valign: "middle", charSpacing: 0.5 });
  s.addText(valor, { x: b.x + 0.2, y: y + 0.36, w: b.w - 0.4, h: 0.44, fontFace: FB, fontSize: 24, color: C.ink, margin: 0, valign: "middle", fit: "shrink" });
  if (detalhe) s.addText(detalhe, { x: b.x + 0.2, y: y + 0.8, w: b.w - 0.4, h: 0.24, fontFace: tom ? FB : F, fontSize: 10.5,
    color: tom === "good" ? C.good : tom === "bad" ? C.bad : C.ink2, margin: 0, valign: "middle" });
}
function painel(s, b, y, h, titulo, legenda) {
  s.addShape(pres.ShapeType.rect, { x: b.x, y, w: b.w, h, fill: { color: C.white }, line: { color: C.line, width: 0.75 } });
  s.addText(titulo, { x: b.x + 0.2, y: y + 0.12, w: b.w * 0.55, h: 0.3, fontFace: FB, fontSize: 13, color: C.ink, margin: 0, valign: "middle" });
  if (legenda) {
    let rx = b.x + b.w - 0.2;
    [...legenda].reverse().forEach(([cor, txt, tipo]) => {
      const tw = txt.length * 0.09 + 0.15;
      rx -= tw;
      s.addText(txt, { x: rx, y: y + 0.12, w: tw, h: 0.3, fontFace: F, fontSize: 11, color: C.ink2, margin: 0, valign: "middle" });
      if (tipo === "linha" || tipo === "solida") s.addShape(pres.ShapeType.line, { x: rx - 0.32, y: y + 0.27, w: 0.24, h: 0, line: { color: cor, width: 1.75, dashType: tipo === "linha" ? "dash" : "solid" } });
      else s.addShape(pres.ShapeType.rect, { x: rx - 0.26, y: y + 0.19, w: 0.16, h: 0.16, fill: { color: cor }, line: { color: cor } });
      rx -= 0.5;
    });
  }
  return { x: b.x + 0.2, y: y + 0.55, w: b.w - 0.4, h: h - 0.7 };
}
function tabela(s, cab, linhas, o) {
  // mesmo aspecto da tabela de Pontuação: cabeçalho vermelho arredondado (texto branco, caixa alta), linhas zebradas com filete fino,
  // linha de TOTAL (1ª célula começando com "Total") em faixa escura arredondada
  const none = { type: "none" }, fino = { type: "solid", pt: 0.75, color: "E6E6E6" }, sepV = { type: "solid", pt: 0.75, color: "E0E0E0" };
  const sepH = { type: "solid", pt: 0.75, color: "F08A8F" }, sep = new Set(o.sep || []), rh = o.rowH || 0.36;
  const hdrs = Array.isArray(cab[0]) ? cab : [cab];
  const txt = c => c !== null && typeof c === "object" ? String(c.text ?? "") : String(c ?? "");
  const temTotal = linhas.length > 0 && /^total/i.test(txt(linhas[linhas.length - 1][0]));
  // fundos desenhados (ficam por trás da tabela)
  s.addShape(pres.ShapeType.roundRect, { x: o.x, y: o.y, w: o.w, h: rh * hdrs.length, rectRadius: 0.08, fill: { color: C.red }, line: { color: C.red, width: 0 } });
  if (temTotal) s.addShape(pres.ShapeType.roundRect, { x: o.x, y: o.y + rh * (hdrs.length + linhas.length - 1), w: o.w, h: rh, rectRadius: 0.08, fill: { color: C.ink }, line: { color: C.ink, width: 0 } });
  const rows = hdrs.map((r, ri) => { let col = 0; return r.map(c => {
    const t = typeof c === "object" ? c : { text: c, options: {} };
    const ult = ri === hdrs.length - 1 || (t.options && t.options.rowspan);
    const { fill, color, ...resto } = t.options || {};
    const cell = { text: String(t.text ?? "").toUpperCase(), options: { color: C.white, bold: true, fontFace: FB,
      align: "center", valign: "middle", fontSize: (o.fs || 12) - (ri === 0 && hdrs.length > 1 ? 0.5 : 1.5),
      border: [none, none, ult ? none : sepH, sep.has(col) ? sepH : none], ...resto } };
    col += (t.options && t.options.colspan) || 1; return cell; }); });
  linhas.forEach((l, i) => {
    const tot = temTotal && i === linhas.length - 1, ultBody = i === linhas.length - (temTotal ? 2 : 1);
    rows.push(l.map((c, ci) => {
      const base = tot ? { color: C.white, bold: true, fontFace: FB, valign: "middle", border: [none, none, none, none] }
        : { fill: { color: i % 2 ? "F7F7F7" : C.white }, color: C.ink, valign: "middle", border: [none, none, ultBody && !temTotal ? { type: "solid", pt: 0.75, color: C.line } : fino, sep.has(ci) ? sepV : none] };
      if (ci === 0) base.bold = true;
      if (c !== null && typeof c === "object") {
        const op = { ...base, ...c.options };
        if (tot) { delete op.fill; op.color = C.white; }
        return { text: tot && ci === 0 ? String(c.text ?? "").toUpperCase() : c.text, options: op };
      }
      return { text: tot && ci === 0 ? String(c ?? "").toUpperCase() : String(c ?? ""), options: base };
    }));
  });
  s.addTable(rows, { x: o.x, y: o.y, w: o.w, colW: o.colW, fontFace: F, fontSize: o.fs || 12, rowH: rh, margin: o.mg || [0.04, 0.12, 0.04, 0.12] });
}
const ajusta = (fixos, wTotal, nVar) => { const resto = wTotal - fixos.reduce((a, b) => a + b, 0); return [...fixos, ...Array(nVar).fill(resto / nVar)]; };
const PLOT = { x: 0.01, y: 0.1, w: 0.98, h: 0.76 };
const ax = {
  layout: PLOT, showLegend: false, valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" }, valAxisLineShow: false,
  catAxisLineShow: true, catAxisLineColor: C.grayL, catAxisLabelFontFace: F, catAxisLabelFontSize: 12, catAxisLabelColor: C.ink,
  dataLabelFontFace: FB, dataLabelFontSize: 12, dataLabelColor: C.ink,
};
function selos(s, area, valores, sufixo = "") {
  const n = valores.length, y = area.y + area.h + 0.05, w = Math.min(1.1, area.w / n - 0.1);
  valores.forEach((v, i) => {
    if (v == null) return;
    const cx = area.x + area.w * (PLOT.x + PLOT.w * (i + 0.5) / n), up = v >= 0;
    s.addText(`${up ? "▲" : "▼"} ${sinal(v)}${sufixo}`, { x: cx - w / 2, y, w, h: 0.3, fontFace: FB, fontSize: 11, color: up ? C.good : C.bad,
      fill: { color: up ? C.goodBg : C.badBg }, align: "center", valign: "middle", margin: 0 });
  });
}
const vazio = (s, msg) => s.addText(msg, { x: X0, y: 3.5, w: CW, h: 0.5, fontFace: F, fontSize: 14, color: C.grayL, align: "center", italic: true });

const M = D.mensal, atual = M[M.length - 1], ant = M.length > 1 ? M[M.length - 2] : null;
const dif = k => atual?.[k] != null && ant?.[k] != null ? atual[k] - ant[k] : null;
const tom = v => v == null ? null : v >= 0 ? "good" : "bad";
const txtDif = v => v == null ? "sem mês anterior" : `${v >= 0 ? "▲" : "▼"} ${sinal(v)} p.p. vs ${ant.lbl}`;
const COMPR = D.compromisso;

// ---------- barras agrupadas no padrão ICE LATAM CANAL (rótulo em caixa branca no topo da barra) ----------
function barrasGrupo(s, area, labels, series, o) {
  const n = labels.length, ns = series.length, P = { x: 0.01, y: 0.04, w: 0.98, h: 0.76 }, gap = o.gap ?? 25, maxV = o.max;
  const tipos = [{ type: pres.ChartType.bar, data: series.map(se => ({ name: se.name, labels, values: se.values })),
    options: { barDir: "col", barGapWidthPct: gap, chartColors: series.map(se => se.cor), showValue: false } }];
  if (o.linha) tipos.push({ type: pres.ChartType.line, data: [{ name: o.linha.name, labels, values: labels.map(() => o.linha.valor) }],
    options: { chartColors: [o.linha.cor || "FF0000"], lineSize: 2.25, lineDataSymbol: "none", showValue: false } });
  s.addChart(tipos, { ...area, layout: P, showLegend: false, valAxisHidden: true, valAxisMinVal: o.min || 0, valAxisMaxVal: maxV,
    valGridLine: { style: "none" }, catGridLine: { style: "none" }, valAxisLineShow: false, catAxisLineShow: false,
    catAxisLabelFontFace: FB, catAxisLabelFontSize: o.catFs || 11, catAxisLabelColor: C.ink, catAxisLabelFontBold: true, catAxisLabelFrequency: 1 });
  const cw = area.w * P.w / n, bw = cw / (ns + gap / 100);
  const yv = v => area.y + area.h * (P.y + P.h * (1 - (Math.min(v, maxV) - (o.min || 0)) / (maxV - (o.min || 0))));
  const lw = Math.min(bw * 0.96, 1.25), fs = o.fs || (lw < 0.45 ? 8 : lw < 0.62 ? 9.5 : 12);
  series.forEach((se, j) => se.values.forEach((v, i) => {
    if (v == null) return;
    const cx = area.x + area.w * P.x + cw * i + bw * gap / 200 + bw * (j + 0.5);
    s.addText(o.fmt(v), { x: cx - lw / 2, y: yv(v) + 0.1, w: lw, h: 0.27, shape: pres.ShapeType.roundRect, rectRadius: 0.05,
      fill: { color: C.white }, line: { color: C.white }, fontFace: FB, fontSize: fs, color: C.ink, align: "center", valign: "middle", margin: 0 });
  }));
  if (o.linha) labels.forEach((_, i) => {
    const cx = area.x + area.w * P.x + cw * (i + 0.5);
    s.addText(o.fmt(o.linha.valor), { x: cx - 0.45, y: yv(o.linha.valor) - 0.33, w: 0.9, h: 0.26, fontFace: FB, fontSize: 11, color: C.ink, align: "center", valign: "middle", margin: 0 });
  });
}

const Y_MID = 4.2;
// ---------- visual no padrão do PPT do Power BI: barras + linha de variação com rótulos em caixa ----------
function barrasVariacao(s, area, labels, valores, vars, o) {
  const n = labels.length, maxV = o.max, P = { x: 0.01, y: 0.04, w: 0.98, h: 0.84 };
  s.addChart(pres.ChartType.bar, [{ name: "ICE", labels, values: valores }], {
    ...area, layout: P, barDir: "col", barGapWidthPct: o.gap || 25, chartColors: [o.cor || "FF0000"], showValue: false, showLegend: false,
    valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: maxV, valGridLine: { style: "none" }, catGridLine: { style: "none" }, valAxisLineShow: false,
    catAxisLineShow: false, catAxisLabelFontFace: FB, catAxisLabelFontSize: o.catFs || 11, catAxisLabelColor: C.ink, catAxisLabelFontBold: true, catAxisLabelFrequency: 1 });
  const cx = i => area.x + area.w * (P.x + P.w * (i + 0.5) / n);
  const topo = v => area.y + area.h * (P.y + P.h * (1 - Math.min(v, maxV) / maxV));
  const base = area.y + area.h * (P.y + P.h);
  const bw = Math.min(1.25, area.w * 0.98 / n * 0.72), lfs = bw < 0.7 ? 9.5 : 12;
  // rótulo do valor: dentro do topo da barra (caixa branca) ou acima da barra
  valores.forEach((v, i) => {
    if (v == null) return;
    const y = o.dentro ? topo(v) + 0.12 : topo(v) - 0.34;
    s.addText(o.fmtV(v), { x: cx(i) - bw / 2, y, w: bw, h: 0.28, fontFace: FB, fontSize: lfs, color: C.ink, align: "center", valign: "middle", margin: 0,
      ...(o.dentro ? { shape: pres.ShapeType.roundRect, rectRadius: 0.06, fill: { color: C.white }, line: { color: C.white } } : {}) });
  });
  // linha de variação (preta) na faixa inferior das barras
  const lv = vars.map(v => v == null ? null : v), lim = Math.max(1, ...lv.filter(v => v != null).map(Math.abs)) * 1.15;
  const band = { x: area.x, y: base - 1.15, w: area.w, h: 1.0 };
  s.addChart(pres.ChartType.line, [{ name: "Variação", labels, values: lv.map(v => v ?? 0) }], {
    ...band, layout: { x: P.x, y: 0, w: P.w, h: 1 }, chartColors: [C.ink], lineSize: 2.25, lineDataSymbol: "none", showLegend: false, showValue: false,
    valAxisHidden: true, catAxisHidden: true, valAxisMinVal: -lim, valAxisMaxVal: lim, valGridLine: { style: "none" }, catGridLine: { style: "none" },
    catAxisLineShow: false, valAxisLineShow: false });
  lv.forEach((v, i) => {
    if (v == null) return;
    const y = band.y + band.h * (1 - (v + lim) / (2 * lim));
    s.addText(o.fmtVar(v), { x: cx(i) - bw / 2, y: y - 0.36, w: bw, h: 0.28, shape: pres.ShapeType.roundRect, rectRadius: 0.06,
      fill: { color: C.white }, line: { color: "BFBFBF", width: 0.75 }, fontFace: FB, fontSize: lfs, color: v >= 0 ? C.good : C.bad, align: "center", valign: "middle", margin: 0 });
  });
}

