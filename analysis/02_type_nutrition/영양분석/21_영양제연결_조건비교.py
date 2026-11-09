# %% [markdown]
# # 개인 결과 → 건강기능식품 연결 조건 비교 (재준님 11/5 13:36 요청)
# 질문: 영양제 정보로 넘기는 조건을 지금("높은 편"이고 살펴볼 영양소 5개 안) → 제안("높은 편" + 같은 모델 확률 ≥ 0.5)으로 바꾸면
#   (1) 연결되는 사람·영양소 수, (2) 연결된 항목 중 실제 기준 미만 비율, (3) 실제 기준 미만인데 빠지는 비율이 어떻게 바뀌나
# 재현 범위 (웹 lib/result.js personalNutrition·supplementTargets와 같게)
#   - 대표 등급: 생활습관 모델 (재준님 v1.4, 웹 nutritionModels.json 트리를 그대로 재현 = 16번과 같은 계산)
#   - 살펴볼 영양소: '높은 편' 중 화면 순서(nutrientGuide 순서)로 최대 5개
#   - 제품 연결 영양소: 마그네슘·비타민 B군(B1·B2)·C·식이섬유·아연·엽산·철·칼슘 (인·단백질·칼륨은 음식 전용이라 제외)
#   - 정답: 2025 KDRI 기준 미만 (24시간 회상, 우리 add_status). 평가 2024년, 가중치 wt_tot/3
# 한계: 평소 식사 모델(19~64세 + 식사 5문항)은 정답이 FFQ 계산값이고 9기에는 FFQ가 없어 같은 방식으로 평가할 수 없음
#       → 그 사람들의 칼슘·철·B1·B2·C·식이섬유는 이 표와 다를 수 있음

# %%
import json
import warnings
import numpy as np
import pandas as pd
from common import *

warnings.filterwarnings('ignore')
REPO = ROOT.parents[1]
NM = json.load(open(REPO / 'web' / 'src' / 'data' / 'nutritionModels.json', encoding='utf-8'))['lifestyle']
# 화면 순서 = nutrientGuide.js 순서 (생활습관 모델에 있는 것만, 나트륨은 맨 끝이라 제품 연결 영양소의 5개 안 여부에 영향 없음)
ORDER = ['protein', 'calcium', 'phosphorus', 'magnesium', 'iron', 'zinc', 'vitamin_a', 'vitamin_b1', 'vitamin_b2', 'folate',
         'vitamin_c', 'potassium', 'fiber']
KEY = {'protein': '단백질', 'calcium': '칼슘', 'magnesium': '마그네슘', 'iron': '철', 'zinc': '아연', 'phosphorus': '인',
       'vitamin_a': '비타민A', 'vitamin_b1': '티아민', 'vitamin_b2': '리보플라빈', 'folate': '엽산', 'vitamin_c': '비타민C',
       'fiber': '식이섬유', 'potassium': '칼륨'}
PRODUCT = {'magnesium': '마그네슘', 'vitamin_b': '비타민 B군', 'vitamin_c': '비타민 C', 'fiber': '식이섬유', 'zinc': '아연',
           'folate': '엽산', 'iron': '철', 'calcium': '칼슘'}
FROM = {'vitamin_b': ['vitamin_b1', 'vitamin_b2']}
MAX_WATCH = 5
CUTS = [None, 0.3, 0.4, 0.5, 0.6, 0.7]

d = add_status(load_persons(ROOT / 'KMedoids_12Types_N1O3.csv', 'Type'))
FEAT = NM['features']
for c in ['식습관_LS_FRUIT', '식습관_LS_VEG2']:
    d[c] = d[c].where(~d[c].isin([99]))
d = d[d[FEAT].notna().all(axis=1) & (d['year'] == 2024)].reset_index(drop=True)
X = d[FEAT].to_numpy(float)
w = d['w'].to_numpy()
print(f'2024 평가 {len(d)}명')


def hgb_prob(m, X):
    raw = np.full(len(X), m['baseline'])
    rows = np.arange(len(X))
    for t in m['trees']:
        f, th, l, r = (np.array(t[k]) for k in 'ftlr')
        node = np.zeros(len(X), dtype=int)
        while True:
            inner = f[node] >= 0
            if not inner.any():
                break
            n = node[inner]
            node[inner] = np.where(X[rows[inner], f[n]] <= th[n], l[n], r[n])
        raw += th[node]
    return 1 / (1 + np.exp(-raw))


def prob(key):
    m = NM['models'][key]
    if m['type'] == 'hgb':
        return hgb_prob(m, X)
    z = (X - np.array(m['mean'])) / np.array(m['scale'])
    return 1 / (1 + np.exp(-(z @ np.array(m['coef']) + m['intercept'])))


