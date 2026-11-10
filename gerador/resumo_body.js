// ---------- encerramento: "OBRIGADO" (homem) / "OBRIGADA" (mulher) — cadastro do portal (generos.json), senão pelo primeiro nome ----------
function generoDe(chave, nome) {
  try { const g = JSON.parse(fs.readFileSync(path.join(process.env.CONFIG_DIR || path.join(__dirname, "..", "dados", "config"), "generos.json"), "utf8"))[chave]; if (g === "F" || g === "M") return g; } catch (_) {}
  const p = (nome || "").trim().split(/\s+/)[0].toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  const FEM = ["thais", "raquel", "isabel", "ines", "beatriz", "ruth", "ester", "carmen", "miriam", "ingrid", "karen", "rachel", "lais", "luiz" === p ? "" : "nicole", "dulce", "alice", "denise", "jaqueline", "aline", "simone", "michele", "gisele", "elaine", "viviane", "rosangela", "liz", "kelly", "suellen", "evelyn", "lucimar", "edinalva"];
  const MASC = ["luca", "joshua", "nikita", "jonatha", "elias"];
  return FEM.includes(p) || (p.endsWith("a") && !MASC.includes(p)) ? "F" : "M";
}
const encerramento = g => A(g === "F" ? "encerramento_obrigada.jpg" : "encerramento_obrigado.jpg");

// ================= APRESENTAÇÃO DO ADMINISTRADOR – RESULTADO GERAL (empresa, sem abertura por GC) =================
const GCS = Object.keys(DATA.gcs);
const mA = MES_ATUAL, mesA = MESES[+mA.slice(5, 7)];
const E = m => DATA.empresa[m] || {};
const MS = DATA.meses;

// 1. Capa
{
  const s = pres.addSlide();
  s.addImage({ path: A("capa_base.jpg"), x: 0.083, y: 0, w: 13.146, h: 7.5 });
  s.addText([{ text: "RESULTADO GERAL", options: { fontFace: FB, fontSize: 36, color: C.ink, breakLine: true } },
             { text: `Comercial Bandeirantes  ·  ${REF}`, options: { fontFace: F, fontSize: 14, color: C.ink2 } }],
            { x: 0.75, y: 4.35, w: 6.2, h: 1.05, margin: 0, valign: "middle" });
}

// 2. Painel de indicadores (empresa × mês)
{
  const s = novo("Painel de indicadores");
  const ab = MS.map(m => cap(MESES[+m.slice(5, 7)]).slice(0, 3));
  const lin = (nome, f, cor) => [nome, ...MS.map(m => { const v = f(E(m), m); return { text: v ?? "–", options: { align: "center", ...(cor ? { color: cor(E(m)) ?? C.ink, bold: true } : {}) } }; })];
  const pct = v => v == null ? null : fmt(v);
  tabela(s, ["Indicador", ...ab], [
    lin("ICE Latam", e => pct(e.ICE), e => e.ICE == null ? null : e.ICE >= PONTOS.ICE_MIN ? C.good : C.bad),
    lin("RED", e => pct(e.RED)),
    lin("RED repositor", e => pct(e.RED_rep)),
    lin("ICE repositor", e => pct(e.ICE_rep)),
    lin("CPI real", e => e.cpi_real == null ? null : fmt(e.cpi_real) + "%", e => e.cpi_real == null ? null : e.cpi_real >= e.cpi_meta ? C.good : C.bad),
    lin("Meta CPI", e => e.cpi_meta == null ? null : fmt(e.cpi_meta) + "%"),
    lin("Venda zero", e => e.vdz == null ? null : String(e.vdz)),
    lin("Instalação GDM", e => e.inst == null ? null : String(e.inst)),
    lin("GDM perdida", e => e.perdida == null ? null : String(e.perdida)),
    lin("TOM executado", e => e.tom_total ? `${e.tom_sim}/${e.tom_total}` : null, e => e.tom_total ? (e.tom_sim === e.tom_total ? C.good : C.bad) : null),
    lin("GCs no compromisso", (e, m) => m >= PONTOS.INICIO_PLUS && e.compr_total ? `${e.compr_ok}/${e.compr_total}` : null)],
    { x: X0, y: Y_STRIP, w: CW, colW: ajusta([2.2], CW, MS.length), fs: 12, rowH: 0.43 });
  s.addText(`ICE Latam e CPI em verde = dentro do critério de pontuação (ICE ≥ ${PONTOS.ICE_MIN}; CPI real ≥ meta)`, { x: X0, y: 6.7, w: CW, h: 0.24, fontFace: F, fontSize: 9.5, color: C.muted, margin: 0 });
}

