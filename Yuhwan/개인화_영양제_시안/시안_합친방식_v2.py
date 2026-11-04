# -*- coding: utf-8 -*-
"""
합친 방식 시안 v2 (전유환, 11/4, 깃허브 미공유) — v1 약점 보완
  후보: 준혁님 변경안 9단계 결과 / 목록: 준혁님 10단계 규칙 재현 + B군은 B1·B2 든 제품만
  v2에서 바꾼 것
    1. 여러 영양소 칸: 덮는 개수가 같으면 '걸리지 않은 성분까지 덮는 개수'가 적은 제품 먼저 (종합비타민 쏠림 완화)
    2. 음식 먼저: 영양소마다 음식 예시(재준님 food_guidance.py 그대로)를 먼저, 제품은 "음식으로 챙기기 어렵다면" 아래 접어 둠
    3. 여러 영양소 칸 1순위가 이미 덮는 영양소는 "이 제품에 함께 들어 있어요"로 표시하고 따로 펼칠 목록에서 뺌
    4. 설계 가정을 ASSUMPTIONS에 적음
    5. 기준값 민감도: 덮는다 기준 20/30/50% × 대상자 확률 0.4/0.5/0.6
    6. 화면에 나올 수 있는 제품 전부를 사람이 확인할 표로 (어린이 의심 단어 자동 표시)
"""
import importlib
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

# 경로: 유환님 작업 폴더(machine2running/준혁_재현)와 깃허브 저장소(Matchum/Yuhwan/개인화_영양제_시안) 둘 다에서 돌아가게
HERE = Path(__file__).resolve().parent
REPO = next((p for p in [HERE.parent.parent, HERE.parent.parent / 'Matchum', Path(r'C:\python-course\Matchum')]
             if (p / 'junhyeok').exists()), None)
JH = REPO / 'junhyeok' / '분류_필터링'                      # 준혁님 코드 (8단계_점수.py의 함수를 그대로 씀)
PKL = HERE if (HERE / '8단계_결과.pkl').exists() else JH  # 준혁님 현재 1~8단계를 돌린 결과(.pkl)가 있는 곳
ROOT = next(p for p in [HERE.parent, REPO / 'Yuhwan'] if (p / '영양분석' / 'common.py').exists())
DATA = Path.home() / 'Desktop' / '영양제품 자료'          # 준혁님 변경안 시험용 CSV (슬랙 11/4)
PERSONS = Path(r'C:/python-course/machine2running/KMedoids_12Types_N1O3.csv')  # 개인 단위(깃허브 금지). 없으면 사람 시뮬레이션은 못 돌림
sys.path[:0] = [str(HERE), str(JH), str(ROOT / '영양분석'), str(REPO / 'Jaejun' / 'nutrition_final_feedback_applied' / 'src')]
from common import load_persons, add_status  # noqa: E402
from food_guidance import FOODS  # noqa: E402  재준님 음식 예시

ASSUMPTIONS = [
    '덮는다 = 하루 함량이 1일 영양성분 기준치의 30% 이상 (준혁님 점수에서 감점이 없는 선). B군은 B1 또는 B2, 식이섬유는 준혁님 식이섬유 목록',
    '제품 정보 대상 = 재준님 v1.4 생활습관 모델 "높은 편" + 부족 확률 0.5 이상 ("10명 중 5명 이상", 유형 결과와 같은 기준)',
    '생활습관 규칙은 팀의 설계 가정: 수면 6시간 미만·스트레스 높음 → 카페인·간 주의 원료 제품 제외, 끼니 불규칙(아침·점심·저녁 중 주 1~2회 이하) → 하루 1개 제품 먼저',
    '효능 연결(예: 스트레스엔 마그네슘)은 하지 않음. 조합을 정해 주지 않고 정보로만 보여 줌',
    '제품명에 어린이 의심 단어가 있는 제품은 사람이 확인하기 전까지 화면에서 뺌',
    '주의 문구 = 영양소별 목록 1순위 + 여러 영양소 칸 1순위를 모두 먹는다고 가정했을 때 상한을 넘는 경우',
]
step8 = importlib.import_module('8단계_점수')
UL, DV = step8.UL, dict(step8.DV)
NUTS = ['비타민 B군', '비타민 C', '칼슘', '마그네슘', '아연', '철', '엽산', '식이섬유']
MODEL2PROD = {'vitamin_b1': '비타민 B군', 'vitamin_b2': '비타민 B군', 'vitamin_c': '비타민 C', 'calcium': '칼슘',
              'magnesium': '마그네슘', 'zinc': '아연', 'iron': '철', 'folate': '엽산', 'fiber': '식이섬유'}
