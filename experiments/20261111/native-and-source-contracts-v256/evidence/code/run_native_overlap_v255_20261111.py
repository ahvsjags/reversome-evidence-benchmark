from pathlib import Path
import json,copy,hashlib,re,time,sys,importlib.util,datetime
import numpy as np
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
from qwen_native_server_v255 import LocalModel
from native_geneagent_transport_v255_20261111 import Transport,B,BudgetExhausted
E=B.parent;sp=importlib.util.spec_from_file_location('nli_native_probe',E/'b3_active_utility_v3_20261110.py');lib=importlib.util.module_from_spec(sp);sp.loader.exec_module(lib);D=B/'benchmark';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def report_label(text):
 t=str(text).lower()[:400]
 if any(k in t for k in ['partial','insufficient','inconclusive','uncertain','not enough','cannot','not supported','unsupported']):return 'NOT_ENOUGH_INFO'
 if any(k in t for k in ['refute','contradict','false','incorrect','inaccurate']):return 'CONTRADICT'
 if any(k in t for k in ['supported','accurate','correct','true','verified']):return 'SUPPORT'
 return 'NOT_ENOUGH_INFO'
def sources(records,anchors):
 out=[]
 for t in records:
  if 'result' not in t:continue
  value=t['result']
  if t['name']=='get_pubmed_articles' and isinstance(value,str):
   for block in re.split(r'(?=PMID: )',value):
    mm=re.match(r'PMID: (\d+)\nTitle: (.*?)\nAbstract: (.*)',block,re.S)
    if mm and mm[3].strip() not in ['', 'No abstract available']:out.append({'source_id':'PMID:'+mm[1],'title':mm[2],'text':mm[3].strip(),'kind':'PubMed','origin_tool_sha256':t['sha256']})
  elif t['name']=='get_gene_summary_for_single_gene' and isinstance(value,dict):
   requested=t['arguments'].get('gene_name','');names={str(value.get(k,'')) for k in ['name','nomenclaturesymbol']};names |= set(str(value.get('otheraliases','')).replace(';',',').split(','));org=value.get('organism',{});taxid=org.get('taxid') if isinstance(org,dict) else None
   if requested in anchors and requested in names and str(taxid)=='9606' and value.get('summary'):out.append({'source_id':'NCBIGene:'+str(value.get('uid',value.get('geneid',requested))),'title':requested,'text':'Gene '+requested+'. '+value['summary'],'kind':'NCBIGene','origin_tool_sha256':t['sha256']})
 unique={}
 for x in out:unique.setdefault(x['source_id'],x)
 return list(unique.values())
def witness(nn,claim,records,anchors):
 docs=sources(records,anchors);q=nn.vec.transform([claim]);candidates=[]
 for d in docs:
  ss=[s.strip() for s in re.split(r'(?<=[.!?])\s+',d['text']) if s.strip()]
  sim=(nn.vec.transform(ss)@q.T).toarray().ravel()
  for i in sorted(range(len(ss)),key=lambda i:(-float(sim[i]),i))[:2]:candidates.append({'doc_id':d['source_id'],'sentence':ss[i],'sentence_index':i,'source_kind':d['kind'],'source_sha256':d['origin_tool_sha256']})
 xs=nn.infer(candidates,claim) if candidates else [];return {'sources':docs,'scored_candidates':xs,'relation':lib.decide(xs),'actual_NLI_pairs':len(xs),'source_count':len(docs)}
