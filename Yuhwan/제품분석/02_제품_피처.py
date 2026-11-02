# %% [markdown]
# # [C]-② 제품 매칭용 피처
# 입력: output/products_clean.csv (01 결과) + 원본 CSV(레티놀/베타카로틴)
# 출력: output/product_features.csv
#
# 피처 구성 (왜 이렇게 했는지)
# - 정량 10개: 함량 열이 있는 성분 → 1일 섭취량의 기준치 대비 %
#     단백질, 식이섬유, 칼슘, 철, 비타민A, 비타민D, 비타민C, 티아민, 리보플라빈, 니아신
# - 함유 여부 11개: 함량 열이 없어서 제품명·대표식품명으로만 판별 (함량 미상)
#     마그네슘, 아연, 엽산, 비타민E, 비타민K, 비타민B6, 비타민B12 / 오메가3, 유산균, 루테인, 밀크씨슬
# - 뺀 것: 인·칼륨(영양제 추천 대상 아님, 안전 체크용으로만 보관), 나트륨·에너지·지방·당(부형제 수준)
# - 품질 신호: 점수에 쓰는 것 = 함량 적정성(기준치 30%~UL), UL 초과 없음
#              표시만 하는 것 = D3, rTG, 리포좀, 활성엽산 (성분 형태 효과를 우리 자료로 검증 못 해서 점수 제외)
# - 안전: 베타카로틴 함유(흡연 군집 제외용), UL 초과/단위오류 의심(01에서 표시)

# %%
from pathlib import Path
import re
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '제품분석' / 'output'
p = pd.read_csv(OUT / 'products_clean.csv', encoding='utf-8-sig')
raw = pd.read_csv(ROOT / '전국건강기능식품영양성분정보표준데이터.csv', encoding='cp949', low_memory=False)
p = p.merge(raw[['식품코드', '레티놀(μg)', '베타카로틴(μg)', '수입여부']].drop_duplicates('식품코드'), on='식품코드', how='left')

QUANT = ['단백질', '식이섬유', '칼슘', '철', '비타민 A', '비타민 D', '비타민 C', '티아민', '리보플라빈', '니아신']
name = (p['식품명'].fillna('') + ' ' + p['대표식품명'].fillna(''))
FLAG = {
    '마그네슘': r'마그네슘|magnesium',
    '아연': r'아연|zinc',
    '엽산': r'엽산|folic|folate|폴레이트',
    '비타민 E': r'비타민\s?E(?![A-Za-z])|vitamin\s?e(?![a-z])',
    '비타민 K': r'비타민\s?K|K2|메나퀴논',
    '비타민 B6': r'B6|피리독신',
    '비타민 B12': r'B12|코발라민',
    '오메가3': r'오메가|EPA|DHA|rTG|알티지|크릴',
    '유산균': r'유산균|프로바이오|락토바실|비피더스|비피도',
    '루테인': r'루테인|마리골드|지아잔틴',
    '밀크씨슬': r'밀크씨슬|실리마린|milk\s?thistle',
}
for k, pat in FLAG.items():
    p[f'has_{k}'] = name.str.contains(pat, flags=re.I, regex=True).astype(int)
# 식이섬유는 함량 열이 있지만, 함량 0이어도 대표식품명이 식이섬유 계열이면 함유로
p.loc[p['대표식품명'].str.contains('식이섬유|폴리덱스트로스|구아검|차전자', na=False) & (p['pct_식이섬유'] == 0), 'has_식이섬유명'] = 1
p['has_식이섬유명'] = p.get('has_식이섬유명', 0)
p['has_식이섬유명'] = p['has_식이섬유명'].fillna(0).astype(int)

# 품질 신호 (표시용)
FORM = {'D3': r'D3', 'rTG': r'rTG|알티지', '리포좀': r'리포좀|리포조말', '활성엽산': r'메틸폴레이트|활성엽산|5-MTHF'}
for k, pat in FORM.items():
    p[f'form_{k}'] = p['식품명'].str.contains(pat, flags=re.I, regex=True).astype(int)

# 안전·편의
p['베타카로틴함유'] = (p['베타카로틴(μg)'].fillna(0) > 0).astype(int)
p['UL초과'] = p['검토사유'].fillna('').str.contains('성인UL초과|단위오류의심|0처리').astype(int)
p['1회개수'] = p['1회분량'].str.extract(r'(\d+)')[0].astype(float)
p['1일개수'] = p['1회개수'] * p['n_day']

# 구성 벡터: 정량은 % (클러스터링 단계에서 변환), 함유 여부는 0/1
for q in QUANT:
    p[f'v_{q}'] = p[f'pct_{q}']
for k in FLAG:
    p[f'v_{k}'] = p[f'has_{k}']
p['v_식이섬유'] = np.where((p['v_식이섬유'] == 0) & (p['has_식이섬유명'] == 1), 100, p['v_식이섬유'])  # 함량 미상 → 100%로 대표
V = [c for c in p.columns if c.startswith('v_')]
p['구성성분수'] = (p[V] > 0).sum(axis=1)
p['대상제품'] = (p['구성성분수'] > 0).astype(int)

p.to_csv(OUT / 'product_features.csv', index=False, encoding='utf-8-sig')
print('전체', len(p), '| 우리 영양소 목록에 해당하는 성분이 1개 이상인 제품', p['대상제품'].sum(),
      '| 해당 없음(홍삼·프로폴리스 등)', (p['대상제품'] == 0).sum())
print(pd.Series({c[2:]: (p[c] > 0).sum() for c in V}).sort_values(ascending=False).to_string())
print('품질 표시:', {k: int(p[f'form_{k}'].sum()) for k in FORM}, '| 베타카로틴', p['베타카로틴함유'].sum(), '| UL초과', p['UL초과'].sum())
print('1일 개수 분포', p['1일개수'].describe()[['50%', 'max']].to_dict())
