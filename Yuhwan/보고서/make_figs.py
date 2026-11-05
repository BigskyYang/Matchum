# 최종 보고서용 그림·표 계산 (군집화 + 유형별 부족 영양소 파트)
# 입력: 영양분석/output 의 08·09·10·13 결과, KMedoids_12Types_N1O3.csv(개인 단위, git 제외)
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.patches import FancyBboxPatch
from statsmodels.stats.outliers_influence import variance_inflation_factor

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / '영양분석'))
from common import *  # noqa

FIG = HERE / 'fig'; FIG.mkdir(exist_ok=True)
plt.rcParams.update({'font.family': 'Malgun Gothic', 'axes.unicode_minus': False, 'font.size': 10,
                     'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.edgecolor': '#8a8984', 'axes.labelcolor': '#0b0b0b', 'xtick.color': '#52514e',
                     'ytick.color': '#52514e', 'figure.facecolor': '#fcfcfb', 'axes.facecolor': '#fcfcfb',
                     'savefig.facecolor': '#fcfcfb', 'grid.color': '#e4e3df', 'grid.linewidth': 0.8})
# 보고서 색: 짙은 청록(주색) + 연한 청록 + 황토(강조), 나머지는 회색
BLUE, ORANGE, AQUA, GRAY, INK, INK2 = '#2c6e6a', '#b9773a', '#8bb5b0', '#c4c2bb', '#0b0b0b', '#52514e'
TEAL_L = '#dcebe8'
DIV = LinearSegmentedColormap.from_list('div', ['#1f4f4c', '#8bb5b0', '#f4f1ea', '#d9a86c', '#9c5b26'])
NAMES = {'N1': '집밥좋아 나무늘보', 'N2': '배고픈 나무늘보', 'N3': '배부른 나무늘보', 'A1': '뚜벅이 갓생러',
         'A2': '파워 갓생러', 'A3': '밸런스 갓생러', 'S1': '쉬고 싶은 예민보스', 'S2': '산책하는 예민보스',
         'S3': '쇠질하는 예민보스', 'O1': '아침패스 워커홀릭', 'O2': '삼시세끼 워커홀릭', 'O3': '운동하는 워커홀릭'}
IDS = list(NAMES)
COMMON = ['비타민A', '비타민D', '비타민E', '비타민C', '엽산', '칼슘', '칼륨', '식이섬유']
OUT8 = ROOT / '영양분석' / 'output'
S = {}


def save(fig, name):
    fig.savefig(FIG / name, dpi=200, bbox_inches='tight'); plt.close(fig)


# ── 데이터 ──
d = add_status(load_persons(ROOT / 'KMedoids_12Types_N1O3.csv', 'Type'))
w = d['w']
S['n'] = len(d)
S['n_year'] = d['year'].value_counts().sort_index().to_dict()
S['male_pct'] = float(np.average(d['sex'] == '남자', weights=w) * 100)
S['age_mean'] = float(np.average(d['age'], weights=w))

# 그림 1. 영양소별 부족률 (가중, 2022–2024)
rate = pd.Series({n: np.average(d[f'below_{n}'], weights=w) * 100 for n in NUTRIENTS}).sort_values()
S['rate'] = rate.round(1).to_dict()
fig, ax = plt.subplots(figsize=(8, 5.2))
cols = [BLUE if KDRI[n][1] == 'EAR' else ORANGE for n in rate.index]
ax.barh(rate.index, rate.values, color=cols, height=0.62)
for i, v in enumerate(rate.values):
    ax.text(v + 1, i, f'{v:.1f}%', va='center', fontsize=9, color=INK, zorder=4, bbox=dict(fc='#fcfcfb', ec='none', pad=0.6))
ax.axvline(50, color=INK2, lw=1, ls='--', zorder=0); ax.text(50.5, -0.9, '50%', color=INK2, fontsize=8)
ax.set_xlim(0, 108); ax.set_xlabel('기준 미만 비율 (%, 조사 가중)')
ax.grid(axis='x'); ax.set_axisbelow(True)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=BLUE, label='평균필요량(EAR) 미만 = 부족 위험'), Patch(color=ORANGE, label='충분섭취량(AI) 미만 = 참고')],
          loc='lower right', frameon=False, fontsize=9)
