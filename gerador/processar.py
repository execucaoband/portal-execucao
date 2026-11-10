"""Processamento mensal: arquivos → resumos → notas → insights → apresentações.

Etapas
  1. SOVI: cada planilha bruta do SOVI (aba RED360) vira um resumo pequeno (cache por nome+tamanho+data);
     o conjunto vira CONFIG/SOVI_RESUMO.pkl (+ .xlsx para conferência)
  2. dados_deck.py   → SAIDA/deck_data.json   (notas por GC, supervisor, canal, pilar, CPI, TOM, SOVI…)
  3. portal_data.py  → SAIDA/portal_data.json + resumo_data.json (empresa, pesos, pontos por segmento)
  4. insights.py     → SAIDA/insights.json
  5. node deck_corp.js / deck_resumo.js → SAIDA/decks/*.pptx

Uso (o servidor chama sozinho):  python processar.py
Variáveis: DADOS_DIR (pastas separadas por ';' no Windows / ':' no Linux), CONFIG_DIR, SAIDA_DIR, ANO
"""
import os, sys, json, glob, subprocess, time, shutil, hashlib, traceback

AQUI = os.path.dirname(os.path.abspath(__file__))
DADOS = os.environ.get("DADOS_DIR", os.path.join(AQUI, "..", "dados", "arquivos"))
CONFIG = os.environ.get("CONFIG_DIR", os.path.join(AQUI, "..", "dados", "config"))
SAIDA = os.environ.get("SAIDA_DIR", os.path.join(AQUI, "..", "dados", "saida"))
SOVI_CACHE = os.environ.get("SOVI_CACHE", os.path.join(AQUI, "..", "dados", "sovi_resumos"))
STATUS = os.path.join(SAIDA, "status_processamento.json")
ANO = os.environ.get("ANO", "")


