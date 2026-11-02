# %% [markdown]
# # [D] 고객 군집 × 제품 추천 (3개 장르)
# 입력: 영양분석/output/군집별_추천영양소조합.csv, 군집_요약.csv  +  제품분석/output/product_types.csv
# 출력: output/추천_군집별.csv, output/recommendations.json (웹용, 군집 ID 키)
#
# 필요 영양소 가중치: 유형특이(+흡수 짝) = 1.0, 한국 성인 공통 주의 = 0.5
# 커버율: 정량 성분 = min(1일 기준치%/100, 1) / 함량 미상(이름 판별) = 0.3
#         (0.3 근거: 고시형 기능성은 1일 섭취량이 기준치 30% 이상이어야 표시 가능 → 최소 보장치로 가정)
# 장르
#   품질형  : 핵심 영양소(유형특이 상위 2개, 없으면 공통주의 상위 2개)를 '실제 함량'으로 기준치 30% 이상·UL 이하로 채우는 제품
#             점수 = 핵심 커버율 합 + 0.3 × 전체 가중 커버율 - 0.05 × 필요 없는 성분 수  (올인원형과 구분되도록 핵심에 집중)
#   올인원형: 필요 영양소를 몇 개 덮는지(가중 개수), 동점이면 커버율
#   가성비형: price_per_day 열이 있으면 커버율/1일 가격. 없으면 '간편형' = 커버율/1일 복용 개수 (가격 확보 전 임시)
# 안전 필터: UL 초과·단위오류 의심 제외 / 흡연율 ≥ 50% 군집은 베타카로틴 함유 제외 / 인·칼륨은 대상 아님
# 다양성: 장르 안 3개는 제조사가 모두 다르게
# 기능성 원료(오메가3·유산균·루테인·밀크씨슬·비타민K)는 섭취 데이터가 없어 순위 없이 '참고'로만

# %%
from pathlib import Path
import json
import re
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '제품분석' / 'output'
NOUT = ROOT / '영양분석' / 'output'

combo = pd.read_csv(NOUT / '군집별_추천영양소조합.csv', encoding='utf-8-sig', index_col=0)
need = pd.read_csv(NOUT / '군집별_영양니즈_long.csv', encoding='utf-8-sig')
prof = pd.read_csv(NOUT / '군집_요약.csv', encoding='utf-8-sig', index_col=0)
p = pd.read_csv(OUT / 'product_types.csv', encoding='utf-8-sig')

# 분석용 이름 → 제품 피처 열
COLMAP = {'단백질': '단백질', '비타민A': '비타민 A', '비타민D': '비타민 D', '비타민E': '비타민 E', '비타민C': '비타민 C',
          '티아민': '티아민', '리보플라빈': '리보플라빈', '엽산': '엽산', '칼슘': '칼슘', '마그네슘': '마그네슘',
          '철': '철', '아연': '아연', '식이섬유': '식이섬유'}
QUANT = {'단백질', '식이섬유', '칼슘', '철', '비타민 A', '비타민 D', '비타민 C', '티아민', '리보플라빈', '니아신'}
V = [c for c in p.columns if c.startswith('v_')]
FOOD_ONLY = {'인', '칼륨'}
COMMON = [n for n in need.drop_duplicates('영양소').query('전체미달률 >= 0.5')['영양소'] if n not in FOOD_ONLY]
REFERENCE = ['오메가3', '유산균', '루테인', '밀크씨슬', '비타민 K']


def coverage(col):
    v = p[f'v_{col}'].astype(float)
    return np.minimum(v / 100, 1) if col in QUANT else v * 0.3


def targets(c):
    s = combo.loc[c, '유형특이조합']
    spec = [] if s.startswith('(') else [x.strip() for x in s.split('+')]
    w = {COLMAP[n]: 1.0 for n in spec if n in COLMAP}
    for n in COMMON:
        w.setdefault(COLMAP[n], 0.5)
    return w, spec


def norm_name(s):
    return re.sub(r'[\(\[].*?[\)\]]|\d+\s*(정|캡슐|포|ml|mg|g|개|병)|\s', '', str(s))[:12]


def pick(df, score, n=3):
    df = df.assign(score=score).sort_values('score', ascending=False)
    out, seen_m, seen_n = [], set(), set()
    for _, r in df.iterrows():
        if r['score'] <= 0 or r['제조사명'] in seen_m or norm_name(r['식품명']) in seen_n:
            continue
        out.append(r); seen_m.add(r['제조사명']); seen_n.add(norm_name(r['식품명']))
        if len(out) == n:
            break
    return pd.DataFrame(out)


