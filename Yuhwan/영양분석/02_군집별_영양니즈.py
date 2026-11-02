# %% [markdown]
# # [B] 고객 군집별 영양 니즈 (흡수율 반영)
# 군집 파일만 바꾸면 그대로 재실행: CLUSTER_FILE, LABEL_COL
#
# 판정 (결과 보기 전에 확정, CLAUDE.md 4절)
# - 사람마다 본인 성별·연령의 2025 KDRI와 비교: EAR 미만 = 부족 위험 / AI 미만 = 참고지표
# - 유형 특이: 성별·연령 보정 오즈비 ≥ 1.2 그리고 p < 0.05 그리고 민감도(N_DUSUAL==2)에서도 OR > 1
# - 공통 주의: 전체 가중 미달률 ≥ 50%
# - 해당 없음: 나머지
#
# 흡수율 반영 방식
# 1) EAR 자체에 식이 흡수율이 들어 있음 (철 16/18%, 아연 40%, 칼슘 37~43%, 엽산 DFE) → 섭취량 그대로 비교
# 2) 생활습관 흡수 영향(KDRI 정성 근거): 음주 → 티아민 흡수 저해, 마그네슘 배설 증가
#    → 음주율이 전체보다 높은 군집에서 두 영양소에 '흡수주의' 표시, 우선순위 동점 시 앞으로
#    흡연 → 비타민C는 KDRI가 '근거 불충분'이라 적용 안 함
# 3) 영양소 간 상호작용(비타민D→칼슘, 비타민C→철 등)은 03_영양소조합 에서 조합 규칙으로 사용

# %%
import warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import seaborn as sns
from common import *

warnings.filterwarnings('ignore')
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

CLUSTER_FILE = ROOT / 'KMeans_Final_MicroClustered.xlsx'
LABEL_COL = 'Sub_Cluster'
OR_CUT, RATE_CUT, SMALL_N = 1.2, 0.50, 100

d = add_status(load_persons(CLUSTER_FILE, LABEL_COL))
clusters = sorted(d['cluster'].unique())
print('사람', len(d), '| 군집', len(clusters))

# %% 성별·연령 보정 오즈비: below ~ 이군집여부 + 성별 + 연령대 (군집 vs 나머지 전체)
X_base = pd.get_dummies(d[['sex', 'age_grp']].astype(str), drop_first=True).astype(float)
# 에너지까지 보정: 유형특이가 이걸로 사라지면 '덜 먹어서' 부족(식사량형), 남으면 '식단 구성' 때문(구성형)
X_energy = X_base.assign(logE=np.log1p(d['영양_N_EN']))


def adj_or(sub, y, inc, Xc=X_base):
    X = sm.add_constant(pd.concat([inc.rename('inc'), Xc], axis=1).loc[sub.index])
    fit = sm.Logit(y.loc[sub.index], X).fit(disp=0)
    return np.exp(fit.params['inc']), fit.pvalues['inc'], np.exp(fit.conf_int().loc['inc']).values


usual = d['식이상태_N_DUSUAL'] == 2
rows = []
for n in NUTRIENTS:
    y = d[f'below_{n}']
    overall = np.average(y, weights=d['w'])
    for c in clusters:
        inc = (d['cluster'] == c).astype(float)
        m = inc == 1
        o, p, ci = adj_or(d, y, inc)
        o_s, p_s, _ = adj_or(d[usual], y, inc)
        o_e, p_e, _ = adj_or(d, y, inc, X_energy)
        rows.append(dict(cluster=c, 영양소=n, 기준=KDRI[n][1], n=int(m.sum()),
                         미달률=np.average(y[m], weights=d.loc[m, 'w']), 전체미달률=overall,
                         보정OR=o, p=p, CI_low=ci[0], CI_high=ci[1], 민감도OR=o_s, 에너지보정OR=o_e))
res = pd.DataFrame(rows)
res['차이pp'] = (res['미달률'] - res['전체미달률']) * 100

# %% 등급
res['유형특이'] = (res['보정OR'] >= OR_CUT) & (res['p'] < 0.05) & (res['민감도OR'] > 1)
res['공통주의'] = res['전체미달률'] >= RATE_CUT
res['등급'] = np.select([res['유형특이'], res['공통주의']], ['유형특이', '공통주의'], '해당없음')
res['표본적음'] = res['n'] < SMALL_N
res['원인'] = np.where(~res['유형특이'], '',
                     np.where(res['에너지보정OR'] >= OR_CUT, '구성형', '식사량형'))

