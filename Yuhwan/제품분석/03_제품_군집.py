# %% [markdown]
# # [C]-③ 제품 성분 군집 실험: 코사인 계층적 vs k-medoids
# 왜 군집화하나: 제품 75%가 공식 분류상 '복합제품'이라 어떤 유형인지 알 수 없음 → 성분 구성으로 유형을 찾음
# 왜 코사인: 함량 크기보다 '어떤 성분을 어떤 비율로' 담았는지가 유형을 결정. 고함량 단일제가 튀는 것도 줄임
# v3: k 범위 4~20, k-medoids 시작점 10회(재추출 시 5회)로 확대 — v2에서 선택된 k=16이 범위 끝이라 확인용
# 비교 기준 (실험 전에 확정한 순서)
#   1) 안정성: 80% 재추출 10회, 겹치는 제품의 ARI 평균
#   2) 실루엣(코사인), 0.02 미만 차이는 동률
#   3) 크기: 최대 군집 ≤ 50%, 최소 군집 ≥ 10개
#   4) 해석: 군집별 상위 3성분이 서로 겹치지 않을 것
# 정량 % 변환 비교: cap300 = min(%,300)/100, log = log1p(%/100), cap100 = min(%,100)/100  (함유 여부 0/1은 그대로)
# ※ cap100은 1차 실험 후 추가: cap300/log에서 비타민D(수천%)가 방향을 지배해 칼슘·마그네슘 복합제가 'D 단일형'으로 흡수됨
#    cap100은 '기준치를 채웠는지'만 보고 함유 여부(0/1)와 크기를 맞춤. 용량 크기는 04 장르 점수에서 따로 반영

# %%
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import linkage, fcluster, dendrogram
from scipy.spatial.distance import pdist, squareform
from sklearn.metrics import silhouette_score, adjusted_rand_score

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '제품분석' / 'output'
rng = np.random.default_rng(42)

p = pd.read_csv(OUT / 'product_features.csv', encoding='utf-8-sig')
p = p[p['대상제품'] == 1].reset_index(drop=True)
V = [c for c in p.columns if c.startswith('v_')]
QV = ['v_' + q for q in ['단백질', '식이섬유', '칼슘', '철', '비타민 A', '비타민 D', '비타민 C', '티아민', '리보플라빈', '니아신']]
print('제품', len(p), '| 차원', len(V))


def transform(kind):
    X = p[V].astype(float).copy()
    if kind == 'log':
        X[QV] = np.log1p(X[QV] / 100)
    else:
        cap = 300 if kind == 'cap300' else 100
        X[QV] = np.minimum(X[QV], cap) / 100
    return X.values


def kmedoids(D, k, n_init=3, max_iter=50, seed=0):
    r = np.random.default_rng(seed)
    best = (np.inf, None)
    for _ in range(n_init):
        # k-medoids++ 초기화
        med = [r.integers(len(D))]
        for _ in range(k - 1):
            dmin = D[:, med].min(axis=1)
            med.append(r.choice(len(D), p=dmin ** 2 / (dmin ** 2).sum()))
        med = np.array(med)
        for _ in range(max_iter):
            lab = D[:, med].argmin(axis=1)
            new = np.array([np.where(lab == j)[0][D[np.ix_(lab == j, lab == j)].sum(axis=1).argmin()] if (lab == j).any() else med[j]
                            for j in range(k)])
            if set(new) == set(med):
                break
            med = new
        lab = D[:, med].argmin(axis=1)
        cost = D[np.arange(len(D)), med[lab]].sum()
        if cost < best[0]:
            best = (cost, (lab, med))
    return best[1]


def run(method, D, k, seed=0, n_init=10):
    if method == 'hier':
        return fcluster(linkage(squareform(D, checks=False), 'average'), k, 'maxclust') - 1, None
    return kmedoids(D, k, n_init=n_init, seed=seed)


def top3(X, lab):
    return {j: tuple(np.array([c[2:] for c in V])[np.argsort(-X[lab == j].mean(axis=0))[:3]]) for j in np.unique(lab)}


# 주요 성분(제품 100개 이상)은 어느 유형이든 상위 3성분에 나와야 함 (※ 1차 실험 후 추가한 해석 기준)
MAJOR = {c[2:] for c in V if (p[c] > 0).sum() >= 100}
print('주요 성분', sorted(MAJOR))

