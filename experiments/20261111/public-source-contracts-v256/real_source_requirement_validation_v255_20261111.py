"""Public-source unit/assay/claim contract checks and prespecified marker packet.
Developer-authored controlled faults, not independent expert labels or an open-task benchmark.
"""
from pathlib import Path
import csv,gzip,json,hashlib,urllib.request,re,itertools,datetime,copy,sys
from collections import Counter,defaultdict
import numpy as np
from scipy import stats
E=Path(__import__('os').environ.get('REVERSOME_EVIDENCE_ROOT','/ibex/project/c2378/xup0a/reversome_2_1_validation/05_evidence_updates'));B=E/'real_source_requirements_v255_20261111';S=B/'source';O=B/'validation';O.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,obj):(O/name).write_text(json.dumps(obj,indent=2))
def get(url):
 with urllib.request.urlopen(url,timeout=90) as r:return r.read()
# Preserve the original failed URL and add a pinned successful source receipt.
commit='54ec911b1c77b020e6211bc2412cb2bb3b994063';url='https://raw.githubusercontent.com/bioconductor-source/airway/'+commit+'/inst/extdata/sample_table.csv';p=S/'airway_sample_table_pinned.csv';p.write_bytes(get(url));save('airway_source_amendment.json',{'url':url,'commit':commit,'bytes':p.stat().st_size,'sha256':sha(p),'original_failed_receipt_preserved':True})
air=list(csv.DictReader(p.open()));assert len(air)==8;air_cells=sorted({r['cell'] for r in air});assert len(air_cells)==4;air_pairs=all({r['dex'] for r in air if r['cell']==c}=={'trt','untrt'} for c in air_cells)
# Parse the actual GEO header (unlabelled leading barcode column).
p=S/'GSE96583_batch2.total.tsne.df.tsv.gz'
with gzip.open(p,'rt') as f:
 rr=csv.reader(f,delimiter='\t');h=next(rr);first=next(rr);assert len(first)==len(h)+1;pb=[dict(zip(['cell_id']+h,r)) for r in itertools.chain([first],rr)]
mult=Counter(r['multiplets'] for r in pb);inds=sorted({r['ind'] for r in pb});conditions=sorted({r['stim'] for r in pb});pb_pairs=all({r['stim'] for r in pb if r['ind']==i}=={'ctrl','stim'} for i in inds)
# Do not silently choose a singlet filter; disclose the metadata universe and flags.
save('PBMC_metadata_universe.json',{'rows':len(pb),'ind_values':inds,'conditions':conditions,'multiplets_flags':dict(mult),'scope':'All source metadata rows; no expression analysis and no undocumented multiplet filter.','header_repair':'Prepend cell_id to seven named columns, matching eight actual fields.'})
aggregates={};cells=[];by_donor={};genes=['INS','GCG','MS4A1'];library_set=set();barcodes=[];headers=[]
for i in range(1,5):
 p=S/('GSM'+str(2230756+i)+'_human'+str(i)+'_umifm_counts.csv.gz');donor='human'+str(i);n=0;types=Counter()
 with gzip.open(p,'rt') as f:
  rr=csv.reader(f);h=next(rr);idx=[h.index(g)-3 for g in genes];headers.append(h[3:]);acc={}
  for r in rr:
   assert len(r)==len(h);v=np.asarray(r[3:],dtype=np.int64);assert np.min(v)>=0;total=int(v.sum());assert total>0;ct=r[2];n+=1;types[ct]+=1;lib=r[0].split('.final_cell_')[0];library_set.add(lib);barcodes.append(r[1]);cells.append({'cell_id':r[0],'barcode':r[1],'donor':donor,'library':lib,'cell_type':ct,'total_UMI':total,'genes':[int(v[j]) for j in idx]})
   if ct not in acc:acc[ct]={'n_cells':0,'UMI':0,'gene_UMI':[0,0,0]}
   a=acc[ct];a['n_cells']+=1;a['UMI']+=total;a['gene_UMI']=[a['gene_UMI'][j]+int(v[idx[j]]) for j in range(3)]
 aggregates[donor]=acc;by_donor[donor]={'n_cells':n,'cell_types':dict(types),'source_sha256':sha(p)};print('COUNTS_PARSED',donor,n,flush=True)
