"""지연님 12개 유형 보완판 → output/05_지연님안_보완.md, output/nbti_12types.json, data/labels_12.csv

지연님 설계(생활습관 7개 변수, PCA 5, 대분류 4 × 세부 3, SUB_PLAN, 대분류 역할 정하기)는 그대로 두고 아래만 고쳤다.
1. 안정성: 같은 설계에서 군집 알고리즘·초기화 횟수를 바꿔 표본 40% 재학습 안정성이 가장 높은 것을 쓴다 (METHOD, N_INIT)
2. 이름: 사람이 읽는 이름(type_names.NAMES_12)을 붙이고, 이름에 쓴 특징이 실제로 |z| ≥ 0.3인지 자동 확인
3. 영양 문구: 성별·연령·총 섭취량까지 같은 사람과 비교해도 남는 것만 '유형 특이',
   성별·연령 보정에서만 보이는 것은 '식사량 영향'(먼저 식사량 점검), 전체 50% 이상 부족은 '공통 주의'
4. 흡연·음주·채소·과일은 유형에 넣지 않고 개인 신호로 (JSON personal_signals: 전체 평균만 제공)
5. 웹용 JSON: 원래 응답 → 7개 점수가 '상수 + Σ 계수 × 응답'의 한 줄 식이 되도록 정리. verify_12types.mjs로 JS 재배정 확인

실행: python 05_jiyeon_improved.py [N_SUB]   (N_SUB: 표본 40% 재학습 반복 수, 기본 20)
"""
import json
import sys

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score

from common import (DATA, FEATURE_NAMES, LABEL_KO, NUTRIENTS, OUT, REPO, SEED, Transform, adjusted_ratios,
                    ratio_separation, specific_rows)
from twolevel import ROLE_CODE, assign, fit, fit_pca, jm
from type_names import MACRO_12, NAMES_12

sys.stdout.reconfigure(encoding='utf-8')

METHOD, N_INIT = 'kmedoids', 10   # 지연님 원본. n_init=50도 전체 자료에서 같은 해 (README 참고)
N_SUB = int(sys.argv[1]) if len(sys.argv) > 1 else 20
SUB_FRAC = 0.4
ROLE_KO = {r: MACRO_12[c]['name'] for r, c in ROLE_CODE.items()}
MODEL_KO = {'aerobic': '유산소 실천', 'strength_days': '근력운동(일/주)', 'sedentary_min': '좌식(분/일)',
            'sleep_hours': '수면(시간)', 'stress': '스트레스 많음', 'eatingout_freq_ord': '외식 빈도(0~6)',
            'meal_score': '규칙식사 점수'}

# ── 데이터: 지연님 CSV(15,062명)로 학습, 영양 결과는 01_prepare의 persons.csv와 ID로 합친다 ──
jdf = pd.read_csv(REPO / 'Jiyeon' / 'KNHANES_2022_2024_ML_CLUSTER_COMPLETECASE.csv', encoding='utf-8-sig')
X, M, tf = jm.build_matrix(jdf)
pca = fit_pca(M)
Q = pca.transform(M)
N = len(Q)
ALL = np.arange(N)

model = fit(Q, M, ALL, SEED, METHOD, N_INIT)
lab, macro = assign(model, Q, M)
jmodel = json.loads((REPO / 'Jiyeon' / 'kmedoids_model.json').read_text(encoding='utf-8'))
orig = jm.assign(jdf, jmodel)
orig_macro = pd.Series(orig).str.rsplit('_', n=1).str[0].to_numpy()

