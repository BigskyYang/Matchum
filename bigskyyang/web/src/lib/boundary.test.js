import { describe, expect, it } from 'vitest'
import CASES from './classify.fixtures.json'
import { classify, classifyDetail } from './classify.js'
import { STAGE1_SAMPLE } from './fixtures.js'
import { TYPE_AXES } from './profile.js'
import { BOUNDARY_LEVELS, buildTypeResult, compareHabits, typeBoundary } from './result.js'

// 6/10: 나 vs 우리 유형 평균 vs 성인 전체 평균, 유형 경계 (bigskyyang/analysis/07_boundary.py와 같은 경계 여유)
describe('classifyDetail (유형 경계)', () => {
  it.each(CASES.map((c) => [c.leaf, c]))('%s: 판정은 classify와 같고, 경계 여유는 0~1, 이웃은 다른 유형', (_, c) => {
    const d = classifyDetail(c.features)
    expect({ main: d.main, leaf: d.leaf }).toEqual(classify(c.features))
    for (const m of [d.mainMargin, d.leafMargin]) {
      expect(m).toBeGreaterThanOrEqual(0)
      expect(m).toBeLessThanOrEqual(1)
    }
    expect(d.mainNeighbor[0]).not.toBe(d.main)
    expect(d.leafNeighbor[0]).toBe(d.main)
    expect(d.leafNeighbor).not.toBe(d.leaf)
  })
})

describe('typeBoundary', () => {
  const base = { main: 'S', mainNeighbor: 'O1', leafNeighbor: 'S3' }
  it('경계 여유가 작은 쪽의 이웃을 고른다', () => {
    expect(typeBoundary({ ...base, mainMargin: 0.05, leafMargin: 0.4 }).neighbor.id).toBe('O1')
    expect(typeBoundary({ ...base, mainMargin: 0.4, leafMargin: 0.05 }).neighbor.id).toBe('S3')
    expect(typeBoundary({ ...base, mainMargin: 0.4, leafMargin: 0.05 }).sameMain).toBe(true)
  })
  it('10% 미만은 경계, 30% 미만은 가까움, 그 이상은 중심', () => {
    const level = (m) => typeBoundary({ ...base, mainMargin: m, leafMargin: 1 }).level
    expect(level(0)).toBe('edge')
    expect(level(BOUNDARY_LEVELS.edge - 0.001)).toBe('edge')
    expect(level(BOUNDARY_LEVELS.edge)).toBe('near')
    expect(level(BOUNDARY_LEVELS.near)).toBe('core')
  })
  it('그림 위치: 경계 여유 0 → 가운데(0.5), 60% 이상 → 내 유형 쪽 끝(0)', () => {
    const pos = (m) => typeBoundary({ ...base, mainMargin: m, leafMargin: 1 }).pos
    expect(pos(0)).toBe(0.5)
    expect(pos(0.3)).toBeCloseTo(0.25)
    expect(pos(0.6)).toBe(0)
    expect(pos(0.9)).toBe(0)
  })
})

describe('나 vs 평균', () => {
  const r = buildTypeResult(STAGE1_SAMPLE)
  it('습관마다 내 점수·우리 유형 평균·성인 전체 평균 (0~1)', () => {
    expect(r.habits.map((h) => h.key)).toEqual(TYPE_AXES.map((a) => a.key))
    for (const h of r.habits) {
      for (const v of [h.score, h.typeAvg, h.allAvg]) {
        expect(v).toBeGreaterThanOrEqual(0)
        expect(v).toBeLessThanOrEqual(1)
      }
    }
  })
  it('결과에 경계 정보가 있다', () => {
    expect(['edge', 'near', 'core']).toContain(r.boundary.level)
    expect(r.boundary.neighbor.id).not.toBe(r.leafId)
  })
  it('compareHabits: 차이 0.15 이상만, 큰 순서로 2개까지', () => {
    const h = (key, score, typeAvg) => ({ key, score, typeAvg })
    const { ahead, behind } = compareHabits([h('a', 0.9, 0.5), h('b', 0.6, 0.5), h('c', 0.2, 0.8), h('d', 0.7, 0.3), h('e', 0.95, 0.5)])
    expect(ahead.map((x) => x.key)).toEqual(['e', 'a'])
    expect(behind.map((x) => x.key)).toEqual(['c'])
  })
})
