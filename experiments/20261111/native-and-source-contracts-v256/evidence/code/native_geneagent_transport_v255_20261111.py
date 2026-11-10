"""Provider/HTTP transport adapter; original GeneAgent worker and tools unchanged."""
from pathlib import Path
import copy,json,time,types,sys,urllib.request,hashlib,threading,os,fcntl,importlib
import requests
E=Path('/ibex/project/c2378/xup0a/reversome_2_1_validation/05_evidence_updates');B=E/'native_geneagent_overlap_v255_20261111';CACHE=B/'http_cache';CACHE.mkdir(exist_ok=True)
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,default=str).encode()).hexdigest()
class BudgetExhausted(RuntimeError):pass
class Transport:
 def __init__(self,llm,out,seed=20261111):self.llm=llm;self.out=Path(out);self.seed=seed;self.calls=[];self.tools=[];self.http=[];self.toolcall_history=[];self.limit=20;self.force_first_tool=False;self._original_request=requests.sessions.Session.request
 def install(self):
  self.shim=types.ModuleType('openai');self.shim.ChatCompletion=types.SimpleNamespace(create=self.create);sys.modules['openai']=self.shim;self.cache_original=self._original_request;sys.path.insert(0,str(B/'upstream'));self.worker=importlib.import_module('worker');requests.sessions.Session.request=lambda session,method,url,**kwargs:self.http_request(session,method,url,**kwargs);self.agent=self.worker.AgentPhD(function_names=['get_pubmed_articles','get_gene_summary_for_single_gene'])
  for name,func in list(self.agent.name2function.items()):
   def wrap(_func=func,_name=name,**kwargs):
    t=time.perf_counter()
    try:response=_func(**kwargs)
    except Exception as ex:self.tools.append({'name':_name,'arguments':copy.deepcopy(kwargs),'error':str(ex),'elapsed':time.perf_counter()-t});raise
    self.tools.append({'name':_name,'arguments':copy.deepcopy(kwargs),'result':response,'sha256':digest(response),'elapsed':time.perf_counter()-t});return response
   self.agent.name2function[name]=wrap
  return self
 def reset(self,seed=None):self.calls=[];self.tools=[];self.http=[];self.toolcall_history=[];self.seed=self.seed if seed is None else seed
 def create(self,**kwargs):
  if len(self.calls)>=self.limit:raise BudgetExhausted('Prespecified20model-callbudget')
  original=copy.deepcopy(kwargs);messages=[];fi=0
  for msg in kwargs['messages']:
   if msg['role']=='function':
    call=self.toolcall_history[fi];messages.append({'role':'assistant','content':json.dumps({'function_call':call})});messages.append({'role':'user','content':'Native function response for '+msg['name']+':\n'+msg['content']});fi+=1
   else:messages.append(copy.deepcopy(msg))
  variants=[]
  for f in kwargs['functions']:
   variants.append({'type':'object','properties':{'function_call':{'type':'object','properties':{'name':{'type':'string','enum':[f['name']]},'arguments':f['parameters']},'required':['name','arguments'],'additionalProperties':False}},'required':['function_call'],'additionalProperties':False})
  if not(self.force_first_tool and not self.calls):variants.append({'type':'object','properties':{'content':{'type':'string'}},'required':['content'],'additionalProperties':False})
  # Explicit legacy-message serialization, used because native server tool_choice
  # did not enforce its declared contract in the diagnostic. Tool choice remains
  # a model decision except in the separately labelled first-tool control.
  messages[0]['content']+='\nBackend serialization contract: return one legacy assistant-message JSON object. To call a function return {"function_call":{"name":"FUNCTION_NAME","arguments":{...}}}; to answer return {"content":"Report: ..."}. Available native function schemas: '+json.dumps(kwargs['functions'])
  payload={'model':'reversome-qwen3-30b-a3b-official-q4','messages':messages,'temperature':kwargs.get('temperature',0),'top_p':1.,'top_k':0,'min_p':0.,'seed':self.seed,'max_tokens':1536,'chat_template_kwargs':{'enable_thinking':False},'reasoning_effort':'none','response_format':{'type':'json_schema','json_schema':{'name':'native_legacy_message','strict':True,'schema':{'oneOf':variants}}}}
  t=time.perf_counter();request=urllib.request.Request(self.llm.base+'/v1/chat/completions',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
  try:
   with urllib.request.urlopen(request,timeout=600) as response:raw=json.load(response)
  except Exception as ex:
   self.calls.append({'native_request':original,'transport_request':copy.deepcopy(payload),'error':str(ex),'elapsed':time.perf_counter()-t});raise
  msg=json.loads(raw['choices'][0]['message']['content']);content=msg.get('content')
  if isinstance(content,str):content=content.replace('Report:\n','Report: ').replace('Report:\r\n','Report: ')
  legacy={'role':'assistant','content':content}
  if msg.get('function_call'):
   call=copy.deepcopy(msg['function_call']);call['arguments']=json.dumps(call['arguments']);legacy['function_call']=call;self.toolcall_history.append(call)
  self.calls.append({'native_request':original,'transport_request':copy.deepcopy(payload),'raw_response':raw,'native_response':legacy,'elapsed':time.perf_counter()-t});return types.SimpleNamespace(choices=[{'message':legacy}])
 def http_request(self,session,method,url,**kwargs):
  oldurl=url
  if url.startswith('http://maayanlab.cloud/'):url='https://'+url[7:]
  key=digest([method,url,{k:v for k,v in kwargs.items() if k not in ['timeout','headers']}]);p=CACHE/(key+'.json');body=CACHE/(key+'.bin');lock=CACHE/(key+'.lock')
  with lock.open('a+') as lf:
   fcntl.flock(lf,fcntl.LOCK_EX);hit=p.exists() and body.exists()
   if hit:
    d=json.load(p.open());r=requests.Response();r.status_code=d['status'];r.headers.update(d['headers']);r.url=d['url'];r._content=body.read_bytes();r.encoding=d.get('encoding')
   else:
    last=None
    for attempt in range(3):
     if 'eutils.ncbi.nlm.nih.gov' in url:
      with (CACHE/'ncbi_rate.lock').open('a+') as rate:
       fcntl.flock(rate,fcntl.LOCK_EX);rate.seek(0);prior=rate.read().strip();time.sleep(max(0,.6-(time.time()-float(prior or 0))));rate.seek(0);rate.truncate();rate.write(str(time.time()));rate.flush()
     try:r=self.cache_original(session,method,url,timeout=45,**{k:v for k,v in kwargs.items() if k!='timeout'});last=r
     except requests.RequestException as ex:
      if attempt==2:raise
      time.sleep(2**attempt);continue
     if r.status_code not in [429,500,502,503,504]:break
     time.sleep(2**attempt)
    assert last is not None;body.write_bytes(r.content);p.write_text(json.dumps({'status':r.status_code,'headers':dict(r.headers),'url':r.url,'encoding':r.encoding,'sha256':hashlib.sha256(r.content).hexdigest(),'first_fetch_utc':time.time()},indent=2))
   self.http.append({'method':method,'original_url':oldurl,'url':url,'cache_key':key,'cache_hit':hit,'http_status':r.status_code,'response_sha256':hashlib.sha256(r.content).hexdigest()});return r
 def save(self,path,extra):Path(path).write_text(json.dumps({**extra,'LLM_calls':self.calls,'tool_calls':self.tools,'http':self.http},indent=2))
 def close(self):requests.sessions.Session.request=self._original_request