KEY2KOR = {'vitamin_b1': '티아민', 'vitamin_b2': '리보플라빈', 'vitamin_c': '비타민C', 'calcium': '칼슘', 'magnesium': '마그네슘',
           'zinc': '아연', 'iron': '철', 'folate': '엽산', 'fiber': '식이섬유'}
FOOD = {}
for k, n in MODEL2PROD.items():
    FOOD.setdefault(n, [])
    FOOD[n] += [f for f in FOODS[k][1] if f not in FOOD[n]]
KIDS = r'키즈|어린이|아이들|아이용|우리아이|주니어|청소년|성장|키튼|쑥쑥|키크|키 크|베이비|유아|kids|junior|baby'

# %% 데이터 (v1과 같음)
r9 = pd.read_csv(DATA / '9단계_점수_결과시험용.csv', dtype=str, encoding='utf-8-sig')
for c in ['점수', '기준치 대비(%)', '원재료 수']:
    r9[c] = pd.to_numeric(r9[c], errors='coerce')
r9['하루개수'] = pd.to_numeric(r9['1일 섭취량'].str.extract(r'하루\s*([\d\.]+)')[0], errors='coerce')
r9['상'] = r9['등급'] == '상'
r9['dv_gap'] = (np.log(r9['기준치 대비(%)'].clip(lower=1) / 100)).abs().fillna(0)
amt = pd.read_pickle(PKL / '6단계_제품별함량.pkl')
spec = pd.read_pickle(PKL / '8단계_결과.pkl').drop_duplicates('품목제조신고번호').set_index('품목제조신고번호')['기준규격']
ids = r9['품목제조신고번호'].unique()
A = amt.reindex(ids)[list(UL)].apply(pd.to_numeric, errors='coerce').fillna(0)
bp = spec.reindex(ids).fillna('').map(step8.b_percent)
PCT = pd.DataFrame({**{n: A[n] / DV[n] * 100 for n in DV if n in NUTS},
                    '비타민 B군': bp.map(lambda d: max(d.get('비타민 B1', 0), d.get('비타민 B2', 0)))}, index=ids)
FIBER = pd.Series(ids, index=ids).isin(set(r9.loc[r9['영양소'] == '식이섬유', '품목제조신고번호']))
prod = (r9.sort_values(['상', '점수'], ascending=False).drop_duplicates('품목제조신고번호').set_index('품목제조신고번호')
          [['제품명', '업체명', '대상', '구분', '상', '점수', '하루개수', '원재료 수', '주의 원료', 'dv_gap', '기능성']])
prod['주의'] = prod['주의 원료'].fillna('').ne('') & prod['주의 원료'].fillna('').ne('없음')
prod['종합'] = prod['구분'].eq('종합비타민')
prod['어린이의심'] = prod['제품명'].str.contains(KIDS, case=False, regex=True)
print('어린이 의심 제품 (확인 전까지 화면에서 뺌):', prod.loc[prod['어린이의심'], '제품명'].tolist())
KID_IDS = set(prod.index[prod['어린이의심']])
r9 = r9[~r9['품목제조신고번호'].isin(KID_IDS)]
prod = prod[~prod['어린이의심']]
r9['주의'] = r9['품목제조신고번호'].map(prod['주의'])


def cover_table(thr):
    return pd.DataFrame({n: (PCT[n] >= thr) if n != '식이섬유' else FIBER for n in NUTS}, index=ids)


def distinct_vendor(df, n=3):
    out, seen = [], set()
    for i, v in zip(df['품목제조신고번호'], df['업체명']):
        if v in seen or i in out:
            continue
        out.append(i)
        seen.add(v)
        if len(out) == n:
            break
    return out


