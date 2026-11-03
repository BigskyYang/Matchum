"""4·5단계: 최종 모델 학습 → 검증 → 이름 근거 → 웹용 model.json + 보고서

사용: python 03_final.py <k> [--no-weight]
  --no-weight: 영역 가중치 없이 표준화만 (02_모델비교에서 영양 결과 차이가 더 컸던 설정)
출력 (모두 요약 결과, 사람 단위 자료 없음)
- data/nbti_model_7types.json 웹 재현 확인용 (비교안이라 웹에는 쓰지 않음, git 제외)
- output/03_최종모델.md        검증 결과·유형 프로필·이름 근거·영양 결과·지연님 결과와 비교
- output/fig_03_*.png         유형 프로필, 유형별 영양 결과 그림
- data/labels.csv             사람별 유형 (git 제외)
"""
import itertools
import json
import sys

import matplotlib
import numpy as np
import pandas as pd
from scipy.stats import poisson
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score

from common import (DATA, DOMAINS, FEATURE_NAMES, FEATURES, LABEL_KO, NUTRIENTS, OUT, REPO, SEED, Transform, clip,
                    nutrient_separation, standardized_ratio)
from type_names import NAMES

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

K = int(sys.argv[1])
NO_WEIGHT = '--no-weight' in sys.argv
N_BOOT = 100
WEB_SLEEP_YEAR = 2024     # 웹 설문은 2024년과 같이 취침·기상 시각으로 묻는다

d = pd.read_csv(DATA / 'persons.csv', encoding='utf-8-sig')
d['age_grp'] = pd.Categorical(d['age_grp'])
diet = d['N_EN'].notna().to_numpy()
w = (d['wt_tot'] / 3).to_numpy()          # 3개년 통합 가중치 (이용지침서 방식, 유환님 분석과 같음)
tf = Transform().fit(d)
if NO_WEIGHT:
    tf.weights = np.ones(len(FEATURE_NAMES))
X = tf.transform(d)
rng = np.random.default_rng(SEED)
sample = rng.choice(len(d), 5000, replace=False)

km = KMeans(n_clusters=K, n_init=50, random_state=SEED).fit(X)
raw_lab = km.labels_
# 유형 번호는 인원(가중) 많은 순으로 고정
order = pd.Series(w).groupby(raw_lab).sum().sort_values(ascending=False).index.to_list()
remap = {old: new for new, old in enumerate(order)}
lab = np.array([remap[x] for x in raw_lab])
centers = km.cluster_centers_[order]
ids = [chr(ord('A') + i) for i in range(K)]
id_of = np.array(ids)[lab]

# ── 4단계 검증 ──
seeds = [KMeans(n_clusters=K, n_init=50, random_state=s).fit(X).labels_ for s in range(1, 10)]
seed_ari = [adjusted_rand_score(a, b) for a, b in itertools.combinations([lab] + seeds, 2)]
boot = []
for b in range(N_BOOT):
    idx = rng.choice(len(X), int(len(X) * 0.8), replace=False)
    boot.append(adjusted_rand_score(lab, KMeans(n_clusters=K, n_init=50, random_state=b).fit(X[idx]).predict(X)))   # 최종 모델과 같은 초기화 횟수
boot = np.array(boot)

# 시간 검증: 2022–2023으로만 학습 → 2024년 사람 배정 vs 2024년만 따로 군집
tr, te = d['year'] < 2024, d['year'] == 2024
tf_tr = Transform().fit(d[tr])
tf_tr.weights = tf.weights
tf_tr.sleep_by_year[2024] = tf.sleep_by_year[2024]       # 2024 측정 방식은 2024 기준값으로 보정 (웹과 같음)
km_tr = KMeans(n_clusters=K, n_init=50, random_state=SEED).fit(tf_tr.transform(d[tr]))
X24 = tf_tr.transform(d[te])
temporal_vs_own = adjusted_rand_score(km_tr.predict(X24), KMeans(n_clusters=K, n_init=50, random_state=SEED).fit(X24).labels_)
temporal_vs_full = adjusted_rand_score(km_tr.predict(X24), lab[te.to_numpy()])

sil = silhouette_score(X[sample], lab[sample])


# ── 가중 프로필과 z (이름 근거) ──
def wmean(v, ww):
    return float(np.sum(v * ww) / np.sum(ww))


