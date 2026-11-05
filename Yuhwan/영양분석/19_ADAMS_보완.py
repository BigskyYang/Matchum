# %% [markdown]
# # ADAMS 틀 보완 계산 (전유환, 11/4) — 18번 결과와 기존 결과로
#   2. 차별성 편중: 영양소마다 유형 간 차이가 얼마나 큰지 (12유형 관측/기대의 범위·표준편차)
#      → 유형마다 다른 영양소(유형 영역)와 누구에게나 흔한 영양소(공통 영역)가 갈리는지
#   3. 영양 양상이 비슷한 유형 쌍이 실제로 다른 미션을 받는지
#      미션 = 웹 bigskyyang/web/src/data/tips.js의 유형 결과 미션 조건(개인 문항 제외), 유형별 해당 비율(가중)
#   4. 경계에 있는 사람의 안내 품질: 08_군집경계_진단 결과(핵심 vs 경계 2024 AUC) 요약

# %%
import json
import numpy as np
import pandas as pd
from common import *

REPO = ROOT.parent if (ROOT.parent / 'Jiyeon').exists() else ROOT.parent / 'Matchum'
NB = json.load(open(REPO / 'bigskyyang' / 'analysis' / 'output' / 'nbti_12types.json', encoding='utf-8'))
COMMON = [c['nutrient'] for c in NB['common_nutrients']]
IDS = ['N1', 'N2', 'N3', 'A1', 'A2', 'A3', 'S1', 'S2', 'S3', 'O1', 'O2', 'O3']
T = pd.read_csv(OUT / '18_유형_식품군_연결고리.csv', encoding='utf-8-sig')

# %% 2. 영양소별 유형 간 차이
P = T.pivot(index='유형', columns='영양소', values='O/E0').reindex(IDS)
spread = pd.DataFrame({'최소': P.min(), '최대': P.max(), '범위': P.max() - P.min(),
                       '로그 표준편차': np.log(P).std(), '전체 부족률': T.groupby('영양소').apply(
                           lambda g: np.average(g['부족률'], weights=g['인원']), include_groups=False)})
spread['화면 영역'] = ['공통 영역' if n in COMMON else '유형 영역 후보' for n in spread.index]
spread = spread.sort_values('로그 표준편차', ascending=False)
print('2. 영양소별 12유형 관측/기대 차이 (같은 성별·나이 = 1)')
print(spread.round(2).to_string())
print('영역별 로그 표준편차 평균:', spread.groupby('화면 영역')['로그 표준편차'].mean().round(3).to_dict())
spread.round(3).to_csv(OUT / '19_영양소별_유형차이.csv', encoding='utf-8-sig')

# %% 3. 비슷한 유형 쌍의 미션 차이 (웹 tips.js 조건, 유형 결과 미션만)
d = load_persons(ROOT / 'KMedoids_12Types_N1O3.csv', 'Type')
adj = json.load(open(REPO / 'Jiyeon' / 'kmedoids_model.json', encoding='utf-8'))['sleep_year_adjust']['by_year']
d['sleep24'] = [h if y == 2024 else (h - adj[str(int(y))]['mean']) / adj[str(int(y))]['std'] * adj['2024']['std'] + adj['2024']['mean']
                for h, y in zip(d['ML_sleep_hours'], d['year'])]
MISSIONS = {
    '아침 챙기기': d['ML_breakfast_freq_ord'] <= 1,
    '세 끼 시간 맞추기': (d['ML_lunch_freq_ord'] <= 1) | (d['ML_dinner_freq_ord'] <= 1),
    '하루 30분 걷기': d['ML_aerobic'] == 0,
    '주 2회 근력운동': d['ML_strength_days'] < 2,
    '30분 일찍 잠들기': d['sleep24'] < 6,
    '기상 시각 고정': d['sleep24'] > 9.5,
    '하루 10분 쉬어가기': d['ML_stress'] == 1,
    '1시간마다 일어나기': d['ML_sedentary_min'] >= 600,
    '주 2번 집밥·도시락': d['ML_eatingout_freq_ord'] >= 4,
}
M = pd.DataFrame({k: d.assign(x=v.astype(float)).groupby('cluster').apply(lambda g: np.average(g['x'], weights=g['w']), include_groups=False)
                  for k, v in MISSIONS.items()}).reindex(IDS)
print('\n3. 유형별 미션 해당 비율 (가중)')
print((M * 100).round(0).astype(int).to_string())
logP = np.log(P)
pairs = sorted(((a, b, float(np.sqrt(((logP.loc[a] - logP.loc[b]) ** 2).mean()))) for i, a in enumerate(IDS) for b in IDS[i + 1:]),
               key=lambda x: x[2])[:5]
rows = []
for a, b, dist in pairs:
    diff = (M.loc[a] - M.loc[b])
    big = diff[diff.abs() >= 0.3].sort_values(key=abs, ascending=False)
    rows.append(dict(쌍=f'{a}–{b}', 영양_차이=round(dist, 3), 미션_30pp이상_차이=len(big),
                     예시='; '.join(f"{k} {M.at[a, k]:.0%} vs {M.at[b, k]:.0%}" for k in big.index[:3])))
PR = pd.DataFrame(rows)
print('\n영양 양상이 가장 비슷한 5쌍의 미션 차이 (해당 비율 차이 30%p 이상인 미션)')
print(PR.to_string(index=False))
PR.to_csv(OUT / '19_비슷한쌍_미션차이.csv', index=False, encoding='utf-8-sig')

# %% 4. 경계에 있는 사람의 안내 품질 (08_군집경계_진단 결과)
B = pd.read_csv(OUT / '군집경계_핵심vs경계AUC.csv', encoding='utf-8-sig')
bw = B.pivot(index='영양소', columns='구분', values='AUC')[['핵심', '중간', '경계']]
print('\n4. 2024 AUC: 유형 핵심 / 중간 / 경계 고객 (08_군집경계_진단)')
print(bw.round(3).to_string())
print('평균:', bw.mean().round(3).to_dict(), '| 핵심 − 경계 평균', round((bw['핵심'] - bw['경계']).mean(), 3),
      '| 인원:', B.drop_duplicates('구분').set_index('구분')['n'].to_dict())
