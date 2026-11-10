// Apresentação corporativa "Indicadores de Merchandising" por GC – grade fixa
// Uso: node deck_corp.js deck_data.json "GC. AN" saida.pptx
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const [, , dataPath, GC, outPath] = process.argv;
const DATA = JSON.parse(fs.readFileSync(dataPath, "utf8"));
const D = DATA.gcs[GC];
if (!D) { console.error("GC não encontrada:", GC); process.exit(1); }

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


// ---------- encerramento: "OBRIGADO" (homem) / "OBRIGADA" (mulher) — cadastro do portal (generos.json), senão pelo primeiro nome ----------
function generoDe(chave, nome) {
  try { const g = JSON.parse(fs.readFileSync(path.join(process.env.CONFIG_DIR || path.join(__dirname, "..", "dados", "config"), "generos.json"), "utf8"))[chave]; if (g === "F" || g === "M") return g; } catch (_) {}
  const p = (nome || "").trim().split(/\s+/)[0].toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  const FEM = ["thais", "raquel", "isabel", "ines", "beatriz", "ruth", "ester", "carmen", "miriam", "ingrid", "karen", "rachel", "lais", "luiz" === p ? "" : "nicole", "dulce", "alice", "denise", "jaqueline", "aline", "simone", "michele", "gisele", "elaine", "viviane", "rosangela", "liz", "kelly", "suellen", "evelyn", "lucimar", "edinalva"];
  const MASC = ["luca", "joshua", "nikita", "jonatha", "elias"];
  return FEM.includes(p) || (p.endsWith("a") && !MASC.includes(p)) ? "F" : "M";
}
const encerramento = g => A(g === "F" ? "encerramento_obrigada.jpg" : "encerramento_obrigado.jpg");

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

// ================= 1. CAPA =================
{
  const s = pres.addSlide();
  s.addImage({ path: A("capa_base.jpg"), x: 0.083, y: 0, w: 13.146, h: 7.5 });
  s.addText([{ text: GC, options: { fontFace: FB, fontSize: 36, color: C.ink, breakLine: true } },
             { text: `${D.nome ? D.nome + "  ·  " : ""}${REF}`, options: { fontFace: F, fontSize: 14, color: C.ink2 } }],
            { x: 0.75, y: 4.35, w: 6.2, h: 1.05, margin: 0, valign: "middle" });
}

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

// ================= 3. INE GERAL (padrão ICE LATAM CANAL) =================
const Y_MID = 4.2;   // divisão gráfico (em cima) × tabela (embaixo)
{
  const s = novo("INE Geral", "RED vs ICE Latam por mês (nota ponderada por segmento) e desempenho por supervisor");
  const leg = [["FF0000", "RED"], ["808080", "ICE"]];
  const a = painel(s, { x: X0, w: CW }, Y_STRIP, Y_MID - Y_STRIP, "RED VS ICE LATAM", leg);
  barrasGrupo(s, { ...a }, M.map(r => r.lbl), [{ name: "RED", values: M.map(r => r.RED), cor: "FF0000" }, { name: "ICE", values: M.map(r => r.ICE), cor: "808080" }],
    { max: 105, gap: 40, fmt: v => fmt(v) });
  const meses = M.map(r => r.mes);
  const cab1 = [{ text: "Supervisor", options: { rowspan: 2 } }, { text: "Nome", options: { rowspan: 2 } }, ...M.map(r => ({ text: r.lbl, options: { colspan: 2 } }))];
  const cab2 = M.flatMap(() => ["RED", "ICE"]);
  const L = D.supervisores.filter(sv => sv.considerar !== false).map(sv => [{ text: sv.sv, options: { bold: true } }, sv.nome,
    ...meses.flatMap(m => { const ic = sv.meses[m]?.ICE; const corI = COMPR != null && ic != null ? (ic >= COMPR ? C.good : C.bad) : C.ink;
      return [{ text: fmt(sv.meses[m]?.RED), options: { align: "center" } }, { text: fmt(ic), options: { align: "center", color: corI, bold: COMPR != null && ic != null } }]; })]);
  const nm = meses.length;
  tabela(s, [cab1, cab2], L, { x: X0, y: Y_MID + G, w: CW, colW: ajusta([1.0, 0.95], CW, nm * 2), fs: nm > 4 ? 9 : 12, rowH: 0.31, mg: [0.03, 0.02, 0.03, 0.02], sep: Array.from({ length: nm }, (_, i) => 2 + i * 2) });
  if (COMPR != null) s.addText([{ text: "ICE em ", options: {} }, { text: "verde", options: { color: C.good, bold: true } }, { text: " = acima do compromisso · ", options: {} }, { text: "vermelho", options: { color: C.bad, bold: true } }, { text: " = abaixo", options: {} }],
    { x: X0, y: 6.72, w: CW, h: 0.22, fontFace: F, fontSize: 9, color: C.muted, margin: 0, align: "right" });
}

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