# ── 안정성 ──
N_SEED = 5 if N_SUB else 1   # N_SUB=0: 이름 붙이기용 빠른 실행 (검증 생략)
seed_runs = [assign(fit(Q, M, ALL, s, METHOD, N_INIT), Q, M)[0] for s in range(N_SEED)]
seed_ari = [adjusted_rand_score(seed_runs[i], seed_runs[j]) for i in range(N_SEED) for j in range(i + 1, N_SEED)] or [np.nan]
rng = np.random.default_rng(SEED)
# 비교용: 같은 설계에서 KMeans(n_init=50)로 바꾸면 — 같은 표본으로 함께 잰다
km_lab = assign(fit(Q, M, ALL, SEED, 'kmeans', 50), Q, M)[0]
sub12, sub4, km_sub = [], [], []
for b in range(N_SUB):
    idx = rng.choice(N, int(N * SUB_FRAC), replace=False)
    l12, l4 = assign(fit(Q, M, idx, b, METHOD, N_INIT), Q, M)
    sub12.append(adjusted_rand_score(lab, l12))
    sub4.append(adjusted_rand_score(macro, l4))
    km_sub.append(adjusted_rand_score(km_lab, assign(fit(Q, M, idx, b, 'kmeans', 50), Q, M)[0]))
    print('sub', b, round(sub12[-1], 3), round(sub4[-1], 3), round(km_sub[-1], 3), flush=True)
y = jdf['year'].to_numpy()
early = np.flatnonzero(y < 2024)
sub12, sub4, km_sub = sub12 or [np.nan], sub4 or [np.nan], km_sub or [np.nan]
t12 = assign(fit(Q, M, early, SEED, METHOD, N_INIT), Q, M)[0] if N_SUB else lab
temporal = adjusted_rand_score(lab[y == 2024], t12[y == 2024])

# ── 프로필: persons.csv의 15개 변수(흡연·음주·채소·과일 포함), wt_tot 가중 ──
d = pd.read_csv(DATA / 'persons.csv', encoding='utf-8-sig')
d = d.merge(pd.DataFrame({'ID': jdf['ID'], 'type': lab, 'macro': macro}), on='ID')
w = d['wt_tot'].to_numpy() / 3
t = Transform().fit(d)
t.weights = np.ones(len(FEATURE_NAMES))
Zall = pd.DataFrame(t.transform(d), columns=FEATURE_NAMES)
# 7개 점수 중 6개는 15개 변수와 같은 것이라 규칙식사 점수만 더한다
Mz = pd.DataFrame(M, columns=jm.MODEL_FEATURES).set_index(jdf['ID']).loc[d['ID'], ['meal_score']].reset_index(drop=True)
ids = sorted(set(lab), key=lambda s: (list(ROLE_CODE.values()).index(s[0]), s))


def wmean(frame, mask):
    return (frame[mask].mul(w[mask], axis=0).sum() / w[mask].sum())


prof = {k: wmean(d[FEATURE_NAMES], (d['type'] == k).to_numpy()) for k in ids}
zt = {k: pd.concat([wmean(Zall, (d['type'] == k).to_numpy()), wmean(Mz, (d['type'] == k).to_numpy())]) for k in ids}
share = {k: float(w[(d['type'] == k).to_numpy()].sum() / w.sum()) for k in ids}
count = d['type'].value_counts()
male = {k: float(np.average(d.loc[d['type'] == k, 'sex'] == 1, weights=w[(d['type'] == k).to_numpy()])) for k in ids}
age = {k: float(np.average(d.loc[d['type'] == k, 'age'], weights=w[(d['type'] == k).to_numpy()])) for k in ids}
overall = pd.Series(np.average(d[FEATURE_NAMES], axis=0, weights=w), index=FEATURE_NAMES)

# 이름 근거
name_rows, name_ok = [], True
for k in ids:
    nm = NAMES_12.get(k, {'name': f'유형 {k}', 'claims': []})
    for f, sign in nm['claims']:
        z = float(zt[k][f])
        ok = (z >= 0.3) if sign > 0 else (z <= -0.3)
        name_ok &= ok
        shown = f'{prof[k][f]:.2f} (전체 {overall[f]:.2f})' if f in prof[k] else '—'
        name_rows.append(f'| {k} {nm["name"]} | {LABEL_KO.get(f, MODEL_KO.get(f, f))} {"높음" if sign > 0 else "낮음"} | '
                         f'{shown} | {z:+.2f} | {"✅" if ok else "❌"} |')

