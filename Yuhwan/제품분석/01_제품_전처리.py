# %% [markdown]
# # [C]-① 건강기능식품 제품 전처리
# 입력: 전국건강기능식품영양성분정보표준데이터.csv (식약처, cp949)
# 출력: 제품분석/output/products_clean.csv  (제품 1개 = 1행, 1일 섭취량 + 기준치 대비 %)
#
# 확인된 사실 (2026-11-02, 코드로 검증)
# - 영양성분제공단위량 == 1회분량중량/부피 : 5,556행 전부 일치
# - 함량은 "1회분량" 기준 → 1일 섭취량 = 표시값 × 1일섭취횟수
#   근거: 1일 2~3회 단일성분 제품은 표시값 그대로면 기준치 30% 미만이 44~100%,
#         ×섭취횟수 하면 0~12.5% (고시형은 1일 기준치 30% 이상이어야 기능성 표시 가능)
# - NaN = 해당 성분 표시 없음 → 0 으로 처리 (실제 0 입력은 거의 없음)
# - 식품명+제조사명 중복 331그룹 중 99그룹은 성분이 다름(수입 연도별 배합 변경) → 최신 신고번호 1개만 남김

# %%
from pathlib import Path
import re
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1] if '__file__' in globals() else Path.cwd().parent
OUT = ROOT / '제품분석' / 'output'
OUT.mkdir(parents=True, exist_ok=True)

raw = pd.read_csv(ROOT / '전국건강기능식품영양성분정보표준데이터.csv', encoding='cp949', low_memory=False)
print('원본', raw.shape)

# %% 1일 섭취횟수, 1회분량 중량
df = raw.copy()
df['n_day'] = df['1일섭취횟수'].str.extract(r'(\d+)')[0].astype(int)
df['serving_value'] = df['영양성분제공단위량'].str.extract(r'([\d.]+)')[0].astype(float)
df['serving_unit'] = df['영양성분제공단위량'].str.extract(r'([a-zA-Z]+)\s*$')[0]
assert (df['영양성분제공단위량'].str.strip() == df['1회분량중량/부피'].str.strip()).all()

# %% 중복 제거: 같은 식품명+제조사명이면 신고번호 연도(앞 2자리)가 가장 최근인 것
df['신고연도'] = pd.to_numeric(df['품목제조신고번호'].astype(str).str[:2], errors='coerce')
df = (df.sort_values(['신고연도', '품목제조신고번호'])
        .drop_duplicates(['식품명', '제조사명'], keep='last')
        .reset_index(drop=True))
print('중복 제거 후', len(df))
assert len(df) == 5207

# %% 1일 영양성분 기준치 (식약처 식품등의 표시기준, 라벨 % 계산용 / KDRI와 다른 개념)
# verified=False 는 고시 원문 대조 전 값 → 확정 전까지 결과 해석 시 주의
DV = pd.DataFrame([
    # 열 이름,            기준치,  단위,      verified
    ('단백질(g)',          55,     'g',       True),
    ('식이섬유(g)',        25,     'g',       True),
    ('칼슘(mg)',           700,    'mg',      True),
    ('철(mg)',             12,     'mg',      True),
    ('비타민 A(μg RAE)',   700,    'μg RAE',  True),
    ('비타민 D(μg)',       10,     'μg',      True),
    ('비타민 C(mg)',       100,    'mg',      True),
    ('티아민(mg)',         1.2,    'mg',      False),
    ('리보플라빈(mg)',     1.4,    'mg',      False),
    ('니아신(mg)',         15,     'mg NE',   False),
    ('인(mg)',             700,    'mg',      False),
    ('칼륨(mg)',           3500,   'mg',      False),
    ('나트륨(mg)',         2000,   'mg',      False),
], columns=['col', 'dv', 'unit', 'verified']).set_index('col')

NUT = list(DV.index)
df[NUT] = df[NUT].fillna(0)

# %% 오류 의심값 표시
# 규칙 1) g 단위 성분 1개가 1회분량 중량(mg 표기 제품)보다 무거우면 물리적으로 불가능
# 규칙 2) 그중 100배 이상 차이(예: 25g 젤리에 식이섬유 4,200g)는 성분값 입력 오류로 보고 0 처리
#         100배 미만은 1회분량 중량 쪽 오류일 수 있어 값은 유지하고 표시만
df['검토사유'] = ''
mg_serv = df['serving_unit'].eq('mg')
for col in ['단백질(g)', '식이섬유(g)']:
    ratio = df[col] * 1000 / df['serving_value']
    over = mg_serv & (ratio > 1.0)
    df.loc[over, '검토사유'] += f'{col}>1회분량중량;'
    fix = mg_serv & (ratio >= 100)
    df.loc[fix, '검토사유'] += f'{col}값 0처리(입력오류);'
    df.loc[fix, col] = 0