// 2b. Comparativo por gerência (visão executiva) e destaques do mês
const IND = (() => {
  const mAnt = MS[MS.indexOf(mA) - 1];
  const val = (g, m) => { const G = DATA.gcs[g], r = G.mensal.find(x => x.mes === m) || {}, c = G.cpi.find(x => x.mes === m), sv = (G.sovi || []).find(x => x.mes === m) || {},
      t = G.tom.find(x => x.lbl === MESES[+m.slice(5, 7)]);
    return { ICE: r.ICE, RED: r.RED, RED_rep: r.RED_rep, ICE_rep: r.ICE_rep, CPI: c ? c.real : null, CPI_gap: c ? c.real - c.meta : null, SSD: sv.SSD, SAB: sv.SAB, SUC: sv.SUC,
      TOM: t ? t.realizou === "SIM" : null, PTS: pontuacao(m, r.ICE, c, t, G.compromisso).total }; };
  return { mAnt, val, lista: GCS.filter(g => (DATA.gcs[g].mensal.find(x => x.mes === mA) || {}).ICE != null || (DATA.gcs[g].mensal.find(x => x.mes === mA) || {}).RED != null) };
})();
{
  const s = novo(`Comparativo por gerência · ${cap(mesA)}`);
  const v = g => IND.val(g, mA), va = g => IND.mAnt ? IND.val(g, IND.mAnt) : {};
  const L = IND.lista.map(g => ({ g, a: v(g), b: va(g) })).sort((x, y) => (y.a.PTS - x.a.PTS) || ((y.a.ICE ?? -1) - (x.a.ICE ?? -1)));
  const dl = (a, b) => a == null || b == null ? "" : `  ${a - b >= 0 ? "▲" : "▼"}${fmt(Math.abs(a - b), 1)}`;
  const c = (a, b, ok, txt) => ({ text: a == null ? "–" : (txt ?? fmt(a)) + dl(a, b), options: { align: "center", color: a == null ? C.muted : ok == null ? C.ink : ok ? C.good : C.bad, bold: ok != null } });
  tabela(s, ["Gerência", "Gerente comercial", "ICE Latam", "RED", "RED rep.", "ICE rep.", "CPI", "SOVI SSD", "TOM", "Pontos"], L.map(({ g, a, b }) => [
    g, { text: DATA.gcs[g].nome || "–", options: { fontSize: 9 } }, c(a.ICE, b.ICE, a.ICE == null ? null : a.ICE >= PONTOS.ICE_MIN), c(a.RED, b.RED, null), c(a.RED_rep, b.RED_rep, null), c(a.ICE_rep, b.ICE_rep, null),
    c(a.CPI, b.CPI, a.CPI_gap == null ? null : a.CPI_gap >= 0, a.CPI == null ? null : fmt(a.CPI) + "%"), c(a.SSD, b.SSD, null, a.SSD == null ? null : fmt(a.SSD) + "%"),
    { text: a.TOM == null ? "–" : a.TOM ? "✓" : "✕", options: { align: "center", bold: true, color: a.TOM ? C.good : C.bad } },
    { text: a.PTS.toLocaleString("pt-BR"), options: { align: "center", bold: true } }]),
    { x: X0, y: Y_STRIP, w: CW, colW: [0.95, 2.35, 1.3, 1.15, 1.15, 1.15, 1.3, 1.25, 0.65, CW - 11.25], fs: 9.5, rowH: Math.min(0.32, 5.4 / (L.length + 1)) });
  s.addText(`Ordenado por pontos do mês · ▲▼ variação vs ${IND.mAnt ? MESES[+IND.mAnt.slice(5, 7)] : "mês anterior"} · ICE em verde = ≥ ${PONTOS.ICE_MIN} · CPI em verde = na meta`,
    { x: X0, y: 6.72, w: CW, h: 0.22, fontFace: F, fontSize: 9, color: C.muted, margin: 0 });
}
{
  const s = novo(`Destaques do mês · ${cap(mesA)}`);
  const K = [["ICE", "ICE Latam"], ["RED", "RED"], ["RED_rep", "RED repositor"], ["ICE_rep", "ICE repositor"], ["CPI", "CPI real"], ["SSD", "SOVI SSD"], ["SAB", "SOVI Sabores"], ["SUC", "SOVI Sucos"]];
  const nomeG = g => g.replace("GC. ", "");
  const linhas = K.map(([k, n]) => {
    const vs = IND.lista.map(g => ({ g, a: IND.val(g, mA)[k], b: IND.mAnt ? IND.val(g, IND.mAnt)[k] : null })).filter(x => x.a != null);
    if (!vs.length) return null;
    const best = vs.reduce((x, y) => y.a > x.a ? y : x), worst = vs.reduce((x, y) => y.a < x.a ? y : x);
    const d = vs.filter(x => x.b != null).map(x => ({ ...x, d: x.a - x.b }));
    const up = d.length ? d.reduce((x, y) => y.d > x.d ? y : x) : null, dn = d.length ? d.reduce((x, y) => y.d < x.d ? y : x) : null;
    const t = (x, cor, extra) => ({ text: x ? `${nomeG(x.g)}  ${extra}` : "–", options: { align: "center", color: cor, bold: true } });
    return [n, t(best, C.good, fmt(best.a)), t(worst, C.bad, fmt(worst.a)), t(up && up.d > 0 ? up : null, C.good, up ? `▲ ${fmt(up.d)}` : ""), t(dn && dn.d < 0 ? dn : null, C.bad, dn ? `▼ ${fmt(Math.abs(dn.d))}` : "")];
  }).filter(Boolean);
  tabela(s, ["Indicador", "Melhor gerência", "Pior gerência", "Maior alta no mês", "Maior queda no mês"], linhas, { x: X0, y: Y_STRIP, w: CW, colW: [2.33, 2.5, 2.5, 2.5, 2.5], fs: 12, rowH: 0.5 });
  s.addText(`Altas e quedas em pontos percentuais vs ${IND.mAnt ? MESES[+IND.mAnt.slice(5, 7)] : "mês anterior"} · apenas gerências com pesquisa no mês`, { x: X0, y: 6.72, w: CW, h: 0.22, fontFace: F, fontSize: 9, color: C.muted, margin: 0 });
}

