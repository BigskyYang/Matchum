# %% [markdown]
# # 유형 화면 보강 (전유환, 11/5): ① 내 유형이 비교적 덜 부족한 영양소 ② 유형별 음식 한 줄
# 왜: 웹 유형 화면의 '내 유형이 특히 챙길 영양소'가 120칸 중 103칸에서 비어, 대부분 사람에게 유형과 상관있는 영양 안내가 없음
#
# ① '비교적 덜 부족한 영양소' 규칙 (결과 보기 전에 고정, 13번 (나)안을 거꾸로 적용)
#    - 같은 성별·나이 대비 배수 ≤ 1/1.2 (= 0.833)
#    - 제외: 비타민 D·E·칼륨 (민감도에서 유형 신호가 뒤집혀 공통 안내만, 08·09번), 이미 2줄에 들어간 영양소
#    - 문구: "같은 성별·나이보다 덜 부족한 편이에요" — 충분하다는 뜻이 아님 (공통 영양소는 여전히 1줄에 표시)
#    검증 (13번과 같은 시간 분할): 2022–23 학습 모델로 항목을 고르고, 2024년 관측/기대(O/E)가 1보다 작은지
#      + 2024년 안에서 같은 성별·연령대 안 유형 라벨을 섞었을 때(200회)와 비교
# ② 유형별 음식 한 줄: 18번 식품군 배수(같은 성별·연령대 대비, 조사 가중)
#    - 덜 먹는 식품: 배수 ≤ 0.85 / 더 먹는 식품: 배수 ≥ 1.15 (18번 3절과 같은 15% 기준)
#    - 안정성: 2022–23과 2024를 따로 계산해 방향(1보다 크고 작음)과 15% 기준 통과가 같은지
#    해석: 같은 하루 기록의 식품군(육류·생선·유제품·달걀·콩류)은 영양소와 독립이 아님. 과일·채소는 설문 빈도라 독립.
#          인과가 아니라 "이 유형은 이런 음식을 덜 먹는 편" 이라는 서술

# %%
import json
import warnings
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from common import *

warnings.filterwarnings('ignore')
SEED = 42
P_MAIN, RATIO_CUT, P_FLOOR = 0.5, 1.2, 0.3          # 13번 2줄 규칙 그대로
LOW_CUT = 1 / RATIO_CUT                               # ① 덜 부족 기준
WEAK = ['비타민D', '비타민E', '칼륨']                  # 유형 신호 없음 (08·09번)
FOOD_LOW, FOOD_HIGH = 0.85, 1.15
REPO = ROOT.parents[1]
NB = json.load(open(REPO / 'analysis' / '01_clustering' / 'validation' / 'output' / 'nbti_12types.json', encoding='utf-8'))
TYPES = {t['id']: t for t in NB['types']}
IDS = list(TYPES)
COMMON = [c['nutrient'] for c in NB['common_nutrients']]
OTHER = [n for n in NUTRIENTS if n not in COMMON]
CAND = [n for n in NUTRIENTS if n not in WEAK]
KEYS = {'단백질': 'protein', '비타민A': 'vitamin_a', '비타민C': 'vitamin_c', '티아민': 'vitamin_b1', '리보플라빈': 'vitamin_b2',
        '엽산': 'folate', '칼슘': 'calcium', '인': 'phosphorus', '마그네슘': 'magnesium', '철': 'iron', '아연': 'zinc',
        '식이섬유': 'fiber', '비타민D': 'vitamin_d', '비타민E': 'vitamin_e', '칼륨': 'potassium'}


def line2(tbl):
    o = tbl[tbl['영양소'].isin(OTHER)]
    return o[(o['부족확률'] >= P_MAIN) | ((o['배수'] >= RATIO_CUT) & (o['부족확률'] >= P_FLOOR))]


def low_items(tbl):
    """덜 부족: 배수 ≤ 1/1.2, 약한 신호 3개와 2줄 항목 제외."""
    l2 = set(map(tuple, line2(tbl)[['유형', '성별', '연령대', '영양소']].to_numpy()))
    c = tbl[tbl['영양소'].isin(CAND) & (tbl['배수'] <= LOW_CUT)]
    return c[[t not in l2 for t in map(tuple, c[['유형', '성별', '연령대', '영양소']].to_numpy())]]