assert all(x==headers[0] for x in headers)
save('donor_pseudobulk_counts.json',{'genes':genes,'aggregates':aggregates,'by_donor':by_donor,'n_genes':len(headers[0]),'libraries':sorted(library_set),'n_cells':len(cells),'raw_barcode_unique':len(set(barcodes)),'source_qualified_unique':len({c['cell_id'] for c in cells})})
save('cell_marker_counts.json',cells)
marker=[];rng=np.random.default_rng(20261111)
for j,g in enumerate(genes):
 left,right=('alpha','beta') if g=='GCG' else ('beta','alpha');deltas=[];units=[]
 for donor,cs in aggregates.items():
  if min(cs[left]['n_cells'],cs[right]['n_cells'])<20:continue
  vals=[np.log1p(cs[t]['gene_UMI'][j]/cs[t]['UMI']*1e6) for t in [left,right]];deltas.append(float(vals[0]-vals[1]));units.append(donor)
 x=np.asarray(deltas);n=len(x);mean=float(x.mean());se=float(stats.sem(x));ci=stats.t.interval(.95,n-1,loc=mean,scale=se);test=stats.ttest_1samp(x,0);signs=np.asarray(list(itertools.product([-1,1],repeat=n)));p_exact=float(np.mean(np.abs((signs*x).mean(axis=1))>=abs(mean)-1e-12));boot=x[rng.integers(n,size=(20000,n))].mean(axis=1)
 marker.append({'gene':g,'contrast':left+' minus '+right,'role':'prespecified_primary' if g=='INS' else 'positive_control' if g=='GCG' else 'exploratory_negative_control','unit':'donor','n_donors':n,'donors':units,'donor_effects_log1p_CPM':deltas,'mean':mean,'t_CI95':list(map(float,ci)),'two_sided_t_p':float(test.pvalue),'exact_two_sided_signflip_p':p_exact,'bootstrap_sensitivity_CI95':list(map(float,np.quantile(boot,[.025,.975]))),'minimum_cells_per_donor_type':20})
save('prespecified_marker_results.json',marker)
# Every scientific role below has explicit source provenance; dimensions are computed, not hand-filled.
contracts={
 'baron':{'unit':'donor','n':len(by_donor),'descriptive_cells':len(cells),'groups':['alpha','beta'],'paired':True,'modality':'RNA','source_hash':sha(S/'GSM2230757_human1_umifm_counts.csv.gz'),'role_source':'Baron GSE84133 human1-human4 donor matrices; scRNAseq make-baron-pancreas-data.Rmd donor assignment','pairing_key':'donor','donor_provenance':True},
 'pbmc':{'unit':'donor','n':len(inds),'descriptive_cells':len(pb),'groups':conditions,'paired':pb_pairs,'modality':'RNA_metadata','source_hash':sha(S/'GSE96583_batch2.total.tsne.df.tsv.gz'),'role_source':'GSE96583 author metadata ind and stim columns; no expression results inferred','pairing_key':'ind','donor_provenance':True},
 'airway':{'unit':'cell_line','n':len(air_cells),'descriptive_cells':None,'groups':['trt','untrt'],'paired':air_pairs,'modality':'RNA_metadata','source_hash':sha(S/'airway_sample_table_pinned.csv'),'role_source':'Bioconductor airway sample_table cell/dex; four cell lines, not source-verified distinct donors','pairing_key':'cell','donor_provenance':False}}
save('source_derived_contracts.json',contracts)
def validate(spec,c):
 checks=[]
 def add(code,state,why):checks.append({'requirement':code,'state':state,'witness':why})
 if spec.get('source_hash')!=c['source_hash']:add('source','FAIL','Actual source SHA256 mismatch')
 else:add('source','PASS',c['source_hash'])
 unit=spec.get('unit');kind=spec.get('kind','inference')
 if not unit or unit=='sample':add('unit','UNKNOWN','Inferential parent identity missing or ambiguous')
 elif kind=='description' and unit=='cell' and c['descriptive_cells'] is not None:add('unit','PASS','Legitimate descriptive cell count')
 elif unit=='donor' and not c['donor_provenance']:add('unit','UNKNOWN','Source only identifies cell lines, donor equivalence unavailable')
 elif unit!=c['unit']:add('unit','FAIL','Claim unit differs from source independent parent '+c['unit'])
 else:add('unit','PASS',c['role_source'])
 expected=c['descriptive_cells'] if kind=='description' and unit=='cell' else c['n']
 add('n','UNKNOWN' if spec.get('n') is None else 'PASS' if spec['n']==expected else 'FAIL','Computed eligible count '+str(expected))
 if kind!='description':
  add('comparator','UNKNOWN' if not spec.get('groups') else 'PASS' if set(spec['groups'])==set(c['groups']) else 'FAIL','Actual groups '+str(c['groups']))
  add('pairing','UNKNOWN' if not spec.get('pairing_key') else 'PASS' if spec['pairing_key']==c['pairing_key'] and c['paired'] else 'FAIL','Source matched parent '+c['pairing_key'])
  add('uncertainty','PASS' if spec.get('uncertainty_unit')==c['unit'] else 'UNKNOWN' if not spec.get('uncertainty_unit') else 'FAIL','Resampling/SE unit must match independent parent')
  if spec.get('assay')=='RNA_ATAC':add('assay','FAIL','Provided packet contains no verified same-cell ATAC measurement')
  else:add('assay','PASS','Claim restricted to available RNA source/metadata')
  threshold=spec.get('threshold');add('threshold','UNKNOWN' if threshold is None or not spec.get('threshold_origin') else 'PASS','Explicit protocol threshold origin, not data-derived scientific standard')
 states=[x['state'] for x in checks];decision='WITHHOLD' if 'FAIL' in states else 'ESCALATE' if 'UNKNOWN' in states else 'RELEASE'
 return {'decision':decision,'checks':checks}
