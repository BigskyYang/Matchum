// 데이터 파일끼리, 그리고 팀원 설문·모델 정의와 웹이 서로 맞는지 점검한다.
// 군집화를 다시 돌리거나 설문(Jaejun/config)이 바뀌었는데 웹을 안 맞췄으면 여기서 실패한다.
import { existsSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import targets from '../../../../Jaejun/config/targets.json'
import surveySchema from '../../../../Jaejun/config/survey_schema_v3.json'
import nutrientCells from '../data/nutrientCells.json'
import { NUTRIENT_GUIDE } from '../data/nutrientGuide.js'
import { NUTRIENTS } from '../data/nutrients.js'
import { QUESTIONS } from '../data/questions.js'
import { LEAF_TYPES, MAIN_TYPES } from '../data/types.js'
import { MAIN_CODES, model } from './classify.js'

const mainIds = MAIN_CODES
const leafIds = model.types.map((t) => t.id)

describe('군집 모델 ↔ 유형 설명 (types.js) ↔ 마스코트 그림', () => {
  it('대분류 유형마다 이름·이모지·설명이 있다', () => {
    expect(Object.keys(MAIN_TYPES).sort()).toEqual([...mainIds].sort())
    for (const id of mainIds) {
      expect(MAIN_TYPES[id]).toMatchObject({ name: expect.any(String), emoji: expect.any(String), summary: expect.any(String) })
    }
  })

  it('세부 유형마다 이름·설명이 있다', () => {
    expect(Object.keys(LEAF_TYPES).sort()).toEqual([...leafIds].sort())
    for (const id of leafIds) {
      expect(LEAF_TYPES[id]).toMatchObject({ name: expect.any(String), summary: expect.any(String) })
    }
  })

  it('세부 유형마다 마스코트 그림(png·webp)이 있다', () => {
    const missing = leafIds.flatMap((id) =>
      ['png', 'webp'].map((ext) => `type_${id}.${ext}`).filter((f) => !existsSync(new URL(`../../public/mascot/${f}`, import.meta.url))),
    )
    expect(missing).toEqual([])
  })
})

describe('개인화용 영양소 정의 (nutrients.js) ↔ 재준 모델 (Jaejun/config/targets.json)', () => {
  it('14개 영양소 키가 같다', () => {
    expect(NUTRIENTS.map((n) => n.key).sort()).toEqual(Object.keys(targets).sort())
  })
})

describe('부족할 수 있는 영양소 결과표 (nutrientCells.json, 유환님 (나)안 결과)', () => {
  const guideKeys = NUTRIENT_GUIDE.map((n) => n.key)
  const cells = Object.values(nutrientCells.types).flatMap((sexes) => Object.values(sexes).flatMap((ages) => Object.values(ages)))

  it('지금 군집 모델과 같은 유형 ID를 쓴다', () => {
    expect(Object.keys(nutrientCells.types).sort()).toEqual([...leafIds].sort())
    expect(nutrientCells.source_types).toBe(model.version)
  })

  it('유형마다 성별 2 × 연령대 5칸이 있다', () => {
    for (const sexes of Object.values(nutrientCells.types)) {
      expect(Object.keys(sexes).sort()).toEqual(['1', '2'])
      for (const ages of Object.values(sexes)) {
        expect(Object.keys(ages).sort()).toEqual(['19-29', '30-49', '50-64', '65-74', '75+'])
      }
    }
  })

  it('1줄은 모든 칸에서 같은 공통 영양소 8개, 2줄은 1줄과 겹치지 않는다', () => {
    const common = [...cells[0].line1.map((x) => x.key)].sort()
    expect(common).toHaveLength(8)
    for (const cell of cells) {
      expect(cell.line1.map((x) => x.key).sort()).toEqual(common)
      expect(cell.line2.filter((x) => common.includes(x.key))).toEqual([])
    }
  })

  it('영양소는 모두 영양소 안내(nutrientGuide.js)에 있고, 10명 중 몇 명은 0~10이다', () => {
    for (const x of cells.flatMap((c) => [...c.line1, ...c.line2])) {
      expect(guideKeys).toContain(x.key)
      expect(x.of10).toBeGreaterThanOrEqual(0)
      expect(x.of10).toBeLessThanOrEqual(10)
    }
    for (const x of cells.flatMap((c) => c.line2)) {
      expect(x.text).toEqual(expect.any(String))
      expect(x.peerOf10).toBeLessThanOrEqual(10)
    }
  })
})

// 설문 v3 문항 ID ↔ 웹 문항 ID
//   문자열: 같은 문항 / { merged: 웹 문항 }: 웹에서 다른 문항과 합침 / { removed: 이유 }: 웹에서 뺌
const SCHEMA_TO_WEB = {
  Q1: 'sex',
  Q2: { merged: 'birth_year' }, // v3는 만 나이, 웹은 출생연도
  Q3: { merged: 'smoke_now' }, // '평생 100개비'를 먼저 묻지 않고 지금 흡연 상태만 (모델은 현재 흡연만 쓴다)
  Q4: { merged: 'smoke_now' }, // 보기에 '피운 적 없어요'를 더함
  Q5: 'cigarettes',
  Q6: { merged: 'drink_freq' }, // '평생 1잔'을 먼저 묻지 않고 빈도에 '최근 1년 안 마셨어요'
  Q7: 'drink_freq',
  Q8: 'drink_amount',
  Q9: { merged: 'activity' }, // 중강도·고강도 시간 → 주 150분 이상인지 한 문항 (모델은 그것만 쓴다)
  Q10: { merged: 'activity' },
  Q11: 'strength_days',
  Q12: 'sedentary_min',
  Q13: 'weekday_bed',
  Q14: 'weekday_wake',
  Q15: 'weekend_bed',
  Q16: 'weekend_wake',
  Q17: { removed: '교대근무는 모델 입력이 아님. 수면이 들쭉날쭉한지(sleep_regular) 묻고 미션으로 안내' },
  Q18: 'stress',
  Q19: { merged: 'meals' }, // 아침·점심·저녁을 한 화면에서
  Q20: { merged: 'meals' },
  Q21: { merged: 'meals' },
  Q22: 'eating_out',
  Q23: 'veg',
  Q24: 'fruit',
  Q25: { removed: '재준님 최종 설문(SURVEY_FINAL)의 mini-FFQ 5문항(ffq_meat … ffq_dairy)으로 바꿈' },
  Q26: { removed: '재준님 최종 설문(SURVEY_FINAL)의 mini-FFQ 5문항으로 바꿈' },
  ...Object.fromEntries(Array.from({ length: 9 }, (_, i) => [`Q${27 + i}`, `phq${i + 1}`])),
  Q36: { merged: 'health' }, // 대사질환 3문항 + 안전 문항을 '해당하는 것 모두 고르기' 한 화면으로
  Q37: { merged: 'health' },
  Q38: { merged: 'health' },
}

describe('설문 문항 ↔ 설문 v3 (Jaejun/config/survey_schema_v3.json)', () => {
  const schemaQuestions = surveySchema.sections.flatMap((s) => s.questions)
  const web = Object.fromEntries(QUESTIONS.map((q) => [q.id, q]))
  const webId = (m) => (typeof m === 'string' ? m : m?.merged)

  it('v3의 모든 문항이 웹에 있거나, 합치거나 뺀 이유가 적혀 있다 (새 문항이 생기면 여기서 알려준다)', () => {
    const missing = schemaQuestions
      .filter((q) => {
        const m = SCHEMA_TO_WEB[q.id]
        return !m || (!m.removed && !web[webId(m)])
      })
      .map((q) => `${q.id} ${q.text}`)
    expect(missing).toEqual([])
  })

  it('그대로 옮긴 보기 문항은 보기 개수가 v3와 같다', () => {
    const mismatched = schemaQuestions
      .filter((q) => q.type === 'choice' && typeof SCHEMA_TO_WEB[q.id] === 'string')
      .map((q) => ({ id: q.id, text: q.text, v3: q.options.length, web: web[SCHEMA_TO_WEB[q.id]]?.options?.length }))
      .filter((q) => q.v3 !== q.web)
    expect(mismatched).toEqual([])
  })

  it('세 끼는 v3와 같은 보기 수로 한 화면에서 묻는다', () => {
    const meal = schemaQuestions.find((q) => q.id === 'Q19')
    expect(web.meals.options).toHaveLength(meal.options.length)
  })
})

// 재준님 최종 설문(Jaejun/SURVEY_FINAL.md)의 mini-FFQ·안전 문항 ↔ 웹
describe('설문 ↔ 재준님 최종 설문 (mini-FFQ·안전 문항)', () => {
  const web = Object.fromEntries(QUESTIONS.map((q) => [q.id, q]))

  it('mini-FFQ 5문항, 보기 8단계 0~7 (Jaejun/src/mini_ffq.py FOOD_FREQ_ORD)', () => {
    for (const id of ['ffq_meat', 'ffq_fish', 'ffq_egg', 'ffq_legume', 'ffq_dairy']) {
      expect(web[id].options.map((o) => o.value)).toEqual([0, 1, 2, 3, 4, 5, 6, 7])
    }
  })

  it('안전 문항 4가지(영양제·임신수유·항응고제·신장질환)가 있다 (Jaejun/config/supplement_safety_rules.json)', () => {
    expect(web.supplements).toBeDefined()
    expect(web.health.options.map((o) => o.value)).toEqual(expect.arrayContaining(['pregnant', 'anticoagulant', 'kidney']))
  })
})
