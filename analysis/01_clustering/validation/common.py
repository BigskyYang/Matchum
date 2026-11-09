"""서비스용 생활습관 군집화 공통: 경로, 원시데이터 → 웹 설문 값 변환, 영역 가중치, 영양소 부족 판정.

원칙
- 군집 입력은 웹 설문으로 받을 수 있는 값만 쓴다. 값의 범위·방향은 web/src/lib/encode.js, web/src/data/questions.js와 같다.
- 웹에서 같은 계산을 할 수 있도록 전처리는 '자르기(clip) → 표준화 → 영역 가중치'의 선형 변환만 쓴다.
- 원시데이터와 사람 단위 결과는 git에 올리지 않는다 (data/ 폴더, *.csv, *.sas7bdat 는 .gitignore).
"""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RAW = REPO / 'analysis' / 'raw' / '12~16+22~24년 원시데이터'
DATA = HERE / 'data'      # 사람 단위 중간 결과 (git 제외)
OUT = HERE / 'output'     # 요약 결과만 (git에 올려도 되는 것)
DATA.mkdir(exist_ok=True)
OUT.mkdir(exist_ok=True)

YEARS = (2022, 2023, 2024)
SEED = 42

# 2025 KDRI 성인 기준표는 유환님 영양분석과 같은 것을 쓴다 (기준이 둘이 되지 않도록)
_spec = importlib.util.spec_from_file_location('yuhwan_common', REPO / 'analysis' / '02_type_nutrition' / '영양분석' / 'common.py')
_yuhwan = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_yuhwan)
AGE_BINS, AGE_LABELS, KDRI = _yuhwan.AGE_BINS, _yuhwan.AGE_LABELS, _yuhwan.KDRI

# ── 군집 입력 변수 (웹 설문 값 기준) ──
# 영역(domain)마다 변수 수가 달라도 영역의 총 비중이 같도록 1/√(영역 변수 수)를 곱한다.
# 지연님 7개 그룹이 흡연·음주로만 갈린 것은 음주 3개·흡연 2개 변수가 같은 정보를 겹쳐 담았기 때문.
# ML_drink_month(월 1회 이상 음주)는 drink_freq ≥ 2와 완전히 같아서 뺀다.
FEATURES = {
    # 이름            영역        자르기 범위 (웹 설문 값 기준)
    'smoker':        ('흡연',     (0, 1)),
    'cigarettes':    ('흡연',     (0, 40)),
    'drink_freq':    ('음주',     (0, 5)),
    'drink_amount':  ('음주',     (0, 5)),
    'aerobic':       ('신체활동', (0, 1)),
    'strength_days': ('신체활동', (0, 5)),
    'sedentary_min': ('좌식',     (0, 1200)),
    'sleep_hours':   ('수면',     (3, 14)),
    'stress':        ('스트레스', (0, 1)),
    'breakfast':     ('식사',     (0, 3)),
    'lunch':         ('식사',     (0, 3)),
    'dinner':        ('식사',     (0, 3)),
    'eating_out':    ('외식',     (0, 6)),
    'veg':           ('채소과일', (0, 8)),
    'fruit':         ('채소과일', (0, 8)),
}
FEATURE_NAMES = list(FEATURES)
DOMAINS = {f: d for f, (d, _) in FEATURES.items()}
LABEL_KO = {
    'smoker': '현재 흡연', 'cigarettes': '하루 흡연량(개비)', 'drink_freq': '음주 빈도(0~5)',
    'drink_amount': '1회 음주량(0~5)', 'aerobic': '유산소 실천', 'strength_days': '근력운동(일/주)',
    'sedentary_min': '좌식(분/일)', 'sleep_hours': '수면(시간)', 'stress': '스트레스 많음',
    'breakfast': '아침식사(0~3)', 'lunch': '점심식사(0~3)', 'dinner': '저녁식사(0~3)',
    'eating_out': '외식 빈도(0~6)', 'veg': '채소 빈도(0~8)', 'fruit': '과일 빈도(0~8)',
}
# 지연님 COMPLETECASE CSV의 ML_ 변수와 대응 (같은 규칙으로 만들었는지 확인용)
ML_COLUMNS = {
    'smoker': 'ML_smoker', 'cigarettes': 'ML_cigarettes_day', 'drink_freq': 'ML_drink_freq_ord',
    'drink_amount': 'ML_drink_amount_ord', 'aerobic': 'ML_aerobic', 'strength_days': 'ML_strength_days',
    'sedentary_min': 'ML_sedentary_min', 'sleep_hours': 'ML_sleep_hours', 'stress': 'ML_stress',
    'breakfast': 'ML_breakfast_freq_ord', 'lunch': 'ML_lunch_freq_ord', 'dinner': 'ML_dinner_freq_ord',
    'eating_out': 'ML_eatingout_freq_ord',
}


