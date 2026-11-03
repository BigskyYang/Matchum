// 설문 응답 → 군집 모델 입력 변수(ML_*) + 결과 해석용 값
// 변환 규칙은 bigskyyang/사용자_설문조사_초안.html, docs/KNHANES_2022_2024_데이터명세서.pdf 기준

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

// 생년월일 'YYYY-MM-DD' → 만 나이 (오늘 기준, 생일이 안 지났으면 한 살 뺀다)
export function ageFromBirth(birth, today = new Date()) {
  const [y, m, d] = birth.split('-').map(Number)
  const beforeBirthday = today.getMonth() + 1 < m || (today.getMonth() + 1 === m && today.getDate() < d)
  return today.getFullYear() - y - (beforeBirthday ? 1 : 0)
}

export function encode(a) {
  // 앞 문항 응답을 바꿔 건너뛰게 된 문항의 옛 응답은 무시한다
  const smoker = a.smoke_100 === 'yes' && (a.smoke_now === 'daily' || a.smoke_now === 'sometimes') ? 1 : 0
  const drinkFreq = a.drink_ever === 'yes' ? a.drink_freq : 0
  const drinkAmount = drinkFreq > 0 ? a.drink_amount : 0
  // 유산소 신체활동: 중강도 + 고강도×2 가 주 150분 이상 (KNHANES pa_aerobic 기준)
  const aerobicMin = a.moderate_min + a.vigorous_min * 2
  const weekdaySleep = sleepHours(a.weekday_bed, a.weekday_wake)
  const weekendSleep = sleepHours(a.weekend_bed, a.weekend_wake)

  const features = {
    ML_smoker: smoker,
    ML_cigarettes_day: smoker ? clamp(a.cigarettes, 0, 60) : 0,
    ML_drink_month: drinkFreq >= 2 ? 1 : 0,
    ML_drink_freq_ord: drinkFreq,
    ML_drink_amount_ord: drinkAmount,
    ML_aerobic: aerobicMin >= 150 ? 1 : 0,
    ML_strength_days: a.strength_days,
    ML_sedentary_min: clamp(a.sedentary_min, 0, 24 * 60),
    ML_sleep_hours: (weekdaySleep * 5 + weekendSleep * 2) / 7,
    ML_stress: a.stress <= 2 ? 1 : 0,
    ML_breakfast_freq_ord: a.breakfast,
    ML_lunch_freq_ord: a.lunch,
    ML_dinner_freq_ord: a.dinner,
    ML_eatingout_freq_ord: a.eating_out,
  }

  const extras = {
    sex: a.sex,
    age: ageFromBirth(a.birth),
    aerobicMin,
    weekdaySleep,
    weekendSleep,
    shiftWork: a.shift_work !== 'no',
    veg: a.veg,
    fruit: a.fruit,
    proteinServings: a.protein,
    dairyServings: a.dairy,
    // 선택 문항(PHQ-9·대사건강): 답하지 않았으면 null
    optional: a.extra === 'more' ? optionalAnswers(a) : null,
  }

  return { features, extras }
}

function optionalAnswers(a) {
  const phq = Array.from({ length: 9 }, (_, i) => a[`phq${i + 1}`] ?? 0)
  return {
    phqTotal: phq.reduce((sum, v) => sum + v, 0),
    phqItem9: phq[8],
    hypertension: a.dx_hypertension === 'yes',
    diabetes: a.dx_diabetes === 'yes',
    dyslipidemia: a.dx_dyslipidemia === 'yes',
  }
}
