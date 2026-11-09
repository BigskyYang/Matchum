import model from '../data/nbti12.json'

// 생활습관 12개 유형(대분류 4 × 세부 3)을 판정한다. 지연님 k-medoids 모델을 휴대폰에서 그대로 재현한다.
// nbti12.json은 analysis/01_clustering/validation/output/nbti_12types.json을 그대로 복사한 것이다 (계산 순서는 model.steps).
//   응답(ML_*) → 7개 점수(상수 + Σ 계수 × 응답) → PCA 5개 → 가장 가까운 대분류 중심 → 그 대분류의 세부 중심
// 유형 ID: 대분류 N(나무늘보)·A(갓생러)·S(예민보스)·O(워커홀릭) + 세부 번호 1~3. 이름·설명은 types.js
const sqDist = (a, b) => a.reduce((sum, x, i) => sum + (x - b[i]) ** 2, 0)

// 중심까지 거리가 가까운 순서 [[key, 거리], ...] (거리가 같으면 먼저 나온 것이 앞, sort는 안정 정렬)
const ranked = (v, entries) => entries.map(([key, center]) => [key, Math.sqrt(sqDist(v, center))]).sort((a, b) => a[1] - b[1])

// 경계 여유: (두 번째 거리 − 가장 가까운 거리) ÷ 두 번째 거리. 0이면 두 유형의 정확히 가운데, 1이면 유형 중심 위
//   analysis/01_clustering/validation/07_boundary.py의 margin과 같은 정의
const marginOf = (r) => (r[1][1] > 0 ? (r[1][1] - r[0][1]) / r[1][1] : 1)

// 대분류 code 안에서 세부 유형 거리 순서
function rankLeaves(scores, code, m) {
  const sub = m.sub[code]
  const names = m.scores.map((s) => s.name)
  const v = sub.features.map((f, i) => (scores[names.indexOf(f)] - sub.mean[i]) / sub.std[i])
  return ranked(v, Object.entries(sub.centers))
}

// features → 유형과 경계 정보
//   main·leaf: 판정한 대분류·세부 유형
//   mainMargin·leafMargin: 대분류·세부 경계 여유 (위 marginOf)
//   mainNeighbor: 두 번째로 가까운 대분류에 들어간다면 될 세부 유형, leafNeighbor: 같은 대분류 안에서 두 번째로 가까운 세부 유형
export function classifyDetail(features, m = model) {
  const x = Object.fromEntries(m.inputs.map(({ name, clip }) => [name, Math.min(clip[1], Math.max(clip[0], features[name]))]))
  const scores = m.scores.map((s) => Object.entries(s.coef).reduce((sum, [name, c]) => sum + c * x[name], s.const))
  const pc = m.pca.components.map((row) => row.reduce((sum, c, i) => sum + c * (scores[i] - m.pca.mean[i]), 0))
  const mains = ranked(
    pc,
    m.macro.map((g) => [g.code, g.center]),
  )
  const leaves = rankLeaves(scores, mains[0][0], m)
  return {
    main: mains[0][0],
    leaf: leaves[0][0],
    mainMargin: marginOf(mains),
    leafMargin: marginOf(leaves),
    mainNeighbor: rankLeaves(scores, mains[1][0], m)[0][0],
    leafNeighbor: leaves[1][0],
  }
}

// features: encode.js의 features ({ ML_aerobic: 1, ... }) → { main: 'N', leaf: 'N2' }
export function classify(features, m = model) {
  const { main, leaf } = classifyDetail(features, m)
  return { main, leaf }
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

// 유형 평균을 비율로 가중 평균한다 (조사 가중 평균과 같은 값). code가 없으면 성인 전체 평균
export function mainProfile(code, m = model) {
  const subs = code ? m.types.filter((t) => t.id[0] === code) : m.types
  const total = subs.reduce((sum, t) => sum + t.share, 0)
  return Object.fromEntries(
    Object.keys(subs[0].profile).map((k) => [k, subs.reduce((sum, t) => sum + t.profile[k] * t.share, 0) / total]),
  )
}

export { model }
