import { describe, expect, it } from 'vitest'
import models from '../data/nutritionModels.json'
import fixtures from './nutritionModels.fixtures.json'
import rawExample from '../../../analysis/03_personal_prediction/model/examples/example_raw_survey_response.json'
import expectedFeatures from '../../../analysis/03_personal_prediction/model/examples/expected_example_model_features.json'
import exampleResponse from '../../../analysis/03_personal_prediction/model/examples/example_response.json'
import { encode } from './encode.js'
import { SAMPLE, bornAt } from './fixtures.js'
import { habitualFeatures, lifestyleFeatures, predictNutrition, probability } from './nutritionRisk.js'
import { buildPersonalResult } from './result.js'

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

  it('평소 식사 모델은 19~64세만, 등급은 낮음·보통·높음', () => {
    const { features, extras } = encode(SAMPLE)
    const r = predictNutrition(models, lifestyleFeatures(SAMPLE, features), habitualFeatures(extras))
    for (const x of [...Object.values(r.lifestyle), ...Object.values(r.habitual)]) expect(['Low', 'Mid', 'High']).toContain(x.band)
    expect(habitualFeatures({ ...extras, age: 65 })).toBeNull()
    expect(habitualFeatures({ ...extras, ffq: null })).toBeNull()
  })

  // 재준님 v1.4.1 예시 응답(examples/example_raw_survey_response.json)을 웹 설문 보기로 답한 것
  // 기대값: 재준님 파이프라인이 만든 모델 입력(expected_example_model_features.json)과 결과(example_response.json)
  const EXAMPLE = {
    sex: 2, // 여성
    birth_date: bornAt(35), // 만 35세
    activity: 3, // aerobic_150min: true
    strength_days: 1,
    sedentary_min: 600, // 10시간 0분
    weekday_bed: '00:00',
    weekday_wake: '07:30',
    weekend_same: 'no',
    weekend_bed: '01:00',
    weekend_wake: '09:00',
    stress: 1, // 대단히 많이 느낀다
    meals: { breakfast: 3, lunch: 3, dinner: 3 }, // 주 5~7회
    eating_out: 2, // 주 1~2회
    smoke_now: 'no', // currently_smoking: false
    drink_freq: 1, // 월 1회 미만
    drink_amount: 1, // 1~2잔
    veg: 8, // 하루 3회 이상
    fruit: 3, // 주 1회
    ffq_meat: 3, // 주 3~4회
    ffq_fish: 2, // 주 1~2회
    ffq_egg: 3,
    ffq_legume: 3,
    ffq_dairy: 5, // 하루 1회
  }

  it('재준님 예시는 팀 합의 형식 (현재 흡연 예·아니요, 유산소 150분 여부, 규칙적 수면, 만 나이)', () => {
    expect(rawExample).toMatchObject({ age: 35, currently_smoking: false, aerobic_150min: true, regular_sleep_schedule: true })
  })

  it('재준님 예시 응답을 웹 설문으로 답하면 모델 입력 18개가 재준님 파이프라인과 같다', () => {
    const row = lifestyleFeatures(EXAMPLE, encode(EXAMPLE).features)
    expect(Object.keys(row).sort()).toEqual(Object.keys(expectedFeatures).sort())
    for (const [k, v] of Object.entries(expectedFeatures)) expect(row[k], k).toBeCloseTo(v, 12)
  })

  it('확률·등급이 재준님 결과(example_response.json)와 같다', () => {
    const { features, extras } = encode(EXAMPLE)
    const r = predictNutrition(models, lifestyleFeatures(EXAMPLE, features), habitualFeatures(extras))
    const expected = { lifestyle: exampleResponse.nutrition.lifestyle_risk, habitual: exampleResponse.nutrition.habitual_diet_risk }
    for (const [mod, list] of Object.entries(expected)) {
      expect(Object.keys(r[mod]).sort()).toEqual(Object.keys(list).sort())
      for (const [n, x] of Object.entries(list)) {
        expect(Math.abs(r[mod][n].probability - x.probability), `${mod} ${n}`).toBeLessThan(1e-8)
        expect(r[mod][n].band, `${mod} ${n}`).toBe(x.risk_band)
      }
    }
  })

  it('화면 대표 등급은 재준님 display_summary와 같다 (평소 식사 우선, 엇갈림 표시)', () => {
    const { watch, rest } = buildPersonalResult(EXAMPLE, models).nutrition
    const summary = exampleResponse.display_summary.nutrients
    const rows = [...watch, ...rest]
    expect(rows.map((n) => n.key).sort()).toEqual(Object.keys(summary).sort())
    for (const n of rows) {
      const s = summary[n.key]
      expect([n.band, n.source, n.differ], n.key).toEqual([s.risk_band, s.display_source === 'habitual_diet' ? 'habitual' : 'lifestyle', s.signals_differ])
    }
  })
})
