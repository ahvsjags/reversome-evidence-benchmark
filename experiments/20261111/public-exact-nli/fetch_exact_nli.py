"""Anonymous, immutable-commit download and exact NLI restoration. No credentials."""
from pathlib import Path,PurePosixPath
import argparse,json,hashlib,urllib.request,time,zipfile,subprocess,sys,concurrent.futures,datetime,re
ROOT='https://raw.githubusercontent.com/ahvsjags/reversome-evidence-benchmark/'
PREFIX='experiments/20261111/public-exact-nli/'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def download(url,p,expected=None,size=None):
 if p.exists() and (expected is None or sha(p)==expected) and (size is None or p.stat().st_size==size):return
 for trial in range(4):
  try:
   with urllib.request.urlopen(url,timeout=120) as r,p.with_suffix(p.suffix+'.download').open('wb') as f:
    for b in iter(lambda:r.read(1024*1024),b''):f.write(b)
   q=p.with_suffix(p.suffix+'.download');assert expected is None or sha(q)==expected;assert size is None or q.stat().st_size==size;q.replace(p);return
  except Exception:
   if trial==3:raise
   time.sleep(2**trial)
def main():
 a=argparse.ArgumentParser();a.add_argument('--commit',required=True);a.add_argument('--output-dir',required=True);a.add_argument('--base-checkpoint');a.add_argument('--run-neural-probe',action='store_true');a.add_argument('--public-data-dir');x=a.parse_args();assert re.fullmatch('[0-9a-f]{40}',x.commit),'Use an immutable full commit SHA';O=Path(x.output_dir);O.mkdir(parents=True,exist_ok=False);P=O/'parts';P.mkdir();baseurl=ROOT+x.commit+'/'+PREFIX;download(baseurl+'release_index.json',O/'release_index.json');idx=json.loads((O/'release_index.json').read_text());start=time.perf_counter()
 def part(p):download(baseurl+p['path'],P/Path(p['path']).name,p['sha256'],p['bytes'])
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:list(ex.map(part,idx['parts']))
 archive=O/'exact_nli.zip'
 with archive.open('wb') as f:
  for p in idx['parts']:
   with (P/Path(p['path']).name).open('rb') as src:
    for b in iter(lambda:src.read(1024*1024),b''):f.write(b)
 assert archive.stat().st_size==idx['archive_bytes'] and sha(archive)==idx['archive_sha256']
 B=O/'bundle';B.mkdir()
 with zipfile.ZipFile(archive) as z:
  for entry in z.infolist():
   path=PurePosixPath(entry.filename);assert not path.is_absolute() and '..' not in path.parts and not ('\\' in entry.filename);assert not (entry.external_attr>>16)&0o170000==0o120000
  z.extractall(B)
 m=json.loads((B/'delta_manifest.json').read_text());F=Path(x.base_checkpoint) if x.base_checkpoint else O/'pinned_public_base.safetensors';reused=F.exists();download(m['base_url'],F,m['base_sha256']);assert sha(F)==m['base_sha256'];subprocess.run([sys.executable,str(B/'restore_checkpoint.py'),'--bundle-dir',str(B),'--base-checkpoint',str(F),'--output-dir',str(O/'model')],check=True)
 if x.run_neural_probe:
  subprocess.run([sys.executable,str(B/'reproduce_neural.py'),'--bundle-dir',str(B),'--model-dir',str(O/'model'),'--data-dir',str(Path(x.public_data_dir) if x.public_data_dir else O/'public_data'),'--output-dir',str(O/'neural_replay')],check=True)
 result={'status':'PASS','commit':x.commit,'parts':len(idx['parts']),'archive_sha256':sha(archive),'fitted_model_sha256':sha(O/'model/model.safetensors'),'public_base_reused_with_hash_verification':reused,'actual_neural_probe':x.run_neural_probe,'wall_seconds':time.perf_counter()-start,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'credentials_used':False};(O/'public_download_receipt.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()

