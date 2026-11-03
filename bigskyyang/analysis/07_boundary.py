"""재학습 안정성이 낮은 이유(경계에 있는 사람)와 유형이 바뀌면 안내가 얼마나 바뀌는지 → output/07_경계분석.md

1. 경계 여유(margin): 가장 가까운 중심까지 거리 d1, 두 번째 d2 → (d2 − d1) / d2. 0이면 두 유형의 정확히 가운데.
   대분류(PCA 공간)와 세부(대분류 안 2개 변수 공간) 각각, 그리고 둘 중 작은 값
2. 표본 40%로 20번 다시 학습해 사람마다 유형이 바뀐 비율 → 경계 여유 구간별로 비교
   (재학습 유형은 원래 유형과 겹치는 인원이 최대가 되도록 1:1로 맞춘다 — 헝가리안 매칭. 번호만 바뀐 경우를 '바뀜'으로 세지 않기 위해)
3. 유형이 바뀐 경우 안내가 바뀌는지: 대분류가 같은지, '유형 특이'·'식사량 영향' 영양소 목록이 같은지 (nbti_12types.json 기준)

실행: python 07_boundary.py [N_SUB]   (05_jiyeon_improved.py를 먼저 실행)
"""
import json
import sys

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

from common import OUT, REPO, SEED
from twolevel import assign, fit, fit_pca, jm

sys.stdout.reconfigure(encoding='utf-8')
N_SUB = int(sys.argv[1]) if len(sys.argv) > 1 else 20
SUB_FRAC = 0.4

jdf = pd.read_csv(REPO / 'Jiyeon' / 'KNHANES_2022_2024_ML_CLUSTER_COMPLETECASE.csv', encoding='utf-8-sig')
X, M, _ = jm.build_matrix(jdf)
Q = fit_pca(M).transform(M)
N = len(Q)
model = fit(Q, M, np.arange(N), SEED, 'kmedoids', 10)
lab, macro = assign(model, Q, M)
web = json.loads((OUT / 'nbti_12types.json').read_text(encoding='utf-8'))
guide = {t['id']: (frozenset(x['nutrient'] for x in t['nutrients']['specific']),
                   frozenset(x['nutrient'] for x in t['nutrients']['intake_related'])) for t in web['types']}


def margin(V, C):
    d = np.sqrt(((V[:, None, :] - C[None]) ** 2).sum(2))
    d.sort(axis=1)
    return (d[:, 1] - d[:, 0]) / d[:, 1]


# ── 1. 경계 여유 ──
roles = list(model['macro'])
m_macro = margin(Q, np.array([model['macro'][r] for r in roles]))
m_sub = np.empty(N)
for r in roles:
    sel = np.flatnonzero(macro == r)
    s = model['sub'][r]
    m_sub[sel] = margin((M[np.ix_(sel, s['cols'])] - s['mean']) / s['std'], s['centers'])
m_min = np.minimum(m_macro, m_sub)

# ── 2. 재학습 ──
def match(new):
    """재학습 유형 이름을 원래 유형에 1:1로 맞춘다 (겹치는 인원 최대)."""
    ct = pd.crosstab(pd.Series(new, name='new'), pd.Series(lab, name='old'))
    r, c = linear_sum_assignment(-ct.to_numpy())
    return pd.Series(new).map(dict(zip(ct.index[r], ct.columns[c]))).to_numpy()


rng = np.random.default_rng(SEED)
changed = np.zeros((N_SUB, N), dtype=bool)
macro_changed = np.zeros((N_SUB, N), dtype=bool)
new_labels = []
for b in range(N_SUB):
    idx = rng.choice(N, int(N * SUB_FRAC), replace=False)
    l12 = match(assign(fit(Q, M, idx, b, 'kmedoids', 10), Q, M)[0])
    changed[b] = l12 != lab
    macro_changed[b] = pd.Series(l12).str[0].to_numpy() != pd.Series(lab).str[0].to_numpy()
    new_labels.append(l12)
    print(b, f'{changed[b].mean():.1%}', flush=True)
rate = changed.mean(0)

bins = [0, 0.05, 0.1, 0.2, 0.3, 1.0001]
names = ['0–5% (경계 바로 위)', '5–10%', '10–20%', '20–30%', '30% 이상 (중심 가까이)']
grp = pd.cut(m_min, bins, labels=names, right=False)
by = pd.DataFrame({'구간': grp, 'rate': rate, 'never': rate == 0, 'often': rate >= 0.5}).groupby('구간', observed=False).agg(
    인원=('rate', 'size'), 바뀐_비율_평균=('rate', 'mean'), 한_번도_안_바뀜=('never', 'mean'), 절반_이상_바뀜=('often', 'mean'))