def lists(S, T, COVER, irregular=False, avoid=False):
    res = {}
    for n in S:
        g = r9[(r9['영양소'] == n) & r9['대상'].isin(T)]
        if n == '비타민 B군':
            g = g[g['품목제조신고번호'].map(COVER['비타민 B군'])]
        if avoid:
            g = g[~g['주의']]
        g = g.assign(one=g['하루개수'].eq(1) if irregular else True)
        res[n] = distinct_vendor(g.sort_values(['one', '상', '점수', '하루개수', 'dv_gap', '원재료 수'],
                                               ascending=[False, False, False, True, True, True]))
    return res


def multi_box(S, T, COVER, irregular=False, avoid=False, extra_rule=True):
    if len(S) < 2:
        return []
    c = prod[prod['대상'].isin(T)].copy()
    if avoid:
        c = c[~c['주의']]
    c['gain'] = COVER.loc[c.index, list(S)].sum(axis=1)
    c['extra'] = COVER.loc[c.index, [n for n in NUTS if n not in S]].sum(axis=1) if extra_rule else 0
    c = c[c['gain'] >= 2].reset_index()
    if c.empty:
        return []
    c['one'] = c['하루개수'].eq(1) if irregular else True
    c = c.sort_values(['gain', 'extra', 'one', '상', '점수', '하루개수', 'dv_gap', '원재료 수'],
                      ascending=[False, True, False, False, False, True, True, True])
    return distinct_vendor(c)


def over(idlist):
    tot = A.reindex(list(dict.fromkeys(i for i in idlist if i))).fillna(0).sum()
    return [n for n in UL if tot[n] > UL[n]]


# %% 2024 사람들 + 재준님 v1.4
NM = json.load(open(REPO / 'bigskyyang' / 'web' / 'src' / 'data' / 'nutritionModels.json', encoding='utf-8'))['lifestyle']
d = add_status(load_persons(PERSONS, 'Type'))
for c_ in ['식습관_LS_FRUIT', '식습관_LS_VEG2']:
    d[c_] = d[c_].where(~d[c_].isin([99]))
d = d[(d['year'] == 2024) & d[NM['features']].notna().all(axis=1)].reset_index(drop=True)
X = d[NM['features']].to_numpy(float)


def prob(m):
    if m['type'] != 'hgb':
        z = (X - np.array(m['mean'])) / np.array(m['scale'])
        return 1 / (1 + np.exp(-(z @ np.array(m['coef']) + m['intercept'])))
    raw, rows = np.full(len(X), m['baseline']), np.arange(len(X))
    for t in m['trees']:
        f, th, l, r = (np.array(t[k]) for k in 'ftlr')
        node = np.zeros(len(X), dtype=int)
        while (inner := f[node] >= 0).any():
            n = node[inner]
            node[inner] = np.where(X[rows[inner], f[n]] <= th[n], l[n], r[n])
        raw += th[node]
    return 1 / (1 + np.exp(-raw))


Pm = pd.DataFrame({k: prob(NM['models'][k]) for k in MODEL2PROD})
HIGH = pd.DataFrame({k: Pm[k] >= NM['cuts'][k]['mid_high'] for k in MODEL2PROD})
d['irregular'] = (d['ML_breakfast_freq_ord'] <= 1) | (d['ML_lunch_freq_ord'] <= 1) | (d['ML_dinner_freq_ord'] <= 1)
d['avoid'] = (d['ML_sleep_hours'] < 6) | (d['ML_stress'] == 1)
d['T'] = [('일반', '남성' if s == '남자' else '여성') + (('시니어',) if a >= 50 else ()) for s, a in zip(d['sex'], d['age'])]
W = d['w'].to_numpy()


