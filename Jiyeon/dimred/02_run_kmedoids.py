# -*- coding: utf-8 -*-
"""
차원축소 CSV -> K-Medoids(k=4)
알고리즘은 kmedoids_final.py 와 동일(k-medoids++ -> swap -> voronoi). 모든 조건 n_init=5 로 통일.
작업마다 cache/km_*.npz 저장 -> 중단 후 재실행하면 이어서 진행.
"""
import os
os.environ.setdefault('OMP_NUM_THREADS', '2')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '2')
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score as ari

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE.parent))
import kmedoids_final as K

CACHE = HERE / 'cache'
K_ = 4
N_INIT = 5
SEEDS = [42, 0, 1, 2, 3]
SUB_SEEDS = [100, 101, 102]
PCA_SETS = {'pca7_5d': ('input7', 5), 'pca14_5d': ('input14', 5), 'pca14_10d': ('input14', 10)}
UMAP_SETS = ['umap7_5d', 'umap7_10d', 'umap14_5d', 'umap14_10d']
SENS = ['umap7_5d_nn15', 'umap7_5d_nn50', 'umap7_5d_md01']


def read_csv_emb(name):
    e = pd.read_csv(HERE / f'{name}.csv', encoding='utf-8-sig')
    return e[[c for c in e.columns if c.startswith('C')]].values


def inputs():
    df = pd.read_csv(HERE.parent / K.CSV, encoding='utf-8-sig')
    X, M, _ = K.build_matrix(df)
    return {'input7': M, 'input14': (X - X.mean(0)) / X.std(0)}


def fit(E, seed):
    """K.kmedoids 와 같은 순서로 시작점을 돌리되, 시작점별 비용과 라벨도 남긴다."""
    D = K.pairwise_dist(E)
    rng = np.random.default_rng(seed)
    runs = []
    for _ in range(N_INIT):
        med = K.voronoi(D, K.swap_polish(D, K.kmpp_init(D, K_, rng)))
        runs.append((K.total_cost(D, med), med, np.argmin(D[med], axis=0)))
    best = min(runs, key=lambda r: r[0])
    out = dict(labels=best[2], medoids=best[1], cost=best[0], medoid_xy=E[best[1]],
               start_cost=np.array([r[0] for r in runs]),
               start_ari=np.array([ari(best[2], r[2]) for r in runs]),
               sil_own=K.silhouette(D, best[2]))
    return out


def kscan(E, name):
    """k 후보 비교 (단일 시작, 참고용)."""
    D = K.pairwise_dist(E)
    rows = []
    for k in range(3, 9):
        med = K.voronoi(D, K.swap_polish(D, K.kmpp_init(D, k, np.random.default_rng(42))))
        rows.append((k, K.total_cost(D, med), K.silhouette(D, np.argmin(D[med], axis=0))))
    return np.array(rows)


def task(job):
    kind, name, seed = job
    out = CACHE / f'km_{kind}_{name}_{seed}.npz'
    if out.exists():
        return f'skip {out.name}'
    t = time.time()
    if kind == 'kscan':
        np.savez_compressed(out, table=kscan(read_csv_emb(name), name))
    elif kind == 'seed':
        # UMAP 은 시드마다 임베딩도 새로 만든 것을 사용 (파이프라인 전체 안정성)
        if name in PCA_SETS or seed == 42:
            E = read_csv_emb(name)
        else:
            E = np.load(CACHE / f'{name}_s{seed}.npz')['emb']
        np.savez_compressed(out, **fit(E, seed))
    elif kind == 'kmonly':  # 임베딩 고정(시드42), K-Medoids 시드만 변경
        np.savez_compressed(out, **fit(read_csv_emb(name), seed))
    elif kind == 'sens':
        np.savez_compressed(out, **fit(np.load(CACHE / f'{name}.npz')['emb'], 42))
    elif kind == 'sub':
        if name in PCA_SETS:
            src, dim = PCA_SETS[name]
            A = inputs()[src]
            idx = np.random.default_rng(seed).permutation(len(A))
            tr, te = idx[:int(len(A) * .8)], idx[int(len(A) * .8):]
            p = PCA(n_components=dim, random_state=42).fit(A[tr])
            Etr, Ete = p.transform(A[tr]), p.transform(A[te])
        else:
            z = np.load(CACHE / f'{name}_sub{seed}.npz')
            tr, te, Etr, Ete = z['tr'], z['te'], z['emb_tr'], z['emb_te']
        r = fit(Etr, 42)
        r['labels_te'] = np.argmin(cdist(Ete, r['medoid_xy']), axis=1)
        np.savez_compressed(out, tr=tr, te=te, **r)
    return f'{out.name} {time.time() - t:.0f}s'


def main():
    allsets = list(PCA_SETS) + UMAP_SETS
    jobs = [('seed', n, s) for n in allsets for s in SEEDS]
    jobs += [('kmonly', n, s) for n in UMAP_SETS for s in (0, 1)]
    jobs += [('sub', n, s) for n in allsets for s in SUB_SEEDS]
    jobs += [('sens', n, 42) for n in SENS]
    jobs += [('kscan', n, 0) for n in allsets]
    print('K-Medoids 작업', len(jobs), flush=True)
    with ProcessPoolExecutor(max_workers=3) as ex:
        for f in as_completed([ex.submit(task, j) for j in jobs]):
            print(f.result(), flush=True)
    print('완료', flush=True)


if __name__ == '__main__':
    main()
