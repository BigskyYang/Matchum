import { describe, expect, it } from 'vitest'
import { visibleQuestions } from '../data/questions.js'
import { ageFromBirth, encode, sleepHours } from './encode.js'
import { SAMPLE, STAGE1_SAMPLE, bornAt } from './fixtures.js'

describe('sleepHours', () => {
  it('자정을 넘기는 수면을 계산한다', () => {
    expect(sleepHours('23:30', '07:00')).toBe(7.5)
    expect(sleepHours('01:00', '07:00')).toBe(6)
  })
})

describe('ageFromBirth (만 나이)', () => {
  const today = new Date(2026, 10, 4) // 2026-11-04
  it('올해 생일이 지났으면 올해 - 태어난 해, 아직이면 한 살 적게', () => {
    expect(ageFromBirth('2001-03-15', today)).toBe(25)
    expect(ageFromBirth('2001-11-04', today)).toBe(25) // 생일 당일
    expect(ageFromBirth('2001-11-05', today)).toBe(24)
    expect(ageFromBirth('2001-12-31', today)).toBe(24)
  })

  it('2월 29일생은 평년에는 3월 1일에 한 살', () => {
    expect(ageFromBirth('2004-02-29', new Date(2026, 1, 28))).toBe(21)
    expect(ageFromBirth('2004-02-29', new Date(2026, 2, 1))).toBe(22)
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
    expect(extras.age).toBe(ageFromBirth(SAMPLE.birth_date))
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

  it('흡연: 피운다고 답하면 1 (궐련·전자담배 구분 없음), 개비 수는 피우는 사람만', () => {
    const smoker = encode({ ...SAMPLE, smoke_now: 'yes', cigarettes: 5 }).features
    expect([smoker.ML_smoker, smoker.ML_cigarettes_day]).toEqual([1, 5])
    const quit = encode({ ...SAMPLE, smoke_now: 'no', cigarettes: 20 }).features
    expect([quit.ML_smoker, quit.ML_cigarettes_day]).toEqual([0, 0])
  })

  it('스트레스 1·2 → 1', () => {
    expect(encode(SAMPLE).features.ML_stress).toBe(1)
  })
})

describe('visibleQuestions', () => {
  it('1단계는 유형 분류 문항만, 주말이 다르면 수면 시각 4개', () => {
    const ids = visibleQuestions(SAMPLE, 1).map((q) => q.id)
    expect(ids).toEqual([
      'sex',
      'birth_date',
      'activity',
      'strength_days',
      'sedentary_min',
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

  it('주말도 비슷하면 주말 시각은 묻지 않는다', () => {
    const ids = visibleQuestions({ ...SAMPLE, weekend_same: 'yes' }, 1).map((q) => q.id)
    expect(ids).not.toContain('weekend_bed')
    expect(ids).not.toContain('weekend_wake')
  })

  it('만 19세 미만 생년월일은 다음으로 넘어갈 수 없다', () => {
    const q = visibleQuestions(SAMPLE, 1).find((x) => x.id === 'birth_date')
    expect(q.check(bornAt(19))).toBeNull()
    expect(q.check(bornAt(18))).toMatch(/19세/)
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
      'vitd_commute',
      'vitd_lunch_outing',
      'vitd_exercise_setting',
      'vitd_day_off_outing',
    ])
  })

  it('흡연자·음주자는 개비 수·음주량을 묻는다', () => {
    const ids = visibleQuestions({ ...SAMPLE, smoke_now: 'yes', drink_freq: 3 }, 2).map((q) => q.id)
    expect(ids).toContain('cigarettes')
    expect(ids).toContain('drink_amount')
  })

  it('만 65세 이상은 mini-FFQ를 묻지 않는다 (19~64세에서만 검증된 모델)', () => {
    const ids = visibleQuestions({ ...SAMPLE, birth_date: bornAt(65) }, 2).map((q) => q.id)
    expect(ids.filter((id) => id.startsWith('ffq_'))).toEqual([])
    expect(visibleQuestions({ ...SAMPLE, birth_date: bornAt(64) }, 2).map((q) => q.id)).toContain('ffq_meat')
  })
})
