import stats from '../data/surveyStats.json'
import { ageFromBirth } from './encode.js'

// 설문 중간 통계 카드: 문항에 답하면 다음 문항 위에 "나처럼 ~한 30대 여성은 약 55%예요"
//   비율: data/surveyStats.json (bigskyyang/scripts/build_survey_stats.py, 국건영 2022~2024 가중 비율)
//   습관 기준은 미션 규칙(data/tips.js)과 같다. 내 답이 해당하면 그 비율, 아니면 100 − 비율
//   숫자는 5% 단위로 반올림하고 5~95%로 자른다 (작은 차이를 정확한 값처럼 보이지 않게)
export const roundPct = (p) => Math.min(95, Math.max(5, Math.round(p / 5) * 5))

// 문항 ID → 통계. has: 내 답이 그 습관에 해당하는지, yes·no: 해당할 때·아닐 때 문구
export const FACTS = {
  activity: { label: '운동 시간', habit: 'aerobic', has: (a) => a.activity === 3, yes: '주 2시간 반 이상 운동하는', no: '운동이 주 2시간 반이 안 되는' },
  sedentary_min: {
    label: '앉아 있는 시간',
    habit: 'sedentary',
    has: (a) => a.sedentary_min >= 600,
    yes: '하루 10시간 이상 앉아 있는',
    no: '앉아 있는 시간이 하루 10시간이 안 되는',
  },
  stress: { label: '스트레스', habit: 'stress', has: (a) => a.stress <= 2, yes: '스트레스를 많이 느끼는', no: '스트레스를 많이 느끼지 않는' },
  meals: { label: '아침 식사', habit: 'breakfast', has: (a) => a.meals?.breakfast <= 1, yes: '아침을 주 2번 이하로 먹는', no: '아침을 주 3번 이상 먹는' },
}

const SEX = { 1: '남성', 2: '여성' }

// 성별·생년월일 → 통계 칸과 이름 ('30대 여성'). 나이대 칸이 없으면 성별 전체
export function peerGroup(answers, today = new Date()) {
  const sex = answers.sex
  if (!SEX[sex] || !answers.birth_date) return null
  const age = ageFromBirth(answers.birth_date, today)
  const decade = Math.max(20, Math.floor(Math.min(age, 79) / 10) * 10)
  const key = `${sex}-${decade}`
  if (stats.groups[key]) return { key, label: `${decade === 20 ? '19~29세' : decade === 70 ? '70대 이상' : `${decade}대`} ${SEX[sex]}` }
  return { key: `${sex}`, label: `성인 ${SEX[sex]}` }
}

// 방금 답한 문항(qid)의 통계 카드 → { label, lead, pct, tail } 또는 null
export function surveyFact(qid, answers, today = new Date()) {
  const fact = FACTS[qid]
  if (!fact || answers[qid] === undefined) return null
  const group = peerGroup(answers, today)
  if (!group) return null
  const p = stats.groups[group.key][fact.habit]
  const has = fact.has(answers)
  // '남성'·'여성'으로 끝나므로 조사는 '은'
  return { label: fact.label, lead: `나처럼 ${has ? fact.yes : fact.no} ${group.label}은`, pct: roundPct(has ? p : 100 - p), tail: '%예요' }
}
