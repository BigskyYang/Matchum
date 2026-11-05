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

// 내가 먹는 제품 찾기: 제품명·업체명에 검색어가 들어 있는 제품 (띄어쓰기·대소문자 무시, 목록 순서대로 limit개)
//   → { items: [{ id, ...제품 }], total: 찾은 전체 개수 }
const norm = (s) => s.replace(/\s+/g, '').toLowerCase()
export function searchProducts(catalog, query, limit = 20) {
  const q = norm(query)
  if (q.length < 2) return { items: [], total: 0 }
  const found = Object.entries(catalog.products).filter(([, p]) => norm(p.name).includes(q) || norm(p.maker).includes(q))
  return { items: found.slice(0, limit).map(([id, p]) => ({ id, ...p })), total: found.length }
}

// 하루 합계에 넣을 제품: 내가 먹는 제품(목록에 있는 것) + 고른 제품, 같은 제품은 한 번만
export const combinedIds = (mine, picked) => [...new Set([...mine.filter((m) => m.id).map((m) => m.id), ...picked])]

// 고른 제품을 함께 먹을 때 하루 합계와 상한섭취량 (2025 KDRI 성인). 하루 함량을 아는 성분만 더한다
//   → [{ key, label, unit, total, ul, over, count: 그 성분이 든 고른 제품 수 }]
export function dailyTotals(catalog, ids, sex, age = 30) {
  return catalog.daily
    .map((d) => {
      const values = [...new Set(ids)].map((id) => catalog.products[id]?.daily[d.key]).filter((v) => v !== undefined)
      const total = Math.round(values.reduce((s, v) => s + v, 0) * 100) / 100
      const ul = age >= 19 && age < 30 && d.ulUnder30 ? d.ulUnder30[sex === 1 ? 'male' : 'female'] : sex === 1 && d.ulMale ? d.ulMale : d.ul
      return { key: d.key, label: d.label, unit: d.unit, total, ul, over: ul != null && total > ul, count: values.length }
    })
    .filter((x) => x.count > 0)
}

// 목록 갱신으로 제외된 제품은 합계에서 빼고, 이미 등록한 제품은 메모용 이름으로 남긴다.
export function reconcilePicks(catalog, picks) {
  if (picks.ids.every((id) => catalog.products[id]) && picks.mine.every((m) => !m.id || catalog.products[m.id])) return picks
  return {
    ...picks,
    ids: picks.ids.filter((id) => catalog.products[id]),
    mine: picks.mine.map((m) => m.id && !catalog.products[m.id] ? { name: m.name || `목록에서 제외된 제품 (신고번호 ${m.id})` } : m),
  }
}

export function headroomProducts(catalog, ids) {
  if (new Set(ids).size < 2) return []
  return [...new Set(ids)].filter((id) => catalog.products[id]?.headroom === '적음').map((id) => ({ id, ...catalog.products[id] }))
}

export const totalsMessage = (totals) => {
  const over = totals.filter((x) => x.over)
  if (over.length) return `${over.map((x) => x.label).join('·')} 상한섭취량을 넘어요. 함께 먹기 전에 약사와 상의하세요.`
  if (!totals.length) return '하루 함량을 알 수 없어 상한섭취량과 비교할 수 없어요.'
  return '계산할 수 있는 성분 중에는 상한섭취량을 넘는 것이 없어요. 음식으로 먹는 양과 함량을 모르는 제품은 빠져 있으니, 여러 제품을 함께 먹을 때는 약사와 확인해 보세요.'
}
