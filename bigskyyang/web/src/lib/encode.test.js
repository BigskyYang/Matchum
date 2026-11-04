import { describe, expect, it } from 'vitest'
import { QUESTIONS, optionsFor, visibleQuestions } from '../data/questions.js'
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

  it('현재 흡연자·음주자 (요즘 가끔 피움 = 현재 흡연)', () => {
    const { features } = encode({ ...SAMPLE, smoke_now: 'sometimes', cigarettes: 5, drink_freq: 1, drink_amount: 2 })
    expect(features.ML_smoker).toBe(1)
    expect(features.ML_cigarettes_day).toBe(5)
    expect(features.ML_drink_month).toBe(0) // 월 1회 미만
    expect(features.ML_drink_amount_ord).toBe(2)
  })

  it('끊었으면 비흡연, 예전에 답한 개비 수는 무시', () => {
    const { features } = encode({ ...SAMPLE, smoke_now: 'past', cigarettes: 20 })
    expect(features.ML_smoker).toBe(0)
    expect(features.ML_cigarettes_day).toBe(0)
  })

  it('mini-FFQ 5문항은 재준님 모델 입력(0~7)으로, 하나라도 없으면 null', () => {
    expect(encode(SAMPLE).extras.ffq).toEqual({ meat: 3, fish: 2, egg: 3, legume: 2, dairy: 2 })
    expect(encode({ ...SAMPLE, ffq_dairy: undefined }).extras.ffq).toBeNull()
  })

  it('건강 상태·영양제 여러 개 고르기', () => {
    const { extras } = encode({ ...SAMPLE, health: ['kidney', 'hypertension'], supplements: ['vitamin_d', 'omega3'] })
    expect(extras.health).toMatchObject({ kidney: true, hypertension: true, pregnant: false, diabetes: false })
    expect(extras.supplements).toEqual(['vitamin_d', 'omega3'])
    expect(encode(SAMPLE).extras.supplements).toEqual([])
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

  it('2단계: 비흡연·최근 1년 비음주자는 흡연량·음주량 문항을 건너뛴다', () => {
    const ids = visibleQuestions(SAMPLE, 2).map((q) => q.id)
    expect(ids).toEqual([
      'smoke_now',
      'drink_freq',
      'veg',
      'fruit',
      'ffq_meat',
      'ffq_fish',
      'ffq_egg',
      'ffq_legume',
      'ffq_dairy',
      'health',
      'supplements',
      'extra',
    ])
  })

  it('흡연자·음주자는 개비 수·음주량을 묻는다', () => {
    const ids = visibleQuestions({ ...SAMPLE, smoke_now: 'daily', drink_freq: 3 }, 2).map((q) => q.id)
    expect(ids).toContain('cigarettes')
    expect(ids).toContain('drink_amount')
  })

  it('65세 이상은 mini-FFQ를 묻지 않는다 (19~64세에서만 검증된 모델)', () => {
    const year = new Date().getFullYear()
    const ids = visibleQuestions({ ...SAMPLE, birth_year: year - 70 }, 2).map((q) => q.id)
    expect(ids.filter((id) => id.startsWith('ffq_'))).toEqual([])
    expect(visibleQuestions({ ...SAMPLE, birth_year: year - 64 }, 2).map((q) => q.id)).toContain('ffq_meat')
  })
})

describe('optionsFor', () => {
  const health = QUESTIONS.find((q) => q.id === 'health')
  const year = new Date().getFullYear()

  it('임신·수유 보기는 19~49세 여성에게만', () => {
    expect(optionsFor(health, { sex: 2, birth_year: year - 30 }).map((o) => o.value)).toContain('pregnant')
    expect(optionsFor(health, { sex: 1, birth_year: year - 30 }).map((o) => o.value)).not.toContain('pregnant')
    expect(optionsFor(health, { sex: 2, birth_year: year - 55 }).map((o) => o.value)).not.toContain('pregnant')
  })
})