def freeze():
 assert json.load((B/'pilot_v4_legacy_json_transport/receipt.json').open())['status']=='PASS';d={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'driver_sha256':sha(__file__),'transport_sha256':sha(E/'native_geneagent_transport_v255_20261111.py'),'model_server_sha256':sha(E/'qwen_native_server_v255.py'),'selection_protocol_sha256':sha(D/'protocol.json'),'upstream_intake_sha256':sha(B/'protocol/intake.json'),'native_worker_sha256':sha(B/'upstream/worker.py'),'model':'OfficialQwen3-30B-A3BQ4_K_M,nonthinking,temperature0sameasnativeproviderrequest,top_p1,top_k0,seed20261111.','adapter':'NativeOpenAIlegacyfunctions serialized by JSONschema after native server tool_choice contract was not enforced in development. Originalworker,toolfunctions,toolparameters,promptsand20callloop unchanged; reportnewline normalized. Adapter appends serialization format/schema only. OriginalGPT4scoresnotreproduced.','certificate':'Source identities from actual toolresponses,NCBIGeneexactHGNCnameandtaxid9606binding,actualNLI0.7/.2/.1. Unknown witness triggers upto2deterministicPubMedchecks:exactclaim,thenHGNCanchorsplusfirst8nonstoplongwords. TotalAPIcalls<=20. CandidatefactsjudgedwithnativefrozenNLI,notgold.','counterfactual':'Certificatecontinuationreusestheactualfirst-tool-requiredprefix; nativeprefixcostandcallsattributedtoboth. Noindependentfull-armwall/CPUcausalclaim. LogicalAPIcallsandcachehitsseparate.','no_test_key_read_by_inference':True};(D/'execution_freeze.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2))
def run(shard):
 f=json.load((D/'execution_freeze.json').open());assert sha(__file__)==f['driver_sha256'] and sha(E/'native_geneagent_transport_v255_20261111.py')==f['transport_sha256'];out=D/'runs'/('shard_'+str(shard));out.mkdir(parents=True,exist_ok=False);rows=[json.loads(s) for s in (D/'claims_label_free.jsonl').open()];rows=rows[shard::4];nn=lib.Runtime();nn.torch.set_num_threads(4);begin=time.perf_counter()
 with LocalModel(out) as llm:
  t=Transport(llm,out).install()
  try:
   for r in rows:
    cid=r['case_id'];result={'case_id':cid,'claim':r['claim'],'gene_anchors':r['gene_anchors'],'source_component':r['source_component'],'tracks':{}}
    for arm,forced in [('native_auto',False),('native_required_tool',True)]:
     t.reset(20261111);t.force_first_tool=forced;start=time.perf_counter();error=None
     try:report=t.agent.inference(r['claim'])
     except Exception as ex:error=type(ex).__name__+':'+str(ex);report='Failed.'
     rec={'report':report,'label':report_label(report),'error':error,'wall_seconds':time.perf_counter()-start,'model_calls':copy.deepcopy(t.calls),'tool_calls':copy.deepcopy(t.tools),'HTTP':copy.deepcopy(t.http)};rec['actual_source_count']=len(sources(rec['tool_calls'],r['gene_anchors']));result['tracks'][arm]=rec;print('NATIVE_CASE_ARM',cid,arm,len(t.calls),len(t.tools),error,flush=True)
    strong=result['tracks']['native_required_tool'];start=time.perf_counter();records=copy.deepcopy(strong['tool_calls']);w=witness(nn,r['claim'],records,r['gene_anchors']);extra=[];actualpairs=w['actual_NLI_pairs'];words=[x for x in re.findall('[A-Za-z0-9-]+',r['claim']) if len(x)>=5 and x.lower() not in ENGLISH_STOP_WORDS];queries=[r['claim'],' '.join(r['gene_anchors']+words[:8])];seen_queries={z.get('arguments',{}).get('term') for z in records}
    for query in queries:
     if w['relation']!='NOT_ENOUGH_INFO' and w['source_count']>0:break
     if len(records)>=20 or query in seen_queries:continue
     fn=t.agent.name2function['get_pubmed_articles'];before=len(t.tools);err=None
     try:fn(term=query)
     except Exception as ex:err=type(ex).__name__+':'+str(ex)
     new=copy.deepcopy(t.tools[before:]);records+=new;extra.append({'query':query,'error':err,'tool_records':new});w=witness(nn,r['claim'],records,r['gene_anchors']);actualpairs+=w['actual_NLI_pairs'];seen_queries.add(query)
    result['tracks']['certificate_continuation']={'label':w['relation'] if w['source_count']>0 else 'NOT_ENOUGH_INFO','source_witness':w,'extra_actions':extra,'tool_calls':records,'actual_NLI_pairs_including_rechecks':actualpairs,'native_prefix_parent_sha256':hashlib.sha256(json.dumps(strong,sort_keys=True).encode()).hexdigest(),'wall_seconds_with_shared_native_prefix':strong['wall_seconds']+time.perf_counter()-start,'extra_wall_seconds':time.perf_counter()-start};(out/(cid+'.json')).write_text(json.dumps(result,indent=2));print('NATIVE_CASE_DONE',cid,len(extra),w['source_count'],flush=True)
  finally:t.close()
 receipt={'status':'COMPLETE','cases':len(rows),'ids':[r['case_id'] for r in rows],'wall_seconds':time.perf_counter()-begin,'owned_server_stopped':llm.proc.poll() is not None,'driver_sha256':sha(__file__),'private_records_accessed':False};(out/'execution_receipt.json').write_text(json.dumps(receipt,indent=2));assert receipt['owned_server_stopped'];print(json.dumps(receipt))
if __name__=='__main__':freeze() if sys.argv[1]=='freeze' else run(int(sys.argv[1]))
