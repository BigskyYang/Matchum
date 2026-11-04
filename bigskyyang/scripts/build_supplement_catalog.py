"""
준혁님 최종 제품 후보(9단계 통과 전체)를 웹용 제품 목록으로 바꾼다 → web/src/data/supplementCatalog.json

입력: junhyeok/output/web_products.csv (junhyeok/분류_필터링/전체_실행.py 1~9단계 결과, 정보는 web_products_정보.md)
  한 줄 = 영양소 × 대상 × 제품. '순서'는 같은 영양소·대상 안에서 먼저 볼 순서 (점수·등급은 들어 있지 않다)
연결 규칙: Jaejun/nutrition_product_web_handoff (모델 영양소 → 제품 목록, B1·B2 → 비타민 B군, 대상별로 따로, 순서 그대로)

웹에서 하는 일은 고르기·보여 주기뿐이다. 제품을 더하거나 빼거나 순서를 다시 매기지 않는다.
  - 대상(일반·남성·여성·시니어)은 섞지 않고 목록을 따로 둔다
  - 같은 문구(기능성·주의사항)는 한 번만 저장하고 번호로 가리킨다 (파일 크기를 줄이려고)
  - '하루 ○○' 열은 여러 제품을 함께 고를 때 상한섭취량을 합쳐 보는 데 쓴다

실행 (bigskyyang 폴더에서)
  python scripts/build_supplement_catalog.py
"""

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'junhyeok' / 'output' / 'web_products.csv'
OUT = Path(__file__).resolve().parents[1] / 'web' / 'src' / 'data' / 'supplementCatalog.json'

# 재준님 인계 순서 (productBridge.mjs categories)
CATEGORIES = [
    ('magnesium', '마그네슘'), ('vitamin_b', '비타민 B군'), ('vitamin_c', '비타민 C'), ('vitamin_d', '비타민 D'),
    ('fiber', '식이섬유'), ('zinc', '아연'), ('folate', '엽산'), ('multi_balance', '종합비타민 (균형형)'),
    ('multi_energy', '종합비타민 (피로회복형)'), ('iron', '철'), ('calcium', '칼슘'),
]
BY_LABEL = {label: key for key, label in CATEGORIES}
TARGETS = ['일반', '남성', '여성', '시니어']

# 하루 함량 열 → 상한섭취량 (2025 KDRI 성인, web_products_정보.md). B1·B2는 상한이 없어 합계만 보여 준다
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
}
UL_MALE = {'calcium': 2500}  # 남성은 칼슘 상한이 다르다


def text(v):
    return v.replace('\r\n', '\n').strip()


def number(v):
    v = v.strip()
    return None if not v else float(v) if '.' in v else int(v)


def main():
    rows = list(csv.DictReader(SRC.open(encoding='utf-8-sig', newline='')))
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
            v = number(r[col])
            if v is not None:
                daily[key] = v
        p = {
            'name': text(r['제품명']), 'maker': text(r['업체명']), 'form': text(r['제형']),
            'intake': text(r['1일 섭취량']), 'function': tid(r['기능성']), 'caution': tid(r['섭취 시 주의사항']),
            'daily': daily,
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
        'version': 'junhyeok-stage9-2026-11-04',
        'source': 'junhyeok/output/web_products.csv',
        'source_sha256': hashlib.sha256(SRC.read_bytes()).hexdigest(),
        'note': '9단계 통과 후보 전체. 순서는 같은 영양소·대상 안에서 먼저 볼 순서이며 순위가 아니다. 점수·등급·가격·판매처 없음',
        'categories': [{'key': k, 'label': label} for k, label in CATEGORIES],
        'targets': TARGETS,
        'daily': [{'key': k, 'label': label, 'unit': unit, 'ul': ul, **({'ulMale': UL_MALE[k]} if k in UL_MALE else {})}
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
