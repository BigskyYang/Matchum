"""
유환님 12유형 부족 영양소 결과표를 웹용으로 줄인다 → web/src/data/nutrientCells.json

입력: Yuhwan/영양분석/output/08_유형별_부족영양소_추천.json (08_12유형_부족영양소_추천.py가 만든다)
  유형(N1~O3) × 성별 × 연령대 칸마다 영양소 15개의 부족 비율 p(같은 조건 사람 중 2025 KDRI 기준 미만인 비율, 조사 가중)
출력: 결과 화면 '부족할 수 있는 영양소'가 쓰는 값만 남긴다
  common = 모든 칸에서 '공통주의'인 영양소 (대부분의 사람에게 부족한 8개)
  types[유형][성별 1·2][연령대][영양소 키] = { p, vs, tag }
    p   : 부족 비율 (0~1)
    vs  : 같은 성별·연령대 전체 대비 배수
    tag : 유형특이 · 식사량영향 · 공통주의 · '' (판정 기준은 bigskyyang/analysis/05_jiyeon_improved.py)

유환님 분석이 바뀌면 다시 실행한다 (bigskyyang 폴더에서)
  python scripts/build_nutrient_cells.py
"""

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'Yuhwan' / '영양분석' / 'output' / '08_유형별_부족영양소_추천.json'
OUT = ROOT / 'bigskyyang' / 'web' / 'src' / 'data' / 'nutrientCells.json'

# 유환님 결과표의 영양소 이름 → 웹 키 (src/data/nutrientGuide.js)
KEYS = {
    '단백질': 'protein', '비타민A': 'vitamin_a', '비타민D': 'vitamin_d', '비타민E': 'vitamin_e', '비타민C': 'vitamin_c',
    '티아민': 'vitamin_b1', '리보플라빈': 'vitamin_b2', '엽산': 'folate', '칼슘': 'calcium', '인': 'phosphorus',
    '칼륨': 'potassium', '마그네슘': 'magnesium', '철': 'iron', '아연': 'zinc', '식이섬유': 'fiber',
}
SEX = {'남자': '1', '여자': '2'}   # encode.js extras.sex 값

src = json.loads(SRC.read_text(encoding='utf-8'))
cells = [rows for t in src['types'].values() for ages in t['cells'].values() for rows in ages.values()]
commons = {frozenset(KEYS[r['nutrient']] for r in rows if r['tag'] == '공통주의') for rows in cells}
assert len(commons) == 1, '칸마다 공통주의 영양소가 다르다'
out = {
    'generated': date.today().isoformat(),
    'source': 'Yuhwan/영양분석/output/08_유형별_부족영양소_추천.json',
    'version': src['version'],
    'source_types': src['source_types'],
    'note': src['설명'],
    'common': sorted(next(iter(commons))),
    'types': {
        tid: {
            SEX[sex]: {
                age: {KEYS[r['nutrient']]: {'p': r['p'], 'vs': r['vs_same_sex_age'], 'tag': r['tag']} for r in rows}
                for age, rows in ages.items()
            }
            for sex, ages in t['cells'].items()
        }
        for tid, t in src['types'].items()
    },
}
OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
print(f'{len(out["types"])}개 유형 → {OUT} ({OUT.stat().st_size / 1024:.0f}KB)')
