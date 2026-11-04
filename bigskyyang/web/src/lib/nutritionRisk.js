// 개인 영양 위험 예측: 재준님 모델(가중치 v1.4-web-retrained, 입력 규칙 v1.4.1-web-feedback)을 휴대폰에서 계산한다
// 모델 값은 data/nutritionModels.json (scripts/export_nutrition_models.py가 재준님 joblib에서 옮긴 것)
//   생활습관 모델(lifestyle): 영양소 14개, 입력 18개 (1·2단계 생활습관 + 채소·과일)
//   평소 식사 모델(habitual, mini-FFQ): 영양소 10개, 19~64세만 (입력: 성별·나이 + 5문항)
// 두 확률은 평균하지 않고 따로 보여 준다. 등급(낮음·보통·높음)은 학습 자료 안에서의 상대 등급이며 결핍 진단이 아니다
import { ageFromBirth } from './encode.js'

const sigmoid = (z) => 1 / (1 + Math.exp(-z))

function logistic(m, x) {
  let z = m.intercept
  for (let i = 0; i < x.length; i++) z += (m.coef[i] * (x[i] - m.mean[i])) / m.scale[i]
  return sigmoid(z)
}

// HistGradientBoosting: 트리마다 값 <= 경계면 왼쪽으로 내려가 잎 값을 더한다
function hgb(m, x) {
  let raw = m.baseline
  for (const t of m.trees) {
    let i = 0
    while (t.f[i] !== -1) i = x[t.f[i]] <= t.t[i] ? t.l[i] : t.r[i]
    raw += t.t[i]
  }
  return sigmoid(raw)
}

export const probability = (m, x) => (m.type === 'hgb' ? hgb(m, x) : logistic(m, x))

// 등급 경계는 재준님 코드와 같게 (생활습관은 <, 평소 식사는 <=)
const lifestyleBand = (c, p) => (p < c.low_mid ? 'Low' : p < c.mid_high ? 'Mid' : 'High')
const habitualBand = (c, p) => (p <= c.low_max ? 'Low' : p <= c.mid_max ? 'Mid' : 'High')

// 생활습관 모델 입력 18개 (Jaejun/nutrition_final_feedback_applied/config/encoding_contract.json)
//   features: encode.js의 ML_* (끼니·외식·음주 방향은 학습 자료와 같다)
//   채소·과일: 웹은 클수록 자주(8 = 하루 3회 이상), 모델은 1 = 하루 3회 이상 … 9 = 거의 안 함
//   수면: encode.js와 같은 (주중×5 + 주말×2)/7 (재준님 규칙과 같다)
//   나이: 생년월일로 계산한 만 나이 (팀 합의, 재준님 파이프라인도 웹이 넘긴 값을 그대로 쓴다)
export function lifestyleFeatures(answers, features) {
  return {
    설명_sex: answers.sex,
    설명_age: ageFromBirth(answers.birth_date),
    ...features,
    식습관_LS_FRUIT: 9 - answers.fruit,
    식습관_LS_VEG2: 9 - answers.veg,
  }
}

// 평소 식사 모델 입력. 19~64세가 아니거나 5문항을 다 답하지 않았으면 null
export function habitualFeatures(extras) {
  if (!extras.ffq || extras.age < 19 || extras.age > 64) return null
  const { meat, fish, egg, legume, dairy } = extras.ffq
  return { sex: extras.sex, age: extras.age, meat_ord: meat, fish_ord: fish, egg_ord: egg, legume_ord: legume, dairy_ord: dairy }
}

const predictAll = (module, row, band) =>
  Object.fromEntries(
    Object.entries(module.models).map(([n, m]) => {
      const p = probability(m, module.features.map((f) => row[f]))
      return [n, { probability: p, band: band(module.cuts[n], p) }]
    }),
  )

// → { lifestyle: { 영양소: { probability, band } }, habitual: 같은 모양 | null }
export function predictNutrition(models, lifestyleRow, habitualRow) {
  return {
    version: models.version,
    lifestyle: predictAll(models.lifestyle, lifestyleRow, lifestyleBand),
    habitual: habitualRow ? predictAll(models.habitual, habitualRow, habitualBand) : null,
  }
}
