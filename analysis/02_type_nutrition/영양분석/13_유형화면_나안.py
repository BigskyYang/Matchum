# %% [markdown]
# # 유형 화면 결과 (나)안 — 팀 결정 11/3
# 입력: 08번 확률표(08_유형성별연령_부족확률.csv)와 08번이 고른 모델 설정(08_2024검증.csv의 '선택')
#
# (나)안 규칙 (팀 의견 요청 문서 팀공유/08에 올린 값 그대로, 결과 보기 전에 고정)
# - 1줄 '대부분의 사람에게 부족해요': 공통주의 8개 (팀장님 nbti_12types.json common_nutrients) → 항상 표시
# - 2줄 '내 유형에서 살펴볼 것': 공통 외 영양소 중
#       부족 확률 ≥ 0.5  또는  (같은 성별·나이 대비 배수 ≥ 1.2  그리고  부족 확률 ≥ 0.3)
#   표시: "내 유형 10명 중 N명 / 같은 성별·나이 평균 10명 중 M명" + 판정 문구(유형특이 / 식사량영향)
#   2줄이 비면: "공통 영양소 외에 특히 더 부족한 영양소는 없어요"
# 검증 (시간 분할): 2022–23 자료만으로 학습한 모델로 2줄 항목을 고르고,
#   2024년 실제 자료에서 그 칸의 부족 비율이 같은 성별·나이(전체 유형)보다 높은지 확인 (관측/기대 비, 부트스트랩 CI)

# %%
import json
import warnings
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from common import *

warnings.filterwarnings('ignore')
SEED = 42
P_MAIN, RATIO_CUT, P_FLOOR = 0.5, 1.2, 0.3
REPO = ROOT.parents[1]
NB = json.load(open(REPO / 'analysis' / '01_clustering' / 'validation' / 'output' / 'nbti_12types.json', encoding='utf-8'))
TYPES = {t['id']: t for t in NB['types']}
IDS = list(TYPES)
COMMON = [c['nutrient'] for c in NB['common_nutrients']]
OTHER = [n for n in NUTRIENTS if n not in COMMON]
TAG_TEXT = {'유형특이': '이 유형에서 특히 많아요', '식사량영향': '식사량 점검이 먼저예요',
            '흔함': '같은 성별·나이대에서 흔해요'}   # 팀 결정(11/3, 1안): 판정 없는 2줄 항목은 유형이 아니라 성별·나이 때문에 흔한 것


def tag(k, n):
    t = TYPES[k]['nutrients']
    return ('유형특이' if n in [x['nutrient'] for x in t['specific']] else
            '식사량영향' if n in [x['nutrient'] for x in t['intake_related']] else '')


def pick_line2(tbl):
    """tbl: 칸 × 영양소 확률표(부족확률, 성별연령평균, 배수) → 2줄 항목."""
    o = tbl[tbl['영양소'].isin(OTHER)]
    return o[(o['부족확률'] >= P_MAIN) | ((o['배수'] >= RATIO_CUT) & (o['부족확률'] >= P_FLOOR))]


# %% 1. 검증: 2022–23 학습 모델로 고른 2줄 항목이 2024년에도 평균보다 높은가
d = add_status(load_persons(ROOT / 'KMedoids_12Types_N1O3.csv', 'Type'))
d['age_grp_s'] = d['age_grp'].astype(str)
d['male'] = (d['sex'] == '남자').astype(int)
w = d['w'] / d['w'].mean()
tr, te = d['year'] <= 2023, d['year'] == 2024
chosen = pd.read_csv(OUT / '08_2024검증.csv', encoding='utf-8-sig').set_index('영양소')['선택']


