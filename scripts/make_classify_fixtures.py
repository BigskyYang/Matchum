"""
웹 유형 판정(src/lib/classify.js) 테스트용 예시 응답을 만든다 → web/src/lib/classify.fixtures.json

가상의 응답을 무작위로 만들고, 그 응답의 유형을 Python으로 계산해 정답으로 적는다.
JS 판정이 같은 답을 내는지 classify.test.js가 확인한다. (실제 조사 대상자 자료는 쓰지 않는다)
계산은 analysis/01_clustering/validation/05_jiyeon_improved.py의 assign_from_json과 같다.

사용법 (저장소 루트에서, 모델 nbti12.json을 바꾼 뒤)
  python scripts/make_classify_fixtures.py
"""

import json
from pathlib import Path

import numpy as np

WEB = Path(__file__).resolve().parents[1] / 'web'
MODEL = json.loads((WEB / 'src' / 'data' / 'nbti12.json').read_text(encoding='utf-8'))
OUT = WEB / 'src' / 'lib' / 'classify.fixtures.json'
PER_TYPE = 4

# 웹 설문에서 나올 수 있는 값
CHOICES = {
    'ML_aerobic': [0, 1],
    'ML_strength_days': list(range(6)),
    'ML_sedentary_min': list(range(60, 961, 30)),
    'ML_sleep_hours': [x / 2 for x in range(10, 21)],
    'ML_stress': [0, 1],
    'ML_breakfast_freq_ord': list(range(4)),
    'ML_lunch_freq_ord': list(range(4)),
    'ML_dinner_freq_ord': list(range(4)),
    'ML_eatingout_freq_ord': list(range(7)),
}


def classify(x):
    v = {i['name']: min(i['clip'][1], max(i['clip'][0], x[i['name']])) for i in MODEL['inputs']}
    scores = np.array([s['const'] + sum(c * v[n] for n, c in s['coef'].items()) for s in MODEL['scores']])
    pc = np.array(MODEL['pca']['components']) @ (scores - np.array(MODEL['pca']['mean']))
    macro = min(MODEL['macro'], key=lambda g: ((pc - np.array(g['center'])) ** 2).sum())['code']
    sub = MODEL['sub'][macro]
    names = [s['name'] for s in MODEL['scores']]
    z = (scores[[names.index(f) for f in sub['features']]] - np.array(sub['mean'])) / np.array(sub['std'])
    return macro, min(sub['centers'], key=lambda k: ((z - np.array(sub['centers'][k])) ** 2).sum())


rng = np.random.default_rng(42)
need = {t['id']: PER_TYPE for t in MODEL['types']}
cases = []
for _ in range(200_000):
    if not any(need.values()):
        break
    x = {k: float(rng.choice(v)) for k, v in CHOICES.items()}
    main, leaf = classify(x)
    if need[leaf]:
        need[leaf] -= 1
        cases.append({'features': x, 'main': main, 'leaf': leaf})

missing = [k for k, v in need.items() if v]
assert not missing, f'예시를 못 찾은 유형: {missing}'
OUT.write_text(json.dumps(cases, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print(f'{len(cases)}개 → {OUT}')