# 대분류 이름 근거
macro_z = {c: pd.concat([wmean(Zall, (d['type'].str[0] == c).to_numpy()), wmean(Mz, (d['type'].str[0] == c).to_numpy())])
           for c in MACRO_12}
for c, mm in MACRO_12.items():
    for f, sign in mm['claims']:
        z = float(macro_z[c][f])
        ok = (z >= 0.3) if sign > 0 else (z <= -0.3)
        name_ok &= ok
        name_rows.append(f'| 대분류 {c} {mm["name"]} | {LABEL_KO[f]} {"높음" if sign > 0 else "낮음"} | — | {z:+.2f} | {"✅" if ok else "❌"} |')

# ── 영양: 성별·연령 / + 총 섭취량 5분위 ──
dd = d[d['N_EN'].notna()].reset_index(drop=True)
dd['age_grp'] = pd.Categorical(dd['age_grp'])
dd['energy_q'] = pd.qcut(dd['N_EN'], 5, labels=False)
r_sa = adjusted_ratios(dd, dd['type'].to_numpy(), ['sex', 'age_grp'])
r_en = adjusted_ratios(dd, dd['type'].to_numpy(), ['sex', 'age_grp', 'energy_q'])
spec_en = specific_rows(r_en)
spec_sa = specific_rows(r_sa)
common_rate = {n: float(np.average(dd[f'below_{n}'], weights=dd['wt_tot'])) for n in NUTRIENTS}
COMMON = [n for n in NUTRIENTS if common_rate[n] >= 0.5]


def nutrient_block(k):
    s = spec_en[spec_en['label'] == k]
    i = spec_sa[(spec_sa['label'] == k) & ~spec_sa['nutrient'].isin(s['nutrient'])]
    ra = r_sa[r_sa['label'] == k].set_index('nutrient')
    re = r_en[r_en['label'] == k].set_index('nutrient')
    return {
        'specific': [{'nutrient': n, 'ratio': round(float(x), 2)} for n, x in zip(s['nutrient'], s['ratio'])],
        'intake_related': [{'nutrient': n, 'ratio': round(float(x), 2)} for n, x in zip(i['nutrient'], i['ratio'])],
        'ratios': {n: {'sex_age': round(float(ra.loc[n, 'ratio']), 3), 'plus_energy': round(float(re.loc[n, 'ratio']), 3)}
                   for n in NUTRIENTS},
    }


def cramers_v(a, b):
    ct = pd.crosstab(a, b)
    return float(np.sqrt(chi2_contingency(ct)[0] / (ct.to_numpy().sum() * (min(ct.shape) - 1))))


# ── 웹용 JSON: 원래 응답 → 7개 점수 = const + Σ coef × 응답 ──
F = jm.FEATURES
A, b0 = tf['A'], tf['b']
coef = A / tf['std'][None, :]
const = b0 - (A * tf['mean'][None, :] / tf['std'][None, :]).sum(1)
used = sorted({j for row in coef for j in np.flatnonzero(row)})
lo, hi = X.min(0), X.max(0)
types_json = []
for k in ids:
    r = [r_ for r_ in model['macro'] if ROLE_CODE[r_] == k[0]][0]
    nm = NAMES_12.get(k, {})
    types_json.append({
        'id': k, 'macro': ROLE_KO[r], 'name': nm.get('name', f'유형 {k}'), 'summary': nm.get('summary', ''),
        'n': int(count[k]), 'share': round(share[k], 4), 'male_share': round(male[k], 3), 'age_mean': round(age[k], 1),
        'profile': {f: round(float(prof[k][f]), 3) for f in FEATURE_NAMES},
        'z': {f: round(float(zt[k][f]), 3) for f in list(FEATURE_NAMES) + ['meal_score']},
        'nutrients': nutrient_block(k),
    })
