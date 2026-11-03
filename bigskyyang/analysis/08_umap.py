"""발표용 UMAP 그림 (시각화 전용, 군집 입력 아님) → output/fig_08_UMAP_유형.png, fig_08_UMAP_경계.png

지연님 군집 입력(7개 점수)을 UMAP으로 2차원에 펼쳐, 12개 유형이 떨어진 덩어리인지 맞닿은 구분인지 보여 준다.
- 유형 그림: 대분류 4개를 칸으로 나누고(산점도는 3색까지만 색 구분이 확실해서), 칸마다 세부 3개를 색으로
- 경계 그림: 섬이 무엇 때문에 생기는지(스트레스·유산소 '예'), 경계 여유 10% 미만(07_boundary.py와 같은 정의)인 사람이 어디 있는지
주의: UMAP은 가까운 이웃을 뭉치게 그려서 거리·덩어리 모양을 그대로 해석하면 안 된다. 응답이 이산값이라 같은 응답끼리 작은 점 무리가 생긴다.

실행: python 08_umap.py   (umap-learn 필요, 약 3분)
"""
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import umap

from common import OUT, REPO, SEED
from twolevel import assign, fit, fit_pca, jm

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

SURFACE, INK, MUTED, BACK = '#fcfcfb', '#1f1f1e', '#6b6a66', '#dcdbd7'
SUB_COLORS = ['#2a78d6', '#eb6834', '#1baf7a']   # 기본 팔레트 1~3번 (산점도 전체 쌍 색각 검증 통과)
HIGHLIGHT = '#eb6834'

jdf = pd.read_csv(REPO / 'Jiyeon' / 'KNHANES_2022_2024_ML_CLUSTER_COMPLETECASE.csv', encoding='utf-8-sig')
_, M, _ = jm.build_matrix(jdf)
Q = fit_pca(M).transform(M)
model = fit(Q, M, np.arange(len(Q)), SEED, 'kmedoids', 10)
lab, macro = assign(model, Q, M)
web = json.loads((OUT / 'nbti_12types.json').read_text(encoding='utf-8'))
tname = {t['id']: t['name'] for t in web['types']}
mname = {m['code']: m['name'] for m in web['macro']}


def margin(V, C):
    d = np.sqrt(((V[:, None, :] - C[None]) ** 2).sum(2))
    d.sort(axis=1)
    return (d[:, 1] - d[:, 0]) / d[:, 1]


roles = list(model['macro'])
m_min = margin(Q, np.array([model['macro'][r] for r in roles]))
for r in roles:
    sel = np.flatnonzero(macro == r)
    s = model['sub'][r]
    m_min[sel] = np.minimum(m_min[sel], margin((M[np.ix_(sel, s['cols'])] - s['mean']) / s['std'], s['centers']))

stress = jdf['ML_stress'].to_numpy() == 1
aerobic = jdf['ML_aerobic'].to_numpy() == 1
E = umap.UMAP(n_neighbors=30, min_dist=0.3, random_state=SEED).fit_transform(M)
codes = pd.Series(lab).str[0].to_numpy()
note = 'UMAP(n_neighbors=30, min_dist=0.3)으로 7개 군집 점수를 2차원에 펼친 그림. 거리·덩어리 모양은 그대로 해석하지 않는다.'


def style(ax):
    ax.set_facecolor(SURFACE)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


# ── 유형: 대분류 4칸 × 세부 3색 ──
fig, axes = plt.subplots(2, 2, figsize=(12, 12), facecolor=SURFACE)
for ax, c in zip(axes.flat, ['N', 'A', 'S', 'O']):
    style(ax)
    ax.scatter(E[codes != c, 0], E[codes != c, 1], s=1.5, c=BACK, alpha=0.5, linewidths=0, rasterized=True)
    for i, k in enumerate([f'{c}{j}' for j in (1, 2, 3)]):
        p = lab == k
        ax.scatter(E[p, 0], E[p, 1], s=2.5, c=SUB_COLORS[i], alpha=0.6, linewidths=0, rasterized=True,
                   label=f'{k} {tname[k]} ({p.mean():.0%})')
        cx, cy = np.median(E[p], axis=0)
        ax.annotate(k, (cx, cy), ha='center', va='center', fontsize=11, fontweight='bold', color=INK,
                    bbox=dict(boxstyle='round,pad=0.25', fc=SURFACE, ec=SUB_COLORS[i], lw=1.5))
    ax.set_title(f'{mname[c]} ({(codes == c).mean():.0%})', loc='left', fontsize=13, color=INK, pad=6)
    leg = ax.legend(loc='upper left', bbox_to_anchor=(0, -0.01), fontsize=9.5, frameon=False, markerscale=5,
                    handletextpad=0.3, ncol=1)
    for t in leg.get_texts():
        t.set_color(INK)
fig.suptitle('같은 섬 안에서 세부 유형끼리 틈 없이 맞닿아 있다', x=0.02, ha='left', fontsize=16, color=INK)
fig.text(0.02, 0.01, note + ' 회색 = 다른 대분류.\n섬은 스트레스·유산소처럼 예/아니오 문항이 만든 것이다 (fig_08_UMAP_경계.png).', fontsize=9, color=MUTED)
fig.tight_layout(rect=(0, 0.04, 1, 0.96), h_pad=6)
fig.savefig(OUT / 'fig_08_UMAP_유형.png', dpi=150, facecolor=SURFACE)

# ── 섬과 경계: 예/아니오 문항 2개, 경계 여유 10% 미만 ──
edge = m_min < 0.1
panels = [(stress, "스트레스 많음 = 예"), (aerobic, "유산소 실천 = 예"), (edge, "경계 여유 10% 미만 (두 유형의 거의 가운데)")]
fig, axes = plt.subplots(1, 3, figsize=(18, 6.8), facecolor=SURFACE)
for ax, (mask, title) in zip(axes, panels):
    style(ax)
    ax.scatter(E[~mask, 0], E[~mask, 1], s=1.5, c=BACK, alpha=0.6, linewidths=0, rasterized=True)
    ax.scatter(E[mask, 0], E[mask, 1], s=2.5, c=HIGHLIGHT, alpha=0.7, linewidths=0, rasterized=True)
    ax.set_title(f'{title}  {mask.mean():.0%}', loc='left', fontsize=13, color=INK, pad=6)
fig.suptitle('섬은 예/아니오 문항이 만들고, 경계 근처 사람은 섬 안 곳곳에 퍼져 있다', x=0.01, ha='left', fontsize=16, color=INK)
fig.text(0.01, 0.015, note + ' 주황 = 해당하는 사람, 회색 = 나머지.\n'
         '경계 여유 = (두 번째로 가까운 유형 중심 거리 - 가장 가까운 거리) / 두 번째 거리. '
         '이 사람들이 재학습 때 바뀌는 사람의 43%를 차지한다 (07_경계분석.md).', fontsize=9, color=MUTED)
fig.tight_layout(rect=(0, 0.07, 1, 0.94))
fig.savefig(OUT / 'fig_08_UMAP_경계.png', dpi=150, facecolor=SURFACE)
print('saved', edge.mean())
