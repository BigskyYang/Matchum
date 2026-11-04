import { describe, expect, it } from 'vitest'
import { LEAF_TYPES } from '../data/types.js'
import { SAMPLE, STAGE1_SAMPLE } from './fixtures.js'
import { PERSONAL_AXES, TYPE_AXES } from './profile.js'
import { buildPersonalResult, buildTypeResult } from './result.js'

// 설문 응답으로 결과 화면에 필요한 값이 모두 나오는지 (화면 없이 확인)
describe('buildTypeResult (1단계 유형 결과)', () => {
  const r = buildTypeResult(STAGE1_SAMPLE)

  it('1단계만 답해도 유형 이름·설명·해시태그·비율이 나온다', () => {
    expect(LEAF_TYPES[r.leafId]).toBeDefined()
    expect(r.name).toBe(LEAF_TYPES[r.leafId].name)
    expect(r.summary).toBe(LEAF_TYPES[r.leafId].summary)
    expect(r.mainType.name).toEqual(expect.any(String))
    expect(r.tags.length).toBeGreaterThan(0)
    expect(r.sharePct).toBeGreaterThan(0)
    expect(r.sharePct).toBeLessThan(100)
  })

  it('2단계까지 답해도 유형은 같다 (유형은 1단계 문항으로만 정한다)', () => {
    expect(buildTypeResult(SAMPLE).leafId).toBe(r.leafId)
  })

  it('생활습관 신호등은 유형을 만든 영역만 (흡연·음주 제외), 점수 0~1', () => {
    expect(r.habits.map((h) => h.key)).toEqual(TYPE_AXES.map((a) => a.key))
    expect(r.habits.map((h) => h.key)).not.toContain('smoke')
    for (const h of r.habits) expect(h.score >= 0 && h.score <= 1).toBe(true)
  })

  it('이번 주 해볼 것은 3개 이하이고, 흡연·음주 미션은 없다', () => {
    expect(r.missions.length).toBeLessThanOrEqual(3)
    expect(r.missions.map((m) => m.icon)).not.toContain('🚭')
  })

  it('수면이 들쭉날쭉하면 잠·식사 시간 미션이 먼저 나온다', () => {
    const irregular = buildTypeResult({ ...STAGE1_SAMPLE, sleep_regular: 'no', sleep_avg: 7 * 60 })
    expect(irregular.missions[0].title).toBe('잠·식사 시간 맞추기')
  })

  it('부족할 수 있는 영양소: 공통 8개 + 2줄 (판정 코드 포함), 성별·연령대 표시', () => {
    expect(r.nutrients.common).toHaveLength(8)
    for (const n of r.nutrients.picks) expect(['유형특이', '식사량영향', '흔함']).toContain(n.tag)
    expect(r.nutrientsEmptyText).toEqual(expect.any(String))
    expect(r.sexLabel).toBe('여성')
    expect(r.ageLabel).toMatch(/세/)
  })

  it('짝꿍은 다른 대분류', () => {
    expect(r.partner.type.name).not.toBe(r.mainType.name)
  })
})

describe('buildPersonalResult (2단계 개인 결과)', () => {
  const r = buildPersonalResult(SAMPLE)

  it('흡연·음주 신호등과 음식 6개 이하 (이름이 겹치지 않게)', () => {
    expect(r.habits.map((h) => h.key)).toEqual(PERSONAL_AXES.map((a) => a.key))
    expect(r.foods.length).toBeGreaterThan(0)
    expect(r.foods.length).toBeLessThanOrEqual(6)
    expect(new Set(r.foods.map((f) => f.label)).size).toBe(r.foods.length)
  })

  it('흡연자면 금연 미션', () => {
    const smoker = buildPersonalResult({ ...SAMPLE, smoke_now: 'daily', cigarettes: 10 })
    expect(smoker.missions.map((m) => m.icon)).toContain('🚭')
  })

  it('mini-FFQ에 답했는지 (65세 이상은 묻지 않음)', () => {
    expect(r.ffqAsked).toBe(true)
    const year = new Date().getFullYear()
    const older = { ...SAMPLE, birth_year: year - 70 }
    for (const k of ['meat', 'fish', 'egg', 'legume', 'dairy']) delete older[`ffq_${k}`]
    expect(buildPersonalResult(older).ffqAsked).toBe(false)
  })
})
