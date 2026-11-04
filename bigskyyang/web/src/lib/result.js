// 설문 응답 → 결과 화면에 보여 줄 값 (화면 코드와 분리해 테스트한다)
//
// 서비스 흐름 (두 단계)
//   1단계 유형 결과: 유형·비율, 생활습관 신호등(유형을 만든 영역)과 이번 주 해볼 것, 부족할 수 있는 영양소, 짝꿍 유형
//   2단계 개인 결과: 흡연·음주 신호, 개인 영양 위험 예측(재준님 모델 v1.4), 식습관에 맞춘 음식,
//                    건강기능식품 정보(준혁님 제품 분류, 참고용)
//   진단·처방처럼 보일 수 있는 안내(우울 점수, 질환별 식사 조언)는 하지 않는다
import nutrientCells from '../data/nutrientCells.json'
import supplementProducts from '../data/supplementProducts.json'
import { NUTRIENT_GUIDE } from '../data/nutrientGuide.js'
import { BALANCED_FOODS, pickTips } from '../data/tips.js'
import { LEAF_TYPES, MAIN_TYPES } from '../data/types.js'
import { MAIN_CODES, classify, mainProfile, toFeatures, typeOf } from './classify.js'
import { encode } from './encode.js'
import { ageGroup, typeNutrients } from './nutrition.js'
import { habitualFeatures, lifestyleFeatures, predictNutrition } from './nutritionRisk.js'
import { PERSONAL_AXES, TYPE_AXES, bestPartner, groupScores, hashtags, scores } from './profile.js'
import { supplementInfo } from './supplements.js'

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

// 개인 영양 위험 화면에 쓰는 영양소 이름·음식 (나트륨은 '많이 먹을 위험')
const GUIDE = {
  ...Object.fromEntries(NUTRIENT_GUIDE.map((n) => [n.key, { label: n.label, icon: n.icon, guide: `이런 음식에 많아요: ${n.foods.join(' · ')}` }])),
  sodium_excess: { label: '나트륨 (많이 먹을 위험)', icon: '🧂', guide: '국물·소스·가공식품의 영양표시를 살펴보세요.' },
}
const RANK = { Low: 0, Mid: 1, High: 2 }
const MAX_WATCH = 5

// 재준님 두 모델 결과 → 화면용 (확률은 평균하지 않는다)
//   살펴볼 영양소(watch): 평소 식사 기준 '높은 편', 또는 생활습관 기준 '높은 편'이면서 평소 식사 기준이 '낮은 편'이 아닌 것
//     (두 기준이 엇갈리면 더 정확한 평소 식사 기준을 따른다). 많으면 MAX_WATCH개까지, 나머지는 rest로 접는다
function personalNutrition(pred) {
  const rows = Object.keys(GUIDE)
    .filter((key) => pred.lifestyle[key])
    .map((key) => {
      const lifestyle = pred.lifestyle[key].band
      const habitual = pred.habitual?.[key]?.band ?? null
      const bands = [lifestyle, habitual].filter(Boolean)
      const high = habitual === 'High' || (lifestyle === 'High' && habitual !== 'Low')
      return { key, ...GUIDE[key], lifestyle, habitual, high, mixed: bands.includes('High') && bands.includes('Low') }
    })
  // 둘 다 높은 편 → 평소 식사 기준 높은 편 → 생활습관 기준 높은 편
  const score = (n) => (n.habitual === 'High' ? 2 : 0) + (n.lifestyle === 'High' ? 1 : 0) + (n.habitual === 'High' && n.lifestyle === 'High' ? 4 : 0)
  return {
    version: pred.version,
    habitualAvailable: pred.habitual !== null,
    watch: rows.filter((n) => n.high).sort((a, b) => score(b) - score(a)).slice(0, MAX_WATCH),
    rest: [
      ...rows.filter((n) => n.high).sort((a, b) => score(b) - score(a)).slice(MAX_WATCH),
      ...rows.filter((n) => !n.high).sort((a, b) => RANK[b.lifestyle] - RANK[a.lifestyle]),
    ],
  }
}

// 건강기능식품 정보를 찾아볼 영양소
//   개인 예측이 있으면: 부족 위험 '높은 편' 영양소 + 개인 모델이 예측하지 않는 영양소(비타민 D·E)는 유형 결과의 '내 유형에서 살펴볼 것'
//   아직 없으면: 유형 결과의 부족할 수 있는 영양소 (내 유형 것 → 공통)
function supplementKeysOf(leaf, extras, nutrition, modeled) {
  const n = typeNutrients(nutrientCells, leaf, extras.sex, extras.age)
  if (!nutrition) return n ? [...n.picks, ...n.common].map((x) => x.key) : []
  const typeOnly = (n?.picks ?? []).map((x) => x.key).filter((k) => !modeled.includes(k))
  return [...nutrition.watch.map((x) => x.key), ...typeOnly]
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
    // 개인 영양 위험 (재준님 생활습관·평소 식사 모델)
    nutrition,
    supplements: supplementInfo(
      supplementProducts,
      supplementKeysOf(leaf, extras, nutrition, models ? Object.keys(models.lifestyle.models) : []),
      extras,
    ),
  }
}