def make(cfg):
    oh = lambda cols: ColumnTransformer([('oh', OneHotEncoder(drop='first', handle_unknown='ignore'), cols)])
    if cfg.startswith('LR가법'):
        return ['sex', 'age_grp_s', 'cluster'], Pipeline([('p', oh(['sex', 'age_grp_s', 'cluster'])),
                                                           ('m', LogisticRegression(C=float(cfg.split('_C')[1]), max_iter=3000))])
    lr, leaf = cfg.split('_lr')[1].split('_leaf')
    return ['male', 'age', 'cluster'], Pipeline([
        ('p', ColumnTransformer([('ord', OrdinalEncoder(), ['cluster'])], remainder='passthrough')),
        ('m', HistGradientBoostingClassifier(learning_rate=float(lr), max_leaf_nodes=int(leaf), min_samples_leaf=100,
                                             max_iter=200, categorical_features=[0], early_stopping=False, random_state=SEED))])


grid = pd.MultiIndex.from_product([IDS, ['남자', '여자'], AGE_LABELS], names=['cluster', 'sex', 'age_grp_s']).to_frame(index=False)
grid['male'] = (grid['sex'] == '남자').astype(int)
grid['age'] = grid['age_grp_s'].map(d[tr].groupby('age_grp_s').apply(lambda g: np.average(g['age'], weights=g['w'])))
rows = []
for n in OTHER:
    y = d[f'below_{n}']
    cols, mdl = make(chosen[n])
    p = mdl.fit(d.loc[tr, cols], y[tr], m__sample_weight=w[tr].values).predict_proba(grid[cols])[:, 1]
    base = Pipeline([('p', ColumnTransformer([('oh', OneHotEncoder(drop='first'), ['sex', 'age_grp_s'])])),
                     ('m', LogisticRegression(max_iter=3000))]).fit(d.loc[tr, ['sex', 'age_grp_s']], y[tr],
                                                                   m__sample_weight=w[tr].values)
    pb = base.predict_proba(grid[['sex', 'age_grp_s']])[:, 1]
    rows.append(grid[['cluster', 'sex', 'age_grp_s']].assign(영양소=n, 부족확률=p, 성별연령평균=pb, 배수=p / pb))
flag_tr = pick_line2(pd.concat(rows))
print(f'2022–23 모델로 고른 2줄 항목: {len(flag_tr)}개 (칸×영양소)')

# 2024 관측: 그 칸의 부족 비율(관측 O) vs 같은 성별·나이 전체 비율 × 인원(기대 E)
t24 = d[te]
obs = []
for r in flag_tr.itertuples():
    y = t24[f'below_{r.영양소}']
    cell = (t24['cluster'] == r.cluster) & (t24['sex'] == r.sex) & (t24['age_grp_s'] == r.age_grp_s)
    sa = (t24['sex'] == r.sex) & (t24['age_grp_s'] == r.age_grp_s)
    if cell.sum() == 0:
        continue
    rate_sa = np.average(y[sa], weights=t24.loc[sa, 'w'])
    obs.append(dict(유형=r.cluster, 성별=r.sex, 연령대=r.age_grp_s, 영양소=r.영양소, n_2024=int(cell.sum()),
                    O=float((y[cell] * t24.loc[cell, 'w']).sum()), E=float(rate_sa * t24.loc[cell, 'w'].sum()),
                    예측배수=r.배수, 판정=tag(r.cluster, r.영양소)))
obs = pd.DataFrame(obs)
rng = np.random.default_rng(SEED)
boot = [obs.iloc[i]['O'].sum() / obs.iloc[i]['E'].sum() for i in (rng.integers(0, len(obs), len(obs)) for _ in range(2000))]
oe = obs['O'].sum() / obs['E'].sum()
lo, hi = np.percentile(boot, [2.5, 97.5])
obs['관측배수'] = obs['O'] / obs['E']
print(f'2024 관측/기대 비 (2줄 항목 전체, 가중): {oe:.3f} [95% CI {lo:.3f}, {hi:.3f}] | 관측배수>1인 항목 {(obs["관측배수"] > 1).mean():.1%}')
by = obs.groupby('영양소').apply(lambda g: pd.Series({'항목수': len(g), '관측/기대': g['O'].sum() / g['E'].sum(),
                                                      '예측배수평균': g['예측배수'].mean()}))
print(by.round(3).to_string())
by_tag = obs.assign(판정=obs['판정'].replace('', '흔함')).groupby('판정').apply(lambda g: pd.Series({'항목수': len(g), '관측/기대': g['O'].sum() / g['E'].sum()}))
print(by_tag.round(3).to_string())
obs.to_csv(OUT / '13_나안_2024검증.csv', index=False, encoding='utf-8-sig')

