# 최종 결과 보고서 (Word) 생성: 생활습관 고객 군집화 + 유형별 부족 영양소 안내
# 먼저 make_figs.py 실행 → fig/ 의 그림·stats.json 사용
import json
import re
from pathlib import Path
import pandas as pd
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = Path(__file__).resolve().parent
FIG = HERE / 'fig'
MATCHUM = HERE.parents[1] / 'Matchum'
OUT8 = HERE.parent / '영양분석' / 'output'
S = json.load(open(FIG / 'stats.json', encoding='utf-8'))

NAVY, BLUE, INK, INK2 = '1F3A5F', '2A78D6', '1A1A1A', '52514E'
FONT = '맑은 고딕'
doc = Document()

# ── 기본 스타일 ──
for s in doc.sections:
    s.page_width, s.page_height = Cm(21), Cm(29.7)
    s.left_margin = s.right_margin = Cm(2.2); s.top_margin = Cm(2.3); s.bottom_margin = Cm(2)
st = doc.styles['Normal']
st.font.name = FONT; st.font.size = Pt(10); st.font.color.rgb = RGBColor.from_string(INK)
st.element.rPr.rFonts.set(qn('w:eastAsia'), FONT)
st.paragraph_format.line_spacing = 1.35; st.paragraph_format.space_after = Pt(4)
for name, size, color, before, after in [('Heading 1', 16, NAVY, 18, 8), ('Heading 2', 12.5, NAVY, 14, 5), ('Heading 3', 11, BLUE, 10, 3)]:
    h = doc.styles[name]
    h.font.name = FONT; h.font.size = Pt(size); h.font.bold = True; h.font.color.rgb = RGBColor.from_string(color)
    h.element.rPr.rFonts.set(qn('w:eastAsia'), FONT)
    h.paragraph_format.space_before = Pt(before); h.paragraph_format.space_after = Pt(after)
    h.paragraph_format.keep_with_next = True
for name in ['List Bullet', 'List Number']:
    doc.styles[name].font.name = FONT; doc.styles[name].paragraph_format.space_after = Pt(2)

# Word가 열 때 목차 필드 갱신
upd = OxmlElement('w:updateFields'); upd.set(qn('w:val'), 'true'); doc.settings.element.append(upd)


def shade(cell, hex_):
    tcPr = cell._tc.get_or_add_tcPr()
    sh = OxmlElement('w:shd'); sh.set(qn('w:val'), 'clear'); sh.set(qn('w:color'), 'auto'); sh.set(qn('w:fill'), hex_)
    tcPr.append(sh)


def borders(table, color='D5DCE6', size=4, inside=True):
    tblPr = table._tbl.tblPr
    b = OxmlElement('w:tblBorders')
    for edge in ['top', 'left', 'bottom', 'right'] + (['insideH', 'insideV'] if inside else []):
        e = OxmlElement(f'w:{edge}'); e.set(qn('w:val'), 'single'); e.set(qn('w:sz'), str(size)); e.set(qn('w:color'), color)
        b.append(e)
    tblPr.append(b)


def no_borders(table):
    tblPr = table._tbl.tblPr
    b = OxmlElement('w:tblBorders')
    for edge in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
        e = OxmlElement(f'w:{edge}'); e.set(qn('w:val'), 'nil'); b.append(e)
    tblPr.append(b)


def cell_border(cell, edge, color, size=24):
    tcPr = cell._tc.get_or_add_tcPr()
    b = tcPr.find(qn('w:tcBorders'))
    if b is None:
        b = OxmlElement('w:tcBorders'); tcPr.append(b)
    e = OxmlElement(f'w:{edge}'); e.set(qn('w:val'), 'single'); e.set(qn('w:sz'), str(size)); e.set(qn('w:color'), color)
    b.append(e)


def margins(cell, top=80, bottom=80, left=120, right=120):
    tcPr = cell._tc.get_or_add_tcPr()
    m = OxmlElement('w:tcMar')
    for k, v in dict(top=top, bottom=bottom, left=left, right=right).items():
        e = OxmlElement(f'w:{k}'); e.set(qn('w:w'), str(v)); e.set(qn('w:type'), 'dxa'); m.append(e)
    tcPr.append(m)


def rich(p, text, size=None, color=None, bold=None):
    """**굵게** 와 `코드` 표기를 run으로."""
    for part in re.split(r'(\*\*.+?\*\*|`[^`]+`)', text):
        if not part:
            continue
        r = p.add_run(part.strip('*').strip('`') if part[0] in '*`' else part)
        if part.startswith('**'):
            r.bold = True
        if part.startswith('`'):
            r.font.name = 'Consolas'
        if bold is not None and not part.startswith('**'):
            r.bold = bold
        if size:
            r.font.size = Pt(size)
        if color:
            r.font.color.rgb = RGBColor.from_string(color)
    return p


PB = [False]   # 다음 제목·문단을 새 쪽에서 시작 (빈 쪽이 생기는 '쪽 나눔 문단' 대신)


def _pb(p):
    if PB[0]:
        p.paragraph_format.page_break_before = True; PB[0] = False
    return p


def P(text, size=None, color=None, align=None, after=None, bold=None):
    p = _pb(rich(doc.add_paragraph(), text, size, color, bold))
    if align:
        p.alignment = align
    if after is not None:
        p.paragraph_format.space_after = Pt(after)
    return p


def B(items, style='List Bullet'):
    for it in items:
        if isinstance(it, tuple):           # (본문, [하위])
            rich(doc.add_paragraph(style=style), it[0])
            for sub in it[1]:
                p = rich(doc.add_paragraph(style='List Bullet 2'), sub)
        else:
            rich(doc.add_paragraph(style=style), it)


def H(text, lvl=1):
    return _pb(doc.add_heading(text, lvl))


CAP = {'표': 0, '그림': 0}


def caption(kind, text):
    CAP[kind] += 1
    p = doc.add_paragraph()
    r = p.add_run(f'{kind} {CAP[kind]}. '); r.bold = True; r.font.size = Pt(9); r.font.color.rgb = RGBColor.from_string(NAVY)
    r = p.add_run(text); r.font.size = Pt(9); r.font.color.rgb = RGBColor.from_string(INK2)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if kind == '그림' else WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_after = Pt(8 if kind == '그림' else 3)
    if kind == '표':
        p.paragraph_format.keep_with_next = True
    return p


def T(rows, cap=None, widths=None, size=8.5, first_col_bold=False, align_num=True, note=None, hl_rows=()):
    if cap:
        caption('표', cap)
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    borders(t)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = t.cell(i, j); c.text = ''
            c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            margins(c, 50, 50, 90, 90)
            p = c.paragraphs[0]; p.paragraph_format.space_after = Pt(0); p.paragraph_format.line_spacing = 1.15
            rich(p, str(val), size, 'FFFFFF' if i == 0 else None, True if i == 0 or (first_col_bold and j == 0) else None)
            if i == 0:
                shade(c, NAVY); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                if i in hl_rows:
                    shade(c, 'E3EEFB')
                elif i % 2 == 0:
                    shade(c, 'F6F8FB')
                if align_num and re.fullmatch(r'[\s+\-−0-9.,%~×≤≥()\[\]배명개/✓]+', str(val) or 'x'):
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    # 머리글 반복, 행이 쪽 경계에서 갈라지지 않게. 18행 이하 표는 통째로 한 쪽에 묶는다
    trPr = t.rows[0]._tr.get_or_add_trPr(); h = OxmlElement('w:tblHeader'); h.set(qn('w:val'), 'true'); trPr.append(h)
    nosplit(t)
    if len(rows) <= 18:
        for row in t.rows[:-1]:
            for c in row.cells:
                for p in c.paragraphs:
                    p.paragraph_format.keep_with_next = True
    if widths:
        for row in t.rows:
            for j, wv in enumerate(widths):
                row.cells[j].width = Cm(wv)
    if note:
        p = P(note, 8, INK2, after=8)
    else:
        doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def nosplit(t):
    for row in t.rows:
        trPr = row._tr.get_or_add_trPr(); e = OxmlElement('w:cantSplit'); e.set(qn('w:val'), 'true'); trPr.append(e)


