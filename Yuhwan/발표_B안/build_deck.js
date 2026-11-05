// 최종 발표 PPT (B안) — 생활습관으로 찾는 나의 부족 영양소 (Matchum / NBTI 유형 검사)
// 디자인: 우리 웹앱 브랜드(분홍·초록·짙은 갈색 글자, 크림, 유형 마스코트)를 그대로 사용, 맑은 고딕
// 숫자는 모두 결과 파일(data.json ← 영양분석/output, 보고서/fig/stats.json)과 최종 보고서 값
const pptxgen = require('pptxgenjs');
const path = require('path');
const fs = require('fs');
const { applyTheme } = require('./apply_theme.js');

const D = JSON.parse(fs.readFileSync(path.join(__dirname, 'data.json'), 'utf8'));
const IMG = (n) => path.join(__dirname, 'img', n);
const FONT = '맑은 고딕';
// 웹앱 index.css 색
const K = {
  ink: '4A3F3F', ink2: '6B5D59', faint: '766864', pink: 'E06A80', pinkD: 'A8425A', pinkL: 'F8B4BF', pinkXL: 'FDE4E8',
  mint: '2E8063', mintL: 'CDEEE0', butter: 'FFEEB8', lav: 'E3DBF8', cream: 'FFF9F2', grey: 'C9BFBB', greyL: 'F3EEEC', white: 'FFFFFF',
};
const THEME = {
  name: 'Matchum NBTI', headFontFace: FONT, bodyFontFace: FONT,
  colors: { dk1: K.ink, lt1: K.white, dk2: K.pinkD, lt2: K.cream, accent1: K.pink, accent2: K.mint, accent3: K.pinkL,
    accent4: K.mintL, accent5: K.butter, accent6: K.lav, hlink: K.pinkD, folHlink: K.ink2 },
};

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE'; // 13.333 x 7.5
pres.theme = { headFontFace: FONT, bodyFontFace: FONT };
pres.title = '생활습관으로 찾는 나의 부족 영양소';
pres.author = '2조 머신2러닝';
const W = 13.333, X0 = 0.6, CW = 12.13;

// ── 레이아웃 ──
pres.defineSlideMaster({
  title: 'CONTENT', background: { color: K.white },
  objects: [
    { placeholder: { options: { name: 'title', type: 'title', x: X0, y: 0.72, w: CW, h: 0.95, fontFace: FONT, fontSize: 28, bold: true, color: K.ink, align: 'left', valign: 'top', margin: 0 }, text: '' } },
    { text: { text: '2조 머신2러닝 · Matchum', options: { x: X0, y: 7.02, w: 4, h: 0.3, fontFace: FONT, fontSize: 9, color: K.faint, margin: 0 } } },
  ],
  slideNumber: { x: 12.2, y: 7.0, w: 0.55, h: 0.3, fontFace: FONT, fontSize: 9, color: K.faint, align: 'right' },
});
pres.defineSlideMaster({ title: 'COVER', background: { color: K.cream }, objects: [] });
pres.defineSlideMaster({ title: 'BLANK', background: { color: K.white }, objects: [] });

// ── 도우미 ──
let SEC = '';
function slide(layout = 'CONTENT') { return pres.addSlide({ masterName: layout, sectionTitle: SEC }); }
function section(t) { SEC = t; pres.addSection({ title: t }); }
function txt(s, text, o) { s.addText(text, Object.assign({ fontFace: FONT, color: K.ink, isTextBox: true, margin: 0, valign: 'top' }, o)); }
function head(s, label, title, lead) {
  txt(s, label, { x: X0, y: 0.34, w: 8, h: 0.3, fontSize: 11, bold: true, color: K.pinkD, objectName: 'section-label' });
  s.addText(title, { placeholder: 'title' });
  if (lead) txt(s, lead, { x: X0, y: 1.62, w: CW, h: 0.6, fontSize: 15, color: K.ink2, objectName: 'lead' });
}
function card(s, x, y, w, h, fill = K.greyL, name = 'card') {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: fill, width: 0 }, rectRadius: 0.18, objectName: name });
}
function bigStat(s, x, y, w, val, label, color = K.pink) {
  txt(s, val, { x, y, w, h: 0.95, fontSize: 44, bold: true, color });
  txt(s, label, { x, y: y + 0.95, w, h: 0.7, fontSize: 13, color: K.ink2 });
}
function source(s, t) { txt(s, t, { x: X0, y: 6.62, w: 11.2, h: 0.32, fontSize: 10, color: K.faint, objectName: 'source' }); }
function img(s, f, x, y, w, h, name) { s.addImage({ path: IMG(f), x, y, w, h, objectName: name || f }); }
function phone(s, f, x, y, w, h) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x - 0.06, y: y - 0.06, w: w + 0.12, h: h + 0.12, fill: { color: K.white }, line: { color: 'E4D9D5', width: 1 }, rectRadius: 0.2,
    shadow: { type: 'outer', color: '000000', opacity: 0.12, blur: 8, offset: 2, angle: 90 }, objectName: 'phone-frame' });
  s.addImage({ path: IMG(f), x, y, w, h, objectName: 'screen-' + f });
}
const chartText = { catAxisLabelFontFace: FONT, valAxisLabelFontFace: FONT, dataLabelFontFace: FONT, catAxisLabelColor: K.ink2, valAxisLabelColor: K.faint,
  catAxisLabelFontSize: 12, valAxisLabelFontSize: 10, dataLabelFontSize: 11, dataLabelColor: K.ink, valGridLine: { color: 'EDE6E3', size: 0.75 }, catGridLine: { style: 'none' } };

const TYPES = [
  ['N1', '집밥좋아 나무늘보', '비활동형', '8.7%'], ['N2', '배고픈 나무늘보', '비활동형', '8.1%'], ['N3', '배부른 나무늘보', '비활동형', '8.3%'],
  ['A1', '뚜벅이 갓생러', '운동형', '9.3%'], ['A2', '파워 갓생러', '운동형', '8.4%'], ['A3', '밸런스 갓생러', '운동형', '9.3%'],
  ['S1', '쉬고 싶은 예민보스', '고스트레스형', '11.0%'], ['S2', '산책하는 예민보스', '고스트레스형', '10.5%'], ['S3', '쇠질하는 예민보스', '고스트레스형', '3.6%'],
  ['O1', '아침패스 워커홀릭', '좌식·외식형', '10.0%'], ['O2', '삼시세끼 워커홀릭', '좌식·외식형', '8.0%'], ['O3', '운동하는 워커홀릭', '좌식·외식형', '4.7%'],
];

// ════════════ 1. 표지 ════════════
section('표지');
let s = slide('COVER');
img(s, 'type_N1.png', 8.45, 1.15, 1.55, 1.55); img(s, 'type_A3.png', 10.15, 0.85, 1.55, 1.55); img(s, 'type_S1.png', 9.2, 2.75, 1.55, 1.55);
img(s, 'type_O2.png', 10.95, 2.55, 1.55, 1.55); img(s, 'type_N2.png', 8.3, 4.35, 1.4, 1.4); img(s, 'type_A1.png', 10.1, 4.45, 1.4, 1.4); img(s, 'type_O3.png', 11.6, 4.25, 1.3, 1.3);
txt(s, '머신러닝 팀 프로젝트 최종 발표', { x: X0 + 0.1, y: 1.25, w: 7.5, h: 0.4, fontSize: 15, bold: true, color: K.pinkD });
txt(s, '생활습관으로 찾는\n나의 부족 영양소', { x: X0 + 0.1, y: 1.8, w: 7.6, h: 2.2, fontSize: 46, bold: true, color: K.ink, lineSpacingMultiple: 1.05 });
txt(s, '국민건강영양조사 15,062명의 생활습관을 12개 유형으로 나누고,\n유형마다 부족하기 쉬운 영양소와 바꿀 습관을 안내합니다', { x: X0 + 0.1, y: 4.15, w: 7.4, h: 0.9, fontSize: 15, color: K.ink2 });
txt(s, [{ text: 'NBTI 유형 검사 · Matchum', options: { bold: true, color: K.ink, breakLine: true } },
  { text: '2조 머신2러닝  |  양대천 · 최지연 · 전유환 · 황재준 · 박준혁', options: { color: K.ink2 } }],
  { x: X0 + 0.1, y: 5.75, w: 7.6, h: 0.75, fontSize: 13 });
s.addNotes('[0:30] 인사. "생활습관 설문만으로 내가 부족하기 쉬운 영양소를 알려 주는 서비스"를 만들었습니다. 국민건강영양조사 성인 1만 5천 명 자료로 12개 생활습관 유형을 만들고, 유형별 부족 영양소와 바꿀 습관까지 연결했습니다.');

// ════════════ 2. 한 장 요약 ════════════
section('요약');
s = slide();
head(s, '요약', '12유형으로 부족 영양소를 짚고, 2024년 자료로 확인했습니다');
const sum = [
  ['15,062명', '국민건강영양조사\n2022–24년 성인', K.pink],
  ['12개 유형', '생활습관 7개로\n나눈 유형', K.pink],
  ['13 / 15', '유형을 알면 더 잘\n구분한 영양소', K.pink],
  ['1.09배', '2024년에도 안내 항목이\n실제로 더 부족', K.mint],
];
sum.forEach(([v, l, c], i) => {
  const x = X0 + i * 3.08; card(s, x, 2.1, 2.88, 2.55, i === 3 ? K.mintL : K.pinkXL);
  txt(s, v, { x: x + 0.28, y: 2.38, w: 2.4, h: 0.85, fontSize: 36, bold: true, color: c === K.mint ? K.mint : K.pinkD });
  txt(s, l, { x: x + 0.28, y: 3.35, w: 2.45, h: 1.1, fontSize: 15, color: K.ink2 });
});
txt(s, [{ text: '서비스 흐름  ', options: { bold: true, color: K.pinkD } },
  { text: '설문 1단계 → 내 유형 → 유형에서 부족하기 쉬운 영양소 → 이번 주 바꿀 습관 → (설문 2단계) 개인 결과·건강기능식품 정보', options: { color: K.ink } }],
  { x: X0, y: 5.05, w: CW, h: 0.45, fontSize: 14 });
