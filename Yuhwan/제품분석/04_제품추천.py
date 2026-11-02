# %% [markdown]
# # [D] 고객 군집 → 영양소 모듈 → 제품 유형 → 장르별 제품 추천 (v2)
# 입력: 영양분석/output/군집별_추천영양소조합.csv, 군집별_영양니즈_long.csv, 군집_요약.csv
#       제품분석/output/product_types.csv (03 결과), 원본 CSV(에너지)
# 출력: output/추천_군집별.csv, 군집x제품유형_매칭.csv, 추천_변별력.csv, recommendations.json
#
# 흐름
#  1) 고객 군집 → 필요 영양소 (유형특이 가중치 1.0, 공통주의 0.5) + 매칭된 영양소 모듈(→ 식품 안내)
#  2) 필요 영양소 벡터 ↔ 제품 유형 16개 중심 코사인 유사도 → 상위 3개 유형
#     안전장치: 유형 안 최고 커버율 < 전체 최고의 90%면 다음 유형을 하나씩 추가 (함량 미상 성분 때문에 놓치는 것 방지)
#  3) 고른 유형 안에서 장르별 TOP3
#     품질형  : 핵심 영양소(유형특이 상위 2개, 없으면 공통주의 상위 2개)를 실제 함량으로 기준치 30%↑·UL 이하
#     올인원형: 여러 성분 유형(평균 성분 2개↑) 전체에서. 유형특이 덮은 개수 → 공통주의 덮은 개수 → 커버율 순
#     가성비형: price_per_day 열이 있으면 커버율/1일 가격, 없으면 '간편형' = 핵심 커버율/1일 복용 개수 (임시)
#              (전체 커버율로 나누면 1정짜리 종합비타민이 모든 군집에서 1등 → 핵심 영양소 기준으로 바꿈)
# 필터: UL 초과·단위오류 의심 / 흡연 군집 베타카로틴 / 1일 200kcal 이상(식사 대용) /
#       키즈·청소년·임산부용 / 성별 전용(군집 성비가 반대면) / 실버(군집 평균 50세 미만이면)
# 다양성: 장르 안 3개는 제조사·제품명 중복 없이

# %%
from pathlib import Path
import itertools
import json
import re
import numpy as np
import pandas as pd
from price_file import read_price_file, write_price_file

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '제품분석' / 'output'
NOUT = ROOT / '영양분석' / 'output'

combo = pd.read_csv(NOUT / '군집별_추천영양소조합.csv', encoding='utf-8-sig', index_col=0)
need = pd.read_csv(NOUT / '군집별_영양니즈_long.csv', encoding='utf-8-sig')
prof = pd.read_csv(NOUT / '군집_요약.csv', encoding='utf-8-sig', index_col=0)
p = pd.read_csv(OUT / 'product_types.csv', encoding='utf-8-sig')
# v5: 02에서 새로 만든 열(주목적·목적일치·종합형·원료 배지)을 붙임 (군집 벡터는 그대로라 03을 다시 돌릴 필요 없음)
_f = pd.read_csv(OUT / 'product_features.csv', encoding='utf-8-sig')
_new = [c for c in _f.columns if c not in p.columns]
p = p.merge(_f[['식품코드'] + _new].drop_duplicates('식품코드'), on='식품코드', how='left')
p['주목적_기능성'] = p['주목적_기능성'].fillna('')
raw = pd.read_csv(ROOT / '전국건강기능식품영양성분정보표준데이터.csv', encoding='cp949', low_memory=False)
p = p.merge(raw[['식품코드', '에너지(kcal)']].drop_duplicates('식품코드'), on='식품코드', how='left')
p['일_에너지'] = p['에너지(kcal)'].fillna(0) * p['n_day']

COLMAP = {'단백질': '단백질', '비타민A': '비타민 A', '비타민D': '비타민 D', '비타민E': '비타민 E', '비타민C': '비타민 C',
          '티아민': '티아민', '리보플라빈': '리보플라빈', '엽산': '엽산', '칼슘': '칼슘', '마그네슘': '마그네슘',
          '철': '철', '아연': '아연', '식이섬유': '식이섬유'}
QUANT = {'단백질', '식이섬유', '칼슘', '철', '비타민 A', '비타민 D', '비타민 C', '티아민', '리보플라빈', '니아신'}
V = [c for c in p.columns if c.startswith('v_')]
FOOD_ONLY = {'인', '칼륨'}
# 공통주의 순서: EAR 기준 먼저, 그 안에서 미달률 높은 순 (03과 같은 규칙)
COMMON = [n for n in (need.drop_duplicates('영양소').query('전체미달률 >= 0.5')
                      .assign(ai=lambda x: x['기준'].eq('AI')).sort_values(['ai', '전체미달률'], ascending=[True, False])['영양소'])
          if n not in FOOD_ONLY]
