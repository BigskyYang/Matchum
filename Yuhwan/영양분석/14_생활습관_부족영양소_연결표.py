# %% [markdown]
# # 생활습관 ↔ 부족 영양소 연결표 — 팀장님 요청 11/4
# 목적: 유형 결과의 '이번 주 해볼 것'에 데이터 근거와 우선순위를 붙인다.
#   미션은 지금처럼 본인 응답에 해당하는 습관만 보여 주고, 이 표로 "내 유형의 부족 영양소와 가장 많이 이어진 습관"을 먼저 보여 준다.
# 내용: 바꿀 수 있는 습관마다, 같은 성별·연령대 안에서 그 습관이 있는 사람과 없는 사람의 영양소 부족 비율(10명 중 몇 명)
#   - 영양소 15종과 부족 기준(EAR·AI)은 (나)안과 같음 (common.KDRI, add_status)
#   - 조사 가중치 wt_tot/3 적용, 연령대 19-29/30-49/50-64/65-74/75+
#   - 상관관계라 화면 문구는 "~한 사람은 ○○이 부족한 경우가 적은 편이에요"처럼 경향으로만 쓴다 (인과·질병 표현 금지)
#
# 습관 정의 = 웹 tips.js 미션 기준 (팀장님 11/4 답변). 값은 지연님 군집 파일의 ML_ 변수 = 웹 encode.js와 같은 척도
#   breakfast   아침 거르기        아침 주 1~2회 이하              ML_breakfast_freq_ord ≤ 1
#   skip_meal   점심·저녁 거르기   점심 또는 저녁 주 1~2회 이하     ML_lunch_freq_ord ≤ 1 또는 ML_dinner_freq_ord ≤ 1
#   eating_out  외식 잦음          주 5~6회 이상                   ML_eatingout_freq_ord ≥ 4
#               → 팀장님 결정: 결과는 그대로 남기되 웹 미션의 영양소 근거로는 쓰지 않음 (상관관계 해석 주의 사례)
#   sedentary   오래 앉아 있기     하루 10시간 이상                ML_sedentary_min ≥ 600
#   aerobic     유산소 활동 부족   주 2시간 반 미만                ML_aerobic = 0 (KNHANES pa_aerobic 정의)
#   strength    근력운동 부족      주 2일 미만                     ML_strength_days < 2
#   sleep_short 수면 부족          하루 6시간 미만                 (주중×5+주말×2)/7, 2022·23은 2024 척도로 환산(웹·지연님 모델과 같은 방식)
#   수면 불규칙은 뺌 (팀장님 결정: 웹 미션에 없고, 잠든 시각은 2024년에만 물어서 근거가 약함)
#
# 인원이 적은 조합: 습관이 있는 쪽·없는 쪽 중 적은 쪽이 30명 미만이면 few=True (팀장님 확인)
# 차이가 뚜렷한지: 가중 비율 차이의 95% 구간(Kish 유효표본수 근사)이 0을 넘지 않으면 clear=True
# 웹 근거 문구 규칙 (팀장님): few가 아니고 차이가 10명 중 0.5명 이상인 항목만 → show=True (외식은 항상 False)

# %%
import json
import numpy as np
import pandas as pd
from common import *

MIN_N = 30
SEXES = ['남자', '여자']
REPO = ROOT.parent if (ROOT.parent / 'Jiyeon').exists() else ROOT.parent / 'Matchum'
ADJ = json.load(open(REPO / 'Jiyeon' / 'kmedoids_model.json', encoding='utf-8'))['sleep_year_adjust']['by_year']

d = add_status(load_persons(ROOT / 'KMedoids_12Types_N1O3.csv', 'Type'))
d['age_grp_s'] = d['age_grp'].astype(str)
print('사람', len(d), '| 연도', d['year'].value_counts().sort_index().to_dict())