def domain_weights():
    n = pd.Series(DOMAINS).value_counts()
    return np.array([1 / np.sqrt(n[DOMAINS[f]]) for f in FEATURE_NAMES])


def _valid(s, bad):
    return s.where(~s.isin(bad))


def _clock_hours(bh, bm, wh, wm):
    """취침·기상 시각 → 수면 시간. 자정을 넘기면 다음 날로 본다 (encode.js sleepHours와 같음)."""
    diff = ((wh * 60 + wm) - (bh * 60 + bm)) % 1440
    return diff.mask(diff == 0, 1440) / 60      # 결측(NaN)은 그대로 결측 (where(diff > 0)는 NaN을 24시간으로 바꿨음)


def load_raw():
    return pd.concat([pd.read_csv(RAW / f'hn{str(y)[2:]}_all_reduced.csv', encoding='utf-8-sig', low_memory=False)
                      for y in YEARS], ignore_index=True)


def encode_knhanes(raw):
    """KNHANES 원시 코드 → 웹 설문 값 (값이 클수록 '더 자주/더 많이'). 응답 거부·모름은 결측.

    흡연    sm_presnt, BS3_2 (888 비해당 → 0, 999 결측)
    음주    BD1_11 1·8 → 0, 2~6 → 1~5 / BD2_1 8 → 0
    운동    pa_aerobic / BE5_1 1~6 → 0~5
    좌식    BE8_1 × 60 + BE8_2
    수면    2022·2023: 주중(BP16_1)·주말(BP16_2) 수면 시간을 직접 물음 (정수 시간)
            2024: 취침·기상 시각(BP16_11~14, 21~24)으로 물음 ← 웹과 같은 방식
            주중 5일·주말 2일 가중평균 (encode.js와 같음)
    식사    L_BR/LN/DN_FQ 1~4 → 3~0 / L_OUT_FQ 1~7 → 6~0
    채소과일 LS_VEG2(김치 제외)·LS_FRUIT 1~9 → 8~0
    """
    e = pd.DataFrame({'ID': raw['ID'], 'year': raw['year'].astype(int)})
    smoker = raw['sm_presnt']
    cig = _valid(raw['BS3_2'], [999]).where(raw['BS3_2'] != 888, 0)
    e['smoker'] = smoker
    e['cigarettes'] = np.where(smoker == 1, cig, 0.0)

    freq = _valid(raw['BD1_11'], [9])
    e['drink_freq'] = (freq - 1).where(~freq.isin([1, 8]), 0)
    amt = _valid(raw['BD2_1'], [9])
    e['drink_amount'] = amt.where(amt != 8, 0)
    e.loc[e['drink_freq'] == 0, 'drink_amount'] = 0

    e['aerobic'] = raw['pa_aerobic']
    e['strength_days'] = _valid(raw['BE5_1'], [9]) - 1
    e['sedentary_min'] = _valid(raw['BE8_1'], [88, 99]) * 60 + _valid(raw['BE8_2'], [88, 99])

    old = (raw['year'] < 2024).to_numpy()
    sleep = pd.Series(np.nan, index=raw.index)
    if 'BP16_1' in raw:
        wd, we = _valid(raw['BP16_1'], [88, 99]), _valid(raw['BP16_2'], [88, 99])
        sleep[old] = ((wd * 5 + we * 2) / 7)[old]
    t = {c: _valid(raw[c], [88, 99]) for c in
         ['BP16_11', 'BP16_12', 'BP16_13', 'BP16_14', 'BP16_21', 'BP16_22', 'BP16_23', 'BP16_24']}
    wd24 = _clock_hours(t['BP16_11'], t['BP16_12'], t['BP16_13'], t['BP16_14'])
    we24 = _clock_hours(t['BP16_21'], t['BP16_22'], t['BP16_23'], t['BP16_24'])
    sleep[~old] = ((wd24 * 5 + we24 * 2) / 7)[~old]
    e['sleep_hours'] = sleep

    e['stress'] = raw['mh_stress']
    for col, src in [('breakfast', 'L_BR_FQ'), ('lunch', 'L_LN_FQ'), ('dinner', 'L_DN_FQ')]:
        e[col] = 4 - _valid(raw[src], [9])
    e['eating_out'] = 7 - _valid(raw['L_OUT_FQ'], [9])
    e['veg'] = 9 - _valid(raw['LS_VEG2'], [99])
    e['fruit'] = 9 - _valid(raw['LS_FRUIT'], [99])
    return e


def clip(X):
    lo = np.array([FEATURES[f][1][0] for f in FEATURE_NAMES], dtype=float)
    hi = np.array([FEATURES[f][1][1] for f in FEATURE_NAMES], dtype=float)
    return np.clip(X, lo, hi)