Xc = pd.DataFrame(clip(d[FEATURE_NAMES].to_numpy(float)), columns=FEATURE_NAMES)
overall_mean = {f: wmean(Xc[f].to_numpy(), w) for f in FEATURE_NAMES}
overall_sd = {f: float(np.sqrt(wmean((Xc[f].to_numpy() - overall_mean[f]) ** 2, w))) for f in FEATURE_NAMES}
sleep_adj = X[:, FEATURE_NAMES.index('sleep_hours')] / tf.weights[FEATURE_NAMES.index('sleep_hours')]   # 연도 보정 z
prof, zt = {}, {}
for i, t in enumerate(ids):
    m = lab == i
    prof[t] = {f: wmean(Xc.loc[m, f].to_numpy(), w[m]) for f in FEATURE_NAMES}
    zt[t] = {f: (prof[t][f] - overall_mean[f]) / overall_sd[f] for f in FEATURE_NAMES}
    zt[t]['sleep_hours'] = wmean(sleep_adj[m], w[m]) - wmean(sleep_adj, w)   # 수면은 연도 보정 값으로 비교
share = pd.Series(w).groupby(id_of).sum() / w.sum()
count = pd.Series(id_of).value_counts()

# 변수별 η² (유형이 각 변수를 얼마나 가르는지) — 흡연·음주만 가르는지 확인
eta = {}
for j, f in enumerate(FEATURE_NAMES):
    s = pd.Series(X[:, j])
    eta[f] = 1 - (s.groupby(lab).var(ddof=0) * np.bincount(lab)).sum() / (s.var(ddof=0) * len(s))

# ── 유형별 영양 결과 (군집에 쓰지 않은 결과 변수) ──
dd = d[diet].reset_index(drop=True)
lab_d = id_of[diet]
nut = {}
for n in NUTRIENTS:
    t = standardized_ratio(dd, lab_d, n)
    t['p'] = [2 * min(poisson.cdf(o, e), poisson.sf(o - 1, e)) for o, e in zip(t['obs'], t['exp'])]
    nut[n] = t
ratio = pd.DataFrame({n: nut[n]['ratio'] for n in NUTRIENTS}).loc[ids]
pval = pd.DataFrame({n: nut[n]['p'] for n in NUTRIENTS}).loc[ids]
rate = pd.DataFrame({n: dd.groupby(lab_d)[f'below_{n}'].mean() for n in NUTRIENTS}).loc[ids]
specific = (ratio >= 1.2) & (pval < 0.05)          # 유형 특이: 성별·연령 감안해도 1.2배 이상 + 유의
common_flag = {n: float(dd[f'below_{n}'].mean()) >= 0.5 for n in NUTRIENTS}   # 공통 주의: 전체 부족률 50% 이상
sep = nutrient_separation(dd, lab_d)

# ── 지연님 결과와 비교 (같은 사람, 같은 지표) ──
cmp_lines = []
jx = REPO / 'Jiyeon' / 'KMedoids_Final_Corrected.xlsx'
if jx.exists():
    jl = pd.read_excel(jx, sheet_name='Raw_Data')[['ID', 'Micro_Cluster']]
    mj = d[['ID']].assign(mine=id_of, i=np.arange(len(d))).merge(jl, on='ID')
    jlab = pd.factorize(mj['Micro_Cluster'])[0]
    jdiet = diet[mj['i'].to_numpy()]
    jsep = nutrient_separation(d.iloc[mj['i'][jdiet]].reset_index(drop=True), mj['Micro_Cluster'].to_numpy()[jdiet])
    jsil = silhouette_score(X[mj['i'].to_numpy()][:5000], jlab[:5000])
    msil = silhouette_score(X[mj['i'].to_numpy()][:5000], pd.factorize(mj['mine'])[0][:5000])
    jeta = {}
    for j, f in enumerate(FEATURE_NAMES):
        s = pd.Series(X[mj['i'].to_numpy(), j])
        jeta[f] = 1 - (s.groupby(jlab).var(ddof=0) * np.bincount(jlab)).sum() / (s.var(ddof=0) * len(s))
    cmp_lines = [
        '| 지표 | 지연님 11개 (k-medoids) | 이번 안 |', '|---|---:|---:|',
        f'| 비교 인원 | {len(mj):,} | {len(mj):,} |',
        f'| 유형 수 | {jl["Micro_Cluster"].nunique()} | {K} |',
        f'| 실루엣 (같은 변수 공간, 표본 5,000) | {jsil:.3f} | {msil:.3f} |',
        f'| 시드 안정성 ARI | 0.52 (이전 검토) | {np.mean(seed_ari):.3f} |',
        f'| 유형 간 영양 결과 차이 | {jsep:.3f} | {sep:.3f} |',
        f'| 흡연·음주 η² 평균 | {np.mean([jeta[f] for f in FEATURE_NAMES if DOMAINS[f] in ("흡연", "음주")]):.2f} | '
        f'{np.mean([eta[f] for f in FEATURE_NAMES if DOMAINS[f] in ("흡연", "음주")]):.2f} |',
        f'| 그 밖의 변수 η² 평균 | {np.mean([jeta[f] for f in FEATURE_NAMES if DOMAINS[f] not in ("흡연", "음주")]):.2f} | '
        f'{np.mean([eta[f] for f in FEATURE_NAMES if DOMAINS[f] not in ("흡연", "음주")]):.2f} |',
        f'| 두 결과의 일치도 ARI | {adjusted_rand_score(jlab, pd.factorize(mj["mine"])[0]):.3f} | |',
    ]