save(fig, 'f01_부족률.png')

# 연령대별 부족 영양소 개수 (EAR 11개 중)
S['ear_cnt_by_age'] = {a: round(float(np.average(g['부족개수_EAR'], weights=g['w'])), 2)
                       for a, g in d.groupby('age_grp', observed=True)}
S['ear_cnt_by_sex'] = {s: round(float(np.average(g['부족개수_EAR'], weights=g['w'])), 2) for s, g in d.groupby('sex')}

# 생활습관 기술통계 + 상관 + VIF
LS = {'ML_aerobic': '유산소 실천(0/1)', 'ML_strength_days': '근력운동(일/주)', 'ML_sedentary_min': '좌식 시간(분/일)',
      'ML_sleep_hours': '수면(시간/일)', 'ML_stress': '스트레스 인지(0/1)', 'ML_breakfast_freq_ord': '아침 빈도(0~3)',
      'ML_lunch_freq_ord': '점심 빈도(0~3)', 'ML_dinner_freq_ord': '저녁 빈도(0~3)', 'ML_eatingout_freq_ord': '외식 빈도(0~6)',
      'ML_smoker': '현재 흡연(0/1)', 'ML_cigarettes_day': '하루 흡연량(개비)', 'ML_drink_month': '월 음주(0/1)',
      'ML_drink_freq_ord': '음주 빈도(0~5)', 'ML_drink_amount_ord': '1회 음주량(0~5)'}
X = d[list(LS)]
from scipy.stats import skew, kurtosis
desc = pd.DataFrame({'변수': list(LS.values()),
                     '가중 평균': [np.average(X[c], weights=w) for c in LS],
                     '표준편차': [np.sqrt(np.average((X[c] - np.average(X[c], weights=w)) ** 2, weights=w)) for c in LS],
                     '최소': [X[c].min() for c in LS], 'Q1': [X[c].quantile(0.25) for c in LS],
                     '중앙값': [X[c].median() for c in LS], 'Q3': [X[c].quantile(0.75) for c in LS], '최대': [X[c].max() for c in LS],
                     '왜도': [skew(X[c]) for c in LS], '첨도': [kurtosis(X[c]) for c in LS]})
desc.round(2).to_csv(FIG / 't_생활습관_기술통계.csv', index=False, encoding='utf-8-sig')
corr = X.rename(columns=LS).corr(method='spearman')
fig, ax = plt.subplots(figsize=(8.6, 7.2))
im = ax.imshow(corr.values, cmap=DIV, vmin=-1, vmax=1)
ax.set_xticks(range(len(corr))); ax.set_xticklabels(corr.columns, rotation=60, ha='right', fontsize=8.5)
ax.set_yticks(range(len(corr))); ax.set_yticklabels(corr.index, fontsize=8.5)
for i in range(len(corr)):
    for j in range(len(corr)):
        v = corr.values[i, j]
        if i != j and abs(v) >= 0.3:
            ax.text(j, i, f'{v:.2f}', ha='center', va='center', fontsize=7.5, color='white' if abs(v) > 0.6 else INK)
ax.spines[:].set_visible(False)
cb = fig.colorbar(im, ax=ax, shrink=0.75); cb.set_label('스피어만 상관계수'); cb.outline.set_visible(False)
save(fig, 'f02_상관.png')
up = corr.where(np.triu(np.ones(corr.shape, bool), 1)).stack().sort_values(key=abs, ascending=False)
S['top_corr'] = [(a, b, round(v, 2)) for (a, b), v in up.head(6).items()]
Z = (X - X.mean()) / X.std()
Z = Z.assign(const=1.0)
vif = pd.Series({LS[c]: variance_inflation_factor(Z.values, i) for i, c in enumerate(LS)}).sort_values(ascending=False)
S['vif'] = vif.round(2).to_dict()