// 3. INE Geral – RED vs ICE (empresa)
{
  const s = novo("INE Geral");
  const a = painel(s, { x: X0, w: CW }, Y_STRIP, Y_END - Y_STRIP, "RED VS ICE LATAM", [["FF0000", "RED"], ["808080", "ICE"]]);
  barrasGrupo(s, { ...a }, M.map(r => r.lbl), [{ name: "RED", values: M.map(r => r.RED), cor: "FF0000" }, { name: "ICE", values: M.map(r => r.ICE), cor: "808080" }],
    { max: 105, gap: 40, fmt: v => fmt(v) });
}

// 4. ICE Latam canal (empresa)
{
  const it = DATA.empresa_canal.itens;
  const s = novo("ICE Latam canal");
  const a = painel(s, { x: X0, w: CW }, Y_STRIP, Y_END - Y_STRIP, `ICE LATAM CANAL · ${mesA.toUpperCase()}`, [["FF0000", "Nota ICE"], [C.ink, "Variação vs mês anterior", "solida"]]);
  barrasVariacao(s, { ...a, y: a.y + 0.1, h: a.h - 0.1 }, it.map(i => i.seg.replace(/ \(.*\)/, "")), it.map(i => i.nota), it.map(i => i.var),
    { max: 108, dentro: true, gap: 25, catFs: 9, fmtV: v => fmt(v) + "%", fmtVar: v => fmt(v) + "%" });
}

