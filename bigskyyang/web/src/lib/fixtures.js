// 테스트용 설문 응답 예시: 비흡연·비음주, 운동 부족, 아침 결식
export const SAMPLE = {
  // 1단계
  sex: 2,
  birth_date: '2001-01-01',
  activity: 2, // 주 1시간 ~ 2시간 반 미만 → 유산소 미달
  strength_days: 0,
  sedentary_min: 600,
  weekday_bed: '01:00',
  weekday_wake: '07:00',
  weekend_same: 'no',
  weekend_bed: '02:00',
  weekend_wake: '10:00',
  stress: 2,
  meals: { breakfast: 0, lunch: 3, dinner: 3 },
  eating_out: 4,
  // 2단계
  smoke_now: 'no',
  drink_freq: 0,
  veg: 5,
  fruit: 3,
  ffq_meat: 3,
  ffq_fish: 2,
  ffq_egg: 3,
  ffq_legume: 2,
  ffq_dairy: 2,
}

// 오늘 기준 만 나이가 age인 생년월일 (1월 1일생이라 올해 생일은 항상 지났다)
export const bornAt = (age, today = new Date()) => `${today.getFullYear() - age}-01-01`

// 1단계까지만 답한 상태
export const STAGE1_SAMPLE = Object.fromEntries(
  Object.entries(SAMPLE).filter(
    ([k]) => !['smoke_now', 'drink_freq', 'veg', 'fruit'].includes(k) && !k.startsWith('ffq_'),
  ),
)
