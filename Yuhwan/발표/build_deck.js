// 최종 발표 PPT 생성 (NBTI 유형 검사 · 2조 머신2러닝)
// 실행: node build_deck.js  → 최종발표_생활습관유형_부족영양소.pptx
// 장표 원칙(팀 발표 피드백 체크리스트): 장마다 메시지 한 문장을 위에 크게, 근거는 아래 / 존댓말 / 그래프마다 한 줄 요약
const pptxgen = require('pptxgenjs');
const fs = require('fs');
const path = require('path');

const IMG = path.join(__dirname, 'img');
const OUT = path.join(__dirname, '최종발표_생활습관유형_부족영양소.pptx');
const FONT = '맑은 고딕';

// 보고서와 같은 색: 짙은 청록(주색) + 연한 청록 + 황토(강조)
const K = {
  ink: '1A1A1A', ink2: '595959', mute: '8A8A8A', deep: '1F4F4C', teal: '2C6E6A', tealM: '8BB5B0',
  tealL: 'DCEBE8', tealXL: 'EEF5F3', ochre: 'B9773A', ochreD: '9C5B26', ochreL: 'F5E8D8', white: 'FFFFFF', line: 'C5DCD8',
};

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE'; // 13.333 x 7.5
pres.author = '2조 머신2러닝';
pres.title = '생활습관으로 찾는 나의 부족 영양소';
pres.theme = { headFontFace: FONT, bodyFontFace: FONT };

// ── 레이아웃 ──
const FOOT = { text: 'NBTI 유형 검사 · 2조 머신2러닝', options: { x: 0.6, y: 7.02, w: 6, h: 0.3, fontSize: 9, color: K.mute, fontFace: FONT } };
const PH_KICKER = { placeholder: { options: { name: 'kicker', type: 'body', x: 0.6, y: 0.32, w: 10, h: 0.34, fontSize: 12, bold: true, color: K.teal, fontFace: FONT, margin: 0 }, text: '' } };
const PH_TITLE = { placeholder: { options: { name: 'title', type: 'title', x: 0.6, y: 0.68, w: 12.1, h: 1.05, fontSize: 24, bold: true, color: K.deep, fontFace: FONT, valign: 'top', align: 'left', margin: 0 }, text: '' } };
const NUM = { x: 12.3, y: 7.0, w: 0.5, h: 0.3, fontSize: 9, color: K.mute, fontFace: FONT, align: 'right' };
pres.defineSlideMaster({ title: 'CONTENT', background: { color: K.white }, objects: [{ text: FOOT }, PH_KICKER, PH_TITLE], slideNumber: NUM });
pres.defineSlideMaster({ title: 'DETOUR', background: { color: K.tealXL }, objects: [{ text: FOOT }, PH_KICKER, PH_TITLE], slideNumber: NUM });
pres.defineSlideMaster({ title: 'DARK', background: { color: K.deep }, objects: [] });
pres.defineSlideMaster({ title: 'APPX', background: { color: K.white }, objects: [{ text: { text: '부록 · 질의응답 대비', options: { x: 0.6, y: 7.02, w: 6, h: 0.3, fontSize: 9, color: K.mute, fontFace: FONT } } }, PH_KICKER, PH_TITLE], slideNumber: NUM });

// ── 도우미 ──
const T = [];        // 발표 시간표 [장 번호, 제목, 초]
function pngSize(f) { const b = fs.readFileSync(f); return [b.readUInt32BE(16), b.readUInt32BE(20)]; }
function slide(master, section, kicker, title, sec, note) {
  if (section && section !== slide.cur) { pres.addSection({ title: section }); slide.cur = section; }
  const s = pres.addSlide({ masterName: master, sectionTitle: slide.cur });
  if (kicker !== null) s.addText(kicker, { placeholder: 'kicker' });
  if (title !== null) s.addText(title, { placeholder: 'title' });
  if (sec) T.push([T.length + 1, title || kicker, sec]);
  if (note) s.addNotes(note);
  return s;
}
function txt(s, text, o) { s.addText(text, { isTextBox: true, fontFace: FONT, color: K.ink, fontSize: 16, margin: 0, valign: 'top', ...o }); }
function box(s, x, y, w, h, fill, o = {}) { s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.12, fill: { color: fill }, line: { color: fill }, ...o }); }
function img(s, file, x, y, w, h, o = {}) {
  const f = path.join(IMG, file); const [iw, ih] = pngSize(f); const r = Math.min(w / iw, h / ih);
  const W = iw * r, H = ih * r;
  s.addImage({ path: f, x: x + (w - W) / 2, y: y + (h - H) / 2, w: W, h: H, ...o });
}
function stat(s, x, y, w, value, label, color = K.teal, vs = 34) {
  txt(s, value, { x, y, w, h: 0.7, fontSize: vs, bold: true, color });
  txt(s, label, { x, y: y + 0.75, w, h: 0.75, fontSize: 13, color: K.ink2 });
}
function tag(s, x, y, text, kind = 'done') {
  const c = { done: [K.teal, K.white], wip: [K.ochre, K.white], idea: [K.white, K.ochreD] }[kind];
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 0.18 * text.length + 0.35, h: 0.32, rectRadius: 0.16, fill: { color: c[0] }, line: { color: c[0] } });
  txt(s, text, { x, y, w: 0.18 * text.length + 0.35, h: 0.32, fontSize: 11, bold: true, color: c[1], align: 'center', valign: 'middle' });
}
function bullets(s, items, o) {
  s.addText(items.map((t, i) => ({ text: t, options: { bullet: { indent: 16 }, breakLine: i < items.length - 1 } })),
    { isTextBox: true, fontFace: FONT, color: K.ink, fontSize: 15, paraSpaceAfter: 8, margin: 0, valign: 'top', ...o });
}
const CH = { // 차트 공통 모양
  catAxisLabelFontFace: FONT, valAxisLabelFontFace: FONT, dataLabelFontFace: FONT, legendFontFace: FONT, titleFontFace: FONT,
  catAxisLabelColor: K.ink2, valAxisLabelColor: K.ink2, catAxisLabelFontSize: 12, valAxisLabelFontSize: 11,
  valGridLine: { color: 'E4E3DF', size: 0.75 }, catGridLine: { style: 'none' }, dataLabelFontSize: 12, dataLabelColor: K.ink,
};
const mm = (sec) => `${Math.floor(sec / 60)}분 ${String(sec % 60).padStart(2, '0')}초`;
function n(sec, script) { return `[발표 시간 약 ${mm(sec)}]\n${script}`; }

