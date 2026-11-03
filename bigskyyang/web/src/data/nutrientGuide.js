// 영양소 신호등(결과 화면)에 보여 줄 영양소 15종: 2025 KDRI 기준 (유환님 12유형 결과표 nutrientCells.json과 같은 키)
// basis: EAR(평균필요량) 미만 = 부족 위험, AI(충분섭취량) 미만 = 충분섭취량보다 적음(참고)
// role: 영양소의 일반적인 역할. 질병 예방·치료 효과 표현 금지 (식품표시광고법 제8조)
// foods: 챙겨 먹으면 좋은 대표 음식 (nutrients.js와 같은 것은 그대로)

// 신호등 단계: 같은 유형·성별·연령대 사람 중 기준보다 적게 먹는 비율(p)로 정한다
// 0.5 = 유환님 추천 규칙(10명 중 5명 이상), 0.3 = 유환님 의견 요청 문서의 하한안(10명 중 3명). 팀 결정에 따라 바뀔 수 있다
export const NUTRIENT_LEVELS = [
  { min: 0.5, key: 'low', label: '부족', tone: 'poor' },
  { min: 0.3, key: 'mid', label: '주의', tone: 'fair' },
  { min: 0, key: 'ok', label: '충분', tone: 'good' },
]
export const nutrientLevelOf = (p) => NUTRIENT_LEVELS.find((l) => p >= l.min)

// 유환님 결과표의 판정 → 화면 문구
export const NUTRIENT_TAGS = {
  유형특이: '이 유형에서 특히 많아요',
  식사량영향: '식사량 점검이 먼저예요',
  공통주의: '대부분의 사람에게 부족해요',
}

export const NUTRIENT_GUIDE = [
  { key: 'protein', label: '단백질', icon: '🥚', basis: 'EAR', role: '근육 같은 몸의 조직을 만들고, 효소·호르몬의 재료가 돼요.', foods: ['달걀', '두부', '생선', '닭가슴살'] },
  { key: 'calcium', label: '칼슘', icon: '🥛', basis: 'EAR', role: '뼈와 치아를 만들고, 신경과 근육이 제 기능을 하는 데 필요해요.', foods: ['우유', '요구르트', '멸치', '두부'] },
  { key: 'phosphorus', label: '인', icon: '🐟', basis: 'EAR', role: '뼈와 치아를 이루는 성분이고, 몸에서 에너지를 쓰는 데 필요해요.', foods: ['우유', '생선', '콩'] },
  { key: 'magnesium', label: '마그네슘', icon: '🥜', basis: 'EAR', role: '에너지를 쓰고, 신경과 근육이 제 기능을 하는 데 필요해요.', foods: ['견과류', '현미', '시금치'] },
  { key: 'iron', label: '철', icon: '🥩', basis: 'EAR', role: '몸 곳곳에 산소를 나르고 혈액을 만드는 데 필요해요.', foods: ['소고기', '굴·조개', '시금치'] },
  { key: 'zinc', label: '아연', icon: '🦪', basis: 'EAR', role: '정상적인 면역 기능과 세포 분열에 필요해요.', foods: ['굴', '소고기', '견과류'] },
  { key: 'vitamin_a', label: '비타민 A', icon: '🥕', basis: 'EAR', role: '어두운 곳에서 눈이 적응하고, 피부와 점막을 건강하게 유지하는 데 필요해요.', foods: ['당근', '시금치', '달걀노른자'] },
  { key: 'vitamin_b1', label: '비타민 B1', icon: '🐷', basis: 'EAR', role: '탄수화물을 에너지로 바꾸는 데 필요해요.', foods: ['돼지고기', '현미', '콩'] },
  { key: 'vitamin_b2', label: '비타민 B2', icon: '🍄', basis: 'EAR', role: '몸에서 에너지를 만드는 데 필요해요.', foods: ['우유', '달걀', '버섯'] },
  { key: 'folate', label: '엽산', icon: '🥬', basis: 'EAR', role: '세포와 혈액을 만드는 데 필요해요.', foods: ['시금치', '브로콜리', '콩'] },
  { key: 'vitamin_c', label: '비타민 C', icon: '🍊', basis: 'EAR', role: '결합조직을 만들고, 철이 흡수되도록 돕고, 유해산소로부터 세포를 보호하는 데 필요해요.', foods: ['귤', '키위', '파프리카'] },
  { key: 'vitamin_d', label: '비타민 D', icon: '☀️', basis: 'AI', role: '칼슘과 인이 흡수되고 쓰이는 데 필요하고, 뼈를 만들고 유지하는 데 필요해요.', foods: ['달걀노른자', '등푸른생선', '버섯'] },
  { key: 'vitamin_e', label: '비타민 E', icon: '🌰', basis: 'AI', role: '유해산소로부터 세포를 보호하는 데 필요해요.', foods: ['견과류', '식물성 기름', '시금치'] },
  { key: 'potassium', label: '칼륨', icon: '🍌', basis: 'AI', role: '몸의 수분과 전해질 균형을 맞추는 데 필요해요.', foods: ['바나나', '감자', '시금치'] },
  { key: 'fiber', label: '식이섬유', icon: '🌾', basis: 'AI', role: '배변 활동을 원활하게 하는 데 도움을 줘요.', foods: ['잡곡밥', '채소', '고구마'] },
]

export const BASIS_TEXT = {
  EAR: '평균필요량(EAR)',
  AI: '충분섭취량(AI)',
}