def callout(title, lines, fill='EEF4FC', bar=BLUE):
    t = doc.add_table(rows=1, cols=1); t.alignment = WD_TABLE_ALIGNMENT.CENTER; no_borders(t); nosplit(t)
    c = t.cell(0, 0); shade(c, fill); cell_border(c, 'left', bar, 36); margins(c, 120, 120, 220, 180)
    p = c.paragraphs[0]; rich(p, title, 10.5, bar if bar != BLUE else NAVY, True); p.paragraph_format.space_after = Pt(3)
    for ln in lines:
        q = c.add_paragraph(); q.paragraph_format.space_after = Pt(2); q.paragraph_format.line_spacing = 1.3
        rich(q, ('•  ' if not ln.startswith('→') else '') + ln, 9.5)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def kpis(items):
    t = doc.add_table(rows=2, cols=len(items)); t.alignment = WD_TABLE_ALIGNMENT.CENTER; no_borders(t)
    for j, (val, lab) in enumerate(items):
        for i in range(2):
            c = t.cell(i, j); shade(c, 'F3F6FA' if i else 'E3EEFB'); margins(c, 100, 100, 80, 80)
        p = t.cell(0, j).paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after = Pt(0)
        r = p.add_run(val); r.bold = True; r.font.size = Pt(17); r.font.color.rgb = RGBColor.from_string(NAVY)
        p = t.cell(1, j).paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after = Pt(0)
        rich(p, lab, 8.5, INK2)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def F(path, cap, width=15.5):
    path = Path(path)
    if not path.exists():
        print('그림 없음:', path); return
    doc.add_picture(str(path), width=Cm(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.paragraphs[-1].paragraph_format.keep_with_next = True
    caption('그림', cap)


def screen_card(title, common, rows, empty=None):
    """서비스 화면 예시 카드."""
    t = doc.add_table(rows=1, cols=1); t.alignment = WD_TABLE_ALIGNMENT.CENTER; no_borders(t); nosplit(t)
    c = t.cell(0, 0); shade(c, 'FFFFFF'); margins(c, 140, 140, 220, 220)
    for e in ['top', 'left', 'bottom', 'right']:
        cell_border(c, e, 'C9D6E8', 8)
    p = c.paragraphs[0]; rich(p, title, 10, NAVY, True)
    q = c.add_paragraph(); rich(q, '많은 사람에게 부족하기 쉬워요', 9, 'B5502A', True); q.paragraph_format.space_after = Pt(1)
    q = c.add_paragraph(); rich(q, common, 9, INK2)
    q = c.add_paragraph(); rich(q, '내 유형에서 살펴볼 것', 9, BLUE, True); q.paragraph_format.space_after = Pt(1); q.paragraph_format.space_before = Pt(4)
    if rows:
        for n, a, b, msg in rows:
            q = c.add_paragraph(); q.paragraph_format.space_after = Pt(1)
            rich(q, f'**{n}**  내 유형 10명 중 {a}명 · 같은 성별·나이 평균 {b}명  —  {msg}', 9)
    else:
        q = c.add_paragraph(); rich(q, empty, 9)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def page_break():
    PB[0] = True


# 각주: 본문에 {{fn:키}}를 적어 두면 Word 변환 단계(to_pdf.ps1)에서 그 자리에 진짜 각주를 단다
FN = {
    'ARI': 'ARI(Adjusted Rand Index, 조정 랜드 지수): 두 군집 결과가 얼마나 같은지. 1 = 완전히 같음, 0 = 우연 수준. 높을수록 좋음. 이 보고서는 0.8 이상을 안정적으로 봄.',
    '실루엣': '실루엣 계수(Silhouette coefficient): 각 사람이 자기 군집에 얼마나 가깝고 다른 군집과 얼마나 먼지(−1~1). 높을수록 군집이 뚜렷함. 0.5 이상 뚜렷, 0.25 미만 약한 구조.',
    'AUC': 'AUC(Area Under the ROC Curve): 부족한 사람과 아닌 사람을 예측 확률로 구분하는 능력. 0.5 = 무작위, 1 = 완벽. 높을수록 좋음. 보통 0.7 이상이면 쓸 만한 수준.',
    'CI': '95% CI(Confidence Interval, 신뢰구간): 같은 방법을 반복할 때 95% 확률로 참값을 포함하는 범위. 좁을수록 정확함. 차이는 하한 > 0, 비율은 하한 > 1이면 유의.',
    'kmedoids': 'k-medoids(PAM): 실제 사람 한 명(대표점)을 군집 중심으로 삼아 k개로 나누는 방법. 평균을 중심으로 쓰는 k-평균보다 이상값에 덜 민감함.',
    'PCA': 'PCA(Principal Component Analysis, 주성분 분석): 서로 겹치는 변수를 정보 손실이 적은 소수의 축으로 요약. 누적 설명분산이 높을수록 정보 보존이 좋음(보통 70~80% 이상).',
    '부트스트랩': '부트스트랩(Bootstrap): 자료에서 복원추출로 표본을 반복해 만들어 통계량의 흔들림을 추정하는 방법. 이 보고서는 2,000회 반복해 95% 신뢰구간을 구함.',
    'KDRI': 'KDRI(Dietary Reference Intakes for Koreans, 한국인 영양소 섭취기준): 보건복지부·한국영양학회가 정한 성별·연령별 섭취 기준. 이 보고서는 2025년 개정판을 씀.',
    'ΔAUC': 'ΔAUC: 유형 추가 모델 AUC − 성별·연령 모델 AUC. 클수록 유형이 주는 추가 정보가 많음. 95% 신뢰구간 하한이 0보다 크면 유의.',
    'EAR': 'EAR(Estimated Average Requirement, 평균필요량): 건강한 사람 절반의 필요를 채우는 하루 섭취량. 이보다 적게 먹으면 부족 위험으로 봄.',
    'AI': 'AI(Adequate Intake, 충분섭취량): EAR을 정할 근거가 부족할 때 쓰는 기준. 건강한 사람들의 섭취 수준이라 미만이어도 부족이라 단정할 수 없음.',
    'VIF': 'VIF(Variance Inflation Factor, 분산팽창계수): 한 변수가 다른 변수들로 얼마나 설명되는지. 낮을수록 좋음. 1 = 겹침 없음, 5~10 이상이면 다중공선성 의심.',
    'Cramér V': 'Cramér V(크라메르 V): 두 범주형 변수의 연관 정도(0~1). 여기서는 유형이 성별에 쏠린 정도라 낮을수록 좋음. 0.1 약함, 0.3 중간, 0.5 이상 강함.',
    'η²': 'η²(에타 제곱): 변수의 전체 분산 중 군집 간 차이로 설명되는 비율(0~1). 높을수록 그 변수가 군집을 강하게 가름. 0.14 이상이면 큰 효과로 봄.',
    '로그 손실': '로그 손실(Log loss): 예측 확률이 실제 결과와 얼마나 어긋나는지. 낮을수록 좋음. 확률이 정확해야 낮아지므로 "10명 중 N명" 표시에 맞는 지표.',
    '1-SE': '1-SE 규칙(One-standard-error rule): 교차검증 손실이 가장 작은 모델의 "최솟값 + 1 표준오차" 안에 드는 모델 중 가장 단순한 것을 고르는 규칙. 과적합 방지 목적.',
    '정밀도': '정밀도(Precision) = 안내한 영양소 중 실제로 부족한 비율, 재현율(Recall) = 실제 부족한 영양소 중 안내된 비율, F1 = 둘의 조화평균. 모두 0~1, 높을수록 좋음.',
    'BH-FDR': 'BH-FDR(Benjamini–Hochberg False Discovery Rate): 여러 번 검정할 때 "유의"로 고른 것 중 거짓 비율을 관리하는 보정. 보정 후 q값이 낮을수록 믿을 만함(보통 q < 0.05).',
}


def fn(key):
    return '{{fn:' + key + '}}'


def field(p, code):
    r = p.add_run(); f = OxmlElement('w:fldChar'); f.set(qn('w:fldCharType'), 'begin'); r._r.append(f)
    r = p.add_run(); it = OxmlElement('w:instrText'); it.set(qn('xml:space'), 'preserve'); it.text = code; r._r.append(it)
    r = p.add_run(); f = OxmlElement('w:fldChar'); f.set(qn('w:fldCharType'), 'separate'); r._r.append(f)
    r = p.add_run('(Word에서 열면 목차가 표시됩니다. 표시되지 않으면 우클릭 → 필드 업데이트)' if 'TOC' in code else '1')
    r = p.add_run(); f = OxmlElement('w:fldChar'); f.set(qn('w:fldCharType'), 'end'); r._r.append(f)


# ════════════════════════════ 표지 ════════════════════════════
sec = doc.sections[0]
sec.different_first_page_header_footer = True
for _ in range(5):
    doc.add_paragraph()
t = doc.add_table(rows=1, cols=1); no_borders(t); c = t.cell(0, 0); shade(c, NAVY); margins(c, 500, 500, 500, 400)
p = c.paragraphs[0]; r = p.add_run('머신러닝 팀 프로젝트 최종 결과 보고서'); r.font.size = Pt(11); r.font.color.rgb = RGBColor.from_string('9EC5F4'); r.bold = True
p = c.add_paragraph(); r = p.add_run('생활습관으로 찾는\n나의 부족 영양소'); r.font.size = Pt(28); r.bold = True; r.font.color.rgb = RGBColor.from_string('FFFFFF')
p.paragraph_format.line_spacing = 1.15; p.paragraph_format.space_before = Pt(8)
p = c.add_paragraph(); r = p.add_run('국민건강영양조사 기반 생활습관 고객 군집화와 유형별 부족 영양소 안내 모델')
r.font.size = Pt(12); r.font.color.rgb = RGBColor.from_string('DCE8F7'); p.paragraph_format.space_before = Pt(10)
for _ in range(3):
    doc.add_paragraph()
meta = [('프로젝트', 'Matchum (맞춤) — 생활습관 기반 영양 안내 서비스'), ('팀', '2조 머신2러닝'),
        ('팀원', '대천(팀장) · 지연 · 유환 · 재준 · 준혁'), ('보고 범위', '고객 군집화, 유형별 부족 영양소 안내'),
        ('기간', '2026. 10. 29. ~ 11. 10.'), ('작성일', '2026. 11. 9.')]
t = doc.add_table(rows=len(meta), cols=2); no_borders(t); t.alignment = WD_TABLE_ALIGNMENT.CENTER
for i, (k, v) in enumerate(meta):
    a, b_ = t.cell(i, 0), t.cell(i, 1); a.width, b_.width = Cm(3.2), Cm(12)
    cell_border(a, 'bottom', 'D5DCE6', 4); cell_border(b_, 'bottom', 'D5DCE6', 4); margins(a, 70, 70, 100, 100); margins(b_, 70, 70, 100, 100)
    rich(a.paragraphs[0], k, 9.5, NAVY, True); rich(b_.paragraphs[0], v, 9.5)
page_break()

# 머리글·바닥글 (본문)
hp = sec.header.paragraphs[0]; hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
rich(hp, '2조 머신2러닝  |  생활습관 고객 군집화와 유형별 부족 영양소 안내', 8, '8A8984')
fp = sec.footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
field(fp, 'PAGE')
for r in fp.runs:
    r.font.size = Pt(9); r.font.color.rgb = RGBColor.from_string('8A8984')

# ════════════════════════════ 목차 ════════════════════════════
p = P('목차', 16, NAVY, bold=True, after=10)
field(doc.add_paragraph(), 'TOC \\o "1-2" \\h \\z \\u')
page_break()

# ════════════════════════════ 1. 요약 ════════════════════════════
H('1. 요약')
P('이 보고서는 국민건강영양조사(KNHANES) 2022–2024년 성인 15,062명의 자료로 **생활습관이 비슷한 사람들을 12개 유형으로 묶고**, '
  '각 유형에서 **부족하기 쉬운 영양소를 머신러닝으로 판단**해 서비스 첫 화면에 안내하는 과정과 결과를 정리합니다. '
  '혈액검사나 식사 기록 없이 설문 몇 문항만으로 "나와 비슷한 사람들은 무엇이 부족한가"를 알려 주는 것이 목표입니다.')
kpis([('15,062명', 'KNHANES 2022–2024\n분석 대상 성인'), ('12개', '생활습관 유형\n(4 대분류 × 3)'),
      ('13 / 15', '성별·연령 대비 예측이\n유의하게 좋아진 영양소'), ('1.09배', '2024년 검증: 안내 항목의\n실제 부족 배수')])
callout('핵심 결과', [
    '**고객 군집화** — 운동·식사·좌식·스트레스 7개 지표로 4개 대분류를 만들고 대분류마다 3개씩 나눠 12개 유형을 확정함. 대분류 안정성(시드 간 ARI' + fn('ARI') + ') 0.945, 웹 재배정 일치율 100%.',
    '**부족 확률 예측** — 유형·성별·연령대로 영양소 15개의 부족 확률을 예측함. 2022–23년으로 학습하고 2024년으로 평가했을 때, 성별·연령만 쓴 모델보다 AUC' + fn('AUC') + '가 +0.014~+0.040 높고 15개 중 13개에서 통계적으로 유의함.',
    '**화면 안내 규칙** — 많은 사람에게 부족한 공통 영양소 8개는 한 줄로 묶고, 그 밖에서 유형 사람들에게 특히 많은 영양소만 따로 보여 주는 2단 표시 규칙을 정함. 학습 자료만으로 고른 안내 항목이 2024년에도 같은 성별·나이보다 1.09배(95% CI' + fn('CI') + ' 1.06~1.12) 더 부족했음.',
    '**한계** — 유형은 자연적으로 뚜렷한 집단이 아니라 재현 가능한 분할이고(실루엣' + fn('실루엣') + ' 0.163), 예측력도 중간 수준임(AUC 0.56~0.70). 그래서 진단이 아닌 경향 안내로만 씀.'])

H('프로젝트 개요', 3)
T([['항목', '내용'],
   ['서비스', '설문 → ① 내 생활습관 유형 + 유형별 부족 영양소 (모든 사용자) → ② 개인 맞춤 분석·영양제 안내 (선택)'],
   ['보고 범위', '①단계: 생활습관 고객 군집화와 유형별 부족 영양소 안내. ②단계 개인 맞춤 분석은 별도로 보고함'],
   ['데이터', 'KNHANES 2022–2024 원시자료 (건강설문 + 24시간 회상 영양조사), 2025 한국인 영양소 섭취기준(KDRI' + fn('KDRI') + ')'],
   ['방법', '비지도 학습(PCA' + fn('PCA') + ' + 2단계 k-medoids' + fn('kmedoids') + ') → 지도 학습(조사 가중 로지스틱 회귀·그래디언트 부스팅 비교)'],
   ['검증', '연도 분할(2022–23 학습 / 2024 평가), 5겹 교차검증, 부트스트랩' + fn('부트스트랩') + ' 신뢰구간, 민감도 분석'],
   ['산출물', '웹용 군집 모델(JSON), 유형 × 성별 × 연령대 120개 조합의 영양소 안내표(JSON), 분석 코드']],
  '프로젝트 개요', widths=[3, 13.5], first_col_bold=True, align_num=False)
page_break()

# ════════════════════════════ 2. 배경 ════════════════════════════
H('2. 프로젝트 배경')
H('2.1 왜 이 문제인가', 2)
P('건강기능식품을 고르는 소비자 대부분은 **자신에게 무엇이 부족한지 모른 채** 광고, 유행, 주변 추천을 보고 제품을 고릅니다. '
  '부족 여부를 정확히 알려면 혈액검사나 여러 날의 식사 기록이 필요하지만, 일반 소비자가 하기에는 비용과 번거로움이 큽니다.')
P('반면 운동, 끼니, 외식, 앉아 있는 시간, 스트레스 같은 **생활습관은 몇 문항이면 답할 수 있습니다.** '
  '생활습관이 비슷한 사람들의 실제 영양 섭취를 대규모 국가 조사로 미리 분석해 두면, 설문만으로도 "나와 비슷한 사람들은 무엇이 부족하기 쉬운지"라는 첫 단서를 줄 수 있습니다.')
H('2.2 왜 생활습관 "유형"인가', 2)
B(['**이해하기 쉬움** — "끼니를 자주 거르는 비활동형"처럼 이름이 붙은 유형은 사용자가 자기 생활을 돌아보게 함. 숫자 15개보다 기억에 남음.',
   '**행동으로 이어짐** — 유형을 가르는 축(운동, 끼니, 좌식, 스트레스)이 곧 바꿀 수 있는 습관임.',
   '**공정한 비교 기준이 됨** — 같은 성별·나이대 사람과 비교해 "이 유형에서 특히 많은 부족"을 보여 줄 수 있음.'])
H('2.3 서비스 안에서의 위치', 2)
F(FIG / 'f03_분석흐름.png', '분석 흐름 — 데이터 준비부터 서비스 표시까지', 16)
P('설문을 마친 모든 사용자는 먼저 **내 유형과 유형별 부족 영양소**를 봅니다(이 보고서의 범위). '
  '더 자세히 알고 싶은 사용자만 개인 맞춤 분석 단계로 넘어가 본인 응답으로 예측한 부족 영양소와 영양제 안내를 받습니다. '
  '첫 화면에서는 영양제 제품을 추천하지 않습니다. 유형 결과는 개인 진단이 아니라 같은 조건 사람들의 경향이기 때문입니다.')

# ════════════════════════════ 3. 문제 정의 ════════════════════════════
H('3. 문제 정의')
T([['구분', '질문', '판단 지표'],
   ['비즈니스 질문', '설문만 한 사용자에게 어떤 영양소를 "살펴볼 것"으로 안내해야 믿을 만하고, 과장되지 않는가?', '안내 항목이 미래 자료에서도 실제로 더 부족한가 (관측/기대 비)'],
   ['분석 질문 1', '생활습관 응답만으로 사람을 해석 가능하고, 같은 응답이면 항상 같은 결과가 나오는 유형으로 나눌 수 있는가?', '안정성(ARI), 실루엣, 재배정 일치율, 유형 이름과 실제 평균의 일치'],
   ['분석 질문 2', '유형을 알면 성별·나이만 알 때보다 영양소 부족을 더 잘 구분할 수 있는가?', '2024년 평가 AUC 향상(ΔAUC' + fn('ΔAUC') + ')과 95% 신뢰구간'],
   ['분석 질문 3', '예측 확률을 화면에 어떤 규칙으로 보여 줘야 유형 차이가 드러나면서 과장이 없는가?', '조합별 목록 다양성, 평균보다 덜 부족한 항목 노출, 2024년 관측/기대 비']],
  '문제 정의와 판단 지표', widths=[2.6, 8, 5.9], first_col_bold=True, align_num=False)
H('범위와 가정', 3)
B(['**대상**: 19세 이상 성인. 임신·수유부 등 별도 기준이 필요한 집단도 KDRI 일반 성인 기준으로 판단함.',
   '**부족의 정의**: 하루 섭취량이 본인 성별·연령대의 2025 KDRI 기준 미만. 평균필요량(EAR' + fn('EAR') + ')이 있는 11개는 "부족 위험", 충분섭취량(AI' + fn('AI') + ')만 있는 4개(비타민D·E, 칼륨, 식이섬유)는 "참고"로 구분함.',
   '**섭취량**: 음식으로 먹은 양만 포함하고 영양제는 포함하지 않음. 하루 24시간 회상 기준임.',
   '**제외**: 개인 맞춤 예측과 영양제 제품 추천은 이 보고서에서 다루지 않음.'])

# ════════════════════════════ 4. 현황 ════════════════════════════
H('4. 현황 — 데이터로 본 성인 영양 섭취')
F(FIG / 'f01_부족률.png', '영양소별 기준 미만 비율 (KNHANES 2022–2024 성인 15,062명, 조사 가중)', 14.5)
r = S['rate']
P(f'성인 대부분이 여러 영양소에서 기준에 못 미칩니다. 비타민D({r["비타민D"]}%), 비타민E({r["비타민E"]}%), 칼륨({r["칼륨"]}%), '
  f'비타민A({r["비타민A"]}%), 비타민C({r["비타민C"]}%), 칼슘({r["칼슘"]}%), 식이섬유({r["식이섬유"]}%), 엽산({r["엽산"]}%)의 **8개는 절반 이상**이 기준 미만입니다. '
  f'반면 인({r["인"]}%), 단백질({r["단백질"]}%), 철({r["철"]}%)은 상대적으로 적습니다.')
a, sx = S['ear_cnt_by_age'], S['ear_cnt_by_sex']
T([['구분', '19–29세', '30–49세', '50–64세', '65–74세', '75세 이상', '남성', '여성'],
   ['평균 부족 영양소 수\n(EAR 11개 중)', a['19-29'], a['30-49'], a['50-64'], a['65-74'], a['75+'], sx['남자'], sx['여자']]],
  '성별·연령대별 평균 부족 영양소 개수 (조사 가중)', widths=[4.6, 1.7, 1.7, 1.7, 1.7, 1.8, 1.6, 1.6],
  note='20대와 75세 이상, 그리고 여성에서 부족한 영양소가 더 많습니다. 성별·나이만으로도 차이가 있으므로, 유형의 효과는 반드시 같은 성별·연령대와 비교해 판단해야 합니다.')
callout('현황에서 얻은 설계 원칙', [
    '절반 이상이 부족한 8개는 유형과 무관하게 많은 사람에게 해당함 → 이것만 보여 주면 모든 유형의 화면이 같아짐. **공통 영양소는 따로 묶어 안내**함.',
    '성별·나이에 따라 부족 정도가 다름 → 유형의 가치는 **같은 성별·연령대 대비 몇 배인지**로 판단함.'])
page_break()

# ════════════════════════════ 5. 팀 구성 ════════════════════════════
H('5. 팀 구성 및 역할')
T([['이름', '역할', '담당 업무', '이 보고서와의 관계'],
   ['대천', '팀장 · 웹', '일정 관리, 군집 결과 검증(대안 비교·규칙 대조군·경계 분석), 유형 이름·판정 정리, 웹 서비스 구현', '군집 검증, 유형별 영양 판정 기준'],
   ['지연', '고객 군집화', '생활습관 변수 전처리, 2단계 k-medoids 모델, k 선택, 웹용 군집 모델(JSON)', '고객 군집화 모델'],
   ['유환', '유형별 부족 영양소', '부족 여부 정의(KDRI), 부족 확률 예측 모델, 2024 검증·민감도 분석, 화면 표시 규칙과 웹용 안내표', '부족 영양소 예측·안내'],
   ['재준', '개인 맞춤 예측', '개인 응답 기반 부족 영양소 예측 모델', '범위 밖 (별도 보고)'],
   ['준혁', '영양제 안내', '개인 예측 결과 기반 제품 필터링·안내', '범위 밖 (별도 보고)']],
  '팀 구성과 역할', widths=[1.6, 2.6, 7.6, 4.7], first_col_bold=True, align_num=False)

# ════════════════════════════ 6. 진행 일정 ════════════════════════════
H('6. 진행 일정')
T([['일자', '단계', '주요 내용', '상태'],
   ['10/29 (1일차)', '주제 선정', '프로젝트 가이드 확인, 서비스 주제 결정', '완료'],
   ['10/30 (2일차)', '기획', '프로젝트 기획서 제출', '완료'],
   ['11/2 (3일차)', '데이터 수집·전처리, 기초 EDA', 'KNHANES 2022–2024 통합, 결측 처리, 분석용 변수 생성. 분포 확인으로 2024년 수면 측정 차이·점심 결식 쏠림 발견', '완료'],
   ['11/3 (4일차)', '모델 설계·1차 모델링 (공식 일정보다 먼저 시작)', '데이터 명세서 제출, 12개 유형 확정, 부족 확률 모델 학습·2024 검증, 민감도 분석, 화면 표시 규칙 결정', '완료'],
   ['11/4 (5일차)', 'EDA 보완·보고서 초안', '상관·다중공선성 점검, 기술통계·교차표 보완, 결과 보고서 초안 작성', '완료'],
   ['11/5~6 (6~7일차)', '모델 고도화', '개인 맞춤 분석 연동, 평가 전략 보완', '완료'],
   ['11/9 (8일차)', '문서화', '최종 결과 보고서·발표 자료 제출 (18:00)', '완료'],
   ['11/10 (9일차)', '발표', '발표 및 상호 평가, 전체 코드 제출', '예정']],
  '진행 일정 (제출일 11/9 기준)', widths=[2.8, 3.4, 8.3, 2], first_col_bold=True, align_num=False)

# ════════════════════════════ 7. 목표 ════════════════════════════
H('7. 목표와 달성 결과')
P('목표와 판단 기준은 결과를 보기 전에 정했습니다. 결과를 본 뒤 기준을 바꾸면 좋은 결과만 고르는 셈이 되기 때문입니다. '
  '다만 아래 표의 마지막 두 행(확률의 신뢰성, 결과의 견고성)은 미리 정한 수치 기준이 없어 **사후 점검 항목**으로 따로 표시했습니다.')
T([['목표', '판단 지표', '기준', '결과', '판정'],
   ['재현 가능한 유형', '대분류 시드 10개 간 평균 ARI', '≥ 0.8', '0.945', '달성'],
   ['', '웹 모델만으로 다시 배정했을 때 일치율', '100%', '100%', '달성'],
   ['해석 가능한 유형', '유형 이름에 쓴 특징이 실제 평균과 일치 (|z| ≥ 0.3)', '전부', '33 / 33', '달성'],
   ['유형의 추가 정보', '성별·연령 모델 대비 2024 AUC 향상의 95% CI > 0', '영양소별', '13 / 15', '대부분 달성'],
   ['미래 자료 일반화', '학습 자료로 고른 안내 항목의 2024년 관측/기대 비', '> 1 (CI 하한 > 1)', '1.087 [1.056, 1.121]', '달성'],
   ['(사후 점검) 확률의 신뢰성', '예측 확률과 실제 비율의 차이 (보정 오차)', '사전 기준 없음', '최대 1.7%p', '양호'],
   ['(사후 점검) 결과의 견고성', '민감도 조건에서 안내 결과 일치율', '사전 기준 없음', '98.7~99.4%', '양호']],
  '목표, 판단 기준과 달성 결과', widths=[3.2, 6, 2.4, 3, 1.9], align_num=True, hl_rows=(6, 7))
P('비타민D·E는 유형별 차이가 확인되지 않았습니다(8.5절 (4) 참고). 거의 모든 사람이 부족해서 유형으로 더 가를 여지가 없기 때문이며, 두 영양소는 공통 안내로만 씁니다.', 9, INK2)
page_break()

# ════════════════════════════ 8. 데이터와 분석 과정 ════════════════════════════
H('8. 데이터 설명 및 분석 과정')
H('8.1 데이터 개요', 2)
ny = S['n_year']
T([['구분', '내용'],
   ['원천', '질병관리청 국민건강영양조사(KNHANES) 2022–2024 원시자료'],
   ['대상', f'19세 이상 성인 중 생활습관 변수에 결측이 없는 15,062명 (2022년 {ny["2022.0"]:,} · 2023년 {ny["2023.0"]:,} · 2024년 {ny["2024.0"]:,}명), 가중 남성 비율 {S["male_pct"]:.1f}%, 가중 평균 나이 {S["age_mean"]:.1f}세'],
   ['생활습관 변수 (14)', '유산소 실천, 근력운동 일수, 좌식 시간, 수면 시간, 스트레스 인지, 아침·점심·저녁 식사 빈도, 외식 빈도, 현재 흡연, 하루 흡연량, 월 음주, 음주 빈도, 1회 음주량'],
   ['영양 변수 (15)', '단백질, 비타민A·D·E·C, 티아민, 리보플라빈, 엽산, 칼슘, 인, 칼륨, 마그네슘, 철, 아연, 식이섬유의 하루 섭취량'],
   ['기준', '2025 한국인 영양소 섭취기준(KDRI) — 성별 2 × 연령대 5(19–29, 30–49, 50–64, 65–74, 75세 이상)'],
   ['가중치', '조사 가중치 wt_tot ÷ 3 (3개년 통합, 이용지침서 방식). 비율 계산과 모델 학습에 사용']],
  '데이터 개요', widths=[3.3, 13.2], first_col_bold=True, align_num=False)

H('8.2 전처리 및 Feature Engineering', 2)
P('결측 제외·표준화처럼 자료를 정리하는 단계와, 군집과 예측에 쓸 변수를 새로 만들거나 고르는 Feature Engineering 단계를 나눠 정리했습니다.')
T([['구분', '단계', '처리', '이유'],
   ['전처리', '결측 제외', '생활습관 14개 변수에 결측이 없는 성인만 사용 (15,062명)', '군집 입력과 웹 재현에 같은 사람이 필요함'],
   ['', '표준화', '군집 지표 7개를 z화 (평균 0, 표준편차 1)', '분 단위 좌식 시간과 0/1 변수의 척도 차이 제거'],
   ['', '선형 변환만 사용', '평균·표준편차·투영 행렬을 JSON으로 저장', '웹에서 같은 계산을 그대로 재현하기 위함'],
   ['Feature Engineering', '수면 연도 보정', '연도별로 표준화한 뒤 2024년 분포로 환원', '2024년만 수면이 길게 측정됨 (평균 6.97 / 6.82 / 7.41시간). 보정하지 않으면 조사 연도가 군집을 만듦'],
   ['', '식사 규칙성 점수', '아침·점심·저녁 빈도의 z값 평균 → 변수 1개', '점심을 거의 안 먹는 838명이 변수 하나로 군집을 이루는 문제 해소'],
   ['', '흡연·음주 제외 (변수 선택)', '군집 입력에서 빼고 결과 설명용으로만 사용', '포함하면 흡연 하나가 군집 분산의 96%를 설명해 다른 습관을 가림 (8.3, 8.4절)'],
   ['', 'PCA 5성분', '7개 지표 → 주성분 5개 (누적 설명분산 78.0%)', '중복 정보 축소'],
   ['', '목표 변수 생성', '사람마다 본인 성별·연령대 KDRI와 비교해 부족(1)/충분(0)', '기준이 성별·나이마다 다름']],
  '전처리와 Feature Engineering 단계', widths=[2.6, 2.9, 5, 6], first_col_bold=True, align_num=False)

H('8.3 탐색적 데이터 분석 (EDA)', 2)
H('(1) 범주형 변수 빈도', 3)
fq = S['freq']
T([['구분', '남성', '여성', '19–29세', '30–49세', '50–64세', '65–74세', '75세 이상'],
   ['인원 (명)'] + [f'{fq["sex"][k][0]:,}' for k in ['남자', '여자']] + [f'{fq["age_grp"][k][0]:,}' for k in ['19-29', '30-49', '50-64', '65-74', '75+']],
   ['가중 비율'] + [f'{fq["sex"][k][1]}%' for k in ['남자', '여자']] + [f'{fq["age_grp"][k][1]}%' for k in ['19-29', '30-49', '50-64', '65-74', '75+']]],
  '성별·연령대 빈도 (15,062명)', widths=[2.6, 1.9, 1.9, 2, 2, 2, 2, 2.1],
  note='표본은 여성과 50세 이상이 많지만(응답률 차이), 조사 가중치를 적용하면 성별은 거의 반반이고 연령 구성도 성인 인구와 맞춰집니다. 이후 비율과 모델 학습은 모두 가중치를 적용했습니다.')
H('(2) 생활습관 변수 기술통계와 분포', 3)
desc = pd.read_csv(FIG / 't_생활습관_기술통계.csv', encoding='utf-8-sig')
rows = [['변수', '가중 평균', '표준편차', '최소', 'Q1', '중앙값', 'Q3', '최대', '왜도', '첨도']] + \
       [[r.변수, f'{r._2:.2f}', f'{r.표준편차:.2f}', f'{r.최소:g}', f'{r.Q1:g}', f'{r.중앙값:g}', f'{r.Q3:g}', f'{r.최대:g}', f'{r.왜도:.2f}', f'{r.첨도:.2f}']
        for r in desc.itertuples()]
T(rows, '생활습관 변수 기술통계 (15,062명)', widths=[3.5, 1.5, 1.5, 1.2, 1.2, 1.4, 1.2, 1.3, 1.3, 1.4], size=7.5,
  note='사분위수(Q1·중앙값·Q3)와 왜도·첨도는 가중치 없이 계산했습니다. 첨도는 정규분포를 0으로 둔 값입니다.')
P('성인의 절반 정도가 유산소 활동을 실천하고(0.49), 근력운동은 주 평균 1일이며 중앙값은 0일입니다. 하루 앉아 있는 시간은 평균 약 9시간(544분)입니다. '
  '아침 식사 빈도의 평균이 1.95로 점심(2.82)·저녁(2.86)보다 뚜렷이 낮아, **끼니 차이는 주로 아침 결식**에서 나옵니다. '
  '점심·저녁 빈도는 왜도 −3.5, −3.9로 "매일 먹음"에 몰려 있고, 흡연량은 왜도 3.4로 0에 몰려 있습니다. '
  '14개 중 4개가 0/1 변수이고 나머지도 순서형이거나 한쪽으로 치우쳐 정규분포로 볼 수 없으므로, **상관은 피어슨 대신 순위 기반인 스피어만 상관**으로 계산했습니다.')
F(FIG / 'f02_상관.png', '생활습관 변수 간 스피어만 상관 (|r| ≥ 0.3만 숫자 표시)', 13.5)
vif = S['vif']
cl7 = ['유산소 실천(0/1)', '근력운동(일/주)', '좌식 시간(분/일)', '수면(시간/일)', '스트레스 인지(0/1)', '아침 빈도(0~3)', '점심 빈도(0~3)', '저녁 빈도(0~3)', '외식 빈도(0~6)']
T([['변수 묶음', '상관', '분산팽창계수(VIF' + fn('VIF') + ')', '판단'],
   ['흡연 2개 · 음주 3개', '흡연 유무–흡연량 1.00, 월 음주–음주 빈도 0.89, 음주 빈도–음주량 0.81',
    f'{min(vif[k] for k in vif if k not in cl7):.2f} ~ {max(vif.values()):.2f}', '서로 강하게 겹침 → 군집 입력에서 제외'],
   ['군집 입력 지표 9개 (식사 3개는 통합)', '모두 |r| < 0.3', f'{min(vif[k] for k in cl7):.2f} ~ {max(vif[k] for k in cl7):.2f}', '다중공선성 없음 → 그대로 사용']],
  '상관과 다중공선성 진단', widths=[3.6, 6.4, 2.8, 3.7], align_num=False,
  note='VIF는 14개 변수를 모두 넣은 회귀에서 계산했습니다. 일반적으로 5~10 이상이면 다중공선성을 의심합니다.')
H('(3) 유형별 성별·연령 구성 (교차표)', 3)
xs = pd.read_csv(FIG / 't_유형x성별.csv', encoding='utf-8-sig', index_col=0)
xa = pd.read_csv(FIG / 't_유형x연령대.csv', encoding='utf-8-sig', index_col=0)
rows = [['유형', '남성', '여성', '19–29', '30–49', '50–64', '65–74', '75+']]
for k in xs.index:
    rows.append([k] + [f'{v:.1f}' for v in xs.loc[k, ['남자', '여자']]] + [f'{v:.1f}' for v in xa.loc[k]])
T(rows, '12개 유형 × 성별, 12개 유형 × 연령대 (유형 안 가중 비율, %)', widths=[1.8, 2, 2, 2.1, 2.1, 2.1, 2.1, 2.1], size=8,
  note='유형은 성별·연령을 입력으로 쓰지 않았지만 구성은 다릅니다. N1은 65세 이상이 68%, O1은 50세 미만이 80%이고, A3·O3는 남성이 2/3 이상입니다.')
P('유형과 성별의 연관은 Cramér V' + fn('Cramér V') + ' 0.226으로 약한 편입니다(흡연·음주를 넣은 7개 유형 안은 0.418). '
  '그래도 성별·연령 구성이 유형마다 다르므로, 영양 부족은 반드시 **같은 성별·연령대와 비교한 배수**로 판단합니다(8.5절).')
H('(4) 유형별 비교 (박스플롯)', 3)
F(FIG / 'f09_유형별_섭취량.png', '유형별 하루 단백질·철 섭취량 (성별·연령 보정 전, 상자 = Q1~Q3, 수염 = 1.5×IQR, 이상값 생략, ◆ = 가중 평균)', 15)
F(FIG / 'f10_유형별_좌식.png', '유형별 하루 좌식 시간 (상자 = Q1~Q3, 수염 = 1.5×IQR, ◆ = 가중 평균)', 15)
B(['**섭취량**: N1·N2(비활동형)의 단백질 중앙값은 약 52g으로 가장 낮고, A3·O3가 가장 높음. 철도 N2의 중앙값(6.5mg)이 가장 낮음.',
   '**주의**: 이 그림은 성별·연령 보정 전이라 남성 비율이 높은 A3·O3가 높게 나오고, 65세 이상이 많은 N1이 낮게 나옴. 보정 후 비교는 8.5절 (5)의 배수 그림으로 함.',
   '**좌식 시간**: 좌식·외식형(O1~O3)은 중앙값 약 700분으로 가장 길고, A1(뚜벅이 갓생러)이 약 400분으로 가장 짧음. 유형 이름과 실제 분포가 일치함.'])

H('8.4 고객 군집화', 2)
H('(1) 초기 모델의 문제 진단', 3)
P('처음 만든 군집(무작위 초기값 1회, 2,000명 표본)은 시드를 바꿀 때마다 결과가 달라졌고(시드 간 ARI 0.56), 흡연 한 변수가 군집 분산의 96%를 설명했습니다. '
  '즉 "생활습관 유형"이 아니라 사실상 "흡연·음주 여부"로 나뉜 상태였습니다.')
T([['변수', '개선 전 (k=7)', '개선 후 (k=4)'],
   ['흡연 여부', '0.964', '0.011'], ['월 음주', '0.916', '0.030'], ['음주 빈도', '0.774', '0.034'],
   ['스트레스', '0.110', '**0.661**'], ['유산소 실천', '0.157', '**0.404**'], ['외식 빈도', '0.239', '**0.308**'],
   ['근력운동', '0.148', '**0.296**'], ['좌식 시간', '0.126', '**0.187**']],
  '변수별 η²' + fn('η²') + ' (군집 간 분산 비율) — 개선 전후', widths=[4.5, 3.5, 3.5],
  note='개선 후에는 서비스가 안내하려는 스트레스·운동·외식·좌식이 군집을 결정합니다.')
H('(2) 대분류 개수(k) 선택', 3)
T([['k', '총거리 (엘보우)', '실루엣', '시드 간 평균 ARI', '최소 ARI'],
   ['3', '27,918', '**0.182**', '**1.000**', '1.000'], ['**4 (선택)**', '**26,436**', '0.163', '**0.945**', '0.725'],
   ['5', '25,257', '0.154', '0.857', '0.773'], ['6', '24,280', '0.162', '0.572', '—']],
  '대분류 개수별 비교 (7개 지표 PCA 5성분, 전체 15,062명)', widths=[2.6, 3.2, 2.4, 3.4, 2.4], hl_rows=(2,))
F(MATCHUM / 'Jiyeon' / 'k_selection.png', '대분류 개수 선택 — 엘보우·실루엣·안정성', 15)
B(['안정성 기준(평균 ARI ≥ 0.8)을 만족하는 것은 k = 3, 4, 5이고 k = 6에서 0.57로 급락함.',
   'k = 3은 실루엣이 가장 높지만 유형이 3개뿐이라 서비스 유형으로는 너무 거칢.',
   'k = 4는 안정성을 유지하면서 세분화가 가능한 최소 지점임. k = 5는 평균 ARI(0.857)와 실루엣(0.154) 모두 k = 4보다 낮음. 최소 ARI는 k = 5(0.773)가 k = 4(0.725)보다 높지만, 판단은 시드 10개의 평균 ARI 기준으로 함.'])
H('(3) 세부 군집', 3)
P('대분류 안에서 남은 편차가 큰 변수의 2~3개 조합을 모두 시험했습니다. 시드 간 ARI ≥ 0.95, 가장 작은 군집 ≥ 12%, 두 변수가 고르게 기여하는 조합 중 실루엣이 높은 것을 골랐습니다.')
T([['대분류', '세분화 변수', '세부 군집 수', '실루엣', '시드 간 ARI'],
   ['비활동형', '외식 + 식사 규칙성', '3', '0.514', '1.00'], ['운동형', '근력운동 + 식사 규칙성', '3', '0.579', '1.00'],
   ['고스트레스형', '유산소 + 근력운동', '3', '0.859', '1.00'], ['좌식·외식형', '근력운동 + 식사 규칙성', '3', '0.595', '1.00']],
  '대분류별 세부 군집', widths=[3, 5, 2.5, 2.3, 2.5])
P('운동형은 처음에 "유산소 + 근력"(실루엣 0.798)이 뽑혔지만, 실루엣 대부분이 0/1 변수에서 나오고 623명짜리 작은 군집이 생겨 "근력 + 식사 규칙성"으로 바꿨습니다. '
  '실루엣은 변수 구성이 다르면 직접 비교할 수 없으므로, 교체 판단은 **변수 기여의 균형**과 **군집 크기의 균형**으로 했습니다.', 9.5)
H('(4) 대안 비교와 검증', 3)
T([['지표', '7개 유형 (비교안)', '12개 유형 (채택)'],
   ['재학습 안정성 (표본 40% × 20회 ARI, 두 안 공통 15,060명·같은 표본)', '**0.911**', '0.679'],
   ['흡연·음주를 가르는 정도 (η²)', '0.58', '0.04'],
   ['운동을 가르는 정도 (η²)', '0.32', '**0.71**'],
   ['좌식·수면·스트레스를 가르는 정도 (η²)', '0.03', '**0.31**'],
   ['성별 쏠림 (Cramér V, 낮을수록 좋음)', '0.418', '**0.226**'],
   ['영양 차이 (성별·연령·총 섭취량 보정)', '0.097', '0.096'],
   ['2024 예측 AUC (성별·연령 + 유형)', '0.635', '0.632']],
  '7개 유형 안과 12개 유형 안 비교 (같은 사람, 같은 지표)', widths=[7.5, 4, 4],
  note='영양 설명력은 같습니다. 7개 안은 더 안정적이지만 흡연·음주가 유형을 주도하고 성별 쏠림이 두 배입니다. 서비스가 안내하려는 운동·좌식·스트레스를 담는 12개 안을 택했습니다.')
T([['확인', '결과', '의미'],
   ['얕은 결정나무로 12개 유형 재현', '질문 2개 32.9%, 4개 65.9%, 6개 79.1%', '몇 문항으로 거르는 단순 필터가 아님'],
   ['사람이 정한 규칙(중앙값 기준 16개)과 비교', '영양 차이 0.096 vs 0.096, AUC 0.630 vs 0.632', '규칙보다 영양을 더 잘 맞히지는 않음 → 유형은 설명 용도'],
   ['표본을 바꿔 다시 학습 (표본 40% × 20회, 전체 15,062명)', 'ARI 0.697, 재학습 1회에 바뀌는 사람 19.1%', '경계 근처 사람이 많음. 경계에서 먼 41%는 9%만 바뀜'],
   ['영양 안내에 미치는 영향', '재학습마다 안내가 달라지는 사람 약 8%', '웹은 고정 모델로 같은 응답이면 같은 유형']],
  '규칙 대조군과 안정성 점검', widths=[4.6, 5.6, 6.3], align_num=False,
  note='재학습 안정성 0.679(앞 표)와 0.697(이 표)은 계산 방식이 같고(표본 40%로 다시 학습해 전체를 배정한 뒤 원래 결과와 비교, 20회 평균), '
       '대상 인원(7개 안과 공통인 15,060명 / 전체 15,062명)과 무작위 표본만 다릅니다. 따라서 재학습 안정성은 0.68~0.70 범위로 봅니다.')
H('(5) 최종 12개 유형', 3)
types = [('비활동형', 'N1', '집밥좋아 나무늘보', '1,802', '8.7%', '외식 최저, 세 끼 규칙적'),
         ('', 'N2', '배고픈 나무늘보', '1,258', '8.1%', '운동 적고 끼니를 자주 거름 (아침 1.28)'),
         ('', 'N3', '배부른 나무늘보', '1,429', '8.3%', '끼니는 규칙적이지만 운동·활동이 적음'),
         ('운동형', 'A1', '뚜벅이 갓생러', '1,542', '9.3%', '유산소 99%, 좌식 403분으로 최단'),
         ('', 'A2', '파워 갓생러', '1,124', '8.4%', '근력 주 2.7일, 아침 1.23으로 불규칙'),
         ('', 'A3', '밸런스 갓생러', '1,505', '9.3%', '근력 주 4.4일(최고), 식사 규칙적'),
         ('고스트레스형', 'S1', '쉬고 싶은 예민보스', '1,561', '11.0%', '스트레스 91%, 운동 없음, 수면 6.99시간'),
         ('', 'S2', '산책하는 예민보스', '1,429', '10.5%', '스트레스 82%, 유산소 100%'),
         ('', 'S3', '쇠질하는 예민보스', '454', '3.6%', '스트레스 97%(최고), 근력 주 3.2일, 외식 최다'),
         ('좌식·외식형', 'O1', '아침패스 워커홀릭', '1,228', '10.0%', '좌식 677분, 아침 0.79로 최저'),
         ('', 'O2', '삼시세끼 워커홀릭', '1,137', '8.0%', '좌식·외식 많지만 세 끼 챙김'),
         ('', 'O3', '운동하는 현대인', '593', '4.7%', '근력 주 3.1일, 좌식 708분으로 최장')]
T([['대분류', 'ID', '유형 이름', '인원', '가중 비율', '특징']] + [list(x) for x in types],
  '최종 12개 생활습관 유형', widths=[2.5, 1.1, 3.6, 1.6, 1.8, 5.9], align_num=True)
F(FIG / 'f04_유형프로필.png', '12개 유형의 생활습관 프로필 (전체 평균 대비 표준화 점수, 조사 가중. 오른쪽 2열은 군집에 쓰지 않은 참고 변수)', 16)
page_break()

H('8.5 유형별 부족 영양소 예측', 2)
H('(1) 문제 설정', 3)
T([['항목', '내용'],
   ['목표 변수', '영양소 15개 각각의 부족 여부 (본인 성별·연령대 KDRI 미만 = 1)'],
   ['입력 변수', '생활습관 유형(12) + 성별 + 연령대(5). 설문 첫 화면에서 바로 알 수 있는 정보만 사용'],
   ['제외 변수', '섭취량(에너지 포함)은 사용자가 모르고 정답을 만든 재료이므로 넣지 않음 (정보 누수 방지)'],
   ['출력', '유형 × 성별 × 연령대 120개 조합마다 영양소별 부족 확률과 "같은 성별·연령대 평균 대비 배수"'],
   ['기준 모델', '성별 + 연령대만 쓴 로지스틱 회귀. 유형을 더했을 때의 향상으로 유형의 가치를 판단']],
  '예측 문제 설정', widths=[3, 13.5], first_col_bold=True, align_num=False)
H('(2) 평가 전략', 3)
B(['**연도 분할** — 2022–23년(9,742명)으로 학습하고 2024년(5,320명)으로 평가함. 무작위 분할보다 엄격하며, 내년 사용자에게도 통하는지를 봄.',
   '**하이퍼파라미터** — 학습 자료 안에서만 5겹 교차검증으로 고름. 지표는 조사 가중 로그 손실' + fn('로그 손실') + '(확률의 정확도)임.',
   '**1-SE 규칙' + fn('1-SE') + '** — 손실이 가장 작은 모델과 1 표준오차 안에서 차이가 나지 않으면 더 단순한 모델을 고름. 작은 차이를 좇다 과적합하는 것을 막음.',
   '**유의성** — 2024년 AUC 향상의 95% 신뢰구간을 부트스트랩 2,000회로 구하고, 하한이 0보다 크면 "유형이 도움이 된다"고 판단함.'])
H('(3) 모델 후보와 하이퍼파라미터', 3)
T([['모델', '특징', '하이퍼파라미터', '탐색 범위'],
   ['로지스틱 회귀 (가법)', '해석이 쉽고 확률이 안정적', 'C (규제 강도의 역수)', '0.01, 0.1, 1, 10'],
   ['로지스틱 회귀 + 유형×성별', '유형 효과가 성별에 따라 다를 수 있음', 'C', '0.1, 1'],
   ['그래디언트 부스팅 (HistGB)', '비선형·상호작용 자동 반영', '학습률 × 최대 잎 수', '{0.05, 0.1} × {7, 15}, 잎당 최소 100명, 200회']],
  '모델 후보와 탐색 범위 (영양소마다 10개 후보 비교)', widths=[4.2, 4.6, 3.6, 4.1], align_num=False)
tune = pd.read_csv(OUT8 / '08_튜닝기록.csv', encoding='utf-8-sig')
nm = lambda s: (s.replace('LR가법_C', '로지스틱 C=').replace('LR교호_C', '로지스틱+유형×성별 C=')
                .replace('HGB_lr', '부스팅 학습률 ').replace('_leaf', ', 잎 '))
rows = [['후보', 'CV 로그 손실', '표준오차', 'CV AUC', '선택']]
for r in tune[tune['영양소'] == '단백질'].itertuples():
    rows.append([nm(r.후보), f'{r.CV로그손실:.4f}', f'{r.SE:.4f}', f'{r.CV_AUC:.3f}', '✓' if r.선택 else ''])
T(rows, '하이퍼파라미터 선정 과정 예시 — 단백질 (2022–23년 5겹 교차검증)', widths=[6, 2.8, 2.4, 2.4, 1.6], hl_rows=(2,),
  note='손실 최소는 C=0.1(0.5161)입니다. 더 단순한 C=0.01(0.5190)은 최소 + 1 표준오차(0.5189)를 넘어 선택되지 않았습니다. '
       '15개 영양소 결과는 C=0.01이 10개, C=0.1이 4개(단백질·엽산·마그네슘·식이섬유), 부스팅이 1개(철)이며, 영양소별 최종값은 첨부 D에 정리했습니다.')
H('(4) 2024년 평가 결과', 3)
V = pd.read_csv(OUT8 / '08_2024검증.csv', encoding='utf-8-sig')
sel = lambda s: nm(s).replace('부스팅 학습률 0.05, 잎 7', '부스팅')
rows = [['영양소', '기준', '2024 부족률', '선택 모델', '기준 모델 AUC', '유형 추가 AUC', 'ΔAUC [95% CI]']]
for r in V.itertuples():
    rows.append([r.영양소, r.기준, f'{r.부족률_2024 * 100:.1f}%', sel(r.선택), f'{r.M0_Test_AUC:.3f}', f'{r.Test_AUC:.3f}',
                 f'{r.ΔAUC:+.3f} [{r.ΔAUC_CI_low:+.3f}, {r.ΔAUC_CI_high:+.3f}]'])
T(rows, '영양소별 2024년 평가 결과', widths=[2.2, 1.3, 2, 3.2, 2.3, 2.3, 3.6], size=8,
  hl_rows=tuple(i + 1 for i, r in enumerate(V.itertuples()) if r.ΔAUC_CI_low <= 0))
F(FIG / 'f06_ΔAUC.png', '유형을 추가했을 때의 AUC 향상과 95% 신뢰구간 (2024년 평가)', 14)
au = S['auc']
B([f'**13개 영양소에서 유형이 성별·나이 이상의 정보를 줌.** 비타민D·E는 신뢰구간이 0을 포함함 (표에서 강조한 행).',
   f'과적합은 작음: 학습 − 평가 AUC 차이는 최대 {au["over_max"]:.3f}임.',
   '예측 확률과 실제 비율의 차이(보정 오차)는 10분위 기준 최대 1.7%p로, 확률을 그대로 "10명 중 N명"으로 써도 됨.',
   f'AUC 자체는 {au["test_min"]:.2f}~{au["test_max"]:.2f}로 중간 수준임. 유형과 성별·나이만으로 개인의 부족 여부를 정확히 가를 수는 없음.'])
T([['방식', '평균 안내 개수', '정밀도' + fn('정밀도'), '재현율', 'F1'],
   ['공통 8개 고정', '8.00', '0.749', '0.808', '0.777'],
   ['성별·연령 모델 (확률 ≥ 0.5)', '8.80', '0.733', '0.853', '0.788'],
   ['유형 추가 모델 (확률 ≥ 0.5)', '8.62', '0.739', '0.845', '0.789']],
  '부족 영양소 목록을 맞히는 정확도 (2024년, 개인 단위)', widths=[5.6, 2.8, 2.4, 2.4, 2.2],
  note='목록 자체의 정확도는 세 방식이 비슷합니다. 유형의 가치는 목록을 맞히는 데보다 "같은 성별·나이보다 몇 배 더 부족한지"를 보여 주는 데 있습니다. 이 결과가 8.6절 표시 규칙의 근거입니다.')
H('(5) 유형별 부족 패턴', 3)
F(FIG / 'f05_유형x영양소_배수.png', '유형 × 영양소: 같은 성별·연령대 평균 대비 부족 확률 배수 (성별·연령대 10개 조합 평균)', 16.5)
B(['**N2 배고픈 나무늘보, S1 쉬고 싶은 예민보스, O1 아침패스 워커홀릭**은 철·인·단백질·아연에서 평균보다 1.2~1.7배 더 부족함. 셋 다 끼니를 자주 거르거나 활동이 적은 유형임.',
   '**A3 밸런스 갓생러, O2 삼시세끼 워커홀릭, N3 배부른 나무늘보**는 대부분 영양소에서 평균보다 덜 부족함(0.67~0.9배). 세 끼를 규칙적으로 먹는 유형임.',
   '공통 영양소 8개(오른쪽)는 유형 간 차이가 작음(대부분 0.95~1.05배). 공통 영양소를 따로 묶는 설계가 맞다는 근거임.'])
T([['판정', '기준', '해당 (유형: 영양소)'],
   ['공통 주의 영양소', '전체 부족률 ≥ 50%', '비타민A·D·E·C, 엽산, 칼슘, 칼륨, 식이섬유 (8개)'],
   ['유형 고유 영양소', '성별·연령·총 섭취량(5분위)까지 같은 사람과 비교해도 1.2배 이상, BH-FDR' + fn('BH-FDR') + ' q < 0.05', 'N2: 인·철 / S1: 인'],
   ['식사량 관련 영양소', '성별·연령만 맞추면 더 부족하지만 총 섭취량까지 맞추면 차이가 사라짐', 'N2: 단백질·티아민·리보플라빈·마그네슘·아연 / A2: 아연 / S1: 단백질·철']],
  '유형별 영양소 판정 기준', widths=[3.2, 7, 6.3], first_col_bold=True, align_num=False,
  note='다중검정 보정은 BH-FDR(Benjamini–Hochberg)을 썼습니다. 180개(12유형 × 15영양소) 조합에서 "살펴볼 후보"를 고르는 목적이라 거짓 발견 비율을 관리하는 방식이 적합합니다. 하나도 틀리면 안 되는 상황에 쓰는 Holm 보정은 너무 엄격해 유형 차이를 대부분 지웁니다.')
H('(6) 민감도 분석', 3)
T([['조건', '설명', '안내 일치율', '확률 차이 평균 (최대)', '유형 효과 판정'],
   ['에너지 제한', '하루 에너지 500~5,000kcal만', '99.4%', '0.7%p (10.1%p)', '비타민E·칼륨 경계에서 바뀜'],
   ['평소 식사일', '평소처럼 먹었다고 답한 날만', '98.7%', '1.5%p (16.2%p)', '모두 같음'],
   ['둘 다', '두 조건 모두 적용', '98.7%', '1.2%p (12.0%p)', '칼륨 경계에서 바뀜']],
  '민감도 분석 (120개 조합 × 15개 영양소 = 1,800개 판정 비교)', widths=[2.6, 4.6, 2.2, 3.5, 3.6], align_num=False,
  note='특이한 날의 기록을 빼도 안내 결과는 98.7% 이상 같았습니다. 다만 비타민E·칼륨은 유형 효과가 조건에 따라 뒤집혀, 비타민D와 함께 유형별 안내 없이 공통 안내로만 씁니다.')
H('(7) 개선 실험 — 변수 추가와 모델 결합', 3)
F(FIG / 'f07_피처모델.png', '변수 묶음·모델별 2024년 평가 AUC (영양소 15개 평균)', 14)
fe = S['feat']
T([['변수 묶음', '로지스틱 회귀', '그래디언트 부스팅', '앙상블 (평균)'],
   ['유형 + 성별 + 연령대 (채택)', f'{fe["F0_LR"]["Test_AUC"]:.3f}', f'{fe["F0_HGB"]["Test_AUC"]:.3f}', f'{fe["F0_ENS"]["Test_AUC"]:.3f}'],
   ['+ 나이 곡선, 유형×성별', f'{fe["F1_LR"]["Test_AUC"]:.3f}', f'{fe["F1_HGB"]["Test_AUC"]:.3f}', f'{fe["F1_ENS"]["Test_AUC"]:.3f}'],
   ['+ 생활습관 응답 14개', f'{fe["F2_LR"]["Test_AUC"]:.3f}', f'{fe["F2_HGB"]["Test_AUC"]:.3f}', f'{fe["F2_ENS"]["Test_AUC"]:.3f}'],
   ['+ 채소·과일 섭취 빈도', f'{fe["F3_LR"]["Test_AUC"]:.3f}', f'{fe["F3_HGB"]["Test_AUC"]:.3f}', f'{fe["F3_ENS"]["Test_AUC"]:.3f}']],
  '개선 실험 결과 (2024년 평가 AUC, 영양소 15개 평균)', widths=[6, 3.4, 3.6, 3.4], hl_rows=(1,))
B(['**모델을 복잡하게 해도 나아지지 않음.** 부스팅은 로지스틱 회귀보다 낮고, 앙상블도 차이가 0.003 이내임.',
   '**개인 응답을 더 넣으면 AUC가 +0.030 오름.** 하지만 이는 유형이 아니라 개인 응답을 쓰는 예측이므로 개인 맞춤 분석 단계의 몫임. 유형 화면은 "같은 유형 사람들의 경향"을 보여 주는 단계라 유형·성별·연령대 모델을 유지함.'])
page_break()

H('8.6 화면 표시 규칙 설계', 2)
P('예측 확률을 그대로 보여 주면 안 됩니다. 공통 영양소 8개가 거의 모든 조합에서 상위를 차지해, 유형이 달라도 화면이 비슷해지기 때문입니다. 세 가지 규칙을 120개 조합에 적용해 비교했습니다.')
ru = S['rules']
T([['비교 항목', '확률 기준 표시', '2단 표시 (채택)', '상위 3개 표시'],
   ['규칙', '부족 확률 ≥ 0.5인 영양소 모두', '공통 8개 한 줄 + 그 밖에서 기준을 넘는 것', '공통 8개 한 줄 + 그 밖에서 확률 상위 3개'],
   ['조합당 표시 개수', f'{ru["확률 기준"]["n"]}개', f'공통 8개 + {ru["2단 표시"]["n"]}개 (총 {ru["2단 표시"]["total"]}개)', '공통 8개 + 3개 (총 360개)'],
   ['같은 성별·연령대에서 유형별로 다른 목록 수 (평균)', f'{ru["확률 기준"]["within"]}', f'{ru["2단 표시"]["within"]}', f'{ru["상위 3개"]["within"]}'],
   ['평균보다 덜 부족한데 "유형 영양소"로 표시', '해당 없음', f'{ru["2단 표시"]["below1"]} / {ru["2단 표시"]["total"]}개 (별도 문구로 구분)', f'{ru["상위 3개"]["below1"]} / 360개'],
   ['10명 중 3명 미만인데 표시', '0개', '0개', f'{ru["상위 3개"]["lowp"]}개'],
   ['"특히 더 부족한 것 없음" 안내', '불가', f'{ru["2단 표시"]["empty"]} / 120개 조합', '불가']],
  '화면 표시 규칙 3가지 비교 (120개 조합, 최종 모델)', widths=[5, 3.6, 4.4, 3.5], align_num=False)
B(['**확률 기준 표시**는 규칙이 가장 단순하지만 화면당 8~9개가 나열되고 공통 영양소에 유형 신호가 묻힘.',
   f'**상위 3개 표시**는 화면이 일정하지만, 평균보다 오히려 덜 부족한 영양소를 "부족"으로 보여 주는 경우가 절반 가까이({ru["상위 3개"]["below1"]}/360) 됨.',
   f'**2단 표시**는 유형 차이를 보여 주면서 과장을 막고(평균보다 덜 부족한 항목 {ru["2단 표시"]["below1"]}/{ru["2단 표시"]["total"]}), 부족이 적은 유형에는 "특히 더 부족한 것은 없다"는 좋은 소식도 줄 수 있어 팀 논의 끝에 채택함.'])
callout('채택한 2단 표시 규칙', [
    '**공통 영역** — 공통 주의 영양소 8개는 확률과 상관없이 항상 "많은 사람에게 부족하기 쉬워요"로 표시. 조합에 따라 10명 중 3명 정도인 영양소도 있어(최저 0.26) "대부분"이라고 쓰지 않음',
    '**유형 영역** — 그 밖의 영양소 중 ① 부족 확률 ≥ 0.5, 또는 ② 같은 성별·연령대 대비 1.2배 이상이면서 부족 확률 ≥ 0.3',
    '**표시 형식** — "내 유형 10명 중 N명 · 같은 성별·나이 평균 10명 중 M명" + 근거 문구',
    '**근거 문구** — 유형 고유 → "이 유형에서 특히 많아요" / 식사량 관련 → "식사량 점검이 먼저예요" / 그 외 → "같은 성별·나이대에서 흔해요"',
    '**유형 영역이 비면** — "공통 영양소 외에 특히 더 부족한 영양소는 없어요"',
    '→ 기준값(1.2배, 0.3)은 결과를 보기 전에 팀 문서로 정하고 고정함. 0.3은 "1.2배지만 10명 중 2명" 같은 과장을 막는 하한임.'], 'F1F8F4', '1BAF7A')
H('2024년 검증', 3)
F(FIG / 'f08_2024검증.png', '2022–23년 자료로만 고른 안내 항목의 2024년 관측/기대 부족 비 (근거 문구별, 95% CI)', 14)
oe = S['oe']
P(f'검증은 2024년 자료를 보지 않은 모델로 해야 하므로, **2022–23년 자료로만 다시 학습한 모델**로 유형 영역 항목을 골랐고 그 수는 {oe["전체"][3]}개입니다. '
  f'(위 표의 {ru["2단 표시"]["total"]}개는 3개년 전체로 학습한 최종 모델 기준이라 개수가 조금 다릅니다.) '
  '이 항목들을 2024년 실제 자료에 대 보니, 같은 성별·연령대 전체 비율로 기대한 인원보다 **1.087배(95% CI 1.056~1.121)** 더 많은 사람이 부족했습니다. '
  f'근거 문구별로는 "이 유형에서 특히 많아요" {oe["유형특이"][0]:.2f}배, "식사량 점검이 먼저예요" {oe["식사량영향"][0]:.2f}배, "같은 성별·나이대에서 흔해요" {oe["흔함"][0]:.2f}배로, '
  '**문구가 말하는 강도와 실제 차이의 순서가 일치**합니다.')
H('서비스 화면 예시', 3)
screen_card('N2 배고픈 나무늘보 · 여성 · 30–49세',
            '비타민D 10명 · 비타민E 9명 · 칼륨 9명 · 엽산 8명 · 비타민A 8명 · 비타민C 8명 · 식이섬유 7명 · 칼슘 7명 (10명 중)',
            [('철', 6, 4, '이 유형에서 특히 많아요'), ('마그네슘', 6, 5, '식사량 점검이 먼저예요'), ('티아민', 6, 5, '식사량 점검이 먼저예요')])
screen_card('A3 밸런스 갓생러 · 남성 · 50–64세', '비타민D 9명 · 비타민E 8명 · 칼슘 7명 · 비타민A 6명 · 비타민C 6명 · 칼륨 6명 · 식이섬유 5명 · 엽산 3명 (10명 중)',
            [], '공통 영양소 외에 특히 더 부족한 영양소는 없어요')
P('화면에는 "질환이 있으면 전문가와 상담하세요"라는 안내와 "음식 섭취 기준, 진단이 아님"이라는 설명을 함께 표시합니다.', 9, INK2)
page_break()

# ════════════════════════════ 9. 인사이트·제언 ════════════════════════════
H('9. 핵심 인사이트 및 비즈니스 제언')
H('9.1 핵심 인사이트', 2)
ins = [('영양 부족은 "누구나"의 문제다', '비타민D·E, 칼륨 등 8개는 유형과 관계없이 성인 절반 이상이 부족함. 개인화보다 일반 정보와 식품 안내가 더 효율적인 영역임.'),
       ('유형 차이의 대부분은 "덜 먹어서" 생긴다', '총 섭취량까지 맞추면 남는 유형 고유 차이는 3건(N2 인·철, S1 인)뿐임. 나머지 차이는 식사량이 적어서 생김. 이런 유형에는 특정 영양제보다 끼니와 식사량 회복을 먼저 안내해야 함.'),
       ('끼니를 지키는 습관이 가장 강한 보호 요인이다', '세 끼를 규칙적으로 먹는 A3·O2·N3는 대부분 영양소에서 평균보다 덜 부족하고, 아침을 거르는 N2·O1·S1은 더 부족함. 운동을 열심히 하는 A2도 끼니가 불규칙하면 철·아연이 더 부족해, 이 자료에서는 운동보다 식사 규칙성이 영양 부족과 더 뚜렷하게 연결됨(인과 관계는 아님).'),
       ('같은 유형 안에서도 사람마다 다르다', '유형은 부족 비율을 바꿀 뿐 모두를 부족하게 만들지 않음. 그래서 "당신은 철이 부족합니다"가 아니라 "10명 중 6명"처럼 비율로 말함.'),
       ('유형은 설명, 정확도는 개인 분석이 맡는다', '개인 응답을 더 쓰면 AUC가 더 오름(+0.030). 유형은 사용자가 자기 생활을 이해하는 입구이고, 정밀한 판단은 개인 맞춤 분석의 몫임.')]
for i, (t_, d_) in enumerate(ins, 1):
    callout(f'인사이트 {i}. {t_}', [d_])
H('9.2 비즈니스 제언', 2)
T([['제언', '근거', '기대 효과'],
   ['첫 화면은 유형과 부족 영양소까지만 보여 주고, 영양제는 개인 맞춤 단계에서 안내', '유형 결과는 경향이지 진단이 아님', '처방처럼 보이는 표현을 피하고 신뢰를 얻음'],
   ['식사량 관련 영양소가 있는 유형(N2·A2·S1)에는 끼니·식사 안내를 먼저', '"식사량 점검" 항목이 2024년에도 1.24배로 확인됨', '불필요한 영양제 구매를 줄이고 서비스 신뢰도를 높임'],
   ['"특히 더 부족한 것은 없어요"를 긍정 피드백으로 활용', '120개 조합 중 40개', '건강한 습관을 강화하고 재방문을 유도함'],
   ['공통 영양소 8개는 식품·생활 콘텐츠(햇빛, 채소·과일, 유제품)로 안내', '많은 사람에게 해당, 유형 차이 작음', '모든 사용자에게 쓸 수 있는 콘텐츠를 한 번에 만듦'],
   ['유형 화면에서 개인 맞춤 분석으로 자연스럽게 연결', '같은 유형 안에서도 개인차가 큼', '심화 분석으로의 전환율을 높임'],
   ['사용자 응답이 쌓이면 유형 경계와 확률을 다시 검증', '경계 근처 사용자가 많음 (재학습 시 안내 변화 약 8%)', '서비스 데이터로 모델을 개선함']],
  '비즈니스 제언', widths=[5.6, 5.4, 5.5], align_num=False)

# ════════════════════════════ 10. 한계 ════════════════════════════
H('10. 한계 및 향후 과제')
T([['한계', '영향', '대응 / 향후 과제'],
   ['군집 분리가 약함 (실루엣 0.163), 표본을 바꿔 학습하면 경계가 움직임 (재학습 안정성 ARI 0.68~0.70: 표본 40% × 20회, 8.4절 (4))', '"한국인은 12개 유형으로 나뉜다"고 말할 수 없음', '고정 모델로 같은 응답이면 같은 유형. 화면에 본인 생활습관 점수를 함께 표시'],
   ['섭취량은 음식만, 하루 기록', '영양제 복용자의 섭취를 과소평가, 개인 평소량과 다를 수 있음', '"진단 아님", "같은 조건 사람들의 비율"로 표현'],
   ['예측력이 중간 수준 (AUC 0.56~0.70)', '개인의 부족 여부를 정확히 가르지 못함', '경향 안내용으로만 쓰고, 개인 판단은 개인 맞춤 분석'],
   ['복합표본 설계(층·집락) 미반영', '신뢰구간이 실제보다 좁을 수 있음', '가중치는 반영함. 향후 층·집락을 반영한 분산 추정'],
   ['인과 관계가 아님', '"이 습관 때문에 부족하다"고 말할 수 없음', '"이 유형에서 많아요" 수준의 표현만 사용'],
   ['비타민D·E·칼륨은 유형 신호가 없거나 불안정', '유형별 안내 불가', '공통 안내로만 사용']],
  '한계와 대응', widths=[5.4, 5.2, 5.9], align_num=False)

# ════════════════════════════ 11. 참고 자료 ════════════════════════════
H('11. 참고 자료')
refs = ['질병관리청. 국민건강영양조사 제9기(2022–2024) 원시자료 및 이용지침서.',
        '보건복지부·한국영양학회 (2025). 2025 한국인 영양소 섭취기준 요약표(2025.12.29) 및 정오표(2026.3.16 3차 수정).',
        'Kaufman, L. & Rousseeuw, P. J. (1990). Finding Groups in Data: An Introduction to Cluster Analysis. Wiley. (k-medoids / PAM)',
        'Hubert, L. & Arabie, P. (1985). Comparing partitions. Journal of Classification, 2, 193–218. (Adjusted Rand Index)',
        'Rousseeuw, P. J. (1987). Silhouettes: a graphical aid to the interpretation and validation of cluster analysis. Journal of Computational and Applied Mathematics, 20, 53–65.',
        'Benjamini, Y. & Hochberg, Y. (1995). Controlling the false discovery rate. Journal of the Royal Statistical Society B, 57(1), 289–300.',
        'Hastie, T., Tibshirani, R. & Friedman, J. (2009). The Elements of Statistical Learning (2nd ed.). Springer. (교차검증과 1-SE 규칙)',
        'Pedregosa, F. et al. (2011). Scikit-learn: Machine Learning in Python. Journal of Machine Learning Research, 12, 2825–2830.']
for i, r_ in enumerate(refs, 1):
    p = P(f'[{i}] {r_}', 8.5, after=1); p.paragraph_format.left_indent = Cm(0.6); p.paragraph_format.first_line_indent = Cm(-0.6); p.paragraph_format.line_spacing = 1.15

# ════════════════════════════ 첨부 ════════════════════════════
page_break()
H('첨부')
H('A. 2025 KDRI 성인 기준 (이 분석에서 사용한 값)', 3)
import sys
sys.path.insert(0, str(HERE.parent / '영양분석'))
from common import KDRI  # noqa
unit = {'단백질': 'g', '비타민A': 'μg RAE', '비타민D': 'μg', '비타민E': 'mg α-TE', '비타민C': 'mg', '티아민': 'mg', '리보플라빈': 'mg',
        '엽산': 'μg DFE', '칼슘': 'mg', '인': 'mg', '칼륨': 'mg', '마그네슘': 'mg', '철': 'mg', '아연': 'mg', '식이섬유': 'g'}
rows = [['영양소', '단위', '기준', '남성 (19–29 / 30–49 / 50–64 / 65–74 / 75+)', '여성 (같은 순서)']]
for n, (_, basis, m, f, *_r) in KDRI.items():
    rows.append([n, unit[n], basis, ' / '.join(f'{v:g}' for v in m), ' / '.join(f'{v:g}' for v in f)])
T(rows, '성별·연령대별 기준값', widths=[2.2, 2.2, 1.4, 5.5, 5.2], size=8,
  note='모든 값을 2025 KDRI 요약표(2025.12.29) 원문(철·아연 xvii쪽, 칼슘·인·칼륨·마그네슘 xvi쪽, 식이섬유 ix쪽)과 정오표(2026.3.16 3차 수정, 성인 기준값 변경 없음)로 다시 대조했습니다. '
       '철 평균필요량은 2020 KDRI(여성 19–49세 11mg, 남성 19–49세 8mg)보다 낮게 개정된 값이며, 이 분석은 2025 개정값을 그대로 씁니다.')
H('B. 산출물과 코드', 3)
T([['파일', '내용'],
   ['Jiyeon/kmedoids_final.py · cluster_report.md · kmedoids_model.json', '군집 모델, k·변수 선택 근거, 웹용 군집 모델'],
   ['bigskyyang/analysis/군집화_결론.md · output/nbti_12types.json', '12개 유형 채택 근거, 대안 비교, 규칙 대조군, 경계 분석, 유형별 영양 판정'],
   ['Yuhwan/영양분석/08_12유형_부족영양소_추천.py', '부족 확률 모델, 하이퍼파라미터 기록, 2024 검증'],
   ['Yuhwan/영양분석/09_민감도_비교.py · 10_피처_모델_비교.py', '민감도 분석, 변수·모델 개선 실험'],
   ['Yuhwan/영양분석/13_유형화면_나안.py · output/13_유형화면_나안.json', '2단 표시 규칙 적용, 2024 검증, 웹 연결용 안내표'],
   ['보고서/make_figs.py · build_report.py', '이 보고서의 그림·표 생성 코드']],
  '산출물 목록 (GitHub Matchum 저장소)', widths=[8, 8.5], align_num=False)
H('C. 예상 질문과 답변', 3)
qa = [('생활습관 군집을 영양소 안내에 연결해도 되나요?', '2024년 자료로 검증했을 때 15개 중 13개 영양소에서 성별·나이만 알 때보다 유의하게 더 잘 구분했습니다. 다만 향상 폭이 크지 않아 경향 안내로만 씁니다.'),
      ('같은 유형인데 왜 모두 같은 영양소가 부족하지 않나요?', '유형은 생활습관으로 나눈 것이고 섭취량은 사람마다 다릅니다. 그래서 "10명 중 N명"으로 비율을 보여 줍니다.'),
      ('군집이 그냥 필터링 아닌가요?', '질문 4개짜리 결정나무로는 66%만 재현됩니다. 여러 습관을 함께 봐야 나오는 구분입니다. 다만 영양 예측력은 사람이 정한 규칙과 같아, 유형은 설명 용도로 씁니다.'),
      ('재학습 안정성이 0.68~0.70인데 왜 12개 유형을 썼나요?', '표본 40%로 20번 다시 학습했을 때의 ARI입니다(7개 안과 같은 표본 0.679, 전체 인원 0.697). 생활습관은 연속적이라 경계 근처 사람이 많습니다. 더 안정적인 7개 안도 비교했지만 영양 설명력은 같고 흡연·음주가 유형을 주도했습니다. 서비스는 모델을 고정해 같은 응답이면 같은 유형이 나옵니다.'),
      ('왜 복잡한 모델을 쓰지 않았나요?', '부스팅과 앙상블도 비교했지만 교차검증과 2024년 평가에서 이득이 없었습니다. 1-SE 규칙으로 더 단순한 모델을 골랐습니다(철만 부스팅).'),
      ('1.2배, 0.3 같은 기준은 결과를 보고 고른 것 아닌가요?', '팀 문서에 미리 적고 고정한 뒤 적용했고, 학습에 쓰지 않은 2024년 자료로 따로 확인했습니다.')]
T([['질문', '답변']] + [list(x) for x in qa], '예상 질문', widths=[5.2, 11.3], first_col_bold=True, align_num=False)
H('D. 영양소별 최종 하이퍼파라미터', 3)
rows = [['영양소', '선택 모델', 'CV 로그 손실', 'CV AUC', '손실 최소 후보', '최소 손실', '최소 + 1SE']]
for t_ in S['tune']:
    rows.append([t_['n'], nm(t_['sel']), f'{t_["loss"]:.4f}', f'{t_["auc"]:.3f}', nm(t_['best']), f'{t_["best_loss"]:.4f}', f'{t_["lim"]:.4f}'])
T(rows, '15개 영양소의 최종 선택 (2022–23년 5겹 교차검증, 1-SE 규칙)', widths=[2, 3.4, 2.1, 1.7, 3.4, 1.9, 2], size=8,
  note='"손실 최소 후보"의 1 표준오차 안에 드는 후보 중 가장 단순한 것(로지스틱 C가 작을수록 단순, 로지스틱이 부스팅보다 단순)을 골랐습니다. 철은 부스팅이 최소이고 그 범위 안에 로지스틱 후보가 없어 부스팅을 썼습니다.')

out = HERE / '최종결과보고서_생활습관군집_부족영양소.docx'
doc.save(out)
json.dump(FN, open(HERE / 'fig' / 'footnotes.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('저장:', out, '| 표', CAP['표'], '그림', CAP['그림'])