// ════════════════════ 1. 여는 장 ════════════════════
{
  const s = slide('DARK', '여는 장', null, null, 20, n(20, '안녕하세요, 2조 머신2러닝입니다. 오늘은 생활습관 설문 몇 문항으로 "나와 비슷한 사람들은 무엇이 부족한지"를 알려 주는 NBTI 유형 검사를 소개하겠습니다.'));
  T[T.length - 1][1] = '표지';
  txt(s, '머신러닝 팀 프로젝트 최종 발표', { x: 0.8, y: 1.3, w: 7, h: 0.4, fontSize: 14, bold: true, color: K.tealM });
  txt(s, '생활습관으로 찾는\n나의 부족 영양소', { x: 0.8, y: 1.85, w: 7.6, h: 2.0, fontSize: 44, bold: true, color: K.white });
  txt(s, '국민건강영양조사 성인 15,062명으로 만든\n생활습관 유형 검사와 부족 영양소 안내', { x: 0.8, y: 4.05, w: 7.5, h: 0.9, fontSize: 17, color: K.tealL });
  txt(s, 'NBTI 유형 검사 (Nutrient + MBTI)  ·  2조 머신2러닝', { x: 0.8, y: 5.6, w: 7.5, h: 0.35, fontSize: 13, bold: true, color: K.white });
  txt(s, '양대천(팀장) · 박준혁 · 전유환 · 최지연 · 황재준   |   2026. 11. 10.', { x: 0.8, y: 6.0, w: 8, h: 0.35, fontSize: 12, color: K.tealM });
  s.addShape(pres.shapes.OVAL, { x: 8.75, y: 1.25, w: 4.0, h: 4.0, fill: { color: K.teal }, line: { color: K.teal } });
  img(s, 'mascot/happy.png', 8.95, 1.45, 3.6, 3.6);
}
{
  const s = slide('CONTENT', '여는 장', '왜 이 문제인가', '영양제는 고르는데, 정작 무엇이 부족한지는 모릅니다', 60,
    n(60, '건강기능식품을 고를 때 우리는 대부분 광고나 주변 추천을 봅니다. 내게 무엇이 부족한지 정확히 알려면 혈액검사나 여러 날의 식사 기록이 필요하기 때문입니다. 그런데 국민건강영양조사를 보면, 성인 절반 이상이 기준에 못 미치는 영양소가 8개나 됩니다. 특히 20대와 여성은 평균 5개 이상이 부족합니다. 반대로 운동, 끼니, 외식, 스트레스 같은 생활습관은 몇 문항이면 답할 수 있습니다. 그래서 "생활습관이 비슷한 사람들의 실제 식사를 미리 분석해 두면, 설문만으로 첫 단서를 줄 수 있지 않을까"에서 출발했습니다.'));
  const cards = [['8개', '성인 절반 이상이\n기준에 못 미치는 영양소\n(비타민D·E·A·C, 칼륨,\n칼슘, 식이섬유, 엽산)'],
    ['5.7개', '20대가 평균적으로\n부족한 영양소 수\n(평균필요량이 있는 11개 중,\n여성 평균 5.2개)'],
    ['몇 문항', '생활습관은 설문 몇 문항이면\n답할 수 있습니다\n→ 혈액검사·식사 기록 없이\n첫 단서를 줄 수 있을까?']];
  cards.forEach(([v, l], i) => { const x = 0.6 + i * 4.1; box(s, x, 2.25, 3.8, 3.5, i === 2 ? K.ochreL : K.tealXL); stat(s, x + 0.35, 2.6, 3.2, v, '', i === 2 ? K.ochreD : K.teal, 44); txt(s, l, { x: x + 0.35, y: 3.6, w: 3.2, h: 1.9, fontSize: 15, color: K.ink }); });
  txt(s, '출처: 국민건강영양조사 2022–2024 성인 15,062명, 2025 한국인 영양소 섭취기준, 조사 가중', { x: 0.6, y: 6.1, w: 12, h: 0.35, fontSize: 11, color: K.mute });
}
{
  const s = slide('CONTENT', '여는 장', '오늘의 결론', '설문 3분이면 "나와 비슷한 사람들이 무엇이 부족한지"\n알려 줄 수 있습니다', 70,
    n(70, '결론부터 말씀드리겠습니다. 생활습관으로 성인을 12개 유형으로 나눴고, 유형을 알면 성별과 나이만 알 때보다 영양소 15개 중 13개에서 부족한 사람을 더 잘 가려냅니다. 학습에 쓰지 않은 2024년 자료로 확인해도, 저희가 안내한 영양소는 같은 성별·나이 평균보다 실제로 1.09배 더 부족했습니다. 서비스는 두 단계입니다. 누구나 보는 1단계 유형 결과와, 원하는 사람만 들어가는 2단계 개인 결과입니다. 2단계는 지금 마무리 중입니다.'));
  [['12개', '생활습관 유형\n(4개 대분류 × 3)'], ['15개 중 13개', '성별·나이만 알 때보다\n부족을 더 잘 가려내는 영양소'], ['1.09배', '학습에 쓰지 않은 2024년에도\n안내한 영양소가 실제로 더 부족']]
    .forEach(([v, l], i) => { const x = 0.6 + i * 4.1; box(s, x, 2.15, 3.8, 2.0, K.tealXL); stat(s, x + 0.35, 2.4, 3.2, v, l, K.teal, 32); });
  // 2단계 서비스 흐름
  const steps = [['설문', '생활습관 1단계 문항', K.tealL, K.deep], ['1단계 유형 결과', '모두에게 · 공유용\n유형 + 부족할 수 있는 영양소', K.teal, K.white], ['2단계 개인 결과', '원하는 사람만 · 나만 보기\n개인 부족 위험 + 음식·제품 정보', K.ochre, K.white]];
  steps.forEach(([h, b, fill, fc], i) => {
    const x = 0.6 + i * 4.1; box(s, x, 4.6, 3.8, 1.55, fill);
    txt(s, h, { x: x + 0.3, y: 4.75, w: 3.3, h: 0.4, fontSize: 17, bold: true, color: fc });
    txt(s, b, { x: x + 0.3, y: 5.2, w: 3.3, h: 0.85, fontSize: 13, color: fc });
    if (i < 2) txt(s, '→', { x: x + 3.82, y: 5.05, w: 0.3, h: 0.5, fontSize: 22, bold: true, color: K.teal, align: 'center' });
  });
  tag(s, 9.0, 4.25, '마무리 중', 'wip');
}
{
  const s = slide('CONTENT', '여는 장', '발표 흐름과 담당', '데이터 → 유형 → 부족 영양소 → 개인화 순서로 말씀드리겠습니다', 30,
    n(30, '발표는 데이터를 어떻게 준비했는지, 생활습관 유형을 어떻게 만들었는지, 유형별 부족 영양소를 어떻게 예측하고 보여 주는지, 그리고 개인화를 어디까지 했는지 순서로 진행합니다. 각 단계 아래에 담당자를 적어 두었습니다.'));
  const parts = [['데이터 준비', 'KNHANES 3년치 통합,\n정답(부족) 정의', '황재준'], ['생활습관\n유형', '2단계 k-medoids,\n12개 유형과 검증', '최지연 · 양대천'], ['유형별\n부족 영양소', '부족 확률 예측,\n화면 표시 규칙', '전유환'], ['개인 맞춤', '개인 예측 모델,\n건강기능식품 정보', '황재준 · 박준혁'], ['웹 서비스', '설문 → 결과 화면,\n휴대폰에서 계산', '양대천']];
  parts.forEach(([h, b, who], i) => {
    const x = 0.6 + i * 2.48; box(s, x, 2.3, 2.25, 3.2, i % 2 ? K.tealXL : K.tealL);
    txt(s, String(i + 1), { x: x + 0.25, y: 2.5, w: 0.6, h: 0.6, fontSize: 28, bold: true, color: K.teal });
    txt(s, h, { x: x + 0.25, y: 3.2, w: 1.9, h: 0.75, fontSize: 17, bold: true, color: K.deep });
    txt(s, b, { x: x + 0.25, y: 3.95, w: 1.9, h: 0.9, fontSize: 13, color: K.ink2 });
    txt(s, who, { x: x + 0.25, y: 4.95, w: 1.9, h: 0.35, fontSize: 13, bold: true, color: K.ochreD });
  });
  txt(s, '기간 2026. 10. 29. ~ 11. 10.  ·  데이터 명세서(11/3) → EDA(11/4) → 모델 고도화(11/5~6) → 보고서·발표 자료(11/9)', { x: 0.6, y: 5.9, w: 12, h: 0.4, fontSize: 13, color: K.ink2 });
}
{
  const s = slide('CONTENT', '여는 장', '서비스 시연', '직접 해 보면 3분, 결과는 두 단계로 나옵니다', 100,
    n(100, '[시연] 휴대폰으로 QR을 찍으면 바로 해 볼 수 있습니다. 발표자 휴대폰 화면을 띄워 1단계 설문을 빠르게 진행합니다. 생년월일, 운동, 수면, 세 끼, 외식, 스트레스를 묻고 나면 유형 결과가 나옵니다. 유형 결과에는 내 유형과 비율, 생활습관 신호등과 이번 주 해볼 것, 부족할 수 있는 영양소, 짝꿍 유형이 나옵니다. 더 알고 싶은 사람은 2단계로 흡연·음주와 평소 식사 5문항을 답하면 개인 결과를 봅니다. 응답은 서버로 보내지 않고 휴대폰 안에서만 계산합니다. (시연이 어려우면 이 장의 화면 순서로 설명합니다.)'));
  box(s, 0.6, 2.1, 3.6, 4.4, K.tealXL);
  img(s, 'qr_matchum.png', 0.95, 2.35, 2.9, 2.9);
  txt(s, 'matchum.vercel.app', { x: 0.6, y: 5.4, w: 3.6, h: 0.4, fontSize: 16, bold: true, color: K.deep, align: 'center' });
  txt(s, '응답은 서버로 보내지 않고\n휴대폰 안에서만 계산합니다', { x: 0.6, y: 5.8, w: 3.6, h: 0.6, fontSize: 12, color: K.ink2, align: 'center' });
  const cols = [['1단계 유형 결과 (공유용)', K.teal, ['내 유형과 같은 유형 비율', '생활습관 신호등 · 이번 주 해볼 것', '모두가 챙겨야 할 영양소', '내 유형이 특히 챙길 영양소', '함께하면 좋은 짝꿍 유형']],
    ['2단계 개인 결과 (나만 보기)', K.ochre, ['흡연·음주 신호등', '나의 영양소 부족 위험', '챙겨 먹으면 좋은 음식', '건강기능식품 정보 (음식 다음)', '임신·질환·복용약은 상담 안내']]];
  cols.forEach(([h, c, items], i) => {
    const x = 4.6 + i * 4.15; txt(s, h, { x, y: 2.1, w: 3.9, h: 0.45, fontSize: 17, bold: true, color: c });
    items.forEach((t, j) => { box(s, x, 2.7 + j * 0.74, 3.9, 0.6, j % 2 ? K.white : K.tealXL, { line: { color: K.line, width: 0.75 } }); txt(s, `${j + 1}  ${t}`, { x: x + 0.2, y: 2.7 + j * 0.74, w: 3.6, h: 0.6, fontSize: 14, valign: 'middle' }); });
  });
}

// ════════════════════ 2. 데이터 ════════════════════
{
  const s = slide('CONTENT', '데이터', '데이터 준비', '국민건강영양조사 3년치 성인 15,062명의\n생활습관과 하루 식사를 사용했습니다', 60,
    n(60, '데이터는 질병관리청 국민건강영양조사 2022년부터 2024년까지의 원시자료입니다. 19세 이상 성인 중 생활습관 문항에 빠짐없이 답한 15,062명을 썼습니다. 생활습관 변수 14개와, 24시간 동안 먹은 음식으로 계산한 영양소 15개의 하루 섭취량이 있습니다. 정답 기준은 2025년에 새로 나온 한국인 영양소 섭취기준입니다. 표본이 실제 인구와 비율이 다르기 때문에, 모든 비율과 모델 학습에 조사 가중치를 적용했습니다.'));
  [['15,062명', '19세 이상 성인\n(생활습관 결측 없음)'], ['3개년', '2022 · 2023 · 2024\n원시자료 통합'], ['14개', '생활습관 변수\n운동·끼니·수면·스트레스 등'], ['15개', '영양소 하루 섭취량\n(24시간 회상)']]
    .forEach(([v, l], i) => { const x = 0.6 + i * 3.1; box(s, x, 2.15, 2.85, 1.95, K.tealXL); stat(s, x + 0.3, 2.35, 2.4, v, l, K.teal, 30); });
  const rows = [['원천', '질병관리청 국민건강영양조사(KNHANES) 원시자료 + 이용지침서'], ['정답 기준', '2025 한국인 영양소 섭취기준(KDRI), 성별 2 × 연령대 5 (원문·정오표와 값 대조)'], ['가중치', '조사 가중치 ÷ 3 (3개년 통합) → 표본 쏠림(여성·50세 이상 많음)을 인구 비율로 맞춤'], ['나누기', '2022–23년 9,742명 학습 / 2024년 5,320명 평가 (내년 사용자에게도 통하는지 확인)']];
  rows.forEach(([a, b], i) => {
    const y = 4.4 + i * 0.6; box(s, 0.6, y, 2.0, 0.5, K.tealL); box(s, 2.7, y, 10.0, 0.5, i % 2 ? K.white : K.tealXL);
    txt(s, a, { x: 0.8, y, w: 1.7, h: 0.5, fontSize: 14, bold: true, color: K.deep, valign: 'middle' });
    txt(s, b, { x: 2.9, y, w: 9.7, h: 0.5, fontSize: 14, valign: 'middle' });
  });
}
{
  const s = slide('CONTENT', '데이터', '정답 만들기', '하루 섭취량이 2025 기준에 못 미치면 "부족"으로 정의했습니다', 60,
    n(60, '머신러닝으로 맞힐 정답을 먼저 정했습니다. 사람마다 본인 성별·연령대 기준과 비교해 기준보다 적게 먹었으면 부족 1, 아니면 0입니다. 기준이 평균필요량인 11개는 "부족 위험", 근거가 부족해 충분섭취량만 있는 비타민D·E, 칼륨, 식이섬유 4개는 "참고"로 나눴습니다. 그래프에서 보시듯 비타민D·E, 칼륨, 비타민A·C, 칼슘, 식이섬유, 엽산 8개는 절반 이상이 기준 미만입니다. 이 8개는 유형과 상관없이 많은 사람에게 해당하므로, 뒤에서 "공통 영양소"로 따로 묶습니다.'));
  img(s, 'f01_부족률.png', 0.5, 1.95, 7.6, 4.45);
  box(s, 8.5, 2.1, 4.2, 2.05, K.tealXL);
  txt(s, '평균필요량(EAR) 11개', { x: 8.8, y: 2.25, w: 3.7, h: 0.4, fontSize: 16, bold: true, color: K.teal });
  txt(s, '건강한 사람 절반의 필요량\n→ 이보다 적으면 "부족 위험"', { x: 8.8, y: 2.7, w: 3.7, h: 1.2, fontSize: 14 });
  box(s, 8.5, 4.35, 4.2, 2.05, K.ochreL);
  txt(s, '충분섭취량(AI) 4개', { x: 8.8, y: 4.5, w: 3.7, h: 0.4, fontSize: 16, bold: true, color: K.ochreD });
  txt(s, '비타민D·E, 칼륨, 식이섬유\n→ 미만이어도 부족이라 단정할 수\n없어 "참고"로 구분', { x: 8.8, y: 4.95, w: 3.7, h: 1.2, fontSize: 14 });
  txt(s, '절반 이상이 부족한 8개 = 유형과 무관한 "공통 영양소"', { x: 0.6, y: 6.5, w: 7.5, h: 0.35, fontSize: 13, bold: true, color: K.deep });
}
{
  const s = slide('CONTENT', '데이터', '탐색적 분석(EDA)에서 바꾼 것', '데이터를 먼저 살펴보고, 군집에 넣을 변수를 세 가지 손봤습니다', 75,
    n(75, '군집을 돌리기 전에 분포와 상관을 먼저 봤습니다. 첫째, 2024년만 수면 시간이 길게 측정되어 있었습니다. 그대로 두면 조사 연도가 군집을 만들기 때문에 연도별로 표준화해 맞췄습니다. 둘째, 점심을 거의 안 먹는 838명이 그 변수 하나로 무리를 이뤄서, 아침·점심·저녁을 "식사 규칙성 점수" 하나로 합쳤습니다. 셋째, 흡연과 음주 변수 5개가 서로 강하게 겹쳐서 군집 입력에서 빼고 결과 설명에만 썼습니다. 변수 대부분이 0/1이나 순서형이고 한쪽으로 치우쳐 있어 상관은 스피어만으로 봤습니다.'));
  const items = [['2024년만 수면이 길게 측정됨', '평균 6.97 → 6.82 → 7.41시간', '연도별 표준화 후\n2024년 분포로 맞춤', '조사 연도가 군집을 만드는 것 방지'],
    ['점심 거의 안 먹는 838명', '변수 하나가 혼자 무리를 만듦', '아침·점심·저녁 →\n식사 규칙성 점수 1개', '끼니 차이는 대부분 아침 결식'],
    ['흡연·음주 5개가 강하게 겹침', '스피어만 상관 0.81~1.00, VIF 최대 5.83', '군집 입력에서 빼고\n설명용으로만 사용', '나머지 지표는 VIF 1.01~1.20']];
  items.forEach(([h, d, a, w], i) => {
    const x = 0.6 + i * 4.1; box(s, x, 2.15, 3.8, 1.75, K.tealXL);
    txt(s, '발견', { x: x + 0.3, y: 2.3, w: 1.5, h: 0.3, fontSize: 12, bold: true, color: K.mute });
    txt(s, h, { x: x + 0.3, y: 2.62, w: 3.3, h: 0.75, fontSize: 17, bold: true, color: K.deep });
    txt(s, d, { x: x + 0.3, y: 3.37, w: 3.3, h: 0.4, fontSize: 13, color: K.ink2 });
    txt(s, '↓', { x: x + 1.6, y: 3.95, w: 0.6, h: 0.45, fontSize: 22, bold: true, color: K.ochre, align: 'center' });
    box(s, x, 4.45, 3.8, 1.75, K.teal);
    txt(s, '처리', { x: x + 0.3, y: 4.6, w: 1.5, h: 0.3, fontSize: 12, bold: true, color: K.tealL });
    txt(s, a, { x: x + 0.3, y: 4.92, w: 3.3, h: 0.75, fontSize: 16, bold: true, color: K.white });
    txt(s, w, { x: x + 0.3, y: 5.67, w: 3.3, h: 0.4, fontSize: 13, color: K.tealL });
  });
  txt(s, '변수 대부분이 0/1·순서형이고 분포가 치우쳐 피어슨 대신 스피어만 상관을 사용했습니다', { x: 0.6, y: 6.5, w: 12, h: 0.35, fontSize: 13, color: K.ink2 });
}

