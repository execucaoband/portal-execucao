"""Transforma as apresentações em imagem: gráficos, tabelas e números deixam de ser editáveis.

Cada slide de dados vira uma única figura do tamanho do slide e os gráficos são apagados de dentro
do arquivo (incluindo a planilha que o PowerPoint guarda dentro de cada gráfico).
Os slides "Plano de ação" continuam editáveis, porque são para preencher.

Renderização (nesta ordem):
  1. PowerPoint instalado no Windows (fidelidade total; precisa de pywin32)
  2. LibreOffice (soffice)
Para forçar um deles: variável PPT_RENDER=powerpoint ou PPT_RENDER=libreoffice.

Uso: python achatar_ppt.py arquivo.pptx [arquivo2.pptx ...]
"""
import glob, io, os, shutil, subprocess, sys, tempfile

DPI = int(os.environ.get("PPT_DPI", "200"))
EDITAVEIS = ("Plano de ação",)          # slides que continuam editáveis (título começa com…)
R_LAYOUT = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout"
R_NOTES = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide"


# ---------------------------------------------------------------- PPTX → PDF
def _soffice():
    for c in [shutil.which("soffice"), shutil.which("libreoffice"),
              r"C:\Program Files\LibreOffice\program\soffice.exe", r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"]:
        if c and os.path.exists(c):
            return c
    return None


def _pdf_powerpoint(arqs, pasta):
    import win32com.client  # pywin32
    app = win32com.client.DispatchEx("PowerPoint.Application")
    try:
        for a in arqs:
            p = app.Presentations.Open(os.path.abspath(a), True, False, False)   # ReadOnly, Untitled, WithWindow
            try:
                p.SaveAs(os.path.join(os.path.abspath(pasta), os.path.splitext(os.path.basename(a))[0] + ".pdf"), 32)
            finally:
                p.Close()
    finally:
        app.Quit()


def _pdf_libreoffice(arqs, pasta):
    so = _soffice()
    if not so:
        raise RuntimeError("LibreOffice não encontrado")
    perfil = tempfile.mkdtemp(prefix="lo_perfil_")
    try:
        subprocess.run([so, f"-env:UserInstallation=file:///{perfil.replace(os.sep, '/')}", "--headless",
                        "--convert-to", "pdf", "--outdir", pasta, *arqs], check=True, capture_output=True, timeout=900)
    finally:
        shutil.rmtree(perfil, ignore_errors=True)


def para_pdf(arqs, pasta):
    modo = os.environ.get("PPT_RENDER", "").lower()
    ordem = [modo] if modo else (["powerpoint", "libreoffice"] if os.name == "nt" else ["libreoffice"])
    erros = []
    for m in ordem:
        try:
            (_pdf_powerpoint if m == "powerpoint" else _pdf_libreoffice)(arqs, pasta)
            faltam = [a for a in arqs if not os.path.exists(os.path.join(pasta, os.path.splitext(os.path.basename(a))[0] + ".pdf"))]
            if not faltam:
                return m
            erros.append(f"{m}: não gerou {len(faltam)} arquivo(s)")
        except Exception as e:  # tenta o próximo renderizador
            erros.append(f"{m}: {e}")
    raise RuntimeError("Não foi possível transformar as apresentações em imagem. Instale o PowerPoint (com pywin32) "
                       "ou o LibreOffice. Detalhes: " + " | ".join(erros))


# ---------------------------------------------------------------- PDF → imagens → PPTX
def _titulo(slide):
    for sh in slide.shapes:
        if sh.has_text_frame and sh.text_frame.text.strip():
            return sh.text_frame.text.strip()
    return ""


def achatar(arqs):
    import pypdfium2 as pdfium
    from pptx import Presentation
    arqs = [os.path.abspath(a) for a in arqs]
    tmp = tempfile.mkdtemp(prefix="achatar_")
    try:
        modo = para_pdf(arqs, tmp)
        for a in arqs:
            pdf = pdfium.PdfDocument(os.path.join(tmp, os.path.splitext(os.path.basename(a))[0] + ".pdf"))
            prs = Presentation(a)
            if len(pdf) != len(prs.slides):
                raise RuntimeError(f"{os.path.basename(a)}: o PDF tem {len(pdf)} páginas e o PPT {len(prs.slides)} slides")
            W, H = prs.slide_width, prs.slide_height
            for i, slide in enumerate(prs.slides):
                if _titulo(slide).startswith(EDITAVEIS):
                    continue
                img = pdf[i].render(scale=DPI / 72).to_pil().convert("RGB")
                buf = io.BytesIO()
                img.quantize(256, method=0, dither=0).save(buf, "PNG", optimize=True)   # 256 cores: mesma nitidez, ~1/3 do tamanho
                if buf.tell() > 600_000:                   # capa/encerramento com foto: JPEG fica bem menor
                    buf = io.BytesIO(); img.save(buf, "JPEG", quality=90, optimize=True)
                buf.seek(0)
                arvore = slide.shapes._spTree
                for el in list(arvore)[2:]:            # mantém só nvGrpSpPr e grpSpPr
                    arvore.remove(el)
                for rid, rel in list(slide.part.rels.items()):
                    if rel.reltype not in (R_LAYOUT, R_NOTES):
                        slide.part.drop_rel(rid)       # some o gráfico e a planilha embutida
                slide.shapes.add_picture(buf, 0, 0, W, H)
            pdf.close()
            prs.save(a)
        return modo
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    print("renderizado com", achatar(sys.argv[1:]))
