// 비타민 D 기존 영양소 카드 연결 (재준님 analysis/03_personal_prediction/vitamin_d_card v1.3.0) ↔ 웹 설문
//   - 설문: 개인 식사 설문 맨 끝 선택 4문항 (출퇴근·점심 외출·운동 장소·쉬는 날 외출). 응답 키는 vitd_ + 재준님 문항 id
//   - '건너뛰기'는 SKIP으로 저장하고, 재준님 함수에는 넘기지 않는다 (= 미응답)
//   - 결과: '내가 특히 살펴볼 영양소' 카드 목록 끝에 비타민 D 카드 하나 (점심·운동·휴일 중 하나라도 알려진 응답이 있을 때만)
//     등급·확률은 없다 (학습된 모델 없음). 출처는 '추가 생활문항 기반 안내'로 표시
//   - 이 응답은 기존 영양 모델·시뮬레이터·약사 메모의 '부족하기 쉬운 영양소'에 쓰지 않는다
import survey from '../data/vitaminDSurvey.json'
import { buildVitaminDCard } from './vitaminDCard.js'

export const VITD_PREFIX = 'vitd_'
export const SKIP = 'skip'
export const VITD_SURVEY = survey
// 비타민 D 제품 목록 위 안내 (재준님 카드의 productNotice와 같은 문장, 테스트로 확인)
export const VITAMIN_D_PRODUCT_NOTICE = '관련 제품의 정보이며, 개인의 복용 필요성이나 적합성을 확인한 결과는 아니에요.'

// 웹 응답 → 재준님 함수 입력 (건너뛴 문항·답하지 않은 문항은 넣지 않는다)
export function vitaminDAnswers(answers = {}) {
  const out = {}
  for (const q of survey.questions) {
    const v = answers[VITD_PREFIX + q.id]
    if (v != null && v !== SKIP && q.options.some((o) => o.value === v)) out[q.id] = v
  }
  return out
}

// 카드 또는 null (근거가 되는 응답이 없으면 카드를 붙이지 않는다)
export const vitaminDCard = (answers) => buildVitaminDCard(vitaminDAnswers(answers))
