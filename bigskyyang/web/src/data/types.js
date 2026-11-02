// NBTI 유형 설명. 군집 결과가 확정되면 이 파일의 문구만 채우면 된다.
//
// MAIN_TYPES: 대분류 4개 (결과 화면의 큰 유형). 이름은 현재 군집 평균을 보고 붙인 가칭
// LEAF_TYPES: 세부 유형 20개 (model.json의 leaves). 비어 있으면 화면에서 자동 생성 문구를 쓴다
//
// 각 항목에 넣을 수 있는 값 (모두 선택)
//   name        유형 이름
//   emoji       대표 이모지
//   summary     한 줄 설명
//   nutrients   부족하기 쉬운 영양소 ['칼슘', ...]          ← 유형별 영양 분석(KDRI) 후 채움
//   foods       추천 음식 ['우유·요구르트', ...]
//   supplements 고려해 볼 수 있는 건강기능식품 원료 ['비타민 D', ...]
//               ※ 질병 예방·치료 효능 표현 금지 (식품표시광고법 제8조)

export const MAIN_TYPES = {
  Group_0: {
    name: '점심 건너뛰기형',
    emoji: '⏭️',
    summary: '하루 중 점심을 자주 거르는 생활 패턴이 두드러진 유형이에요.',
  },
  Group_1: {
    name: '담백 절제형',
    emoji: '🌿',
    summary: '술과 담배를 거의 하지 않고 식사도 규칙적인 유형이에요.',
  },
  Group_2: {
    name: '흡연 동반형',
    emoji: '💨',
    summary: '흡연과 함께 음주·외식이 잦고 아침을 자주 거르는 유형이에요.',
  },
  Group_3: {
    name: '사교 음주형',
    emoji: '🍻',
    summary: '담배는 피우지 않지만 술자리와 외식이 잦은 유형이에요.',
  },
}

export const LEAF_TYPES = {
  // 예시
  // 'Group_1-1_A': { name: '…', summary: '…', nutrients: [], foods: [], supplements: [] },
}

// 세부 유형 번호를 사람이 읽기 쉽게: 'Group_1-0_B' → '1-0-B'
export const leafCode = (leaf) => leaf.replace('Group_', '').replace('_', '-')