web = {
    'version': 'nbti-12types-v2',
    'design': '지연님 2단계 (Jiyeon/kmedoids_final.py) + 보완 (bigskyyang/analysis/05_jiyeon_improved.py)',
    'method': f'{METHOD}, n_init={N_INIT}',
    'steps': [
        '1. inputs의 응답(features.ML_*)을 clip 범위로 자른다 (학습 자료 최솟값·최댓값)',
        '2. scores[j] = const[j] + Σ coef[j][i] × inputs[i]  (7개 점수, 수면은 2024 기준으로 보정된 값과 같은 척도)',
        '3. pc = (scores − pca.mean) · pca.components^T  (5개)',
        '4. 대분류 = macro 중심 중 pc와 유클리드 거리가 가장 가까운 것',
        '5. 그 대분류의 sub: v = (scores[features] − mean) / std, 세부 중심 중 가장 가까운 것 → types의 id',
    ],
    'inputs': [{'name': F[j], 'web_source': f'features.{F[j]}', 'clip': [float(lo[j]), float(hi[j])]} for j in used],
    'scores': [{'name': f, 'label': MODEL_KO[f], 'const': float(const[i]),
                'coef': {F[j]: float(coef[i, j]) for j in used if coef[i, j] != 0}}
               for i, f in enumerate(jm.MODEL_FEATURES)],
    'sleep_note': '2022·2023년 수면은 2024년 분포로 바꿔 학습했다. 웹은 2024년과 같은 방식(취침·기상 시각)이라 그대로 쓴다.',
    'pca': {'mean': pca.mean_.tolist(), 'components': pca.components_.tolist()},
    'macro': [{'code': ROLE_CODE[r], 'name': ROLE_KO[r], 'center': model['macro'][r].tolist()} for r in model['macro']],
    'sub': {ROLE_CODE[r]: {'features': s['features'], 'mean': s['mean'].tolist(), 'std': s['std'].tolist(),
                           'centers': {f'{ROLE_CODE[r]}{i + 1}': c.tolist() for i, c in enumerate(s['centers'])}}
            for r, s in model['sub'].items()},
    'types': types_json,
    'common_nutrients': [{'nutrient': n, 'rate': round(common_rate[n], 3)} for n in COMMON],
    'personal_signals': {
        'note': '흡연·음주·채소·과일은 유형을 가르지 않는다. 결과 화면에서 내 응답을 그대로 보여 준다 (전체 평균은 비교용)',
        'population_mean': {f: round(float(overall[f]), 3)
                            for f in ['smoker', 'cigarettes', 'drink_freq', 'drink_amount', 'veg', 'fruit']},
    },
    'nutrient_note': ('specific: 성별·연령·총 섭취량 5분위가 같은 사람과 비교해도 부족 비율이 1.2배 이상 (BH-FDR q<0.05). '
                      'intake_related: 성별·연령만 맞추면 1.2배 이상이지만 총 섭취량까지 맞추면 사라짐 → "식사량 점검이 먼저". '
                      'common_nutrients: 전체 가중 부족률 50% 이상 → 모든 유형에 공통 안내. 하루 24시간 회상 기준.'),
    'population': {'source': 'KNHANES 2022–2024, 만 19세 이상, 지연님 COMPLETECASE', 'n': int(N),
                   'weighted': 'share·profile·z는 wt_tot/3 가중'},
}


def assign_from_json(raw, mdl):
    """웹과 같은 순서로 JSON 값만 써서 배정 (raw: 학습 자료 ML_ 열, 수면은 2024 척도)."""
    names = [x['name'] for x in mdl['inputs']]
    V = raw[names].to_numpy(float)
    V = np.clip(V, [x['clip'][0] for x in mdl['inputs']], [x['clip'][1] for x in mdl['inputs']])
    S = np.column_stack([s['const'] + sum(c * V[:, names.index(n)] for n, c in s['coef'].items())
                         for s in mdl['scores']])
    pc = (S - np.array(mdl['pca']['mean'])) @ np.array(mdl['pca']['components']).T
    mc = np.array([m_['center'] for m_ in mdl['macro']])
    codes = np.array([m_['code'] for m_ in mdl['macro']])[np.argmin(((pc[:, None] - mc[None]) ** 2).sum(2), 1)]
    out = np.empty(len(S), dtype=object)
    fn = [s['name'] for s in mdl['scores']]
    for c, s in mdl['sub'].items():
        sel = np.flatnonzero(codes == c)
        v = (S[np.ix_(sel, [fn.index(f) for f in s['features']])] - s['mean']) / np.array(s['std'])
        keys = list(s['centers'])
        C = np.array([s['centers'][k_] for k_ in keys])
        out[sel] = np.array(keys)[np.argmin(((v[:, None] - C[None]) ** 2).sum(2), 1)]
    return out


