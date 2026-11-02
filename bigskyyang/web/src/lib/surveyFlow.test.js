import { describe, expect, it } from 'vitest'
import { visibleQuestions } from '../data/questions.js'
import { resolveStep, surveyPath } from './surveyFlow.js'

const answers = { sex: 2, birth: '2000-01-01', smoke_100: 'no' }
const list = visibleQuestions(answers)
const idx = (id) => list.findIndex((q) => q.id === id)

describe('resolveStep', () => {
  it('주소의 문항으로 뒤로 갈 수 있다', () => {
    expect(resolveStep(list, answers, 'birth', 3)).toBe(idx('birth'))
    expect(resolveStep(list, answers, 'sex', 3)).toBe(0)
  })

  it('아직 답하지 않은 문항보다 앞으로는 건너뛸 수 없다', () => {
    // 답한 것은 smoke_100까지, 다음 문항은 drink_ever
    expect(resolveStep(list, answers, 'stress', 0)).toBe(idx('drink_ever'))
  })

  it('주소에 문항이 없으면 저장해 둔 위치에서 이어 간다', () => {
    expect(resolveStep(list, answers, null, 2)).toBe(2)
    expect(resolveStep(list, answers, null, 99)).toBe(idx('drink_ever'))
  })

  it('지금은 숨겨진 문항(흡연하지 않는데 흡연량)을 요청하면 저장 위치로 간다', () => {
    expect(resolveStep(list, answers, 'cigarettes', 1)).toBe(1)
  })

  it('모두 답했으면 마지막 문항까지 갈 수 있다', () => {
    const all = Object.fromEntries(list.map((q) => [q.id, 0]))
    const full = visibleQuestions(all)
    expect(resolveStep(full, all, full.at(-1).id, 0)).toBe(full.length - 1)
  })
})

describe('surveyPath', () => {
  it('문항 ID로 주소를 만든다', () => {
    expect(surveyPath({ id: 'birth' })).toBe('/survey?q=birth')
  })
})
