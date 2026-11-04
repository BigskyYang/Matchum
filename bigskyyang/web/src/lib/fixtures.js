// 테스트용 설문 응답 예시: 비흡연·비음주, 운동 부족, 아침 결식
export const SAMPLE = {
  // 1단계
  sex: 2,
  birth_year: 2001,
  activity: 2, // 주 1시간 ~ 2시간 반 미만 → 유산소 미달
  strength_days: 0,
  sedentary_min: 600,
  sleep_regular: 'yes',
  weekday_bed: '01:00',
  weekday_wake: '07:00',
  weekend_same: 'no',
  weekend_bed: '02:00',
  weekend_wake: '10:00',
  stress: 2,
  meals: { breakfast: 0, lunch: 3, dinner: 3 },
  eating_out: 4,
  // 2단계
  smoke_now: 'never',
  drink_freq: 0,
  veg: 5,
  fruit: 3,
  ffq_meat: 3,
  ffq_fish: 2,
  ffq_egg: 3,
  ffq_legume: 2,
  ffq_dairy: 2,
  health: ['none'],
  supplements: ['none'],
}

// 1단계까지만 답한 상태
export const STAGE1_SAMPLE = Object.fromEntries(
  Object.entries(SAMPLE).filter(
    ([k]) => !['smoke_now', 'drink_freq', 'veg', 'fruit', 'health', 'supplements'].includes(k) && !k.startsWith('ffq_'),
  ),
)
