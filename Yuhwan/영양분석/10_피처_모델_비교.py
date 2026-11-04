# %% [markdown]
# # [B-3 확장] 파생변수 추가 · 모델 섞기(앙상블)로 08번 추천이 나아지는가
# 08번: 유형+성별+연령대 → 영양소별 부족 확률 (가중 로지스틱, 2022–23 튜닝 → 2024 검증)
#
# 입력 규칙: 웹 설문으로 받을 수 있는 값만. 섭취량(에너지 포함)은 사용자가 모르고 정답을 만든 재료라 넣지 않음(누수)
# 피처 세트 (누적)
#   F0 유형 + 성별 + 연령대                         ← 08번 그대로
#   F1 + 나이(연속, 2차항) + 유형×성별
#   F2 + 생활습관 설문 응답 14개 (군집 입력 원값, 흡연·음주 포함)
#   F3 + 채소·과일 섭취 빈도 (주당 횟수, 웹 설문 문항)
# 모델: LR(C 0.01·0.1·1, 1-SE) / HGB(잎 7·15, 1-SE) / ENS = LR과 HGB 확률 평균
# 선택: 2022–23 5-fold CV 가중 로그손실 (영양소 평균)로만 고름. 2024는 최종 확인용
# 판정 (결과 보기 전에 확정): 08번(F0·LR) 대비 2024 평균 로그손실이 줄고, AUC가 오른 영양소의 95% CI가 0을 넘는 경우만 '개선'

# %%
import warnings
import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score, log_loss
from common import *

warnings.filterwarnings('ignore')
SEED, CUT = 42, 0.5
TYPE_FILE = ROOT / 'KMedoids_12Types_N1O3.csv'        # 08번이 만든 N1~O3 배정 (개인 단위, git 제외)

d = add_status(load_persons(TYPE_FILE, 'Type'))
d['age_grp_s'] = d['age_grp'].astype(str)
d['type_sex'] = d['cluster'] + '_' + d['sex']
d['age2'] = (d['age'] - 50) ** 2 / 100
LS = ['ML_smoker', 'ML_cigarettes_day', 'ML_drink_month', 'ML_drink_freq_ord', 'ML_drink_amount_ord',
      'ML_aerobic', 'ML_strength_days', 'ML_sedentary_min', 'ML_sleep_hours', 'ML_stress',
      'ML_breakfast_freq_ord', 'ML_lunch_freq_ord', 'ML_dinner_freq_ord', 'ML_eatingout_freq_ord']
VF = ['과일_주당', '채소_김치포함_주당', '채소_김치제외_주당']          # 99(모름) → 결측, 파이프라인 안에서 중앙값 대체
FSETS = {
    'F0': (['sex', 'age_grp_s', 'cluster'], []),
    'F1': (['sex', 'age_grp_s', 'cluster', 'type_sex'], ['age', 'age2']),
    'F2': (['sex', 'age_grp_s', 'cluster', 'type_sex'], ['age', 'age2'] + LS),
    'F3': (['sex', 'age_grp_s', 'cluster', 'type_sex'], ['age', 'age2'] + LS + VF),
}
GROUPS = {'유형': ['cluster', 'type_sex'], '성별·나이': ['sex', 'age_grp_s', 'age', 'age2'],
          '생활습관14': LS, '채소·과일': VF}
tr_idx = np.flatnonzero(d['year'] <= 2023)
te_idx = np.flatnonzero(d['year'] == 2024)
w = (d['w'] / d['w'].mean()).values
print('사람', len(d), '| 학습', len(tr_idx), '| 2024', len(te_idx), '| 과일·채소 결측', int(d[VF].isna().any(axis=1).sum()))


def lr(cat, num, C):
    parts = [('cat', OneHotEncoder(drop='first', handle_unknown='ignore'), cat)]
    if num:
        parts.append(('num', Pipeline([('imp', SimpleImputer(strategy='median')), ('sc', StandardScaler())]), num))
    return Pipeline([('p', ColumnTransformer(parts)), ('m', LogisticRegression(C=C, max_iter=5000))])


def hgb(cat, num, leaf):
    hcat = [c for c in cat if c != 'age_grp_s'] if num else cat     # 나이 연속값이 있으면 연령대는 중복이라 뺌
    return Pipeline([('p', ColumnTransformer([('ord', OrdinalEncoder(), hcat)] +
                                            ([('num', 'passthrough', [c for c in num if c != 'age2'])] if num else []))),
                     ('m', HistGradientBoostingClassifier(learning_rate=0.05, max_leaf_nodes=leaf, min_samples_leaf=100,
                                                          max_iter=200, categorical_features=list(range(len(hcat))),
                                                          random_state=SEED))])