by['인원 비율'] = by['인원'] / N
by['전체 바뀜 중 차지'] = [changed[:, (grp == g)].sum() / changed.sum() for g in names]
by = by[['인원', '인원 비율', '바뀐_비율_평균', '한_번도_안_바뀜', '절반_이상_바뀜', '전체 바뀜 중 차지']]

# 같은 응답을 가진 사람 묶음: 설문 응답이 이산값이라 같은 칸에 몰린 사람이 경계에 걸리면 한꺼번에 바뀐다
inputs = ['ML_aerobic', 'ML_strength_days', 'ML_sedentary_min', 'ML_sleep_hours', 'ML_stress',
          'ML_breakfast_freq_ord', 'ML_lunch_freq_ord', 'ML_dinner_freq_ord', 'ML_eatingout_freq_ord']
raw = pd.DataFrame(X, columns=jm.FEATURES)[inputs].round(3)
n_unique = len(raw.drop_duplicates())

# ── 3. 바뀌면 안내가 바뀌나 ──
pairs = []
for b in range(N_SUB):
    ch = np.flatnonzero(changed[b])
    for i in ch:
        o, n_ = lab[i], new_labels[b][i]
        pairs.append((o[0] == n_[0], guide[o][0] == guide[n_][0], guide[o] == guide[n_], o, n_))
pairs = pd.DataFrame(pairs, columns=['same_macro', 'same_specific', 'same_all', 'from', 'to'])
top_moves = pairs.groupby(['from', 'to']).size().sort_values(ascending=False).head(8)
tnames = {t['id']: t['name'] for t in web['types']}

# 유형별: 경계 여유 중앙값과 재학습 때 바뀐 비율
per_type = pd.DataFrame({'type': lab, 'margin': m_min, 'rate': rate}).groupby('type').agg(
    인원=('rate', 'size'), 경계여유_중앙값=('margin', 'median'), 재학습시_바뀐_비율=('rate', 'mean'))
order = [t['id'] for t in web['types']]
per_type = per_type.loc[order]
per_type.index = [f'{k} {tnames[k]}' for k in per_type.index]

pct = lambda x: f'{x:.1%}'  # noqa: E731
md = [
    '# 경계 분석: 재학습 안정성이 낮은 이유와 안내에 미치는 영향', '',
    f'지연님 12개 유형(보완판) {N:,}명. 표본 {SUB_FRAC:.0%}로 {N_SUB}번 다시 학습해 원래 유형과 비교했다.', '',
    '## 요약', '',
    f'- 재학습 1회에 유형이 바뀌는 사람: 평균 {changed.mean():.1%} (대분류가 바뀌는 사람 {macro_changed.mean():.1%})',
    f'- {N_SUB}번 중 한 번도 안 바뀐 사람 {pct((rate == 0).mean())}, 절반 이상 바뀐 사람 {pct((rate >= 0.5).mean())}',
    f'- 경계 여유 10% 미만(두 유형 거의 가운데)인 사람 {pct((m_min < 0.1).mean())} → 이 사람들이 전체 바뀜의 '
    f'{changed[:, m_min < 0.1].sum() / changed.sum():.0%}를 차지',
    f'- 유형이 바뀐 경우 {pct(pairs["same_macro"].mean())}는 같은 대분류 안에서 옆 유형으로 이동, '
    f'{pct(pairs["same_specific"].mean())}는 "유형 특이 영양소" 안내가 그대로, '
    f'{pct(pairs["same_all"].mean())}는 영양 안내(유형 특이 + 식사량 영향)가 모두 그대로',
    f'- 공통 주의 영양소({", ".join(x["nutrient"] for x in web["common_nutrients"])})는 모든 유형에 같아 유형이 바뀌어도 그대로',
    '',
    '## 1. 경계 여유 구간별로 보면', '',
    '경계 여유 = (두 번째로 가까운 중심 거리 − 가장 가까운 중심 거리) ÷ 두 번째 거리. 대분류와 세부 중 작은 값.', '',
    by.to_markdown(floatfmt='.3f'), '',
    f'- 설문 응답이 이산값(0/1, 0~3, 0~6 등)이라 9개 응답 조합은 {n_unique:,}가지뿐이다. 같은 칸의 사람들이 경계에 걸리면 함께 바뀐다.',
    '',
    '## 2. 유형별', '',
    per_type.to_markdown(floatfmt='.3f'), '',
    '## 3. 자주 일어나는 이동 (재학습 전체 합)', '',
    '| 원래 유형 | 바뀐 유형 | 횟수 | 대분류 같음 |', '|---|---|---:|---|',
] + [f'| {a} {tnames[a]} | {b_} {tnames[b_]} | {c:,} | {"예" if a[0] == b_[0] else "아니오"} |'
     for (a, b_), c in top_moves.items()] + ['']
(OUT / '07_경계분석.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
print('\n'.join(md))
