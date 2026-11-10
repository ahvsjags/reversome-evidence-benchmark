from pathlib import Path
import json,hashlib,urllib.request
from qwen_native_server_v255 import LocalModel
E=Path('/ibex/project/c2378/xup0a/reversome_2_1_validation/05_evidence_updates');B=E/'native_geneagent_overlap_v255_20261111';D=B/'benchmark';O=D/'trace_witness_check_v256';O.mkdir(exist_ok=False);checks={};count=0;records=[]
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,default=str).encode()).hexdigest()
def post(llm,path,payload):
 req=urllib.request.Request(llm.base+path,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=90) as r:return json.load(r)
with LocalModel(O) as llm:
 for p in sorted((D/'runs').glob('shard_*/*.json')):
  if p.name=='execution_receipt.json':continue
  r=json.load(p.open());cid=r['case_id'];g=r['tracks']['certificate_continuation'];prefix=r['tracks']['native_required_tool']['tool_calls'];checks[cid+'_exact_reused_tool_prefix']=g['tool_calls'][:len(prefix)]==prefix;toolhashes={}
  for i,t in enumerate(g['tool_calls']):
   if 'result' in t:checks[cid+'_tool_result_'+str(i)]=digest(t['result'])==t['sha256'];toolhashes[t['sha256']]=t
  sources={s['source_id']:s for s in g['source_witness']['sources']}
  for i,x in enumerate(g['source_witness']['scored_candidates']):
   s=sources.get(str(x['doc_id']),{});checks[cid+'_candidate_text_'+str(i)]=bool(s) and x['sentence'] in s['text'];checks[cid+'_candidate_actual_tool_'+str(i)]=x['source_sha256'] in toolhashes and x['source_sha256']==s.get('origin_tool_sha256')
  for arm in ['native_auto','native_required_tool']:
   for i,rec in enumerate(r['tracks'][arm]['model_calls']):
    req=rec['transport_request'];prompt=post(llm,'/apply-template',req)['prompt'];tokens=post(llm,'/tokenize',{'content':prompt,'add_special':True,'parse_special':True})['tokens'];expected=rec['raw_response']['usage']['prompt_tokens'];key=cid+'_'+arm+'_'+str(i);checks[key+'_exact_token_count']=len(tokens)==expected;records.append({'key':key,'expected':expected,'actual':len(tokens),'request_sha256':digest(req),'token_sha256':digest(tokens)});count+=1
receipt={'status':'PASS' if all(checks.values()) else 'FAIL','passed':sum(checks.values()),'total':len(checks),'actual_model_requests_checked':count,'checks':checks,'owned_tokenizer_server_stopped':llm.proc.poll() is not None,'new_generation_calls':0,'scope':'Exact immutable request replay through the same template/tokenizer and actual tool-result-to-certificate text binding. Does not substitute for scientific truth evaluation. Extra-action HTTP sequence was not separately persisted in the original continuation output; tool result hashes are retained and verified, not invented as wire captures.'};(O/'receipt.json').write_text(json.dumps(receipt,indent=2));(O/'token_counts.json').write_text(json.dumps(records,indent=2));print(json.dumps({k:v for k,v in receipt.items() if k!='checks'},indent=2));assert receipt['status']=='PASS' and receipt['owned_tokenizer_server_stopped']
