# %% [markdown]
# # 군집 덩어리 귀무 검정: 실루엣 0.163이 '구조가 없는 자료'보다 높은가
# 질문: 지연님 대분류(7변수 → PCA5 → k-medoids k=4)의 실루엣 0.163은 낮은 값이다.
#       이것이 '뚜렷한 덩어리가 전혀 없는 자료'에서도 나오는 값인지 확인한다.
# 방법: 지연님 kmedoids_final.py의 build_matrix·kmedoids·silhouette를 그대로 불러 같은 절차를 무작위 자료에 반복
#   귀무 A (상관 없음): 7변수를 각각 따로 섞음 → 변수별 분포는 같고 변수 사이 관계만 없앰
#   귀무 B (상관 유지): 가우시안 코퓰라 — 변수별 분포(이산값 포함)와 순위상관은 같고, 덩어리(다봉성)만 없앰
#   각 20회, 같은 PCA(5)·k=4·n_init=10
# 판정 기준 (결과 보기 전에 확정)
#   실제 실루엣 > 귀무 20회 최댓값 (경험적 p < 1/21 ≈ 0.048) → "우연보다 뚜렷한 구조"
#   귀무 A만 넘고 B는 못 넘음 → "변수 간 상관에서 오는 구조일 뿐, 따로 떨어진 덩어리는 아님"
#   둘 다 못 넘음 → "연속 분포를 나눈 구분" (현재 보고서 표현 유지)

# %%
import sys
import time
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import norm, spearmanr
from sklearn.decomposition import PCA
from common import ROOT, OUT

REPO = ROOT.parent if (ROOT.parent / 'Jiyeon').exists() else ROOT.parent / 'Matchum'
sys.path.insert(0, str(REPO / 'Jiyeon'))
import kmedoids_final as kf

R, SEED = 20, 42
lab = pd.read_csv(ROOT / 'KMedoids_12Types_N1O3.csv')
yr = pd.read_csv(ROOT / 'KNHANES_2022_2024_ANALYSIS_BASE.csv', usecols=['ID', 'year'], encoding='utf-8-sig')
df = lab.merge(yr, on='ID')
_, M, _ = kf.build_matrix(df)


def run(M):
    pca = PCA(n_components=5, random_state=SEED).fit(M)
    D = kf.pairwise_dist(pca.transform(M))
    med, _ = kf.kmedoids(D, 4, seed=SEED, n_init=10)
    lb = np.argmin(D[med], axis=0)
    return kf.silhouette(D, lb), pca.explained_variance_ratio_.sum(), np.bincount(lb, minlength=4).min() / len(lb)


def null_a(M, rng):
    return np.column_stack([rng.permutation(M[:, j]) for j in range(M.shape[1])])


rho = spearmanr(M).statistic
C = 2 * np.sin(np.pi * rho / 6)                     # 순위상관 → 정규 상관 (Pearson 1907 변환)
Ms = np.sort(M, axis=0)


def null_b(M, rng):
    U = norm.cdf(rng.multivariate_normal(np.zeros(M.shape[1]), C, size=len(M)))
    idx = np.minimum((U * len(M)).astype(int), len(M) - 1)
    return np.column_stack([Ms[idx[:, j], j] for j in range(M.shape[1])])


t0 = time.time()
obs = run(M)
print(f'실제: 실루엣 {obs[0]:.3f}, PCA 설명분산 {obs[1]:.3f}, 최소 군집 비율 {obs[2]:.1%}')
rows = [dict(자료='실제', 회차=0, 실루엣=obs[0], 설명분산=obs[1], 최소군집비율=obs[2])]
rng = np.random.default_rng(SEED)
for name, f in [('귀무A_상관없음', null_a), ('귀무B_상관유지', null_b)]:
    for r in range(1, R + 1):
        s = run(f(M, rng))
        rows.append(dict(자료=name, 회차=r, 실루엣=s[0], 설명분산=s[1], 최소군집비율=s[2]))
        print(f'{name} {r:2d}: 실루엣 {s[0]:.3f} ({time.time() - t0:.0f}초)', flush=True)
res = pd.DataFrame(rows)
res.to_csv(OUT / '15_군집_귀무검정.csv', index=False, encoding='utf-8-sig')

# %% 요약과 판정
print()
summ = []
for name in ['귀무A_상관없음', '귀무B_상관유지']:
    s = res.loc[res['자료'] == name, '실루엣']
    p = (1 + (s >= obs[0]).sum()) / (1 + len(s))
    summ.append(dict(귀무=name, 평균=s.mean(), 표준편차=s.std(), 최소=s.min(), 최대=s.max(), 실제=obs[0],
                     실제_평균차_SD=(obs[0] - s.mean()) / s.std(), 경험적p=p, 넘음=obs[0] > s.max()))
summ = pd.DataFrame(summ)
print(summ.round(3).to_string(index=False))
a, b = summ['넘음']
verdict = ('우연보다 뚜렷한 구조 (두 귀무 모두 넘음)' if a and b else
           '변수 간 상관에서 오는 구조, 따로 떨어진 덩어리는 아님' if a else '연속 분포를 나눈 구분')
print('판정:', verdict)

# %% 그림 (보고서 팔레트: 청록 #2C6E6A, 연청록 #8BB5B0, 황토 #B9773A)
plt.rcParams['font.family'] = 'Malgun Gothic'
fig, ax = plt.subplots(figsize=(7, 3.2), dpi=200)
fig.patch.set_facecolor('white')
for i, (name, c, lab_) in enumerate([('귀무A_상관없음', '#8BB5B0', '무작위 A (변수 관계 없앰)'),
                                     ('귀무B_상관유지', '#2C6E6A', '무작위 B (관계 유지, 덩어리만 없앰)')]):
    s = res.loc[res['자료'] == name, '실루엣']
    ax.scatter(s, np.full(len(s), i) + np.random.default_rng(i).uniform(-0.12, 0.12, len(s)), s=22, color=c, label=lab_, zorder=3)
ax.axvline(obs[0], color='#B9773A', lw=2, zorder=2)
ax.text(obs[0], 1.45, f' 실제 {obs[0]:.3f}', color='#B9773A', va='center', fontsize=9)
ax.set_yticks([0, 1], ['무작위 A', '무작위 B'])
ax.set_ylim(-0.5, 1.7)
ax.set_xlabel('대분류 실루엣 (k=4)')
for sp in ['top', 'right', 'left']:
    ax.spines[sp].set_visible(False)
ax.grid(axis='x', color='#e5e5e5', lw=0.6)
ax.legend(frameon=False, fontsize=8, loc='lower right')
fig.tight_layout()
fig.savefig(OUT / 'fig_15_군집_귀무검정.png')
print('저장:', OUT / '15_군집_귀무검정.csv', OUT / 'fig_15_군집_귀무검정.png')
