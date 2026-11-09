"""설문 중간 통계 카드용: 성별 × 나이대별로 그 습관이 있는 사람 비율 → web/src/data/surveyStats.json

대상: 지연님 유형 분석과 같은 15,062명 (analysis/01_clustering/KNHANES_2022_2024_ML_CLUSTER_COMPLETECASE.csv의 ID, 만 19세 이상)
값:   analysis/data/persons.csv (웹 설문 값과 같은 척도), 조사 가중치 wt_tot 가중 비율
습관 기준은 웹 미션 규칙(web/src/data/tips.js)과 같다
  aerobic     유산소 주 150분 이상 (aerobic = 1)
  sedentary   하루 10시간 이상 앉아 있음 (sedentary_min ≥ 600)
  stress      스트레스를 많이 느낌 (stress = 1)
  breakfast   아침을 주 2번 이하로 먹음 (breakfast ≤ 1)
나이대: 19~29세는 '20대'로 묶고, 70세 이상은 '70대 이상' 한 칸

사람 단위 자료는 git에 올리지 않는다. 이 스크립트가 만드는 JSON에는 칸별 비율과 인원만 들어간다.
사용법 (저장소 루트에서): python scripts/build_survey_stats.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT
OUT = ROOT / 'web' / 'src' / 'data' / 'surveyStats.json'
MIN_N = 100  # 칸 인원이 이보다 적으면 그 칸은 쓰지 않는다 (웹은 성별 전체 값으로 대신)

ids = pd.read_csv(REPO / 'analysis' / '01_clustering' / 'KNHANES_2022_2024_ML_CLUSTER_COMPLETECASE.csv', encoding='utf-8-sig', usecols=['ID'])
d = pd.read_csv(ROOT / 'analysis' / '01_clustering' / 'validation' / 'data' / 'persons.csv', encoding='utf-8-sig').merge(ids, on='ID')
d = d[d['age'] >= 19]

HABITS = {
    'aerobic': d['aerobic'] == 1,
    'sedentary': d['sedentary_min'] >= 600,
    'stress': d['stress'] == 1,
    'breakfast': d['breakfast'] <= 1,
}
d['decade'] = (np.minimum(d['age'], 79) // 10 * 10).clip(lower=20).astype(int)


def rates(sel):
    w = d.loc[sel, 'wt_tot']
    return {'n': int(sel.sum()), **{k: round(float(np.average(v[sel], weights=w)) * 100, 1) for k, v in HABITS.items()}}


groups = {}
for sex in (1, 2):
    groups[f'{sex}'] = rates(d['sex'] == sex)
    for dec in sorted(d['decade'].unique()):
        sel = (d['sex'] == sex) & (d['decade'] == dec)
        if sel.sum() >= MIN_N:
            groups[f'{sex}-{dec}'] = rates(sel)

out = {
    'source': 'KNHANES 2022–2024, 만 19세 이상, 지연님 유형 분석 대상 (wt_tot 가중)',
    'n': int(len(d)),
    'habits': {
        'aerobic': '유산소 주 150분 이상',
        'sedentary': '하루 10시간 이상 앉아 있음',
        'stress': '스트레스를 많이 느낌',
        'breakfast': '아침 주 2번 이하',
    },
    'groups': groups,
}
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'{OUT.name}: {len(d):,}명, {len(groups)}칸')
for k, v in groups.items():
    print(k, v)
