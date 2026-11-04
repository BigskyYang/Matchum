// 설문 응답 → 모델 입력 변수(ML_*) + 결과 해석용 값
// 변환 규칙은 bigskyyang/사용자_설문조사_초안.html, docs/KNHANES_2022_2024_데이터명세서.pdf 기준
// 1단계만 답한 상태에서도 쓸 수 있다: 2단계 문항(흡연·음주·채소·과일·식품)에 답하지 않았으면 0 또는 null

const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v))

const toMinutes = (hhmm) => {
  const [h, m] = hhmm.split(':').map(Number)
  return h * 60 + m
}

// 취침·기상 시각으로 수면 시간(시간) 계산. 자정을 넘기면 다음 날로 본다
export const sleepHours = (bed, wake) => {
  let diff = toMinutes(wake) - toMinutes(bed)
  if (diff <= 0) diff += 24 * 60
  return diff / 60
}

// 출생연도 → 나이 (올해 생일이 지났다고 본다. 나이대만 쓰므로 1살 차이는 괜찮다)
export const ageFromYear = (year, today = new Date()) => today.getFullYear() - year

// '평균 몇 시간'으로 답한 수면을 모델 척도로 바꾼다.
// KNHANES 2022·2023은 수면 시간을 직접 물었고(평균 0.5시간 짧게 나옴) 2024는 취침·기상 시각으로 물었다.
// 지연님 모델은 2024 척도로 맞춰 학습했으므로, 직접 답한 시간은 2022–23 분포 → 2024 분포로 옮긴다
// (Jiyeon/kmedoids_model.json sleep_year_adjust의 2022·2023 평균, 2024 값)
const SLEEP_ASKED = { mean: (6.968 + 6.816) / 2, std: (1.262 + 1.237) / 2 }
const SLEEP_2024 = { mean: 7.408, std: 1.225 }
export const sleepFromAverage = (hours) =>
  ((hours - SLEEP_ASKED.mean) / SLEEP_ASKED.std) * SLEEP_2024.std + SLEEP_2024.mean

const FFQ_KEYS = ['meat', 'fish', 'egg', 'legume', 'dairy']

function sleepOf(a) {
  if (a.sleep_regular === 'no') return { hours: sleepFromAverage(a.sleep_avg / 60), irregular: true }
  const weekday = sleepHours(a.weekday_bed, a.weekday_wake)
  const weekend = a.weekend_same === 'no' ? sleepHours(a.weekend_bed, a.weekend_wake) : weekday
  return { hours: (weekday * 5 + weekend * 2) / 7, irregular: false }
}

export function encode(a) {
  // 앞 문항 응답을 바꿔 건너뛰게 된 문항의 옛 응답은 무시한다
  // 현재 흡연 = 요즘 매일·가끔 피움, 전자담배 포함
  // (KNHANES 학습 자료는 '궐련 평생 100개비 이상 + 현재 흡연'. 지금 피우는 사람은 거의 모두 해당하고, 전자담배만 피우는 사람만 다르다)
  const smoker = a.smoke_now === 'daily' || a.smoke_now === 'sometimes' ? 1 : 0
  const drinkFreq = a.drink_freq ?? 0
  const drinkAmount = drinkFreq > 0 ? a.drink_amount : 0
  const sleep = sleepOf(a)
  const meals = a.meals ?? {}

  const features = {
    ML_smoker: smoker,
    ML_cigarettes_day: smoker ? clamp(a.cigarettes, 0, 60) : 0,
    ML_drink_month: drinkFreq >= 2 ? 1 : 0,
    ML_drink_freq_ord: drinkFreq,
    ML_drink_amount_ord: drinkAmount,
    // 유산소 신체활동: 중강도 + 고강도×2 가 주 150분 이상 (KNHANES pa_aerobic 기준) = 보기 '2시간 반 이상'
    ML_aerobic: a.activity === 3 ? 1 : 0,
    ML_strength_days: a.strength_days,
    ML_sedentary_min: clamp(a.sedentary_min, 0, 24 * 60),
    ML_sleep_hours: sleep.hours,
    ML_stress: a.stress <= 2 ? 1 : 0,
    ML_breakfast_freq_ord: meals.breakfast,
    ML_lunch_freq_ord: meals.lunch,
    ML_dinner_freq_ord: meals.dinner,
    ML_eatingout_freq_ord: a.eating_out,
  }

  const extras = {
    sex: a.sex,
    age: ageFromYear(a.birth_year),
    // 수면 시간이 들쭉날쭉하다고 답함 (교대·야간 근무 포함) → 수면·식사 시간 미션
    sleepIrregular: sleep.irregular,
    // 2단계 문항 (답하지 않았으면 null)
    veg: a.veg ?? null,
    fruit: a.fruit ?? null,
    // mini-FFQ 5문항 (재준님 mini-FFQ 모델 입력 meat_ord … dairy_ord, 0~7). 65세 이상은 묻지 않아 null
    ffq: FFQ_KEYS.every((k) => a[`ffq_${k}`] !== undefined) ? Object.fromEntries(FFQ_KEYS.map((k) => [k, a[`ffq_${k}`]])) : null,
  }

  return { features, extras }
}
