# -*- coding: utf-8 -*-
"""
영양제 분류·필터링 공통 설정
- 모든 단계 파일(입력엑셀_최종본_만들기.py, 1단계_...py)이 이 파일을 불러서 씁니다.
- 기준: 「영양제_분류_필터링_기준(1104).pdf」
"""
import os, re, unicodedata, warnings
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

warnings.filterwarnings("ignore")

# ── 경로
# 이 파일이 있는 폴더(HERE)에 결과 엑셀을 저장해요.
# 원본 데이터(메인.csv, 기존 제품목록)는 아래 순서로 찾아요.
#   ① 이 폴더 ② 바로 위 폴더 (깃허브의 junhyeok 폴더) ③ 바탕화면\영양제품 자료
#   ④ 바탕화면\분류 및 필터링 작업에 필요한 최종 파일들
HERE = os.path.dirname(os.path.abspath(__file__))
_DESK = os.path.join(os.path.expanduser("~"), "Desktop")
SEARCH = [HERE, os.path.dirname(HERE),
          os.path.join(_DESK, "영양제품 자료"),
          os.path.join(_DESK, "분류 및 필터링 작업에 필요한 최종 파일들")]


def find(name):
    """원본 파일을 SEARCH 순서대로 찾기"""
    for folder in SEARCH:
        path = os.path.join(folder, name)
        if os.path.exists(path):
            return path
    raise FileNotFoundError(f"{name} 파일을 찾을 수 없어요. 이 폴더나 바탕화면의 '영양제품 자료' 폴더에 넣어 주세요.")


DATA = HERE
PRODUCT_XLSX = "성분별_영양제_제품목록(수출 제외).xlsx"      # 기존 목록 (최종본 만들 때만 사용)
FINAL_XLSX = "성분별_영양제_제품목록(최종).xlsx"            # 분류·필터링 입력
MAIN_CSV = "메인.csv"                                       # 식약처 C003 원본


def out(name):
    """결과 파일 경로 (이 폴더 안)"""
    return os.path.join(HERE, name)


def load_final():
    """최종본 엑셀의 '제품 목록' 시트 (제품당 한 줄) 읽기"""
    book = pd.ExcelFile(find(FINAL_XLSX))
    sheet = [s for s in book.sheet_names if s.startswith("제품 목록")][0]
    d = pd.read_excel(book, sheet_name=sheet, dtype=str).fillna("")
    return d


def nf(t):
    """글자 모양 통일 (전각·반각 등)"""
    return unicodedata.normalize("NFKC", t or "")


def load_main():
    """메인.csv (식약처 C003 원본) 읽기. 품목제조신고번호를 색인으로."""
    m = pd.read_csv(find(MAIN_CSV), encoding="utf-8-sig", dtype=str).fillna("")
    return m.drop_duplicates("PRDLST_REPORT_NO").set_index("PRDLST_REPORT_NO")


# ── 대상 판별 키워드 (기준 PDF 2절, 3-4절: 어린이에 '우리 아이·앙팡·Kid's' 추가)
TARGET = [
    ("어린이", r"키즈|어린이|주니어|유아|아기|베이비|앙팡|우리\s*아이|(?i:kids?\b|kid's|junior|baby|children|enfant)"),
    ("임산부·수유부", r"임산부|임신|수유|산모|(?i:prenatal|pregnan|mama)"),
    ("시니어", r"실버|시니어|50\+|(?i:silver|senior)"),
    ("남성", r"남성|(?<![가-힣])맨(?![가-힣])|(?i:\bmen\b|\bman\b|for him)"),
    ("여성", r"여성|우먼|레이디|(?i:women|woman|lady|for her)"),
]


# ── 제외·표시용 패턴 (입력 엑셀 최종본과 1단계에서 같이 씀)
# 괄호 안 해외 국가명 → 해외 판매 의심 (기준 PDF 2절)
OVERSEAS = (r"\([^)]*(?:우즈베키스탄|카자흐스탄|키르기스|베트남|몽골|중국|대만|홍콩|러시아|태국|"
            r"인도네시아|말레이시아|필리핀|싱가포르|캄보디아|미얀마)")
