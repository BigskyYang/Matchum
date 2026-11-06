# 대분류별 세부 군집 변수 조합 전수 탐색 재현
# usage: python sub_search.py <Jiyeon dir> <out csv> [group filter] [max combo size]
import sys, time, itertools
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score as ari

JY = sys.argv[1]
OUT = sys.argv[2]
ONLY = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] != 'all' else None
MAXC = int(sys.argv[4]) if len(sys.argv) > 4 else 3
sys.path.insert(0, JY)
import kmedoids_final as K

SEEDS = [0, 1, 2, 3, 4]
N_INIT = 3

df = pd.read_csv(f'{JY}/{K.CSV}', encoding='utf-8-sig')
X, M, _ = K.build_matrix(df)
raw = pd.read_excel(f'{JY}/{K.OUT_XLSX}', sheet_name='Raw_Data', usecols=['Macro_Cluster', 'Type_Code'])
assert len(raw) == len(M)
macro = raw['Macro_Cluster'].values

F = K.MODEL_FEATURES
rows, sd_rows = [], []
for g in sorted(set(macro)):
    if ONLY and not g.startswith(ONLY):
        continue
    sel = np.flatnonzero(macro == g)
    Mg = M[sel]
    sd_rows.append({'대분류': g, **{K.KOR[c]: round(float(Mg[:, i].std()), 2) for i, c in enumerate(F)}})
    for r in range(2, MAXC + 1):
        for cols in itertools.combinations(F, r):
            t = time.time()
            B = Mg[:, [F.index(c) for c in cols]]
            Bz = (B - B.mean(0)) / B.std(0)
            D = K.pairwise_dist(Bz)
            labs = []
            for s in SEEDS:
                med, _ = K.kmedoids(D, 3, seed=s, n_init=N_INIT)
                labs.append(np.argmin(D[med], axis=0))
            aris = [ari(a, b) for a, b in itertools.combinations(labs, 2)]
            # 대표 해: 시드 42 와 같은 방식(최소 비용) 대신 첫 시드 사용
            lab = labs[0]
            sizes = np.sort(np.bincount(lab, minlength=3))
            # 기여도 = 각 변수의 η² (세부 군집 간 분산 / 전체 분산)
            eta = []
            for j in range(Bz.shape[1]):
                v = Bz[:, j]
                bss = sum((lab == c).sum() * (v[lab == c].mean() - v.mean()) ** 2 for c in range(3))
                eta.append(bss / ((v - v.mean()) ** 2).sum())
            rows.append(dict(대분류=g, 변수=' + '.join(K.KOR[c] for c in cols), 변수수=r,
                             실루엣=round(K.silhouette(D, lab), 3),
                             ARI평균=round(float(np.mean(aris)), 3), ARI최소=round(float(np.min(aris)), 3),
                             최소군집비율=round(sizes[0] / len(lab), 3),
                             군집크기='/'.join(map(str, sizes[::-1])),
                             기여도='/'.join(f'{e:.2f}' for e in eta),
                             이진변수포함=('aerobic' in cols or 'stress' in cols)))
            print(g, rows[-1]['변수'], rows[-1]['실루엣'], rows[-1]['ARI평균'], rows[-1]['군집크기'],
                  rows[-1]['기여도'], f'{time.time() - t:.1f}s', flush=True)

pd.DataFrame(rows).to_csv(OUT, index=False, encoding='utf-8-sig')
pd.DataFrame(sd_rows).to_csv(OUT.replace('.csv', '_sd.csv'), index=False, encoding='utf-8-sig')
print('done')