# ── 이름 근거 확인: 이름에 쓴 특징이 실제로 그 방향인지 ──
name_rows, name_ok = [], True
for t in ids:
    nm = NAMES.get(t, {'name': f'유형 {t}', 'claims': []})
    for f, sign in nm['claims']:
        z = zt[t][f]
        ok = (z >= 0.3) if sign > 0 else (z <= -0.3)
        name_ok &= ok
        name_rows.append(f'| {t} {nm["name"]} | {LABEL_KO[f]} {"높음" if sign > 0 else "낮음"} | '
                         f'{prof[t][f]:.2f} (전체 {overall_mean[f]:.2f}) | {z:+.2f} | {"✅" if ok else "❌"} |')

# ── 웹 재현 확인: JSON 값만으로 다시 배정 ──
model = {
    'version': 'nbti-kmeans-v1',
    'method': 'kmeans',
    'domain_weighting': not NO_WEIGHT,
    'k': K,
    'note': 'clip → (x-mean)/std (수면은 sleep 기준값) → × weight → 가장 가까운 중심(유클리드)',
    'features': [{'name': f, 'label': LABEL_KO[f], 'domain': DOMAINS[f], 'clip': list(FEATURES[f][1]),
                  'mean': float(tf.mean[j]), 'std': float(tf.std[j]), 'weight': float(tf.weights[j])}
                 for j, f in enumerate(FEATURE_NAMES)],
    'web_source': {
        'smoker': 'features.ML_smoker', 'cigarettes': 'features.ML_cigarettes_day',
        'drink_freq': 'features.ML_drink_freq_ord', 'drink_amount': 'features.ML_drink_amount_ord',
        'aerobic': 'features.ML_aerobic', 'strength_days': 'features.ML_strength_days',
        'sedentary_min': 'features.ML_sedentary_min', 'sleep_hours': 'features.ML_sleep_hours',
        'stress': 'features.ML_stress', 'breakfast': 'features.ML_breakfast_freq_ord',
        'lunch': 'features.ML_lunch_freq_ord', 'dinner': 'features.ML_dinner_freq_ord',
        'eating_out': 'features.ML_eatingout_freq_ord', 'veg': 'extras.veg', 'fruit': 'extras.fruit',
    },
    'sleep': {'feature': 'sleep_hours', 'web_year': WEB_SLEEP_YEAR,
              'mean': tf.sleep_by_year[WEB_SLEEP_YEAR][0], 'std': tf.sleep_by_year[WEB_SLEEP_YEAR][1],
              'by_year': {str(y): {'mean': mu, 'std': sd} for y, (mu, sd) in tf.sleep_by_year.items()}},
    'types': [{
        'id': t, 'name': NAMES.get(t, {}).get('name', f'유형 {t}'), 'centroid': centers[i].tolist(),
        'n': int(count[t]), 'share': float(share[t]),
        'profile': {f: round(prof[t][f], 3) for f in FEATURE_NAMES},
        'z': {f: round(zt[t][f], 3) for f in FEATURE_NAMES},
        'nutrients': {n: {'ratio': round(float(ratio.loc[t, n]), 3), 'rate': round(float(rate.loc[t, n]), 3),
                          'specific': bool(specific.loc[t, n])} for n in NUTRIENTS},
    } for i, t in enumerate(ids)],
    'common_nutrients': [n for n in NUTRIENTS if common_flag[n]],
    'population': {'source': 'KNHANES 2022–2024, 만 19세 이상, 생활습관 15개 변수 응답 완료', 'n': int(len(d)),
                   'weighted': 'share·profile은 wt_tot/3 가중'},
    'metrics': {'silhouette': round(float(sil), 3), 'seed_ari_mean': round(float(np.mean(seed_ari)), 3),
                'boot_ari_mean': round(float(boot.mean()), 3), 'boot_ari_p05': round(float(np.quantile(boot, 0.05)), 3),
                'temporal_ari_vs_2024_own': round(float(temporal_vs_own), 3),
                'temporal_ari_vs_full': round(float(temporal_vs_full), 3), 'nutrient_separation': round(sep, 3)},
}


