"""
유환님 유형 화면 (나)안 결과를 웹용으로 줄인다 → web/src/data/nutrientCells.json

입력: analysis/02_type_nutrition/영양분석/output/13_유형화면_나안.json (13_유형화면_나안.py가 만든다, 팀 결정 (나)안)
  유형(N1~O3) × 성별 × 연령대 칸마다
    line1: 대부분의 사람에게 부족한 공통 영양소 8개
    line2: 그 밖에 '내 유형에서 살펴볼 것' (부족 비율 ≥ 0.5 또는 같은 성별·나이 대비 1.2배 이상 그리고 ≥ 0.3)
  어떤 영양소를 고를지는 유환님 코드가 정한다. 웹은 그 결과를 그대로 보여 준다.
출력: 결과 화면이 쓰는 값만 남긴다 (영양소 이름·역할·음식은 web/src/data/nutrientGuide.js)
  types[유형][성별 1·2][연령대] = { line1: [{ key, of10 }], line2: [{ key, of10, peerOf10, tag, text }] }
    of10     : 같은 유형·성별·연령대 10명 중 기준보다 적게 먹는 사람 수
    peerOf10 : 같은 성별·연령대 전체 10명 중 몇 명
    tag      : 유형특이 · 식사량영향 · 흔함 (흔함 = 유형이 아니라 성별·나이 때문에 흔한 것, 화면에서 따로 묶는다)
    text     : 판정 문구 (이 유형에서 특히 많아요 / 식사량 점검이 먼저예요 / 같은 성별·나이대에서 흔해요)

유환님 분석이 바뀌면 다시 실행한다 (저장소 루트에서)
  python scripts/build_nutrient_cells.py
"""

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'analysis' / '02_type_nutrition' / '영양분석' / 'output' / '13_유형화면_나안.json'
OUT = ROOT / 'web' / 'src' / 'data' / 'nutrientCells.json'

# 유환님 결과표의 영양소 이름 → 웹 키 (src/data/nutrientGuide.js)
KEYS = {
    '단백질': 'protein', '비타민A': 'vitamin_a', '비타민D': 'vitamin_d', '비타민E': 'vitamin_e', '비타민C': 'vitamin_c',
    '티아민': 'vitamin_b1', '리보플라빈': 'vitamin_b2', '엽산': 'folate', '칼슘': 'calcium', '인': 'phosphorus',
    '칼륨': 'potassium', '마그네슘': 'magnesium', '철': 'iron', '아연': 'zinc', '식이섬유': 'fiber',
}
SEX = {'남자': '1', '여자': '2'}   # encode.js extras.sex 값

src = json.loads(SRC.read_text(encoding='utf-8'))
out = {
    'generated': date.today().isoformat(),
    'source': 'analysis/02_type_nutrition/영양분석/output/13_유형화면_나안.json',
    'version': src['version'],
    'source_types': src['source_types'],
    'rule': src['규칙'],
    'note': src['설명'],
    'empty_line2_text': src['empty_line2_text'],
    'types': {
        tid: {
            SEX[sex]: {
                age: {
                    'line1': [{'key': KEYS[r['nutrient']], 'of10': r['of10']} for r in cell['line1']],
                    'line2': [{'key': KEYS[r['nutrient']], 'of10': r['of10'], 'peerOf10': r['same_sex_age_of10'],
                               'tag': r['tag'], 'text': r['tag_text']} for r in cell['line2']],
                }
                for age, cell in ages.items()
            }
            for sex, ages in t['cells'].items()
        }
        for tid, t in src['types'].items()
    },
}
OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
print(f'{len(out["types"])}개 유형 → {OUT} ({OUT.stat().st_size / 1024:.0f}KB)')
