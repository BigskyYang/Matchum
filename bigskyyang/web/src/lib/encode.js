// 설문 응답 → 모델 입력 변수(ML_*) + 결과 해석용 값
// 변환 규칙은 bigskyyang/사용자_설문조사_초안.html, docs/KNHANES_2022_2024_데이터명세서.pdf 기준
// 팀 합의 (2026-11-04, 지연님 군집 모델·재준님 영양 모델에 같은 값을 넣는다)
//   흡연: 궐련(일반 담배)·전자담배를 구분하지 않고 지금 피우는지만
//   유산소: 중강도·고강도를 나눠 묻지 않고, 합친 시간이 주 150분 이상인지만 (고강도 ×2 계산 없음)
//   수면: 취침·기상 시각으로만 계산 ('날마다 들쭉날쭉' 보기는 두지 않는다)
//   나이: 생년월일로 계산한 만 나이
// 1단계만 답한 상태에서도 쓸 수 있다: 2단계 문항(흡연·음주·채소·과일·식품)에 답하지 않았으면 0 또는 null

const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v))

const toMinutes = (hhmm) => {
  const [h, m] = hhmm.split(':').map(Number)
  return h * 60 + m
}

// 유산소 운동 문항(주 몇 시간, 0~5) → 3시간 이상이면 주 150분 이상 (팀 합의 aerobic_150min)
export const AEROBIC_HOURS = 3

// 취침·기상 시각으로 수면 시간(시간) 계산. 자정을 넘기면 다음 날로 본다
export const sleepHours = (bed, wake) => {
  let diff = toMinutes(wake) - toMinutes(bed)
  if (diff <= 0) diff += 24 * 60
  return diff / 60
}

// 생년월일 'YYYY-MM-DD' → 만 나이 (올해 생일이 아직 지나지 않았으면 한 살 적게)
export function ageFromBirth(birth, today = new Date()) {
  const [y, m, d] = birth.split('-').map(Number)
  const month = today.getMonth() + 1
  const passed = month > m || (month === m && today.getDate() >= d)
  return today.getFullYear() - y - (passed ? 0 : 1)
}

const FFQ_KEYS = ['meat', 'fish', 'egg', 'legume', 'dairy']

// 평균 수면 = (주중×5 + 주말×2) / 7. 주말도 비슷하다고 했으면 주중 값 그대로 (재준님 v1.4.1 규칙과 같다)
function sleepOf(a) {
  const weekday = sleepHours(a.weekday_bed, a.weekday_wake)
  const weekend = a.weekend_same === 'no' ? sleepHours(a.weekend_bed, a.weekend_wake) : weekday
  return (weekday * 5 + weekend * 2) / 7
}

export function encode(a) {
  // 앞 문항 응답을 바꿔 건너뛰게 된 문항의 옛 응답은 무시한다
  // 현재 흡연 = 요즘 피움 (매일·가끔, 궐련·전자담배 모두)
  const smoker = a.smoke_now === 'yes' ? 1 : 0
  const drinkFreq = a.drink_freq ?? 0
  const drinkAmount = drinkFreq > 0 ? a.drink_amount : 0
  const meals = a.meals ?? {}

  const features = {
    ML_smoker: smoker,
    ML_cigarettes_day: smoker ? clamp(a.cigarettes, 0, 60) : 0,
    ML_drink_month: drinkFreq >= 2 ? 1 : 0,
    ML_drink_freq_ord: drinkFreq,
    ML_drink_amount_ord: drinkAmount,
    // 유산소 신체활동: 숨이 찰 정도의 운동을 합쳐 주 150분 이상 = 보기 '3시간' 이상 (AEROBIC_HOURS)
    ML_aerobic: a.activity >= AEROBIC_HOURS ? 1 : 0,
    ML_strength_days: a.strength_days,
    ML_sedentary_min: clamp(a.sedentary_min, 0, 24 * 60),
    ML_sleep_hours: sleepOf(a),
    ML_stress: a.stress <= 2 ? 1 : 0,
    ML_breakfast_freq_ord: meals.breakfast,
    ML_lunch_freq_ord: meals.lunch,
    ML_dinner_freq_ord: meals.dinner,
    ML_eatingout_freq_ord: a.eating_out,
  }

  const extras = {
    sex: a.sex,
    age: ageFromBirth(a.birth_date),
    // 2단계 문항 (답하지 않았으면 null)
    veg: a.veg ?? null,
    fruit: a.fruit ?? null,
    // mini-FFQ 5문항 (재준님 mini-FFQ 모델 입력 meat_ord … dairy_ord, 0~7). 65세 이상은 묻지 않아 null
    ffq: FFQ_KEYS.every((k) => a[`ffq_${k}`] !== undefined) ? Object.fromEntries(FFQ_KEYS.map((k) => [k, a[`ffq_${k}`]])) : null,
  }

  return { features, extras }
}