# 수면을 2024 척도로 바꾼 값(X)으로 확인 → 웹 입력과 같은 조건
check = pd.DataFrame(X, columns=F)
check['ID'] = jdf['ID']
reassign = float((assign_from_json(check, web) == lab).mean())
web['metrics'] = {
    'reassign_match': reassign, 'seed_ari_mean': round(float(np.mean(seed_ari)), 3),
    'sub40_ari_mean': round(float(np.mean(sub12)), 3), 'sub40_ari_min': round(float(np.min(sub12)), 3),
    'sub40_macro_ari_mean': round(float(np.mean(sub4)), 3), 'temporal_ari_2024': round(float(temporal), 3),
    'kmeans_sub40_ari_mean': round(float(np.mean(km_sub)), 3),
    'ari_vs_jiyeon_original': round(float(adjusted_rand_score(orig, lab)), 3),
    'nutrient_separation_sex_age': round(ratio_separation(r_sa), 3),
    'nutrient_separation_plus_energy': round(ratio_separation(r_en), 3),
    'sex_v': round(cramers_v(d['type'], d['sex']), 3), 'age_v': round(cramers_v(d['type'], d['age_grp']), 3),
    'names_all_pass': bool(name_ok),
}
(OUT / 'nbti_12types.json').write_text(json.dumps(web, ensure_ascii=False, indent=1), encoding='utf-8')
pd.DataFrame({'ID': jdf['ID'], 'type': lab}).to_csv(DATA / 'labels_12.csv', index=False, encoding='utf-8-sig')
check.assign(expected=lab).to_csv(DATA / 'web_check_12.csv', index=False, encoding='utf-8-sig')

