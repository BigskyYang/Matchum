# -*- coding: utf-8 -*-
"""실루엣 외 지표로 귀무 검정 교차 확인 (대분류 k=4와 12유형).

자료는 기존 검정과 같은 난수 흐름: 귀무 A·B 각 20회, 12덩어리 양성 대조 d=2,3,4 각 5회.
재현 확인용으로 대분류 실루엣과 12유형 실루엣(PCA5)도 함께 기록한다.

지표 (좋은 방향)
  CH: Calinski-Harabasz (높을수록 분리)      대분류=PCA5 공간, 12유형=7변수 공간
  DB: Davies-Bouldin (낮을수록 분리)          대분류=PCA5 공간, 12유형=7변수 공간
  평균거리: k-medoids 평균거리 (낮을수록 응집)  대분류만
  Hopkins: 군집 수와 무관한 군집 경향 (높을수록 뭉침), 7변수 공간, 표본 1000점

판정 기준 (실행 전 확정). 지표마다 실루엣 검정과 같은 규칙:
  좋은 방향으로 A·B 20회 극값을 모두 넘음 -> 우연보다 뚜렷한 구조
  A만 넘음 -> 변수 간 관계에서 오는 구조
  둘 다 못 넘음 -> 연속 분포를 나눈 구분
양성 대조: 같은 극값(A·B 합산)을 넘으면 검출.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from scipy.stats import norm, spearmanr
from sklearn.decomposition import PCA
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import power_12types as pw            # 자료, planted 재사용
kf = pw.kf
M, n, p, Ms = pw.M, pw.n, pw.p, pw.Ms
F = kf.MODEL_FEATURES
OUT = HERE / 'null_test_other_metrics.csv'
SEED = 42
BETTER = {'대분류_CH': 1, '대분류_DB': -1, '대분류_평균거리': -1, '12유형_CH': 1, '12유형_DB': -1, 'Hopkins': 1}


def hopkins(X, m=1000):
    rng = np.random.default_rng(SEED)
    tree = cKDTree(X)
    idx = rng.choice(len(X), m, replace=False)
    w = tree.query(X[idx], k=2)[0][:, 1]
    U = rng.uniform(X.min(0), X.max(0), size=(m, X.shape[1]))
    u = tree.query(U, k=1)[0]
    return float(u.sum() / (u.sum() + w.sum()))


def run(X):
    pca = PCA(n_components=5, random_state=SEED).fit(X)
    Q = pca.transform(X)
    D = kf.pairwise_dist(Q)
    med, cost = kf.kmedoids(D, 4, seed=SEED, n_init=10)
    labels = np.argmin(D[med], axis=0)
    out = {'대분류_실루엣': kf.silhouette(D, labels),
           '대분류_CH': calinski_harabasz_score(Q, labels),
           '대분류_DB': davies_bouldin_score(Q, labels),
           '대분류_평균거리': cost / n}
    macro = kf.name_macro(X, labels)
    types = np.empty(n, dtype=int)
    for g in range(4):
        cols, k = kf.SUB_PLAN[macro[g]]
        sel = np.flatnonzero(labels == g)
        B = X[np.ix_(sel, [F.index(c) for c in cols])]
        bs = B.std(0)
        Bz = (B - B.mean(0)) / np.where(bs == 0, 1, bs)
        Ds = kf.pairwise_dist(Bz)
        m, _ = kf.kmedoids(Ds, k, seed=SEED, n_init=10)
        types[sel] = g * 3 + np.argmin(Ds[m], axis=0)
        del Ds
    lb = np.unique(types, return_inverse=True)[1]
    out['12유형_실루엣_PCA5'] = kf.silhouette(D, lb)
    del D
    out['12유형_CH'] = calinski_harabasz_score(X, lb)
    out['12유형_DB'] = davies_bouldin_score(X, lb)
    out['Hopkins'] = hopkins(X)
    return out


def main():
    rows = pd.read_csv(OUT, encoding='utf-8-sig').to_dict('records') if OUT.exists() else []
    done = {(r['자료'], int(r['회차'])) for r in rows}

    def record(name, r, res):
        rows.append({'자료': name, '회차': r, **res})
        pd.DataFrame(rows).to_csv(OUT, index=False, encoding='utf-8-sig')
        print(name, r, {k: round(float(v), 3) for k, v in res.items()}, flush=True)

    if ('실제', 0) not in done:
        record('실제', 0, run(M))
    if '--only-obs' in sys.argv:
        return

    rho = spearmanr(M).statistic
    C = 2 * np.sin(np.pi * rho / 6)

    def null_a(rng):
        return np.column_stack([rng.permutation(M[:, j]) for j in range(p)])

    def null_b(rng):
        U = norm.cdf(rng.multivariate_normal(np.zeros(p), C, size=n))
        idx = np.minimum((U * n).astype(int), n - 1)
        return np.column_stack([Ms[idx[:, j], j] for j in range(p)])

    rng = np.random.default_rng(SEED)
    for name, f in [('A', null_a), ('B', null_b)]:
        for r in range(1, 21):
            X = f(rng)
            if (name, r) not in done:
                record(name, r, run(X))

    rng = np.random.default_rng(SEED + 1)          # power_12types와 같은 난수 흐름
    for d in [0, 1, 2, 3, 4, 6]:
        for r in range(1, 6):
            X, _ = pw.planted(d, rng)
            if d in (2, 3, 4) and (f'심음_d{d}', r) not in done:
                record(f'심음_d{d}', r, run(X))

    res = pd.DataFrame(rows)
    obs = res[res['자료'] == '실제'].iloc[0]
    print()
    for m, s in BETTER.items():
        a, b = res.loc[res['자료'] == 'A', m], res.loc[res['자료'] == 'B', m]
        ext = (lambda v: v.max()) if s > 0 else (lambda v: v.min())
        over = (lambda v, t: v > t) if s > 0 else (lambda v, t: v < t)
        pa, pb = over(obs[m], ext(a)), over(obs[m], ext(b))
        verdict = '뚜렷한 구조' if pa and pb else '변수 관계 구조' if pa else '연속 분포 구분'
        thr = ext(pd.concat([a, b]))
        det = {d: int(over(res.loc[res['자료'] == f'심음_d{d}', m], thr).sum()) for d in (2, 3, 4)}
        print(f'{m}: 실제 {obs[m]:.3f} | A {a.mean():.3f} ({a.min():.3f}~{a.max():.3f}) 넘음 {pa}, '
              f'더 좋은 횟수 {int((a > obs[m]).sum() if s > 0 else (a < obs[m]).sum())}/20 '
              f'| B {b.mean():.3f} ({b.min():.3f}~{b.max():.3f}) 넘음 {pb}, '
              f'더 좋은 횟수 {int((b > obs[m]).sum() if s > 0 else (b < obs[m]).sum())}/20 '
              f'| 판정 {verdict} | 양성대조 검출 d2/3/4 {det[2]}/{det[3]}/{det[4]}')
    print('완료', flush=True)


if __name__ == '__main__':
    main()