txt(s, [{ text: '정직하게 말할 것  ', options: { bold: true, color: K.pinkD } },
  { text: '유형은 자연스러운 무리가 아니라 "쓸모 있게 나눈 구분"이고, 결과는 진단이 아닌 같은 조건 사람들의 비율입니다', options: { color: K.ink } }],
  { x: X0, y: 5.65, w: CW, h: 0.45, fontSize: 14 });
s.addNotes('[1:00] 결론부터 말씀드립니다. 숫자 네 개로 요약하면 1만 5천 명, 12개 유형, 15개 중 13개 영양소, 2024년 검증 1.09배입니다. 그리고 처음부터 정직하게 말씀드릴 한계 하나: 유형은 데이터에 원래 있던 무리가 아니라, 서비스에 쓰려고 나눈 구분입니다. 이게 왜 괜찮은지는 뒤에서 보여 드리겠습니다.');

// ════════════ 3. 목차 ════════════
s = slide();
head(s, '목차', '오늘 발표 순서');
const toc = [['01', '문제', '왜 생활습관으로 부족 영양소를 짚나'], ['02', '데이터', '국민건강영양조사와 분석 설계'], ['03', '유형', '12개 생활습관 유형과 그 쓸모'],
  ['04', '부족 영양소', '예측 모델, 이유, 화면 규칙, 2024 검증'], ['05', '서비스', '웹 시연과 개인화 단계'], ['06', '마무리', '한계와 제언']];
toc.forEach(([n, t, d], i) => {
  const col = i % 2, row = Math.floor(i / 2), x = X0 + col * 6.15, y = 2.0 + row * 1.45;
  txt(s, n, { x, y, w: 0.9, h: 0.7, fontSize: 30, bold: true, color: K.pink });
  txt(s, t, { x: x + 1.0, y: y + 0.02, w: 4.8, h: 0.45, fontSize: 19, bold: true });
  txt(s, d, { x: x + 1.0, y: y + 0.5, w: 4.9, h: 0.4, fontSize: 13, color: K.ink2 });
});
s.addNotes('[0:20] 문제, 데이터, 유형, 부족 영양소, 서비스, 마무리 순서로 30분 동안 말씀드리겠습니다.');

// ════════════ 01 문제 ════════════
section('01 문제');
s = slide();
head(s, '01 문제', '성인 절반 이상이 부족한 영양소가 8개나 됩니다', '하루 섭취량이 2025 한국인 영양소 섭취기준보다 적은 성인 비율 (조사 가중)');
const rk = Object.entries(D.rate).sort((a, b) => b[1] - a[1]);
const common = rk.filter(([, v]) => v >= 50).map(([k]) => k);
s.addChart(pres.charts.BAR, [{ name: '부족 비율', labels: rk.map(([k]) => k), values: rk.map(([, v]) => v) }],
{ x: X0, y: 2.25, w: 7.9, h: 4.3, barDir: 'bar', chartColors: rk.map(([, v]) => (v >= 50 ? K.pink : K.grey)), catAxisOrientation: 'maxMin',
  showValue: true, dataLabelPosition: 'outEnd', dataLabelFormatCode: '0"%"', showLegend: false, barGapWidthPct: 40,
  valAxisMaxVal: 100, valAxisMinVal: 0, valAxisLabelFormatCode: '0"%"', ...chartText, catAxisLabelFontSize: 11, objectName: 'chart-deficiency' });
card(s, 8.85, 2.35, 3.88, 3.95, K.cream);
bigStat(s, 9.15, 2.6, 3.4, '10명 중 7명', '칼슘이 부족합니다\n(평균필요량 기준, 성인 71%)', K.pinkD);
txt(s, '비타민D·E는 90% 이상, 칼륨·비타민A·C·칼슘·식이섬유·엽산도 절반을 넘습니다. 이 8개는 생활습관과 상관없이 누구에게나 흔한 부족입니다.',
  { x: 9.15, y: 4.35, w: 3.35, h: 1.8, fontSize: 13, color: K.ink2 });
source(s, '출처: 국민건강영양조사 2022–2024 성인 15,062명, 24시간 회상 섭취량. 비타민D·E·칼륨·식이섬유는 충분섭취량 기준이라 "참고"로 봅니다');
s.addNotes('[1:30] 국민건강영양조사로 보면 성인 10명 중 7명이 칼슘 기준보다 적게 먹습니다. 비타민D는 96%입니다. 절반을 넘는 영양소가 8개나 됩니다. 문제는 이런 정보가 "한국인 평균"으로만 나와서, 나와 연결되지 않는다는 점입니다.');

s = slide();
head(s, '01 문제', '"나는 무엇이 부족하기 쉬울까"를 생활습관으로 짚어 보려 했습니다');
const qs = [['질문 1', '생활습관만으로 사람들을 의미 있는 유형으로 나눌 수 있을까?', '비지도 학습 · 군집화'],
  ['질문 2', '유형을 알면 성별·나이만 알 때보다 부족 영양소를 더 잘 구분할까?', '지도 학습 · 2024년 검증'],
  ['질문 3', '그 결과를 진단처럼 보이지 않게 화면에 어떻게 보여 줄까?', '표시 규칙 설계 · 웹']];
qs.forEach(([a, b, c], i) => {
  const y = 2.05 + i * 1.45; card(s, X0, y, 8.6, 1.22, i === 1 ? K.pinkXL : K.greyL);
  txt(s, a, { x: X0 + 0.35, y: y + 0.22, w: 1.3, h: 0.4, fontSize: 14, bold: true, color: K.pinkD });
  txt(s, b, { x: X0 + 1.65, y: y + 0.2, w: 6.7, h: 0.5, fontSize: 17, bold: true });
  txt(s, c, { x: X0 + 1.65, y: y + 0.72, w: 6.7, h: 0.35, fontSize: 13, color: K.ink2 });
});
img(s, 'thinking.png', 9.75, 2.25, 2.7, 2.7, 'mascot-thinking');
txt(s, '혈액 검사 없이, 설문 몇 분으로', { x: 9.35, y: 5.15, w: 3.5, h: 0.4, fontSize: 14, bold: true, color: K.ink2, align: 'center' });
s.addNotes('[1:00] 그래서 세 가지 질문을 던졌습니다. 생활습관으로 유형을 나눌 수 있는지, 그 유형이 성별·나이보다 더 알려 주는지, 그리고 진단처럼 보이지 않게 어떻게 보여 줄지입니다. 첫 번째가 비지도 학습, 두 번째가 지도 학습입니다.');

s = slide();
head(s, '01 문제', '서비스는 "유형 결과"와 "개인 결과" 두 단계로 나눴습니다');
const steps1 = [['설문 1단계', '생활습관 7개 + 성별·나이'], ['내 유형', '12개 중 가장 가까운 유형'], ['부족하기 쉬운 영양소', '같은 유형·성별·나이 10명 중 N명'], ['이번 주 해볼 것', '내 응답에 해당하는 습관 미션']];
steps1.forEach(([a, b], i) => {
  const x = X0 + i * 3.08; card(s, x, 2.15, 2.75, 1.45, K.pinkXL);
  txt(s, a, { x: x + 0.25, y: 2.35, w: 2.3, h: 0.45, fontSize: 16, bold: true, color: K.pinkD });
  txt(s, b, { x: x + 0.25, y: 2.85, w: 2.35, h: 0.6, fontSize: 12.5, color: K.ink2 });
  if (i < 3) txt(s, '›', { x: x + 2.78, y: 2.45, w: 0.3, h: 0.6, fontSize: 28, color: K.pink, bold: true });
});
txt(s, '유형 결과 (이 발표의 중심)', { x: X0, y: 1.72, w: 6, h: 0.35, fontSize: 13, bold: true, color: K.ink });
txt(s, '개인 결과 (진행 중)', { x: X0, y: 4.02, w: 6, h: 0.35, fontSize: 13, bold: true, color: K.ink });
const steps2 = [['설문 2단계', '흡연·음주·식사 5문항 추가'], ['개인 부족 위험', '응답 18개로 사람마다 계산'], ['건강기능식품 정보', '음식 먼저, 제품은 정보로만']];
steps2.forEach(([a, b], i) => {
  const x = X0 + i * 3.08; card(s, x, 4.45, 2.75, 1.45, K.mintL);
  txt(s, a, { x: x + 0.25, y: 4.65, w: 2.3, h: 0.45, fontSize: 16, bold: true, color: K.mint });
  txt(s, b, { x: x + 0.25, y: 5.15, w: 2.35, h: 0.6, fontSize: 12.5, color: K.ink2 });
  if (i < 2) txt(s, '›', { x: x + 2.78, y: 4.75, w: 0.3, h: 0.6, fontSize: 28, color: K.mint, bold: true });
});
card(s, X0 + 3 * 3.08, 4.45, 2.75, 1.45, K.cream);
txt(s, '유형 결과는 같은 조건 사람들의 평균(120가지 조합 고정), 개인 결과는 사람마다 다릅니다', { x: X0 + 3 * 3.08 + 0.22, y: 4.62, w: 2.35, h: 1.15, fontSize: 12.5, color: K.ink2 });
source(s, '영양제는 유형 화면에 넣지 않고 개인 단계에서만 다룹니다 (11/3 팀 결정: 처방처럼 보이지 않게)');
s.addNotes('[1:00] 서비스는 두 단계입니다. 1단계 설문으로 내 유형과 그 유형에서 부족하기 쉬운 영양소, 이번 주 바꿀 습관을 보여 줍니다. 2단계는 사람마다 다른 개인 결과와 건강기능식품 정보인데, 현재 진행 중이라 마지막에 짧게 소개하겠습니다.');