// ════════════════════ 3. 생활습관 유형 ════════════════════
{
  const s = slide('CONTENT', '생활습관 유형', '고객 군집화 (비지도 학습)', '처음 군집은 "흡연 여부"로 나뉘었고,\n입력을 바꾸자 생활습관이 군집을 결정했습니다', 60,
    n(60, '처음 만든 군집은 시드를 바꿀 때마다 결과가 달라졌고, 흡연 한 변수가 군집 차이의 96%를 설명했습니다. 생활습관 유형이 아니라 사실상 흡연·음주 여부로 나뉜 것입니다. 그래프는 변수마다 군집이 그 변수를 얼마나 가르는지(η²)입니다. 앞에서 말씀드린 세 가지를 바꾸고 나니 흡연·음주는 0.01~0.03으로 내려가고, 서비스가 안내하려는 스트레스·유산소·외식·근력·좌식이 군집을 결정하게 됐습니다. 시드를 바꿔도 같은 결과가 나오는 정도(ARI)는 0.56에서 0.945로 올랐습니다.'));
  const labels = ['흡연 여부', '월 음주', '음주 빈도', '스트레스', '유산소 실천', '외식 빈도', '근력운동', '좌식 시간'];
  s.addChart(pres.charts.BAR, [{ name: '개선 전', labels, values: [0.964, 0.916, 0.774, 0.110, 0.157, 0.239, 0.148, 0.126] }, { name: '개선 후', labels, values: [0.011, 0.030, 0.034, 0.661, 0.404, 0.308, 0.296, 0.187] }],
    { x: 0.5, y: 1.95, w: 8.2, h: 4.9, barDir: 'bar', barGrouping: 'clustered', chartColors: [K.tealM, K.teal], showLegend: true, legendPos: 't', legendFontSize: 12,
      showValue: true, dataLabelPosition: 'outEnd', dataLabelFormatCode: '0.00', valAxisMaxVal: 1.1, valAxisLabelFormatCode: '0.0', catAxisOrientation: 'maxMin',
      showTitle: true, title: '변수별 η² (군집이 그 변수를 가르는 정도, 0~1)', titleFontSize: 13, titleColor: K.ink2, ...CH });
  stat(s, 9.2, 2.2, 3.5, '0.96 → 0.01', '흡연이 군집을 가르는 정도', K.ochre, 30);
  stat(s, 9.2, 3.85, 3.5, '0.56 → 0.945', '시드를 바꿔도 같은 결과가\n나오는 정도 (평균 ARI)', K.teal, 30);
  txt(s, '흡연·음주는 군집에 넣지 않고\n결과 설명용으로만 사용', { x: 9.2, y: 5.6, w: 3.5, h: 0.8, fontSize: 14, bold: true, color: K.deep });
}
{
  const s = slide('CONTENT', '생활습관 유형', '유형 개수 정하기', '대분류는 안정성을 지키면서 가장 잘게 나눌 수 있는 4개로 정했습니다', 60,
    n(60, '생활습관 지표 7개를 주성분 5개로 줄이고 k-medoids로 대분류를 나눴습니다. 개수를 고르는 기준은 시드를 10번 바꿨을 때 평균 ARI 0.8 이상입니다. 3, 4, 5개가 통과하고 6개에서 0.57로 떨어집니다. 3개는 서비스 유형으로 너무 거칠어서, 기준을 지키면서 가장 잘게 나눌 수 있는 4개를 골랐습니다. 그다음 대분류마다 남은 차이가 큰 변수 두 개로 다시 3개씩 나눠 모두 12개 유형이 됐습니다. k-medoids는 실제 사람 한 명을 중심으로 삼아 이상값에 덜 흔들립니다.'));
  s.addChart(pres.charts.BAR, [{ name: '시드 간 평균 ARI', labels: ['k = 3', 'k = 4 (선택)', 'k = 5', 'k = 6'], values: [1.0, 0.945, 0.857, 0.572] }],
    { x: 0.5, y: 1.95, w: 6.4, h: 4.6, barDir: 'col', chartColors: [K.tealM, K.teal, K.tealM, K.tealM], showLegend: false, showValue: true, dataLabelPosition: 'outEnd', dataLabelFormatCode: '0.000',
      valAxisMaxVal: 1.1, valAxisMinVal: 0, valAxisLabelFormatCode: '0.0', showTitle: true, title: '시드 10개 간 평균 ARI (기준 0.8 이상)', titleFontSize: 13, titleColor: K.ink2, ...CH });
  txt(s, '실루엣 0.182 · 0.163 · 0.154 · 0.162', { x: 0.6, y: 6.55, w: 6.3, h: 0.35, fontSize: 12, color: K.ink2, align: 'center' });
  const flow = [['생활습관 지표 7개', '유산소·근력·좌식·수면·스트레스·식사 규칙성·외식'], ['표준화 + 주성분 5개', '누적 설명분산 78.0%'], ['대분류 4개', '비활동형 · 운동형 · 고스트레스형 · 좌식·외식형'], ['대분류마다 3개씩', '남은 차이가 큰 변수 2개로 세분 → 12개 유형']];
  flow.forEach(([h, b], i) => {
    const y = 2.0 + i * 1.2; box(s, 7.4, y, 5.3, 0.95, i === 3 ? K.teal : K.tealXL);
    txt(s, h, { x: 7.65, y: y + 0.1, w: 4.9, h: 0.38, fontSize: 16, bold: true, color: i === 3 ? K.white : K.deep });
    txt(s, b, { x: 7.65, y: y + 0.5, w: 4.9, h: 0.38, fontSize: 12, color: i === 3 ? K.tealL : K.ink2 });
  });
}
{
  const s = slide('CONTENT', '생활습관 유형', '12개 생활습관 유형', '그렇게 나온 12개 유형에 생활습관이 드러나는 이름을 붙였습니다', 90,
    n(90, '이렇게 나온 12개 유형입니다. 몸을 덜 움직이는 나무늘보, 운동을 꾸준히 하는 갓생러, 스트레스가 많은 예민보스, 오래 앉아 있고 외식이 잦은 워커홀릭이 대분류입니다. 그 안에서 끼니나 근력운동 같은 습관으로 다시 나뉩니다. 예를 들어 배고픈 나무늘보는 운동이 적고 끼니를 자주 거르는 유형이고, 밸런스 갓생러는 근력운동도 하고 세 끼도 챙기는 유형입니다. 가장 작은 유형도 3.6%로, 따로 안내할 만한 크기입니다. 비율은 조사 가중치를 적용한 성인 인구 기준입니다.'));
  const G = [['나무늘보', '몸을 움직이는 시간이 적음', [['N1', '집밥좋아 나무늘보', '8.7%'], ['N2', '배고픈 나무늘보', '8.1%'], ['N3', '배부른 나무늘보', '8.3%']]],
    ['갓생러', '유산소·근력 운동을 꾸준히 함', [['A1', '뚜벅이 갓생러', '9.3%'], ['A2', '파워 갓생러', '8.4%'], ['A3', '밸런스 갓생러', '9.3%']]],
    ['예민보스', '스트레스를 많이 느낌', [['S1', '쉬고 싶은 예민보스', '11.0%'], ['S2', '산책하는 예민보스', '10.5%'], ['S3', '쇠질하는 예민보스', '3.6%']]],
    ['워커홀릭', '오래 앉아 있고 외식이 잦음', [['O1', '아침패스 워커홀릭', '10.0%'], ['O2', '삼시세끼 워커홀릭', '8.0%'], ['O3', '운동하는 워커홀릭', '4.7%']]]];
  G.forEach(([h, d, ts], i) => {
    const x = 0.6 + i * 3.1; box(s, x, 1.95, 2.9, 4.85, i % 2 ? K.tealXL : K.tealL);
    txt(s, h, { x: x + 0.2, y: 2.05, w: 2.5, h: 0.4, fontSize: 18, bold: true, color: K.deep });
    txt(s, d, { x: x + 0.2, y: 2.45, w: 2.6, h: 0.35, fontSize: 12, color: K.ink2 });
    ts.forEach(([id, nm, pct], j) => {
      const y = 2.95 + j * 1.27; s.addShape(pres.shapes.OVAL, { x: x + 0.15, y, w: 1.15, h: 1.15, fill: { color: K.white }, line: { color: K.white } });
      img(s, `mascot/type_${id}.png`, x + 0.18, y + 0.03, 1.09, 1.09);
      txt(s, id, { x: x + 1.38, y: y + 0.1, w: 1.4, h: 0.3, fontSize: 12, bold: true, color: K.teal });
      txt(s, nm.replace(/ (\S+)$/, '\n$1'), { x: x + 1.38, y: y + 0.36, w: 1.5, h: 0.5, fontSize: 13, bold: true, color: K.ink });
      txt(s, pct, { x: x + 1.38, y: y + 0.82, w: 1.4, h: 0.3, fontSize: 12, color: K.ink2 });
    });
  });
}
const SIL_TITLE = '다만 12개 유형은 "뚜렷이 떨어진 무리"는 아닙니다';
const SIL_NOTE = '정직하게 말씀드릴 부분이 있습니다. 군집이 얼마나 뚜렷한지 보는 실루엣이 0.163으로 낮습니다. 그래서 구조가 없는 무작위 자료를 같은 방법으로 20번씩 군집화해 비교했습니다. 실제 값은 무작위 자료 평균(0.183, 0.207)보다도 낮았습니다. 변수별 분포와 상관관계만으로 설명되는 수준을 넘는 구조는 확인되지 않은 것입니다. 이 검정은 간격 4 표준편차 이상의 덩어리는 잡아내지만 2 이하의 약한 덩어리는 못 잡아서, 덩어리가 전혀 없다는 뜻은 아닙니다. 그럼 나눈 유형은 의미가 없을까요? 예를 하나 들어 보겠습니다.';
function silhouetteSlide(s, caption = true) {
  img(s, 'fig_15_군집_귀무검정.png', 0.5, 2.05, 7.4, 3.9);
  [['0.163', '실제 자료의 실루엣'], ['0.183', '무작위 A 평균\n(변수 관계 없앰)'], ['0.207', '무작위 B 평균\n(관계 유지, 덩어리 없앰)']]
    .forEach(([v, l], i) => { box(s, 8.4, 2.05 + i * 1.18, 4.3, 1.02, i ? K.tealXL : K.ochreL); txt(s, v, { x: 8.65, y: 2.12 + i * 1.18, w: 1.5, h: 0.85, fontSize: 26, bold: true, color: i ? K.teal : K.ochreD, valign: 'middle' }); txt(s, l, { x: 10.15, y: 2.12 + i * 1.18, w: 2.45, h: 0.85, fontSize: 13, valign: 'middle' }); });
  if (caption) txt(s, '변수별 분포와 상관관계만으로 설명되는 수준을 넘는 구조는 확인되지 않았습니다\n(간격 2 표준편차 이하의 약한 덩어리는 이 검정으로 잡지 못합니다)', { x: 0.6, y: 6.1, w: 12.1, h: 0.75, fontSize: 14, color: K.ink2 });
}
{
  const s = slide('CONTENT', '생활습관 유형', '유형은 얼마나 뚜렷한가 (귀무 검정)', SIL_TITLE, 50, n(50, SIL_NOTE));
  silhouetteSlide(s);
}
{
  const s = slide('DETOUR', '생활습관 유형', '잠깐, 예를 하나 들어 보겠습니다', '무지개에는 경계선이 없지만, 우리는 일곱 색으로 나눠 부릅니다', 40,
    n(40, '무지개를 떠올려 보세요. 빨강과 주황 사이에 선이 그어져 있지 않습니다. 색은 이어져 있습니다. 그래도 우리는 일곱 가지 이름으로 나눠 부르고, 그 덕분에 "주황색 옷"이라고 말하면 서로 알아듣습니다. 나누는 기준이 같으면 누가 봐도 같은 이름이 나오고요. 중요한 것은 "경계가 뚜렷한가"가 아니라 "나눈 이름이 쓸모 있는가"입니다. 생활습관도 이어져 있지만, 같은 응답이면 항상 같은 유형이 나오게 나눠 두면 안내하기 좋은 이름이 됩니다.'));
  img(s, 'rainbow.png', 0.6, 2.15, 12.1, 1.8);
  ['빨강', '주황', '노랑', '초록', '파랑', '남색', '보라'].forEach((c, i) => txt(s, c, { x: 0.6 + i * (12.1 / 7), y: 4.05, w: 12.1 / 7, h: 0.4, fontSize: 15, bold: true, color: K.deep, align: 'center' }));
  [['경계선은 없지만', '색은 이어져 있음\n= 생활습관도 이어진 분포'], ['이름이 있으면', '"주황색 옷"처럼 말하고 기억하기 쉬움\n= "배고픈 나무늘보"'], ['기준이 같으면', '누가 봐도 같은 색 이름\n= 같은 응답이면 항상 같은 유형']]
    .forEach(([h, b], i) => { const x = 0.6 + i * 4.1; box(s, x, 4.75, 3.8, 1.75, K.white); txt(s, h, { x: x + 0.3, y: 4.9, w: 3.3, h: 0.4, fontSize: 17, bold: true, color: K.teal }); txt(s, b, { x: x + 0.3, y: 5.35, w: 3.3, h: 1.0, fontSize: 14 }); });
}
{
  const s = slide('CONTENT', '생활습관 유형', '다시 돌아와서', SIL_TITLE, 25,
    n(25, '다시 돌아와서, 실루엣이 낮다는 것은 생활습관이 무지개처럼 이어져 있다는 뜻입니다. 그래서 저희는 유형의 가치를 "얼마나 뚜렷한가" 대신 "서비스에 쓸모 있는가"로 따로 확인했습니다.'));
  silhouetteSlide(s, false);
  box(s, 0.6, 6.05, 12.1, 0.85, K.teal);
  txt(s, '생활습관은 무지개처럼 이어져 있습니다 → 그래서 유형의 가치는 "뚜렷함" 대신 "쓸모"로 확인했습니다', { x: 0.85, y: 6.05, w: 11.7, h: 0.85, fontSize: 17, bold: true, color: K.white, valign: 'middle' });
}
{
  const s = slide('CONTENT', '생활습관 유형', '쓸모 있는 구분인가 (ADAMS)', '실무 고객 세분화의 다섯 조건(ADAMS)을 모두 통과했습니다', 75,
    n(75, '실무에서 고객 세분화가 쓸모 있는지는 ADAMS라는 다섯 조건으로 봅니다. 셀 수 있는가, 따로 다룰 만큼 큰가, 새 사용자를 넣을 수 있는가, 그룹마다 다른가, 그룹마다 다른 안내를 줄 수 있는가입니다. 12개 유형은 가장 작은 유형도 3.6%이고, 웹 설문만으로 100% 같은 유형이 다시 나오며, 유형과 영양소 156쌍 중 72쌍이 같은 성별·나이보다 10% 이상 다르고, 유형마다 해당하는 습관 미션이 크게 다릅니다. 참고로 흡연·음주를 넣은 7개 유형 안은 더 안정적이었지만 흡연·음주가 유형을 주도하고 성별 쏠림이 두 배라 택하지 않았습니다.'));
  const A = [['M', '측정 가능', '15,062명 전원이\n유형에 배정되고\n비율을 셀 수 있음'], ['S', '충분한 크기', '가장 작은 유형도\n3.6% (454명),\n나머지 4.7~11%'], ['A', '도달 가능', '웹 설문만으로\n재배정 일치율 100%,\n시드를 바꿔도 같음'], ['D', '차별성', '유형×영양소\n156쌍 중 72쌍이\n같은 성별·나이보다\n10% 이상 다름'], ['A', '실행 가능', '유형마다\n해당 비율이 크게\n다른 습관 미션\n(30%p 이상 차이)']];
  A.forEach(([l, h, b], i) => {
    const x = 0.6 + i * 2.48; box(s, x, 2.1, 2.25, 3.55, K.tealXL);
    s.addShape(pres.shapes.OVAL, { x: x + 0.25, y: 2.3, w: 0.8, h: 0.8, fill: { color: K.teal }, line: { color: K.teal } });
    txt(s, l, { x: x + 0.25, y: 2.3, w: 0.8, h: 0.8, fontSize: 26, bold: true, color: K.white, align: 'center', valign: 'middle' });
    txt(s, h, { x: x + 0.25, y: 3.3, w: 1.9, h: 0.4, fontSize: 17, bold: true, color: K.deep });
    txt(s, b, { x: x + 0.25, y: 3.8, w: 1.95, h: 1.3, fontSize: 13, color: K.ink2 });
    tag(s, x + 0.25, 5.15, '통과', 'done');
  });
  txt(s, '비교한 7개 유형 안: 더 안정적(0.911 vs 0.679)이지만 흡연·음주가 유형을 주도하고 성별 쏠림이 두 배(Cramér V 0.418 vs 0.226) → 12개 안 채택', { x: 0.6, y: 5.95, w: 12.1, h: 0.7, fontSize: 13, color: K.ink2 });
}

