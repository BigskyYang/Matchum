"""원본의 '남은 제품' 시트만 JSON으로 변환. 필터링/점수 변경 없음.
실행: python scripts/export_products.py /path/to/생활기능_분류.xlsx
필요 패키지: openpyxl (웹 실행에는 필요 없음)
"""
import collections
import hashlib
import json
from pathlib import Path
import sys
import openpyxl

source = Path(sys.argv[1])
dest = Path(__file__).resolve().parents[1] / 'data'
dest.mkdir(exist_ok=True)
book = openpyxl.load_workbook(source, read_only=True, data_only=True)
sheet = next(s for s in book if s.title.startswith('남은 제품'))
rows = sheet.values
headers = next(rows)
products = []
for row in rows:
    if not any(v is not None for v in row):
        continue
    r = dict(zip(headers, row))
    p = {
        'id': str(r['품목제조신고번호']),
        'ingredient': r['주 성분'], 'name': r['제품명'], 'manufacturer': r['업체명'],
        'reportedDate': str(r['신고일자']), 'pool': r['풀'], 'form': r['제형'],
        'dailyIntakeText': r['1일 섭취량'], 'dailyUnits': r['하루 개수'],
        'dailyMainAmountRaw': r['주성분 하루 함량'],
        # 원본에 단위 열이 없으므로 표시 가능한 단위/환산량을 추정하지 않음.
        'dailyMainAmountUnit': None, 'amountReadMethod': r['읽은 방법'],
        'rawIngredientCount': r['원재료 수'], 'companionCount': r['함께 든 성분 수'],
        'companionIngredients': r['함께 든 가이드 성분'], 'omega3Source': r['오메가3 원료'],
        'sameFormulaCount': r['같은 처방 제품 수'], 'sameFormulaNames': r['같은 처방 제품명'],
        'functionText': r['기능성'], 'cautionText': r['섭취 시 주의사항'],
    }
    for field in ['id', 'ingredient', 'name', 'functionText', 'cautionText']:
        if not p[field]:
            raise ValueError(f'필수값 없음: {field}, {p["id"]}')
    products.append(p)
ids = [p['id'] for p in products]
if len(ids) != len(set(ids)):
    raise ValueError('중복 품목제조신고번호')
counts = dict(collections.Counter(p['ingredient'] for p in products))
metadata = {
    'version': '1.0.0', 'sourceFilename': source.name, 'sourceSheet': sheet.title,
    'sourceSha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'count': len(products), 'byIngredient': counts,
    'filteringChanged': False, 'scoreProvided': False,
    'amountDisplayPolicy': '단위 확인 전 dailyMainAmountRaw를 사용자에게 표시하거나 상한 합산에 사용하지 않음',
}
for name, value in [('products.json', products), ('metadata.json', metadata)]:
    (dest / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(metadata, ensure_ascii=False))
