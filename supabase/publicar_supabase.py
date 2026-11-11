"""Liga o processamento local (na sua máquina) ao Supabase.

    python publicar_supabase.py baixar-config   → traz do portal os pesos, supervisores e gerentes comerciais cadastrados
    python publicar_supabase.py publicar        → envia notas, insights, ranking, apresentações e os SOVI resumidos
    (baixar-config também traz do Supabase os SOVI resumidos e as planilhas enviadas pela aba Cargas)
    python publicar_supabase.py baixar-bases    → só baixa as planilhas da aba Cargas para dados/bases
  Processamento na nuvem (GitHub Actions, .github/workflows/processar.yml):
    precisa             → sai com código 0 se há carga/alteração pendente no portal (1 se não há)
    status <estado> [mensagem]  → grava no portal o andamento (aguardando, rodando, ok, erro)
    montar-sovi-bruto   → junta as partes do SOVI bruto enviadas pelo portal (BASES/SOVI_BRUTO) em dados/bases/SOVI_BRUTO
    limpar-sovi-bruto   → apaga do Supabase as partes do SOVI bruto que já viraram SOVI resumido
    avisar              → e-mail aos gerentes quando um mês novo é publicado (Outlook pelo Microsoft Graph, ou SMTP)

Variáveis de ambiente (só na máquina de processamento – NUNCA no HTML):
    SUPABASE_URL           ex.: https://xxxx.supabase.co
    SUPABASE_SERVICE_KEY   chave service_role (Project Settings → API)
    PASTA_SAIDA / PASTA_CONFIG   (padrão: gerador/../dados/saida e dados/config)
Só usa a biblioteca padrão do Python.
"""
import os, sys, json, re, time, urllib.request, urllib.error, urllib.parse

AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(AQUI)
SAIDA = os.environ.get("PASTA_SAIDA", os.path.join(BASE, "dados", "saida"))
CONFIG = os.environ.get("PASTA_CONFIG", os.path.join(BASE, "dados", "config"))
SOVI_RES = os.environ.get("SOVI_RESUMIDO", os.path.join(BASE, "dados", "sovi_resumido"))
BUCKET = "apresentacoes"
PASTA_SOVI = "BASES/SOVI"
BASES_DIR = os.environ.get("PASTA_BASES", os.path.join(BASE, "dados", "bases"))
TIPOS_BASE = ["RED", "ICE", "RP", "CPI", "TOM", "COMPROMISSO", "DIM"]   # planilhas enviadas pela aba Cargas do portal          # SOVI resumidos no Storage privado (só administrador e service_role)
PT = {"ICE_MIN": 75, "ICE": 5000, "CPI": 3000, "TOM": 2000, "PLUS": 1000, "INICIO_PLUS": "2026-07"}
MESES = ["", "janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
ROT = ["", "JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]


def slug(gc): return re.sub(r"\s+", "_", re.sub(r"\.\s*", "_", gc))          # "GC. AN" → "GC_AN" (igual ao HTML e à RLS)


def pontos(m, ice, cpi, tom, cp):
    ok_i = ice is not None and ice >= PT["ICE_MIN"]; ok_c = bool(cpi and cpi["real"] >= cpi["meta"]); ok_t = bool(tom and tom["realizou"] == "SIM")
    plus = cp is not None and ice is not None and m >= PT["INICIO_PLUS"] and ice >= cp
    return ok_i * PT["ICE"] + ok_c * PT["CPI"] + ok_t * PT["TOM"] + plus * PT["PLUS"]


def ranking_gc(PD):
    """pontos e ICE por GC e mês (o portal agrupa por gerente comercial e faz a média quando há 2+ GCs)"""
    out = []
    for g, G in PD["gcs"].items():
        for m in PD["meses"]:
            r = next((x for x in G["mensal"] if x["mes"] == m), {}) or {}
            c = next((x for x in G["cpi"] if x["mes"] == m), None); t = next((x for x in G["tom"] if x["lbl"] == MESES[int(m[5:7])]), None)
            if r.get("ICE") is None: continue          # gerência sem pesquisa de ICE no mês fica fora da média do gerente
            out.append({"mes": m, "gc": g, "pts": pontos(m, r.get("ICE"), c, t, G.get("compromisso")), "ice": r.get("ICE")})
    return out


def pacote_decks(idx):
    ref = idx["ref"]
    return {"ref": ref, "rotulo": ROT[int(ref[5:7])] + ref[2:4], "geral": "EMPRESA/" + idx["geral"],
            "gcs": {g: f"{slug(g)}/{a}" for g, a in idx["gcs"].items()}}


# ---------------------------------------------------------------- REST do Supabase (service_role)
_CRED = None


def cred():
    """Lê URL e chave do segredos.bat, limpa espaços/aspas e confere se a chave é mesmo a service_role do projeto."""
    global _CRED
    if _CRED: return _CRED
    limpa = lambda v: re.sub(r"\s+", "", (v or "")).strip("\"'")
    url, key = limpa(os.environ.get("SUPABASE_URL")).rstrip("/"), limpa(os.environ.get("SUPABASE_SERVICE_KEY"))
    if not url or not key or "COLE_AQUI" in key or "SEU-PROJETO" in url:
        sys.exit("Preencha SUPABASE_URL e SUPABASE_SERVICE_KEY (chave service_role) no segredos.bat.")
    if key.startswith("sb_publishable_"):
        sys.exit("A chave do segredos.bat é a 'publishable' (pública). Use a service_role: Project Settings > API Keys > Legacy > service_role > Reveal.")
    if key.startswith("eyJ"):
        try:
            import base64
            parte = key.split(".")[1]; parte += "=" * (-len(parte) % 4)
            info = json.loads(base64.urlsafe_b64decode(parte))
        except Exception:
            sys.exit(f"A chave do segredos.bat está incompleta ou com caracteres a mais ({len(key)} caracteres). Copie de novo com o botão Copy.")
        if info.get("role") != "service_role":
            sys.exit(f"A chave do segredos.bat é a '{info.get('role')}', não a service_role. Copie a de baixo (service_role > Reveal > Copy).")
        ref = re.search(r"https://([a-z0-9]+)\.supabase\.co", url)
        if ref and info.get("ref") and info["ref"] != ref.group(1):
            sys.exit(f"A chave é do projeto '{info['ref']}', mas a URL é do projeto '{ref.group(1)}'. Use a chave do mesmo projeto.")
        if key.count(".") != 2 or len(key) < 150:
            sys.exit(f"A chave do segredos.bat parece cortada ({len(key)} caracteres). Copie de novo com o botão Copy.")
    elif not key.startswith("sb_secret_"):
        sys.exit("A chave do segredos.bat não parece uma chave do Supabase. Copie a service_role (começa com eyJ) com o botão Copy.")
    _CRED = (url, key)
    return _CRED


def req(metodo, caminho, corpo=None, tipo="application/json", extra=None):
    url, key = cred()
    h = {"apikey": key, **({} if key.startswith("sb_secret_") else {"Authorization": f"Bearer {key}"}), **(extra or {})}
    dados = None
    if corpo is not None:
        dados = corpo if isinstance(corpo, (bytes, bytearray)) else json.dumps(corpo, ensure_ascii=False).encode()
        h["Content-Type"] = tipo
    for tentativa in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url + caminho, data=dados, method=metodo, headers=h), timeout=120) as r:
                b = r.read(); return json.loads(b) if b and "json" in r.headers.get("Content-Type", "") else b
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:400]
            if e.code >= 500 and tentativa < 2: time.sleep(2); continue
            raise SystemExit(f"Supabase {metodo} {caminho.split('?')[0]} → {e.code}: {msg}")


def upsert(tabela, linhas, conflito=None, ignorar=False):
    pref = "resolution=ignore-duplicates" if ignorar else "resolution=merge-duplicates"
    q = f"?on_conflict={conflito}" if conflito else ""
    for i in range(0, len(linhas), 25):
        req("POST", f"/rest/v1/{tabela}{q}", linhas[i:i + 25], extra={"Prefer": pref + ",return=minimal"})


def sovi_nuvem():
    """lista os SOVI resumidos guardados no Supabase: {nome: tamanho}"""
    L = req("POST", f"/storage/v1/object/list/{BUCKET}", {"prefix": PASTA_SOVI, "limit": 1000}) or []
    return {x["name"]: (x.get("metadata") or {}).get("size") for x in L if x.get("name", "").upper().startswith("SOVI_RESUMIDO_")}


