// 건강기능식품: 재준님 모델의 '살펴볼 영양소' → 준혁님 제품 목록(data/supplementCatalog.json)
//   웹은 고르기·보여 주기만 한다. 제품을 더하거나 빼지 않고, 같은 영양소·대상 안의 순서도 그대로 쓴다
//   대상(일반·남성·여성·시니어)은 섞지 않고 칸을 나눈다 (재준님 인계: 서로 다른 대상의 순서는 같은 척도가 아님)
import { NUTRIENT_GUIDE } from '../data/nutrientGuide.js'
import { FOOD_ONLY, PRODUCT_NUTRIENTS, SENIOR_AGE } from '../data/supplementInfo.js'

const GUIDE = Object.fromEntries(NUTRIENT_GUIDE.map((n) => [n.key, n]))

// 내 성별·나이에 맞는 대상 칸 (내게 맞춘 칸 먼저, '일반'은 마지막)
export function targetsFor(sex, age) {
  return [sex === 1 ? '남성' : '여성', ...(age >= SENIOR_AGE ? ['시니어'] : []), '일반']
}

// watchKeys: 재준님 모델의 '살펴볼 영양소' 키 (순서대로)
// → { nutrients: 제품 목록이 있는 영양소 [{ key, label, icon, from: 해당 모델 영양소 키 }], foodOnly: 음식으로만 챙길 영양소 이름 }
//   비타민 B1·B2는 비타민 B군 하나로. 나트륨·비타민 A는 제품 목록이 없어 빠진다
export function supplementTargets(watchKeys) {
  const nutrients = PRODUCT_NUTRIENTS.filter((n) => n.from.some((k) => watchKeys.includes(k))).map((n) => ({
    key: n.key,
    label: n.label,
    icon: n.icon,
    from: n.from.filter((k) => watchKeys.includes(k)),
  }))
  return { nutrients, foodOnly: FOOD_ONLY.filter((k) => watchKeys.includes(k)).map((k) => GUIDE[k].label) }
}

// 제품 한 줄: 목록 줄 [신고번호, 구분, 1일 함량, 기준치 %] + 제품 정보
const productOf = (catalog, [id, type, amount, dvPct]) => ({ id, type, amount, dvPct, ...catalog.products[id] })

// 영양소 하나의 제품을 대상 칸별로. forms가 있으면 그 제형만 (순서는 그대로)
//   → [{ target, total: 거르기 전 개수, items }] (제품이 없는 대상은 빠진다)
export function productSections(catalog, key, targets, forms = []) {
  return targets
    .map((target) => {
      const rows = catalog.lists[key]?.[target] ?? []
      const items = rows.map((row) => productOf(catalog, row)).filter((p) => !forms.length || forms.includes(p.form))
      return { target, total: rows.length, items }
    })
    .filter((s) => s.total > 0)
}

// 영양소 하나에서 내 대상의 제품 수 (같은 제품이 여러 대상 칸에 있으면 한 번만)
export function productCount(catalog, key, targets) {
  return new Set(targets.flatMap((t) => (catalog.lists[key]?.[t] ?? []).map(([id]) => id))).size
}

// 고를 수 있는 제형과 개수 (많은 순)
export function formsOf(catalog, key, targets) {
  const count = {}
  for (const t of targets) for (const [id] of catalog.lists[key]?.[t] ?? []) count[catalog.products[id].form] = (count[catalog.products[id].form] ?? 0) + 1
  return Object.entries(count)
    .sort((a, b) => b[1] - a[1])
    .map(([form, n]) => ({ form, count: n }))
}

// 제품 정보 원문 (기능성·섭취 시 주의사항은 같은 문구를 한 번만 저장해 번호로 가리킨다)
export const productTexts = (catalog, p) => ({ function: catalog.texts[p.function], caution: catalog.texts[p.caution] })

// 고른 제품을 함께 먹을 때 하루 합계와 상한섭취량 (2025 KDRI 성인). 하루 함량을 아는 성분만 더한다
//   → [{ key, label, unit, total, ul, over, count: 그 성분이 든 고른 제품 수 }]
export function dailyTotals(catalog, ids, sex) {
  return catalog.daily
    .map((d) => {
      const values = ids.map((id) => catalog.products[id]?.daily[d.key]).filter((v) => v !== undefined)
      const total = Math.round(values.reduce((s, v) => s + v, 0) * 100) / 100
      const ul = sex === 1 && d.ulMale ? d.ulMale : d.ul
      return { key: d.key, label: d.label, unit: d.unit, total, ul, over: ul != null && total > ul, count: values.length }
    })
    .filter((x) => x.count > 0)
}