// ════════════════════ 4. 유형별 부족 영양소 ════════════════════
{
  const s = slide('CONTENT', '유형별 부족 영양소', '예측 문제 설정 (지도 학습)', '유형·성별·연령대만으로 영양소 15개의 "부족 확률"을 예측합니다', 60,
    n(60, '이제 지도 학습입니다. 입력은 설문 첫 화면에서 바로 알 수 있는 유형, 성별, 연령대뿐이고, 출력은 영양소 15개 각각의 부족 확률입니다. 섭취량은 사용자가 모르고 정답을 만든 재료이므로 넣지 않았습니다. 유형이 정말 도움이 되는지 보려고, 성별과 연령대만 쓴 모델을 기준으로 두고 유형을 더했을 때 얼마나 좋아지는지를 봤습니다. 평가는 2022–23년으로 학습하고 2024년으로 하는 연도 분할입니다. 무작위 분할보다 엄격하고, 내년 사용자에게도 통하는지를 보여 줍니다.'));
  const ins = ['생활습관 유형 (12)', '성별 (2)', '연령대 (5)'];
  ins.forEach((t, i) => { box(s, 0.6, 2.15 + i * 0.85, 3.2, 0.68, K.tealL); txt(s, t, { x: 0.85, y: 2.15 + i * 0.85, w: 2.8, h: 0.68, fontSize: 15, bold: true, color: K.deep, valign: 'middle' }); });
  txt(s, '→', { x: 3.9, y: 2.8, w: 0.5, h: 0.6, fontSize: 28, bold: true, color: K.teal, align: 'center' });
  box(s, 4.5, 2.15, 3.3, 2.38, K.teal);
  txt(s, '조사 가중\n로지스틱 회귀 /\n그래디언트 부스팅', { x: 4.7, y: 2.3, w: 2.9, h: 1.3, fontSize: 15, bold: true, color: K.white });
  txt(s, '영양소마다 후보 10개 비교', { x: 4.7, y: 3.75, w: 2.9, h: 0.6, fontSize: 12, color: K.tealL });
  txt(s, '→', { x: 7.9, y: 2.8, w: 0.5, h: 0.6, fontSize: 28, bold: true, color: K.teal, align: 'center' });
  box(s, 8.5, 2.15, 4.2, 2.38, K.ochreL);
  txt(s, '영양소 15개의 부족 확률', { x: 8.75, y: 2.3, w: 3.8, h: 0.45, fontSize: 16, bold: true, color: K.ochreD });
  txt(s, '유형 × 성별 × 연령대 120개 조합마다\n"10명 중 N명" + 같은 성별·나이 대비 몇 배', { x: 8.75, y: 2.85, w: 3.8, h: 1.4, fontSize: 13 });
  txt(s, '넣지 않은 것: 섭취량·에너지 (사용자가 모르고, 정답을 만든 재료 → 정보 누수 방지)', { x: 0.6, y: 4.75, w: 12, h: 0.4, fontSize: 14, bold: true, color: K.deep });
  box(s, 0.6, 5.35, 8.1, 0.8, K.tealM); txt(s, '2022–23년 9,742명: 학습 + 5겹 교차검증으로 후보 선택', { x: 0.8, y: 5.35, w: 7.8, h: 0.8, fontSize: 14, bold: true, color: K.white, valign: 'middle' });
  box(s, 8.8, 5.35, 3.9, 0.8, K.ochre); txt(s, '2024년 5,320명: 최종 평가', { x: 9.0, y: 5.35, w: 3.6, h: 0.8, fontSize: 14, bold: true, color: K.white, valign: 'middle' });
  txt(s, '기준 모델 = 성별 + 연령대만 사용 → 유형을 더해 좋아진 만큼이 유형의 가치', { x: 0.6, y: 6.35, w: 12, h: 0.4, fontSize: 13, color: K.ink2 });
}
{
  const s = slide('CONTENT', '유형별 부족 영양소', '모델 선택과 하이퍼파라미터', '후보 10개를 비교했지만 단순한 로지스틱 회귀로 충분했습니다', 60,
    n(60, '영양소마다 규제 강도가 다른 로지스틱 회귀, 유형과 성별의 교호작용을 넣은 모델, 그래디언트 부스팅까지 10개 후보를 교차검증 로그 손실로 비교했습니다. 손실이 가장 작은 모델과 1 표준오차 안에서 차이가 없으면 더 단순한 모델을 고르는 1-SE 규칙을 썼습니다. 그 결과 15개 중 14개는 로지스틱 회귀, 철 하나만 부스팅이 남았습니다. 그래프에서 보듯 부스팅이나 앙상블은 로지스틱보다 나아지지 않았습니다. 반면 개인 응답을 더 넣으면 AUC가 0.03 오릅니다. 이건 유형이 아니라 개인 예측이므로 개인화 단계의 몫으로 넘겼습니다.'));
  const L = ['유형+성별+연령대\n(채택)', '+ 나이 곡선\n유형×성별', '+ 생활습관\n응답 14개', '+ 채소·과일\n섭취 빈도'];
  s.addChart(pres.charts.BAR, [{ name: '로지스틱 회귀', labels: L, values: [0.631, 0.633, 0.648, 0.660] }, { name: '그래디언트 부스팅', labels: L, values: [0.630, 0.626, 0.639, 0.653] }, { name: '앙상블(평균)', labels: L, values: [0.633, 0.633, 0.648, 0.661] }],
    { x: 0.5, y: 1.95, w: 7.9, h: 4.9, barDir: 'col', barGrouping: 'clustered', chartColors: [K.teal, K.ochre, K.tealM], showLegend: true, legendPos: 't', legendFontSize: 12,
      valAxisMinVal: 0.6, valAxisMaxVal: 0.67, valAxisLabelFormatCode: '0.00', showValue: false, showTitle: true, title: '2024년 평가 AUC (영양소 15개 평균)', titleFontSize: 13, titleColor: K.ink2, ...CH });
  [['14 / 15', '로지스틱 회귀가 선택된 영양소\n(C=0.01 10개, C=0.1 4개)'], ['1 / 15', '부스팅이 남은 영양소 (철)\n1-SE 안에 로지스틱 후보 없음'], ['+0.030', '개인 응답을 더했을 때 AUC\n→ 개인화 단계의 근거']]
    .forEach(([v, l], i) => { box(s, 8.8, 2.05 + i * 1.6, 3.9, 1.42, i === 2 ? K.ochreL : K.tealXL); stat(s, 9.05, 2.13 + i * 1.6, 3.5, v, l, i === 2 ? K.ochreD : K.teal, 26); });
}
{
  const s = slide('CONTENT', '유형별 부족 영양소', '2024년 평가 결과', '유형을 더하면 15개 중 13개 영양소에서\n성별·나이만 알 때보다 더 잘 가려냅니다', 60,
    n(60, '2024년 평가 결과입니다. 점은 유형을 더했을 때 AUC가 오른 정도이고, 선은 부트스트랩 2,000번으로 구한 95% 신뢰구간입니다. 13개 영양소에서 구간 전체가 0보다 오른쪽이라, 유형이 성별·나이 이상의 정보를 준다고 판단했습니다. 회색인 비타민D와 E는 거의 모든 사람이 부족해서 유형으로 더 가를 여지가 없습니다. 이 둘은 공통 안내로만 씁니다. 학습과 평가의 차이는 최대 0.029로 과적합은 작고, 예측 확률과 실제 비율의 차이도 최대 1.7%p라 "10명 중 N명"으로 그대로 보여 줄 수 있습니다. 다만 AUC 자체는 0.56~0.70으로 중간 수준이라, 진단이 아니라 경향 안내로 씁니다.'));
  img(s, 'f06_ΔAUC.png', 0.5, 1.95, 7.3, 4.95);
  [['+0.014 ~ +0.040', 'AUC 향상 (13개 영양소, 95% 신뢰구간 하한 > 0)'], ['최대 0.029', '학습 − 평가 AUC 차이 (과적합 작음)'], ['최대 1.7%p', '예측 확률과 실제 비율 차이\n→ "10명 중 N명"으로 표시 가능']]
    .forEach(([v, l], i) => { box(s, 8.2, 2.05 + i * 1.45, 4.5, 1.3, K.tealXL); stat(s, 8.45, 2.12 + i * 1.45, 4.1, v, l, K.teal, 24); });
  txt(s, 'AUC 0.56~0.70 = 중간 수준\n→ 진단이 아닌 "경향 안내"로 사용', { x: 8.2, y: 6.4, w: 4.6, h: 0.6, fontSize: 13, bold: true, color: K.ochreD });
}
{
  const s = slide('CONTENT', '유형별 부족 영양소', '유형별 부족 패턴', '끼니를 거르는 유형일수록 철·인·단백질·아연이 더 부족합니다', 60,
    n(60, '유형마다 같은 성별·연령대 평균보다 몇 배 부족한지 나타낸 그림입니다. 1보다 크면 황토색, 작으면 청록색입니다. 배고픈 나무늘보, 쉬고 싶은 예민보스, 아침패스 워커홀릭처럼 끼니를 자주 거르거나 활동이 적은 유형은 철·인·단백질·아연이 1.2~1.7배 더 부족합니다. 반대로 세 끼를 규칙적으로 먹는 밸런스 갓생러, 삼시세끼 워커홀릭, 배부른 나무늘보는 대부분 덜 부족합니다. 오른쪽 공통 영양소 8개는 유형 간 차이가 거의 없습니다. 공통 영양소를 따로 묶는 설계가 맞다는 근거입니다.'));
  img(s, 'f05_유형x영양소_배수.png', 0.5, 1.95, 8.4, 4.95);
  [['1.2 ~ 1.7배', '끼니를 거르는 N2·S1·O1의\n철·인·단백질·아연', K.ochreD, K.ochreL], ['0.67 ~ 0.9배', '세 끼를 챙기는 A3·O2·N3는\n대부분 덜 부족', K.teal, K.tealXL], ['0.95 ~ 1.05배', '공통 영양소 8개는\n유형 간 차이가 작음', K.ink2, 'F2F2F2']]
    .forEach(([v, l, c, f], i) => { box(s, 9.2, 2.05 + i * 1.6, 3.5, 1.42, f); stat(s, 9.45, 2.13 + i * 1.6, 3.1, v, l, c, 24); });
}
{
  const s = slide('CONTENT', '유형별 부족 영양소', '왜 부족한가', '유형 차이의 82%는 "얼마나, 무엇을 먹느냐"로 설명됩니다', 60,
    n(60, '"왜 그 유형은 철이 부족한가"에 이유를 붙이려고, 군집에 쓰지 않은 식품 섭취와 에너지로 차이를 나눠 봤습니다. 같은 성별·나이와 비교한 부족 비율에서 출발해, 식사량을 맞추거나 식품군을 맞추면 차이가 얼마나 줄어드는지 계산했습니다. 차이가 10% 이상인 72쌍에서 식사량만 맞춰도 59%, 식품군만 맞춰도 67%, 둘 다 맞추면 82%가 줄어듭니다. 배고픈 나무늘보는 콩·유제품·달걀을 덜 먹고 식사량도 적어서, 밸런스 갓생러는 콩·달걀·유제품을 30% 넘게 더 먹어서 차이가 납니다. 같은 하루 기록에서 나온 값이라 독립 검증은 아니고, 상관관계이므로 "콩을 먹으면 좋아진다"는 뜻은 아닙니다.'));
  [['59%', '식사량(에너지)만\n맞췄을 때 줄어든 몫'], ['67%', '식품군만\n맞췄을 때'], ['82%', '둘 다\n맞췄을 때']]
    .forEach(([v, l], i) => { const x = 0.6 + i * 2.2; box(s, x, 2.1, 2.0, 1.95, i === 2 ? K.teal : K.tealXL); txt(s, v, { x: x + 0.2, y: 2.2, w: 1.7, h: 0.75, fontSize: 32, bold: true, color: i === 2 ? K.white : K.teal }); txt(s, l, { x: x + 0.2, y: 3.0, w: 1.7, h: 0.9, fontSize: 12, color: i === 2 ? K.tealL : K.ink2 }); });
  txt(s, '같은 성별·나이보다 10% 이상 차이 나는 72쌍(유형 × 영양소) 평균', { x: 0.6, y: 4.15, w: 6.6, h: 0.35, fontSize: 12, color: K.ink2 });
  const rows = [['', '같은 성별·나이 대비\n식품 섭취', '부족\n(관측/기대)'], ['N2\n배고픈\n나무늘보', '콩류 25%↓ 유제품 18%↓\n과일 16%↓ 달걀 15%↓\n에너지 8%↓', '인 1.65\n단백질 1.44\n철 1.42'], ['A3\n밸런스\n갓생러', '콩류 38%↑ 달걀 34%↑\n유제품 32%↑ 과일 32%↑', '인 0.46\n철 0.61\n아연 0.64']];
  s.addTable(rows.map((r, i) => r.map((c, j) => ({ text: c, options: i === 0 ? { bold: true, color: K.deep, fill: { color: K.tealL } } : (j === 0 ? { bold: true, color: K.deep } : {}) }))),
    { x: 7.4, y: 2.1, w: 5.3, colW: [1.2, 2.6, 1.5], fontFace: FONT, fontSize: 13, color: K.ink, border: { type: 'solid', pt: 0.75, color: K.line }, rowH: [0.6, 1.05, 1.05], valign: 'middle', margin: [3, 6, 3, 6] });
  txt(s, 'N2·O1은 식사량 쪽, A3는 식품 선택 쪽이 더 큽니다', { x: 7.4, y: 5.05, w: 5.3, h: 0.4, fontSize: 14, bold: true, color: K.deep });
  txt(s, '→ 특정 영양제보다 끼니와 식사 구성을 먼저 안내합니다\n식품군과 영양소가 같은 하루 기록이라 독립 검증은 아니며, 상관관계입니다', { x: 0.6, y: 5.75, w: 12.1, h: 0.9, fontSize: 14, color: K.ink });
}
{
  const s = slide('CONTENT', '유형별 부족 영양소', '화면 표시 규칙', '화면은 "모두 챙길 영양소"와\n"내 유형이 특히 챙길 영양소"로 나눠 보여 줍니다', 60,
    n(60, '확률을 그대로 보여 주면 공통 영양소 8개가 늘 위를 차지해서 유형이 달라도 화면이 비슷해집니다. 그래서 세 가지 규칙을 120개 조합에 적용해 비교했습니다. 확률 0.5 이상을 모두 보여 주면 화면마다 8~9개가 나열됩니다. 상위 3개를 보여 주면 평균보다 오히려 덜 부족한 영양소를 절반 가까이 "부족"으로 보여 줍니다. 채택한 2단 표시는 공통 8개를 한 줄로 묶고, 그 밖에서는 같은 성별·나이보다 1.2배 이상이면서 10명 중 3명 이상일 때만 보여 줍니다. 부족이 적은 유형에는 "특히 더 부족한 건 없어요"라는 좋은 소식도 줄 수 있습니다. 기준값은 결과를 보기 전에 정했습니다.'));
  box(s, 0.6, 2.05, 5.6, 4.6, K.white, { line: { color: K.tealM, width: 1 } });
  txt(s, 'N2 배고픈 나무늘보 · 여성 · 30–49세', { x: 0.85, y: 2.2, w: 5.2, h: 0.4, fontSize: 15, bold: true, color: K.deep });
  txt(s, '모두가 챙겨야 할 영양소', { x: 0.85, y: 2.75, w: 5.2, h: 0.35, fontSize: 13, bold: true, color: K.ochreD });
  txt(s, '비타민D · 비타민E · 칼륨 · 엽산 · 비타민A · 비타민C · 식이섬유 · 칼슘', { x: 0.85, y: 3.1, w: 5.2, h: 0.7, fontSize: 13, color: K.ink2 });
  txt(s, '내 유형이 특히 챙길 영양소', { x: 0.85, y: 3.95, w: 5.2, h: 0.35, fontSize: 13, bold: true, color: K.teal });
  [['철', '10명 중 6명 · 평균 4명', '이 유형에서 특히 많아요'], ['마그네슘', '10명 중 6명 · 평균 5명', '식사량 점검이 먼저예요'], ['티아민', '10명 중 6명 · 평균 5명', '식사량 점검이 먼저예요']]
    .forEach(([a, b, c], i) => { const y = 4.38 + i * 0.7; box(s, 0.85, y, 5.1, 0.6, K.tealXL); txt(s, a, { x: 1.0, y, w: 1.2, h: 0.6, fontSize: 14, bold: true, valign: 'middle' }); txt(s, b, { x: 2.15, y, w: 2.1, h: 0.6, fontSize: 12, color: K.ink2, valign: 'middle' }); txt(s, c, { x: 4.2, y, w: 1.75, h: 0.6, fontSize: 11, color: K.teal, valign: 'middle' }); });
  const rows = [['', '확률 ≥ 0.5 전부', '2단 표시 (채택)', '상위 3개'], ['한 화면 영양소 수', '8.6개', '공통 8 + 1.3개', '공통 8 + 3개'], ['평균보다 덜 부족한데 표시', '해당 없음', '28 / 160', '158 / 360'], ['"특히 없음" 좋은 소식', '불가', '40 / 120 조합', '불가']];
  s.addTable(rows.map((r, i) => r.map((c, j) => ({ text: c, options: { bold: i === 0 || j === 2, color: i === 0 ? K.deep : (j === 2 ? K.teal : K.ink), fill: { color: i === 0 ? K.tealL : (j === 2 ? K.tealXL : K.white) }, align: j ? 'center' : 'left' } }))),
    { x: 6.6, y: 2.05, w: 6.1, colW: [2.0, 1.25, 1.6, 1.25], fontFace: FONT, fontSize: 13, color: K.ink, border: { type: 'solid', pt: 0.75, color: K.line }, rowH: 0.7, valign: 'middle', margin: [3, 6, 3, 6] });
  txt(s, '기준값(1.2배, 10명 중 3명)은\n결과를 보기 전에 팀 문서로 정하고 고정했습니다', { x: 6.6, y: 5.15, w: 6.1, h: 0.7, fontSize: 13, color: K.ink2 });
}
{
  const s = slide('CONTENT', '유형별 부족 영양소', '미래 자료로 검증', '학습에 사용하지 않은 2024년에도\n안내한 영양소는 실제로 1.09배 더 부족했습니다', 50,
    n(50, '마지막으로 가장 엄격한 확인입니다. 2022–23년 자료로만 다시 학습한 모델로 안내 항목을 고른 뒤, 2024년 실제 자료에 대 봤습니다. 같은 성별·연령대 전체 비율로 기대한 인원보다 1.09배 더 많은 사람이 실제로 부족했습니다. 문구별로 보면 "이 유형에서 특히 많아요"가 1.36배, "식사량 점검이 먼저예요"가 1.24배, "같은 성별·나이대에서 흔해요"가 1.04배로, 문구가 말하는 강도와 실제 차이의 순서가 일치합니다.'));
  s.addChart(pres.charts.BAR, [{ name: '관측 ÷ 기대', labels: ['"이 유형에서\n특히 많아요"', '"식사량 점검이\n먼저예요"', '"같은 성별·나이대\n에서 흔해요"', '표시 항목\n전체'], values: [1.36, 1.24, 1.04, 1.09] }],
    { x: 0.5, y: 1.95, w: 7.6, h: 4.9, barDir: 'col', chartColors: [K.teal, K.teal, K.tealM, K.ochre], showLegend: false, showValue: true, dataLabelPosition: 'outEnd', dataLabelFormatCode: '0.00"배"',
      valAxisMinVal: 0.9, valAxisMaxVal: 1.5, valAxisLabelFormatCode: '0.0', showTitle: true, title: '2024년 실제 부족 인원 ÷ 기대 인원 (1.0 = 같은 성별·나이 평균)', titleFontSize: 13, titleColor: K.ink2, ...CH });
  [['1.09배', '안내 항목 163개 전체\n(95% 신뢰구간 1.06~1.12)', K.ochreD, K.ochreL], ['순서 일치', '문구가 말하는 강도 =\n실제로 더 부족한 정도', K.teal, K.tealXL]]
    .forEach(([v, l, c, f], i) => { box(s, 8.6, 2.15 + i * 2.1, 4.1, 1.85, f); stat(s, 8.9, 2.3 + i * 2.1, 3.6, v, l, c, 32); });
}

