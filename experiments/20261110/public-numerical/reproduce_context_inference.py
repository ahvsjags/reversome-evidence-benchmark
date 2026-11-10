"""Public data -> frozen CPU model -> complete source-pair predictions -> audit.

All paths are CLI arguments; no IBEX project file or private data is required.
Run prepare, infer, verify separately to keep labels out of model execution.
"""
from pathlib import Path
import argparse,json,hashlib,pickle,urllib.request,tarfile,csv,time,os
import numpy as np
L=['SUPPORT','NOT_ENOUGH_INFO','CONTRADICT'];SOURCE='https://scifact.s3.us-west-2.amazonaws.com/longchecker/latest/data.tar.gz';SOURCE_SHA='0ce25066f18572af3307438a08d0d318a734d97d1d8c27ca43b51e81ae3d683c';MODEL='MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli';REV='6f5cf0a2b59cabb106aca4c287eed12e357e90eb';WEIGHT_SHA='06d6fd89edd4f97816831626daafbdb0b029cf63bae8edc0bccab1d64e2e7707';POL=['fixed2','fixed6','fixed_full']
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return [json.loads(s) for s in Path(p).open() if s.strip()]
def write(p,rows):
 with p.open('x') as f:
  for r in rows:f.write(json.dumps(r)+'\n')
def put(p,d):
 with p.open('x') as f:json.dump(d,f,indent=2)
def prepare(a):
 b=a.work;b.mkdir(exist_ok=False);(b/'source').mkdir();(b/'inputs').mkdir();(b/'keys').mkdir();(b/'results').mkdir();p=b/'source/public_data.tar.gz'
 with urllib.request.urlopen(SOURCE,timeout=120) as r,p.open('xb') as f:
  import shutil;shutil.copyfileobj(r,f)
 assert sha(p)==SOURCE_SHA
 with tarfile.open(p,'r:gz') as t:
  for member in t:
   if member.isfile() and member.name in ['data/'+ds+'/'+name for ds in ['healthver','covidfact'] for name in ['corpus.jsonl','claims_test.jsonl']]:
    parts=member.name.split('/');dest=b/'source'/parts[1];dest.mkdir(exist_ok=True)
    with t.extractfile(member) as r,(dest/parts[2]).open('xb') as f:f.write(r.read())
 for ds,prefix in [('healthver','HV-test-'),('covidfact','COVIDFACT-test-')]:
  docs={str(r['doc_id']):r for r in read(b/'source'/ds/'corpus.jsonl')};cases=[];keys=[]
  for r in read(b/'source'/ds/'claims_test.jsonl'):
   for did0 in r.get('doc_ids',r.get('cited_doc_ids',[])):
    did=str(did0);doc=docs[did];labs={z['label'] for z in (r.get('evidence') or {}).get(did,[])};assert len(labs)<=1 and labs<=set(L);case_id=prefix+str(r['id'])+'-doc-'+did
    cases.append({'case_id':case_id,'claim':r['claim'],'doc_id':did,'title':doc.get('title',''),'sentences':doc['abstract'],'claim_group':prefix+str(r['id'])});keys.append({'case_id':case_id,'claim_group':prefix+str(r['id']),'doc_id':did,'label':next(iter(labs)) if labs else L[1]})
  write(b/'inputs'/f'{ds}.jsonl',cases);write(b/'keys'/f'{ds}.jsonl',keys)
 put(b/'input_manifest.json',{'source_url':SOURCE,'source_sha256':SOURCE_SHA,'files':{str(p.relative_to(b)):sha(p) for folder in ['inputs','keys'] for p in (b/folder).glob('*.jsonl')},'phase':'Prepared public source pairs; no neural inference.'})
