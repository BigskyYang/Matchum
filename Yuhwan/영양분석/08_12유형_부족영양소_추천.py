# %% [markdown]
# # [B-3] 12개 유형(N1~O3) 기반 부족 영양소 추천 (ML)
# 입력: 팀장님 채택안 bigskyyang/analysis/output/nbti_12types.json (11/3, 지연님 12유형 보완판, 새 ID N1~O3)
#   - 유형별 판정(유형 특이 / 식사량 영향 / 공통 주의)은 이 JSON 값을 그대로 쓴다 (사용자 결정: 팀장님 기준으로 통일)
#   - 이 스크립트가 더하는 것: 유형 + 성별 + 연령대 → 영양소별 부족 확률 → "10명 중 N명" 순위와 추천 목록
#
# 설계 (결과 보기 전에 확정)
# - 목표: 영양소 15개 각각 below_<영양소> (2025 KDRI, 본인 성별·연령 EAR/AI 미만)
# - 입력: 유형·성별·연령대만 (웹 설문으로 이미 아는 값). 섭취량은 넣지 않음 = 누수 없음
# - 분할: 2022–23 학습(5-fold CV로 모델·하이퍼파라미터 선택) → 2024 검증 (재준님 모델과 같은 시간 분할)
# - 후보: LR(가법, C 0.01·0.1·1·10) → LR(+유형×성별, C 0.1·1) → HGB(학습률·잎 수)  ← 단순한 순
#   선택: CV 가중 로그손실 최소 모델의 1-SE 안에서 가장 단순한 것 (확률을 그대로 보여주므로 로그손실 기준)
# - 가중치: 조사 가중치 wt_tot/3로 학습·평가 (화면의 "10명 중 N명"이 국민 대표값이 되도록)
# - 추천 규칙: 예측 부족 확률 ≥ 0.5 ("10명 중 5명 이상") → 공통 주의(전체 50%)와 같은 기준을 개인 칸으로 확장
#   비교 기준선: ① 모두에게 공통 8개 고정 ② 성별·연령만 쓴 모델
# - 서비스 규칙(11/3 회의): 유형 화면은 부족 영양소까지, 영양제 제품·처방 문구 없음

# %%
import sys
import json
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score, log_loss, brier_score_loss
from common import *

warnings.filterwarnings('ignore')
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

MATCHUM = ROOT.parent if (ROOT.parent / 'Jiyeon').exists() else ROOT.parent / 'Matchum'   # Yuhwan/ 안 또는 로컬 작업 폴더
sys.path.insert(0, str(MATCHUM / 'Jiyeon'))
from kmedoids_final import assign                     # 학습 자료 배정 (수면 연도 보정 포함)

JM = json.load(open(MATCHUM / 'Jiyeon' / 'kmedoids_model.json', encoding='utf-8'))
NB = json.load(open(MATCHUM / 'bigskyyang' / 'analysis' / 'output' / 'nbti_12types.json', encoding='utf-8'))
TYPES = {t['id']: t for t in NB['types']}
IDS = list(TYPES)
SEED, CUT = 42, 0.5
# 민감도 분석: python 08_...py [전체|에너지|평소|둘다]  (기본 전체 = 본 분석)
#   에너지: 하루 에너지 500~5,000kcal만 (극단적 과소·과다 보고 제외)
#   평소: 조사일 식사량이 평소와 비슷한 사람만 (N_DUSUAL == 2)
SUBSET = sys.argv[1] if len(sys.argv) > 1 else '전체'
SUF = '' if SUBSET == '전체' else f'_민감도_{SUBSET}'

# 지연님 코드 → 팀장님 ID (인원수·이름으로 대응. 세부 번호는 '세분화 변수 값이 작은 순'으로 다시 매김)
G2ID = {'G0-0': 'N1', 'G0-1': 'N2', 'G0-2': 'N3', 'G1-1': 'A1', 'G1-0': 'A2', 'G1-2': 'A3',
        'G2-1': 'S1', 'G2-0': 'S2', 'G2-2': 'S3', 'G3-0': 'O1', 'G3-1': 'O2', 'G3-2': 'O3'}


