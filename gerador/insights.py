"""Insights do portal: explica o que moveu cada indicador (mês × mês anterior), só com dados reais.
Gera insights.json com, para cada mês e cada escopo (EMPRESA e cada GC):
  blocos      – um por indicador (ICE, RED, SOVI SSD/Sabores/Sucos, Repositor, CPI, TOM, Compromisso, Pontuação)
  oportunidades / atencao – regras objetivas sobre os resultados do mês
Uso: (variáveis DADOS_DIR, CONFIG_DIR, SAIDA_DIR) python insights.py
"""
import os, sys, json
AQUI = os.path.dirname(os.path.abspath(__file__))
OUTD = os.environ.get("SAIDA_DIR", AQUI)
sys.argv = ["x", os.environ.get("DADOS_DIR", AQUI), os.path.join(OUTD, "_x.json")]
__file__ = os.path.join(AQUI, "dados_deck.py")
exec(open(os.path.join(AQUI, "dados_deck.py"), encoding="utf-8").read().split("ger = pd.read_excel")[0])
src = open(os.path.join(AQUI, "dados_deck.py"), encoding="utf-8").read()
exec(src[src.index("ger = pd.read_excel"):src.index("lbl = lambda m")])           # cadastros, CPI, TOM, compromisso, repositor
D = json.load(open(os.path.join(OUTD, "deck_data.json"), encoding="utf-8"))

MESN = MESES
f2 = lambda v: "–" if v is None else f"{v:.2f}".replace(".", ",")
pp_ = lambda v: f"{'+' if v >= 0 else '−'}{abs(v):.2f}".replace(".", ",") + " p.p."
def mov(d): return "subiu" if d > 0 else "caiu"
def svn(sv): n = sup_nome.get(sv, ""); return sv if not n or n.upper().startswith("ROTA") else f"{sv} ({n.title()})"
def lim(v, n=5): return v[:n]


# ---------------------------------------------------------------- ICE / RED
def decomp(df, tipo):
    """nota = Σ_seg n_seg·w_seg / Σw ; decompõe por segmento, métrica (kpi) e pergunta (somas exatas)"""
    if df.empty: return None
    s = df.groupby("seg").agg(pp=("pp", "sum"), pr=("pr", "sum"))
    s = s[s.pp > 0]
    w = pesos(df, tipo)
    s["w"] = s.index.map(w); s = s.dropna(subset=["w"])
    if s.empty: return None
    W = s.w.sum()
    s["n"] = s.pr / s.pp * 100; s["c"] = s.n * s.w / W
    k = df[df.seg.isin(s.index)].groupby(["seg", "kpi"]).pr.sum().reset_index()
    k["c"] = k.pr / k.seg.map(s.pp) * 100 * k.seg.map(s.w) / W
    q = df[df.seg.isin(s.index)].groupby(["seg", "pergunta"]).pr.sum().reset_index()
    q["c"] = q.pr / q.seg.map(s.pp) * 100 * q.seg.map(s.w) / W
    q["pergunta"] = q.pergunta.astype(str).str.replace(r"^\s*\S+\s+-\s+", "", regex=True).str.strip()
    return {"nota": float(s.c.sum()), "seg": s, "kpi": k.groupby("kpi").c.sum(), "perg": q.groupby("pergunta").c.sum(), "W": W, "w": s.w}


def clientes(dm, da, dcm):
    pm = dm.groupby("pdv").agg(pp=("pp", "sum"), pr=("pr", "sum"), nome=("nome_fantasia", "first"), seg=("seg", "first"), gc=("gc", "first"), sv=("sv", "first"))
    pa = da.groupby("pdv").agg(pp=("pp", "sum"), pr=("pr", "sum"))
    j = pm.join(pa, rsuffix="_a", how="inner")
    j = j[(j.pp > 0) & (j.pp_a > 0)]
    if j.empty or dcm is None: return []
    j["nm"], j["na"] = j.pr / j.pp * 100, j.pr_a / j.pp_a * 100
    j["d"] = j.nm - j.na
    npdv = pm.groupby("seg").size()
    j["imp"] = j.d * j.seg.map(dcm["w"]).fillna(0) / dcm["W"] / j.seg.map(npdv)
    return [{"pdv": p, "nome": str(r.nome).strip().title(), "seg": ROTULO_SEG.get(r.seg, r.seg).title(), "gc": r.gc, "sv": svn(r.sv),
             "ant": round(r.na, 2), "atual": round(r.nm, 2), "delta": round(r.d, 2), "impacto": round(r.imp, 3)} for p, r in j.iterrows()]


