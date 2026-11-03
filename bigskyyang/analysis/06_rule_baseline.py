"""지연님 12개 유형(보완판) vs 규칙 대조군 → output/06_규칙대조군.md

질문: "군집이 단순 규칙(필터링)과 다를 게 있나?"
1. 재현: 설문 9개 응답으로 얕은 결정나무(깊이 1~6)가 12개 유형·4개 대분류를 얼마나 맞히나
   (2022–23 학습 → 2024 평가. 깊이 d 나무 = 질문 d개 이하로 나누는 규칙)
2. 대조군 규칙: 사람이 정한 MBTI식 4축(운동·스트레스·좌식·규칙식사, 각 예/아니오 → 16개)과
   깊이별 나무 규칙을 '유형'으로 써서 군집과 같은 지표(영양 차이, 2024 AUC, 생활습관 η²)로 비교
3. 대분류가 문항 하나로 갈리는지: 대분류별 스트레스·유산소 '예' 비율

실행: python 06_rule_baseline.py   (05_jiyeon_improved.py를 먼저 실행해야 data/labels_12.csv가 있다)
"""
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier, export_text

from common import DATA, EAR_NUTRIENTS, FEATURE_NAMES, OUT, REPO, SEED, adjusted_ratios, ratio_separation, specific_rows
from twolevel import jm

sys.stdout.reconfigure(encoding='utf-8')

INPUTS = ['ML_aerobic', 'ML_strength_days', 'ML_sedentary_min', 'ML_sleep_hours', 'ML_stress',
          'ML_breakfast_freq_ord', 'ML_lunch_freq_ord', 'ML_dinner_freq_ord', 'ML_eatingout_freq_ord']
KO = {'ML_aerobic': '유산소', 'ML_strength_days': '근력운동일', 'ML_sedentary_min': '좌식분', 'ML_sleep_hours': '수면',
      'ML_stress': '스트레스', 'ML_breakfast_freq_ord': '아침', 'ML_lunch_freq_ord': '점심', 'ML_dinner_freq_ord': '저녁',
      'ML_eatingout_freq_ord': '외식'}

# ── 데이터: 군집 입력(수면은 2024 척도), 12개 유형, 영양 결과 ──
jdf = pd.read_csv(REPO / 'Jiyeon' / 'KNHANES_2022_2024_ML_CLUSTER_COMPLETECASE.csv', encoding='utf-8-sig')
X, _, _ = jm.build_matrix(jdf)
inp = pd.DataFrame(X, columns=jm.FEATURES)[INPUTS].assign(ID=jdf['ID'].to_numpy(), year=jdf['year'].to_numpy())
lab = pd.read_csv(DATA / 'labels_12.csv', encoding='utf-8-sig')
inp = inp.merge(lab, on='ID')
inp['macro'] = inp['type'].str[0]
tr = (inp['year'] < 2024).to_numpy()
te = ~tr
Xi = inp[INPUTS].to_numpy()

# ── 1. 얕은 나무로 재현 ──
rep_rows, trees = [], {}
for depth in range(1, 7):
    row = {'깊이(질문 수)': depth}
    for target, name in [('type', '12개 유형'), ('macro', '대분류 4개')]:
        t = DecisionTreeClassifier(max_depth=depth, random_state=SEED).fit(Xi[tr], inp.loc[tr, target])
        row[f'{name} 재현율(2024)'] = f'{(t.predict(Xi[te]) == inp.loc[te, target]).mean():.1%}'
        row[f'{name} 규칙 수(잎)'] = t.get_n_leaves()
        trees[(target, depth)] = t
    rep_rows.append(row)
rep = pd.DataFrame(rep_rows).set_index('깊이(질문 수)')

# ── 2. 대조군 규칙 ──
# 기준점은 전체 중앙값 (사람이 정한다고 가정하는 단순한 기준)
meal_sum = inp[['ML_breakfast_freq_ord', 'ML_lunch_freq_ord', 'ML_dinner_freq_ord']].sum(axis=1)
cut_sed, cut_meal = float(inp['ML_sedentary_min'].median()), float(meal_sum.median())
axes = {
    '운동': (inp['ML_aerobic'] == 1) | (inp['ML_strength_days'] >= 2),
    '스트레스': inp['ML_stress'] == 1,
    '좌식': inp['ML_sedentary_min'] >= cut_sed,
    '규칙식사': meal_sum >= cut_meal,
}
inp['rule16'] = [''.join(k[0] if v else '·' for k, v in zip(axes, r)) for r in zip(*axes.values())]
for depth in (2, 4, 6):
    # 나무 규칙은 12개 유형을 흉내 내도록 학습한 것 → 전체에 적용해 '규칙 유형'으로 쓴다
    inp[f'tree{depth}'] = trees[('type', depth)].predict(Xi)
    inp[f'leaf{depth}'] = trees[('type', depth)].apply(Xi)

d = pd.read_csv(DATA / 'persons.csv', encoding='utf-8-sig').merge(
    inp.drop(columns=['year'] + INPUTS), on='ID')
dd = d[d['N_EN'].notna()].reset_index(drop=True)
dd['age_grp'] = pd.Categorical(dd['age_grp'])
dd['energy_q'] = pd.qcut(dd['N_EN'], 5, labels=False)
ttr = (dd['year'] < 2024).to_numpy()
demo = OneHotEncoder(handle_unknown='ignore').fit(dd[['sex', 'age_grp']].astype(str))
Xd = demo.transform(dd[['sex', 'age_grp']].astype(str)).toarray()


