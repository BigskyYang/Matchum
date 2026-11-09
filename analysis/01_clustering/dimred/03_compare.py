# -*- coding: utf-8 -*-
"""차원축소별 K-Medoids(k=4) 결과 비교 -> dimred_comparison.csv, dimred_labels.csv"""
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.manifold import trustworthiness
from sklearn.metrics import adjusted_rand_score as ari, roc_auc_score, silhouette_score
from sklearn.model_selection import KFold
from sklearn.preprocessing import OneHotEncoder

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE.parent))
import kmedoids_final as K

CACHE = HERE / 'cache'
SEEDS = [42, 0, 1, 2, 3]
SUB_SEEDS = [100, 101, 102]
SETS = ['pca7_5d', 'umap7_5d', 'umap7_10d', 'pca14_5d', 'pca14_10d', 'umap14_5d', 'umap14_10d']
SRC = {s: ('input7' if '7_' in s else 'input14') for s in SETS}
pd.set_option('display.width', 240, 'display.max_columns', 40, 'display.max_rows', 100)

df = pd.read_csv(HERE.parent / K.CSV, encoding='utf-8-sig')
X, M, _ = K.build_matrix(df)
Z = (X - X.mean(0)) / X.std(0)
INP = {'input7': M, 'input14': Z}
n = len(df)
lab = pd.read_excel(HERE.parent / K.OUT_XLSX, sheet_name='Raw_Data', usecols=['Macro_Cluster', 'Type_Code'])
stored = pd.factorize(lab.Macro_Cluster)[0]

base = pd.read_csv(HERE.parent / 'KNHANES_2022_2024_ANALYSIS_BASE.csv', encoding='utf-8-sig', low_memory=False)
d = df[['ID']].merge(base, on='ID', how='left', validate='1:1')
src = (ROOT / 'analysis/02_type_nutrition/영양분석/common.py').read_text(encoding='utf-8')
ns = {}
exec(src[src.index('KDRI = {'):src.index('NUTRIENTS = list(KDRI)')], ns)
KDRI = ns['KDRI']
NUT = list(KDRI)
EAR = [m for m in NUT if KDRI[m][1] == 'EAR']
ag = pd.cut(d['설명_age'], [18, 29, 49, 64, 74, 200], labels=['19-29', '30-49', '50-64', '65-74', '75+'])
idx = ag.cat.codes.values
male = (d['설명_sex'] == 1).values
R, B = {}, {}
for nu, (c, b, a1, a2, *_) in KDRI.items():
    ref = np.where(male, np.array(a1)[idx], np.array(a2)[idx]).astype(float)
    R[nu] = np.log(np.maximum(d[c].values / ref, .01))
    B[nu] = (d[c].values < ref).astype(int)
R, B = pd.DataFrame(R), pd.DataFrame(B)
sa = (d['설명_sex'].astype(int).astype(str) + ag.astype(str)).values


def km(kind, name, seed):
    return np.load(CACHE / f'km_{kind}_{name}_{seed}.npz')


def cv_auc(cols):
    Xo = OneHotEncoder(handle_unknown='ignore').fit_transform(np.column_stack(cols).astype(str))
    p = np.zeros((n, len(EAR)))
    for tr, te in KFold(5, shuffle=True, random_state=0).split(Xo):
        p[te] = Ridge(alpha=1.0).fit(Xo[tr], B[EAR].values[tr]).predict(Xo[te])
    return float(np.mean([roc_auc_score(B[EAR].values[:, j], p[:, j]) for j in range(len(EAR))]))


def eta_mean(Y, g):
    g = pd.Series(g)
    vals = []
    for j in range(Y.shape[1]):
        y = pd.Series(Y[:, j])
        vals.append(((y.groupby(g).transform('mean') - y.mean()) ** 2).sum() / ((y - y.mean()) ** 2).sum())
    return vals