// 5. Pilar da FDS (empresa)
{
  const it = DATA.empresa_pilar.itens;
  const s = novo("Pilar da FDS");
  const a = painel(s, { x: X0, w: CW }, Y_STRIP, Y_END - Y_STRIP, `ICE LATAM PILAR · ${mesA.toUpperCase()}`, [["FF0000", "Nota do pilar"], [C.ink, "Variação vs mês anterior", "solida"]]);
  barrasVariacao(s, { x: a.x + 0.6, y: a.y + 0.45, w: a.w - 1.2, h: a.h - 0.45 }, it.map(i => i.kpi), it.map(i => i.nota), it.map(i => i.var),
    { max: 122, dentro: false, gap: 30, catFs: 12, fmtV: v => fmt(v), fmtVar: v => fmt(v) });
}

// 6. INE Repositor (empresa)
{
  const s = novo("INE Repositor");
  const a = painel(s, { x: X0, w: CW }, Y_STRIP, Y_END - Y_STRIP, "RED VS ICE - REPOSITOR", [["FF0000", "RED repositor"], ["808080", "ICE repositor"]]);
  barrasGrupo(s, { ...a }, M.map(r => r.lbl), [{ name: "RED", values: M.map(r => r.RED_rep), cor: "FF0000" }, { name: "ICE", values: M.map(r => r.ICE_rep), cor: "808080" }],
    { max: 112, gap: 40, fmt: v => fmt(v) });
}

// 6b. SOVI pilares foco (empresa)
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
soviSlide(novo("SOVI pilares foco"), MS.filter(m => E(m).sovi_SSD != null).map(m => ({ mes: m, lbl: MESES[+m.slice(5, 7)], SSD: E(m).sovi_SSD, SAB: E(m).sovi_SAB, SUC: E(m).sovi_SUC })), "EMPRESA");

// 7. CPI (empresa)
{
  const s = novo("CPI: Cooler Profitability Index");
  const ms = MS.filter(m => E(m).cpi_real != null);
  const a = painel(s, { x: X0, w: CW }, Y_STRIP, Y_MID - Y_STRIP, "CPI", [["BFBFBF", "Meta CPI"], ["FF0000", "Real CPI"]]);
  barrasGrupo(s, { ...a }, ms.map(m => MESES[+m.slice(5, 7)]), [{ name: "Meta", values: ms.map(m => E(m).cpi_meta), cor: "BFBFBF" }, { name: "Real", values: ms.map(m => E(m).cpi_real), cor: "FF0000" }],
    { min: 50, max: 101, gap: 30, catFs: 11, fmt: v => fmt(v) + "%" });
  const ab = ms.map(m => cap(MESES[+m.slice(5, 7)]).slice(0, 3));
  const l = (n, k) => [n, ...ms.map(m => ({ text: String(E(m)[k] ?? "–"), options: { align: "center" } }))];
  tabela(s, ["Empresa", ...ab], [l("Venda zero", "vdz"), l("Instalação GDM", "inst"), l("GDM perdida", "perdida")], { x: X0, y: Y_MID + G, w: CW, colW: ajusta([2.0], CW, ms.length), fs: 12, rowH: 0.4 });
}

// 8. TOM e Compromisso (empresa)
{
  const s = novo("TOM e Compromisso");
  const temas = m => [...new Set(GCS.map(g => DATA.gcs[g].tom.find(t => t.lbl === MESES[+m.slice(5, 7)])?.tema).filter(Boolean))].join(" / ");
  const L = MS.map(m => { const e = E(m), tomOk = e.tom_total && e.tom_sim === e.tom_total;
    return [cap(MESES[+m.slice(5, 7)]), { text: e.tom_total ? `${e.tom_sim} de ${e.tom_total}` : "–", options: { align: "center", bold: true, color: tomOk ? C.good : C.bad } }, temas(m) || "–",
      { text: m >= PONTOS.INICIO_PLUS && e.compr_total ? `${e.compr_ok} de ${e.compr_total}` : "–", options: { align: "center", bold: true } }]; });
  tabela(s, ["Mês", "Gerências com TOM executado", "Tema do TOM", "Gerências no compromisso de ICE"], L, { x: X0, y: Y_STRIP, w: CW, colW: [1.6, 2.8, CW - 7.6, 3.2], fs: 12, rowH: 0.44 });
}

