# %% [markdown]
# # [B-3 보완] 유형별 섭취량이 평균보다 얼마나 적은가 (대천님 요청, 11/3)
# 요청: (가)안을 쓰되, 그 유형의 섭취량이 평균보다 떨어지는 영양소가 있으면 "평균에서 떨어진 거리"를 알려주기
#
# 방법 (결과 보기 전에 확정)
# - 거리 = 같은 성별·연령대끼리 비교한 섭취량 % 차이: 가중 회귀 log(섭취량) ~ 이유형여부 + 성별 + 연령대
#   → (exp(계수) − 1) × 100 = "같은 성별·나이의 다른 유형 사람보다 몇 % 더/덜 먹는가" (기하평균 기준)
#   섭취량 0(비타민D 등)은 log를 못 하므로 전체 중앙값의 1%를 더함
# - 판정 '평균보다 적음': 95% CI 상한 < 0 그리고 BH-FDR q < 0.05 (12유형 × 16항목)
# - 참고: 유형 섭취량 중앙값이 본인 기준(EAR/AI)의 몇 %인지 (가중 중앙값), 에너지(kcal)도 함께 → 덜 먹어서 생긴 차이인지
# - 섭취량은 음식만(영양제 미포함), 하루 24시간 회상

# %%
import json
import warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
import matplotlib.pyplot as plt
import seaborn as sns
from common import *

warnings.filterwarnings('ignore')
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

NB = json.load(open(ROOT.parents[1]
                    / 'analysis' / '01_clustering' / 'validation' / 'output' / 'nbti_12types.json', encoding='utf-8'))
NAME = {t['id']: t['name'] for t in NB['types']}
IDS = list(NAME)
d = add_status(load_persons(ROOT / 'KMedoids_12Types_N1O3.csv', 'Type'))    # 08번이 만든 N1~O3 배정
d['age_grp_s'] = d['age_grp'].astype(str)
COLS = {'에너지': '영양_N_EN'} | {n: KDRI[n][0] for n in NUTRIENTS}
UNIT = {'에너지': 'kcal'}
X_base = pd.get_dummies(d[['sex', 'age_grp_s']], drop_first=True).astype(float)


def wmedian(x, w):
    o = np.argsort(x.values)
    cw = np.cumsum(w.values[o])
    return float(x.values[o][np.searchsorted(cw, cw[-1] / 2)])


rows = []
for n, col in COLS.items():
    x = d[col]
    y = np.log(x + 0.01 * wmedian(x, d['w']))
    ratio = d[f'ratio_{n}'] if n in KDRI else None
    for c in IDS:
        inc = (d['cluster'] == c).astype(float).rename('inc')
        fit = sm.WLS(y, sm.add_constant(pd.concat([inc, X_base], axis=1)), weights=d['w']).fit(cov_type='HC1')
        b, (lo, hi), p = fit.params['inc'], fit.conf_int().loc['inc'], fit.pvalues['inc']
        m = d['cluster'] == c
        rows.append(dict(유형=c, 이름=NAME[c], 항목=n, n=int(m.sum()),
                         평균대비pct=(np.exp(b) - 1) * 100, CI_low=(np.exp(lo) - 1) * 100, CI_high=(np.exp(hi) - 1) * 100, p=p,
                         유형_중앙값=wmedian(x[m], d.loc[m, 'w']), 전체_중앙값=wmedian(x, d['w']),
                         유형_기준대비중앙값pct=wmedian(ratio[m], d.loc[m, 'w']) * 100 if ratio is not None else np.nan,
                         전체_기준대비중앙값pct=wmedian(ratio, d['w']) * 100 if ratio is not None else np.nan))
res = pd.DataFrame(rows)
res['q'] = multipletests(res['p'], method='fdr_bh')[1]
res['판정'] = np.select([(res['CI_high'] < 0) & (res['q'] < 0.05), (res['CI_low'] > 0) & (res['q'] < 0.05)],
                        ['평균보다 적음', '평균보다 많음'], '차이 없음')
res.to_csv(OUT / '11_유형별_섭취량_평균대비.csv', index=False, encoding='utf-8-sig')

# 에너지보다 더 적은가: 영양소 % 차이 − 에너지 % 차이 (같은 유형). 음수면 '덜 먹는 것 이상으로' 적음
en = res[res['항목'] == '에너지'].set_index('유형')['평균대비pct']
res['에너지보다_더적음pp'] = res['평균대비pct'] - res['유형'].map(en)

# 웹 JSON: 유형별로 '평균보다 적음' 판정만 (적게 먹는 순)
web = {'설명': '같은 성별·나이대의 다른 유형 사람과 비교한 하루 섭취량 차이(%, 기하평균). 음식만, 하루 24시간 회상 기준. '
               '95% 신뢰구간과 다중검정 보정 후에도 적은 것만 표시. 진단이 아닙니다.', 'types': {}}
for c in IDS:
    g = res[(res['유형'] == c)]
    low = g[(g['판정'] == '평균보다 적음') & (g['항목'] != '에너지')].sort_values('평균대비pct')
    e = g[g['항목'] == '에너지'].iloc[0]
    web['types'][c] = dict(
        name=NAME[c],
        energy=dict(pct=round(e['평균대비pct'], 1), 판정=e['판정']),
        lower_than_average=[dict(nutrient=r.항목, pct=round(r.평균대비pct, 1), ci=[round(r.CI_low, 1), round(r.CI_high, 1)],
                                 text=f"같은 성별·나이 평균보다 {abs(r.평균대비pct):.0f}% 적게 먹어요",
                                 type_median_pct_of_ref=round(r.유형_기준대비중앙값pct), all_median_pct_of_ref=round(r.전체_기준대비중앙값pct))
                            for r in low.itertuples()])
with open(OUT / '11_유형별_섭취량_평균대비.json', 'w', encoding='utf-8') as fp:
    json.dump(web, fp, ensure_ascii=False, indent=1)

# %% 출력
pd.set_option('display.width', 250)
piv = res.pivot(index='유형', columns='항목', values='평균대비pct').loc[IDS, list(COLS)]
mk = res.assign(m=res['판정'].map({'평균보다 적음': '▼', '평균보다 많음': '▲'}).fillna('')).pivot(
    index='유형', columns='항목', values='m').loc[IDS, list(COLS)]
print('[같은 성별·나이 대비 섭취량 % 차이 (▼ 유의하게 적음, ▲ 많음)]')
print((piv.round(0).astype(int).astype(str) + mk).to_string())
print('\n[유형별 "평균보다 적음" 영양소 (에너지 제외), 적은 순]')
for c in IDS:
    w_ = web['types'][c]
    s = ', '.join(f"{x['nutrient']} {x['pct']:+.0f}%" for x in w_['lower_than_average']) or '없음'
    print(f"{c} {NAME[c]:16s} 에너지 {w_['energy']['pct']:+.0f}% ({w_['energy']['판정']}) | {s}")

fig, ax = plt.subplots(figsize=(15, 7))
sns.heatmap(piv, center=0, cmap='RdBu', annot=piv.round(0).astype(int).astype(str) + mk, fmt='',
            yticklabels=[f'{c} {NAME[c]}' for c in IDS], cbar_kws={'label': '같은 성별·나이 대비 섭취량 차이 (%)'}, ax=ax)
ax.set_title('유형별 하루 섭취량: 같은 성별·나이 대비 % 차이 (▼ 유의하게 적음 / ▲ 많음, BH-FDR q<0.05)')
plt.tight_layout(); plt.savefig(OUT / 'fig_11_유형별_섭취량_평균대비.png', dpi=150)
print('\n저장:', OUT)