// ================= 4. ICE LATAM POR CANAL (padrão do PPT do Power BI) =================
if (D.canal) {
  const it = D.canal.itens, mes = MESES[+D.canal.mes.slice(5, 7)];
  const s = novo("ICE Latam canal", `Nota ICE Latam por segmento em ${mes} · linha = variação em p.p. vs mês anterior`);
  const a = painel(s, { x: X0, w: CW }, Y_STRIP, Y_END - Y_STRIP, "ICE LATAM CANAL", [["FF0000", "Nota ICE"], [C.ink, "Variação vs mês anterior", "solida"]]);
  barrasVariacao(s, { ...a, y: a.y + 0.1, h: a.h - 0.1 }, it.map(i => i.seg.replace(/MINIMERCADO \(AS (\d-\d)CK\)/, "AS $1").replace(/ \(.*\)/, "")), it.map(i => i.nota), it.map(i => i.var),
    { max: Math.max(105, ...it.map(i => i.nota)) * 1.02, dentro: true, gap: 25, catFs: 10, fmtV: v => fmt(v) + "%", fmtVar: v => fmt(v) + "%" });
}

// ================= 5. INE REPOSITOR (padrão ICE LATAM CANAL) =================
{
  const s = novo("INE Repositor", "Σ pontos realizados ÷ Σ pontos possíveis nas lojas com rota de repositor (sem peso de segmento)");
  const a = painel(s, { x: X0, w: CW }, Y_STRIP, Y_END - Y_STRIP, "RED VS ICE - REPOSITOR", [["FF0000", "RED repositor"], ["808080", "ICE repositor"]]);
  barrasGrupo(s, { ...a }, M.map(r => r.lbl), [{ name: "RED repositor", values: M.map(r => r.RED_rep), cor: "FF0000" }, { name: "ICE repositor", values: M.map(r => r.ICE_rep), cor: "808080" }],
    { max: 112, gap: 40, fmt: v => fmt(v) });
}

// ================= 6. PILAR DA FDS (padrão do PPT do Power BI) =================
if (D.pilar) {
  const it = D.pilar.itens, mes = MESES[+D.pilar.mes.slice(5, 7)];
  const s = novo("Pilar da FDS", `ICE Latam por pilar em ${mes} (ponderado por segmento, teto 110) · linha = variação vs mês anterior`);
  const a = painel(s, { x: X0, w: CW }, Y_STRIP, Y_END - Y_STRIP, "ICE LATAM PILAR", [["FF0000", "Nota do pilar"], [C.ink, "Variação vs mês anterior", "solida"]]);
  barrasVariacao(s, { x: a.x + 0.6, y: a.y + 0.45, w: a.w - 1.2, h: a.h - 0.45 }, it.map(i => i.kpi), it.map(i => i.nota), it.map(i => i.var),
    { max: 122, dentro: false, gap: 30, catFs: 12, fmtV: v => fmt(v), fmtVar: v => fmt(v) });
}

// ================= 7-9. PLANO DE AÇÃO (tela livre para preencher) =================
for (const n of [1, 2, 3]) novo(`Plano de ação ${n}`);

