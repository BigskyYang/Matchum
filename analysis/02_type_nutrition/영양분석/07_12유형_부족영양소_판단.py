# %% [markdown]
# # [B-2] 12개 생활습관 유형별 부족 영양소 분석·판단 (ML)
# 입력: 지연님 analysis/01_clustering/kmedoids_model.json (2026-11-03 '12개 유형 새로 군집', 4대분류 × 3세부)
#   → 개인 결과 엑셀은 git에 없으므로 JSON의 assign()으로 같은 15,062명을 직접 재배정하고 인원수 일치를 확인
#
# 판정 기준 (결과 보기 전에 확정)
# A. 분석 — 유형 vs 나머지, 성별·연령 보정 로지스틱
#    - 유형특이: 보정 OR ≥ 1.2, BH-FDR q < 0.05 (12유형 × 15영양소 = 180개 검정), 평소 식사(N_DUSUAL==2)에서도 OR > 1
#    - 상대적양호: 보정 OR ≤ 1/1.2, q < 0.05
#    - 공통주의: 전체 가중 미달률 ≥ 50% (유형과 상관없이 모두에게 해당)
# B. 판단(ML) — "유형을 알면 부족 여부를 더 잘 맞히는가?"
#    - 재준님 모델과 같은 시간 분할: 2022–2023 학습 → 2024 검증 (섭취량 변수는 입력에 넣지 않음 = 누수 없음)
#    - M0 성별·연령(기준선) / M1 +유형 / M2 +생활습관 14개 원변수(선형) / M3 HGB(성별·나이·14변수, 비선형 상한)
#    - 유형으로 판단 가능: 2024 검증 ΔAUC(M1−M0)의 부트스트랩 95% CI 하한 > 0
#    - 정보보존율 = (M1−M0) / (max(M2, M3)−M0): 12개로 묶으면서 원변수 정보를 얼마나 남겼는지
# C. 웹용 — M1을 전체 자료로 다시 학습해 유형 × 성별 × 연령대별 부족확률표
#
# 서비스 규칙(11/3 회의): 유형 화면은 '부족 영양소'까지만, 영양제 추천 문구 없음

# %%
import sys
import json
import warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score, GridSearchCV
from sklearn.metrics import roc_auc_score
from common import *

warnings.filterwarnings('ignore')
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

REPO = ROOT.parents[1]   # 저장소 루트
JIYEON = REPO / 'analysis' / '01_clustering'
sys.path.insert(0, str(JIYEON))
from kmedoids_final import assign          # 웹에서 구현할 배정 계산과 같은 함수

MODEL = json.load(open(JIYEON / 'kmedoids_model.json', encoding='utf-8'))
# 이름: analysis/01_clustering/README.md (JSON 'name'은 자동생성 문구라 README 이름 사용, 인원수로 대응 확인)
TYPE_NAME = {
    'G0-0': '집밥형', 'G0-1': '불규칙형', 'G0-2': '외식형',
    'G1-0': '운동우선 불규칙식사형', 'G1-1': '유산소 규칙식사형', 'G1-2': '근력 규칙식사형',
    'G2-0': '스트레스 유산소형', 'G2-1': '스트레스 비활동형', 'G2-2': '스트레스 복합운동형',
    'G3-0': '아침거름형', 'G3-1': '규칙식사형', 'G3-2': '운동보완형',
}
MACRO_NAME = {'G0': '비활동형', 'G1': '운동형', 'G2': '고스트레스형', 'G3': '좌식·외식형'}
README_N = {'G0-0': 1802, 'G0-1': 1258, 'G0-2': 1429, 'G1-0': 1124, 'G1-1': 1542, 'G1-2': 1505,
            'G2-0': 1429, 'G2-1': 1561, 'G2-2': 454, 'G3-0': 1228, 'G3-1': 1137, 'G3-2': 593}
OR_CUT, Q_CUT, RATE_CUT, SEED = 1.2, 0.05, 0.50, 42