# 그림 3. 유형 × 영양소: 같은 성별·연령대 대비 배수 (10칸 평균)
P = pd.read_csv(OUT8 / '08_유형성별연령_부족확률.csv', encoding='utf-8-sig')
order_n = [n for n in NUTRIENTS if n not in COMMON] + COMMON
H = P.groupby(['유형', '영양소'])['배수'].mean().unstack().loc[IDS, order_n]
fig, ax = plt.subplots(figsize=(10, 5.6))
im = ax.imshow(H.values, cmap=DIV, norm=TwoSlopeNorm(1, 0.6, 1.4), aspect='auto')
ax.set_xticks(range(H.shape[1])); ax.set_xticklabels(H.columns, rotation=45, ha='right')
ax.set_yticks(range(12)); ax.set_yticklabels([f'{k} {NAMES[k]}' for k in IDS])
for i in range(H.shape[0]):
    for j in range(H.shape[1]):
        v = H.values[i, j]
        ax.text(j, i, f'{v:.2f}', ha='center', va='center', fontsize=7.5, color='white' if abs(v - 1) > 0.28 else INK)
ax.axvline(len(order_n) - len(COMMON) - 0.5, color=INK, lw=1.5)
ax.text(len(order_n) - len(COMMON) - 0.4, -0.9, '← 그 밖의 영양소 | 공통 주의 영양소 →', fontsize=8.5, color=INK2, ha='center')
ax.spines[:].set_visible(False)
cb = fig.colorbar(im, ax=ax, shrink=0.8); cb.set_label('같은 성별·연령대 평균 대비 부족 확률 배수'); cb.outline.set_visible(False)
save(fig, 'f05_유형x영양소_배수.png')

# 그림 4. ΔAUC forest
V = pd.read_csv(OUT8 / '08_2024검증.csv', encoding='utf-8-sig').sort_values('ΔAUC')
fig, ax = plt.subplots(figsize=(7.6, 5.4))
y = np.arange(len(V))
sig = V['ΔAUC_CI_low'] > 0
ax.hlines(y, V['ΔAUC_CI_low'], V['ΔAUC_CI_high'], color=np.where(sig, BLUE, GRAY), lw=2)
ax.scatter(V['ΔAUC'], y, s=46, color=np.where(sig, BLUE, GRAY), zorder=3, edgecolor='#fcfcfb', linewidth=1.5)
ax.axvline(0, color=INK2, lw=1)
ax.set_yticks(y); ax.set_yticklabels(V['영양소'])
ax.set_xlabel('AUC 향상 (유형 추가 모델 - 성별·연령 모델), 2024년 평가')
for yi, (v, s_) in enumerate(zip(V['ΔAUC'], sig)):
    ax.text(V['ΔAUC_CI_high'].iloc[yi] + 0.002, yi, f'{v:+.3f}', va='center', fontsize=8.5, color=INK if s_ else INK2)
ax.legend(handles=[plt.Line2D([], [], color=BLUE, marker='o', lw=2, label='95% CI가 0보다 큼 (13개)'),
                   plt.Line2D([], [], color=GRAY, marker='o', lw=2, label='유의하지 않음 (2개)')],
          loc='lower right', frameon=False, fontsize=9)
ax.grid(axis='x'); ax.set_axisbelow(True)
save(fig, 'f06_ΔAUC.png')
S['auc'] = dict(test_min=round(V['Test_AUC'].min(), 3), test_max=round(V['Test_AUC'].max(), 3),
               m0_min=round(V['M0_Test_AUC'].min(), 3), m0_max=round(V['M0_Test_AUC'].max(), 3),
               over_max=round(V['과적합(Train−Test)'].max(), 3), brier_max=round(V['Test_Brier'].max(), 3))

# 그림 5. 피처·모델 비교 (영양소 15개 평균 Test AUC)
F = pd.read_csv(OUT8 / '10_피처모델_영양소별.csv', encoding='utf-8-sig')
FM = F.groupby(['피처', '모델'])[['CV_AUC', 'Test_AUC', 'CV로그손실']].mean().round(4)
S['feat'] = {f'{a}_{b}': r.to_dict() for (a, b), r in FM.iterrows()}
fig, ax = plt.subplots(figsize=(7.6, 4.2))
FL = {'F0': '유형+성별+연령대\n(최종 채택)', 'F1': '+ 나이 곡선·\n유형×성별', 'F2': '+ 생활습관\n응답 14개', 'F3': '+ 채소·과일\n섭취 빈도'}
MC = {'LR': (BLUE, '로지스틱 회귀'), 'HGB': (ORANGE, '그래디언트 부스팅'), 'ENS': (AQUA, '앙상블(평균)')}
xb = np.arange(4)
for k, (m, (c, lab)) in enumerate(MC.items()):
    vals = [FM.loc[(f, m), 'Test_AUC'] for f in FL]
    ax.bar(xb + (k - 1) * 0.26, vals, width=0.24, color=c, label=lab)