CANDS = {'LR': [(f'C{C}', lambda cat, num, C=C: lr(cat, num, C)) for C in [0.01, 0.1, 1]],     # 단순한 순
         'HGB': [(f'leaf{l}', lambda cat, num, l=l: hgb(cat, num, l)) for l in [7, 15]]}


def fit(make, cat, num, idx, y):
    return make(cat, num).fit(d.iloc[idx][cat + num], y[idx], m__sample_weight=w[idx])


def oof(make, cat, num, y):
    """2022–23 안에서 5-fold out-of-fold 예측."""
    p = np.empty(len(tr_idx))
    for a, b in StratifiedKFold(5, shuffle=True, random_state=SEED).split(tr_idx, y[tr_idx]):
        p[b] = fit(make, cat, num, tr_idx[a], y).predict_proba(d.iloc[tr_idx[b]][cat + num])[:, 1]
    return p


def wll(y, p, sw):
    return log_loss(y, np.clip(p, 1e-6, 1 - 1e-6), sample_weight=sw)


def run(n):
    y = d[f'below_{n}'].values
    yt, wt, yte, wte = y[tr_idx], w[tr_idx], y[te_idx], w[te_idx]
    rows, preds, tune = [], {}, []
    for fs, (cat, num) in FSETS.items():
        picked = {}
        for fam, cands in CANDS.items():
            sc = []
            for name, make in cands:
                p = oof(make, cat, num, y)
                # 폴드별 로그손실 → 평균·SE (1-SE 규칙)
                fl = [wll(yt[b], p[b], wt[b]) for _, b in StratifiedKFold(5, shuffle=True, random_state=SEED).split(tr_idx, yt)]
                sc.append((name, make, np.mean(fl), np.std(fl, ddof=1) / np.sqrt(5), p))
                tune.append(dict(영양소=n, 피처=fs, 모델=fam, 설정=name, CV로그손실=np.mean(fl)))
            best = min(sc, key=lambda s: s[2])
            picked[fam] = next(s for s in sc if s[2] <= best[2] + best[3])
        oof_ens = (picked['LR'][4] + picked['HGB'][4]) / 2
        te_p = {fam: fit(s[1], cat, num, tr_idx, y).predict_proba(d.iloc[te_idx][cat + num])[:, 1]
                for fam, s in picked.items()}
        te_p['ENS'] = (te_p['LR'] + te_p['HGB']) / 2
        cv_p = {'LR': picked['LR'][4], 'HGB': picked['HGB'][4], 'ENS': oof_ens}
        for fam in ['LR', 'HGB', 'ENS']:
            rows.append(dict(영양소=n, 피처=fs, 모델=fam,
                             설정=picked[fam][0] if fam != 'ENS' else f"{picked['LR'][0]}+{picked['HGB'][0]}",
                             CV로그손실=wll(yt, cv_p[fam], wt), CV_AUC=roc_auc_score(yt, cv_p[fam], sample_weight=wt),
                             Test로그손실=wll(yte, te_p[fam], wte), Test_AUC=roc_auc_score(yte, te_p[fam], sample_weight=wte)))
            preds[(fs, fam)] = te_p[fam]
    return rows, preds, tune


out = Parallel(n_jobs=-1)(delayed(run)(n) for n in NUTRIENTS)
res = pd.DataFrame([r for o in out for r in o[0]])
PRED = {n: o[1] for n, o in zip(NUTRIENTS, out)}
pd.DataFrame([t for o in out for t in o[2]]).to_csv(OUT / '10_튜닝기록.csv', index=False, encoding='utf-8-sig')
res.to_csv(OUT / '10_피처모델_영양소별.csv', index=False, encoding='utf-8-sig')

# %% 1. 평균 성능 (선택은 CV로)
summ = res.groupby(['피처', '모델'])[['CV로그손실', 'CV_AUC', 'Test로그손실', 'Test_AUC']].mean()
Y = d.iloc[te_idx][[f'below_{n}' for n in NUTRIENTS]].values
wte = w[te_idx]
f1 = {}
for key in summ.index:
    R = np.column_stack([PRED[n][key] >= CUT for n in NUTRIENTS])
    tp = (R & (Y == 1)).sum(1); fp = (R & (Y == 0)).sum(1); fn = (~R & (Y == 1)).sum(1)
    pr = np.average(tp / np.maximum(tp + fp, 1), weights=wte)
    rc = np.average(tp / np.maximum(tp + fn, 1), weights=wte)
    f1[key] = 2 * pr * rc / (pr + rc)
