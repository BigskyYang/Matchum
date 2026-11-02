import { describe, expect, it } from 'vitest'
import { visibleQuestions } from '../data/questions.js'
import { ageFromBirth, encode, sleepHours } from './encode.js'
import { SAMPLE } from './fixtures.js'

describe('sleepHours', () => {
  it('자정을 넘기는 수면을 계산한다', () => {
    expect(sleepHours('23:30', '07:00')).toBe(7.5)
    expect(sleepHours('01:00', '07:00')).toBe(6)
  })
})

describe('ageFromBirth', () => {
  it('생일이 지나지 않았으면 한 살 적다', () => {
    const today = new Date(2026, 10, 2) // 2026-11-02
    expect(ageFromBirth('2001-03-15', today)).toBe(25)
    expect(ageFromBirth('2001-11-02', today)).toBe(25)
    expect(ageFromBirth('2001-11-03', today)).toBe(24)
  })
})

describe('encode', () => {
  it('비흡연·비음주 응답을 0으로 변환한다', () => {
    const { features } = encode(SAMPLE)
    expect(features.ML_smoker).toBe(0)
    expect(features.ML_cigarettes_day).toBe(0)
    expect(features.ML_drink_month).toBe(0)
    expect(features.ML_drink_freq_ord).toBe(0)
    expect(features.ML_drink_amount_ord).toBe(0)
  })

  it('유산소 기준은 중강도 + 고강도×2 ≥ 150분', () => {
    expect(encode(SAMPLE).features.ML_aerobic).toBe(0) // 60 + 60 = 120
    expect(encode({ ...SAMPLE, vigorous_min: 45 }).features.ML_aerobic).toBe(1) // 60 + 90 = 150
  })

  it('평균 수면 = (주중×5 + 주말×2) / 7', () => {
    expect(encode(SAMPLE).features.ML_sleep_hours).toBeCloseTo((6 * 5 + 8 * 2) / 7)
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
  it('비흡연·비음주자는 흡연량·음주 문항을 건너뛴다', () => {
    const ids = visibleQuestions(SAMPLE).map((q) => q.id)
    expect(ids).not.toContain('smoke_now')
    expect(ids).not.toContain('cigarettes')
    expect(ids).not.toContain('drink_freq')
    expect(ids).toHaveLength(22) // 26문항 - 흡연 2 - 음주 2
  })

  it('최근 1년 음주를 안 했으면 음주량 문항만 건너뛴다', () => {
    const ids = visibleQuestions({ ...SAMPLE, drink_ever: 'yes', drink_freq: 0 }).map((q) => q.id)
    expect(ids).toContain('drink_freq')
    expect(ids).not.toContain('drink_amount')
  })
})