// ════════════ 02 데이터 ════════════
section('02 데이터');
s = slide();
head(s, '02 데이터', '국민건강영양조사 3년치로 학습하고, 마지막 해로 검증했습니다');
const dat = [['데이터', '국민건강영양조사 2022–2024\n건강설문 + 24시간 회상 영양조사\n성인 15,062명, 조사 가중치 사용'],
  ['군집 입력 (7개)', '유산소 · 근력운동 · 앉아 있는 시간\n수면 · 스트레스 · 세 끼 · 외식\n흡연·음주는 군집을 지배해서 제외'],
  ['정답 (15개 영양소)', '하루 섭취량 < 2025 섭취기준\n평균필요량 11개: 부족 위험\n충분섭취량 4개: 참고']];
dat.forEach(([a, b], i) => {
  const x = X0 + i * 4.1; card(s, x, 1.85, 3.85, 2.55, K.greyL);
  txt(s, a, { x: x + 0.3, y: 2.07, w: 3.3, h: 0.4, fontSize: 16, bold: true, color: K.pinkD });
  txt(s, b, { x: x + 0.3, y: 2.55, w: 3.35, h: 1.7, fontSize: 13, color: K.ink, lineSpacingMultiple: 1.15 });
});
// 시간 분할 막대
txt(s, '검증 설계', { x: X0, y: 4.72, w: 3, h: 0.35, fontSize: 14, bold: true });
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: X0, y: 5.15, w: 7.8, h: 0.7, fill: { color: K.pinkL }, line: { color: K.pinkL, width: 0 }, rectRadius: 0.12, objectName: 'train-bar' });
txt(s, '학습 2022–2023 · 9,742명 · 5겹 교차검증으로 모델 선택', { x: X0 + 0.3, y: 5.33, w: 7.3, h: 0.35, fontSize: 13, bold: true, color: K.pinkD });
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: X0 + 7.95, y: 5.15, w: 4.18, h: 0.7, fill: { color: K.mintL }, line: { color: K.mintL, width: 0 }, rectRadius: 0.12, objectName: 'test-bar' });
txt(s, '검증 2024 · 5,320명 · 한 번만 확인', { x: X0 + 8.2, y: 5.33, w: 3.8, h: 0.35, fontSize: 13, bold: true, color: K.mint });
source(s, '수면 시간은 2022·23년(시간 응답)과 2024년(시각 응답) 측정 방식이 달라 2024년 기준으로 맞췄습니다');
s.addNotes('[1:30] 데이터는 국민건강영양조사 2022~24년 성인 1만 5천 명입니다. 군집에는 바꿀 수 있는 생활습관 7개만 넣었고, 흡연·음주는 군집 전체를 끌고 가서 뺐습니다. 정답은 하루 섭취량이 2025년 섭취기준보다 적은지입니다. 핵심은 검증 방식입니다. 2022~23년으로만 모델을 고르고, 2024년은 마지막에 딱 한 번만 확인했습니다.');

// ════════════ 03 유형 ════════════
section('03 유형');
s = slide();
head(s, '03 유형', '7개 습관을 두 단계로 나눠 12개 유형을 만들었습니다', '비지도 학습: 주성분 분석(PCA) → k-medoids 군집화 (실제 한 사람을 군집 중심으로 삼는 방법)');
const fl = [['7개 생활습관', '표준화'], ['주성분 5개', '정보 78% 보존'], ['대분류 4개', 'k-medoids, k=4'], ['세부 3개씩', '대분류마다 습관 2개로'], ['12개 유형', '웹 재배정 일치 100%']];
fl.forEach(([a, b], i) => {
  const x = X0 + i * 2.47; card(s, x, 2.5, 2.2, 1.35, i === 4 ? K.pink : K.pinkXL);
  txt(s, a, { x: x + 0.2, y: 2.7, w: 1.85, h: 0.45, fontSize: 16, bold: true, color: i === 4 ? K.white : K.pinkD });
  txt(s, b, { x: x + 0.2, y: 3.2, w: 1.9, h: 0.5, fontSize: 12, color: i === 4 ? K.white : K.ink2 });
  if (i < 4) txt(s, '›', { x: x + 2.22, y: 2.8, w: 0.25, h: 0.6, fontSize: 26, bold: true, color: K.pink });
});
const big4 = [['비활동형', 'N', '운동이 적은 편'], ['운동형', 'A', '유산소·근력이 많은 편'], ['고스트레스형', 'S', '스트레스가 높은 편'], ['좌식·외식형', 'O', '오래 앉고 외식이 잦은 편']];
big4.forEach(([a, c, b], i) => {
  const x = X0 + i * 3.08; img(s, `type_${c}${i === 1 ? 3 : 1}.png`, x, 4.3, 1.1, 1.1);
  txt(s, `${a} (${c})`, { x: x + 1.2, y: 4.45, w: 1.8, h: 0.4, fontSize: 14, bold: true });
  txt(s, b, { x: x + 1.2, y: 4.85, w: 1.85, h: 0.4, fontSize: 12, color: K.ink2 });
});
source(s, '7개 유형 안(흡연·음주 포함)도 비교했지만 영양 설명력은 같고 흡연·음주가 유형을 주도해, 서비스가 안내할 습관을 담는 12개 안을 택했습니다');
s.addNotes('[1:30] 군집은 지연 님이 맡았습니다. 7개 습관을 주성분 5개로 줄이고, k-medoids로 먼저 큰 무리 4개를 나눈 뒤, 무리마다 그 무리를 가장 잘 가르는 습관 2개로 다시 3개씩 나눠 12개 유형을 만들었습니다. k-medoids는 실제 한 사람을 중심으로 삼아서 "이 유형의 대표 사람"을 보여 줄 수 있습니다.');

s = slide();
head(s, '03 유형', '12개 유형에는 웹에서 쓰는 이름과 캐릭터가 있습니다');
TYPES.forEach(([id, nm, grp, pct], i) => {
  const col = i % 6, row = Math.floor(i / 6), x = X0 + col * 2.03, y = 1.85 + row * 2.45;
  card(s, x, y, 1.88, 2.25, row === 0 && col < 3 ? K.greyL : K.greyL);
  img(s, `type_${id}.png`, x + 0.34, y + 0.12, 1.2, 1.2);
  txt(s, id, { x: x + 0.15, y: y + 1.32, w: 1.6, h: 0.3, fontSize: 11, bold: true, color: K.pinkD, align: 'center' });
  txt(s, nm, { x: x + 0.08, y: y + 1.6, w: 1.72, h: 0.35, fontSize: 12, bold: true, align: 'center' });
  txt(s, `${grp} · ${pct}`, { x: x + 0.08, y: y + 1.9, w: 1.72, h: 0.3, fontSize: 10, color: K.ink2, align: 'center' });
});
source(s, '가중 비율은 성인 인구 대비. 가장 작은 유형 S3 3.6%, O3 4.7%');
s.addNotes('[1:30] 12개 유형입니다. 예를 들어 N2 배고픈 나무늘보는 운동이 적고 끼니를 자주 거르는 유형, A3 밸런스 갓생러는 근력운동이 가장 많고 식사도 규칙적인 유형입니다. 그런데 여기서 중요한 질문이 하나 생깁니다. 이 12개가 정말 데이터 안에 원래 있던 무리일까요?');

// ── 질문 → 비유 → 돌아오기 ──
function nullChart(s) {
  const mean = (a) => a.reduce((x, y) => x + y, 0) / a.length;
  const A = D.null['귀무A_상관없음'], B = D.null['귀무B_상관유지'];
  s.addChart(pres.charts.BAR, [{ name: '실루엣', labels: ['실제 자료', '무작위 A (관계 없앰)', '무작위 B (관계 유지, 덩어리만 없앰)'], values: [0.163, +mean(A).toFixed(3), +mean(B).toFixed(3)] }],
    { x: X0, y: 2.25, w: 7.6, h: 3.6, barDir: 'bar', catAxisOrientation: 'maxMin', chartColors: [K.pink, K.grey, K.grey], showValue: true, dataLabelPosition: 'outEnd',
      dataLabelFormatCode: '0.000', valAxisMinVal: 0, valAxisMaxVal: 0.25, showLegend: false, ...chartText, objectName: 'chart-null' });
  // 한 계열에 막대마다 색: invertedColors 대신 계열 하나라 첫 색만 쓰이므로 실제만 강조하려면 표기 텍스트로 보완
}
s = slide();
head(s, '03 유형', '이 12개는 데이터에 원래 있던 "무리"일까요?', '실루엣: 같은 무리끼리 가깝고 다른 무리와 먼 정도 (−1~1, 높을수록 뚜렷)');
nullChart(s);
card(s, 8.6, 2.3, 4.13, 3.5, K.cream);
txt(s, '확인 방법', { x: 8.9, y: 2.55, w: 3.6, h: 0.4, fontSize: 15, bold: true, color: K.pinkD });
txt(s, '구조가 전혀 없는 무작위 자료를 같은 방법으로 20번 군집화해서, 실제 자료의 실루엣과 비교했습니다 (귀무 검정).\n\n판정 기준은 결과를 보기 전에 정했습니다.',
  { x: 8.9, y: 3.05, w: 3.6, h: 2.5, fontSize: 13.5, color: K.ink });