// 9. Resumo de indicadores – pontuação (empresa)
{
  const s = novo("Resumo de indicadores");
  const pts = m => GCS.map(g => { const r = DATA.gcs[g].mensal.find(x => x.mes === m) || {}, c = DATA.gcs[g].cpi.find(x => x.mes === m), t = DATA.gcs[g].tom.find(x => x.lbl === MESES[+m.slice(5, 7)]);
    return pontuacao(m, r.ICE, c, t, DATA.gcs[g].compromisso); });
  const ok = (v, p) => v == null ? { text: "–", options: { align: "center", color: C.muted } } : { text: v ? "✓" : "✕", options: { align: "center", bold: true, fontSize: 13, color: v ? C.white : C.bad, fill: { color: v ? C.good : C.badBg } } };
  const L = MS.map(m => { const e = E(m), p = pontuacao(m, e.ICE, e.cpi_real != null ? { real: e.cpi_real, meta: e.cpi_meta } : null, e.tom_total ? { realizou: e.tom_sim === e.tom_total ? "SIM" : "NÃO" } : null, null);
    const g = pts(m), med = g.reduce((a, b) => a + b.total, 0) / g.length, max11 = g.filter(x => x.total >= 11000).length, max10 = g.filter(x => x.total >= 10000).length;
    return [cap(MESES[+m.slice(5, 7)]), { text: fmt(e.ICE), options: { align: "center" } }, ok(p.iceOk, PONTOS.ICE), ok(p.cpiOk, PONTOS.CPI), ok(p.tomOk, PONTOS.TOM),
      { text: p.total.toLocaleString("pt-BR"), options: { align: "center", bold: true } }, { text: Math.round(med).toLocaleString("pt-BR"), options: { align: "center" } },
      { text: `${max10} de ${g.length}`, options: { align: "center" } }]; });
  const somaE = MS.reduce((a, m) => { const e = E(m); return a + pontuacao(m, e.ICE, e.cpi_real != null ? { real: e.cpi_real, meta: e.cpi_meta } : null, e.tom_total ? { realizou: e.tom_sim === e.tom_total ? "SIM" : "NÃO" } : null, null).total; }, 0);
  const somaMed = MS.reduce((a, m) => a + pts(m).reduce((x, y) => x + y.total, 0) / GCS.length, 0);
  const c = t => ({ text: t, options: { align: "center" } });
  L.push([{ text: `Total acumulado ${mA.slice(0, 4)}`, options: { colspan: 5 } }, c(somaE.toLocaleString("pt-BR")), c(Math.round(somaMed).toLocaleString("pt-BR")), c("")]);
  tabela(s, ["Mês", "ICE Latam", `ICE ≥ ${PONTOS.ICE_MIN}`, "CPI ≥ meta", "TOM (todas as GCs)", "Total empresa", "Média por gerência", "GCs com 10 mil ou mais"], L,
    { x: X0, y: Y_STRIP, w: CW, colW: [1.4, 1.2, 1.75, 1.75, 1.95, 1.4, 1.45, CW - 10.9], fs: 11.5, rowH: 0.43 });
  s.addText("Pontuação: ICE Latam ≥ 85 = 5 mil · CPI real ≥ meta = 3 mil · TOM executado = 2 mil · ICE ≥ compromisso = +1 mil por gerência (a partir de julho)",
    { x: X0, y: 6.7, w: CW, h: 0.24, fontFace: F, fontSize: 9.5, color: C.muted, margin: 0 });
}

