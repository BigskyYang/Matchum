// 건강기능식품 정보의 영양소·대상·안내 문구
//   제품 목록: data/supplementCatalog.json (준혁님 9단계 통과 후보 전체, scripts/build_supplement_catalog.py가 만든다)
//   연결 규칙: Jaejun/nutrition_product_web_handoff (모델 영양소 → 제품 목록, B1·B2 → 비타민 B군)
// 화면 원칙 (준혁님 기준·재준님 인계): 제안 톤("이런 제품도 있어요"), 순위·점수·등급·가격·판매처·'베스트' 표현 없음,
//   기능성 문구와 섭취 시 주의사항은 식약처 원문 그대로, 질환·약·임신은 제품을 보기 전에 한 번 묻고 해당되면 상담을 권한다

// 재준님 모델이 '부족하기 쉬워요'로 고른 영양소 → 제품 목록 키 (key: supplementCatalog.json categories). from: 모델 영양소 키
export const PRODUCT_NUTRIENTS = [
  { key: 'magnesium', label: '마그네슘', icon: '🥜', from: ['magnesium'] },
  { key: 'vitamin_b', label: '비타민 B군', icon: '🐷', from: ['vitamin_b1', 'vitamin_b2'] },
  { key: 'vitamin_c', label: '비타민 C', icon: '🍊', from: ['vitamin_c'] },
  { key: 'fiber', label: '식이섬유', icon: '🌾', from: ['fiber'] },
  { key: 'zinc', label: '아연', icon: '🦪', from: ['zinc'] },
  { key: 'folate', label: '엽산', icon: '🥬', from: ['folate'] },
  { key: 'iron', label: '철', icon: '🥩', from: ['iron'] },
  { key: 'calcium', label: '칼슘', icon: '🥛', from: ['calcium'] },
]
// 비타민 D·종합비타민은 재준님 모델이 예측하지 않아 자동으로 연결하지 않는다 (재준님 인계: 웹이 따로 정할 때만)

// 제품 없이 음식으로 챙기는 영양소
export const FOOD_ONLY = ['protein', 'potassium', 'phosphorus']

// 제품 대상. 어린이·임산부·수유부 대상 제품은 목록에 없다. 대상끼리 순서를 섞지 않고 칸을 나눈다
export const TARGET_LABELS = { 일반: '누구나', 남성: '남성용', 여성: '여성용', 시니어: '시니어용' }
export const SENIOR_AGE = 50

// 한 번에 보여 줄 제품 수 ('더 보기'로 이어서)
export const PAGE_SIZE = 20

export const UL_NOTICES = [
  '2025 한국인 영양소 섭취기준의 성인 상한섭취량이에요. 음식으로 먹는 양과 하루 함량을 알 수 없는 성분은 계산하지 않았어요.',
  '마그네슘은 식품 외 급원, 엽산은 강화식품·보충제, 비타민 A는 레티놀 기준이에요. 다른 성분은 음식을 포함한 하루 총량 기준이에요.',
  '니아신은 니코틴산 기준 35mg으로 비교해요. 니코틴산아미드는 기준이 달라요. 형태를 알 수 없는 니아신·비타민 A는 제품 표시량 전체를 보수적으로 비교해요.',
]

export const SUPPLEMENT_NOTICES = [
  '제품 순서는 순위가 아니에요. 팀이 정한 기준(함량·하루 섭취 개수·원재료 수)으로 먼저 볼 순서만 정했어요.',
  '이미 드시는 영양제와 성분이 겹치는지 확인해 보세요.',
  '건강기능식품은 질병의 예방 및 치료를 위한 의약품이 아닙니다.',
  '참고용 정보이며 의학적 진단이나 처방이 아니에요. 특정 제품을 광고하거나 권장하지 않아요.',
]