# %% 0. 재배정: 같은 15,062명(ML_ 14변수·year)을 JSON 모델로 배정 → 인원수가 README·JSON과 같아야 함
lab = pd.read_excel(FINAL_CLUSTER_FILE)[['ID', 'year'] + MODEL['features']]
code = pd.Series(assign(lab, MODEL)).str.replace(r'^(G\d)_.*_(\d)$', r'\1-\2', regex=True)
lab['Type'] = code.values
cnt = lab['Type'].value_counts()
assert cnt.to_dict() == README_N, cnt
TYPE_FILE = ROOT / 'KMedoids_12Types_재배정.csv'          # 개인 단위 → git 업로드 금지
lab.drop(columns='year').to_csv(TYPE_FILE, index=False, encoding='utf-8-sig')

d = add_status(load_persons(TYPE_FILE, 'Type'))
d['age_grp_s'] = d['age_grp'].astype(str)
types = sorted(d['cluster'].unique())
print('사람', len(d), '| 유형', len(types), '| 인원수 README와 일치')

# %% A. 분석: 유형 vs 나머지, 성별·연령 보정 오즈비
X_base = pd.get_dummies(d[['sex', 'age_grp_s']], drop_first=True).astype(float)
X_energy = X_base.assign(logE=np.log1p(d['영양_N_EN']))   # 에너지까지 보정 → 식사량형/구성형 구분
usual = d['식이상태_N_DUSUAL'] == 2


def adj_or(sub, y, inc, Xc=X_base):
    X = sm.add_constant(pd.concat([inc.rename('inc'), Xc], axis=1).loc[sub.index])
    fit = sm.Logit(y.loc[sub.index], X).fit(disp=0)
    return np.exp(fit.params['inc']), fit.pvalues['inc'], np.exp(fit.conf_int().loc['inc']).values


rows = []
for n in NUTRIENTS:
    y = d[f'below_{n}']
    overall = np.average(y, weights=d['w'])
    for c in types:
        inc = (d['cluster'] == c).astype(float)
        m = inc == 1
        o, p, ci = adj_or(d, y, inc)
        o_s, _, _ = adj_or(d[usual], y, inc)
        o_e, _, _ = adj_or(d, y, inc, X_energy)
        rows.append(dict(유형=c, 이름=TYPE_NAME[c], 영양소=n, 기준=KDRI[n][1], n=int(m.sum()),
                         미달률=np.average(y[m], weights=d.loc[m, 'w']), 전체미달률=overall,
                         보정OR=o, p=p, CI_low=ci[0], CI_high=ci[1], 민감도OR=o_s, 에너지보정OR=o_e))
res = pd.DataFrame(rows)
res['q'] = multipletests(res['p'], method='fdr_bh')[1]
res['차이pp'] = (res['미달률'] - res['전체미달률']) * 100
res['유형특이'] = (res['보정OR'] >= OR_CUT) & (res['q'] < Q_CUT) & (res['민감도OR'] > 1)
res['상대적양호'] = (res['보정OR'] <= 1 / OR_CUT) & (res['q'] < Q_CUT)
res['공통주의'] = res['전체미달률'] >= RATE_CUT
res['등급'] = np.select([res['유형특이'], res['공통주의'], res['상대적양호']],
                        ['유형특이', '공통주의', '상대적양호'], '해당없음')
res['원인'] = np.where(~res['유형특이'], '', np.where(res['에너지보정OR'] >= OR_CUT, '구성형', '식사량형'))

# 흡수 영향: 음주(월 음주 비율)가 전체보다 높은 유형 → 티아민·마그네슘 '흡수주의' (KDRI 2권 p240, 3권 p184)
drink = d.groupby('cluster').apply(lambda g: np.average(g['ML_drink_month'], weights=g['w']))
drink_all = np.average(d['ML_drink_month'], weights=d['w'])
alc_nut = LIFESTYLE_ABSORPTION.query('생활습관=="음주" and 적용')['영양소'].tolist()
res['흡수주의'] = [('음주' if (n in alc_nut and drink[c] > drink_all) else '') for c, n in zip(res['유형'], res['영양소'])]