source(s, '무작위 A·B는 각 20회 평균. 범위 A 0.155~0.222, B 0.186~0.216');
s.addNotes('[1:00] 실루엣은 같은 무리끼리 가깝고 다른 무리와 먼 정도입니다. 우리 값은 0.163으로 낮습니다. 그래서 일부러 구조가 없는 무작위 자료를 만들어 같은 방법으로 군집화해 봤습니다. 결과를 보시면, 무작위 자료가 오히려 더 높게 나옵니다. 이게 무슨 뜻인지 잠깐 비유로 설명드리겠습니다.');

s = slide('BLANK');
txt(s, '잠깐, 비유로 보면', { x: X0, y: 0.45, w: 8, h: 0.4, fontSize: 13, bold: true, color: K.pinkD });
txt(s, '운동장에 고르게 흩어진 학생들도 반은 나눌 수 있습니다', { x: X0, y: 0.85, w: CW, h: 0.8, fontSize: 28, bold: true });
// 운동장: 고르게 흩어진 점
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: X0, y: 1.85, w: 7.3, h: 4.6, fill: { color: 'EAF6EF' }, line: { color: 'CFE6D8', width: 1 }, rectRadius: 0.3, objectName: 'playground' });
let seed = 7; const rnd = () => { seed = (seed * 9301 + 49297) % 233280; return seed / 233280; };
const cols4 = [K.pink, K.mint, 'C99A2E', '8C79C9'];
for (let i = 0; i < 90; i++) {
  const px = X0 + 0.35 + rnd() * 6.6, py = 2.1 + rnd() * 4.05;
  const q = (px < X0 + 3.65 ? 0 : 1) + (py < 4.15 ? 0 : 2);
  s.addShape(pres.shapes.OVAL, { x: px, y: py, w: 0.16, h: 0.16, fill: { color: cols4[q] }, line: { color: K.white, width: 0.5 }, objectName: 'student' });
}
s.addShape(pres.shapes.LINE, { x: X0 + 3.65, y: 1.95, w: 0, h: 4.4, line: { color: K.ink2, width: 1.5, dashType: 'dash' }, objectName: 'divider-v' });
s.addShape(pres.shapes.LINE, { x: X0 + 0.1, y: 4.15, w: 7.1, h: 0, line: { color: K.ink2, width: 1.5, dashType: 'dash' }, objectName: 'divider-h' });
['1반', '2반', '3반', '4반'].forEach((t, i) => txt(s, t, { x: X0 + 0.25 + (i % 2) * 3.65, y: 1.98 + Math.floor(i / 2) * 2.3, w: 1, h: 0.35, fontSize: 13, bold: true, color: K.ink2 }));
const an = [['학생들이 원래 무리 지어 서 있던 건 아니에요', '그래서 "반이 자연스러운 무리인가?"라고 물으면 답은 아니오입니다 (실루엣이 낮음)'],
  ['그래도 반 편성은 쓸모가 있어요', '반마다 담임이 다른 지도를 할 수 있고, 새 학생도 바로 반에 넣을 수 있습니다'],
  ['물어야 할 질문이 바뀝니다', '"뚜렷한 무리인가?"가 아니라 "나눠서 다르게 안내할 수 있나?"']];
an.forEach(([a, b], i) => {
  const y = 1.95 + i * 1.55;
  txt(s, a, { x: 8.3, y, w: 4.45, h: 0.45, fontSize: 16, bold: true, color: i === 2 ? K.pinkD : K.ink });
  txt(s, b, { x: 8.3, y: y + 0.48, w: 4.45, h: 0.9, fontSize: 13, color: K.ink2 });
});
s.addNotes('[1:00] 운동장에 학생들이 고르게 흩어져 있다고 해 보겠습니다. 원래 무리 지어 있던 게 아니니 "반이 자연스러운 무리냐"고 물으면 아니라고 답해야 합니다. 그런데 반을 나누면 담임마다 다른 지도를 할 수 있죠. 생활습관도 똑같습니다. 사람들의 생활습관은 이어진 분포라 원래 무리는 없지만, 나눠서 다르게 안내할 수 있다면 쓸모 있는 구분입니다. 다시 아까 장표로 돌아가겠습니다.');

s = slide();
head(s, '03 유형', '원래 무리는 아니지만, 나눠서 쓸 수 있는 구분입니다', '실루엣: 같은 무리끼리 가깝고 다른 무리와 먼 정도 (−1~1, 높을수록 뚜렷)');
nullChart(s);
card(s, 8.6, 2.3, 4.13, 3.5, K.pinkXL);
txt(s, '판정: 이어진 분포를 나눈 구분', { x: 8.9, y: 2.55, w: 3.6, h: 0.45, fontSize: 15, bold: true, color: K.pinkD });
txt(s, '실제 0.163은 구조 없는 무작위 자료(0.18~0.21)보다도 낮습니다. 12개 유형 수준에서도 결과가 같았고, 일부러 무리를 심은 자료에서는 검정이 무리를 찾아냈습니다 (지연 님 확인).\n\n→ 그래서 "쓸모"를 따로 확인했습니다',
  { x: 8.9, y: 3.08, w: 3.6, h: 2.6, fontSize: 13.5, color: K.ink });
source(s, '무작위 A·B 각 20회 평균. 12유형 실루엣 실제 0.100 vs 무작위 B 0.117, 무리를 심은 자료(간격 3 이상)는 5번 중 5번 검출');
s.addNotes('[0:40] 그래서 판정은 "이어진 분포를 나눈 구분"입니다. 12개 유형 수준에서도 같았고, 지연 님이 일부러 무리를 심은 자료로 확인해 보니 이 검정은 무리가 있으면 찾아냅니다. 즉 검정이 약해서가 아니라 정말 무리가 없는 겁니다. 그러면 이 구분이 쓸모 있는지를 어떻게 보여 줄까요?');

s = slide();
head(s, '03 유형', '실무 세분화 기준 다섯 가지를 모두 통과했습니다', 'ADAMS: 고객 세분화가 쓸모 있는지 보는 마케팅 실무 기준 (영양 서비스에 맞게 팀이 적용)');
const ad = [['M', '측정 가능', '인원을 셀 수 있나', '15,062명 전원 배정'], ['S', '충분한 크기', '따로 다룰 만큼 큰가', '가장 작은 유형 3.6%'], ['A', '도달 가능', '새 사용자를 넣을 수 있나', '웹 재배정 100%'],
  ['D', '차별성', '부족이 유형마다 다른가', '156칸 중 72칸이\n10% 이상 다름'], ['A', '실행 가능', '다른 안내를 줄 수 있나', '유형마다 다른\n습관 미션']];
ad.forEach(([l, a, q, e], i) => {
  const x = X0 + i * 2.47; card(s, x, 2.35, 2.25, 3.45, i === 3 ? K.pinkXL : K.greyL);
  txt(s, l, { x: x + 0.25, y: 2.55, w: 1, h: 0.75, fontSize: 40, bold: true, color: K.pink });
  txt(s, a, { x: x + 0.25, y: 3.35, w: 1.9, h: 0.4, fontSize: 16, bold: true });
  txt(s, q, { x: x + 0.25, y: 3.8, w: 1.95, h: 0.7, fontSize: 12.5, color: K.ink2 });
  txt(s, e, { x: x + 0.25, y: 4.6, w: 1.85, h: 1.0, fontSize: 13, bold: true, color: K.pinkD });
});
source(s, '핵심 원칙: 똑같이 반응하는 두 그룹은 합치고, 경계가 흐려도 다르게 대응할 수 있으면 쓸모 있는 구분 (OpenStax, Principles of Marketing 5.4)');
s.addNotes('[1:30] 실무에서 고객을 나눌 때 쓰는 ADAMS 기준입니다. 셀 수 있는지, 충분히 큰지, 새 사람을 넣을 수 있는지, 그룹마다 반응이 다른지, 다르게 대응할 수 있는지. 다섯 가지 모두 숫자로 통과했습니다. 특히 차별성은 유형 12개 곱하기 영양소 13개 156칸 중 72칸이 같은 성별·나이보다 10% 이상 달랐습니다.');

s = slide();
head(s, '03 유형', '영양 차이는 끼니 규칙성으로 세 무리, 안내는 12유형으로 합니다');
const g3 = [['덜 부족한 무리', 'N3 · A1 · A3 · O2 · O3', '끼니가 규칙적', '인 0.46~0.89배 · 철 0.61~0.91배', K.mintL, K.mint],
  ['조금 더 부족한 무리', 'N1 · A2 · S1 · S2 · S3 · O1', '과일·콩류·달걀을 덜 먹음', '1.0~1.4배 (S1 인 1.38배)', K.pinkXL, K.pinkD],
  ['가장 부족한 유형', 'N2 배고픈 나무늘보', '끼니를 자주 거름', '인 1.65배 · 단백질 1.44배 · 철 1.42배', K.pinkL, K.pinkD]];
