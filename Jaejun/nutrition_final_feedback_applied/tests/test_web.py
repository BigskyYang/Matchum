import copy,json,math,tempfile,unittest
from pathlib import Path
from src.preprocess_survey import preprocess_survey_response,MEAL_FREQ_ORD_MAP,EATINGOUT_FREQ_ORD_MAP,DRINK_FREQ_ORD_MAP
from src.pipeline_web import predict_from_survey_web,predict_from_features_web,_ffq_band
from src.predict import _band,CUTS
from src.validation import validate_service_features
from src.cluster_hook import attach_web_cluster
from scripts.clean_training_unknowns import clean_table
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
class WebTests(unittest.TestCase):
 def setUp(self):self.s=json.loads((ROOT/'examples/example_raw_survey_response.json').read_text())
 def test_meal_out_direction(self):
  for label,expected in {'주 5~7회':3,'주 3~4회':2,'주 1~2회':1,'주 0회':0}.items():
   for field,col in [('breakfast_frequency','ML_breakfast_freq_ord'),('lunch_frequency','ML_lunch_freq_ord'),('dinner_frequency','ML_dinner_freq_ord')]:
    self.s[field]=label;self.assertEqual(preprocess_survey_response(self.s)['model_features'][col],expected)
  for label,expected in {'하루 2회 이상':6,'하루 1회':5,'주 5~6회':4,'주 3~4회':3,'주 1~2회':2,'월 1~3회':1,'거의 안 함':0}.items():
   self.s['eatingout_frequency']=label;self.assertEqual(preprocess_survey_response(self.s)['model_features']['ML_eatingout_freq_ord'],expected)
 def test_month_and_amount_are_independent(self):
  for label,code in DRINK_FREQ_ORD_MAP.items():
   self.s.update(ever_drink=True,drink_frequency=label,drink_amount='3~4잔')
   f=preprocess_survey_response(self.s)['model_features'];self.assertEqual(f['ML_drink_month'],int(code>=2));self.assertEqual(f['ML_drink_amount_ord'],0 if code==0 else 2)
  self.s['ever_drink']=False;self.s.pop('drink_frequency');self.s.pop('drink_amount')
  self.assertEqual(preprocess_survey_response(self.s)['model_features']['ML_drink_freq_ord'],0)
 def test_unknown_rejected(self):
  for field in ('fruit_frequency','vegetable_frequency'):
   s=copy.deepcopy(self.s);s[field]=99
   with self.assertRaises(ValueError):predict_from_survey_web(s)
  f=preprocess_survey_response(self.s)['model_features']
  for bad in (99,float('nan'),float('inf')):
   f['식습관_LS_FRUIT']=bad
   with self.assertRaises(ValueError):validate_service_features(f)
 def test_removed_fields_rejected(self):
  for field in ('phq9','hypertension_diagnosed','diabetes_diagnosed','dyslipidemia_diagnosed','pregnant_or_breastfeeding','kidney_disease_or_stones','anticoagulant_or_aspirin','current_supplements'):
   s=copy.deepcopy(self.s);s[field]=False
   with self.assertRaises(ValueError):predict_from_survey_web(s)
 def test_inference_and_direct_encoded_parity(self):
  out=predict_from_survey_web(self.s)
  direct=predict_from_features_web(preprocess_survey_response(self.s)['model_features'],mini_ffq_survey=self.s)
  self.assertEqual(out,direct);self.assertEqual(len(out['nutrition']['lifestyle_risk']),14);self.assertEqual(len(out['nutrition']['habitual_diet_risk']),10)
  self.assertEqual(set(out),{'version','nutrition','food_guidance','lifestyle_cluster','model_data_quality'})
  for module in ('lifestyle_risk','habitual_diet_risk'):
   for v in out['nutrition'][module].values():self.assertTrue(0<=v['probability']<=1);self.assertIn(v['risk_band'],('Low','Mid','High'))
  phosphorus=next(x for x in out['food_guidance'] if x['nutrient_id']=='phosphorus');self.assertEqual(phosphorus['target'],'below_EAR')
 def test_ffq_fallback(self):
  s=copy.deepcopy(self.s);s['age']=65;o=predict_from_survey_web(s);self.assertIsNone(o['nutrition']['habitual_diet_risk'])
  s=copy.deepcopy(self.s);s.pop('egg_frequency');o=predict_from_survey_web(s);self.assertEqual(o['nutrition']['habitual_diet_fallback_reason'],'mini_ffq_incomplete')
 def test_ffq_age_endpoints_and_json_contract(self):
  for age in (19,64):
   s=copy.deepcopy(self.s);s['age']=age;o=predict_from_survey_web(s)
   self.assertTrue(o['nutrition']['habitual_diet_available'])
   schema=json.loads((ROOT/'config/api_response_schema.json').read_text())
   self.assertEqual(set(o),set(schema['required']))
   self.assertEqual(set(o['nutrition']),set(schema['properties']['nutrition']['required']))
   for values in (o['nutrition']['lifestyle_risk'],o['nutrition']['habitual_diet_risk']):
    for v in values.values():self.assertEqual(set(v),set(schema['$defs']['prediction']['required']))
 def test_required_fields_and_no_extra_profile_output(self):
  required=[q['id'] for q in json.loads((ROOT/'config/survey_web.json').read_text())['questions'] if q['required']]
  for field in required:
   s=copy.deepcopy(self.s);s.pop(field)
   with self.assertRaises(ValueError):predict_from_survey_web(s)
 def test_age_bool_and_duration_validation(self):
  for field,val in [('age',18),('age',35.5),('ever_drink','false'),('smoked_100_cigarettes','false'),('sedentary_minutes',60),('moderate_hours',-1)]:
   s=copy.deepcopy(self.s);s[field]=val
   with self.assertRaises(ValueError):predict_from_survey_web(s)
 def test_threshold_equality(self):
  for n,c in CUTS.items():self.assertEqual(_band(n,c['low_mid']),'Mid');self.assertEqual(_band(n,c['mid_high']),'High')
  c=json.loads((ROOT/'config/mini_ffq_risk_thresholds.json').read_text())
  for n,t in c.items():self.assertEqual(_ffq_band(n,t['low_max']),'Low');self.assertEqual(_ffq_band(n,t['mid_max']),'Mid')
 def test_cleaner_preserves_valid_values(self):
  d=pd.DataFrame({'식습관_LS_FRUIT':[1,9,99,None],'식습관_LS_VEG2':[99,2,8,None]});clean,counts=clean_table(d)
  self.assertEqual(counts,{'식습관_LS_FRUIT':1,'식습관_LS_VEG2':1});self.assertEqual(clean.loc[1,'식습관_LS_FRUIT'],9);self.assertEqual(d.loc[2,'식습관_LS_FRUIT'],99)
 def test_cluster_ids_only_from_supplied_source(self):
  with self.assertRaises(ValueError):attach_web_cluster('N1')
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'nbti12.json';p.write_text(json.dumps([{'id':'N1'},{'id':'O3'}]))
   self.assertEqual(attach_web_cluster('N1',p)['cluster_id'],'N1')
   with self.assertRaises(ValueError):attach_web_cluster('G0_비활동형_0',p)
if __name__=='__main__':unittest.main()
