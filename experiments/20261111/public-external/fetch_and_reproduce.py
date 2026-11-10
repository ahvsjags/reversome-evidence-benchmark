"""Download SHA-pinned public parts, then execute the portable frozen scorer.

Run from a venv with NumPy2.0.2 installed. No hospital credentials are used.
"""
from pathlib import Path
import argparse,json,urllib.request,hashlib,zipfile,shutil,subprocess,sys,datetime,stat
A=argparse.ArgumentParser();A.add_argument('--base-url',required=True);A.add_argument('--work-dir',required=True);a=A.parse_args();B=Path(a.work_dir);B.mkdir(exist_ok=False);base=a.base_url.rstrip('/');urllib.request.urlretrieve(base+'/release_index.json',B/'release_index.json');index=json.load((B/'release_index.json').open());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();parts=[]
for p in index['parts']:
 name=p['name'];assert Path(name).name==name and not name.startswith('.');target=B/name;urllib.request.urlretrieve(base+'/'+name,target);assert target.stat().st_size==p['bytes'] and sha(target)==p['sha256'];parts.append(target)
Z=B/'public_external_bundle.zip'
with Z.open('wb') as f:
 for p in parts:
  with p.open('rb') as g:shutil.copyfileobj(g,f)
assert Z.stat().st_size==index['archive_bytes'] and sha(Z)==index['archive_sha256'];D=B/'bundle';D.mkdir()
with zipfile.ZipFile(Z) as z:
 for item in z.infolist():
  dest=(D/item.filename).resolve();assert D.resolve()==dest or D.resolve() in dest.parents;assert not stat.S_ISLNK(item.external_attr>>16)
 z.extractall(D)
cmd=[sys.executable,'-I',str(D/'reproduce_external_score.py'),'--bundle-dir',str(D),'--output-dir',str(B/'actual_replay')];r=subprocess.run(cmd,capture_output=True,text=True);(B/'replay_stdout.txt').write_text(r.stdout);(B/'replay_stderr.txt').write_text(r.stderr);assert r.returncode==0,r.stderr;proof=json.load((B/'actual_replay/reproduction_receipt.json').open());assert proof['status']=='PASS';receipt={'schema':'REVERSOME.AnonymousPublicExternalDownloadAndInference.v1','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS','public_base_url':base,'archive_sha256':sha(Z),'parts_verified':len(parts),'passed':proof['passed'],'total':proof['total'],'summary':proof['summary'],'max_per_cell_prediction_difference':proof['max_per_cell_prediction_difference'],'anonymous_download':True,'actual_model_inference_and_statistics_reexecuted':True,'raw_FASTQ_alignment_reexecuted_by_this_loader':False,'private_hospital_records_accessed':False};(B/'anonymous_reproduction_receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))

