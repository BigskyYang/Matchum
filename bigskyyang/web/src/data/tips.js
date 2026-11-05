// 응답자 본인의 생활습관에서 개선할 점을 골라 보여주는 규칙. 배열 순서가 우선순위다.
// when(features, extras): 해당하면 true
//   personal: true면 2단계 문항(흡연·음주·채소·과일·식품)을 쓰는 팁 → 개인 결과에만, 없으면 유형 결과에
//   mission: '이번 주 해볼 것' { icon(components/Icon.jsx 아이콘 이름), title, detail }
//   foods:   '챙겨 먹으면 좋은 음식' 타일 [{ emoji, label, why }] (개인 결과)
// ※ 의료적 효능을 말하지 않고, 일반적인 생활·식생활 정보 수준으로 쓴다.

export const TIPS = [
  {
    id: 'smoke',
    personal: true,
    when: (f) => f.ML_smoker === 1,
    mission: { icon: 'smoke', title: '금연 상담 받아보기', support: 'smoke', detail: '가까운 보건소 금연클리닉에서 무료로 상담받을 수 있어요.' },
    foods: [{ emoji: '🍊', label: '귤·키위', why: '매일 간식으로' }],
  },
  {
    id: 'drink',
    personal: true,
    when: (f) => f.ML_drink_freq_ord >= 4 || f.ML_drink_amount_ord >= 3,
    mission: { icon: 'drink', title: '술자리 한 번 줄이기', support: 'drink', detail: '횟수와 한 번에 마시는 양을 조금씩 줄여 보세요.' },
    foods: [{ emoji: '🐟', label: '두부·생선 안주', why: '술 마실 때 함께' }],
  },
  {
    id: 'breakfast',
    when: (f) => f.ML_breakfast_freq_ord <= 1,
    mission: { icon: 'sunrise', title: '간단한 아침 챙기기', detail: '우유 한 잔, 바나나 하나로도 충분해요.' },
    foods: [
      { emoji: '🥛', label: '우유·요구르트', why: '간단한 아침' },
      { emoji: '🍌', label: '바나나', why: '간단한 아침' },
    ],
  },
  {
    id: 'skip_meal',
    when: (f) => f.ML_lunch_freq_ord <= 1 || f.ML_dinner_freq_ord <= 1,
    mission: { icon: 'clock', title: '세 끼 시간 맞추기', detail: '하루 세 끼를 비슷한 시간에 먹어 보세요.' },
  },
  {
    id: 'aerobic',
    when: (f) => f.ML_aerobic === 0,
    mission: { icon: 'active', title: '하루 30분 빠르게 걷기', detail: '일주일에 150분이 목표예요. 출퇴근길 한 정거장 걷기부터!' },
  },
  {
    id: 'strength',
    when: (f) => f.ML_strength_days < 2,
    mission: { icon: 'exercise', title: '주 2회 근력운동', detail: '스쿼트·팔굽혀펴기 10개씩부터 시작해 보세요.' },
  },
  {
    id: 'sleep_short',
    when: (f) => f.ML_sleep_hours < 6,
    mission: { icon: 'sleep', title: '30분 일찍 잠들기', detail: '잠드는 시각을 조금씩 앞당겨 보세요.' },
  },
  {
    id: 'sleep_long',
    when: (f) => f.ML_sleep_hours > 9.5,
    mission: { icon: 'alarm', title: '기상 시각 고정하기', detail: '주말에도 비슷한 시간에 일어나 보세요.' },
  },
  {
    id: 'stress',
    when: (f) => f.ML_stress === 1,
    mission: { icon: 'leaf', title: '하루 10분 쉬어가기', detail: '짧은 산책이나 깊은 호흡으로 쉬는 시간을 만들어 보세요.' },
  },
  {
    id: 'sedentary',
    when: (f) => f.ML_sedentary_min >= 600,
    mission: { icon: 'armchair', title: '1시간마다 일어나기', detail: '잠깐 걷거나 스트레칭만 해도 좋아요.' },
  },
  {
    id: 'eating_out',
    when: (f) => f.ML_eatingout_freq_ord >= 4,
    mission: { icon: 'kitchen', title: '주 2번 집밥·도시락', detail: '외식할 때는 국물은 덜, 채소 반찬은 더!' },
    foods: [{ emoji: '🥬', label: '채소 반찬', why: '외식할 때 추가' }],
  },
  {
    id: 'veg',
    personal: true,
    when: (_, x) => x.veg !== null && x.veg < 6,
    foods: [{ emoji: '🥦', label: '채소·나물', why: '하루 한 번 이상' }],
  },
  {
    id: 'fruit',
    personal: true,
    when: (_, x) => x.fruit !== null && x.fruit < 6,
    foods: [{ emoji: '🍎', label: '과일', why: '하루 1~2회 간식' }],
  },
  {
    id: 'protein',
    personal: true,
    // 고기·생선·달걀·두부 중 어느 것도 하루 1회 이상 먹지 않음 (mini-FFQ 5 = 하루 1회)
    when: (_, x) => x.ffq !== null && Math.max(x.ffq.meat, x.ffq.fish, x.ffq.egg, x.ffq.legume) < 5,
    foods: [
      { emoji: '🥚', label: '달걀', why: '매끼 단백질' },
      { emoji: '🫘', label: '콩·두부', why: '매끼 단백질' },
    ],
  },
  {
    id: 'dairy',
    personal: true,
    when: (_, x) => x.ffq !== null && x.ffq.dairy < 5,
    foods: [{ emoji: '🧀', label: '치즈·요구르트', why: '하루 1회 이상' }],
  },
]

// 고칠 점이 없을 때 보여줄 기본 음식
export const BALANCED_FOODS = [
  { emoji: '🍚', label: '잡곡밥', why: '골고루' },
  { emoji: '🥦', label: '채소', why: '골고루' },
  { emoji: '🐟', label: '생선', why: '골고루' },
  { emoji: '🍎', label: '과일', why: '골고루' },
]

// personal: false = 유형 결과용 팁, true = 개인 결과용 팁
export const pickTips = (features, extras, personal = false) =>
  TIPS.filter((t) => Boolean(t.personal) === personal && t.when(features, extras))
