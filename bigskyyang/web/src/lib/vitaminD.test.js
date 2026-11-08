import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import cases from '../../../../Jaejun/nutrition_vitamin_d_card/examples/card_cases.json'
import { visibleQuestions } from '../data/questions.js'
import { SAMPLE } from './fixtures.js'
import { recordAnswer } from './surveyFlow.js'
import { SKIP, VITAMIN_D_PRODUCT_NOTICE, VITD_SURVEY, vitaminDAnswers, vitaminDCard } from './vitaminD.js'
import { VERSION, appendVitaminDCard, buildVitaminDCard } from './vitaminDCard.js'

const JAEJUN = new URL('../../../../Jaejun/nutrition_vitamin_d_card/', import.meta.url)
const read = (rel) => readFileSync(new URL(rel, JAEJUN), 'utf8').replace(/\r\n/g, '\n')
const own = (rel) => readFileSync(new URL(rel, import.meta.url), 'utf8').replace(/\r\n/g, '\n')

describe('재준님 비타민 D 카드 v1.3.0 사본', () => {
  it('설문 정의는 재준님 config/survey.ko.json과 같다', () => {
    expect(VITD_SURVEY).toEqual(JSON.parse(read('config/survey.ko.json')))
    expect(VITD_SURVEY.version).toBe(VERSION)
  })

  it('계산 함수 본문은 재준님 src/vitaminDCard.mjs와 같다 (머리 주석 두 줄만 다름)', () => {
    const body = own('./vitaminDCard.js').split('\n').slice(2).join('\n')
    expect(body.trim()).toBe(read('src/vitaminDCard.mjs').trim())
  })

  it.each(cases.map((c, i) => [i + 1, c]))('재준님 예시 %s: 같은 카드', (_, c) => {
    expect(buildVitaminDCard(c.answers)).toEqual(c.card)
  })

  it('등급·확률이 없고, 제품 안내 문장은 웹 상수와 같다', () => {
    const card = buildVitaminDCard({ lunch_outing: 'rarely', day_off_outing: 'rarely', exercise_setting: 'indoor' })
    expect(card.assessment).toEqual({ type: 'guidance', grade: null, probability: null })
    expect(card.productNotice).toBe(VITAMIN_D_PRODUCT_NOTICE)
  })

  it('기존 카드 순서를 지키고 끝에 하나만 붙인다', () => {
    const cards = appendVitaminDCard([{ id: 'calcium' }, { id: 'vitamin_d' }, { id: 'zinc' }], { lunch_outing: 'often' })
    expect(cards.map((c) => c.id)).toEqual(['calcium', 'vitamin_d', 'zinc'])
    expect(appendVitaminDCard([{ id: 'calcium' }], { lunch_outing: 'often' }).map((c) => c.id)).toEqual(['calcium', 'vitamin_d'])
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

  it('건너뛴 문항은 넘기지 않고, 근거가 되는 응답이 없으면 카드가 없다', () => {
    expect(vitaminDAnswers({ vitd_commute: 'car', vitd_lunch_outing: SKIP, ffq_meat: 3 })).toEqual({ commute: 'car' })
    expect(vitaminDCard({ vitd_commute: 'car', vitd_lunch_outing: SKIP })).toBeNull()
    expect(vitaminDCard({ vitd_lunch_outing: 'unknown', vitd_exercise_setting: 'unknown', vitd_day_off_outing: 'unknown' })).toBeNull()
    expect(vitaminDCard(SAMPLE).id).toBe('vitamin_d')
  })

  it('건너뛰기로 답해도 설문이 끝난다', () => {
    const base = Object.fromEntries(Object.entries(SAMPLE).filter(([k]) => !k.startsWith('vitd_')))
    let state = { answers: base, done: { 1: true, 2: false }, step: { 1: 0, 2: 0 } }
    for (const q of vitd) state = recordAnswer(state, 2, q, SKIP)
    expect(state.done[2]).toBe(true)
  })

  it('비타민 D 응답은 영양 모델 입력을 바꾸지 않는다', async () => {
    const { encode } = await import('./encode.js')
    expect(encode({ ...SAMPLE, vitd_exercise_setting: 'daytime_outdoor' })).toEqual(encode({ ...SAMPLE, vitd_exercise_setting: 'indoor' }))
  })
})
