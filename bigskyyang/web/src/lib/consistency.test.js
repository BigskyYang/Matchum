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

describe('부족할 수 있는 영양소 결과표 (nutrientCells.json, 유환님 12유형 결과)', () => {
  it('지금 군집 모델과 같은 유형 ID를 쓴다', () => {
    expect(Object.keys(nutrientCells.types).sort()).toEqual([...leafIds].sort())
    expect(nutrientCells.source_types).toBe(model.version)
  })

  it('공통 영양소 8개가 모두 영양소 안내(nutrientGuide.js)에 있다', () => {
    expect(nutrientCells.common).toHaveLength(8)
    expect(nutrientCells.common.filter((k) => !NUTRIENT_GUIDE.some((n) => n.key === k))).toEqual([])
  })

  it('유형마다 성별 2 × 연령대 5칸이 있고, 칸마다 영양소 15개가 모두 있다', () => {
    const keys = NUTRIENT_GUIDE.map((n) => n.key).sort()
    for (const sexes of Object.values(nutrientCells.types)) {
      expect(Object.keys(sexes).sort()).toEqual(['1', '2'])
      for (const ages of Object.values(sexes)) {
        expect(Object.keys(ages).sort()).toEqual(['19-29', '30-49', '50-64', '65-74', '75+'])
        for (const cell of Object.values(ages)) {
          expect(Object.keys(cell).sort()).toEqual(keys)
          for (const v of Object.values(cell)) {
            expect(v.p).toBeGreaterThanOrEqual(0)
            expect(v.p).toBeLessThanOrEqual(1)
          }
        }
      }
    }
  })
})

// 설문 v3 문항 ID ↔ 웹 문항 ID
const SCHEMA_TO_WEB = {
  Q1: 'sex',
  Q2: 'birth', // v3는 만 나이 숫자, 웹은 생년월일로 받는다
  Q3: 'smoke_100',
  Q4: 'smoke_now',
  Q5: 'cigarettes',
  Q6: 'drink_ever',
  Q7: 'drink_freq',
  Q8: 'drink_amount',
  Q9: 'moderate_min',
  Q10: 'vigorous_min',
  Q11: 'strength_days',
  Q12: 'sedentary_min',
  Q13: 'weekday_bed',
  Q14: 'weekday_wake',
  Q15: 'weekend_bed',
  Q16: 'weekend_wake',
  Q17: 'shift_work',
  Q18: 'stress',
  Q19: 'breakfast',
  Q20: 'lunch',
  Q21: 'dinner',
  Q22: 'eating_out',
  Q23: 'veg',
  Q24: 'fruit',
  Q25: 'protein',
  Q26: 'dairy',
  ...Object.fromEntries(Array.from({ length: 9 }, (_, i) => [`Q${27 + i}`, `phq${i + 1}`])),
  Q36: 'dx_hypertension',
  Q37: 'dx_diabetes',
  Q38: 'dx_dyslipidemia',
}

describe('설문 문항 ↔ 설문 v3 (Jaejun/config/survey_schema_v3.json)', () => {
  const schemaQuestions = surveySchema.sections.flatMap((s) => s.questions)
  const web = Object.fromEntries(QUESTIONS.map((q) => [q.id, q]))

  it('v3의 모든 문항이 웹에 있다 (새 문항이 생기면 여기서 알려준다)', () => {
    const missing = schemaQuestions.filter((q) => !web[SCHEMA_TO_WEB[q.id]]).map((q) => `${q.id} ${q.text}`)
    expect(missing).toEqual([])
  })

  it('보기 문항은 보기 개수가 v3와 같다', () => {
    const mismatched = schemaQuestions
      .filter((q) => q.type === 'choice')
      .map((q) => ({ id: q.id, text: q.text, v3: q.options.length, web: web[SCHEMA_TO_WEB[q.id]]?.options?.length }))
      .filter((q) => q.v3 !== q.web)
    expect(mismatched).toEqual([])
  })
})
