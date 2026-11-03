"""1단계: 대상자 선정 + 웹 설문 값으로 변환 + 영양소 부족 판정 → data/persons.csv (사람 단위, git 제외)

출력: output/01_대상자.md (선정 단계별 인원, 변수 대응 확인 결과)
"""
import numpy as np
import pandas as pd

from common import DATA, FEATURE_NAMES, LABEL_KO, ML_COLUMNS, NUTRIENTS, OUT, REPO, add_nutrient_status, encode_knhanes, load_raw

raw = load_raw()
enc = encode_knhanes(raw)
keep = ['ID', 'sex', 'age', 'wt_tot', 'psu', 'kstrata'] + [c for c in raw.columns if c.startswith('N_')]
d = enc.merge(raw[keep], on='ID')

flow = [('2022–2024 전체 조사 대상', len(d))]
d = d[d['age'] >= 19]
flow.append(('만 19세 이상', len(d)))
miss = d[FEATURE_NAMES].isna()
lines_missing = [f'| {LABEL_KO[f]} | {int(miss[f].sum()):,} |' for f in FEATURE_NAMES if miss[f].sum()]
d = d[~miss.any(axis=1)]
flow.append(('생활습관 15개 변수 응답 완료', len(d)))
has_diet = d['N_EN'].notna()
flow.append(('그중 24시간 회상(영양소 섭취량) 있음 → 영양 결과 검증에 사용', int(has_diet.sum())))

d = add_nutrient_status(d)
d.to_csv(DATA / 'persons.csv', index=False, encoding='utf-8-sig')

# ── 지연님 COMPLETECASE CSV와 같은 규칙인지 확인 (같은 ID, 같은 값) ──
cc_path = REPO / 'Jiyeon' / 'KNHANES_2022_2024_ML_CLUSTER_COMPLETECASE.csv'
check = []
if cc_path.exists():
    cc = pd.read_csv(cc_path, encoding='utf-8-sig')
    m = cc.merge(d, on='ID', how='inner')
    check.append(f'- 지연님 CSV {len(cc):,}명 중 이번 대상자에 포함: {len(m):,}명')
    for f, ml in ML_COLUMNS.items():
        same = np.isclose(m[f].to_numpy(float), m[ml].to_numpy(float), atol=1e-6)
        check.append(f'  - {LABEL_KO[f]}: 일치 {same.mean():.1%}' + ('' if same.all() else f' (다른 {int((~same).sum())}명)'))
    only_here = len(d) - len(m)
    check.append(f'- 이번 대상자에만 있는 사람: {only_here:,}명 (과일·채소 외 변수 기준이 같으면 0에 가까워야 함)')

years = d.groupby('year').size()
sleep_year = d.groupby('year')['sleep_hours'].agg(['mean', 'std']).round(2)

md = ['# 1단계: 대상자와 변수', '', '## 대상자 선정', '', '| 단계 | 인원 |', '|---|---:|']
md += [f'| {s} | {n:,} |' for s, n in flow]
md += ['', '연도별: ' + ', '.join(f'{y}년 {n:,}명' for y, n in years.items()), '']
md += ['### 결측으로 빠진 인원 (변수별, 중복 포함)', '', '| 변수 | 결측 |', '|---|---:|'] + lines_missing
md += ['', '## 지연님 데이터와 변환 규칙 비교', ''] + check
md += ['', '## 연도별 수면 시간 (측정 방식 차이)', '',
       '2022·2023년은 수면 시간을 정수 시간으로 직접 물었고, 2024년은 취침·기상 시각으로 물었다 (웹과 같은 방식).', '',
       '| 연도 | 평균 | 표준편차 |', '|---|---:|---:|']
md += [f'| {y} | {r["mean"]} | {r["std"]} |' for y, r in sleep_year.iterrows()]
md += ['', '→ 수면은 연도별로 표준화하고, 웹 사용자는 2024년 기준으로 변환한다.', '',
       '## 영양소 부족 비율 (가중치 없음, 24시간 회상 있는 사람)', '', '| 영양소 | 부족 비율 |', '|---|---:|']
md += [f'| {n} | {d[f"below_{n}"].mean():.1%} |' for n in NUTRIENTS]
(OUT / '01_대상자.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
print('\n'.join(md))