# 제품명에 질환(또는 질환 관련 수치)을 직접 내세운 경우 (11-04 결정, 갑상선 포함)
DISEASE = (r"당뇨|혈당|당\s*케어|혈압|고지혈|콜레스테롤|골다공증|갑상선|전립선|치매|관절염|"
           r"간\s*질환|지방간|통풍|요산|환자|투석|항암")


def target_of(name):
    for label, pat in TARGET:
        if re.search(pat, name or ""):
            return label
    return "일반"


# ── 기준·고려사항 목록 (기준 PDF 1104). 단계를 진행하면 처리 상태를 바꿉니다.
CRITERIA = [
    # (단계, 구분, 기준·고려사항, PDF 위치)
    ("0", "데이터", "식품영양성분DB(보조 출처, 대부분 수입) 제품은 분류하지 않음", "2절"),
    ("0", "데이터", "기능성 문구만 있는 제품도 성분으로 인정 (원재료에 해당 원료 + 기능성 칸에 식약처 문구)", "3-4절"),
    ("0", "데이터", "원재료·섭취방법·기준규격은 메인.csv(C003 원본)에서 붙임", "2절"),
    ("1", "기본 거르기", "2022년 이후 신고 제품만 (프로젝트 수집 범위 제한, 판매 중이라는 뜻 아님)", "2절"),
    ("1", "기본 거르기", "제품명에 '수출' 또는 괄호 안 해외 국가명(우즈베키스탄·베트남 등)이 있으면 제외", "2절"),
    ("1", "기본 거르기", "대상 판별: 제품명 키워드 (어린이에 '우리 아이·앙팡·Kid's' 추가). '일반'만 다음 단계로, 나머지는 보관", "2절, 3-4절"),
    ("1", "기본 거르기", "임산부·수유부 대상 제품은 제외 (11-04 결정, 보관하지 않음)", "5-4절"),
    ("1", "기본 거르기", "제품명이 질환을 대상으로 하는 제품(당뇨·혈당·혈압·콜레스테롤·골다공증·전립선·갑상선 등)은 제외 (11-04 결정)", "5-4절, 10절"),
    ("1", "기본 거르기", "일반·전문 의약품 없음 확인", "2절"),
    ("2", "성분 확인", "성분은 기능성 칸으로 판단, 원재료 칸은 보조 (부형제 오인 방지)", "2절"),
    ("2", "성분 확인", "나이아신·판토텐산·비오틴은 비타민 B군으로 인정 (모델의 B1·B2도 B군으로 통일)", "3-1절, 5-1절"),
    ("2", "성분 확인", "식이섬유는 기능성 칸에 식이섬유 원료 이름이 있을 때만 인정", "3-4절"),
    ("2", "성분 확인", "제품명에 나온 영양소가 기능성 칸에 없으면 '확인 필요'", "3-4절"),
    ("2", "성분 확인", "원료 껍데기형(홍삼·천마 등 주원료에 영양소만 넣은 제품)은 '확인 필요'", "3-4절"),
    ("3", "목적 충돌", "다른 목적 원료·문구(체지방·혈당, 관절, 피부, 혈압, 기억력, 갱년기, 단백질·근력 등)가 섞이면 제외", "3-4절"),
    ("3", "목적 충돌", "제품명의 피부·미백·다이어트·콜라겐·관절·프로틴 등도 목적 충돌로 제외", "3-4절"),
    ("3", "목적 충돌", "수면·긴장 원료(테아닌 등)는 제외 대신 '스트레스 참고'", "3절, 9절"),
    ("3", "목적 충돌", "오메가3 자체의 기억력 문구, 식이섬유의 콜레스테롤 문구는 충돌로 보지 않음", "3-4절"),
    ("4", "풀 나누기", "단일: 성분 1개 또는 주성분 1개 + 보조 1개. 가이드 밖 영양소(셀렌 등)는 1개까지만 보조", "3절, 3-1절"),
    ("4", "풀 나누기", "주성분 판단 순서: 제품명 → 기능성 원료 쪽 → 기준치 대비 2배 이상", "3-1절"),
    ("4", "풀 나누기", "제품명에 우리 영양소가 2개 이상이면 단일이 아니라 목적형", "3-1절"),
    ("4", "풀 나누기", "목적형: 성분 2~6개, 단서 가중치 제품명 3 · 기능성 원료 문구 2 · 비타민·미네랄 문구 1, 판정 7단계, 목적 3개 이상이면 제외, 두 목적이면 복수 목적", "3-3절"),
    ("4", "풀 나누기", "종합비타민: 성분 7개 이상 또는 이름에 멀티·종합·올인원 + 3개 이상. 균형형 / 피로회복형(B군·C + 피로 관련 이름·문구)", "3절, 8절"),
    ("4", "풀 나누기", "칼슘+철 제품도 제외하지 않음 (주의사항 원문 표시)", "6-②절"),
    ("5", "모델 연결", "13개 항목(비타민 A·E·K·칼륨 단일은 후보에서 제외)별로 단일·목적형 후보를 묶음", "1절, 5-1절"),
    ("5", "모델 연결", "목적형은 이름이 아니라 해당 성분이 실제로 든 제품만 (함께 든 가이드 성분 열로 확인). 혈행 그룹이라고 오메가3 연결 금지", "5-1절"),
    ("5", "모델 연결", "단백질·인·칼륨·비타민 A·나트륨은 제품 없이 식품·식습관 안내", "5-1절"),
    ("5", "모델 연결", "비타민 D는 일반 정보로, 유산균·오메가3·루테인·밀크씨슬은 직접 응답·관심 고민 선택으로 연결 (설문 확인 후 확정)", "5-2절"),
    ("5", "모델 연결", "제품 식별자는 품목제조신고번호, 여러 영양소에 해당하면 중복 제거", "5-3절, 5-5절"),
    ("-", "후보 압축", "후보를 몇 개까지 남길지 결정", "11절"),
    ("6", "1일 환산", "압축된 후보만 표시량(함량/기준 중량) × 섭취방법으로 1일 섭취량당 함량 계산. 안 되면 확인 필요", "2절"),
    ("7", "상한 거르기", "상한섭취량 초과 제품 제외 (모든 포함 성분 확인, 마그네슘은 식품 외 섭취분, B군은 개별 단위, 상한 미설정 ≠ 무제한)", "6-①절"),
    ("7", "상한 거르기", "기능성 원료는 상한이 아니라 식약처 인정 섭취범위로 확인 (오메가3는 기능성별 범위)", "6-①절"),
    ("8", "점수", "함량 기준 충족 50: 기준치 100% 이상 50 / 30~100% 40 / 30% 미만 20 / 상한 80% 이상 −10 (고함량 가점 없음)", "6-①절"),
    ("8", "점수", "섭취 편의 25: 하루 1개 25 / 2개 15 / 3개 이상 6 / 미확인 12 + 정보 미확인 표시", "6-③절"),
    ("8", "점수", "주의 원료 15: 없음 15 / 있음 0", "6-④절"),
    ("8", "점수", "성분 구성 관련성 10: 철←비타민 C, 칼슘←비타민 D만 10점, 나머지 짝은 설명 정보", "6-②절"),
    ("9", "후보 고르기", "화면에 보여 줄 제품 선택 (개수, 동점 처리, 다양성)", "11절"),
    ("화면", "사용자 조건", "약 복용·임신·수유·신장질환·19세 미만이면 제품 전체 보류 + 상담 안내 (미응답은 추가 확인)", "5-4절"),
    ("화면", "사용자 조건", "현재 영양제 복용자는 성분 중복 확인 전 보류", "5-4절"),
    ("화면", "사용자 조건", "두 모델 결과 조합: High 포함 + 불일치 아님 → 제품군, 불일치 → 재확인, Mid/Low → 식품·일반 안내", "5-3절"),
    ("화면", "표현", "제안 톤, 처방·진단 표현 금지, 1위·베스트·안전한 제품 표현 금지, 1일 함량·기준치 %·식약처 문구 원문 표시, 고지문", "10절"),
    ("화면", "표현", "쓰지 않는 기준: 가격·판매처, 브랜드·랭킹, 함량 백분위, 위험도→고함량 연결, 원료 형태", "7절"),
]

