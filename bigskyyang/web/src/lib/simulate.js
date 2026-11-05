// '이렇게 바꾸면?' 시뮬레이터: 습관 몇 개를 바꾼 응답으로 유형·영양소 결과를 다시 계산해 지금과 비교한다
//   응답 단위로 바꾼 뒤 결과 계산(lib/result.js)을 그대로 다시 돌린다. 화면 결과와 계산 방법이 하나라 어긋나지 않는다
//   바꿀 수 있는 습관은 미션 기준(data/tips.js)과 같은 방향. 지금 응답이 이미 그 기준을 넘으면 보여 주지 않는다
//   모델이 학습 자료에서 본 경향을 보여 줄 뿐, 습관을 바꾸면 실제로 그렇게 된다는 뜻이 아니다 (인과 아님)
import { encode } from './encode.js'
import { buildPersonalResult, buildTypeResult } from './result.js'

const toTime = (min) => {
  const m = ((min % 1440) + 1440) % 1440
  return `${String(Math.floor(m / 60)).padStart(2, '0')}:${String(m % 60).padStart(2, '0')}`
}
const minutesOf = (t) => {
  const [h, m] = t.split(':').map(Number)
  return h * 60 + m
}

// id, icon(components/icons.js), label(켜면 이렇게), now(지금 응답 설명), when(보여 줄지), apply(바꾼 응답)
export const CHANGES = [
  {
    id: 'aerobic',
    icon: 'exercise',
    label: '운동을 주 2시간 반 이상',
    when: (a) => a.activity !== 3,
    apply: (a) => ({ ...a, activity: 3 }),
  },
  {
    id: 'strength',
    icon: 'exercise',
    label: '근력운동 주 2일',
    when: (a) => a.strength_days < 2,
    apply: (a) => ({ ...a, strength_days: 2 }),
  },
  {
    id: 'sit',
    icon: 'active',
    label: '하루 2시간 덜 앉기',
    when: (a) => a.sedentary_min >= 360,
    apply: (a) => ({ ...a, sedentary_min: Math.max(0, a.sedentary_min - 120) }),
  },
  {
    // 평일·주말 모두 7시간 (기상 시각은 그대로, 잠드는 시각을 당기거나 늦춘다)
    id: 'sleep',
    icon: 'sleep',
    label: '매일 7시간 자기',
    when: (_, f) => f.ML_sleep_hours < 6 || f.ML_sleep_hours > 9.5,
    apply: (a) => ({ ...a, weekend_same: 'yes', weekday_bed: toTime(minutesOf(a.weekday_wake) - 7 * 60) }),
  },
  {
    id: 'breakfast',
    icon: 'sunrise',
    label: '아침을 주 5번 이상',
    when: (a) => a.meals?.breakfast <= 1,
    apply: (a) => ({ ...a, meals: { ...a.meals, breakfast: 3 } }),
  },
  {
    id: 'meals',
    icon: 'meal',
    label: '점심·저녁 거르지 않기',
    when: (a) => a.meals?.lunch <= 1 || a.meals?.dinner <= 1,
    apply: (a) => ({ ...a, meals: { ...a.meals, lunch: Math.max(a.meals.lunch, 3), dinner: Math.max(a.meals.dinner, 3) } }),
  },
  {
    id: 'eatout',
    icon: 'homeMeal',
    label: '외식을 주 1~2회로',
    when: (a) => a.eating_out >= 4,
    apply: (a) => ({ ...a, eating_out: 2 }),
  },
  { id: 'veg', icon: 'salad', label: '채소를 하루 1번 이상', when: (a) => a.veg !== undefined && a.veg < 6, apply: (a) => ({ ...a, veg: 6 }) },
  { id: 'fruit', icon: 'apple', label: '과일을 하루 1번 이상', when: (a) => a.fruit !== undefined && a.fruit < 6, apply: (a) => ({ ...a, fruit: 6 }) },
  {
    id: 'dairy',
    model: 'habitual',
    icon: 'kitchen',
    label: '우유·유제품 하루 1번',
    when: (a) => a.ffq_dairy !== undefined && a.ffq_dairy < 5,
    apply: (a) => ({ ...a, ffq_dairy: 5 }),
  },
  {
    id: 'legume',
    model: 'habitual',
    icon: 'kitchen',
    label: '두부·콩 하루 1번',
    when: (a) => a.ffq_legume !== undefined && a.ffq_legume < 5,
    apply: (a) => ({ ...a, ffq_legume: 5 }),
  },
  { id: 'smoke', icon: 'smoke', label: '담배 끊기', when: (a) => a.smoke_now === 'yes', apply: (a) => ({ ...a, smoke_now: 'no', cigarettes: 0 }) },
  {
    id: 'drink',
    icon: 'drink',
    label: '술은 한 달 2~4번, 1~2잔',
    when: (a) => a.drink_freq >= 4 || (a.drink_freq > 0 && a.drink_amount >= 3),
    apply: (a) => ({ ...a, drink_freq: Math.min(a.drink_freq, 3), drink_amount: a.drink_freq > 0 ? Math.min(a.drink_amount, 1) : 0 }),
  },
]

// 지금 응답에서 켤 수 있는 습관
export function availableChanges(answers) {
  const { features } = encode(answers)
  return CHANGES.filter((c) => c.when(answers, features)).map((c) => ({ ...c, model: c.model ?? 'lifestyle' }))
}

// 이미 충족한 응답은 낮추지 않는다. 저장된 선택이나 직접 호출에도 같은 규칙을 적용한다.
export const applyChanges = (answers, ids) =>
  CHANGES.filter((c) => ids.includes(c.id)).reduce((a, c) => (c.when(a, encode(a).features) ? c.apply(a) : a), answers)

const bandsOf = (nutrition) => Object.fromEntries([...nutrition.watch, ...nutrition.rest].map((n) => [n.key, n]))

const changesOf = (before, after, field) =>
  Object.values(before)
    .filter((n) => after[n.key] && after[n.key][field] !== n[field])
    .map((n) => ({ key: n.key, label: n.label, icon: n.icon, excess: !!n.excess, source: field === 'band' ? n.source : 'lifestyle', from: n[field], to: after[n.key][field] }))

// 현재 응답 vs 변경 응답. 개선·악화 순으로 정렬하지 않고 현재 결과의 영양소 순서로 비교한다.
//   영양소는 화면과 같은 대표 등급(평소 식사 기준이 있으면 그것, 없으면 생활습관 기준)으로 비교한다
export function simulate(answers, ids, models) {
  const next = applyChanges(answers, ids)
  const t0 = buildTypeResult(answers)
  const t1 = buildTypeResult(next)
  const type = {
    before: { id: t0.leafId, name: t0.name },
    after: { id: t1.leafId, name: t1.name, main: t1.mainType },
    changed: t0.leafId !== t1.leafId,
  }
  if (!models) return { type, nutrients: null, lifestyleNutrients: null, habitualAvailable: false }
  const b0 = bandsOf(buildPersonalResult(answers, models).nutrition)
  const b1 = bandsOf(buildPersonalResult(next, models).nutrition)
  return {
    type,
    nutrients: changesOf(b0, b1, 'band'),
    lifestyleNutrients: changesOf(b0, b1, 'lifestyle'),
    habitualAvailable: Object.values(b0).some((n) => n.habitual !== null),
  }
}
