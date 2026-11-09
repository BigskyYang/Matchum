"""
준혁님 최종 제품 후보(9단계 통과 전체)를 웹용 제품 목록으로 바꾼다 → web/src/data/supplementCatalog.json

입력: scripts/inputs/web_products_20261105.xlsx (준혁님 답변에 첨부된 11-05 최신 파일)
  한 줄 = 영양소 × 대상 × 제품. '순서'는 같은 영양소·대상 안에서 먼저 볼 순서 (점수·등급은 들어 있지 않다)
연결 규칙: analysis/04_supplements/product_link (모델 영양소 → 제품 목록, B1·B2 → 비타민 B군, 대상별로 따로, 순서 그대로)

웹에서 하는 일은 고르기·보여 주기뿐이다. 제품을 더하거나 빼거나 순서를 다시 매기지 않는다.
  - 대상(일반·남성·여성·시니어)은 섞지 않고 목록을 따로 둔다
  - 같은 문구(기능성·주의사항)는 한 번만 저장하고 번호로 가리킨다 (파일 크기를 줄이려고)
  - '하루 ○○' 열은 여러 제품을 함께 고를 때 상한섭취량을 합쳐 보는 데 쓴다

실행 (저장소 루트에서)
  python scripts/build_supplement_catalog.py
"""

import argparse
import csv
import hashlib
import json
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'scripts' / 'inputs' / 'web_products_20261105.xlsx'
OUT = Path(__file__).resolve().parents[1] / 'web' / 'src' / 'data' / 'supplementCatalog.json'

# 재준님 인계 순서 (productBridge.mjs categories)
CATEGORIES = [
    ('magnesium', '마그네슘'), ('vitamin_b', '비타민 B군'), ('vitamin_c', '비타민 C'), ('vitamin_d', '비타민 D'),
    ('fiber', '식이섬유'), ('zinc', '아연'), ('folate', '엽산'), ('multi_balance', '종합비타민 (균형형)'),
    ('multi_energy', '종합비타민 (피로회복형)'), ('iron', '철'), ('calcium', '칼슘'),
]
BY_LABEL = {label: key for key, label in CATEGORIES}
TARGETS = ['일반', '남성', '여성', '시니어']

# 하루 함량 열 → 상한섭취량 (2025 KDRI 성인). B1·B2는 상한이 없어 합계만 보여 준다
DAILY = {
    '하루 비타민 C(mg)': ('vitamin_c', '비타민 C', 'mg', 2000),
    '하루 비타민 D(μg)': ('vitamin_d', '비타민 D', 'μg', 100),
    '하루 비타민 B1(mg)': ('vitamin_b1', '비타민 B1', 'mg', None),
    '하루 비타민 B2(mg)': ('vitamin_b2', '비타민 B2', 'mg', None),
    '하루 비타민 B6(mg)': ('vitamin_b6', '비타민 B6', 'mg', 50),
    '하루 니아신(mg)': ('niacin', '니아신', 'mg', 35),
    '하루 칼슘(mg)': ('calcium', '칼슘', 'mg', 2000),
    '하루 마그네슘(mg)': ('magnesium', '마그네슘', 'mg', 350),
    '하루 철(mg)': ('iron', '철', 'mg', 45),
    '하루 아연(mg)': ('zinc', '아연', 'mg', 35),
    '하루 엽산(μg)': ('folate', '엽산', 'μg', 1000),
    '하루 비타민 A(μg RAE)': ('vitamin_a', '비타민 A', 'μg RAE', 3000),
    '하루 비타민 E(mg α-TE)': ('vitamin_e', '비타민 E', 'mg α-TE', 540),
    '하루 요오드(μg)': ('iodine', '요오드', 'μg', 2400),
}
UL_MALE = {'calcium': 2500}
# 2025 KDRI 요약표 xix: 19~29세 칼슘 상한은 남성 3,000mg / 여성 2,500mg.
UL_UNDER30 = {'calcium': {'male': 3000, 'female': 2500}}


def text(v):
    return v.replace('\r\n', '\n').strip()


def number(v):
    v = v.strip()
    return None if not v else float(v) if '.' in v else int(v)


