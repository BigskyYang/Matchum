# %% [markdown]
# # [B'] 추천 영양소 조합 군집화 (흡수 상호작용 반영)
# 1) 영양소 모듈: 15,062명의 '에너지 보정 섭취량' 상관으로 영양소 14개를 계층적 군집
#    - 에너지 보정(잔차법): 많이 먹는 사람은 모든 영양소가 많아서 전부 상관이 높게 나오는 걸 제거
#      → 남는 상관 = 같은 식품에서 같이 오는 영양소 (예: 유제품 → 칼슘·리보플라빈·인)
#    - 거리 = 1 - 스피어만 상관, average linkage, 실루엣으로 k 선택, 사람 부트스트랩으로 안정성(ARI)
# 2) 고객 군집 니즈 그룹: 군집별 보정 OR 벡터를 계층적 군집 (점이 군집 수뿐이라 요약 용도)
# 3) 군집별 추천 조합: 우선 영양소 → 모듈로 묶고, 흡수 상승 짝은 같이 / 저해 짝은 따로 복용 표시

# %%
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import linkage, fcluster, dendrogram
from scipy.spatial.distance import squareform
from sklearn.metrics import silhouette_score, adjusted_rand_score
from common import *

warnings.filterwarnings('ignore')
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False
rng = np.random.default_rng(42)

# 2026-11-02 지연님 k-medoids 11개 유형 (Jiyeon/KMedoids_Lifestyle_MicroClustered.xlsx, Raw_Data 시트)
CLUSTER_FILE = ROOT / 'KMedoids_Lifestyle_MicroClustered.xlsx'
LABEL_COL = 'Micro_Cluster'
d = load_persons(CLUSTER_FILE, LABEL_COL)
need = pd.read_csv(OUT / '군집별_영양니즈_long.csv', encoding='utf-8-sig')

# %% 1) 에너지 보정 섭취량 (잔차법: log 섭취량 ~ log 에너지)
loge = np.log1p(d['영양_N_EN'].values)
A = np.column_stack([np.ones_like(loge), loge])
resid = {}
for n in NUTRIENTS:
    y = np.log1p(d[KDRI[n][0]].values)
    beta, *_ = np.linalg.lstsq(A, y, rcond=None)
    resid[n] = y - A @ beta
R = pd.DataFrame(resid)


def modules(R, k):
    C = R.rank().corr().values                     # 스피어만
    D = np.clip(1 - C, 0, None); np.fill_diagonal(D, 0)
    Z = linkage(squareform(D, checks=False), 'average')
    return Z, D, fcluster(Z, k, 'maxclust')


Z, D, _ = modules(R, 2)
sil = {k: silhouette_score(D, fcluster(Z, k, 'maxclust'), metric='precomputed') for k in range(2, 8)}
# k 선택: 최고 실루엣과 0.02 미만 차이는 동률로 보고, 그중 '2개 이상 영양소 모듈' 수가 가장 많은 k
# (목적이 '조합'이라 단독 모듈은 조합이 아님. ※ 이 동률 규칙은 1차 결과 확인 후 추가함 → 보고서에 명시)
tie = [k for k in sil if sil[k] >= max(sil.values()) - 0.02]
multi = {k: (pd.Series(fcluster(Z, k, 'maxclust')).value_counts() >= 2).sum() for k in tie}
best_k = max(tie, key=lambda k: (multi[k], sil[k]))
labels = fcluster(Z, best_k, 'maxclust')
Zc_ = linkage(squareform(D, checks=False), 'complete')
print('complete linkage와 일치(ARI):', round(adjusted_rand_score(labels, fcluster(Zc_, best_k, 'maxclust')), 3))
# 안정성: 사람을 복원추출해 다시 군집 → 원래 모듈과 ARI
ari = [adjusted_rand_score(labels, modules(R.iloc[rng.integers(0, len(R), len(R))], best_k)[2]) for _ in range(50)]