def contrafactual(dm, da, col, tipo):
    """impacto de cada grupo (GC ou supervisor) = nota atual − nota com o grupo como no mês anterior"""
    base = nota(dm, tipo); out = []
    if base is None: return out
    for g in sorted(set(dm[col]) | set(da[col])):
        alt = pd.concat([dm[dm[col] != g], da[da[col] == g]])
        n_alt = nota(alt, tipo)
        nm, na = nota(dm[dm[col] == g], tipo), nota(da[da[col] == g], tipo)
        if n_alt is None: continue
        out.append({"nome": g if col == "gc" else svn(g), "ant": na and round(na, 2), "atual": nm and round(nm, 2),
                    "delta": None if nm is None or na is None else round(nm - na, 2), "impacto": round(base - n_alt, 3)})
    return sorted(out, key=lambda r: r["impacto"])


def bloco_nota(tipo, dm, da, escopo):
    nome = "ICE Latam" if tipo == "ICE" else "RED"
    cm, ca = decomp(dm, tipo), decomp(da, tipo)
    if not cm or not ca: return None
    d = cm["nota"] - ca["nota"]; sinal = 1 if d >= 0 else -1
    segs = []
    for sg in sorted(set(cm["seg"].index) | set(ca["seg"].index)):
        a = ca["seg"].loc[sg] if sg in ca["seg"].index else None; m = cm["seg"].loc[sg] if sg in cm["seg"].index else None
        segs.append({"nome": ROTULO_SEG.get(sg, sg).title(), "ant": a is not None and round(a.n, 2) or None, "atual": m is not None and round(m.n, 2) or None,
                     "delta": round(m.n - a.n, 2) if a is not None and m is not None else None,
                     "impacto": round((m.c if m is not None else 0) - (a.c if a is not None else 0), 3)})
    segs.sort(key=lambda r: r["impacto"])
    kp = (cm["kpi"].sub(ca["kpi"], fill_value=0)).sort_values()
    KPI_NOME = {"ATIVACAO": "Ativação", "PRECO": "Preço", "DISPONIBILIDADE": "Disponibilidade", "SOVI": "SOVI", "GDM": "GDM"}
    met = [{"nome": KPI_NOME.get(str(k).upper(), str(k).title()), "atual": round(float(cm["kpi"].get(k, 0)), 2), "ant": round(float(ca["kpi"].get(k, 0)), 2), "impacto": round(float(v), 3)} for k, v in kp.items()]
    pq = (cm["perg"].sub(ca["perg"], fill_value=0)).sort_values()
    perg = [{"nome": k, "impacto": round(float(v), 3)} for k, v in pq.items()]
    cli = sorted(clientes(dm, da, cm), key=lambda r: r["impacto"])
    grp = contrafactual(dm, da, "gc" if escopo == "EMPRESA" else "sv", tipo)
    rot_grp = "gerência" if escopo == "EMPRESA" else "supervisor"
    F = [f"{nome} {mov(d)} {f2(abs(d))} p.p. ({f2(ca['nota'])} → {f2(cm['nota'])})."]
    lado = segs if sinal < 0 else segs[::-1]
    if lado and lado[0]["impacto"] * sinal > 0:
        s0 = lado[0]; F.append(f"Segmento que mais {'derrubou' if sinal < 0 else 'puxou'} o resultado: {s0['nome']} (nota {f2(s0['ant'])} → {f2(s0['atual'])}; impacto de {pp_(s0['impacto'])} na nota).")
    contra = (segs[::-1] if sinal < 0 else segs)
    if contra and contra[0]["impacto"] * sinal < -0.05:
        F.append(f"Em sentido contrário, {contra[0]['nome']} compensou {pp_(contra[0]['impacto'])}.")
    ml = met if sinal < 0 else met[::-1]
    if ml and ml[0]["impacto"] * sinal > 0:
        F.append(f"Métrica com maior contribuição: {ml[0]['nome']} ({pp_(ml[0]['impacto'])} no resultado).")
    pl = perg if sinal < 0 else perg[::-1]
    if pl and pl[0]["impacto"] * sinal > 0:
        F.append(f"Pergunta que mais pesou: “{pl[0]['nome']}” ({pp_(pl[0]['impacto'])}).")
    gl = grp if sinal < 0 else grp[::-1]
    if gl and gl[0]["impacto"] * sinal > 0:
        F.append(f"Maior impacto por {rot_grp}: {gl[0]['nome']} ({pp_(gl[0]['impacto'])} no resultado; nota {f2(gl[0]['ant'])} → {f2(gl[0]['atual'])}).")
    cl = cli if sinal < 0 else cli[::-1]
    if cl and cl[0]["delta"] * sinal > 0:
        c0 = cl[0]; F.append(f"Cliente com maior {'queda' if sinal < 0 else 'alta'}: {c0['nome']} – PDV {c0['pdv']} ({c0['seg']}, {c0['gc']}), {f2(c0['ant'])} → {f2(c0['atual'])} pontos.")
    return {"ind": tipo, "titulo": nome, "ant": round(ca["nota"], 2), "atual": round(cm["nota"], 2), "delta": round(d, 2), "frases": F,
            "tabelas": {"Segmentos (impacto na nota)": segs, "Métricas": met, ("Gerências" if escopo == "EMPRESA" else "Supervisores"): grp,
                        "Clientes – maiores quedas": lim([c for c in cli if c["delta"] < 0]), "Clientes – maiores altas": lim([c for c in cli[::-1] if c["delta"] > 0])}}


