import hashlib,json,unittest
from pathlib import Path
import joblib,numpy as np
ROOT=Path(__file__).resolve().parents[1]

class RetrainedWeightTests(unittest.TestCase):
 def test_training_cohort_and_reproduction(self):
  r=json.loads((ROOT/'reports/retraining/RETRAIN_COMPARISON.json').read_text())
  self.assertEqual((r['n_training_original'],r['n_training_clean'],r['n_training_removed'],r['n_evaluation']),(9742,9740,2,5320))
  self.assertEqual(len(r['nutrients']),14)
  self.assertTrue(all(x['baseline_reproduction_max_abs_error']<=1e-10 for x in r['nutrients']))
 def test_clean_model_bins_and_input_names(self):
  features=json.loads((ROOT/'config/service_features.json').read_text())
  paths=list((ROOT/'models/service').glob('*.joblib'));self.assertEqual(len(paths),14)
  for p in paths:
   model=joblib.load(p);self.assertEqual(list(model.feature_names_in_),features)
   mapper=getattr(model,'_bin_mapper',None)
   if mapper is not None:
    for bins in mapper.bin_thresholds_[-2:]:self.assertTrue(np.all(bins<=9),p.stem)
 def test_ffq_and_band_boundaries_preserved(self):
  items=json.loads((ROOT/'reports/retraining/PRESERVED_ARTIFACTS.json').read_text());self.assertEqual(len(items),12)
  for item in items:self.assertEqual(hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest(),item['sha256'])

if __name__=='__main__':unittest.main()
