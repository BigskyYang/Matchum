"""
군집화 결과 엑셀(Jiyeon/KMeans_Final_MicroClustered.xlsx)을 읽어 웹에서 쓸 모델 파일(model.json)을 만든다.

three_clustering.py는 학습된 스케일러·군집 중심을 저장하지 않으므로, 엑셀의 라벨을 기준으로 다시 계산한다.
  1단계: 전체 데이터 StandardScaler → Main_Cluster 중심
  2단계: 대분류별 StandardScaler → Sub_Cluster 중심
  3단계: 마이크로 분할된 소분류별 StandardScaler → Micro_Cluster 중심
K-Means의 중심은 소속 데이터의 평균이므로, 웹에서 '가장 가까운 중심'을 고르면 같은 라벨이 나온다.
마지막에 학습 데이터 전체를 같은 방식으로 다시 분류해 엑셀 라벨과 일치율을 출력한다.

사용법 (bigskyyang 폴더에서):
  python scripts/export_model.py [엑셀 경로] [출력 경로]
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
XLSX = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'Jiyeon' / 'KMeans_Final_MicroClustered.xlsx'
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / 'bigskyyang' / 'web' / 'src' / 'data' / 'model.json'

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

pred = [predict(r) for r in X.to_numpy()]
for level, col in enumerate(['Main_Cluster', 'Sub_Cluster', 'Micro_Cluster']):
    truth = df[col].map(lambda m: f'Group_{m}') if col == 'Main_Cluster' else df[col]
    got = [p[min(level, len(p) - 1)] for p in pred]
    print(f'{col}: 일치율 {np.mean(np.array(got) == truth.to_numpy()):.4%}')

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(model, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
print(f'저장: {OUT} ({OUT.stat().st_size / 1024:.1f} KB), 최종 유형 {len(model["leaves"])}개')
