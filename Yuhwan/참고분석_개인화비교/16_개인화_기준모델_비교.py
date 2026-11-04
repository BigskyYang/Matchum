# %% [markdown]
# # [참고용 분석] 개인 설문이 얼마나 더 알려 주나: 기준 모델 / 유형 모델 / 재준님 개인 모델 비교 (2024 검증)
# ⚠️ 참고용: 웹·모델이 이 결과를 읽지 않고, 재준님 모델도 바꾸지 않음. 발표·보고서 근거용. 3번(유형 대비 등급)은 검토했지만 채택하지 않음
# 같은 사람(15,062명), 같은 정답(2025 KDRI 기준 미만, add_status), 같은 분할(2022–23 학습 → 2024 검증), 같은 가중치(wt_tot/3)
#   M0 기준 모델: 성별 + 연령대 (로지스틱)
#   M1 유형 모델: 유형 + 성별 + 연령대 (08번이 고른 설정 그대로)
#   M2 개인 모델: 재준님 v1.4 생활습관 모델 그대로 (웹 nutritionModels.json의 트리를 재현, 입력 18개, 2022–23으로 학습된 모델)
# 재준님 정답(TargetMatrix)은 저장소에 없어 우리 정답으로 평가 → 재준님 보고 AUC와 비교해 정답 정의 차이를 확인
# 추가: (1) 같은 유형·성별·연령대 안에서 개인 확률이 얼마나 퍼지는지
#       (2) 등급 방식별 분포: 지금(전체 세 등분) vs 내 유형 평균 대비(1.2배 이상 높음 / 0.8배 이하 낮음, 2단 표시의 1.2배와 같은 기준)

# %%
import json
import warnings
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from common import *

warnings.filterwarnings('ignore')
SEED = 42
REPO = ROOT.parent if (ROOT.parent / 'Jiyeon').exists() else ROOT.parent / 'Matchum'
NM = json.load(open(REPO / 'bigskyyang' / 'web' / 'src' / 'data' / 'nutritionModels.json', encoding='utf-8'))['lifestyle']
KEY = {'protein': '단백질', 'calcium': '칼슘', 'magnesium': '마그네슘', 'iron': '철', 'zinc': '아연', 'phosphorus': '인',
       'vitamin_a': '비타민A', 'vitamin_b1': '티아민', 'vitamin_b2': '리보플라빈', 'folate': '엽산', 'vitamin_c': '비타민C',
       'fiber': '식이섬유', 'potassium': '칼륨'}          # sodium_excess는 우리 정답이 없어 제외
REPORTED = {'protein': .672, 'calcium': .601, 'magnesium': .663, 'iron': .728, 'zinc': .664, 'phosphorus': .726, 'vitamin_a': .607,
            'vitamin_b1': .629, 'vitamin_b2': .615, 'folate': .691, 'vitamin_c': .654, 'fiber': .676, 'potassium': .682}  # service_2024_holdout_metrics.md

d = add_status(load_persons(ROOT / 'KMedoids_12Types_N1O3.csv', 'Type'))
d['age_grp_s'] = d['age_grp'].astype(str)
d['male'] = (d['sex'] == '남자').astype(int)
FEAT = NM['features']
print('입력 18개:', FEAT)
for c in ['식습관_LS_FRUIT', '식습관_LS_VEG2']:
    d[c] = d[c].where(~d[c].isin([99]))
ok = d[FEAT].notna().all(axis=1)
print(f'입력 결측(모름·무응답 99) 제외 {(~ok).sum()}명')
assert ((d['ML_drink_month'] == (d['ML_drink_freq_ord'] >= 2).astype(int)) | (d['ML_drink_freq_ord'].isna())).mean() > 0.99
d = d[ok].reset_index(drop=True)
X = d[FEAT].to_numpy(float)
w = (d['w'] / d['w'].mean()).to_numpy()
tr, te = (d['year'] <= 2023).to_numpy(), (d['year'] == 2024).to_numpy()
print(f'학습 {tr.sum()} / 검증 {te.sum()}')