# %% 실험
rows, store = [], {}
for kind in ['cap100', 'cap300', 'log']:
    X = transform(kind)
    D = squareform(pdist(X, 'cosine'))
    D = np.nan_to_num(D, nan=1.0)
    for method in ['hier', 'kmedoids']:
        for k in range(4, 21):
            lab, med = run(method, D, k)
            sizes = np.bincount(lab)
            aris = []
            for b in range(10):
                idx = np.sort(rng.choice(len(D), int(0.8 * len(D)), replace=False))
                lb, _ = run(method, D[np.ix_(idx, idx)], k, seed=b + 1, n_init=5)
                aris.append(adjusted_rand_score(lab[idx], lb))
            t3 = top3(X, lab)
            covered = set(sum(map(list, t3.values()), []))
            rows.append(dict(누락주요성분=','.join(sorted(MAJOR - covered)), 변환=kind, 방법=method, k=k, ARI=np.mean(aris), 실루엣=silhouette_score(D, lab, metric='precomputed'),
                             최대비율=sizes.max() / len(lab), 최소크기=sizes.min(), 상위3중복=len(t3) - len(set(t3.values()))))
            store[(kind, method, k)] = (lab, med)
        print(kind, method, 'done')
res = pd.DataFrame(rows)
res['크기OK'] = (res['최대비율'] <= 0.5) & (res['최소크기'] >= 10)
res['해석OK'] = (res['상위3중복'] == 0) & (res['누락주요성분'] == '')
res.to_csv(OUT / '제품군집_실험결과.csv', index=False, encoding='utf-8-sig')
pd.set_option('display.width', 200)
print(res.round(3).to_string())

# %% 선택: 크기·해석 조건 통과 → ARI 최대 → (ARI 0.02 이내 동률이면) 실루엣 최대
ok = res[res['크기OK'] & res['해석OK']]
cand = ok[ok['ARI'] >= ok['ARI'].max() - 0.02] if len(ok) else res
best = cand.sort_values('실루엣', ascending=False).iloc[0]
print('\n선택:', best[['변환', '방법', 'k', 'ARI', '실루엣', '최대비율', '최소크기']].to_dict())
lab, med = store[(best['변환'], best['방법'], int(best['k']))]
X = transform(best['변환'])
D = np.nan_to_num(squareform(pdist(X, 'cosine')), nan=1.0)
if med is None:   # 계층적이면 군집 안에서 거리 합이 가장 작은 제품을 대표(medoid)로
    med = np.array([np.where(lab == j)[0][D[np.ix_(lab == j, lab == j)].sum(axis=1).argmin()] for j in np.unique(lab)])
p['제품유형'] = lab
p['군집변환'] = best['변환']
p['대표거리'] = D[np.arange(len(p)), med[lab]]

# %% 유형 이름: 평균 구성 상위 성분으로 자동 생성 + 대표 제품
names = {}
summ = []
for j in np.unique(lab):
    m = X[lab == j].mean(axis=0)
    comp = [V[i][2:] for i in np.argsort(-m) if m[i] >= 0.25 * m.max()][:4]
    names[j] = '·'.join(comp) + ('형' if len(comp) > 1 else ' 단일형')
    sub = p[lab == j]
    rep = p.iloc[med[j]]
    summ.append(dict(유형=j, 이름=names[j], 제품수=int((lab == j).sum()), 평균성분수=sub['구성성분수'].mean(),
                     대표제품=rep['식품명'], 대표식품명_최빈=sub['대표식품명'].mode().iat[0]))
p['제품유형명'] = p['제품유형'].map(names)
summ = pd.DataFrame(summ).sort_values('제품수', ascending=False)
print(summ.round(1).to_string(index=False))
summ.to_csv(OUT / '제품유형_요약.csv', index=False, encoding='utf-8-sig')
p.to_csv(OUT / 'product_types.csv', index=False, encoding='utf-8-sig')

# 유형별 평균 구성 히트맵
prof = pd.DataFrame(X, columns=[c[2:] for c in V]).groupby(lab).mean()
prof.index = [names[j] for j in prof.index]
fig, ax = plt.subplots(figsize=(14, 0.45 * len(prof) + 2))
import seaborn as sns
sns.heatmap(prof, cmap='Blues', annot=True, fmt='.1f', ax=ax)
ax.set_title(f"제품 유형별 평균 구성 ({best['방법']}, {best['변환']}, k={int(best['k'])})")
plt.tight_layout(); plt.savefig(OUT / 'fig_제품유형_구성.png', dpi=150)
