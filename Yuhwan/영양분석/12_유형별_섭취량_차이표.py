# %% [markdown]
# # 유형별 섭취량 vs 전체 평균 차이표 (대천님 요청, 11/3)
# 12유형 × 16항목(에너지 + 영양소 15) 전부: 유형 평균, 전체 평균, 차이(단위), 차이(%), 같은 성별·나이 보정 차이(%, 11번)
# 평균 = 조사 가중 평균(wt_tot/3). 섭취량은 음식만, 하루 24시간 회상

# %%
import json
import numpy as np
import pandas as pd
from common import *

NB = json.load(open((ROOT.parent if (ROOT.parent / 'Jiyeon').exists() else ROOT.parent / 'Matchum')
                    / 'bigskyyang' / 'analysis' / 'output' / 'nbti_12types.json', encoding='utf-8'))
NAME = {t['id']: t['name'] for t in NB['types']}
IDS = list(NAME)
d = load_persons(ROOT / 'KMedoids_12Types_N1O3.csv', 'Type')
COLS = {'에너지': '영양_N_EN'} | {n: KDRI[n][0] for n in NUTRIENTS}
UNIT = {'에너지': 'kcal', '단백질': 'g', '비타민A': 'μg RAE', '비타민D': 'μg', '비타민E': 'mg', '비타민C': 'mg',
        '티아민': 'mg', '리보플라빈': 'mg', '엽산': 'μg DFE', '칼슘': 'mg', '인': 'mg', '칼륨': 'mg',
        '마그네슘': 'mg', '철': 'mg', '아연': 'mg', '식이섬유': 'g'}
adj = pd.read_csv(OUT / '11_유형별_섭취량_평균대비.csv', encoding='utf-8-sig').set_index(['유형', '항목'])

rows = []
for n, col in COLS.items():
    allm = np.average(d[col], weights=d['w'])
    for c in IDS:
        m = d['cluster'] == c
        tm = np.average(d.loc[m, col], weights=d.loc[m, 'w'])
        a = adj.loc[(c, n)]
        rows.append(dict(유형=c, 이름=NAME[c], 항목=n, 단위=UNIT[n], 유형평균=tm, 전체평균=allm, 차이=tm - allm,
                         차이pct=(tm / allm - 1) * 100, 보정차이pct=a['평균대비pct'], 보정판정=a['판정']))
t = pd.DataFrame(rows)
t.to_csv(OUT / '12_유형별_섭취량_차이표.csv', index=False, encoding='utf-8-sig')

fmt = lambda v, n: f'{v:,.0f}' if abs(v) >= 100 else (f'{v:.1f}' if abs(v) >= 1 else f'{v:.2f}')
lines = ['# 유형별 하루 섭취량 vs 전체 평균 (12유형 × 16항목)', '',
         '- 평균은 조사 가중 평균, 섭취량은 **음식만**(영양제 미포함), 하루 24시간 회상 기준',
         '- **단순 차이**: 유형 평균 − 전체 평균. 유형마다 나이·성별 구성이 달라서 이 값만 보면 오해할 수 있어요 (예: N1 평균 67세)',
         '- **보정 차이**: 같은 성별·나이대끼리 비교한 % 차이 (▼ 의미 있게 적음 / ▲ 많음, 95% CI + FDR)', '']
lines += ['## 한눈에: 보정 차이(%)', '', '| 유형 | ' + ' | '.join(COLS) + ' |', '|---|' + '---:|' * len(COLS)]
for c in IDS:
    g = t[t['유형'] == c].set_index('항목')
    lines.append(f'| {c} {NAME[c]} | ' + ' | '.join(
        f"{g.loc[n, '보정차이pct']:+.0f}{'▼' if g.loc[n, '보정판정'] == '평균보다 적음' else '▲' if g.loc[n, '보정판정'] == '평균보다 많음' else ''}"
        for n in COLS) + ' |')
for c in IDS:
    g = t[t['유형'] == c]
    lines += ['', f'## {c} {NAME[c]}', '', '| 항목 | 단위 | 유형 평균 | 전체 평균 | 단순 차이 | 단순 차이(%) | 보정 차이(%) |', '|---|---|---:|---:|---:|---:|---:|']
    for r in g.itertuples():
        mark = '▼' if r.보정판정 == '평균보다 적음' else '▲' if r.보정판정 == '평균보다 많음' else ''
        lines.append(f'| {r.항목} | {r.단위} | {fmt(r.유형평균, r.항목)} | {fmt(r.전체평균, r.항목)} | {r.차이:+,.1f} | {r.차이pct:+.0f}% | {r.보정차이pct:+.0f}%{mark} |')
open(OUT / '12_유형별_섭취량_차이표.md', 'w', encoding='utf-8').write('\n'.join(lines) + '\n')

pd.set_option('display.width', 250)
print(t.pivot(index='유형', columns='항목', values='차이pct').loc[IDS, list(COLS)].round(0).astype(int).to_string())
print('\n[예시 N2]')
print(t[t['유형'] == 'N2'][['항목', '단위', '유형평균', '전체평균', '차이', '차이pct', '보정차이pct']].round(1).to_string(index=False))