ax.set_xticks(xb); ax.set_xticklabels(FL.values(), fontsize=9)
ax.set_ylim(0.6, 0.68); ax.set_ylabel('2024 평가 AUC (영양소 15개 평균)')
ax.legend(frameon=False, ncol=3, loc='upper left', fontsize=9); ax.grid(axis='y'); ax.set_axisbelow(True)
save(fig, 'f07_피처모델.png')

# 표시 규칙 3안 비교 (최종 확률표, 120칸)
L = P.copy()
L['cell'] = L['유형'] + '|' + L['성별'] + '|' + L['연령대']
oth = L[~L['영양소'].isin(COMMON)]
ruleA = L[L['부족확률'] >= 0.5]
ruleB2 = oth[(oth['부족확률'] >= 0.5) | ((oth['배수'] >= 1.2) & (oth['부족확률'] >= 0.3))]
ruleC2 = oth.sort_values('부족확률', ascending=False).groupby('cell').head(3)


def lists(df):
    return df.groupby('cell')['영양소'].apply(lambda s: tuple(sorted(s))).reindex(L['cell'].unique(), fill_value=())


def within_sa(df):
    lst = lists(df).rename('lst').reset_index()
    lst[['유형', '성별', '연령대']] = lst['cell'].str.split('|', expand=True)
    return lst.groupby(['성별', '연령대'])['lst'].nunique().mean()


S['rules'] = {
    '확률 기준': dict(n=round(lists(ruleA).map(len).mean(), 1), kinds=lists(ruleA).nunique(), within=round(within_sa(ruleA), 1),
                    below1=int((ruleA['배수'] < 1).sum()), lowp=0),
    '2단 표시': dict(n=round(lists(ruleB2).map(len).mean(), 1), kinds=lists(ruleB2).nunique(), within=round(within_sa(ruleB2), 1),
                   below1=int((ruleB2['배수'] < 1).sum()), total=len(ruleB2), empty=int((lists(ruleB2).map(len) == 0).sum())),
    '상위 3개': dict(n=3.0, kinds=lists(ruleC2).nunique(), within=round(within_sa(ruleC2), 1),
                   below1=int((ruleC2['배수'] < 1).sum()), lowp=int((ruleC2['부족확률'] < 0.3).sum())),
}

# 그림 6. 2024 검증: 관측/기대 비 (문구별)
O = pd.read_csv(OUT8 / '13_나안_2024검증.csv', encoding='utf-8-sig')
O['판정'] = O['판정'].fillna('').replace('', '흔함')
rng = np.random.default_rng(42)


def oe_ci(g):
    b = [g.iloc[i]['O'].sum() / g.iloc[i]['E'].sum() for i in (rng.integers(0, len(g), len(g)) for _ in range(2000))]
    return g['O'].sum() / g['E'].sum(), *np.percentile(b, [2.5, 97.5]), len(g)


lab = {'유형특이': '이 유형에서\n특히 많아요', '식사량영향': '식사량 점검이\n먼저예요', '흔함': '같은 성별·나이대에서\n흔해요', '전체': '표시 항목\n전체'}
R = {k: oe_ci(O[O['판정'] == k]) for k in ['유형특이', '식사량영향', '흔함']} | {'전체': oe_ci(O)}
S['oe'] = {k: [round(x, 3) for x in v[:3]] + [v[3]] for k, v in R.items()}
fig, ax = plt.subplots(figsize=(7.4, 3.9))
ks = list(R)
ax.bar(range(4), [R[k][0] - 1 for k in ks], bottom=1, color=[BLUE, BLUE, BLUE, INK2], width=0.52)
ax.errorbar(range(4), [R[k][0] for k in ks], yerr=[[R[k][0] - R[k][1] for k in ks], [R[k][2] - R[k][0] for k in ks]],
            fmt='none', ecolor=INK, capsize=4, lw=1.2)
