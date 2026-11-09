import { describe, expect, it } from 'vitest'
import { visibleQuestions } from '../data/questions.js'
import { SAMPLE, bornAt } from './fixtures.js'
import { recordAnswer, restoreSurvey, resolveStep, resultPath, surveyPath } from './surveyFlow.js'

const answers = { sex: 2, birth_date: '2000-05-01', activity: 0 }
const list = visibleQuestions(answers, 1)
const idx = (id) => list.findIndex((q) => q.id === id)

describe('resolveStep', () => {
  it('주소의 문항으로 뒤로 갈 수 있다', () => {
    expect(resolveStep(list, answers, 'birth_date', 3)).toBe(idx('birth_date'))
    expect(resolveStep(list, answers, 'sex', 3)).toBe(0)
  })

  it('아직 답하지 않은 문항보다 앞으로는 건너뛸 수 없다', () => {
    // 답한 것은 activity까지, 다음 문항은 strength_days
    expect(resolveStep(list, answers, 'stress', 0)).toBe(idx('strength_days'))
  })

  it('주소에 문항이 없으면 저장해 둔 위치에서 이어 간다', () => {
    expect(resolveStep(list, answers, null, 2)).toBe(2)
    expect(resolveStep(list, answers, null, 99)).toBe(idx('strength_days'))
  })

  it('지금은 숨겨진 문항(주말이 다른지 답하기 전 주말 취침 시각)을 요청하면 저장 위치로 간다', () => {
    expect(resolveStep(list, answers, 'weekend_bed', 1)).toBe(1)
  })

  it('모두 답했으면 마지막 문항까지 갈 수 있다', () => {
    const all = { ...SAMPLE, activity: 0 }
    const full = visibleQuestions(all, 1)
    expect(resolveStep(full, all, full.at(-1).id, 0)).toBe(full.length - 1)
  })
})

describe('surveyPath', () => {
  it('단계와 문항 ID로 주소를 만든다', () => {
    expect(surveyPath({ id: 'birth_date' })).toBe('/survey?q=birth_date')
    expect(surveyPath({ id: 'veg' }, 2)).toBe('/survey2?q=veg')
    expect(resultPath(1)).toBe('/reveal')
    expect(resultPath(2)).toBe('/result2')
  })
})

describe('기존 응답 변경과 완료 상태', () => {
  const completed = () => ({ answers: { ...SAMPLE }, done: { 1: true, 2: true }, step: { 1: 0, 2: 0 } })
  const answer = (state, stage, id, value) => recordAnswer(state, stage, { id }, value)
  it('흡연·음주 추가 문항이 열리면 답을 받기 전까지 개인 결과를 잠근다', () => {
    for (const [id, value, follow, amount] of [['smoke_now', 'yes', 'cigarettes', 5], ['drink_freq', 3, 'drink_amount', 2]]) {
      const changed = answer(completed(), 2, id, value)
      expect(changed.done).toEqual({ 1: true, 2: false })
      expect(answer(changed, 2, follow, amount).done[2]).toBe(true)
    }
  })
  it('65세에서 식사 5문항을 생략하고 64세로 수정하면 다시 응답을 받는다', () => {
    const older = answer(completed(), 1, 'birth_date', bornAt(65))
    expect(older.answers.ffq_meat).toBeUndefined()
    expect(older.done[2]).toBe(true)
    const younger = answer(older, 1, 'birth_date', bornAt(64))
    expect(younger.done[2]).toBe(false)
  })
  it('예전 완료 세션도 필수 응답 누락 또는 동일한 취침·기상 시각을 감지한다', () => {
    const old = completed()
    old.answers.weekday_wake = old.answers.weekday_bed
    expect(restoreSurvey(old).done).toEqual({ 1: false, 2: false })
  })
})

describe('수면 응답 수정', () => {
  it('주말 응답을 생략했다가 다시 열면 이전 시각을 재사용하지 않는다', () => {
    const old = { answers: { ...SAMPLE }, done: { 1: true, 2: true }, step: { 1: 0, 2: 0 } }
    const same = recordAnswer(old, 1, { id: 'weekend_same' }, 'yes')
    expect(same.answers.weekend_wake).toBeUndefined()
    const changed = recordAnswer(same, 1, { id: 'weekend_same' }, 'no')
    expect(changed.done).toEqual({ 1: false, 2: false })
    expect(visibleQuestions(changed.answers, 1)[changed.step[1]].id).toBe('weekend_bed')
  })
})

it('운동 응답(주 0~5시간)은 그대로 두고 3시간 이상만 150분 이상으로 본다 (예전 0·3 값도 같은 뜻)', async () => {
  const { encode } = await import('./encode.js')
  for (const [hours, aerobic] of [[0, 0], [1, 0], [2, 0], [3, 1], [4, 1], [5, 1]]) {
    const restored = restoreSurvey({ answers: { ...SAMPLE, activity: hours }, done: { 1: true, 2: true } })
    expect(restored.answers.activity).toBe(hours)
    expect(restored.done[2]).toBe(true)
    expect(encode(restored.answers).features.ML_aerobic).toBe(aerobic)
  }
})