g3.forEach(([a, b, c, d, f, tc], i) => {
  const y = 1.85 + i * 1.18; card(s, X0, y, 6.3, 1.03, f);
  txt(s, a, { x: X0 + 0.3, y: y + 0.13, w: 2.4, h: 0.4, fontSize: 15, bold: true, color: tc });
  txt(s, b, { x: X0 + 0.3, y: y + 0.55, w: 2.6, h: 0.35, fontSize: 12, color: K.ink2 });
  txt(s, c, { x: X0 + 2.95, y: y + 0.13, w: 3.2, h: 0.35, fontSize: 13, bold: true });
  txt(s, d, { x: X0 + 2.95, y: y + 0.55, w: 3.2, h: 0.35, fontSize: 12, color: K.ink2 });
});
txt(s, '영양이 거의 같은 쌍도 받는 미션은 다릅니다', { x: 7.25, y: 1.85, w: 5.5, h: 0.4, fontSize: 15, bold: true });
s.addTable([
  [{ text: '유형 쌍', options: { bold: true, color: K.pinkD, fill: { color: K.pinkXL } } }, { text: '미션 해당 비율', options: { bold: true, color: K.pinkD, fill: { color: K.pinkXL } } }],
  ['S1 – O1', '하루 10분 쉬어가기 91% vs 1%'], ['A2 – S2', '하루 10분 쉬어가기 5% vs 82%'], ['N1 – S2', '하루 30분 걷기 94% vs 0%'], ['S2 – S3', '주 2회 근력운동 100% vs 0%']],
{ x: 7.25, y: 2.35, w: 5.48, colW: [1.5, 3.98], fontFace: FONT, fontSize: 13, color: K.ink, border: { type: 'solid', pt: 0.75, color: 'EDE6E3' }, rowH: 0.48, objectName: 'table-pairs' });
source(s, '영양 무리: 13개 영양소 관측/기대 비(같은 성별·나이 = 1)로 Ward 군집. 미션 = 웹 유형 결과 "이번 주 해볼 것" 조건');
s.addNotes('[1:30] 부족 영양소만 보면 12개 유형은 크게 세 무리로 갈립니다. 끼니가 규칙적인 다섯 유형은 덜 부족하고, N2는 가장 부족합니다. 그럼 영양이 비슷한 유형은 합치면 되지 않냐고 물으실 수 있는데, 오른쪽처럼 받는 습관 미션이 전혀 다릅니다. 그래서 12개 유형은 생활습관 안내 단위로 유지하고, 영양 차이는 끼니 규칙성으로 설명합니다.');

// ════════════ 04 부족 영양소 ════════════
section('04 부족 영양소');
s = slide();
head(s, '04 부족 영양소', '유형·성별·나이로 영양소 15개의 부족 확률을 예측했습니다', '지도 학습: 정답은 "하루 섭취량이 섭취기준보다 적은가", 확률이 정확해야 해서 로그 손실로 모델을 골랐습니다');
const mm = [['입력', '12개 유형 + 성별 + 연령대(5구간)'], ['후보 모델', '로지스틱 회귀(규제 4단계) · 유형×성별 · 그래디언트 부스팅 4개'], ['고르는 법', '5겹 교차검증 + 1-SE 규칙 (차이가 없으면 더 단순한 모델)'], ['결과', '14개 영양소 로지스틱 회귀, 철만 부스팅']];
mm.forEach(([a, b], i) => {
  const y = 2.4 + i * 0.92; card(s, X0, y, 7.6, 0.78, i === 3 ? K.pinkXL : K.greyL);
  txt(s, a, { x: X0 + 0.3, y: y + 0.21, w: 1.6, h: 0.4, fontSize: 14, bold: true, color: K.pinkD });
  txt(s, b, { x: X0 + 1.95, y: y + 0.21, w: 5.5, h: 0.4, fontSize: 14 });
});
card(s, 8.6, 2.4, 4.13, 3.5, K.cream);
bigStat(s, 8.9, 2.6, 3.6, '≤ 1.7%p', '확률 보정 오차\n"10명 중 N명"을 그대로 보여 줘도 되는 수준', K.pinkD);
txt(s, '과적합(학습 − 검증 AUC)도 최대 0.029로 작았습니다', { x: 8.9, y: 4.45, w: 3.6, h: 0.8, fontSize: 13, color: K.ink2 });
source(s, '부스팅·앙상블·변수 추가도 시험했지만 2024년 평가에서 이득이 없어 단순한 모델을 유지했습니다');
s.addNotes('[1:00] 부족 영양소 예측은 제가 맡았습니다. 입력은 유형, 성별, 연령대뿐입니다. 로지스틱 회귀와 부스팅 후보를 교차검증으로 비교하고, 차이가 없으면 단순한 모델을 고르는 1-SE 규칙을 썼습니다. 화면에 "10명 중 N명"으로 확률을 그대로 보여 주기 때문에, 확률이 맞는지가 중요했고 보정 오차가 1.7%p 이하였습니다.');

s = slide();
head(s, '04 부족 영양소', '유형을 알면 15개 중 13개 영양소에서 더 잘 구분합니다', '2024년 AUC: 유형+성별·나이 모델 − 성별·나이만 쓴 모델 (막대가 클수록 유형이 더 알려 줌)');
const dd = [...D.dauc].sort((a, b) => b.d - a.d);
const sig = (r) => r.lo > 0;
s.addChart(pres.charts.BAR, [{ name: 'ΔAUC', labels: dd.map((r) => r.n), values: dd.map((r) => r.d) }],
{ x: X0, y: 2.2, w: 8.4, h: 4.35, barDir: 'bar', catAxisOrientation: 'maxMin', chartColors: dd.map((r) => (sig(r) ? K.pink : K.grey)), showValue: true, dataLabelPosition: 'outEnd',
  dataLabelFormatCode: '+0.000;-0.000', dataLabelFontSize: 10, showLegend: false, barGapWidthPct: 40,
  valAxisMinVal: -0.02, valAxisMaxVal: 0.05, valAxisLabelFormatCode: '0.00', catAxisLabelPos: 'low', ...chartText, catAxisLabelFontSize: 11, objectName: 'chart-dauc' });
card(s, 9.35, 2.3, 3.38, 3.95, K.cream);
txt(s, '+0.014 ~ +0.040', { x: 9.65, y: 2.55, w: 2.95, h: 0.6, fontSize: 24, bold: true, color: K.pinkD });
txt(s, 'AUC 향상 폭. 크지는 않아서 "진단"이 아니라 "같은 유형 사람들의 경향"으로만 씁니다.\n\n회색(비타민D·E)은 유형 신호가 없어 공통 안내로만 보여 줍니다.', { x: 9.65, y: 3.3, w: 2.9, h: 2.8, fontSize: 13, color: K.ink2 });
source(s, '유의 = 부트스트랩 95% 신뢰구간 하한 > 0. 2024년 AUC 0.56~0.70');
s.addNotes('[1:30] 결과입니다. 유형을 넣으면 15개 중 13개 영양소에서 AUC가 유의하게 올랐습니다. 다만 향상 폭은 0.014에서 0.040으로 크지 않습니다. 그래서 개인 진단이 아니라 "같은 유형 사람들의 경향"으로만 안내합니다. 비타민D·E는 유형 신호가 없어서 공통 안내로만 씁니다.');

s = slide();
head(s, '04 부족 영양소', '끼니를 거르는 유형일수록 인·단백질·철이 더 부족합니다', '같은 성별·나이 대비 부족 배수 (관측/기대, 1 = 평균)   ■ 더 부족   ■ 덜 부족');
const hv = D.heat;
const shadeOf = (v) => (v >= 1.3 ? [K.pink, K.white] : v >= 1.1 ? [K.pinkL, K.ink] : v > 0.9 ? [K.white, K.ink2] : v > 0.7 ? [K.mintL, K.ink] : [K.mint, K.white]);
const nameOf = Object.fromEntries(TYPES.map(([id, nm]) => [id, nm]));
const rows = [[{ text: '유형', options: { bold: true, color: K.pinkD, fill: { color: K.cream } } },
  ...hv.nuts.map((n) => ({ text: n, options: { bold: true, color: K.pinkD, fill: { color: K.cream }, align: 'center' } }))]];
hv.ids.forEach((id, i) => rows.push([{ text: `${id} ${nameOf[id]}`, options: { bold: true, fontSize: 11 } },
  ...hv.v[i].map((v) => { const [f, c] = shadeOf(v); return { text: v.toFixed(2), options: { fill: { color: f }, color: c, align: 'center', bold: v >= 1.3 || v <= 0.7 } }; })]));
s.addTable(rows, { x: X0, y: 2.15, w: 9.2, colW: [2.45, ...hv.nuts.map(() => 0.75)], fontFace: FONT, fontSize: 11, color: K.ink, rowH: 0.33,
  border: { type: 'solid', pt: 0.75, color: 'F1EBE8' }, objectName: 'table-heat' });
card(s, 10.1, 2.15, 2.63, 4.25, K.greyL);
txt(s, '읽는 법', { x: 10.35, y: 2.35, w: 2.2, h: 0.4, fontSize: 14, bold: true, color: K.pinkD });
txt(s, 'N2 배고픈 나무늘보의 인 1.65 = 같은 성별·나이 평균보다 1.65배 많은 사람이 기준보다 적게 먹음.\n\n칼슘·비타민C·D는 누구에게나 비슷해서(0.86~1.10) 공통 안내로 둡니다.',
  { x: 10.35, y: 2.8, w: 2.2, h: 3.4, fontSize: 12, color: K.ink });
source(s, '156칸 중 72칸이 10% 이상 다름. 유형 간 차이: 인·단백질·철·아연 등 0.237 vs 공통 영양소 0.068 (로그 표준편차)');
s.addNotes('[1:30] 유형마다 실제로 다릅니다. 분홍이 더 부족, 초록이 덜 부족입니다. 위쪽 N2와 아래쪽 끼니를 거르는 O1이 분홍이고, A3·O2처럼 세 끼를 챙기는 유형은 초록입니다. 칼슘이나 비타민C는 누구에게나 비슷하게 부족해서 유형 차이가 작습니다. 그래서 화면도 공통 영역과 유형 영역으로 나눴습니다.');