def assign_from_json(df, mdl, year=None):
    f = mdl['features']
    Xr = df[[x['name'] for x in f]].to_numpy(float)
    lo, hi = np.array([x['clip'][0] for x in f]), np.array([x['clip'][1] for x in f])
    mean, std, wt = (np.array([x[k] for x in f]) for k in ('mean', 'std', 'weight'))
    Z = (np.clip(Xr, lo, hi) - mean) / std
    j = [x['name'] for x in f].index(mdl['sleep']['feature'])
    years = df['year'].to_numpy() if year is None else np.full(len(df), year)
    for y, s in mdl['sleep']['by_year'].items():
        Z[years == int(y), j] = (np.clip(Xr[years == int(y), j], lo[j], hi[j]) - s['mean']) / s['std']
    C = np.array([t['centroid'] for t in mdl['types']])
    dist = (((Z * wt)[:, None, :] - C[None]) ** 2).sum(axis=2)
    return np.array([t['id'] for t in mdl['types']])[dist.argmin(axis=1)]


reassign = float((assign_from_json(d, model) == id_of).mean())
web_basis = float((assign_from_json(d, model, year=WEB_SLEEP_YEAR) == id_of).mean())
model['metrics']['reassign_match'] = reassign
(DATA / 'nbti_model_7types.json').write_text(json.dumps(model, ensure_ascii=False, indent=1), encoding='utf-8')
pd.DataFrame({'ID': d['ID'], 'type': id_of}).to_csv(DATA / 'labels.csv', index=False, encoding='utf-8-sig')

# ── 그림 ──
zdf = pd.DataFrame(zt).T.loc[ids, FEATURE_NAMES]
fig, ax = plt.subplots(figsize=(12, 0.5 * K + 2))
im = ax.imshow(zdf.to_numpy(), cmap='RdBu_r', vmin=-1.5, vmax=1.5, aspect='auto')
ax.set_xticks(range(len(FEATURE_NAMES)), [LABEL_KO[f] for f in FEATURE_NAMES], rotation=45, ha='right')
ax.set_yticks(range(K), [f'{t} {NAMES.get(t, {}).get("name", "")}' for t in ids])
for i in range(K):
    for j in range(len(FEATURE_NAMES)):
        ax.text(j, i, f'{zdf.iat[i, j]:+.1f}', ha='center', va='center', fontsize=7)
fig.colorbar(im, ax=ax, label='전체 평균 대비 z')
ax.set_title('유형별 생활습관 (전체 평균 대비)')
fig.tight_layout()
fig.savefig(OUT / 'fig_03_유형프로필.png', dpi=130)

fig, ax = plt.subplots(figsize=(12, 0.5 * K + 2))
lr = np.log2(ratio.to_numpy())
im = ax.imshow(lr, cmap='PuOr_r', vmin=-0.8, vmax=0.8, aspect='auto')
ax.set_xticks(range(len(NUTRIENTS)), NUTRIENTS, rotation=45, ha='right')
ax.set_yticks(range(K), [f'{t} {NAMES.get(t, {}).get("name", "")}' for t in ids])
for i, t in enumerate(ids):
    for j, n in enumerate(NUTRIENTS):
        ax.text(j, i, f'{ratio.loc[t, n]:.2f}' + ('*' if specific.loc[t, n] else ''), ha='center', va='center', fontsize=7)
