// 설문 응답을 브라우저(sessionStorage)에 임시 저장한다. 새로고침해도 이어서 할 수 있게.
// 시크릿 창 등에서 저장소를 못 쓰면 조용히 무시한다. 응답은 서버로 보내지 않는다.
// 응답(answers)은 1단계·2단계가 함께 쓰고, 진행 위치(step)와 완료 여부(done)는 단계마다 따로 둔다.

// 문항 구성이 바뀌면 버전을 올려 예전 응답을 무시한다
//   v3: 1단계·2단계로 나눔, 운동 1문항, 세 끼 한 화면
//   v4: 생년월일(만 나이), 흡연 예·아니요, 수면 들쭉날쭉 보기 뺌 (팀 합의 2026-11-04)
const KEY = 'nbti-survey-v4'

const EMPTY = { answers: {}, step: { 1: 0, 2: 0 }, done: { 1: false, 2: false } }

export function loadSurvey() {
  try {
    const saved = JSON.parse(sessionStorage.getItem(KEY))
    if (saved?.answers) return { ...EMPTY, ...saved }
  } catch {
    // 저장소 접근 불가 또는 손상된 값
  }
  return EMPTY
}

export function saveSurvey(state) {
  try {
    sessionStorage.setItem(KEY, JSON.stringify(state))
  } catch {
    // 저장 실패해도 설문은 계속 진행
  }
}

// 건강기능식품 화면: 고른 제품(신고번호), '임신·질환·복용약' 확인 답 ('ok' | 'consult' | null),
//   내가 먹는 제품 mine: [{ id: 신고번호 } | { name: 목록에 없어 이름만 적은 제품 }]
const PICKS_KEY = 'nbti-picks-v1'
const NO_PICKS = { ids: [], gate: null, mine: [] }

export function loadPicks() {
  try {
    const saved = JSON.parse(sessionStorage.getItem(PICKS_KEY))
    if (Array.isArray(saved?.ids)) return { ...NO_PICKS, ...saved, mine: Array.isArray(saved.mine) ? saved.mine : [] }
  } catch {
    // 저장소 접근 불가 또는 손상된 값
  }
  return NO_PICKS
}

export function savePicks(picks) {
  try {
    sessionStorage.setItem(PICKS_KEY, JSON.stringify(picks))
  } catch {
    // 저장 실패해도 화면은 계속
  }
}

export function clearSurvey() {
  try {
    sessionStorage.removeItem(KEY)
    sessionStorage.removeItem(PICKS_KEY)
  } catch {
    // 무시
  }
}
