"""Inferencia estadística y ranking en dos etapas con evaluación por grupos.
No se consultan servicios externos ni se generan consultas o juicios nuevos.
"""
import json,sys
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import ndcg_score
from stats_tesis import comparar,holm

OUT=Path(__file__).resolve().parent;WORK=OUT.parent.parent/'work/validacion_total'
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2))
qs=json.loads((WORK/'consultas.json').read_text());qm={q['id']:q for q in qs}
groups=np.array([q['cluster'] for q in qs]);folds=np.array([q['fold'] for q in qs])
arms=json.loads((OUT/'manifiesto.json').read_text())['variantes']
results={a:json.loads((WORK/'resultados'/f'{a}.json').read_text()) for a in arms}
for a,d in results.items():
    assert d['documentos']==d['documentos_densos']==757554
    assert [q['id'] for q in d['consultas']]==[q['id'] for q in qs]
def metric(ranking,rel):
    gold=sorted([float(v) for v in rel.values() if v>0],reverse=True)[:10]
    z=sum((2**g-1)/np.log2(i+2) for i,g in enumerate(gold))
    return float(sum((2**rel.get(d,0)-1)/np.log2(i+2) for i,d in enumerate(ranking[:10]))/z) if z else 0.0
def cluster_ic(d):
    labels=sorted(set(groups));s=np.array([d[groups==g].sum() for g in labels]);ns=np.array([(groups==g).sum() for g in labels]);rng=np.random.default_rng(42);idx=rng.integers(0,len(labels),size=(2000,len(labels)))
    return np.percentile(s[idx].sum(axis=1)/ns[idx].sum(axis=1),[2.5,97.5]).tolist()
def family(pairs):
    rr={k:{**comparar(a,b,n_boot=1000,semilla=42),'ic95_componentes':cluster_ic(a-b)} for k,a,b in pairs}
    for src,dst in [('p_valor','p_holm'),('p_permutacion','p_holm_permutacion')]:
        for k,p in holm({k:v[src] for k,v in rr.items()}).items():rr[k][dst]=p
    for r in rr.values():r['concordante']=bool(r['p_holm'] is not None and r['p_holm_permutacion'] is not None and max(r['p_holm'],r['p_holm_permutacion'])<.05)
    return rr
V={a:{k:np.array([q['metricas'][k] for q in d['consultas']]) for k in d['consultas'][0]['metricas']} for a,d in results.items()}
out={'medias':{a:{k:float(v.mean()) for k,v in vv.items()} for a,vv in V.items()},'protocolo':'Mismos 450 juicios existentes; no evaluación independiente. Fondo documental sin cambios entre brazos; todos los documentos tienen vector real.'}
out['ontologia_vs_alternativas']=family([(f'{algo}:ontologia-{b}',V['ontologia'][algo+'_libre'],V[b][algo+'_libre']) for algo in ('denso','rrf','convexa') for b in ('sin_ontologia','repeticion','vecinos','metadatos')])
out['enrutamiento_vs_oracle']=family([(f'{algo}:predicha-oracle',V['ontologia'][algo+'_predicha'],V['ontologia'][algo+'_oracle']) for algo in ('denso','rrf','convexa')])
out['enrutamiento_vs_libre']=family([(f'{algo}:predicha-libre',V['ontologia'][algo+'_predicha'],V['ontologia'][algo+'_libre']) for algo in ('denso','rrf','convexa')])
out['enrutamiento_semantico_vs_libre']=family([(f'{algo}:semantica-libre',V['ontologia'][algo+'_semantica'],V['ontologia'][algo+'_libre']) for algo in ('denso','rrf','convexa')])
out['grupos']={}
for g in sorted({q['grupo'] for q in qs}):
    mask=np.array([q['grupo']==g for q in qs]);out['grupos'][g]={'n':int(mask.sum()),'medias':{a:{k:float(v[mask].mean()) for k,v in vv.items()} for a,vv in V.items()}}
# Reordenamiento del pool recuperado, con modelos fijados y folds por objetivos compartidos.
# Las etiquetas de test SOLO se usan tras predecir para computar métricas.
r=results['ontologia']['consultas'];Xs=[];ys=[];qidx=[];rows=[]
for i,q in enumerate(r):
    for c in q['candidatos']:
        dn,bn=c['dn'],c['bn'];rd=60/(60+c['rd']);rb=60/(60+c['rb']) if c['rb'] else 0.0
        Xs.append([dn,bn,rd,rb,dn*bn,min(dn,bn),max(dn,bn),dn-bn]);ys.append(int(qs[i]['relevancia'].get(c['id'],0)>0));qidx.append(i);rows.append(c)
