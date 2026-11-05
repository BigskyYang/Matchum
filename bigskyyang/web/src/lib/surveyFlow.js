import { QUESTIONS, visibleQuestions } from '../data/questions.js'
import { SKIP } from './vitaminD.js'

// 설문에서 지금 보여줄 문항 고르기.
// 주소의 ?q=문항ID를 따르되(휴대폰 뒤로·앞으로 가기), 아직 답하지 않은 문항을 건너뛰어 앞으로 갈 수는 없다.
// 주소에 문항이 없거나(처음 들어옴) 지금은 숨겨진 문항이면 저장해 둔 위치에서 이어 간다.
function answered(q, answers) {
  const value = answers[q.id]
  if (value == null || q.check?.(value, answers)) return false
  // 선택 문항(비타민 D)은 '건너뛰기'도 답한 것으로 본다
  if (q.optional && value === SKIP) return true
  if (q.type === 'rows') return q.rows.every((row) => q.options.some((o) => o.value === value[row.id]))
  if (q.type === 'choice') return q.options.some((o) => o.value === value)
  if (q.type === 'number') return Number.isInteger(value) && value >= q.min && value <= q.max
  if (q.type === 'duration') return Number.isFinite(value) && value >= 0 && value <= q.maxHours * 60
  if (q.type === 'time') return typeof value === 'string' && /^([01]\d|2[0-3]):[0-5]\d$/.test(value)
  return true
}

export function resolveStep(list, answers, requestedId, storedStep = 0) {
  const firstOpen = list.findIndex((q) => !answered(q, answers))
  const limit = firstOpen === -1 ? list.length - 1 : firstOpen
  const requested = list.findIndex((q) => q.id === requestedId)
  const step = requested !== -1 ? requested : storedStep
  return Math.min(Math.max(0, step), limit)
}

// 단계마다 설문 주소가 다르다: 1단계 /survey, 2단계 /survey2
export const surveyBase = (stage) => (stage === 2 ? '/survey2' : '/survey')
// 설문을 마치면: 1단계는 결과 공개 스토리(/reveal → /result), 2단계는 개인 결과
export const resultPath = (stage) => (stage === 2 ? '/result2' : '/reveal')
export const surveyPath = (q, stage = 1) => `${surveyBase(stage)}?q=${q.id}`

// 이전 문항을 수정하면 숨겨진 응답을 비우고 새로 필요한 문항을 다시 확인한다.
export function recordAnswer(state, stage, question, value) {
  const answers = visibleAnswers({ ...state.answers, [question.id]: value })
  const done = { ...state.done }
  for (const part of [1, 2]) {
    const list = visibleQuestions(answers, part)
    const complete = list.every((q) => answered(q, answers))
    done[part] = complete && (state.done[part] || part === stage)
  }
  if (!done[1]) done[2] = false
  const list = visibleQuestions(answers, stage)
  const index = list.findIndex((q) => q.id === question.id)
  const step = Math.min(index + 1, list.length - 1)
  return { answers, done, step: { ...state.step, [stage]: step } }
}


// 이전 버전에서 완료 처리한 세션도 현재 보이는 문항으로 다시 점검한다.
export function restoreSurvey(saved) {
  const answers = visibleAnswers(saved.answers)
  const done1 = Boolean(saved.done?.[1]) && visibleQuestions(answers, 1).every((q) => answered(q, answers))
  const done2 = done1 && Boolean(saved.done?.[2]) && visibleQuestions(answers, 2).every((q) => answered(q, answers))
  return { ...saved, answers, done: { 1: done1, 2: done2 } }
}


function visibleAnswers(raw) {
  const answers = { ...raw }
  // 기존 4지선다의 1·2번도 동일한 '150분 미만' 모델 입력이었다.
  if ([1, 2].includes(answers.activity)) answers.activity = 0
  for (const q of QUESTIONS) {
    if (q.showIf && !q.showIf(answers)) delete answers[q.id]
  }
  return answers
}
