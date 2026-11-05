// 설문 응답 → 결과 화면에 보여 줄 값 (화면 코드와 분리해 테스트한다)
//
// 서비스 흐름 (두 단계)
//   1단계 유형 결과: 유형·비율, 생활습관 신호등(유형을 만든 영역)과 이번 주 해볼 것, 부족할 수 있는 영양소, 짝꿍 유형 2개
//   2단계 개인 결과: 흡연·음주 신호, 개인 영양 위험 예측(재준님 모델 v1.4), 식습관에 맞춘 음식,
//                    건강기능식품 정보(재준님 결과 중 준혁님 제품 분류로 넘기는 영양소. 제품 표시는 팀 합의 후)
//   진단·처방처럼 보일 수 있는 안내(우울 점수, 질환별 식사 조언)는 하지 않는다
import nutrientCells from '../data/nutrientCells.json'
import { NUTRIENT_GUIDE } from '../data/nutrientGuide.js'
import { FOOD_ONLY, PRODUCT_NUTRIENTS } from '../data/supplementInfo.js'
import { BALANCED_FOODS, pickTips } from '../data/tips.js'
import { LEAF_TYPES, MAIN_TYPES } from '../data/types.js'
import { MAIN_CODES, classify, model, toFeatures, typeOf } from './classify.js'
import { encode } from './encode.js'
import { ageGroup, typeNutrients } from './nutrition.js'
import { habitualFeatures, lifestyleFeatures, predictNutrition } from './nutritionRisk.js'
import { PERSONAL_AXES, TYPE_AXES, groupScores, hashtags, partnerTypes, scores } from './profile.js'
import { supplementTargets } from './supplements.js'

const MAX_MISSIONS = 3
const MAX_FOODS = 6
const AGE_LABELS = { '19-29': '19~29세', '30-49': '30~49세', '50-64': '50~64세', '65-74': '65~74세', '75+': '75세 이상' }

// 세부 유형 12개 평균의 신호등 점수 (짝꿍 유형 고르기)
const LEAF_SCORES = Object.fromEntries(model.types.map((t) => [t.id, groupScores(toFeatures(t.profile), TYPE_AXES)]))
const partnerOf = ({ id, axes }) => ({ id, name: LEAF_TYPES[id].name, summary: LEAF_TYPES[id].summary, main: MAIN_TYPES[id[0]], axes })

const missionsOf = (tips) => tips.flatMap((t) => (t.mission ? [t.mission] : [])).slice(0, MAX_MISSIONS)

// 전체 유형 보기 (/types): 대분류마다 세부 유형 3개 (이름·설명·해시태그·비율·유형 평균의 생활습관 신호등)
export function allTypes() {
  return MAIN_CODES.map((code) => {
    const types = model.types
      .filter((t) => t.id[0] === code)
      .sort((a, b) => a.id.localeCompare(b.id))
      .map((t) => ({
        id: t.id,
        name: LEAF_TYPES[t.id].name,
        summary: LEAF_TYPES[t.id].summary,
        main: MAIN_TYPES[code],
        tags: hashtags(t),
        sharePct: t.share * 100,
        habits: TYPE_AXES.map((axis, i) => ({ ...axis, score: LEAF_SCORES[t.id][i] })),
      }))
    return { code, ...MAIN_TYPES[code], sharePct: types.reduce((s, t) => s + t.sharePct, 0), types }
  })
}

// 1단계 응답(+ 있으면 2단계)으로 유형 결과
export function buildTypeResult(answers) {
  const { features, extras } = encode(answers)
  // main: 대분류 코드 (N·A·S·O), leaf: 세부 유형 ID (N1~O3). 이름(types.js)·영양소 결과표도 이 ID로 찾는다
  const { main, leaf } = classify(features)
  const mainType = MAIN_TYPES[main]
  const leafType = LEAF_TYPES[leaf]
  const type = typeOf(leaf)
  const myScores = scores(features, TYPE_AXES)

  const { fill, together } = partnerTypes(myScores, leaf, LEAF_SCORES, TYPE_AXES)

  return {
    leafId: leaf,
    mainType,
    name: leafType.name,
    summary: leafType.summary,
    tags: hashtags(type),
    sharePct: type.share * 100,
    habits: TYPE_AXES.map((axis, i) => ({ ...axis, score: myScores[i] })),
    missions: missionsOf(pickTips(features, extras)),
    // 부족할 수 있는 영양소: 유환님 (나)안 결과 (유형 × 성별 × 연령대)
    nutrients: typeNutrients(nutrientCells, leaf, extras.sex, extras.age),
    sexLabel: extras.sex === 1 ? '남성' : '여성',
    ageLabel: AGE_LABELS[ageGroup(extras.age)],
    // 같이 다니면 좋은 유형: 내 약점을 채워 주는 유형, 나와 같은 약점이 있어 같이 바꿔 보기 좋은 유형
    partners: { fill: partnerOf(fill), together: partnerOf(together) },
  }
}

