# -*- coding: utf-8 -*-
"""12유형 양성 대조: 2단계 절차에 가장 유리한 구조를 심어 12유형 귀무 검정의 검정력을 본다.

심는 구조: 대분류 4개 x 세부 3개 = 12덩어리.
  대분류 중심은 name_macro가 찾는 방향으로 두고(거리 평균 d),
  세부 중심은 그 대분류의 SUB_PLAN 2변수 평면에 정삼각형(변 d)으로 둔다.
  각 변수는 순위로 실제 정렬값에 대응 -> 변수별 분포는 실제와 정확히 같음.
  간격 d = 0,1,2,3,4,6, 각 5회.

판정 기준 (실행 전 확정). 기존 귀무 A·B 40회 최댓값 기준:
  주 지표: 12유형 실루엣(7변수) > 0.140 이면 검출
  보조: 세부 가중평균 > 0.687, 대분류 실루엣 > 0.222
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / 'analysis' / '01_clustering'))
import kmedoids_final as kf

HERE = Path(__file__).parent
OUT = HERE / 'power_12types.csv'
SEED = 42
T12, TSUB, TMACRO = 0.140, 0.687, 0.222
F = kf.MODEL_FEATURES
ROLE_DIR = {'G2_고스트레스형': {'stress': 1},
            'G1_운동형': {'aerobic': 1, 'strength_days': 1, 'sedentary_min': -1},
            'G3_좌식외식형': {'sedentary_min': 1, 'eatingout_freq_ord': 1},
            'G0_비활동형': {'aerobic': -1, 'strength_days': -1, 'stress': -1, 'eatingout_freq_ord': -1}}
ROLES = list(ROLE_DIR)

df = pd.read_csv(REPO / 'analysis' / '01_clustering' / kf.CSV, encoding='utf-8-sig')
_, M, _ = kf.build_matrix(df)
n, p = M.shape
Ms = np.sort(M, axis=0)
cov2 = np.load(HERE / 'cov2.npy')


def centers(d):
    mac = np.zeros((4, p))
    for i, r in enumerate(ROLES):
        for c, s in ROLE_DIR[r].items():
            mac[i, F.index(c)] = s
        mac[i] /= np.linalg.norm(mac[i])
    iu = np.triu_indices(4, 1)
    mean_dist = np.linalg.norm(mac[iu[0]] - mac[iu[1]], axis=1).mean()
    mac = mac * d / mean_dist
    tri = np.array([[0, 1], [np.sqrt(3) / 2, -0.5], [-np.sqrt(3) / 2, -0.5]]) * d / np.sqrt(3)  # 변 길이 d
    out = np.zeros((12, p))
    for i, r in enumerate(ROLES):
        cols = [F.index(c) for c in kf.SUB_PLAN[r][0]]
        for s in range(3):
            out[i * 3 + s] = mac[i]
            out[i * 3 + s, cols] += tri[s]
    return out


def planted(d, rng):
    truth = rng.integers(12, size=n)
    Z = rng.multivariate_normal(np.zeros(p), cov2, size=n) + centers(d)[truth]
    R = np.column_stack([rankdata(Z[:, j], method='ordinal') - 1 for j in range(p)]).astype(int)
    return np.column_stack([Ms[R[:, j], j] for j in range(p)]), truth


def sil(D, labels):
    uniq, lb = np.unique(labels, return_inverse=True)
    return float('nan') if len(uniq) < 2 else kf.silhouette(D, lb)


def run(X, truth):
    pca = PCA(n_components=5, random_state=SEED).fit(X)
    D = kf.pairwise_dist(pca.transform(X))
    med, _ = kf.kmedoids(D, 4, seed=SEED, n_init=10)
    labels = np.argmin(D[med], axis=0)
    out = {'대분류_실루엣': kf.silhouette(D, labels), '대분류_ARI': adjusted_rand_score(truth // 3, labels)}
    macro = kf.name_macro(X, labels)
    types = np.empty(n, dtype=int)
    w = 0.0
    for g in range(4):
        cols, k = kf.SUB_PLAN[macro[g]]
        sel = np.flatnonzero(labels == g)
        B = X[np.ix_(sel, [F.index(c) for c in cols])]
        bs = B.std(0)
        Bz = (B - B.mean(0)) / np.where(bs == 0, 1, bs)
        Ds = kf.pairwise_dist(Bz)
        m, _ = kf.kmedoids(Ds, k, seed=SEED, n_init=10)
        sub = np.argmin(Ds[m], axis=0)
        w += sil(Ds, sub) * len(sel) / n
        types[sel] = g * 3 + sub
        del Ds
    out['세부_가중평균'] = w
    out['12유형_ARI'] = adjusted_rand_score(truth, types)
    out['12유형_실루엣_PCA5'] = sil(D, types)
    del D
    D7 = kf.pairwise_dist(X)
    out['12유형_실루엣_7변수'] = sil(D7, types)
    return out


def test():
    rng = np.random.default_rng(SEED)
    c = centers(3)
    iu = np.triu_indices(12, 1)
    dist = np.linalg.norm(c[iu[0]] - c[iu[1]], axis=1)
    print('d=3 중심 간 거리 최소/평균/최대', dist.min().round(2), dist.mean().round(2), dist.max().round(2))
    X, truth = planted(3, rng)
    print('변수별 분포 동일:', bool((np.sort(X, axis=0) == Ms).all()), '| 덩어리 수', len(np.unique(truth)))
    print('d=0 대분류 이름 확인용 평균', np.round(X.mean(0), 3))


def main():
    rows = pd.read_csv(OUT, encoding='utf-8-sig').to_dict('records') if OUT.exists() else []
    done = {(int(r['간격']), int(r['회차'])) for r in rows}
    rng = np.random.default_rng(SEED + 1)
    for d in [0, 1, 2, 3, 4, 6]:
        for r in range(1, 6):
            X, truth = planted(d, rng)
            if (d, r) in done:
                continue
            res = run(X, truth)
            rows.append({'간격': d, '회차': r, **res})
            pd.DataFrame(rows).to_csv(OUT, index=False, encoding='utf-8-sig')
            print(d, r, {k: round(float(v), 3) for k, v in res.items()}, flush=True)
    res = pd.DataFrame(rows)
    print()
    print(res.groupby('간격').mean(numeric_only=True).drop(columns='회차').round(3).to_string())
    print('\n검출 횟수')
    print(pd.DataFrame({'12유형': res.assign(x=res['12유형_실루엣_7변수'] > T12).groupby('간격')['x'].sum(),
                        '세부': res.assign(x=res['세부_가중평균'] > TSUB).groupby('간격')['x'].sum(),
                        '대분류': res.assign(x=res['대분류_실루엣'] > TMACRO).groupby('간격')['x'].sum()}).to_string())
    print('완료', flush=True)


if __name__ == '__main__':
    test() if '--test' in sys.argv else main()
