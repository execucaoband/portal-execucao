"""Confere se a pasta de planilhas (DADOS_DIR, normalmente no OneDrive) tem tudo o que o processamento precisa.

Uso: python gerador\\conferir_pasta.py        (lê DADOS_DIR e ANO do segredos.bat via conferir_pasta.bat)
"""
import glob, os, re, sys, time

DADOS = os.environ.get("DADOS_DIR", "")
ANO = os.environ.get("ANO", "2026")
A2 = ANO[2:]
MESES = "Janeiro|Fevereiro|Mar.o|Abril|Maio|Junho|Julho|Agosto|Setembro|Outubro|Novembro|Dezembro"

ITENS = [  # (nome, regra no nome do arquivo, obrigatório, explicação)
    ("RED (um arquivo por mês)", r"FATOS_RED", True, "FATOS_RED_JAN26.xlsx, FATOS_RED_FEV26.xlsx…"),
    ("ICE Latam (um arquivo por mês)", r"FATOS_ICE", True, "FATOS_ICE_JAN26.xlsx, FATOS_ICE_FEV26.xlsx…"),
    ("Gerências", r"DIM_GERENCIA", True, "DIM_GERENCIA.xlsx"),
    ("Supervisores", r"DIM_SUPERVISOR", True, "DIM_SUPERVISOR.xlsx"),
    ("CPI", r"FATOS_CPI", True, "FATOS_CPI.xlsx"),
    ("TOM", r"(^|[-_ ])TOM\.xlsx$", True, "TOM.xlsx"),
    ("Compromisso de ICE", r"COMPROMISSO", True, "COMPROMISSO_ICE.xlsx"),
    ("Repositor (um arquivo por mês)", rf"(({MESES})\d{{2}}|BASE_RP_RESUMO.*)\.xlsx$", True, "Janeiro26.xlsx, Fevereiro26.xlsx…"),
    ("SOVI bruto (só os do ano)", None, False, f"arquivos do SOVI com '{A2}' no nome, dentro de FATOS_SOVI"),
]


def main():
    print("=" * 70)
    print(" Conferência da pasta de planilhas")
    print("=" * 70)
    pastas = [p for p in DADOS.split(os.pathsep) if p.strip()]
    if not pastas:
        sys.exit("DADOS_DIR não definido. Preencha no segredos.bat.")
    faltam = [p for p in pastas if not os.path.isdir(p)]
    for p in pastas:
        print(" Pasta:", p, "" if os.path.isdir(p) else "  ← NÃO ENCONTRADA")
    pastas = [p for p in pastas if os.path.isdir(p)]
    if faltam and any(not p.rstrip("\\/").endswith(os.path.join("dados", "bases")) for p in faltam):
        print("\n [AVISO] Confira o caminho no segredos.bat (copie da barra de endereço do Explorador).")
    if not pastas:
        sys.exit("Nenhuma pasta de planilhas encontrada. Preencha o DADOS_DIR no segredos.bat ou envie as planilhas pela aba Cargas do portal.")
    todos = [x for p in pastas for x in glob.glob(os.path.join(p, "**", "*.xls*"), recursive=True) if not os.path.basename(x).startswith("~$")]
    xlsb = [x for x in todos if x.lower().endswith((".xls", ".xlsb", ".xlsm"))]
    xlsx = [x for x in todos if x.lower().endswith(".xlsx")]
    print(f" {len(xlsx)} planilhas .xlsx encontradas (subpastas incluídas)\n")
    falta = 0
    for nome, regra, obrig, ex in ITENS:
        if regra:
            achados = sorted(x for x in xlsx if re.search(regra, os.path.basename(x), re.I))
        else:
            achados = sorted(x for x in xlsx if "SOVI" in x.upper() and A2 in os.path.basename(x)
                             and not os.path.basename(x).upper().startswith(("FATOS_", "DIM_", "SOVI_RESUMO")))
        ok = bool(achados)
        if not ok and obrig:
            falta += 1
        print(f" [{'OK ' if ok else ('FALTA' if obrig else 'AVISO')}] {nome}: {len(achados)} arquivo(s)")
        for x in achados[:14]:
            mb = os.path.getsize(x) / 1e6
            print(f"        {os.path.relpath(x, pastas[0])}  ({mb:.1f} MB, {time.strftime('%d/%m %H:%M', time.localtime(os.path.getmtime(x)))})")
        if not ok:
            print(f"        esperado: {ex}")
    res = sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dados", "sovi_resumido", "SOVI_RESUMIDO_*.xlsx")))
    print(f" [{'OK ' if res else 'AVISO'}] SOVI resumido (dados\\sovi_resumido): {len(res)} arquivo(s)")
    for x in res: print(f"        {os.path.basename(x)}  ({os.path.getsize(x) / 1e6:.2f} MB)")
    if not res: print("        gerado pelo reduzir_sovi.bat ou pelo atualizar_portal.bat; outras máquinas baixam do Supabase")
    # arquivos só na nuvem (OneDrive "sob demanda"): tamanho 0 ou atributo de arquivo offline no Windows
    nuvem = []
    if os.name == "nt":
        for x in xlsx:
            try:
                if os.stat(x).st_file_attributes & 0x00400000:   # FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS
                    nuvem.append(x)
            except (AttributeError, OSError):
                pass
    if nuvem:
        print(f"\n [AVISO] {len(nuvem)} planilha(s) estão só na nuvem do OneDrive (ícone de nuvem).")
        print("         O processamento baixa sozinho, mas fica bem mais lento. Clique com o botão direito")
        print("         na pasta Prévia 2026 > 'Sempre manter neste dispositivo'.")
    if xlsb:
        print(f"\n [AVISO] {len(xlsb)} arquivo(s) .xls/.xlsb/.xlsm serão ignorados. Salve como .xlsx se forem necessários.")
    print()
    if falta:
        sys.exit(f" {falta} item(ns) obrigatório(s) faltando. Corrija antes de rodar o atualizar_portal.bat.")
    print(" Tudo certo. Pode rodar o atualizar_portal.bat.")


if __name__ == "__main__":
    main()
