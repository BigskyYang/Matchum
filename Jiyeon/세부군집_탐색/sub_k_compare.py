# 선택된 세분화 변수 조합에서 k=2~5 비교
import sys, itertools
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score as ari

JY = sys.argv[1]
OUT = sys.argv[2]
sys.path.insert(0, JY)
import kmedoids_final as K

df = pd.read_csv(f'{JY}/{K.CSV}', encoding='utf-8-sig')
X, M, _ = K.build_matrix(df)
macro = pd.read_excel(f'{JY}/{K.OUT_XLSX}', sheet_name='Raw_Data', usecols=['Macro_Cluster'])['Macro_Cluster'].values
F = K.MODEL_FEATURES
rows = []
for g, (cols, _) in K.SUB_PLAN.items():
    sel = np.flatnonzero(macro == g)
    B = M[np.ix_(sel, [F.index(c) for c in cols])]
    Bz = (B - B.mean(0)) / B.std(0)
    D = K.pairwise_dist(Bz)
    for k in range(2, 6):
        labs, costs = [], []
        for s in range(5):
            med, cost = K.kmedoids(D, k, seed=s, n_init=3)
            labs.append(np.argmin(D[med], axis=0)); costs.append(cost)
        lab = labs[0]
        sizes = np.sort(np.bincount(lab, minlength=k))
        rows.append(dict(대분류=g, 변수=' + '.join(K.KOR[c] for c in cols), k=k,
                         실루엣=round(K.silhouette(D, lab), 3),
                         ARI평균=round(float(np.mean([ari(a, b) for a, b in itertools.combinations(labs, 2)])), 3),
                         최소군집비율=round(sizes[0] / len(lab), 3), 최소군집=int(sizes[0]),
                         총거리=round(min(costs), 1)))
        print(rows[-1], flush=True)
pd.DataFrame(rows).to_csv(OUT, index=False, encoding='utf-8-sig')