def infer(a):
 import torch
 from transformers import AutoTokenizer,AutoModelForSequenceClassification
 from huggingface_hub import snapshot_download
 from sklearn.feature_extraction.text import TfidfVectorizer
 b=a.work;modelpath=a.encoder or Path(snapshot_download(MODEL,revision=REV,token=False,cache_dir=str(b/'model_cache')));assert sha(modelpath/'model.safetensors')==WEIGHT_SHA;headpath=a.bundle/'models/context_adapter.pkl';manifest=json.load((a.bundle/'MANIFEST.json').open());record=next(r for r in manifest['files'] if r['path']=='models/context_adapter.pkl');assert sha(headpath)==record['sha256'];head=pickle.load(headpath.open('rb'));torch.set_num_threads(a.threads);tok=AutoTokenizer.from_pretrained(str(modelpath),local_files_only=True);model=AutoModelForSequenceClassification.from_pretrained(str(modelpath),local_files_only=True).cpu().eval();assert model.config.id2label=={0:'entailment',1:'neutral',2:'contradiction'};vec=TfidfVectorizer(ngram_range=(1,2),stop_words='english',sublinear_tf=True,max_features=200000);docs=read(b/'source/healthver/corpus.jsonl');vec.fit([r.get('title','')+' '+' '.join(r['abstract']) for r in docs]);start=time.perf_counter()
 for ds in ['healthver','covidfact']:
  out=[]
  for i,r in enumerate(read(b/'inputs'/f'{ds}.jsonl')):
   # Full-source mode preserves sentence order. Prefix modes rank by the same
   # frozen-corpus TFIDF and restore selected sentences to original order.
   ss=r['sentences'];q=vec.transform([r['claim']]);scores=(vec.transform(ss)@q.T).toarray().ravel();order=sorted(range(len(ss)),key=lambda j:(-float(scores[j]),j));states={}
   for pol,n in [('fixed2',2),('fixed6',6),('fixed_full',None)]:
    idx=sorted(order[:n] if n is not None else order);text=' '.join(ss[j] for j in idx);x=tok(text,r['claim'],truncation=True,max_length=384,padding=True,return_tensors='pt')
    with torch.inference_mode():
     hidden=model.deberta(**x,return_dict=True).last_hidden_state;logits=model.classifier(model.pooler(hidden));f=torch.cat([hidden[:,0,:],logits],dim=1).numpy()
    p0=head.predict_proba(f)[0];p=[float(p0[list(head.classes_).index(k)]) for k in L];states[pol]={'label':L[int(np.argmax(p))],'probabilities':p,'tokens':int(x['attention_mask'].sum()),'sentence_indices':idx}
   out.append({'case_id':r['case_id'],'claim_group':r['claim_group'],'doc_id':r['doc_id'],'states':states})
   if (i+1)%100==0:print('PORTABLE_INFERENCE',ds,i+1,flush=True)
  write(b/'results'/f'{ds}_predictions.jsonl',out)
 put(b/'inference_receipt.json',{'encoder_sha256':WEIGHT_SHA,'encoder_revision':REV,'adapter_sha256':sha(headpath),'inputs':{p.name:sha(p) for p in (b/'inputs').glob('*.jsonl')},'model_execution_reads_no_key_file':True,'elapsed_seconds':time.perf_counter()-start,'scope':'Real frozen CPU inference,3 physically executed fixed contexts per pair. Active/random fixed-full fallback decisions are reproduced by equality, not additional new timing runs.'})
def verify(a):
 b=a.work;checks={};results={};manifest=json.load((b/'input_manifest.json').open());checks['downloaded_official_archive_hash']=sha(b/'source/public_data.tar.gz')==SOURCE_SHA
 for ds in ['healthver','covidfact']:
  name=ds+'_test';rows=read(b/'results'/f'{ds}_predictions.jsonl');key={r['case_id']:r for r in read(b/'keys'/f'{ds}.jsonl')};expected={r['case_id']:r for r in read(a.bundle/'vectors'/f'{name}_predictions_v8_1.jsonl')};checks[ds+'_all_pairs']=len(rows)==len(key)==len(expected)==len({r['case_id'] for r in rows});pmax=0.;drift=[];stats={}
  for pol in POL:
   cm=np.zeros((3,3),int);tokenok=True
   for r in rows:
    z=r['states'][pol];ref=expected[r['case_id']]['routes'][pol]['trace'][0];pmax=max(pmax,float(np.max(np.abs(np.array(z['probabilities'])-ref['probabilities']))));tokenok &= z['tokens']==ref['tokens'] and z['sentence_indices']==ref['sentence_indices'];cm[L.index(key[r['case_id']]['label']),L.index(z['label'])]+=1
    if z['label']!=ref['label']:drift.append([r['case_id'],pol])
   checks[ds+'_'+pol+'_exact_tokens_and_source_sentence_indices']=bool(tokenok);checks[ds+'_'+pol+'_matrix_matches_released_vectors']=cm.tolist()==json.load((a.bundle/'expected'/f'{name}_v8_1_predictions.json').open())[pol]['CM'];stats[pol]={'accuracy':float(cm.trace()/cm.sum()),'CM':cm.tolist()}
  checks[ds+'_posterior_tolerance_1e4']=pmax<=1e-4;checks[ds+'_all_labels_exact']=not drift;results[ds]={'pairs':len(rows),'claims':len({r['claim_group'] for r in rows}),'max_posterior_difference':pmax,'label_differences':drift,'statistics':stats}
 out={'schema':'REVERSOME.PublicContextInferenceReproduction.v1','status':'PASS' if all(checks.values()) else 'FAIL','passed':sum(checks.values()),'total':len(checks),'checks':checks,'results':results,'scope':'Two public source-bound benchmark loops reconstructed from official download to real frozen neural predictions and complete-vector verification; not a full requirements-generation Agent or human judgment experiment.'};put(b/'end_to_end_reproduction_receipt.json',out);print(json.dumps(out,indent=2));assert all(checks.values())
p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','infer','verify']);p.add_argument('--work',type=Path,required=True);p.add_argument('--bundle',type=Path,required=True);p.add_argument('--encoder',type=Path);p.add_argument('--threads',type=int,default=16);a=p.parse_args();{'prepare':prepare,'infer':infer,'verify':verify}[a.phase](a)

