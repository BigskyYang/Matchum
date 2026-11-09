import { describe, expect, it } from 'vitest'
import { encode } from './encode.js'
import { MAIN_CODES, classify, mainProfile, model, typeOf } from './classify.js'
import { SAMPLE } from './fixtures.js'
import CASES from './classify.fixtures.json'

// 예시 응답과 정답은 scripts/make_classify_fixtures.py가 Python으로 계산한 것이다.
// 웹 판정이 분석 쪽 계산(분석 결과 15,062명과 100% 일치)과 같은 답을 내는지 확인한다.
describe('classify', () => {
  it.each(CASES.map((c) => [c.leaf, c]))('%s 예시 응답이 같은 유형으로 판정된다', (_, c) => {
    expect(classify(c.features)).toEqual({ main: c.main, leaf: c.leaf })
  })

  it('예시 응답에 12개 유형이 모두 있다', () => {
    expect(new Set(CASES.map((c) => c.leaf)).size).toBe(model.types.length)
  })

  it('설문 응답 → 변수 변환 → 유형 판정까지 이어진다', () => {
    const { main, leaf } = classify(encode(SAMPLE).features)
    expect(MAIN_CODES).toContain(main)
    expect(leaf[0]).toBe(main)
    expect(typeOf(leaf)).toBeDefined()
  })

  it('범위를 벗어난 응답도 학습 자료 범위로 잘라서 판정한다', () => {
    const base = CASES[0].features
    expect(classify({ ...base, ML_sedentary_min: 5000 })).toEqual(classify({ ...base, ML_sedentary_min: 1200 }))
  })
})

describe('mainProfile', () => {
  it('대분류 평균은 세부 유형 평균 사이에 있다', () => {
    for (const code of MAIN_CODES) {
      const subs = model.types.filter((t) => t.id[0] === code).map((t) => t.profile.sedentary_min)
      const v = mainProfile(code).sedentary_min
      expect(v).toBeGreaterThanOrEqual(Math.min(...subs))
      expect(v).toBeLessThanOrEqual(Math.max(...subs))
    }
  })
})