// ================= 10. SOVI PILARES FOCO =================
// SOVI = Σ frentes COCA COLA ÷ Σ frentes com fabricante (≠ "-") · SSD = refrigerante · Sabores = guaraná/laranja/uva/tônica · Sucos = suco
function soviSlide(s, linhas, rot, ins) {
  const SER = [["SSD", "SOVI SSD", "FF0000"], ["SAB", "SOVI SABORES", "E8702A"], ["SUC", "SOVI SUCOS", "1E88E5"]];
  if (!linhas.length) return vazio(s, "Sem base de SOVI para o período.");
  ins = ins || []; const wG = ins.length ? CW * 0.6 : CW;
  const a = painel(s, { x: X0, w: wG }, Y_STRIP, 3.55, "SOVI SSD, SABORES E SUCOS", ins.length ? [] : SER.map(([, n, c]) => [c, n, "solida"]));
  if (ins.length) {   // legenda compacta abaixo do título do painel + quadro de insights à direita
    s.addText(SER.map(([, n, c]) => ({ text: "━ " + n.replace("SOVI ", "") + "   ", options: { color: c } })), { x: a.x, y: Y_STRIP + 0.38, w: a.w, h: 0.2, fontFace: FB, fontSize: 9, margin: 0 });
    const ix = X0 + wG + G, iw = CW - wG - G;
    s.addShape(pres.ShapeType.rect, { x: ix, y: Y_STRIP, w: iw, h: 3.55, fill: { color: "FAFAFA" }, line: { color: C.line, width: 0.75 } });
    s.addShape(pres.ShapeType.rect, { x: ix, y: Y_STRIP, w: 0.07, h: 3.55, fill: { color: C.red }, line: { color: C.red, width: 0 } });
    s.addText("INSIGHTS · O QUE MOVEU O SOVI", { x: ix + 0.22, y: Y_STRIP + 0.12, w: iw - 0.3, h: 0.28, fontFace: FB, fontSize: 11, bold: true, color: C.ink, margin: 0, charSpacing: 1 });
    const runs = [];
    ins.slice(0, 4).forEach((t, i) => {
      runs.push({ text: t.tipo === "queda" ? "▼  " : "▲  ", options: { color: t.tipo === "queda" ? C.bad : C.good, bold: true, breakLine: false } });
      runs.push({ text: t.texto, options: { color: C.ink2, bold: !!t.destaque, breakLine: true, paraSpaceAfter: 6 } });
    });
    s.addText(runs, { x: ix + 0.22, y: Y_STRIP + 0.48, w: iw - 0.35, h: 3.0, fontFace: F, fontSize: 9.5, valign: "top", margin: 0 });
  }
  const labels = linhas.map(r => cap(r.lbl));
  // linhas sem rótulo automático; os rótulos são posicionados aqui, empilhados por mês com distância mínima (nunca se sobrepõem)
  const todos = linhas.flatMap(r => SER.map(([k]) => r[k])).filter(v => v != null);
  const lo = Math.max(0, Math.floor(Math.min(...todos) - 10)), hi = Math.min(100, Math.ceil(Math.max(...todos) + 8));
  const L = { x: 0.01, y: 0.08, w: 0.98, h: 0.80 };
  s.addChart(pres.ChartType.line, SER.map(([k, n]) => ({ name: n, labels, values: linhas.map(r => r[k] ?? null) })), {
    x: a.x, y: a.y, w: a.w, h: a.h, ...ax, layout: L, chartColors: SER.map(x => x[2]), lineSize: 2.5, lineDataSymbol: "circle", lineDataSymbolSize: 7,
    valAxisMinVal: lo, valAxisMaxVal: hi, showValue: false });
  const n = linhas.length, cw = a.w * L.w / n, lw = Math.min(0.78, cw - 0.06), lh = 0.21, gap = 0.03;
  const yTop = a.y + a.h * L.y, yBot = a.y + a.h * (L.y + L.h);
  const py = v => a.y + a.h * (L.y + L.h * (1 - (v - lo) / (hi - lo)));
  linhas.forEach((r, i) => {
    const cx = a.x + a.w * L.x + cw * (i + 0.5);
    const pts = SER.map(([k, , cor]) => ({ v: r[k], cor })).filter(p => p.v != null).map(p => ({ ...p, y: py(p.v) })).sort((p, q) => p.y - q.y);
    if (!pts.length) return;
    // posição desejada: o mais alto acima do ponto, o mais baixo abaixo, o do meio do lado com mais espaço
    pts.forEach((p, j) => {
      const acima = j === 0 ? true : j === pts.length - 1 ? false : (p.y - pts[j - 1].y) >= (pts[j + 1].y - p.y);
      p.ly = acima ? p.y - lh - 0.07 : p.y + 0.07;
    });
    // empilha sem sobreposição (de cima para baixo) e mantém dentro do gráfico
    for (let j = 1; j < pts.length; j++) pts[j].ly = Math.max(pts[j].ly, pts[j - 1].ly + lh + gap);
    const exced = pts[pts.length - 1].ly + lh - yBot;
    if (exced > 0) for (let j = pts.length - 1; j >= 0; j--) { pts[j].ly = Math.min(pts[j].ly, (j === pts.length - 1 ? yBot - lh : pts[j + 1].ly - lh - gap)); }
    if (pts[0].ly < yTop - 0.15) { const d = yTop - 0.15 - pts[0].ly; pts.forEach(p => p.ly += d); }
    pts.forEach(p => s.addText(fmt(p.v) + "%", { x: cx - lw / 2, y: p.ly, w: lw, h: lh, shape: pres.ShapeType.roundRect, rectRadius: 0.04,
      fill: { color: C.white }, line: { color: p.cor, width: 0.75 }, fontFace: FB, fontSize: 9, bold: true, color: p.cor, align: "center", valign: "middle", margin: 0 }));
  });
  const ab = linhas.map(r => cap(r.lbl).slice(0, 3));
  const cel = (v, ant) => ({ text: v == null ? "–" : fmt(v) + "%", options: { align: "center", color: v == null || ant == null ? C.ink : v >= ant ? C.good : C.bad } });
  tabela(s, [rot, ...ab], SER.map(([k, n]) => [n.replace("SOVI ", "SOVI "), ...linhas.map((r, i) => cel(r[k], i ? linhas[i - 1][k] : null))]),
    { x: X0, y: Y_STRIP + 3.55 + G, w: CW, colW: ajusta([1.9], CW, linhas.length), fs: 11, rowH: 0.36 });
  s.addText("SOVI = frentes Coca-Cola ÷ frentes totais · SSD = refrigerantes · Sabores = guaraná, laranja, uva e tônica · Sucos = sucos  ·  verde/vermelho = subiu/caiu vs mês anterior",
    { x: X0, y: 6.72, w: CW, h: 0.22, fontFace: F, fontSize: 9, color: C.muted, margin: 0 });
}
soviSlide(novo("SOVI pilares foco"), D.sovi || [], "GERÊNCIA " + GC);   // insights ficam na aba Insights do portal

