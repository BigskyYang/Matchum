# 지연님 2단계 유형(대분류 4개 × 세부 3개) 학습·배정 — 05_jiyeon_improved.py와 04_compare_jiyeon.py가 같이 쓴다
#
# 전처리·변수·SUB_PLAN·대분류 역할 정하기(name_macro)는 지연님 analysis/01_clustering/kmedoids_final.py를 그대로 불러 쓴다.
# 바꾼 것은 세부 유형 번호를 고정하는 규칙뿐이다 (method='kmeans'는 비교 실험용).
import importlib.util

import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

from common import REPO

_spec = importlib.util.spec_from_file_location('jiyeon_km', REPO / 'analysis' / '01_clustering' / 'kmedoids_final.py')
jm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(jm)

# 대분류 역할 → 짧은 코드 (유형 ID 접두어)
ROLE_CODE = {'G0_비활동형': 'N', 'G1_운동형': 'A', 'G2_고스트레스형': 'S', 'G3_좌식외식형': 'O'}


def fit_pca(M):
    return PCA(n_components=5, random_state=jm.RANDOM_STATE).fit(M)


def _centers(X, k, seed, method, n_init):
    """X에서 k개 중심과 라벨. kmedoids는 지연님 구현(PAM swap), kmeans는 sklearn."""
    if method == 'kmedoids':
        D = jm.pairwise_dist(X)
        med, _ = jm.kmedoids(D, k, seed=seed, n_init=n_init)
        return X[med], np.argmin(D[med], axis=0)
    km = KMeans(n_clusters=k, n_init=n_init, random_state=seed).fit(X)
    return km.cluster_centers_, km.labels_


def nearest(V, C):
    return np.argmin(((V[:, None, :] - C[None]) ** 2).sum(2), axis=1)


def fit(Q, M, idx, seed, method='kmedoids', n_init=10):
    """idx 사람으로 학습한 모델(dict). 세부 유형 번호는 세분화 변수 첫째 → 둘째 값이 작은 순으로 1·2·3."""
    Qi, Mi = Q[idx], M[idx]
    C, lab = _centers(Qi, 4, seed, method, n_init)
    role = jm.name_macro(Mi, lab)
    model = {'macro': {}, 'sub': {}}
    for g in range(4):
        r = role[g]
        model['macro'][r] = C[g]
        cols, k = jm.SUB_PLAN[r]
        ci = [jm.MODEL_FEATURES.index(c) for c in cols]
        B = Mi[lab == g][:, ci]
        bm, bs = B.mean(0), B.std(0)
        SC, _ = _centers((B - bm) / bs, k, seed, method, n_init)
        SC = SC[np.lexsort(SC.T[::-1])]
        model['sub'][r] = {'features': cols, 'cols': ci, 'mean': bm, 'std': bs, 'centers': SC}
    return model


def assign(model, Q, M):
    """(세부 유형 ID, 대분류 역할) 배열. ID 예: A2 = 운동형의 2번째 세부 유형."""
    roles = list(model['macro'])
    macro = np.array(roles)[nearest(Q, np.array([model['macro'][r] for r in roles]))]
    out = np.empty(len(Q), dtype=object)
    for r in roles:
        sel = np.flatnonzero(macro == r)
        if not len(sel):
            continue
        s = model['sub'][r]
        V = (M[np.ix_(sel, s['cols'])] - s['mean']) / s['std']
        out[sel] = [f'{ROLE_CODE[r]}{i + 1}' for i in nearest(V, s['centers'])]
    return out, macro
