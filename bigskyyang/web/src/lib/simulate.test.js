import { describe, expect, it } from 'vitest'
import models from '../data/nutritionModels.json'
import { encode } from './encode.js'
import { SAMPLE } from './fixtures.js'
import { CHANGES, applyChanges, availableChanges, simulate } from './simulate.js'
import { pickTips } from '../data/tips.js'

// '이렇게 바꾸면?' 시뮬레이터 (lib/simulate.js)
describe('simulate', () => {
  it('지금 응답이 이미 기준을 넘는 습관은 보여 주지 않는다', () => {
    const ids = availableChanges(SAMPLE).map((c) => c.id)
    expect(ids).toContain('breakfast') // 아침 0
    expect(ids).toContain('aerobic') // 주 1시간~2시간 반
    expect(ids).not.toContain('smoke') // 비흡연
    expect(ids).not.toContain('drink') // 음주 안 함
    expect(ids).not.toContain('meals') // 점심·저녁은 챙김
  })

  it('켠 습관을 적용하면 그 습관의 미션은 더 나오지 않는다', () => {
    const ids = availableChanges(SAMPLE).map((c) => c.id)
    const next = applyChanges(SAMPLE, ids)
    const { features, extras } = encode(next)
    // '하루 2시간 덜 앉기'는 한 번 더 켤 수 있다 (600분 → 480분, 아직 6시간 이상)
    expect(availableChanges(next).map((c) => c.id)).toEqual(['sit'])
    const missions = pickTips(features, extras, true).map((t) => t.id)
    for (const id of ['breakfast', 'aerobic', 'strength', 'eating_out', 'sedentary']) expect(missions).not.toContain(id)
  })

  it('수면: 기상 시각은 그대로 두고 평일·주말 모두 7시간', () => {
    const short = { ...SAMPLE, weekday_bed: '02:00', weekday_wake: '06:30', weekend_same: 'yes' }
    expect(availableChanges(short).map((c) => c.id)).toContain('sleep')
    const next = applyChanges(short, ['sleep'])
    expect(next.weekday_bed).toBe('23:30')
    expect(encode(next).features.ML_sleep_hours).toBe(7)
  })

  it('아무것도 켜지 않으면 바뀌는 것이 없다', () => {
    const s = simulate(SAMPLE, [], models)
    expect(s.type.changed).toBe(false)
    expect(s.nutrients).toEqual([])
  })

  it('바뀐 영양소는 등급이 다르고, 좋아진 것이 먼저', () => {
    const s = simulate(SAMPLE, availableChanges(SAMPLE).map((c) => c.id), models)
    for (const n of s.nutrients) expect(n.from).not.toBe(n.to)
    const firstWorse = s.nutrients.findIndex((n) => !n.better)
    if (firstWorse !== -1) expect(s.nutrients.slice(firstWorse).every((n) => !n.better)).toBe(true)
  })

  it('모델을 불러오기 전에는 유형만', () => {
    expect(simulate(SAMPLE, ['aerobic'], null).nutrients).toBeNull()
  })

  it('습관 id가 겹치지 않는다', () => {
    expect(new Set(CHANGES.map((c) => c.id)).size).toBe(CHANGES.length)
  })
})