fig.colorbar(im, ax=ax, label='log2(성별·연령 표준화 부족비)')
ax.set_title('유형별 영양소 부족 (1보다 크면 같은 성별·연령보다 더 많이 부족, * 유형 특이)')
fig.tight_layout()
fig.savefig(OUT / 'fig_03_유형별영양.png', dpi=130)

# ── 보고서 ──
md = [f'# 4·5단계: 최종 모델 (KMeans, k={K}, 영역 가중치 {"없음" if NO_WEIGHT else "있음"})', '',
      '## 검증', '', '| 항목 | 값 | 기준 |', '|---|---:|---|',
      f'| 실루엣 (가중 공간, 표본 5,000) | {sil:.3f} | 0.25 이상이면 약한 구조 |',
      f'| 시드 안정성 (10개 시드 쌍 평균 ARI) | {np.mean(seed_ari):.3f} (최소 {np.min(seed_ari):.3f}) | 0.8 이상 |',
      f'| 부트스트랩 안정성 (80% × {N_BOOT}회 평균 ARI) | {boot.mean():.3f} (하위 5% {np.quantile(boot, 0.05):.3f}) | 0.8 이상 |',
      f'| 시간 검증: 2022–23 학습 → 2024 배정 vs 2024 단독 군집 | {temporal_vs_own:.3f} | 높을수록 새 사람에게도 같은 구조 |',
      f'| 시간 검증: 2022–23 학습 → 2024 배정 vs 전체 학습 결과 | {temporal_vs_full:.3f} | |',
      f'| 유형 간 영양 결과 차이 | {sep:.3f} | 클수록 유형마다 부족 영양소가 다름 |',
      f'| JSON 값만으로 다시 배정한 일치율 | {reassign:.2%} | 100% |',
      f'| 2022–23년 수면을 2024 기준으로 바꿔도 같은 유형인 비율 | {web_basis:.2%} | 웹 기준 민감도 |',
      '', '## 유형 (인원·비율은 조사 가중치 적용)', '',
      '| ID | 이름 | 인원 | 가중 비율 | 두드러진 특징 (z ≥ 0.5) |', '|---|---|---:|---:|---|']
for t in ids:
    top = sorted(((f, z) for f, z in zt[t].items() if abs(z) >= 0.5), key=lambda x: -abs(x[1]))
    desc = ', '.join(f'{LABEL_KO[f]} {z:+.1f}' for f, z in top) or '전체 평균과 비슷'
    md.append(f'| {t} | {NAMES.get(t, {}).get("name", "")} | {count[t]:,} | {share[t]:.1%} | {desc} |')
md += ['', '## 유형별 평균 (가중)', '', pd.DataFrame(prof).T.loc[ids].rename(columns=LABEL_KO).round(2).to_markdown(),
       '', '## 이름 근거 (이름에 쓴 특징이 실제로 z ≥ 0.3 / ≤ −0.3 인지)', '',
       '| 유형 | 이름에 쓴 특징 | 유형 평균 | z | 확인 |', '|---|---|---|---:|---|'] + name_rows
md += ['', f'모든 이름 근거 통과: {"✅" if name_ok else "❌"}', '',
       '## 변수별 η² (유형이 그 변수를 얼마나 가르는지)', '',
       '| 변수 | 영역 | η² |', '|---|---|---:|']
md += [f'| {LABEL_KO[f]} | {DOMAINS[f]} | {eta[f]:.2f} |' for f in sorted(eta, key=eta.get, reverse=True)]
md += ['', '## 유형별 영양소 부족 (성별·연령 간접 표준화비, 24시간 회상 있는 사람)', '',
       '1보다 크면 같은 성별·연령대보다 더 많이 부족. **굵게** = 유형 특이 (1.2배 이상, p < 0.05)', '']
tbl = ratio.round(2).astype(str)
tbl[specific] = '**' + tbl[specific] + '**'
md += [tbl.to_markdown(), '', '공통 주의 (전체 부족률 50% 이상): ' + ', '.join(model['common_nutrients']), '']
if cmp_lines:
    md += ['## 지연님 11개 유형과 비교', ''] + cmp_lines + ['']
(OUT / '03_최종모델.md').write_text('\n'.join(md), encoding='utf-8')
print('\n'.join(md))
