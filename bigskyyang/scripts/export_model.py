"""
군집화 결과 엑셀(Jiyeon/KMeans_Final_MicroClustered.xlsx)을 읽어 웹에서 쓸 모델 파일(model.json)을 만든다.

three_clustering.py는 학습된 스케일러·군집 중심을 저장하지 않으므로, 엑셀의 라벨을 기준으로 다시 계산한다.
  1단계: 전체 데이터 StandardScaler → Main_Cluster 중심
  2단계: 대분류별 StandardScaler → Sub_Cluster 중심
  3단계: 마이크로 분할된 소분류별 StandardScaler → Micro_Cluster 중심
K-Means의 중심은 소속 데이터의 평균이므로, 웹에서 '가장 가까운 중심'을 고르면 같은 라벨이 나온다.
마지막에 학습 데이터 전체를 같은 방식으로 다시 분류해 엑셀 라벨과 일치율을 출력한다.

유형 ID (typeIds)
  K-Means는 다시 돌릴 때마다 군집 번호가 바뀔 수 있다 (예: 이전 Group_1이 새로 돌리면 Group_3).
  그래서 이전 model.json의 유형별 평균과 비교해 가장 비슷한 유형끼리 짝짓고, 이전 유형 ID를 물려준다.
  웹의 유형 이름(types.js)과 영양소 결과표(nutrientProfiles.json)는 군집 번호가 아니라 이 ID를 쓴다.
  처음 내보낼 때는 ID = 군집 번호이고, 이후에는 군집 번호가 바뀌어도 같은 유형은 같은 ID를 유지한다.

사용법 (bigskyyang 폴더에서):
  python scripts/export_model.py [엑셀 경로] [출력 경로] [--reset-ids]
  --reset-ids  이전 ID를 무시하고 ID = 현재 군집 번호로 새로 시작 (types.js도 새로 맞춰야 함)
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

ROOT = Path(__file__).resolve().parents[2]
ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
RESET_IDS = '--reset-ids' in sys.argv
XLSX = Path(ARGS[0]) if len(ARGS) > 0 else ROOT / 'Jiyeon' / 'KMeans_Final_MicroClustered.xlsx'
OUT = Path(ARGS[1]) if len(ARGS) > 1 else ROOT / 'bigskyyang' / 'web' / 'src' / 'data' / 'model.json'
# 유형 평균 차이가 이보다 크면(표준편차 단위 RMS) '많이 달라진 유형'으로 알린다
CHANGED_WARN = 0.5

df = pd.read_excel(XLSX)
FEATURES = [c for c in df.columns if c.startswith('ML_')]
X = df[FEATURES].astype(float)


def scaler(frame):
    # sklearn StandardScaler와 같은 모집단 표준편차(ddof=0). 분산이 0이면 1로 둔다(sklearn과 동일)
    mean = frame.mean()
    std = frame.std(ddof=0).replace(0, 1.0)
    return mean, std


def node(frame, labels):
    mean, std = scaler(frame)
    scaled = (frame - mean) / std
    centers = scaled.groupby(labels).mean()
    return {
        'mean': mean.round(6).tolist(),
        'std': std.round(6).tolist(),
        'centers': {str(k): v.round(6).tolist() for k, v in centers.iterrows()},
    }


def profile(frame):
    return {'n': int(len(frame)), 'mean': frame.mean().round(4).tolist()}


model = {
    'features': FEATURES,
    'source': XLSX.name,
    'root': node(X, df['Main_Cluster'].map(lambda m: f'Group_{m}')),
    'children': {},
    'profiles': {'all': profile(X)},
}

for main, g in df.groupby('Main_Cluster'):
    main_label = f'Group_{main}'
    model['children'][main_label] = node(X.loc[g.index], g['Sub_Cluster'])
    model['profiles'][main_label] = profile(X.loc[g.index])
    for sub, s in g.groupby('Sub_Cluster'):
        model['profiles'][sub] = profile(X.loc[s.index])
        if (s['Micro_Cluster'] != sub).any():  # 3단계 마이크로 분할된 소분류
            model['children'][sub] = node(X.loc[s.index], s['Micro_Cluster'])
            for micro, m in s.groupby('Micro_Cluster'):
                model['profiles'][micro] = profile(X.loc[m.index])


def predict(row):
    # 웹(src/lib/classify.js)과 같은 계산: 단계마다 해당 스케일러로 변환 후 가장 가까운 중심 선택
    label, path = 'root', []
    while True:
        n = model['root'] if label == 'root' else model['children'].get(label)
        if n is None:
            return path
        z = (row - np.array(n['mean'])) / np.array(n['std'])
        names = list(n['centers'])
        dist = [((z - np.array(n['centers'][k])) ** 2).sum() for k in names]
        label = names[int(np.argmin(dist))]
        path.append(label)


# 최종 유형(더 쪼개지지 않는 소분류·마이크로 군집) 목록
model['leaves'] = sorted(k for k in model['profiles'] if '-' in k and k not in model['children'])


# ── 유형 ID 물려주기 ──
def main_labels(m):
    return list(m['root']['centers'])


def leaves_of(m, main):
    return [leaf for leaf in m['leaves'] if leaf == main or leaf.startswith(main + '-')]


def match(new_labels, old_labels, old_model):
    # 유형별 평균의 차이(전체 표준편차 단위 RMS)가 가장 작아지도록 1:1로 짝짓는다
    std = np.array(model['root']['std'])
    cost = np.array(
        [
            [np.sqrt(np.mean(((np.array(model['profiles'][a]['mean']) - np.array(old_model['profiles'][b]['mean'])) / std) ** 2)) for b in old_labels]
            for a in new_labels
        ]
    ).reshape(len(new_labels), len(old_labels))
    pairs = {}
    if cost.size:
        for i, j in zip(*linear_sum_assignment(cost)):
            pairs[new_labels[i]] = (old_labels[j], float(cost[i, j]))
    return pairs


prev = None
if OUT.exists() and not RESET_IDS:
    prev = json.loads(OUT.read_text(encoding='utf-8'))
    if prev.get('features') != FEATURES:
        print('알림: 이전 모델과 변수 구성이 달라 유형 ID를 새로 시작합니다.')
        prev = None

type_ids, report = {}, []
if prev is None:
    type_ids = {label: label for label in main_labels(model) + model['leaves']}
else:
    prev_ids = prev.get('typeIds') or {label: label for label in main_labels(prev) + prev['leaves']}
    used = set()

    def give(new, old, dist):
        if old is None:
            type_ids[new] = f'new-{new}'
            report.append(f'  새 유형 {new} → ID {type_ids[new]} (types.js에 내용 추가 필요)')
            return
        type_ids[new] = prev_ids[old]
        used.add(old)
        if new != old or dist > CHANGED_WARN:
            note = ' ※ 많이 달라짐: 이름·설명 확인 필요' if dist > CHANGED_WARN else ''
            report.append(f'  {new} ← 이전 {old} (ID {type_ids[new]}, 차이 {dist:.2f}){note}')

    for new_main in main_labels(model):
        old_main, dist = match(main_labels(model), main_labels(prev), prev).get(new_main, (None, 0))
        give(new_main, old_main, dist)
        old_leaves = leaves_of(prev, old_main) if old_main else []
        leaf_pairs = match(leaves_of(model, new_main), old_leaves, prev)
        for leaf in leaves_of(model, new_main):
            give(leaf, *leaf_pairs.get(leaf, (None, 0)))
    gone = [prev_ids[o] for o in main_labels(prev) + prev['leaves'] if o not in used]
    if gone:
        report.append(f'  사라진 유형 ID: {gone} (types.js에서 정리 필요)')

model['typeIds'] = type_ids
if prev is None:
    print('유형 ID: 현재 군집 번호로 새로 시작' + (' (--reset-ids)' if RESET_IDS else ''))
elif report:
    print('유형 ID: 군집 번호가 바뀐 유형이 있어 이전 ID를 물려줍니다')
    print('\n'.join(report))
else:
    print('유형 ID: 이전과 같음')

pred = [predict(r) for r in X.to_numpy()]
for level, col in enumerate(['Main_Cluster', 'Sub_Cluster', 'Micro_Cluster']):
    truth = df[col].map(lambda m: f'Group_{m}') if col == 'Main_Cluster' else df[col]
    got = [p[min(level, len(p) - 1)] for p in pred]
    print(f'{col}: 일치율 {np.mean(np.array(got) == truth.to_numpy()):.4%}')

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(model, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
print(f'저장: {OUT} ({OUT.stat().st_size / 1024:.1f} KB), 최종 유형 {len(model["leaves"])}개')
