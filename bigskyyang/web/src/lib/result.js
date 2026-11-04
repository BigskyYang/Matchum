// 설문 응답 → 결과 화면에 보여 줄 값 (화면 코드와 분리해 테스트한다)
//
// 서비스 흐름 (두 단계)
//   1단계 유형 결과: 유형·비율, 생활습관 신호등(유형을 만든 영역)과 이번 주 해볼 것, 부족할 수 있는 영양소, 짝꿍 유형
//   2단계 개인 결과: 흡연·음주 신호, 식습관에 맞춘 음식, 마음·대사 건강. 개인 영양 위험 예측(재준님 모델)과
//                    건강기능식품 정보(유환님·준혁님)는 연결 준비 중
import nutrientCells from '../data/nutrientCells.json'
import { BALANCED_FOODS, pickTips } from '../data/tips.js'
import { LEAF_TYPES, MAIN_TYPES } from '../data/types.js'
import { MAIN_CODES, classify, mainProfile, toFeatures, typeOf } from './classify.js'
import { encode } from './encode.js'
import { ageGroup, typeNutrients } from './nutrition.js'
import { PERSONAL_AXES, TYPE_AXES, bestPartner, groupScores, hashtags, scores } from './profile.js'

const MAX_MISSIONS = 3
const MAX_FOODS = 6
const AGE_LABELS = { '19-29': '19~29세', '30-49': '30~49세', '50-64': '50~64세', '65-74': '65~74세', '75+': '75세 이상' }
const IRREGULAR_MISSION = { icon: '🌙', title: '잠·식사 시간 맞추기', detail: '근무나 일정이 바뀌어도 잠드는 시간과 식사 시간을 최대한 비슷하게!' }

const missionsOf = (tips, first = []) => [...first, ...tips.flatMap((t) => (t.mission ? [t.mission] : []))].slice(0, MAX_MISSIONS)

// 1단계 응답(+ 있으면 2단계)으로 유형 결과
export function buildTypeResult(answers) {
  const { features, extras } = encode(answers)
  // main: 대분류 코드 (N·A·S·O), leaf: 세부 유형 ID (N1~O3). 이름(types.js)·영양소 결과표도 이 ID로 찾는다
  const { main, leaf } = classify(features)
  const mainType = MAIN_TYPES[main]
  const leafType = LEAF_TYPES[leaf]
  const type = typeOf(leaf)
  const myScores = scores(features, TYPE_AXES)

  const mainScores = Object.fromEntries(MAIN_CODES.map((code) => [code, groupScores(toFeatures(mainProfile(code)), TYPE_AXES)]))
  const partner = bestPartner(myScores, main, mainScores, TYPE_AXES)

  return {
    leafId: leaf,
    mainType,
    name: leafType.name,
    summary: leafType.summary,
    tags: hashtags(type),
    sharePct: type.share * 100,
    habits: TYPE_AXES.map((axis, i) => ({ ...axis, score: myScores[i] })),
    missions: missionsOf(pickTips(features, extras), extras.sleepIrregular ? [IRREGULAR_MISSION] : []),
    // 부족할 수 있는 영양소: 유환님 (나)안 결과 (유형 × 성별 × 연령대)
    nutrients: typeNutrients(nutrientCells, leaf, extras.sex, extras.age),
    nutrientsEmptyText: nutrientCells.empty_line2_text,
    sexLabel: extras.sex === 1 ? '남성' : '여성',
    ageLabel: AGE_LABELS[ageGroup(extras.age)],
    partner: { type: MAIN_TYPES[partner.label], helps: partner.helps },
  }
}

// 1·2단계 응답으로 개인 결과
export function buildPersonalResult(answers) {
  const { features, extras } = encode(answers)
  const { leaf } = classify(features)
  const tips = pickTips(features, extras, true)
  const personalScores = scores(features, PERSONAL_AXES)

  // 음식은 이름이 겹치지 않게 모은다
  const foods = []
  for (const f of tips.flatMap((t) => t.foods ?? [])) {
    if (!foods.some((x) => x.label === f.label)) foods.push(f)
  }
  const { health } = extras

  return {
    leafId: leaf,
    typeName: LEAF_TYPES[leaf].name,
    habits: PERSONAL_AXES.map((axis, i) => ({ ...axis, score: personalScores[i] })),
    missions: missionsOf(tips),
    foods: (foods.length ? foods : BALANCED_FOODS).slice(0, MAX_FOODS),
    // 선택 문항 PHQ-9 (답하지 않았으면 null)
    optional: extras.optional,
    health,
    // 대사질환 진단 → 식생활 주의점 카드
    hasCondition: health.hypertension || health.diabetes || health.dyslipidemia,
    // 건강기능식품 안내 전에 전문가 상담이 필요한 경우 (재준님 안전 규칙: 임신·수유는 제품 안내 중단)
    consult: health.pregnant ? 'pregnant' : health.kidney || health.anticoagulant ? 'caution' : null,
    supplements: extras.supplements,
    ffqAsked: extras.ffq !== null,
  }
}
