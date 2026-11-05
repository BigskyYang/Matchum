# -*- coding: utf-8 -*-
"""추가검증 결과 그림 3개 (추가검증.py를 먼저 실행). 색은 보고서(make_figs.py)와 같다."""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
plt.rcParams.update({'font.family': 'Malgun Gothic', 'axes.unicode_minus': False, 'font.size': 11,
                     'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.edgecolor': '#8a8984', 'axes.labelcolor': '#0b0b0b', 'xtick.color': '#52514e',
                     'ytick.color': '#52514e', 'figure.facecolor': '#fcfcfb', 'axes.facecolor': '#fcfcfb',
                     'savefig.facecolor': '#fcfcfb', 'grid.color': '#e4e3df', 'grid.linewidth': 0.8})
BLUE, ORANGE, GRAY, INK, INK2 = '#2c6e6a', '#b9773a', '#c4c2bb', '#0b0b0b', '#52514e'


def title(ax, main, sub):
    ax.set_title(main, loc='left', fontsize=14, fontweight='bold', color=INK, pad=26)
    ax.text(0, 1.025, sub, transform=ax.transAxes, fontsize=10, color=INK2)


def save(fig, name):
    fig.savefig(HERE / name, dpi=200, bbox_inches='tight')
    plt.close(fig)


# 그림 1. 라벨 섞기
r = pd.read_csv(HERE / '결과_섞기_회차별.csv', encoding='utf-8-sig')
REAL_OE = 1.0874
assert len(r) == 200
fig, ax = plt.subplots(figsize=(8.6, 4.5))
ax.hist(r['OE'], bins=np.arange(0.986, 1.0145, 0.002), color=GRAY, edgecolor='#fcfcfb', linewidth=1.5, label='유형을 섞은 자료 200회')
ax.axvline(REAL_OE, color=BLUE, lw=2.5, label='실제 유형')
ax.axvline(1, color=INK2, lw=1, ls=':')
top = ax.get_ylim()[1]
ax.text(REAL_OE - 0.0015, top * 0.9, f'실제 {REAL_OE:.3f}', ha='right', color=INK, fontweight='bold')
ax.text(r['OE'].max() + 0.002, top * 0.62, f'섞은 자료\n평균 {r["OE"].mean():.3f}\n최대 {r["OE"].max():.3f}', ha='left', va='center', color=INK2)
ax.set_xlim(0.98, 1.095)
ax.set_xlabel('2024년 관측 ÷ 기대 부족 (1이면 같은 성별·나이와 같음)')
ax.set_ylabel('회차 수')
ax.grid(axis='y'); ax.set_axisbelow(True)
ax.legend(loc='upper center', frameon=False, fontsize=10)
title(ax, '유형을 섞으면 효과가 사라집니다', '같은 성별×연령대×연도 안에서 유형 라벨을 섞어 같은 절차를 200회 반복')
save(fig, '그림1_라벨섞기.png')

# 그림 2. 판정별 O/E
o = pd.read_csv(HERE / '결과_판정_OE.csv', encoding='utf-8-sig')
tags = ['유형 고유', '식사량 관련', '흔함']
names = {'유형 고유': '유형 고유\n(N2 철)', '식사량 관련': '식사량 관련', '흔함': '흔함'}
series = [('전체 연도', '전체 연도 판정 (2024 포함)', ORANGE, 's', 0.16), ('2022-23', '2022–23 판정 (2024 제외)', BLUE, 'o', -0.16)]
fig, ax = plt.subplots(figsize=(8.6, 4.5))
ypos = np.arange(len(tags))[::-1]
for key, lab, col, mk, off in series:
    t = o[o['판정기준'] == key].set_index('판정').loc[tags]
    y = ypos + off
    ax.hlines(y, t['사람CI_low'], t['사람CI_high'], color=col, lw=2.5, zorder=2)
    ax.scatter(t['OE'], y, s=70, color=col, marker=mk, zorder=3, edgecolor='#fcfcfb', linewidth=1.5, label=lab)
    for yi, (v, hi, n) in zip(y, zip(t['OE'], t['사람CI_high'], t['항목수'])):
        ax.text(hi + 0.008, yi, f'{v:.2f}  ({int(n)}개 항목)', va='center', fontsize=9.5, color=INK)
ax.axvline(1, color=INK2, lw=1)
ax.set_yticks(ypos); ax.set_yticklabels([names[t] for t in tags])
ax.set_ylim(-0.6, 2.6); ax.set_xlim(0.98, 1.72)
ax.set_xlabel('2024년 관측 ÷ 기대 부족 (점: 값, 선: 95% CI, 사람 단위 부트스트랩)')
ax.grid(axis='x'); ax.set_axisbelow(True)
ax.legend(loc='lower right', frameon=False, fontsize=10)
title(ax, '2024년을 뺀 판정으로도 결과가 유지됩니다', '2022–23 모델로 고른 2줄 항목을 2024년 자료로 확인')
save(fig, '그림2_판정별_OE.png')

# 그림 3. 경계 그룹별 ΔAUC
e = pd.read_csv(HERE / '결과_경계_영양소별.csv', encoding='utf-8-sig')
c = pd.read_csv(HERE / '결과_경계_CI.csv', encoding='utf-8-sig', index_col=0)
groups = ['핵심', '중간', '경계']
mean = e.groupby('구분')['ΔAUC'].mean()
n = e.drop_duplicates('구분').set_index('구분')['n']
fig, ax = plt.subplots(figsize=(8.6, 3.8))
ypos = np.arange(3)[::-1]
for g, y in zip(groups, ypos):
    lo, hi = c[f'{g}Δ'].iloc[0], c[f'{g}Δ'].iloc[1]
    col = ORANGE if lo <= 0 else BLUE
    ax.hlines(y, lo, hi, color=col, lw=2.5, zorder=2)
    ax.scatter(mean[g], y, s=80, color=col, marker='s' if lo <= 0 else 'o', zorder=3, edgecolor='#fcfcfb', linewidth=1.5)
    ax.text(hi + 0.0012, y, f'+{mean[g]:.3f}  [{lo:+.3f}, {hi:+.3f}]', va='center', fontsize=10, color=INK)
ax.axvline(0, color=INK2, lw=1)
ax.set_yticks(ypos); ax.set_yticklabels([f'{g}\n{int(n[g]):,}명' for g in groups])
ax.set_ylim(-0.6, 2.6); ax.set_xlim(-0.008, 0.066)
ax.set_xlabel('ΔAUC: 유형 추가 모델 - 성별·나이 모델, 영양소 15개 평균 (선: 95% CI)')
ax.grid(axis='x'); ax.set_axisbelow(True)
title(ax, '경계 고객만 보면 유형을 더한 효과가 확인되지 않습니다', '2024년 5,320명. 네모·황토는 신뢰구간이 0을 포함한 그룹')
save(fig, '그림3_경계_ΔAUC.png')
print('완료')