// 개인 영양 위험 화면에 쓰는 영양소 이름·음식 (나트륨은 '많이 먹을 위험')
//   supplement: 'product' 건강기능식품 정보가 있는 영양소 (준혁님 제품 분류), 'food' 음식으로만 챙기는 영양소, null 해당 없음
const PRODUCT_KEYS = PRODUCT_NUTRIENTS.flatMap((n) => n.from)
const GUIDE = {
  ...Object.fromEntries(
    NUTRIENT_GUIDE.map((n) => [
      n.key,
      {
        label: n.label,
        icon: n.icon,
        role: n.role,
        foods: n.foods,
        supplement: PRODUCT_KEYS.includes(n.key) ? 'product' : FOOD_ONLY.includes(n.key) ? 'food' : null,
      },
    ]),
  ),
  sodium_excess: {
    label: '나트륨',
    excess: true,
    icon: '🧂',
    role: '국물·소스·가공식품에 많이 들어 있어요.',
    tip: '국물은 덜 먹고, 가공식품은 영양표시의 나트륨 양을 살펴보세요.',
    supplement: null,
  },
}
const RANK = { Low: 0, Mid: 1, High: 2 }
const MAX_WATCH = 5

// 재준님 두 모델 결과 → 화면용 (Jaejun/nutrition_final_feedback_applied/config/display_policy.json)
//   대표 등급(band): 평소 식사 기준이 있으면 그것, 없으면 생활습관 기준. 확률은 평균하지 않고 화면에 숫자도 쓰지 않는다
//   살펴볼 영양소(watch): 대표 등급이 '높은 편'인 것, 최대 MAX_WATCH개 (고르는 규칙은 웹이 정한다). 나머지는 rest로 접는다
function personalNutrition(pred) {
  const rows = Object.keys(GUIDE)
    .filter((key) => pred.lifestyle[key])
    .map((key) => {
      const lifestyle = pred.lifestyle[key].band
      const habitual = pred.habitual?.[key]?.band ?? null
      const band = habitual ?? lifestyle
      return { key, ...GUIDE[key], band, source: habitual ? 'habitual' : 'lifestyle', lifestyle, habitual, differ: habitual !== null && habitual !== lifestyle }
    })
  // 같은 '높은 편'이면 두 기준이 모두 높은 편인 것 → 평소 식사 기준 → 생활습관 기준 순 (영양소끼리 확률은 비교하지 않는다)
  const score = (n) => (n.habitual === 'High') * 2 + (n.lifestyle === 'High')
  const high = rows.filter((n) => n.band === 'High').sort((a, b) => score(b) - score(a))
  return {
    version: pred.version,
    habitualAvailable: pred.habitual !== null,
    watch: high.slice(0, MAX_WATCH),
    rest: [...high.slice(MAX_WATCH), ...rows.filter((n) => n.band !== 'High').sort((a, b) => RANK[b.band] - RANK[a.band])],
  }
}

// 1·2단계 응답으로 개인 결과. models: data/nutritionModels.json (화면에서 나중에 불러온다, 없으면 영양 위험은 null)
export function buildPersonalResult(answers, models = null) {
  const { features, extras } = encode(answers)
  const { leaf } = classify(features)
  const tips = pickTips(features, extras, true)
  const personalScores = scores(features, PERSONAL_AXES)
  const nutrition = models
    ? personalNutrition(predictNutrition(models, lifestyleFeatures(answers, features), habitualFeatures(extras)))
    : null

  // 음식은 이름이 겹치지 않게 모은다
  const foods = []
  for (const f of tips.flatMap((t) => t.foods ?? [])) {
    if (!foods.some((x) => x.label === f.label)) foods.push(f)
  }

  return {
    leafId: leaf,
    typeName: LEAF_TYPES[leaf].name,
    habits: PERSONAL_AXES.map((axis, i) => ({ ...axis, score: personalScores[i] })),
    missions: missionsOf(tips),
    foods: (foods.length ? foods : BALANCED_FOODS).slice(0, MAX_FOODS),
    ffqAsked: extras.ffq !== null,
    sex: extras.sex,
    age: extras.age,
    // 개인 영양 위험 (재준님 생활습관·평소 식사 모델)
    nutrition,
    // 건강기능식품 정보: 재준님 모델의 '살펴볼 영양소' 중 준혁님 제품 분류에 있는 영양소만 (모델을 불러오기 전에는 null)
    supplements: nutrition ? supplementTargets(nutrition.watch.map((n) => n.key)) : null,
  }
}