def half_corr(l):
    perm = np.random.default_rng(0).permutation(n)
    half = np.zeros(n, bool)
    half[perm[:n // 2]] = True
    s = pd.Series(l)
    a, b = B[EAR][half].groupby(s[half]).mean(), B[EAR][~half].groupby(s[~half]).mean()
    return float(np.corrcoef((a - B[EAR].mean()).values.ravel(), (b - B[EAR].mean()).values.ravel())[0, 1])


rng = np.random.default_rng(0)
samp = rng.choice(n, 6000, replace=False)
tw_samp = rng.choice(n, 3000, replace=False)
aero_stress = (df.ML_aerobic.astype(int) * 2 + df.ML_stress.astype(int)).values
FEAT7 = K.MODEL_FEATURES
rows, etas, labels_out = [], {}, {'ID': df.ID}
for name in SETS:
    main = km('seed', name, 42)
    l = main['labels']
    labels_out[name] = l
    labs = [km('seed', name, s)['labels'] for s in SEEDS]
    aris = [ari(a, b) for a, b in combinations(labs, 2)]
    kmonly = [ari(l, km('kmonly', name, s)['labels']) for s in (0, 1)] if 'umap' in name else [np.nan]
    subs = [km('sub', name, s) for s in SUB_SEEDS]
    sub_tr = [ari(l[z['tr']], z['labels']) for z in subs]
    sub_te = [ari(l[z['te']], z['labels_te']) for z in subs]
    e = pd.read_csv(HERE / f'{name}.csv', encoding='utf-8-sig')
    E = e[[c for c in e.columns if c.startswith('C')]].values
    size = pd.Series(l).value_counts(normalize=True)
    eta = eta_mean(M, l)
    etas[name] = dict(zip(FEAT7, eta))
    au, au2 = cv_auc([l]), cv_auc([l, sa])
    rows.append(dict(방식=name, 시드ARI평균=np.mean(aris), 시드ARI최소=np.min(aris),
                     KM만시드ARI=np.nanmean(kmonly), 시작점ARI최소=main['start_ari'].min(),
                     비용격차pct=(main['start_cost'].max() / main['start_cost'].min() - 1) * 100,
                     부분표본ARI평균=np.mean(sub_tr), 부분표본ARI최소=np.min(sub_tr), 미학습자ARI평균=np.mean(sub_te),
                     실루엣_자기공간=float(main['sil_own']),
                     실루엣_7변수공간=silhouette_score(M[samp], l[samp]),
                     최소군집pct=size.min() * 100, 최대군집pct=size.max() * 100,
                     저장본ARI=ari(stored, l), 유산소x스트레스ARI=ari(aero_stress, l),
                     생활습관eta2평균=np.mean(eta), 영양AUC=au, 영양AUC_성연령=au2,
                     영양eta2=np.mean(eta_mean(R.values, l)), 영양반분상관=half_corr(l),
                     신뢰도=trustworthiness(INP[SRC[name]][tw_samp], E[tw_samp], n_neighbors=15)))
res = pd.DataFrame(rows).set_index('방식')
res.round(3).to_csv(HERE / 'dimred_comparison.csv', encoding='utf-8-sig')
pd.DataFrame(labels_out).to_csv(HERE / 'dimred_labels.csv', index=False, encoding='utf-8-sig')
print(res.T.round(3).to_string())

print('\n[생활습관 변수 eta2]')
print(pd.DataFrame(etas).round(3).to_string())
print('\n[시작점별 비용]')
for name in SETS:
    z = km('seed', name, 42)
    print(name, np.round(z['start_cost'], 1), 'ARI', np.round(z['start_ari'], 3))
print('\n[UMAP 파라미터 민감도: 기본(nn30,md0) 대비 ARI]')
b0 = km('seed', 'umap7_5d', 42)['labels']
for t in ['nn15', 'nn50', 'md01']:
    print(t, round(ari(b0, km('sens', f'umap7_5d_{t}', 42)['labels']), 3))
print('\n[k 탐색: k, 총거리, 자기공간 실루엣]')
for name in SETS:
    print(name, np.round(km('kscan', name, 0)['table'], 3)[:, [0, 2]].tolist())
print('\n[군집 프로파일: 7변수 z 평균]')
for name in ['pca7_5d', 'umap7_5d', 'umap7_10d']:
    l = km('seed', name, 42)['labels']
    print(name)
    print(pd.DataFrame(M, columns=FEAT7).groupby(l).mean().round(2).assign(n=pd.Series(l).value_counts()).to_string())