mod = pd.Series(labels, index=NUTRIENTS, name='모듈')
print('실루엣', {k: round(v, 3) for k, v in sil.items()}, '→ k =', best_k)
print(f'부트스트랩 ARI 평균 {np.mean(ari):.3f} (최소 {np.min(ari):.3f})')
for m, g in mod.groupby(mod):
    print(f'  모듈 {m}: {", ".join(g.index)}')

# 모듈 이름 = 데이터로 확인한 식품군: 모듈 평균(표준화 잔차)과 식품군 섭취량의 스피어만 상관 r ≥ 0.2 상위 2개
FOOD = {'보조_DAIRY_G': '유제품', '보조_MEAT_G': '육류', '보조_FISH_G': '생선', '보조_EGG_G': '달걀',
        '보조_LEGUME_G': '콩류', '식습관_LS_FRUIT': '과일', '식습관_LS_VEG1': '채소'}
F = d[list(FOOD)].copy()
for c in ['식습관_LS_FRUIT', '식습관_LS_VEG1']:          # 1=하루3회 … 9=거의 안 먹음, 99=무응답 → 클수록 자주
    F[c] = 10 - F[c].where(F[c] != 99)
Zs = (R - R.mean()) / R.std()
food_r = pd.DataFrame({m: F.corrwith(Zs[g.index].mean(axis=1), method='spearman') for m, g in mod.groupby(mod)}).T
food_r.columns = [FOOD[c] for c in food_r.columns]
MOD_FOOD = {m: [f for f, r in food_r.loc[m].sort_values(ascending=False).items() if r >= 0.2][:3] for m in food_r.index}
print('\n[모듈 ↔ 식품군 상관]'); print(food_r.round(2).to_string())
mod_df = pd.DataFrame({'모듈': mod, '식품군': mod.map(lambda m: '·'.join(MOD_FOOD[m]))})
mod_df.to_csv(OUT / '영양소모듈.csv', encoding='utf-8-sig')
food_r.to_csv(OUT / '모듈_식품군_상관.csv', encoding='utf-8-sig')

fig, ax = plt.subplots(figsize=(9, 4))
dendrogram(Z, labels=NUTRIENTS, ax=ax, color_threshold=Z[-(best_k - 1), 2])
ax.set_title(f'영양소 모듈 (에너지 보정 섭취 상관, k={best_k}, 실루엣 {sil[best_k]:.2f})'); ax.set_ylabel('1 - 스피어만 상관')
plt.tight_layout(); plt.savefig(OUT / 'fig_영양소모듈_덴드로그램.png', dpi=150)

# %% 2) 고객 군집 니즈 그룹: log(보정 OR) 벡터 계층적 군집
lor = np.log(need.pivot(index='cluster', columns='영양소', values='보정OR')[NUTRIENTS])
Zc = linkage(lor.values, 'average', metric='euclidean')
silc = {k: silhouette_score(lor.values, fcluster(Zc, k, 'maxclust')) for k in range(2, min(7, len(lor)))}
kc = max(silc, key=silc.get)
grp = pd.Series(fcluster(Zc, kc, 'maxclust'), index=lor.index, name='니즈그룹')
print('\n니즈그룹 실루엣', {k: round(v, 3) for k, v in silc.items()}, '→ k =', kc)
print(grp.groupby(grp).apply(lambda s: ', '.join(s.index)).to_string())
fig, ax = plt.subplots(figsize=(8, 4))
dendrogram(Zc, labels=lor.index.tolist(), ax=ax)
ax.set_title(f'고객 군집 니즈 그룹 (log 보정 OR, k={kc})'); plt.tight_layout()
plt.savefig(OUT / 'fig_니즈그룹_덴드로그램.png', dpi=150)

# %% 3) 군집별 추천 조합
# 영양제 추천 제외: 인·칼륨(식품으로만, 팀 가이드), 식이섬유는 기능성 원료 쪽으로
FOOD_ONLY = ['인', '칼륨']
syn = ABSORPTION.query('유형=="상승"')
ant = ABSORPTION.query('유형=="저해"')
FAT_SOL = {'비타민A', '비타민D', '비타민E'}


