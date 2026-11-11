"""Calcula os dados da apresentação por GC (regras validadas contra o Power BI).
Uso: python dados_deck.py <pasta_uploads> <saida.json>
"""
import sys, json, re, glob, os, hashlib
import pandas as pd

U, OUT = sys.argv[1], sys.argv[2]
MESES = ["", "janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
CAP_PILAR = 110.0   # teto observado no Power BI (Ativação = 110,00)


def _todos_xlsx():
    """todas as planilhas das pastas de dados (várias pastas separadas por os.pathsep; subpastas incluídas)"""
    out = []
    for d in [p for p in U.split(os.pathsep) if p.strip()]:
        out += glob.glob(os.path.join(d, "**", "*.xlsx"), recursive=True)
    return [x for x in out if not os.path.basename(x).startswith("~$")]


def f(pat):
    r = sorted(x for x in _todos_xlsx() if re.search(pat, os.path.basename(x), re.I))
    ult = {}                      # mesmo nome em duas pastas (OneDrive e carga do portal): vale o mais recente
    for x in r:
        k = os.path.basename(x).lower()
        if k not in ult or os.path.getmtime(x) > os.path.getmtime(ult[k]): ult[k] = x
    r = list(ult.values())
    vis, out = set(), []          # ignora reenvios idênticos (mesmo conteúdo)
    for x in sorted(r, key=os.path.getmtime, reverse=True):
        h = hashlib.md5(open(x, "rb").read()).hexdigest()
        if h not in vis:
            vis.add(h); out.append(x)
    return sorted(out)


def num(s):
    """aceita '1,50' (pt-BR), '1.234,50', '1.5' (ponto decimal) e números já convertidos"""
    t = s.astype(str).str.strip()
    br = t.str.contains(",", regex=False)
    t = t.where(~br, t.str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
    return pd.to_numeric(t, errors="coerce").fillna(0)


import hashlib, pickle
AQUI = os.path.dirname(os.path.abspath(globals().get("__file__", "dados_deck.py")))
CONFIG = os.environ.get("CONFIG_DIR", AQUI)   # pesos.json, supervisores.json, gerencias.json, SOVI_RESUMO
CACHE = os.environ.get("CACHE_DIR", os.path.join(AQUI, "cache"))
os.makedirs(CACHE, exist_ok=True)
COLS = ["kpi", "pdv", "nome_fantasia", "razao_social", "gerencia_vendas", "supervisao", "rota_vendedor", "canal_fds", "data_pesquisa", "pergunta",
        "pontos_possiveis", "pontos_realizados", "pontua", "aplicar_pontuacao", "frentes_total", "frentes_ko", "classificacao"]

def mes_da_data(s):
    """data_pesquisa vem como data (2026-09-01 00:00:00) ou texto brasileiro (20/10/2026): sempre dia/mês/ano"""
    t = s.astype(str).str.strip()
    br = t.str.match(r"^\d{1,2}/\d{1,2}/\d{4}")
    d = pd.to_datetime(t.where(~br), errors="coerce")
    d = d.where(~br, pd.to_datetime(t.where(br).str[:10], format="%d/%m/%Y", errors="coerce"))
    return d.dt.strftime("%Y-%m")


def load(path):
    # chave: nome + tamanho + data em segundos (o cache da nuvem guarda a data sem as frações de segundo)
    st = os.stat(path); key = hashlib.md5(f"{os.path.basename(path)}{st.st_size}{int(st.st_mtime)}".encode()).hexdigest()
    cp = os.path.join(CACHE, key + ".pkl")
    if os.path.exists(cp):
        x = pd.read_pickle(cp)
        try: os.utime(cp)          # marca como usado (a nuvem descarta o que não é usado há mais de 1 dia)
        except OSError: pass
    else:
        x = pd.read_excel(path, dtype=str)
        x = x[[c for c in COLS if c in x.columns]]
        x.to_pickle(cp)
    x["pp"], x["pr"] = num(x.pontos_possiveis), num(x.pontos_realizados)
    x["seg"] = x.canal_fds.str.replace(" - ICE LATAM", "", regex=False).str.strip()
    x["gc"], x["sv"] = x.gerencia_vendas.str.strip(), x.supervisao.str.strip()
    x["mes"] = mes_da_data(x.data_pesquisa)
    x["pdv"] = x.pdv.astype(str).str.strip()
    return x


# Pesos por ano de metodologia (sufixo da coluna classificacao: *_2025 / *_2026) – tabela oficial PESO_ICE25/26 · PESO_RED25/26
SEGS = ["SUPERMERCADO (AS 5-19CK)", "CASH & CARRY", "MINIMERCADO (AS 1-2CK)", "MINIMERCADO (AS 3-4CK)", "HIPERMERCADO (AS 20+CK)", "LANCHONETE",
        "PADARIA", "RESTAURANTE", "MERCEARIA", "BOTECO", "ADEGAS", "CONVENIÊNCIA"]
_T = {  # seg: (ICE25, ICE26, RED25, RED26)
    "ADEGAS": (None, None, 1.80, 1.40), "MINIMERCADO (AS 1-2CK)": (19.74, 13.22, 19.64, 13.22), "MINIMERCADO (AS 3-4CK)": (10.43, 20.95, 10.33, 20.35),
    "BOTECO": (1.65, 1.35, 1.55, 1.35), "CASH & CARRY": (22.02, 17.17, 22.02, 17.17), "CONVENIÊNCIA": (None, None, 1.20, 1.00),
    "HIPERMERCADO (AS 20+CK)": (3.66, 3.46, 3.56, 3.46), "LANCHONETE": (3.22, 3.45, 3.12, 3.45), "MERCEARIA": (1.75, 0.90, 1.65, 1.10),
    "PADARIA": (2.94, 2.47, 2.84, 2.47), "RESTAURANTE": (2.16, 6.82, 2.16, 5.82), "SUPERMERCADO (AS 5-19CK)": (32.43, 30.21, 30.13, 29.21)}
PESOS = {a: {t: pd.Series({k: v[i] for k, v in _T.items() if v[i] is not None}) for t, i in (("ICE", 0 if a == "2025" else 1), ("RED", 2 if a == "2025" else 3))}
         for a in ("2025", "2026")}
_pj = os.path.join(CONFIG, "pesos.json")
if os.path.exists(_pj):   # pesos cadastrados no Painel Gerencial: {ano: {segmento: {RED, ICE}}}
    _P = json.load(open(_pj, encoding="utf-8"))
    PESOS = {a: {t: pd.Series({sg: v[t] for sg, v in segs.items() if v.get(t) is not None}, dtype=float) for t in ("RED", "ICE")} for a, segs in _P.items()}
ORDEM_SEG = SEGS
W = PESOS["2026"]
W25 = PESOS["2025"]
def pesos(df, tipo):
    ano = str(df.classificacao.iloc[0])[-4:] if "classificacao" in df and len(df) else "2026"
    return PESOS.get(ano, W)[tipo]
ROTULO_SEG = {"SUPERMERCADO (AS 5-19CK)": "SUPERMERCADO", "MINIMERCADO (AS 1-2CK)": "AS 1-2", "MINIMERCADO (AS 3-4CK)": "AS 3-4",
              "HIPERMERCADO (AS 20+CK)": "HIPERMERCADO"}


def nota(df, tipo):
    """Σ realizados ÷ Σ possíveis por segmento × peso, com peso redistribuído entre segmentos presentes"""
    if df.empty:
        return None
    s = df.groupby("seg").agg(pp=("pp", "sum"), pr=("pr", "sum")).reset_index()
    s = s[s.pp > 0]
    s["n"], s["w"] = s.pr / s.pp, s.seg.map(pesos(df, tipo))
    s = s.dropna(subset=["w"])
    return None if s.empty else float((s.n * s.w).sum() / s.w.sum() * 100)


def nota_seg(df):
    s = df.groupby("seg").agg(pp=("pp", "sum"), pr=("pr", "sum"))
    return {k: float(v) for k, v in (s.pr / s.pp * 100).items() if s.pp[k] > 0}


# RED x ICE é definido pela última coluna (classificacao): RED_2026 / ICE_LATAM_2026 – não pelo nome do arquivo
_todas = pd.concat([load(p).assign(_mt=os.path.getmtime(p)) for p in f(r"FATOS_(RED|ICE)")], ignore_index=True)
_todas["tipo"] = _todas.classificacao.str.upper().map(lambda c: "ICE" if "ICE" in c else ("RED" if "RED" in c else None))
# mesmo mês da mesma pesquisa em mais de um arquivo (reenvio corrigido): vale o arquivo mais recente
_todas = _todas[_todas._mt == _todas.groupby(["tipo", "mes"])._mt.transform("max")].drop(columns="_mt")
_todas = _todas.drop_duplicates()
ANO = os.environ.get("ANO") or (max(_todas.mes.dropna()) [:4] if len(_todas) else "2026")
_todas = _todas[_todas.mes.astype(str).str.startswith(ANO)]   # só o ano de acompanhamento
pesq = {t: _todas[_todas.tipo == t] for t in ("RED", "ICE")}
meses_pesq = sorted(set(pesq["ICE"].mes) | set(pesq["RED"].mes))

ger = pd.read_excel(f(r"DIM_GERENCIA")[-1])
ger = ger.rename(columns={"Gerencia Comercial": "gc", "Nome G.C": "nome"})[["gc", "nome"]]
# nome do Gerente Comercial exibido = cadastro do Painel Gerencial (gerencias.json); sem cadastro = DIM_GERENCIA
_gj = os.path.join(CONFIG, "gerencias.json")
GERENTES = json.load(open(_gj, encoding="utf-8")) if os.path.exists(_gj) else {}
ger["nome"] = [GERENTES.get(g.strip(), n if not str(n).upper().startswith("ROTA") else "") for g, n in zip(ger.gc, ger.nome)]
USUARIOS = [{"nome": n, "perfil": "gerente", "gcs": [g for g, x in GERENTES.items() if x == n]} for n in sorted(set(v for v in GERENTES.values() if v))]
sup = pd.read_excel(f(r"DIM_SUPERVISOR")[0], sheet_name=0)
sup_nome = {r.Supervisor.strip(): str(r.Nome).split()[0] for r in sup.itertuples()}

# ---- cadastro de supervisores (editável no portal: nome exibido + se entra no cálculo da nota) ----
_svf = os.path.join(CONFIG, "supervisores.json")
SVCFG = json.load(open(_svf, encoding="utf-8")) if os.path.exists(_svf) else {}
for _sv in sorted(set(_todas.sv.dropna())):
    if _sv not in SVCFG:   # novos supervisores entram com o nome do DIM_SUPERVISOR e considerados
        SVCFG[_sv] = {"gc": str(_todas[_todas.sv == _sv].gc.mode().iloc[0]), "nome": sup_nome.get(_sv, ""), "considerar": True}
for _sv, _c in SVCFG.items():
    if _c.get("nome", "").strip():
        sup_nome[_sv] = _c["nome"].strip()
SV_FORA = {k for k, v in SVCFG.items() if not v.get("considerar", True)}
json.dump(dict(sorted(SVCFG.items())), open(_svf, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
pesq_all = pesq
pesq = {t: x[~x.sv.isin(SV_FORA)] for t, x in pesq.items()}   # supervisor desmarcado não entra em nenhuma nota

novo = lambda pat: max(f(pat), key=os.path.getmtime)   # versão mais recente enviada
cpi = pd.read_excel(novo(r"FATOS_CPI"))
cpi["mes"] = pd.to_datetime(cpi.Data).dt.strftime("%Y-%m")
tom = pd.read_excel(novo(r"(^|[-_ ])TOM\.xlsx$"))
_cp = f(r"COMPROMISSO")
compromisso = ({str(r.GC).strip(): (None if pd.isna(r.Compromisso) else float(r.Compromisso)) for r in pd.read_excel(max(_cp, key=os.path.getmtime)).itertuples()} if _cp else {})
tom["dt"] = pd.to_datetime(tom.DATA)

# base de atendimento de repositor por mês (cada linha = loja atendida por uma rota RP)
def ler_base_rep(path):
    """lê só PV, Gerência, Rota RP e Referencia da aba Base Atendimento Repositor (resumo em cache)"""
    st = os.stat(path); cp = os.path.join(CACHE, "rp_" + hashlib.md5(f"{os.path.basename(path)}{st.st_size}".encode()).hexdigest() + ".pkl")
    if os.path.exists(cp):
        return pd.read_pickle(cp)
    r = _ler_base_rep(path)
    if r is not None:
        r.to_pickle(cp)
    return r

def _ler_base_rep(path):
    if re.search(r"BASE_RP_RESUMO", os.path.basename(path), re.I):   # resumo já pronto (mes, pdv, gc_rep, Rota RP)
        b = pd.read_excel(path, dtype=str); return b[["mes", "pdv", "gc_rep", "Rota RP"]]
    for hdr in (0, 1, 2):
        try:
            b = pd.read_excel(path, sheet_name="Base Atendimento Repositor", header=hdr)
        except Exception:
            return None
        b.columns = [str(c).strip() for c in b.columns]
        if {"PV", "Referencia"} <= set(b.columns):
            b = b[pd.to_numeric(b.PV, errors="coerce").notna()].copy()
            b["pdv"] = b.PV.astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
            b["gc_rep"] = b["Gerência"].astype(str).str.strip()
            b["mes"] = pd.to_datetime(b.Referencia).dt.strftime("%Y-%m")
            return b[["mes", "pdv", "gc_rep", "Rota RP"]]
    return None

_rp = f(r"((Janeiro|Fevereiro|Mar.o|Abril|Maio|Junho|Julho|Agosto|Setembro|Outubro|Novembro|Dezembro)\d{2}|BASE_RP_RESUMO.*)\.xlsx$")
_pm = {}   # mês → base; se o mesmo mês vier em mais de um arquivo, vale o enviado por último
for p in sorted(_rp, key=os.path.getmtime):
    b = ler_base_rep(p)
    if b is not None:
        for m, x in b.groupby("mes"):
            _pm[m] = x
base_rep = pd.concat(_pm.values(), ignore_index=True) if _pm else pd.DataFrame(columns=["mes", "pdv", "gc_rep", "Rota RP"])
print("bases repositor:", {m: len(x) for m, x in sorted(_pm.items())})

# pontos por PDV (mês, tipo)
pts_pdv = {t: pesq[t].groupby(["mes", "pdv"]).agg(pp=("pp", "sum"), pr=("pr", "sum")).reset_index() for t in ("RED", "ICE")}

# TAB_AUX_RP (réplica do Power BI): todas as bases de repositor empilhadas, sem chave de mês
TAB_AUX_RP = base_rep[["pdv", "Rota RP"]]
pts_pdv_gc = {t: pesq[t].groupby(["mes", "gc", "pdv"]).agg(pp=("pp", "sum"), pr=("pr", "sum")).reset_index() for t in ("RED", "ICE")}

def nota_repositor(gc, m, t):
    """RED_REPOSITOR: base de atendimento do MÊS (linha loja×rota), GC da base – bate com o PBI.
    ICE_REPOSITOR (réplica da consulta ICE_RP): ICE de todos os meses × TAB_AUX_RP só por PDV (LeftOuter,
    repete a loja a cada linha da TAB_AUX_RP), filtra mês e GC da pesquisa e faz Σ realizados ÷ Σ possíveis."""
    if t == "RED":
        b = base_rep[(base_rep.mes == m) & (base_rep.gc_rep == gc)]
        j = b.merge(pts_pdv[t][pts_pdv[t].mes == m][["pdv", "pp", "pr"]], on="pdv")
    else:
        x = pts_pdv_gc[t][(pts_pdv_gc[t].mes == m) & (pts_pdv_gc[t].gc == gc)]
        j = x.merge(TAB_AUX_RP, on="pdv")
    return float(j.pr.sum() / j.pp.sum() * 100) if len(j) and j.pp.sum() > 0 else None

# ================= SOVI pilares foco (regra do Power BI – TAB_FATOS_SOVI, aba RED360) =================
# SOVI = Σ frentes Fabricante "COCA COLA" ÷ Σ frentes Fabricante <> "-", por série:
#   SSD = Categoria REFRIGERANTE · SABORES = REFRIGERANTE com Sabor GUARANA/LARANJA/UVA/TONICA · SUCOS = Categoria SUCO
SOVI_SABORES = ["GUARANA", "LARANJA", "UVA", "TONICA"]
_svp = os.path.join(CONFIG, "SOVI_RESUMO.pkl")
if os.path.exists(_svp):
    sovi_base = pd.read_pickle(_svp)
else:
    _sv = f(r"SOVI_RESUMO") or [p for p in [os.path.join(CONFIG, "SOVI_RESUMO_2026.xlsx")] if os.path.exists(p)]
    sovi_base = pd.read_excel(max(_sv, key=os.path.getmtime), dtype={"frentes": float}) if _sv else pd.DataFrame(columns=["mes", "gc", "sv", "canal", "categoria", "sabor", "fabricante", "fabricante_nome", "area", "ponto", "frentes"])
def _sovi(x):
    t = x[x.fabricante != "-"].frentes.sum()
    return float(x[x.fabricante == "COCA COLA"].frentes.sum() / t * 100) if t else None
def sovi(x):
    ref = x[x.categoria == "REFRIGERANTE"]
    return {"SSD": _sovi(ref), "SAB": _sovi(ref[ref.sabor.isin(SOVI_SABORES)]), "SUC": _sovi(x[x.categoria == "SUCO"])}


# ---- insights do SOVI: o que puxou a variação (frentes KO x concorrência, supervisor, canal, sabor) ----
SOVI_SER = {"SSD": ("SOVI SSD", lambda d: d[d.categoria == "REFRIGERANTE"]),
            "SAB": ("SOVI Sabores", lambda d: d[(d.categoria == "REFRIGERANTE") & d.sabor.isin(SOVI_SABORES)]),
            "SUC": ("SOVI Sucos", lambda d: d[d.categoria == "SUCO"])}
def _pp(v): return f"{v:+.2f}".replace(".", ",") + " p.p."
def _pc(v): return f"{v:.2f}".replace(".", ",") + "%"
def _var(a, b): return None if not a else (b - a) / a * 100
def _mov(xa, xm, col, rot, sinal):
    """grupo (supervisor/canal/sabor) que mais puxou a variação: Δ SOVI do grupo × peso do grupo nas frentes"""
    tot = xm[xm.fabricante != "-"].frentes.sum() or 1
    best = None
    for g, gm in xm.groupby(col):
        ga = xa[xa[col] == g]
        tm = gm[gm.fabricante != "-"].frentes.sum()
        if tm < 0.03 * tot or ga.empty: continue
        na, nm = _sovi(ga), _sovi(gm)
        if na is None or nm is None: continue
        imp = (nm - na) * tm / tot
        if best is None or imp * sinal > best[0] * sinal: best = (imp, rot(g), nm - na)
    return best if best and best[0] * sinal > 0 else None
def _canal(v): return "canal " + re.sub(r"\s*\(.*\)", "", str(v).replace(" - ICE LATAM", "")).strip().title()
_SAB_NOME = {"GUARANA": "Guaraná", "LARANJA": "Laranja", "UVA": "Uva", "TONICA": "Tônica"}
def sovi_insights(x, col_grupo, rot_grupo):
    ms = sorted(x.mes.unique()); out = []
    if len(ms) < 2: return out
    def frase(k, a, m, destaque=False):
        nome, filt = SOVI_SER[k]; xa, xm = filt(x[x.mes == a]), filt(x[x.mes == m])
        na, nm = _sovi(xa), _sovi(xm)
        if na is None or nm is None: return None
        d = nm - na; sinal = -1 if d < 0 else 1
        ko = _var(xa[xa.fabricante == "COCA COLA"].frentes.sum(), xm[xm.fabricante == "COCA COLA"].frentes.sum())
        cc = _var(xa[xa.fabricante == "CONCORRENTE"].frentes.sum(), xm[xm.fabricante == "CONCORRENTE"].frentes.sum())
        t = f"{nome} {'caiu' if d < 0 else 'subiu'} {abs(d):.2f} p.p. em {MESES[int(m[5:7])]} ({_pc(na)} → {_pc(nm)})".replace(".", ",", 1)
        if ko is not None and cc is not None:
            t += f". Frentes Coca-Cola {ko:+.0f}% e concorrência {cc:+.0f}%"
        partes = []
        for col, rot in [(col_grupo, rot_grupo), ("canal", _canal)] + ([("sabor", lambda v: "sabor " + _SAB_NOME.get(v, str(v).title()))] if k == "SAB" else []):
            g = _mov(xa, xm, col, rot, sinal)
            if g: partes.append(f"{g[1]} {_pp(g[2])}")
        if partes: t += (". Principais quedas: " if d < 0 else ". Principais altas: ") + " · ".join(partes)
        return {"serie": k, "mes": m, "delta": round(d, 2), "tipo": "queda" if d < 0 else "alta", "destaque": destaque, "texto": t.rstrip(".") + "."}
    for k in SOVI_SER:
        f_ = frase(k, ms[-2], ms[-1])
        if f_: out.append(f_)
    # maior queda do ano (meses anteriores ao atual)
    pior = None
    for k, (nome, filt) in SOVI_SER.items():
        for a, m in zip(ms[:-2], ms[1:-1]):
            na, nm = _sovi(filt(x[x.mes == a])), _sovi(filt(x[x.mes == m]))
            if na is not None and nm is not None and (pior is None or nm - na < pior[0]): pior = (nm - na, k, a, m)
    if pior and pior[0] <= -1:
        f_ = frase(pior[1], pior[2], pior[3], destaque=True)
        if f_: f_["texto"] = "Maior queda do ano: " + f_["texto"]; out.append(f_)
    return out

lbl = lambda m: MESES[int(m[5:7])]
out = {"meses": meses_pesq, "gcs": {}}
for g in ger.itertuples():
    gc = g.gc
    D = {"gc": gc, "nome": g.nome, "compromisso": compromisso.get(gc), "mensal": [], "supervisores": [], "repositor": [], "cpi": [], "tom": []}
    for m in meses_pesq:
        r = {"mes": m, "lbl": lbl(m)}
        for t in ("RED", "ICE"):
            x = pesq[t][(pesq[t].mes == m) & (pesq[t].gc == gc)]
            r[t] = nota(x, t)
            r[t + "_rep"] = nota_repositor(gc, m, t)
        D["mensal"].append(r)
    # supervisores x mês
    svs = sorted(set(pesq_all["ICE"][pesq_all["ICE"].gc == gc].sv) | set(pesq_all["RED"][pesq_all["RED"].gc == gc].sv))
    for sv in svs:
        if sup_nome.get(sv, "").upper().startswith("ROTA"):
            continue
        linha = {"sv": sv, "nome": sup_nome.get(sv, ""), "considerar": sv not in SV_FORA, "meses": {}}
        for m in meses_pesq:
            linha["meses"][m] = {t: nota(pesq_all[t][(pesq_all[t].mes == m) & (pesq_all[t].sv == sv)], t) for t in ("RED", "ICE")}
        D["supervisores"].append(linha)
    # ICE por canal (mês atual vs anterior)
    mi = sorted(pesq["ICE"][pesq["ICE"].gc == gc].mes.unique())
    if mi:
        atual = nota_seg(pesq["ICE"][(pesq["ICE"].mes == mi[-1]) & (pesq["ICE"].gc == gc)])
        ant = nota_seg(pesq["ICE"][(pesq["ICE"].mes == mi[-2]) & (pesq["ICE"].gc == gc)]) if len(mi) > 1 else {}
        D["canal"] = {"mes": mi[-1], "itens": [{"seg": ROTULO_SEG.get(s, s), "nota": atual[s], "var": (atual[s] - ant[s]) if s in ant else None}
                                              for s in ORDEM_SEG if s in atual]}
        # ICE por pilar (kpi), ponderado por segmento, teto 110
        def pil(m):
            x = pesq["ICE"][(pesq["ICE"].mes == m) & (pesq["ICE"].gc == gc)]
            return {k: min(CAP_PILAR, nota(d, "ICE")) for k, d in x.groupby("kpi")}
        pa, pb = pil(mi[-1]), (pil(mi[-2]) if len(mi) > 1 else {})
        D["pilar"] = {"mes": mi[-1], "itens": sorted([{"kpi": k, "nota": v, "var": (v - pb[k]) if k in pb else None} for k, v in pa.items()], key=lambda z: -z["nota"])}
    for c in cpi[cpi.GERENCIA.str.strip() == gc].sort_values("mes").itertuples():
        D["cpi"].append({"mes": c.mes, "lbl": lbl(c.mes), "meta": c.META_CPI * 100, "real": c.REAL_CPI * 100,
                         "vdz": int(c.REAL_VDZ), "inst": int(c.REAL_INSTALÇAO), "perdida": int(c.QTD_EQP_PERD)})
    for t in tom[tom.GERENCIA.str.strip() == gc].sort_values("dt").itertuples():
        if pd.isna(t.dt):
            continue
        D["tom"].append({"lbl": MESES[t.dt.month], "realizou": str(t.TOM).upper(),
                         "data": f"{DIAS[t.dt.weekday()]}, {t.dt.day} de {MESES[t.dt.month]} de {t.dt.year}",
                         "tema": "" if pd.isna(t.TEMA) else str(t.TEMA)})
    _sb = sovi_base[(sovi_base.gc == gc) & ~sovi_base.sv.isin(SV_FORA)]
    D["sovi"] = [{"mes": m, "lbl": lbl(m), **sovi(x)} for m, x in _sb.groupby("mes")]
    D["sovi_insights"] = sovi_insights(_sb, "sv", lambda v: v if (not sup_nome.get(v) or sup_nome[v].upper().startswith("ROTA")) else f"{sup_nome[v].title()} ({v})")
    out["gcs"][gc] = D

json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
an = out["gcs"]["GC. AN"]
print("meses", meses_pesq)
print("AN mensal", [(r["lbl"], r["RED"] and round(r["RED"], 2), r["ICE"] and round(r["ICE"], 2), r["RED_rep"] and round(r["RED_rep"], 2), r["ICE_rep"] and round(r["ICE_rep"], 2)) for r in an["mensal"]])
print("AN canal", [(i["seg"], round(i["nota"], 2), i["var"] and round(i["var"], 2)) for i in an["canal"]["itens"]])
print("AN pilar", [(i["kpi"], round(i["nota"], 2), i["var"] is not None and round(i["var"], 2)) for i in an["pilar"]["itens"]])
print("AN sv", [(s["sv"], s["nome"], {m: {k: v and round(v, 2) for k, v in d.items()} for m, d in s["meses"].items()}) for s in an["supervisores"]])