has_price = 'price_per_day' in p.columns
rows, web = [], {}
for c in combo.index:
    w, spec = targets(c)
    cols = list(w)
    cov = pd.DataFrame({k: coverage(k) for k in cols})
    wcov = sum(cov[k] * w[k] for k in cols) / sum(w.values())
    covered = sum((cov[k] >= 0.3) * w[k] for k in cols)
    spec_cols = [COLMAP[n] for n in spec if n in COLMAP]
    hit_spec = (cov[spec_cols] > 0).any(axis=1) if spec_cols else (cov > 0).any(axis=1)

    ok = (p['UL초과'] == 0) & hit_spec
    if prof.loc[c, '흡연율'] >= 0.5:
        ok &= p['베타카로틴함유'] == 0
    extra = (p[V] > 0).sum(axis=1) - (cov > 0).sum(axis=1)       # 필요 없는 성분 수
    # 품질형: 덮는 필요 성분이 전부 '정량'으로 기준치 30% 이상
    quant_hit = [k for k in cols if k in QUANT]
    adequate = pd.Series(True, index=p.index)
    for k in quant_hit:
        adequate &= ~((p[f'v_{k}'] > 0) & (p[f'v_{k}'] < 30))
    q_ok = ok & adequate & (cov[[k for k in cols if k in QUANT]].sum(axis=1) > 0)

    core = (spec_cols or [COLMAP[n] for n in COMMON])[:2]
    core_cov = cov[core].sum(axis=1)
    genres = {
        '품질형': pick(p[q_ok & (core_cov > 0)], (core_cov + 0.3 * wcov - 0.05 * extra)[q_ok & (core_cov > 0)]),
        '올인원형': pick(p[ok], (covered + 0.01 * wcov)[ok]),
    }
    if has_price:
        genres['가성비형'] = pick(p[ok], (wcov / p['price_per_day'])[ok])
    else:
        genres['간편형(가격 확보 전 임시)'] = pick(p[ok & p['1일개수'].between(1, 4)], (wcov / p['1일개수'].clip(lower=1))[ok])

    web[c] = {'유형특이': spec, '공통주의': COMMON, '원인': combo.loc[c, '원인'] if pd.notna(combo.loc[c, '원인']) else '',
              '같이복용': combo.loc[c, '같이'] if pd.notna(combo.loc[c, '같이']) else '',
              '따로복용': combo.loc[c, '따로'] if pd.notna(combo.loc[c, '따로']) else '',
              '식품으로만': combo.loc[c, '식품으로만'] if pd.notna(combo.loc[c, '식품으로만']) else '',
              '참고정보(순위없음)': REFERENCE, '장르': {}}
    for g, df in genres.items():
        web[c]['장르'][g] = []
        for _, r in df.iterrows():
            covers = [k for k in cols if cov.loc[r.name, k] >= 0.3]
            item = dict(식품명=r['식품명'], 제조사=r['제조사명'], 제품유형=r['제품유형명'], 덮는영양소=covers,
                        가중커버율=round(float(wcov[r.name]), 3), 일개수=r['1일개수'],
                        표시형태=[f for f in ['D3', 'rTG', '리포좀', '활성엽산'] if r.get(f'form_{f}', 0) == 1])
            web[c]['장르'][g].append(item)
            rows.append(dict(cluster=c, 장르=g, **{k: v for k, v in item.items() if k != '표시형태'}))

rec = pd.DataFrame(rows)
rec.to_csv(OUT / '추천_군집별.csv', index=False, encoding='utf-8-sig')
(OUT / 'recommendations.json').write_text(json.dumps(web, ensure_ascii=False, indent=1, default=str), encoding='utf-8')

# 군집 니즈 ↔ 제품 유형 매칭 (코사인): 어떤 제품 유형이 이 군집에 맞는지
Xv = p[V].astype(float).copy()
qcols = [f'v_{q}' for q in QUANT]
kind = p['군집변환'].iat[0]                             # 03에서 선택된 변환과 같은 스케일
Xv[qcols] = np.log1p(Xv[qcols] / 100) if kind == 'log' else np.minimum(Xv[qcols], 300 if kind == 'cap300' else 100) / 100
cent = Xv.groupby(p['제품유형명']).mean()
match = {}
for c in combo.index:
    w, _ = targets(c)
    vec = np.array([w.get(col[2:], 0) for col in V])
    sim = cent.values @ vec / (np.linalg.norm(cent.values, axis=1) * np.linalg.norm(vec) + 1e-9)
    match[c] = ', '.join(f'{n}({s:.2f})' for n, s in sorted(zip(cent.index, sim), key=lambda x: -x[1])[:3])
pd.Series(match, name='맞는 제품유형 top3').to_csv(OUT / '군집x제품유형_매칭.csv', encoding='utf-8-sig')

pd.set_option('display.width', 250); pd.set_option('display.max_colwidth', 60)
print('공통 주의:', COMMON, '| 가격 열:', has_price)
print(pd.Series(match).to_string())
for c in combo.index[:3]:
    print(f'\n### {c} 유형특이={web[c]["유형특이"]}')
    print(rec[rec.cluster == c][['장르', '식품명', '제품유형', '덮는영양소', '가중커버율', '일개수']].to_string(index=False))