# %% B. 판단(ML): 2022–23 학습 → 2024 검증
LS_COLS = MODEL['features']                       # 생활습관 14개 원변수 (군집 입력 그대로)
d['male'] = (d['sex'] == '남자').astype(int)
tr, te = d['year'] <= 2023, d['year'] == 2024
cv = StratifiedKFold(5, shuffle=True, random_state=SEED)


def lr_pipe(cat, num=()):
    parts = [('cat', OneHotEncoder(drop='first', handle_unknown='ignore'), list(cat))]
    if num:
        parts.append(('num', StandardScaler(), list(num)))
    return Pipeline([('prep', ColumnTransformer(parts)), ('lr', LogisticRegression(max_iter=3000))])


SPECS = {
    'M0_성별연령': (lambda: lr_pipe(['sex', 'age_grp_s']), ['sex', 'age_grp_s']),
    'M1_+유형': (lambda: lr_pipe(['sex', 'age_grp_s', 'cluster']), ['sex', 'age_grp_s', 'cluster']),
    'M2_+원변수14': (lambda: lr_pipe(['sex', 'age_grp_s'], LS_COLS), ['sex', 'age_grp_s'] + LS_COLS),
}
HGB_GRID = {'learning_rate': [0.05, 0.1], 'max_leaf_nodes': [7, 15], 'min_samples_leaf': [50, 200]}


def boot_delta(y, p_a, p_b, B=1000, seed=SEED):
    """2024 검증셋 쌍체 부트스트랩: AUC(b) − AUC(a)의 95% CI."""
    rng = np.random.default_rng(seed)
    y, p_a, p_b = map(np.asarray, (y, p_a, p_b))
    out = []
    for _ in range(B):
        i = rng.integers(0, len(y), len(y))
        if y[i].min() == y[i].max():
            continue
        out.append(roc_auc_score(y[i], p_b[i]) - roc_auc_score(y[i], p_a[i]))
    return np.percentile(out, [2.5, 97.5])


ml_rows, hgb_params = [], {}
for n in NUTRIENTS:
    y = d[f'below_{n}']
    r, pred = dict(영양소=n, 기준=KDRI[n][1], 미달률_학습=y[tr].mean(), 미달률_2024=y[te].mean()), {}
    for name, (make, cols) in SPECS.items():
        mdl = make()
        r[f'{name}_CV'] = cross_val_score(mdl, d.loc[tr, cols], y[tr], cv=cv, scoring='roc_auc').mean()
        mdl.fit(d.loc[tr, cols], y[tr])
        r[f'{name}_Train'] = roc_auc_score(y[tr], mdl.predict_proba(d.loc[tr, cols])[:, 1])
        pred[name] = mdl.predict_proba(d.loc[te, cols])[:, 1]
        r[f'{name}_Test'] = roc_auc_score(y[te], pred[name])
    hcols = ['male', 'age'] + LS_COLS
    gs = GridSearchCV(HistGradientBoostingClassifier(max_iter=300, early_stopping=True, random_state=SEED),
                      HGB_GRID, cv=cv, scoring='roc_auc').fit(d.loc[tr, hcols], y[tr])
    hgb_params[n] = gs.best_params_
    r['M3_HGB_CV'] = gs.best_score_
    r['M3_HGB_Train'] = roc_auc_score(y[tr], gs.predict_proba(d.loc[tr, hcols])[:, 1])
    pred['M3_HGB'] = gs.predict_proba(d.loc[te, hcols])[:, 1]
    r['M3_HGB_Test'] = roc_auc_score(y[te], pred['M3_HGB'])

    r['ΔAUC_유형'] = r['M1_+유형_Test'] - r['M0_성별연령_Test']
    r['ΔAUC_유형_CI_low'], r['ΔAUC_유형_CI_high'] = boot_delta(y[te], pred['M0_성별연령'], pred['M1_+유형'])
    upper = max(r['M2_+원변수14_Test'], r['M3_HGB_Test']) - r['M0_성별연령_Test']
    r['정보보존율'] = r['ΔAUC_유형'] / upper if upper > 0.005 else np.nan
    r['M1_과적합(Train−Test)'] = r['M1_+유형_Train'] - r['M1_+유형_Test']
    ml_rows.append(r)
    print(f"{n:6s} AUC M0 {r['M0_성별연령_Test']:.3f} → M1 {r['M1_+유형_Test']:.3f} "
          f"(Δ {r['ΔAUC_유형']:+.3f} [{r['ΔAUC_유형_CI_low']:+.3f}, {r['ΔAUC_유형_CI_high']:+.3f}]) "
          f"| M2 {r['M2_+원변수14_Test']:.3f} M3 {r['M3_HGB_Test']:.3f}")
