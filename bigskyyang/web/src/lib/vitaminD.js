// 비타민 D 생활 안내 (재준님 Jaejun/nutrition_vitamin_d_info v1.2.0) ↔ 웹 설문 연결
//   - 설문: 개인 식사 설문 맨 끝 선택 4문항 (출퇴근·점심 외출·운동 장소·쉬는 날 외출). 응답 키는 vitd_ + 재준님 문항 id
//   - '건너뛰기'는 SKIP으로 저장하고, 재준님 함수에는 넘기지 않는다 (= 미응답, 일반 안내)
//   - 이 응답은 기존 영양 모델·시뮬레이터·건강기능식품 고르기에 쓰지 않는다 (재준님 HANDOFF.md)
//   - 점수·등급·부족 예측을 만들지 않는다. 결과 계산은 재준님 함수(lib/vitaminDInfo.js)를 그대로 쓴다
import survey from '../data/vitaminDSurvey.json'
import { buildVitaminDInfo } from './vitaminDInfo.js'

export const VITD_PREFIX = 'vitd_'
export const SKIP = 'skip'
export const VITD_SURVEY = survey

// 웹 응답 → 재준님 함수 입력 (건너뛴 문항·답하지 않은 문항은 넣지 않는다)
export function vitaminDAnswers(answers = {}) {
  const out = {}
  for (const q of survey.questions) {
    const v = answers[VITD_PREFIX + q.id]
    if (v != null && v !== SKIP && q.options.some((o) => o.value === v)) out[q.id] = v
  }
  return out
}

export const vitaminDInfo = (answers) => buildVitaminDInfo(vitaminDAnswers(answers))
