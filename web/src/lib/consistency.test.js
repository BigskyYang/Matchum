// 데이터 파일끼리, 그리고 팀원 설문·모델 정의와 웹이 서로 맞는지 점검한다.
// 군집화를 다시 돌리거나 설문(analysis/03_personal_prediction/model/config)이 바뀌었는데 웹을 안 맞췄으면 여기서 실패한다.
import { existsSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import targets from '../../../analysis/03_personal_prediction/model/config/targets.json'
import contract from '../../../analysis/03_personal_prediction/model/config/encoding_contract.json'
import surveySchema from '../../../analysis/03_personal_prediction/survey_schema_v3.json'
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

describe('개인화용 영양소 정의 (nutrients.js) ↔ 재준 모델 (analysis/03_personal_prediction/model/config/targets.json)', () => {
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
  Q2: { merged: 'birth_date' }, // 생년월일로 만 나이를 계산 (팀 합의: 웹은 항상 만 나이)
  Q3: { merged: 'smoke_now' }, // '평생 100개비'를 먼저 묻지 않고 지금 피우는지만 (팀 합의: 궐련·전자담배 구분 없음)
  Q4: { merged: 'smoke_now' }, // 매일·가끔 → '네', 끊음·안 피움 → '아니요' (재준님 currently_smoking)
  Q5: 'cigarettes',
  Q6: { merged: 'drink_freq' }, // '평생 1잔'을 먼저 묻지 않고 빈도에 '최근 1년 안 마셨어요'
  Q7: 'drink_freq',
  Q8: 'drink_amount',
  Q9: { merged: 'activity' }, // 팀 합의: 중강도·고강도를 나누지 않고 합친 시간이 주 150분 이상인지 한 문항 (재준님 aerobic_150min)
  Q10: { merged: 'activity' },
  Q11: 'strength_days',
  Q12: 'sedentary_min',
  Q13: 'weekday_bed',
  Q14: 'weekday_wake',
  Q15: 'weekend_bed',
  Q16: 'weekend_wake',
  Q17: { removed: '교대근무는 모델 입력이 아님. 팀 합의로 수면이 들쭉날쭉한 경우는 따로 묻지 않음' },
  Q18: 'stress',
  Q19: { merged: 'meals' }, // 아침·점심·저녁을 한 화면에서
  Q20: { merged: 'meals' },
  Q21: { merged: 'meals' },
  Q22: 'eating_out',
  Q23: 'veg',
  Q24: 'fruit',
  Q25: { removed: '재준님 최종 설문(SURVEY_FINAL)의 mini-FFQ 5문항(ffq_meat … ffq_dairy)으로 바꿈' },
  Q26: { removed: '재준님 최종 설문(SURVEY_FINAL)의 mini-FFQ 5문항으로 바꿈' },
  // PHQ-9·대사질환 진단은 묻지 않는다: 점수 해석이나 질환별 조언이 진단·처방처럼 보일 소지가 있고(의료법),
  // 영양 예측 모델에도 쓰지 않는다. 건강 정보(민감정보)도 꼭 필요한 만큼만 받는다
  ...Object.fromEntries(Array.from({ length: 9 }, (_, i) => [`Q${27 + i}`, { removed: 'PHQ-9: 우울 점수 해석이 진단처럼 보일 소지' }])),
  Q36: { removed: '대사질환 진단: 질환별 식사 조언이 처방처럼 보일 소지' },
  Q37: { removed: '대사질환 진단' },
  Q38: { removed: '대사질환 진단' },
}

describe('설문 문항 ↔ 설문 v3 (analysis/03_personal_prediction/survey_schema_v3.json)', () => {
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

// 재준님 최종 설문(analysis/03_personal_prediction/model/SURVEY_FINAL.md)의 mini-FFQ ↔ 웹
// (제품 추천 안전 문항 4가지는 웹에서 건강기능식품 제품을 추천하지 않으므로 묻지 않는다)
describe('설문 ↔ 재준님 최종 설문 (mini-FFQ)', () => {
  const web = Object.fromEntries(QUESTIONS.map((q) => [q.id, q]))

  it('mini-FFQ 5문항, 보기 8단계 0~7 (analysis/03_personal_prediction/model/src/mini_ffq.py FOOD_FREQ_ORD)', () => {
    for (const id of ['ffq_meat', 'ffq_fish', 'ffq_egg', 'ffq_legume', 'ffq_dairy']) {
      expect(web[id].options.map((o) => o.value)).toEqual([0, 1, 2, 3, 4, 5, 6, 7])
    }
  })

})

// 재준님 v1.4 입력 계약(encoding_contract.json) ↔ 웹 보기 값: 보기 순서대로 같은 코드인지 (방향이 뒤집히면 실패)
describe('설문 보기 값 ↔ 재준님 v1.4 입력 계약 (encoding_contract.json)', () => {
  const web = Object.fromEntries(QUESTIONS.map((q) => [q.id, q]))
  const codes = (key) => Object.values(contract.encoded_training_features[key])
  const values = (id) => web[id].options.map((o) => o.value)

  it('끼니(주 5~7회 = 3)·외식(하루 2회 이상 = 6)·음주 빈도·음주량', () => {
    expect(values('meals')).toEqual(codes('ML_breakfast_freq_ord'))
    expect(values('eating_out')).toEqual(codes('ML_eatingout_freq_ord'))
    expect(values('drink_freq')).toEqual(codes('ML_drink_freq_ord'))
    expect(values('drink_amount')).toEqual(codes('ML_drink_amount_ord'))
  })

  it('채소·과일: 웹 값 v → 모델 9 − v (1 = 하루 3회 이상 … 9 = 거의 안 함)', () => {
    expect(values('veg').map((v) => 9 - v)).toEqual(codes('식습관_LS_VEG2'))
    expect(values('fruit').map((v) => 9 - v)).toEqual(codes('식습관_LS_FRUIT'))
  })

  it('mini-FFQ 5문항 (거의 먹지 않음 = 0 … 하루 3회 이상 = 7)', () => {
    for (const id of ['ffq_meat', 'ffq_fish', 'ffq_egg', 'ffq_legume', 'ffq_dairy']) {
      expect(values(id)).toEqual(Object.values(contract.mini_ffq_frequency))
    }
  })
})
