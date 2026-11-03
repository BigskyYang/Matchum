# %% [markdown]
# # [D-2] 개인 추천 함수(recommend_api.py) 검증
# 1) 같은 입력이면 04_제품추천.py(유형 기반)와 같은 제품이 나오는지: 유형별 필요 영양소를 '개인 입력'처럼 넣어 비교
# 2) 안전 문항(조용히 제외)·임신 상담 안내·식품으로만·보조 지표가 의도대로 동작하는지

# %%
import pandas as pd
from recommend_api import Recommender, JAEJUN_KEY, needs_from_model

rec = Recommender()
NOUT = rec.p.attrs.get('nout') or (__import__('pathlib').Path(__file__).resolve().parents[1] / '영양분석' / 'output')
combo = pd.read_csv(NOUT / '군집별_추천영양소조합.csv', encoding='utf-8-sig', index_col=0)
need = pd.read_csv(NOUT / '군집별_영양니즈_long.csv', encoding='utf-8-sig')
prof = pd.read_csv(NOUT / '군집_요약.csv', encoding='utf-8-sig', index_col=0)
old = pd.read_csv(rec.p.attrs.get('out', __import__('pathlib').Path(__file__).resolve().parent / 'output') / '추천_군집별.csv', encoding='utf-8-sig')
FOOD = {'인', '칼륨'}
COMMON = [n for n in (need.drop_duplicates('영양소').query('전체미달률 >= 0.5')
                      .assign(ai=lambda x: x['기준'].eq('AI')).sort_values(['ai', '전체미달률'], ascending=[True, False])['영양소'])
          if n not in FOOD]

# %% 1) 04와 같은 결과인지
rows = []
for c in combo.index:
    s = combo.loc[c, '유형특이조합']
    spec = [] if s.startswith('(') else [x.strip() for x in s.split('+')]
    needs = {n: 1.0 for n in spec}
    for n in COMMON:
        needs.setdefault(n, 0.5)
    profile = {'sex': '남자' if prof.loc[c, '남성비율'] >= 0.5 else '여자', 'age': prof.loc[c, '평균나이'],
               'smoker': prof.loc[c, '흡연율'] >= 0.5}
    out = rec.recommend(needs, profile)
    for g, items in out['장르'].items():
        new = [x['식품명'] for x in items]
        prev = old[(old.cluster == c) & (old.장르 == g)]['식품명'].tolist()
        rows.append(dict(유형=c, 장르=g, 같음=new == prev, 함수=' | '.join(new), 기존04=' | '.join(prev)))
cmp = pd.DataFrame(rows)
print('04와 같은 칸:', int(cmp['같음'].sum()), '/', len(cmp))
print(cmp[~cmp['같음']].to_string(index=False))

# %% 2) 동작 확인
base = {'iron': 'High', 'calcium': 'High', 'vitamin_c': 'Mid'}
person = {'sex': '여자', 'age': 35, 'smoker': False}
a = rec.recommend(base, person)
b = rec.recommend(base, {**person, 'kidney_disease_or_stones': True})
calc = lambda o: sum(1 for g in o['장르'].values() for x in g if '칼슘' in x['채우는영양소'])
print('\n[신장질환] 칼슘을 채우는 추천 칸: 기본', calc(a), '→ 신장질환 응답', calc(b), '| 화면 문구:', b['상담안내'])
o3 = rec.recommend({'iron': 'High'}, person)
o3k = rec.recommend({'iron': 'High'}, {**person, 'anticoagulant_or_aspirin': True})
names = lambda o: {x['식품명'] for g in o['장르'].values() for x in g}
om = rec.p.set_index('식품명')['safety_omega3'].groupby(level=0).max()
print('[항응고제] 오메가3 함유 추천 수: 기본', sum(om.get(n, False) for n in names(o3)), '→', sum(om.get(n, False) for n in names(o3k)))
pg = rec.recommend(base, {**person, 'pregnant_or_breastfeeding': True})
print('[임신·수유] 상태:', pg['상태'], '| 안내:', pg['안내'], '| 추천 칸:', sum(len(v) for v in pg['장르'].values()))
fo = rec.recommend({'potassium': 'High', 'phosphorus': 'High', 'sodium_excess': 'High'}, person)
print('[식품으로만] 상태:', fo['상태'], '|', [x['영양소'] for x in fo['식품으로만']])
ty = rec.recommend({'iron': 'High'}, person, type_nutrients=['철', '비타민D', '엽산'])
print('[보조 지표] 추천영양소:', ty['추천영양소'], '(엽산은 개인 결과에 없어 추가 안 함, 비타민D는 개인 모델에 없어 0.3 추가)')
print('[현재 영양제] 겹침 표시 예:', rec.recommend({'iron': 'High', 'vitamin_c': 'High'}, {**person, 'current_supplements': ['vitamin_c']})['장르']['충분함량형'][0]['지금드시는영양제와겹침'])
nd, bs = needs_from_model({'iron': 'Mid', 'calcium': 'Low', 'sodium_excess': 'High'}, {'iron': 'High', 'calcium': 'Mid'})
print('[재준님 두 신호 합치기]', nd, bs)