# ---------------------------------------------------------------- SOVI
PONTO_NOME = {"GONDOLA": "Gôndola", "PONTO EXTRA": "Ponto extra", "GDM KO": "GDM KO", "GDM DO CLIENTE": "GDM do cliente", "GDM DA CONCORRÊNCIA": "GDM da concorrência"}
def bloco_sovi(k, xm, xa, escopo):
    nome, filt = SOVI_SER[k]; m, a = filt(xm), filt(xa)
    sm, sa = _sovi(m), _sovi(a)
    if sm is None or sa is None: return None
    d = sm - sa; sinal = 1 if d >= 0 else -1
    Tm, Ta = m[m.fabricante != "-"].frentes.sum(), a[a.fabricante != "-"].frentes.sum()
    # participação por fabricante
    fm = m[m.fabricante != "-"].groupby("fabricante_nome").frentes.sum() / Tm * 100
    fa = a[a.fabricante != "-"].groupby("fabricante_nome").frentes.sum() / Ta * 100
    fab = [{"nome": str(n).title(), "ant": round(float(fa.get(n, 0)), 2), "atual": round(float(fm.get(n, 0)), 2), "delta": round(float(fm.get(n, 0) - fa.get(n, 0)), 2)}
           for n in sorted(set(fm.index) | set(fa.index))]
    fab.sort(key=lambda r: r["delta"])
    # contribuição de cada ponto de contato para o SOVI (frentes KO no ponto ÷ frentes totais)
    pm = m[m.fabricante == "COCA COLA"].groupby("ponto").frentes.sum() / Tm * 100
    pa = a[a.fabricante == "COCA COLA"].groupby("ponto").frentes.sum() / Ta * 100
    sv_p = lambda x, p: _sovi(x[x.ponto == p])
    pts = [{"nome": PONTO_NOME.get(p, str(p).title()), "contrib_ant": round(float(pa.get(p, 0)), 2), "contrib_atual": round(float(pm.get(p, 0)), 2),
            "impacto": round(float(pm.get(p, 0) - pa.get(p, 0)), 2), "sovi_ant": sv_p(a, p) and round(sv_p(a, p), 2), "sovi_atual": sv_p(m, p) and round(sv_p(m, p), 2)}
           for p in sorted(set(pm.index) | set(pa.index))]
    pts.sort(key=lambda r: r["impacto"])
    col = "gc" if escopo == "EMPRESA" else "sv"
    grp = []
    for g in sorted(set(m[col]) | set(a[col])):
        alt = pd.concat([m[m[col] != g], a[a[col] == g]]); n_alt = _sovi(alt)
        gm, ga = _sovi(m[m[col] == g]), _sovi(a[a[col] == g])
        if n_alt is not None: grp.append({"nome": g if col == "gc" else svn(g), "ant": ga and round(ga, 2), "atual": gm and round(gm, 2), "impacto": round(sm - n_alt, 3)})
    grp.sort(key=lambda r: r["impacto"])
    ko = _var(a[a.fabricante == "COCA COLA"].frentes.sum(), m[m.fabricante == "COCA COLA"].frentes.sum())
    cc = _var(a[a.fabricante == "CONCORRENTE"].frentes.sum(), m[m.fabricante == "CONCORRENTE"].frentes.sum())
    F = [f"{nome} {mov(d)} {f2(abs(d))} p.p. ({f2(sa)}% → {f2(sm)}%)."]
    if ko is not None and cc is not None:
        F.append(f"Frentes Coca-Cola {ko:+.1f}% e frentes da concorrência {cc:+.1f}% no período.".replace(".", ",", 2).replace(",,", ","))
    conc = [r for r in fab if r["nome"].upper() != "COCA COLA"]
    if conc:
        up, dn = conc[-1], conc[0]
        if up["delta"] > 0: F.append(f"Fabricante concorrente que mais ganhou espaço: {up['nome']} ({pp_(up['delta'])}; {f2(up['ant'])}% → {f2(up['atual'])}%).")
        if dn["delta"] < 0: F.append(f"Fabricante concorrente que mais perdeu espaço: {dn['nome']} ({pp_(dn['delta'])}).")
    pl = pts if sinal < 0 else pts[::-1]
    if pl and pl[0]["impacto"] * sinal > 0:
        F.append(f"A {'queda' if sinal < 0 else 'alta'} aconteceu principalmente em {pl[0]['nome']} ({pp_(pl[0]['impacto'])} de contribuição"
                 + (f"; SOVI no ponto {f2(pl[0]['sovi_ant'])}% → {f2(pl[0]['sovi_atual'])}%" if pl[0]["sovi_ant"] is not None and pl[0]["sovi_atual"] is not None else "") + ").")
        if len(pl) > 1 and pl[1]["impacto"] * sinal > 0: F.append(f"Em seguida, {pl[1]['nome']} ({pp_(pl[1]['impacto'])}).")
    gl = grp if sinal < 0 else grp[::-1]
    if gl and gl[0]["impacto"] * sinal > 0:
        F.append(f"Maior impacto por {'gerência' if col == 'gc' else 'supervisor'}: {gl[0]['nome']} ({pp_(gl[0]['impacto'])}; {f2(gl[0]['ant'])}% → {f2(gl[0]['atual'])}%).")
    return {"ind": "SOVI_" + k, "titulo": nome, "ant": round(sa, 2), "atual": round(sm, 2), "delta": round(d, 2), "frases": F,
            "tabelas": {"Participação por fabricante (% das frentes)": fab[:3] + fab[-3:] if len(fab) > 6 else fab,
                        "Contribuição por ponto de contato": pts, ("Gerências" if col == "gc" else "Supervisores"): grp}}


