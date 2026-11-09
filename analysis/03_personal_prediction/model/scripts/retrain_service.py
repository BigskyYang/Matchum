"""Re-fit only lifestyle models after removing invalid fruit/vegetable codes.

Ground-truth labels must be supplied from the original TargetMatrix. Models are
never trained on pseudo-labels. Held-out 2024 rows cannot influence fitting,
binary cutoff selection, or relative risk-band boundaries.
"""
import os
os.environ.setdefault('OMP_NUM_THREADS','1')
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import argparse,json,hashlib,platform
from pathlib import Path
import joblib,numpy as np,pandas as pd,sklearn
from sklearn.base import clone
from sklearn.metrics import roc_auc_score,average_precision_score,brier_score_loss,roc_curve,accuracy_score,recall_score,precision_score,f1_score

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def md(headers,rows):
 return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(str(v) for v in row)+' |' for row in rows])
def metrics(y,p,t):
 pred=p>=t
 return {'auc':float(roc_auc_score(y,p)),'pr_auc':float(average_precision_score(y,p)),'brier':float(brier_score_loss(y,p)),
         'accuracy':float(accuracy_score(y,pred)),'sensitivity':float(recall_score(y,pred)),
         'specificity':float(recall_score(y,pred,pos_label=0)),'precision':float(precision_score(y,pred,zero_division=0)),
         'f1':float(f1_score(y,pred,zero_division=0))}
def youden(y,p):
 fpr,tpr,t=roc_curve(y,p,drop_intermediate=False);keep=np.isfinite(t);scores=np.where(keep,tpr-fpr,-np.inf)
 return float(t[np.argmax(scores)])
def bands(p,c):return np.where(p<c['low_mid'],'Low',np.where(p<c['mid_high'],'Mid','High'))
def prepare(analysis_path,cluster_path,target_path,features,targets):
 a=pd.read_csv(analysis_path,low_memory=False);c=pd.read_csv(cluster_path,low_memory=False);y=pd.read_csv(target_path,low_memory=False)
 for label,df in [('analysis',a),('cluster',c),('targets',y)]:
  if df.duplicated(['ID','year']).any():raise ValueError(f'Duplicate ID/year in {label}')
 d=a.merge(c,on=['ID','year'],validate='one_to_one').merge(y[['ID','year']+list(targets.values())],on=['ID','year'],validate='one_to_one')
 if len(d)!=len(y):raise ValueError('Some original labeled rows could not be joined')
 if d[features+list(targets.values())].isna().any().any():raise ValueError('Missing features/labels; do not silently change the established cohort')
 for t in targets.values():
  if not d[t].isin([0,1]).all():raise ValueError(f'Nonbinary label: {t}')
 if not (d['ML_drink_month']==(d['ML_drink_freq_ord']>=2).astype(int)).all():raise ValueError('Training drinking codes disagree with >=2 contract')
 for f,valid in [('ML_breakfast_freq_ord',range(4)),('ML_lunch_freq_ord',range(4)),('ML_dinner_freq_ord',range(4)),('ML_eatingout_freq_ord',range(7))]:
  if not d[f].isin(valid).all():raise ValueError(f'Invalid training code: {f}')
 return d

