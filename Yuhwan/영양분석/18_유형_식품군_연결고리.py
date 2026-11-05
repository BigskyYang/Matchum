# %% [markdown]
# # 유형 → 식품군 → 부족 영양소 연결 고리 (전유환, 11/4)
# 목적: "이 유형은 ○○이 부족해요"에 '왜'를 붙인다 — 유형마다 어떤 식품을 덜 먹어서 그 영양소가 부족한지
#   (ADAMS 틀의 Differentiable: 유형마다 부족의 '이유'가 다른가)
# 방법 (결과 보기 전에 확정)
#   1. 유형 × 식품군: 같은 성별·연령대 평균 대비 배수 (간접 표준화, 조사 가중)
#      식품군 = 24시간 회상 육류·생선·유제품·달걀·콩류(g) + 설문 과일·채소(김치 제외) 주당 빈도 + 에너지(kcal)
#   2. 유형 × 영양소 부족: 관측/기대 비를 세 가지 기대값으로
#      E0 = 성별×연령대만 / E1 = + 식품군(위 7개, 로그 변환) / E2 = + 에너지(로그)
#      (로지스틱, 유형은 넣지 않음, 조사 가중, 전체 연도)
#   3. 설명되는 몫 (유형 차이가 클 때만: |O/E0 − 1| ≥ 0.1)
#      식품 선택 몫 = (O/E0 − O/E1) / (O/E0 − 1), 식사량 몫 = (O/E1 − O/E2) / (O/E0 − 1)
#      ※ 11/4 정정: 위 몫은 '식품군 먼저 → 에너지' 순서라 순서에 따라 달라짐 (식품군과 식사량이 많이 겹침)
#        → 4번에서 순서와 상관없는 값도 계산: 에너지만 / 식품군만 / 둘 다 맞췄을 때 각각 줄어드는 몫
#   해석: 인과가 아니라 '부족의 차이가 어떤 식품에서 오는지' 나눠 보는 분석.
#         식품군과 영양소는 같은 하루 기록에서 나와서 독립 검증은 아님 (과일·채소는 설문 빈도라 독립)
#   보고 대상: 팀장님 nbti_12types.json의 유형 고유(specific)·식사량 관련(intake_related) 영양소 = 화면 유형 영역 항목

# %%
import json
import warnings
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from common import *

warnings.filterwarnings('ignore')
REPO = ROOT.parent if (ROOT.parent / 'Jiyeon').exists() else ROOT.parent / 'Matchum'
NB = json.load(open(REPO / 'bigskyyang' / 'analysis' / 'output' / 'nbti_12types.json', encoding='utf-8'))
TYPES = {t['id']: t for t in NB['types']}
FOODS = {'육류': '보조_MEAT_G', '생선': '보조_FISH_G', '유제품': '보조_DAIRY_G', '달걀': '보조_EGG_G', '콩류': '보조_LEGUME_G',
         '과일(빈도)': '과일_주당', '채소(빈도)': '채소_김치제외_주당'}

d = add_status(load_persons(ROOT / 'KMedoids_12Types_N1O3.csv', 'Type'))
d['sa'] = d['sex'] + '_' + d['age_grp'].astype(str)
d['에너지'] = d['영양_N_EN']
ok = d[list(FOODS.values()) + ['에너지']].notna().all(axis=1)
print(f'사람 {len(d)} | 식품군·에너지 결측 제외 {(~ok).sum()}')
d = d[ok].reset_index(drop=True)
w = d['w'].to_numpy()


def ratio(col):
    """유형별 가중 평균 ÷ 같은 성별·연령대 평균으로 기대한 값 (간접 표준화)."""
    sa_mean = d.groupby('sa').apply(lambda g: np.average(g[col], weights=g['w']), include_groups=False)
    exp = d['sa'].map(sa_mean)
    return d.assign(o=d[col] * d['w'], e=exp * d['w']).groupby('cluster').apply(lambda g: g['o'].sum() / g['e'].sum(), include_groups=False)


# %% 1. 유형 × 식품군 배수
FR = pd.DataFrame({k: ratio(c) for k, c in {**FOODS, '에너지': '에너지'}.items()}).reindex(list(TYPES))
FR.index = [f"{k} {TYPES[k]['name']}" for k in FR.index]
print('\n1. 유형별 식품 섭취: 같은 성별·연령대 대비 배수 (1.00 = 평균, 조사 가중)')
print(FR.round(2).to_string())

