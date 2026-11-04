// 개인 결과 '건강기능식품 정보'
//   supplementTargets: 재준님 모델 결과 → 준혁님 제품 분류(11종)로 넘기는 영양소. 지금 화면은 이것만 보여 준다
//   supplementInfo: 그 영양소의 제품 목록(supplementProducts.json)에서 내 성별·나이에 맞는 제품 (제품 표시는 팀 합의 후 다시 연결)
// 어떤 제품을 어떤 순서로 둘지는 준혁님·유환님 분류 결과가 정하고, 웹은 대상만 맞춰 앞에서부터 보여 준다
// 임신·수유·질환·복용약은 묻지 않는다. 화면에서 제품 정보를 펼치기 전에 한 번 확인하고(저장하지 않음), 해당되면 상담을 권한다
import { NUTRIENT_GUIDE } from '../data/nutrientGuide.js'
import { FOOD_ONLY, MAX_PRODUCTS, PRODUCT_NUTRIENTS, SENIOR_AGE } from '../data/supplementInfo.js'

const GUIDE = Object.fromEntries(NUTRIENT_GUIDE.map((n) => [n.key, n]))

// 내 성별·나이에 보여 줄 제품 대상
export function targetsFor(sex, age) {
  return ['일반', sex === 1 ? '남성' : '여성', ...(age >= SENIOR_AGE ? ['시니어'] : [])]
}

// 제품 분류에 있는 영양소만, 부족 영양소 순서대로 (비타민 B1·B2 → 비타민 B군 하나)
const productNutrients = (nutrientKeys) =>
  PRODUCT_NUTRIENTS.filter((n) => n.from.some((k) => nutrientKeys.includes(k)))
    .map((n) => ({ ...n, order: Math.min(...n.from.map((k) => nutrientKeys.indexOf(k)).filter((i) => i >= 0)) }))
    .sort((a, b) => a.order - b.order)
const foodOnlyOf = (nutrientKeys) => FOOD_ONLY.filter((k) => nutrientKeys.includes(k)).map((k) => GUIDE[k].label)

// watchKeys: 재준님 모델의 '살펴볼 영양소'(대표 등급 높은 편) 키 → { nutrients: 제품 분류 영양소, foodOnly: 음식으로만 챙길 영양소 이름 }
//   나트륨(많이 먹을 위험)·비타민 A는 제품 분류에 없어 빠진다
export function supplementTargets(watchKeys) {
  return {
    nutrients: productNutrients(watchKeys).map(({ key, label, icon }) => ({ key, label, icon })),
    foodOnly: foodOnlyOf(watchKeys),
  }
}

const pick = (products, targets, n = MAX_PRODUCTS) => (products ?? []).filter((p) => targets.includes(p.target)).slice(0, n)

// nutrientKeys: 부족할 수 있는 영양소 (결과표 키, 앞일수록 먼저 보여 준다)
// → { ready: 제품 목록이 있는지, nutrients: 제품을 찾아볼 영양소와 제품, foodOnly: 음식으로만 챙길 영양소 이름, multivitamins }
export function supplementInfo(data, nutrientKeys, { sex, age }) {
  const targets = targetsFor(sex, age)
  const nutrients = productNutrients(nutrientKeys).map(({ key, label, icon }) => ({
    key,
    label,
    icon,
    products: pick(data.nutrients?.[key], targets),
  }))

  return {
    ready: Object.values(data.nutrients ?? {}).some((list) => list.length > 0),
    nutrients,
    foodOnly: foodOnlyOf(nutrientKeys),
    multivitamins: pick(data.multivitamin?.balanced, targets),
    source: data.source,
  }
}