def auc_with(extra):
    aucs = []
    for n in EAR_NUTRIENTS:
        y = dd[f'below_{n}'].to_numpy()
        Xa = Xd if extra is None else np.hstack([Xd, extra])
        clf = LogisticRegression(max_iter=2000).fit(Xa[ttr], y[ttr])
        aucs.append(roc_auc_score(y[~ttr], clf.predict_proba(Xa[~ttr])[:, 1]))
    return float(np.mean(aucs))


def eta2(col):
    Z = StandardScaler().fit_transform(d[FEATURE_NAMES].to_numpy(float))
    out = {}
    for j, f in enumerate(FEATURE_NAMES):
        s = pd.Series(Z[:, j])
        g = s.groupby(d[col].to_numpy())
        out[f] = 1 - (g.var(ddof=0) * g.size()).sum() / (s.var(ddof=0) * len(s))
    return out


ACTIVE = ['aerobic', 'strength_days', 'sedentary_min', 'sleep_hours', 'stress', 'breakfast', 'lunch', 'dinner', 'eating_out']
CANDS = {'군집 12개 (보완판)': 'type', '군집 대분류 4개': 'macro',
         '나무 규칙 깊이 2': 'leaf2', '나무 규칙 깊이 4': 'leaf4', '나무 규칙 깊이 6': 'leaf6',
         '사람이 정한 4축 규칙 (16개)': 'rule16'}
cmp_rows = []
for name, col in CANDS.items():
    r_sa = adjusted_ratios(dd, dd[col].to_numpy(), ['sex', 'age_grp'])
    r_en = adjusted_ratios(dd, dd[col].to_numpy(), ['sex', 'age_grp', 'energy_q'])
    size = d[col].value_counts(normalize=True)
    e = eta2(col)
    cmp_rows.append({
        '안': name, '유형 수': d[col].nunique(), '가장 작은 유형': f'{size.min():.1%}',
        '12개 유형과 일치': f'{(d[col].map(pd.crosstab(d[col], d["type"]).idxmax(axis=1)) == d["type"]).mean():.1%}',
        '군집 입력 9개 η² 평균': round(float(np.mean([e[f] for f in ACTIVE])), 3),
        '영양 차이(성별·연령)': round(ratio_separation(r_sa), 3),
        '영양 차이(+에너지)': round(ratio_separation(r_en), 3),
        '특이 영양소(+에너지)': len(specific_rows(r_en)),
        '2024 AUC(성별·연령+유형)': round(auc_with(OneHotEncoder(handle_unknown='ignore').fit_transform(dd[[col]].astype(str)).toarray()), 3),
    })
cmp = pd.DataFrame(cmp_rows).set_index('안').T
auc_demo = auc_with(None)
auc_raw = auc_with(StandardScaler().fit(dd.loc[ttr, FEATURE_NAMES]).transform(dd[FEATURE_NAMES]))

# ── 3. 대분류가 문항 하나로 갈리나 ──
one = inp.groupby('macro').agg(인원=('ID', 'size'), 스트레스_예=('ML_stress', 'mean'), 유산소_예=('ML_aerobic', 'mean'),
                               근력운동일_평균=('ML_strength_days', 'mean'), 좌식분_평균=('ML_sedentary_min', 'mean'),
                               외식_평균=('ML_eatingout_freq_ord', 'mean'))
one = one.reindex(['N', 'A', 'S', 'O']).round(2)
stress_rule = (inp['ML_stress'] == 1) == (inp['macro'] == 'S')

md = [
    '# 군집 vs 규칙 대조군', '',
    '"군집이 단순 규칙(필터링)과 다를 게 있나?"를 확인한다. 대상: 지연님 12개 유형(보완판, 원본과 같은 배정) '
    f'{len(inp):,}명.', '',
    '## 1. 얕은 결정나무가 12개 유형을 얼마나 재현하나', '',
    '설문 9개 응답만 보고 2022–23년으로 학습, 2024년에서 맞힌 비율. 깊이 d = 한 사람당 질문 d개 이하로 가르는 규칙.', '',
    rep.to_markdown(), '',
    '깊이 4 나무 (12개 유형):', '', '```', export_text(trees[('type', 4)], feature_names=[KO[c] for c in INPUTS]), '```', '',
    '## 2. 규칙을 유형으로 쓰면 (같은 지표)', '',
    cmp.to_markdown(), '',
    f'- 사람이 정한 4축: 운동 = 유산소 실천 또는 근력운동 주 2일 이상 / 스트레스 많음 / 좌식 ≥ {cut_sed:.0f}분 / 세 끼 합 ≥ {cut_meal:.0f} (중앙값)',
    '- 나무 규칙: 위 1의 나무가 나누는 칸(잎)을 그대로 유형으로 쓴 것 (깊이 2 = 최대 4칸, 4 = 최대 16칸, 6 = 최대 64칸)',
    '- 12개 유형과 일치: 각 칸을 가장 많이 겹치는 군집 유형에 대응시켰을 때 같은 사람 비율',
    f'- AUC 기준선: 성별·연령만 {auc_demo:.3f} / 15개 응답 그대로 {auc_raw:.3f}', '',
    '## 3. 대분류와 문항 하나', '',
    one.to_markdown(), '',
    f'- "스트레스 많음 = 예"이면 고스트레스형이라는 한 줄 규칙의 일치율: {stress_rule.mean():.1%}', '',
]
(OUT / '06_규칙대조군.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
print('\n'.join(md))
