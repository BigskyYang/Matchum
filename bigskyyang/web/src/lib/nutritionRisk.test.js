import { describe, expect, it } from 'vitest'
import models from '../data/nutritionModels.json'
import fixtures from './nutritionModels.fixtures.json'
import { encode } from './encode.js'
import { SAMPLE } from './fixtures.js'
import { habitualFeatures, lifestyleFeatures, predictNutrition, probability } from './nutritionRisk.js'

// 재준님 모델을 웹에서 계산한 값 = 파이썬(scikit-learn 1.8.0) predict_proba (scripts/export_nutrition_models.py가 만든 예시)
describe('개인 영양 위험 예측 (재준님 v1.4 모델)', () => {
  for (const module of ['lifestyle', 'habitual']) {
    it(`${module}: 예시 ${fixtures[module].rows.length}명의 확률이 파이썬과 같다`, () => {
      const { features, models: ms } = models[module]
      for (const [n, expected] of Object.entries(fixtures[module].probability)) {
        fixtures[module].rows.forEach((row, i) => {
          expect(Math.abs(probability(ms[n], features.map((f) => row[f])) - expected[i])).toBeLessThan(1e-8)
        })
      }
    })
  }

  it('생활습관 14개·평소 식사 10개 영양소, 입력 키가 재준님 계약과 같다', () => {
    expect(Object.keys(models.lifestyle.models)).toHaveLength(14)
    expect(Object.keys(models.habitual.models)).toHaveLength(10)
    const { features, extras } = encode(SAMPLE)
    expect(Object.keys(lifestyleFeatures(SAMPLE, features)).sort()).toEqual([...models.lifestyle.features].sort())
    expect(Object.keys(habitualFeatures(extras)).sort()).toEqual([...models.habitual.features].sort())
  })

  it('채소·과일은 모델 척도(1 = 하루 3회 이상 … 9 = 거의 안 함)로', () => {
    const { features } = encode(SAMPLE)
    const row = lifestyleFeatures({ ...SAMPLE, veg: 8, fruit: 0 }, features)
    expect(row.식습관_LS_VEG2).toBe(1)
    expect(row.식습관_LS_FRUIT).toBe(9)
  })

  it('수면을 평균 시간으로 답했으면 그 시간 그대로 (군집 모델용 척도 변환 없이)', () => {
    const a = { ...SAMPLE, sleep_regular: 'no', sleep_avg: 390 }
    expect(lifestyleFeatures(a, encode(a).features).ML_sleep_hours).toBe(6.5)
  })

  it('평소 식사 모델은 19~64세만, 등급은 낮음·보통·높음', () => {
    const { features, extras } = encode(SAMPLE)
    const r = predictNutrition(models, lifestyleFeatures(SAMPLE, features), habitualFeatures(extras))
    for (const x of [...Object.values(r.lifestyle), ...Object.values(r.habitual)]) expect(['Low', 'Mid', 'High']).toContain(x.band)
    expect(habitualFeatures({ ...extras, age: 65 })).toBeNull()
    expect(habitualFeatures({ ...extras, ffq: null })).toBeNull()
  })

  // Jaejun/nutrition_final_feedback_applied/examples/example_raw_survey_response.json을 웹 설문 보기로 답한 것
  // 기대값: 재준님 predict_from_survey_web(그 예시) 실행 결과 (scikit-learn 1.8.0)
  it('재준님 예시 응답을 웹 설문으로 답하면 재준님 파이프라인과 같은 입력·결과', () => {
    const a = {
      sex: 2,
      birth_year: new Date().getFullYear() - 35,
      activity: 3, // 중강도 6시간 40분 + 고강도 1시간 40분 → 주 150분 이상
      strength_days: 1,
      sedentary_min: 600,
      sleep_regular: 'yes',
      weekday_bed: '00:00',
      weekday_wake: '07:30',
      weekend_same: 'no',
      weekend_bed: '01:00',
      weekend_wake: '09:00',
      stress: 1,
      meals: { breakfast: 3, lunch: 3, dinner: 3 },
      eating_out: 2,
      smoke_now: 'never',
      drink_freq: 1,
      drink_amount: 1,
      veg: 8,
      fruit: 3,
      ffq_meat: 3,
      ffq_fish: 2,
      ffq_egg: 3,
      ffq_legume: 3,
      ffq_dairy: 5,
    }
    const { features, extras } = encode(a)
    const row = lifestyleFeatures(a, features)
    expect(row).toMatchObject({
      설명_sex: 2,
      설명_age: 35,
      ML_drink_month: 0,
      ML_drink_freq_ord: 1,
      ML_drink_amount_ord: 1,
      ML_aerobic: 1,
      ML_sedentary_min: 600,
      ML_stress: 1,
      ML_breakfast_freq_ord: 3,
      ML_eatingout_freq_ord: 2,
      식습관_LS_FRUIT: 6,
      식습관_LS_VEG2: 1,
    })
    expect(row.ML_sleep_hours).toBeCloseTo(7.642857142857143, 12)

    const r = predictNutrition(models, row, habitualFeatures(extras))
    const LIFESTYLE = {
      calcium: [0.59572, 'Low'],
      fiber: [0.623514, 'Mid'],
      folate: [0.685072, 'High'],
      iron: [0.369778, 'High'],
      magnesium: [0.474131, 'Mid'],
      phosphorus: [0.085232, 'Mid'],
      potassium: [0.898583, 'High'],
      protein: [0.154238, 'Low'],
      sodium_excess: [0.660753, 'Mid'],
      vitamin_a: [0.725182, 'Mid'],
      vitamin_b1: [0.511872, 'Mid'],
      vitamin_b2: [0.242578, 'Low'],
      vitamin_c: [0.782329, 'High'],
      zinc: [0.310304, 'Mid'],
    }
    const HABITUAL = {
      protein: [0.025376, 'Low'],
      calcium: [0.39248, 'Low'],
      iron: [0.009459, 'Mid'],
      phosphorus: [0.007591, 'Low'],
      vitamin_b1: [0.006382, 'Low'],
      vitamin_b2: [0.057363, 'Low'],
      vitamin_c: [0.206556, 'Low'],
      fiber: [0.508849, 'Low'],
      potassium: [0.735731, 'Low'],
      sodium_excess: [0.876742, 'High'],
    }
    for (const [mod, expected] of [['lifestyle', LIFESTYLE], ['habitual', HABITUAL]]) {
      for (const [n, [p, band]] of Object.entries(expected)) {
        expect(r[mod][n].probability).toBeCloseTo(p, 6)
        expect(r[mod][n].band).toBe(band)
      }
    }
  })
})