# ---------------------------------------------------------------- Repositor (RED, por rota RP)
def bloco_repositor(escopo, m, a):
    def por_rota(mes, gcs):
        b = base_rep[(base_rep.mes == mes) & base_rep.gc_rep.isin(gcs)]
        j = b.merge(pts_pdv["RED"][pts_pdv["RED"].mes == mes][["pdv", "pp", "pr"]], on="pdv")
        return j
    gcs = list(D["gcs"]) if escopo == "EMPRESA" else [escopo]
    jm, ja = por_rota(m, gcs), por_rota(a, gcs)
    if jm.empty or ja.empty or jm.pp.sum() == 0 or ja.pp.sum() == 0: return None
    nm, na = jm.pr.sum() / jm.pp.sum() * 100, ja.pr.sum() / ja.pp.sum() * 100
    d = nm - na
    rm = jm.groupby("Rota RP").agg(pp=("pp", "sum"), pr=("pr", "sum")); ra = ja.groupby("Rota RP").agg(pp=("pp", "sum"), pr=("pr", "sum"))
    rot = []
    for r in sorted(set(rm.index) & set(ra.index), key=str):
        vm, va = rm.loc[r].pr / rm.loc[r].pp * 100, ra.loc[r].pr / ra.loc[r].pp * 100
        imp = (rm.loc[r].pr - rm.loc[r].pp * na / 100) / jm.pp.sum() * 100 - (ra.loc[r].pr - ra.loc[r].pp * na / 100) / ja.pp.sum() * 100
        rot.append({"nome": str(r), "ant": round(va, 2), "atual": round(vm, 2), "delta": round(vm - va, 2), "impacto": round(imp, 3)})
    rot.sort(key=lambda x: x["delta"])
    F = [f"RED repositor {mov(d)} {f2(abs(d))} p.p. ({f2(na)} → {f2(nm)}): {len(jm)} atendimentos (loja × rota) em {jm.pdv.nunique()} lojas pesquisadas, {jm['Rota RP'].nunique()} rotas RP."]
    if rot and d < 0 and rot[0]["delta"] < 0: F.append(f"Rota com maior queda: {rot[0]['nome']} ({f2(rot[0]['ant'])} → {f2(rot[0]['atual'])}).")
    if rot and d >= 0 and rot[-1]["delta"] > 0: F.append(f"Rota com maior alta: {rot[-1]['nome']} ({f2(rot[-1]['ant'])} → {f2(rot[-1]['atual'])}).")
    return {"ind": "REPOSITOR", "titulo": "RED repositor", "ant": round(na, 2), "atual": round(nm, 2), "delta": round(d, 2), "frases": F,
            "tabelas": {"Rotas RP – maiores quedas": lim([r for r in rot if r["delta"] < 0]), "Rotas RP – maiores altas": lim([r for r in rot[::-1] if r["delta"] > 0])}}