// ════════════════════ 5. 개인 맞춤 ════════════════════
const PER_TITLE = '유형만으로는 한계가 있어,\n원하는 사람은 개인 응답으로 한 단계 더 들어갑니다';
function personalChart(s, h = 4.9) {
  s.addChart(pres.charts.BAR, [{ name: 'AUC', labels: ['성별·나이만', '+ 생활습관 유형', '개인 응답 18개\n(개인 모델)'], values: [0.604, 0.631, 0.659] }],
    { x: 0.5, y: 1.95, w: 7.3, h, barDir: 'col', chartColors: [K.tealM, K.teal, K.ochre], showLegend: false, showValue: true, dataLabelPosition: 'outEnd', dataLabelFormatCode: '0.000',
      valAxisMinVal: 0.55, valAxisMaxVal: 0.68, valAxisLabelFormatCode: '0.00', showTitle: true, title: '같은 사람·같은 정답·같은 2024년 평가에서 AUC (13개 영양소 평균)', titleFontSize: 13, titleColor: K.ink2, ...CH });
  const items = [['+0.027', '유형을 더했을 때', K.teal, K.tealXL], ['+0.028', '개인 응답까지 갔을 때\n(13개 중 11개 유의)', K.ochreD, K.ochreL], ['52%', '같은 유형·성별·나이 안에서도 철 부족\n확률이 유형 평균에서 20% 이상 벗어남', K.ink2, 'F2F2F2']];
  const short = h < 4.9, g = short ? 1.95 : 1.6;
  (short ? items.slice(0, 2) : items).forEach(([v, l, c, f], i) => { box(s, 8.2, 2.05 + i * g, 4.5, g - 0.15, f); stat(s, 8.45, 2.1 + i * g, 4.1, v, l, c, 24); });
}
{
  const s = slide('CONTENT', '개인 맞춤', '왜 두 단계인가', PER_TITLE, 60,
    n(60, '그럼 유형만으로 충분할까요? 같은 사람, 같은 정답, 같은 2024년 평가에서 비교했습니다. 성별·나이만 쓰면 AUC 0.604, 유형을 더하면 0.631, 재준님의 개인 모델처럼 개인 응답 18개를 쓰면 0.659까지 오릅니다. 그리고 같은 유형·성별·나이 안에서도 사람마다 확률이 꽤 다릅니다. 철의 경우 절반 넘는 사람이 유형 평균에서 20% 이상 벗어납니다. 이것도 비유로 설명드리겠습니다.'));
  personalChart(s);
}
{
  const s = slide('DETOUR', '개인 맞춤', '잠깐, 날씨 예보로 비유하면', '전국 예보 → 우리 동네 예보 → 내가 서 있는 곳의 날씨', 40,
    n(40, '날씨 예보를 생각해 보세요. 전국 예보만 봐도 대략은 압니다. 이게 성별·나이 평균입니다. 우리 동네 예보를 보면 더 정확해지고, 무엇보다 이웃과 함께 이야기할 수 있습니다. 이게 생활습관 유형이고, 그래서 1단계 결과는 친구와 공유할 수 있게 만들었습니다. 외출 직전에 내가 서 있는 곳의 날씨를 확인하면 우산을 챙길지 정확히 정할 수 있습니다. 이게 2단계 개인 결과입니다.'));
  // 크기가 줄어드는 원 세 개: 넓은 범위 → 좁은 범위
  const C = [[0.8, 3.6, '전국 예보', '성별·나이 평균', 'AUC 0.604', K.tealL, K.deep], [5.15, 3.1, '우리 동네 예보', '생활습관 유형\n1단계 (공유용)', 'AUC 0.631', K.tealM, K.deep], [9.35, 2.6, '내 위치', '개인 응답\n2단계 (나만 보기)', 'AUC 0.659', K.ochre, K.white]];
  const cy = 4.15;
  C.forEach(([x, d, h, b, v, f, fc]) => {
    const y = cy - d / 2;
    s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: f }, line: { color: f } });
    txt(s, h, { x, y: cy - 0.95, w: d, h: 0.45, fontSize: 18, bold: true, color: fc, align: 'center' });
    txt(s, b, { x: x + 0.1, y: cy - 0.42, w: d - 0.2, h: 0.65, fontSize: 12, color: fc, align: 'center' });
    txt(s, v, { x, y: cy + 0.35, w: d, h: 0.4, fontSize: 15, bold: true, color: fc, align: 'center' });
  });
  txt(s, '→', { x: 4.5, y: cy - 0.3, w: 0.6, h: 0.6, fontSize: 28, bold: true, color: K.teal, align: 'center' });
  txt(s, '→', { x: 8.35, y: cy - 0.3, w: 0.9, h: 0.6, fontSize: 28, bold: true, color: K.teal, align: 'center' });
  txt(s, '동네 예보로 감을 잡고(공유), 나갈 때 내 위치를 확인합니다(개인)', { x: 0.6, y: 6.45, w: 12.1, h: 0.4, fontSize: 15, bold: true, color: K.deep, align: 'center' });
}
{
  const s = slide('CONTENT', '개인 맞춤', '다시 돌아와서', PER_TITLE, 25,
    n(25, '다시 돌아와서, 그래서 유형 결과는 모두에게 공유용으로, 개인 결과는 원하는 사람만 나만 보기로 나눴습니다. 개인 결과가 어떻게 계산되는지 보겠습니다.'));
  personalChart(s, 4.0);
  box(s, 0.6, 6.05, 12.1, 0.85, K.ochre);
  txt(s, '그래서 1단계 유형 결과는 모두에게, 공유용  ·  2단계 개인 결과는 원하는 사람만, 나만 보기', { x: 0.85, y: 6.05, w: 11.7, h: 0.85, fontSize: 17, bold: true, color: K.white, valign: 'middle' });
}
{
  const s = slide('CONTENT', '개인 맞춤', '개인 예측 모델', '개인 결과는 두 가지 신호를 평균하지 않고 나란히 보여 줍니다', 75,
    n(75, '개인 결과에는 두 모델이 있습니다. 첫째, 생활습관 모델은 생활습관 응답과 성별·나이로 영양 신호 14개를 냅니다. 2022–23년 학습, 2024년 독립 평가에서 평균 AUC 0.665입니다. 둘째, 평소 식사 모델은 고기·생선·달걀·콩·유제품을 얼마나 자주 먹는지 5문항으로 10개 신호를 냅니다. 2012–2016년 식품섭취빈도 자료로 학습하고 2016년으로 평가해 AUC 0.877이며, 19–64세에서 검증했습니다. 두 확률은 성격이 달라 평균하지 않고, 예를 들어 칼슘이 생활습관으로는 보통, 평소 식사로는 높음처럼 나란히 보여 줍니다. 평소 식사 모델의 정답 정의는 지금 팀 안에서 한 번 더 확인하고 있습니다.'));
  tag(s, 10.9, 0.3, '마무리 중', 'wip');
  const M = [['생활습관 모델', '생활습관 응답 + 성별·나이', '영양 신호 14개', '0.665', '2022–23 학습 → 2024 평가', K.teal, K.tealXL],
    ['평소 식사 5문항 모델', '고기·생선·달걀·콩·유제품 빈도 + 성별·나이', '영양 신호 10개', '0.877', '2012–15 학습 → 2016 평가 (19–64세)', K.ochreD, K.ochreL]];
  M.forEach(([h, i1, o, auc, sp, c, f], k) => {
    const x = 0.6 + k * 6.15; box(s, x, 2.05, 5.95, 3.15, f);
    txt(s, h, { x: x + 0.3, y: 2.2, w: 5.4, h: 0.45, fontSize: 19, bold: true, color: c });
    txt(s, '입력  ' + i1, { x: x + 0.3, y: 2.8, w: 5.4, h: 0.4, fontSize: 14 });
    txt(s, '출력  ' + o, { x: x + 0.3, y: 3.22, w: 5.4, h: 0.4, fontSize: 14 });
    txt(s, auc, { x: x + 0.3, y: 3.75, w: 2.2, h: 0.8, fontSize: 36, bold: true, color: c });
    txt(s, '평균 AUC\n' + sp, { x: x + 2.45, y: 3.8, w: 3.3, h: 0.8, fontSize: 12, color: K.ink2 });
    if (k === 1) tag(s, x + 0.3, 4.72, '정답 정의 팀 내 확인 중', 'idea');
  });
  box(s, 0.6, 5.45, 12.1, 1.2, K.white, { line: { color: K.line, width: 0.75 } });
  txt(s, '화면 예시', { x: 0.85, y: 5.55, w: 2, h: 0.35, fontSize: 12, bold: true, color: K.mute });
  txt(s, '칼슘   생활습관 신호: 보통   ·   평소 식사 신호: 높음   →  "평소 식사로 보면 챙겨 볼 만해요"', { x: 0.85, y: 5.9, w: 11.6, h: 0.55, fontSize: 16, bold: true, color: K.deep });
}
{
  const s = slide('CONTENT', '개인 맞춤', '건강기능식품 정보', '건강기능식품 46,154개를 9단계로 걸러 2,785개 후보만 남겼습니다', 75,
    n(75, '개인 결과의 마지막은 건강기능식품 정보입니다. 준혁님이 식약처에 신고된 46,154개 제품에서 출발해, 임산부·질환 대상 제품을 빼고, 이름과 성분이 다른 제품, 다이어트처럼 목적이 다른 제품, 하루 섭취량이 상한을 넘거나 확인할 수 없는 제품, 품질 정보가 부족한 제품을 단계별로 걸러 2,785개 후보만 남겼습니다. 화면 원칙은 네 가지입니다. 음식 안내가 먼저이고, "이런 제품도 있어요"라는 제안 톤으로 순위·가격·판매처는 보여 주지 않습니다. 여러 제품을 함께 볼 때는 상한을 합쳐 확인하고, 임신·질환·복용약이 있으면 전문가와 먼저 상의하도록 안내합니다. 사람마다 고르는 규칙은 지금 마무리하고 있습니다.'));
  tag(s, 10.9, 0.3, '마무리 중', 'wip');
  const F = [['식약처 신고 제품', 46154], ['1 대상 거르기 (임산부·질환 제외)', 17834], ['2 이름-성분 불일치 제외', 16738], ['3 다른 목적 제외', 11222], ['5 영양소 11종 제품군', 6318], ['7 상한섭취량 초과 제외', 5187], ['8 품질 거르기', 3815], ['9 적정성 점수 70점 이상', 2785]];
  s.addChart(pres.charts.BAR, [{ name: '남은 제품 수', labels: F.map((f) => f[0]), values: F.map((f) => f[1]) }],
    { x: 0.5, y: 1.95, w: 7.6, h: 4.9, barDir: 'bar', chartColors: [K.tealM, K.tealM, K.tealM, K.tealM, K.tealM, K.tealM, K.tealM, K.ochre], showLegend: false, showValue: true, dataLabelPosition: 'outEnd', dataLabelFormatCode: '#,##0',
      catAxisOrientation: 'maxMin', valAxisHidden: true, valGridLine: { style: 'none' }, showTitle: true, title: '단계별 남은 제품 수 (2022년 이후 신고분 기준, 일부 단계 생략)', titleFontSize: 13, titleColor: K.ink2,
      ...Object.fromEntries(Object.entries(CH).filter(([k]) => k !== 'valGridLine')) });
  [['음식 안내가 먼저', '제품은 그다음 정보로'], ['제안 톤', '"이런 제품도 있어요", 순위·가격·판매처 없음'], ['상한 확인', '여러 제품을 함께 보면 하루 양을 합쳐 확인'], ['전문가 상담', '임신·질환·복용약이 있으면 먼저 상의']]
    .forEach(([h, b], i) => { const y = 2.05 + i * 1.18; box(s, 8.5, y, 4.2, 1.02, K.tealXL); txt(s, h, { x: 8.75, y: y + 0.1, w: 3.8, h: 0.4, fontSize: 16, bold: true, color: K.deep }); txt(s, b, { x: 8.75, y: y + 0.5, w: 3.8, h: 0.45, fontSize: 12, color: K.ink2 }); });
}

