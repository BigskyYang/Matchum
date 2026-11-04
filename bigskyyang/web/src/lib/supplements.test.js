import { describe, expect, it } from 'vitest'
import catalog from '../data/supplementCatalog.json'
import { PRODUCT_NUTRIENTS } from '../data/supplementInfo.js'
import { dailyTotals, formsOf, productCount, productSections, productTexts, supplementTargets, targetsFor } from './supplements.js'

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
  it('재준님 인수 확인: 칼슘 일반 대상 334개 (자르지 않는다)', () => {
    const [general] = productSections(catalog, 'calcium', ['일반'])
    expect(general.items).toHaveLength(334)
  })

  it('대상 칸을 섞지 않고, 원본 순서를 그대로 쓴다', () => {
    const sections = productSections(catalog, 'zinc', ['여성', '일반'])
    expect(sections.map((s) => s.target)).toEqual(['여성', '일반'])
    expect(sections[1].items.map((p) => p.id)).toEqual(catalog.lists.zinc['일반'].map(([id]) => id))
  })

  it('제형으로 거르면 그 제형만, 순서는 그대로', () => {
    const [all] = productSections(catalog, 'calcium', ['일반'])
    const [tablets] = productSections(catalog, 'calcium', ['일반'], ['정'])
    expect(tablets.items.every((p) => p.form === '정')).toBe(true)
    expect(tablets.items.map((p) => p.id)).toEqual(all.items.filter((p) => p.form === '정').map((p) => p.id))
    expect(formsOf(catalog, 'calcium', ['일반']).reduce((s, f) => s + f.count, 0)).toBe(334)
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
    const allowed = ['name', 'maker', 'form', 'intake', 'function', 'caution', 'daily']
    for (const p of Object.values(catalog.products)) expect(Object.keys(p).sort()).toEqual([...allowed].sort())
  })
})
