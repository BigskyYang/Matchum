# -*- coding: utf-8 -*-
"""
후속 점검
  A. 현재 방식을 시작점 충분히(20회) 주고 재평가: 시작점별 해, 80% 부분표본 안정성 (저장본 기준)
  B. 이진변수(유산소·스트레스) 제거 후 UMAP -> 연속형 구조가 있는지
  C. 차원의 저주 점검: 거리 집중도, 고유값
  D. 14변수 UMAP 이 어떤 변수로 갈리는지
  E. 규칙 분류(유산소×스트레스)와 UMAP 군집 일치도
"""
import os
os.environ.setdefault('OMP_NUM_THREADS', '2')
os.environ.setdefault('NUMBA_NUM_THREADS', '2')
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist, pdist, squareform
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge
from sklearn.metrics import adjusted_rand_score as ari, roc_auc_score, silhouette_score
from sklearn.model_selection import KFold
from sklearn.preprocessing import OneHotEncoder

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE.parent))
import kmedoids_final as K

CACHE = HERE / 'cache'


def load():
    df = pd.read_csv(HERE.parent / K.CSV, encoding='utf-8-sig')
    X, M, _ = K.build_matrix(df)
    lab = pd.read_excel(HERE.parent / K.OUT_XLSX, sheet_name='Raw_Data', usecols=['Macro_Cluster'])
    return df, X, M, pd.factorize(lab.Macro_Cluster)[0]


def starts(E, seed, n_init):
    D = K.pairwise_dist(E)
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n_init):
        med = K.voronoi(D, K.swap_polish(D, K.kmpp_init(D, 4, rng)))
        out.append((K.total_cost(D, med), np.argmin(D[med], axis=0), E[med]))
    return out, K.silhouette(D, min(out, key=lambda r: r[0])[1])


def full_starts(_):
    df, X, M, stored = load()
    r, sil = starts(PCA(5, random_state=42).fit_transform(M), 42, 20)
    return [(round(c, 1), round(ari(stored, l), 3)) for c, l, _ in r]


def sub_job(s):
    df, X, M, stored = load()
    idx = np.random.default_rng(s).permutation(len(M))
    tr, te = idx[:int(len(M) * .8)], idx[int(len(M) * .8):]
    p = PCA(5, random_state=42).fit(M[tr])
    r, _ = starts(p.transform(M[tr]), 42, 20)
    c, l, med = min(r, key=lambda x: x[0])
    lt = np.argmin(cdist(p.transform(M[te]), med), axis=1)
    return s, round(ari(stored[tr], l), 3), round(ari(stored[te], lt), 3), round(c, 1)


def umap_job(job):
    import umap
    seed, sub = job
    df, X, M, stored = load()
    drop = [K.MODEL_FEATURES.index(c) for c in ('aerobic', 'stress')]
    A = np.delete(M, drop, axis=1)
    if sub:
        idx = np.random.default_rng(sub).permutation(len(A))
        tr = idx[:int(len(A) * .8)]
    else:
        tr = np.arange(len(A))
    E = umap.UMAP(n_components=5, n_neighbors=30, min_dist=0.0, random_state=seed).fit_transform(A[tr])
    r, sil = starts(E, seed, 5)
    c, l, _ = min(r, key=lambda x: x[0])
    return dict(seed=seed, sub=sub, tr=tr, labels=l, sil=sil, cost=c, start_ari=[round(ari(l, x[1]), 3) for x in r])


