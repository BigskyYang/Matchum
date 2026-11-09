# 팀 전체 보고서용 추가 그림 (11/5): 서비스 흐름, 웹 화면, 제품 분류 단계, 개인 예측 비교
# make_figs.py와 같은 색·글꼴. 입력: 영양분석/output/16_*.csv, 발표_B안/_qa_web/*.png (matchum.vercel.app 11/5 14:50 캡처)
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from PIL import Image

HERE = Path(__file__).resolve().parent
FIG = HERE / 'fig'
OUT8 = HERE.parent / '영양분석' / 'output'
WEB = HERE.parent / '발표_B안' / '_qa_web'
plt.rcParams.update({'font.family': 'Malgun Gothic', 'axes.unicode_minus': False, 'font.size': 10,
                     'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.edgecolor': '#8a8984', 'axes.labelcolor': '#0b0b0b', 'xtick.color': '#52514e',
                     'ytick.color': '#52514e', 'figure.facecolor': '#fcfcfb', 'axes.facecolor': '#fcfcfb',
                     'savefig.facecolor': '#fcfcfb', 'grid.color': '#e4e3df', 'grid.linewidth': 0.8})
BLUE, ORANGE, AQUA, GRAY, INK, INK2 = '#2c6e6a', '#b9773a', '#8bb5b0', '#c4c2bb', '#0b0b0b', '#52514e'
TEAL_L, OCHRE_L = '#dcebe8', '#f3e6d6'


def save(fig, name):
    fig.savefig(FIG / name, dpi=200, bbox_inches='tight'); plt.close(fig); print('저장', name)


# 1. 서비스 전체 흐름 (두 단계)
fig, ax = plt.subplots(figsize=(10.5, 4.6)); ax.axis('off'); ax.set_xlim(0, 10.5); ax.set_ylim(0, 4.6)


def box(x, y, w, h, title, body, fc):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='square,pad=0.02', fc=fc, ec=AQUA, lw=0.8))
    ax.text(x + w / 2, y + h - 0.28, title, ha='center', va='center', fontsize=10, weight='bold', color=INK)
    ax.text(x + w / 2, y + (h - 0.45) / 2, body, ha='center', va='center', fontsize=8.2, color=INK2, linespacing=1.45)


def arrow(x1, y1, x2, y2):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle='-|>', color=INK2, lw=1.3))


ax.text(0.05, 4.4, '① 유형 단계 (모든 사용자)', fontsize=10, weight='bold', color=BLUE)
box(0.05, 2.55, 1.9, 1.65, '1단계 설문', '운동·좌식·수면\n스트레스·끼니·외식\n성별·생년월일', TEAL_L)
box(2.25, 2.55, 1.9, 1.65, '고객 군집화', '최지연\nPCA + 2단계 k-medoids\n12개 유형', TEAL_L)
box(4.45, 2.55, 1.9, 1.65, '유형별 부족 영양소', '전유환\n유형·성별·연령대\n→ 영양소 15개 확률', TEAL_L)
box(6.65, 2.55, 1.9, 1.65, '유형 결과 화면', '유형·습관 신호등·미션\n부족할 수 있는 영양소\n(영양제 없음)', TEAL_L)
for x in (1.95, 4.15, 6.35):
    arrow(x + 0.02, 3.37, x + 0.28, 3.37)
ax.text(0.05, 2.15, '② 개인 단계 (선택: "나에게 맞는 결과")', fontsize=10, weight='bold', color=ORANGE)
box(0.05, 0.25, 1.9, 1.65, '2단계 설문', '흡연·음주·채소·과일\n19~64세: 식사 5문항\n(고기·생선·달걀·콩·유제품)', OCHRE_L)
box(2.25, 0.25, 1.9, 1.65, '개인 영양 위험 예측', '황재준\n생활습관 모델 14개\n평소 식사 모델 10개', OCHRE_L)
box(4.45, 0.25, 1.9, 1.65, '제품 분류·필터링', '박준혁\n식약처 19,165개\n→ 9단계 → 2,227개', OCHRE_L)
box(6.65, 0.25, 1.9, 1.65, '개인 결과 화면', '살펴볼 영양소 (최대 5개)\n음식·실천 먼저\n관련 제품 정보 탐색', OCHRE_L)
arrow(1.97, 1.07, 2.23, 1.07); arrow(4.17, 1.07, 4.43, 1.07); arrow(6.37, 1.07, 6.63, 1.07)
ax.text(5.4, 1.98, '', fontsize=8)
box(8.85, 0.25, 1.6, 3.95, '웹 서비스', '양대천\n\nmatchum.vercel.app\n\n학습은 미리,\n휴대폰에서 계산만\n\n응답은 서버로\n보내지 않고\n브라우저에 저장\n(7일 뒤 다음\n조회 때 삭제)', '#eef5f3')
arrow(8.57, 3.37, 8.83, 3.37); arrow(8.57, 1.07, 8.83, 1.07)
arrow(7.6, 2.53, 7.6, 1.92)
ax.text(7.7, 2.2, '더 알아보기', fontsize=8, color=INK2)
save(fig, 'f11_서비스흐름.png')

