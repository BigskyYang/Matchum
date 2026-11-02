# %% [markdown]
# # B군(티아민·리보플라빈) 추천 검증: 준혁님 Top 5 vs 우리 방식 수정 전(v4) vs 수정 후(v5)
# 상황 가정: 필요 영양소 = 티아민(B1) + 리보플라빈(B2) (군집과 무관하게 B군만 보는 실험)
# - 수정 전(v4): 함량만 봄 (B1·B2 커버율 + 불필요 성분 감점), 목적·종합형 구분 없음
# - 수정 후(v5): + 이름에 B군이 적힌 제품 가산 + 목적 일치(기능성 원료 제품은 이름에 B군이 있을 때만) + 종합형 따로 + 충분함량(한 성분 이상 기준치 100%↑)
# 공통: UL 초과·단위오류 의심 제외, 핵심 성분 중 30% 미만 섞인 제품 제외, 제조사·제품명 중복 없이 5개

# %%
from pathlib import Path
import re
import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent / 'output'
p = pd.read_csv(OUT / 'product_features.csv', encoding='utf-8-sig')
p = p[p['대상제품'] == 1].reset_index(drop=True)
p['주목적_기능성'] = p['주목적_기능성'].fillna('')
V = [c for c in p.columns if c.startswith('v_')]
CORE = ['티아민', '리보플라빈']
cov = pd.DataFrame({k: np.minimum(p[f'v_{k}'] / 100, 1) for k in CORE})
core_cov = cov.sum(axis=1)
extra = (p[V] > 0).sum(axis=1) - (cov > 0).sum(axis=1)
score = core_cov - 0.05 * extra
named = p[[f'name_{k}' for k in CORE]].max(axis=1)
score_v5 = score + 0.5 * named          # v5: 이름에 B군이 적힌 제품 우선
base = (p['UL초과'] == 0) & (core_cov > 0) & ~((p[[f'v_{k}' for k in CORE]] > 0) & (p[[f'v_{k}' for k in CORE]] < 30)).any(axis=1)


def norm(s):
    return re.sub(r'[\(\[].*?[\)\]]|\d+\s*(정|캡슐|포|ml|mg|g|개|병)|\s', '', str(s))[:12]


def top5(mask, sc):
    d = p[mask].assign(score=sc[mask]).sort_values('score', ascending=False)
    out, sm, sn = [], set(), set()
    for _, r in d.iterrows():
        if r['제조사명'] in sm or norm(r['식품명']) in sn:
            continue
        out.append(r); sm.add(r['제조사명']); sn.add(norm(r['식품명']))
        if len(out) == 5:
            break
    return pd.DataFrame(out)


purpose = pd.Series(False, index=p.index)
for k in CORE:
    purpose |= (cov[k] > 0) & (p[f'목적일치_{k}'] == 1)
full = (p[[f'v_{k}' for k in CORE]] >= 100).any(axis=1)
v4 = top5(base, score)
v5_suff = top5(base & purpose & (p['종합형'] == 0) & full, score_v5)
v5_conv = top5(base & purpose & (p['종합형'] == 0) & p['1일개수'].eq(1) & p['n_day'].eq(1), score_v5)
v5_multi = top5((p['UL초과'] == 0) & (p['종합형'] == 1) & (core_cov > 0), core_cov)

JH = ['닥터하이 365 판토하이 비오틴 부스터', '유한m 리버클린400', '유한m 가넨헤파', '유한m 면역앤 프로폴리스 아연 플러스', '유한m 굿라이프 파워맨']
jh = p[p['식품명'].isin(JH)].drop_duplicates('식품명').set_index('식품명').loc[JH].reset_index()

COLS = ['식품명', '제조사명', 'pct_티아민', 'pct_리보플라빈', '구성성분수', '1일개수', '주목적_기능성', '대표식품명']


def show(title, d):
    d = d[COLS].copy()
    d['B군 이름'] = d['식품명'].str.contains(r'비타민\s?B|B\s?컴플렉스|비컴플렉스|활성\s?비타민|벤포|B군', regex=True).map({True: 'O', False: ''})
    d[['pct_티아민', 'pct_리보플라빈']] = d[['pct_티아민', 'pct_리보플라빈']].round(0)
    d['주목적_기능성'] = d['주목적_기능성'].replace('', '비타민·미네랄')
    print(f'\n## {title}'); print(d.rename(columns={'pct_티아민': 'B1%', 'pct_리보플라빈': 'B2%'}).to_string(index=False))
    return d


res = {}
for title, d in [('① 준혁님 3차 필터링 Top 5', jh), ('② 우리 방식 수정 전(v4, 함량 기준)', v4),
                 ('③ 수정 후(v5) 충분함량형', v5_suff), ('④ 수정 후(v5) 편의형(1일 1회 1개)', v5_conv), ('⑤ 수정 후(v5) 종합형', v5_multi)]:
    res[title] = show(title, d)

summary = pd.DataFrame({t: {'B군 이름 제품': int((d['B군 이름'] == 'O').sum()),
                            '기능성 주목적(간·면역 등)': int((~d['주목적_기능성'].isin(['비타민·미네랄'])).sum())}
                        for t, d in res.items()}).T
print('\n## 요약 (5개 중)'); print(summary.to_string())
pd.concat({t: d for t, d in res.items()}).to_csv(OUT / 'B군_검증.csv', encoding='utf-8-sig')