cases=[]
for key,c in contracts.items():
 good={'source_hash':c['source_hash'],'unit':c['unit'],'n':c['n'],'groups':c['groups'],'pairing_key':c['pairing_key'],'uncertainty_unit':c['unit'],'assay':'RNA','threshold':.05,'threshold_origin':'Declared two-sided primary protocol, not a universal scientific-validity threshold'}
 variants=[('correct_inference',{},'RELEASE'),('missing_unit',{'unit':None},'ESCALATE'),('ambiguous_sample',{'unit':'sample'},'ESCALATE'),('cell_pseudoreplication',{'unit':'cell','n':c['descriptive_cells'] or 8,'uncertainty_unit':'cell'},'WITHHOLD'),('wrong_n',{'n':c['n']+1},'WITHHOLD'),('missing_n',{'n':None},'ESCALATE'),('wrong_comparator',{'groups':['treated','healthy']},'WITHHOLD'),('missing_pairing',{'pairing_key':None},'ESCALATE'),('false_pairing',{'pairing_key':'barcode'},'WITHHOLD'),('missing_uncertainty',{'uncertainty_unit':None},'ESCALATE'),('cell_resampling',{'uncertainty_unit':'cell'},'WITHHOLD'),('unsupported_ATAC',{'assay':'RNA_ATAC'},'WITHHOLD'),('source_mismatch',{'source_hash':'0'*64},'WITHHOLD'),('missing_threshold_origin',{'threshold_origin':None},'ESCALATE'),('stricter_registered_threshold',{'threshold':.01},'RELEASE')]
 if c['descriptive_cells'] is not None:variants.append(('legitimate_cell_description',{'kind':'description','unit':'cell','n':c['descriptive_cells']},'RELEASE'))
 if key=='airway':variants.append(('unsupported_donor_role',{'unit':'donor'},'ESCALATE'))
 for name,change,expected in variants:
  spec=copy.deepcopy(good);spec.update(change);actual=validate(spec,c);cases.append({'case_id':key+':'+name,'source':key,'input':spec,'expected_control_disposition':expected,'actual':actual,'matches_control':expected==actual['decision']})
save('controlled_source_fault_results.json',cases)
counts=Counter((r['expected_control_disposition'],r['actual']['decision']) for r in cases);summary={'status':'PASS' if all(r['matches_control'] for r in cases) else 'FAIL','cases':len(cases),'passed':sum(r['matches_control'] for r in cases),'retained_valid_controls':sum(r['actual']['decision']=='RELEASE' and r['expected_control_disposition']=='RELEASE' for r in cases),'decision_confusion':{a+' -> '+b:v for (a,b),v in counts.items()},'classification_scope':'Developer-authored controlled scientific contract faults against three actual public artifacts; expected dispositions are not independent expert adjudications. Not a general open-language reasoning accuracy benchmark.','scientific_thresholds':'Protocol declaration checked, not an assertion that p<.05 is sufficient for biological truth.','marker_scope':'Prespecified public donor-level worked packet; not novel biological discovery or researcher-judgment trial.','private_records_accessed':False,'manuscript_modified':False,'source_protocol_sha256':sha(B/'protocol.json'),'driver_sha256':sha(__file__),'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};save('validation_summary.json',summary);print(json.dumps(summary,indent=2));assert summary['status']=='PASS'
