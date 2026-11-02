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
import warnings
import numpy as np
import pandas as pd
warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)

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
FORM = {'D3': r'D3', 'rTG': r'rTG|알티지', '리포좀': r'리포좀|리포조말', '활성엽산': r'메틸폴레이트|활성엽산|5-MTHF',
        '활성비타민B': r'활성\s?비타민|벤포|벤포티아민', '장용성': r'장용'}   # 준혁님 '프리미엄 원료' 키워드 추가 (배지 표시용)
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

# %% v5: 제품 '주목적' 판별 (준혁님 B군 결과 검증에서 발견한 문제 보완)
# 문제: CSV에는 비타민·미네랄 함량 칸만 있어서, 간·면역 제품에 소량 들어간 B1이 'B1 제품'처럼 보임
#       (B1 기준치 100%↑ 723개 중 207개가 간·면역·모발·남성 계열 이름)
# 규칙(목적 일치): 이름에 기능성 키워드가 있는 제품은, 추천하려는 영양소가 '제품명에도' 나올 때만 그 영양소 후보로 인정
FUNC_KW = {
    '간': r'리버|헤파|밀크씨슬|실리마린|간\s?건강|간케어',
    '면역': r'프로폴리스|면역|이뮨',
    '모발·피부': r'비오틴|판토|모발|헤어|피부|콜라겐|히알루론|스킨',
    '눈': r'루테인|지아잔틴|빌베리|아스타잔틴|아이케어|눈건강|아이뷰',
    '관절': r'엠에스엠|MSM|관절|글루코사민|보스웰리아|홍합|연골',
    '잇몸·치아': r'잇몸|치아|덴탈|덴티|인사덴|인사텐|인사돌|이가돌|이가탄',
    '혈행': r'오메가|EPA|DHA|크릴|rTG|알티지',
    '장': r'유산균|프로바이오|락토|비피더스|포스트바이오',
    '체지방·혈당': r'가르시니아|다이어트|슬림|컷팅|바나바|혈당',
    '수면·스트레스': r'테아닌|스트레스|수면|숙면|멜라토닌',
    '기타 기능성': r'라이코펜|코엔자임|코큐텐|쏘팔메토|옥타코사놀|아르기닌|마카|홍삼|흑마늘|녹용|녹혈|브레인|기억력|은행잎|징코|포스파티딜',
}
name_all = (p['식품명'].fillna('') + ' ' + p['대표식품명'].fillna(''))
for k, pat in FUNC_KW.items():
    p[f'func_{k}'] = p['식품명'].str.contains(pat, case=False, regex=True).astype(int)
p['주목적_기능성'] = p[[f'func_{k}' for k in FUNC_KW]].apply(lambda r: '·'.join(k for k in FUNC_KW if r[f'func_{k}']), axis=1)
# 이름만으로는 못 잡는 기능성 제품(히아루벨·인사골드·아우겐 등)이 있어 식약처 분류도 사용:
# 대표식품명이 '복합제품(영양소, 기능성)'·'복합제품(기능성)'이면 기능성 원료 포함 → 영양소 이름이 제품명에 있을 때만 그 영양소 후보
p['기능성원료포함'] = p['대표식품명'].fillna('').str.contains('기능성').astype(int)
p.loc[(p['주목적_기능성'] == '') & (p['기능성원료포함'] == 1), '주목적_기능성'] = '기능성 원료 포함'

# 제품명에 영양소 이름이 있는지 (종합·멀티 제품은 모든 비타민·미네랄을 언급한 것으로 봄)
NAME_KW = {
    '티아민': r'비타민\s?B|B1\b|티아민|B군|B\s?컴플렉스|비\s?컴플렉스|벤포|활성\s?비타민|임팩타민|아로나민|비맥스',
    '리보플라빈': r'비타민\s?B|B2\b|리보플라빈|B군|B\s?컴플렉스|비\s?컴플렉스|활성\s?비타민|임팩타민|아로나민|비맥스',
    '니아신': r'비타민\s?B|B3\b|니아신|B군|B\s?컴플렉스|비\s?컴플렉스',
    '비타민 C': r'비타민\s?C|비타민씨|아스코르빈',
    '비타민 D': r'비타민\s?D|D3\b|D3',
    '비타민 A': r'비타민\s?A|베타카로틴|레티놀',
    '비타민 E': r'비타민\s?E(?![A-Za-z])|토코페롤',
    '칼슘': r'칼슘|칼마|Ca\b',
    '마그네슘': r'마그네슘|마그|Mg\b',
    '철': r'철분|헴철|철\b|아이언',
    '아연': r'아연|징크|Zn\b',
    '엽산': r'엽산|폴릭|폴레이트',
    '단백질': r'단백질|프로틴|웨이|게이너',
    '식이섬유': r'식이섬유|차전자|화이바|파이버|귀리',
}
p['종합명칭'] = p['식품명'].str.contains(r'종합|멀티|올인원', regex=True).astype(int)
for n, pat in NAME_KW.items():
    p[f'name_{n}'] = (name_all.str.contains(pat, case=False, regex=True) | p['종합명칭'].astype(bool)).astype(int)
    # 목적 일치: 기능성 키워드가 없거나, 있어도 이름에 이 영양소가 나오면 이 영양소 추천 후보
    p[f'목적일치_{n}'] = ((p['주목적_기능성'] == '') | (p[f'name_{n}'] == 1)).astype(int)

# 종합형 풀 (준혁님 아이디어 + 수정): 이름에 종합·멀티·올인원 또는 성분 5개 이상. '메가'는 오메가3·메가 B컴플렉스가 걸려서 제외
p['종합형'] = ((p['종합명칭'] == 1) | (p['구성성분수'] >= 5)).astype(int)
p.loc[(p['주목적_기능성'] != '') & (p['종합명칭'] == 0), '종합형'] = 0     # 기능성 주목적 제품은 이름이 종합일 때만

p.to_csv(OUT / 'product_features.csv', index=False, encoding='utf-8-sig')
print('전체', len(p), '| 우리 영양소 목록에 해당하는 성분이 1개 이상인 제품', p['대상제품'].sum(),
      '| 해당 없음(홍삼·프로폴리스 등)', (p['대상제품'] == 0).sum())
print(pd.Series({c[2:]: (p[c] > 0).sum() for c in V}).sort_values(ascending=False).to_string())
print('품질 표시:', {k: int(p[f'form_{k}'].sum()) for k in FORM}, '| 베타카로틴', p['베타카로틴함유'].sum(), '| UL초과', p['UL초과'].sum())
print('1일 개수 분포', p['1일개수'].describe()[['50%', 'max']].to_dict())
t = p[p['대상제품'] == 1]
print('\n[v5] 기능성 주목적 제품', int((t['주목적_기능성'] != '').sum()), '/', len(t), '|',
      {k: int(t[f'func_{k}'].sum()) for k in FUNC_KW})
print('[v5] 종합형 풀', int(t['종합형'].sum()), '(이름 종합·멀티·올인원', int(t['종합명칭'].sum()), '| 성분 5개+', int((t['구성성분수'] >= 5).sum()), ')')
b1 = t['pct_티아민'] >= 100
print('[v5] B1 100%↑', int(b1.sum()), '→ 목적 일치(B 추천 후보로 인정)', int((b1 & (t['목적일치_티아민'] == 1)).sum()))
