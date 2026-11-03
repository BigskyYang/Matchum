// 결과 화면용 계산: 생활습관 점수(신호등), 유형 해시태그, 같이 다니면 좋은 유형

const clamp01 = (v) => Math.min(1, Math.max(0, v))

// 생활습관 영역별 점수 (0~1, 높을수록 건강한 습관). 개인 응답과 유형 평균 모두에 쓴다
export const SCORE_AXES = [
  { key: 'smoke', icon: '🚭', label: '금연', score: (f) => clamp01(1 - 0.3 * f.ML_smoker - 0.7 * Math.min(f.ML_cigarettes_day / 20, 1)) },
  { key: 'drink', icon: '🍶', label: '절주', score: (f) => clamp01(1 - (f.ML_drink_freq_ord + f.ML_drink_amount_ord) / 10) },
  { key: 'exercise', icon: '🏋️', label: '운동', score: (f) => clamp01(0.5 * f.ML_aerobic + 0.5 * Math.min(f.ML_strength_days / 3, 1)) },
  // 하루 4시간 이하 = 1, 12시간 이상 = 0
  { key: 'active', icon: '🚶', label: '활동량', score: (f) => clamp01(1 - (f.ML_sedentary_min - 240) / 480) },
  // 7~9시간 = 1, 벗어난 만큼 감점
  {
    key: 'sleep',
    icon: '😴',
    label: '수면',
    score: (f) => {
      const s = f.ML_sleep_hours
      const off = s < 7 ? 7 - s : s > 9 ? s - 9 : 0
      return clamp01(1 - off / 3)
    },
  },
  { key: 'mind', icon: '🧘', label: '마음 여유', score: (f) => clamp01(1 - f.ML_stress) },
  { key: 'meal', icon: '🍚', label: '규칙적 식사', score: (f) => clamp01((f.ML_breakfast_freq_ord + f.ML_lunch_freq_ord + f.ML_dinner_freq_ord) / 9) },
  { key: 'homeMeal', icon: '🏠', label: '집밥', score: (f) => clamp01(1 - f.ML_eatingout_freq_ord / 6) },
]

export const scores = (features) => SCORE_AXES.map((axis) => axis.score(features))

// 점수 → 신호등 단계
export const LEVELS = [
  { min: 0.75, label: '좋아요', tone: 'good' },
  { min: 0.45, label: '보통', tone: 'fair' },
  { min: 0, label: '노력 필요', tone: 'poor' },
]
export const levelOf = (score) => LEVELS.find((l) => score >= l.min)

// 유형 평균(classify.js의 toFeatures로 ML_* 이름으로 바꾼 값)의 신호등 점수
export const groupScores = (typeFeatures) => scores(typeFeatures)

// 전체 평균 대비 크게 다른 항목(|z| ≥ 0.5)을 해시태그로. [평균보다 높을 때, 낮을 때]
// 키는 유형 정보(nbti12.json types[].z)의 변수 이름
const TAGS = {
  smoker: ['#흡연러', '#비흡연'],
  cigarettes: ['#흡연량많음', null],
  drink_freq: ['#술자리잦음', '#술안마심'],
  drink_amount: ['#주량많음', null],
  aerobic: ['#유산소러', '#운동부족'],
  strength_days: ['#근력러', '#근력운동0'],
  sedentary_min: ['#의자붙박이', '#활동파'],
  sleep_hours: ['#꿀잠러', '#수면부족'],
  stress: ['#스트레스많음', '#마음평화'],
  meal_score: ['#삼시세끼', '#끼니패스'],
  breakfast: ['#아침챙김', '#아침패스'],
  lunch: [null, '#점심패스'],
  dinner: [null, '#저녁패스'],
  eating_out: ['#외식러', '#집밥러'],
  veg: ['#채소러', '#채소부족'],
  fruit: ['#과일러', '#과일부족'],
}

export function hashtags(type, limit = 4) {
  const picked = []
  Object.entries(type.z)
    .filter(([, z]) => Math.abs(z) >= 0.5)
    .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
    .forEach(([name, z]) => {
      const tag = TAGS[name]?.[z > 0 ? 0 : 1]
      if (tag && !picked.includes(tag)) picked.push(tag)
    })
  return picked.slice(0, limit)
}

// 같이 다니면 좋은 유형: 내가 약한 영역을 잘 챙기는 대분류 유형.
// 내 점수보다 그 유형 평균이 높은 만큼을 모두 더해 가장 큰 유형을 고르고, 차이가 큰 영역 2개를 이유로 든다.
// mainScores: { 대분류 코드: 그 대분류 평균의 신호등 점수 }
export function bestPartner(myScores, myMain, mainScores) {
  const ranked = Object.entries(mainScores)
    .filter(([label]) => label !== myMain)
    .map(([label, theirs]) => {
      const gains = theirs.map((s, i) => ({ axis: SCORE_AXES[i], gain: s - myScores[i] }))
      const total = gains.reduce((sum, g) => sum + Math.max(0, g.gain), 0)
      return { label, total, gains }
    })
    .sort((a, b) => b.total - a.total)
  const best = ranked[0]
  const helps = best.gains
    .filter((g) => g.gain > 0.05)
    .sort((a, b) => b.gain - a.gain)
    .slice(0, 2)
    .map((g) => g.axis)
  return { label: best.label, helps }
}
