"""영양분석 공통: 경로, 2025 KDRI 성인 기준표, 사람 데이터 로더, 흡수 관련 근거표.

군집 파일이 바뀌면 load_persons(cluster_file, label_col)만 바꿔 부르면 된다.
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '영양분석' / 'output'
OUT.mkdir(parents=True, exist_ok=True)

AGE_BINS = [18, 29, 49, 64, 74, 200]
AGE_LABELS = ['19-29', '30-49', '50-64', '65-74', '75+']

# ── 2025 KDRI 성인 기준 (보건복지부, 2025 KDRI 요약표 국문 2025.12.29, xii~xvii쪽) ──
# basis: EAR(평균필요량, 미만 = 부족 위험) / AI(충분섭취량, 미만 = 참고지표, 부족이라 단정 못 함)
# 값 순서: 19-29, 30-49, 50-64, 65-74, 75+
KDRI = {
    # 영양소     KNHANES 열      basis  남자                          여자                          UL(성인 최저)  쪽
    '단백질':    ('영양_N_PROT',   'EAR', [50, 50, 50, 50, 50],         [45, 40, 40, 40, 40],         None, 'x'),
    '비타민A':   ('영양_N_VA_RAE', 'EAR', [570, 560, 530, 520, 500],    [460, 450, 430, 410, 410],    3000, 'xii'),
    '비타민D':   ('영양_N_VITD',   'AI',  [10, 10, 10, 15, 15],         [10, 10, 10, 15, 15],         100,  'xii'),
    '비타민E':   ('영양_N_VITE',   'AI',  [12, 12, 12, 12, 12],         [12, 12, 12, 12, 12],         540,  'xii'),
    '비타민C':   ('영양_N_VITC',   'EAR', [75, 75, 75, 75, 75],         [75, 75, 75, 75, 75],         2000, 'xiii'),
    '티아민':    ('영양_N_B1',     'EAR', [1.0, 1.0, 1.0, 0.9, 0.9],    [0.9, 0.9, 0.9, 0.8, 0.7],    None, 'xiii'),
    '리보플라빈': ('영양_N_B2',     'EAR', [1.3, 1.3, 1.3, 1.2, 1.1],    [1.0, 1.0, 1.0, 0.9, 0.8],    None, 'xiii'),
    '엽산':      ('영양_N_FOLATE', 'EAR', [320, 320, 320, 320, 320],    [320, 320, 320, 320, 320],    1000, 'xiv'),   # μg DFE (UL은 엽산 보충제 μg)
    '칼슘':      ('영양_N_CA',     'EAR', [650, 650, 650, 650, 650],    [500, 500, 650, 600, 600],    2000, 'xvi'),
    '인':        ('영양_N_PHOS',   'EAR', [540, 540, 540, 540, 540],    [540, 540, 540, 540, 540],    3000, 'xvi'),
    '칼륨':      ('영양_N_K',      'AI',  [3500, 3500, 3500, 3500, 3500], [3500, 3500, 3500, 3500, 3500], None, 'xvi'),
    '마그네슘':  ('영양_N_MG',     'EAR', [300, 310, 310, 310, 310],    [240, 240, 240, 240, 240],    350,  'xvi'),   # UL은 식품 외 급원
    '철':        ('영양_N_FE',     'EAR', [6, 6, 6, 6, 5],              [7, 7, 5, 4, 4],              45,   'xvii'),
    '아연':      ('영양_N_ZN',     'EAR', [9, 8, 8, 8, 7],              [7, 7, 6, 6, 6],              35,   'xvii'),
    '식이섬유':  ('영양_N_TDF',    'AI',  [30, 30, 30, 30, 30],         [20, 20, 25, 25, 25],         None, 'ix'),
}
NUTRIENTS = list(KDRI)

# 추천 목록에 있지만 KNHANES 섭취량이 없어 데이터로 필요도를 판단할 수 없는 것 → 참고 정보로만
NO_INTAKE_DATA = ['비타민K', '비타민B6', '비타민B12', '오메가3', '유산균', '루테인', '밀크씨슬']

# ── 영양소 칼럼 3세트 (분석용 ≠ 고객 안내용 ≠ 제품 매칭용) ──
# 분석용: KNHANES 섭취량 + KDRI 기준이 둘 다 있어 '부족 위험'을 판정할 수 있는 것 = KDRI 키 전체(15개)
# 고객 안내용: 화면에 보여줄 이름 묶음. 영양제 추천 대상 / 식품으로만 안내 / 참고 정보로 나눔
CUSTOMER_GROUP = {
    '단백질': '단백질', '비타민A': '비타민 A·D·E', '비타민D': '비타민 A·D·E', '비타민E': '비타민 A·D·E',
    '비타민C': '비타민 C', '티아민': '비타민 B군', '리보플라빈': '비타민 B군', '엽산': '엽산',
    '칼슘': '칼슘·마그네슘', '마그네슘': '칼슘·마그네슘', '철': '철·아연', '아연': '철·아연',
    '식이섬유': '식이섬유', '인': '(식품 안내)', '칼륨': '(식품 안내)',
}
FOOD_ONLY = ['인', '칼륨']          # 팀 가이드: 인은 영양제 추천 안 함, 칼륨은 식품으로만
# 대리지표: 섭취량 자료가 없는 기능성 원료의 '참고' 근거 (순위에는 안 씀)
PROXY = {'오메가3': '보조_FISH_G', '칼슘(설명)': '보조_DAIRY_G'}

# ── 흡수 관련 근거 (2025 KDRI 2권 비타민 / 3권 무기질, 쪽은 PDF 쪽번호) ──
# strength: 강 = 기능으로 명시 / 약 = 원문이 '근거 불충분'이라고 적음
ABSORPTION = pd.DataFrame([
    # 유형,   A,        B,        효과,                                   strength, 출처
    ('상승', '비타민D', '칼슘',   '비타민D가 소장의 칼슘·인 흡수 촉진',        '강', '2권 p91, p97'),
    ('상승', '비타민D', '인',     '비타민D가 소장의 칼슘·인 흡수 촉진',        '강', '2권 p91, p97'),
    ('상승', '비타민C', '철',     '비타민C(약 75mg)가 비헴철 흡수 향상',       '강', '2권 p204, 3권 p218'),
    ('저해', '칼슘',    '철',     '과량 칼슘이 철 흡수 저해 가능',            '약', '3권 p50 (근거 불충분 명시)'),
    ('저해', '칼슘',    '아연',   '과량 칼슘이 아연 흡수 저해 가능',          '약', '3권 p50 (근거 불충분 명시)'),
    ('저해', '철',      '아연',   '철 과량 섭취가 아연 흡수 감소 가능',       '약', '3권 p214 (근거 부족 명시)'),
], columns=['유형', 'A', 'B', '효과', '근거강도', '출처'])

# 생활습관이 흡수·배설에 미치는 영향 (정성적, 수치 보정계수 없음)
LIFESTYLE_ABSORPTION = pd.DataFrame([
    ('음주', '티아민',   '만성 알코올 섭취가 소장 흡수를 저해해 체내 이용률 감소', '2권 p240', True),
    ('음주', '마그네슘', '알코올·카페인이 소변 마그네슘 배설 증가',             '3권 p184', True),
    ('흡연', '비타민C',  '흡연자 권장량을 늘려야 한다는 근거 불충분 → 적용 안 함', '2권 p216', False),
], columns=['생활습관', '영양소', '내용', '출처', '적용'])
# 지용성(A·D·E·K)은 지방과 같은 방식으로 흡수(2권 p49) → 복용 안내 '식사와 함께'


# 최종 11개 유형: analysis/01_clustering/kmedoids_finally.py 를 COMPLETECASE CSV로 실행한 결과 (개인 단위라 깃허브엔 안 올림)
FINAL_CLUSTER_FILE = ROOT / 'KMedoids_Final_Corrected.xlsx'


def load_persons(cluster_file=ROOT / 'KMeans_Final_MicroClustered.xlsx', label_col='Sub_Cluster'):
    """ID + 군집 라벨 파일과 ANALYSIS_BASE를 ID로 결합. 군집 파일의 ML_ 생활습관 변수도 같이 가져온다."""
    cf = Path(cluster_file)
    lab = pd.read_excel(cf) if cf.suffix in ('.xlsx', '.xls') else pd.read_csv(cf, encoding='utf-8-sig')
    keep = ['ID', label_col] + [c for c in lab.columns if c.startswith('ML_')]
    base = pd.read_csv(ROOT / 'KNHANES_2022_2024_ANALYSIS_BASE.csv', encoding='utf-8-sig', low_memory=False)
    d = lab[keep].rename(columns={label_col: 'cluster'}).merge(base, on='ID', how='inner')
    # 유형 이름은 지연님 코드가 군집 번호에 고정으로 붙여서 데이터와 안 맞는 곳이 있음(0_A·0_B 뒤바뀜)
    # → 분석·웹 키는 번호만 사용 (예: 'Group_0_A(유산소형)' → 'Group_0_A'), 엑셀 이름은 참고로 보관
    d['엑셀이름'] = d['cluster'].astype(str).str.extract(r'\((.*)\)$')[0].fillna('')
    d['cluster'] = d['cluster'].astype(str).str.replace(r'\(.*\)$', '', regex=True)
    assert len(d) == len(lab), '군집 파일 ID 중 ANALYSIS_BASE에 없는 ID가 있음'
    d['sex'] = d['설명_sex'].map({1: '남자', 2: '여자'})
    d['age'] = d['설명_age']
    d['age_grp'] = pd.cut(d['age'], AGE_BINS, labels=AGE_LABELS)
    d['w'] = d['wt_tot'] / 3   # 3개년 통합 가중치 (이용지침서 p47 예제 방식)
    # 파생변수 1: 과일·채소 섭취빈도(최근 1년, 설문) → 주당 횟수 (이용지침서 p228 보기를 대표값으로 근사)
    #   1 하루3회↑=21, 2 하루2회=14, 3 하루1회=7, 4 주5-6회=5.5, 5 주2-4회=3, 6 주1회=1,
    #   7 월2-3회=0.58(2.5/4.3), 8 월1회=0.23(1/4.3), 9 거의 안 먹음=0, 99 모름/무응답=결측
    per_week = {1: 21, 2: 14, 3: 7, 4: 5.5, 5: 3, 6: 1, 7: 2.5 / 4.3, 8: 1 / 4.3, 9: 0}
    d['과일_주당'] = d['식습관_LS_FRUIT'].map(per_week)
    d['채소_김치포함_주당'] = d['식습관_LS_VEG1'].map(per_week)
    d['채소_김치제외_주당'] = d['식습관_LS_VEG2'].map(per_week)
    return d


def add_status(d):
    """사람마다 본인 성별·연령 KDRI 기준과 비교: below_<영양소> = 1/0, ratio_<영양소> = 섭취/기준."""
    idx = d['age_grp'].cat.codes.values
    male = (d['sex'] == '남자').values
    new = {}                                  # 열을 모아서 한 번에 붙임 (조각난 프레임 경고 방지)
    for n, (col, basis, m, f, ul, _) in KDRI.items():
        ref = np.where(male, np.array(m)[idx], np.array(f)[idx]).astype(float)
        new[f'ref_{n}'] = ref
        new[f'ratio_{n}'] = d[col].values / ref
        new[f'below_{n}'] = (d[col].values < ref).astype(int)
    d = pd.concat([d, pd.DataFrame(new, index=d.index)], axis=1)
    # 파생변수 2: 부족 영양소 개수 (EAR 기준 11개 중 미만 개수 = 부족 위험 / AI 기준 4개는 참고라 따로)
    ear = [n for n in KDRI if KDRI[n][1] == 'EAR']
    ai = [n for n in KDRI if KDRI[n][1] == 'AI']
    d['부족개수_EAR'] = d[[f'below_{n}' for n in ear]].sum(axis=1)
    d['미만개수_AI'] = d[[f'below_{n}' for n in ai]].sum(axis=1)
    return d
