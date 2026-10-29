"""Validación local, sin nuevas consultas humanas ni servicios externos.
Ejecución: python3 pipeline.py preparar|ejecutar|resumir
El corpus y los vectores con datos personales se guardan solo en work/.
"""
from pathlib import Path
import os, sys, json, hashlib, subprocess, time, csv
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import make_pipeline, FeatureUnion
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.metrics import accuracy_score, confusion_matrix
from tokenizers import Tokenizer

OUT=Path(__file__).resolve().parent
TASK=OUT.parent.parent
WORK=TASK/'work/validacion_total'
PROJECT=Path('/content/tesis/sin_indices_legacy')
EXP=PROJECT/'experimentos'
ENGINE=WORK/'engine/target/release/tesis-validacion'
ARMS=['sin_ontologia','ontologia','repeticion','vecinos','metadatos']
def dump(p,v):
    tmp=Path(str(p)+'.tmp');tmp.write_text(json.dumps(v,ensure_ascii=False,indent=2));tmp.replace(p)
def jl(p):
    with p.open() as f:
        for l in f:
            if l.strip():yield json.loads(l)
def status(phase,**kw):
    dump(OUT/'estado.json',{'fase':phase,'fecha_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),**kw})
def run(args,**kw):
    print('Ejecutando:',args,flush=True);subprocess.run([str(a) for a in args],check=True,**kw)
def export():
    dest=WORK/'corpus.jsonl'
    if dest.exists():return
    run([ENGINE,'exportar',PROJECT/'lince/datos/fuentes',PROJECT/'lince/datos/base',EXP/'corpus/corpus_v3.jsonl',WORK/'corpus.tmp'])
    (WORK/'corpus.tmp').replace(dest)
def preparar():
    WORK.mkdir(parents=True,exist_ok=True);status('preparando_corpus');export()
    core0=list(jl(EXP/'corpus/corpus_v3.jsonl'))
    assert len(core0)==811
    source={r['id']:r for r in core0}
    core=[];types={}
    for i,r in enumerate(jl(WORK/'corpus.jsonl')):
        types[r['id']]=r['tipo']
        if i<811:core.append(r)
    assert len(types)==757554 and {r['id'] for r in core}==set(source)
    tokenizer=Tokenizer.from_file(str(Path.home()/'.cache/huggingface/hub/models--jinaai--jina-embeddings-v3/snapshots/ab036b023d30b4d1138c4c3bfa9f0c445ab455d6/tokenizer.json'))
    def nt(s):return len(tokenizer.encode(s,add_special_tokens=False).ids)
    def budget(desc,extra,total):
        # Mismo presupuesto TOTAL de subpalabras que el documento con ontología.
        if nt(desc)>=total:return desc
        words=extra.split() or desc.split() or ['documento']
        extension=' '.join(words)
        while nt(desc+' '+extension)<total:extension+=' '+' '.join(words)
        ids_=tokenizer.encode(desc+' '+extension,add_special_tokens=False).ids[:total]
        return tokenizer.decode(ids_,skip_special_tokens=False)
    desc=[r['descripcion'] for r in core]
    tf=TfidfVectorizer(strip_accents='unicode',lowercase=True,ngram_range=(1,2),min_df=1)
    x=tf.fit_transform(desc);sim=(x@x.T).toarray();terms=np.array(tf.get_feature_names_out())
    built=[];audit=[]
    for i,r in enumerate(core):
        raw=r['descripcion'];onto=r['ontologia'];n=nt(onto)
        neighbors=[int(j) for j in np.argsort(-sim[i],kind='stable') if j!=i and sim[i,j]>0][:5]
        weight=np.asarray(x[neighbors].multiply(np.array([sim[i,j] for j in neighbors])[:,None]).sum(axis=0)).ravel() if neighbors else x[i].toarray().ravel()
        relterms=terms[np.argsort(-weight,kind='stable')[:80]]
        relterms=[t for t in relterms if weight[tf.vocabulary_[t]]>0]
        s=source[r['id']];fac=s.get('facetas',{})
        metadata=' '.join([str(s.get(k,'')) for k in ('titulo','subtitulo')]+[f'{k}: {v}' for k,v in sorted(fac.items()) if isinstance(v,(str,int,float))])
        variants={'sin_ontologia':raw,'ontologia':onto,'repeticion':budget(raw,raw,n),'vecinos':budget(raw,' '.join(relterms),n),'metadatos':budget(raw,metadata,n)}
        built.append({'id':r['id'],'tipo':r['tipo'],**variants})
        audit.append({'id':r['id'],'tokens':{k:nt(v) for k,v in variants.items()},'vecinos':[core[j]['id'] for j in neighbors]})
    dump(WORK/'core.json',built);dump(OUT/'auditoria_presupuestos.json',audit)
    # Deduplicación textual exacta, un solo vector por texto. No se inventan vectores.
    mapping={};base_rows=[];core_rows={a:[] for a in ARMS}
    with (WORK/'textos.jsonl').open('w') as w:
        def add(text):
            key=hashlib.sha256(text.encode()).hexdigest()
            if key not in mapping:
                mapping[key]=len(mapping);w.write(json.dumps({'text':text},ensure_ascii=False)+'\n')
            return mapping[key]
        for r in jl(WORK/'corpus.jsonl'):base_rows.append(add(r['descripcion']))
        for a in ARMS:
            for r in built:core_rows[a].append(add(r[a]))
    np.save(WORK/'filas_base.npy',np.array(base_rows,dtype=np.int32));dump(WORK/'filas_core.json',core_rows)
    manifest={'documentos':len(types),'documentos_core':811,'textos_unicos':len(mapping),'dim':1024,'variantes':ARMS,'fondo':'Descripción original idéntica en todos los brazos; solo varían los 811 documentos del corpus v3.'}
    # Etiquetas de ruta de entrenamiento; gold nunca entra como atributo de consulta.
    qs=[]
    for cf,qf,difficult in [('consultas_final_v3','qrels_final_v3',False),('consultas_dificil_ab','qrels_dificil_ab',True)]:
        qrels={r['id']:r['relevancia'] for r in jl(EXP/'datos'/f'{qf}.jsonl')}
        groups={'competencias':'pruebas_regionales','funcionalidad':'funcionalidades','prueba_catalogo':'pruebas_catalogo','regla_participacion':'reglas'}
        for q in jl(EXP/'datos'/f'{cf}.jsonl'):
            rel=qrels[q['id']];target=sorted(rel,key=lambda k:(-rel[k],k))[0]
            qs.append({'id':q['id'],'grupo':'dificiles_ab' if difficult else groups.get(q.get('estrato'),'reportes'),'text':q['texto'],'relevancia':rel,'objetivo':target,'tipo_gold':types[target]})
    assert len(qs)==450 and len({q['id'] for q in qs})==450
    # Componentes conexas por CUALQUIER relevante compartido: evita fuga entre consultas hermanas.
    parent=list(range(len(qs)))
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    first={}
    for i,q in enumerate(qs):
        for doc,g in q['relevancia'].items():
            if g<=0:continue
            if doc in first:parent[find(i)]=find(first[doc])
            else:first[doc]=i
    cluster=np.array([find(i) for i in range(len(qs))]);labels=np.array([q['tipo_gold'] for q in qs]);texts=np.array([q['text'] for q in qs])
    folds=list(GroupKFold(n_splits=5).split(texts,labels,cluster));pred=np.empty(len(qs),dtype=object)
    for fold,(train,test) in enumerate(folds):
        assert not(set(cluster[train])&set(cluster[test]))
        clf=make_pipeline(FeatureUnion([('word',TfidfVectorizer(strip_accents='unicode',ngram_range=(1,2),sublinear_tf=True)),('char',TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),sublinear_tf=True))]),LogisticRegression(C=1.0,class_weight='balanced',max_iter=2000,random_state=42))
        clf.fit(texts[train],labels[train]);pred[test]=clf.predict(texts[test])
        for i in test:qs[i]['fold']=fold;qs[i]['cluster']=int(cluster[i])
    for i,q in enumerate(qs):q['tipo_predicho']=str(pred[i])
    dump(WORK/'consultas.json',qs)
    with (WORK/'textos_consulta.jsonl').open('w') as w:
        for q in qs:w.write(json.dumps({'text':q['text']},ensure_ascii=False)+'\n')
    cats=sorted(set(labels));routing={'accuracy_agrupada':float(accuracy_score(labels,pred)),'n_componentes':len(set(cluster)),'clases':cats,'confusion':confusion_matrix(labels,pred,labels=cats).tolist(),'cv':'5 folds, componentes por cualquier documento relevante compartido','hiperparametros':'TFIDF palabras 1-2 + caracteres 3-5, LogisticRegression C=1, balanced, semilla42','independiente':False}
    dump(OUT/'enrutamiento.json',routing)
    manifest['sha256_textos']=hashlib.sha256((WORK/'textos.jsonl').read_bytes()).hexdigest()
    manifest['bytes_vectores']=len(mapping)*4096
    dump(OUT/'manifiesto.json',manifest);status('preparado',**manifest)
    print(manifest, routing,flush=True)