# ---------------------------------------------------------------- CPI, TOM, Compromisso, Pontuação (dados por gerência)
def linha_gc(g, mes):
    G = D["gcs"][g]; r = next((x for x in G["mensal"] if x["mes"] == mes), {}) or {}
    c = next((x for x in G["cpi"] if x["mes"] == mes), None); t = next((x for x in G["tom"] if x["lbl"] == MESN[int(mes[5:7])]), None)
    return G, r, c, t

PT = {"ICE_MIN": 75, "ICE": 5000, "CPI": 3000, "TOM": 2000, "PLUS": 1000, "INICIO_PLUS": "2026-07"}
def pontos(g, mes):
    G, r, c, t = linha_gc(g, mes); ice = r.get("ICE"); cp = G.get("compromisso")
    ok = {f"ICE ≥ {PT['ICE_MIN']}": ice is not None and ice >= PT["ICE_MIN"], "CPI ≥ meta": bool(c and c["real"] >= c["meta"]), "TOM": bool(t and t["realizou"] == "SIM"),
          "Compromisso": bool(cp is not None and ice is not None and mes >= PT["INICIO_PLUS"] and ice >= cp)}
    return ok, ok[f"ICE ≥ {PT['ICE_MIN']}"] * PT["ICE"] + ok["CPI ≥ meta"] * PT["CPI"] + ok["TOM"] * PT["TOM"] + ok["Compromisso"] * PT["PLUS"]