def listar(prefixo):
    L = req("POST", f"/storage/v1/object/list/{BUCKET}", {"prefix": prefixo, "limit": 1000}) or []
    return {x["name"]: (x.get("metadata") or {}).get("size") for x in L if x.get("name") and x.get("id")}


def baixar_bases():
    """espelha em dados/bases as planilhas enviadas pela aba Cargas (BASES/<tipo>/) · o que foi excluído no portal sai daqui também"""
    n = 0
    for t in TIPOS_BASE:
        nuvem = listar(f"BASES/{t}")
        pasta = os.path.join(BASES_DIR, t); os.makedirs(pasta, exist_ok=True)
        for nome, tam in nuvem.items():
            local = os.path.join(pasta, nome)
            if os.path.exists(local) and (tam is None or os.path.getsize(local) == tam):
                continue
            open(local, "wb").write(req("GET", f"/storage/v1/object/{BUCKET}/BASES/{t}/" + urllib.parse.quote(nome)))
            print(f"  planilha do portal → {t}/{nome}"); n += 1
        for nome in os.listdir(pasta):
            if nome not in nuvem and nome.lower().endswith(".xlsx"):
                os.remove(os.path.join(pasta, nome)); print(f"  removida (excluída no portal) → {t}/{nome}")
    return n


def baixar_sovi():
    os.makedirs(SOVI_RES, exist_ok=True)
    n = 0
    for nome, tam in sovi_nuvem().items():
        local = os.path.join(SOVI_RES, nome)
        if os.path.exists(local) and (tam is None or os.path.getsize(local) == tam):
            continue
        open(local, "wb").write(req("GET", f"/storage/v1/object/{BUCKET}/{PASTA_SOVI}/" + urllib.parse.quote(nome)))
        print("  SOVI resumido baixado do portal →", nome); n += 1
    return n


def enviar_sovi():
    if not os.path.isdir(SOVI_RES):
        return 0
    nuvem, n = sovi_nuvem(), 0
    for nome in sorted(os.listdir(SOVI_RES)):
        if not nome.upper().startswith("SOVI_RESUMIDO_") or not nome.lower().endswith(".xlsx"):
            continue
        local = os.path.join(SOVI_RES, nome)
        if nuvem.get(nome) == os.path.getsize(local):
            continue
        req("POST", f"/storage/v1/object/{BUCKET}/{PASTA_SOVI}/" + urllib.parse.quote(nome), open(local, "rb").read(),
            tipo="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", extra={"x-upsert": "true"})
        print("   ", f"{PASTA_SOVI}/{nome}"); n += 1
    return n