# 수면 시간: 지연님 모델과 같은 연도 환산 (2022·23 직접 응답 → 2024 분포)
mu24, sd24 = ADJ['2024']['mean'], ADJ['2024']['std']
d['sleep_h24'] = [h if y == 2024 else (h - ADJ[str(int(y))]['mean']) / ADJ[str(int(y))]['std'] * sd24 + mu24
                  for h, y in zip(d['ML_sleep_hours'], d['year'])]

# %% 습관 정의 (웹 tips.js 기준)
HABITS = {
    'breakfast': ('아침 거르기', '아침 주 1~2회 이하', d['ML_breakfast_freq_ord'] <= 1),
    'skip_meal': ('점심·저녁 거르기', '점심 또는 저녁 주 1~2회 이하', (d['ML_lunch_freq_ord'] <= 1) | (d['ML_dinner_freq_ord'] <= 1)),
    'eating_out': ('외식 잦음', '외식 주 5~6회 이상', d['ML_eatingout_freq_ord'] >= 4),
    'sedentary': ('오래 앉아 있기', '앉아 있는 시간 하루 10시간 이상', d['ML_sedentary_min'] >= 600),
    'aerobic': ('유산소 활동 부족', '숨이 찰 정도의 활동 주 2시간 반 미만', d['ML_aerobic'] == 0),
    'strength': ('근력운동 부족', '근력운동 주 2일 미만', d['ML_strength_days'] < 2),
    'sleep_short': ('수면 부족', '하루 평균 6시간 미만', d['sleep_h24'] < 6),
}
NO_BASIS = {'eating_out'}   # 결과는 남기되 웹 근거 문구로는 쓰지 않음
SHOW_DIFF = 0.05            # 10명 중 0.5명
prev = []
for k, (lab, _, h) in HABITS.items():
    prev.append(dict(습관=lab, 해당=int(h.sum()), 가중비율=np.average(h.astype(float), weights=d['w'])))
print(pd.DataFrame(prev).round(3).to_string(index=False))


# %% 성별 × 연령대 × 습관 × 영양소: 있는 사람 vs 없는 사람 부족 비율 (가중)
def wrate(y, w):
    p = np.average(y, weights=w)
    neff = w.sum() ** 2 / (w ** 2).sum()
    return p, p * (1 - p) / neff


rows = []
for k, (lab, _, h) in HABITS.items():
    for s in SEXES:
        for a in AGE_LABELS:
            cell = (d['sex'] == s) & (d['age_grp_s'] == a) & h.notna()
            g1, g0 = cell & (h == 1), cell & (h == 0)
            n1, n0 = int(g1.sum()), int(g0.sum())
            for n in NUTRIENTS:
                y = d[f'below_{n}']
                p1, v1 = wrate(y[g1], d.loc[g1, 'w']) if n1 else (np.nan, np.nan)
                p0, v0 = wrate(y[g0], d.loc[g0, 'w']) if n0 else (np.nan, np.nan)
                se = np.sqrt(v1 + v0)
                rows.append(dict(habit=k, 습관=lab, 성별=s, 연령대=a, 영양소=n, 기준=KDRI[n][1], n_with=n1, n_without=n0,
                                 p_with=p1, p_without=p0, diff=p1 - p0, se=se,
                                 pop=d.loc[cell, 'w'].sum(), few=min(n1, n0) < MIN_N,
                                 show=k not in NO_BASIS and min(n1, n0) >= MIN_N and (p1 - p0) >= SHOW_DIFF,
                                 clear=bool(abs(p1 - p0) > 1.96 * se) if n1 and n0 else False))
T = pd.DataFrame(rows)
T.to_csv(OUT / '14_습관_부족영양소_연결표.csv', index=False, encoding='utf-8-sig')
print(f'조합 {len(T)}개 (습관 {T.habit.nunique()} × 성별·연령 10 × 영양소 15) | 인원 적음 {T.few.mean():.1%} | 차이 뚜렷 {T.clear.mean():.1%} | 웹 근거(show) {T.show.sum()}개')
print(T.groupby('습관')[['few', 'clear', 'show']].mean().round(2).to_string())

