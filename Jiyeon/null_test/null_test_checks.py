# -*- coding: utf-8 -*-
"""귀무 검정 점검 (대분류 k=4 기준).

--diag : 무작위 B가 실제 자료를 얼마나 본뜨는지 (빠름)
기본   : 군집화 실행
  부트스트랩 10회 : 실제 자료 표본 변동 범위
  B2 10회        : 상관을 표본 순위상관에 맞춰 보정한 B
  양성 대조      : 잠재 공간에 4덩어리를 심고 변수별 분포는 실제와 똑같이 맞춘 자료.
                   덩어리 간격 d = 0,1,2,3,4,6 (잠재 SD 단위), 각 5회.

양성 대조 판정 기준 (실행 전 확정):
  실루엣 > 0.222 (기존 A·B 20회 최댓값) 이면 '구조 있음'으로 검출.
  검정력 있음 = 심은 덩어리가 복원(ARI >= 0.8)되는 간격에서 5회 모두 검출.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm, rankdata, spearmanr
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'Jiyeon'))
import kmedoids_final as kf

OUT = Path(__file__).parent / 'null_test_checks.csv'
SEED, THRESH = 42, 0.222
NAMES = kf.MODEL_FEATURES

df = pd.read_csv(REPO / 'Jiyeon' / kf.CSV, encoding='utf-8-sig')
_, M, _ = kf.build_matrix(df)
n, p = M.shape
Ms = np.sort(M, axis=0)
rho = spearmanr(M).statistic
C = 2 * np.sin(np.pi * rho / 6)


def to_margins(U):
    idx = np.minimum((U * n).astype(int), n - 1)
    return np.column_stack([Ms[idx[:, j], j] for j in range(p)])


def null_b(rng, cov=C, size=n):
    U = norm.cdf(rng.multivariate_normal(np.zeros(p), cov, size=size))
    idx = np.minimum((U * n).astype(int), n - 1)
    return np.column_stack([Ms[idx[:, j], j] for j in range(p)])


def null_a(rng):
    return np.column_stack([rng.permutation(M[:, j]) for j in range(p)])


def calibrate(iters=25, size=100_000):
    """표본 순위상관(동점 포함)이 실제와 같아지도록 잠재 상관을 조정."""
    rng = np.random.default_rng(SEED)
    cov = C.copy()
    for _ in range(iters):
        r = spearmanr(null_b(rng, cov, size)).statistic
        cov = cov + (rho - r)
        w, v = np.linalg.eigh(cov)
        cov = (v * np.clip(w, 1e-4, None)) @ v.T
        d = np.sqrt(np.diag(cov))
        cov = cov / np.outer(d, d)
    return cov


def tv_pairs(X, Y, bins=5):
    """변수 쌍별 결합분포 차이(총변동거리). 값이 많은 변수는 실제 분위수로 구간화."""
    out = []
    edges = [np.unique(np.quantile(M[:, j], np.linspace(0, 1, bins + 1)[1:-1])) for j in range(p)]
    bx = np.column_stack([np.searchsorted(edges[j], X[:, j], side='left') for j in range(p)])
    by = np.column_stack([np.searchsorted(edges[j], Y[:, j], side='left') for j in range(p)])
    for i in range(p):
        for j in range(i + 1, p):
            a = pd.crosstab(bx[:, i], bx[:, j], normalize=True)
            b = pd.crosstab(by[:, i], by[:, j], normalize=True)
            out.append((NAMES[i], NAMES[j], 0.5 * a.sub(b, fill_value=0).abs().to_numpy().sum()))
    return sorted(out, key=lambda t: -t[2])


def diag():
    print('변수별 고유값 수와 최빈값 비율')
    for j, c in enumerate(NAMES):
        v, k = np.unique(np.round(M[:, j], 6), return_counts=True)
        print(f'  {c}: 고유값 {len(v)}, 최빈 {k.max() / n:.1%}')

    rng = np.random.default_rng(SEED)
    cov2 = calibrate()
    np.save(Path(__file__).parent / 'cov2.npy', cov2)
    iu = np.triu_indices(p, 1)
    samples = {'A': [null_a(rng) for _ in range(3)],
               'B': [null_b(rng) for _ in range(5)],
               'B2': [null_b(rng, cov2) for _ in range(5)]}
    print('\n순위상관 재현 (실제와의 차이)')
    for k in ['B', 'B2']:
        r = np.mean([spearmanr(x).statistic for x in samples[k]], axis=0)
        d = (r - rho)[iu]
        print(f'  {k}: 평균 |차이| {np.abs(d).mean():.4f}, 최대 |차이| {np.abs(d).max():.4f}, 부호 있는 평균 {d.mean():+.4f}')
    print('  실제 |순위상관| 평균', round(np.abs(rho[iu]).mean(), 4), '최대', round(np.abs(rho[iu]).max(), 4))
    for i, j in zip(*iu):
        print(f'    {NAMES[i]}-{NAMES[j]}: 실제 {rho[i, j]:+.3f}')

    print('\nPCA 설명분산 비율 (1~7축)')
    print('  실제', np.round(PCA().fit(M).explained_variance_ratio_, 3))
    for k, xs in samples.items():
        print(f'  {k}  ', np.round(np.mean([PCA().fit(x).explained_variance_ratio_ for x in xs], axis=0), 3))

    print('\n변수 쌍 결합분포 차이: 실제 vs B (상위 8, 총변동거리)')
    base = np.mean([t[2] for t in tv_pairs(samples['B'][0], samples['B'][1])])
    print(f'  참고: 표본 잡음 수준(B끼리) 평균 {base:.4f}')
    for a, b, v in tv_pairs(M, samples['B'][0])[:8]:
        print(f'  {a}-{b}: {v:.4f}')

    print('\n실제 vs B 첨도형 차이: PCA1·2 점수 사분위 폭 / 표준편차')
    for label, x in [('실제', M), ('B', samples['B'][0])]:
        q = PCA(n_components=2).fit_transform(x)
        print(f'  {label}: ', [round(float((np.quantile(q[:, i], .75) - np.quantile(q[:, i], .25)) / q[:, i].std()), 3) for i in range(2)])


def run(X):
    pca = PCA(n_components=5, random_state=SEED).fit(X)
    D = kf.pairwise_dist(pca.transform(X))
    med, cost = kf.kmedoids(D, 4, seed=SEED, n_init=10)
    lb = np.argmin(D[med], axis=0)
    return dict(실루엣=kf.silhouette(D, lb), 평균거리=cost / n, 최소군집=np.bincount(lb, minlength=4).min() / n), lb


def planted(d, rng, cov):
    Q, _ = np.linalg.qr(rng.standard_normal((p, 4)))
    centers = Q.T * d / np.sqrt(2)                     # 네 중심 사이 거리 = d
    truth = rng.integers(4, size=n)
    Z = rng.multivariate_normal(np.zeros(p), cov, size=n) + centers[truth]
    # 순위를 실제 정렬값에 대응 -> 변수별 분포가 실제와 정확히 같음
    R = np.column_stack([rankdata(Z[:, j], method='ordinal') - 1 for j in range(p)]).astype(int)
    return np.column_stack([Ms[R[:, j], j] for j in range(p)]), truth


def main():
    cov2 = np.load(Path(__file__).parent / 'cov2.npy')
    rows = pd.read_csv(OUT, encoding='utf-8-sig').to_dict('records') if OUT.exists() else []
    done = {(r['자료'], int(r['회차'])) for r in rows}

    def record(name, r, res):
        rows.append({'자료': name, '회차': r, **res})
        pd.DataFrame(rows).to_csv(OUT, index=False, encoding='utf-8-sig')
        print(name, r, {k: round(float(v), 3) for k, v in res.items()}, flush=True)

    if ('실제', 0) not in done:
        record('실제', 0, run(M)[0])

    rng = np.random.default_rng(SEED)
    for r in range(1, 11):
        idx = rng.integers(n, size=n)
        if ('부트스트랩', r) not in done:
            record('부트스트랩', r, run(M[idx])[0])
    for r in range(1, 11):
        X = null_b(rng, cov2)
        if ('B2', r) not in done:
            record('B2', r, run(X)[0])
    for d in [0, 1, 2, 3, 4, 6]:
        for r in range(1, 6):
            X, truth = planted(d, rng, cov2)
            if (f'심음_d{d}', r) not in done:
                res, lb = run(X)
                res['ARI'] = adjusted_rand_score(truth, lb)
                record(f'심음_d{d}', r, res)

    res = pd.DataFrame(rows)
    print()
    print(res.groupby('자료', sort=False)[['실루엣', '평균거리', '최소군집', 'ARI']].agg(['mean', 'min', 'max']).round(3).to_string())
    pl = res[res['자료'].str.startswith('심음')]
    print('\n검출 횟수 (실루엣 >', THRESH, ')')
    print(pl.assign(검출=pl['실루엣'] > THRESH).groupby('자료', sort=False)['검출'].sum().to_string())
    print('완료', flush=True)


if __name__ == '__main__':
    diag() if '--diag' in sys.argv else main()
