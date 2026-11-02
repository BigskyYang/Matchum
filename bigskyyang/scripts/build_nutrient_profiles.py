"""
유형별 영양소 결과표(web/src/data/nutrientProfiles.json)를 만든다.

웹은 사용자의 유형만 판정하고, 영양소 결과는 이 표에서 그 유형의 값을 찾아 보여준다.
(앱에서 영양 모델을 돌리지 않는다)

입력
  --nutrients  개인별 영양소 값 CSV. ID, year 열 + 영양소별 열
               · 예측확률을 쓰려면 열 이름을 '<영양소키>_prob' (예: calcium_prob)
               · 실제 부족 여부(0/1)를 쓰려면 Jaejun/config/targets.json의 target 열 이름 (예: Calcium_mg_below_EAR)
               둘 다 있으면 예측확률을 쓴다.
  --clusters   군집 결과 엑셀 (기본: Jiyeon/KMeans_Final_MicroClustered.xlsx). ID, year로 위 CSV와 합친다.
  --model      웹 군집 모델 (기본: web/src/data/model.json). 군집 번호 → 유형 ID 변환에 쓴다.
               반드시 같은 엑셀로 export_model.py를 먼저 돌린 뒤 실행할 것.

계산
  유형(대분류 Group_0~3, 세부 유형 20개)마다 영양소별 평균(= 부족·과잉 위험 비율)을 구하고,
  Jaejun/config/risk_thresholds.json의 기준으로 Low / Mid / High를 붙인다.
  결과표의 키는 군집 번호가 아니라 model.json의 유형 ID(typeIds)다.
  가중치를 적용하지 않은 표본 평균이므로 국민 전체 비율로 해석하지 않는다.

사용법 (bigskyyang 폴더에서)
  python scripts/build_nutrient_profiles.py --nutrients <개인별 영양소 CSV>
"""

import argparse
import json
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
TARGETS = json.loads((ROOT / 'Jaejun' / 'config' / 'targets.json').read_text(encoding='utf-8'))
THRESHOLDS = json.loads((ROOT / 'Jaejun' / 'config' / 'risk_thresholds.json').read_text(encoding='utf-8'))


def band(nutrient, rate):
    cut = THRESHOLDS[nutrient]
    if rate < cut['low_mid']:
        return 'Low'
    return 'Mid' if rate < cut['mid_high'] else 'High'


def summarize(frame, columns):
    return {
        'n': int(len(frame)),
        'nutrients': {
            key: {'rate': round(float(frame[col].mean()), 4), 'band': band(key, frame[col].mean())}
            for key, col in columns.items()
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--nutrients', required=True)
    ap.add_argument('--clusters', default=str(ROOT / 'Jiyeon' / 'KMeans_Final_MicroClustered.xlsx'))
    ap.add_argument('--model', default=str(ROOT / 'bigskyyang' / 'web' / 'src' / 'data' / 'model.json'))
    ap.add_argument('--out', default=str(ROOT / 'bigskyyang' / 'web' / 'src' / 'data' / 'nutrientProfiles.json'))
    args = ap.parse_args()
    model = json.loads(Path(args.model).read_text(encoding='utf-8'))
    type_ids = model['typeIds']

    nut = pd.read_csv(args.nutrients)
    columns, measure = {}, set()
    for key, target in TARGETS.items():
        if f'{key}_prob' in nut.columns:
            columns[key] = f'{key}_prob'
            measure.add('probability')
        elif target in nut.columns:
            columns[key] = target
            measure.add('observed')
    missing = [k for k in TARGETS if k not in columns]
    if missing:
        print(f'경고: 값이 없는 영양소는 빠집니다 → {missing}')

    clusters = pd.read_excel(args.clusters, usecols=['ID', 'year', 'Main_Cluster', 'Micro_Cluster'])
    df = clusters.merge(nut[['ID', 'year', *columns.values()]], on=['ID', 'year'], how='inner')
    print(f'합친 대상자: {len(df):,}명 (군집 {len(clusters):,}명 중)')
    if df.empty:
        raise SystemExit('ID·year가 겹치는 대상자가 없습니다.')

    df['main'] = 'Group_' + df['Main_Cluster'].astype(str)
    labels = set(df['main']) | set(df['Micro_Cluster'])
    unknown = sorted(labels - set(type_ids))
    if unknown:
        raise SystemExit(f'model.json에 없는 군집 번호가 있습니다 {unknown}. 같은 엑셀로 export_model.py를 먼저 실행하세요.')
    types = {}
    for label, g in df.groupby('main'):
        types[type_ids[label]] = summarize(g, columns)
    for label, g in df.groupby('Micro_Cluster'):
        types[type_ids[label]] = summarize(g, columns)

    out = {
        'generated': date.today().isoformat(),
        'source': Path(args.nutrients).name,
        'measure': '+'.join(sorted(measure)),
        'all': summarize(df, columns),
        'types': types,
    }
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'저장: {args.out} (유형 {len(types)}개, 영양소 {len(columns)}개)')


if __name__ == '__main__':
    main()