def read_rows(source):
    if source.suffix.lower() == '.csv':
        with source.open(encoding='utf-8-sig', newline='') as f:
            return list(csv.DictReader(f))
    # 첨부 엑셀을 수정하지 않고 원문 셀 값만 읽는다. 신고번호를 숫자로 변환하지 않는다.
    ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(source) as z:
        strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            strings = [''.join(t.text or '' for t in si.findall('.//s:t', ns))
                       for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si', ns)]
        rows = []
        for row in ET.fromstring(z.read('xl/worksheets/sheet1.xml')).findall('s:sheetData/s:row', ns):
            values = {}
            for cell in row.findall('s:c', ns):
                column = ''.join(c for c in cell.attrib['r'] if c.isalpha())
                value = cell.findtext('s:v', default='', namespaces=ns)
                if cell.get('t') == 's':
                    value = strings[int(value)]
                elif cell.get('t') == 'inlineStr':
                    value = ''.join(t.text or '' for t in cell.findall('.//s:t', ns))
                values[column] = value
            if any(values.values()):
                rows.append(values)
        headers = rows[0]
        return [{label: row.get(column, '') for column, label in headers.items()} for row in rows[1:]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=SRC, help='준혁님 제품 CSV 또는 엑셀')
    source = parser.parse_args().source.resolve()
    rows = read_rows(source)
    texts, text_id = [], {}

    def tid(s):
        s = text(s)
        if s not in text_id:
            text_id[s] = len(texts)
            texts.append(s)
        return text_id[s]

    products, lists = {}, {k: {t: [] for t in TARGETS} for k, _ in CATEGORIES}
    for r in rows:
        pid = r['품목제조신고번호'].strip()
        assert pid.isdigit(), pid
        daily = {}
        for col, (key, *_rest) in DAILY.items():
            v = number(r.get(col, ''))
            if v is not None:
                daily[key] = v
        p = {
            'name': text(r['제품명']), 'maker': text(r['업체명']), 'form': text(r['제형']),
            'intake': text(r['1일 섭취량']), 'function': tid(r['기능성']), 'caution': tid(r['섭취 시 주의사항']),
            'daily': daily,
            'headroom': text(r.get('상한 여유', '')),
            'halfUlIngredients': text(r.get('상한 50% 이상 성분', '')),
        }
        if pid in products:
            assert products[pid] == p, f'같은 신고번호인데 내용이 달라요: {pid}'
        products[pid] = p
        target = r['대상'].strip()
        assert target in TARGETS, target
        amount = text(r['1일 함량']) or None
        lists[BY_LABEL[r['영양소'].strip()]][target].append(
            (int(r['순서']), [pid, text(r['구분']), amount, number(r['기준치 대비(%)'])]))

    out_lists = {}
    for key, by_target in lists.items():
        out_lists[key] = {}
        for t, items in by_target.items():
            items.sort(key=lambda x: x[0])
            assert [o for o, _ in items] == list(range(1, len(items) + 1)), (key, t)
            if items:
                out_lists[key][t] = [row for _, row in items]

    catalog = {
        'version': 'junhyeok-stage9-2026-11-05',
        'source': source.relative_to(ROOT).as_posix() if source.is_relative_to(ROOT) else source.name,
        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'note': '9단계 통과 후보 전체. 순서는 같은 영양소·대상 안에서 먼저 볼 순서이며 순위가 아니다. 점수·등급·가격·판매처 없음',
        'categories': [{'key': k, 'label': label} for k, label in CATEGORIES],
        'targets': TARGETS,
        'daily': [{'key': k, 'label': label, 'unit': unit, 'ul': ul,
                   **({'ulMale': UL_MALE[k]} if k in UL_MALE else {}),
                   **({'ulUnder30': UL_UNDER30[k]} if k in UL_UNDER30 else {})}
                  for k, label, unit, ul in DAILY.values()],
        'texts': texts,
        'products': products,
        # lists[영양소][대상] = [[신고번호, 구분, 1일 함량, 기준치 대비 %], ...] (순서대로)
        'lists': out_lists,
    }
    OUT.write_text(json.dumps(catalog, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    links = sum(len(v) for t in out_lists.values() for v in t.values())
    print(f'{OUT.name}: 제품 {len(products):,}개, 연결 {links:,}줄, 문구 {len(texts):,}개, {OUT.stat().st_size / 1e6:.2f} MB')


if __name__ == '__main__':
    main()