# %% 2. 웹 JSON: 08번 최종 확률표(전체 연도 학습)에 (나)안 적용
L = pd.read_csv(OUT / '08_유형성별연령_부족확률.csv', encoding='utf-8-sig')
L2 = pick_line2(L)
web = {'version': 'yuhwan-12types-screen-B-v1', 'source_types': NB['version'],
       '규칙': {'line1': '공통주의 8개 (전체 부족률 50% 이상) 항상 표시',
               'line2': f'공통 외: 부족 확률 ≥ {P_MAIN} 또는 (같은 성별·나이 대비 {RATIO_CUT}배 이상 그리고 부족 확률 ≥ {P_FLOOR})'},
       '설명': '같은 유형·성별·연령대 사람 중 2025 KDRI 기준 미만인 비율(조사 가중). 음식만(영양제 미포함), 하루 24시간 회상 기준. '
               '개인 진단이나 영양제 추천이 아니며, 질환이 있으면 전문가와 상담하세요.',
       'empty_line2_text': '공통 영양소 외에 특히 더 부족한 영양소는 없어요',
       '검증_2024': dict(항목수=len(obs), 관측기대비=round(oe, 3), CI=[round(lo, 3), round(hi, 3)]),
       'types': {}}
for k in IDS:
    web['types'][k] = {'name': TYPES[k]['name'], 'macro': TYPES[k]['macro'], 'cells': {}}
    for s in ['남자', '여자']:
        web['types'][k]['cells'][s] = {}
        for a in AGE_LABELS:
            c = L[(L['유형'] == k) & (L['성별'] == s) & (L['연령대'] == a)]
            c2 = L2[(L2['유형'] == k) & (L2['성별'] == s) & (L2['연령대'] == a)].sort_values('배수', ascending=False)
            web['types'][k]['cells'][s][a] = {
                'line1': [dict(nutrient=r.영양소, basis=r.기준, of10=int(round(r.부족확률 * 10))) for r in
                          c[c['영양소'].isin(COMMON)].sort_values('부족확률', ascending=False).itertuples()],
                'line2': [dict(nutrient=r.영양소, basis=r.기준, p=round(r.부족확률, 3), of10=int(round(r.부족확률 * 10)),
                               same_sex_age_of10=int(round(r.성별연령평균 * 10)), ratio=round(r.배수, 2),
                               tag=tag(k, r.영양소) or '흔함', tag_text=TAG_TEXT[tag(k, r.영양소) or '흔함'])
                          for r in c2.itertuples()]}
with open(OUT / '13_유형화면_나안.json', 'w', encoding='utf-8') as fp:
    json.dump(web, fp, ensure_ascii=False, indent=1)

# %% 출력: 유형별 2줄 요약
cnt = L2.groupby(['유형', '성별', '연령대']).size().reindex(L.groupby(['유형', '성별', '연령대']).size().index, fill_value=0)
print(f'\n2줄 항목: 칸당 평균 {cnt.mean():.1f}개, 빈 칸 {int((cnt == 0).sum())}/120')
summ = L2.groupby('유형').apply(lambda g: ', '.join(f"{n}({m})" for n, m in g['영양소'].value_counts().items()))
for k in IDS:
    print(f"{k} {TYPES[k]['name']:16s} 빈칸 {int((cnt.loc[k] == 0).sum()):2d}/10 | {summ.get(k, '-')}")
ex = web['types']['N2']['cells']['여자']['30-49']
print('\n[예시 N2 · 여자 · 30-49]')
print('1줄:', ', '.join(f"{x['nutrient']} {x['of10']}명" for x in ex['line1']))
for x in ex['line2']:
    print(f"2줄: {x['nutrient']} 내 유형 10명 중 {x['of10']}명 / 같은 성별·나이 평균 {x['same_sex_age_of10']}명 ({x['ratio']}배) {x['tag_text']}")
print('\n저장:', OUT)