s = slide();
head(s, '04 부족 영양소', '왜 부족한지: 얼마나, 무엇을 먹느냐로 82%가 설명됩니다', '군집에 쓰지 않은 실제 식품 섭취(24시간 회상)로 유형 차이를 나눠 봤습니다');
const vs = [['N2', '배고픈 나무늘보', K.pinkXL, K.pinkD, ['콩류 25%↓', '유제품 18%↓', '과일 16%↓', '달걀 15%↓', '에너지 8%↓'], '인 1.65배 · 단백질 1.44배 · 철 1.42배', '식사량 쪽이 더 큼 → 끼니 회복부터'],
  ['A3', '밸런스 갓생러', K.mintL, K.mint, ['콩류 38%↑', '달걀 34%↑', '유제품 32%↑', '과일 32%↑'], '인 0.46배 · 철 0.61배 · 아연 0.64배', '식품 선택 쪽이 더 큼 → 지금 식단 유지']];
vs.forEach(([id, nm, f, tc, foods, nut, msg], i) => {
  const x = X0 + i * 4.3; card(s, x, 2.3, 4.05, 3.9, f);
  img(s, `type_${id}.png`, x + 0.2, 2.42, 1.15, 1.15);
  txt(s, `${id} ${nm}`, { x: x + 1.45, y: 2.62, w: 2.5, h: 0.4, fontSize: 16, bold: true, color: tc });
  txt(s, '같은 성별·나이보다', { x: x + 1.45, y: 3.05, w: 2.5, h: 0.35, fontSize: 11, color: K.ink2 });
  txt(s, foods.reduce((a, f, j) => a + f + (j % 2 ? '\n' : '    '), '').trim(), { x: x + 0.3, y: 3.68, w: 3.55, h: 0.85, fontSize: 13.5, bold: true });
  txt(s, nut, { x: x + 0.3, y: 4.55, w: 3.6, h: 0.4, fontSize: 13 });
  txt(s, msg, { x: x + 0.3, y: 5.35, w: 3.6, h: 0.5, fontSize: 13, bold: true, color: tc });
});
card(s, 9.35, 2.3, 3.38, 3.9, K.cream);
txt(s, '유형 차이가 줄어드는 몫', { x: 9.6, y: 2.5, w: 3, h: 0.4, fontSize: 14, bold: true, color: K.pinkD });
[['식사량만 맞춤', '59%'], ['식품군만 맞춤', '67%'], ['둘 다 맞춤', '82%']].forEach(([a, b], i) => {
  txt(s, a, { x: 9.6, y: 3.05 + i * 0.8, w: 1.8, h: 0.4, fontSize: 13, color: K.ink2 });
  txt(s, b, { x: 11.3, y: 2.95 + i * 0.8, w: 1.3, h: 0.55, fontSize: 24, bold: true, color: i === 2 ? K.pinkD : K.ink, align: 'right' });
});
txt(s, '둘 다 맞추면 남는 유형 고유 차이는 3건뿐', { x: 9.6, y: 5.45, w: 3, h: 0.6, fontSize: 11.5, color: K.ink2 });
source(s, '육류·생선·유제품·달걀·콩류 g과 과일·채소 빈도, 에너지로 관측/기대 비를 다시 맞춤. 같은 하루 기록이라 독립 검증이 아니고, 상관관계입니다');
s.addNotes('[1:30] 그럼 왜 부족할까요. 군집에 쓰지 않은 실제 식품 섭취로 나눠 봤습니다. N2는 콩류·유제품·달걀을 덜 먹고 식사량도 적습니다. A3는 반대로 훨씬 많이 먹고 덜 부족합니다. 식사량과 식품을 함께 맞추면 유형 차이의 82%가 사라집니다. 즉 유형 차이는 대부분 "얼마나, 무엇을 먹느냐"에서 옵니다. 그래서 영양제보다 끼니와 식사 구성을 먼저 안내합니다.');

s = slide();
head(s, '04 부족 영양소', '화면은 "누구에게나 흔한 것"과 "내 유형에서 많은 것"을 나눕니다');
phone(s, 'web/r_nutri.png', 0.95, 1.85, 3.05, 4.34);
const rl = [['공통 영역', '성인 절반 이상이 부족한 8개 (비타민D·E, 칼륨, 칼슘 등)', '확률과 상관없이 항상 표시', K.greyL],
  ['유형 영역', '그 밖의 영양소 중 부족 확률 ≥ 0.5, 또는 같은 성별·나이 대비 1.2배 이상이면서 확률 ≥ 0.3', '"내 유형 10명 중 N명 · 평균 M명" + 근거 문구', K.pinkXL],
  ['비었을 때', '공통 외에 특히 더 부족한 게 없으면 그렇게 알려 줌', '120개 조합 중 40개는 좋은 소식', K.mintL]];
rl.forEach(([a, b, c, f], i) => {
  const y = 1.85 + i * 1.5; card(s, 4.6, y, 8.13, 1.3, f);
  txt(s, a, { x: 4.9, y: y + 0.18, w: 1.7, h: 0.4, fontSize: 15, bold: true, color: K.pinkD });
  txt(s, b, { x: 6.55, y: y + 0.16, w: 6.0, h: 0.62, fontSize: 13.5 });
  txt(s, c, { x: 6.55, y: y + 0.8, w: 6.0, h: 0.35, fontSize: 12, color: K.ink2 });
});
source(s, '세 가지 표시 규칙을 120개 조합에 비교해 채택. 기준값(1.2배, 0.3)은 결과를 보기 전에 팀 문서로 정하고 고정');
s.addNotes('[1:30] 확률을 그대로 나열하면 공통 영양소 8개가 모든 화면을 덮어서 유형이 달라도 화면이 같아집니다. 그래서 두 영역으로 나눴습니다. 누구에게나 흔한 8개는 공통 영역에, 그 밖에서 내 유형에 특히 많은 것만 유형 영역에 보여 줍니다. 기준값은 결과를 보기 전에 정했습니다.');

s = slide();
head(s, '04 부족 영양소', '2024년에도 안내한 항목이 실제로 더 부족했습니다', '2022–23년 모델로만 고른 유형 영역 항목 163개의 2024년 관측/기대 비 (1 = 같은 성별·나이 평균)');
s.addChart(pres.charts.BAR, [{ name: '관측/기대', labels: ['이 유형에서 특히 많아요 (8개)', '식사량 점검이 먼저예요 (38개)', '같은 성별·나이대에서 흔해요 (117개)'], values: [1.36, 1.24, 1.04] }],
  { x: X0, y: 2.3, w: 7.6, h: 3.9, barDir: 'bar', catAxisOrientation: 'maxMin', chartColors: [K.pink], showValue: true, dataLabelPosition: 'outEnd', dataLabelFormatCode: '0.00"배"',
    valAxisMinVal: 0.9, valAxisMaxVal: 1.5, valAxisLabelFormatCode: '0.0', showLegend: false, ...chartText, objectName: 'chart-oe' });
card(s, 8.6, 2.35, 4.13, 3.85, K.mintL);
bigStat(s, 8.9, 2.55, 3.6, '1.087배', '전체 관측/기대 비\n95% 신뢰구간 1.056~1.121', K.mint);
txt(s, '근거 문구가 말하는 강도의 순서와 실제 차이의 순서가 같습니다.', { x: 8.9, y: 4.5, w: 3.6, h: 0.9, fontSize: 13.5, bold: true, color: K.ink });
source(s, '2024년 자료는 모델 학습·선택에 쓰지 않았습니다. 부트스트랩 2,000회');
s.addNotes('[1:00] 가장 중요한 검증입니다. 2024년 자료를 전혀 보지 않은 모델로 안내 항목을 고르고, 2024년 실제 자료에 대 봤습니다. 안내한 항목은 평균보다 1.087배 더 부족했고, "이 유형에서 특히 많아요"가 1.36배로 가장 컸습니다. 문구가 말하는 강도와 실제 차이의 순서가 일치합니다.');

s = slide();
head(s, '04 부족 영양소', '끼니를 거르는 습관이 부족과 가장 크게 이어집니다', '같은 성별·나이 안에서 습관이 있는 사람 − 없는 사람의 부족 차이 (10명 중 몇 명, 가장 큰 영양소)');
const hb = [['아침 거르기', 1.6, '엽산·마그네슘'], ['점심·저녁 거르기', 1.6, '아연'], ['근력운동 부족', 0.7, '마그네슘·칼슘'], ['유산소 활동 부족', 0.6, '마그네슘·엽산'],
  ['수면 부족', 0.6, '마그네슘·철'], ['오래 앉아 있기', 0.2, '식이섬유'], ['외식 잦음', -0.6, '단백질 (반대 방향)']];
s.addChart(pres.charts.BAR, [{ name: '차이', labels: hb.map(([a, , c]) => `${a}  (${c})`), values: hb.map(([, b]) => b) }],
  { x: X0, y: 2.3, w: 8.3, h: 4.1, barDir: 'bar', catAxisOrientation: 'maxMin', chartColors: [K.pink], showValue: true, dataLabelPosition: 'outEnd', dataLabelFormatCode: '+0.0"명";-0.0"명"',
    valAxisMinVal: -1, valAxisMaxVal: 2, showLegend: false, catAxisLabelPos: 'low', ...chartText, catAxisLabelFontSize: 11.5, objectName: 'chart-habit' });
