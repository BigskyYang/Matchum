import { describe, expect, it } from 'vitest'
import { LEAF_TYPES } from '../data/types.js'
import { SCORE_AXES } from './profile.js'
import { SAMPLE } from './fixtures.js'
import { buildResult } from './result.js'

// 설문 응답 하나로 결과 화면에 필요한 값이 모두 나오는지 (화면 없이 확인)
describe('buildResult', () => {
  const r = buildResult(SAMPLE)

  it('유형 이름·설명·해시태그·비율', () => {
    expect(LEAF_TYPES[r.leafId]).toBeDefined()
    expect(r.name).toBe(LEAF_TYPES[r.leafId].name)
    expect(r.summary).toBe(LEAF_TYPES[r.leafId].summary)
    expect(r.mainType.name).toEqual(expect.any(String))
    expect(r.tags.length).toBeGreaterThan(0)
    expect(r.sharePct).toBeGreaterThan(0)
    expect(r.sharePct).toBeLessThan(100)
  })

  it('생활습관 신호등은 영역마다 내 점수와 유형 평균이 0~1', () => {
    for (const s of [r.myScores, r.typeScores]) {
      expect(s).toHaveLength(SCORE_AXES.length)
      for (const v of s) expect(v >= 0 && v <= 1).toBe(true)
    }
  })

  it('미션 3개 이하, 음식 6개 이하이고 음식 이름이 겹치지 않는다', () => {
    expect(r.missions.length).toBeLessThanOrEqual(3)
    expect(r.foods.length).toBeGreaterThan(0)
    expect(r.foods.length).toBeLessThanOrEqual(6)
    expect(new Set(r.foods.map((f) => f.label)).size).toBe(r.foods.length)
  })

  it('부족할 수 있는 영양소: 공통 8개 + 내 유형에서 살펴볼 것, 성별·연령대 표시', () => {
    expect(r.nutrients.common).toHaveLength(8)
    expect(Array.isArray(r.nutrients.picks)).toBe(true)
    expect(r.nutrientsEmptyText).toEqual(expect.any(String))
    expect(r.sexLabel).toBe('여성')
    expect(r.ageLabel).toMatch(/세/)
  })

  it('짝꿍은 다른 대분류이고, 선택 문항을 안 고르면 마음·대사 건강 카드가 없다', () => {
    expect(r.partner.type.name).not.toBe(r.mainType.name)
    expect(r.optional).toBeNull()
    expect(r.hasCondition).toBe(false)
  })
})