def classify12(df):
    """nbti_12types.json만으로 배정 (웹 classify12와 같은 계산). 수면은 2024 기준 척도로 간주."""
    X = np.column_stack([df[i['name']].clip(*i['clip']).values for i in NB['inputs']])
    names = [i['name'] for i in NB['inputs']]
    S = np.column_stack([s['const'] + sum(c * X[:, names.index(k)] for k, c in s['coef'].items())
                         for s in NB['scores']])
    pc = (S - np.array(NB['pca']['mean'])) @ np.array(NB['pca']['components']).T
    mc = np.array([m['center'] for m in NB['macro']])
    macro = np.array([m['code'] for m in NB['macro']])[np.argmin(((pc[:, None] - mc) ** 2).sum(2), 1)]
    snames = [s['name'] for s in NB['scores']]
    out = np.empty(len(df), dtype=object)
    for code, sub in NB['sub'].items():
        sel = macro == code
        V = (S[np.ix_(sel, [snames.index(f) for f in sub['features']])] - sub['mean']) / np.array(sub['std'])
        keys = list(sub['centers'])
        C = np.array([sub['centers'][k] for k in keys])
        out[sel] = np.array(keys)[np.argmin(((V[:, None] - C) ** 2).sum(2), 1)]
    return out


# %% 0. 배정과 확인
lab = pd.read_excel(FINAL_CLUSTER_FILE)[['ID', 'year'] + JM['features']]
g = pd.Series(assign(lab, JM)).str.replace(r'^(G\d)_.*_(\d)$', r'\1-\2', regex=True)
lab['Type'] = g.map(G2ID).values
n_chk = lab['Type'].value_counts()
gap = {k: int(n_chk[k] - TYPES[k]['n']) for k in IDS}
assert max(abs(v) for v in gap.values()) <= 1, gap          # 팀장님은 15,060명(2명 제외) 기준
y24 = lab['year'] == 2024                                    # 2024는 수면 보정이 없어 웹 계산과 바로 비교 가능
agree24 = (classify12(lab[y24]) == lab.loc[y24, 'Type']).mean()
print(f'인원수 차이(팀장님 JSON 대비) {gap} | 2024년 웹 배정식 일치율 {agree24:.4%}')
TYPE_FILE = ROOT / 'KMedoids_12Types_N1O3.csv'             # 개인 단위 → git 업로드 금지
lab.drop(columns='year').to_csv(TYPE_FILE, index=False, encoding='utf-8-sig')

d = add_status(load_persons(TYPE_FILE, 'Type'))
keep = pd.Series(True, index=d.index)
if SUBSET in ('에너지', '둘다'):
    keep &= d['영양_N_EN'].between(500, 5000)
if SUBSET in ('평소', '둘다'):
    keep &= d['식이상태_N_DUSUAL'] == 2
d = d[keep].reset_index(drop=True)
print('대상자 조건:', SUBSET)
d['age_grp_s'] = d['age_grp'].astype(str)
d['type_sex'] = d['cluster'] + '_' + d['sex']
d['male'] = (d['sex'] == '남자').astype(int)
print('사람', len(d))

# 팀장님 판정 (그대로 사용)
COMMON = [c['nutrient'] for c in NB['common_nutrients']]
TAG = {}
for k, t in TYPES.items():
    for n in NUTRIENTS:
        TAG[(k, n)] = ('유형특이' if n in [x['nutrient'] for x in t['nutrients']['specific']] else
                       '식사량영향' if n in [x['nutrient'] for x in t['nutrients']['intake_related']] else
                       '공통주의' if n in COMMON else '')

# %% 1. 후보 모델 (단순한 순서)
OH = lambda cols: ColumnTransformer([('oh', OneHotEncoder(drop='first', handle_unknown='ignore'), cols)])
CANDS = []
for C in [0.01, 0.1, 1, 10]:
    CANDS.append((f'LR가법_C{C}', ['sex', 'age_grp_s', 'cluster'],
                  lambda C=C: Pipeline([('p', OH(['sex', 'age_grp_s', 'cluster'])),
                                        ('m', LogisticRegression(C=C, max_iter=3000))])))
for C in [0.1, 1]:
    CANDS.append((f'LR교호_C{C}', ['sex', 'age_grp_s', 'cluster', 'type_sex'],
                  lambda C=C: Pipeline([('p', OH(['sex', 'age_grp_s', 'cluster', 'type_sex'])),
                                        ('m', LogisticRegression(C=C, max_iter=3000))])))
for lr in [0.05, 0.1]:
    for leaf in [7, 15]:
        CANDS.append((f'HGB_lr{lr}_leaf{leaf}', ['male', 'age', 'cluster'],
                      lambda lr=lr, leaf=leaf: Pipeline([
                          ('p', ColumnTransformer([('ord', OrdinalEncoder(), ['cluster'])], remainder='passthrough')),
                          ('m', HistGradientBoostingClassifier(learning_rate=lr, max_leaf_nodes=leaf, min_samples_leaf=100,
                                                               max_iter=200, categorical_features=[0],
                                                               early_stopping=False, random_state=SEED))])))