card(s, 9.3, 2.35, 3.43, 3.95, K.cream);
txt(s, '화면에 쓰는 방식', { x: 9.55, y: 2.55, w: 3, h: 0.4, fontSize: 14, bold: true, color: K.pinkD });
txt(s, '"이번 주 해볼 것"은 내 응답에 해당하는 습관만 보여 주고, 근거는 경향으로만 씁니다.\n\n"아침을 챙기는 사람은 엽산이 부족한 경우가 적은 편이에요"\n\n외식은 반대 방향이라 근거로 쓰지 않습니다.',
  { x: 9.55, y: 3.0, w: 3.0, h: 3.2, fontSize: 12.5, color: K.ink });
source(s, '습관 기준은 웹 미션 조건과 같음. 상관관계라 "~하면 좋아져요" 같은 인과 표현은 쓰지 않습니다');
s.addNotes('[1:00] 마지막으로 바꿀 습관과의 연결입니다. 같은 성별·나이 안에서 비교하면, 아침을 거르는 사람은 엽산·마그네슘이 부족한 사람이 10명 중 1.6명 더 많습니다. 선행 연구에서도 아침 결식과 칼슘·철 섭취 저하가 보고됐습니다. 외식은 오히려 반대로 나와서 근거로 쓰지 않습니다. 인과가 아니라 경향이라는 점을 화면 문구에도 지켰습니다.');

// ════════════ 05 서비스 ════════════
section('05 서비스');
s = slide();
head(s, '05 서비스', '웹에서는 설문 3분이면 유형과 부족 영양소를 봅니다', '예시: 20대 여성, 아침을 거의 안 먹고 하루 10시간 앉아 있으며 스트레스가 많은 편');
[['web/home.png', '시작'], ['web/survey.png', '설문 1단계'], ['web/r_type.png', '내 유형'], ['web/r_signal.png', '습관 신호등·미션']].forEach(([f, l], i) => {
  const x = 0.85 + i * 3.12, wImg = 2.35; const hImg = f.includes('r_type') ? wImg * (1050 / 780) : f.includes('r_signal') ? wImg * (1130 / 780) : wImg * (1688 / 780);
  const hh = Math.min(hImg, 3.9), ww = hh === hImg ? wImg : 3.9 * 780 / (f.includes('r_type') ? 1050 : f.includes('r_signal') ? 1130 : 1688);
  phone(s, f, x + (wImg - ww) / 2, 2.35, ww, hh);
  txt(s, l, { x, y: 6.35, w: wImg, h: 0.3, fontSize: 13, bold: true, align: 'center', color: K.pinkD });
});
s.addNotes('[1:30] 웹 화면입니다(팀장 대천 님 제작). 설문 1단계에 답하면 가장 가까운 유형이 나오고, 생활습관 신호등과 이번 주 해볼 미션을 보여 줍니다. 이 예시 분은 쉬고 싶은 예민보스로 나왔고, 철이 같은 성별·나이 평균 10명 중 5명보다 많은 6명으로 표시됩니다. 웹은 머신러닝을 직접 돌리지 않고, 저희가 미리 계산한 결과표로 가장 가까운 유형을 찾습니다.');

s = slide();
head(s, '05 서비스', '개인 단계는 설문을 더 받아 사람마다 계산합니다 (진행 중)');
s.addChart(pres.charts.BAR, [{ name: 'AUC', labels: ['성별·나이만', '+ 유형', '개인 응답 18개'], values: [D.cmp.base, D.cmp.type, D.cmp.pers] }],
  { x: X0, y: 1.95, w: 5.6, h: 3.6, barDir: 'col', chartColors: [K.pink], showValue: true, dataLabelPosition: 'outEnd', dataLabelFormatCode: '0.000', valAxisMinVal: 0.55, valAxisMaxVal: 0.68,
    valAxisLabelFormatCode: '0.00', showLegend: false, showTitle: true, title: '2024년 평균 AUC (13개 영양소)', titleFontFace: FONT, titleFontSize: 13, titleColor: K.ink, ...chartText, objectName: 'chart-personal' });
txt(s, '유형이 성별·나이보다 알려 주는 만큼을, 개인 설문이 한 번 더 알려 줍니다 (개인 − 유형 +0.028, 13개 중 11개 유의)', { x: X0, y: 5.65, w: 5.6, h: 0.75, fontSize: 12.5, color: K.ink2 });
const pr = [['개인 부족 위험 (재준 님)', '응답 18개 + 평소 식사 5문항으로 "높은 편 / 보통 / 낮은 편"'], ['건강기능식품 정보 (준혁 님)', '식약처 신고 제품 5,187개 → 품질·점수로 걸러 2,785개 후보'],
  ['화면 원칙', '음식 먼저 → 여러 영양소가 함께 든 제품 → 영양소별 목록. 조합을 정해 주지 않고 정보로만'], ['안전', '같이 먹을 때 상한 초과 주의, B군은 B1·B2 든 제품만, 어린이 제품 제외']];
pr.forEach(([a, b], i) => {
  const y = 1.95 + i * 1.12; card(s, 6.75, y, 5.98, 0.98, i < 2 ? K.mintL : K.greyL);
  txt(s, a, { x: 7.0, y: y + 0.13, w: 5.5, h: 0.35, fontSize: 13.5, bold: true, color: i < 2 ? K.mint : K.pinkD });
  txt(s, b, { x: 7.0, y: y + 0.5, w: 5.55, h: 0.4, fontSize: 12, color: K.ink });
});
source(s, '개인 단계는 개발 중이라 수치는 현재 시안 기준입니다. 웹 유형 화면에는 영양제를 넣지 않습니다');
s.addNotes('[1:30] 개인 단계는 재준 님과 준혁 님이 진행 중입니다. 같은 2024년 자료로 비교해 보면 성별·나이만 0.604, 유형을 더하면 0.631, 개인 응답 18개를 쓰면 0.659입니다. 유형이 알려 주는 만큼을 개인 설문이 한 번 더 알려 주는 구조라 두 단계로 나눈 이유가 숫자로도 보입니다. 건강기능식품은 음식을 먼저 안내하고, 제품은 조합을 정해 주지 않고 정보로만 보여 줍니다.');

// ════════════ 06 마무리 ════════════
section('06 마무리');
s = slide();
head(s, '06 마무리', '한계를 알고, 결과는 "경향 안내"로만 씁니다');
const lim = [['유형은 원래 무리가 아님', '실루엣 0.163, 무작위 자료보다 낮음', '쓸모는 ADAMS로 확인, 웹은 고정 모델이라 같은 응답이면 같은 유형'],
  ['하루 식사 기록 기준', '평소 섭취와 다를 수 있고 부족률이 커질 수 있음', '핵심 결과는 같은 성별·나이와의 비교라 영향이 적음, 요일 차이도 작음'],
  ['예측력은 중간 수준', 'AUC 0.56~0.70, 개인을 정확히 가르지 못함', '"10명 중 N명" 비율로만 표시, 개인 판단은 개인 단계'],
  ['상관관계, 음식만', '인과가 아니며 영양제 섭취는 빠짐', '"~하면 좋아져요" 금지, 질환이 있으면 전문가 상담 안내']];
s.addTable([[{ text: '한계', options: { bold: true, color: K.pinkD, fill: { color: K.pinkXL } } }, { text: '영향', options: { bold: true, color: K.pinkD, fill: { color: K.pinkXL } } }, { text: '대응', options: { bold: true, color: K.pinkD, fill: { color: K.pinkXL } } }],
  ...lim.map(([a, b, c]) => [{ text: a, options: { bold: true } }, b, c])],
{ x: X0, y: 1.95, w: CW, colW: [3.0, 4.2, 4.93], fontFace: FONT, fontSize: 13.5, color: K.ink, rowH: 0.85, valign: 'middle', border: { type: 'solid', pt: 0.75, color: 'EDE6E3' }, objectName: 'table-limits' });
s.addNotes('[1:00] 한계는 네 가지입니다. 유형은 원래 무리가 아니고, 하루 식사 기록 기준이며, 예측력은 중간 수준이고, 상관관계입니다. 그래서 결과는 진단이 아닌 "같은 조건 사람들의 비율"로만 보여 줍니다.');

s = slide();
head(s, '06 마무리', '그래서 이렇게 쓰는 것을 제안합니다');
const pro = [['01', '끼니부터 안내합니다', '유형 차이의 82%가 "얼마나, 무엇을 먹느냐"로 설명됩니다. 영양제보다 끼니와 식사 구성을 먼저.'],
  ['02', '좋은 소식도 전합니다', '120개 조합 중 40개는 "공통 외에 특히 더 부족한 것은 없어요". 건강한 습관을 강화합니다.'],
  ['03', '유형은 입구입니다', '유형으로 내 생활을 이해하고, 더 정밀한 판단은 개인 결과 단계가 맡습니다.']];
pro.forEach(([n, a, b], i) => {
  const x = X0 + i * 4.1; card(s, x, 2.0, 3.85, 2.95, i === 0 ? K.pinkXL : K.greyL);
  txt(s, n, { x: x + 0.3, y: 2.25, w: 1, h: 0.7, fontSize: 32, bold: true, color: K.pink });
  txt(s, a, { x: x + 0.3, y: 3.05, w: 3.3, h: 0.5, fontSize: 18, bold: true });
  txt(s, b, { x: x + 0.3, y: 3.65, w: 3.3, h: 1.8, fontSize: 13.5, color: K.ink2 });
});
s.addNotes('[1:00] 제안은 세 가지입니다. 끼니부터 안내하고, 좋은 소식도 전하고, 유형은 입구로 두고 정밀한 판단은 개인 단계에 맡기는 것입니다.');

