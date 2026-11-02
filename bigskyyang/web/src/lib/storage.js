// 설문 응답을 브라우저(sessionStorage)에 임시 저장한다. 새로고침해도 이어서 할 수 있게.
// 시크릿 창 등에서 저장소를 못 쓰면 조용히 무시한다. 응답은 서버로 보내지 않는다.

// 문항 구성이 바뀌면 버전을 올려 예전 응답을 무시한다 (v2: 키·체중 삭제, 나이 → 생년월일)
const KEY = 'nbti-survey-v2'

export function loadSurvey() {
  try {
    const saved = JSON.parse(sessionStorage.getItem(KEY))
    if (saved?.answers) return saved
  } catch {
    // 저장소 접근 불가 또는 손상된 값
  }
  return { answers: {}, step: 0, done: false }
}

export function saveSurvey(state) {
  try {
    sessionStorage.setItem(KEY, JSON.stringify(state))
  } catch {
    // 저장 실패해도 설문은 계속 진행
  }
}

export function clearSurvey() {
  try {
    sessionStorage.removeItem(KEY)
  } catch {
    // 무시
  }
}