REFERENCE = ['오메가3', '유산균', '루테인', '밀크씨슬', '비타민 K']
K_TYPES, FALLBACK = 3, 0.90

# %% 제품 대상 키워드 (제품명 기준)
nm = p['식품명'].fillna('')
p['대상_제외'] = nm.str.contains(r'키즈|어린이|유아|주니어|청소년|베이비|키디|kids|junior|children|임산부|임신|맘스|프리나탈|prenatal|수유', case=False, regex=True)
p['대상_여성'] = nm.str.contains(r'우먼|여성|레이디|woman|women|for\s?her', case=False, regex=True)
p['대상_남성'] = nm.str.contains(r'남성|맨즈|포\s?맨|실버맨|for\s?men|\bmen\b|\bman\b', case=False, regex=True)
p['대상_실버'] = nm.str.contains(r'실버|시니어|50\+|50플러스|silver|senior', case=False, regex=True)
p['식사대용'] = p['일_에너지'] >= 200

# %% 재준님 안전 규칙 연결 (Jaejun/config/supplement_safety_rules.json)
#  신장질환·결석 → calcium·potassium·phosphorus / 항응고제·아스피린 → omega3·vitamin_k 함유 제품 제한
#  함량 칸이 있는 성분(칼슘·칼륨·인)은 1일 함량 > 0 또는 제품명에 성분명, 칸이 없는 성분(오메가3·비타민K)은 제품명 키워드
#  → 제품마다 '함유' 표시만 붙이고, 걸러내기는 웹에서 설문 응답으로 (임신·수유는 규칙상 추천 자체 중단이라 표시 불필요)
SAFETY_RULES = json.loads((ROOT / 'Jaejun_config' / 'supplement_safety_rules.json').read_text(encoding='utf-8')) \
    if (ROOT / 'Jaejun_config' / 'supplement_safety_rules.json').exists() else None
SAFETY = {
    'calcium': (p['일_칼슘'].fillna(0) > 0) | nm.str.contains('칼슘|calcium', case=False),
    'potassium': (p['일_칼륨'].fillna(0) > 0) | nm.str.contains('칼륨|potassium', case=False),
    'phosphorus': p['일_인'].fillna(0) > 0,
    'omega3': p['has_오메가3'] == 1,
    'vitamin_k': p['has_비타민 K'] == 1,
}
SAFETY_BASIS = {'calcium': '1일 함량>0 또는 제품명', 'potassium': '1일 함량>0 또는 제품명', 'phosphorus': '1일 함량>0',
                'omega3': '제품명 키워드(오메가·EPA·DHA·rTG·크릴)', 'vitamin_k': '제품명 키워드(비타민K·K2·메나퀴논)'}
for k, s in SAFETY.items():
    p[f'safety_{k}'] = s.astype(bool)
p = p.copy()   # 열을 많이 붙여서 생기는 조각난 프레임 경고 방지

# 제품 자체의 주성분(유형 이름과 다를 수 있어 같이 표시)
Xv = p[V].astype(float).copy()
qcols = [f'v_{q}' for q in QUANT]
kind = p['군집변환'].iat[0]
Xv[qcols] = np.log1p(Xv[qcols] / 100) if kind == 'log' else np.minimum(Xv[qcols], 300 if kind == 'cap300' else 100) / 100
p['주성분'] = Xv.apply(lambda r: '·'.join(c[2:] for c in r.sort_values(ascending=False).index[:3] if r[c] > 0), axis=1)
cent = Xv.groupby(p['제품유형명']).mean()
multi_types = set(p.groupby('제품유형명')['구성성분수'].mean().loc[lambda s: s >= 2].index)


def coverage(col):
    v = p[f'v_{col}'].astype(float)
    return np.minimum(v / 100, 1) if col in QUANT else v * 0.3     # 함량 미상 = 고시형 최소 30% 가정


def targets(c):
    s = combo.loc[c, '유형특이조합']
    spec = [] if s.startswith('(') else [x.strip() for x in s.split('+')]
    w = {COLMAP[n]: 1.0 for n in spec if n in COLMAP}
    for n in COMMON:
        w.setdefault(COLMAP[n], 0.5)
    return w, [COLMAP[n] for n in spec if n in COLMAP]


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


