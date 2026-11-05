"""콩 섭취 빈도만 변경한 Python 예측 회귀 자료를 재생성한다 (scikit-learn 1.8.0)."""
import json
from pathlib import Path

import joblib
import pandas as pd
import sklearn

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'Jaejun' / 'nutrition_final_feedback_applied'
OUT = ROOT / 'bigskyyang' / 'web' / 'src' / 'lib' / 'simulationNutrition.fixtures.json'


def main():
    assert sklearn.__version__ == '1.8.0', f'scikit-learn 1.8.0 필요 (현재 {sklearn.__version__})'
    manifest = json.loads((SRC / 'config/mini_ffq_manifest.json').read_text(encoding='utf-8'))
    cuts = json.loads((SRC / 'config/mini_ffq_risk_thresholds.json').read_text(encoding='utf-8'))
    before = {'sex': 2, 'age': 25, 'meat_ord': 3, 'fish_ord': 2, 'egg_ord': 3, 'legume_ord': 2, 'dairy_ord': 2}
    rows = []
    for row in [before, {**before, 'legume_ord': 5}]:
        expected = {}
        for key, meta in manifest.items():
            model = joblib.load(SRC / meta['model_path'])
            p = float(model.predict_proba(pd.DataFrame([row])[meta['features']])[0, 1])
            c = cuts[key]
            expected[key] = {'probability': p, 'band': 'Low' if p <= c['low_max'] else 'Mid' if p <= c['mid_max'] else 'High'}
        rows.append({'row': row, 'expected': expected})
    result = {
        'source': 'Jaejun/nutrition_final_feedback_applied/models/mini_ffq',
        'sklearn': sklearn.__version__, 'change': 'legume_ord 2 -> 5 only', 'cases': rows,
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('sodium:', ' -> '.join(r['expected']['sodium_excess']['band'] for r in rows))


if __name__ == '__main__':
    main()
