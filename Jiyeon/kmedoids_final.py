# -*- coding: utf-8 -*-
"""
KNHANES 2022-2024 생활습관 군집화 (개선판)

설계 요약
  1단계(대분류 4개) : 생활습관 7변수 -> 표준화 -> PCA(5) -> K-Medoids(k=4)
  2단계(세부 3개씩) : 대분류마다 서로 다른 2개 변수로 K-Medoids(k=3)  -> 최종 12개 유형
  흡연/음주 5변수는 군집 입력에서 제외(군집을 지배하던 문제). 프로파일 설명용으로만 사용.

개선 내용
  - 초기값: k-medoids++ 초기화 + PAM 계열 swap 탐색 + n_init회 반복 중 최소 비용 선택
  - 전체 거리행렬 사용(샘플링 없음) -> 시드 의존성 제거
  - 수면 변수의 연도별 측정 차이를 2024년 기준으로 보정
  - 군집 이름은 번호에 고정하지 않고 프로파일(z값)에서 자동 생성
  - 웹 연동용 kmedoids_model.json 저장(재배정 일치율 100% 검증)
"""
import json
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from scipy.spatial.distance import cdist

CSV = 'KNHANES_2022_2024_ML_CLUSTER_COMPLETECASE.csv'
OUT_XLSX = 'KMedoids_Lifestyle_12Types.xlsx'
OUT_JSON = 'kmedoids_model.json'
RANDOM_STATE = 42

FEATURES = ['ML_smoker', 'ML_cigarettes_day', 'ML_drink_month', 'ML_drink_freq_ord',
            'ML_drink_amount_ord', 'ML_aerobic', 'ML_strength_days', 'ML_sedentary_min',
            'ML_sleep_hours', 'ML_stress', 'ML_breakfast_freq_ord', 'ML_lunch_freq_ord',
            'ML_dinner_freq_ord', 'ML_eatingout_freq_ord']
MEALS = ['ML_breakfast_freq_ord', 'ML_lunch_freq_ord', 'ML_dinner_freq_ord']
BASE = ['ML_aerobic', 'ML_strength_days', 'ML_sedentary_min', 'ML_sleep_hours',
        'ML_stress', 'ML_eatingout_freq_ord']
MODEL_FEATURES = [c.replace('ML_', '') for c in BASE] + ['meal_score']
SLEEP_REF_YEAR = 2024

# 대분류별 세분화 변수 (군집 내 잔여 분산과 실루엣/안정성 탐색으로 선정)
SUB_PLAN = {'G0_비활동형': (['eatingout_freq_ord', 'meal_score'], 3),
            'G1_운동형': (['strength_days', 'meal_score'], 3),
            'G2_고스트레스형': (['aerobic', 'strength_days'], 3),
            'G3_좌식외식형': (['strength_days', 'meal_score'], 3)}
KOR = {'aerobic': '유산소', 'strength_days': '근력운동', 'sedentary_min': '좌식시간',
       'sleep_hours': '수면', 'stress': '스트레스', 'eatingout_freq_ord': '외식',
       'meal_score': '규칙식사'}


# ------------------------------------------------------------------ K-Medoids
def pairwise_dist(X, chunk=1000):
    n = len(X)
    D = np.empty((n, n), dtype=np.float32)
    for i in range(0, n, chunk):
        D[i:i + chunk] = cdist(X[i:i + chunk], X)
    return D


def kmpp_init(D, k, rng):
    """k-medoids++ : 기존 medoid에서 멀수록 뽑힐 확률이 높은 초기화."""
    n = D.shape[0]
    med = [int(rng.integers(n))]
    dmin = D[med[0]].astype(np.float64)
    for _ in range(1, k):
        c = int(rng.choice(n, p=dmin / dmin.sum()))
        med.append(c)
        dmin = np.minimum(dmin, D[c])
    return np.array(med, dtype=np.int64)


def voronoi(D, med, max_iter=300):
    """각 군집 내 거리합 최소 점으로 medoid 갱신(샘플링 없음)."""
    med = med.copy()
    for _ in range(max_iter):
        labels = np.argmin(D[med], axis=0)
        new = med.copy()
        for c in range(len(med)):
            I = np.flatnonzero(labels == c)
            if len(I) == 0:
                continue
            new[c] = I[np.argmin(D[np.ix_(I, I)].sum(axis=1, dtype=np.float64))]
        if np.array_equal(new, med):
            break
        med = new
    return med