def main():
    df, X, M, stored = load()
    Z = (X - X.mean(0)) / X.std(0)
    n = len(M)
    with ProcessPoolExecutor(max_workers=3) as ex:
        fs = ex.submit(full_starts, 0)
        subs = list(ex.map(sub_job, [100, 101, 102, 103, 104]))
        res = fs.result()
    costs = sorted(res)
    print('[A] 현재 방식 시작점 20회 (비용, 저장본 ARI, 오름차순)')
    print(costs)
    print('저장본(26436.3) 도달 시작점 수', sum(abs(c - 26436.3) < .2 for c, _ in res), '/ 20')
    print('[A] 80% 부분표본 (시드, 학습자 ARI, 미학습자 ARI, 비용)', subs)
    print('    평균 학습자 ARI', round(np.mean([s[1] for s in subs]), 3), '최소', min(s[1] for s in subs))

    print('\n[B] 이진변수 제거 5변수 UMAP(5D)')
    with ProcessPoolExecutor(max_workers=3) as ex:
        U = list(ex.map(umap_job, [(42, None), (0, None), (1, None), (42, 100), (42, 101)]))
    main_l = U[0]['labels']
    print('자기공간 실루엣', round(U[0]['sil'], 3), '| 7변수 공간 실루엣', round(silhouette_score(M[np.random.default_rng(0).choice(n, 6000, replace=False)], main_l[np.random.default_rng(0).choice(n, 6000, replace=False)]), 3))
    print('시작점 ARI', U[0]['start_ari'], '| UMAP 시드 ARI', round(ari(main_l, U[1]['labels']), 3), round(ari(main_l, U[2]['labels']), 3), round(ari(U[1]['labels'], U[2]['labels']), 3))
    print('부분표본 ARI', [round(ari(main_l[u['tr']], u['labels']), 3) for u in U[3:]])
    print('군집 크기', pd.Series(main_l).value_counts().tolist())
    print(pd.DataFrame(M, columns=K.MODEL_FEATURES).groupby(main_l).mean().round(2).to_string())

    print('\n[C] 차원의 저주 점검')
    s = np.random.default_rng(0).choice(n, 3000, replace=False)
    rng = np.random.default_rng(0)
    for nm, A in [('7변수', M), ('14변수', Z), ('PCA5(7변수)', PCA(5, random_state=42).fit_transform(M)),
                  ('무관 정규난수 7차원', rng.normal(size=(3000, 7))), ('무관 정규난수 100차원', rng.normal(size=(3000, 100)))]:
        Dm = squareform(pdist(A[s] if len(A) == n else A))
        np.fill_diagonal(Dm, np.nan)
        nn, far, mean = np.nanmin(Dm, 1), np.nanmax(Dm, 1), np.nanmean(Dm, 1)
        print(f'{nm:16s} 최근접/평균거리 {np.mean(nn / mean):.3f} | (최원-최근접)/최근접 {np.median((far - nn) / np.maximum(nn, 1e-9)):.2f}')
    print('7변수 고유값 비율', np.round(PCA().fit(M).explained_variance_ratio_, 3))
    cor = np.corrcoef(M.T)
    print('7변수 절대상관 최대', round(np.abs(cor - np.eye(7)).max(), 3), '평균', round((np.abs(cor).sum() - 7) / 42, 3))

    print('\n[D] 14변수 공간 군집의 변수별 eta2')
    labs = pd.read_csv(HERE / 'dimred_labels.csv', encoding='utf-8-sig')
    F = [c.replace('ML_', '') for c in K.FEATURES]
    def eta(l):
        g = pd.Series(l)
        return {f: round(float(((pd.Series(Z[:, j]).groupby(g).transform('mean')) ** 2).sum() / (Z[:, j] ** 2).sum()), 3) for j, f in enumerate(F)}
    print(pd.DataFrame({k: eta(labs[k].values) for k in ['pca14_5d', 'pca14_10d', 'umap14_5d', 'umap14_10d']}).to_string())
    smk, drk, aer, st = [df[c].astype(int).values for c in ('ML_smoker', 'ML_drink_month', 'ML_aerobic', 'ML_stress')]
    for nm, g in [('음주×유산소', drk * 2 + aer), ('흡연×음주', smk * 2 + drk), ('흡연×음주×유산소', smk * 4 + drk * 2 + aer), ('4개 이진 전부', smk * 8 + drk * 4 + aer * 2 + st)]:
        print(nm, 'ARI umap14_5d', round(ari(g, labs['umap14_5d']), 3), 'umap14_10d', round(ari(g, labs['umap14_10d']), 3))
    E14 = pd.read_csv(HERE / 'umap14_5d.csv', encoding='utf-8-sig').filter(regex='^C').values
    D = K.pairwise_dist(E14)
    for k in (8, 16):
        med = K.voronoi(D, K.swap_polish(D, K.kmpp_init(D, k, np.random.default_rng(42))))
        l = np.argmin(D[med], axis=0)
        print(f'umap14_5d k={k} 실루엣 {K.silhouette(D, l):.3f} ARI 4개이진 {ari(smk * 8 + drk * 4 + aer * 2 + st, l):.3f} ARI 흡연음주유산소 {ari(smk * 4 + drk * 2 + aer, l):.3f}')
    del D

    print('\n[E] 규칙 분류 일치')
    rule = aer * 2 + st
    print('유산소×스트레스 규칙 vs umap7_5d', round(ari(rule, labs['umap7_5d']), 4), 'umap7_10d', round(ari(rule, labs['umap7_10d']), 4),
          '| umap7_5d vs umap7_10d', round(ari(labs['umap7_5d'], labs['umap7_10d']), 4))

    # 저장본 대분류의 영양 지표 (같은 평가식)
    base = pd.read_csv(HERE.parent / 'KNHANES_2022_2024_ANALYSIS_BASE.csv', encoding='utf-8-sig', low_memory=False)
    d = df[['ID']].merge(base, on='ID', how='left', validate='1:1')
    src = (ROOT / 'Yuhwan/영양분석/common.py').read_text(encoding='utf-8')
    ns = {}
    exec(src[src.index('KDRI = {'):src.index('NUTRIENTS = list(KDRI)')], ns)
    KD = ns['KDRI']
    EAR = [m for m in KD if KD[m][1] == 'EAR']
    ag = pd.cut(d['설명_age'], [18, 29, 49, 64, 74, 200], labels=['19-29', '30-49', '50-64', '65-74', '75+'])
    idx, male = ag.cat.codes.values, (d['설명_sex'] == 1).values
    B = np.column_stack([(d[KD[m][0]].values < np.where(male, np.array(KD[m][2])[idx], np.array(KD[m][3])[idx])).astype(int) for m in EAR])
    sa = (d['설명_sex'].astype(int).astype(str) + ag.astype(str)).values
    def auc(cols):
        Xo = OneHotEncoder(handle_unknown='ignore').fit_transform(np.column_stack(cols).astype(str))
        p = np.zeros(B.shape)
        for tr, te in KFold(5, shuffle=True, random_state=0).split(Xo):
            p[te] = Ridge(alpha=1.0).fit(Xo[tr], B[tr]).predict(Xo[te])
        return round(float(np.mean([roc_auc_score(B[:, j], p[:, j]) for j in range(B.shape[1])])), 3)
    print('\n[F] 영양 AUC (단독 / 성연령 포함)')
    for nm, l in [('저장본 대분류', stored), ('유산소×스트레스 규칙', rule), ('5변수 UMAP', main_l)]:
        print(nm, auc([l]), auc([l, sa]))
    print('성연령만', auc([sa]))


if __name__ == '__main__':
    main()