# %% 1. 2022–23 학습 모델 → 칸별 확률표 (13번과 같은 방식, 08번이 고른 설정)
d = add_status(load_persons(ROOT / 'KMedoids_12Types_N1O3.csv', 'Type'))
d['age_grp_s'] = d['age_grp'].astype(str)
d['male'] = (d['sex'] == '남자').astype(int)
w = d['w'] / d['w'].mean()
tr, te = d['year'] <= 2023, d['year'] == 2024
chosen = pd.read_csv(OUT / '08_2024검증.csv', encoding='utf-8-sig').set_index('영양소')['선택']


def make(cfg):
    oh = lambda cols: ColumnTransformer([('oh', OneHotEncoder(drop='first', handle_unknown='ignore'), cols)])
    if cfg.startswith('LR가법'):
        return ['sex', 'age_grp_s', 'cluster'], Pipeline([('p', oh(['sex', 'age_grp_s', 'cluster'])),
                                                           ('m', LogisticRegression(C=float(cfg.split('_C')[1]), max_iter=3000))])
    lr, leaf = cfg.split('_lr')[1].split('_leaf')
    return ['male', 'age', 'cluster'], Pipeline([
        ('p', ColumnTransformer([('ord', OrdinalEncoder(), ['cluster'])], remainder='passthrough')),
        ('m', HistGradientBoostingClassifier(learning_rate=float(lr), max_leaf_nodes=int(leaf), min_samples_leaf=100,
                                             max_iter=200, categorical_features=[0], early_stopping=False, random_state=SEED))])


grid = pd.MultiIndex.from_product([IDS, ['남자', '여자'], AGE_LABELS], names=['cluster', 'sex', 'age_grp_s']).to_frame(index=False)
grid['male'] = (grid['sex'] == '남자').astype(int)
grid['age'] = grid['age_grp_s'].map(d[tr].groupby('age_grp_s').apply(lambda g: np.average(g['age'], weights=g['w'])))
rows = []
for n in NUTRIENTS:
    y = d[f'below_{n}']
    cols, mdl = make(chosen[n])
    p = mdl.fit(d.loc[tr, cols], y[tr], m__sample_weight=w[tr].values).predict_proba(grid[cols])[:, 1]
    base = Pipeline([('p', ColumnTransformer([('oh', OneHotEncoder(drop='first'), ['sex', 'age_grp_s'])])),
                     ('m', LogisticRegression(max_iter=3000))]).fit(d.loc[tr, ['sex', 'age_grp_s']], y[tr], m__sample_weight=w[tr].values)
    pb = base.predict_proba(grid[['sex', 'age_grp_s']])[:, 1]
    rows.append(pd.DataFrame({'유형': grid['cluster'], '성별': grid['sex'], '연령대': grid['age_grp_s'], '영양소': n,
                              '부족확률': p, '성별연령평균': pb, '배수': p / pb}))
TR = pd.concat(rows, ignore_index=True)
pick = low_items(TR)
print(f'① 2022–23 모델로 고른 덜 부족 항목: {len(pick)}개 (칸×영양소), 항목이 있는 칸 {pick.groupby(["유형", "성별", "연령대"]).ngroups}/120')

# %% 2. 2024 검증: O/E < 1 인가 + 같은 성별·연령대 안에서 유형을 섞은 경우
t24 = d[te].reset_index(drop=True)
t24['sa'] = t24['sex'] + '_' + t24['age_grp_s']
W24 = t24['w'].to_numpy()
SA_RATE = {n: t24.groupby('sa').apply(lambda g: np.average(g[f'below_{n}'], weights=g['w'])) for n in NUTRIENTS}


def oe_table(clusters):
    out = []
    for r in pick.itertuples():
        cell = (clusters == r.유형) & (t24['sex'] == r.성별).to_numpy() & (t24['age_grp_s'] == r.연령대).to_numpy()
        if cell.sum() == 0:
            continue
        y = t24[f'below_{r.영양소}'].to_numpy()
        rate = SA_RATE[r.영양소][f'{r.성별}_{r.연령대}']
        out.append((r.유형, r.성별, r.연령대, r.영양소, int(cell.sum()), (y[cell] * W24[cell]).sum(), rate * W24[cell].sum(), r.배수))
    return pd.DataFrame(out, columns=['유형', '성별', '연령대', '영양소', 'n_2024', 'O', 'E', '예측배수'])