def total_cost(D, med):
    return float(D[med].min(axis=0).sum(dtype=np.float64))


def _state(D, med):
    n = D.shape[0]
    ar = np.arange(n)
    Dm = D[med]
    two = np.argpartition(Dm, 1, axis=0)[:2]
    i0, i1 = Dm[two[0], ar], Dm[two[1], ar]
    near = np.where(i0 <= i1, two[0], two[1])
    onehot = np.zeros((n, len(med)), dtype=np.float32)
    onehot[ar, near] = 1
    return np.minimum(i0, i1), np.maximum(i0, i1), onehot


def swap_polish(D, med, block=500, max_pass=30):
    """PAM 계열 swap 탐색(FasterPAM 방식의 블록 단위 eager swap)."""
    med = med.copy()
    n = D.shape[0]
    dn, ds, onehot = _state(D, med)
    for _ in range(max_pass):
        improved = False
        for s in range(0, n, block):
            Db = D[s:s + block]
            neg = np.minimum(Db - dn, 0)
            acc = neg.sum(axis=1, dtype=np.float64)
            t = np.minimum(Db, ds) - dn - neg
            delta = acc[:, None] + (t @ onehot).astype(np.float64)
            delta[np.isin(np.arange(s, s + len(Db)), med)] = np.inf
            j = np.unravel_index(np.argmin(delta), delta.shape)
            if delta[j] < -1e-6 * float(dn.sum(dtype=np.float64)):
                med[j[1]] = s + j[0]
                dn, ds, onehot = _state(D, med)
                improved = True
        if not improved:
            break
    return med


def kmedoids(D, k, seed=RANDOM_STATE, n_init=10):
    """n_init회 서로 다른 초기값에서 시작해 총거리가 최소인 해를 선택."""
    rng = np.random.default_rng(seed)
    best = None
    for _ in range(n_init):
        med = voronoi(D, swap_polish(D, kmpp_init(D, k, rng)))
        cost = total_cost(D, med)
        if best is None or cost < best[1]:
            best = (med, cost)
    return best


def silhouette(D, labels):
    n = len(labels)
    k = labels.max() + 1
    oh = np.zeros((n, k), dtype=np.float32)
    oh[np.arange(n), labels] = 1
    S = D @ oh
    cnt = oh.sum(0)
    own = S[np.arange(n), labels] / np.maximum(cnt[labels] - 1, 1)
    other = S / cnt
    other[np.arange(n), labels] = np.inf
    b = other.min(1)
    return float(((b - own) / np.maximum(own, b)).mean())


# ------------------------------------------------------------- 전처리(선형만)
def build_matrix(df):
    """원자료 -> 수면 연도보정 -> 표준화 -> 생활습관 7변수. 모두 선형 변환."""
    X = df[FEATURES].values.astype(float)
    year = df['year'].values.astype(int)

    raw_sleep = X[:, FEATURES.index('ML_sleep_hours')].copy()
    by_year = {int(y): {'mean': float(raw_sleep[year == y].mean()),
                        'std': float(raw_sleep[year == y].std())}
               for y in np.unique(year)}
    ref = by_year[SLEEP_REF_YEAR]
    X[:, FEATURES.index('ML_sleep_hours')] = np.array(
        [(raw_sleep[i] - by_year[year[i]]['mean']) / by_year[year[i]]['std'] * ref['std'] + ref['mean']
         for i in range(len(raw_sleep))])

    mean, std = X.mean(0), X.std(0)
    Zs = (X - mean) / std

    meal_raw = Zs[:, [FEATURES.index(c) for c in MEALS]].mean(1)
    meal_mu, meal_sd = meal_raw.mean(), meal_raw.std()
    M = np.column_stack([Zs[:, [FEATURES.index(c) for c in BASE]],
                         (meal_raw - meal_mu) / meal_sd])

    # 표준화된 14변수 z -> 7변수: model = A @ z + b
    A = np.zeros((7, 14))
    for i, c in enumerate(BASE):
        A[i, FEATURES.index(c)] = 1.0
    for c in MEALS:
        A[6, FEATURES.index(c)] = 1.0 / 3 / meal_sd
    b = np.zeros(7)
    b[6] = -meal_mu / meal_sd
    return X, M, dict(mean=mean, std=std, A=A, b=b, sleep_by_year=by_year)


