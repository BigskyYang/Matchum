import { describe, expect, it } from 'vitest'
import CASES from './classify.fixtures.json'
import averages from '../data/habitAverages.json'
import { classify, classifyDetail, model } from './classify.js'
import { STAGE1_SAMPLE } from './fixtures.js'
import { TYPE_AXES, levelOf, partnerTypes } from './profile.js'
import { BOUNDARY_LEVELS, allTypes, buildTypeResult, compareHabits, typeBoundary } from './result.js'

// 6/10: 나 vs 우리 유형 평균 vs 성인 전체 평균, 유형 경계 (analysis/01_clustering/validation/07_boundary.py와 같은 경계 여유)
describe('classifyDetail (유형 경계)', () => {
  it('제곱거리가 아닌 실제 거리로 여유를 계산하고 이웃 대분류의 척도로 세부 유형을 고른다', () => {
    const toy = {
      inputs: [{ name: 'x', clip: [-100, 100] }],
      scores: [{ name: 's', const: 0, coef: { x: 1 } }],
      pca: { mean: [0], components: [[1]] },
      macro: [{ code: 'N', center: [0] }, { code: 'O', center: [10] }],
      sub: {
        N: { features: ['s'], mean: [0], std: [1], centers: { N1: [0], N2: [20] } },
        O: { features: ['s'], mean: [20], std: [2], centers: { O1: [0], O2: [-8] } },
      },
    }
    const detail = classifyDetail({ x: 2 }, toy)
    expect(detail.mainMargin).toBeCloseTo(0.75, 12)
    expect(detail.mainNeighbor).toBe('O2')
    expect(detail.leafNeighbor).toBe('N2')
  })
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
  it('지연님 가중 평균을 평균 비교·전체 유형·짝꿍 선택에 일관되게 쓴다', () => {
    expect(averages.modelVersion).toBe(model.version)
    expect(averages.axes).toEqual(TYPE_AXES.map((a) => a.key))
    expect(r.habits.map((h) => h.allAvg)).toEqual([0.375, 0.404, 0.892, 0.742, 0.848, 0.518])
    expect(r.habits.map((h) => h.typeAvg)).toEqual(averages.types[r.leafId])
    for (const t of allTypes().flatMap((g) => g.types)) {
      expect(t.habits.map((h) => h.score)).toEqual(averages.types[t.id])
    }
    const o3 = allTypes().flatMap((g) => g.types).find((t) => t.id === 'O3')
    expect(o3.habits.find((h) => h.key === 'exercise').score).toBe(0.700)
    expect(levelOf(o3.habits.find((h) => h.key === 'exercise').score).tone).toBe('fair')
    const expected = partnerTypes(r.habits.map((h) => h.score), r.leafId, averages.types, TYPE_AXES)
    expect(r.partners.fill.id).toBe(expected.fill.id)
    expect(r.partners.together.id).toBe(expected.together.id)
  })
  it('compareHabits: 차이 0.15 이상만, 큰 순서로 2개까지', () => {
    const h = (key, score, typeAvg) => ({ key, score, typeAvg })
    const { ahead, behind } = compareHabits([h('a', 0.9, 0.5), h('b', 0.6, 0.5), h('c', 0.2, 0.8), h('d', 0.7, 0.3), h('e', 0.95, 0.5)])
    expect(ahead.map((x) => x.key)).toEqual(['e', 'a'])
    expect(behind.map((x) => x.key)).toEqual(['c'])
  })
})
