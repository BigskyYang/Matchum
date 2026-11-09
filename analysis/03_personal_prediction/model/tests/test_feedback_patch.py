import copy,json,hashlib,unittest
from pathlib import Path
from src.preprocess_survey import preprocess_survey_response
from src.pipeline_web import predict_from_survey_web
from src.display_policy import build_display_summary
ROOT=Path(__file__).resolve().parents[1]

class FeedbackTests(unittest.TestCase):
 def setUp(self):self.s=json.loads((ROOT/'examples/example_raw_survey_response.json').read_text())
 def test_smoking_current_status_only(self):
  for state,amount in [(False,0),(True,5)]:
   self.s.update(currently_smoking=state,cigarettes_per_day=amount)
   f=preprocess_survey_response(self.s)['model_features']
   self.assertEqual(f['ML_smoker'],int(state));self.assertEqual(f['ML_cigarettes_day'],amount)
  self.assertNotIn('smoked_100_cigarettes',self.s)
 def test_unified_activity_binary(self):
  for answer in (True,False):
   self.s['aerobic_150min']=answer
   self.assertEqual(preprocess_survey_response(self.s)['model_features']['ML_aerobic'],int(answer))
 def test_sleep_both_web_routes(self):
  self.s.update(regular_sleep_schedule=True,workday_bedtime='00:00',workday_waketime='07:00',restday_bedtime='01:00',restday_waketime='10:00')
  self.assertAlmostEqual(preprocess_survey_response(self.s)['model_features']['ML_sleep_hours'],(7*5+9*2)/7)
  self.s.update(regular_sleep_schedule=False,average_sleep_hours=6.25)
  for key in ('workday_bedtime','workday_waketime','restday_bedtime','restday_waketime'):self.s.pop(key)
  self.assertEqual(preprocess_survey_response(self.s)['model_features']['ML_sleep_hours'],6.25)
 def test_display_prefers_habitual_and_has_no_probability(self):
  ls={'calcium':{'probability':.9,'risk_band':'High'},'magnesium':{'probability':.6,'risk_band':'High'}}
  ff={'calcium':{'probability':.3,'risk_band':'Low'}}
  out=build_display_summary(ls,ff,['calcium','magnesium'])
  self.assertEqual(out['nutrients']['calcium']['display_label'],'낮은 편')
  self.assertEqual(out['nutrients']['calcium']['display_source'],'habitual_diet')
  self.assertTrue(out['nutrients']['calcium']['signals_differ'])
  self.assertEqual(out['nutrients']['magnesium']['display_source'],'lifestyle')
  for row in out['selected_nutrients']:self.assertNotIn('probability',row)
 def test_selection_limit_and_no_invented_ranking(self):
  ls={str(i):{'probability':.9-i*.01,'risk_band':'High'} for i in range(6)}
  out=build_display_summary(ls,None);self.assertEqual(out['selected_nutrients'],[])
  self.assertEqual([x['nutrient_id'] for x in build_display_summary(ls,None,['3','1'])['selected_nutrients']],['3','1'])
  with self.assertRaises(ValueError):build_display_summary(ls,None,list(ls))
  with self.assertRaises(ValueError):build_display_summary(ls,None,['1','1'])
 def test_weight_version_separate_from_adapter(self):
  out=predict_from_survey_web(self.s)
  self.assertEqual(out['model_version'],'v1.4-web-retrained');self.assertEqual(out['version'],'v1.4.1-web-feedback')
  self.assertEqual(out['lifestyle_cluster']['status'],'managed_by_web')
 def test_all_model_and_cutoff_files_preserved(self):
  manifest=json.loads((ROOT/'reports/FEEDBACK_PATCH_PRESERVED_ARTIFACTS.json').read_text())
  self.assertEqual(len(manifest),26)
  for p,digest in manifest.items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),digest)

if __name__=='__main__':unittest.main()