// ════════════════════ 6. 맺는 장 ════════════════════
{
  const s = slide('CONTENT', '맺는 장', '핵심 인사이트', '분석으로 세 가지를 알게 되었습니다', 60,
    n(60, '정리하면 세 가지입니다. 첫째, 영양 부족은 누구나의 문제입니다. 8개 영양소는 유형과 상관없이 절반 이상이 부족하니, 개인화보다 모두에게 주는 식품 안내가 효율적입니다. 둘째, 유형 차이는 끼니에서 나옵니다. 세 끼를 챙기는 유형은 덜 부족하고 거르는 유형은 더 부족하며, 차이의 82%가 식사량과 식품 선택으로 설명됩니다. 운동을 열심히 해도 끼니가 불규칙하면 철·아연이 더 부족했습니다. 셋째, 유형은 입구이고 정밀한 판단은 개인 단계의 몫입니다.'));
  const I = [['1', '영양 부족은\n"누구나"의 문제입니다', '8개 영양소는 유형과 상관없이\n성인 절반 이상이 부족합니다\n→ 모두에게 주는 식품 안내가\n효율적입니다'], ['2', '유형 차이는\n"끼니"에서 나옵니다', '세 끼를 챙기는 A3·O2·N3는 덜,\n거르는 N2·O1·S1은 더 부족합니다\n차이의 82%가 식사량·식품 선택으로\n설명됩니다 (인과는 아님)'], ['3', '유형은 입구,\n정밀한 판단은 개인 단계', 'AUC 0.604 → 0.631 → 0.659\n같은 유형 안에서도 사람마다\n다릅니다 → "10명 중 N명"으로\n비율로 말합니다']];
  I.forEach(([k, h, b], i) => {
    const x = 0.6 + i * 4.1; box(s, x, 2.1, 3.8, 4.4, i === 1 ? K.tealL : K.tealXL);
    txt(s, k, { x: x + 0.3, y: 2.3, w: 1, h: 0.8, fontSize: 40, bold: true, color: K.teal });
    txt(s, h, { x: x + 0.3, y: 3.2, w: 3.3, h: 1.0, fontSize: 19, bold: true, color: K.deep });
    txt(s, b, { x: x + 0.3, y: 4.35, w: 3.3, h: 1.9, fontSize: 14, color: K.ink2 });
  });
}
{
  const s = slide('CONTENT', '맺는 장', '비즈니스 제언', '그래서 서비스는 이렇게 쓰자고 제안합니다', 60,
    n(60, '이 결과로 네 가지를 제안합니다. 첫 화면은 유형과 부족할 수 있는 영양소까지만 보여 주고, 영양제는 개인 단계에서 안내해 처방처럼 보이지 않게 합니다. 식사량 관련 영양소가 있는 유형에는 영양제보다 끼니 안내를 먼저 합니다. 2024년에도 1.24배로 확인된 항목입니다. 120개 조합 중 40개는 "특히 더 부족한 건 없어요"가 나오니, 칭찬 피드백으로 재방문을 유도합니다. 공통 8개는 햇빛, 채소·과일, 유제품 같은 콘텐츠를 한 번 만들어 모두에게 씁니다.'));
  const R = [['첫 화면은 유형과 부족 영양소까지', '영양제는 2단계 개인 결과에서', '처방처럼 보이지 않고 신뢰를 얻음'], ['식사량 관련 유형엔 끼니 안내 먼저', '"식사량 점검" 항목 2024년 1.24배', '불필요한 영양제 구매를 줄임'], ['"특히 없음"은 칭찬 피드백으로', '120개 조합 중 40개', '좋은 습관 강화, 재방문 유도'], ['공통 8개는 음식 콘텐츠 한 번에', '유형 간 차이 0.95~1.05배', '모든 사용자에게 같은 콘텐츠 재사용']];
  const hdr = ['제언', '근거', '기대 효과'];
  s.addTable([hdr.map((h) => ({ text: h, options: { bold: true, color: K.white, fill: { color: K.teal } } })), ...R.map((r) => r.map((c, j) => ({ text: c, options: j === 0 ? { bold: true, color: K.deep } : {} })))],
    { x: 0.6, y: 2.1, w: 12.1, colW: [4.6, 3.8, 3.7], fontFace: FONT, fontSize: 15, color: K.ink, border: { type: 'solid', pt: 0.75, color: K.line }, rowH: [0.55, 0.95, 0.95, 0.95, 0.95], valign: 'middle', margin: [4, 10, 4, 10], fill: { color: K.white } });
}
{
  const s = slide('CONTENT', '맺는 장', '한계와 넘는 방법', '한계는 숨기지 않고, 이렇게 넘으려고 합니다', 75,
    n(75, '한계도 분명합니다. 정답이 하루 식사 기록이라 평소 섭취와 다를 수 있습니다. 그래서 "진단이 아님"을 밝히고, 사용자 응답이 쌓이면 다시 검증할 계획입니다. 예측력이 중간 수준이라 경향 안내로만 쓰고, 정밀한 판단은 개인 단계로 넘깁니다. 표본을 바꾸면 유형 경계가 조금 움직여서, 웹은 고정 모델로 같은 응답이면 같은 유형이 나오게 했습니다. 마지막으로 인과가 아니므로 "이 습관 때문에 부족하다" 대신 "이 유형에서 많아요" 수준으로만 말합니다.'));
  const R = [['정답이 하루 식사 기록(24시간 회상)', '평소 섭취와 다를 수 있음', '"진단 아님" 표시, 사용자 응답 누적 후 재검증'], ['예측력 중간 (AUC 0.56~0.70)', '개인 부족 여부를 정확히 가르지 못함', '경향 안내로만, 정밀 판단은 2단계 개인 결과'], ['표본을 바꾸면 경계가 움직임 (재학습 ARI 0.68~0.70)', '경계 근처 사람의 유형이 바뀔 수 있음', '웹은 고정 모델 → 같은 응답이면 같은 유형'], ['인과 관계가 아님', '"이 습관 때문에"라고 말할 수 없음', '"이 유형에서 많아요" 수준의 표현만']];
  s.addTable([['한계', '영향', '넘는 방법'].map((h) => ({ text: h, options: { bold: true, color: K.white, fill: { color: K.teal } } })), ...R.map((r) => r.map((c, j) => ({ text: c, options: j === 2 ? { bold: true, color: K.teal, fill: { color: K.tealXL } } : (j === 0 ? { bold: true, color: K.deep } : {}) })))],
    { x: 0.6, y: 2.1, w: 12.1, colW: [4.4, 3.7, 4.0], fontFace: FONT, fontSize: 15, color: K.ink, border: { type: 'solid', pt: 0.75, color: K.line }, rowH: [0.55, 0.95, 0.95, 0.95, 0.95], valign: 'middle', margin: [4, 10, 4, 10] });
}
{
  const s = slide('DARK', '맺는 장', null, null, 40,
    n(40, '정리하겠습니다. 저희는 생활습관 몇 문항으로, 나와 비슷한 사람들이 무엇이 부족하기 쉬운지를 먼저 알려 주는 서비스를 만들었습니다. 유형은 이야기를 시작하는 입구이고, 더 알고 싶은 분은 개인 결과로 이어집니다. 들어 주셔서 감사합니다. 질문 받겠습니다.'));
  T[T.length - 1][1] = '마무리 · 질의응답';
  txt(s, '한 문장으로 정리하면', { x: 0.8, y: 1.4, w: 8, h: 0.4, fontSize: 15, bold: true, color: K.tealM });
  txt(s, '생활습관 몇 문항으로,\n나와 비슷한 사람들의\n부족 영양소를 먼저 알려 줍니다', { x: 0.8, y: 1.9, w: 8, h: 2.6, fontSize: 36, bold: true, color: K.white });
  txt(s, '감사합니다 · 질의응답', { x: 0.8, y: 4.9, w: 7, h: 0.55, fontSize: 22, bold: true, color: K.tealL });
  txt(s, '2조 머신2러닝  ·  양대천 · 박준혁 · 전유환 · 최지연 · 황재준  ·  matchum.vercel.app', { x: 0.8, y: 5.6, w: 9, h: 0.4, fontSize: 13, color: K.tealM });
  s.addShape(pres.shapes.OVAL, { x: 9.1, y: 1.6, w: 3.6, h: 3.6, fill: { color: K.teal }, line: { color: K.teal } });
  img(s, 'mascot/start.png', 9.3, 1.8, 3.2, 3.2);
}

