"""지연님 12개 유형(Jiyeon/kmedoids_final.py, 11/3)·보완판(05_jiyeon_improved.py)·이번 7개 유형을 같은 사람·같은 지표로 비교
→ output/04_지연님안_비교.md  (05를 먼저 실행해야 data/labels_12.csv가 있다)

지연님 유형은 Jiyeon/kmedoids_model.json + 같은 파일의 assign()으로 재현한다 (지연님 README: 재배정 일치율 100%).
지표
- 유형 수·가장 작은 유형, 변수별 η² (어떤 생활습관을 담는지)
- 성별·연령 대리 정도 (Cramér's V)
- 영양 결과 차이: 성별·연령 보정 / 성별·연령·총 섭취량(에너지 5분위) 보정 — Codex 검토에서 끼니 결식 유형의 차이가 에너지 보정 후 사라짐
- 유형 특이 영양소 수 (비 ≥ 1.2, BH-FDR q < 0.05)
- 시간 분리 AUC (2022–23 학습 → 2024 평가): 성별·연령만 / + 유형 / 15개 응답 그대로
- 안정성: 같은 방식(전처리 고정, 표본 40% 재학습 → 전체 배정, 10회)으로 두 안 모두 측정
"""
import importlib.util
import sys

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency
from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import adjusted_rand_score, roc_auc_score
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from common import (DATA, DOMAINS, EAR_NUTRIENTS, FEATURE_NAMES, OUT, REPO, SEED, Transform, adjusted_ratios,
                    ratio_separation, specific_rows)

N_BOOT = int(sys.argv[1]) if len(sys.argv) > 1 else 10
SUB_FRAC = 0.4

# ── 데이터와 두 안의 라벨 ──
d = pd.read_csv(DATA / 'persons.csv', encoding='utf-8-sig')
mine = pd.read_csv(DATA / 'labels.csv', encoding='utf-8-sig').rename(columns={'type': 'mine'})

spec = importlib.util.spec_from_file_location('jiyeon_km', REPO / 'Jiyeon' / 'kmedoids_final.py')
jm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jm)
import json  # noqa: E402

import twolevel  # noqa: E402

IMP_METHOD, IMP_N_INIT = 'kmedoids', 10  # 05_jiyeon_improved.py와 같게

jmodel = json.loads((REPO / 'Jiyeon' / 'kmedoids_model.json').read_text(encoding='utf-8'))
jdf = pd.read_csv(REPO / 'Jiyeon' / 'KNHANES_2022_2024_ML_CLUSTER_COMPLETECASE.csv', encoding='utf-8-sig')
jdf['jiyeon'] = jm.assign(jdf, jmodel)
jdf['jiyeon_macro'] = jdf['jiyeon'].str.rsplit('_', n=1).str[0]
jcount = jdf['jiyeon'].value_counts()
jnames = {k: v['name'] for k, v in jmodel['types'].items()}
jnames.update({t['id']: t['name'] for t in json.loads((OUT / 'nbti_12types.json').read_text(encoding='utf-8'))['types']})
json_counts_ok = all(jcount.get(k, 0) == v['n'] for k, v in jmodel['types'].items())

improved = pd.read_csv(DATA / 'labels_12.csv', encoding='utf-8-sig').rename(columns={'type': 'improved'})
d = d.merge(mine, on='ID').merge(jdf[['ID', 'jiyeon', 'jiyeon_macro']], on='ID').merge(improved, on='ID')
d['age_grp'] = pd.Categorical(d['age_grp'])
n_common = len(d)
diet = d['N_EN'].notna().to_numpy()
LABELS = {'이번 7개': 'mine', '지연님 12개': 'jiyeon', '지연님 대분류 4개': 'jiyeon_macro', '지연님 12개 보완': 'improved'}


# ── 지표 함수 ──
def cramers_v(a, b):
    ct = pd.crosstab(a, b)
    chi2 = chi2_contingency(ct)[0]
    return float(np.sqrt(chi2 / (ct.to_numpy().sum() * (min(ct.shape) - 1))))


def eta2(lab):
    Z = StandardScaler().fit_transform(d[FEATURE_NAMES].to_numpy(float))
    out = {}
    for j, f in enumerate(FEATURE_NAMES):
        s = pd.Series(Z[:, j])
        out[f] = 1 - (s.groupby(lab).var(ddof=0) * s.groupby(lab).size()).sum() / (s.var(ddof=0) * len(s))
    return out


dd = d[diet].reset_index(drop=True)
dd['energy_q'] = pd.qcut(dd['N_EN'], 5, labels=False)


def ratios(lab, strata):
    return adjusted_ratios(dd, lab, strata)


separation, specific = ratio_separation, specific_rows