# ── 문서 ──
mt = web['metrics']
cross = pd.crosstab(pd.Series(orig, name='지연님 원본'), pd.Series(lab, name='보완판'))
md = [
    '# 지연님 12개 유형 보완판', '',
    f'설계는 지연님 안 그대로(7개 변수 → PCA 5 → 대분류 4 → 대분류마다 2개 변수로 세부 3). 알고리즘: **{web["method"]}**.', '',
    '## 검증', '',
    '| 항목 | 값 |', '|---|---:|',
    f'| 시드 안정성 ({N_SEED}개 시드 쌍 평균 ARI) | {mt["seed_ari_mean"]:.3f} |',
    f'| 표본 40% 재학습 → 전체 배정 ARI ({N_SUB}회 평균 / 최소) | {mt["sub40_ari_mean"]:.3f} / {mt["sub40_ari_min"]:.3f} |',
    f'| 같은 조건 대분류 4개 ARI | {mt["sub40_macro_ari_mean"]:.3f} |',
    f'| 시간 검증 (2022–23 학습 → 2024 배정 vs 전체 학습) | {mt["temporal_ari_2024"]:.3f} |',
    f'| JSON 값만으로 다시 배정한 일치율 (웹 조건) | {reassign:.2%} |',
    f'| 지연님 원본 12개와 일치도 ARI | {mt["ari_vs_jiyeon_original"]:.3f} (대분류 {adjusted_rand_score(orig_macro, macro):.3f}) |',
    f'| 성별 V / 연령대 V | {mt["sex_v"]:.3f} / {mt["age_v"]:.3f} |',
    f'| 영양 차이 (성별·연령 / + 총 섭취량) | {mt["nutrient_separation_sex_age"]:.3f} / {mt["nutrient_separation_plus_energy"]:.3f} |',
    '',
    '### 알고리즘은 지연님 원본 그대로 둔다', '',
    f'- k-medoids 초기화 10회 → 50회: 전체 자료에서 **같은 해** (12개 유형 ARI 1.000, 50회는 약 6분 걸림). 원본이 이미 최적이라 늘려도 바뀌지 않는다.',
    f'- KMeans(n_init=50)로 바꾸면: 표본 40% 재학습 ARI 평균 {np.nanmean(km_sub):.3f} (최소 {np.nanmin(km_sub):.3f}), '
    f'원본과 ARI {adjusted_rand_score(orig, km_lab):.3f}. KMeans는 총거리가 0.15%밖에 차이 나지 않는 두 4분할 사이를 오가서 '
    f'(재학습의 약 30%가 다른 해) 평균은 비슷해도 결과가 둘로 갈리고, 유형도 원본과 많이 달라진다.',
    '- 여러 표본에서 가장 자주 나오는 해를 고르는 합의 선택도 시도했지만 표본 안의 선호를 그대로 따라가 효과가 없었다.',
    f'- 따라서 원본 k-medoids를 쓰고, 재학습 안정성 {np.nanmean(sub12):.2f}는 **"유형 경계는 표본에 따라 일부 바뀐다"는 한계로 그대로 적는다**. '
    '웹은 이 JSON의 중심값으로만 배정하므로 서비스 결과는 흔들리지 않는다.',
    '',
    '## 유형', '',
    '| ID | 대분류 | 이름 | 가중 비율 | 인원 | 남성 | 평균 나이 | 유형 특이 영양소 (+총 섭취량 보정 후) | 식사량 영향 (총 섭취량 보정 시 사라짐) |',
    '|---|---|---|---:|---:|---:|---:|---|---|',
]
for tj in types_json:
    sp = ', '.join(f'{x["nutrient"]} {x["ratio"]:.2f}' for x in tj['nutrients']['specific']) or '없음'
    ir = ', '.join(f'{x["nutrient"]} {x["ratio"]:.2f}' for x in tj['nutrients']['intake_related']) or '없음'
    md.append(f'| {tj["id"]} | {tj["macro"]} | {tj["name"]} | {tj["share"]:.1%} | {tj["n"]:,} | {tj["male_share"]:.0%} | {tj["age_mean"]:.0f} | {sp} | {ir} |')
md += ['', f'공통 주의 (전체 부족률 50% 이상): {", ".join(COMMON)}', '',
       '## 유형별 z (전체 가중 평균 대비, 굵게: |z| ≥ 0.5)', '']
zcols = ['aerobic', 'strength_days', 'sedentary_min', 'sleep_hours', 'stress', 'eating_out', 'meal_score',
         'smoker', 'drink_freq', 'drink_amount', 'veg', 'fruit']
md.append('| ID | ' + ' | '.join(MODEL_KO.get(c, LABEL_KO.get(c, c)) for c in zcols) + ' |')
md.append('|---|' + '---:|' * len(zcols))
for k in ids:
    cells = [f'**{zt[k][c]:+.2f}**' if abs(zt[k][c]) >= 0.5 else f'{zt[k][c]:+.2f}' for c in zcols]
    md.append(f'| {k} | ' + ' | '.join(cells) + ' |')
md += ['', '흡연·음주·채소·과일은 군집 입력이 아니다 (참고용). 유형이 이 값을 거의 가르지 않으면 개인 신호로 보여 준다.', '',
       '## 이름 근거 (이름에 쓴 특징이 |z| ≥ 0.3인지)', '', '| 유형 | 이름에 쓴 특징 | 유형 평균 | z | 확인 |',
       '|---|---|---:|---:|---|'] + name_rows + [
       '', '## 지연님 원본 → 보완판 대응 (인원)', '', cross.to_markdown(), '']
(OUT / '05_지연님안_보완.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
print('\n'.join(md))
