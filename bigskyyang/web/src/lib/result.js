// 설문 응답 → 결과 화면에 보여 줄 값 (화면 코드와 분리해 테스트한다)
//
// 서비스 흐름: 유형 화면은 생활습관과 '부족할 수 있는 영양소'까지만 보여 준다.
// 개인별 영양 위험 예측과 건강기능식품 안내는 개인화('더 알아보기', 재준님 모델·준혁님 제품 자료)에서 한다.
import nutrientCells from '../data/nutrientCells.json'
import { BALANCED_FOODS, pickTips } from '../data/tips.js'
import { LEAF_TYPES, MAIN_TYPES } from '../data/types.js'
import { MAIN_CODES, classify, mainProfile, toFeatures, typeOf } from './classify.js'
import { encode } from './encode.js'
import { ageGroup, typeNutrients } from './nutrition.js'
import { bestPartner, groupScores, hashtags, scores } from './profile.js'

const MAX_MISSIONS = 3
const MAX_FOODS = 6
const AGE_LABELS = { '19-29': '19~29세', '30-49': '30~49세', '50-64': '50~64세', '65-74': '65~74세', '75+': '75세 이상' }
const SHIFT_MISSION = { icon: '🌙', title: '잠·식사 시간 지키기', detail: '근무가 바뀌어도 잠드는 시간과 식사 시간을 최대한 일정하게!' }

export function buildResult(answers) {
  const { features, extras } = encode(answers)
  // main: 대분류 코드 (N·A·S·O), leaf: 세부 유형 ID (N1~O3). 이름(types.js)·영양소 결과표도 이 ID로 찾는다
  const { main, leaf } = classify(features)
  const mainType = MAIN_TYPES[main]
  const leafType = LEAF_TYPES[leaf]
  const type = typeOf(leaf)
  const tips = pickTips(features, extras)
  const myScores = scores(features)

  // 부족할 수 있는 영양소: 유환님 (나)안 결과 (유형 × 성별 × 연령대)
  const nutrients = typeNutrients(nutrientCells, leaf, extras.sex, extras.age)

  // 음식: 내 응답에 맞춘 팁 → '내 유형에서 살펴볼 것' 영양소의 대표 음식. 이름이 겹치지 않게 모은다
  const nutrientFoods = (nutrients?.picks ?? []).map((n) => ({ emoji: n.icon, label: n.foods[0], why: `${n.label} 챙기기` }))
  const foods = []
  for (const f of [...(leafType.foods ?? mainType.foods ?? []), ...tips.flatMap((t) => t.foods ?? []), ...nutrientFoods]) {
    if (!foods.some((x) => x.label === f.label)) foods.push(f)
  }

  const mainScores = Object.fromEntries(MAIN_CODES.map((code) => [code, groupScores(toFeatures(mainProfile(code)))]))
  const partner = bestPartner(myScores, main, mainScores)
  const optional = extras.optional

  return {
    leafId: leaf,
    mainType,
    name: leafType.name,
    summary: leafType.summary,
    tags: hashtags(type),
    sharePct: type.share * 100,
    myScores,
    typeScores: groupScores(toFeatures(type.profile)),
    missions: [...(extras.shiftWork ? [SHIFT_MISSION] : []), ...tips.flatMap((t) => (t.mission ? [t.mission] : []))].slice(
      0,
      MAX_MISSIONS,
    ),
    foods: (foods.length ? foods : BALANCED_FOODS).slice(0, MAX_FOODS),
    nutrients,
    nutrientsEmptyText: nutrientCells.empty_line2_text,
    sexLabel: extras.sex === 1 ? '남성' : '여성',
    ageLabel: AGE_LABELS[ageGroup(extras.age)],
    optional,
    hasCondition: Boolean(optional && (optional.hypertension || optional.diabetes || optional.dyslipidemia)),
    partner: { type: MAIN_TYPES[partner.label], helps: partner.helps },
  }
}