for i, k in enumerate(ks):
    ax.text(i, R[k][2] + 0.02, f'{R[k][0]:.2f}배\n(n={R[k][3]})', ha='center', fontsize=9)
ax.axhline(1, color=INK2, lw=1, ls='--'); ax.text(-0.42, 0.965, '1.0 = 같은 성별·나이 평균과 같음', fontsize=8, color=INK2, ha='left')
ax.set_xticks(range(4)); ax.set_xticklabels([lab[k] for k in ks], fontsize=9)
ax.set_ylim(0.9, 1.75); ax.set_ylabel('2024년 관측 ÷ 기대 부족 인원')
ax.grid(axis='y'); ax.set_axisbelow(True)
save(fig, 'f08_2024검증.png')

# 그림 2. 전체 분석 흐름 (도식)
fig, ax = plt.subplots(figsize=(10, 2.5)); ax.axis('off'); ax.set_xlim(0, 10); ax.set_ylim(0, 2.5)
steps = [('데이터 준비', 'KNHANES 2022–24\n성인 15,062명\nKDRI 2025 기준', TEAL_L),
         ('고객 군집화', '생활습관 7개 지표\nPCA → 2단계 k-medoids\n4 대분류 × 3 = 12유형', TEAL_L),
         ('부족 확률 예측', '유형+성별+연령대\n→ 영양소 15개\n가중 로지스틱 회귀', TEAL_L),
         ('검증', '2022–23 학습\n→ 2024 평가\n민감도 분석', TEAL_L),
         ('서비스 표시', '공통 영양소 +\n유형 영양소 2단 표시\n웹 JSON 120조합', TEAL_L)]
for i, (t, b, c) in enumerate(steps):
    x = 0.1 + i * 2
    ax.add_patch(FancyBboxPatch((x, 0.3), 1.75, 2.05, boxstyle='square,pad=0.02', fc=c, ec=AQUA, lw=0.8))
    ax.text(x + 0.875, 2.0, t, ha='center', va='center', fontsize=11, weight='bold', color=INK)
    ax.text(x + 0.875, 1.12, b, ha='center', va='center', fontsize=8.8, color=INK2, linespacing=1.5)
    if i < 4:
        ax.annotate('', xy=(x + 2.03, 1.3), xytext=(x + 1.8, 1.3), arrowprops=dict(arrowstyle='-|>', color=INK2, lw=1.4))
ax.text(1.95, 0.05, '비지도 학습', ha='center', fontsize=8.5, color=INK2)
ax.text(5.05, 0.05, '지도 학습', ha='center', fontsize=8.5, color=INK2)
save(fig, 'f03_분석흐름.png')

# 범주형 빈도와 12유형 교차표 (인원 + 조사 가중 비율)
S['freq'] = {c: {k: [int(len(g)), round(float(g['w'].sum() / w.sum() * 100), 1)] for k, g in d.groupby(c, observed=True)}
             for c in ['sex', 'age_grp']}
for c, fn in [('sex', 't_유형x성별.csv'), ('age_grp', 't_유형x연령대.csv')]:
    ct = d.pivot_table(index='cluster', columns=c, values='w', aggfunc='sum', observed=True).loc[IDS]
    (ct.div(ct.sum(axis=1), axis=0) * 100).round(1).to_csv(FIG / fn, encoding='utf-8-sig')

# 그림 9. 유형별 단백질·철 섭취량, 그림 10. 유형별 좌식 시간 (박스플롯, 비가중·보정 전)
TC = {'N': AQUA, 'A': AQUA, 'S': AQUA, 'O': AQUA}


def box(ax, col, ylab, ref=None):
    data = [d.loc[d['cluster'] == k, col].to_numpy() for k in IDS]
    bp = ax.boxplot(data, showfliers=False, patch_artist=True, widths=0.6, medianprops=dict(color=INK, lw=1.4))
    for patch, k in zip(bp['boxes'], IDS):
        patch.set_facecolor(TC[k[0]]); patch.set_edgecolor(INK2)
    ax.scatter(range(1, 13), [np.average(d.loc[d['cluster'] == k, col], weights=d.loc[d['cluster'] == k, 'w']) for k in IDS],
               marker='D', s=18, color=INK, zorder=3, label='가중 평균')
    ax.set_xticks(range(1, 13)); ax.set_xticklabels(IDS); ax.set_ylabel(ylab); ax.grid(axis='y'); ax.set_axisbelow(True)
    for xv in (3.5, 6.5, 9.5):      # 대분류(N·A·S·O) 경계
        ax.axvline(xv, color=GRAY, lw=0.8)
    if ref:
        ax.axhline(ref[0], color=ORANGE, lw=1, ls='--'); ax.text(12.6, ref[0], ref[1], color=ORANGE, fontsize=8, va='center')