ml = pd.DataFrame(ml_rows)
ml['유형판단'] = np.where(ml['ΔAUC_유형_CI_low'] > 0, '유형으로 판단 가능', '성별·연령 수준')
ml.to_csv(OUT / '12유형_ML판단.csv', index=False, encoding='utf-8-sig')

# %% 판정 합치기 → 유형별 우선순위 (유형특이: OR 큰 순 → 공통주의: 미달률 큰 순)
res = res.merge(ml[['영양소', '유형판단', 'ΔAUC_유형']], on='영양소')
res['정렬'] = res['등급'].map({'유형특이': 0, '공통주의': 1}).fillna(2)
res = res.sort_values(['유형', '정렬', '흡수주의', '보정OR', '미달률'], ascending=[True, True, False, False, False])
res['순위'] = res.groupby('유형').cumcount() + 1
res.to_csv(OUT / '12유형_영양니즈_long.csv', index=False, encoding='utf-8-sig')

fmt = lambda g, grade: ', '.join(f"{r.영양소}({r.보정OR:.2f}{'·' + r.원인 if r.원인 else ''})"
                                 for r in g[g['등급'] == grade].itertuples())
prof = d.groupby('cluster').apply(lambda g: pd.Series({
    'n': len(g), '평균나이': g['age'].mean(), '남성비율': (g['sex'] == '남자').mean(),
    '에너지섭취': np.average(g['영양_N_EN'], weights=g['w']),
    '부족개수_EAR': np.average(g['부족개수_EAR'], weights=g['w'])}))
prof.insert(0, '이름', [TYPE_NAME[c] for c in prof.index])
prof['유형특이 부족'] = res.groupby('유형').apply(lambda g: fmt(g, '유형특이'))
prof['상대적양호'] = res.groupby('유형').apply(lambda g: fmt(g, '상대적양호'))
prof.to_csv(OUT / '12유형_요약.csv', encoding='utf-8-sig')

# %% C. 웹용 부족확률표: M1을 전체 자료로 학습 → 유형 × 성별 × 연령대
grid = pd.MultiIndex.from_product([types, ['남자', '여자'], AGE_LABELS],
                                  names=['cluster', 'sex', 'age_grp_s']).to_frame(index=False)
for n in NUTRIENTS:
    cols = SPECS['M1_+유형'][1]
    grid[n] = SPECS['M1_+유형'][0]().fit(d[cols], d[f'below_{n}']).predict_proba(grid[cols])[:, 1].round(3)
grid.rename(columns={'cluster': '유형', 'age_grp_s': '연령대', 'sex': '성별'}).to_csv(
    OUT / '12유형_부족확률표.csv', index=False, encoding='utf-8-sig')

web = {'설명': '유형별 부족 영양소 (2025 KDRI 기준 미달 비율). EAR 미만=부족 위험, AI 미만=참고. '
               '영양제 추천 아님. 질환이 있으면 전문가와 상담하세요.',
       '공통주의': res.query('등급=="공통주의"')['영양소'].unique().tolist(),
       'types': {}}