def name_macro(M, labels):
    """군집 번호가 아니라 프로파일로 대분류 역할을 정한다(번호는 실행마다 바뀔 수 있음)."""
    z = pd.DataFrame(M, columns=MODEL_FEATURES).groupby(labels).mean()
    left, out = list(z.index), {}
    for role, score in [('G2_고스트레스형', lambda r: r['stress']),
                        ('G1_운동형', lambda r: r['aerobic'] + r['strength_days'] - r['sedentary_min']),
                        ('G3_좌식외식형', lambda r: r['sedentary_min'] + r['eatingout_freq_ord'])]:
        g = max(left, key=lambda i: score(z.loc[i]))
        out[g] = role
        left.remove(g)
    out[left[0]] = 'G0_비활동형'
    return out


def auto_name(M, labels_macro, key, g, cols):
    """군집 번호가 아니라 프로파일(소속 대분류 평균 대비 z)로 이름을 만든다."""
    z = pd.DataFrame(M, columns=MODEL_FEATURES)
    base = z[labels_macro == g][cols].mean()
    out = {}
    for name in sorted(set(key[labels_macro == g])):
        d = z[key == name][cols].mean() - base
        out[name] = '·'.join(f"{KOR[c]}{'높음' if d[c] > 0 else '낮음'}"
                             for c in sorted(cols, key=lambda c: -abs(d[c])))
    return out


# ------------------------------------------------------------------------ main
def main():
    print('[1/5] 데이터 로드 및 전처리')
    df = pd.read_csv(CSV, encoding='utf-8-sig')
    X, M, tf = build_matrix(df)

    print('[2/5] 1단계: 생활습관 7변수 -> PCA(5) -> K-Medoids(k=4)')
    pca = PCA(n_components=5, random_state=RANDOM_STATE).fit(M)
    Q = pca.transform(M)
    D = pairwise_dist(Q)
    med_macro, _ = kmedoids(D, 4, seed=RANDOM_STATE, n_init=10)
    labels = np.argmin(D[med_macro], axis=0)
    macro_name = name_macro(M, labels)
    sil_macro = silhouette(D, labels)
    print(f'    PCA 설명분산 {pca.explained_variance_ratio_.sum():.3f} / 실루엣 {sil_macro:.3f}')

    print('[3/5] 2단계: 대분류별 세부 군집(각 3개)')
    sub = np.empty(len(M), dtype=int)
    sub_model = {}
    for g in range(4):
        cols, k = SUB_PLAN[macro_name[g]]
        sel = np.flatnonzero(labels == g)
        B = M[np.ix_(sel, [MODEL_FEATURES.index(c) for c in cols])]
        bm, bs = B.mean(0), B.std(0)
        Bz = (B - bm) / bs
        Ds = pairwise_dist(Bz)
        med, _ = kmedoids(Ds, k, seed=RANDOM_STATE, n_init=10)
        sub[sel] = np.argmin(Ds[med], axis=0)
        sub_model[macro_name[g]] = dict(features=cols, mean=bm.tolist(), std=bs.tolist(),
                            medoids=Bz[med].tolist())
        print(f'    {macro_name[g]} ({len(sel)}명) <- {"+".join(cols)} : 실루엣 {silhouette(Ds, sub[sel]):.3f}')

    key = np.array([f'{macro_name[labels[i]]}_{sub[i]}' for i in range(len(M))])
    names = {}
    for g in range(4):
        names.update(auto_name(M, labels, key, g, SUB_PLAN[macro_name[g]][0]))

    df['Macro_Cluster'] = [macro_name[g] for g in labels]
    df['Type_Code'] = key
    df['Type_Name'] = [f'{k}({names[k]})' for k in key]

    print('[4/5] 엑셀 저장')
    summary = pd.concat([
        pd.Series(key).value_counts().rename('인원수(명)').sort_index(),
        pd.Series(names).rename('자동생성 이름'),
        pd.DataFrame(X, columns=FEATURES).groupby(key).mean().round(2)], axis=1)
    with pd.ExcelWriter(OUT_XLSX, engine='openpyxl') as w:
        df.to_excel(w, sheet_name='Raw_Data', index=False)
        summary.to_excel(w, sheet_name='Profile_Summary')

    print('[5/5] 웹 연동용 JSON 저장 및 재배정 검증')
    model = dict(
        features=FEATURES,
        sleep_year_adjust=dict(기준연도=SLEEP_REF_YEAR, by_year=tf['sleep_by_year'],
                               설명='연도별 z화 후 기준연도 분포로 환원. 웹 입력은 기준연도로 간주하여 변환하지 않음.'),
        scaler=dict(mean=tf['mean'].tolist(), std=tf['std'].tolist()),
        weights=[1.0] * 14,
        model_features=MODEL_FEATURES,
        projection=dict(설명='model = A @ z + b (z는 표준화된 14변수)',
                        A=tf['A'].tolist(), b=tf['b'].tolist()),
        pca=dict(mean=pca.mean_.tolist(), components=pca.components_.tolist()),
        macro=dict(space='pca', medoids={macro_name[g]: Q[med_macro[g]].tolist() for g in range(4)}),
        sub={r: dict(features=v['features'],
                     scaler=dict(mean=v['mean'], std=v['std']),
                     medoids={f'{r}_{i}': mv for i, mv in enumerate(v['medoids'])})
             for r, v in sub_model.items()},
        types={k: dict(name=names[k], n=int((key == k).sum()),
                       mean={c: round(float(X[key == k, i].mean()), 3)
                             for i, c in enumerate(FEATURES)})
               for k in sorted(set(key))},
        metrics=dict(k=4, silhouette_macro=round(sil_macro, 3), n_types=len(set(key))))

    match = verify(df, model, key)
    model['metrics']['reassign_match_type'] = round(match, 4)
    with open(OUT_JSON, 'w', encoding='utf-8') as fp:
        json.dump(model, fp, ensure_ascii=False, indent=1)
    print(f'    JSON 재배정 일치율: {match:.4%}')
    print(f'완료: {OUT_XLSX}, {OUT_JSON}')


