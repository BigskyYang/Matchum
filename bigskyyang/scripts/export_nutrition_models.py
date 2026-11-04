"""
재준님 영양 위험 예측 모델(v1.4-web-retrained)을 웹용 JSON으로 바꾼다 → web/src/data/nutritionModels.json
휴대폰에서 같은 계산을 하도록 모델 값(트리 분기·계수)만 옮긴다. 학습·확률 보정·등급 경계는 바꾸지 않는다

입력: Jaejun/nutrition_final_feedback_applied/
  models/service/*.joblib   생활습관 모델 14개 (HistGradientBoosting 13 + 로지스틱 회귀 1, 입력 18개)
  models/mini_ffq/*.joblib  평소 식사(mini-FFQ) 모델 10개 (로지스틱 회귀, 입력 7개, 19~64세)
  config/service_risk_thresholds.json, config/mini_ffq_risk_thresholds.json  낮음·보통·높음 경계 (고정값)
출력:
  web/src/data/nutritionModels.json      모델 값 + 경계
  web/src/lib/nutritionModels.fixtures.json  파이썬으로 계산한 예시 응답의 확률 (웹 계산과 같은지 테스트)

재준님 모델이 바뀌면 다시 실행한다 (bigskyyang 폴더에서, scikit-learn 1.8.0 필요: 모델 파일이 1.8.0으로 저장됨)
  python scripts/export_nutrition_models.py
"""

import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'Jaejun' / 'nutrition_final_feedback_applied'
WEB = ROOT / 'bigskyyang' / 'web' / 'src'
OUT = WEB / 'data' / 'nutritionModels.json'
FIXTURES = WEB / 'lib' / 'nutritionModels.fixtures.json'

assert sklearn.__version__ == '1.8.0', f'scikit-learn 1.8.0이 필요해요 (지금 {sklearn.__version__})'

read = lambda p: json.loads((SRC / p).read_text(encoding='utf-8'))
FEATURES = read('config/service_features.json')
FFQ = read('config/mini_ffq_manifest.json')
SIG = 10   # 소수 유효숫자 (확률 차이 1e-9 이하)


def num(x):
    return float(f'{float(x):.{SIG}g}')


def logistic(pipe, features):
    scaler, lr = pipe.named_steps['standardscaler'], pipe.named_steps['logisticregression']
    assert list(pipe.feature_names_in_) == features
    return {
        'type': 'logistic',
        'mean': [num(v) for v in scaler.mean_],
        'scale': [num(v) for v in scaler.scale_],
        'coef': [num(v) for v in lr.coef_[0]],
        'intercept': num(lr.intercept_[0]),
    }


def hgb(model):
    assert list(model.feature_names_in_) == FEATURES and model.is_categorical_ is None
    trees = []
    for [predictor] in model._predictors:
        nodes = predictor.nodes
        assert not np.isnan(nodes['num_threshold'][~nodes['is_leaf'].astype(bool)]).any()
        leaf = nodes['is_leaf'].astype(bool)
        # 노드마다 [변수 번호(잎이면 -1), 경계값(잎이면 값), 왼쪽, 오른쪽]. 값 <= 경계면 왼쪽
        trees.append({
            'f': [-1 if lf else int(f) for lf, f in zip(leaf, nodes['feature_idx'])],
            # 경계값은 반올림하지 않는다: (주중×5 + 주말×2)/7 같은 응답값이 경계와 정확히 같을 수 있다
            't': [num(v) if lf else float(t) for lf, v, t in zip(leaf, nodes['value'], nodes['num_threshold'])],
            'l': [int(x) for x in nodes['left']],
            'r': [int(x) for x in nodes['right']],
        })
    return {'type': 'hgb', 'baseline': num(model._baseline_prediction[0][0]), 'trees': trees}


def export(model, features):
    return logistic(model, features) if hasattr(model, 'named_steps') else hgb(model)


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


lifestyle, ffq, files = {}, {}, {}
for path in sorted((SRC / 'models' / 'service').glob('*.joblib')):
    lifestyle[path.stem] = export(joblib.load(path), FEATURES)
    files[f'models/service/{path.name}'] = sha(path)
for nutrient, meta in FFQ.items():
    path = SRC / meta['model_path']
    ffq[nutrient] = export(joblib.load(path), meta['features'])
    files[meta['model_path']] = sha(path)