# ---------------------------------------------------------------- comandos
def baixar_config():
    os.makedirs(CONFIG, exist_ok=True)
    C = {r["chave"]: r["valor"] for r in req("GET", "/rest/v1/config?select=chave,valor")}
    linhas = req("GET", "/rest/v1/gerencias?select=gc,nome_gerente,genero")
    G = {r["gc"]: r["nome_gerente"] or "" for r in linhas}
    GEN = {r["gc"]: r["genero"] for r in linhas if r.get("genero") in ("M", "F")}
    if not any(G.values()):   # primeira carga: nomes guardados na configuração (o repositório público não leva nomes)
        G = C.get("nomes_gerentes") or G
        GEN = {**(C.get("generos_gc") or {}), **GEN}
    if C.get("genero_empresa") in ("M", "F"): GEN["EMPRESA"] = C["genero_empresa"]
    for nome, v in (("pesos.json", C.get("pesos")), ("supervisores.json", C.get("supervisores")), ("gerencias.json", G or None), ("generos.json", GEN or None)):
        if v:
            json.dump(v, open(os.path.join(CONFIG, nome), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print("  configuração do portal →", nome)
    baixar_sovi()
    baixar_bases()


def publicar():
    PD = json.load(open(os.path.join(SAIDA, "portal_data.json"), encoding="utf-8"))
    INS = json.load(open(os.path.join(SAIDA, "insights.json"), encoding="utf-8"))
    idx = json.load(open(os.path.join(SAIDA, "decks", "indice.json"), encoding="utf-8"))
    ler = lambda n: json.load(open(os.path.join(CONFIG, n), encoding="utf-8")) if os.path.exists(os.path.join(CONFIG, n)) else None
    print("1/6 gerências e configuração inicial")
    nomes = ler("gerencias.json") or {}
    gen = ler("generos.json") or {}
    upsert("gerencias", [{"gc": g, "nome_gerente": nomes.get(g, G.get("nome", "")), "genero": gen.get(g, "")} for g, G in PD["gcs"].items()], "gc", ignorar=True)
    iniciais = [{"chave": "pesos", "valor": ler("pesos.json") or PD.get("pesos")}, {"chave": "supervisores", "valor": ler("supervisores.json") or PD.get("supervisores_cfg") or {}},
                {"chave": "ranking_publico", "valor": True}, {"chave": "genero_empresa", "valor": gen.get("EMPRESA", "M")}]
    upsert("config", iniciais, "chave", ignorar=True)
    print("2/6 dados por gerência")
    upsert("dados_gc", [{"gc": g, "payload": G} for g, G in PD["gcs"].items()], "gc")
    upsert("dados_empresa", [{"id": 1, "payload": {k: PD.get(k) for k in ("empresa", "empresa_canal", "empresa_pilar")}}], "id")
    print("3/6 insights")
    if INS.get("parcial"):   # só o último mês foi recalculado: os insights dos meses anteriores ficam como estão
        for m in INS["por_mes"]: req("DELETE", f"/rest/v1/insights?mes=eq.{m}", extra={"Prefer": "return=minimal"})
    else:
        req("DELETE", "/rest/v1/insights?mes=neq.__", extra={"Prefer": "return=minimal"})
    upsert("insights", [{"mes": m, "escopo": e, "payload": v} for m, R in INS["por_mes"].items() for e, v in R.items()], "mes,escopo")
    print("4/6 ranking")
    req("DELETE", "/rest/v1/ranking_gc?mes=neq.__", extra={"Prefer": "return=minimal"})
    upsert("ranking_gc", ranking_gc(PD), "mes,gc")
    print("5/6 apresentações")
    dk = pacote_decks(idx); pasta = os.path.join(SAIDA, "decks")
    arqs = [(dk["geral"], idx["geral"])] + [(dk["gcs"][g], a) for g, a in idx["gcs"].items()]
    for destino, local in arqs:
        req("POST", f"/storage/v1/object/{BUCKET}/" + urllib.parse.quote(destino), open(os.path.join(pasta, local), "rb").read(),
            tipo="application/vnd.openxmlformats-officedocument.presentationml.presentation", extra={"x-upsert": "true"})
        print("   ", destino)
    print("   SOVI resumidos (backup para outras máquinas)")
    enviar_sovi()
    print("6/6 publicação")
    # histórico: as apresentações de meses anteriores continuam no Storage e podem ser baixadas no portal
    antes = (req("GET", "/rest/v1/portal_meta?select=payload&id=eq.1") or [{}])[0].get("payload") or {}
    hist = dict(antes.get("decks_hist") or {})
    if (antes.get("decks") or {}).get("ref"): hist[antes["decks"]["ref"]] = antes["decks"]
    hist[dk["ref"]] = dk
    upsert("portal_meta", [{"id": 1, "payload": {"meses": PD["meses"], "ano": PD.get("ano"), "pontos_regra": PT, "decks": dk, "decks_hist": hist},
                            "publicado_em": time.strftime("%Y-%m-%dT%H:%M:%S%z")}], "id")
    upsert("config", [{"chave": "pendente", "valor": False}, {"chave": "carga_pendente", "valor": False}], "chave")
    print("Portal atualizado.")


# ---------------------------------------------------------------- processamento na nuvem
PASTA_BRUTO = "BASES/SOVI_BRUTO"


def cfg(chave, padrao=None):
    r = req("GET", f"/rest/v1/config?chave=eq.{chave}&select=valor") or []
    return r[0]["valor"] if r else padrao


def precisa():
    pend = [k for k in ("carga_pendente", "pendente", "processar_agora", "aviso_email_forcar") if cfg(k, False) is True]
    print("pendente:", ", ".join(pend) if pend else "nada")
    return bool(pend)


def gravar_status(estado, msg=""):
    v = {"estado": estado, "msg": msg[-1500:], "quando": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    run = os.environ.get("GITHUB_RUN_ID")
    if run and os.environ.get("GITHUB_REPOSITORY"):
        v["log"] = f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{run}"
    linhas = [{"chave": "status_nuvem", "valor": v}]
    if estado == "rodando":      # o que chegar durante o processamento dispara uma nova rodada
        linhas += [{"chave": k, "valor": False} for k in ("carga_pendente", "pendente", "processar_agora")]
    upsert("config", linhas, "chave")
    print("status:", estado, msg[:200])


def partes_bruto():
    """{arquivo: [partes em ordem]} das partes 'Outubro-26.xlsx.part001' enviadas pelo portal"""
    G = {}
    for nome in listar(PASTA_BRUTO):
        m = re.match(r"(.+\.xlsx)\.part(\d{3})$", nome, re.I)
        if m: G.setdefault(m.group(1), []).append(nome)
    return {k: sorted(v) for k, v in G.items()}


def montar_sovi_bruto():
    pasta = os.path.join(BASES_DIR, "SOVI_BRUTO"); os.makedirs(pasta, exist_ok=True)
    n = 0
    for arq, partes in partes_bruto().items():
        nums = [int(x[-3:]) for x in partes]
        if nums != list(range(1, len(nums) + 1)):
            print(f"  [AVISO] {arq}: partes incompletas {nums}, ignorado até o envio terminar"); continue
        with open(os.path.join(pasta, arq), "wb") as f:
            for x in partes:
                f.write(req("GET", f"/storage/v1/object/{BUCKET}/{PASTA_BRUTO}/" + urllib.parse.quote(x)))
        print(f"  SOVI bruto montado → {arq} ({os.path.getsize(os.path.join(pasta, arq)) / 1e6:.0f} MB, {len(partes)} partes)"); n += 1
    return n


def limpar_sovi_bruto():
    """apaga as partes cujo SOVI resumido já está no Supabase (o bruto não fica guardado: só o resumo)"""
    nuvem, apagar = sovi_nuvem(), []
    for arq, partes in partes_bruto().items():
        if f"SOVI_RESUMIDO_{os.path.splitext(arq)[0]}.xlsx" in nuvem:
            apagar += [f"{PASTA_BRUTO}/{x}" for x in partes]
    if apagar:
        req("DELETE", f"/storage/v1/object/{BUCKET}", {"prefixes": apagar})
    print(f"{len(apagar)} parte(s) do SOVI bruto apagada(s) do Supabase.")


# ---------------------------------------------------------------- aviso por e-mail aos gerentes
def _dt_br(v):
    try:
        import datetime as dt
        d = dt.datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        if d.tzinfo: d = d.astimezone(dt.timezone(dt.timedelta(hours=-3)))
        return d.strftime("%d/%m às %H:%M")
    except Exception:
        return str(v)


def _corpo(nome, gcs, ref, link, prazo):
    import html
    m = int(ref[5:7]); rot = f"{MESES[m].capitalize()}/{ref[2:4]}"
    lista = ", ".join(gcs)
    pz = (f'<p style="margin:0 0 14px">Envie a versão final pelo portal até <b>{html.escape(prazo)}</b>.</p>' if prazo else "")
    h = f"""<div style="font-family:Segoe UI,Arial,sans-serif;max-width:560px;margin:auto;color:#1f2937">
<div style="background:#c8102e;color:#fff;padding:18px 22px;border-radius:10px 10px 0 0;font-size:18px;font-weight:600">Portal Execução</div>
<div style="border:1px solid #e5e7eb;border-top:0;padding:22px;border-radius:0 0 10px 10px">
<p style="margin:0 0 14px">Olá, {html.escape(nome.split()[0].title() if nome else "")}!</p>
<p style="margin:0 0 14px">A apresentação de <b>{rot}</b> de <b>{html.escape(lista)}</b> já está pronta no Portal Execução, com os indicadores atualizados (RED, ICE, SOVI, pontuação e ranking).</p>
{pz}<p style="margin:22px 0"><a href="{link}" style="background:#c8102e;color:#fff;text-decoration:none;padding:12px 22px;border-radius:8px;font-weight:600">Abrir o portal</a></p>
<p style="margin:0;color:#6b7280;font-size:13px">Entre com o seu e-mail e senha. Este é um aviso automático: não precisa responder.</p></div></div>"""
    txt = (f"Olá!\n\nA apresentação de {rot} de {lista} já está pronta no Portal Execução.\n"
           + (f"Envie a versão final pelo portal até {prazo}.\n" if prazo else "") + f"\nAcesse: {link}\n")
    return f"Portal Execução · apresentação de {rot} pronta", txt, h


class _Graph:
    """Outlook / Microsoft 365 pelo Microsoft Graph (OAuth, o jeito que a Microsoft mantém).
    Segredos: OUTLOOK_TENANT_ID, OUTLOOK_CLIENT_ID, OUTLOOK_CLIENT_SECRET e OUTLOOK_REMETENTE (caixa que envia)."""
    def __init__(self):
        e = os.environ
        self.tenant, self.cid, self.sec, self.de = (e.get(k, "").strip() for k in ("OUTLOOK_TENANT_ID", "OUTLOOK_CLIENT_ID", "OUTLOOK_CLIENT_SECRET", "OUTLOOK_REMETENTE"))
        corpo = urllib.parse.urlencode({"client_id": self.cid, "client_secret": self.sec, "scope": "https://graph.microsoft.com/.default", "grant_type": "client_credentials"}).encode()
        try:
            with urllib.request.urlopen(urllib.request.Request(f"https://login.microsoftonline.com/{self.tenant}/oauth2/v2.0/token", data=corpo), timeout=60) as r:
                self.tok = json.loads(r.read())["access_token"]
        except urllib.error.HTTPError as x:
            raise RuntimeError(f"Microsoft recusou o acesso: {x.read().decode(errors='replace')[:300]}")
    def enviar(self, para, assunto, txt, h):
        msg = {"message": {"subject": assunto, "body": {"contentType": "HTML", "content": h}, "toRecipients": [{"emailAddress": {"address": para}}]}, "saveToSentItems": True}
        rq = urllib.request.Request(f"https://graph.microsoft.com/v1.0/users/{urllib.parse.quote(self.de)}/sendMail", data=json.dumps(msg).encode(),
                                    headers={"Authorization": f"Bearer {self.tok}", "Content-Type": "application/json"})
        try: urllib.request.urlopen(rq, timeout=60).read()
        except urllib.error.HTTPError as x: raise RuntimeError(x.read().decode(errors="replace")[:300])
    def fechar(self): pass


class _Smtp:
    """Outlook por SMTP (smtp.office365.com:587) com e-mail e senha. A Microsoft está desligando esse modo
    (desligado por padrão a partir do fim de 2026): use enquanto a sua TI permitir. Também serve para Gmail (SMTP_HOST=smtp.gmail.com)."""
    def __init__(self):
        import smtplib, ssl
        e = os.environ
        self.de = (e.get("EMAIL_USER") or e.get("GMAIL_USER") or "").strip()
        senha = (e.get("EMAIL_PASSWORD") or re.sub(r"\s+", "", e.get("GMAIL_APP_PASSWORD", ""))).strip()
        host = e.get("SMTP_HOST", "").strip() or ("smtp.gmail.com" if self.de.endswith("@gmail.com") else "smtp.office365.com")
        porta = int(e.get("SMTP_PORT", "").strip() or 587)
        self.s = smtplib.SMTP(host, porta, timeout=60); self.s.starttls(context=ssl.create_default_context()); self.s.login(self.de, senha)
    def enviar(self, para, assunto, txt, h):
        from email.message import EmailMessage
        from email.utils import formataddr
        m = EmailMessage(); m["Subject"] = assunto; m["From"] = formataddr(("Portal Execução", self.de)); m["To"] = para
        m.set_content(txt); m.add_alternative(h, subtype="html"); self.s.send_message(m)
    def fechar(self):
        try: self.s.quit()
        except Exception: pass


def _remetente():
    e = os.environ
    if all(e.get(k, "").strip() for k in ("OUTLOOK_TENANT_ID", "OUTLOOK_CLIENT_ID", "OUTLOOK_CLIENT_SECRET", "OUTLOOK_REMETENTE")): return _Graph
    if (e.get("EMAIL_USER") and e.get("EMAIL_PASSWORD")) or (e.get("GMAIL_USER") and e.get("GMAIL_APP_PASSWORD")): return _Smtp
    return None


def avisar():
    desliga = lambda: upsert("config", [{"chave": "aviso_email_forcar", "valor": False}], "chave")   # nunca deixa o robô em laço
    Classe = _remetente()
    if not Classe:
        desliga(); print("Aviso por e-mail: remetente não configurado no GitHub (Outlook: OUTLOOK_TENANT_ID, OUTLOOK_CLIENT_ID, OUTLOOK_CLIENT_SECRET, OUTLOOK_REMETENTE; ou EMAIL_USER e EMAIL_PASSWORD). Nada enviado."); return 0
    if cfg("aviso_email_ativo", True) is False:
        desliga(); print("Aviso por e-mail desligado no Painel (Configurações)."); return 0
    meta = req("GET", "/rest/v1/portal_meta?select=payload&id=eq.1") or []
    if not meta: print("Nada publicado ainda."); return 0
    ref = meta[0]["payload"]["meses"][-1]
    forcar = cfg("aviso_email_forcar", False) is True
    if cfg("aviso_email_ref") == ref and not forcar:     # só avisa quando chega um mês novo (reprocessar o mesmo mês não manda de novo)
        print(f"Os gerentes já foram avisados de {ref}."); return 0
    perfis = req("GET", "/rest/v1/perfis?select=id,nome,email,perfil,ativo,pode_ver&ativo=eq.true&pode_ver=eq.true&perfil=eq.usuario") or []
    vinc = req("GET", "/rest/v1/usuario_gc?select=usuario_id,gc") or []
    gcs = {}
    for v in vinc: gcs.setdefault(v["usuario_id"], []).append(v["gc"])
    dest = [(p["nome"], p["email"], sorted(gcs[p["id"]])) for p in perfis if gcs.get(p["id"]) and p.get("email")]
    if not dest:
        desliga(); print("Nenhum gerente com e-mail e gerência cadastrados no portal. Nada enviado."); return 0
    P = cfg("prazo_envio") or {}
    fecha = P.get("fecha")
    prazo = _dt_br(fecha) if fecha and fecha > time.strftime("%Y-%m-%dT%H:%M") else ""
    link = os.environ.get("PORTAL_URL", "").strip() or "https://execucaoband.github.io/portal-execucao/"
    log = lambda n, f: upsert("config", [{"chave": "aviso_email_log", "valor": {"ref": ref, "quando": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "enviados": n, "falhas": f[:20]}}], "chave")
    try:
        env = Classe()
    except Exception as e:
        desliga(); log(0, [f"o servidor de e-mail recusou o acesso: {e}"])
        raise SystemExit(f"O servidor de e-mail recusou o acesso ({e}). Confira os segredos no GitHub.")
    ok, falhas = [], []
    for nome, email, g in dest:
        assunto, txt, h = _corpo(nome, g, ref, link, prazo)
        try: env.enviar(email, assunto, txt, h); ok.append(email)
        except Exception as e: falhas.append(f"{email}: {e}")
    env.fechar()
    upsert("config", [{"chave": "aviso_email_ref", "valor": ref}, {"chave": "aviso_email_forcar", "valor": False}], "chave")
    log(len(ok), falhas)
    print(f"Aviso de {ref}: {len(ok)} e-mail(s) enviado(s)" + (f", {len(falhas)} falha(s): {falhas}" if falhas else "."))
    return len(ok)

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "baixar-config": baixar_config()
    elif cmd == "publicar": publicar()
    elif cmd == "enviar-sovi": print(f"{enviar_sovi()} SOVI resumido(s) enviado(s) ao Supabase ({PASTA_SOVI}).")
    elif cmd == "baixar-bases": print(f"{baixar_bases()} planilha(s) baixada(s) da aba Cargas do portal."); baixar_sovi()
    elif cmd == "baixar-sovi": print(f"{baixar_sovi()} SOVI resumido(s) baixado(s) do Supabase.")
    elif cmd == "precisa": sys.exit(0 if precisa() else 1)
    elif cmd == "status": gravar_status(sys.argv[2], " ".join(sys.argv[3:]))
    elif cmd == "montar-sovi-bruto": print(f"{montar_sovi_bruto()} SOVI bruto(s) montado(s).")
    elif cmd == "limpar-sovi-bruto": limpar_sovi_bruto()
    elif cmd == "avisar": avisar()
    else: print(__doc__)