def assign(raw_df, model):
    """JSON만으로 유형 배정 (웹에서 구현할 계산과 동일한 순서)."""
    F = model['features']
    X = raw_df[F].values.astype(float)
    if 'year' in raw_df.columns:  # 학습 데이터 검증용. 웹 입력은 기준연도로 간주.
        by = {str(k): v for k, v in model['sleep_year_adjust']['by_year'].items()}
        year = raw_df['year'].values.astype(int)
        ref = by[str(SLEEP_REF_YEAR)]
        i_sleep = F.index('ML_sleep_hours')
        s = X[:, i_sleep].copy()
        X[:, i_sleep] = [(s[i] - by[str(year[i])]['mean']) / by[str(year[i])]['std'] * ref['std'] + ref['mean']
                         for i in range(len(s))]
    z = (X - np.array(model['scaler']['mean'])) / np.array(model['scaler']['std'])
    mv = z @ np.array(model['projection']['A']).T + np.array(model['projection']['b'])
    pc = (mv - np.array(model['pca']['mean'])) @ np.array(model['pca']['components']).T

    mk = list(model['macro']['medoids'])
    mm = np.array([model['macro']['medoids'][k] for k in mk])
    macro = np.array(mk)[np.argmin(((pc[:, None, :] - mm[None]) ** 2).sum(2), axis=1)]

    out = np.empty(len(X), dtype=object)
    for gk in mk:
        sel = np.flatnonzero(macro == gk)
        if not len(sel):
            continue
        sm = model['sub'][gk]
        V = mv[np.ix_(sel, [model['model_features'].index(c) for c in sm['features']])]
        V = (V - np.array(sm['scaler']['mean'])) / np.array(sm['scaler']['std'])
        sk = list(sm['medoids'])
        smm = np.array([sm['medoids'][k] for k in sk])
        out[sel] = np.array(sk)[np.argmin(((V[:, None, :] - smm[None]) ** 2).sum(2), axis=1)]
    return out


def verify(df, model, key):
    return float((assign(df, model) == key).mean())


if __name__ == '__main__':
    main()