for c in types:
    g = res[res['유형'] == c]
    pr = grid[grid['cluster'] == c]
    web['types'][c] = dict(
        이름=TYPE_NAME[c], 대분류=MACRO_NAME[c[:2]], n=int(prof.loc[c, 'n']),
        부족영양소=[dict(영양소=r.영양소, 등급=r.등급, 기준=r.기준, 미달률=round(r.미달률, 3),
                    전체미달률=round(r.전체미달률, 3), 보정OR=round(r.보정OR, 2), 흡수주의=r.흡수주의)
                   for r in g[g['등급'].isin(['유형특이', '공통주의'])].itertuples()],
        상대적양호=g.query('등급=="상대적양호"')['영양소'].tolist(),
        부족확률={s: {a: pr[(pr['sex'] == s) & (pr['age_grp_s'] == a)][NUTRIENTS].iloc[0].to_dict()
                   for a in AGE_LABELS} for s in ['남자', '여자']})
with open(OUT / '12유형_부족영양소.json', 'w', encoding='utf-8') as fp:
    json.dump(web, fp, ensure_ascii=False, indent=1)

# %% 출력
pd.set_option('display.width', 250)
print('\n[A. 전체 가중 미달률]')
print(res.drop_duplicates('영양소').set_index('영양소')[['기준', '전체미달률']]
      .assign(전체미달률=lambda x: (x['전체미달률'] * 100).round(1)).to_string())
print('\n[A. 유형 요약]')
print(prof.round(2).to_string())
print('\n[B. ML 판단: 2024 검증 AUC]')
show = ['영양소', 'M0_성별연령_Test', 'M1_+유형_CV', 'M1_+유형_Train', 'M1_+유형_Test', 'M2_+원변수14_Test',
        'M3_HGB_Test', 'ΔAUC_유형', 'ΔAUC_유형_CI_low', '정보보존율', '유형판단']
print(ml[show].round(3).to_string(index=False))
print('HGB 최적 파라미터:', hgb_params)

# %% 그림 1: 보정 OR 히트맵 (★ 유형특이, ○ 상대적양호)
lbl = [f'{c} {TYPE_NAME[c]}' for c in types]
piv = res.pivot(index='유형', columns='영양소', values='보정OR').loc[types, NUTRIENTS]
mk = res.assign(m=np.select([res['유형특이'], res['상대적양호']], ['★', '○'], '')).pivot(
    index='유형', columns='영양소', values='m').loc[types, NUTRIENTS]
fig, ax = plt.subplots(figsize=(15, 8))
sns.heatmap(np.log2(piv), center=0, cmap='RdBu_r', annot=piv.round(2).astype(str) + mk, fmt='',
            yticklabels=lbl, cbar_kws={'label': 'log2(보정 OR)'}, ax=ax)
ax.set_title('12개 생활습관 유형별 부족 위험 보정 오즈비 (성별·연령 보정, ★ 유형특이 / ○ 상대적양호, BH-FDR q<0.05)')
plt.tight_layout(); plt.savefig(OUT / 'fig_12유형x영양소_보정OR.png', dpi=150)

# 그림 2: 유형 정보의 예측 기여 (2024 검증 ΔAUC, 95% CI)
m2 = ml.sort_values('ΔAUC_유형')
fig, ax = plt.subplots(figsize=(8, 6))
ax.barh(m2['영양소'], m2['ΔAUC_유형'],
        xerr=[m2['ΔAUC_유형'] - m2['ΔAUC_유형_CI_low'], m2['ΔAUC_유형_CI_high'] - m2['ΔAUC_유형']],
        color=np.where(m2['ΔAUC_유형_CI_low'] > 0, '#2a6fbb', '#bbbbbb'), capsize=3)
ax.axvline(0, color='k', lw=0.8)
ax.set_xlabel('ΔAUC (성별·연령 + 유형) − (성별·연령), 2024 검증')
ax.set_title('유형을 알면 부족 여부를 더 잘 맞히는가 (파랑 = 95% CI > 0)')
plt.tight_layout(); plt.savefig(OUT / 'fig_12유형_ΔAUC.png', dpi=150)
print('\n저장:', OUT)
