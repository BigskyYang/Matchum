# -*- coding: utf-8 -*-
"""12유형 → 부족 영양소 흐름 추가 검증 (2026-11-05, 최지연)

실행: python 추가검증.py [재현|경계|판정|섞기] [섞기 횟수, 기본 200]

기준은 결과를 보기 전에 아래와 같이 정했다. 모델·유형·화면 규칙은 바꾸지 않고 평가만 한다.

[재현] 다음이 기존 값과 같아야 뒤의 결과를 믿는다.
  - 판정표 = nbti_12types.json, ΔAUC = 보고서 그림(칼슘 +0.040 등), 유의 13/15,
    (나)안 O/E 1.087과 판정별 1.36 / 1.24 / 1.04

[경계] 경계 여유 = (d2 - d1) / d2, 대분류·세부 중 작은 값 (bigskyyang 07_boundary.py와 같음)
  - 구분: 경계 < 10%, 중간 10~30%, 핵심 >= 30%  (원본 진단 코드가 없어 인원수로 대조)
  - 판정: 핵심-경계의 영양소 평균 ΔAUC와 AUC 차이의 95% CI가 0을 포함하면 "차이 확인 안 됨"
  - AUC는 성별·나이 효과를 포함하므로, 유형의 기여는 그룹 안의 ΔAUC로 본다

[판정] 2022-23 자료만으로 판정을 다시 만들고 2024년에서 O/E 확인
  - 판정 규칙은 05_jiyeon_improved.py와 같다 (1.2배, BH-FDR q<0.05, 180개 검정)
  - 판정 순서 유지: 유형 고유 > 식사량 관련 > 흔함, 각 CI는 사람 단위 부트스트랩 2,000회
  - 판단: 유형 고유 또는 식사량 관련의 O/E CI 하한이 1보다 크면 그 판정이 새 연도에도 유지

[섞기] 같은 성별×연령대×연도 안에서 유형 라벨을 섞고 같은 절차를 200회 반복
  - 통과: 섞은 자료의 평균 O/E 0.98~1.02, 평균 ΔAUC 절댓값 0.005 미만 (절차가 없는 신호를 만들지 않음)
  - 통과: 실제 값이 섞은 자료의 최댓값보다 큼 (유형 신호가 우연보다 큼)
  - 영양소별 순열 p는 (1 + 실제 이하가 아닌 횟수) / (R + 1), BH 보정
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import poisson
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / 'Jiyeon'))
sys.path.insert(0, str(REPO / 'Yuhwan' / '영양분석'))
from kmedoids_final import SLEEP_REF_YEAR, assign  # noqa: E402
from common import AGE_BINS, AGE_LABELS, KDRI, NUTRIENTS  # noqa: E402

SEED = 42
P_MAIN, RATIO_CUT, P_FLOOR = 0.5, 1.2, 0.3
G2ID = {'G0-0': 'N1', 'G0-1': 'N2', 'G0-2': 'N3', 'G1-1': 'A1', 'G1-0': 'A2', 'G1-2': 'A3',
        'G2-1': 'S1', 'G2-0': 'S2', 'G2-2': 'S3', 'G3-0': 'O1', 'G3-1': 'O2', 'G3-2': 'O3'}
JM = json.load(open(REPO / 'Jiyeon' / 'kmedoids_model.json', encoding='utf-8'))
NB = json.load(open(REPO / 'bigskyyang' / 'analysis' / 'output' / 'nbti_12types.json', encoding='utf-8'))
IDS = [t['id'] for t in NB['types']]
COMMON = [c['nutrient'] for c in NB['common_nutrients']]
OTHER = [n for n in NUTRIENTS if n not in COMMON]
# 08번이 2022-23 교차검증으로 고른 설정 (README v8, 보고서 첨부 D). 재현 단계에서 확인한다
C_01 = {'단백질', '엽산', '마그네슘', '식이섬유'}


def margins(raw):
    """사람마다 경계 여유: 대분류·세부 공간 중 작은 값."""
    F = JM['features']
    X = raw[F].values.astype(float)
    by = {str(k): v for k, v in JM['sleep_year_adjust']['by_year'].items()}
    ref, i = by[str(SLEEP_REF_YEAR)], F.index('ML_sleep_hours')
    yr = raw['year'].values.astype(int).astype(str)
    X[:, i] = [(s - by[y]['mean']) / by[y]['std'] * ref['std'] + ref['mean'] for s, y in zip(X[:, i], yr)]
    z = (X - np.array(JM['scaler']['mean'])) / np.array(JM['scaler']['std'])
    mv = z @ np.array(JM['projection']['A']).T + np.array(JM['projection']['b'])
    pc = (mv - np.array(JM['pca']['mean'])) @ np.array(JM['pca']['components']).T

    def mg(V, C):
        d = np.sqrt(((V[:, None, :] - C[None]) ** 2).sum(2))
        near = d.argmin(1)
        d.sort(axis=1)
        return (d[:, 1] - d[:, 0]) / d[:, 1], near
    keys = list(JM['macro']['medoids'])
    m_macro, near = mg(pc, np.array([JM['macro']['medoids'][k] for k in keys]))
    m_sub = np.empty(len(X))
    for i_k, k in enumerate(keys):
        sel = np.flatnonzero(near == i_k)
        s = JM['sub'][k]
        V = mv[np.ix_(sel, [JM['model_features'].index(c) for c in s['features']])]
        V = (V - np.array(s['scaler']['mean'])) / np.array(s['scaler']['std'])
        m_sub[sel] = mg(V, np.array(list(s['medoids'].values())))[0]
    return np.minimum(m_macro, m_sub)


def load():
    raw = pd.read_csv(REPO / 'Jiyeon' / 'KNHANES_2022_2024_ML_CLUSTER_COMPLETECASE.csv', encoding='utf-8-sig')
    g = pd.Series(assign(raw, JM)).str.replace(r'^(G\d)_.*_(\d)$', r'\1-\2', regex=True)
    lab = pd.DataFrame({'ID': raw['ID'], 'cluster': g.map(G2ID).values, 'margin': margins(raw)})
    base = pd.read_csv(REPO / 'Jiyeon' / 'KNHANES_2022_2024_ANALYSIS_BASE.csv', encoding='utf-8-sig', low_memory=False)
    d = lab.merge(base, on='ID', how='inner')
    assert len(d) == len(raw)
    d['sex'] = d['설명_sex'].map({1: '남자', 2: '여자'})
    d['age'] = d['설명_age']
    d['age_grp'] = pd.cut(d['age'], AGE_BINS, labels=AGE_LABELS)
    d['age_grp_s'] = d['age_grp'].astype(str)
    d['male'] = (d['sex'] == '남자').astype(int)
    d['w'] = d['wt_tot'] / 3
    d['w_n'] = d['w'] / d['w'].mean()
    idx, male = d['age_grp'].cat.codes.values, d['male'].values == 1
    new = {}
    for n, (col, _, m, f, *_r) in KDRI.items():
        ref = np.where(male, np.array(m)[idx], np.array(f)[idx]).astype(float)
        new[f'below_{n}'] = (d[col].values < ref).astype(int)
    return pd.concat([d, pd.DataFrame(new, index=d.index)], axis=1)


def make_model(n):
    """(입력 열, 파이프라인)"""
    oh = lambda cols: ColumnTransformer([('oh', OneHotEncoder(drop='first', handle_unknown='ignore'), cols)])
    if n == '철':
        return ['male', 'age', 'cluster'], Pipeline([
            ('p', ColumnTransformer([('ord', OrdinalEncoder(), ['cluster'])], remainder='passthrough')),
            ('m', HistGradientBoostingClassifier(learning_rate=0.05, max_leaf_nodes=7, min_samples_leaf=100, max_iter=200,
                                                 categorical_features=[0], early_stopping=False, random_state=SEED))])
    C = 0.1 if n in C_01 else 0.01
    cols = ['sex', 'age_grp_s', 'cluster']
    return cols, Pipeline([('p', oh(cols)), ('m', LogisticRegression(C=C, max_iter=3000))])


def base_model():
    cols = ['sex', 'age_grp_s']
    return cols, Pipeline([('p', ColumnTransformer([('oh', OneHotEncoder(drop='first', handle_unknown='ignore'), cols)])),
                           ('m', LogisticRegression(max_iter=3000))])


def make_grid(d, tr):
    grid = pd.MultiIndex.from_product([IDS, ['남자', '여자'], AGE_LABELS], names=['cluster', 'sex', 'age_grp_s']).to_frame(index=False)
    grid['male'] = (grid['sex'] == '남자').astype(int)
    grid['age'] = grid['age_grp_s'].map(d[tr].groupby('age_grp_s').apply(lambda g: np.average(g['age'], weights=g['w']), include_groups=False))
    return grid


def base_preds(d, tr, te, grid):
    out = {}
    for n in NUTRIENTS:
        y = d[f'below_{n}']
        c, m = base_model()
        m.fit(d.loc[tr, c], y[tr], m__sample_weight=d.loc[tr, 'w_n'].values)
        out[n] = (m.predict_proba(d.loc[te, c])[:, 1], m.predict_proba(grid[c])[:, 1])
    return out


def fit_preds(d, tr, te, grid, nutrients=NUTRIENTS):
    out = {}
    for n in nutrients:
        y = d[f'below_{n}']
        c, m = make_model(n)
        m.fit(d.loc[tr, c], y[tr], m__sample_weight=d.loc[tr, 'w_n'].values)
        out[n] = (m.predict_proba(d.loc[te, c])[:, 1], m.predict_proba(grid[c])[:, 1])
    return out


def pick_items(grid, preds, base, other=OTHER):
    rows = []
    for n in other:
        p, pb = preds[n][1], base[n][1]
        keep = (p >= P_MAIN) | ((p / pb >= RATIO_CUT) & (p >= P_FLOOR))
        t = grid.loc[keep, ['cluster', 'sex', 'age_grp_s']].copy()
        t['영양소'] = n
        t['예측배수'] = (p / pb)[keep]
        rows.append(t)
    return pd.concat(rows, ignore_index=True)


def item_arrays(items, t24, weights=None):
    """항목마다 (칸 여부, 같은 성별·나이 여부, y) 배열"""
    w = t24['w'].values if weights is None else weights
    cl, sx, ag = t24['cluster'].values, t24['sex'].values, t24['age_grp_s'].values
    arr = []
    for r in items.itertuples():
        sa = (sx == r.sex) & (ag == r.age_grp_s)
        cell = sa & (cl == r.cluster)
        if cell.any():
            arr.append((cell, sa, t24[f'below_{r.영양소}'].values, r.Index))
    return arr, w


def oe(arr, w):
    O = E = 0.0
    for cell, sa, y, _ in arr:
        O += (w[cell] * y[cell]).sum()
        E += (w[sa] * y[sa]).sum() / w[sa].sum() * w[cell].sum()
    return O / E if E else np.nan


def oe_person_ci(arr, w, B=2000, seed=SEED):
    rng = np.random.default_rng(seed)
    n = len(w)
    out = np.empty(B)
    for b in range(B):
        c = np.bincount(rng.integers(0, n, n), minlength=n) * w
        O = E = 0.0
        for cell, sa, y, _ in arr:
            O += (c[cell] * y[cell]).sum()
            s = c[sa].sum()
            E += (c[sa] * y[sa]).sum() / s * c[cell].sum() if s else 0
        out[b] = O / E if E else np.nan
    return np.nanpercentile(out, [2.5, 97.5])


def oe_item_ci(arr, w, B=2000, seed=SEED):
    """13번 코드와 같은 항목 단위 부트스트랩"""
    O = np.array([(w[c] * y[c]).sum() for c, s, y, _ in arr])
    E = np.array([(w[s] * y[s]).sum() / w[s].sum() * w[c].sum() for c, s, y, _ in arr])
    rng = np.random.default_rng(seed)
    b = [O[i].sum() / E[i].sum() for i in (rng.integers(0, len(O), len(O)) for _ in range(B))]
    return np.percentile(b, [2.5, 97.5])


def adjusted_ratios(dd, strata):
    """05번 common.adjusted_ratios와 같은 계산"""
    rows = []
    for n in NUTRIENTS:
        col = f'below_{n}'
        t = dd[strata + [col, 'cluster']].copy()
        t['exp'] = t.groupby(strata, observed=True)[col].transform('mean')
        g = t.groupby('cluster')
        r = pd.DataFrame({'obs': g[col].sum(), 'exp': g['exp'].sum(), 'n': g[col].size()})
        r['ratio'] = r['obs'] / r['exp']
        r['p'] = [2 * min(poisson.cdf(o, e), poisson.sf(o - 1, e)) for o, e in zip(r['obs'], r['exp'])]
        r['nutrient'] = n
        rows.append(r.reset_index())
    r = pd.concat(rows, ignore_index=True)
    order = np.argsort(r['p'].to_numpy())
    m = len(r)
    q = np.empty(m)
    q[order] = np.minimum.accumulate((r['p'].to_numpy()[order] * m / np.arange(1, m + 1))[::-1])[::-1]
    r['q'] = np.minimum(q, 1)
    return r


def make_tags(dd):
    dd = dd[dd['영양_N_EN'].notna()].copy()
    dd['energy_q'] = pd.qcut(dd['영양_N_EN'], 5, labels=False)
    r_sa = adjusted_ratios(dd, ['sex', 'age_grp'])
    r_en = adjusted_ratios(dd, ['sex', 'age_grp', 'energy_q'])
    hit = lambda r: {(a, b) for a, b in zip(*[r.loc[(r['ratio'] >= RATIO_CUT) & (r['q'] < 0.05), c] for c in ('cluster', 'nutrient')])}
    spec = hit(r_en)
    intake = hit(r_sa) - spec
    return spec, intake, r_sa, r_en


def json_tags():
    spec, intake = set(), set()
    for t in NB['types']:
        spec |= {(t['id'], x['nutrient']) for x in t['nutrients']['specific']}
        intake |= {(t['id'], x['nutrient']) for x in t['nutrients']['intake_related']}
    return spec, intake


def label_of(r, spec, intake):
    return '유형 고유' if (r.cluster, r.영양소) in spec else '식사량 관련' if (r.cluster, r.영양소) in intake else '흔함'


def oe_by_tag(items, t24, spec, intake, ci=True):
    t = items.assign(판정=[label_of(r, spec, intake) for r in items.itertuples()])
    rows = []
    for name in ['전체', '유형 고유', '식사량 관련', '흔함']:
        sub = t if name == '전체' else t[t['판정'] == name]
        if sub.empty:
            rows.append(dict(판정=name, 항목수=0))
            continue
        arr, w = item_arrays(sub, t24)
        row = dict(판정=name, 항목수=len(arr), OE=oe(arr, w))
        if ci:
            lo, hi = oe_person_ci(arr, w)
            row.update(사람CI_low=lo, 사람CI_high=hi)
            if len(arr) > 1:
                il, ih = oe_item_ci(arr, w)
                row.update(항목CI_low=il, 항목CI_high=ih)
        rows.append(row)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ 단계별 실행
def run_check(d, tr, te, grid, base, preds):
    print('\n[재현 1] 유형 인원 (JSON 대비 차이)')
    n = d['cluster'].value_counts()
    print({t['id']: int(n[t['id']] - t['n']) for t in NB['types']})
    print('\n[재현 2] 판정표 (전체 연도 vs JSON)')
    s, i, *_ = make_tags(d)
    js, ji = json_tags()
    print('유형 고유: 같음' if s == js else f'유형 고유 차이: 재현만 {s - js}, JSON만 {js - s}')
    print('식사량 관련: 같음' if i == ji else f'식사량 관련 차이: 재현만 {i - ji}, JSON만 {ji - i}')
    print('\n[재현 3] 2024 ΔAUC (부트스트랩 1,000회)')
    t = d.loc[te]
    rows = []
    for nu in NUTRIENTS:
        y, w = t[f'below_{nu}'].values, t['w_n'].values
        p1, p0 = preds[nu][0], base[nu][0]
        a1, a0 = roc_auc_score(y, p1, sample_weight=w), roc_auc_score(y, p0, sample_weight=w)
        rng = np.random.default_rng(SEED)
        bs = []
        for _ in range(1000):
            ix = rng.integers(0, len(y), len(y))
            bs.append(roc_auc_score(y[ix], p1[ix], sample_weight=w[ix]) - roc_auc_score(y[ix], p0[ix], sample_weight=w[ix]))
        lo, hi = np.percentile(bs, [2.5, 97.5])
        rows.append(dict(영양소=nu, M0=a0, 유형=a1, ΔAUC=a1 - a0, low=lo, high=hi))
    r = pd.DataFrame(rows).sort_values('ΔAUC', ascending=False)
    print(r.round(3).to_string(index=False))
    print('유의 개수', int((r['low'] > 0).sum()))
    r.to_csv(HERE / '결과_재현_ΔAUC.csv', index=False, encoding='utf-8-sig')
    print('\n[재현 4] (나)안 O/E, 전체 연도 판정')
    items = pick_items(grid, preds, base)
    print(oe_by_tag(items, t, js, ji).round(3).to_string(index=False))


def run_boundary(d, te, base, preds):
    t = d.loc[te].reset_index(drop=True)
    grp = np.where(t['margin'] < 0.1, '경계', np.where(t['margin'] >= 0.3, '핵심', '중간'))
    groups = ['핵심', '중간', '경계']
    print('인원 (기존 문서: 핵심 2,343 / 중간 2,010 / 경계 967):', {g: int((grp == g).sum()) for g in groups})
    rows = []
    for n in NUTRIENTS:
        y, w = t[f'below_{n}'].values, t['w_n'].values
        for g in groups:
            m = grp == g
            a1 = roc_auc_score(y[m], preds[n][0][m], sample_weight=w[m])
            a0 = roc_auc_score(y[m], base[n][0][m], sample_weight=w[m])
            obs, ex = np.average(y[m], weights=w[m]), np.average(preds[n][0][m], weights=w[m])
            rows.append(dict(영양소=n, 구분=g, n=int(m.sum()), AUC=a1, M0=a0, ΔAUC=a1 - a0, 실제부족률=obs, 예측부족률=ex, 보정오차=ex - obs))
    r = pd.DataFrame(rows)
    r.to_csv(HERE / '결과_경계_영양소별.csv', index=False, encoding='utf-8-sig')
    print(r.pivot(index='영양소', columns='구분', values='AUC')[groups].round(3).to_string())
    print('\n[평균]')
    avg = r.groupby('구분')[['AUC', 'M0', 'ΔAUC']].mean().loc[groups]
    avg['보정오차_절댓값평균'] = r.assign(a=r['보정오차'].abs()).groupby('구분')['a'].mean()
    avg['보정오차_최대'] = r.assign(a=r['보정오차'].abs()).groupby('구분')['a'].max()
    print(avg.round(3).to_string())

    # 사람 단위 부트스트랩: 핵심-경계 차이
    rng = np.random.default_rng(SEED)
    B = 500
    N = len(t)
    Y = {n: t[f'below_{n}'].values for n in NUTRIENTS}
    W = t['w_n'].values
    boot = []
    for _ in range(B):
        ix = rng.integers(0, N, N)
        g = grp[ix]
        res = {k: {'AUC': [], 'Δ': []} for k in groups}
        for n in NUTRIENTS:
            y, w, p1, p0 = Y[n][ix], W[ix], preds[n][0][ix], base[n][0][ix]
            for k in groups:
                m = g == k
                a1 = roc_auc_score(y[m], p1[m], sample_weight=w[m])
                res[k]['AUC'].append(a1)
                res[k]['Δ'].append(a1 - roc_auc_score(y[m], p0[m], sample_weight=w[m]))
        boot.append(dict(AUC차이=np.mean(res['핵심']['AUC']) - np.mean(res['경계']['AUC']),
                         Δ차이=np.mean(res['핵심']['Δ']) - np.mean(res['경계']['Δ']),
                         핵심Δ=np.mean(res['핵심']['Δ']), 중간Δ=np.mean(res['중간']['Δ']), 경계Δ=np.mean(res['경계']['Δ'])))
    b = pd.DataFrame(boot)
    print('\n[95% CI, 부트스트랩 500회]')
    print(b.quantile([.025, .975]).round(4).to_string())
    print('핵심-경계 AUC 차이', round(avg.loc['핵심', 'AUC'] - avg.loc['경계', 'AUC'], 4),
          '| ΔAUC 차이', round(avg.loc['핵심', 'ΔAUC'] - avg.loc['경계', 'ΔAUC'], 4))
    b.quantile([.025, .975]).to_csv(HERE / '결과_경계_CI.csv', encoding='utf-8-sig')


def run_tags(d, tr, te, grid, base, preds):
    t = d.loc[te].reset_index(drop=True)
    d2 = d.loc[tr]
    s_all, i_all = json_tags()
    s_new, i_new, *_ = make_tags(d2)
    print('2022-23 판정')
    print('유형 고유:', sorted(s_new))
    print('식사량 관련:', sorted(i_new))
    print('전체 연도 유형 고유:', sorted(s_all))
    print('전체 연도 식사량 관련:', sorted(i_all))
    print('유형 고유 유지/빠짐/새로:', len(s_all & s_new), sorted(s_all - s_new), sorted(s_new - s_all))
    print('식사량 관련 유지/빠짐/새로:', len(i_all & i_new), sorted(i_all - i_new), sorted(i_new - i_all))
    rates = {n: float(np.average(d2[f'below_{n}'], weights=d2['w'])) for n in NUTRIENTS}
    common_new = [n for n in NUTRIENTS if rates[n] >= 0.5]
    print('2022-23 부족률:', {k: round(v, 3) for k, v in rates.items()})
    print('공통 8개와 같은가:', set(common_new) == set(COMMON), '| 2022-23 공통:', common_new)

    items = pick_items(grid, preds, base)
    print('\n[기존 공통 8개, 2022-23 판정으로 2024 O/E]')
    a = oe_by_tag(items, t, s_new, i_new)
    print(a.round(3).to_string(index=False))
    print('\n[비교: 같은 항목, 전체 연도 판정]')
    c = oe_by_tag(items, t, s_all, i_all)
    print(c.round(3).to_string(index=False))
    out = pd.concat([a.assign(판정기준='2022-23'), c.assign(판정기준='전체 연도')])
    if set(common_new) != set(COMMON):
        other2 = [n for n in NUTRIENTS if n not in common_new]
        print('\n[민감도: 공통 목록도 2022-23으로]')
        e = oe_by_tag(pick_items(grid, preds, base, other2), t, s_new, i_new)
        print(e.round(3).to_string(index=False))
        out = pd.concat([out, e.assign(판정기준='2022-23 + 공통 목록도')])
    out.to_csv(HERE / '결과_판정_OE.csv', index=False, encoding='utf-8-sig')

    # 2024년 안에서 판정 자체가 유지되는가 (2줄 규칙과 무관, 같은 판정 기준의 비)
    t2 = t[t['영양_N_EN'].notna()].copy()
    t2['energy_q'] = pd.qcut(t2['영양_N_EN'], 5, labels=False)
    sa = adjusted_ratios(t2, ['sex', 'age_grp']).set_index(['cluster', 'nutrient'])
    en = adjusted_ratios(t2, ['sex', 'age_grp', 'energy_q']).set_index(['cluster', 'nutrient'])
    rows = [dict(판정=lb, 유형=k, 영양소=n, 비_성별나이=sa.loc[(k, n), 'ratio'], 비_섭취량까지=en.loc[(k, n), 'ratio'], 인원=int(sa.loc[(k, n), 'n']))
            for lb, st in [('유형 고유', s_new), ('식사량 관련', i_new)] for k, n in sorted(st)]
    r = pd.DataFrame(rows)
    print('\n[2022-23 판정 항목의 2024년 표준화비]')
    print(r.round(3).to_string(index=False))
    if len(r):
        print(r.groupby('판정')[['비_성별나이', '비_섭취량까지']].mean().round(3).to_string())
        print('2024에서 1보다 큰 비율:', r.groupby('판정').apply(lambda g: pd.Series({
            '성별나이>1': (g['비_성별나이'] > 1).mean(), '섭취량까지>1': (g['비_섭취량까지'] > 1).mean()}), include_groups=False).round(3).to_dict('index'))
    r.to_csv(HERE / '결과_판정_2024표준화비.csv', index=False, encoding='utf-8-sig')


def run_shuffle(d, tr, te, grid, base, preds, R):
    t = d.loc[te]
    w = t['w_n'].values
    Y = {n: t[f'below_{n}'].values for n in NUTRIENTS}
    a0 = {n: roc_auc_score(Y[n], base[n][0], sample_weight=w) for n in NUTRIENTS}
    real_d = {n: roc_auc_score(Y[n], preds[n][0], sample_weight=w) - a0[n] for n in NUTRIENTS}
    items = pick_items(grid, preds, base)
    arr, ww = item_arrays(items, t)
    real_oe = oe(arr, ww)
    print(f'실제: O/E {real_oe:.3f} ({len(arr)}개 항목), 평균 ΔAUC {np.mean(list(real_d.values())):.4f}', flush=True)

    rng = np.random.default_rng(SEED)
    keys = d['sex'].astype(str) + d['age_grp_s'] + d['year'].astype(int).astype(str)
    pos = {k: np.flatnonzero(keys.values == k) for k in keys.unique()}
    orig = d['cluster'].values.copy()
    rows = []
    s = d.copy()
    for b in range(R):
        lab = orig.copy()
        for ix in pos.values():
            lab[ix] = orig[rng.permutation(ix)]
        s['cluster'] = lab
        pr = fit_preds(s, tr, te, grid)
        row = {n: roc_auc_score(Y[n], pr[n][0], sample_weight=w) - a0[n] for n in NUTRIENTS}
        it = pick_items(grid, pr, base)
        ar, wa = item_arrays(it, s.loc[te])
        row.update(회차=b, OE=oe(ar, wa), 항목수=len(ar), 평균Δ=np.mean([row[n] for n in NUTRIENTS]))
        rows.append(row)
        if b % 10 == 0:
            print(b, round(row['OE'], 3), row['항목수'], round(row['평균Δ'], 4), flush=True)
            pd.DataFrame(rows).to_csv(HERE / '결과_섞기_회차별.csv', index=False, encoding='utf-8-sig')
    r = pd.DataFrame(rows)
    r.to_csv(HERE / '결과_섞기_회차별.csv', index=False, encoding='utf-8-sig')
    print(f'\n섞은 자료 {R}회')
    print('O/E 평균 %.3f, 범위 %.3f~%.3f, 2.5~97.5%% %.3f~%.3f | 실제 %.3f, 실제 이상 %d회' % (
        r['OE'].mean(), r['OE'].min(), r['OE'].max(), *r['OE'].quantile([.025, .975]), real_oe, (r['OE'] >= real_oe).sum()))
    rd = np.mean(list(real_d.values()))
    print('평균 ΔAUC 평균 %.4f, 범위 %.4f~%.4f | 실제 %.4f, 실제 이상 %d회' % (r['평균Δ'].mean(), r['평균Δ'].min(), r['평균Δ'].max(), rd, (r['평균Δ'] >= rd).sum()))
    print('항목수 평균 %.1f, 범위 %d~%d | 실제 %d' % (r['항목수'].mean(), r['항목수'].min(), r['항목수'].max(), len(arr)))
    ps = pd.DataFrame([dict(영양소=n, 실제Δ=real_d[n], 섞기평균=r[n].mean(), 섞기최대=r[n].max(),
                            p=(1 + (r[n] >= real_d[n]).sum()) / (R + 1)) for n in NUTRIENTS])
    o = np.argsort(ps['p'].values)
    q = np.empty(len(ps))
    q[o] = np.minimum.accumulate((ps['p'].values[o] * len(ps) / np.arange(1, len(ps) + 1))[::-1])[::-1]
    ps['BH_q'] = np.minimum(q, 1)
    print(ps.sort_values('실제Δ', ascending=False).round(4).to_string(index=False))
    print('BH q<0.05 개수', int((ps['BH_q'] < 0.05).sum()))
    ps.to_csv(HERE / '결과_섞기_영양소별.csv', index=False, encoding='utf-8-sig')


if __name__ == '__main__':
    stage = sys.argv[1] if len(sys.argv) > 1 else '재현'
    R = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    d = load()
    print('사람', len(d), '| 연도', d['year'].value_counts().sort_index().to_dict(), flush=True)
    tr, te = d['year'] <= 2023, d['year'] == 2024
    grid = make_grid(d, tr)
    base = base_preds(d, tr, te, grid)
    preds = fit_preds(d, tr, te, grid)
    {'재현': lambda: run_check(d, tr, te, grid, base, preds),
     '경계': lambda: run_boundary(d, te, base, preds),
     '판정': lambda: run_tags(d, tr, te, grid, base, preds),
     '섞기': lambda: run_shuffle(d, tr, te, grid, base, preds, R)}[stage]()
