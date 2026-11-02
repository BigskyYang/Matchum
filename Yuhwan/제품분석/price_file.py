"""가격 조사 엑셀(가격조사_대상.xlsx) 읽기·쓰기.

팀원이 쉽게 채우도록: 채울 칸은 노란 헤더, 자동 칸은 회색, '1일가격(자동)' 엑셀 수식, '작성방법' 시트 포함.
04_제품추천.py가 새 후보를 덧붙일 때도 이 형식을 유지한다.
"""
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter

SHEET = '가격조사'
INFO = ['식품코드', '식품명', '제조사명', '품목제조신고번호', '제품유형명', '주성분',
        '1회분량', '1회분량중량', '1일섭취횟수', '1일개수', '총개수_제품명추정', '검색어']
FILL = ['판매가격(원)', '총개수']            # 꼭 채울 칸
AUTO = ['1일가격(자동)']                     # 엑셀 수식
MORE = ['판매처', 'URL', '조사일', '비고']    # 채울 칸(보조)
COLUMNS = INFO + FILL + AUTO + MORE

GUIDE = [
    ('항목', '뜻', '예시'),
    ('■ 미리 채워둔 칸 (수정하지 마세요)', '', ''),
    ('1회분량', '한 번 먹을 때의 양 (식약처 표시 기준)', '2정 → 한 번에 2정'),
    ('1회분량중량', '1회분량의 무게(또는 부피). 분말·액상 총개수 계산에 씀', '31000mg = 31g / 20ml'),
    ('1일섭취횟수', '하루에 몇 번 먹는지', '2 → 하루 2번'),
    ('1일개수', '하루에 먹는 총 개수 = 1회분량 숫자 × 1일섭취횟수 (단위는 1회분량과 같음)', '2정 × 2번 = 4 (하루 4정)'),
    ('총개수_제품명추정', '제품명에 "(112정)"처럼 적힌 숫자를 자동으로 뽑은 참고값. 틀릴 수 있으니 판매 페이지로 꼭 확인', '센트룸실버맨(112정) → 112'),
    ('검색어', '네이버쇼핑에 그대로 붙여넣을 검색어 (제품명 + 제조사)', ''),
    ('■ 채울 칸 (노란색)', '', ''),
    ('판매가격(원)', '한 통(단품)의 판매가. 숫자만 (원·쉼표 없이)', '23900'),
    ('총개수', '한 통에 든 개수. ★ 1회분량과 같은 단위로 (정이면 정, 포면 포, 스쿱이면 스쿱)', '120정짜리 → 120'),
    ('판매처', '가격을 본 쇼핑몰 이름', '쿠팡 / 네이버 스마트스토어(OO약국)'),
    ('URL', '상품 페이지 주소 (가격비교 목록 말고 실제 상품 페이지)', 'https://...'),
    ('조사일', '조사한 날짜', '2026-11-03'),
    ('비고', '특이사항: 없음 / 해외직구 / 세트만 있음 / 단위 다름 등', '없음'),
    ('■ 자동 칸 (회색)', '', ''),
    ('1일가격(자동)', '= 판매가격 ÷ (총개수 ÷ 1일개수). 판매가격·총개수를 넣으면 자동 계산. 이상하게 크거나 작으면 총개수 단위를 다시 확인', '30000원, 120정, 하루 4정 → 30일분 → 1,000원/일'),
    ('', '', ''),
    ('■ 가격 찾는 기준 (모두 같은 기준으로!)', '', ''),
    ('1. 검색', '검색어 칸을 복사해 네이버쇼핑에 검색 → 제품명·제조사·1회분량이 같은 제품인지 확인', ''),
    ('2. 가격', '가격비교의 단품 최저가. 배송비·쿠폰·카드할인·멤버십 할인은 빼고 표시가 그대로', ''),
    ('3. 묶음', '2개·3개 묶음 말고 1개 단품 가격. 묶음만 있으면 묶음가 ÷ 개수, 비고에 "세트만 있음"', '2개 39800원 → 19900'),
    ('4. 용량', '제품명에 용량(예: 112정)이 있으면 그 용량. 없으면 판매 페이지의 가장 작은 기본 용량', ''),
    ('5. 분말·액상', '총개수 = 라벨의 "총 ○회분". 없으면 총 내용량 ÷ 1회분량중량', '900g ÷ 31g = 29 (스쿱)'),
    ('6. 해외직구', '원화 가격 그대로(배송비 제외), 비고에 "해외직구"', ''),
    ('7. 못 찾음', '판매가격·총개수 비우고 비고에 "없음" (단종·품절 포함)', ''),
    ('8. 맛만 다름', '맛이 다른 제품도 각 행을 따로 채움 (가격이 같으면 같은 값)', ''),
]


def read_price_file(path):
    df = pd.read_excel(path, sheet_name=0)
    # 팀원이 '23,900원'·'120정'처럼 적어도 숫자로 읽음 (쉼표·글자 제거)
    for c in FILL:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce')
    return df.drop(columns=[c for c in AUTO if c in df.columns])


def write_price_file(df, path):
    df = df.reindex(columns=COLUMNS)
    with pd.ExcelWriter(path, engine='openpyxl') as w:
        df.drop(columns=AUTO).to_excel(w, sheet_name=SHEET, index=False)
        pd.DataFrame(GUIDE[1:], columns=GUIDE[0]).to_excel(w, sheet_name='작성방법', index=False)
    wb = load_workbook(path)
    ws = wb[SHEET]
    # 자동 수식 열 끼워 넣기
    pos = COLUMNS.index(AUTO[0]) + 1
    ws.insert_cols(pos)
    col = {name: get_column_letter(COLUMNS.index(name) + 1) for name in COLUMNS}
    ws.cell(row=1, column=pos, value=AUTO[0])
    for r in range(2, ws.max_row + 1):
        p, n, d = (f'{col[c]}{r}' for c in ['판매가격(원)', '총개수', '1일개수'])
        ws.cell(row=r, column=pos, value=f'=IF(AND(ISNUMBER({p}),ISNUMBER({n}),{n}>0),ROUND({p}/({n}/{d}),0),"")')
    yellow, grey = PatternFill('solid', fgColor='FFF2A8'), PatternFill('solid', fgColor='E0E0E0')
    for i, name in enumerate(COLUMNS, start=1):
        c = ws.cell(row=1, column=i)
        c.font = Font(bold=True)
        c.fill = yellow if name in FILL + MORE else grey
        ws.column_dimensions[get_column_letter(i)].width = {'식품명': 34, '검색어': 40, 'URL': 30, '제조사명': 22}.get(name, 13)
    ws.freeze_panes = 'C2'
    g = wb['작성방법']
    for i, w_ in enumerate([22, 70, 34], start=1):
        g.column_dimensions[get_column_letter(i)].width = w_
    for row in g.iter_rows(min_row=1):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical='top')
            if str(c.value or '').startswith('■'):
                c.font = Font(bold=True)
    wb.save(path)