def hgb_prob(m, X):
    """웹 nutritionRisk.js와 같은 계산: 트리마다 값 <= 경계면 왼쪽, 잎 값을 모두 더해 로지스틱."""
    raw = np.full(len(X), m['baseline'])
    rows = np.arange(len(X))
    for t in m['trees']:
        f, th, l, r = (np.array(t[k]) for k in 'ftlr')
        node = np.zeros(len(X), dtype=int)
        while True:
            inner = f[node] >= 0
            if not inner.any():
                break
            n = node[inner]
            go_left = X[rows[inner], f[n]] <= th[n]
            node[inner] = np.where(go_left, l[n], r[n])
        raw += th[node]
    return 1 / (1 + np.exp(-raw))


def personal_prob(key):
    m = NM['models'][key]
    if m['type'] == 'hgb':
        return hgb_prob(m, X)
    z = (X - np.array(m['mean'])) / np.array(m['scale'])
    return 1 / (1 + np.exp(-(z @ np.array(m['coef']) + m['intercept'])))


chosen = pd.read_csv(OUT / '08_2024검증.csv', encoding='utf-8-sig').set_index('영양소')['선택']


def type_model(cfg):
    if cfg.startswith('LR가법'):
        cols = ['sex', 'age_grp_s', 'cluster']
        return cols, Pipeline([('p', ColumnTransformer([('oh', OneHotEncoder(drop='first', handle_unknown='ignore'), cols)])),
                               ('m', LogisticRegression(C=float(cfg.split('_C')[1]), max_iter=3000))])
    lr, leaf = cfg.split('_lr')[1].split('_leaf')
    return ['male', 'age', 'cluster'], Pipeline([
        ('p', ColumnTransformer([('ord', OrdinalEncoder(), ['cluster'])], remainder='passthrough')),
        ('m', HistGradientBoostingClassifier(learning_rate=float(lr), max_leaf_nodes=int(leaf), min_samples_leaf=100, max_iter=200,
                                             categorical_features=[0], early_stopping=False, random_state=SEED))])


# %% 1. AUC 비교 (2024, 가중)
rows, P = [], {}
for key, n in KEY.items():
    y = d[f'below_{n}'].to_numpy()
    m0 = Pipeline([('p', ColumnTransformer([('oh', OneHotEncoder(drop='first'), ['sex', 'age_grp_s'])])),
                   ('m', LogisticRegression(max_iter=3000))]).fit(d.loc[tr, ['sex', 'age_grp_s']], y[tr], m__sample_weight=w[tr])
    p0 = m0.predict_proba(d[['sex', 'age_grp_s']])[:, 1]
    cols, m1 = type_model(chosen[n])
    p1 = m1.fit(d.loc[tr, cols], y[tr], m__sample_weight=w[tr]).predict_proba(d[cols])[:, 1]
    p2 = personal_prob(key)
    P[key] = (p0, p1, p2)
    auc = lambda p: roc_auc_score(y[te], p[te], sample_weight=w[te])
    rows.append(dict(영양소=n, 기준모델=auc(p0), 유형모델=auc(p1), 개인모델=auc(p2),
                     개인모델_비가중=roc_auc_score(y[te], p2[te]), 재준님보고=REPORTED[key],
                     부족률_2024=np.average(y[te], weights=w[te]), 개인모델_평균확률=np.average(p2[te], weights=w[te])))
A = pd.DataFrame(rows)
A['유형−기준'] = A['유형모델'] - A['기준모델']
A['개인−기준'] = A['개인모델'] - A['기준모델']
A['개인−유형'] = A['개인모델'] - A['유형모델']
A.to_csv(OUT / '16_개인화_기준모델_비교.csv', index=False, encoding='utf-8-sig')
print(A.round(3).to_string(index=False))
print('\n평균:', A[['기준모델', '유형모델', '개인모델', '유형−기준', '개인−기준', '개인−유형']].mean().round(3).to_dict())
print('재준님 보고 AUC와 우리 정답 기준 비가중 AUC 차이(평균 절대):', round((A['개인모델_비가중'] - A['재준님보고']).abs().mean(), 3))

