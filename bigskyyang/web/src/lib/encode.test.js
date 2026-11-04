import { describe, expect, it } from 'vitest'
import { visibleQuestions } from '../data/questions.js'
import { ageFromYear, encode, sleepFromAverage, sleepHours } from './encode.js'
import { SAMPLE, STAGE1_SAMPLE } from './fixtures.js'

describe('sleepHours', () => {
  it('자정을 넘기는 수면을 계산한다', () => {
    expect(sleepHours('23:30', '07:00')).toBe(7.5)
    expect(sleepHours('01:00', '07:00')).toBe(6)
  })
})

describe('ageFromYear', () => {
  it('올해 - 출생연도', () => {
    expect(ageFromYear(2001, new Date(2026, 10, 4))).toBe(25)
  })
})

describe('encode', () => {
  it('2단계에서 비흡연·비음주로 답하면 0', () => {
    const { features } = encode(SAMPLE)
    expect(features.ML_smoker).toBe(0)
    expect(features.ML_cigarettes_day).toBe(0)
    expect(features.ML_drink_month).toBe(0)
    expect(features.ML_drink_freq_ord).toBe(0)
    expect(features.ML_drink_amount_ord).toBe(0)
  })

  it('1단계만 답해도 변환된다 (2단계 값은 0 또는 null)', () => {
    const { features, extras } = encode(STAGE1_SAMPLE)
    expect(features.ML_smoker).toBe(0)
    expect(features.ML_drink_freq_ord).toBe(0)
    expect(extras.veg).toBeNull()
    expect(extras.age).toBeGreaterThanOrEqual(19)
  })

  it('유산소: 보기 "2시간 반 이상"만 주 150분 이상', () => {
    expect(encode(SAMPLE).features.ML_aerobic).toBe(0)
    expect(encode({ ...SAMPLE, activity: 3 }).features.ML_aerobic).toBe(1)
  })

  it('세 끼는 한 문항의 줄별 응답', () => {
    const { features } = encode(SAMPLE)
    expect([features.ML_breakfast_freq_ord, features.ML_lunch_freq_ord, features.ML_dinner_freq_ord]).toEqual([0, 3, 3])
  })

  it('평균 수면 = (주중×5 + 주말×2) / 7, 주말이 비슷하면 주중 값을 그대로', () => {
    expect(encode(SAMPLE).features.ML_sleep_hours).toBeCloseTo((6 * 5 + 8 * 2) / 7)
    expect(encode({ ...SAMPLE, weekend_same: 'yes' }).features.ML_sleep_hours).toBeCloseTo(6)
  })

  it('수면이 들쭉날쭉하면 평균 시간을 2024 척도로 옮겨 쓰고, 미션 안내용으로 표시한다', () => {
    const { features, extras } = encode({ ...SAMPLE, sleep_regular: 'no', sleep_avg: 7 * 60 })
    expect(features.ML_sleep_hours).toBeCloseTo(sleepFromAverage(7))
    expect(features.ML_sleep_hours).toBeGreaterThan(7) // 직접 답한 시간은 시각으로 계산한 것보다 짧게 나오는 경향
    expect(extras.sleepIrregular).toBe(true)
  })

  it('스트레스 1·2 → 1', () => {
    expect(encode(SAMPLE).features.ML_stress).toBe(1)
  })

  it('현재 흡연자·음주자', () => {
    const { features } = encode({
      ...SAMPLE,
      smoke_100: 'yes',
      smoke_now: 'sometimes',
      cigarettes: 5,
      drink_ever: 'yes',
      drink_freq: 1,
      drink_amount: 2,
    })
    expect(features.ML_smoker).toBe(1)
    expect(features.ML_cigarettes_day).toBe(5)
    expect(features.ML_drink_month).toBe(0) // 월 1회 미만
    expect(features.ML_drink_amount_ord).toBe(2)
  })
})

describe('visibleQuestions', () => {
  it('1단계는 유형 분류 문항만, 수면이 일정하고 주말이 다르면 시각 4개', () => {
    const ids = visibleQuestions(SAMPLE, 1).map((q) => q.id)
    expect(ids).toEqual([
      'sex',
      'birth_year',
      'activity',
      'strength_days',
      'sedentary_min',
      'sleep_regular',
      'weekday_bed',
      'weekday_wake',
      'weekend_same',
      'weekend_bed',
      'weekend_wake',
      'stress',
      'meals',
      'eating_out',
    ])
  })

  it('수면이 들쭉날쭉하면 시각 대신 평균 시간 한 문항', () => {
    const ids = visibleQuestions({ ...SAMPLE, sleep_regular: 'no' }, 1).map((q) => q.id)
    expect(ids).toContain('sleep_avg')
    expect(ids).not.toContain('weekday_bed')
    expect(ids).not.toContain('weekend_same')
  })

  it('2단계: 비흡연·비음주자는 흡연량·음주 문항을 건너뛴다', () => {
    const ids = visibleQuestions(SAMPLE, 2).map((q) => q.id)
    expect(ids).toEqual(['smoke_100', 'drink_ever', 'veg', 'fruit', 'protein', 'dairy', 'extra'])
  })

  it('최근 1년 음주를 안 했으면 음주량 문항만 건너뛴다', () => {
    const ids = visibleQuestions({ ...SAMPLE, drink_ever: 'yes', drink_freq: 0 }, 2).map((q) => q.id)
    expect(ids).toContain('drink_freq')
    expect(ids).not.toContain('drink_amount')
  })
})