# %% 군집별 추천
# 가격: 팀원이 채운 output/가격조사_대상.xlsx가 있으면 1일 가격 계산 → 가성비형 자동 전환
#   1일 가격 = 판매가격 ÷ (총개수 ÷ 1일개수). 가격이 없는 제품은 가성비형 후보에서만 빠짐
PRICE_FILE = OUT / '가격조사_대상.xlsx'
if PRICE_FILE.exists():
    pr = read_price_file(PRICE_FILE)
    pr = pr[pd.to_numeric(pr['판매가격(원)'], errors='coerce').gt(0) & pd.to_numeric(pr['총개수'], errors='coerce').gt(0)]
    pr['price_per_day'] = pr['판매가격(원)'].astype(float) / (pr['총개수'].astype(float) / pr['1일개수'].astype(float))
    p = p.merge(pr[['식품코드', 'price_per_day']], on='식품코드', how='left')
has_price = 'price_per_day' in p.columns and p['price_per_day'].notna().sum() >= 30
rows, web, match_rows, price_cand = [], {}, [], []
for c in combo.index:
    w, spec_cols = targets(c)
    cols = list(w)
    common_cols = [k for k in cols if k not in spec_cols]
    cov = pd.DataFrame({k: coverage(k) for k in cols})
    wcov = sum(cov[k] * w[k] for k in cols) / sum(w.values())

    # 필터
    male, age = prof.loc[c, '남성비율'], prof.loc[c, '평균나이']
    ok = (p['UL초과'] == 0) & ~p['식사대용'] & ~p['대상_제외']
    ok &= ~(p['대상_여성'] & (male >= 0.5)) & ~(p['대상_남성'] & (male < 0.5)) & ~(p['대상_실버'] & (age < 50))
    if prof.loc[c, '흡연율'] >= 0.5:
        ok &= p['베타카로틴함유'] == 0
    ok &= (cov[spec_cols] > 0).any(axis=1) if spec_cols else (cov > 0).any(axis=1)

    # 2) 제품 유형 매칭 (코사인) + 안전장치
    vec = np.array([w.get(col[2:], 0) for col in V])
    sim = pd.Series(cent.values @ vec / (np.linalg.norm(cent.values, axis=1) * np.linalg.norm(vec) + 1e-9), index=cent.index)
    order = sim.sort_values(ascending=False).index.tolist()
    k = K_TYPES
    best_all = wcov[ok].max()
    while k < len(order) and wcov[ok & p['제품유형명'].isin(order[:k])].max() < FALLBACK * best_all:
        k += 1
    types = order[:k]
    in_type = ok & p['제품유형명'].isin(types)
    for t in types:                                                 # 가격 조사 후보: 매칭 유형마다 커버율 상위 10
        price_cand += wcov[in_type & p['제품유형명'].eq(t)].nlargest(10).index.tolist()
    match_rows.append(dict(cluster=c, 매칭유형=' | '.join(f'{t}({sim[t]:.2f})' for t in types), 유형수=k,
                           안전장치_추가=k - K_TYPES))

    # 3) 장르 (v5: 준혁님 5가지 큐레이션 + 우리 방식 혼합)
    #   충분함량형: 핵심 영양소 중 하나 이상을 기준치 100%↑로 채우고(UL 이하), 나머지 핵심 성분도 30%↑ (준혁님 '최고 함량'을 UL·적정 기준으로 수정)
    #   편의형    : 1일 1회 1개로 끝나는 제품 중 핵심 커버율 순 (준혁님 '섭취 편의성')
    #   가성비형  : 가격 조사 후 1일 가격당 커버율 (가격 없으면 '가격 조사 중'으로 비움)
    #   종합형    : 종합비타민 전용 풀에서 따로 (준혁님 아이디어, '메가' 키워드 제외) — 단일 영양소 장르에서는 종합형 제외
    #   원료 형태(D3·rTG·활성비타민B·장용성 등)는 순위가 아니라 배지로 표시 / 대중성·브랜드 점수는 쓰지 않음 (팀 원칙)
    #   목적 일치: 기능성 주목적 제품(간·면역 등)은 핵심 영양소 이름이 제품명에 있을 때만 후보
    core = (spec_cols or [COLMAP[n] for n in COMMON])[:2]
    core_cov = cov[core].sum(axis=1)
    extra = (p[V] > 0).sum(axis=1) - (cov > 0).sum(axis=1)
    purpose = pd.Series(False, index=p.index)
    for k in core:
        if f'목적일치_{k}' in p.columns:
            purpose |= (cov[k] > 0) & (p[f'목적일치_{k}'] == 1)
    single = in_type & purpose & (p['종합형'] == 0) & (core_cov > 0)
    qcore = [k for k in core if k in QUANT]
    full = pd.Series(False, index=p.index)
    low = pd.Series(False, index=p.index)
    for k in qcore:
        full |= p[f'v_{k}'] >= 100
        low |= (p[f'v_{k}'] > 0) & (p[f'v_{k}'] < 30)
    suff = single & full & ~low
    # 이름에 핵심 영양소가 적힌 제품(예: '비타민B 컴플렉스') 우선: 함량이 둘 다 기준치 이상이면 커버율이 같아져 순서가 임의로 정해지는 문제 보완
    named = pd.Series(0.0, index=p.index)
    for k in core:
        if f'name_{k}' in p.columns:
            named = np.maximum(named, p[f'name_{k}'].fillna(0))
    conv = single & p['1일개수'].eq(1) & p['n_day'].eq(1)
    n_spec = (cov[spec_cols] >= 0.3).sum(axis=1) if spec_cols else 0
    n_comm = (cov[common_cols] >= 0.3).sum(axis=1)
    multi = ok & (p['종합형'] == 1)
    genres = {
        '충분함량형': pick(p[suff], (core_cov + 0.3 * wcov - 0.05 * extra + 0.5 * named)[suff]),
        '편의형(1일 1회 1개)': pick(p[conv], (core_cov + 0.3 * wcov - 0.05 * extra + 0.5 * named)[conv]),
    }
    if has_price:
        pv = single & p['price_per_day'].notna()
        genres['가성비형'] = pick(p[pv], ((core_cov + 0.3 * wcov) / p['price_per_day'])[pv])
    genres['종합형'] = pick(p[multi], (100 * n_spec + 10 * n_comm + wcov)[multi])

    get = lambda col: combo.loc[c, col] if col in combo.columns and pd.notna(combo.loc[c, col]) else ''
    web[c] = {'유형ID': c, '유형이름': '(이름 확인 중)', '엑셀이름(참고)': prof.loc[c, '엑셀이름(확인중)'] if '엑셀이름(확인중)' in prof.columns else '',
              '유형특이': [n for n in get('유형특이조합').split(' + ') if not n.startswith('(')],
              '공통주의': COMMON, '원인': get('원인'), '매칭영양소모듈': get('매칭모듈'), '식품안내': get('식품안내'),
              '같이복용': get('같이'), '따로복용': get('따로'), '식품으로만': get('식품으로만'),
              '매칭제품유형': types, '참고정보(순위없음)': REFERENCE,
              '가성비형': '' if has_price else '가격 조사 중 (가격조사_대상.xlsx)', '장르': {}}
    for g, df in genres.items():
        web[c]['장르'][g] = []
        for _, r in df.iterrows():
            covers = [x for x in cols if cov.loc[r.name, x] >= 0.3]
            if not covers:      # 필요한 영양소를 하나도 30% 이상 못 채우는 제품은 빼기 (예: Group_2_B 종합형 '슈퍼 그린(엽록소)')
                continue
            unknown = [x for x in covers if x not in QUANT]
            item = dict(식품명=r['식품명'], 제조사=r['제조사명'], 제품유형=r['제품유형명'], 주성분=r['주성분'],
                        덮는영양소=covers, 함량미상=unknown, 가중커버율=round(float(wcov[r.name]), 3), 일개수=r['1일개수'],
                        표시형태=[f for f in ['D3', 'rTG', '리포좀', '활성엽산', '활성비타민B', '장용성'] if r.get(f'form_{f}', 0) == 1],
                        주목적=r.get('주목적_기능성', '') or '비타민·미네랄',
                        안전_함유=[k for k in SAFETY if r[f'safety_{k}']])
            web[c]['장르'][g].append(item)
            rows.append(dict(cluster=c, 장르=g, **{kk: vv for kk, vv in item.items() if kk != '표시형태'}))

