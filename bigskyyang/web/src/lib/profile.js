// 결과 화면용 계산: 생활습관 점수(신호등), 유형 해시태그, 같이 다니면 좋은 유형 2개

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

// 유형 결과에는 유형을 만든 생활습관 영역만, 흡연·음주는 개인 결과에 (유형이 흡연·음주를 거의 가르지 않는다)
const PERSONAL_KEYS = ['smoke', 'drink']
export const TYPE_AXES = SCORE_AXES.filter((a) => !PERSONAL_KEYS.includes(a.key))
export const PERSONAL_AXES = SCORE_AXES.filter((a) => PERSONAL_KEYS.includes(a.key))

export const scores = (features, axes = SCORE_AXES) => axes.map((axis) => axis.score(features))

// 점수 → 신호등 단계
export const LEVELS = [
  { min: 0.75, label: '좋아요', tone: 'good' },
  { min: 0.45, label: '보통', tone: 'fair' },
  { min: 0, label: '노력 필요', tone: 'poor' },
]
export const levelOf = (score) => LEVELS.find((l) => score >= l.min)

// 유형 평균(classify.js의 toFeatures로 ML_* 이름으로 바꾼 값)의 신호등 점수
export const groupScores = (typeFeatures, axes = SCORE_AXES) => scores(typeFeatures, axes)

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

// 같이 다니면 좋은 유형 2개 (세부 유형 12개 중, 내 유형 제외)
//   fill (채워 주는 짝꿍): 내가 약한 영역을 잘 챙기는 유형. 그 유형 평균이 내 점수보다 높은 만큼을 모두 더해 가장 큰 유형
//   together (같이 크는 짝꿍): 나와 같은 영역이 약해 함께 바꿔 보기 좋은 유형.
//     영역마다 '좋아요'(0.75)에 못 미치는 만큼이 나와 겹치는 정도를 더해 가장 큰 유형 (fill과 같은 유형은 뺀다).
//     겹치는 약점이 없으면 생활습관 점수가 가장 비슷한 유형
//   axes: 이유로 드는 영역 (차이·겹침이 큰 순서로 2개까지)
// leafScores: { 세부 유형 ID: 그 유형 평균의 신호등 점수 } (axes와 같은 순서)
const GOOD = LEVELS[0].min
const topAxes = (list) =>
  list
    .filter((g) => g.v > 0.05)
    .sort((a, b) => b.v - a.v)
    .slice(0, 2)
    .map((g) => g.axis)

export function partnerTypes(myScores, myLeaf, leafScores, axes = SCORE_AXES) {
  const others = Object.entries(leafScores).filter(([id]) => id !== myLeaf)
  const sum = (list) => list.reduce((t, g) => t + Math.max(0, g.v), 0)

  const fill = others
    .map(([id, theirs]) => ({ id, gains: theirs.map((s, i) => ({ axis: axes[i], v: s - myScores[i] })) }))
    .map((x) => ({ ...x, total: sum(x.gains) }))
    .sort((a, b) => b.total - a.total)[0]

  const lack = (s) => Math.max(0, GOOD - s)
  const together = others
    .filter(([id]) => id !== fill.id)
    .map(([id, theirs]) => ({
      id,
      shared: theirs.map((s, i) => ({ axis: axes[i], v: Math.min(lack(s), lack(myScores[i])) })),
      distance: theirs.reduce((t, s, i) => t + (s - myScores[i]) ** 2, 0),
    }))
    .map((x) => ({ ...x, total: sum(x.shared) }))
    .sort((a, b) => b.total - a.total || a.distance - b.distance)[0]

  return { fill: { id: fill.id, axes: topAxes(fill.gains) }, together: { id: together.id, axes: topAxes(together.shared) } }
}