# 시간 분리 AUC: 2022–23 학습 → 2024 평가, EAR 영양소 평균
tr = (dd['year'] < 2024).to_numpy()
te = ~tr
demo = OneHotEncoder(handle_unknown='ignore').fit(dd[['sex', 'age_grp']].astype(str))


def auc_with(extra):
    aucs = []
    for n in EAR_NUTRIENTS:
        y = dd[f'below_{n}'].to_numpy()
        Xd = demo.transform(dd[['sex', 'age_grp']].astype(str)).toarray()
        X = Xd if extra is None else np.hstack([Xd, extra])
        clf = LogisticRegression(max_iter=2000).fit(X[tr], y[tr])
        aucs.append(roc_auc_score(y[te], clf.predict_proba(X[te])[:, 1]))
    return float(np.mean(aucs))


auc_demo = auc_with(None)
auc_raw = auc_with(StandardScaler().fit(dd.loc[tr, FEATURE_NAMES]).transform(dd[FEATURE_NAMES]))
auc_type = {k: auc_with(OneHotEncoder(handle_unknown='ignore').fit_transform(dd[[c]].astype(str)).toarray())
            for k, c in LABELS.items()}

# ── 안정성: 두 안 모두 '전처리 고정 → 표본 40%로 재학습 → 전체 배정' 10회 ──
rng = np.random.default_rng(SEED)
tf = Transform().fit(d)
tf.weights = np.ones(len(FEATURE_NAMES))
Xm = tf.transform(d)
X_j, M_j, _ = jm.build_matrix(jdf.merge(d[['ID']], on='ID'))
from sklearn.decomposition import PCA  # noqa: E402

Q_j = PCA(n_components=5, random_state=jm.RANDOM_STATE).fit(M_j).transform(M_j)
jfull = jdf.merge(d[['ID']], on='ID')['jiyeon'].to_numpy()
jfull_macro = pd.Series(jfull).str.rsplit('_', n=1).str[0].to_numpy()
mfull = d['mine'].to_numpy()


def jiyeon_refit(idx, seed):
    D = jm.pairwise_dist(Q_j[idx])
    med, _ = jm.kmedoids(D, 4, seed=seed, n_init=10)
    lab_s = np.argmin(D[med], axis=0)
    role = jm.name_macro(M_j[idx], lab_s)
    centers = Q_j[idx][med]
    macro_all = np.argmin(((Q_j[:, None, :] - centers[None]) ** 2).sum(2), axis=1)
    out = np.empty(len(Q_j), dtype=object)
    for g in range(4):
        cols, k = jm.SUB_PLAN[role[g]]
        ci = [jm.MODEL_FEATURES.index(c) for c in cols]
        B = M_j[idx][lab_s == g][:, ci]
        bm, bs = B.mean(0), B.std(0)
        Bz = (B - bm) / bs
        Ds = jm.pairwise_dist(Bz)
        smed, _ = jm.kmedoids(Ds, k, seed=seed, n_init=10)
        sc = Bz[smed]
        sel = np.flatnonzero(macro_all == g)
        V = (M_j[sel][:, ci] - bm) / bs
        out[sel] = [f'{role[g]}_{s}' for s in np.argmin(((V[:, None, :] - sc[None]) ** 2).sum(2), axis=1)]
    return out, np.array([role[g] for g in macro_all])


# 보완판이 원본과 같은 사람 배정이면(유형은 그대로, 이름·문구만 보완) 안정성도 같으므로 다시 재지 않는다
same_as_jiyeon = adjusted_rand_score(d['jiyeon'], d['improved']) > 0.999
if not same_as_jiyeon:
    imp_ref = twolevel.assign(twolevel.fit(Q_j, M_j, np.arange(len(Q_j)), SEED, IMP_METHOD, IMP_N_INIT), Q_j, M_j)[0]
stab = {k: [] for k in LABELS}
for b in range(N_BOOT):
    idx = rng.choice(n_common, int(n_common * SUB_FRAC), replace=False)
    km = KMeans(n_clusters=7, n_init=50, random_state=b).fit(Xm[idx])
    stab['이번 7개'].append(adjusted_rand_score(mfull, km.predict(Xm)))
    j12, j4 = jiyeon_refit(idx, b)
    stab['지연님 12개'].append(adjusted_rand_score(jfull, j12))
    stab['지연님 대분류 4개'].append(adjusted_rand_score(jfull_macro, j4))
    stab['지연님 12개 보완'].append(stab['지연님 12개'][-1] if same_as_jiyeon else adjusted_rand_score(
        imp_ref, twolevel.assign(twolevel.fit(Q_j, M_j, idx, b, IMP_METHOD, IMP_N_INIT), Q_j, M_j)[0]))
    print(b, {k: round(v[-1], 3) for k, v in stab.items()}, flush=True)