def run(thr=30, gate_p=0.5, extra_rule=True, keep=False):
    COVER = cover_table(thr)
    G = HIGH & (Pm >= gate_p)
    rows, cache, hits = [], {}, []
    for i, r in enumerate(d.itertuples()):
        flagged = [kk for kk in MODEL2PROD if G.at[i, kk]]
        for kk in flagged:
            hits.append((r.w, d.at[i, f'below_{KEY2KOR[kk]}']))
        S = tuple(sorted({MODEL2PROD[kk] for kk in flagged}))
        if not S:
            rows.append(dict(w=r.w, k=0))
            continue
        key = (S, r.T, r.irregular, r.avoid)
        if key not in cache:
            box = multi_box(S, r.T, COVER, r.irregular, r.avoid, extra_rule)
            L = lists(S, r.T, COVER, r.irregular, r.avoid)
            inbox = [n for n in S if box and COVER.at[box[0], n]]
            cache[key] = dict(box=box, L=L, inbox=inbox,
                              over=over([v[0] for v in L.values() if v] + box[:1]),
                              box_multi=bool(box) and prod.at[box[0], '종합'],
                              box_extra=int(COVER.loc[box[0], [n for n in NUTS if n not in S]].sum()) if box else np.nan)
        c = cache[key]
        rows.append(dict(w=r.w, k=len(S), 상자=bool(c['box']), 상자_종합=c['box_multi'], 상자_군더더기=c['box_extra'],
                         상자가_덮은수=len(c['inbox']), 따로펼칠목록=len(S) - len(c['inbox']), 주의=bool(c['over']),
                         주의성분='·'.join(c['over'])))
    R = pd.DataFrame(rows)
    hw = np.array(hits, float)
    seen = R[R['k'] > 0]
    wa = lambda col, g: np.average(g[col].astype(float), weights=g['w']) if len(g) else np.nan
    two3 = seen[seen['k'].between(2, 3)]
    out = dict(덮는기준=thr, 확률기준=gate_p, 보는사람=wa('k', R.assign(k=R['k'] > 0)),
               실제부족률=np.average(hw[:, 1], weights=hw[:, 0]), 평균영양소=wa('k', seen),
               상자있음_2개이상=wa('상자', seen[seen['k'] >= 2]), 상자종합_2_3개=wa('상자_종합', two3[two3['상자']]),
               상자군더더기_2_3개=wa('상자_군더더기', two3[two3['상자']]), 주의문구=wa('주의', seen),
               따로펼칠목록=wa('따로펼칠목록', seen))
    return (out, R, cache, COVER) if keep else out


# %% 1. 기본 결과 (30%, 0.5) — v1(군더더기 규칙 없음)과 비교
base, R, cache, COVER = run(keep=True)
v1 = run(extra_rule=False)
print('설계 가정'); [print(' -', a) for a in ASSUMPTIONS]
cmp_ = pd.DataFrame({'v1': v1, 'v2': base}).drop(['덮는기준', '확률기준'])
print('\n1. v1 → v2 (A안 30% 기준)')
print(cmp_.round(3).to_string())
seen = R[R['k'] > 0]
print('걸린 영양소 개수별 여러 영양소 칸 1순위가 종합비타민인 비율 (v2):',
      seen[seen['상자']].groupby('k').apply(lambda g: np.average(g['상자_종합'].astype(float), weights=g['w']), include_groups=False).round(2).to_dict())
print('주의 문구 성분:', R.loc[R.get('주의', False) == True, '주의성분'].value_counts().to_dict())

# %% 5. 기준값 민감도
sens = pd.DataFrame([run(t, p) for t in (20, 30, 50) for p in (0.4, 0.5, 0.6)])
sens.to_csv(HERE / '시안v2_민감도.csv', index=False, encoding='utf-8-sig')
print('\n5. 기준값 민감도 (덮는 기준 × 대상자 확률)')
print(sens.round(3).to_string(index=False))

