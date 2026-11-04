"""
준혁님·유환님 제품 분류 결과를 웹용 제품 목록으로 바꾼다 → web/src/data/supplementProducts.json

입력: 화면에 보여 줄 제품만 모은 표 1개 (CSV 또는 엑셀 첫 시트). 원본·전체 목록은 구글 드라이브에 두고 저장소에 올리지 않는다
  준혁님 분류·필터링 기준 v3(junhyeok/영양제_분류_필터링_기준(피드백).pdf)으로 고르고 점수 순으로 정렬한 결과
  한 줄 = 제품 하나, 같은 영양소·대상 안에서 위에 있을수록 먼저 보여 준다 (화면에는 순위 번호를 쓰지 않는다)

  열 이름                  내용
  영양소                   비타민 B군 · 비타민 C · 비타민 D · 칼슘 · 마그네슘 · 아연 · 철 · 엽산 · 식이섬유
                           · 종합비타민(균형형) · 종합비타민(피로회복형)
  제품명 / 업체명          업체명은 제조사 (브랜드 아님)
  품목제조신고번호
  대상                     일반 · 남성 · 여성 · 시니어 (어린이·임산부·수유부 대상은 넣지 않는다)
  1일 섭취량               예: 1일 1정 (선택)
  1일 함량                 1일 섭취량당 함량, 예: 500 mg (선택, 환산 전이면 비워 둔다)
  기준치 대비(%)           1일 영양성분 기준치 대비 % (선택)
  기능성                   식약처 기능성 문구 원문
  섭취 시 주의사항         제품 표시 문구 원문 (선택)

  가격·판매처·점수·순위 열은 있어도 웹으로 옮기지 않는다 (v3 6절: 홍보처럼 보일 수 있음)

실행 (bigskyyang 폴더에서)
  python scripts/build_supplement_products.py 경로/영양제_웹표시목록.xlsx
"""

import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parents[1] / 'web' / 'src' / 'data' / 'supplementProducts.json'
SOURCE = '식품의약품안전처 건강기능식품 품목제조 신고사항(C003), 2022년 이후 신고분'

# 영양소 이름 → 웹 키 (web/src/data/supplementInfo.js의 PRODUCT_NUTRIENTS)
NUTRIENTS = {
    '비타민 B군': 'vitamin_b', '비타민 C': 'vitamin_c', '비타민 D': 'vitamin_d', '칼슘': 'calcium', '마그네슘': 'magnesium',
    '아연': 'zinc', '철': 'iron', '엽산': 'folate', '식이섬유': 'fiber',
}
MULTI = {'종합비타민(균형형)': 'balanced', '종합비타민(피로회복형)': 'fatigue'}
TARGETS = {'일반', '남성', '여성', '시니어'}
PER_GROUP = 3          # 영양소 × 대상마다 남길 제품 수 (웹은 내 대상 중 앞에서 3개)

COLUMNS = {
    '제품명': 'name', '업체명': 'maker', '품목제조신고번호': 'reportNo', '대상': 'target', '1일 섭취량': 'perDay',
    '1일 함량': 'amount', '기준치 대비(%)': 'dvPct', '기능성': 'function', '섭취 시 주의사항': 'caution',
}
REQUIRED = ['영양소', '제품명', '업체명', '품목제조신고번호', '대상', '기능성']


def read(path):
    path = Path(path)
    if path.suffix.lower() in ('.xlsx', '.xls'):
        return pd.read_excel(path, dtype=str)
    return pd.read_csv(path, dtype=str, encoding='utf-8-sig')


def clean(v):
    if v is None or pd.isna(v):
        return None
    v = str(v).strip()
    return v or None


def product(row):
    p = {key: clean(row.get(col)) for col, key in COLUMNS.items()}
    if p['dvPct'] is not None:
        p['dvPct'] = round(float(p['dvPct'].rstrip('%')))
    return p


def main(path):
    df = read(path)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        sys.exit(f'필요한 열이 없어요: {missing}')

    out = {
        'version': date.today().isoformat(),
        'source': SOURCE,
        'note': f'{Path(path).name}에서 scripts/build_supplement_products.py로 만듦',
        'nutrients': {},
        'multivitamin': {k: [] for k in MULTI.values()},
    }
    skipped = []
    for _, row in df.iterrows():
        name, target = clean(row['영양소']), clean(row['대상'])
        if target not in TARGETS:
            skipped.append(f"{row['제품명']} (대상 {target})")
            continue
        if any(clean(row[c]) is None for c in REQUIRED):
            skipped.append(f"{row['제품명']} (빈 칸)")
            continue
        if name in NUTRIENTS:
            group = out['nutrients'].setdefault(NUTRIENTS[name], [])
        elif name in MULTI:
            group = out['multivitamin'][MULTI[name]]
        else:
            sys.exit(f'모르는 영양소: {name} (가능: {list(NUTRIENTS) + list(MULTI)})')
        if sum(p['target'] == target for p in group) < PER_GROUP:
            group.append(product(row))

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    n = sum(map(len, out['nutrients'].values())) + sum(map(len, out['multivitamin'].values()))
    print(f'{OUT.name}: 제품 {n}개 ({", ".join(f"{k} {len(v)}" for k, v in out["nutrients"].items())})')
    for s in skipped:
        print('  뺌:', s)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('사용법: python scripts/build_supplement_products.py 경로/영양제_웹표시목록.xlsx')
    main(sys.argv[1])
