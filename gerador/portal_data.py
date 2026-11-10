"""Gera portal_data.json (dados do portal) e resumo_data.json (apresentação consolidada do administrador)"""
import sys, json, base64
import os
AQUI_PD = os.path.dirname(os.path.abspath(__file__)); OUTD = os.environ.get('SAIDA_DIR', AQUI_PD)
sys.argv = ['x', os.environ.get('DADOS_DIR', AQUI_PD), os.path.join(OUTD, '_x.json')]
__file__ = os.path.join(AQUI_PD, 'dados_deck.py')
exec(open(os.path.join(AQUI_PD, 'dados_deck.py'), encoding='utf-8').read().split('lbl = lambda m')[0])
d = json.load(open(os.path.join(OUTD, 'deck_data.json'), encoding='utf-8'))
emp = {}
for m in d['meses']:
    e = {'mes': m}
    for t in ('RED', 'ICE'):
        e[t] = nota(pesq[t][pesq[t].mes == m], t)
    # repositor empresa
    b = base_rep[base_rep.mes == m]
    j = b.merge(pts_pdv['RED'][pts_pdv['RED'].mes == m][['pdv', 'pp', 'pr']], on='pdv')
    e['RED_rep'] = float(j.pr.sum() / j.pp.sum() * 100) if len(j) else None
    x = pts_pdv_gc['ICE'][pts_pdv_gc['ICE'].mes == m].merge(TAB_AUX_RP, on='pdv')
    e['ICE_rep'] = float(x.pr.sum() / x.pp.sum() * 100) if len(x) else None
    c = cpi[cpi.mes == m]
    if len(c):
        e['cpi_real'] = float((c.REAL_CPI * c.QTD_GDM).sum() / c.QTD_GDM.sum() * 100); e['cpi_meta'] = float((c.META_CPI * c.QTD_GDM).sum() / c.QTD_GDM.sum() * 100)
        e['vdz'] = int(c.REAL_VDZ.sum()); e['inst'] = int(c.REAL_INSTALÇAO.sum()); e['inst_meta'] = float(c.META_INSTALÇAO.sum()); e['perdida'] = int(c.QTD_EQP_PERD.sum())
    t = tom[tom.dt.dt.strftime('%Y-%m') == m]
    e['tom_sim'] = int((t.TOM.str.upper() == 'SIM').sum()); e['tom_total'] = int(t.GERENCIA.nunique())
    ok = [g for g in d['gcs'] if d['gcs'][g]['compromisso'] is not None and next((r['ICE'] for r in d['gcs'][g]['mensal'] if r['mes'] == m), None) is not None]
    e['compr_ok'] = sum(1 for g in ok if next(r['ICE'] for r in d['gcs'][g]['mensal'] if r['mes'] == m) >= d['gcs'][g]['compromisso']); e['compr_total'] = len(ok)
    e.update({'sovi_' + k: v for k, v in sovi(sovi_base[(sovi_base.mes == m) & ~sovi_base.sv.isin(SV_FORA)]).items()})
    emp[m] = e
# canal e pilar da empresa (mês atual vs anterior)
mi = sorted(pesq['ICE'].mes.unique()); ma, mb = mi[-1], mi[-2]
I = pesq['ICE']
a, b_ = nota_seg(I[I.mes == ma]), nota_seg(I[I.mes == mb])
canal = [{'seg': ROTULO_SEG.get(s, s), 'nota': a[s], 'var': a[s] - b_[s] if s in b_ else None} for s in ORDEM_SEG if s in a]
pil = lambda m: {k: min(CAP_PILAR, nota(dd, 'ICE')) for k, dd in I[I.mes == m].groupby('kpi')}
pa, pb = pil(ma), pil(mb)
pilar = sorted([{'kpi': k, 'nota': v, 'var': v - pb[k] if k in pb else None} for k, v in pa.items()], key=lambda z: -z['nota'])
d['empresa'] = emp; d['empresa_canal'] = {'mes': ma, 'itens': canal}; d['empresa_pilar'] = {'mes': ma, 'itens': pilar}
# pontos por segmento (para recalcular no portal quando o admin editar os pesos)
seg=[]
for t in ('RED','ICE'):
    g=pesq_all[t].groupby(['mes','gc','sv','seg']).agg(pp=('pp','sum'),pr=('pr','sum')).reset_index()
    seg += [[t,r.mes,r.gc,r.sv,r.seg,round(float(r.pp),2),round(float(r.pr),2)] for r in g.itertuples()]
d['segpts']=seg
d['ano']={t:{m:str(x.classificacao.iloc[0])[-4:] for m,x in pesq[t].groupby('mes')} for t in ('RED','ICE')}
d['pesos']={a:{s_:{t:(float(PESOS[a][t][s_]) if s_ in PESOS[a][t] else None) for t in ('RED','ICE')} for s_ in SEGS} for a in PESOS}
d['usuarios'] = USUARIOS
d['sovi_insights'] = sovi_insights(sovi_base[~sovi_base.sv.isin(SV_FORA)], 'gc', lambda v: v)
d['supervisores_cfg'] = SVCFG
json.dump(d, open(os.path.join(OUTD, 'resumo_data.json'), 'w', encoding='utf-8'), ensure_ascii=False)
d['logos'] = 'data:image/png;base64,' + base64.b64encode(open(os.path.join(AQUI_PD, 'assets', 'logos.png'), 'rb').read()).decode()
json.dump(d, open(os.path.join(OUTD, 'portal_data.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print({m: {k: (round(v, 2) if isinstance(v, float) else v) for k, v in e.items() if k != 'mes'} for m, e in list(emp.items())[-2:]})