obs = oe_table(t24['cluster'].to_numpy())
oe = obs['O'].sum() / obs['E'].sum()
rng = np.random.default_rng(SEED)
boot = [obs.iloc[i]['O'].sum() / obs.iloc[i]['E'].sum() for i in (rng.integers(0, len(obs), len(obs)) for _ in range(2000))]
lo, hi = np.percentile(boot, [2.5, 97.5])
obs['관측배수'] = obs['O'] / obs['E']
null = []
for _ in range(200):
    sh = t24.groupby('sa')['cluster'].transform(lambda s: rng.permutation(s.to_numpy())).to_numpy()
    o = oe_table(sh)
    null.append(o['O'].sum() / o['E'].sum())
null = np.array(null)
print(f'   2024 O/E {oe:.3f} [95% CI {lo:.3f}, {hi:.3f}] | 관측배수 < 1인 항목 {(obs["관측배수"] < 1).mean():.1%} '
      f'| 유형 섞기 200회 O/E 평균 {null.mean():.3f} (최소 {null.min():.3f}) → 실제가 더 작은 비율 {(null <= oe).mean():.1%}')
by_n = obs.groupby('영양소').apply(lambda g: pd.Series({'항목수': len(g), 'O/E': g['O'].sum() / g['E'].sum()}), include_groups=False)
by_t = obs.groupby('유형').apply(lambda g: pd.Series({'항목수': len(g), 'O/E': g['O'].sum() / g['E'].sum()}), include_groups=False)
print('   영양소별:', by_n.round(3).to_dict('index'))
print('   유형별:', by_t.round(3).to_dict('index'))
obs.to_csv(OUT / '20_덜부족_2024검증.csv', index=False, encoding='utf-8-sig')

# %% 3. 웹용: 08번 최종 확률표(전체 연도)에 같은 규칙
L = pd.read_csv(OUT / '08_유형성별연령_부족확률.csv', encoding='utf-8-sig')
LOW = low_items(L).sort_values('배수')
cells = {}
for k in IDS:
    cells[k] = {}
    for sx, sk in [('남자', '1'), ('여자', '2')]:
        cells[k][sk] = {}
        for a in AGE_LABELS:
            c = LOW[(LOW['유형'] == k) & (LOW['성별'] == sx) & (LOW['연령대'] == a)]
            cells[k][sk][a] = [dict(key=KEYS[r.영양소], nutrient=r.영양소, of10=int(round(r.부족확률 * 10)),
                                    peerOf10=int(round(r.성별연령평균 * 10)), ratio=round(r.배수, 2),
                                    common=r.영양소 in COMMON) for r in c.itertuples()]
n_cells = sum(bool(v) for k in cells for s in cells[k] for v in cells[k][s].values())
print(f'\n   최종 표: 덜 부족 항목 {len(LOW)}개, 항목이 있는 칸 {n_cells}/120')
print('   유형별 항목 수:', LOW['유형'].value_counts().reindex(IDS, fill_value=0).to_dict())

# %% 4. ② 유형별 음식 한 줄 (18번 식품군 배수) + 연도별 안정성
FOODS = {'육류': '보조_MEAT_G', '생선': '보조_FISH_G', '유제품': '보조_DAIRY_G', '달걀': '보조_EGG_G', '콩류': '보조_LEGUME_G',
         '과일': '과일_주당', '채소': '채소_김치제외_주당'}
f = d.copy()
f['에너지'] = f['영양_N_EN']
f = f[f[list(FOODS.values()) + ['에너지']].notna().all(axis=1)].copy()
f['sa'] = f['sex'] + '_' + f['age_grp_s']


def ratios(g):
    res = {}
    for name, col in {**FOODS, '에너지': '에너지'}.items():
        sa_mean = g.groupby('sa').apply(lambda x: np.average(x[col], weights=x['w']))
        e = g['sa'].map(sa_mean) * g['w']
        o = g[col] * g['w']
        res[name] = (o.groupby(g['cluster']).sum() / e.groupby(g['cluster']).sum())
    return pd.DataFrame(res).reindex(IDS)