def blocos_gerencia(escopo, m, a):
    gcs = list(D["gcs"]) if escopo == "EMPRESA" else [escopo]
    out = []
    # CPI
    cm = [(g, linha_gc(g, m)[2], linha_gc(g, a)[2]) for g in gcs]; cm = [x for x in cm if x[1] and x[2]]
    if cm:
        if escopo == "EMPRESA":
            q = cpi[cpi.mes == m]; qa = cpi[cpi.mes == a]
            rm_, ra_ = (q.REAL_CPI * q.QTD_GDM).sum() / q.QTD_GDM.sum() * 100, (qa.REAL_CPI * qa.QTD_GDM).sum() / qa.QTD_GDM.sum() * 100
            mm = (q.META_CPI * q.QTD_GDM).sum() / q.QTD_GDM.sum() * 100
            vz = (q.REAL_VDZ.sum(), qa.REAL_VDZ.sum()); ins = (q.REAL_INSTALÇAO.sum(), qa.REAL_INSTALÇAO.sum()); pe = (q.QTD_EQP_PERD.sum(), qa.QTD_EQP_PERD.sum())
        else:
            g, c1, c0 = cm[0]; rm_, ra_, mm = c1["real"], c0["real"], c1["meta"]
            vz = (c1["vdz"], c0["vdz"]); ins = (c1["inst"], c0["inst"]); pe = (c1["perdida"], c0["perdida"])
        d = rm_ - ra_
        F = [f"CPI {mov(d)} {f2(abs(d))} p.p. ({f2(ra_)}% → {f2(rm_)}%), {'acima' if rm_ >= mm else 'abaixo'} da meta de {f2(mm)}% ({pp_(rm_ - mm)})."]
        F.append(f"Venda zero {vz[1]:.0f} → {vz[0]:.0f} · instalação de GDM {ins[1]:.0f} → {ins[0]:.0f} · GDM perdida {pe[1]:.0f} → {pe[0]:.0f}.")
        tab = {}
        if escopo == "EMPRESA":
            dd = sorted([{"nome": g, "ant": round(c0["real"], 2), "atual": round(c1["real"], 2), "delta": round(c1["real"] - c0["real"], 2), "meta": round(c1["meta"], 2)} for g, c1, c0 in cm], key=lambda r: r["delta"])
            if dd: F.append(f"Gerência com maior {'queda' if d < 0 else 'alta'} de CPI: {(dd[0] if d < 0 else dd[-1])['nome']} ({pp_((dd[0] if d < 0 else dd[-1])['delta'])}).")
            abaixo = [r["nome"] for r in dd if r["atual"] < r["meta"]]
            if abaixo: F.append(f"Abaixo da meta no mês: {', '.join(sorted(abaixo))}.")
            tab["Gerências"] = dd
        F.append("O CPI vem consolidado por gerência; não há abertura por cliente ou equipamento na base recebida.")
        out.append({"ind": "CPI", "titulo": "CPI", "ant": round(ra_, 2), "atual": round(rm_, 2), "delta": round(d, 2), "frases": F, "tabelas": tab})
    # TOM
    tm = [(g, linha_gc(g, m)[3]) for g in gcs]; tm = [x for x in tm if x[1]]
    if tm:
        nao = [g for g, t in tm if t["realizou"] != "SIM"]; temas = sorted({t["tema"] for _, t in tm if t.get("tema")})
        F = [f"TOM executado em {len(tm) - len(nao)} de {len(tm)} gerência(s)" + (f"; tema: {', '.join(temas)}." if temas else ".")]
        if nao: F.append(f"Não executaram: {', '.join(nao)} (perdem 2 mil pontos cada).")
        out.append({"ind": "TOM", "titulo": "TOM", "ant": None, "atual": len(tm) - len(nao), "delta": None, "frases": F, "tabelas": {}})
    # Compromisso
    if m >= PT["INICIO_PLUS"]:
        cp = [(g, D["gcs"][g].get("compromisso"), linha_gc(g, m)[1].get("ICE")) for g in gcs]; cp = [x for x in cp if x[1] is not None and x[2] is not None]
        if cp:
            ok = [g for g, c, i in cp if i >= c]; gap = sorted([{"nome": g, "compromisso": c, "atual": round(i, 2), "gap": round(i - c, 2)} for g, c, i in cp], key=lambda r: r["gap"])
            F = [f"{len(ok)} de {len(cp)} gerência(s) acima do compromisso de ICE no mês."]
            perto = [r for r in gap if -1 <= r["gap"] < 0]
            if perto: F.append("Ficaram a menos de 1 p.p. do compromisso: " + ", ".join(f"{r['nome']} ({pp_(r['gap'])})" for r in perto) + ".")
            out.append({"ind": "COMPROMISSO", "titulo": "Compromisso de ICE", "ant": None, "atual": len(ok), "delta": None, "frases": F, "tabelas": {"Gerências (ICE − compromisso)": gap}})
    # Pontuação
    pts_ = []
    for g in gcs:
        okm, pm_ = pontos(g, m); oka, pa_ = pontos(g, a)
        mud = [k for k in okm if okm[k] != oka[k]]
        pts_.append({"nome": g, "ant": pa_, "atual": pm_, "delta": pm_ - pa_, "motivo": ", ".join(("ganhou " if okm[k] else "perdeu ") + k for k in mud) or "sem mudança"})
    tot_m, tot_a = sum(r["atual"] for r in pts_), sum(r["ant"] for r in pts_)
    nf = lambda v: f"{v:,.0f}".replace(",", ".")
    F = [f"Pontuação {'total ' if escopo == 'EMPRESA' else ''}{'subiu' if tot_m > tot_a else 'caiu' if tot_m < tot_a else 'ficou estável'}: {nf(tot_a)} → {nf(tot_m)} pontos."]
    for r in sorted(pts_, key=lambda r: r["delta"]):
        if r["delta"] < 0: F.append(f"{r['nome']}: {'−' + nf(-r['delta'])} pontos ({r['motivo']}).")
    for r in sorted(pts_, key=lambda r: -r["delta"]):
        if r["delta"] > 0: F.append(f"{r['nome']}: +{nf(r['delta'])} pontos ({r['motivo']}).")
    out.append({"ind": "PONTOS", "titulo": "Pontuação", "ant": tot_a, "atual": tot_m, "delta": tot_m - tot_a, "frases": F[:8], "tabelas": {"Gerências": sorted(pts_, key=lambda r: r["delta"])} if escopo == "EMPRESA" else {}})
    return out


