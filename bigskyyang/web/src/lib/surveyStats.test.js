import { describe, expect, it } from 'vitest'
import stats from '../data/surveyStats.json'
import { FACTS, peerGroup, roundPct, surveyFact } from './surveyStats.js'

const TODAY = new Date(2026, 10, 5)

describe('설문 중간 통계 카드', () => {
  it('5% 단위로 반올림하고 5~95%로 자른다', () => {
    expect(roundPct(54.8)).toBe(55)
    expect(roundPct(57.4)).toBe(55)
    expect(roundPct(57.6)).toBe(60)
    expect(roundPct(1.2)).toBe(5)
    expect(roundPct(99)).toBe(95)
  })

  it('나이대는 19~29세를 20대로, 70세 이상을 한 칸으로', () => {
    expect(peerGroup({ sex: 2, birth_date: '2006-01-01' }, TODAY).label).toBe('19~29세 여성')
    expect(peerGroup({ sex: 1, birth_date: '1990-06-01' }, TODAY).label).toBe('30대 남성')
    expect(peerGroup({ sex: 1, birth_date: '1940-01-01' }, TODAY).label).toBe('70대 이상 남성')
    expect(peerGroup({ sex: 1 }, TODAY)).toBeNull()
  })

  it('내 답이 해당하면 그 비율, 아니면 100 − 비율', () => {
    const base = { sex: 2, birth_date: '1990-06-01' }
    const p = stats.groups['2-30'].breakfast
    const skip = surveyFact('meals', { ...base, meals: { breakfast: 1, lunch: 3, dinner: 3 } }, TODAY)
    expect(skip.lead).toBe('나처럼 아침을 주 2번 이하로 먹는 30대 여성은')
    expect(skip.pct).toBe(roundPct(p))
    const eat = surveyFact('meals', { ...base, meals: { breakfast: 3, lunch: 3, dinner: 3 } }, TODAY)
    expect(eat.pct).toBe(roundPct(100 - p))
  })

  it('통계가 없는 문항·아직 답하지 않은 문항은 카드가 없다', () => {
    const base = { sex: 1, birth_date: '1990-06-01' }
    expect(surveyFact('strength_days', { ...base, strength_days: 2 }, TODAY)).toBeNull()
    expect(surveyFact('activity', base, TODAY)).toBeNull()
  })

  it('모든 칸에 습관 비율이 있다', () => {
    for (const g of Object.values(stats.groups)) {
      for (const f of Object.values(FACTS)) expect(g[f.habit]).toBeGreaterThan(0)
    }
  })
})