rec = pd.DataFrame(rows)

# %% 가격 조사 대상 목록: 없으면 새로 만들고, 있으면 '새 후보만 덧붙임' (팀원이 채운 가격은 그대로 둠)
idx = list(dict.fromkeys(price_cand + p.index[p['식품명'].isin(rec['식품명'])].tolist()))
cand = p.loc[idx, ['식품코드', '식품명', '제조사명', '품목제조신고번호', '제품유형명', '주성분', '1회분량', '영양성분제공단위량', 'n_day', '1일개수']]
cand = cand.rename(columns={'n_day': '1일섭취횟수', '영양성분제공단위량': '1회분량중량'})
cnt = cand['식품명'].str.extract(r'(\d+)\s*(?:정|캡슐|포|병|구미|소프트젤|베지캡)')[0]   # 제품명의 '120정' 등 (확인 필요)
cand['총개수_제품명추정'] = pd.to_numeric(cnt, errors='coerce')
cand['검색어'] = cand['식품명'] + ' ' + cand['제조사명'].fillna('')
for col in ['판매가격(원)', '총개수', '판매처', 'URL', '조사일', '비고']:
    cand[col] = ''
if PRICE_FILE.exists():
    old = read_price_file(PRICE_FILE)
    if '1회분량중량' not in old.columns:                      # 예전 형식 파일이면 1회분량중량 채워 넣기
        old['1회분량중량'] = old['식품코드'].map(p.drop_duplicates('식품코드').set_index('식품코드')['영양성분제공단위량'])
    add = cand[~cand['식품코드'].isin(old['식품코드'])]
    write_price_file(pd.concat([old, add.sort_values(['제품유형명', '식품명'])], ignore_index=True), PRICE_FILE)
    print('가격 조사 대상: 기존', len(old), '개 + 새 후보', len(add), '개 →', PRICE_FILE.name)
