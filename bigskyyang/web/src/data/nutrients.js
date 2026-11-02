// 영양소 14종 정보 (Jaejun/config/targets.json, Jaejun/README.md 기준)
// auc: 2024 독립검증 AUC. RELIABLE_AUC 미만은 결과 화면에서 '참고'로 표시한다
// foods: 챙겨 먹으면 좋은 대표 음식, supplement: 고려해 볼 수 있는 건강기능식품 원료(없으면 음식으로만 안내)
// excess: true면 '부족'이 아니라 '과잉' 위험

export const RELIABLE_AUC = 0.75

export const NUTRIENTS = [
  { key: 'protein', label: '단백질', icon: '🥚', auc: 0.913, foods: ['달걀', '두부', '생선', '닭가슴살'], supplement: '단백질' },
  { key: 'calcium', label: '칼슘', icon: '🥛', auc: 0.808, foods: ['우유', '요구르트', '멸치', '두부'], supplement: '칼슘' },
  { key: 'magnesium', label: '마그네슘', icon: '🥜', auc: 0.767, foods: ['견과류', '현미', '시금치'], supplement: '마그네슘' },
  { key: 'iron', label: '철', icon: '🥩', auc: 0.86, foods: ['소고기', '굴·조개', '시금치'], supplement: '철' },
  { key: 'zinc', label: '아연', icon: '🦪', auc: 0.859, foods: ['굴', '소고기', '견과류'], supplement: '아연' },
  { key: 'phosphorus', label: '인', icon: '🐟', auc: 0.92, foods: ['우유', '생선', '콩'] },
  { key: 'vitamin_a', label: '비타민 A', icon: '🥕', auc: 0.709, foods: ['당근', '시금치', '달걀노른자'], supplement: '비타민 A' },
  { key: 'vitamin_b1', label: '비타민 B1', icon: '🐷', auc: 0.774, foods: ['돼지고기', '현미', '콩'], supplement: '비타민 B1' },
  { key: 'vitamin_b2', label: '비타민 B2', icon: '🍄', auc: 0.824, foods: ['우유', '달걀', '버섯'], supplement: '비타민 B2' },
  { key: 'folate', label: '엽산', icon: '🥬', auc: 0.756, foods: ['시금치', '브로콜리', '콩'], supplement: '엽산' },
  { key: 'vitamin_c', label: '비타민 C', icon: '🍊', auc: 0.672, foods: ['귤', '키위', '파프리카'], supplement: '비타민 C' },
  { key: 'fiber', label: '식이섬유', icon: '🌾', auc: 0.707, foods: ['잡곡밥', '채소', '고구마'], supplement: '식이섬유' },
  { key: 'potassium', label: '칼륨', icon: '🍌', auc: 0.759, foods: ['바나나', '감자', '시금치'] },
  { key: 'sodium_excess', label: '나트륨', icon: '🧂', auc: 0.751, excess: true, foods: ['국물 덜 먹기', '젓갈·장아찌 줄이기', '라면·가공식품 줄이기'] },
]

export const BANDS = {
  High: { label: '주의', tone: 'poor' },
  Mid: { label: '보통', tone: 'fair' },
  Low: { label: '양호', tone: 'good' },
}