# %% 요약 (우선순위·발표용): 성별·연령 구성을 맞춘 평균 차이 = 칸 인구로 가중한 칸별 차이의 평균
ok = T[~T.few & T['diff'].notna()]
S = ok.groupby(['habit', '습관', '영양소']).apply(
    lambda g: pd.Series({'평균차이_10명중': np.average(g['diff'], weights=g['pop']) * 10,
                         '칸수': len(g), '뚜렷한칸': int(g['clear'].sum()),
                         '같은방향칸': int((np.sign(g['diff']) == np.sign(np.average(g['diff'], weights=g['pop']))).sum())}),
    include_groups=False).reset_index()
S.to_csv(OUT / '14_습관_부족영양소_요약.csv', index=False, encoding='utf-8-sig')
piv = S.pivot(index='영양소', columns='습관', values='평균차이_10명중').reindex(NUTRIENTS)
print('\n습관이 있는 사람 − 없는 사람, 10명 중 몇 명 차이 (성별·연령 맞춤, +면 습관 있는 쪽이 더 부족)')
print(piv.round(1).to_string())

# %% 웹 JSON: 습관 → 성별 → 연령대 → [{영양소, 있는 사람 10명 중, 없는 사람 10명 중, 인원}]
o1 = lambda p: None if pd.isna(p) else round(float(p) * 10, 1)
web = {'version': 'yuhwan-habit-nutrient-v2',
       'source_types': 'nbti-12types-v2',
       '설명': '같은 성별·연령대 안에서 그 습관이 있는 사람과 없는 사람 중 2025 KDRI 기준 미만인 비율(조사 가중, 10명 중 몇 명). '
               '음식만(영양제 미포함), 하루 24시간 회상 기준. 상관관계라 원인·효과를 뜻하지 않으며, 개인 진단이 아닙니다.',
       '표현_규칙': '경향으로만: "아침을 챙기는 사람은 칼슘이 부족한 경우가 적은 편이에요". "~하면 좋아져요" 같은 인과 표현과 질병 표현 금지',
       '필드': {'with_of10': '습관이 있는 사람 10명 중 부족한 사람 수(소수 1자리)', 'without_of10': '습관이 없는 사람 10명 중',
               'diff_of10': 'with − without', 'n_with': '습관이 있는 사람 수(가중 전)', 'n_without': '없는 사람 수',
               'few': f'적은 쪽 인원이 {MIN_N}명 미만 → 표시하지 않거나 "자료가 적어요"', 'clear': '차이의 95% 구간이 0을 넘지 않음',
               'basis': 'EAR(부족 위험) / AI(참고 지표)',
               'show': '웹 근거 문구로 쓸 항목: few가 아니고 diff ≥ 0.5명(10명 중). 외식 잦음은 결과만 남기고 항상 false'},
       'habits': {k: {'label': lab, 'definition': df, 'use_as_basis': k not in NO_BASIS} for k, (lab, df, _) in HABITS.items()},
       'summary': {}, 'cells': {}}
for k in HABITS:
    web['cells'][k] = {s: {a: [dict(nutrient=r.영양소, basis=r.기준, with_of10=o1(r.p_with), without_of10=o1(r.p_without),
                                    diff_of10=o1(r.diff), n_with=r.n_with, n_without=r.n_without, few=bool(r.few), clear=r.clear,
                                    show=bool(r.show))
                               for r in T[(T.habit == k) & (T.성별 == s) & (T.연령대 == a)].itertuples()]
                           for a in AGE_LABELS} for s in SEXES}
    web['summary'][k] = [dict(nutrient=r.영양소, diff_of10=round(r.평균차이_10명중, 2), clear_cells=int(r.뚜렷한칸), cells=int(r.칸수))
                         for r in S[S.habit == k].sort_values('평균차이_10명중', ascending=False).itertuples()]
with open(OUT / '14_습관_부족영양소_연결표.json', 'w', encoding='utf-8') as fp:
    json.dump(web, fp, ensure_ascii=False, indent=1)
print('저장:', OUT / '14_습관_부족영양소_연결표.json')