ffq_features = next(iter(FFQ.values()))['features']
assert all(m['features'] == ffq_features for m in FFQ.values())

cuts = read('config/service_risk_thresholds.json')
ffq_cuts = read('config/mini_ffq_risk_thresholds.json')
out = {
    'version': 'v1.4-web-retrained',
    'source': 'Jaejun/nutrition_final_feedback_applied',
    'note': [
        '생활습관 모델(lifestyle): 입력 18개, 낮음 p < low_mid ≤ 보통 < mid_high ≤ 높음',
        '평소 식사 모델(habitual, mini-FFQ): 19~64세만, 입력 7개, 낮음 p ≤ low_max < 보통 ≤ mid_max < 높음',
        '두 모델의 확률은 평균하지 않는다 (재준님 원칙). 위험 등급은 학습 자료 안의 상대 등급이며 결핍 진단이 아니다',
    ],
    'lifestyle': {
        'features': FEATURES,
        'cuts': {n: {'low_mid': cuts[n]['low_mid'], 'mid_high': cuts[n]['mid_high']} for n in lifestyle},
        'models': lifestyle,
    },
    'habitual': {
        'features': ffq_features,
        'cuts': {n: {'low_max': ffq_cuts[n]['low_max'], 'mid_max': ffq_cuts[n]['mid_max']} for n in ffq},
        'models': ffq,
    },
    'model_sha256': files,
}
OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')

# 웹 계산과 비교할 예시: 학습 범위 안의 무작위 응답 + 경계값
rng = np.random.default_rng(2026)
RANGES = {
    '설명_sex': [1, 2], '설명_age': list(range(19, 81)), 'ML_smoker': [0, 1], 'ML_drink_freq_ord': list(range(6)),
    'ML_aerobic': [0, 1], 'ML_strength_days': list(range(6)), 'ML_stress': [0, 1],
    'ML_breakfast_freq_ord': list(range(4)), 'ML_lunch_freq_ord': list(range(4)), 'ML_dinner_freq_ord': list(range(4)),
    'ML_eatingout_freq_ord': list(range(7)), '식습관_LS_FRUIT': list(range(1, 10)), '식습관_LS_VEG2': list(range(1, 10)),
}
rows = []
for _ in range(60):
    r = {k: float(rng.choice(v)) for k, v in RANGES.items()}
    r['ML_cigarettes_day'] = float(rng.integers(1, 30)) if r['ML_smoker'] else 0.0
    r['ML_drink_month'] = float(r['ML_drink_freq_ord'] >= 2)
    r['ML_drink_amount_ord'] = float(rng.integers(1, 6)) if r['ML_drink_freq_ord'] else 0.0
    r['ML_sedentary_min'] = float(rng.integers(0, 17) * 60)
    # 수면: 절반은 30분 단위 시각으로 답한 (주중×5 + 주말×2)/7 (트리 경계와 정확히 같은 값이 나올 수 있다)
    r['ML_sleep_hours'] = (float(rng.integers(8, 20)) / 2 * 5 + float(rng.integers(8, 22)) / 2 * 2) / 7 if rng.random() < 0.5         else float(np.round(rng.uniform(4, 10), 3))
    rows.append({f: r[f] for f in FEATURES})
X = pd.DataFrame(rows)
ffq_rows = [{'sex': r['설명_sex'], 'age': min(r['설명_age'], 64), **{k: float(rng.integers(0, 8)) for k in ffq_features[2:]}} for r in rows]
XF = pd.DataFrame(ffq_rows)
fixtures = {
    'lifestyle': {'rows': rows, 'probability': {}},
    'habitual': {'rows': ffq_rows, 'probability': {}},
}
for path in sorted((SRC / 'models' / 'service').glob('*.joblib')):
    fixtures['lifestyle']['probability'][path.stem] = joblib.load(path).predict_proba(X)[:, 1].tolist()
for nutrient, meta in FFQ.items():
    fixtures['habitual']['probability'][nutrient] = joblib.load(SRC / meta['model_path']).predict_proba(XF[meta['features']])[:, 1].tolist()
FIXTURES.write_text(json.dumps(fixtures, ensure_ascii=False) + '\n', encoding='utf-8')

print(f'{OUT.name}: {OUT.stat().st_size / 1e6:.2f} MB, 생활습관 {len(lifestyle)}개 · 평소 식사 {len(ffq)}개')
print(f'{FIXTURES.name}: 예시 {len(rows)}명')
