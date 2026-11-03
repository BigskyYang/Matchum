import { describe, expect, it } from 'vitest'
import { NUTRIENTS } from '../data/nutrients.js'
import { visibleQuestions } from '../data/questions.js'
import { encode } from './encode.js'
import { SAMPLE } from './fixtures.js'
import { ageGroup, lookupProfile, nutrientSignals, rankNutrients, supplementsFor } from './nutrition.js'

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

describe('영양소 신호등', () => {
  const CELLS = {
    types: {
      N2: {
        2: {
          '30-49': {
            iron: { p: 0.57, vs: 1.35, tag: '유형특이' },
            protein: { p: 0.34, vs: 1.36, tag: '' },
            zinc: { p: 0.12, vs: 0.9, tag: '' },
          },
        },
      },
    },
  }

  it('나이를 결과표의 연령대로 나눈다', () => {
    expect([19, 29, 30, 49, 50, 64, 65, 74, 75, 90].map(ageGroup)).toEqual([
      '19-29', '19-29', '30-49', '30-49', '50-64', '50-64', '65-74', '65-74', '75+', '75+',
    ])
  })

  it('내 유형·성별·연령대 칸을 찾아 부족 비율이 높은 순으로, 부족·주의·충분을 붙인다', () => {
    const items = nutrientSignals(CELLS, 'N2', 2, 35)
    expect(items.map((n) => [n.key, n.level.label])).toEqual([
      ['iron', '부족'],
      ['protein', '주의'],
      ['zinc', '충분'],
    ])
    expect(items[0]).toMatchObject({ label: '철', basis: 'EAR', tag: '유형특이', of10: 6 })
  })

  it('단계는 화면에 보이는 10명 중 N명(반올림)으로 정한다', () => {
    const cells = { types: { N2: { 2: { '30-49': { protein: { p: 0.29 }, zinc: { p: 0.24 } } } } } }
    expect(nutrientSignals(cells, 'N2', 2, 35).map((n) => [n.of10, n.level.label])).toEqual([
      [3, '주의'],
      [2, '충분'],
    ])
  })

  it('칸이 없으면 빈 목록', () => {
    expect(nutrientSignals(CELLS, 'N2', 1, 35)).toEqual([])
    expect(nutrientSignals(CELLS, 'O3', 2, 35)).toEqual([])
  })
})