summ['추천F1_2024'] = pd.Series(f1)
winner = summ['CV로그손실'].idxmin()
print('[피처 세트 × 모델: 15개 영양소 평균]')
print(summ.round(4).to_string())
print('\nCV 로그손실 최소 조합:', winner)

# %% 2. 08번(F0·LR) 대비: 영양소별 2024 ΔAUC와 95% CI (CV 최적 조합, F2·F3 앙상블도 같이)
def boot(y, pa, pb, sw, B=500):
    rng = np.random.default_rng(SEED)
    o = []
    for _ in range(B):
        i = rng.integers(0, len(y), len(y))
        o.append(roc_auc_score(y[i], pb[i], sample_weight=sw[i]) - roc_auc_score(y[i], pa[i], sample_weight=sw[i]))
    return np.percentile(o, [2.5, 97.5])


cmp_rows = []
for key in sorted({winner, ('F1', 'ENS'), ('F2', 'ENS'), ('F3', 'ENS'), ('F3', 'LR')}):
    for n in NUTRIENTS:
        y = d.iloc[te_idx][f'below_{n}'].values
        pa, pb = PRED[n][('F0', 'LR')], PRED[n][key]
        lo, hi = boot(y, pa, pb, wte)
        cmp_rows.append(dict(비교=f'{key[0]}·{key[1]}', 영양소=n,
                             ΔAUC=roc_auc_score(y, pb, sample_weight=wte) - roc_auc_score(y, pa, sample_weight=wte),
                             CI_low=lo, CI_high=hi,
                             Δ로그손실=wll(y, pb, wte) - wll(y, pa, wte)))
cmp = pd.DataFrame(cmp_rows)
cmp.to_csv(OUT / '10_08번대비_개선.csv', index=False, encoding='utf-8-sig')
agg = cmp.groupby('비교').agg(평균ΔAUC=('ΔAUC', 'mean'), 유의개선수=('CI_low', lambda s: int((s > 0).sum())),
                            유의악화수=('CI_high', lambda s: int((s < 0).sum())), 평균Δ로그손실=('Δ로그손실', 'mean'))
print('\n[08번(F0·LR) 대비 2024]')
print(agg.round(4).to_string())

# %% 3. 무엇이 기여하나: F3 앙상블의 그룹별 순열 중요도 (2024, 그룹 열을 같이 섞음 → AUC 감소, 영양소 평균)
cat3, num3 = FSETS['F3']
rng = np.random.default_rng(SEED)
imp_rows = []
for n in NUTRIENTS:
    y = d[f'below_{n}'].values
    res_n = res[(res['영양소'] == n) & (res['피처'] == 'F3')].set_index('모델')
    lr_cfg, hgb_cfg = res_n.loc['ENS', '설정'].split('+')
    m_lr = fit(dict(CANDS['LR'])[lr_cfg], cat3, num3, tr_idx, y)
    m_hgb = fit(dict(CANDS['HGB'])[hgb_cfg], cat3, num3, tr_idx, y)
    Xte = d.iloc[te_idx][cat3 + num3].reset_index(drop=True)
    pred = lambda X: (m_lr.predict_proba(X)[:, 1] + m_hgb.predict_proba(X)[:, 1]) / 2
    base = roc_auc_score(y[te_idx], pred(Xte), sample_weight=wte)
    for g, cols in GROUPS.items():
        drops = []
        for _ in range(5):
            Xp = Xte.copy()
            Xp[cols] = Xte[cols].iloc[rng.permutation(len(Xte))].values
            drops.append(base - roc_auc_score(y[te_idx], pred(Xp), sample_weight=wte))
        imp_rows.append(dict(영양소=n, 그룹=g, AUC감소=np.mean(drops)))
imp = pd.DataFrame(imp_rows)
imp.to_csv(OUT / '10_순열중요도_F3앙상블.csv', index=False, encoding='utf-8-sig')
print('\n[F3 앙상블 그룹별 순열 중요도: 2024 AUC 감소, 영양소 평균 / 최대]')
print(imp.groupby('그룹')['AUC감소'].agg(['mean', 'max']).sort_values('mean', ascending=False).round(4).to_string())
print('\n[영양소별 Test AUC: F0·LR vs F3·ENS]')
pv = res.pivot_table(index='영양소', columns=['피처', '모델'], values='Test_AUC').loc[NUTRIENTS]
print(pv[[('F0', 'LR'), ('F1', 'ENS'), ('F2', 'ENS'), ('F3', 'ENS')]].round(3).to_string())
print('\n저장:', OUT)
