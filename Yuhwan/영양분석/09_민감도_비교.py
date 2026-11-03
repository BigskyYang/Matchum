# %% [markdown]
# # [B-3 민감도] 08번 결과가 대상자 조건에 따라 바뀌는지
# 먼저 실행: python 08_12유형_부족영양소_추천.py [전체|에너지|평소|둘다]
#   에너지 = 하루 에너지 500~5,000kcal만 / 평소 = 조사일 식사량이 평소와 비슷한 사람만(N_DUSUAL==2) / 둘다
# 판정 (결과 보기 전에 확정): 추천 여부(확률 ≥ 0.5)가 칸×영양소의 95% 이상 같고,
#   유형 기여(ΔAUC 95% CI > 0) 판정이 같으면 '결과 견고'

# %%
import pandas as pd
from common import OUT, NUTRIENTS

SUBS = {'전체': '', '에너지': '_민감도_에너지', '평소': '_민감도_평소', '둘다': '_민감도_둘다'}
KEY = ['유형', '성별', '연령대', '영양소']
read = lambda name, s: pd.read_csv(OUT / f'{name}{SUBS[s]}.csv', encoding='utf-8-sig')

# 1. 2024 검증 AUC와 유형 기여
auc = pd.concat({s: read('08_2024검증', s).set_index('영양소')[['Test_AUC', 'ΔAUC', 'ΔAUC_CI_low', '부족률_2024']]
                 for s in SUBS}, axis=1)
auc_tbl = pd.DataFrame({f'{s}_AUC': auc[s]['Test_AUC'] for s in SUBS} |
                       {f'{s}_ΔAUC': auc[s]['ΔAUC'] for s in SUBS} |
                       {f'{s}_유형기여': auc[s]['ΔAUC_CI_low'] > 0 for s in SUBS} |
                       {f'{s}_부족률': auc[s]['부족률_2024'] for s in SUBS}).loc[NUTRIENTS]

# 2. 추천 목록 검증 (2024)
rec = pd.concat({s: read('08_추천목록_2024검증', s).set_index('방법') for s in SUBS})[['평균추천개수', '정밀도', '재현율', 'F1']]

# 3. 확률표: 전체 대비 칸별 차이
base = read('08_유형성별연령_부족확률', '전체').set_index(KEY)
rows = []
for s in ['에너지', '평소', '둘다']:
    o = read('08_유형성별연령_부족확률', s).set_index(KEY).loc[base.index]
    diff = (o['부족확률'] - base['부족확률']).abs()
    flip = o['추천'] != base['추천']
    rows.append(dict(조건=s, 추천일치율=1 - flip.mean(), 추천바뀐칸=int(flip.sum()), 칸수=len(flip),
                     확률차_평균=diff.mean(), 확률차_최대=diff.max(),
                     배수차_평균=(o['배수'] - base['배수']).abs().mean(),
                     **{'바뀐 영양소': ', '.join(f'{k}({v})' for k, v in
                                               flip.groupby(level='영양소').sum().loc[lambda x: x > 0].items())}))
cmp = pd.DataFrame(rows).set_index('조건')
cmp['유형기여_판정같음'] = [(auc_tbl[f'{s}_유형기여'] == auc_tbl['전체_유형기여']).all() for s in cmp.index]
cmp['결과견고'] = (cmp['추천일치율'] >= 0.95) & cmp['유형기여_판정같음']

# 4. 영양소별 확률이 가장 크게 움직인 방향 (둘다 vs 전체, 칸 평균)
o = read('08_유형성별연령_부족확률', '둘다').set_index(KEY).loc[base.index]
shift = (o['부족확률'] - base['부족확률']).groupby(level='영양소').mean().loc[NUTRIENTS]

pd.set_option('display.width', 250)
print('[1. 2024 검증 AUC / 유형 기여 / 2024 부족률]')
print(auc_tbl.round(3).to_string())
print('\n[2. 추천 목록 2024 검증]')
print(rec.round(3).to_string())
print('\n[3. 확률표 비교 (전체 대비, 12유형×2성별×5연령대×15영양소 = 1,800칸)]')
print(cmp.round(3).to_string())
print('\n[4. 둘다 조건에서 부족 확률 평균 변화 (pp)]')
print((shift * 100).round(1).to_string())

auc_tbl.to_csv(OUT / '09_민감도_AUC.csv', encoding='utf-8-sig')
rec.to_csv(OUT / '09_민감도_추천목록.csv', encoding='utf-8-sig')
cmp.to_csv(OUT / '09_민감도_확률표비교.csv', encoding='utf-8-sig')
print('\n저장:', OUT)