X=np.array(Xs);y=np.array(ys);qi=np.array(qidx);pred=np.zeros(len(y));chosen={}
alphas=np.linspace(0,1,11);selected_scores=np.zeros(len(y));upper=[]
for fold in sorted(set(folds)):
    train=folds[qi]!=fold;test=~train
    assert not(set(groups[qi[train]])&set(groups[qi[test]]))
    model=make_pipeline(StandardScaler(),LogisticRegression(C=1,class_weight='balanced',max_iter=2000,random_state=42))
    model.fit(X[train],y[train]);pred[test]=model.predict_proba(X[test])[:,1]
    # Elección de alfa solo en consultas de entrenamiento; ranking sobre el pool fijo.
    scores=[]
    for alpha in alphas:
        metrics=[]
        for i in np.flatnonzero(folds!=fold):
            ix=np.flatnonzero(qi==i);order=sorted(ix,key=lambda j:(-(alpha*rows[j]['dn']+(1-alpha)*rows[j]['bn']),rows[j]['id']))
            metrics.append(metric([rows[j]['id'] for j in order],qs[i]['relevancia']))
        scores.append(np.mean(metrics))
    alpha=float(alphas[int(np.argmax(scores))]);chosen[str(fold)]=alpha
    selected_scores[test]=[alpha*rows[j]['dn']+(1-alpha)*rows[j]['bn'] for j in np.flatnonzero(test)]
rank_metrics={f'{a}_{m}':[] for a in ('reordenador','alfa_cv') for m in ('libre','predicha','semantica','oracle')};per=[]
for i,q in enumerate(qs):
    ix=np.flatnonzero(qi==i);ideal=sorted([rows[j]['id'] for j in ix],key=lambda d:(-q['relevancia'].get(d,0),d));upper.append(metric(ideal,q['relevancia']))
    record={'id':q['id'],'fold':q['fold'],'metricas':{}}
    for label,score in [('reordenador',pred),('alfa_cv',selected_scores)]:
        for mode,typ in [('libre',None),('predicha',q['tipo_predicho']),('semantica',q['tipo_semantico']),('oracle',q['tipo_gold'])]:
            chosen_ix=[j for j in ix if typ is None or rows[j]['tipo']==typ];order=sorted(chosen_ix,key=lambda j:(-score[j],rows[j]['id']))
            value=metric([rows[j]['id'] for j in order],q['relevancia']);key=f'{label}_{mode}';rank_metrics[key].append(value);record['metricas'][key]=value
    per.append(record)
rv={k:np.array(v) for k,v in rank_metrics.items()};out['dos_etapas']={'medias':{k:float(v.mean()) for k,v in rv.items()},'alfa_por_fold':chosen,'ndcg_oracle_del_pool':float(np.mean(upper)),'pool':'Unión top100 de BM25, denso, RRF y convexa; hasta 400 documentos por consulta; no se insertan relevantes a mano.','features':'dn,bn,60/(60+rd),60/(60+rb),dn*bn,min,max,dn-bn','cv':'5 folds por componentes de relevantes compartidos. StandardScaler y LogisticRegression C=1 balanced ajustados solo en train. Alfa elegido solo en train.'}
out['dos_etapas']['comparaciones']=family([(f'{k}-convexa_{mode}',rv[k],V['ontologia'][f'convexa_{mode}']) for mode in ('libre','predicha','semantica','oracle') for k in (f'reordenador_{mode}',f'alfa_cv_{mode}')])
dump(OUT/'dos_etapas_por_consulta.json',per);dump(OUT/'estadisticas.json',out)
lines=['VALIDACIÓN COMPLETA Y MEJORA DEL RANKING','',out['protocolo'],'', 'MEDIAS POR VARIANTE']
for a,v in out['medias'].items():lines.extend([a,json.dumps(v,ensure_ascii=False)])
for title in ['ontologia_vs_alternativas','enrutamiento_vs_oracle','enrutamiento_vs_libre','enrutamiento_semantico_vs_libre']:
    lines.extend(['',title])
    for k,v in out[title].items():lines.append(f'{k}: delta={v["media_dif"]:+.6f}, IC95 componentes={v["ic95_componentes"]}, pH W={v["p_holm"]}, pH P={v["p_holm_permutacion"]}, concordante={v["concordante"]}')
lines.extend(['','DOS ETAPAS',json.dumps(out['dos_etapas'],ensure_ascii=False,indent=2),'','LÍMITES','No hay evaluación independiente ni nuevos juicios. Los documentos agregados no recibieron juicios nuevos. Los controles son alternativas específicas y no representan todas las formas de enriquecimiento posibles. La predicción de función y el reordenador se validan internamente por grupos; no constituyen validación externa. Las mejoras deben contrastarse con las configuraciones de este experimento: el 0,684619 anterior usa otra cobertura densa y otra política de enriquecimiento de distractores.'])
(OUT/'informe.txt').write_text('\n'.join(lines)+'\n');print('\n'.join(lines[:15]),flush=True)