# %% 2·3. 화면 예시 (음식 먼저 → 여러 영양소 칸 → 접힌 목록)
nm = lambda i: f"{prod.at[i, '제품명']} ({prod.at[i, '업체명']})"
print('\n2·3. 화면 예시')
done = set()
for (S, T, irr, av), c in cache.items():
    if len(S) not in (2, 4) or len(S) in done or not c['box']:
        continue
    done.add(len(S))
    print(f"\n● {', '.join(S)} | {'·'.join(T)} | 끼니 불규칙 {irr} | 수면부족·스트레스 {av}")
    print('  먼저 음식으로: ' + ' / '.join(f"{n}({', '.join(FOOD[n][:3])})" for n in S))
    print('  음식으로 챙기기 어렵다면 ▸ 한 제품에 여러 영양소가 함께 든 제품도 있어요')
    for i in c['box']:
        print(f"     - {nm(i)}: {'·'.join(n for n in S if COVER.at[i, n])}")
    for n, v in c['L'].items():
        tag = '  (위 제품에 함께 들어 있어요)' if n in c['inbox'] else ''
        print(f"  ▸ {n} 제품 정보 (접힘){tag}: " + ' / '.join(nm(i) for i in v))
    if c['over']:
        print('  ⚠ 함께 드시면 상한을 넘을 수 있는 성분:', ', '.join(c['over']))

# %% 6. 사람이 확인할 표: 화면에 나올 수 있는 제품 전부 + 자동 점검 (걸린 것만 사람이 봄)
import re
FN = {'비타민 B군': r'비타민\s*B1|티아민|비타민\s*B2|리보플라빈|탄수화물과 에너지 대사|체내 에너지 생성',
      '비타민 C': r'비타민\s*C|결합조직 형성|유해산소로부터 세포를 보호|철의 흡수', '칼슘': r'칼슘|뼈와 치아 형성|골다공증 ?발생 위험',
      '마그네슘': r'마그네슘|에너지 이용|신경과 근육 기능 유지', '아연': r'아연|정상적인 면역기능|정상적인 세포분열',
      '철': r'철|체내 산소운반|혈액생성', '엽산': r'엽산|세포와 혈액생성|태아 신경관|호모시스테인', '식이섬유': r'식이섬유|차전자피|배변'}
# 다른 목적 문구. 영양소 자체의 식약처 기능(비타민 A '피부와 점막', 차전자피 '콜레스테롤')은 제외
OTHER = r'체지방|혈당|혈압|관절|연골|피부(?!와 점막)|모발|기억|인지|눈 건강|눈의 피로|간 건강|전립선|갱년기|수면|긴장'
note = r9.drop_duplicates('품목제조신고번호').set_index('품목제조신고번호')['섭취 시 주의사항']
shown_ids = sorted({i for c in cache.values() for i in c['box'] + [x for v in c['L'].values() for x in v]})
chk = prod.loc[shown_ids, ['제품명', '업체명', '대상', '구분', '하루개수', '원재료 수', '기능성']].copy().fillna('')
chk['덮는 영양소'] = ['·'.join(n for n in NUTS if COVER.at[i, n]) for i in shown_ids]
chk['주의사항'] = note.reindex(shown_ids).fillna('')


def auto_check(r):
    why = []
    if re.search(KIDS, r['제품명'], re.I) or re.search(r'어린이|성장기|청소년', r['기능성']):
        why.append('대상')
    miss = [n for n in r['덮는 영양소'].split('·') if n and not re.search(FN[n], r['기능성'])]
    if miss:
        why.append('영양소(' + ','.join(miss) + ')')
    m = sorted(set(re.findall(OTHER, r['기능성'])))
    if m:
        why.append('목적(' + ','.join(m) + ')')
    return ' / '.join(why)


chk['자동점검'] = chk.apply(auto_check, axis=1)
chk['확인(맞음/틀림)'] = ''
chk['메모'] = ''
chk = chk.reset_index().rename(columns={'index': '품목제조신고번호'})
chk.sort_values('자동점검', ascending=False).to_csv(HERE / '시안v2_사람확인표.csv', index=False, encoding='utf-8-sig')
flag = chk[chk['자동점검'] != '']
print(f"\n6. 화면에 나올 수 있는 제품 {len(chk)}개 (어린이 의심 {len(KID_IDS)}개는 이미 뺌) → 자동 점검에 걸린 제품 {len(flag)}개 (사람 확인 대상)")
for r in flag.itertuples():
    print(f"   - {r.제품명} | {r.구분} | {r.자동점검}")