BASE = ('M0_성별연령', ['sex', 'age_grp_s'],
        lambda: Pipeline([('p', OH(['sex', 'age_grp_s'])), ('m', LogisticRegression(max_iter=3000))]))

tr, te = d['year'] <= 2023, d['year'] == 2024
w = d['w'] / d['w'].mean()
cv = StratifiedKFold(5, shuffle=True, random_state=SEED)


def fit(make, cols, idx, y):
    return make().fit(d.loc[idx, cols], y[idx], m__sample_weight=w[idx].values)


def cv_score(make, cols, y):
    idx = np.flatnonzero(tr)
    ll, auc = [], []
    for a, b in cv.split(idx, y.iloc[idx]):
        ia, ib = d.index[idx[a]], d.index[idx[b]]
        p = fit(make, cols, ia, y).predict_proba(d.loc[ib, cols])[:, 1]
        ll.append(log_loss(y[ib], p, sample_weight=w[ib]))
        auc.append(roc_auc_score(y[ib], p, sample_weight=w[ib]))
    return np.mean(ll), np.std(ll, ddof=1) / np.sqrt(len(ll)), np.mean(auc)


def boot_delta(y, pa, pb, sw, B=1000):
    rng = np.random.default_rng(SEED)
    y, pa, pb, sw = map(np.asarray, (y, pa, pb, sw))
    out = []
    for _ in range(B):
        i = rng.integers(0, len(y), len(y))
        out.append(roc_auc_score(y[i], pb[i], sample_weight=sw[i]) - roc_auc_score(y[i], pa[i], sample_weight=sw[i]))
    return np.percentile(out, [2.5, 97.5])


# %% 2. 영양소별 튜닝(2022–23 CV) → 2024 검증
tune_rows, test_rows, chosen = [], [], {}
P_te = {'공통8고정': {}, 'M0_성별연령': {}, '선택모델': {}}
for n in NUTRIENTS:
    y = d[f'below_{n}']
    scores = [(name, cols, make, *cv_score(make, cols, y)) for name, cols, make in CANDS]
    best = min(scores, key=lambda s: s[3])
    pick = next(s for s in scores if s[3] <= best[3] + best[4])          # 1-SE 규칙: 단순한 순서로 첫 번째
    chosen[n] = pick
    for s in scores:
        tune_rows.append(dict(영양소=n, 후보=s[0], CV로그손실=s[3], SE=s[4], CV_AUC=s[5],
                              최소=s[0] == best[0], 선택=s[0] == pick[0]))

    m_pick = fit(pick[2], pick[1], d.index[tr], y)
    m0 = fit(BASE[2], BASE[1], d.index[tr], y)
    p1 = m_pick.predict_proba(d.loc[te, pick[1]])[:, 1]
    p0 = m0.predict_proba(d.loc[te, BASE[1]])[:, 1]
    rate_tr = np.average(y[tr], weights=w[tr])
    yt, wt = y[te], w[te]
    lo, hi = boot_delta(yt, p0, p1, wt)
    P_te['공통8고정'][n] = np.full(te.sum(), 1.0 if n in COMMON else 0.0)
    P_te['M0_성별연령'][n], P_te['선택모델'][n] = p0, p1
    test_rows.append(dict(
        영양소=n, 기준=KDRI[n][1], 선택=pick[0], 부족률_2024=np.average(yt, weights=wt),
        Train_AUC=roc_auc_score(y[tr], m_pick.predict_proba(d.loc[tr, pick[1]])[:, 1], sample_weight=w[tr]),
        CV_AUC=pick[5], Test_AUC=roc_auc_score(yt, p1, sample_weight=wt),
        M0_Test_AUC=roc_auc_score(yt, p0, sample_weight=wt), ΔAUC_CI_low=lo, ΔAUC_CI_high=hi,
        Test_로그손실=log_loss(yt, p1, sample_weight=wt), M0_로그손실=log_loss(yt, p0, sample_weight=wt),
        상수_로그손실=log_loss(yt, np.full(len(yt), rate_tr), sample_weight=wt),
        Test_Brier=brier_score_loss(yt, p1, sample_weight=wt)))
    print(f"{n:6s} 선택 {pick[0]:16s} AUC Train {test_rows[-1]['Train_AUC']:.3f} / CV {pick[5]:.3f} / "
          f"2024 {test_rows[-1]['Test_AUC']:.3f} (M0 {test_rows[-1]['M0_Test_AUC']:.3f}, Δ CI [{lo:+.3f}, {hi:+.3f}])")
