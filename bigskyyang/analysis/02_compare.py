"""2·3단계: 전처리 방식 × 모델 × k 비교 → output/02_모델비교.csv, .md, fig_02_k비교.png

비교 대상
- KMeans (영역 가중치)       : 웹에서 '가장 가까운 중심' 계산만으로 재현 가능 → 1순위 후보
- KMeans (가중치 없음)        : 영역 가중치의 효과 확인용
- GMM (영역 가중치, 대각 공분산): 모양이 다른 군집을 허용하는 모델과 비교
- 규칙 기반 4축 유형 (MBTI식)  : '군집이 꼭 필요한가'에 답하기 위한 기준선
지표
- 실루엣·Calinski-Harabasz·Davies-Bouldin, 가장 작은 유형 비율
- 시드 안정성: 시작점만 바꾼 5회 결과끼리 평균 ARI
- 부트스트랩 안정성: 80% 표본으로 학습 → 전체에 배정한 결과와 기준 결과의 ARI (20회 평균)
- 영양 결과 차이: 군집에 쓰지 않은 영양소 부족 여부가 유형마다 얼마나 다른지 (common.nutrient_separation)
"""
import itertools

import matplotlib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, calinski_harabasz_score, davies_bouldin_score, silhouette_score
from sklearn.mixture import GaussianMixture

from common import DATA, FEATURE_NAMES, OUT, SEED, Transform, nutrient_separation

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

d = pd.read_csv(DATA / 'persons.csv', encoding='utf-8-sig')
d['age_grp'] = pd.Categorical(d['age_grp'])
diet = d['N_EN'].notna().to_numpy()
tf = Transform().fit(d)
X_w = tf.transform(d)
X_u = X_w / tf.weights                       # 가중치 없음 (표준화만)
rng = np.random.default_rng(SEED)
sample = rng.choice(len(d), 5000, replace=False)   # 실루엣 계산용 고정 표본
KS = range(3, 13)
N_BOOT = 20


def kmeans(X, k, seed=SEED, n_init=20):
    return KMeans(n_clusters=k, n_init=n_init, random_state=seed).fit(X)


def internal(X, lab):
    sizes = np.bincount(lab)
    return {
        'silhouette': silhouette_score(X[sample], lab[sample]),
        'calinski': calinski_harabasz_score(X, lab),
        'davies_bouldin': davies_bouldin_score(X, lab),
        'min_size_pct': sizes.min() / len(lab) * 100,
    }


def nutri(lab):
    return nutrient_separation(d[diet], lab[diet])


rows = []
for name, X in [('KMeans_가중치', X_w), ('KMeans_가중치없음', X_u)]:
    for k in KS:
        base = kmeans(X, k)
        lab = base.labels_
        seeds = [kmeans(X, k, seed=s).labels_ for s in range(1, 6)]
        seed_ari = np.mean([adjusted_rand_score(a, b) for a, b in itertools.combinations([lab] + seeds, 2)])
        boot = []
        for b in range(N_BOOT):
            idx = rng.choice(len(X), int(len(X) * 0.8), replace=False)
            boot.append(adjusted_rand_score(lab, kmeans(X[idx], k, seed=b, n_init=10).predict(X)))
        rows.append({'method': name, 'k': k, **internal(X, lab), 'seed_ari': seed_ari,
                     'boot_ari': np.mean(boot), 'boot_ari_min': np.min(boot), 'nutrient_sep': nutri(lab)})
        print(rows[-1])

for k in KS:
    gm = GaussianMixture(n_components=k, covariance_type='diag', n_init=3, random_state=SEED).fit(X_w)
    lab = gm.predict(X_w)
    seeds = [GaussianMixture(n_components=k, covariance_type='diag', n_init=3, random_state=s).fit(X_w).predict(X_w)
             for s in range(1, 4)]
    seed_ari = np.mean([adjusted_rand_score(a, b) for a, b in itertools.combinations([lab] + seeds, 2)])
    rows.append({'method': 'GMM_가중치', 'k': k, **internal(X_w, lab), 'seed_ari': seed_ari,
                 'boot_ari': np.nan, 'boot_ari_min': np.nan, 'nutrient_sep': nutri(lab), 'bic': gm.bic(X_w)})
    print(rows[-1])

# 규칙 기반 4축 (값이 정해져 있어 시드·부트스트랩 안정성은 항상 1)
axes = pd.DataFrame({
    '음주': d['drink_freq'] >= 2,                                   # 월 1회 이상
    '흡연': d['smoker'] == 1,
    '운동': (d['aerobic'] == 1) | (d['strength_days'] >= 2),
    '아침': d['breakfast'] >= 2,                                     # 주 3회 이상
}).astype(int)
rule = (axes['음주'] * 8 + axes['흡연'] * 4 + axes['운동'] * 2 + axes['아침']).to_numpy()
rule = pd.factorize(rule)[0]
rows.append({'method': '규칙기반_4축', 'k': len(np.unique(rule)), **internal(X_w, rule), 'seed_ari': 1.0,
             'boot_ari': 1.0, 'boot_ari_min': 1.0, 'nutrient_sep': nutri(rule)})

res = pd.DataFrame(rows)
res.to_csv(OUT / '02_모델비교.csv', index=False, encoding='utf-8-sig')

fig, ax = plt.subplots(2, 2, figsize=(11, 7.5))
for (col, title), a in zip([('silhouette', '실루엣 (클수록 잘 나뉨)'), ('boot_ari', '부트스트랩 안정성 ARI'),
                            ('nutrient_sep', '유형 간 영양 결과 차이'), ('min_size_pct', '가장 작은 유형 비율 (%)')], ax.flat):
    for m, g in res[res['method'] != '규칙기반_4축'].groupby('method'):
        a.plot(g['k'], g[col], marker='o', label=m)
    rb = res[res['method'] == '규칙기반_4축'].iloc[0]
    a.scatter([rb['k']], [rb[col]], marker='*', s=150, color='black', label='규칙기반 4축', zorder=5)
    a.set_title(title)
    a.set_xlabel('유형 수 k')
    a.grid(alpha=0.3)
ax[0, 1].axhline(0.8, ls='--', color='gray', lw=1)
ax[1, 1].axhline(3, ls='--', color='gray', lw=1)
ax[0, 0].legend(fontsize=8)
fig.tight_layout()
fig.savefig(OUT / 'fig_02_k비교.png', dpi=130)

fmt = res.copy()
for c in ['silhouette', 'seed_ari', 'boot_ari', 'boot_ari_min', 'nutrient_sep', 'davies_bouldin']:
    fmt[c] = fmt[c].round(3)
fmt['calinski'] = fmt['calinski'].round(0)
fmt['min_size_pct'] = fmt['min_size_pct'].round(1)
fmt = fmt.drop(columns=[c for c in ['bic'] if c in fmt])
md = ['# 2·3단계: 모델·k 비교', '', f'대상 {len(d):,}명, 변수 {len(FEATURE_NAMES)}개, 실루엣은 고정 표본 5,000명, 부트스트랩 {N_BOOT}회', '',
      fmt.to_markdown(index=False), '']
(OUT / '02_모델비교.md').write_text('\n'.join(md), encoding='utf-8')
print(fmt.to_string())
