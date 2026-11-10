"""Explicit scientific scope, full packet identity and threshold-provenance gates."""
from pathlib import Path
import json,hashlib,copy,datetime,math
E=Path('/ibex/project/c2378/xup0a/reversome_2_1_validation/05_evidence_updates');B=E/'real_source_requirements_v255_20261111';V=B/'validation';O=B/'scientific_extension_v256_1';O.mkdir(exist_ok=False);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();protocol=sha(B/'protocol.json');base=json.load((V/'source_derived_contracts.json').open());facts={}
for name,c in base.items():
 names=sorted(p.name for p in (B/'source').glob('*human*_counts.csv.gz')) if name=='baron' else ['GSE96583_batch2.total.tsne.df.tsv.gz'] if name=='pbmc' else ['airway_sample_table_pinned.csv'];files={n:sha(B/'source'/n) for n in names};bundle=hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest();facts[name]={**c,'files':files,'packet_sha256':bundle,'available_claims':['unit_design','cell_description']+(['marker_contrast'] if name=='baron' else []),'protocol_sha256':protocol}
(O/'actual_source_facts.json').write_text(json.dumps(facts,indent=2))
def check(spec,facts,markers):
 states=[]
 def add(k,state,why):states.append({'requirement':k,'state':state,'witness':why})
 add('full_source_packet','PASS' if spec.get('packet_sha256')==facts['packet_sha256'] else 'FAIL','All declared source files hashed together, not just one matrix')
 kind=spec.get('claim_kind')
 if not kind:add('scientific_claim_type','UNKNOWN','Scientific target must be explicit')
 elif kind not in facts['available_claims']:add('scientific_claim_type','FAIL' if kind=='RNA_ATAC_transfer' else 'UNKNOWN','Provided packet supports '+str(facts['available_claims'])+'; metadata does not establish expression results')
 else:add('scientific_claim_type','PASS','Available source evidence type')
 if spec.get('unit')=='donor' and not facts['donor_provenance']:add('independent_unit','UNKNOWN','Only cell-line provenance is present')
 else:add('independent_unit','PASS' if spec.get('unit')==facts['unit'] else 'FAIL','Actual parent '+facts['unit'])
 add('independent_n','PASS' if spec.get('n')==facts['n'] else 'UNKNOWN' if spec.get('n') is None else 'FAIL','Computed independent parent count '+str(facts['n']))
 add('threshold_provenance','PASS' if spec.get('threshold_protocol_sha256')==facts['protocol_sha256'] else 'UNKNOWN','Must resolve to actual frozen protocol bytes, not a free-text declaration')
 a=spec.get('alpha');alpha_valid=isinstance(a,(int,float)) and not isinstance(a,bool) and math.isfinite(a) and 0<a<=.05;add('threshold_value','UNKNOWN' if a is None else 'PASS' if alpha_valid else 'FAIL','Declared conservative analysis alpha range (0,.05], not a universal biological truth criterion')
 if kind=='marker_contrast':
  m=markers.get(spec.get('gene'));add('computed_effect','UNKNOWN' if m is None or not alpha_valid else 'PASS' if m['mean']>0 and m['two_sided_t_p']<=a else 'FAIL','Actual donor pseudobulk paired-t result, not a prefilled validity label')
  add('statistical_unit','PASS' if spec.get('uncertainty_unit')=='donor' else 'FAIL','Actual paired donor differences; cells do not become independent replicates')
  add('scientific_scope','PASS' if spec.get('scope')=='this_public_packet_parametric_contrast' else 'UNKNOWN','Four-donor parametric result does not establish universal, causal, or cross-modal effects')
 decision='WITHHOLD' if any(r['state']=='FAIL' for r in states) else 'ESCALATE' if any(r['state']=='UNKNOWN' for r in states) else 'RELEASE'
 return {'decision':decision,'checks':states}
markers={m['gene']:m for m in json.load((V/'prespecified_marker_results.json').open())};cases=[]
for name,f in facts.items():
 s={'packet_sha256':f['packet_sha256'],'claim_kind':'unit_design','unit':f['unit'],'n':f['n'],'alpha':.05,'threshold_protocol_sha256':protocol}
 variants=[('correct_design',{},'RELEASE'),('wrong_full_packet',{'packet_sha256':'0'*64},'WITHHOLD'),('missing_claim_type',{'claim_kind':None},'ESCALATE'),('free_text_threshold_claim',{'threshold_protocol_sha256':'we preregistered this'},'ESCALATE'),('permissive_alpha',{'alpha':.5},'WITHHOLD'),('negative_alpha',{'alpha':-.1},'WITHHOLD'),('conservative_alpha',{'alpha':.01},'RELEASE'),('unsupported_cross_modality',{'claim_kind':'RNA_ATAC_transfer'},'WITHHOLD')]
 if name!='baron':variants.append(('metadata_as_expression_result',{'claim_kind':'marker_contrast','gene':'INS','uncertainty_unit':'donor','scope':'this_public_packet_parametric_contrast'},'ESCALATE'))
 for title,patch,expected in variants:
  z=copy.deepcopy(s);z.update(patch);r=check(z,f,markers);cases.append({'case_id':name+':'+title,'input':z,'expected_control':expected,'actual':r,'matches':expected==r['decision']})
for gene in markers:
 s={'packet_sha256':facts['baron']['packet_sha256'],'claim_kind':'marker_contrast','unit':'donor','n':4,'alpha':.05,'threshold_protocol_sha256':protocol,'gene':gene,'uncertainty_unit':'donor','scope':'this_public_packet_parametric_contrast'};r=check(s,facts['baron'],markers);expected='WITHHOLD' if gene=='MS4A1' else 'RELEASE';cases.append({'case_id':'baron:actual_marker:'+gene,'input':s,'expected_control':expected,'actual':r,'matches':expected==r['decision']})
 if gene=='INS':
  for title,patch,expected in [('cell_inference',{'unit':'cell','n':8569,'uncertainty_unit':'cell'},'WITHHOLD'),('universal_scope',{'scope':'all_humans'},'ESCALATE'),('missing_alpha',{'alpha':None},'ESCALATE'),('malformed_alpha',{'alpha':'bad'},'WITHHOLD'),('boolean_alpha',{'alpha':True},'WITHHOLD'),('missing_marker',{'gene':None},'ESCALATE')]:
   z=copy.deepcopy(s);z.update(patch);r=check(z,facts['baron'],markers);cases.append({'case_id':'baron:'+title,'input':z,'expected_control':expected,'actual':r,'matches':expected==r['decision']})
(O/'case_results.json').write_text(json.dumps(cases,indent=2));out={'status':'PASS' if all(r['matches'] for r in cases) else 'FAIL','cases':len(cases),'matched_controls':sum(r['matches'] for r in cases),'valid_controls_retained':sum(r['actual']['decision']=='RELEASE' for r in cases),'source_facts_sha256':sha(O/'actual_source_facts.json'),'base_checks_independently_recomputed':json.load((B/'independent_check/receipt.json').open())['status'],'scope':'Source-bound controlled test extension. No independent expert labels; metadata-only packets cannot authorize measured-expression claims. Threshold validity is a frozen protocol constraint, not automatic scientific-standard discovery.','private_records_accessed':False,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};(O/'summary.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2));assert out['status']=='PASS'