# %% 흡수 영향 표시: 음주율(ML_drink_month 가중평균)이 전체보다 높은 군집 → 티아민·마그네슘
drink = d.groupby('cluster').apply(lambda g: np.average(g['ML_drink_month'], weights=g['w']))
drink_all = np.average(d['ML_drink_month'], weights=d['w'])
alc_nut = LIFESTYLE_ABSORPTION.query('생활습관=="음주" and 적용')['영양소'].tolist()
res['흡수주의'] = res.apply(lambda r: '음주' if (r['영양소'] in alc_nut and drink[r['cluster']] > drink_all) else '', axis=1)

# %% 군집별 우선 영양소: 유형특이(OR 큰 순) → 공통주의(미달률 큰 순), 흡수주의는 같은 등급 안에서 앞으로
res['정렬'] = np.select([res['등급'] == '유형특이', res['등급'] == '공통주의'], [0, 1], 2)
res = res.sort_values(['cluster', '정렬', '흡수주의', '보정OR'], ascending=[True, True, False, False])
res['순위'] = res.groupby('cluster').cumcount() + 1
res.to_csv(OUT / '군집별_영양니즈_long.csv', index=False, encoding='utf-8-sig')

prof = (d.groupby('cluster').apply(lambda g: pd.Series({
            'n': len(g), '평균나이': g['age'].mean(), '남성비율': (g['sex'] == '남자').mean(),
            '음주율': np.average(g['ML_drink_month'], weights=g['w']),
            '흡연율': np.average(g['ML_smoker'], weights=g['w'])})))
top = (res[res['등급'] == '유형특이'].groupby('cluster')
          .apply(lambda g: ', '.join(f"{r.영양소}({r.보정OR:.2f}{'·'+r.흡수주의 if r.흡수주의 else ''})" for r in g.itertuples())))
prof['유형특이 영양소'] = top
prof['식사량형 비율'] = res[res['유형특이']].groupby('cluster')['원인'].apply(lambda s: (s == '식사량형').mean())
prof['에너지섭취'] = d.groupby('cluster').apply(lambda g: np.average(g['영양_N_EN'], weights=g['w']))
# 오메가3 참고용 대리지표: 조사일 생선 섭취 0g 비율 (하루 기록이라 개인 판단 불가, 군집 비교만)
prof['생선0g비율'] = d.groupby('cluster').apply(lambda g: np.average(g['보조_FISH_G'] == 0, weights=g['w']))
print('전체 생선0g비율', round(np.average(d['보조_FISH_G'] == 0, weights=d['w']), 3))
prof['표본적음'] = prof['n'] < SMALL_N
prof.to_csv(OUT / '군집_요약.csv', encoding='utf-8-sig')

# %% 출력
print('\n[전체 가중 미달률] (EAR=부족 위험, AI=참고)')
print(res.drop_duplicates('영양소').set_index('영양소')[['기준', '전체미달률']]
      .assign(전체미달률=lambda x: (x['전체미달률'] * 100).round(1)).to_string())
print('\n[군집 요약]')
print(prof.round(2).to_string())

# %% 그림: 보정 오즈비 히트맵 (★ 유형특이)
piv = res.pivot(index='cluster', columns='영양소', values='보정OR')[NUTRIENTS]
mark = res.pivot(index='cluster', columns='영양소', values='유형특이')[NUTRIENTS]
annot = piv.round(2).astype(str) + np.where(mark, '★', '')
fig, ax = plt.subplots(figsize=(14, 0.5 * len(clusters) + 2))
sns.heatmap(np.log2(piv), center=0, cmap='RdBu_r', annot=annot, fmt='', cbar_kws={'label': 'log2(보정 OR)'}, ax=ax)
ax.set_title('군집별 부족 위험 보정 오즈비 (성별·연령 보정, ★ = 유형 특이)')
plt.tight_layout(); plt.savefig(OUT / 'fig_군집x영양소_보정OR.png', dpi=150)
print('\n저장:', OUT)
