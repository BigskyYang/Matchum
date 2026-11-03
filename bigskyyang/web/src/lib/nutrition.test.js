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
  const CELLS = {
    common: ['vitamin_d', 'calcium'],
    types: {
      N2: {
        2: {
          '30-49': {
            vitamin_d: { p: 0.96, vs: 1.0, tag: '공통주의' },
            calcium: { p: 0.71, vs: 1.0, tag: '공통주의' },
            iron: { p: 0.57, vs: 1.35, tag: '유형특이' }, // 0.5 이상 → 보임
            magnesium: { p: 0.63, vs: 1.19, tag: '식사량영향' }, // 0.5 이상 → 보임
            protein: { p: 0.34, vs: 1.36, tag: '' }, // 1.2배 이상 + 10명 중 3명 이상 → 보임
            phosphorus: { p: 0.2, vs: 1.25, tag: '' }, // 1.2배여도 하한 미만 → 안 보임
            zinc: { p: 0.45, vs: 1.1, tag: '' }, // 0.5 미만 + 1.2배 미만 → 안 보임
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

  it('1줄은 공통 영양소, 2줄은 하한 이상이면서 (0.5 이상 또는 1.2배 이상)인 것을 부족한 사람이 많은 순으로', () => {
    const { common, picks } = typeNutrients(CELLS, 'N2', 2, 35)
    expect(common.map((n) => n.key)).toEqual(['calcium', 'vitamin_d'])
    expect(picks.map((n) => [n.key, n.of10, n.level.label])).toEqual([
      ['magnesium', 6, '부족'],
      ['iron', 6, '부족'],
      ['protein', 3, '주의'],
    ])
    expect(picks.find((n) => n.key === 'iron')).toMatchObject({ label: '철', tag: '유형특이', peerOf10: 4 })
  })

  it('칸이 없으면 null', () => {
    expect(typeNutrients(CELLS, 'N2', 1, 35)).toBeNull()
    expect(typeNutrients(CELLS, 'O3', 2, 35)).toBeNull()
  })
})