FA, F1, F2 = ratios(f), ratios(f[f['year'] <= 2023]), ratios(f[f['year'] == 2024])
same_dir = ((F1 - 1) * (F2 - 1) > 0)
flag = lambda F: (F <= FOOD_LOW).astype(int) - (F >= FOOD_HIGH).astype(int)
stable_flag = (flag(F1) == flag(F2))
print('\n② 유형 × 식품 배수 (전체 연도, 같은 성별·연령대 대비)')
print(FA.round(2).to_string())
food_only = list(FOODS)
sel = flag(FA)[food_only] != 0
print(f'   15% 기준 통과 {int(sel.values.sum())}칸 중 2022–23과 2024 방향이 같은 칸 {int((same_dir[food_only] & sel).values.sum())}, '
      f'두 기간 모두 15% 기준까지 같은 칸 {int((stable_flag[food_only] & sel).values.sum())}')

T18 = pd.read_csv(OUT / '18_유형_식품군_연결고리.csv', encoding='utf-8-sig')
food_line = {}
for k in IDS:
    less = [dict(food=x, pct=round((1 - FA.at[k, x]) * 100), stable=bool(same_dir.at[k, x]))
            for x in FA.loc[k, food_only].sort_values().index if FA.at[k, x] <= FOOD_LOW]
    more = [dict(food=x, pct=round((FA.at[k, x] - 1) * 100), stable=bool(same_dir.at[k, x]))
            for x in FA.loc[k, food_only].sort_values(ascending=False).index if FA.at[k, x] >= FOOD_HIGH]
    # 화면 유형 영역 항목(유형특이·식사량관련)의 설명 몫: 순서와 상관없는 값 (18번 4절)
    why = [dict(nutrient=r.영양소, key=KEYS[r.영양소], energy_only=round(r.에너지만_몫, 2), foods_only=round(r.식품군만_몫, 2),
                both=round(r.둘다_몫, 2)) for r in T18[(T18['유형'] == k) & T18['판정'].notna()].itertuples() if pd.notna(r.둘다_몫)]
    food_line[k] = dict(energy_ratio=round(FA.at[k, '에너지'], 2), less=less, more=more, why=why)
    s_less = ', '.join(f"{x['food']} {x['pct']}%" for x in less) or '-'
    s_more = ', '.join(f"{x['food']} {x['pct']}%" for x in more) or '-'
    print(f"   {k} {TYPES[k]['name']:16s} 에너지 {FA.at[k, '에너지']:.2f}배 | 덜 먹음: {s_less} | 더 먹음: {s_more}")

# %% 5. 저장 (웹 nutrientCells와 같은 키: 유형 → 성별 1·2 → 연령대)
out = {
    'version': 'yuhwan-12types-screen-B-v1.1-addon', 'generated': '2026-11-05', 'source_types': NB['version'],
    'low': {
        'rule': '같은 성별·나이 대비 1/1.2배(0.83배) 이하, 비타민 D·E·칼륨과 2줄 항목 제외. 08번 최종 확률표 기준',
        'text': '같은 성별·나이보다 덜 부족한 편이에요',
        'note': '덜 부족하다는 뜻이며 충분하다는 뜻이 아님. 공통 영양소(common=true)는 1줄에도 그대로 표시',
        'validation_2024': dict(items=len(obs), oe=round(oe, 3), ci=[round(lo, 3), round(hi, 3)],
                                shuffle_mean=round(float(null.mean()), 3), shuffle_min=round(float(null.min()), 3)),
        'cells': cells,
    },
    'foods': {
        'rule': f'같은 성별·나이 대비 섭취 배수 ≤ {FOOD_LOW} 덜 먹음 / ≥ {FOOD_HIGH} 더 먹음 (조사 가중). stable = 2022–23과 2024에서 방향이 같음',
        'source': '육류·생선·유제품·달걀·콩류는 24시간 회상 g, 과일·채소(김치 제외)는 설문 주당 빈도',
        'note': '관련성이며 인과가 아님. why의 몫 = 유형 차이 중 에너지만/식품군만/둘 다 맞췄을 때 줄어드는 비율 (18번 4절)',
        'types': food_line,
    },
}
with open(OUT / '20_유형화면_보강.json', 'w', encoding='utf-8') as fp:
    json.dump(out, fp, ensure_ascii=False, indent=1)
print('\n저장:', OUT / '20_유형화면_보강.json', '|', OUT / '20_덜부족_2024검증.csv')
