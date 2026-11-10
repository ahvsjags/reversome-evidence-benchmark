"""Second implementation: pandas chunks and independent donor arithmetic."""
from pathlib import Path
import json,hashlib,urllib.request,itertools
import numpy as np,pandas as pd
from scipy import stats
E=Path(__import__('os').environ.get('REVERSOME_EVIDENCE_ROOT','/ibex/project/c2378/xup0a/reversome_2_1_validation/05_evidence_updates'));B=E/'real_source_requirements_v255_20261111';O=B/'independent_check';O.mkdir(exist_ok=False);V=B/'validation';source=json.load((V/'donor_pseudobulk_counts.json').open());checks={};recomputed={};n_cells=0;unique=set();libs=set();genes=['INS','GCG','MS4A1'];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for i in range(1,5):
 donor='human'+str(i);p=B/'source'/('GSM'+str(2230756+i)+'_human'+str(i)+'_umifm_counts.csv.gz');a={}
 for chunk in pd.read_csv(p,chunksize=128):
  cols=chunk.columns[3:];assert len(cols)==20125;totals=chunk.iloc[:,3:].sum(axis=1).to_numpy(dtype=np.int64);n_cells+=len(chunk);unique.update(chunk.iloc[:,0]);libs.update(chunk.iloc[:,0].str.split('.final_cell_',regex=False).str[0]);chunk=chunk.assign(ALL_UMI=totals)
  for ct,g in chunk.groupby('assigned_cluster',sort=True):
   z=a.setdefault(ct,{'n_cells':0,'UMI':0,'gene_UMI':[0,0,0]});z['n_cells']+=len(g);z['UMI']+=int(g.ALL_UMI.sum());z['gene_UMI']=[z['gene_UMI'][j]+int(g[gene].sum()) for j,gene in enumerate(genes)]
 recomputed[donor]=a;checks[donor+'_all_celltype_pseudobulk']=a==source['aggregates'][donor]
checks['total_cells']=n_cells==source['n_cells'];checks['source_qualified_cell_IDs']=len(unique)==source['source_qualified_unique']==n_cells;checks['libraries']=sorted(libs)==source['libraries']
for m in json.load((V/'prespecified_marker_results.json').open()):
 j=genes.index(m['gene']);left,right=m['contrast'].split(' minus ');x=[]
 for donor in sorted(recomputed):
  c=recomputed[donor]
  if min(c[left]['n_cells'],c[right]['n_cells'])>=20:x.append(np.log1p(c[left]['gene_UMI'][j]*1e6/c[left]['UMI'])-np.log1p(c[right]['gene_UMI'][j]*1e6/c[right]['UMI']))
 x=np.asarray(x);checks[m['gene']+'_donor_effects']=bool(np.allclose(x,m['donor_effects_log1p_CPM'],atol=1e-12,rtol=0));checks[m['gene']+'_t_p']=abs(float(stats.ttest_1samp(x,0).pvalue)-m['two_sided_t_p'])<1e-12;v=np.asarray(list(itertools.product([-1,1],repeat=len(x))));checks[m['gene']+'_exact_signflip']=float(np.mean(np.abs(v@x/len(x))>=abs(x.mean())-1e-12))==m['exact_two_sided_signflip_p']
# Retain source-role witnesses, rather than treating filenames as donor proof.
urls={'baron_curator':'https://genome.ucsc.edu/cgi-bin/hgTrackUi?db=hg38&g=pancreasBaron','baron_recipe':'https://rdrr.io/github/drisso/scRNAseq/f/inst/scripts/2.0.0/make-baron-pancreas-data.Rmd','airway_package':'https://bioconductor.org/packages/release/data/experiment/html/airway.html','pbmc_GEO':'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE96583'};receipts=[]
for name,url in urls.items():
 try:
  p=O/(name+'.html')
  with urllib.request.urlopen(url,timeout=90) as r:p.write_bytes(r.read())
  receipts.append({'name':name,'url':url,'sha256':sha(p),'bytes':p.stat().st_size,'status':'DOWNLOADED'})
 except Exception as ex:receipts.append({'name':name,'url':url,'status':'FAILED','error':str(ex)})
(O/'source_role_witnesses.json').write_text(json.dumps(receipts,indent=2))
tests=json.load((V/'controlled_source_fault_results.json').open());checks['all_frozen_fault_axes_present']=all(any(x in r['case_id'] for r in tests) for x in ['missing_unit','wrong_n','wrong_comparator','false_pairing','unsupported_ATAC','source_mismatch','missing_uncertainty','missing_threshold_origin']);checks['valid_controls_retained']=sum(r['actual']['decision']=='RELEASE' for r in tests)==8;checks['all_actual_source_hashes_bound']=all(r['input']['source_hash']==json.load((V/'source_derived_contracts.json').open())[r['source']]['source_hash'] for r in tests if 'source_mismatch' not in r['case_id']);checks['at_least_one_donor_role_witness_fetched']=any(r['status']=='DOWNLOADED' and r['name'] in ['baron_curator','baron_recipe'] for r in receipts)
receipt={'status':'PASS' if all(checks.values()) else 'FAIL','passed':sum(checks.values()),'total':len(checks),'checks':checks,'independent_implementation':'Pandas chunked full 20125-gene sums versus original CSV/NumPy row parser; independently recomputed donor t/signflip. Fault labels remain developer-authored, not independent human adjudication.'};(O/'receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2));assert receipt['status']=='PASS'
