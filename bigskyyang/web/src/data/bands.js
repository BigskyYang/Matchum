// 재준님 등급(High·Mid·Low)의 화면 이름과 색. 개인 결과(NutritionRisk)와 시뮬레이터(SimulatePage)가 같이 쓴다
//   판정처럼 보이지 않게 경향으로: 부족하기 쉬워요 · 보통 · 잘 챙기는 편 (나트륨은 많이 먹을 위험이라 따로)
export const BAND_CLS = { High: 'bg-primary-soft text-primary-shade', Mid: 'bg-butter text-ink', Low: 'bg-mint text-ink' }
export const BAND_LABELS = {
  lack: { High: '부족하기 쉬워요', Mid: '보통', Low: '잘 챙기는 편' },
  excess: { High: '많이 먹기 쉬워요', Mid: '보통', Low: '잘 조절하는 편' },
}
export const bandLabel = (n, band) => BAND_LABELS[n.excess ? 'excess' : 'lack'][band]
