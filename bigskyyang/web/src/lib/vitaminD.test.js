import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import cases from '../../../../Jaejun/nutrition_vitamin_d_info/examples/display_cases.json'
import { visibleQuestions } from '../data/questions.js'
import { SAMPLE } from './fixtures.js'
import { recordAnswer } from './surveyFlow.js'
import { SKIP, VITD_SURVEY, vitaminDAnswers, vitaminDInfo } from './vitaminD.js'
import { VERSION, buildVitaminDInfo } from './vitaminDInfo.js'

const JAEJUN = new URL('../../../../Jaejun/nutrition_vitamin_d_info/', import.meta.url)
const read = (rel) => readFileSync(new URL(rel, JAEJUN), 'utf8').replace(/\r\n/g, '\n')
const own = (rel) => readFileSync(new URL(rel, import.meta.url), 'utf8').replace(/\r\n/g, '\n')

describe('재준님 비타민 D 모듈 사본', () => {
  it('설문 정의는 재준님 config/survey.ko.json과 같다', () => {
    expect(VITD_SURVEY).toEqual(JSON.parse(read('config/survey.ko.json')))
    expect(VITD_SURVEY.version).toBe(VERSION)
  })

  it('계산 함수 본문은 재준님 src/vitaminDInfo.mjs와 같다 (머리 주석만 다름)', () => {
    const body = own('./vitaminDInfo.js').split('\n').slice(2).join('\n')
    expect(body.trim()).toBe(read('src/vitaminDInfo.mjs').trim())
  })

  it.each(cases.map((c) => [c.name, c]))('재준님 예시 %s: 같은 결과', (_, c) => {
    expect(buildVitaminDInfo(c.answers)).toEqual(c.result)
  })
})

describe('웹 설문 ↔ 비타민 D', () => {
  const vitd = visibleQuestions(SAMPLE, 2).filter((q) => q.section === 'vitd')

  it('개인 식사 설문 맨 끝에 선택 4문항, 보기는 재준님 값 그대로', () => {
    expect(vitd.map((q) => q.id)).toEqual(VITD_SURVEY.questions.map((q) => `vitd_${q.id}`))
    expect(visibleQuestions(SAMPLE, 2).slice(-4)).toEqual(vitd)
    vitd.forEach((q, i) => expect(q.options.map((o) => o.value)).toEqual(VITD_SURVEY.questions[i].options.map((o) => o.value)))
    expect(vitd.every((q) => q.optional)).toBe(true)
  })

  it('건너뛴 문항은 재준님 함수에 넘기지 않는다 (= 미응답)', () => {
    expect(vitaminDAnswers({ vitd_commute: 'car', vitd_lunch_outing: SKIP, ffq_meat: 3 })).toEqual({ commute: 'car' })
    expect(vitaminDInfo({ vitd_commute: SKIP }).completion).toBe('unanswered')
  })

  it('건너뛰기로 답해도 설문이 끝난다', () => {
    const base = Object.fromEntries(Object.entries(SAMPLE).filter(([k]) => !k.startsWith('vitd_')))
    let state = { answers: base, done: { 1: true, 2: false }, step: { 1: 0, 2: 0 } }
    for (const q of vitd) state = recordAnswer(state, 2, q, SKIP)
    expect(state.done[2]).toBe(true)
  })

  it('비타민 D 응답은 영양 모델 결과를 바꾸지 않는다', async () => {
    const { encode } = await import('./encode.js')
    const a = { ...SAMPLE, vitd_exercise_setting: 'daytime_outdoor' }
    const b = { ...SAMPLE, vitd_exercise_setting: 'indoor' }
    expect(encode(a)).toEqual(encode(b))
  })
})