def scores():
    m=json.loads((OUT/'manifiesto.json').read_text());n=m['textos_unicos'];nq=450
    vec=np.memmap(WORK/'documentos.f32',dtype='<f4',mode='r',shape=(n,1024));query=np.memmap(WORK/'consultas.f32',dtype='<f4',mode='r',shape=(nq,1024));rows=np.load(WORK/'filas_base.npy');nc=len(rows)
    score_path=WORK/'scores_base.f32';cp=WORK/'scores_checkpoint.json'
    done=json.loads(cp.read_text())['filas'] if cp.exists() else 0
    mode='r+' if score_path.exists() else 'w+'
    out=np.memmap(score_path,dtype='<f4',mode=mode,shape=(nq,nc))
    import torch
    torch.backends.cuda.matmul.allow_tf32=False
    tq=torch.as_tensor(np.array(query),device='cuda')
    from threadpoolctl import threadpool_limits
    with threadpool_limits(limits=4):
        for start in range(done,nc,4096):
            end=min(start+4096,nc);out[:,start:end]=(tq @ torch.as_tensor(np.asarray(vec[rows[start:end]]),device='cuda').T).cpu().numpy();out.flush();dump(cp,{'filas':end});print('scores',end,'/',nc,flush=True)
        for arm,ix in json.loads((WORK/'filas_core.json').read_text()).items():
            ov=np.asarray((tq @ torch.as_tensor(np.asarray(vec[ix]),device='cuda').T).cpu().numpy(),dtype='<f4');ov.tofile(WORK/f'scores_{arm}.f32')
    assert np.isfinite(out).all()
    # Ruta semántica sin gold, calculada sobre las descripciones de conocimiento.
    # Los scores de recuperación y todos los rankings siguen incluyendo los 757.554 documentos.
    from itertools import islice
    types=np.array([r['tipo'] for r in islice(jl(WORK/'corpus.jsonl'),811)])
    pred=types[np.argmax(out[:,:811],axis=1)]
    qs=json.loads((WORK/'consultas.json').read_text())
    for q,t in zip(qs,pred):q['tipo_semantico']=str(t)
    dump(WORK/'consultas.json',qs)
    route=json.loads((OUT/'enrutamiento.json').read_text());cats=route['clases']
    route['alternativa_semantica_sin_entrenamiento']={'metodo':'Tipo de la descripción v3 más similar a la consulta, sin consultar gold. Solo para predecir contexto; el ranking posterior usa el universo completo.','accuracy':float(np.mean([q['tipo_gold']==q['tipo_semantico'] for q in qs])),'confusion':confusion_matrix([q['tipo_gold'] for q in qs],[q['tipo_semantico'] for q in qs],labels=cats).tolist()}
    dump(OUT/'enrutamiento.json',route)
    dump(WORK/'evaluacion_config.json',{'salida':str(WORK/'resultados'),'corpus':str(WORK/'corpus.jsonl'),'consultas':str(WORK/'consultas.json'),'scores':str(score_path),'core':str(WORK/'core.json'),'variantes':[{'nombre':a,'scores_core':str(WORK/f'scores_{a}.f32')} for a in ARMS]})