// ================= 11. CPI (padrão ICE LATAM CANAL) =================
{
  const Cp = D.cpi;
  const s = novo("CPI: Cooler Profitability Index", "Real vs meta por mês · venda zero, instalação e perda de GDM");
  const a = painel(s, { x: X0, w: CW }, Y_STRIP, Y_MID - Y_STRIP, "CPI", [["BFBFBF", "Meta CPI"], ["FF0000", "Real CPI"]]);
  barrasGrupo(s, { ...a }, Cp.map(r => r.lbl), [{ name: "Meta CPI", values: Cp.map(r => r.meta), cor: "BFBFBF" }, { name: "Real CPI", values: Cp.map(r => r.real), cor: "FF0000" }],
    { min: 50, max: 101, gap: 30, catFs: 11, fmt: v => fmt(v) + "%" });
  const meses = Cp.map(r => cap(r.lbl).slice(0, 3));
  const lin = (nome, f, cor) => [{ text: nome, options: { bold: true, align: "left" } }, ...Cp.map(r => ({ text: f(r), options: { align: "center", ...(cor ? { color: cor(r), bold: true } : {}) } }))];
  tabela(s, ["GERÊNCIA " + GC, ...meses], [lin("Venda zero", r => String(r.vdz)), lin("Inst. GDM", r => String(r.inst)), lin("GDM perdida", r => String(r.perdida))],
    { x: X0, y: Y_MID + G, w: CW, colW: ajusta([2.0], CW, meses.length), fs: 12, rowH: 0.4 });
}