fig, axs = plt.subplots(2, 1, figsize=(9, 6.4), sharex=True)
box(axs[0], '영양_N_PROT', '단백질 (g/일)', (50, '남성 EAR\n50g'))
box(axs[1], '영양_N_FE', '철 (mg/일)', (6, '남성 EAR\n6mg'))
axs[0].legend(frameon=False, fontsize=8.5, loc='upper left')
save(fig, 'f09_유형별_섭취량.png')
fig, ax = plt.subplots(figsize=(9, 3.4))
box(ax, 'ML_sedentary_min', '좌식 시간 (분/일)')
save(fig, 'f10_유형별_좌식.png')

# 15개 영양소 최종 하이퍼파라미터 (08 튜닝 기록)
tu = pd.read_csv(OUT8 / '08_튜닝기록.csv', encoding='utf-8-sig')
S['tune'] = []
for n, g in tu.groupby('영양소', sort=False):
    sel_, best = g[g['선택']].iloc[0], g.loc[g['CV로그손실'].idxmin()]
    S['tune'].append(dict(n=n, sel=sel_['후보'], loss=round(sel_['CV로그손실'], 4), auc=round(sel_['CV_AUC'], 3),
                          best=best['후보'], best_loss=round(best['CV로그손실'], 4), lim=round(best['CV로그손실'] + best['SE'], 4)))

json.dump(S, open(FIG / 'stats.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print(json.dumps(S, ensure_ascii=False, indent=1, default=str))

# 그림 4. 12개 유형 생활습관 프로필 (전체 평균 대비 z, 조사 가중)
PV = {'ML_aerobic': '유산소 실천', 'ML_strength_days': '근력운동 일수', 'ML_sedentary_min': '좌식 시간', 'ML_sleep_hours': '수면 시간',
      'ML_stress': '스트레스 인지', 'ML_breakfast_freq_ord': '아침 빈도', 'ML_lunch_freq_ord': '점심 빈도', 'ML_dinner_freq_ord': '저녁 빈도',
      'ML_eatingout_freq_ord': '외식 빈도', 'ML_smoker': '흡연(참고)', 'ML_drink_freq_ord': '음주 빈도(참고)'}
mu = {c: np.average(d[c], weights=w) for c in PV}
sd = {c: np.sqrt(np.average((d[c] - mu[c]) ** 2, weights=w)) for c in PV}
Zt = pd.DataFrame({PV[c]: {k: (np.average(g[c], weights=g['w']) - mu[c]) / sd[c] for k, g in d.groupby('cluster')} for c in PV}).loc[IDS]
fig, ax = plt.subplots(figsize=(10, 5.6))
im = ax.imshow(Zt.values, cmap=DIV, vmin=-1.5, vmax=1.5, aspect='auto')
ax.set_xticks(range(Zt.shape[1])); ax.set_xticklabels(Zt.columns, rotation=40, ha='right')
ax.set_yticks(range(12)); ax.set_yticklabels([f'{k} {NAMES[k]}' for k in IDS])
for i in range(12):
    for j in range(Zt.shape[1]):
        v = Zt.values[i, j]
        ax.text(j, i, f'{v:+.1f}', ha='center', va='center', fontsize=7.5, color='white' if abs(v) > 1.0 else INK)
for y_ in [2.5, 5.5, 8.5]:
    ax.axhline(y_, color='#fcfcfb', lw=3)
ax.axvline(8.5, color=INK, lw=1.5)
ax.spines[:].set_visible(False)
cb = fig.colorbar(im, ax=ax, shrink=0.8); cb.set_label('전체 평균 대비 표준화 점수 (z)'); cb.outline.set_visible(False)
save(fig, 'f04_유형프로필.png')