# ── 표 만들기 ──
rows = []
detail = {}
for k, c in LABELS.items():
    lab = d[c].to_numpy()
    e = eta2(lab)
    r_sa = ratios(dd[c].to_numpy(), ['sex', 'age_grp'])
    r_en = ratios(dd[c].to_numpy(), ['sex', 'age_grp', 'energy_q'])
    detail[k] = (r_sa, r_en)
    size = pd.Series(lab).value_counts(normalize=True)
    rows.append({
        '안': k, '유형 수': len(size), '가장 작은 유형': f'{size.min():.1%}',
        '안정성 ARI (40%×' + str(N_BOOT) + ')': f'{np.mean(stab[k]):.3f} (최소 {np.min(stab[k]):.3f})',
        '흡연·음주 η²': round(np.mean([e[f] for f in FEATURE_NAMES if DOMAINS[f] in ('흡연', '음주')]), 2),
        '운동 η²': round(np.mean([e[f] for f in FEATURE_NAMES if DOMAINS[f] == '신체활동']), 2),
        '식사·외식 η²': round(np.mean([e[f] for f in FEATURE_NAMES if DOMAINS[f] in ('식사', '외식')]), 2),
        '좌식·수면·스트레스 η²': round(np.mean([e[f] for f in FEATURE_NAMES if DOMAINS[f] in ('좌식', '수면', '스트레스')]), 2),
        '채소·과일 η²': round(np.mean([e[f] for f in FEATURE_NAMES if DOMAINS[f] == '채소과일']), 2),
        '성별 V': round(cramers_v(lab, d['sex']), 3), '연령대 V': round(cramers_v(lab, d['age_grp']), 3),
        '영양 차이(성별·연령)': round(separation(r_sa), 3),
        '영양 차이(+에너지)': round(separation(r_en), 3),
        '특이 영양소 건수(성별·연령)': len(specific(r_sa)), '특이 영양소 건수(+에너지)': len(specific(r_en)),
        '2024 AUC(성별·연령+유형)': round(auc_type[k], 3),
    })
tbl = pd.DataFrame(rows)


def spec_lines(k):
    r_sa, r_en = detail[k]
    out = []
    for lab_, g in specific(r_en).groupby('label'):
        out.append(f'- {lab_} {jnames.get(lab_, "")}: ' + ', '.join(f'{n} {x:.2f}' for n, x in zip(g['nutrient'], g['ratio'])))
    return out or ['- 없음']


md = ['# 지연님 12개 유형(원본·보완판) vs 이번 7개 유형', '',
      f'같은 사람 {n_common:,}명 (두 안 공통). 지연님 유형은 kmedoids_model.json으로 재현 '
      f'(JSON 인원이 README와 {"일치" if json_counts_ok else "불일치"}).', '',
      tbl.set_index('안').T.to_markdown(), '',
      '- η²: 유형이 그 변수를 얼마나 가르는지 (0~1, 영역 평균)',
      '- 영양 차이: EAR 영양소별 log(간접 표준화비)의 가중 표준편차 평균. "+에너지"는 성별·연령·총 섭취량 5분위까지 같은 사람과 비교',
      '- 특이 영양소: 비 ≥ 1.2이고 BH-FDR q < 0.05 (15개 영양소 × 유형 수 비교)',
      f'- 2024 AUC 기준선: 성별·연령만 {auc_demo:.3f} / 15개 응답 그대로 + 성별·연령 {auc_raw:.3f}',
      f'- 안정성: 전처리 고정, 표본 {SUB_FRAC:.0%}로 재학습해 전체 배정, 원래 결과와 ARI. 이번 안 KMeans n_init=50, 지연님 안 원본 kmedoids(n_init=10), 보완판 ' + f'{IMP_METHOD}(n_init={IMP_N_INIT})', '',
      '## 에너지까지 보정해도 남는 유형 특이 영양소', '', '### 이번 7개'] + spec_lines('이번 7개') + [
      '', '### 지연님 12개'] + spec_lines('지연님 12개') + ['', '### 지연님 대분류 4개'] + spec_lines('지연님 대분류 4개') + [
      '', '### 지연님 12개 보완'] + spec_lines('지연님 12개 보완') + [
      '', '## 두 안의 관계', '', f'- 이번 7개 vs 지연님 12개 ARI {adjusted_rand_score(d["mine"], d["jiyeon"]):.3f}',
      f'- 지연님 원본 12개 vs 보완판 ARI {adjusted_rand_score(d["jiyeon"], d["improved"]):.3f}',
      f'- 이번 7개 vs 보완판 ARI {adjusted_rand_score(d["mine"], d["improved"]):.3f}',
      f'- 지연님 유형 인원: ' + ', '.join(f'{k} {v:,}' for k, v in jcount.sort_index().items())]
(OUT / '04_지연님안_비교.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
print('\n'.join(md))