// ================= 12. TOM =================
{
  const T = D.tom;
  const s = novo("TOM: Treinamento Obrigatório Mensal", "Realização, data e tema do treinamento por mês");
  const sim = { text: "SIM", options: { align: "center", color: C.good, bold: true } }, nao = { text: "NÃO", options: { align: "center", color: C.bad, bold: true } };
  tabela(s, ["Gerência", "Mês", "Realizou TOM?", "Data", "Tema"], T.map(t => [{ text: GC, options: { align: "center" } }, t.lbl, t.realizou === "SIM" ? sim : nao, t.data, t.tema]),
    { x: X0, y: Y_STRIP, w: CW, colW: [1.3, 1.5, 1.7, 3.6, CW - 8.1], fs: 12, rowH: 0.42 });
}

// ================= 13. COMPROMISSO =================
{
  const s = novo("Compromisso", "Compromisso vs real · ICE Latam do mês frente ao compromisso da gerência");
  if (COMPR == null) vazio(s, "Gerência sem compromisso de ICE cadastrado.");
  else {
    const INICIO_COMPROMISSO = "2026-07";   // como no PPT do Power BI: compromisso acompanhado a partir de julho
    const L = M.filter(r => r.ICE != null && r.mes >= INICIO_COMPROMISSO);
    const cel = (v, o) => ({ text: v, options: { align: "center", ...o } });
    const linhas = L.map(r => { const x = r.ICE - COMPR, kk = x >= 0, cor = kk ? { fill: { color: C.good }, color: C.white, bold: true } : { fill: { color: C.badBg }, color: C.bad, bold: true };
      return [cel(GC), cel(r.lbl), cel(fmt(COMPR)), cel(fmt(r.ICE)), cel(sinal(x), { color: kk ? C.good : C.bad, bold: true }), cel(kk ? "✓  1 mil" : "✕  0", cor)]; });
    tabela(s, ["Gerência", "Mês", "Compromisso", "ICE", "DIF", "PLUS"], linhas, { x: X0, y: Y_STRIP, w: CW, colW: Array(6).fill(CW / 6), fs: 14, rowH: 0.5 });
  }
}

