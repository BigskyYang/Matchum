import { describe, expect, it } from 'vitest'
import { NUTRIENTS } from '../data/nutrients.js'
import { visibleQuestions } from '../data/questions.js'
import { encode } from './encode.js'
import { SAMPLE } from './fixtures.js'
import { lookupProfile, rankNutrients, supplementsFor } from './nutrition.js'

// 결과표 형식 예시 (scripts/build_nutrient_profiles.py가 만드는 형식과 같다)
const PROFILES = {
  types: {
    Group_1: {
      n: 100,
      nutrients: {
        calcium: { rate: 0.9, band: 'High' },
        vitamin_c: { rate: 0.8, band: 'High' },
        potassium: { rate: 0.95, band: 'High' },
        protein: { rate: 0.1, band: 'Mid' },
        iron: { rate: 0.02, band: 'Low' },
      },
    },
    'Group_1-1_A': { n: 30, nutrients: { zinc: { rate: 0.4, band: 'High' } } },
  },
}

describe('lookupProfile', () => {
  it('세부 유형이 있으면 세부 유형, 없으면 대분류 값을 쓴다', () => {
    expect(lookupProfile(PROFILES, 'Group_1-1_A', 'Group_1').label).toBe('Group_1-1_A')
    expect(lookupProfile(PROFILES, 'Group_1-0_B', 'Group_1').label).toBe('Group_1')
    expect(lookupProfile(PROFILES, 'Group_2-0', 'Group_2')).toBeNull()
    expect(lookupProfile({ types: {} }, 'Group_1-0_B', 'Group_1')).toBeNull()
  })
})

describe('rankNutrients', () => {
  const ranked = rankNutrients(lookupProfile(PROFILES, 'Group_1-0_B', 'Group_1'))

  it('주의 → 보통 → 양호, 같은 등급은 비율 높은 순', () => {
    expect(ranked.map((n) => n.key)).toEqual(['potassium', 'calcium', 'vitamin_c', 'protein', 'iron'])
  })

  it('예측 정확도가 낮은 영양소는 참고로 표시한다', () => {
    expect(ranked.find((n) => n.key === 'vitamin_c').reliable).toBe(false)
    expect(ranked.find((n) => n.key === 'calcium').reliable).toBe(true)
  })

  it('건강기능식품 원료는 주의 등급이면서 원료가 있는 영양소만 (칼륨은 음식으로만)', () => {
    expect(supplementsFor(ranked)).toEqual(['칼슘', '비타민 C'])
  })

  it('영양소 정보는 Jaejun 모델의 14개와 같다', () => {
    expect(NUTRIENTS).toHaveLength(14)
  })
})

describe('선택 문항 (PHQ-9·대사건강)', () => {
  it('결과 바로 보기를 고르면 선택 문항이 나오지 않고 optional은 null', () => {
    const ids = visibleQuestions({ ...SAMPLE, extra: 'skip' }).map((q) => q.id)
    expect(ids).not.toContain('phq1')
    expect(encode({ ...SAMPLE, extra: 'skip' }).extras.optional).toBeNull()
  })

  it('추가 질문을 고르면 PHQ-9 9문항 + 대사건강 3문항이 나온다', () => {
    const ids = visibleQuestions({ ...SAMPLE, extra: 'more' }).map((q) => q.id)
    expect(ids.filter((id) => id.startsWith('phq'))).toHaveLength(9)
    expect(ids.filter((id) => id.startsWith('dx_'))).toHaveLength(3)
  })

  it('PHQ-9 총점과 9번 문항, 진단 여부를 정리한다', () => {
    const phq = Object.fromEntries(Array.from({ length: 9 }, (_, i) => [`phq${i + 1}`, i === 8 ? 1 : 2]))
    const { optional } = encode({ ...SAMPLE, extra: 'more', ...phq, dx_hypertension: 'yes', dx_diabetes: 'no', dx_dyslipidemia: 'no' })
      .extras
    expect(optional.phqTotal).toBe(17)
    expect(optional.phqItem9).toBe(1)
    expect(optional.hypertension).toBe(true)
    expect(optional.diabetes).toBe(false)
  })
})