P = {k: prob(k) for k in ORDER}
HIGH = {k: P[k] >= NM['cuts'][k]['mid_high'] for k in ORDER}           # 웹: p < low_mid 낮음, < mid_high 보통, 그 이상 높은 편
Y = {k: d[f'below_{KEY[k]}'].to_numpy().astype(bool) for k in ORDER}

# 살펴볼 영양소: 높은 편을 화면 순서로 최대 5개
rank = np.zeros(len(d), dtype=int)
WATCH = {}
for k in ORDER:
    WATCH[k] = HIGH[k] & (rank < MAX_WATCH)
    rank += HIGH[k]
print(f"높은 편 개수 평균 {np.average(rank, weights=w):.2f}개 (생활습관 모델 13개 영양소) / 5개를 넘는 사람 {np.average(rank > MAX_WATCH, weights=w):.1%}")


def linked(cut):
    """제품 연결 영양소별 (사람 수 배열) 연결 여부, 그 영양소의 '실제 기준 미만', 높은 편 판정 모델의 최대 확률."""
    out = {}
    for pk, label in PRODUCT.items():
        src = FROM.get(pk, [pk])
        # 비타민 B군: B1·B2 중 하나라도 조건을 만족하면 연결. 실제 미만도 둘 중 하나라도 미만이면
        lk = np.zeros(len(d), bool)
        for k in src:
            lk |= WATCH[k] & (True if cut is None else (P[k] >= cut))
        y = np.zeros(len(d), bool)
        for k in src:
            y |= Y[k]
        out[pk] = (lk, y)
    return out


rows, per = [], []
base = linked(None)
for cut in CUTS:
    L = linked(cut)
    n_link = sum(L[k][0].astype(int) for k in PRODUCT)
    lk_all = np.concatenate([L[k][0] for k in PRODUCT])
    y_all = np.concatenate([L[k][1] for k in PRODUCT])
    b_all = np.concatenate([base[k][0] for k in PRODUCT])
    ww = np.tile(w, len(PRODUCT))
    rows.append({
        '조건': '지금 (높은 편 + 5개 안)' if cut is None else f'+ 확률 ≥ {cut}',
        '영양제로 넘어가는 사람': np.average(n_link > 0, weights=w),
        '1인당 연결 영양소 수': np.average(n_link, weights=w),
        '연결 항목 중 실제 기준 미만': np.average(y_all[lk_all], weights=ww[lk_all]),
        '실제 미만 중 연결된 비율': np.average(lk_all[y_all], weights=ww[y_all]),
        '지금 연결된 실제 미만 중 빠지는 비율': np.average(~lk_all[b_all & y_all], weights=ww[b_all & y_all]),
        '연결 안 된 항목 중 실제 기준 미만': np.average(y_all[~lk_all], weights=ww[~lk_all]),
    })
    for pk, label in PRODUCT.items():
        lk, y = L[pk]
        b = base[pk][0]
        per.append({'조건': rows[-1]['조건'], '영양소': label, '기준 미만 비율(전체)': np.average(y, weights=w),
                    '연결 비율(사람)': np.average(lk, weights=w),
                    '연결된 사람 중 실제 미만': np.average(y[lk], weights=w[lk]) if lk.any() else np.nan,
                    '지금 연결된 실제 미만 중 빠짐': np.average(~lk[b & y], weights=w[b & y]) if (b & y).any() else np.nan})
R, PN = pd.DataFrame(rows), pd.DataFrame(per)
R.to_csv(OUT / '21_영양제연결_조건비교.csv', index=False, encoding='utf-8-sig')
PN.to_csv(OUT / '21_영양제연결_영양소별.csv', index=False, encoding='utf-8-sig')
pd.set_option('display.width', 250)
print('\n전체 (2024, 가중, 제품 연결 영양소 8개 기준)')
print(R.round(3).to_string(index=False))
print('\n영양소별: 지금 vs 확률 ≥ 0.5')
print(PN[PN['조건'].isin(['지금 (높은 편 + 5개 안)', '+ 확률 ≥ 0.5'])].round(3).to_string(index=False))
print('\n참고: 높은 편 확률 하한(mid_high 경계값) — 이 값이 0.5보다 크면 확률 조건은 그 영양소에 영향이 없음')
print({PRODUCT.get(k, k): round(NM['cuts'][k]['mid_high'], 3) for k in ORDER if k in PRODUCT or k in ('vitamin_b1', 'vitamin_b2')})