// ================= 14. RESUMO DE INDICADORES · PONTUAÇÃO (tabela premium desenhada) =================
{
  const s = novo("Pontuação");
  const meses = [...new Set([...M.map(r => r.mes), ...D.cpi.map(c => c.mes)])].sort();
  const rows = meses.map(m => {
    const r = M.find(x => x.mes === m) || {}, c = D.cpi.find(x => x.mes === m), t = D.tom.find(x => x.lbl === MESES[+m.slice(5, 7)]);
    return { m, ice: r.ICE, p: pontuacao(m, r.ICE, c, t, COMPR) };
  });
  const tot = rows.reduce((a, r) => a + r.p.total, 0);
  // ---- tabela (esquerda)
  const TW = CW, x0 = X0, y0 = Y_STRIP, hH = 0.46, hT = 0.5;
  const rh = Math.min(0.46, (Y_END - 0.35 - y0 - hH - hT) / rows.length);
  const col = [["MÊS", 2.4, "l"], ["ICE", 2.05], ["CPI", 2.05], ["TOM", 2.05], ["COMPROMISSO", 2.05], ["TOTAL", TW - 10.6]];
  let cx = x0; const X = col.map(c => { const r = { x: cx, w: c[1] }; cx += c[1]; return r; });
  // cabeçalho vermelho com cantos arredondados
  s.addShape(pres.ShapeType.roundRect, { x: x0, y: y0, w: TW, h: hH + 0.1, fill: { color: C.red }, line: { color: C.red }, rectRadius: 0.08 });
  col.forEach((c, i) => s.addText(c[0], { x: X[i].x + (c[2] ? 0.2 : 0), y: y0, w: X[i].w - (c[2] ? 0.2 : 0), h: hH, fontFace: FB, fontSize: 11, bold: true, color: C.white, align: c[2] ? "left" : "center", valign: "middle", margin: 0, charSpacing: 1 }));
  s.addShape(pres.ShapeType.rect, { x: x0, y: y0 + hH, w: TW, h: rh * rows.length, fill: { color: C.white }, line: { color: C.line, width: 0.75 } });
  const badge = (i, y, ok, pts) => {
    const bw = 0.7, bh = Math.min(0.27, rh - 0.1), bx = X[i].x + (X[i].w - bw) / 2, by = y + (rh - bh) / 2;
    if (ok == null) return s.addText("–", { x: X[i].x, y, w: X[i].w, h: rh, fontFace: F, fontSize: 11, color: C.grayL, align: "center", valign: "middle", margin: 0 });
    s.addShape(pres.ShapeType.roundRect, { x: bx, y: by, w: bw, h: bh, rectRadius: bh / 2, fill: { color: ok ? C.good : C.badBg }, line: { color: ok ? C.good : C.badBg } });
    s.addText(ok ? "✓" : "✕", { x: bx, y: by, w: bw, h: bh, fontFace: FB, fontSize: 13, bold: true, color: ok ? C.white : C.bad, align: "center", valign: "middle", margin: 0 });
  };
  rows.forEach((r, k) => {
    const y = y0 + hH + k * rh, atual = r.m === MES_ATUAL;
    if (k % 2) s.addShape(pres.ShapeType.rect, { x: x0 + 0.01, y, w: TW - 0.02, h: rh, fill: { color: "F7F7F7" }, line: { color: "F7F7F7", width: 0 } });
    if (atual) s.addShape(pres.ShapeType.rect, { x: x0 + 0.01, y, w: TW - 0.02, h: rh, fill: { color: "FFF1F1" }, line: { color: "FFF1F1", width: 0 } });
    if (k) s.addShape(pres.ShapeType.line, { x: x0 + 0.15, y, w: TW - 0.3, h: 0, line: { color: "E6E6E6", width: 0.75 } });
    if (atual) s.addShape(pres.ShapeType.rect, { x: x0 + 0.01, y, w: 0.06, h: rh, fill: { color: C.red }, line: { color: C.red, width: 0 } });
    s.addText(cap(MESES[+r.m.slice(5, 7)]), { x: X[0].x + 0.2, y, w: X[0].w - 0.2, h: rh, fontFace: atual ? FB : F, fontSize: 11.5, bold: atual, color: C.ink, valign: "middle", margin: 0 });
    badge(1, y, r.p.iceOk, PONTOS.ICE); badge(2, y, r.p.cpiOk, PONTOS.CPI); badge(3, y, r.p.tomOk, PONTOS.TOM); badge(4, y, r.p.plus, PONTOS.PLUS);
    const tx = X[5].x, tw = X[5].w;
    s.addText(r.p.total.toLocaleString("pt-BR"), { x: tx, y, w: tw - 0.3, h: rh, fontFace: FB, fontSize: 12.5, bold: true, color: C.ink, align: "right", valign: "middle", margin: 0 });
  });
  // linha de total
  const yT = y0 + hH + rows.length * rh + 0.08;
  s.addShape(pres.ShapeType.roundRect, { x: x0, y: yT, w: TW, h: hT, fill: { color: C.ink }, line: { color: C.ink }, rectRadius: 0.08 });
  s.addText(`TOTAL ACUMULADO ${MES_ATUAL.slice(0, 4)}`, { x: x0 + 0.2, y: yT, w: 5, h: hT, fontFace: FB, fontSize: 11, bold: true, color: C.white, valign: "middle", margin: 0, charSpacing: 1 });
  s.addText(`${tot.toLocaleString("pt-BR")} pts`, { x: X[5].x - 1, y: yT, w: X[5].w + 1 - 0.3, h: hT, fontFace: FB, fontSize: 14, bold: true, color: C.white, align: "right", valign: "middle", margin: 0 });

  s.addText(`Critérios: ICE = ICE Latam ≥ ${PONTOS.ICE_MIN} (5 mil)  ·  CPI = real ≥ meta (3 mil)  ·  TOM executado (2 mil)  ·  COMPROMISSO = ICE ≥ compromisso da GC (1 mil, a partir de julho)`,
    { x: X0, y: 6.72, w: CW, h: 0.22, fontFace: F, fontSize: 9, color: C.muted, margin: 0 });
}

// ================= 15. ENCERRAMENTO =================
pres.addSlide().addImage({ path: encerramento(generoDe(GC, D.nome)), x: 0.083, y: 0, w: 13.146, h: 7.5 });

pres.writeFile({ fileName: outPath }).then(() => console.log("ok", outPath));