# %% 2. 유형 × 영양소 부족: 관측/기대 (E0 성별·연령 / E1 + 식품군 / E2 + 에너지)
SA = pd.get_dummies(d['sa'], drop_first=True).astype(float)
FX = np.log1p(d[list(FOODS.values())].clip(lower=0))
EX = np.log(d[['에너지']].clip(lower=100))
designs = {'E0': SA, 'E1': pd.concat([SA, FX], axis=1), 'E2': pd.concat([SA, FX, EX], axis=1), 'En': pd.concat([SA, EX], axis=1)}
rows = []
for n in NUTRIENTS:
    y = d[f'below_{n}'].to_numpy()
    E = {k: LogisticRegression(C=1e4, max_iter=5000).fit(X.to_numpy(), y, sample_weight=w).predict_proba(X.to_numpy())[:, 1]
         for k, X in designs.items()}
    for k in TYPES:
        m = (d['cluster'] == k).to_numpy()
        o = (y[m] * w[m]).sum()
        r = dict(유형=k, 이름=TYPES[k]['name'], 영양소=n, 인원=int(m.sum()), 부족률=o / w[m].sum(),
                 **{f'O/{e}': o / (E[e][m] * w[m]).sum() for e in E})
        gap = r['O/E0'] - 1
        r['식품선택_몫'] = (r['O/E0'] - r['O/E1']) / gap if abs(gap) >= 0.1 else np.nan
        r['식사량_몫'] = (r['O/E1'] - r['O/E2']) / gap if abs(gap) >= 0.1 else np.nan
        r['에너지만_몫'] = (r['O/E0'] - r['O/En']) / gap if abs(gap) >= 0.1 else np.nan
        r['식품군만_몫'] = (r['O/E0'] - r['O/E1']) / gap if abs(gap) >= 0.1 else np.nan
        r['둘다_몫'] = (r['O/E0'] - r['O/E2']) / gap if abs(gap) >= 0.1 else np.nan
        rows.append(r)
T = pd.DataFrame(rows)


def tag(k, n):
    t = TYPES[k]['nutrients']
    return '유형 고유' if n in [x['nutrient'] for x in t['specific']] else '식사량 관련' if n in [x['nutrient'] for x in t['intake_related']] else ''


T['판정'] = [tag(k, n) for k, n in zip(T['유형'], T['영양소'])]
T.to_csv(OUT / '18_유형_식품군_연결고리.csv', index=False, encoding='utf-8-sig')
S = T[T['판정'] != ''].copy()
print('\n2. 화면 유형 영역 항목: 부족 관측/기대 (E0 성별·연령 → E1 + 식품군 → E2 + 에너지)와 설명되는 몫')
print(S[['유형', '이름', '영양소', '판정', '부족률', 'O/E0', 'O/E1', 'O/E2', '식품선택_몫', '식사량_몫']].round(2).to_string(index=False))
print('\n판정별 평균 설명 몫:', S.groupby('판정')[['식품선택_몫', '식사량_몫']].mean().round(2).to_dict('index'))

# %% 3. 유형별 한 줄 이야기 (화면 유형 영역 항목 기준)
FRk = pd.DataFrame({k: ratio(c) for k, c in {**FOODS, '에너지': '에너지'}.items()})
print('\n3. 유형별 한 줄 (식품은 평균보다 15% 이상 적은 것만)')
for k in TYPES:
    low = FRk.loc[k].drop('에너지')
    low = low[low <= 0.85].sort_values()
    s = S[S['유형'] == k].sort_values('O/E0', ascending=False)
    if s.empty:
        continue
    foods = ', '.join(f"{f} {(1 - v) * 100:.0f}%↓" for f, v in low.items()) or '두드러지게 적은 식품군 없음'
    nut = ', '.join(f"{r.영양소} {r._6:.2f}배" for r in s.itertuples())
    expl = '; '.join(f"{r.영양소}: 식품 선택 {r.식품선택_몫:.0%} · 식사량 {r.식사량_몫:.0%}" for r in s.itertuples() if pd.notna(r.식품선택_몫))
    print(f"● {k} {TYPES[k]['name']} | 에너지 {FRk.at[k, '에너지']:.2f}배 | 덜 먹는 식품: {foods}\n   부족(관측/기대): {nut}\n   설명: {expl or '-'}")


# %% 4. 순서와 상관없는 몫 (11/4 정정)
big = T[(T['O/E0'] - 1).abs() >= 0.1]
print(f"\n4. 순서와 상관없는 설명 몫 (유형 차이 10% 이상 {len(big)}칸 평균)")
print(f"   에너지만 맞춤 {big['에너지만_몫'].mean():.0%} | 식품군만 맞춤 {big['식품군만_몫'].mean():.0%} | 둘 다 {big['둘다_몫'].mean():.0%}")
print(f"   겹치지 않는 몫: 식품군 {(big['둘다_몫'] - big['에너지만_몫']).mean():.0%}, 에너지 {(big['둘다_몫'] - big['식품군만_몫']).mean():.0%}")
print(f"   둘 다 맞춘 뒤에도 1.1배 이상 남는 칸 {int((big['O/E2'] >= 1.1).sum())}개 (보고서 '총 섭취량 보정 후 유형 고유 3건'과 같은 방향)")
print(big.groupby('유형')[['에너지만_몫', '식품군만_몫', '둘다_몫']].mean().round(2).to_string())