# 부트스트랩: 개인−유형 차이의 95% 구간 (2024 사람 단위 재표본, 200회)
rng = np.random.default_rng(SEED)
idx24 = np.where(te)[0]
ci = []
for key, n in KEY.items():
    y = d[f'below_{n}'].to_numpy()
    _, p1, p2 = P[key]
    b = []
    for _ in range(200):
        s = rng.choice(idx24, len(idx24))
        b.append(roc_auc_score(y[s], p2[s], sample_weight=w[s]) - roc_auc_score(y[s], p1[s], sample_weight=w[s]))
    ci.append(dict(영양소=n, 개인_유형_차이=np.mean(b), 하한=np.percentile(b, 2.5), 상한=np.percentile(b, 97.5)))
CI = pd.DataFrame(ci)
CI['유의'] = CI['하한'] > 0
print('\n개인 − 유형 AUC 차이 95% 구간 (부트스트랩 200회)')
print(CI.round(3).to_string(index=False))

# %% 2. 같은 유형·성별·연령대 안에서 개인 확률이 퍼지는 정도 + 3. 등급 방식별 분포 (2024)
d24 = d[te].copy()
spread, band = [], []
for key, n in KEY.items():
    _, p1, p2 = P[key]
    d24['p_type'], d24['p_pers'] = p1[te], p2[te]
    g = d24.groupby(['cluster', 'sex', 'age_grp_s'], observed=True)['p_pers']
    within_sd = np.sqrt(np.average((d24['p_pers'] - g.transform('mean')) ** 2, weights=d24['w']))
    ratio = d24['p_pers'] / d24['p_type']
    cut = NM['cuts'][key]
    now = np.select([d24['p_pers'] >= cut['mid_high'], d24['p_pers'] < cut['low_mid']], ['높은 편', '낮은 편'], '보통')
    vs_type = np.select([ratio >= 1.2, ratio <= 0.8], ['높음', '낮음'], '비슷')
    wt = d24['w']
    spread.append(dict(영양소=n, 유형조합안_표준편차=within_sd, 전체_표준편차=np.sqrt(np.average((d24['p_pers'] - np.average(d24['p_pers'], weights=wt)) ** 2, weights=wt)),
                       유형평균에서_20퍼센트이상_벗어난_비율=np.average((ratio >= 1.2) | (ratio <= 0.8), weights=wt)))
    band.append(dict(영양소=n, 부족률=np.average(d24[f'below_{n}'], weights=wt),
                     **{f'지금_{b}': np.average(now == b, weights=wt) for b in ['높은 편', '보통', '낮은 편']},
                     **{f'유형대비_{b}': np.average(vs_type == b, weights=wt) for b in ['높음', '비슷', '낮음']},
                     지금_높은편_실제부족률=np.average(d24.loc[now == '높은 편', f'below_{n}'], weights=wt[now == '높은 편']),
                     유형대비_높음_실제부족률=(np.average(d24.loc[vs_type == '높음', f'below_{n}'], weights=wt[vs_type == '높음'])
                                     if (vs_type == '높음').any() else np.nan)))
SP, BD = pd.DataFrame(spread), pd.DataFrame(band)
SP.to_csv(OUT / '16_개인확률_퍼짐.csv', index=False, encoding='utf-8-sig')
BD.to_csv(OUT / '16_등급방식_분포.csv', index=False, encoding='utf-8-sig')
print('\n개인 확률의 퍼짐 (2024, 가중)')
print(SP.round(3).to_string(index=False))
print('\n등급 방식별 분포 (2024, 가중)')
print(BD.round(3).to_string(index=False))