else:
    write_price_file(cand.sort_values(['제품유형명', '식품명']), PRICE_FILE)
    print('가격 조사 대상', len(cand), '개 →', PRICE_FILE.name)
rec.to_csv(OUT / '추천_군집별.csv', index=False, encoding='utf-8-sig')
pd.DataFrame(match_rows).to_csv(OUT / '군집x제품유형_매칭.csv', index=False, encoding='utf-8-sig')
web_out = {'_meta': {'유형키': 'Micro_Cluster 번호 (api_response_schema의 lifestyle_cluster.cluster_id)',
                     '안전_함유_기준': SAFETY_BASIS,
                     '안전규칙': {'kidney_disease_or_stones': ['calcium', 'potassium', 'phosphorus'],
                               'anticoagulant_or_aspirin': ['omega3', 'vitamin_k'],
                               'pregnant_or_breastfeeding': '추천 중단'}}, **web}
(OUT / 'recommendations.json').write_text(json.dumps(web_out, ensure_ascii=False, indent=1, default=str), encoding='utf-8')

# %% 변별력 점검: 군집 간 추천 겹침(Jaccard). 공통주의만 있는 군집은 원래 같으므로 유형특이 군집끼리도 따로
spec_cl = [c for c in combo.index if not combo.loc[c, '유형특이조합'].startswith('(')]
div = []
for g, s in rec.groupby('장르'):
    sets = {c: set(x['식품명']) for c, x in s.groupby('cluster')}
    jac = lambda cs: np.mean([len(sets[a] & sets[b]) / len(sets[a] | sets[b]) for a, b in itertools.combinations(cs, 2)])
    div.append(dict(장르=g, 서로다른제품=s['식품명'].nunique(), 칸수=len(s), 평균겹침_전체=jac(list(sets)),
                    평균겹침_유형특이군집=jac([c for c in spec_cl if c in sets]), 최다등장=s['식품명'].value_counts().iat[0]))
div = pd.DataFrame(div)
div.to_csv(OUT / '추천_변별력.csv', index=False, encoding='utf-8-sig')

pd.set_option('display.width', 250); pd.set_option('display.max_colwidth', 70)
print('공통 주의:', COMMON, '| 가격 열:', has_price)
print('필터로 빠지는 제품: 식사대용', int(p['식사대용'].sum()), '| 키즈·임산부', int(p['대상_제외'].sum()),
      '| 여성용', int(p['대상_여성'].sum()), '| 남성용', int(p['대상_남성'].sum()), '| 실버', int(p['대상_실버'].sum()))
print(pd.DataFrame(match_rows).to_string(index=False))
print(div.round(2).to_string(index=False))

# %% 안전 표시 개수: 전체 후보 제품 / 추천된 제품(군집×장르 칸 기준)
print('\n[안전 함유 표시] 전체 제품', len(p), '개 중:', {k: int(p[f'safety_{k}'].sum()) for k in SAFETY})
rec['안전_함유'] = rec['안전_함유'].apply(lambda x: x if isinstance(x, list) else [])
print(pd.DataFrame({k: rec.groupby('cluster')['안전_함유'].apply(lambda s: sum(k in x for x in s)) for k in SAFETY})
      .assign(추천칸=rec.groupby('cluster').size()).to_string())
