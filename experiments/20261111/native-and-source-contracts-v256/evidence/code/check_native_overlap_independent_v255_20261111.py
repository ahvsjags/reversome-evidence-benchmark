from pathlib import Path
import json,hashlib,collections
E=Path('/ibex/project/c2378/xup0a/reversome_2_1_validation/05_evidence_updates');B=E/'native_geneagent_overlap_v255_20261111';V=B/'benchmark/evaluation_v3';rows=json.load((V/'public_prediction_vectors.json').open());out=json.load((V/'summary.json').open());checks={};single=[r for r in rows if r['reference_label']!='MIXED_SOURCE_RELATIONS'];order=['SUPPORT','CONTRADICT','NOT_ENOUGH_INFO']
for arm,m in out['metrics'].items():
 matrix=[[sum(r['reference_label']==a and r[arm]==b for r in single) for b in order] for a in order];f=[]
 for i in range(3):
  den=sum(matrix[i])+sum(x[i] for x in matrix);f.append(2*matrix[i][i]/den if den else 0)
 checks[arm+'_independent_confusion']=matrix==m['confusion_matrix'];checks[arm+'_independent_macroF1']=abs(sum(f)/3-m['macro_F1_3declaredclasses'])<1e-12;checks[arm+'_all16_compatibility']=sum(r[arm] in r['reference_relation_set'] for r in rows)/16==m['all16_reference_set_compatibility']
checks['all16outputs_retained']=len(rows)==16;checks['mixed_reference_not_silently_relabelled']=[r['case_id'] for r in rows if r['reference_label']=='MIXED_SOURCE_RELATIONS']==['207'];checks['original_worker_intact']=hashlib.sha256((B/'upstream/worker.py').read_bytes()).hexdigest()=='30093aca89feca1578f03d27bfe77ff7dbb2ea053a4e49b6d5cd893f2cd2d7f4';checks['negative_result_not_claimed_superior']=out['certificate_minus_required_corrected_reference_agreement']['difference']==0
resources=json.load((V/'measured_resources.json').open());totals={}
for a in ['native_auto','native_required_tool','certificate_continuation']:
 rs=[r for r in resources if r['arm']==a];fields={k for r in rs for k,v in r.items() if isinstance(v,(int,float))};totals[a]={k:sum(r.get(k,0) for r in rs) for k in fields}
receipt={'status':'PASS' if all(checks.values()) else 'FAIL','passed':sum(checks.values()),'total':len(checks),'checks':checks,'measured_totals':totals,'scope':'Independent standard-library metric reconstruction, not new model executions or independent expert adjudication.'};(V/'independent_check.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2));assert receipt['status']=='PASS'