def ejecutar():
    if not(OUT/'manifiesto.json').exists():preparar()
    import shutil
    m=json.loads((OUT/'manifiesto.json').read_text())
    assert hashlib.sha256((WORK/'textos.jsonl').read_bytes()).hexdigest()==m['sha256_textos']
    existing=lambda p:p.stat().st_size if p.exists() else 0
    needed=max(0,m['bytes_vectores']-existing(WORK/'documentos.f32'))+max(0,450*757554*4-existing(WORK/'scores_base.f32'))+2_000_000_000
    assert shutil.disk_usage(WORK).free>needed,'Espacio insuficiente; se conservan checkpoints.'
    os.environ['TESIS_PILOTO']=str(WORK/'piloto')
    status('codificando_consultas')
    run([ENGINE,'codificar',WORK/'textos_consulta.jsonl',WORK/'consultas.f32',WORK/'consultas_checkpoint.json','consulta',PROJECT/'lince'])
    status('codificando_todos_los_documentos')
    run([ENGINE,'codificar',WORK/'textos.jsonl',WORK/'documentos.f32',WORK/'documentos_checkpoint.json','documento',PROJECT/'lince'])
    status('calculando_coseno_exacto');scores()
    status('evaluando_recuperacion_completa');run([ENGINE,'evaluar',WORK/'evaluacion_config.json'])
    status('analizando_resultados');run([sys.executable,OUT/'postprocesar.py'])
    status('completo')
if __name__=='__main__':
    try:
        import fcntl
        lock=(WORK/'pipeline.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX if sys.argv[1]=='ejecutar' else fcntl.LOCK_EX|fcntl.LOCK_NB)
        {'preparar':preparar,'ejecutar':ejecutar}[sys.argv[1]]()
    except Exception as e:
        status('error',error=repr(e));raise