# 2. 웹 화면 (11/9 배포본을 내장 브라우저로 캡처, 예시 응답: 30대 여성 = 대천님 capture_screens.py의 SURVEY)
W9 = HERE / 'fig' / 'web_1109'
crops = [(W9 / '1_유형결과.png', (0, 90, 364, 640), '① 유형 결과'),
         (W9 / '2_부족영양소.jpg', (0, 0, 364, 550), '② 부족할 수 있는 영양소'),
         (W9 / '3_개인결과.jpg', (0, 0, 364, 550), '③ 개인 결과'),
         (W9 / '4_제품정보.jpg', None, '④ 제품 정보 (확인 질문 뒤)')]
fig, axes = plt.subplots(1, 4, figsize=(12, 4.8))
for ax, (f, b, t) in zip(axes, crops):
    im = Image.open(f).convert('RGB')
    if b is None:   # 해상도가 다른 캡처: 다른 그림과 같은 가로세로 비율(364 × 550)로 위쪽을 자른다
        b = (0, 0, im.width, round(im.width * 550 / 364))
    ax.imshow(im.crop(b));ax.set_xticks([]); ax.set_yticks([]); ax.set_title(t, fontsize=10.5, color=INK, pad=6)
    for sp in ax.spines.values():
        sp.set_visible(True); sp.set_color('#C9D9D6')
fig.subplots_adjust(wspace=0.06)
save(fig, 'f12_웹화면.png')

# 3. 제품 분류 단계별 남은 제품 수 (준혁님 README 11/5 14:57)
st = [('준비: 2022년 이후 신고·국내 판매', 19165), ('1 기본 거르기 (임산부·질환·해외·어린이)', 17472), ('2 이름-성분 확인', 16390),
      ('3 목적 충돌 제외', 10768), ('4 풀 나누기', 10639), ('5 웹 영양제 11종 묶기', 5385), ('6 하루 함량·한 제품 한 칸', 5385),
      ('7 상한섭취량 초과 제외', 4450), ('8 품질 거르기', 3287), ('9 점수 70점 이상', 2227)]
fig, ax = plt.subplots(figsize=(9, 4.2))
y = range(len(st))[::-1]
ax.barh(list(y), [v for _, v in st], color=[AQUA] * 9 + [BLUE], height=0.62, zorder=3)
for yi, (lab, v) in zip(y, st):
    ax.text(v + 250, yi, f'{v:,}', va='center', fontsize=9, color=INK)
ax.set_yticks(list(y)); ax.set_yticklabels([s for s, _ in st], fontsize=9)
ax.set_xlabel('남은 제품 수'); ax.grid(axis='x'); ax.set_axisbelow(True); ax.set_xlim(0, 21500)
save(fig, 'f13_제품분류단계.png')

# 4. 개인 예측이 더하는 정보 (같은 정답·같은 분할, 2024 평가)
A = pd.read_csv(OUT8 / '16_개인화_기준모델_비교.csv', encoding='utf-8-sig').sort_values('개인모델')
fig, ax = plt.subplots(figsize=(9, 4.6))
yy = range(len(A))
ax.hlines(list(yy), A['기준모델'], A['개인모델'], color=GRAY, lw=2, zorder=1)
ax.scatter(A['기준모델'], yy, color=GRAY, s=30, zorder=3, label='성별·연령대')
ax.scatter(A['유형모델'], yy, color=AQUA, s=34, zorder=3, label='+ 유형 (전유환)')
ax.scatter(A['개인모델'], yy, color=BLUE, s=40, zorder=3, label='개인 응답 18개 (황재준 v1.4)')
ax.set_yticks(list(yy)); ax.set_yticklabels(A['영양소'], fontsize=9)
ax.set_xlabel('2024년 평가 AUC (조사 가중)'); ax.grid(axis='x'); ax.set_axisbelow(True)
ax.legend(frameon=False, fontsize=9, loc='lower right')
save(fig, 'f14_개인예측_비교.png')
