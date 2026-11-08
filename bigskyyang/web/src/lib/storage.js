import { restoreSurvey } from './surveyFlow.js'

// 설문 응답을 이 휴대폰(localStorage)에 저장한다. 탭을 닫거나 카카오톡 안에서 링크를 다시 열어도 이어서 볼 수 있게.
//   서버로는 보내지 않는다. 마지막 저장 후 KEEP_DAYS가 지나면 지우고, '처음부터 다시 검사하기'를 누르면 바로 지운다.
//   시크릿 창 등에서 저장소를 못 쓰면 조용히 무시한다 (그 탭에서는 설문만 계속된다).
// 응답(answers)은 1단계·2단계가 함께 쓰고, 진행 위치(step)와 완료 여부(done)는 단계마다 따로 둔다.

// 문항 구성이 바뀌면 버전을 올려 예전 응답을 무시한다
//   v3: 1단계·2단계로 나눔, 운동 1문항, 세 끼 한 화면
//   v4: 생년월일(만 나이), 흡연 예·아니요, 수면 들쭉날쭉 보기 뺌 (팀 합의 2026-11-04)
const KEY = 'nbti-survey-v4'
const PICKS_KEY = 'nbti-picks-v1'
export const KEEP_DAYS = 7
const KEEP_MS = KEEP_DAYS * 24 * 60 * 60 * 1000

const EMPTY = { answers: {}, step: { 1: 0, 2: 0 }, done: { 1: false, 2: false } }
const NO_PICKS = { ids: [], gate: null, mine: [] }

// 저장할 때 시각을 함께 남기고, 읽을 때 오래됐으면 지운다. 예전(sessionStorage) 값이 있으면 한 번 옮긴다
function read(key, now = Date.now()) {
  try {
    let raw = localStorage.getItem(key)
    if (raw == null) {
      raw = sessionStorage.getItem(key)
      if (raw != null) {
        sessionStorage.removeItem(key)
        const old = JSON.parse(raw)
        write(key, old, now)
        return old
      }
      return null
    }
    const { savedAt, value } = JSON.parse(raw)
    if (!Number.isFinite(savedAt) || now - savedAt > KEEP_MS) {
      localStorage.removeItem(key)
      return null
    }
    return value
  } catch {
    // 저장소 접근 불가 또는 손상된 값
    return null
  }
}

function write(key, value, now = Date.now()) {
  try {
    localStorage.setItem(key, JSON.stringify({ savedAt: now, value }))
  } catch {
    // 저장 실패해도 설문·화면은 계속
  }
}

export function loadSurvey(now) {
  const saved = read(KEY, now)
  return saved?.answers ? restoreSurvey({ ...EMPTY, ...saved }) : EMPTY
}

export const saveSurvey = (state) => write(KEY, state)

// 건강기능식품 화면: 고른 제품(신고번호), '임신·질환·복용약' 확인 답 ('ok' | 'consult' | null),
//   내가 먹는 제품 mine: [{ id: 신고번호 } | { name: 목록에 없어 이름만 적은 제품 }]
export function loadPicks(now) {
  const saved = read(PICKS_KEY, now)
  return Array.isArray(saved?.ids) ? { ...NO_PICKS, ...saved, mine: Array.isArray(saved.mine) ? saved.mine : [] } : NO_PICKS
}

export const savePicks = (picks) => write(PICKS_KEY, picks)

export function clearSurvey() {
  for (const key of [KEY, PICKS_KEY]) {
    try {
      localStorage.removeItem(key)
      sessionStorage.removeItem(key)
    } catch {
      // 무시
    }
  }
}
