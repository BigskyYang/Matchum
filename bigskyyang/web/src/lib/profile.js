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

// 배열 평균값을 { ML_*: 값 } 형태로
export const toFeatures = (featureNames, values) => Object.fromEntries(featureNames.map((name, i) => [name, values[i]]))

export const groupScores = (model, label) => scores(toFeatures(model.features, model.profiles[label].mean))

// 전체 평균 대비 크게 다른 항목(z ≥ 0.5)을 해시태그로. [평균보다 높을 때, 낮을 때]
const TAGS = {
  ML_smoker: ['#흡연러', '#비흡연'],
  ML_cigarettes_day: ['#흡연량많음', null],
  ML_drink_month: ['#애주가', '#술안마심'],
  ML_drink_freq_ord: ['#술자리잦음', '#술안마심'],
  ML_drink_amount_ord: ['#주량많음', null],
  ML_aerobic: ['#유산소러', '#운동부족'],
  ML_strength_days: ['#근력러', '#근력운동0'],
  ML_sedentary_min: ['#의자붙박이', '#활동파'],
  ML_sleep_hours: ['#꿀잠러', '#수면부족'],
  ML_stress: ['#스트레스많음', '#마음평화'],
  ML_breakfast_freq_ord: ['#아침챙김', '#아침패스'],
  ML_lunch_freq_ord: [null, '#점심패스'],
  ML_dinner_freq_ord: [null, '#저녁패스'],
  ML_eatingout_freq_ord: ['#외식러', '#집밥러'],
}

export function hashtags(model, label, limit = 4) {
  const all = model.profiles.all.mean
  const group = model.profiles[label].mean
  const std = model.root.std
  const picked = []
  model.features
    .map((name, i) => ({ name, z: (group[i] - all[i]) / std[i] }))
    .filter((t) => Math.abs(t.z) >= 0.5)
    .sort((a, b) => Math.abs(b.z) - Math.abs(a.z))
    .forEach(({ name, z }) => {
      const tag = TAGS[name]?.[z > 0 ? 0 : 1]
      if (tag && !picked.includes(tag)) picked.push(tag)
    })
  return picked.slice(0, limit)
}

// 조사 대상자 중 이 유형의 비율(%)
export const share = (model, label) => (model.profiles[label].n / model.profiles.all.n) * 100

// 같이 다니면 좋은 유형: 내가 약한 영역을 잘 챙기는 대분류 유형.
// 내 점수보다 그 유형 평균이 높은 만큼을 모두 더해 가장 큰 유형을 고르고, 차이가 큰 영역 2개를 이유로 든다.
export function bestPartner(model, myScores, myMain, mainLabels) {
  const ranked = mainLabels
    .filter((label) => label !== myMain)
    .map((label) => {
      const theirs = groupScores(model, label)
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