def main(args):
 baseline=Path(args.baseline_root);out=Path(args.output_root)
 if baseline.resolve()==out.resolve():raise ValueError('Keep the baseline separate')
 if sklearn.__version__!='1.8.0':raise ValueError('Use scikit-learn==1.8.0 for original-model reproduction')
 features=json.loads((baseline/'config/service_features.json').read_text());targets=json.loads((baseline/'config/targets.json').read_text());cuts=json.loads((baseline/'config/service_risk_thresholds.json').read_text())
 d=prepare(args.analysis_base,args.cluster_features,args.targets,features,targets)
 invalid=~d['식습관_LS_FRUIT'].isin(range(1,10))|~d['식습관_LS_VEG2'].isin(range(1,10))
 oldtrain=d[d.year.isin([2022,2023])].copy();train=d[d.year.isin([2022,2023])&~invalid].copy();test=d[d.year==2024].copy()
 if invalid[d.year==2024].any():raise ValueError('Holdout has invalid codes; predefine one common valid evaluation cohort first')
 if not len(train) or not len(test):raise ValueError('Both training and evaluation cohorts are required')
 (out/'models/service').mkdir(parents=True,exist_ok=True);(out/'reports/retraining').mkdir(parents=True,exist_ok=True)
 report={'version':'v1.4-web-retrained','training_years':[2022,2023],'evaluation_year':2024,
  'n_training_original':len(oldtrain),'n_training_clean':len(train),'n_training_removed':len(oldtrain)-len(train),'n_evaluation':len(test),
  'cleaning_policy':'drop training rows with fruit/vegetable codes outside 1..9; no imputation; same untouched 2024 cohort',
  'relative_band_policy':'retain original v1.2 fixed JSON thresholds, do not re-estimate from 2024',
  'binary_cutoff_policy':'training predictions only, Youden J, used for diagnostic metrics; not used for Low/Mid/High display',
  'python':platform.python_version(),'sklearn':sklearn.__version__,
  'sources':[{'name':Path(p).name,'sha256':sha(p)} for p in [args.analysis_base,args.cluster_features,args.targets]],'nutrients':[]}
 predictions={};binary={}
 for n,t in targets.items():
  frozen=joblib.load(baseline/f'models/service/{n}.joblib')
  oldp=frozen.predict_proba(test[features])[:,1]
  reproduced=clone(frozen).fit(oldtrain[features],oldtrain[t].astype(int));rp=reproduced.predict_proba(test[features])[:,1]
  maxerr=float(np.max(np.abs(oldp-rp)))
  if maxerr>1e-10:raise ValueError(f'Baseline reproduction failed for {n}: {maxerr}')
  cleaned=clone(frozen).fit(train[features],train[t].astype(int));p=cleaned.predict_proba(test[features])[:,1]
  trainp=cleaned.predict_proba(train[features])[:,1];oldtrainp=frozen.predict_proba(oldtrain[features])[:,1]
  threshold=youden(train[t],trainp);oldthreshold=youden(oldtrain[t],oldtrainp)
  before=metrics(test[t],oldp,oldthreshold);after=metrics(test[t],p,threshold)
  item={'nutrient':n,'target':t,'baseline_reproduction_max_abs_error':maxerr,'n_train':len(train),'n_test':len(test),
    'baseline':before,'cleaned':after,'auc_delta':after['auc']-before['auc'],'brier_delta':after['brier']-before['brier'],
    'mean_abs_probability_change':float(np.mean(abs(p-oldp))),'changed_relative_bands':int(np.sum(bands(p,cuts[n])!=bands(oldp,cuts[n]))),
    'baseline_binary_cutoff':oldthreshold,'cleaned_binary_cutoff':threshold}
  report['nutrients'].append(item)
  binary[n]={'threshold':threshold,'selection':'Youden J on clean training predictions only','n':len(train)}
  joblib.dump(cleaned,out/f'models/service/{n}.joblib')
  # Full individual predictions are retained only in scratch for aggregation.
  predictions[n]={'y':test[t].to_numpy(),'old':oldp,'new':p}
  print(f'{n}: AUC {before["auc"]:.6f} -> {after["auc"]:.6f}; bands changed {item["changed_relative_bands"]}/{len(test)}',flush=True)
 for side in ('baseline','cleaned'):
  report[side+'_macro']={k:float(np.mean([x[side][k] for x in report['nutrients']])) for k in report['nutrients'][0][side]}
 report['macro_auc_delta']=report['cleaned_macro']['auc']-report['baseline_macro']['auc']
 report['macro_brier_delta']=report['cleaned_macro']['brier']-report['baseline_macro']['brier']
 report['average_changed_band_rate']=float(np.mean([x['changed_relative_bands']/len(test) for x in report['nutrients']]))
 for n in targets:
  m=joblib.load(out/f'models/service/{n}.joblib');mapper=getattr(m,'_bin_mapper',None)
  if mapper is not None:
   if any(np.any(b>9) for b in mapper.bin_thresholds_[-2:]):raise ValueError('Invalid fruit/vegetable bin survived re-fit')
 (out/'config/service_binary_thresholds.json').write_text(json.dumps(binary,ensure_ascii=False,indent=2))
 (out/'reports/retraining/RETRAIN_COMPARISON.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 headers=['영양소','기존 AUC','재학습 AUC','차이','기존 Brier','재학습 Brier','등급 변경/5,320']
 rows=[[x['nutrient'],f"{x['baseline']['auc']:.6f}",f"{x['cleaned']['auc']:.6f}",f"{x['auc_delta']:+.6f}",f"{x['baseline']['brier']:.6f}",f"{x['cleaned']['brier']:.6f}",str(x['changed_relative_bands'])] for x in report['nutrients']]
 body='# 과일·채소 99 정리 후 생활습관 모형 재학습\n\n2026-11-04 · 사전에 정한 입력 유효값 정리 목적이며 평가 성능에 따라 후보를 탐색·선택하지 않음.\n\n'
 body+=f'학습: 2022–2023년 {len(oldtrain):,}명 → {len(train):,}명. 평가: 동일 2024년 {len(test):,}명.\n\n'
 body+='정답은 기존 TargetMatrix의 실제 정답 열을 사용함. 원래 영양소 기준을 새로 추정하거나 모형 예측값을 정답으로 사용하지 않음. 전처리와 독립적으로 원본 기준값의 공식 문헌 정확성을 재검증한 작업은 아님.\n\n'
 body+='14개 모든 원본 모형을 같은 데이터·파라미터로 다시 학습했을 때 2024 예측의 최대 절대 차이가 1e-10 이하인지 확인한 후, 비정상 코드가 있는 학습 행만 제외해 같은 파라미터로 재학습함.\n\n'
 body+=md(headers,rows)+'\n\n'
 body+=f"평균 AUC: {report['baseline_macro']['auc']:.6f} → {report['cleaned_macro']['auc']:.6f} (차이 {report['macro_auc_delta']:+.6f}). 평균 Brier: {report['baseline_macro']['brier']:.6f} → {report['cleaned_macro']['brier']:.6f}.\n\n"
 body+=f"고정 등급 경계에서 영양소별 등급 변경률 평균: {report['average_changed_band_rate']*100:.3f}%. 이는 군집 유형 변경률이 아니라 영양소별 Low/Mid/High 변경률임.\n\n"
 body+='## 평가·등급 정책\n\n- 평가 자료는 학습·확률 보정·파라미터 선택·새 경계값 선택에 사용하지 않음.\n- 상대등급은 기존 고정 JSON 경계값을 그대로 사용하여 가중치 정리 효과를 비교함. 등급을 다시 3등분한 버전이 아님.\n- 이진 평가 지표용 cutoff는 각 모형의 학습 예측에서만 Youden J로 계산함. 낮음/보통/높음 표시에는 이진 cutoff를 사용하지 않음.\n- 이번 정리 대상은 생활습관 14개 모형임. mini-FFQ 10개 가중치·경계는 변경하지 않음.\n- 각 영양소의 성능 변화가 모두 같은 방향인 것은 아님. 통계적 유의성·동등성·실제 사용자 효과를 입증한 결과로 해석하지 않음.\n- 제외 2명이 영향을 주는 이유는 단순 표본 수뿐 아니라 트리 분할·최적화 경로 변화도 포함할 수 있음.\n'
 (out/'reports/retraining/RETRAIN_COMPARISON.md').write_text(body,encoding='utf-8')
 print('SUMMARY',json.dumps({k:report[k] for k in ('n_training_removed','baseline_macro','cleaned_macro','macro_auc_delta','average_changed_band_rate')},ensure_ascii=False),flush=True)
 return report
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--analysis-base',required=True);ap.add_argument('--cluster-features',required=True);ap.add_argument('--targets',required=True);ap.add_argument('--baseline-root',required=True);ap.add_argument('--output-root',required=True)
 main(ap.parse_args())
