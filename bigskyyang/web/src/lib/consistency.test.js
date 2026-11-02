// 데이터 파일끼리, 그리고 팀원 설문·모델 정의와 웹이 서로 맞는지 점검한다.
// 군집화를 다시 돌리거나 설문(Jaejun/config)이 바뀌었는데 웹을 안 맞췄으면 여기서 실패한다.
import { describe, expect, it } from 'vitest'
import targets from '../../../../Jaejun/config/targets.json'
import surveySchema from '../../../../Jaejun/config/survey_schema_v3.json'
import nutrientProfiles from '../data/nutrientProfiles.json'
import { BANDS, NUTRIENTS } from '../data/nutrients.js'
import { QUESTIONS } from '../data/questions.js'
import { LEAF_TYPES, MAIN_TYPES } from '../data/types.js'
import { mainLabels, model, typeId } from './classify.js'

const mainIds = mainLabels().map((l) => typeId(l))
const leafIds = model.leaves.map((l) => typeId(l))

describe('군집 모델 ↔ 유형 설명 (types.js)', () => {
  it('모든 군집 번호에 유형 ID가 있고 겹치지 않는다', () => {
    const labels = [...mainLabels(), ...model.leaves]
    expect(labels.every((l) => model.typeIds[l])).toBe(true)
    expect(new Set(labels.map((l) => typeId(l))).size).toBe(labels.length)
  })

  it('대분류 유형마다 이름·이모지·설명이 있다', () => {
    expect(Object.keys(MAIN_TYPES).sort()).toEqual([...mainIds].sort())
    for (const id of mainIds) {
      expect(MAIN_TYPES[id]).toMatchObject({ name: expect.any(String), emoji: expect.any(String), summary: expect.any(String) })
    }
  })

  it('세부 유형 설명은 지금 있는 세부 유형에만 붙어 있다', () => {
    expect(Object.keys(LEAF_TYPES).filter((id) => !leafIds.includes(id))).toEqual([])
  })
})

describe('영양소 정의 ↔ 재준 모델 (Jaejun/config/targets.json)', () => {
  it('14개 영양소 키가 같다', () => {
    expect(NUTRIENTS.map((n) => n.key).sort()).toEqual(Object.keys(targets).sort())
  })
})

describe('유형별 영양소 결과표 (nutrientProfiles.json)', () => {
  const entries = Object.entries(nutrientProfiles.types)

  it('결과표의 유형은 모두 지금 군집 모델의 유형 ID다', () => {
    const known = [...mainIds, ...leafIds]
    expect(entries.map(([id]) => id).filter((id) => !known.includes(id))).toEqual([])
  })

  it('영양소 키·등급·비율이 올바르다', () => {
    const keys = NUTRIENTS.map((n) => n.key)
    for (const [, profile] of entries) {
      for (const [key, v] of Object.entries(profile.nutrients)) {
        expect(keys).toContain(key)
        expect(Object.keys(BANDS)).toContain(v.band)
        expect(v.rate).toBeGreaterThanOrEqual(0)
        expect(v.rate).toBeLessThanOrEqual(1)
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