s = slide('COVER');
img(s, 'happy.png', 9.1, 1.5, 3.2, 3.2, 'mascot-happy');
txt(s, '생활습관은 이어진 분포지만,\n나눠서 다르게 안내할 수 있습니다', { x: X0 + 0.1, y: 1.7, w: 8.2, h: 1.8, fontSize: 34, bold: true, color: K.ink, lineSpacingMultiple: 1.1 });
txt(s, '12개 유형은 "자연스러운 무리"가 아니라, 같은 성별·나이보다 더 부족한 영양소와 바꿀 습관을 알려 주는 쓸모 있는 구분입니다.', { x: X0 + 0.1, y: 3.75, w: 7.9, h: 1.0, fontSize: 15, color: K.ink2 });
txt(s, '감사합니다  ·  질문 받겠습니다', { x: X0 + 0.1, y: 5.4, w: 7.5, h: 0.5, fontSize: 18, bold: true, color: K.pinkD });
txt(s, '2조 머신2러닝  |  양대천 · 최지연 · 전유환 · 황재준 · 박준혁', { x: X0 + 0.1, y: 6.0, w: 7.5, h: 0.4, fontSize: 12, color: K.ink2 });
s.addNotes('[0:30] 한 문장으로 마무리하겠습니다. 생활습관은 이어진 분포지만, 나눠서 다르게 안내할 수 있습니다. 감사합니다. 질문 받겠습니다.');

// ════════════ 부록 (질의응답) ════════════
section('부록 Q&A');
function qa(label, title, rowsQ, src, colW) {
  const sl = slide(); head(sl, label, title);
  sl.addTable(rowsQ.map((r, i) => r.map((c) => (i === 0 ? { text: c, options: { bold: true, color: K.pinkD, fill: { color: K.pinkXL } } } : c))),
    { x: X0, y: 1.9, w: CW, colW: colW || (rowsQ[0].length === 2 ? [4.2, 7.93] : [3.2, 4.5, 4.43]), fontFace: FONT, fontSize: 12.5, color: K.ink, rowH: 0.5, valign: 'middle', border: { type: 'solid', pt: 0.75, color: 'EDE6E3' }, objectName: 'table-appendix' });
  if (src) source(sl, src);
  return sl;
}
s = qa('부록 A1', '예상 질문 목록', [['질문', '답이 있는 장표'], ['실루엣이 낮은데 유형이 의미가 있나요?', '본편 귀무 검정 · ADAMS'], ['군집이 몇 문항짜리 필터 아닌가요?', '부록 A2'], ['왜 복잡한 모델을 쓰지 않았나요?', '부록 A3'],
  ['기준값(1.2배, 0.3)은 결과를 보고 고른 것 아닌가요?', '부록 A4'], ['하루 식사 기록인데 믿을 수 있나요?', '부록 A5'], ['경계에 있는 사람은 결과가 흔들리지 않나요?', '부록 A6'],
  ['유형 결과와 개인화는 뭐가 다른가요?', '부록 A7'], ['영양제는 어떻게 고르나요? 처방 아닌가요?', '부록 A8'], ['누가 무엇을 했나요?', '부록 A9']]);
s.addNotes('질의응답용 목차입니다. 질문에 맞는 장표로 바로 이동하세요.');
qa('부록 A2', '7개 유형 안과 비교하고, 사람이 정한 규칙과도 비교했습니다', [['확인', '결과', '의미'],
  ['7개 유형 안 (흡연·음주 포함)', '재학습 안정성 0.911 vs 0.679, 영양 차이 0.097 vs 0.096', '7개 안이 더 안정적이지만 흡연·음주가 주도, 성별 쏠림 2배'],
  ['얕은 결정나무로 12유형 재현', '질문 2개 32.9%, 4개 65.9%, 6개 79.1%', '몇 문항짜리 필터가 아님'],
  ['사람이 정한 규칙 16개', '영양 차이 0.096 vs 0.096, AUC 0.630 vs 0.632', '영양 예측력은 같아 유형은 설명 용도'],
  ['표본 40% × 20회 재학습', 'ARI 0.697, 한 번에 바뀌는 사람 19.1%', '경계 근처 사람이 많음, 웹은 고정 모델']], '출처: 팀장님 군집화_결론.md, 지연님 cluster_report.md');
qa('부록 A3', '모델은 교차검증과 1-SE 규칙으로 골랐습니다', [['단계', '내용'],
  ['후보', '로지스틱 회귀 규제 C {0.01, 0.1, 1, 10} · 유형×성별 C {0.1, 1} · 그래디언트 부스팅 학습률 {0.05, 0.1} × 잎 {7, 15}'],
  ['기준', '조사 가중 로그 손실 (확률 정확도), 5겹 교차검증 (2022–23만)'],
  ['1-SE 규칙', '최소 손실 + 1 표준오차 안에서 가장 단순한 모델 → C=0.01 10개, C=0.1 4개, 철만 부스팅'],
  ['개선 실험', '나이 곡선·유형×성별 추가, 생활습관 응답 14개, 채소·과일, 앙상블 → 유형 모델 범위에서는 이득 없음'],
  ['과적합', '학습 − 검증 AUC 최대 0.029']]);
qa('부록 A4', '기준값은 결과를 보기 전에 정했고, 민감도도 확인했습니다', [['확인', '결과'],
  ['표시 기준 (확률 0.5, 1.2배, 0.3)', '11/3 팀 문서에 먼저 적고 고정, 2024년 자료로 따로 확인 (1.087배)'],
  ['민감도: 평소처럼 먹은 날만', '안내 일치율 99.4%'], ['민감도: 에너지 500~5,000kcal만', '안내 일치율 98.7%'], ['민감도: 둘 다', '안내 일치율 98.7%'],
  ['표시 규칙 3가지 비교', '확률 기준(8.6개 나열) · 2단 표시(채택) · 상위 3개(평균보다 덜 부족한 항목 158/360)']]);
qa('부록 A5', '하루 식사 기록의 한계와 확인한 것', [['질문', '답'],
  ['평소 섭취로 보정할 수 있나요?', '2022–24년은 하루 기록만 있고, 해마다 다른 사람이라 반복 측정이 없어 보정 불가'],
  ['그러면 결론이 틀어지나요?', '핵심은 같은 성별·나이와의 비교라 흔들림이 양쪽에 같이 들어가 영향이 적음 (흔들림은 차이를 작게 보이게 함)'],
  ['요일 영향은?', '일요일 식사 기록 마그네슘 50.3% vs 평일 47.8~48.4%, 차이 작음'],
  ['AUC가 낮은 이유는?', '모델 탓만이 아니라 정답 자체가 하루 기록이라 흔들리는 것이 이유 중 하나']]);
qa('부록 A6', '경계에 있는 사람도 안내 품질은 비슷합니다', [['구분', '인원', '2024 AUC (15개 평균)'],
  ['유형 중심에 가까운 사람', '2,343명', '0.637'], ['중간', '2,010명', '0.639'], ['경계에 있는 사람', '967명', '0.623'], ['차이 (중심 − 경계)', '', '0.014']],
  '재학습마다 안내가 달라지는 사람 약 8%. 서비스는 모델을 고정해 같은 응답이면 같은 결과');
qa('부록 A7', '유형 결과와 개인 결과는 역할이 다릅니다', [['', '유형 결과 (이 발표)', '개인 결과 (진행 중)'],
  ['입력', '1단계 생활습관 + 성별·나이', '응답 18개 + 평소 식사 5문항'], ['결과 단위', '120가지 조합 고정', '사람마다 다름'],
  ['식품 정보', '그 유형의 평균 (국민건강영양조사)', '본인 응답'], ['영양제', '없음', '정보로만 제공'], ['표현', '"이 유형은 평균적으로"', '"다른 사람보다 높은 편"']]);
qa('부록 A8', '영양제는 처방이 아니라 정보로만 보여 줍니다', [['단계', '내용'],
  ['거르기 (준혁 님)', '임산부·질환 제품, 이름-성분 불일치, 다른 목적 원료, 상한 초과 제외 → 5,187개'],
  ['품질·점수', '함량 적정성(100~300% 만점), 섭취 편의, 원료 단순성, 주의 원료 → 70점 미만 탈락, 2,785개'],
  ['보여 주는 방식 (시안)', '음식 먼저 → 여러 영양소가 함께 든 제품 → 영양소별 목록 (접힘)'],
  ['안전', '같이 먹을 때 상한 초과 주의 (예: 엽산), B군은 B1·B2 든 제품만, 어린이 의심 제품 제외'],
  ['쓰지 않는 것', '가격·판매처·브랜드 순위, "드세요", 용량 안내']], '개인 단계는 개발 중이라 기준값은 시안입니다');
qa('부록 A9', '역할과 일정', [['이름', '역할'], ['양대천 (팀장)', '기획, 웹앱 개발(유형 검사·결과 화면), 군집 검증, 저장소 관리'],
  ['최지연', '생활습관 군집화 (PCA + 2단계 k-medoids, 12유형, 귀무 검정)'], ['전유환', '유형별 부족 영양소 예측 모델, 표시 규칙, 2024 검증, 최종 보고서'],
  ['황재준', '데이터 전처리, 설문 문항, 개인 영양 위험 예측 모델 (생활습관 + 평소 식사 문항)'], ['박준혁', '건강기능식품 분류·필터링·점수'], ['일정', '10/29 시작 → 11/3 12유형 확정 → 11/4 웹 연결 → 11/9 제출 → 11/10 발표']]);

pres.writeFile({ fileName: path.join(__dirname, '최종발표_B안_생활습관유형_부족영양소.pptx') }).then(async (f) => {
  await applyTheme(f, THEME);
  console.log('저장:', f);
});
