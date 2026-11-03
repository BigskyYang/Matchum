import model from '../data/nbti12.json'

// 생활습관 12개 유형(대분류 4 × 세부 3)을 판정한다. 지연님 k-medoids 모델을 휴대폰에서 그대로 재현한다.
// nbti12.json은 bigskyyang/analysis/output/nbti_12types.json을 그대로 복사한 것이다 (계산 순서는 model.steps).
//   응답(ML_*) → 7개 점수(상수 + Σ 계수 × 응답) → PCA 5개 → 가장 가까운 대분류 중심 → 그 대분류의 세부 중심
// 유형 ID: 대분류 N(나무늘보)·A(갓생러)·S(예민보스)·O(워커홀릭) + 세부 번호 1~3. 이름·설명은 types.js
const sqDist = (a, b) => a.reduce((sum, x, i) => sum + (x - b[i]) ** 2, 0)

const nearest = (v, entries) => {
  let best = null
  let bestDist = Infinity
  for (const [key, center] of entries) {
    const dist = sqDist(v, center)
    if (dist < bestDist) [best, bestDist] = [key, dist]
  }
  return best
}

// features: encode.js의 features ({ ML_aerobic: 1, ... }) → { main: 'N', leaf: 'N2' }
export function classify(features, m = model) {
  const x = Object.fromEntries(m.inputs.map(({ name, clip }) => [name, Math.min(clip[1], Math.max(clip[0], features[name]))]))
  const scores = m.scores.map((s) => Object.entries(s.coef).reduce((sum, [name, c]) => sum + c * x[name], s.const))
  const pc = m.pca.components.map((row) => row.reduce((sum, c, i) => sum + c * (scores[i] - m.pca.mean[i]), 0))
  const main = nearest(
    pc,
    m.macro.map((g) => [g.code, g.center]),
  )
  const sub = m.sub[main]
  const names = m.scores.map((s) => s.name)
  const v = sub.features.map((f, i) => (scores[names.indexOf(f)] - sub.mean[i]) / sub.std[i])
  return { main, leaf: nearest(v, Object.entries(sub.centers)) }
}

// 대분류 코드 목록 (N, A, S, O)
export const MAIN_CODES = model.macro.map((g) => g.code)

// 세부 유형 정보 (비율·유형 평균·z 등)
export const typeOf = (id, m = model) => m.types.find((t) => t.id === id)

// 유형 평균의 변수 이름 → encode.js의 features 이름
const FEATURE_KEYS = {
  smoker: 'ML_smoker',
  cigarettes: 'ML_cigarettes_day',
  drink_freq: 'ML_drink_freq_ord',
  drink_amount: 'ML_drink_amount_ord',
  aerobic: 'ML_aerobic',
  strength_days: 'ML_strength_days',
  sedentary_min: 'ML_sedentary_min',
  sleep_hours: 'ML_sleep_hours',
  stress: 'ML_stress',
  breakfast: 'ML_breakfast_freq_ord',
  lunch: 'ML_lunch_freq_ord',
  dinner: 'ML_dinner_freq_ord',
  eating_out: 'ML_eatingout_freq_ord',
}
export const toFeatures = (profile) => Object.fromEntries(Object.entries(FEATURE_KEYS).map(([k, ml]) => [ml, profile[k]]))

// 대분류 평균: 세부 유형 평균을 비율로 가중 평균한다 (조사 가중 평균과 같은 값)
export function mainProfile(code, m = model) {
  const subs = m.types.filter((t) => t.id[0] === code)
  const total = subs.reduce((sum, t) => sum + t.share, 0)
  return Object.fromEntries(
    Object.keys(subs[0].profile).map((k) => [k, subs.reduce((sum, t) => sum + t.profile[k] * t.share, 0) / total]),
  )
}

export { model }
