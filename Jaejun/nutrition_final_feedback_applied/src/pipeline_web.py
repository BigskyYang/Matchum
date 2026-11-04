"""v1.4.1-web-feedback: nutrient signals and general food information only."""
import json
import math
from pathlib import Path
from .preprocess_survey import preprocess_survey_response
from .predict import predict_service_features
from .mini_ffq import predict_mini_ffq
from .food_guidance import build_food_guidance
from .display_policy import build_display_summary
ROOT=Path(__file__).resolve().parents[1]
CUTS=json.loads((ROOT/'config/mini_ffq_risk_thresholds.json').read_text(encoding='utf-8'))
SURVEY=json.loads((ROOT/'config/survey_web.json').read_text(encoding='utf-8'))
FFQ_KEYS=('meat_frequency','fish_frequency','egg_frequency','legume_frequency','dairy_frequency')
def _ffq_band(n,p):
 c=CUTS[n]
 return 'Low' if p<=c['low_max'] else ('Mid' if p<=c['mid_max'] else 'High')
def predict_from_survey_web(survey):
 if not isinstance(survey,dict):raise ValueError('survey must be an object')
 extra=set(survey)-{q['id'] for q in SURVEY['questions']}
 if extra:raise ValueError(f'Fields outside web scope: {sorted(extra)}')
 for q in SURVEY['questions']:
  value=survey.get(q['id'])
  if value is None:
   if q['required']:raise ValueError(f"Missing required survey field: {q['id']}")
   continue
  if q['type']=='boolean' and type(value) is not bool:raise ValueError(f"{q['id']}: boolean required")
  if q['type'] in ('number','integer'):
   if type(value) not in (int,float) or not math.isfinite(value):raise ValueError(f"{q['id']}: finite number required")
   if not q['minimum']<=value<=q['maximum']:raise ValueError(f"{q['id']}: value outside permitted range")
   if q['type']=='integer' and int(value)!=value:raise ValueError(f"{q['id']}: integer required")
  if q['type']=='select' and value not in [o['value'] for o in q['options']]:raise ValueError(f"{q['id']}: unexpected answer")
 features=preprocess_survey_response(survey)['model_features']
 return predict_from_features_web(features,mini_ffq_survey=survey)
def predict_from_features_web(feature_row,*,mini_ffq_survey=None):
 lifestyle=predict_service_features(feature_row)
 age=float(feature_row['설명_age']);habitual=None;reason=None
 if not 19<=age<=64:reason='mini_ffq_validated_for_age_19_64_only'
 elif not mini_ffq_survey or any(mini_ffq_survey.get(k) is None for k in FFQ_KEYS):reason='mini_ffq_incomplete'
 else:
  sex='남성' if feature_row['설명_sex']==1 else '여성'
  if mini_ffq_survey.get('sex')!=sex or float(mini_ffq_survey.get('age',-1))!=age:raise ValueError('The two modules must use the same sex and age')
  probs=predict_mini_ffq(mini_ffq_survey)
  habitual={n:{'probability':p,'risk_band':_ffq_band(n,p)} for n,p in probs.items()}
 return {'version':'v1.4.1-web-feedback','model_version':'v1.4-web-retrained','nutrition':{
  'lifestyle_risk':lifestyle,'habitual_diet_risk':habitual,'habitual_diet_available':habitual is not None,
  'habitual_diet_fallback_reason':reason,'combination_policy':'separate_signals_no_probability_averaging'},
  'food_guidance':build_food_guidance(lifestyle,habitual),
  'display_summary':build_display_summary(lifestyle,habitual),
  'lifestyle_cluster':{'status':'managed_by_web','cluster_id':None},
  'model_data_quality':{'status':'invalid_training_codes_removed','reference':'reports/TRAINING_DATA_QUALITY.md','weights_retrained':True}}