// 10. Ranking de gerentes (mês + anual) – pessoa com 2 GCs = média das GCs; empate → melhor ICE Latam
{
  const PREMIOS = [7500, 5000, 3000];
  const avg = a => a.length ? a.reduce((x, y) => x + y, 0) / a.length : null;
  const ptsGC = (g, m) => { const G = DATA.gcs[g], r = G.mensal.find(x => x.mes === m) || {};
    return { pts: pontuacao(m, r.ICE, G.cpi.find(x => x.mes === m), G.tom.find(x => x.lbl === MESES[+m.slice(5, 7)]), G.compromisso).total, ice: r.ICE }; };
  const pess = (DATA.usuarios || []).filter(u => u.perfil === "gerente" && u.gcs.some(g => DATA.gcs[g]));
  const pp = (u, m) => { const v = u.gcs.filter(g => DATA.gcs[g]).map(g => ptsGC(g, m)).filter(x => x.ice != null); return { pts: avg(v.map(x => x.pts)), ice: avg(v.map(x => x.ice).filter(x => x != null)) }; };
  const ord = (a, b) => b.pts - a.pts || (b.ice ?? -1) - (a.ice ?? -1);
  const RM = pess.map(u => ({ u, ...pp(u, mA) })).sort(ord);
  const ms = MS.filter(m => m.slice(0, 4) === mA.slice(0, 4) && m <= mA);
  const RA = pess.map(u => { const r = ms.map(m => pp(u, m)); return { u, pts: r.reduce((s, z) => s + (z.pts || 0), 0), ice: avg(r.map(z => z.ice).filter(x => x != null)) }; }).sort(ord);
  const emp = (L, i) => (i > 0 && L[i - 1].pts === L[i].pts) || (i < L.length - 1 && L[i + 1].pts === L[i].pts);
  const P = v => Math.round(v).toLocaleString("pt-BR"), nm = u => "GC. " + [...u.gcs].sort((a, b) => ((DATA.gcs[b].mensal.some(x => x.ICE != null)) - (DATA.gcs[a].mensal.some(x => x.ICE != null))) || a.localeCompare(b)).map(g => g.replace("GC. ", "")).join("/") + "  ·  " + u.nome.split(" ").slice(0, 2).join(" ");
  const s = novo("Ranking de gerentes");
  const w2 = (CW - G) / 2, n = Math.min(14, Math.max(RM.length, RA.length)), rh = Math.min(0.4, (Y_END - Y_STRIP - 0.45) / (n + 1));
  const destaque = { bold: true, color: C.white, fill: { color: C.good } };
  tabela(s, ["#", `Jantar romântico · ${cap(mesA)}`, "ICE", "Pontos"], RM.slice(0, n).map((r, i) => [`${i + 1}º`, nm(r.u) + (emp(RM, i) ? " *" : ""),
    { text: fmt(r.ice), options: { align: "center" } }, { text: P(r.pts), options: { align: "center", bold: true, ...(i === 0 ? destaque : {}) } }]),
    { x: X0, y: Y_STRIP, w: w2, colW: [0.5, w2 - 2.6, 1.0, 1.1], fs: 11, rowH: rh });
  tabela(s, ["#", `Melhores do ano · parcial ${mA.slice(0, 4)}`, "Pontos", "Prêmio"], RA.slice(0, n).map((r, i) => [`${i + 1}º`, nm(r.u) + (emp(RA, i) ? " *" : ""),
    { text: P(r.pts), options: { align: "center", bold: true } }, { text: i < 3 ? `R$ ${PREMIOS[i].toLocaleString("pt-BR")}` : "", options: { align: "center", ...(i < 3 ? destaque : {}) } }]),
    { x: X0 + w2 + G, y: Y_STRIP, w: w2, colW: [0.5, w2 - 2.8, 1.1, 1.2], fs: 11, rowH: rh });
  s.addText(`Melhor do mês: ${RM[0] ? RM[0].u.nome : "–"} — jantar romântico  ·  Melhores do ano: 1º R$ 7.500 · 2º R$ 5.000 · 3º R$ 3.000  ·  * empate decidido pelo melhor ICE Latam`,
    { x: X0, y: 6.7, w: CW, h: 0.24, fontFace: F, fontSize: 9.5, color: C.muted, margin: 0 });
}

// 11. Encerramento
pres.addSlide().addImage({ path: encerramento(generoDe("EMPRESA", "")), x: 0.083, y: 0, w: 13.146, h: 7.5 });
pres.writeFile({ fileName: outPath }).then(() => console.log("ok", outPath));