tune = pd.DataFrame(tune_rows)
test = pd.DataFrame(test_rows)
test['ΔAUC'] = test['Test_AUC'] - test['M0_Test_AUC']
test['과적합(Train−Test)'] = test['Train_AUC'] - test['Test_AUC']
tune.to_csv(OUT / ('08_튜닝기록' + SUF + '.csv'), index=False, encoding='utf-8-sig')
test.to_csv(OUT / ('08_2024검증' + SUF + '.csv'), index=False, encoding='utf-8-sig')

# %% 3. 추천 목록 검증 (2024, 사람 단위): 추천 = 확률 ≥ 0.5
Y = d.loc[te, [f'below_{n}' for n in NUTRIENTS]].values
wt = w[te].values
rec_rows = []
for name, P in P_te.items():
    R = np.column_stack([P[n] >= CUT for n in NUTRIENTS])
    tp = (R & (Y == 1)).sum(1); fp = (R & (Y == 0)).sum(1); fn = (~R & (Y == 1)).sum(1)
    prec = np.average(tp / np.maximum(tp + fp, 1), weights=wt)
    rec = np.average(tp / np.maximum(tp + fn, 1), weights=wt)
    jac = np.average(tp / np.maximum(tp + fp + fn, 1), weights=wt)
    rec_rows.append(dict(방법=name, 평균추천개수=np.average(R.sum(1), weights=wt), 정밀도=prec, 재현율=rec,
                         F1=2 * prec * rec / (prec + rec), 자카드=jac,
                         목록종류=len({tuple(r) for r in R})))
recq = pd.DataFrame(rec_rows)
recq.to_csv(OUT / ('08_추천목록_2024검증' + SUF + '.csv'), index=False, encoding='utf-8-sig')

# 보정(calibration): 2024 선택모델 예측 10분위 vs 실제 (전 영양소 합침)
pp = np.concatenate([P_te['선택모델'][n] for n in NUTRIENTS])
yy = np.concatenate([d.loc[te, f'below_{n}'].values for n in NUTRIENTS])
ww = np.tile(wt, len(NUTRIENTS))
bins = pd.qcut(pp, 10, duplicates='drop')
calib = pd.DataFrame({'p': pp, 'y': yy, 'w': ww, 'bin': bins}).groupby('bin', observed=True).apply(
    lambda g: pd.Series({'예측': np.average(g['p'], weights=g['w']), '실제': np.average(g['y'], weights=g['w'])}))

# %% 4. 최종 학습(전체 연도) → 유형 × 성별 × 연령대 확률표 + 웹 JSON
grid = pd.MultiIndex.from_product([IDS, ['남자', '여자'], AGE_LABELS],
                                  names=['cluster', 'sex', 'age_grp_s']).to_frame(index=False)
grid['type_sex'] = grid['cluster'] + '_' + grid['sex']
grid['male'] = (grid['sex'] == '남자').astype(int)
# HGB가 선택되면 연령 대표값이 필요 → 각 연령대의 가중 평균 나이로 대체
age_mean = d.groupby('age_grp_s').apply(lambda g: np.average(g['age'], weights=g['w']))
grid['age'] = grid['age_grp_s'].map(age_mean)
base_grid = grid.copy()
for n in NUTRIENTS:
    y = d[f'below_{n}']
    _, cols, make, *_ = chosen[n]
    grid[n] = fit(make, cols, d.index, y).predict_proba(grid[cols])[:, 1]
    base_grid[n] = fit(BASE[2], BASE[1], d.index, y).predict_proba(base_grid[BASE[1]])[:, 1]

long = grid.melt(id_vars=['cluster', 'sex', 'age_grp_s'], value_vars=NUTRIENTS, var_name='영양소', value_name='부족확률')
long['성별연령평균'] = base_grid.melt(id_vars=['cluster', 'sex', 'age_grp_s'], value_vars=NUTRIENTS)['value'].values
long['배수'] = long['부족확률'] / long['성별연령평균']
long['of10'] = (long['부족확률'] * 10).round().astype(int)
long['추천'] = long['부족확률'] >= CUT
long['판정'] = [TAG[(c, n)] for c, n in zip(long['cluster'], long['영양소'])]
long['기준'] = long['영양소'].map(lambda n: KDRI[n][1])
long = long.sort_values(['cluster', 'sex', 'age_grp_s', '부족확률'], ascending=[True, True, True, False])
long['순위'] = long.groupby(['cluster', 'sex', 'age_grp_s']).cumcount() + 1
long.rename(columns={'cluster': '유형', 'sex': '성별', 'age_grp_s': '연령대', 'of10': '10명중'}).to_csv(
    OUT / ('08_유형성별연령_부족확률' + SUF + '.csv'), index=False, encoding='utf-8-sig')

