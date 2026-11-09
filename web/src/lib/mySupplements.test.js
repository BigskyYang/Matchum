import { describe, expect, it } from 'vitest'
import catalog from '../data/supplementCatalog.json'
import { wrapText } from './memoImage.js'
import { combinedIds, dailyTotals, searchProducts } from './supplements.js'

// 9/10 내가 먹는 건강기능식품 (pages/MySupplementsPage.jsx)
describe('searchProducts (먹고 있는 제품 찾기)', () => {
  const [id, p] = Object.entries(catalog.products).find(([, x]) => x.name.length >= 6)

  it('제품명 일부로 찾는다 (띄어쓰기·대소문자 무시)', () => {
    const part = p.name.replace(/\s+/g, '').slice(0, 5)
    const { items } = searchProducts(catalog, part, 3000)
    expect(items.map((x) => x.id)).toContain(id)
  })

  it('회사 이름으로도 찾는다', () => {
    const { items } = searchProducts(catalog, p.maker, 3000)
    expect(items.every((x) => x.maker.replace(/\s+/g, '').toLowerCase().includes(p.maker.replace(/\s+/g, '').toLowerCase()) || x.name.includes(p.maker))).toBe(true)
    expect(items.map((x) => x.id)).toContain(id)
  })

  it('2글자 미만이면 찾지 않고, limit개까지만 돌려주며 전체 개수를 알려 준다', () => {
    expect(searchProducts(catalog, '비').items).toEqual([])
    const r = searchProducts(catalog, '비타민', 5)
    expect(r.items.length).toBe(5)
    expect(r.total).toBeGreaterThan(5)
  })
})

describe('combinedIds (하루 합계에 넣을 제품)', () => {
  it('목록에 있는 내 제품 + 고른 제품, 겹치면 한 번만, 이름만 적은 제품은 빠진다', () => {
    expect(combinedIds([{ id: 'a' }, { name: '직접 적은 것' }, { id: 'b' }], ['b', 'c'])).toEqual(['a', 'b', 'c'])
  })

  it('같은 제품을 두 번 더하지 않는다', () => {
    const [id] = Object.entries(catalog.products).find(([, x]) => Object.keys(x.daily).length)
    const once = dailyTotals(catalog, [id], 2)
    const both = dailyTotals(catalog, combinedIds([{ id }], [id]), 2)
    expect(both).toEqual(once)
  })
})

describe('wrapText (메모 이미지 줄바꿈)', () => {
  const measure = (t) => t.length * 10
  it('폭을 넘으면 글자 단위로 줄을 바꾸고, 줄 끝 공백은 지운다', () => {
    expect(wrapText(measure, '가나다 라마바사', 40)).toEqual(['가나다', '라마바사'])
    expect(wrapText(measure, '짧음', 100)).toEqual(['짧음'])
  })
})
