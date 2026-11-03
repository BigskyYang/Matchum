import { describe, expect, it } from 'vitest'
import { visibleQuestions } from '../data/questions.js'
import { encode } from './encode.js'
import { SAMPLE } from './fixtures.js'
import { ageGroup, typeNutrients } from './nutrition.js'

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

describe('부족할 수 있는 영양소 ((나)안)', () => {
  // 유환님 결과 형식 예시 (scripts/build_nutrient_cells.py가 만드는 형식)
  const CELLS = {
    types: {
      N2: {
        2: {
          '30-49': {
            line1: [
              { key: 'vitamin_d', of10: 10 },
              { key: 'calcium', of10: 7 },
            ],
            line2: [
              { key: 'iron', of10: 6, peerOf10: 4, text: '이 유형에서 특히 많아요' },
              { key: 'zinc', of10: 4, peerOf10: 3, text: '식사량 점검이 먼저예요' },
            ],
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

  it('내 유형·성별·연령대 칸의 1줄·2줄을 순서 그대로 가져오고 영양소 이름·역할을 붙인다', () => {
    const { common, picks } = typeNutrients(CELLS, 'N2', 2, 35)
    expect(common.map((n) => [n.label, n.of10])).toEqual([
      ['비타민 D', 10],
      ['칼슘', 7],
    ])
    expect(picks.map((n) => [n.label, n.of10, n.peerOf10, n.level.label])).toEqual([
      ['철', 6, 4, '부족'],
      ['아연', 4, 3, '주의'],
    ])
    expect(picks[0]).toMatchObject({ basis: 'EAR', text: '이 유형에서 특히 많아요', role: expect.any(String) })
  })

  it('칸이 없으면 null', () => {
    expect(typeNutrients(CELLS, 'N2', 1, 35)).toBeNull()
    expect(typeNutrients(CELLS, 'O3', 2, 35)).toBeNull()
  })
})
