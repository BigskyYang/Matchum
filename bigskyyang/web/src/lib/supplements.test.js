import { describe, expect, it } from 'vitest'
import catalog from '../data/supplementCatalog.json'
import { PRODUCT_NUTRIENTS } from '../data/supplementInfo.js'
import { dailyTotals, formsOf, headroomProducts, productCount, productSections, productTexts, reconcilePicks, supplementTargets, targetsFor, totalsMessage } from './supplements.js'

describe('제품 대상 칸 (targetsFor)', () => {
  it('내게 맞춘 칸 먼저, 50세 이상은 시니어, 일반은 마지막', () => {
    expect(targetsFor(2, 30)).toEqual(['여성', '일반'])
    expect(targetsFor(1, 55)).toEqual(['남성', '시니어', '일반'])
  })
})

describe('재준님 결과 → 제품 목록 영양소 (supplementTargets)', () => {
  it('B1·B2는 비타민 B군 하나로, 나트륨·비타민 A는 빠지고, 단백질은 음식으로', () => {
    const t = supplementTargets(['sodium_excess', 'zinc', 'vitamin_b2', 'vitamin_a', 'vitamin_b1', 'protein'])
    expect(t.nutrients.map((n) => n.key)).toEqual(['vitamin_b', 'zinc'])
    expect(t.nutrients[0].from).toEqual(['vitamin_b1', 'vitamin_b2'])
    expect(t.foodOnly).toEqual(['단백질'])
  })

  it('살펴볼 영양소가 없으면 빈 목록', () => {
    expect(supplementTargets([])).toEqual({ nutrients: [], foodOnly: [] })
  })
})

describe('제품 목록 (준혁님 9단계 후보 전체)', () => {
  it('11-05 최신 파일: 칼슘 일반 대상 319개 (자르지 않는다)', () => {
    const [general] = productSections(catalog, 'calcium', ['일반'])
    expect(general.items).toHaveLength(319)
  })

  it('대상 칸을 섞지 않고, 원본 순서를 그대로 쓴다', () => {
    const sections = productSections(catalog, 'multi_balance', ['여성', '일반'])
    expect(sections.map((s) => s.target)).toEqual(['여성', '일반'])
    expect(sections[1].items.map((p) => p.id)).toEqual(catalog.lists.multi_balance['일반'].map(([id]) => id))
  })

  it('제형으로 거르면 그 제형만, 순서는 그대로', () => {
    const [all] = productSections(catalog, 'calcium', ['일반'])
    const [tablets] = productSections(catalog, 'calcium', ['일반'], ['정'])
    expect(tablets.items.every((p) => p.form === '정')).toBe(true)
    expect(tablets.items.map((p) => p.id)).toEqual(all.items.filter((p) => p.form === '정').map((p) => p.id))
    expect(formsOf(catalog, 'calcium', ['일반']).reduce((s, f) => s + f.count, 0)).toBe(319)
  })

  it('제품 수는 같은 제품을 한 번만 센다', () => {
    const ids = ['남성', '시니어', '일반'].flatMap((t) => (catalog.lists.zinc[t] ?? []).map(([id]) => id))
    expect(productCount(catalog, 'zinc', ['남성', '시니어', '일반'])).toBe(new Set(ids).size)
  })

  it('기능성·주의사항 원문을 찾을 수 있다', () => {
    const [{ items }] = productSections(catalog, 'magnesium', ['일반'])
    const t = productTexts(catalog, items[0])
    expect(t.function.length).toBeGreaterThan(0)
    expect(t.caution.length).toBeGreaterThan(0)
  })
})