def status(etapa, ok=None, msg="", **kw):
    st = {"etapa": etapa, "ok": ok, "msg": msg, "quando": time.strftime("%Y-%m-%d %H:%M:%S"), **kw}
    os.makedirs(SAIDA, exist_ok=True)
    json.dump(st, open(STATUS, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"[{st['quando']}] {etapa} {msg}", flush=True)


def env():
    e = dict(os.environ, DADOS_DIR=DADOS, CONFIG_DIR=CONFIG, SAIDA_DIR=SAIDA, CACHE_DIR=os.path.join(AQUI, "..", "dados", "cache"), PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    if ANO: e["ANO"] = ANO
    return e


def run(cmd):
    if cmd and cmd[0] == sys.executable and "-X" not in cmd:   # -I ignora PYTHONIOENCODING; -X utf8 vale sempre (Windows cp1252)
        cmd = [cmd[0], "-X", "utf8"] + cmd[1:]
    r = subprocess.run(cmd, cwd=AQUI, env=env(), capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd[:2])} falhou:\n{(r.stderr or r.stdout)[-2500:]}")
    return r.stdout


def eh_sovi(path):
    try:
        from python_calamine import CalamineWorkbook
        return "RED360" in CalamineWorkbook.from_path(path).sheet_names
    except Exception:
        return False


SOVI_RESUMIDO = os.environ.get("SOVI_RESUMIDO", os.path.join(AQUI, "..", "dados", "sovi_resumido"))
COLS_RES = ["mes", "Gerencia", "Supervisao", "Canal", "Categoria", "Sabor", "Fabricante", "AREA", "Ponto de Contato"]


def gravar_resumido(pkl, base):
    """SOVI resumido do mês (só refrigerante e suco, frentes somadas): de ~130 MB para < 1 MB · pode ir para o Supabase"""
    import pandas as pd
    d = pd.read_pickle(pkl)
    if "Ponto de Contato" not in d: d["Ponto de Contato"] = "-"
    r = d[d.Categoria.isin(["REFRIGERANTE", "SUCO"])].groupby(COLS_RES, dropna=False).frentes.sum().reset_index()
    os.makedirs(SOVI_RESUMIDO, exist_ok=True)
    dest = os.path.join(SOVI_RESUMIDO, f"SOVI_RESUMIDO_{base}.xlsx")
    r.to_excel(dest, index=False, sheet_name="SOVI_RESUMIDO")
    return dest


def etapa_sovi():
    """SOVI: planilhas brutas (aba RED360) e/ou SOVI resumidos → cache por arquivo → CONFIG/SOVI_RESUMO.pkl"""
    import pandas as pd
    os.makedirs(SOVI_CACHE, exist_ok=True)
    pastas = [p for p in DADOS.split(os.pathsep) if p.strip()]
    brutos, resumidos = [], {}
    for d in pastas + [SOVI_RESUMIDO]:
        for x in glob.glob(os.path.join(d, "**", "*.xlsx"), recursive=True):
            b = os.path.basename(x)
            if b.startswith("~$"):
                continue
            if b.upper().startswith("SOVI_RESUMIDO_"):
                base = os.path.splitext(b)[0][len("SOVI_RESUMIDO_"):]
                if base not in resumidos or os.path.getmtime(x) > os.path.getmtime(resumidos[base]):
                    resumidos[base] = x
                continue
            if d == SOVI_RESUMIDO or b.upper().startswith(("FATOS_", "DIM_", "SOVI_RESUMO", "BASE_RP", "COMPROMISSO", "TOM")):
                continue
            if ANO and ANO[2:] not in b:            # só arquivos do ano (ex.: "-26")
                continue
            if "SOVI" in x.upper() or os.path.getsize(x) > 40e6:
                brutos.append(x)
    novos = 0
    bases_brutas = set()
    for x in brutos:
        base = os.path.splitext(os.path.basename(x))[0]
        st = os.stat(x); chave = hashlib.md5(f"{os.path.basename(x)}{st.st_size}{int(st.st_mtime)}".encode()).hexdigest()[:12]
        destino = os.path.join(SOVI_CACHE, f"{base}__{chave}.pkl")
        if os.path.exists(destino):
            bases_brutas.add(base)
            if not os.path.exists(os.path.join(SOVI_RESUMIDO, f"SOVI_RESUMIDO_{base}.xlsx")):
                gravar_resumido(destino, base)
            continue
        if not eh_sovi(x):
            continue
        status("sovi", None, f"resumindo {os.path.basename(x)}")
        for velho in glob.glob(os.path.join(SOVI_CACHE, f"{base}__*.pkl")):
            os.remove(velho)
        run([sys.executable, "-I", os.path.join(AQUI, "resumir_sovi.py"), x, destino])
        r = gravar_resumido(destino, base)
        status("sovi", None, f"SOVI resumido: {os.path.basename(r)} ({os.path.getsize(r) / 1e6:.1f} MB)")
        bases_brutas.add(base); novos += 1
        if os.path.abspath(os.path.dirname(x)) == os.path.abspath(os.path.join(AQUI, "..", "dados", "arquivos")):
            os.remove(x)                              # bruto enviado pela tela de Cargas: fica só o resumo
    # SOVI resumidos sem o bruto neste computador (ex.: baixados do Supabase por outra pessoa)
    for base, x in resumidos.items():
        if base in bases_brutas or any(not os.path.basename(p).split("__")[-1].startswith("R") for p in glob.glob(os.path.join(SOVI_CACHE, f"{base}__*.pkl"))):
            continue
        st = os.stat(x); chave = "R" + hashlib.md5(f"{st.st_size}{int(st.st_mtime)}".encode()).hexdigest()[:11]
        destino = os.path.join(SOVI_CACHE, f"{base}__{chave}.pkl")
        if os.path.exists(destino):
            continue
        for velho in glob.glob(os.path.join(SOVI_CACHE, f"{base}__R*.pkl")):
            os.remove(velho)
        d = pd.read_excel(x, dtype={c: str for c in COLS_RES})
        d["frentes"] = pd.to_numeric(d.frentes, errors="coerce").fillna(0)
        d.fillna("-").to_pickle(destino)
        status("sovi", None, f"usando SOVI resumido {os.path.basename(x)}"); novos += 1
    pk = glob.glob(os.path.join(SOVI_CACHE, "*.pkl"))
    if not pk:
        return 0
    if not novos and os.path.exists(os.path.join(CONFIG, "SOVI_RESUMO.pkl")):
        return 0
    # mesmo mês em mais de um arquivo: vale o arquivo processado por último (nunca soma em dobro)
    partes, dono = [], {}
    for p in sorted(pk, key=os.path.getmtime):
        x = pd.read_pickle(p); x["_arq"] = p
        for m in x.mes.dropna().astype(str).unique(): dono[m] = p
        partes.append(x)
    r = pd.concat(partes, ignore_index=True)
    r = r[r.mes.astype(str).map(dono) == r._arq]
    if ANO: r = r[r.mes.astype(str).str.startswith(ANO)]
    r = r[r.Categoria.isin(["REFRIGERANTE", "SUCO"])].copy()
    r["fabricante_ko"] = r.Fabricante.map(lambda f: "COCA COLA" if f == "COCA COLA" else ("-" if f == "-" else "CONCORRENTE"))
    if "Ponto de Contato" not in r: r["Ponto de Contato"] = "-"
    g = r.groupby(["mes", "Gerencia", "Supervisao", "Canal", "Categoria", "Sabor", "fabricante_ko", "Fabricante", "AREA", "Ponto de Contato"], dropna=False).frentes.sum().reset_index()
    g.columns = ["mes", "gc", "sv", "canal", "categoria", "sabor", "fabricante", "fabricante_nome", "area", "ponto", "frentes"]
    g.to_pickle(os.path.join(CONFIG, "SOVI_RESUMO.pkl"))
    g.to_excel(os.path.join(CONFIG, "SOVI_RESUMO.xlsx"), index=False)
    return novos


def gerar_decks():
    sys.path.insert(0, AQUI)
    d = json.load(open(os.path.join(SAIDA, "deck_data.json"), encoding="utf-8"))
    ref = d["meses"][-1]
    mes = ["", "JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"][int(ref[5:7])] + ref[2:4]
    pasta = os.path.join(SAIDA, "decks"); tmp = pasta + "_novo"
    shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    run([sys.executable, os.path.join(AQUI, "montar_resumo.py")])
    idx = {"ref": ref, "gcs": {}}
    for gc in d["gcs"]:
        nome = f"Merchandising_{gc.replace('.', '').replace(' ', '')}_{mes}.pptx"
        status("apresentacoes", None, f"gerando {gc}")
        run(["node", os.path.join(AQUI, "deck_corp.js"), os.path.join(SAIDA, "deck_data.json"), gc, os.path.join(tmp, nome)])
        idx["gcs"][gc] = nome
    idx["geral"] = f"Resultado_Geral_{mes}.pptx"
    run(["node", os.path.join(AQUI, "deck_resumo.js"), os.path.join(SAIDA, "resumo_data.json"), os.path.join(tmp, idx["geral"])])
    status("apresentacoes", None, "transformando gráficos e tabelas em imagem (não editáveis)")
    from achatar_ppt import achatar
    modo = achatar([os.path.join(tmp, a) for a in list(idx["gcs"].values()) + [idx["geral"]]])
    status("apresentacoes", None, f"imagens geradas com {modo}")
    json.dump(idx, open(os.path.join(tmp, "indice.json"), "w", encoding="utf-8"), ensure_ascii=False)
    shutil.rmtree(pasta + "_antigo", ignore_errors=True)
    if os.path.exists(pasta): os.rename(pasta, pasta + "_antigo")
    os.rename(tmp, pasta)
    shutil.rmtree(pasta + "_antigo", ignore_errors=True)


def processar(so_apresentacoes=False):
    t0 = time.time()
    try:
        if not so_apresentacoes:
            status("sovi", None, "verificando planilhas do SOVI")
            etapa_sovi()
            status("notas", None, "calculando RED, ICE, repositor, CPI, TOM, SOVI")
            run([sys.executable, os.path.join(AQUI, "dados_deck.py"), DADOS, os.path.join(SAIDA, "deck_data.json")])
            status("portal", None, "consolidando empresa e pontuação")
            run([sys.executable, os.path.join(AQUI, "portal_data.py")])
            status("insights", None, "gerando insights")
            run([sys.executable, os.path.join(AQUI, "insights.py")])
        status("apresentacoes", None, "gerando apresentações")
        gerar_decks()
        status("concluido", True, f"processamento concluído em {time.time() - t0:.0f}s")
        return True
    except Exception as e:
        status("erro", False, str(e)[-3000:], detalhe=traceback.format_exc()[-3000:])
        return False


def so_sovi():
    """reduzir_sovi.bat: só gera os SOVI resumidos (dados/sovi_resumido), sem calcular o resto"""
    try:
        etapa_sovi()
        L = sorted(glob.glob(os.path.join(SOVI_RESUMIDO, "SOVI_RESUMIDO_*.xlsx")))
        print("\nSOVI resumidos em", os.path.abspath(SOVI_RESUMIDO))
        for x in L: print(f"   {os.path.basename(x)}  ({os.path.getsize(x) / 1e6:.2f} MB)")
        if not L: print("   nenhum: confira se os arquivos do SOVI (aba RED360, com o ano no nome) estão na pasta DADOS_DIR")
        return bool(L)
    except Exception as e:
        status("erro", False, str(e)[-3000:], detalhe=traceback.format_exc()[-3000:]); return False


if __name__ == "__main__":
    if "--so-sovi" in sys.argv: sys.exit(0 if so_sovi() else 1)
    ok = processar("--so-apresentacoes" in sys.argv)
    sys.exit(0 if ok else 1)