# 처음 상태. 각 단계가 끝나면 그 단계 파일에서 '적용 완료 (…)'로 바꿉니다.
DEFAULT_STATUS = {
    "-": "논의 필요", "9": "논의 필요",
    "화면": "추천 화면 단계 (엑셀 필터 아님)",
}
SPECIAL_STATUS = {
    "비타민 D는 일반 정보로": "방향 확정, 설문 확인 필요",
    "상한섭취량 초과 제품 제외": "2025 KDRI 값 확정 필요",
    "기능성 원료는 상한이 아니라": "원문 확인 필요",
    "주의 원료 15": "주의 원료 목록 확정 필요",
    "현재 영양제 복용자": "팀 확정 필요",
}


def criteria_table(done):
    """done: {기준 문구 앞부분: '적용 완료 (…)'} → 기준·고려사항 표"""
    rows = []
    for step, kind, text, pdf in CRITERIA:
        status = DEFAULT_STATUS.get(step, "적용 예정")
        for key, st in SPECIAL_STATUS.items():
            if text.startswith(key):
                status = st
        for key, st in done.items():
            if text.startswith(key):
                status = st
        rows.append((step, kind, text, pdf, status))
    return pd.DataFrame(rows, columns=["단계", "구분", "기준·고려사항", "기준 PDF", "처리"])


