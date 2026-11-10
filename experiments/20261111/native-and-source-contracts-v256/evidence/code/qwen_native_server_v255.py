"""Owned, CPU-only, localhost model server. No paid/provider authentication path."""
from pathlib import Path
import json,os,socket,subprocess,time,urllib.request,urllib.error
B=Path('/ibex/project/c2378/xup0a/reversome_2_1_validation/05_evidence_updates/review_gap_breakthrough_v252_20261111');ALIAS='reversome-qwen3-30b-a3b-official-q4'
class LocalModel:
 def __init__(self,out):self.out=Path(out);self.calls=0;self.proc=None
 def __enter__(self):
  source=json.load((B/'protocol/model_source.json').open());assert json.load((B/'models/download_receipt.json').open())['status']=='PASS';self.log=(self.out/'model_server.log').open('w');sock=socket.socket();sock.bind(('127.0.0.1',0));self.port=sock.getsockname()[1];sock.close();self.base=f'http://127.0.0.1:{self.port}';self.command=[str(B/'llama.cpp/build-cpu/bin/llama-server'),'-m',str(B/'models'/source['file']),'--host','127.0.0.1','--port',str(self.port),'--alias',ALIAS,'--gpu-layers','0','--threads','16','--threads-batch','16','--ctx-size','32768','--parallel','1','--batch-size','512','--ubatch-size','128','--jinja','--reasoning','off','--no-context-shift','--no-warmup'];self.proc=subprocess.Popen(self.command,stdout=self.log,stderr=subprocess.STDOUT);start=time.perf_counter()
  for _ in range(1200):
   if self.proc.poll() is not None:
    self.__exit__();raise RuntimeError('Local model exited: inspect owned model_server.log')
   try:
    r=json.load(urllib.request.urlopen(self.base+'/v1/models',timeout=2))
    if r.get('data') and r['data'][0]['id']==ALIAS:self.setup=time.perf_counter()-start;return self
   except (urllib.error.URLError,ValueError,TimeoutError):pass
   time.sleep(1)
  self.__exit__();raise TimeoutError('Model startup >20min')
 def request(self,messages,schema,seed=20261111,max_tokens=256):
  self.calls+=1;payload={'model':ALIAS,'messages':messages,'temperature':.7,'top_p':.8,'top_k':20,'min_p':0,'seed':int(seed)%2147483647,'max_tokens':max_tokens,'chat_template_kwargs':{'enable_thinking':False},'reasoning_effort':'none','response_format':{'type':'json_schema','json_schema':{'name':'scientific_action','strict':True,'schema':schema}}};start=time.perf_counter();req=urllib.request.Request(self.base+'/v1/chat/completions',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
  try:
   with urllib.request.urlopen(req,timeout=600) as response:result=json.load(response)
  except urllib.error.HTTPError as ex:raise RuntimeError('Local inference HTTP '+str(ex.code)+' '+ex.read().decode()[:1500])
  record={'request':json.loads(json.dumps(payload)),'response':result,'service_elapsed_seconds':time.perf_counter()-start};content=result['choices'][0]['message'].get('content','');return json.loads(content),record
 def __exit__(self,*args):
  if self.proc is not None and self.proc.poll() is None:
   self.proc.terminate()
   try:self.proc.wait(timeout=30)
   except subprocess.TimeoutExpired:self.proc.kill();self.proc.wait()
  if hasattr(self,'log'):self.log.close()
