// 설문에서 지금 보여줄 문항 고르기.
// 주소의 ?q=문항ID를 따르되(휴대폰 뒤로·앞으로 가기), 아직 답하지 않은 문항을 건너뛰어 앞으로 갈 수는 없다.
// 주소에 문항이 없거나(처음 들어옴) 지금은 숨겨진 문항이면 저장해 둔 위치에서 이어 간다.
export function resolveStep(list, answers, requestedId, storedStep = 0) {
  const firstOpen = list.findIndex((q) => answers[q.id] === undefined)
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
