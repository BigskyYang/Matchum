import { describe, expect, it } from 'vitest'
import models from '../data/nutritionModels.json'
import pythonLegume from './simulationNutrition.fixtures.json'
import { encode } from './encode.js'
import { SAMPLE, bornAt } from './fixtures.js'
import { habitualFeatures, lifestyleFeatures, predictNutrition } from './nutritionRisk.js'
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

  it('바뀐 영양소는 대표 모델의 등급 차이이며 개선·악화로 분류하지 않는다', () => {
    const s = simulate(SAMPLE, availableChanges(SAMPLE).map((c) => c.id), models)
    for (const n of s.nutrients) {
      expect(n.from).not.toBe(n.to)
      expect(['habitual', 'lifestyle']).toContain(n.source)
      expect(n).not.toHaveProperty('better')
    }
  })

  it('이미 기준을 충족한 응답을 선택해도 낮추지 않으며 원래 응답을 수정하지 않는다', () => {
    const enough = { ...SAMPLE, strength_days: 5, sedentary_min: 60, ffq_dairy: 7, ffq_legume: 6, meals: { breakfast: 3, lunch: 3, dinner: 3 } }
    expect(applyChanges(enough, ['strength', 'sit', 'breakfast', 'dairy', 'legume'])).toEqual(enough)
    expect(applyChanges(SAMPLE, ['legume']).ffq_legume).toBe(5)
    expect(SAMPLE.ffq_legume).toBe(2)
  })

  it('금연은 현재 흡연과 하루 흡연량 모두 0, 절주는 음주 입력끼리 일관된다', () => {
    const smoking = applyChanges({ ...SAMPLE, smoke_now: 'yes', cigarettes: 20 }, ['smoke'])
    expect(smoking).toMatchObject({ smoke_now: 'no', cigarettes: 0 })
    expect(encode(smoking).features).toMatchObject({ ML_smoker: 0, ML_cigarettes_day: 0 })
    const reduced = applyChanges({ ...SAMPLE, drink_freq: 5, drink_amount: 5 }, ['drink'])
    expect(encode(reduced).features).toMatchObject({ ML_drink_month: 1, ML_drink_freq_ord: 3, ML_drink_amount_ord: 1 })
    const rare = applyChanges({ ...SAMPLE, drink_freq: 1, drink_amount: 5 }, ['drink'])
    expect(encode(rare).features).toMatchObject({ ML_drink_month: 0, ML_drink_freq_ord: 1, ML_drink_amount_ord: 1 })
    const none = applyChanges({ ...SAMPLE, drink_amount: 5 }, ['drink'])
    expect(encode(none).features).toMatchObject({ ML_drink_month: 0, ML_drink_freq_ord: 0, ML_drink_amount_ord: 0 })
  })

  it('채소·과일 변경은 학습 코드의 하루 1회(3)와 대응하고 좌식은 음수가 되지 않는다', () => {
    const next = applyChanges(SAMPLE, ['veg', 'fruit', 'sit'])
    expect(lifestyleFeatures(next, encode(next).features)).toMatchObject({ 식습관_LS_FRUIT: 3, 식습관_LS_VEG2: 3 })
    expect(CHANGES.find((c) => c.id === 'sit').apply({ ...SAMPLE, sedentary_min: 30 }).sedentary_min).toBe(0)
  })

  it('운동 변경은 평소 식사 대표 등급을 유지하고 생활습관 결과는 별도로 비교한다', () => {
    const before = buildNutrition(SAMPLE)
    const next = applyChanges(SAMPLE, ['aerobic'])
    expect(buildNutrition(next).habitual).toEqual(before.habitual)
    const s = simulate(SAMPLE, ['aerobic'], models)
    expect(s.habitualAvailable).toBe(true)
    expect(s.nutrients.every((n) => n.source === 'lifestyle')).toBe(true)
    expect(s.lifestyleNutrients).toEqual(expect.any(Array))
  })

  it('콩 섭취만 바꾼 모델 입력·확률·등급이 Python 1.8.0의 재현 결과와 같다', () => {
    const original = { ...SAMPLE, birth_date: bornAt(25) }
    const next = applyChanges(original, ['legume'])
    expect(Object.keys(next).filter((k) => next[k] !== original[k])).toEqual(['ffq_legume'])
    for (const [i, a] of [original, next].entries()) {
      const { extras } = encode(a)
      expect(habitualFeatures(extras)).toEqual(pythonLegume.cases[i].row)
      const result = buildNutrition(a).habitual
      for (const [key, expected] of Object.entries(pythonLegume.cases[i].expected)) {
        expect(result[key].probability).toBeCloseTo(expected.probability, 8)
        expect(result[key].band).toBe(expected.band)
      }
    }
    expect(simulate(original, ['legume'], models).nutrients).toContainEqual(expect.objectContaining({ key: 'sodium_excess', from: 'Mid', to: 'High' }))
  })

  it('모델을 불러오기 전에는 유형만', () => {
    expect(simulate(SAMPLE, ['aerobic'], null).nutrients).toBeNull()
  })

  it('습관 id가 겹치지 않는다', () => {
    expect(new Set(CHANGES.map((c) => c.id)).size).toBe(CHANGES.length)
  })
})

function buildNutrition(answers) {
  const { features, extras } = encode(answers)
  return predictNutrition(models, lifestyleFeatures(answers, features), habitualFeatures(extras))
}
