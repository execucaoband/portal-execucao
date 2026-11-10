"""Resume um arquivo FATOS_SOVI (aba RED360) por mês × GC × supervisor × canal × categoria × grupo × fabricante × sabor × área → Σ frentes"""
import sys, os, pandas as pd
from python_calamine import CalamineWorkbook
src, out = sys.argv[1], sys.argv[2]
wb = CalamineWorkbook.from_path(src)
aba = "RED360" if "RED360" in wb.sheet_names else wb.sheet_names[0]
rows = wb.get_sheet_by_name(aba).to_python()
cols = [str(c).strip() for c in rows[0]]
df = pd.DataFrame(rows[1:], columns=cols).loc[:, lambda d: ~d.columns.duplicated()]
keep = ["Gerencia", "Supervisao", "Canal", "Categoria", "Grupo", "Fabricante", "Sabor", "AREA", "Ponto de Contato", "Tipo", "Embalagem", "Espelho"]
for c in keep:
    if c not in df.columns: df[c] = "-"
for c in keep: df[c] = df[c].astype(str).str.strip()
df["Frentes"] = pd.to_numeric(df.Frentes, errors="coerce").fillna(0)
import datetime as _dt
def _mes(v):
    if isinstance(v, (_dt.date, _dt.datetime)): return v.strftime("%Y-%m")
    t = pd.to_datetime(str(v), dayfirst=True, errors="coerce"); return None if pd.isna(t) else t.strftime("%Y-%m")
_u = {v: _mes(v) for v in df.Data_pesquisa.unique()}
df["mes"] = df.Data_pesquisa.map(_u)
r = df.groupby(["mes"] + keep, dropna=False).agg(frentes=("Frentes", "sum"), linhas=("Frentes", "size"), pdvs=("pdv", "nunique")).reset_index()
r["arquivo"] = os.path.basename(src)
r.to_pickle(out)
print(os.path.basename(src), aba, len(df), "->", len(r), r.mes.value_counts().to_dict())
