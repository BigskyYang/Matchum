import { describe, expect, it } from 'vitest'
import { ageGroup, typeNutrients } from './nutrition.js'

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