# %% 1일 섭취량, 기준치 대비 %
for col in NUT:
    name = col.split('(')[0].strip()
    df[f'일_{name}'] = df[col] * df['n_day']
    df[f'pct_{name}'] = df[f'일_{name}'] / DV.loc[col, 'dv'] * 100
PCT = [c for c in df.columns if c.startswith('pct_')]

# 규칙 3) 2025 KDRI 성인(19세 이상) 상한섭취량(UL) 중 가장 낮은 값과 비교 (요약표 xii~xvii쪽에서 추출)
#   - UL 초과        → '성인UL초과' 표시 (값 유지, [D] 안전 필터에서 제외 판단)
#   - UL의 10배 이상 → '단위오류의심' (예: 오메가3 제품 비타민D 1,000μg = IU를 μg로 입력한 것으로 추정)
#   티아민·리보플라빈·단백질·식이섬유·칼륨은 KDRI에 UL 없음
#   니아신 UL 35mg은 니코틴산 기준 (니코틴아마이드는 850mg) → 제품 형태를 몰라 보수적으로 35 사용
UL_ADULT_MIN = {'비타민 A': 3000, '비타민 D': 100, '비타민 C': 2000, '니아신': 35,
                '칼슘': 2000, '인': 3000, '철': 45}
for name, ul in UL_ADULT_MIN.items():
    day = df[f'일_{name}']
    df.loc[day > ul, '검토사유'] += f'{name} 성인UL초과;'
    df.loc[day >= ul * 10, '검토사유'] += f'{name} 단위오류의심;'

# %% 함량 열이 없는 성분: 제품명/대표식품명으로 함유 여부만 표시 (함량 미상)
NAME_FLAGS = {
    'has_마그네슘': r'마그네슘|magnesium',
    'has_아연':     r'아연|zinc',
    'has_엽산':     r'엽산|folic|folate',
    'has_비타민E':  r'비타민\s?E(?![A-Za-z])|vitamin\s?e(?![a-z])',
}
text = (df['식품명'].fillna('') + ' ' + df['대표식품명'].fillna('')).str.lower()
for k, pat in NAME_FLAGS.items():
    df[k] = text.str.contains(pat, flags=re.I, regex=True).astype(int)

# %% 영양소 성분이 하나도 없는 제품(프로바이오틱스, 홍삼 등 기능성 원료만) 구분
df['영양소_개수'] = (df[PCT] > 0).sum(axis=1) + df[list(NAME_FLAGS)].sum(axis=1)
df['영양소제품'] = (df['영양소_개수'] > 0).astype(int)

# %% 저장
keep = ['식품코드', '식품명', '제조사명', '품목제조신고번호', '대표식품명', '식품대분류명',
        '1회분량', '영양성분제공단위량', 'n_day', '섭취대상']
out = df[keep + NUT + [c for c in df.columns if c.startswith('일_')] + PCT
         + list(NAME_FLAGS) + ['영양소_개수', '영양소제품', '검토사유']]
out.to_csv(OUT / 'products_clean.csv', index=False, encoding='utf-8-sig')
out[out['검토사유'] != ''].to_csv(OUT / 'products_검토필요.csv', index=False, encoding='utf-8-sig')
DV.to_csv(OUT / '기준치_사용값.csv', encoding='utf-8-sig')

# %% 요약
print('\n제품 수', len(out), '| 영양소 성분 있는 제품', out['영양소제품'].sum(),
      '| 기능성 원료만', (out['영양소제품'] == 0).sum())
summary = pd.DataFrame({
    '함유 제품 수': [(out[c] > 0).sum() for c in PCT] + [out[k].sum() for k in NAME_FLAGS],
    '1일 기준치% 중앙값': [out.loc[out[c] > 0, c].median().round(1) for c in PCT] + [np.nan] * len(NAME_FLAGS),
}, index=[c.replace('pct_', '') for c in PCT] + [k.replace('has_', '') + '(이름기준)' for k in NAME_FLAGS])
print(summary.to_string())
print('\n검토필요 제품', (out['검토사유'] != '').sum())
print(out.loc[out['검토사유'] != '', '검토사유'].str.split(';').explode().loc[lambda s: s != '']
      .value_counts().to_string())
sus = out[out['검토사유'].str.contains('단위오류의심|0처리')]
print('\n단위오류의심/0처리 제품'); print(sus[['식품명', '대표식품명', '일_비타민 D', '일_비타민 C', '일_니아신', '검토사유']].to_string())