describe('함께 먹을 때 하루 합계와 상한 (dailyTotals)', () => {
  const vitC = Object.entries(catalog.products).filter(([, p]) => p.daily.vitamin_c >= 1000).map(([id]) => id)

  it('하루 함량을 더하고 상한을 넘으면 표시한다', () => {
    const two = vitC.slice(0, 3)
    const row = dailyTotals(catalog, two, 2).find((x) => x.key === 'vitamin_c')
    const sum = two.reduce((s, id) => s + catalog.products[id].daily.vitamin_c, 0)
    expect(row.total).toBeCloseTo(sum, 2)
    expect(row.over).toBe(sum > 2000)
  })

  it('남성은 칼슘 상한 2,500mg', () => {
    const id = Object.keys(catalog.products).find((k) => catalog.products[k].daily.calcium)
    expect(dailyTotals(catalog, [id], 1).find((x) => x.key === 'calcium').ul).toBe(2500)
    expect(dailyTotals(catalog, [id], 2).find((x) => x.key === 'calcium').ul).toBe(2000)
  })

  it('아무것도 고르지 않으면 빈 목록', () => {
    expect(dailyTotals(catalog, [], 2)).toEqual([])
  })

  it('19~29세는 칼슘의 별도 상한을 적용하고 30세부터 성인 기준을 쓴다', () => {
    const id = Object.keys(catalog.products).find((k) => catalog.products[k].daily.calcium)
    const ul = (sex, age) => dailyTotals(catalog, [id], sex, age).find((x) => x.key === 'calcium').ul
    expect(ul(1, 19)).toBe(3000)
    expect(ul(2, 29)).toBe(2500)
    expect(ul(1, 30)).toBe(2500)
    expect(ul(2, 30)).toBe(2000)
  })

  it('요오드를 합산하고 2,400μg 경계를 넘을 때만 초과로 표시한다', () => {
    const fixture = { ...catalog, products: { a: { daily: { iodine: 1200 } }, b: { daily: { iodine: 1201 } } } }
    expect(dailyTotals(fixture, ['a', 'a'], 2).find((x) => x.key === 'iodine')).toMatchObject({ total: 1200, ul: 2400, over: false })
    expect(dailyTotals(fixture, ['a', 'b'], 2).find((x) => x.key === 'iodine')).toMatchObject({ total: 2401, over: true })
  })

  it('함량을 몰라 계산하지 못한 경우를 초과 없음으로 안내하지 않는다', () => {
    expect(totalsMessage([])).toContain('비교할 수 없어요')
    expect(totalsMessage([{ label: '요오드', over: false }])).toContain('계산할 수 있는 성분 중에는')
    expect(totalsMessage([{ label: '요오드', over: true }])).toContain('요오드 상한섭취량을 넘어요')
  })

  it('상한 여유가 적은 제품을 다른 제품과 함께 볼 때만 안내한다', () => {
    const [low] = Object.keys(catalog.products).filter((id) => catalog.products[id].headroom === '적음')
    const other = Object.keys(catalog.products).find((id) => id !== low)
    expect(headroomProducts(catalog, [low])).toEqual([])
    expect(headroomProducts(catalog, [low, low])).toEqual([])
    expect(headroomProducts(catalog, [low, other]).map((p) => p.id)).toContain(low)
  })
})

describe('제품 목록 파일 supplementCatalog.json 형식', () => {
  it('웹이 연결하는 영양소는 모두 목록에 있다', () => {
    const keys = catalog.categories.map((c) => c.key)
    for (const n of PRODUCT_NUTRIENTS) expect(keys).toContain(n.key)
  })

  it('목록의 모든 제품이 제품 정보에 있고, 대상은 일반·남성·여성·시니어', () => {
    for (const byTarget of Object.values(catalog.lists)) {
      for (const [t, rows] of Object.entries(byTarget)) {
        expect(catalog.targets).toContain(t)
        for (const [id] of rows) expect(catalog.products[id]).toBeDefined()
      }
    }
  })

  it('점수·등급·순위·가격·판매처는 넣지 않는다', () => {
    const allowed = ['name', 'maker', 'form', 'intake', 'function', 'caution', 'daily', 'headroom', 'halfUlIngredients']
    for (const p of Object.values(catalog.products)) expect(Object.keys(p).sort()).toEqual([...allowed].sort())
  })

  it('첨부 최신 제품 2,220개이며 함량이 없는 61개는 모두 식이섬유다', () => {
    expect(Object.keys(catalog.products)).toHaveLength(2220)
    const missing = Object.keys(catalog.products).filter((id) => !Object.keys(catalog.products[id].daily).length)
    expect(missing).toHaveLength(61)
    const fiber = new Set(Object.values(catalog.lists.fiber).flat().map(([id]) => id))
    expect(missing.every((id) => fiber.has(id))).toBe(true)
    const linked = Object.values(catalog.lists).flatMap((targets) => Object.values(targets).flat().map(([id]) => id))
    expect(linked).toHaveLength(2220)
    expect(new Set(linked).size).toBe(2220)
  })

  it('목록 갱신 후 제외된 제품은 합계에서 빼고 기존 등록은 함량 모름으로 남긴다', () => {
    const id = Object.keys(catalog.products)[0]
    const original = { ids: [id, 'removed'], gate: 'consult', mine: [{ id: 'removed' }, { name: '직접 적은 제품' }] }
    const next = reconcilePicks(catalog, original)
    expect(next.ids).toEqual([id])
    expect(next.mine[0]).toEqual({ name: '목록에서 제외된 제품 (신고번호 removed)' })
    expect(next.gate).toBe('consult')
    expect(original.ids).toContain('removed')
    expect(reconcilePicks(catalog, next)).toBe(next)
  })
})
