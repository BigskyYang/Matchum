// 개인 결과 '건강기능식품 정보'의 영양소: 준혁님 분류·필터링 기준 v3 (junhyeok/영양제_분류_필터링_기준(피드백).pdf)
//   제품 조사 13종 중 부족 위험(KNHANES 영양소)과 이어지는 9종만 쓴다. 오메가3·유산균·루테인·밀크씨슬은 부족 위험으로 정하지 않는다
//   단백질·칼륨·인은 제품 없이 음식으로 안내, 비타민 A·E는 추천 대상에서 제외 (다른 제품의 보조 성분으로는 들어 있을 수 있다)
// 화면 원칙 (v3 9절): 제안 톤("이런 제품도 있어요"), 순위·가격·판매처·"안전한 제품"·"맞춤 용량" 표현 없음,
//   기능성 문구와 섭취 시 주의사항은 식약처 원문 그대로, 질환·약·임신은 제품을 거르지 않고 상담을 권한다

// 제품 목록(supplementProducts.json)의 영양소 키. from: 결과표(nutrientGuide.js) 영양소 키
export const PRODUCT_NUTRIENTS = [
  { key: 'vitamin_b', label: '비타민 B군', icon: '🐷', from: ['vitamin_b1', 'vitamin_b2'] },
  { key: 'vitamin_c', label: '비타민 C', icon: '🍊', from: ['vitamin_c'] },
  { key: 'vitamin_d', label: '비타민 D', icon: '☀️', from: ['vitamin_d'] },
  { key: 'calcium', label: '칼슘', icon: '🥛', from: ['calcium'] },
  { key: 'magnesium', label: '마그네슘', icon: '🥜', from: ['magnesium'] },
  { key: 'zinc', label: '아연', icon: '🦪', from: ['zinc'] },
  { key: 'iron', label: '철', icon: '🥩', from: ['iron'] },
  { key: 'folate', label: '엽산', icon: '🥬', from: ['folate'] },
  { key: 'fiber', label: '식이섬유', icon: '🌾', from: ['fiber'] },
]

// 제품 없이 음식으로 챙기는 영양소
export const FOOD_ONLY = ['protein', 'potassium', 'phosphorus']

// 제품 대상 (제품명 기준, 준혁님 기준 2절). 어린이·임산부·수유부 대상 제품은 보여 주지 않는다
export const TARGETS = ['일반', '남성', '여성', '시니어']
export const SENIOR_AGE = 50

// 영양소마다 보여 줄 제품 수 (v3: 개수는 추후 논의)
export const MAX_PRODUCTS = 3

export const SUPPLEMENT_NOTICES = [
  '제품 순서는 순위가 아니에요. 함량 기준과 먹기 편한 정도로 팀이 정한 규칙에 따라 고른 예시예요.',
  '이미 드시는 영양제와 성분이 겹치는지 확인해 보세요.',
  '건강기능식품은 질병의 예방 및 치료를 위한 의약품이 아닙니다.',
  '본 결과는 참고용 정보이며 의학적 진단이나 처방이 아닙니다. 특정 제품을 광고하거나 권장하지 않습니다.',
]