// ════════════════════ 부록 (질의응답 대비) ════════════════════
const QA = [
  ['군집이 그냥 몇 문항으로 거르는 필터 아닌가요?', '질문 4개짜리 결정나무로는 12개 유형의 66%만 다시 만들어집니다 (2개 33%, 6개 79%)', ['여러 습관을 함께 봐야 나오는 구분입니다', '다만 영양 예측력은 사람이 정한 규칙(중앙값 16개 그룹)과 같아(AUC 0.630 vs 0.632), 유형은 "설명과 안내" 용도로 씁니다']],
  ['안정성(ARI)이 0.68~0.70인데 왜 12개 유형을 썼나요?', '표본 40%로 20번 다시 학습했을 때의 값이고, 웹은 고정 모델이라 같은 응답이면 항상 같은 유형입니다', ['7개 유형 안은 0.911로 더 안정적이지만 흡연·음주가 유형을 주도하고 성별 쏠림이 두 배였습니다', '영양 설명력은 두 안이 같아(0.097 vs 0.096), 안내하려는 운동·좌식·스트레스를 담는 12개 안을 택했습니다', '재학습마다 영양 안내가 달라지는 사람은 약 8%입니다']],
  ['AUC 0.63이면 낮은 것 아닌가요?', '네, 중간 수준이라 "진단"이 아니라 "같은 유형 사람들의 경향"으로만 보여 줍니다', ['예측 확률과 실제 비율 차이가 최대 1.7%p라 "10명 중 N명" 표현은 정확합니다', '개인 응답을 쓰면 0.659까지 오르고, 정밀한 판단은 2단계에서 합니다', '목록 맞히기 정확도(F1)는 공통 8개 고정 0.777, 유형 모델 0.789로 비슷합니다 → 유형의 가치는 "같은 성별·나이보다 몇 배"에 있습니다']],
  ['정답(섭취량) 정보가 모델에 새지 않았나요?', '섭취량·에너지는 입력에 넣지 않았고, 연도로 나눠 2024년 자료는 학습에 쓰지 않았습니다', ['입력은 유형·성별·연령대뿐입니다', '하이퍼파라미터도 2022–23년 안의 5겹 교차검증으로만 골랐습니다', '1.2배·0.3 같은 표시 기준은 결과를 보기 전에 팀 문서로 정했습니다']],
  ['평소 식사 5문항 모델의 AUC 0.877은 너무 높지 않나요?', '같은 조사의 식품섭취빈도 문항으로 학습·평가해 높게 나올 수 있어, 정답을 어떻게 만들었는지 팀에서 확인하고 있습니다', ['2012–15년 학습 → 2016년 독립 평가, 19–64세에서만 검증했습니다', '그래서 생활습관 신호와 평균하지 않고 별도 신호로 나란히 보여 줍니다']],
  ['비타민D는 95.8%가 부족한데 맞나요?', '충분섭취량(AI) 기준이고, 음식으로 먹은 양만 계산해 햇빛으로 만드는 양이 빠져 있습니다', ['그래서 "부족 위험"이 아니라 "참고"로 구분합니다', '유형 차이도 없어(0.98~1.01배) 공통 안내로만 씁니다']],
  ['영양제 정보는 처방처럼 보이지 않나요?', '1단계에서는 영양제를 보여 주지 않고, 2단계에서도 음식 안내 다음에 "이런 제품도 있어요"로만 보여 줍니다', ['순위·가격·판매처·질병 효과 문구가 없습니다 (식품표시광고법)', '임신·질환·복용약은 묻지 않고 전문가 상담을 안내합니다', '여러 제품의 하루 양을 합쳐 상한을 넘지 않는지 확인합니다']],
  ['하루 식사 기록으로 부족을 판단해도 되나요?', '하루 기록은 날마다 흔들려 부족 비율이 평소보다 크게 나올 수 있어, 화면에 "진단 아님"을 밝힙니다', ['평소처럼 먹은 날만 쓰거나 에너지가 극단적인 날을 빼도 안내 결과는 98.7% 이상 같았습니다', '사용자 응답이 쌓이면 다시 검증할 계획입니다']],
];
{
  const s = slide('APPX', '부록', '부록 · 질의응답 대비', '예상 질문 바로 가기', 0, '질의응답 때 해당 장 번호로 바로 이동합니다. 질문을 받으면 먼저 질문을 한 번 정리해 청중에게 들려준 뒤 답합니다.');
  QA.forEach(([q], i) => { const y = 2.0 + i * 0.6; box(s, 0.6, y, 12.1, 0.5, i % 2 ? K.white : K.tealXL); txt(s, `Q${i + 1}`, { x: 0.8, y, w: 0.8, h: 0.5, fontSize: 15, bold: true, color: K.teal, valign: 'middle' }); txt(s, q, { x: 1.6, y, w: 9.5, h: 0.5, fontSize: 15, valign: 'middle' }); txt(s, `→ ${T.length + 2 + i}쪽`, { x: 11.2, y, w: 1.4, h: 0.5, fontSize: 13, color: K.ink2, valign: 'middle', align: 'right' }); });
}
QA.forEach(([q, a, pts], i) => {
  const s = slide('APPX', '부록', `Q${i + 1}`, q, 0, `질문을 한 번 정리해 들려준 뒤 답합니다. 핵심 답: ${a}`);
  box(s, 0.6, 2.05, 12.1, 1.3, K.teal);
  txt(s, a, { x: 0.9, y: 2.05, w: 11.5, h: 1.3, fontSize: 18, bold: true, color: K.white, valign: 'middle' });
  bullets(s, pts, { x: 0.9, y: 3.7, w: 11.5, h: 2.9, fontSize: 16 });
});
{
  const s = slide('APPX', '부록', '부록 · 자료', '12개 유형의 생활습관 프로필', 0, '유형 이름에 쓴 특징 33개가 모두 실제 평균과 일치(|z| ≥ 0.3)합니다. 오른쪽 2열(흡연·음주)은 군집에 쓰지 않은 참고 변수입니다.');
  img(s, 'f04_유형프로필.png', 0.6, 1.95, 12.1, 4.95);
}
{
  const s = slide('APPX', '부록', '부록 · 자료', '유형별 하루 단백질·철 섭취량 (성별·연령 보정 전)', 0, '보정 전이라 남성 비율이 높은 A3·O3가 높게, 65세 이상이 많은 N1이 낮게 나옵니다. 보정 후 비교는 유형별 부족 패턴 장의 배수 그림을 봅니다.');
  img(s, 'f09_유형별_섭취량.png', 0.6, 1.95, 12.1, 4.95);
}

// ── 저장 ──
pres.writeFile({ fileName: OUT }).then(() => {
  let acc = 0;
  const lines = T.filter((t) => t[2] > 0).map(([i, tt, sec]) => { acc += sec; return `${String(i).padStart(2)}  ${mm(sec).padStart(7)}  누적 ${mm(acc).padStart(7)}  ${tt}`; });
  fs.writeFileSync(path.join(__dirname, '발표_시간표.txt'), lines.join('\n') + `\n\n본문 합계 ${mm(acc)}\n`, 'utf8');
  console.log('저장:', OUT, '| 본문 합계', mm(acc), '| 전체 장 수', pres.slides.length);
});