class Transform:
    """clip → 표준화(수면만 연도별) → 영역 가중치. 웹은 수면에 2024년 기준값을 쓴다 (측정 방식이 같아서)."""

    SLEEP = FEATURE_NAMES.index('sleep_hours')

    def fit(self, df):
        X = clip(df[FEATURE_NAMES].to_numpy(float))
        self.mean, self.std = X.mean(axis=0), X.std(axis=0)
        years = df['year'].to_numpy()
        self.sleep_by_year = {int(y): (float(X[years == y, self.SLEEP].mean()), float(X[years == y, self.SLEEP].std()))
                              for y in np.unique(years)}
        self.weights = domain_weights()
        return self

    def transform(self, df, year=None):
        X = clip(df[FEATURE_NAMES].to_numpy(float))
        Z = (X - self.mean) / self.std
        years = df['year'].to_numpy() if year is None else np.full(len(df), year)
        for y, (mu, sd) in self.sleep_by_year.items():
            Z[years == y, self.SLEEP] = (X[years == y, self.SLEEP] - mu) / sd
        return Z * self.weights


def add_nutrient_status(d):
    """사람마다 본인 성별·연령 2025 KDRI와 비교해 below_<영양소> = 1/0 (유환님 add_status와 같은 규칙)."""
    d = d.copy()
    d['age_grp'] = pd.cut(d['age'], AGE_BINS, labels=AGE_LABELS)
    idx = d['age_grp'].cat.codes.to_numpy()
    male = (d['sex'] == 1).to_numpy()
    new = {}
    for n, (col, basis, m, f, *_rest) in KDRI.items():
        ref = np.where(male, np.array(m)[idx], np.array(f)[idx]).astype(float)
        x = d[col.replace('영양_', '')].to_numpy(float)
        new[f'below_{n}'] = np.where(np.isnan(x), np.nan, (x < ref).astype(float))
    return pd.concat([d, pd.DataFrame(new, index=d.index)], axis=1)


NUTRIENTS = list(KDRI)
EAR_NUTRIENTS = [n for n in KDRI if KDRI[n][1] == 'EAR']


def standardized_ratio(d, labels, nutrient):
    """간접 표준화: 유형의 실제 부족 인원 ÷ (같은 성별·연령대 전체 비율로 기대되는 인원).

    1보다 크면 성별·연령 구성을 감안해도 그 유형에서 더 많이 부족하다는 뜻.
    """
    col = f'below_{nutrient}'
    ok = d[col].notna().to_numpy()
    dd = d.loc[ok, ['sex', 'age_grp', col]].copy()
    dd['label'] = np.asarray(labels)[ok]
    dd['exp'] = dd.groupby(['sex', 'age_grp'], observed=True)[col].transform('mean')
    g = dd.groupby('label')
    return pd.DataFrame({'obs': g[col].sum(), 'exp': g['exp'].sum(), 'n': g[col].size()}).assign(
        ratio=lambda t: t['obs'] / t['exp'])


def nutrient_separation(d, labels):
    """유형 간 영양 결과 차이: EAR 영양소별 log(표준화비)의 인원 가중 표준편차 평균. 클수록 유형마다 부족 영양소가 다르다."""
    vals = []
    for n in EAR_NUTRIENTS:
        t = standardized_ratio(d, labels, n)
        w = t['n'] / t['n'].sum()
        lr = np.log(t['ratio'].clip(lower=1e-6))
        vals.append(float(np.sqrt((w * (lr - (w * lr).sum()) ** 2).sum())))
    return float(np.mean(vals))


def adjusted_ratios(dd, labels, strata):
    """유형 × 영양소 간접 표준화비 + 포아송 p + BH-FDR q (영양소 × 유형 전체를 한 번에 보정).

    strata: 같은 층끼리 비교할 변수. ['sex', 'age_grp'] 또는 + 'energy_q'(총 섭취량 5분위).
    """
    from scipy.stats import poisson
    rows = []
    for n in NUTRIENTS:
        col = f'below_{n}'
        t = dd[strata + [col]].copy()
        t['label'] = np.asarray(labels)
        t['exp'] = t.groupby(strata, observed=True)[col].transform('mean')
        g = t.groupby('label')
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


def ratio_separation(r):
    """adjusted_ratios 결과로 유형 간 영양 결과 차이 (nutrient_separation과 같은 정의)."""
    vals = []
    for n in EAR_NUTRIENTS:
        t = r[r['nutrient'] == n]
        w = t['n'] / t['n'].sum()
        lr = np.log(t['ratio'].clip(lower=1e-6))
        vals.append(float(np.sqrt((w * (lr - (w * lr).sum()) ** 2).sum())))
    return float(np.mean(vals))


def specific_rows(r, min_ratio=1.2, max_q=0.05):
    """유형 특이 영양소: 비 ≥ 1.2이고 BH-FDR q < 0.05."""
    return r[(r['ratio'] >= min_ratio) & (r['q'] < max_q)]