# ── 엑셀 저장 도우미
_ILLEGAL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_HEAD = PatternFill("solid", fgColor="23324D")
_HEAD_FONT = Font(bold=True, color="FFFFFF")


def _clean(v):
    if isinstance(v, str):
        return _ILLEGAL.sub("", v)
    if v is None or (isinstance(v, float) and v != v):
        return None
    return v


def new_book(summary_lines):
    """요약 시트가 있는 새 엑셀. summary_lines: [(문장, 굵게 여부)]"""
    wb = Workbook()
    ws = wb.active
    ws.title = "요약"
    for text, bold in summary_lines:
        ws.append([text])
        if bold:
            ws.cell(ws.max_row, 1).font = Font(bold=True, size=11)
    ws.column_dimensions["A"].width = 130
    return wb


def add_sheet(wb, name, df, widths=None):
    ws = wb.create_sheet(name)
    ws.append(list(df.columns))
    for c in ws[1]:
        c.fill, c.font = _HEAD, _HEAD_FONT
    for row in df.itertuples(index=False):
        ws.append([_clean(x) for x in row])
    for i in range(len(df.columns)):
        ws.column_dimensions[get_column_letter(i + 1)].width = widths[i] if widths and i < len(widths) else 18
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = ws.dimensions
    return ws


def add_criteria_sheet(wb, done):
    df = criteria_table(done)
    ws = add_sheet(wb, "기준·고려사항", df, [7, 12, 95, 14, 30])
    ws.freeze_panes = "A2"
    for r in ws.iter_rows(min_row=2):
        for c in r:
            c.alignment = Alignment(wrap_text=True, vertical="top")
        st = r[4].value
        color = "E2F0D9" if "완료" in st else ("FCE4D6" if "필요" in st else ("EDEDED" if "화면" in st else None))
        if color:
            r[4].fill = PatternFill("solid", fgColor=color)
    return df