def regras(escopo, m, a):
    """oportunidades e pontos de atenção – regras objetivas sobre o mês"""
    gcs = list(D["gcs"]) if escopo == "EMPRESA" else [escopo]
    op, at = [], []
    for g in gcs:
        G, r, c, t = linha_gc(g, m); _, ra, ca, _ = linha_gc(g, a)
        ice, red = r.get("ICE"), r.get("RED")
        K = PT["ICE_MIN"]
        if ice is not None and K - 2 <= ice < K: op.append(f"{g}: ICE {f2(ice)}, a {f2(K - ice)} p.p. dos {K} que garantem 5 mil pontos.")
        if ice is not None and K <= ice < K + 1: at.append(f"{g}: ICE {f2(ice)}, menos de 1 p.p. acima do corte de {K}.")
        if ice is not None and ice < K - 2: at.append(f"{g}: ICE {f2(ice)}, abaixo do corte de {K} (sem os 5 mil pontos).")
        if c and c["real"] < c["meta"]:
            (op if c["meta"] - c["real"] <= 0.5 else at).append(f"{g}: CPI {f2(c['real'])}% vs meta {f2(c['meta'])}% ({pp_(c['real'] - c['meta'])}).")
        if t and t["realizou"] != "SIM": at.append(f"{g}: TOM não executado no mês.")
        cp = G.get("compromisso")
        if cp is not None and ice is not None and m >= PT["INICIO_PLUS"] and cp - 1 <= ice < cp: op.append(f"{g}: ICE a {f2(cp - ice)} p.p. do compromisso de {f2(cp)} (+1 mil pontos).")
        for k, n in (("ICE", "ICE Latam"), ("RED", "RED")):
            if r.get(k) is not None and ra.get(k) is not None and r[k] - ra[k] <= -3: at.append(f"{g}: {n} caiu {f2(ra[k] - r[k])} p.p. no mês.")
    return op, at


def gerar():
    meses = sorted(set(pesq["ICE"].mes) | set(pesq["RED"].mes))
    out = {"meses": meses, "por_mes": {}}
    for a, m in zip(meses, meses[1:]):
        R = {}
        for esc in ["EMPRESA"] + list(D["gcs"]):
            sel = (lambda x: x) if esc == "EMPRESA" else (lambda x, e=esc: x[x.gc == e])
            B = []
            for tipo in ("ICE", "RED"):
                b = bloco_nota(tipo, sel(pesq[tipo][pesq[tipo].mes == m]), sel(pesq[tipo][pesq[tipo].mes == a]), esc)
                if b: B.append(b)
            sb = sovi_base[~sovi_base.sv.isin(SV_FORA)]
            for k in SOVI_SER:
                b = bloco_sovi(k, sel(sb[sb.mes == m]), sel(sb[sb.mes == a]), esc)
                if b: B.append(b)
            b = bloco_repositor(esc, m, a)
            if b: B.append(b)
            B += blocos_gerencia(esc, m, a)
            op, at = regras(esc, m, a)
            R[esc] = {"blocos": B, "oportunidades": op, "atencao": at}
        out["por_mes"][m] = R
        print("insights", m, sum(len(v["blocos"]) for v in R.values()), "blocos")
    json.dump(out, open(os.path.join(OUTD, "insights.json"), "w", encoding="utf-8"), ensure_ascii=False, default=lambda o: float(o) if hasattr(o, "__float__") else str(o))


gerar()