MOD_NAME = {m: f"{'·'.join(g.index)} ({'·'.join(MOD_FOOD[m]) or '식품군 불명확'})" for m, g in mod.groupby(mod)}
# 공통 주의: EAR 기준(부족 판정 가능)을 AI 기준(참고)보다 앞에, 그 안에서는 미달률 높은 순
COMMON = (need.drop_duplicates('영양소').query('전체미달률 >= 0.5')
              .assign(ai=lambda x: x['기준'].eq('AI')).sort_values(['ai', '전체미달률'], ascending=[True, False])['영양소'].tolist())
COMMON_SUPP = [n for n in COMMON if n not in FOOD_ONLY]
MAX_PICK = 4


def combo(c):
    g = need[(need['cluster'] == c) & need['유형특이']].sort_values('순위')
    spec = [n for n in g['영양소'] if n not in FOOD_ONLY][:MAX_PICK]
    meal = g['원인'].eq('식사량형').mean() if len(g) else 0
    # 흡수 상승 짝 보충: 유형특이 영양소의 상승 파트너가 공통주의면 조합에 추가 (예: 칼슘 → 비타민D)
    add = [r.A for r in syn.itertuples() if r.B in spec and r.A in COMMON_SUPP and r.A not in spec]
    picks = spec + sorted(set(add))
    together = sorted({f'{r.A}+{r.B}' for r in syn.itertuples() if r.A in picks and r.B in picks})
    apart = sorted({f'{r.A}/{r.B}({r.근거강도})' for r in ant.itertuples() if r.A in picks and r.B in picks})
    mods = sorted({int(mod[n]) for n in picks})
    # 고객 군집 ↔ 영양소 모듈 매칭 (변별력 위해 유형특이 우선)
    #  유형특이 영양소가 있는 모듈만 매칭(유형특이 수 많은 순). 유형특이가 없으면 공통주의 상위 2개 영양소의 모듈
    spec_all = list(g['영양소'])[:MAX_PICK]                # 유형특이 상위 4개(인·칼륨 포함: 식품 안내에는 씀)
    ms = {m: sum(n in spec_all for n in gm.index) for m, gm in mod.groupby(mod)}
    matched = [m for m, s in sorted(ms.items(), key=lambda x: -x[1]) if s > 0][:3]
    if not matched:
        matched = list(dict.fromkeys(int(mod[n]) for n in COMMON[:2]))
    return dict(
        유형특이조합=' + '.join(picks) if picks else '(없음: 공통 주의만 안내)',
        매칭모듈=' | '.join(MOD_NAME[m] for m in matched),
        식품안내=', '.join(dict.fromkeys(f for m in matched for f in MOD_FOOD[m])),
        식품군모듈=' | '.join(MOD_NAME[m] for m in mods),
        원인=('식사량형 → 끼니 챙기기 우선' if meal >= 0.5 else '구성형') if spec else '',
        흡수짝추가=', '.join(sorted(set(add))),
        같이=', '.join(together), 따로=', '.join(apart),
        식사와함께=', '.join(sorted(set(picks) & FAT_SOL)),
        식품으로만=', '.join(n for n in g['영양소'] if n in FOOD_ONLY))


rec = pd.DataFrame({c: combo(c) for c in lor.index}).T
rec.insert(0, '니즈그룹', grp)
rec.to_csv(OUT / '군집별_추천영양소조합.csv', encoding='utf-8-sig')
mod.to_csv(OUT / '영양소모듈.csv', encoding='utf-8-sig')
pd.set_option('display.width', 250); pd.set_option('display.max_colwidth', 90)
print('\n[한국 성인 공통 주의 (전 군집 공통 안내)]', ', '.join(COMMON))
print('\n[군집별 추천 조합]'); print(rec.to_string())