TAG_TEXT = {'유형특이': '이 유형에서 특히 많아요', '식사량영향': '식사량 점검이 먼저예요',
            '공통주의': '대부분의 사람에게 부족해요', '': ''}
web = {'version': 'yuhwan-12types-reco-v1', 'source_types': NB['version'],
       '설명': '유형·성별·연령대가 같은 사람 중 2025 KDRI 기준 미만인 비율(조사 가중). EAR 미만=부족 위험, '
               'AI 미만=충분섭취량 미만(참고). 하루 24시간 회상 기준이며 개인 진단이 아닙니다. '
               '영양제 추천이 아니며, 질환이 있으면 전문가와 상담하세요.',
       '추천규칙': f'부족 확률 ≥ {CUT} (10명 중 5명 이상)', 'types': {}}
for k in IDS:
    web['types'][k] = {'name': TYPES[k]['name'], 'macro': TYPES[k]['macro'], 'cells': {}}
    for s in ['남자', '여자']:
        web['types'][k]['cells'][s] = {}
        for a in AGE_LABELS:
            g = long[(long['cluster'] == k) & (long['sex'] == s) & (long['age_grp_s'] == a)]
            web['types'][k]['cells'][s][a] = [
                dict(nutrient=r.영양소, basis=r.기준, p=round(r.부족확률, 3), of10=int(r.of10), vs_same_sex_age=round(r.배수, 2),
                     recommend=bool(r.추천), tag=r.판정, tag_text=TAG_TEXT[r.판정])
                for r in g.itertuples()]
with open(OUT / ('08_유형별_부족영양소_추천' + SUF + '.json'), 'w', encoding='utf-8') as fp:
    json.dump(web, fp, ensure_ascii=False, indent=1)

# %% 출력
pd.set_option('display.width', 250)
print('\n[튜닝 결과: 영양소별 선택 모델]')
print(test[['영양소', '선택', 'Train_AUC', 'CV_AUC', 'Test_AUC', 'M0_Test_AUC', 'ΔAUC', 'ΔAUC_CI_low',
            'Test_로그손실', 'M0_로그손실', '상수_로그손실', '과적합(Train−Test)']].round(3).to_string(index=False))
print('\n선택 모델 분포:', test['선택'].value_counts().to_dict())
print('\n[추천 목록 2024 검증 (추천 = 확률 ≥ 0.5)]')
print(recq.round(3).to_string(index=False))
print('\n[보정: 예측 10분위 vs 실제]')
print(calib.round(3).to_string())
ex = long[(long['cluster'] == 'N2') & (long['sex'] == '여자') & (long['age_grp_s'] == '30-49')]
print('\n[예시: N2 끼니 거르는 형 · 여자 · 30-49]')
print(ex[['순위', '영양소', '기준', '부족확률', 'of10', '성별연령평균', '배수', '추천', '판정']].round(2).to_string(index=False))

# %% 그림: 2024 보정곡선 + 유형별 추천 개수(여자 30-49 예시와 남자 30-49)
fig, ax = plt.subplots(1, 2, figsize=(13, 5))
ax[0].plot([0, 1], [0, 1], 'k--', lw=0.8)
ax[0].plot(calib['예측'], calib['실제'], 'o-', color='#2a6fbb')
ax[0].set_xlabel('예측 부족 확률 (2024, 10분위)'); ax[0].set_ylabel('실제 부족 비율')
ax[0].set_title('2024 검증 보정곡선 (15개 영양소 합침)')
cnt = long[long['age_grp_s'] == '30-49'].groupby(['cluster', 'sex'])['추천'].sum().unstack().loc[IDS]
cnt.index = [f'{k} {TYPES[k]["name"]}' for k in IDS]
cnt.plot.barh(ax=ax[1], color=['#2a6fbb', '#e07b39'])
ax[1].axvline(len(COMMON), color='gray', ls=':', label=f'공통 고정 {len(COMMON)}개')
ax[1].invert_yaxis(); ax[1].set_xlabel('추천 영양소 수 (확률 ≥ 0.5)'); ax[1].legend()
ax[1].set_title('유형별 추천 개수 (30-49세)')
plt.tight_layout(); plt.savefig(OUT / ('fig_08_보정곡선_추천개수' + SUF + '.png'), dpi=150)
print('\n저장:', OUT)
