# -*- coding: utf-8 -*-
"""
전처리 데이터 -> PCA/UMAP 차원축소 -> CSV 저장

입력 2종
  input7  : 군집에 쓰는 생활습관 7변수 (kmedoids_final.build_matrix 의 전처리 그대로)
  input14 : 흡연/음주 포함 14변수 (수면 연도보정 후 표준화)

안정성 평가용 재실행(시드 5개, 80% 부분표본 3개)은 cache/ 에 npz 로 저장한다.
실행: python 01_make_embeddings.py   (Jiyeon/dimred 안에서 경로 무관)
"""
import os
os.environ.setdefault('NUMBA_NUM_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE.parent))
import kmedoids_final as K

CACHE = HERE / 'cache'
SEEDS = [42, 0, 1, 2, 3]
SUB_SEEDS = [100, 101, 102]
UMAP_SETS = [('umap7_5d', 'input7', 5), ('umap7_10d', 'input7', 10),
             ('umap14_5d', 'input14', 5), ('umap14_10d', 'input14', 10)]
UMAP_ARGS = dict(n_neighbors=30, min_dist=0.0, metric='euclidean')
SENSITIVITY = [('nn15', dict(n_neighbors=15, min_dist=0.0)),
               ('nn50', dict(n_neighbors=50, min_dist=0.0)),
               ('md01', dict(n_neighbors=30, min_dist=0.1))]
_INPUTS = None


def load_inputs():
    df = pd.read_csv(HERE.parent / K.CSV, encoding='utf-8-sig')
    X, M, _ = K.build_matrix(df)
    Z = (X - X.mean(0)) / X.std(0)
    return df, {'input7': M, 'input14': Z}


def run_umap(tag, A, dim, seed, sub_seed=None, **args):
    out = CACHE / f'{tag}.npz'
    if out.exists():
        return f'skip {tag}'
    import umap
    t = time.time()
    if sub_seed is None:
        emb = umap.UMAP(n_components=dim, random_state=seed, **args).fit_transform(A)
        np.savez_compressed(out, emb=emb)
    else:
        n = len(A)
        idx = np.random.default_rng(sub_seed).permutation(n)
        tr, te = idx[:int(n * .8)], idx[int(n * .8):]
        mdl = umap.UMAP(n_components=dim, random_state=seed, **args).fit(A[tr])
        np.savez_compressed(out, tr=tr, te=te, emb_tr=mdl.embedding_, emb_te=mdl.transform(A[te]))
    return f'{tag} {time.time() - t:.0f}s'


def worker(job):
    global _INPUTS
    tag, src, dim, seed, sub_seed, args = job
    if (CACHE / f'{tag}.npz').exists():
        return f'skip {tag}'
    if _INPUTS is None:
        _INPUTS = load_inputs()[1]
    return run_umap(tag, _INPUTS[src], dim, seed, sub_seed, **args)


def save_csv(df, emb, name):
    cols = {f'C{i + 1}': emb[:, i] for i in range(emb.shape[1])}
    pd.DataFrame({'ID': df.ID, 'year': df.year, **cols}).to_csv(HERE / f'{name}.csv', index=False, encoding='utf-8-sig')


def main():
    CACHE.mkdir(exist_ok=True)
    df, inputs = load_inputs()

    for name, src, dim in [('pca7_5d', 'input7', 5), ('pca14_5d', 'input14', 5), ('pca14_10d', 'input14', 10)]:
        p = PCA(n_components=dim, random_state=K.RANDOM_STATE)
        save_csv(df, p.fit_transform(inputs[src]), name)
        print(name, '누적 설명분산', round(p.explained_variance_ratio_.sum(), 3), flush=True)

    jobs = []
    for name, src, dim in UMAP_SETS:
        jobs += [(f'{name}_s{s}', src, dim, s, None, UMAP_ARGS) for s in SEEDS]
        jobs += [(f'{name}_sub{s}', src, dim, 42, s, UMAP_ARGS) for s in SUB_SEEDS]
    jobs += [(f'umap7_5d_{t}', 'input7', 5, 42, None, a) for t, a in SENSITIVITY]
    print('UMAP 작업', len(jobs), flush=True)
    # joblib(loky)은 한글 임시경로에서 실패하므로 표준 프로세스 풀 사용
    with ProcessPoolExecutor(max_workers=4) as ex:
        for f in as_completed([ex.submit(worker, j) for j in jobs]):
            print(f.result(), flush=True)

    for name, _, _ in UMAP_SETS:
        save_csv(df, np.load(CACHE / f'{name}_s42.npz')['emb'], name)
    print('완료', flush=True)


if __name__ == '__main__':
    main()
