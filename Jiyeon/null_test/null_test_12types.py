# -*- coding: utf-8 -*-
"""12유형 귀무 검정. Yuhwan/영양분석/15_군집_귀무검정.py를 2단계까지 확장.

같은 가짜 자료 생성(시드 42, A 20회 -> B 20회)을 쓰고, 가짜 자료마다 2단계 전체를 다시 실행한다.
SUB_PLAN(대분류별 세분화 변수)은 실제 자료에서 탐색해 고른 것을 고정해서 쓴다.

주 지표: 12유형 실루엣(7변수 공간). 보조: PCA5 공간, 대분류별 세부 실루엣(각자의 2변수 공간).
판정 기준(실행 전 확정, 대분류 검정과 동일):
  A·B 20회 최댓값을 모두 넘음 -> 우연보다 뚜렷한 구조
  A만 넘음 -> 변수 간 관계에서 오는 구조
  둘 다 못 넘음 -> 연속 분포를 나눈 구분
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm, spearmanr
from sklearn.decomposition import PCA

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'Jiyeon'))
import kmedoids_final as kf

OUT = Path(__file__).parent / 'null_test_12types.csv'
R, SEED = 20, 42
ROLES = ['G0_비활동형', 'G1_운동형', 'G2_고스트레스형', 'G3_좌식외식형']


def sil(D, labels):
    """빈 군집이 생겨도 계산되도록 번호를 다시 매긴다. 군집이 1개면 NaN."""
    uniq, lb = np.unique(labels, return_inverse=True)
    return float('nan') if len(uniq) < 2 else kf.silhouette(D, lb)


def run(M):
    out = {}
    pca = PCA(n_components=5, random_state=SEED).fit(M)
    D = kf.pairwise_dist(pca.transform(M))
    med, _ = kf.kmedoids(D, 4, seed=SEED, n_init=10)
    labels = np.argmin(D[med], axis=0)
    out['대분류_실루엣'] = kf.silhouette(D, labels)
    macro = kf.name_macro(M, labels)

    types = np.empty(len(M), dtype=int)
    weighted, constant = 0.0, 0
    for g in range(4):
        role = macro[g]
        cols, k = kf.SUB_PLAN[role]
        sel = np.flatnonzero(labels == g)
        B = M[np.ix_(sel, [kf.MODEL_FEATURES.index(c) for c in cols])]
        bs = B.std(0)
        constant += int((bs == 0).sum())          # 가짜 자료에서 대분류 안 변수가 상수가 되는 경우
        Bz = (B - B.mean(0)) / np.where(bs == 0, 1, bs)
        Ds = kf.pairwise_dist(Bz)
        m, _ = kf.kmedoids(Ds, k, seed=SEED, n_init=10)
        sub = np.argmin(Ds[m], axis=0)
        s = sil(Ds, sub)
        out[f'세부_{role}'] = s
        weighted += s * len(sel) / len(M)
        types[sel] = g * 3 + sub
        del Ds
    out['세부_가중평균'] = weighted
    out['상수변수수'] = constant
    out['유형수'] = len(np.unique(types))
    out['최소유형비율'] = np.bincount(types).min() / len(M) if out['유형수'] == 12 else 0.0
    out['12유형_실루엣_PCA5'] = sil(D, types)
    del D
    D7 = kf.pairwise_dist(M)
    out['12유형_실루엣_7변수'] = sil(D7, types)
    return out


def main():
    only_obs = '--only-obs' in sys.argv
    df = pd.read_csv(REPO / 'Jiyeon' / kf.CSV, encoding='utf-8-sig')
    _, M, _ = kf.build_matrix(df)
    print('n =', len(M), flush=True)

    rows = pd.read_csv(OUT, encoding='utf-8-sig').to_dict('records') if OUT.exists() else []
    done = {(r['자료'], int(r['회차'])) for r in rows}

    def save():
        pd.DataFrame(rows).to_csv(OUT, index=False, encoding='utf-8-sig')

    t0 = time.time()
    if ('실제', 0) not in done:
        rows.append({'자료': '실제', '회차': 0, **run(M)})
        save()
    print('실제', {k: round(v, 3) for k, v in rows[0].items() if k not in ('자료', '회차')},
          f'({time.time() - t0:.0f}초)', flush=True)
    if only_obs:
        return

    rho = spearmanr(M).statistic
    C = 2 * np.sin(np.pi * rho / 6)
    Ms = np.sort(M, axis=0)

    def null_a(rng):
        return np.column_stack([rng.permutation(M[:, j]) for j in range(M.shape[1])])

    def null_b(rng):
        U = norm.cdf(rng.multivariate_normal(np.zeros(M.shape[1]), C, size=len(M)))
        idx = np.minimum((U * len(M)).astype(int), len(M) - 1)
        return np.column_stack([Ms[idx[:, j], j] for j in range(M.shape[1])])

    rng = np.random.default_rng(SEED)
    for name, f in [('귀무A_상관없음', null_a), ('귀무B_상관유지', null_b)]:
        for r in range(1, R + 1):
            X = f(rng)                            # 재개해도 난수 흐름이 같도록 항상 생성
            if (name, r) in done:
                continue
            res = run(X)
            rows.append({'자료': name, '회차': r, **res})
            save()
            print(f"{name} {r:2d}: 대분류 {res['대분류_실루엣']:.3f} 12유형(7변수) {res['12유형_실루엣_7변수']:.3f} "
                  f"12유형(PCA5) {res['12유형_실루엣_PCA5']:.3f} 세부 {res['세부_가중평균']:.3f} "
                  f"상수 {res['상수변수수']} ({time.time() - t0:.0f}초)", flush=True)

    res = pd.DataFrame(rows)
    obs = res[res['자료'] == '실제'].iloc[0]
    metrics = ['대분류_실루엣', '12유형_실루엣_7변수', '12유형_실루엣_PCA5', '세부_가중평균'] + [f'세부_{r}' for r in ROLES]
    print()
    for name in ['귀무A_상관없음', '귀무B_상관유지']:
        sub = res[res['자료'] == name]
        print(name)
        for m in metrics:
            s = sub[m].dropna()
            print(f'  {m}: 실제 {obs[m]:.3f} | 평균 {s.mean():.3f} SD {s.std():.3f} 범위 {s.min():.3f}~{s.max():.3f} '
                  f'| 실제 이상 {(s >= obs[m]).sum()}/{len(s)} | 경험적p {(1 + (s >= obs[m]).sum()) / (1 + len(s)):.3f}')
        print('  상수변수 발생 회차:', int((sub['상수변수수'] > 0).sum()), '/ 유형수 12 미만 회차:', int((sub['유형수'] < 12).sum()),
              f"/ 최소유형비율 평균 {sub['최소유형비율'].mean():.3f} (실제 {obs['최소유형비율']:.3f})")
    print('완료', flush=True)


if __name__ == '__main__':
    main()
